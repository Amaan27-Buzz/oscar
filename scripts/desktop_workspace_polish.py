"""Native long-response scrolling and material review against a disposable reference Core."""

import ctypes
import json
from ctypes import wintypes
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_baseline import capture_owned, windows
from scripts.desktop_native_fixture import native_fixture

OUTPUT = Path(__file__).resolve().parents[1] / "docs/ui/desktop/workspace/material-review"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks = []
    with native_fixture(workspace=True) as (info, _, command), sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
        pages = [p for c in browser.contexts for p in c.pages]
        companion = next(p for p in pages if "?companion" in p.url)
        page = next(p for p in pages if "?companion" not in p.url)
        companion.get_by_text("Disconnected", exact=True).wait_for(state="hidden")
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        hwnd = next(h for h, _, t in windows(info["pid"]) if t == "OSCAR Workspace")
        command("long")
        page.get_by_label("Ask OSCAR").fill("Give a long response for the native scrolling check.")
        page.get_by_role("button", name="Send", exact=True).click()
        companion.get_by_text("Review needed", exact=True).wait_for(timeout=15000)
        command("execute")
        page.get_by_text("Running", exact=True).first.wait_for(timeout=15000)
        command("finish")
        page.get_by_role("button", name="Read response", exact=True).click(timeout=15000)
        thread = page.get_by_role("region", name="Conversation scroll area")
        composer = page.locator(".workspace-composer")

        def check(name, condition):
            assert condition, name
            checks.append(name)
            print("PASS", name, flush=True)

        for theme in ("light", "dark"):
            read = page.get_by_role("button", name="Read response", exact=True)
            if read.count():
                read.click()
            page.evaluate(
                """theme=>window.__TAURI_INTERNALS__.invoke('surface_command',{
                    request:{kind:'theme',theme}})""",
                theme,
            )
            page.wait_for_timeout(350)
            check(
                f"{theme}: sidebar has no chat/task list",
                page.locator(".rail-history").count() == 0,
            )
            check(
                f"{theme}: long response needs scrolling",
                thread.evaluate("e=>e.scrollHeight>e.clientHeight"),
            )
            check(
                f"{theme}: scrollbar sits at the Workspace edge",
                thread.evaluate(
                    "e=>Math.abs(e.getBoundingClientRect().right-document.querySelector('.workspace-body').getBoundingClientRect().right)<2"
                ),
            )
            before = composer.bounding_box()
            thread.evaluate("e=>e.scrollTop=e.scrollHeight")
            page.wait_for_timeout(200)
            check(
                f"{theme}: reading scrolls without moving composer",
                thread.evaluate("e=>e.scrollTop>0") and before == composer.bounding_box(),
            )
            check(
                f"{theme}: composer fits and has paired relief shadows",
                composer.evaluate(
                    """e=>e.getBoundingClientRect().bottom<=innerHeight &&
                    (getComputedStyle(e).boxShadow.match(/[(]/g)||[]).length>=2"""
                ),
            )
            capture_owned(info["pid"], hwnd, OUTPUT / f"long-response-{theme}.png")
            for name in ("Text tools", "Act", "Activity", "Devices", "Preferences"):
                page.get_by_role("navigation", name="Workspace").get_by_role(
                    "button", name=name, exact=True
                ).click()
                page.wait_for_timeout(300)
                check(
                    f"{theme}: {name} does not overflow horizontally",
                    page.evaluate("document.documentElement.scrollWidth<=innerWidth"),
                )
                capture_owned(
                    info["pid"], hwnd, OUTPUT / f"{name.lower().replace(' ', '-')}-{theme}.png"
                )
            page.get_by_role("navigation", name="Workspace").get_by_role(
                "button", name="Conversation", exact=True
            ).click()
        user = ctypes.WinDLL("user32")
        user.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user.GetDpiForWindow.argtypes = [wintypes.HWND]
        scale = user.GetDpiForWindow(hwnd) / 96
        assert user.SetWindowPos(hwnd, None, 0, 0, round(860 * scale), round(680 * scale), 0x0006)
        read = page.get_by_role("button", name="Read response", exact=True)
        if read.count():
            read.click()
        page.wait_for_timeout(350)
        check(
            "narrow reading keeps scrollbar at edge",
            thread.evaluate("e=>Math.abs(e.getBoundingClientRect().right-innerWidth)<2"),
        )
        check(
            "narrow composer stays visible",
            composer.evaluate("e=>e.getBoundingClientRect().bottom<=innerHeight"),
        )
        capture_owned(info["pid"], hwnd, OUTPUT / "long-response-narrow.png")
        (OUTPUT / "receipt.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "capture": "ACTUAL_TAURI_WEBVIEW2_OWNED_HWND",
                    "core": "authenticated disposable reference",
                    "response": "SCRIPTED / REPORTED; no actual inference",
                    "owner_visual_acceptance": "PENDING",
                },
                indent=2,
            )
            + "\n"
        )
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
