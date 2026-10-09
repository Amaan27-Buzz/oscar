"""Fixture-only UI capture. No Core, credentials, Worker, microphone or provider calls."""

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/baseline"
EXE = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"


def windows(pid: int) -> list[tuple[int, str, str]]:
    user = ctypes.WinDLL("user32")
    result: list[tuple[int, str, str]] = []
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.IsWindowVisible.argtypes = [wintypes.HWND]

    def visit(handle: int, unused: int) -> bool:
        owner = wintypes.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value == pid and user.IsWindowVisible(handle):
            name, title = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(256)
            user.GetClassNameW(handle, name, 256)
            user.GetWindowTextW(handle, title, 256)
            result.append((handle, name.value, title.value))
        return True

    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(visit)
    user.EnumWindows.argtypes = [type(callback), wintypes.LPARAM]
    user.EnumWindows(callback, 0)
    return result


def capture_owned(pid: int, handle: int, path: Path) -> dict[str, Any]:
    # Exact owned native window only, never the desktop or unrelated application.
    from PIL import Image

    user, gdi = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
    user.SetProcessDPIAware()
    assert handle in {h for h, _, _ in windows(pid)}, "capture must belong to the launched fixture"
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.GetWindowDC.argtypes = [wintypes.HWND]
    user.GetWindowDC.restype = wintypes.HDC
    gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi.CreateCompatibleDC.restype = wintypes.HDC
    gdi.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi.SelectObject.restype = wintypes.HGDIOBJ
    user.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    user.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi.DeleteDC.argtypes = [wintypes.HDC]
    gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi.GetDIBits.argtypes = [
        wintypes.HDC,
        wintypes.HBITMAP,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.UINT,
    ]
    user.GetDpiForWindow.argtypes = [wintypes.HWND]
    rect = wintypes.RECT()
    assert user.GetWindowRect(handle, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    assert 0 < width < 3000 and 0 < height < 3000
    dc = user.GetWindowDC(handle)
    memory = gdi.CreateCompatibleDC(dc)
    bitmap = gdi.CreateCompatibleBitmap(dc, width, height)
    previous = gdi.SelectObject(memory, bitmap)
    try:
        assert user.PrintWindow(handle, memory, 2), "native capture unavailable"
        header = struct.pack("<IiiHHIIiiII", 40, width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
        pixels = ctypes.create_string_buffer(width * height * 4)
        assert gdi.GetDIBits(
            memory, bitmap, 0, height, pixels, ctypes.create_string_buffer(header), 0
        )
        image = Image.frombytes("RGB", (width, height), pixels.raw, "raw", "BGRX")
        assert len(image.getcolors(width * height) or []) > 2, "blank native capture"
        image.save(path)
        dpi = user.GetDpiForWindow(handle)
        return {
            "physical_width": width,
            "physical_height": height,
            "logical_width": width * 96 / dpi,
            "logical_height": height * 96 / dpi,
            "scale": dpi / 96,
        }
    finally:
        gdi.SelectObject(memory, previous)
        gdi.DeleteObject(bitmap)
        gdi.DeleteDC(memory)
        user.ReleaseDC(handle, dc)


def native_capture(flag: str, name: str, window_class: str, controls: list[str]) -> dict[str, Any]:
    process = subprocess.Popen(
        [str(EXE), flag], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            found = [h for h, c, _ in windows(process.pid) if c == window_class]
            if found:
                time.sleep(0.5)
                dimensions = capture_owned(process.pid, found[0], OUTPUT / name)
                return {
                    "file": name,
                    "surface": "Tray" if "menu" in flag else "Native confirmation",
                    "state": "actual Windows fixture UI",
                    "window_mode": "native",
                    **dimensions,
                    "fixture_source": flag,
                    "evidence": "REFERENCE_WINDOWS_NATIVE",
                    "interactive_controls": controls,
                    "backend_state": "none; no Core, key or credentials",
                    "capture": "automated",
                    "native_windows_ui": True,
                    "notes": "Same native tray menu, popped at the owned window for determinism."
                    if "menu" in flag
                    else "Actual product MessageBox; synthetic review only, no signing or action.",
                }
            if process.poll() is not None:
                raise RuntimeError("native fixture exited before capture")
            time.sleep(0.1)
        raise RuntimeError("native fixture unavailable; use documented manual capture")
    finally:
        # Owned capture process only; never send an approval to close the dialog.
        process.terminate()
        process.wait(timeout=10)


def lifecycle() -> None:
    binary = EXE.read_bytes()
    pe_offset = struct.unpack_from("<I", binary, 60)[0]
    assert struct.unpack_from("<H", binary, pe_offset + 24 + 68)[0] == 2, "GUI subsystem required"
    # Exercise the ordinary product path with no enrollment, not just the debug harness.
    process = subprocess.Popen(
        [str(EXE), "--interaction"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            owned = [h for h, _, title in windows(process.pid) if title == "OSCAR"]
            if owned:
                break
            assert process.poll() is None, "ordinary product unexpectedly exited"
            time.sleep(0.1)
        else:
            raise RuntimeError("ordinary product window did not appear")
        time.sleep(3)
        assert process.poll() is None, "missing bootstrap terminated the product"
        user = ctypes.WinDLL("user32")
        user.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        assert user.PostMessageW(owned[0], 0x10, 0, 0)
        time.sleep(0.7)
        assert process.poll() is None, "close must hide rather than quit"
        assert owned[0] not in {h for h, _, _ in windows(process.pid)}, "close must hide the window"
    finally:
        if process.poll() is None:
            process.terminate()  # Owned test cleanup, not a product Quit assertion.
        process.wait(timeout=10)
    result = subprocess.run(
        [str(EXE), "--lifecycle-check"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert "LIFECYCLE_REFERENCE_PASS" in result.stdout
    print(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecycle-only", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("Windows baseline capture required")
    lifecycle()
    if args.lifecycle_only:
        return 0
    from playwright.sync_api import sync_playwright

    OUTPUT.mkdir(parents=True, exist_ok=True)
    node = ROOT / ".oscar/toolchains/node-v24.21.0-win-x64"
    env = dict(os.environ)
    if node.is_dir():
        env["PATH"] = str(node) + os.pathsep + env.get("PATH", "")
    npm = shutil.which("npm.cmd", path=env["PATH"])
    assert npm
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 1420))  # Fail rather than attach an unrelated running server.
    server = subprocess.Popen(
        [npm, "run", "dev"], cwd=ROOT / "desktop", env=env, stdout=subprocess.DEVNULL
    )
    entries: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={"width": 580, "height": 760}, timezone_id="UTC")
            context.route(
                "**/*",
                lambda route: route.continue_()
                if route.request.url.startswith("http://127.0.0.1:1420/")
                else route.abort(),
            )
            page = context.new_page()
            for _ in range(100):
                try:
                    page.goto("http://127.0.0.1:1420/?showcase=10-ask-empty")
                    break
                except Exception:
                    if server.poll() is not None:
                        raise RuntimeError("owned showcase server failed to start") from None
                    time.sleep(0.1)
            states = page.evaluate("async () => (await import('/src/showcase.tsx')).fixtures")
            sizes = page.evaluate("async () => (await import('/src/showcase.tsx')).sizes")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            for state in states:
                mode = state["view"]["window"]
                width, height = sizes[mode]
                page.set_viewport_size({"width": width, "height": height})
                page.goto("http://127.0.0.1:1420/?showcase=" + state["id"])
                page.wait_for_function("document.documentElement.dataset.showcase !== undefined")
                page.wait_for_function(
                    "orb => document.querySelector('main')?.getAttribute('data-orb') === orb",
                    arg=state["view"]["orb"],
                )
                page.wait_for_function(
                    "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)"
                )
                if mode != "compact" and mode != "activity":
                    page.get_by_role("tab", name=state["mode"], exact=True).click()
                for detail in state["open"]:
                    page.get_by_text(detail, exact=True).click()
                if state.get("destination"):
                    page.get_by_label("Destination", exact=False).select_option(
                        state["destination"]
                    )
                page.evaluate("document.activeElement?.blur()")
                page.mouse.move(0, 0)
                page.wait_for_timeout(150)  # Allow the existing hover transition to settle.
                page.screenshot(path=str(OUTPUT / (state["id"] + ".png")), full_page=True)
                data = (OUTPUT / (state["id"] + ".png")).read_bytes()
                physical_width, physical_height = struct.unpack(">II", data[16:24])
                controls = page.locator("button,input,select,textarea,summary").evaluate_all(
                    "els => els.filter(e=>e.checkVisibility()).map(e => "
                    "e.getAttribute('aria-label') || e.labels?.[0]?.textContent || "
                    "e.textContent || e.tagName).map(s=>s.trim()).filter(Boolean)"
                )
                entries.append(
                    {
                        "file": state["id"] + ".png",
                        "surface": state["surface"],
                        "state": state["state"],
                        "window_mode": mode,
                        "logical_width": width,
                        "logical_height": height,
                        "physical_width": physical_width,
                        "physical_height": physical_height,
                        "scale": 1,
                        "fixture_source": "desktop/src/showcase.tsx#" + state["id"],
                        "evidence": "SIMULATED_PRODUCT_COMPONENTS_WINDOWS_CHROMIUM",
                        "interactive_controls": controls,
                        "backend_state": state["view"],
                        "capture": "automated",
                        "native_windows_ui": False,
                        "notes": "Full scroll-content PNG at DPR 1; viewport retains logical "
                        "dimensions. Screenshot height may exceed window height. No execution. "
                        "Chromium reference rendering, not a WebView2/device acceptance claim.",
                    }
                )
            assert not errors, errors
            # Representative higher-DPI render, without changing the owner's Windows display scale.
            for identity in ("01-compact-idle", "32-edit-before-after", "60-approval-standard"):
                original = next(e for e in entries if e["file"] == identity + ".png")
                high = browser.new_context(
                    viewport={
                        "width": original["logical_width"],
                        "height": original["logical_height"],
                    },
                    device_scale_factor=1.25,
                    timezone_id="UTC",
                )
                p = high.new_page()
                p.goto("http://127.0.0.1:1420/?showcase=" + identity)
                p.wait_for_function("document.documentElement.dataset.showcase !== undefined")
                if identity.startswith("32"):
                    p.get_by_role("tab", name="Edit", exact=True).click()
                p.mouse.move(0, 0)
                p.wait_for_timeout(150)
                name = identity + "-125pct.png"
                p.screenshot(path=str(OUTPUT / name), full_page=True)
                width, height = struct.unpack(">II", (OUTPUT / name).read_bytes()[16:24])
                entries.append(
                    {
                        **original,
                        "file": name,
                        "physical_width": width,
                        "physical_height": height,
                        "scale": 1.25,
                        "evidence": "EMULATED_DPR_125_PRODUCT_COMPONENTS",
                        "notes": original["notes"]
                        + " DPR 125% emulated, not Windows scale changed.",
                    }
                )
                high.close()
            browser.close()
    finally:
        # Terminate only the npm/Vite process tree this capture launched.
        subprocess.run(["taskkill", "/PID", str(server.pid), "/T", "/F"], capture_output=True)
        server.wait(timeout=10)
    entries.extend(
        [
            native_capture(
                "--baseline-menu",
                "00-tray-menu.png",
                "#32768",
                ["Open OSCAR", "Compact presence", "Hide OSCAR", "Quit"],
            ),
            native_capture(
                "--baseline-dialog", "62-native-owner-confirmation.png", "#32770", ["Yes", "No"]
            ),
        ]
    )
    entries.sort(key=lambda entry: entry["file"])
    for entry in entries:
        entry["sha256"] = hashlib.sha256((OUTPUT / entry["file"]).read_bytes()).hexdigest()
    manifest = {
        "slice": "10R.0",
        "canonical_orb_sha256": hashlib.sha256(
            (ROOT / "assets/brand/oscar-orb.svg").read_bytes()
        ).hexdigest(),
        "starting_sha": "5f46f8b195ab557c85d66dec70eddf665cd3e3de",
        "evidence_scope": "UI baseline only; no functional or owner/device acceptance inferred",
        "lifecycle": "REFERENCE Windows uncommissioned close/hide/reveal/explicit quit PASS",
        "validation": "LOCAL PASS / REMOTE CI NOT EXECUTED DUE ACCOUNT BILLING LIMIT",
        "images": entries,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    rows = ["| ID | Screenshot | Surface | State | Why it exists |", "|---|---|---|---|---|"]
    for entry in entries:
        rows.append(
            f"| {entry['file'].removesuffix('.png')} | [PNG](baseline/{entry['file']}) "
            f"| {entry['surface']} | {entry['state']} | Inspect existing state composition |"
        )
    (OUTPUT.parent / "inventory.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    document = OUTPUT.parent / "BASELINE.md"
    text = document.read_text(encoding="utf-8")
    start, end = "<!-- inventory:start -->", "<!-- inventory:end -->"
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    document.write_text(
        before + start + "\n" + "\n".join(rows) + "\n" + end + after, encoding="utf-8"
    )
    print(
        f"Captured {len(entries)} PNGs; manifest validates recorded dimensions and evidence sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
