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
    parser.add_argument("--process-recovery", action="store_true")
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
    if args.process_recovery:
        command = [
            str(wrapper),
            ":app:assembleDebug",
            ":app:assembleDebugAndroidTest",
            "--console=plain",
        ]
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
    if args.process_recovery:
        args.test_class = (
            "io.dawnlight.oscar.mobile.SettingsIntegrationTest#prepareProcessDeathRecovery"
        )
        command.append("-Pandroid.testInstrumentationRunnerArguments.group02_process_prepare=true")
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
    if not result.returncode and args.process_recovery:

        def device(*parts):
            return subprocess.run(
                ["adb", "-s", serial, "shell", *parts], capture_output=True, text=True, timeout=30
            )

        # Gradle's connected runner removes APK/data afterwards; direct instrumentation
        # keeps this disposable app installed for genuine process replacement.
        for apk in ("app-debug.apk", "../androidTest/debug/app-debug-androidTest.apk"):
            path = root / "mobile/app/build/outputs/apk/debug" / apk
            subprocess.run(
                ["adb", "-s", serial, "install", "-r", str(path.resolve())],
                check=True,
                capture_output=True,
            )
        package = "io.dawnlight.oscar.mobile"
        runner = package + ".test/androidx.test.runner.AndroidJUnitRunner"
        prepared = device(
            "am",
            "instrument",
            "-w",
            "-e",
            "class",
            "io.dawnlight.oscar.mobile.SettingsIntegrationTest#prepareProcessDeathRecovery",
            "-e",
            "group02_process_prepare",
            "true",
            runner,
        )
        assert "OK (1 test)" in prepared.stdout, "Reference process fixture preparation failed"
        activity = package + "/.MainActivity"
        assert device("am", "start", "-W", "-n", activity).returncode == 0
        before_pid = device("pidof", package).stdout.strip()
        assert before_pid
        assert device("am", "force-stop", package).returncode == 0
        assert not device("pidof", package).stdout.strip()
        assert device("am", "start", "-W", "-n", activity).returncode == 0
        after_pid = device("pidof", package).stdout.strip()
        assert after_pid and after_pid != before_pid
        recovered = False
        for _ in range(10):
            device("uiautomator", "dump", "/sdcard/oscar-group02-recovery.xml")
            view = device("cat", "/sdcard/oscar-group02-recovery.xml").stdout
            if "Group02 synthetic process recovery" in view:
                recovered = True
                break
            time.sleep(0.5)
        assert recovered, "Encrypted unsent draft absent after process replacement"
        (output / "process-recovery.json").write_text(
            json.dumps(
                {
                    "classification": "REFERENCE_VERIFIED",
                    "before_pid": before_pid,
                    "after_pid": after_pid,
                    "draft_recovered": True,
                    "automatic_task_replay": False,
                    "method": "force-stop foreground isolated app then explicit relaunch",
                },
                indent=2,
            )
            + "\n"
        )
        clean = device(
            "am",
            "instrument",
            "-w",
            "-e",
            "class",
            "io.dawnlight.oscar.mobile.SettingsIntegrationTest#clearProcessDeathFixture",
            "-e",
            "group02_process_prepare",
            "true",
            runner,
        )
        (output / "process-recovery-cleanup.log").write_text(clean.stdout)
        assert "OK (1 test)" in clean.stdout, "Reference cleanup failed"
        print("REFERENCE actual process replacement and encrypted draft recovery: PASS")
    print("REFERENCE emulator/Core test exit:", result.returncode)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
