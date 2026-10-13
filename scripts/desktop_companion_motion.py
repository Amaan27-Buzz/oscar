"""Measure and record the bundled native Companion, using an isolated authenticated Core."""

import json
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from scripts.desktop_baseline import capture_owned, windows
from scripts.desktop_native_fixture import native_fixture

OUTPUT = Path(__file__).resolve().parents[1] / "docs/ui/desktop/companion-review"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks = []
    with native_fixture(workspace=True) as (info, _, _), sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
        page = next(p for c in browser.contexts for p in c.pages if "?companion" in p.url)
        page.get_by_text("Disconnected", exact=True).wait_for(state="hidden", timeout=20000)
        hwnd = next(h for h, _, t in windows(info["pid"]) if t == "OSCAR Companion")

        def width():
            return page.locator(".companion-toolbar").evaluate("e=>e.getBoundingClientRect().width")

        def check(name, condition):
            assert condition, name
            checks.append(name)
            print("PASS", name, flush=True)

        page.mouse.move(-5, -5)
        page.evaluate("document.activeElement.blur()")
        page.wait_for_timeout(500)
        resting = width()
        check("resting toolbar is a small handle", abs(resting - 26) < 1)
        orb = page.locator(".companion-orb").bounding_box()
        capture_owned(info["pid"], hwnd, OUTPUT / "companion-rest.png")
        widths = []
        with tempfile.TemporaryDirectory(prefix="oscar-companion-motion-") as temp:
            frames = Path(temp)
            frame = 0

            def record(seconds):
                nonlocal frame
                end = time.monotonic() + seconds
                while time.monotonic() < end:
                    started = time.monotonic()
                    file = frames / f"frame-{frame:04d}.png"
                    capture_owned(info["pid"], hwnd, file)
                    with Image.open(file) as image:
                        canvas = Image.new("RGB", (240, 240), "#20242a")
                        canvas.paste(image, ((240 - image.width) // 2, 10))
                        canvas.save(file)
                    widths.append(width())
                    frame += 1
                    page.wait_for_timeout(max(1, (0.05 - (time.monotonic() - started)) * 1000))

            record(0.5)
            page.mouse.move(74, 60)
            record(1)
            check(
                "hover expands smoothly through intermediate widths",
                any(30 < w < 125 for w in widths),
            )
            check("expanded toolbar is bounded", abs(width() - 128) < 1)
            check("hover never moves the Orb", orb == page.locator(".companion-orb").bounding_box())
            page.mouse.move(25, 134)
            page.wait_for_timeout(200)
            check("moving into controls keeps them expanded", abs(width() - 128) < 1)
            capture_owned(info["pid"], hwnd, OUTPUT / "companion-hover.png")
            page.mouse.move(-5, -5)
            record(1)
            check("pointer leave retracts the toolbar", abs(width() - 26) < 1)
            page.keyboard.press("Tab")
            page.wait_for_timeout(350)
            check("keyboard focus reveals controls", abs(width() - 128) < 1)
            page.evaluate("document.activeElement.blur()")
            page.emulate_media(reduced_motion="reduce")
            page.mouse.move(74, 60)
            page.wait_for_timeout(30)
            check(
                "reduced motion disables toolbar transitions",
                page.locator(".companion-toolbar").evaluate(
                    "e=>getComputedStyle(e).transitionDuration"
                )
                == "0s",
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-framerate",
                    "20",
                    "-i",
                    str(frames / "frame-%04d.png"),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(OUTPUT / "companion-hover.mp4"),
                ],
                check=True,
            )
        (OUTPUT / "motion.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "evidence": "ACTUAL_TAURI_WEBVIEW2",
                    "recording": "owned HWND captures at a target 20 fps; no synthetic animation",
                    "toolbar_width_samples": widths,
                    "owner_visual_acceptance": "NOT_RUN",
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
