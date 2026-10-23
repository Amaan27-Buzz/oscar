"""Actual system SAF/MediaProjection consent on one explicitly named disposable AVD."""

import base64
import hashlib
import io
import json
import os
import re
import subprocess
from pathlib import Path
from time import monotonic, sleep

from PIL import Image

from scripts.verify_connected_grid import android_core_fixture

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
                    "mobile/app/src/androidTest/AndroidManifest.xml",
                    "mobile/app/src/androidTest/java/io/dawnlight/oscar/mobile/ScreenFixtureActivity.java",
                    "mobile/app/src/androidTest/java/io/dawnlight/oscar/mobile/NativePlatformConsentTest.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativeCapabilities.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativeActionGate.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativePlatform.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativePlatformSettings.kt",
                    "mobile/app/src/main/java/io/dawnlight/oscar/mobile/NativeScreenService.kt",
                    "scripts/software_android_platform_reference.py",
                    "scripts/verify_connected_grid.py",
                    "tests/test_connected_acceptance.py",
                )
            }
            | {
                str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
                    p.read_bytes()
                ).hexdigest()
                for p in (
                    *(ROOT / "oscar").glob("*.py"),
                    *(ROOT / "tests").glob("*.py"),
                    *(ROOT / "mobile/app/src").rglob("*.kt"),
                    *(ROOT / "mobile/app/src").rglob("*.java"),
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
        identity_log = device(
            "shell",
            "am",
            "instrument",
            "-w",
            "-r",
            "-e",
            "class",
            PACKAGE + ".GridKeystoreTest#exportGridIdentity",
            PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner",
            timeout=180,
        )
        assert "OK (1 test)" in identity_log
        identity = json.loads(
            device("exec-out", "run-as", PACKAGE, "cat", "files/d2-device-identity.json")
        )
        with android_core_fixture(identity, android_workspace="selected-apps", management=True) as (
            fixture,
            _,
            details,
        ):
            port = str(details["grid_port"])
            device("reverse", "tcp:" + port, "tcp:" + port)
            process = None
            try:
                args = [
                    str(adb),
                    "-s",
                    SERIAL,
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
                    PACKAGE
                    + ".NativePlatformConsentTest#signedGridCapturesSelectedAppAndWithdrawsOnStop",
                ]
                for name in ("grid_origin", "grid_ca", "grid_invitation"):
                    args += ["-e", name, str(details[name])]
                args += [PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner"]
                guard()
                log_path = output / "signed-grid-screen.log"
                with log_path.open("w", encoding="utf-8") as log_file:
                    process = subprocess.Popen(args, stdout=log_file, stderr=subprocess.STDOUT)

                def wait(check, message, seconds=60):
                    until = monotonic() + seconds
                    while monotonic() < until:
                        if check():
                            return
                        if process.poll() is not None:
                            raise AssertionError(
                                "Native screen test ended early; inspect private log"
                            )
                        sleep(0.2)
                    raise AssertionError(message)

                def marker(name):
                    path = "files/" + name
                    try:
                        return device("shell", "run-as", PACKAGE, "ls", path).strip() == path
                    except subprocess.CalledProcessError:
                        return False

                def available():
                    return any(
                        c["id"] == "android.screen.capture"
                        for n in fixture.mobile.request("snapshot", {})["nodes"]
                        if n["id"] == "synthetic-emulated-android"
                        for c in n["capabilities"]
                    )

                wait(lambda: marker("software-screen-ready"), "OS consent fixture not ready")
                wait(available, "Screen capture was not advertised")
                task = fixture.mobile.request(
                    "submit",
                    {
                        "text": "Capture only the synthetic selected app; retain this test frame",
                        "kind": "android_screen_capture",
                        "target": "synthetic-emulated-android",
                        "parameters": {"package": PACKAGE + ".test", "target": "", "value": ""},
                        "retain": True,
                    },
                )
                if task["approval_required"]:
                    fixture.approve(task)
                final = fixture.wait_task(
                    task["task_id"], states=("verified", "partially_verified")
                )
                assert final["result"]["success"] and final["evidence"]
                content = json.loads(final["result"]["value"])
                assert content["package"] == PACKAGE + ".test"
                image = json.loads(content["observations"][0]["text"])
                assert image["mime"] == "image/jpeg"
                jpeg = base64.b64decode(image["base64"], validate=True)
                with Image.open(io.BytesIO(jpeg)) as frame:
                    assert frame.width == 256
                    red, green, blue = frame.convert("RGB").getpixel(
                        (frame.width // 2, frame.height // 2)
                    )
                    assert green > 100 and red < 60 and blue < 90
                device("shell", "run-as", PACKAGE, "touch", "files/software-screen-verified")
                wait(lambda: marker("software-screen-stopped"), "Native capture did not stop")
                wait(lambda: not available(), "Capture remained advertised after OS service stop")
                device("shell", "run-as", PACKAGE, "touch", "files/software-screen-withdrawn")
                process.wait(timeout=45)
                grid_log = log_path.read_text(encoding="utf-8")
                assert (
                    process.returncode == 0
                    and "OK (1 test)" in grid_log
                    and "FAILURES" not in grid_log
                )
                screen_grid = {
                    "task_state": final["state"],
                    "task_id": task["task_id"],
                    "jpeg_sha256": hashlib.sha256(jpeg).hexdigest(),
                    "jpeg_bytes": len(jpeg),
                    "width": 256,
                    "selected_app_pixel_verified": True,
                    "withdrawal_verified": True,
                    "retention": "Explicit synthetic archive grant; no personal screen content",
                    "automatic_effect_retry": False,
                }
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=20)
                device("reverse", "--remove", "tcp:" + port)
        assert inputs() == pinned, "Acceptance source or APK changed during execution"
        receipt = {
            "status": "EMULATED_OS_VERIFIED",
            "serial": SERIAL,
            "avd": AVD,
            "api": 35,
            "checks": list(methods),
            "signed_grid_screen": screen_grid,
            "input_stability": "Source and APK SHA-256 matched before and after execution",
            "authority": (
                "OS adapter checks plus signed synthetic actual Grid capture; no owner activation"
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
