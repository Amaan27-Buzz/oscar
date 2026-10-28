"""Check native WebView semantics, keyboard navigation and offline draft recovery."""

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from scripts.desktop_native_fixture import ROOT, native_fixture
from scripts.desktop_sharing_acceptance import source_hashes


def hashes():
    return source_hashes() | {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "scripts/desktop_accessibility_acceptance.py",
            "scripts/desktop_native_fixture.py",
            "scripts/desktop_presence_quality.py",
        )
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = hashes()
    binary = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    report = {
        "state": "FAILED",
        "qualification": (
            "Actual disposable Tauri/WebView2 and authenticated synthetic Core. "
            "Accessibility protocol tree and WebView keyboard input; no screen-reader, "
            "Windows text-scale, owner visual, microphone or production activation acceptance."
        ),
        "sources": before,
        "binary_sha256": binary_hash,
        "checks": [],
        "pages": {},
    }
    started = time.monotonic()

    def check(name, condition):
        assert condition, name
        report["checks"].append(name)
        print("PASS", name, flush=True)

    try:
        with native_fixture(workspace=True) as (info, _, command), sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            pages = [page for context in browser.contexts for page in context.pages]
            companion = next(page for page in pages if "?companion" in page.url)
            page = next(page for page in pages if "?companion" not in page.url)
            companion.get_by_text("Disconnected", exact=True).wait_for(
                state="hidden", timeout=20000
            )
            companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
            nav = page.get_by_role("navigation", name="Workspace")
            nav.wait_for()
            session = page.context.new_cdp_session(page)
            session.send("Accessibility.enable")
            names = nav.get_by_role("button").all_text_contents()
            check(
                "All Workspace destinations are present",
                names == ["Conversation", "Automations", "Activity", "Devices", "Preferences"],
            )
            controls = {"button", "textbox", "checkbox", "switch", "combobox", "radio"}
            for name in names:
                button = nav.get_by_role("button", name=name, exact=True)
                button.focus()
                button.press("Enter")
                expect(button).to_have_attribute("aria-current", "page")
                expect(nav.locator('[aria-current="page"]')).to_have_count(1)
                if name == "Preferences":
                    for _ in range(32):
                        closed = page.locator(
                            'button.oscar-disclosure-trigger[aria-expanded="false"]'
                        )
                        if not closed.count():
                            break
                        trigger = closed.first
                        trigger.focus()
                        trigger.press("Space")
                    else:
                        raise AssertionError(
                            "Settings disclosures did not reach a bounded open state"
                        )
                    check("Settings disclosures open with the keyboard", True)
                    choice = page.locator(".oscar-choice-trigger").first
                    selected = choice.get_attribute("data-value")
                    choice.focus()
                    choice.press("ArrowDown")
                    expect(page.get_by_role("radiogroup")).to_be_visible()
                    page.keyboard.press("Escape")
                    expect(page.get_by_role("radiogroup")).to_have_count(0)
                    check(
                        "Choice Escape restores focus without changing selection",
                        choice.evaluate("el => el === document.activeElement")
                        and choice.get_attribute("data-value") == selected,
                    )
                tree = session.send("Accessibility.getFullAXTree")["nodes"]
                active = [n for n in tree if not n.get("ignored")]
                interactive = [n for n in active if n.get("role", {}).get("value") in controls]
                report["pages"][name] = dict(Counter(n["role"]["value"] for n in active))
                report["unnamed_controls"] = [
                    {
                        "page": name,
                        "role": n["role"]["value"],
                        "backend_id": n.get("backendDOMNodeId"),
                    }
                    for n in interactive
                    if not str(n.get("name", {}).get("value", "")).strip()
                ]
                check(
                    name + " exposes names for interactive accessibility nodes",
                    bool(interactive)
                    and all(str(n.get("name", {}).get("value", "")).strip() for n in interactive),
                )
                check(
                    name + " fits the native viewport",
                    page.evaluate("document.documentElement.scrollWidth <= innerWidth"),
                )
                report["pages"][name] = dict(Counter(n["role"]["value"] for n in active))
            nav.get_by_role("button", name="Conversation", exact=True).press("Enter")
            draft = page.get_by_role("textbox", name="Ask OSCAR", exact=True)
            expect(page.get_by_role("button", name="Send", exact=True)).to_be_disabled()
            draft.focus()
            draft.press("Shift+Enter")
            draft.fill("Unsent synthetic draft; never execute this text.")
            draft.press("Tab")
            check(
                "Keyboard reaches enabled Send from the composer",
                page.get_by_role("button", name="Send", exact=True).evaluate(
                    "el => el === document.activeElement"
                ),
            )
            page.get_by_role("button", name="Send", exact=True).press("Shift+Tab")
            check(
                "Keyboard returns to the labeled composer",
                draft.evaluate("el => el === document.activeElement"),
            )
            disconnected = False
            try:
                command("disconnect")
                disconnected = True
                page.get_by_role("button", name="Refresh connection", exact=True).click()
                expect(
                    page.get_by_text("OSCAR is offline. Your work is still here.")
                ).to_be_visible(timeout=20000)
                expect(page.get_by_role("button", name="Send", exact=True)).to_be_disabled()
                expect(draft).to_have_value("Unsent synthetic draft; never execute this text.")
                check("Offline state disables submission and retains the unsent draft", True)
                command("reconnect")
                disconnected = False
                page.get_by_role("button", name="Check connection", exact=True).click()
                expect(page.get_by_role("button", name="Send", exact=True)).to_be_enabled(
                    timeout=20000
                )
                expect(draft).to_have_value("Unsent synthetic draft; never execute this text.")
                check("Reconnect restores submission without consuming the draft", True)
                expect(page.locator(".workspace-notice")).to_have_count(0, timeout=3000)
                check("Successful reconnect clears the read-only connection failure notice", True)
                page.screenshot(path=str(output / "webview-recovered.png"))
            finally:
                if disconnected:
                    command("reconnect")
            session.detach()
        check("Sources unchanged during acceptance", before == hashes())
        check(
            "Native executable unchanged",
            binary_hash == hashlib.sha256(binary.read_bytes()).hexdigest(),
        )
        report["state"] = "PASS"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["seconds"] = round(time.monotonic() - started, 3)
        (output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
