"""Capture isolated 10R.1 fixtures at proposed window dimensions; no Core or native IPC."""

import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/explorations/10R.1"
URL = "http://127.0.0.1:1420/"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    node = ROOT / ".oscar/toolchains/node-v24.21.0-win-x64"
    if node.is_dir():
        env["PATH"] = str(node) + os.pathsep + env.get("PATH", "")
    npm = shutil.which("npm.cmd", path=env["PATH"])
    assert npm, "Node/npm required"
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 1420))
    server = subprocess.Popen(
        [npm, "run", "dev"], cwd=ROOT / "desktop", env=env, stdout=subprocess.DEVNULL
    )
    entries = []
    checks = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=["--no-proxy-server"])
            context = browser.new_context(device_scale_factor=1, timezone_id="Asia/Kolkata")
            unexpected = []

            def route(request):
                if request.request.url.startswith(URL):
                    request.continue_()
                else:
                    unexpected.append(request.request.url)
                    request.abort()

            context.route("**/*", route)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            deadline = time.monotonic() + 20
            while True:
                try:
                    page.goto(URL + "?presence=a", timeout=3000)
                    page.wait_for_selector(".presence-object", timeout=2000)
                    break
                except Exception:
                    assert server.poll() is None and time.monotonic() < deadline
                    time.sleep(0.1)
            for concept in "abc":
                for scene in ("idle", "active", "offline"):
                    page.goto(URL + f"?presence={concept}&state={scene}")
                    page.wait_for_selector(".presence-object")
                    size = page.locator(".presence-window").evaluate(
                        "e=>[parseFloat(e.style.width),parseFloat(e.style.height)]"
                    )
                    width, height = size
                    page.set_viewport_size({"width": width, "height": height})
                    page.wait_for_function(
                        "Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)"
                    )
                    page.wait_for_timeout(500)
                    assert page.locator(".presence-object").get_attribute("data-state") == scene
                    assert page.evaluate(
                        "document.documentElement.scrollWidth<=innerWidth && "
                        "document.documentElement.scrollHeight<=innerHeight"
                    )
                    # Visible text and controls must remain inside the real viewport and shell.
                    fit = page.locator(".presence-object").evaluate("""shell => {
                      const box=shell.getBoundingClientRect();
                      if(box.bottom>innerHeight||box.right>innerWidth)return false;
                      return [...shell.querySelectorAll('button,p,h1')]
                        .filter(e=>e.checkVisibility()).every(e=>{
                        const r=e.getBoundingClientRect();
                        return r.left>=box.left&&r.right<=box.right+.5&&r.top>=box.top&&
                          r.bottom<=box.bottom+.5&&e.scrollWidth<=e.clientWidth+1;
                      });
                    }""")
                    assert fit, (concept, scene, "clipped content")
                    name = f"concept-{concept}-{scene}.png"
                    page.screenshot(path=str(OUTPUT / name), full_page=False)
                    data = (OUTPUT / name).read_bytes()
                    assert struct.unpack(">II", data[16:24]) == (width, height)
                    assert len(Image.open(OUTPUT / name).getcolors(width * height) or []) > 10
                    entries.append(
                        {
                            "file": name,
                            "concept": concept,
                            "state": scene,
                            "logical_width": width,
                            "logical_height": height,
                            "physical_width": width,
                            "physical_height": height,
                            "scale": 1,
                            "sha256": hashlib.sha256(data).hexdigest(),
                        }
                    )
                # Exercise uninterrupted state changes in the same mounted tree.
                page.set_viewport_size({"width": 700, "height": 1050})
                page.goto(URL + f"?presence={concept}&tools")
                page.wait_for_selector(".presence-object")
                for scene in ("active", "waiting", "offline", "idle"):
                    page.get_by_role("button", name=scene, exact=True).click()
                    page.wait_for_timeout(450)
                    assert page.locator(".presence-object").get_attribute("data-state") == scene
                    if scene in ("waiting", "offline", "idle"):
                        assert (
                            page.locator(".presence-orb").evaluate(
                                "e=>getComputedStyle(e).animationName"
                            )
                            == "none"
                        )
                page.get_by_role("button", name="Open OSCAR interaction").focus()
                page.keyboard.press("Enter")
                page.wait_for_selector(".presence-expanded .expanded")
                page.wait_for_timeout(450)
                assert page.locator(".presence-window").bounding_box()["width"] == 580
                page.keyboard.press("Escape")
                page.wait_for_timeout(450)
                assert page.get_by_role("button", name="Open OSCAR interaction").evaluate(
                    "e=>e===document.activeElement"
                )
                checks.append(
                    f"{concept}: transitions, offline motion, keyboard expansion/Escape/focus PASS"
                )
            # Browser-owned animation preview, including all three concepts and expansion.
            page.set_viewport_size({"width": 700, "height": 1050})
            frames = []
            for concept in "abc":
                page.goto(URL + f"?presence={concept}&tools")
                page.wait_for_selector(".presence-object")
                for scene in ("idle", "active", "waiting", "offline", "idle"):
                    page.get_by_role("button", name=scene, exact=True).click()
                    for _ in range(6):
                        from io import BytesIO

                        frames.append(Image.open(BytesIO(page.screenshot())).convert("RGB"))
                        page.wait_for_timeout(70)
                page.get_by_role("button", name="Open OSCAR interaction").click()
                for _ in range(6):
                    frames.append(Image.open(BytesIO(page.screenshot())).convert("RGB"))
                    page.wait_for_timeout(70)
            frames[0].save(
                OUTPUT / "transitions.gif",
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0,
            )
            # DPI, reduced-motion, forced-colors and long-copy stress on each composition.
            for concept in "abc":
                high = browser.new_context(
                    device_scale_factor=1.25, reduced_motion="reduce", forced_colors="active"
                )
                high.route("**/*", route)
                p = high.new_page()
                entry = next(
                    e for e in entries if e["concept"] == concept and e["state"] == "active"
                )
                p.set_viewport_size(
                    {"width": entry["logical_width"], "height": entry["logical_height"]}
                )
                p.goto(URL + f"?presence={concept}&state=active")
                p.wait_for_selector(".presence-object")
                assert (
                    p.locator(".presence-orb").evaluate("e=>getComputedStyle(e).animationName")
                    == "none"
                )
                p.screenshot(path=str(OUTPUT / f"concept-{concept}-125pct-reduced-forced.png"))
                assert p.evaluate("document.documentElement.scrollWidth<=innerWidth")
                checks.append(f"{concept}: emulated DPR 1.25 / reduced motion / forced colors PASS")
                high.close()
            assert not errors, errors
            assert not unexpected, unexpected
            browser.close()
    finally:
        subprocess.run(["taskkill", "/PID", str(server.pid), "/T", "/F"], capture_output=True)
        server.wait(timeout=10)

    # Contact sheet keeps each captured window at 1:1 pixels; labels live outside captures.
    sheet = Image.new("RGB", (1200, 730), "#e8e3d9")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    for column, (concept, title) in enumerate(
        zip("abc", ("Ambient Presence", "Living Instrument", "Adaptive Presence"), strict=True)
    ):
        x = 28 + column * 400
        draw.text((x, 24), f"{concept.upper()}  /  {title}", fill="#292b29", font=font)
        for row, state in enumerate(("idle", "active", "offline")):
            entry = next(e for e in entries if e["concept"] == concept and e["state"] == state)
            y = 85 + row * 210
            draw.text(
                (x, y - 24),
                f"{state.title()} · {entry['logical_width']} × {entry['logical_height']}",
                fill="#51534e",
                font=small,
            )
            sheet.paste(Image.open(OUTPUT / entry["file"]), (x, y))
    draw.text(
        (28, 707),
        "10R.1 / Chromium renders at 1:1 / Synthetic / No execution / Native acceptance NOT RUN",
        fill="#51534e",
        font=small,
    )
    sheet.save(OUTPUT / "contact-sheet.png")
    manifest = {
        "starting_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "evidence": "SIMULATED_WINDOWS_CHROMIUM_PRESENTATION",
        "native_windows_acceptance": "NOT_RUN",
        "canonical_orb_sha256": hashlib.sha256(
            (ROOT / "assets/brand/oscar-orb.svg").read_bytes()
        ).hexdigest(),
        "images": entries,
        "checks": checks,
        "page_errors": [],
        "external_requests": [],
        "preview": "transitions.gif",
        "preview_notes": "Browser samples, 10fps; not native or a performance benchmark.",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Captured {len(entries)} PNGs, contact sheet, animation preview; browser checks PASS")


if __name__ == "__main__":
    main()
