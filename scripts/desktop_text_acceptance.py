"""Native text-tool interaction checks; UIA/signing is independently exercised by desktop_tauri."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_native_fixture import native_fixture

OUT = Path(__file__).resolve().parents[1] / "docs/ui/desktop/completion/evidence"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    checks, lines, info, completed, failure_type = [], [], {}, False, None
    try:
        with native_fixture() as (info, lines, command), sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            page = next(p for c in browser.contexts for p in c.pages if "?living" in p.url)
            page.locator(".presence-caption").get_by_text("Here", exact=True).wait_for(
                timeout=20000
            )

            def check(name, condition):
                assert condition, name
                checks.append(name)
                print("PASS", name, flush=True)

            def shot(name):
                page.wait_for_timeout(350)
                page.screenshot(path=str(OUT / f"12-3-{name}.png"), omit_background=True)

            page.locator(".character-button").click()
            page.locator("#presence-ask").fill("unfinished Ask draft")
            page.get_by_role("button", name="Text tools", exact=True).click()
            page.get_by_label("Dictation draft", exact=True).fill("spoken reference")
            check(
                "tools open without microphone activity",
                page.get_by_text(
                    "Dictation capture starts only on your request.", exact=True
                ).count()
                == 1,
            )
            page.get_by_role("tab", name="Edit", exact=True).click()
            page.get_by_label("Transformation instruction", exact=True).fill("shorten reference")
            check(
                "Edit without a fresh target is disabled",
                not page.get_by_role(
                    "button", name="Request transformation", exact=True
                ).is_enabled(),
            )
            page.get_by_role("tab", name="Dictate", exact=True).click()
            check(
                "mode drafts remain separate",
                page.get_by_label("Dictation draft", exact=True).input_value()
                == "spoken reference",
            )
            page.keyboard.press("Escape")
            page.wait_for_timeout(250)
            page.locator(".character-button").click()
            page.get_by_label("Dictation draft", exact=True).wait_for()
            check(
                "tool draft survives native retreat/reinvoke",
                page.get_by_label("Dictation draft", exact=True).input_value()
                == "spoken reference",
            )
            page.get_by_role("button", name="Start dictation", exact=True).click()
            page.get_by_role("alert").filter(has_text="Voice adapter unavailable").wait_for()
            check(
                "absent voice adapter never implies listening",
                not page.get_by_text("Listening — explicit capture active.", exact=True).count(),
            )
            shot("unavailable-microphone")
            page.get_by_role("button", name="Preview text", exact=True).click()
            page.get_by_role("region", name="Review text preview", exact=True).wait_for()
            check(
                "typed dictation produces a real Core preview",
                page.get_by_role("region", name="Review text preview", exact=True)
                .locator("pre")
                .last.inner_text()
                == "spoken reference",
            )
            shot("preview")
            page.get_by_role("button", name="Apply reviewed text", exact=True).click()
            page.get_by_text(
                "VERIFIED · OSCAR surface only: spoken reference", exact=True
            ).wait_for()
            check(
                "surface receipt grants no external write",
                not page.get_by_role("region", name="Review text preview", exact=True).count(),
            )
            shot("surface-result")
            page.get_by_role("button", name="Preview text", exact=True).click()
            page.get_by_role("region", name="Review text preview", exact=True).wait_for()
            page.wait_for_timeout(15300)
            check(
                "expiry disables mutation in the actual WebView",
                not page.get_by_role("button", name="Apply reviewed text", exact=True).is_enabled(),
            )
            shot("expired-preview")
            page.locator(".context-details .oscar-disclosure-trigger").click()
            page.get_by_role(
                "button", name="Discard private drafts and context", exact=True
            ).click()
            check(
                "discard clears dictation draft",
                page.get_by_label("Dictation draft", exact=True).input_value() == "",
            )
            page.get_by_role("tab", name="Edit", exact=True).click()
            check(
                "discard clears edit instruction",
                page.get_by_label("Transformation instruction", exact=True).input_value() == "",
            )
            page.get_by_role("button", name="Ask", exact=True).click()
            check(
                "discard clears Ask draft across surfaces",
                page.locator("#presence-ask").input_value() == "",
            )
            command("status")
            page.wait_for_timeout(100)
            check(
                "preview/surface delivery created no task or action",
                any('"tasks": [], "actions": 0' in line for line in lines),
            )
            completed = True
    except BaseException as error:
        failure_type = type(error).__name__
        raise
    finally:
        (OUT / "12-3-native-receipt.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "completed": completed,
                    "failure_type": failure_type,
                    "classification": "REFERENCE_VERIFIED" if completed else "FAILED",
                    "native": info,
                    "fixture_log": lines,
                    "limits": [
                        "actual native DOM/content/IPC, not OS focus or GUI approval",
                        "no microphone or real STT/model inference",
                        "registered field and CNG checked separately by desktop_tauri --self-check",
                    ],
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
