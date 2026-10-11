"""Native motion/layout reference; raw captures stay in an explicit external archive."""

import argparse
import hashlib
import json
import re
import statistics
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from scripts.desktop_native_fixture import ROOT, native_fixture

OUT = ROOT / "docs/ui/desktop/completion/evidence"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    archive = parser.parse_args().archive.resolve()
    if archive == ROOT or ROOT in archive.parents:
        raise ValueError("raw evidence archive must be outside the repository")
    archive.mkdir(parents=True, exist_ok=True)
    checks, frames, durations, poses = [], [], [], []
    complete, metrics = False, {}
    try:
        with native_fixture() as (info, lines, command), sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            page = next(p for c in browser.contexts for p in c.pages if "?living" in p.url)

            def check(name, condition):
                assert condition, name
                checks.append(name)
                print("PASS", name, flush=True)

            def record(seconds):
                stop = time.monotonic() + seconds
                while time.monotonic() < stop:
                    start = time.monotonic()
                    path = archive / f"frame-{len(frames):04d}.png"
                    page.screenshot(path=str(path), omit_background=False)
                    frames.append(path)
                    poses.append(page.locator('[data-puck="true"]').get_attribute("transform"))
                    page.wait_for_timeout(max(1, 125 - (time.monotonic() - start) * 1000))
                    durations.append(round((time.monotonic() - start) * 1000))

            def shot(name):
                page.screenshot(path=str(OUT / f"12-6-{name}.png"), omit_background=True)

            page.locator(".presence-caption").get_by_text("Here", exact=True).wait_for()
            page.wait_for_timeout(1200)
            page.evaluate("""() => {
                window.__rafOriginal=window.requestAnimationFrame;window.__rafCount=0;
                window.requestAnimationFrame=function(callback){
                    return window.__rafOriginal(t=>{window.__rafCount++;callback(t)})}
                }""")
            session = page.context.new_cdp_session(page)
            session.send("Performance.enable")
            before = {
                m["name"]: m["value"] for m in session.send("Performance.getMetrics")["metrics"]
            }
            page.wait_for_timeout(3200)
            after = {
                m["name"]: m["value"] for m in session.send("Performance.getMetrics")["metrics"]
            }
            metrics = {
                "idle_seconds": 3.2,
                "idle_animation_callbacks": page.evaluate("window.__rafCount"),
                "renderer_task_seconds": after["TaskDuration"] - before["TaskDuration"],
            }
            check(
                "settled idle does not run a continuous animation loop",
                metrics["idle_animation_callbacks"] <= 2,
            )
            page.evaluate("() => {window.requestAnimationFrame=window.__rafOriginal}")
            shot("compact")
            page.locator(".character-button").hover()
            record(0.5)
            page.locator(".character-button").click()
            page.get_by_label("Ask OSCAR", exact=True).fill("unfinished reference draft")
            record(0.75)
            page.keyboard.press("Escape")
            record(0.3)
            page.locator(".character-button").click()
            page.get_by_label("Ask OSCAR", exact=True).wait_for()
            check(
                "retreat and reinvocation preserve draft and input focus",
                page.get_by_label("Ask OSCAR", exact=True).input_value()
                == "unfinished reference draft"
                and page.evaluate("document.activeElement?.id") == "presence-ask",
            )
            check(
                "reinvocation has no obsolete confirmation warning",
                page.get_by_text("The window did not reach", exact=False).count() == 0,
            )
            page.get_by_label("Ask OSCAR", exact=True).fill("2 + 3")
            page.get_by_role("button", name="Ask", exact=True).click()
            page.locator(".presence-caption").get_by_text("Review needed", exact=True).wait_for()
            record(0.75)
            shot("attention")
            command("execute")
            page.locator(".presence-caption").get_by_text("Working", exact=True).wait_for(
                timeout=15000
            )
            record(3)
            xs = [float(re.search(r"translate\(([-\d.]+)", pose)[1]) for pose in poses]
            metrics["whole_sequence_puck_x_travel_svg_units"] = max(xs) - min(xs)
            check(
                "native sequence has readable changing puck poses",
                len(set(poses)) >= 10 and metrics["whole_sequence_puck_x_travel_svg_units"] >= 60,
            )
            shot("working")
            command("finish")
            page.locator(".presence-caption").get_by_text("Here", exact=True).wait_for(
                timeout=15000
            )
            page.get_by_role("button", name="Inspect result", exact=True).click()
            page.get_by_role("heading", name="Verified", exact=True).wait_for()
            check(
                "Activity retains the same responsive character",
                page.locator(".character-button svg").count() == 1,
            )
            check("Activity uses a bounded progressive surface", page.evaluate("innerWidth") <= 620)
            shot("activity")
            page.get_by_role("button", name="Back to presence", exact=True).click()
            page.locator(".presence-settings summary").click()
            page.get_by_role("button", name="Pin on top", exact=True).click()
            page.get_by_role("button", name="Unpin", exact=True).wait_for()
            check(
                "native pin reports applied state",
                page.get_by_role("button", name="Unpin", exact=True).get_attribute("aria-pressed")
                == "true",
            )
            page.get_by_role("button", name="Unpin", exact=True).click()
            page.get_by_role("button", name="To screen edge", exact=True).click()
            page.locator(".presence-settings summary").click()
            page.emulate_media(reduced_motion="reduce")
            page.keyboard.press("Escape")
            page.locator(".character-button[aria-expanded=false]").wait_for()
            page.locator(".character-button").click()
            check(
                "reduced motion removes leaf travel and transitions",
                page.locator(".writing-leaf").evaluate("e=>getComputedStyle(e).transitionDuration")
                == "0s"
                and page.locator(".writing-leaf").evaluate("e=>getComputedStyle(e).transform")
                == "none",
            )
            check(
                "expanded content has no horizontal overflow",
                page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                and page.locator(".writing-leaf").evaluate("e=>e.scrollWidth<=e.clientWidth"),
            )
            shot("reduced-motion")
            command("disconnect")
            page.locator(".presence-caption").get_by_text("Offline", exact=True).wait_for(
                timeout=15000
            )
            record(0.5)
            shot("offline")
            command("reconnect")
            page.get_by_role("button", name="Check connection", exact=False).click()
            page.locator(".presence-caption").get_by_text("Here", exact=True).wait_for(
                timeout=15000
            )
            check(
                "connection restoration preserves actual verified result",
                page.get_by_role("button", name="Inspect result", exact=True).count() == 1,
            )
            images = [Image.open(path).convert("RGB") for path in frames]
            # Different native window sizes are preserved on a common canvas, never scaled.
            width, height = max(i.width for i in images), max(i.height for i in images)
            canvases = []
            for image in images:
                canvas = Image.new("RGB", (width, height), "#e4e5e2")
                canvas.paste(image, (width - image.width, height - image.height))
                canvases.append(canvas)
            canvases[0].save(
                OUT / "12-6-native-motion.gif",
                save_all=True,
                append_images=canvases[1:],
                duration=durations,
                loop=0,
                optimize=True,
            )
            metrics["capture_intervals_ms"] = {
                "median": statistics.median(durations),
                "max": max(durations),
                "frames": len(frames),
            }
            complete = True
    finally:
        manifest = {
            p.name: {
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in frames
        }
        (archive / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (OUT / "12-6-native-receipt.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "completed": complete,
                    "classification": "REFERENCE_VERIFIED" if complete else "FAILED",
                    "metrics": metrics,
                    "raw_archive": str(archive),
                    "limits": [
                        "Actual WebView2 content recording with observed capture timing; "
                        "not compositor or full renderer FPS",
                        "Segments retain capture cadence; waits between segments are cut",
                        "Scripted authenticated Core and trusted disposable task progression",
                        "Reduced-motion preference emulated; "
                        "actual OS accessibility/device/DPI deferred",
                    ],
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
