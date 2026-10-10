"""Actual Tauri/WebView2 reference QA; requires debug exe and owned Vite on port1420.

No Windows input automation, GUI owner approval, real inference or OS DPI acceptance.
"""

import base64
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
out = root / "docs/ui/desktop/presence/quality-recovery/evidence"
out.mkdir(parents=True, exist_ok=True)
fixture = subprocess.Popen(
    [sys.executable, "-m", "scripts.desktop_presence_quality"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
lines = []
ready = threading.Event()
info = {}


def relay():
    for line in fixture.stdout:
        lines.append(line.strip())
        try:
            data = json.loads(line)
            if isinstance(data, dict) and "native_debug_port" in data:
                info.update(data)
                ready.set()
        except ValueError:
            pass


threading.Thread(target=relay, daemon=True).start()
assert ready.wait(20), "Native fixture did not start"
print("NATIVE_SUITE_READY", info["native_debug_port"], flush=True)
checks = []
records = {}
active = [None]
start = [0]


def command(c):
    fixture.stdin.write(c + "\n")
    fixture.stdin.flush()


try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
        page = next(page for ctx in browser.contexts for page in ctx.pages if "?living" in page.url)
        page.locator(".presence-caption").get_by_text("Here", exact=True).wait_for(timeout=120000)
        session = page.context.new_cdp_session(page)

        def frame(e):
            if active[0]:
                name = active[0]
                entries = records[name]
                filename = f"{name}/{len(entries):04d}.png"
                (out / name).mkdir(exist_ok=True)
                (out / filename).write_bytes(base64.b64decode(e["data"]))
                entries.append(
                    {"file": filename, "at_ms": round((time.perf_counter() - start[0]) * 1000)}
                )
            session.send("Page.screencastFrameAck", {"sessionId": e["sessionId"]})

        session.on("Page.screencastFrame", frame)

        def record(name):
            records[name] = []
            active[0] = name
            start[0] = time.perf_counter()
            session.send("Page.startScreencast", {"format": "png", "everyNthFrame": 1})

        def stop():
            session.send("Page.stopScreencast")
            active[0] = None

        def shot(name):
            page.wait_for_timeout(750)
            page.screenshot(path=str(out / (name + ".png")), omit_background=True)

        def check(name, condition):
            assert condition, name
            checks.append(name)
            print("PASS", name, flush=True)

        def caption(text):
            page.locator(".presence-caption").get_by_text(text, exact=True).wait_for(timeout=15000)

        def open_leaf():
            if page.locator(".character-button").get_attribute("aria-expanded") == "false":
                page.locator(".character-button").click()
            page.locator(".writing-leaf").wait_for(state="visible")
            page.wait_for_timeout(300)

        def ask(text):
            if page.get_by_role("button", name="Ask again", exact=True).count():
                page.get_by_role("button", name="Ask again", exact=True).click()
            if page.get_by_role("button", name="Edit request", exact=True).count():
                page.get_by_role("button", name="Edit request", exact=True).click()
            page.locator("#presence-ask").fill(text)
            page.get_by_role("button", name="Ask", exact=True).click()

        page.wait_for_timeout(800)
        shot("after-idle")
        record("native-invoke-retreat")
        open_leaf()
        page.locator("#presence-ask").fill("Unfinished reference draft")
        for i in range(10):
            page.keyboard.press("Escape")
            page.wait_for_timeout(40 if i % 2 == 0 else 240)
            page.locator(".character-button").click()
            page.wait_for_timeout(100)
        page.wait_for_timeout(500)
        stop()
        shot("after-reinvoke")
        check(
            "ten rapid/settled native cycles retain draft",
            page.locator("#presence-ask").input_value() == "Unfinished reference draft",
        )
        check(
            "no obsolete confirmation warning",
            not page.get_by_text(
                "Window confirmation expired. Try opening the presence again."
            ).count(),
        )
        check(
            "native editable DOM focus", page.evaluate("document.activeElement.id==='presence-ask'")
        )
        command("block")
        page.wait_for_timeout(250)
        ask("2 + 3")
        caption("Request blocked")
        shot("after-blocked")
        check(
            "visible exact blocked reason",
            page.get_by_text(
                "Core/Worker capability unavailable or ambiguous; nothing executed", exact=True
            ).count()
            == 1,
        )
        command("status")
        page.wait_for_timeout(100)
        command("restore")
        command("deny")
        page.wait_for_timeout(250)
        ask("2 + 3")
        caption("Permission denied")
        shot("after-denied")
        check(
            "permission denial distinct",
            page.get_by_text(
                "Permission or Personal Policy denied this request; nothing executed", exact=True
            ).count()
            == 1,
        )
        command("allow")
        page.wait_for_timeout(250)
        ask("2 + 3")
        caption("Review needed")
        page.wait_for_timeout(800)
        shot("after-approval")
        check("approval awake", page.locator('svg[aria-label*="attentive delivery"]').count() > 0)
        page.get_by_role("button", name="Leave pending", exact=True).click()
        page.wait_for_timeout(250)
        shot("after-approval-compact")
        open_leaf()
        page.get_by_role("button", name="Review decision", exact=False).click()
        page.get_by_role("heading", name="Owner decision", exact=True).wait_for(timeout=8000)
        section = page.get_by_role("region", name="Owner approval", exact=True)
        assert section.evaluate("(el)=>document.activeElement===el")
        decision = page.get_by_role("heading", name="Owner decision", exact=True).bounding_box()
        assert decision and 0 <= decision["y"] < 200, "Review must enter the first viewport"
        shot("after-exact-review")
        check(
            "opening review does not confirm",
            not any('"state": "verified"' in line for line in lines),
        )
        page.get_by_role("button", name="Back to presence", exact=True).click()
        page.wait_for_timeout(250)
        record("native-weighted-work")
        command("execute")
        caption("Working")
        page.wait_for_timeout(5200)
        shot("after-working")
        command("finish")
        caption("Here")
        page.get_by_text("5", exact=True).wait_for()
        page.wait_for_timeout(800)
        stop()
        shot("after-verified")
        check("actual verified arithmetic", page.get_by_text("VERIFIED", exact=True).count() == 1)
        ask("3 + 4")
        caption("Review needed")
        command("work")
        caption("Waiting")
        shot("after-waiting")
        command("finish")
        caption("Here")
        page.wait_for_timeout(500)
        command("reported")
        ask("reason about a harmless reference")
        caption("Review needed")
        command("execute")
        page.wait_for_timeout(200)
        command("finish")
        caption("Here")
        page.get_by_text(
            "A scripted reference answer; no real model inference.", exact=True
        ).wait_for()
        shot("after-partial")
        check(
            "partial model answer stays reported",
            page.get_by_text("REPORTED", exact=True).count() == 1,
        )
        command("failure")
        ask("reason about a failing reference")
        caption("Review needed")
        command("execute")
        page.wait_for_timeout(200)
        command("finish")
        caption("Task failed")
        shot("after-failure")
        command("disconnect")
        caption("Offline")
        shot("after-offline")
        command("reconnect")
        caption("Task failed")
        shot("after-restored")
        check(
            "genuine failure survives connection restoration",
            page.get_by_text("Something stopped.", exact=True).count() == 1,
        )
        page.locator(".presence-settings summary").click()
        page.get_by_role("button", name="Pin on top", exact=True).click()
        page.get_by_role("button", name="Unpin", exact=True).wait_for()
        check(
            "native pin request acknowledged",
            page.get_by_role("button", name="Unpin", exact=True).count() == 1,
        )
        page.get_by_role("button", name="Unpin", exact=True).click()
        page.get_by_role("button", name="Pin on top", exact=True).wait_for()
        page.get_by_role("button", name="To screen edge", exact=True).click()
        shot("after-edge")
        check(
            "pin float edge bounded native requests",
            page.get_by_role("button", name="Pin on top", exact=True).count() == 1,
        )
        page.emulate_media(reduced_motion="reduce")
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)
        open_leaf()
        shot("native-reduced-motion")
        check(
            "reduced motion usable",
            page.locator(".writing-leaf").get_attribute("aria-hidden") == "false",
        )
        page.emulate_media(forced_colors="active")
        shot("native-forced-colors")
        page.emulate_media(forced_colors="none", reduced_motion="no-preference")
        snapshot = page.evaluate(
            "({width:innerWidth,height:innerHeight,scale:devicePixelRatio,focus:document.activeElement.id,operation:document.querySelector('.living-presence').dataset.operation})"
        )
        session.detach()
finally:
    command("cleanup")
    fixture.wait(15)
    (out / "native-suite.json").write_text(
        json.dumps(
            {
                "checks": checks,
                "native": info,
                "reference_limits": [
                    "programmatic runtime progression is not GUI owner approval",
                    "scripted model is not real inference",
                    "CDP is actual native WebView2; "
                    "OS focus/tray/compositor/DPI coverage not established",
                ],
                "fixture_log": lines,
                "snapshot": locals().get("snapshot"),
                "recordings": records,
            },
            indent=2,
        )
    )
    for name, entries in records.items():
        if not entries:
            continue
        selected = [entries[0]]
        for entry in entries[1:]:
            if entry["at_ms"] - selected[-1]["at_ms"] >= 20:
                selected.append(entry)
        if selected[-1] != entries[-1]:
            selected.append(entries[-1])
        ims = [Image.open(out / e["file"]).convert("RGBA") for e in selected]
        w = max(i.width for i in ims)
        h = max(i.height for i in ims)
        aligned = []
        for im in ims:
            canvas = Image.new("RGBA", (w, h), "#28312f")
            canvas.alpha_composite(im, (w - im.width, h - im.height))
            aligned.append(canvas.convert("RGB"))
        durations = [
            max(10, b["at_ms"] - a["at_ms"]) for a, b in zip(selected, selected[1:], strict=False)
        ] + [500]
        aligned[0].save(
            out / (name + ".gif"),
            save_all=True,
            append_images=aligned[1:],
            duration=durations,
            loop=0,
        )
print("NATIVE_SUITE_COMPLETE", len(checks), flush=True)
