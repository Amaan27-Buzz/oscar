"""Curated actual Tauri/WebView2 reference checks; no owner dialogs or physical audio."""

import json
import subprocess
import sys
from pathlib import Path
from threading import Event, Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/ui/desktop/completion/evidence"


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    fixture = subprocess.Popen(
        [sys.executable, "-m", "scripts.desktop_presence_quality"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    ready, info, lines, checks = Event(), {}, [], []
    completed, failure_type = False, None

    def relay():
        for line in fixture.stdout:
            lines.append(line.strip())
            data = json.loads(line)
            if isinstance(data, dict) and "native_debug_port" in data:
                info.update(data)
                ready.set()

    Thread(target=relay, daemon=True).start()

    def command(value):
        fixture.stdin.write(value + "\n")
        fixture.stdin.flush()

    try:
        assert ready.wait(20), "Owned native reference did not start"
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            page = next(p for c in browser.contexts for p in c.pages if "?living" in p.url)

            def caption(text):
                page.locator(".presence-caption").get_by_text(text, exact=True).wait_for(
                    timeout=15000
                )

            def shot(name):
                page.wait_for_timeout(350)
                page.screenshot(path=str(EVIDENCE / f"12-2-{name}.png"), omit_background=True)

            def check(name, condition):
                assert condition, name
                checks.append(name)
                print("PASS", name, flush=True)

            caption("Here")
            shot("compact")
            page.locator(".character-button").click()
            page.locator("#presence-ask").fill("An unfinished reference draft")
            page.keyboard.press("Escape")
            page.wait_for_timeout(40)
            page.locator(".character-button").click()
            page.wait_for_timeout(250)
            check(
                "unfinished draft survives reversal",
                page.locator("#presence-ask").input_value() == "An unfinished reference draft",
            )
            check(
                "native editable DOM focus",
                page.evaluate("document.activeElement.id==='presence-ask'"),
            )
            page.locator("#presence-ask").fill("2 + 3")
            page.get_by_role("button", name="Ask", exact=True).click()
            caption("Review needed")
            command("execute")
            caption("Working")
            shot("working")
            command("finish")
            caption("Here")
            page.get_by_text("5", exact=True).wait_for()
            check(
                "real arithmetic verification",
                page.get_by_text("VERIFIED", exact=True).count() == 1,
            )
            shot("verified")
            page.get_by_role("button", name="Ask again", exact=True).click()
            page.locator("#presence-ask").wait_for()
            check(
                "fresh composer after actual result",
                page.locator("#presence-ask").input_value() == "",
            )
            command("long")
            page.locator("#presence-ask").fill("Explain an isolated reference")
            page.get_by_role("button", name="Ask", exact=True).click()
            caption("Review needed")
            command("execute")
            caption("Working")
            command("finish")
            caption("Here")
            page.get_by_role("button", name="Read response", exact=True).wait_for()
            check(
                "bounded compact result",
                len(page.get_by_role("region", name="OSCAR response").inner_text()) == 601,
            )
            shot("bounded-result")
            action = page.get_by_role("button", name="Read response", exact=True).bounding_box()
            footer = page.locator(".leaf-bottom").bounding_box()
            assert action and footer and action["y"] + action["height"] <= footer["y"], (
                "Response actions overlap footer"
            )
            page.get_by_role("button", name="Read response", exact=True).click()
            page.wait_for_timeout(350)
            region = page.get_by_role("region", name="OSCAR response")
            check(
                "actual native reading expansion",
                page.evaluate("innerWidth===540&&innerHeight===680"),
            )
            check(
                "long reader preserves reported text and focus",
                len(region.inner_text()) > 600
                and region.evaluate("el=>document.activeElement===el")
                and page.get_by_text("REPORTED", exact=True).count() == 1,
            )
            shot("expanded-response")
            command("disconnect")
            caption("Offline")
            shot("offline")
            command("reconnect")
            caption("Here")
            page.get_by_role("region", name="OSCAR response").wait_for()
            check(
                "restoration does not upgrade model testimony",
                page.get_by_text("REPORTED", exact=True).count() == 1,
            )
            page.get_by_role("button", name="Ask again", exact=True).click()
            command("block")
            page.locator("#presence-ask").fill("Explain another isolated reference")
            page.get_by_role("button", name="Ask", exact=True).click()
            caption("Request blocked")
            check(
                "unavailable capability stays explicit",
                page.get_by_text("This request didn’t start.", exact=True).count() == 1,
            )
            shot("blocked")
            completed = True
    except BaseException as failure:
        failure_type = type(failure).__name__
        raise
    finally:
        if fixture.poll() is None:
            command("cleanup")
            try:
                fixture.wait(15)
            except subprocess.TimeoutExpired:
                fixture.terminate()
                fixture.wait(5)
        (EVIDENCE / "12-2-native-receipt.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "native": info,
                    "fixture_log": lines,
                    "classification": "REFERENCE_VERIFIED" if completed else "FAILED",
                    "completed": completed,
                    "failure_type": failure_type,
                    "limits": [
                        "actual native WebView2 content/IPC, not OS focus acceptance",
                        "programmatic disposable Runtime progression, not GUI owner approval",
                        "scripted model, not real inference; no microphone",
                    ],
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
