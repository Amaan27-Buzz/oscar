"""Actual system SAF/MediaProjection consent on one explicitly named disposable AVD."""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERIAL = "emulator-5582"
AVD = "oscar_group05_capability_api35"
PACKAGE = "io.dawnlight.oscar.mobile"


def main() -> int:
    adb = Path(os.environ["ANDROID_HOME"]) / "platform-tools/adb.exe"
    output = ROOT / ".oscar/software-android-platform"
    output.mkdir(parents=True, exist_ok=True)

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
        assert raw("shell", "getprop", "ro.kernel.qemu").strip() == "1"
        assert raw("shell", "getprop", "ro.build.version.sdk").strip() == "35"
        assert raw("shell", "getprop", "sys.boot_completed").strip() == "1"

    def device(*args: str, timeout: int = 30) -> str:
        guard()
        return raw(*args, timeout=timeout)

    def inputs() -> dict[str, dict[str, str]]:
        return {
            "source_sha256": {
                path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                for path in (
                    "mobile/app/src/androidTest/java/io/dawnlight/oscar/mobile/NativePlatformConsentTest.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativeCapabilities.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativeActionGate.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativePlatform.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativePlatformSettings.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativeScreenService.kt",
                    "scripts/software_android_platform_reference.py",
                )
            },
            "apk_sha256": {
                path: hashlib.sha256((ROOT / "mobile" / path).read_bytes()).hexdigest()
                for path in (
                    "app/build/outputs/apk/debug/app-debug.apk",
                    "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
                )
            },
        }

    pinned = inputs()
    guard()
    previous_services = device(
        "shell", "settings", "get", "secure", "enabled_accessibility_services"
    ).strip()
    previous_access = device("shell", "settings", "get", "secure", "accessibility_enabled").strip()
    parent = "/sdcard/Documents/oscar-platform-acceptance"
    directory = parent + "/selected"
    outside = parent + "/outside.txt"
    created = False
    receipt = None
    try:
        device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        device("shell", "wm", "dismiss-keyguard")
        for apk in (
            "app/build/outputs/apk/debug/app-debug.apk",
            "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
        ):
            assert "Success" in device(
                "install", "-r", "-t", str(ROOT / "mobile" / apk), timeout=120
            )
        device("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
        device("shell", "mkdir", parent)
        created = True
        device("shell", "mkdir", directory)
        device("shell", "touch", outside)
        component = PACKAGE + "/.AppControlService"
        services = ":".join(
            item
            for item in (previous_services if previous_services != "null" else "", component)
            if item
        )
        device("shell", "settings", "put", "secure", "enabled_accessibility_services", services)
        device("shell", "settings", "put", "secure", "accessibility_enabled", "1")
        methods = (
            "systemFolderSelectionScopesWriteReadAndWithdrawal",
            "systemSingleAppConsentRequiresAuthorityAndStopsOnStopAndLock",
        )
        for method in methods:
            log = device(
                "shell",
                "am",
                "instrument",
                "-w",
                "-r",
                "-e",
                "platform_disposable",
                "true",
                "-e",
                "class",
                PACKAGE + ".NativePlatformConsentTest#" + method,
                PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner",
                timeout=180,
            )
            (output / (method + ".log")).write_text(log, encoding="utf-8")
            assert re.search(r"OK \(1 test\)", log) and not re.search(
                r"FAILURES|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -[34]", log
            ), "Inspect private platform instrumentation log"
        assert inputs() == pinned, "Acceptance source or APK changed during execution"
        receipt = {
            "status": "EMULATED_OS_VERIFIED",
            "serial": SERIAL,
            "avd": AVD,
            "api": 35,
            "checks": list(methods),
            "input_stability": "Source and APK SHA-256 matched before and after execution",
            "authority": (
                "Synthetic exact adapter callback only; "
                "not signed Grid task acceptance or owner activation"
            ),
            **pinned,
        }
    finally:
        device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        device("shell", "wm", "dismiss-keyguard")
        for key, value in (
            ("enabled_accessibility_services", previous_services),
            ("accessibility_enabled", previous_access),
        ):
            if value == "null":
                device("shell", "settings", "delete", "secure", key)
            else:
                device("shell", "settings", "put", "secure", key, value)
            assert device("shell", "settings", "get", "secure", key).strip() == value
        for package in (PACKAGE + ".test", PACKAGE):
            assert "Success" in device("uninstall", package)
        if created:
            device("shell", "rm", "-f", directory + "/proof.txt", outside)
            device("shell", "rmdir", directory)
            device("shell", "rmdir", parent)
    assert receipt is not None
    receipt["cleanup"] = (
        "Both packages removed; exact accessibility settings restored and read back; "
        "only exact synthetic document paths removed"
    )
    (output / "platform-consent.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print("Actual disposable Android system folder and screen consent acceptance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
