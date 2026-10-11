"""Own one disposable native fixture for stage checks; credentials stay in its bootstrap."""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread

ROOT = Path(__file__).resolve().parents[1]


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
        yield info, lines, command
    finally:
        if process.poll() is None:
            command("cleanup")
            try:
                process.wait(15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(5)
