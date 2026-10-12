"""Native Activity disclosure and review lifecycle, without approving owner actions."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_native_fixture import native_fixture, presence_page

OUT = Path(__file__).resolve().parents[1] / "docs/ui/desktop/completion/evidence"


def main() -> int:
    checks, complete = [], False
    try:
        with native_fixture() as (info, lines, command), sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            page = presence_page(browser)

            def check(name, condition):
                assert condition, name
                checks.append(name)
                print("PASS", name, flush=True)

            def shot(name):
                page.screenshot(path=str(OUT / f"12-5-{name}.png"), omit_background=True)

            page.locator(".presence-caption").get_by_text("Here", exact=True).wait_for()
            page.locator(".character-button").click()
            page.get_by_label("Ask OSCAR", exact=True).fill("2 + 3")
            page.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_role("button", name="Review decision", exact=False).click()
            page.get_by_role("heading", name="Review approval", exact=True).wait_for()
            check(
                "opening exact review leaves task planned",
                page.get_by_text("planned", exact=True).count() == 1,
            )
            check(
                "native review focuses exact decision",
                page.evaluate("document.activeElement?.getAttribute('aria-label')")
                == "Owner decision",
            )
            check(
                "review material includes exact task input",
                "2" in page.locator(".decision-sheet pre").inner_text(),
            )
            shot("approval")
            page.get_by_role("button", name="Dismiss review", exact=True).click()
            page.get_by_role("button", name="Review approval", exact=True).wait_for()
            check(
                "dismissal leaves pending task and requests no consent",
                page.locator(".decision-sheet").count() == 0,
            )
            page.get_by_role("button", name="Review approval", exact=True).click()
            page.get_by_role("heading", name="Review approval", exact=True).wait_for()
            command("execute")
            page.get_by_role("heading", name="Running", exact=True).wait_for(timeout=15000)
            check(
                "task transition retires obsolete review",
                page.locator(".decision-sheet").count() == 0,
            )
            shot("working")
            command("finish")
            page.get_by_role("heading", name="Verified", exact=True).wait_for(timeout=15000)
            page.get_by_text("Evidence and artifacts", exact=True).click()
            check(
                "verification metadata is inspectable",
                page.locator(".selected-task").get_by_text("VERIFIED", exact=False).count() > 0,
            )
            shot("verified")
            page.get_by_role("button", name="Back to presence", exact=True).click()
            page.get_by_role("button", name="Ask again", exact=True).click()
            page.get_by_label("Ask OSCAR", exact=True).fill("3 + 4")
            page.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_role("button", name="Review decision", exact=False).click()
            page.get_by_role("heading", name="Review approval", exact=True).wait_for()
            page.get_by_role("button", name="Continue to native confirmation", exact=True).wait_for(
                state="visible"
            )
            page.wait_for_timeout(31500)
            check(
                "expired review cannot be confirmed",
                not page.get_by_role(
                    "button", name="Continue to native confirmation", exact=True
                ).count()
                or not page.get_by_role(
                    "button", name="Continue to native confirmation", exact=True
                ).is_enabled(),
            )
            shot("expired")
            command("disconnect")
            page.get_by_text("Current Core state is unavailable.", exact=False).wait_for(
                timeout=15000
            )
            check(
                "offline task history cannot grant approval",
                all(
                    not b.is_enabled()
                    for b in page.get_by_role("button", name="Review approval", exact=True).all()
                ),
            )
            shot("offline")
            command("reconnect")
            page.get_by_role("button", name="Refresh Core", exact=True).click()
            page.get_by_role("button", name="Review approval", exact=True).wait_for(timeout=15000)
            check(
                "reconnect exposes a fresh review path, never auto approves",
                page.locator(".decision-sheet").count() == 0,
            )
            complete = True
    finally:
        (OUT / "12-5-native-receipt.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "completed": complete,
                    "classification": "REFERENCE_VERIFIED" if complete else "FAILED",
                    "limits": [
                        "Actual Tauri/WebView2 and authenticated disposable Core",
                        "Trusted reference task execution; no human/native approval accepted",
                        "OS foreground and owner use deferred",
                    ],
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
