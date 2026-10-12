"""Own one disposable native fixture for stage checks; credentials stay in its bootstrap."""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def presence_page(browser):
    """CDP target discovery may precede Playwright's initial frame navigation event."""
    deadline = monotonic() + 15
    session = browser.new_browser_cdp_session()
    while monotonic() < deadline:
        for context in browser.contexts:
            for page in context.pages:
                if "?living" in page.url:
                    return page
        session.send("Target.getTargets")
        sleep(0.1)
    raise RuntimeError("Owned native presence page unavailable to CDP")


@contextmanager
def native_fixture():
    process = subprocess.Popen(
        [sys.executable, "-m", "scripts.desktop_presence_quality"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    info, lines, ready = {}, [], Event()

    def relay():
        for line in process.stdout:
            lines.append(line.strip())
            data = json.loads(line)
            if isinstance(data, dict) and "native_debug_port" in data:
                info.update(data)
                ready.set()

    def command(value):
        process.stdin.write(value + "\n")
        process.stdin.flush()

    Thread(target=relay, daemon=True).start()
    try:
        assert ready.wait(20), "Owned native fixture did not start"
        deadline = monotonic() + 15
        while monotonic() < deadline:
            endpoint = f"http://127.0.0.1:{info['native_debug_port']}/json/list"
            with urlopen(endpoint, timeout=3) as response:
                pages = json.load(response)
            if any("?living" in page.get("url", "") for page in pages):
                break
            sleep(0.1)
        else:
            raise RuntimeError("Owned presence WebView did not finish navigation")
        yield info, lines, command
    finally:
        if process.poll() is None:
            command("cleanup")
            try:
                process.wait(15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(5)
