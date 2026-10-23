"""Exercise real Android notice surfaces on one explicitly disposable AVD."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERIAL, AVD = "emulator-5582", "oscar_group05_capability_api35"
PACKAGE = "io.dawnlight.oscar.mobile"


def main() -> None:
    adb = Path(os.environ["ANDROID_HOME"]) / "platform-tools/adb.exe"
    output = ROOT / ".oscar/software-sentry"
    output.mkdir(parents=True, exist_ok=True)
    files = [
        ROOT / "mobile/app/src/main/java/io/dawnlight/oscar/mobile" / name
        for name in (
            "SentryAlerts.kt",
            "TaskNotifications.kt",
            "AwarenessScreen.kt",
            "CoreSession.kt",
            "ManagementState.kt",
        )
    ] + [
        ROOT
        / "mobile/app/src/androidTest/java/io/dawnlight/oscar/mobile/NativeSentryDeliveryTest.kt"
    ]
    apks = [
        ROOT / "mobile/app/build/outputs/apk/debug/app-debug.apk",
        ROOT / "mobile/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
    ]

    def hashes() -> dict[str, str]:
        return {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files + apks
        }

    before = hashes()
    assert max(p.stat().st_mtime for p in files[:-1]) <= apks[0].stat().st_mtime, (
        "Rebuild current app source"
    )
    assert files[-1].stat().st_mtime <= apks[1].stat().st_mtime, (
        "Rebuild current instrumentation source"
    )

    def raw(*args: str, timeout: int = 30) -> str:
        result = subprocess.run(
            [str(adb), "-s", SERIAL, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        return result.stdout

    def guard() -> None:
        assert raw("emu", "avd", "name").splitlines()[0].strip() == AVD
        for name, value in (
            ("ro.kernel.qemu", "1"),
            ("ro.build.version.sdk", "35"),
            ("sys.boot_completed", "1"),
        ):
            assert raw("shell", "getprop", name).strip() == value

    def device(*args: str, timeout: int = 30) -> str:
        guard()
        return raw(*args, timeout=timeout)

    for package in (PACKAGE, PACKAGE + ".test"):
        assert not device("shell", "pm", "list", "packages", package).strip(), (
            "Fresh disposable fixture required"
        )
    installed = []
    try:
        for apk, package in zip(apks, (PACKAGE, PACKAGE + ".test"), strict=True):
            assert "Success" in device("install", "-t", str(apk), timeout=90)
            installed.append(package)
        result = device(
            "shell",
            "am",
            "instrument",
            "-w",
            "-r",
            "-e",
            "class",
            PACKAGE + ".NativeSentryDeliveryTest",
            "-e",
            "sentry_disposable",
            "true",
            PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner",
            timeout=150,
        )
        (output / "instrumentation.log").write_text(result, encoding="utf-8")
        assert (
            "OK (1 test)" in result
            and "FAILURES" not in result
            and "INSTRUMENTATION_FAILED" not in result
        ), result
        assert before == hashes(), "Source or APK changed during native acceptance"
    finally:
        for package in reversed(installed):
            assert "Success" in device("uninstall", package)
            assert not device("shell", "pm", "list", "packages", package).strip()
    receipt = {
        "version": 1,
        "observed_at": datetime.now(UTC).isoformat(),
        "serial": SERIAL,
        "avd": AVD,
        "api": 35,
        "source_apk_sha256": before,
        "status": "passed",
        "tests": 1,
        "fixtures_uninstalled": True,
        "checks": [
            "real Compose attention surface",
            "Android notification permission denied",
            "local alert opt-in denied",
            "real NotificationManager result",
            "generic notification body",
            "persisted native receipt suppresses replay",
            "source act revocation hides UI and cancels posted notification",
        ],
        "limitations": [
            "synthetic Core metadata",
            "no signed remote Core transport in this campaign",
            "no real perception or owner activation",
            "not physical-device acceptance",
        ],
    }
    (output / "native-sentry.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "passed", "tests": 1, "fixtures_uninstalled": True}))


if __name__ == "__main__":
    main()
