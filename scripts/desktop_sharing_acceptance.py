"""Check the rebuilt native sharing form with disposable Core credentials.

Run with --output pointing to a new evidence directory. No Worker is activated.
"""

import argparse
import hashlib
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_baseline import capture_owned, windows
from scripts.desktop_native_fixture import ROOT, native_fixture


def source_hashes():
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for folder in ("oscar", "desktop/src", "desktop/src-tauri/src")
        for path in (ROOT / folder).rglob("*")
        if path.is_file() and path.suffix in (".py", ".tsx", ".ts", ".css", ".rs")
    } | {
        "scripts/desktop_sharing_acceptance.py": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    binary = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    report = {
        "qualification": (
            "Actual Tauri/WebView2 against disposable authenticated Core; synthetic paths, "
            "no Worker activation, owner approval or assistive-technology acceptance. "
            "Window capture freshness requires comparison with the WebView image."
        ),
        "sources": before,
        "binary_sha256": binary_hash,
        "checks": [],
        "state": "FAILED",
    }
    started = time.monotonic()

    def check(name, condition):
        assert condition, name
        report["checks"].append(name)
        print("PASS", name, flush=True)

    try:
        with native_fixture(workspace=True) as (info, _, _), sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
            pages = [page for context in browser.contexts for page in context.pages]
            companion = next(page for page in pages if "?companion" in page.url)
            page = next(page for page in pages if "?companion" not in page.url)
            companion.get_by_text("Disconnected", exact=True).wait_for(
                state="hidden", timeout=20000
            )
            companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
            page.get_by_role("navigation", name="Workspace").get_by_role(
                "button", name="Preferences", exact=True
            ).click()
            page.get_by_role("heading", name="Use this Desktop", exact=True).wait_for()
            page.get_by_role("button", name="Set up Desktop sharing", exact=True).click()
            field = page.get_by_label("Installed Python executable", exact=True)
            field.fill(r"C:\Synthetic\python.exe")
            field.focus()
            check(
                "Labeled Python input receives focus",
                field.evaluate("el=>el===document.activeElement"),
            )
            page.get_by_label("Shared workspace folder", exact=True).fill(r"C:\Synthetic\workspace")
            host = page.get_by_label(
                "Allow execution with this Windows account's permissions", exact=True
            )
            terminal = page.get_by_label("Allowlisted commands", exact=True)
            check("Host selection requires explicit opt-in", terminal.is_disabled())
            host.check()
            check("Form opt-in enables selection", terminal.is_enabled())
            terminal.check()
            executable = page.get_by_label("Allowed executable paths, one per line", exact=True)
            executable.fill(r"C:\Synthetic\python.exe")
            check(
                "Allowlist cannot resize",
                executable.evaluate("el=>getComputedStyle(el).resize==='none'"),
            )
            host.uncheck()
            check(
                "Withdrawal clears and disables selection",
                terminal.is_disabled() and not terminal.is_checked(),
            )
            check(
                "Unenrolled workspace prevents start",
                page.get_by_role(
                    "button", name="Review and start sharing", exact=True
                ).is_disabled(),
            )
            check(
                "No horizontal overflow",
                page.evaluate("document.documentElement.scrollWidth<=innerWidth"),
            )
            page.locator(".desktop-sharing").scroll_into_view_if_needed()
            page.screenshot(path=str(output / "webview-sharing.png"))
            check(
                "Captured WebView retains withdrawal",
                not host.is_checked() and executable.count() == 0,
            )
            hwnd = next(h for h, _, title in windows(info["pid"]) if title == "OSCAR Workspace")
            report["capture"] = capture_owned(info["pid"], hwnd, output / "window-sharing.png")
        check("Sources unchanged during acceptance", before == source_hashes())
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
