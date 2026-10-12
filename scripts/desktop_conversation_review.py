"""Render the real Conversation window in both themes using a declared reference Core."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_baseline import capture_owned, windows
from scripts.desktop_native_fixture import native_fixture

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/workspace/conversation-review"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with native_fixture(workspace=True) as (info, lines, command), sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
        pages = [p for c in browser.contexts for p in c.pages]
        companion = next(p for p in pages if "?companion" in p.url)
        page = next(p for p in pages if "?companion" not in p.url)
        companion.get_by_text("Core unavailable", exact=True).wait_for(state="hidden")
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        command("design")
        page.get_by_label("Ask OSCAR").fill("Explain how the Companion and Workspace fit together.")
        page.get_by_role("button", name="Send", exact=True).click()
        companion.get_by_text("Review needed", exact=True).wait_for(timeout=15000)
        command("execute")
        page.get_by_text("Running", exact=True).first.wait_for(timeout=15000)
        command("finish")
        response = page.get_by_role("region", name="OSCAR response")
        response.wait_for(timeout=15000)
        assert response.inner_text().startswith("One OSCAR, two surfaces.")
        assert page.get_by_text("REPORTED", exact=True).count() == 1
        page.get_by_label("Ask OSCAR").fill(
            "Keep the Companion small. Let the Workspace carry the work."
        )
        checks = []
        for theme in ("light", "dark"):
            result = page.evaluate(
                """async theme=>window.__TAURI_INTERNALS__.invoke('surface_command',{
                    request:{kind:'theme',theme}})""",
                theme,
            )
            page.wait_for_function(
                "theme=>document.documentElement.dataset.theme===theme", arg=theme
            )
            page.wait_for_function(
                """theme=>getComputedStyle(document.documentElement)
                    .getPropertyValue('--desk').trim()===(theme==='dark'?'#1c1e1b':'#f5f1e7')""",
                arg=theme,
            )
            page.get_by_role("heading", name="Conversation", exact=True).click()
            page.wait_for_timeout(400)  # PrintWindow needs the WebView and non-client repaint.
            assert result["theme"] == theme
            assert page.get_by_role("button", name="Send").is_visible()
            assert page.locator(".rail-presence .orb").count() == 1
            composer = page.locator(".workspace-composer").bounding_box()
            assert composer and composer["y"] + composer["height"] <= page.evaluate("innerHeight")
            handle = next(h for h, _, title in windows(info["pid"]) if title == "OSCAR Workspace")
            capture_owned(info["pid"], handle, OUTPUT / f"conversation-{theme}.png")
            checks.append(f"{theme}: native theme, exact shared Orb, visible anchored composer")
        (OUTPUT / "receipt.json").write_text(
            json.dumps(
                {
                    "capture": "actual Tauri/WebView2 HWND PrintWindow",
                    "core": "authenticated disposable reference",
                    "model": "SCRIPTED / REPORTED",
                    "checks": checks,
                    "owner_visual_acceptance": "PENDING",
                },
                indent=2,
            )
            + "\n"
        )
        print(json.dumps(checks))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
