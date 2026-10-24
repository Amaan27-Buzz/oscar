"""Bounded typed Playwright plans in isolated contexts. No personal browser profile."""

import argparse
import base64
import hashlib
import importlib
import json
import os
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from oscar.capabilities import ScopedFiles
from oscar.windows_files import WindowsScopedFiles

_posix_os: Any = os


def write_artifact(artifact: Path, data: bytes) -> None:
    """Pin the directory and create a new regular file; never follow an existing leaf."""
    if len(WindowsScopedFiles.parts(artifact.name)) != 1:
        raise ValueError("artifact basename required")
    if len(data) > 4_000_000:
        raise ValueError("artifact bound exceeded")
    if os.name == "nt":
        files = WindowsScopedFiles(artifact.parent)
        files.create_bytes(artifact.name, data)
    else:
        files_posix = ScopedFiles(artifact.parent)
        with files_posix.directory(".") as directory:
            descriptor = os.open(
                artifact.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | _posix_os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)


class NoDownloadRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError("download redirects require a new explicit plan")


def bounded_download(
    url: str,
    artifact: Path,
    allowed: list[str],
    maximum: int,
    timeout: float,
    *,
    page: Any = None,
) -> None:
    """Bounded HTTP anchor bytes; same-origin credentials stay inside the browser."""
    if type(maximum) is not int or not 1 <= maximum <= 1_000_000:
        raise ValueError("bounded download required")
    if type(timeout) not in {int, float} or not 0 < timeout <= 120:
        raise ValueError("bounded download timeout required")
    WindowsScopedFiles.parts(artifact.name)
    if origin(url) not in allowed:
        raise PermissionError("download origin outside grant")
    if artifact.exists():
        raise FileExistsError("artifact overwrite rejected")
    if page is not None and origin(url) == origin(page.url):
        encoded = page.evaluate(
            """async ({url, maximum, timeout}) => {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), timeout);
                try {
                    const response = await fetch(url, {
                        credentials: 'same-origin', redirect: 'error', cache: 'no-store',
                        referrerPolicy: 'no-referrer', signal: controller.signal
                    });
                    if (!response.ok || !response.body) throw new Error('download rejected');
                    const reader = response.body.getReader();
                    const chunks = [];
                    let total = 0;
                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;
                        total += value.byteLength;
                        if (total > maximum) throw new Error('download bound exceeded');
                        chunks.push(value);
                    }
                    let binary = '';
                    for (const chunk of chunks)
                        for (let i = 0; i < chunk.length; i += 32768)
                            binary += String.fromCharCode(...chunk.subarray(i, i + 32768));
                    return btoa(binary);
                } finally {
                    controller.abort();
                    clearTimeout(timer);
                }
            }""",
            {"url": url, "maximum": maximum, "timeout": min(timeout, 15) * 1000},
        )
        if not isinstance(encoded, str) or len(encoded) > 4 * ((maximum + 2) // 3):
            raise ValueError("download bound exceeded")
        data = base64.b64decode(encoded, validate=True)
    else:
        # Other granted origins stay anonymous; browser credentials are never exported.
        with build_opener(NoDownloadRedirects()).open(
            Request(url), timeout=min(timeout, 15)
        ) as response:
            data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("download bound exceeded")
    # Exclusive creation rejects preexisting files, including links/reparse targets.
    write_artifact(artifact, data)


def origin(url: str) -> str:
    if not isinstance(url, str) or len(url) > 8000:
        raise ValueError("bounded HTTP(S) URL required")
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
        "visual_click": {"url", "sha256", "width", "height", "x", "y"},
        "download": {"selector", "path", "max_bytes"},
        "select": {"selector", "value"},
        "scroll": {"selector"},
        "accessibility": {"selector"},
        "upload": {"selector", "path"},
        "new_tab": set(),
        "switch_tab": {"index"},
        "close_tab": set(),
    }
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("structured browser step required")
        operation = step.get("operation")
        if operation not in fields or set(step) != fields[operation] | {"operation"}:
            raise ValueError("unsupported browser operation")
        if operation == "navigate" and origin(step["url"]) not in request["origins"]:
            raise PermissionError("navigation origin outside grant")
        if operation == "visual_click":
            if origin(step["url"]) not in request["origins"]:
                raise PermissionError("visual target origin outside grant")
            if (
                not isinstance(step["sha256"], str)
                or len(step["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in step["sha256"])
                or any(type(step[k]) is not int for k in ("width", "height", "x", "y"))
                or not 64 <= step["width"] <= 4096
                or not 64 <= step["height"] <= 4096
                or not 0 <= step["x"] < step["width"]
                or not 0 <= step["y"] < step["height"]
            ):
                raise ValueError("exact screenshot hash, viewport and pixel target required")
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
        if "path" in step:
            WindowsScopedFiles.parts(step["path"])
        if operation == "download" and (
            type(step["max_bytes"]) is not int or not 1 <= step["max_bytes"] <= 1_000_000
        ):
            raise ValueError("bounded download required")
        if operation == "select" and (
            not isinstance(step["value"], str) or len(step["value"]) > 1000
        ):
            raise ValueError("bounded option value required")
        if operation == "switch_tab" and (
            type(step["index"]) is not int or not 0 <= step["index"] < 8
        ):
            raise ValueError("bounded tab index required")


class BrowserFailure(RuntimeError):
    def __init__(self, category: str, error_type: str):
        self.category = category
        self.error_type = error_type
        super().__init__(category)


def playwright_runtime() -> Any:
    try:
        return importlib.import_module("playwright.sync_api").sync_playwright
    except ImportError as error:
        raise BrowserFailure("browser.playwright_unavailable", type(error).__name__) from error


def probe() -> None:
    with playwright_runtime()() as playwright:
        if not Path(playwright.chromium.executable_path).is_file():
            raise BrowserFailure("browser.chromium_unavailable", "FileNotFoundError")
        try:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
        except Exception as error:
            raise BrowserFailure("browser.playwright_launch", type(error).__name__) from error


def visual_snapshot(page: Any) -> tuple[bytes, dict[str, Any]]:
    """CSS-pixel coordinates and the hash use the same fixed screenshot contract."""
    viewport = page.viewport_size
    if viewport is None:
        raise PermissionError("fixed browser viewport required")
    data = page.screenshot(full_page=False, animations="disabled", caret="hide", scale="css")
    return data, {"url": page.url, "sha256": hashlib.sha256(data).hexdigest(), **viewport}


def run(request: dict[str, Any], root: Path, *, profile: Path | None = None) -> dict[str, Any]:
    validate(request)
    sync_playwright = playwright_runtime()

    started = monotonic()
    env = {
        key: os.environ[key]
        for key in ("SystemRoot", "TEMP", "TMP", "PATH", "HOME")
        if key in os.environ
    }
    observations = []
    with sync_playwright() as playwright:
        browser = None
        try:
            if profile is not None:
                context = playwright.chromium.launch_persistent_context(
                    str(profile),
                    headless=True,
                    env=env,
                    accept_downloads=False,
                    service_workers="block",
                )
            else:
                browser = playwright.chromium.launch(headless=True, env=env)
                context = browser.new_context(accept_downloads=False, service_workers="block")
        except Exception as error:
            if browser:
                browser.close()
            raise BrowserFailure("browser.playwright_launch", type(error).__name__) from error

        # Recheck redirects, subresources and navigation at the network boundary.
        def authorize_route(route: Any) -> None:
            try:
                permitted = origin(route.request.url) in request["origins"]
            except ValueError:
                permitted = False
            route.continue_() if permitted else route.abort()

        context.route("**/*", authorize_route)

        def configure_page(target: Any) -> None:
            target.on("dialog", lambda dialog: dialog.dismiss())
            target.on("popup", lambda popup: popup.close())

        for restored in context.pages:
            restored.close()
        page = context.new_page()
        configure_page(page)
        tabs = [page]
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
                elif operation == "select":
                    page.locator(step["selector"]).select_option(step["value"])
                elif operation == "scroll":
                    page.locator(step["selector"]).scroll_into_view_if_needed()
                elif operation == "accessibility":
                    observations.append(
                        {
                            "url": page.url,
                            "accessibility": page.locator(step["selector"]).aria_snapshot()[
                                : request["max_text"]
                            ],
                            "status": "REPORTED",
                        }
                    )
                elif operation == "new_tab":
                    if len(tabs) >= 8:
                        raise ValueError("browser tab bound exceeded")
                    page = context.new_page()
                    configure_page(page)
                    tabs.append(page)
                elif operation == "switch_tab":
                    page = tabs[step["index"]]
                elif operation == "close_tab":
                    if len(tabs) == 1:
                        raise ValueError("cannot close final tab within a plan")
                    tabs.remove(page)
                    page.close()
                    page = tabs[-1]
                elif operation == "upload":
                    data = ScopedFiles(root).read(step["path"])
                    if len(data) > 1_000_000:
                        raise ValueError("upload bound exceeded")
                    page.locator(step["selector"]).set_input_files(
                        {
                            "name": step["path"],
                            "mimeType": "application/octet-stream",
                            "buffer": data,
                        }
                    )
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
                    data, binding = visual_snapshot(page)
                    write_artifact(artifact, data)
                    observations.append({**binding, "path": step["path"], "status": "REPORTED"})
                elif operation == "visual_click":
                    if page.url != step["url"]:
                        raise PermissionError("visual target URL changed")
                    _, binding = visual_snapshot(page)
                    if binding != {k: step[k] for k in ("url", "sha256", "width", "height")}:
                        raise PermissionError("visual target pixels or viewport changed")
                    if page.url != step["url"] or monotonic() - started >= request["timeout"]:
                        raise PermissionError("visual target expired or navigated")
                    # One attempt only; a matching frame does not prove the click's outcome.
                    page.mouse.click(step["x"], step["y"])
                elif operation == "download":
                    artifact = root / step["path"]
                    if artifact.exists():
                        raise ValueError("artifact overwrite rejected")
                    url = page.locator(step["selector"]).evaluate("e => e.href || ''")
                    bounded_download(
                        url, artifact, request["origins"], step["max_bytes"], remaining, page=page
                    )
            return {"observations": observations, "isolated": True, "status": "REPORTED"}
        finally:
            context.close()
            if browser:
                browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--request")
    mode.add_argument("--probe", action="store_true")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()
    try:
        if args.probe:
            probe()
            print(json.dumps({"category": "browser.ready"}))
        else:
            print(json.dumps(run(json.loads(args.request), Path.cwd(), profile=args.profile)))
        return 0
    except BrowserFailure as error:
        print(json.dumps({"category": error.category, "error_type": error.error_type}))
    except Exception as error:
        # Exception messages can contain selectors, URLs, DOM, cookies or tokens.
        print(
            json.dumps(
                {
                    "category": "browser.playwright_launch"
                    if args.probe
                    else "browser.plan_execution",
                    "error_type": type(error).__name__,
                }
            )
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
