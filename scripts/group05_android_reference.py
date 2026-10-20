"""Run synthetic native app-control checks on the explicitly named disposable emulator."""

import json
import os
import re
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    serial = "emulator-5582"
    sdk = Path(os.environ["ANDROID_HOME"])
    adb = sdk / "platform-tools/adb.exe"
    output = root / ".oscar/group05"
    output.mkdir(parents=True, exist_ok=True)

    def device(*arguments: str, timeout: int = 30) -> str:
        result = subprocess.run(
            [str(adb), "-s", serial, *arguments],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        return result.stdout

    # Host-side AVD identity first; no discovery or physical-device selection.
    assert device("emu", "avd", "name").splitlines()[0].strip() == "oscar_group05_capability_api35"
    assert device("shell", "getprop", "ro.kernel.qemu").strip() == "1"
    assert device("shell", "getprop", "ro.build.version.sdk").strip() == "35"
    assert device("shell", "getprop", "sys.boot_completed").strip() == "1"
    # Cold disposable AVDs may be asleep/locked; foreground admission must stay enforced.
    device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    device("shell", "wm", "dismiss-keyguard")
    with (output / "android-build.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            [
                str(root / "mobile/gradlew.bat"),
                ":app:testDebugUnitTest",
                ":app:lintDebug",
                ":app:assembleDebug",
                ":app:assembleDebugAndroidTest",
                "--console=plain",
                "--no-daemon",
            ],
            cwd=root / "mobile",
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=900,
        )
    try:
        device(
            "install",
            "-r",
            str(root / "mobile/app/build/outputs/apk/debug/app-debug.apk"),
            timeout=120,
        )
        device(
            "install",
            "-r",
            str(root / "mobile/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"),
            timeout=120,
        )
        result = device(
            "shell",
            "am",
            "instrument",
            "-w",
            "-r",
            "-e",
            "class",
            "io.dawnlight.oscar.mobile.NativeCapabilitiesTest",
            "io.dawnlight.oscar.mobile.test/androidx.test.runner.AndroidJUnitRunner",
            timeout=300,
        )
        (output / "android-instrumentation.log").write_text(result, encoding="utf-8")
        passed = re.search(r"OK \((\d+) tests?\)", result)
        skipped = result.count("INSTRUMENTATION_STATUS_CODE: -3")
        assert passed is not None and int(passed.group(1)) == 7 and skipped == 0, (
            "Inspect Android instrumentation log"
        )
        receipt = {
            "classification": "EMULATED_SYNTHETIC",
            "serial": serial,
            "avd": "oscar_group05_capability_api35",
            "api": 35,
            "passed": 7,
            "failed": 0,
            "skipped": skipped,
            "physical_device": "NOT_RUN",
            "owner_authorization": "NOT_RUN",
            "accessibility_service_enabled": False,
        }
        (output / "android-capabilities.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(receipt))
    finally:
        device("uninstall", "io.dawnlight.oscar.mobile.test")
        device("uninstall", "io.dawnlight.oscar.mobile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
