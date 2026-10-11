"""Actual native typed action → temporary file → Core independent verification."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_native_fixture import native_fixture

OUT = Path(__file__).resolve().parents[1] / "docs/ui/desktop/completion/evidence"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    checks, info, lines, complete, failure_type = [], {}, [], False, None
    try:
        with native_fixture() as (info, lines, command), sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            page = next(p for c in browser.contexts for p in c.pages if "?living" in p.url)

            def caption(text):
                page.locator(".presence-caption").get_by_text(text, exact=True).wait_for(
                    timeout=15000
                )

            def check(name, condition):
                assert condition, name
                checks.append(name)
                print("PASS", name, flush=True)

            def shot(name):
                page.wait_for_timeout(350)
                page.screenshot(path=str(OUT / f"12-4-{name}.png"), omit_background=True)

            caption("Here")
            page.locator(".character-button").click()
            page.get_by_role("button", name="Act", exact=True).click()
            page.get_by_label("Relative workspace path", exact=True).wait_for()
            check(
                "empty required path cannot be proposed",
                not page.get_by_role("button", name="Prepare action", exact=True).is_enabled(),
            )
            check(
                "real catalog exposes current required scope",
                page.get_by_text("required scopes: files:write", exact=False).count() == 1,
            )
            page.get_by_label("Relative workspace path", exact=True).fill("group-01-proof.txt")
            page.get_by_label("Exact content", exact=True).fill("exact disposable reference bytes")
            shot("scoped-action")
            page.get_by_role("button", name="Prepare action", exact=True).click()
            caption("Review needed")
            check(
                "proposal displays the exact submitted action",
                page.get_by_text(
                    "Write exact file: group-01-proof.txt · reference-cloud", exact=True
                ).count()
                == 1,
            )
            shot("pending-decision")
            command("execute")
            caption("Working")
            check(
                "working task prohibits a competing proposal",
                not page.get_by_role("button", name="Prepare action", exact=True).is_enabled(),
            )
            command("finish")
            caption("Here")
            page.get_by_text("Verified ·", exact=False).wait_for()
            check(
                "Core independent file readback is verified",
                page.get_by_text("Verified ·", exact=False).count() > 0,
            )
            shot("verified-file")
            page.get_by_role("button", name="Clear private drafts and context", exact=True).click()
            shot("after-clear")
            check(
                "cleared action content is not retained in the form",
                page.get_by_label("Exact content", exact=True).count() == 0
                and page.get_by_label("Available capability", exact=True).input_value() == "",
            )
            command("block")
            page.get_by_role("button", name="Refresh capabilities", exact=True).click()
            page.get_by_text(
                "No eligible action capability is advertised. Nothing will be queued.", exact=True
            ).wait_for()
            check(
                "withdrawn worker never remains an eligible executor",
                not page.get_by_role("button", name="Prepare action", exact=True).count(),
            )
            shot("withdrawn-capability")
            complete = True
    except BaseException as error:
        failure_type = type(error).__name__
        raise
    finally:
        (OUT / "12-4-native-receipt.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "completed": complete,
                    "failure_type": failure_type,
                    "classification": "REFERENCE_VERIFIED" if complete else "FAILED",
                    "native": info,
                    "fixture_log": lines,
                    "limits": [
                        "actual native WebView2/IPC and real temporary file/readback",
                        "programmatic trusted Runtime progression, not owner GUI consent",
                        "no destructive owner-machine operation or provider inference",
                    ],
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
