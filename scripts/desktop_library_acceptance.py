"""Native library controls under the unchanged Tauri CSP, with disposable Core state."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_baseline import capture_owned, windows
from scripts.desktop_native_fixture import native_fixture

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/workspace/library-controls-review"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks = []
    with native_fixture(workspace=True) as (info, _lines, _command), sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
        pages = [p for c in browser.contexts for p in c.pages]
        companion = next(p for p in pages if "?companion" in p.url)
        page = next(p for p in pages if "?companion" not in p.url)
        companion.get_by_text("Disconnected", exact=True).wait_for(state="hidden")
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        page.evaluate("""window.policyEvents=[];document.addEventListener(
            'securitypolicyviolation',e=>policyEvents.push(e.violatedDirective))""")
        for theme in ("light", "dark"):
            page.evaluate(
                """theme=>window.__TAURI_INTERNALS__.invoke(
                'surface_command',{request:{kind:'theme',theme}})""",
                theme,
            )
            page.get_by_role("button", name="Act", exact=True).click()
            page.get_by_role("button", name="Clear drafts and context", exact=True).click()
            trigger = page.get_by_label("Available capability", exact=True)
            trigger.click()
            page.get_by_role("radio", name="Write exact file", exact=True).wait_for()
            page.wait_for_timeout(300)
            handle = next(h for h, _, t in windows(info["pid"]) if t == "OSCAR Workspace")
            capture_owned(info["pid"], handle, OUTPUT / f"action-picker-{theme}.png")
            page.keyboard.press("Escape")
            page.wait_for_function("""()=>document.querySelector(
                '[aria-label="Available capability"]')===document.activeElement""")
            trigger.click()
            page.get_by_role("radio", name="Write exact file", exact=True).click()
            page.get_by_role("heading", name="Write exact file", exact=True).wait_for()
            disclosure = page.get_by_role("button", name="Optional context", exact=True)
            if disclosure.get_attribute("aria-expanded") == "true":
                disclosure.click()
            assert disclosure.get_attribute("aria-expanded") == "false"
            disclosure.focus()
            page.keyboard.press("Enter")
            assert disclosure.get_attribute("aria-expanded") == "true"
            page.wait_for_timeout(250)
            capture_owned(info["pid"], handle, OUTPUT / f"disclosure-{theme}.png")
            assert not page.evaluate("policyEvents"), "library must not relax or violate CSP"
            checks.append(f"{theme}: popup, selection, Escape focus return, disclosure and CSP")
        (OUTPUT / "library-receipt.json").write_text(
            json.dumps(
                {
                    "capture": "actual Tauri/WebView2 HWND PrintWindow",
                    "core": "authenticated disposable reference",
                    "checks": checks,
                    "csp_violations": [],
                    "owner_visual_acceptance": "PENDING",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(checks))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
