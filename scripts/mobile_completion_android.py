"""Opt-in isolated emulator/Core reference. Never targets a physical owner phone."""

import argparse
import atexit
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--class", dest="test_class")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    serial = "emulator-5582"
    output = root / ".oscar/mobile"
    output.mkdir(parents=True, exist_ok=True)
    ready = subprocess.run(
        ["adb", "-s", serial, "shell", "getprop", "sys.boot_completed"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if ready.returncode or ready.stdout.strip() != "1":
        raise RuntimeError("Start the isolated Group 2 reference emulator first")
    fixture_file = output / "group02-session.json"
    before = fixture_file.stat().st_mtime_ns if fixture_file.exists() else 0
    fixture_log = (output / "android-reference-service.log").open("w")
    service = subprocess.Popen(
        [sys.executable, "-m", "scripts.mobile_completion_reference", "--serve"],
        stdout=fixture_log,
        stderr=subprocess.STDOUT,
    )

    def close():
        if service.poll() is None:
            service.terminate()
            service.wait(timeout=10)
        fixture_log.close()

    atexit.register(close)
    for _ in range(60):
        if fixture_file.exists() and fixture_file.stat().st_mtime_ns != before:
            break
        if service.poll() is not None:
            raise RuntimeError("Reference service failed; inspect local service log")
        time.sleep(0.5)
    else:
        raise RuntimeError("Reference service did not become ready")
    fixture = json.loads(fixture_file.read_text())
    assert fixture["node_id"] == "reference-mobile-software"
    for field in ("url", "control_url"):
        assert fixture[field].startswith("http://127.0.0.1:")
        port = fixture[field].rsplit(":", 1)[1]
        subprocess.run(
            ["adb", "-s", serial, "reverse", "tcp:" + port, "tcp:" + port],
            check=True,
            capture_output=True,
        )
    wrapper = root / "mobile/gradlew.bat"
    command = [str(wrapper), ":app:connectedDebugAndroidTest", "--console=plain"]
    mapping = {
        "group02_origin": "url",
        "group02_session": "session_id",
        "group02_token": "token",
        "group02_control": "control_url",
        "group02_control_token": "control_token",
        "group02_desktop_task": "desktop_task_id",
    }
    for name, field in mapping.items():
        command.append(
            "-Pandroid.testInstrumentationRunnerArguments." + name + "=" + fixture[field]
        )
    if args.test_class:
        command.append("-Pandroid.testInstrumentationRunnerArguments.class=" + args.test_class)
    with (output / "android-reference-gradle.log").open("w") as log:
        result = subprocess.run(
            command,
            cwd=root / "mobile",
            env=dict(os.environ, ANDROID_SERIAL=serial),
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    print("REFERENCE emulator/Core test exit:", result.returncode)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
