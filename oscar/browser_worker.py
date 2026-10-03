"""Bounded typed Playwright plans in isolated contexts. No personal browser profile."""

import argparse
import importlib
import json
import os
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlsplit


def origin(url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.username
        or parsed.password
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
    ):
        raise ValueError("credential-free HTTP(S) URL required")
    return f"{parsed.scheme}://{parsed.netloc.lower()}"


def validate(request: dict[str, Any]) -> None:
    if set(request) != {"origins", "steps", "timeout", "max_text"}:
        raise ValueError("invalid browser plan fields")
    if not isinstance(request["origins"], list) or not 1 <= len(request["origins"]) <= 8:
        raise ValueError("bounded explicit origins required")
    if any(origin(url) != url for url in request["origins"]):
        raise ValueError("exact origins required")
    if type(request["timeout"]) not in {int, float} or not 0 < request["timeout"] <= 120:
        raise ValueError("bounded browser timeout required")
    if type(request["max_text"]) is not int or not 1 <= request["max_text"] <= 16_000:
        raise ValueError("bounded DOM text required")
    steps = request["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise ValueError("bounded browser steps required")
    fields = {
        "navigate": {"url"},
        "fill": {"selector", "text"},
        "click": {"selector"},
        "submit": {"selector"},
        "wait": {"selector"},
        "inspect": set(),
        "screenshot": {"path"},
        "download": {"selector", "path", "max_bytes"},
    }
    for step in steps:
        operation = step.get("operation")
        if operation not in fields or set(step) != fields[operation] | {"operation"}:
            raise ValueError("unsupported browser operation")
        if operation == "navigate" and origin(step["url"]) not in request["origins"]:
            raise PermissionError("navigation origin outside grant")
        if "selector" in step and (
            not isinstance(step["selector"], str) or not 0 < len(step["selector"]) <= 500
        ):
            raise ValueError("bounded selector required")
        if "text" in step and (not isinstance(step["text"], str) or len(step["text"]) > 8192):
            raise ValueError("bounded form text required")
        if "path" in step and (
            not isinstance(step["path"], str)
            or Path(step["path"]).name != step["path"]
            or step["path"] in {"", ".", ".."}
            or ":" in step["path"]
        ):
            raise ValueError("artifact must be a new workspace basename")
        if operation == "download" and (
            type(step["max_bytes"]) is not int or not 1 <= step["max_bytes"] <= 1_000_000
        ):
            raise ValueError("bounded download required")


def run(request: dict[str, Any], root: Path) -> dict[str, Any]:
    validate(request)
    sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright

    started = monotonic()
    env = {
        key: os.environ[key]
        for key in ("SystemRoot", "TEMP", "TMP", "PATH", "HOME")
        if key in os.environ
    }
    observations = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, env=env)
        context = browser.new_context(
            accept_downloads=any(s["operation"] == "download" for s in request["steps"])
        )
        # Recheck redirects, subresources and navigation at the network boundary.
        context.route(
            "**/*",
            lambda route: route.continue_()
            if origin(route.request.url) in request["origins"]
            else route.abort(),
        )
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.dismiss())
        page.on("popup", lambda popup: popup.close())
        try:
            for step in request["steps"]:
                remaining = request["timeout"] - (monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("browser plan deadline")
                page.set_default_timeout(min(remaining, 10) * 1000)
                page.set_default_navigation_timeout(min(remaining, 15) * 1000)
                operation = step["operation"]
                if operation == "navigate":
                    page.goto(step["url"], wait_until="domcontentloaded")
                elif operation == "fill":
                    page.locator(step["selector"]).fill(step["text"])
                elif operation in {"click", "submit"}:
                    page.locator(step["selector"]).click()
                elif operation == "wait":
                    page.locator(step["selector"]).wait_for(state="visible")
                elif operation == "inspect":
                    # Fixed bounded evaluation avoids retrieving an entire unbounded DOM first.
                    snapshot = page.evaluate(
                        """limit => {
                        const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
                        let text='',n,count=0;
                        while((n=walker.nextNode()) && count++<2000 && text.length<limit)
                            text+=(n.textContent||'').slice(0,limit-text.length)+' ';
                        return text.slice(0,limit);
                    }""",
                        request["max_text"],
                    )
                    observations.append(
                        {
                            "url": page.url,
                            "title": page.title()[:1000],
                            "text": snapshot,
                            "status": "REPORTED",
                        }
                    )
                elif operation == "screenshot":
                    artifact = root / step["path"]
                    if artifact.exists():
                        raise ValueError("artifact overwrite rejected")
                    page.screenshot(path=str(artifact), full_page=False)
                elif operation == "download":
                    artifact = root / step["path"]
                    if artifact.exists():
                        raise ValueError("artifact overwrite rejected")
                    with page.expect_download() as download_info:
                        page.locator(step["selector"]).click()
                    download = download_info.value
                    path = download.path()
                    if path is None or path.stat().st_size > step["max_bytes"]:
                        download.cancel()
                        raise ValueError("download bound exceeded")
                    download.save_as(str(artifact))
            return {"observations": observations, "isolated": True, "status": "REPORTED"}
        finally:
            context.close()
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    print(json.dumps(run(json.loads(args.request), Path.cwd())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
