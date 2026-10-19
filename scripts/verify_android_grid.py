"""Actual native Android/Core/Worker TLS acceptance on an explicitly selected emulator."""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from scripts.verify_connected_grid import android_core_fixture

PACKAGE = "io.dawnlight.oscar.mobile"
RUNNER = PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner"
ROOT = Path(__file__).resolve().parents[1]


def private_log(operation: str, output: str, secrets: tuple[str, ...] = ()) -> Path:
    logs = ROOT / ".oscar" / "d2-android"
    logs.mkdir(parents=True, exist_ok=True)
    for secret in secrets:
        if secret:
            output = output.replace(secret, "[credential redacted]")
    # Also scrub credential fields if an assertion formats its JSON input.
    output = re.sub(
        r"(?i)([\"\'](?:token|invitation|signature|private_key)[\"\']\s*:\s*)[\"\'][^\"\']*[\"\']",
        r'\1"[credential redacted]"',
        output,
    )
    log = logs / (operation + ".log")
    log.write_text(output[-1_048_576:], encoding="utf-8")
    log.chmod(0o600)
    return log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", type=Path)
    arguments = parser.parse_args()
    # Deliberately refuse every physical serial before invoking device commands.
    if not re.fullmatch(r"emulator-[0-9]+", arguments.serial):
        parser.error("an explicitly identified disposable emulator serial is required")
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    adb = arguments.adb or shutil.which("adb")
    if adb is None and sdk:
        adb = Path(sdk) / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
    if adb is None:
        parser.error("ADB must be available through --adb, PATH or ANDROID_HOME")
    inventory = subprocess.run(
        [str(adb), "devices", "-l"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=20,
    ).stdout
    if not re.search(r"^" + re.escape(arguments.serial) + r"\s+device\b", inventory, re.MULTILINE):
        raise RuntimeError("explicit emulator is absent from the ADB device inventory")

    def invoke(
        *command: str,
        timeout: int = 30,
        operation: str | None = None,
        secrets: tuple[str, ...] = (),
    ) -> str:
        operation = operation or command[0]
        try:
            process = subprocess.run(
                [str(adb), "-s", arguments.serial, *command],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:

            def decoded(value: str | bytes | None) -> str:
                return (
                    value.decode("utf-8", errors="replace")
                    if isinstance(value, bytes)
                    else value or ""
                )

            timeout_log = private_log(
                operation, decoded(error.stdout) + "\n" + decoded(error.stderr), secrets
            )
            # TimeoutExpired embeds the complete command, including enrollment arguments.
            raise RuntimeError(
                f"explicit emulator operation timed out: {operation}; private log: {timeout_log}"
            ) from None
        log: Path | None = None
        if process.returncode or operation.startswith("instrument-"):
            log = private_log(operation, process.stdout + "\n" + process.stderr, secrets)
        if process.returncode:
            # Instrumentation arguments contain a short-lived invitation: never echo them.
            raise RuntimeError(
                f"explicit emulator operation failed: {operation} (exit {process.returncode}); "
                f"private log: {log}"
            )
        return process.stdout

    if invoke("get-state").strip() != "device":
        raise RuntimeError("selected emulator is not online")
    if invoke("shell", "getprop", "ro.kernel.qemu").strip() != "1":
        raise RuntimeError("selected serial is not an emulator")
    names = invoke("emu", "avd", "name").splitlines()
    avd = names[0] if names else ""
    if not avd or avd == "OK":
        raise RuntimeError("selected emulator has no identifiable AVD")

    # connectedDebugAndroidTest removes its test APKs during teardown. Reinstall
    # both exact build outputs after the emulator guard and before direct am instrument.
    apks = (
        ("app", "app/build/outputs/apk/debug/app-debug.apk"),
        ("instrumentation", "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"),
    )
    if not all((ROOT / "mobile" / relative).is_file() for _, relative in apks):
        raise RuntimeError(
            "built Android APK is missing; assembleDebug and assembleDebugAndroidTest are required"
        )
    for name, relative in apks:
        apk = ROOT / "mobile" / relative
        result = invoke("install", "-r", "-t", str(apk), timeout=120, operation="install-" + name)
        if not re.search(r"^Success\s*$", result, re.MULTILINE):
            log = private_log("install-" + name, result)
            raise RuntimeError(
                "Android APK installation was not confirmed; private log: " + str(log)
            )

    def instrument(class_name: str, method: str, **values: str) -> None:
        command = ["shell", "am", "instrument", "-w", "-r", "-e", "class"]
        command.append(PACKAGE + "." + class_name + "#" + method)
        for name, value in values.items():
            command.extend(["-e", name, str(value)])
        command.append(RUNNER)
        result = invoke(
            *command,
            timeout=180,
            operation="instrument-" + method,
            secrets=(values.get("grid_invitation", ""),),
        )
        # JUnit assumptions/skips or a zero-test invocation cannot establish acceptance.
        if not re.search(r"OK \(1 test\)", result) or re.search(
            r"FAILURES|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -[34]", result
        ):
            raise RuntimeError(
                "native emulator check failed: "
                + method
                + "; private log: "
                + str(ROOT / ".oscar" / "d2-android" / ("instrument-" + method + ".log"))
            )
        print(json.dumps({"emulated_check": method, "status": "verified"}), flush=True)

    instrument("GridKeystoreTest", "exportGridIdentity")
    identity = json.loads(
        invoke("exec-out", "run-as", PACKAGE, "cat", "files/d2-device-identity.json")
    )
    with android_core_fixture(identity) as (fixture, core_process, details):
        port = str(details["grid_port"])
        invoke("reverse", "tcp:" + port, "tcp:" + port)
        try:
            connection = {k: str(v) for k, v in details.items() if k.startswith("grid_")}
            connection.pop("grid_port")
            instrument("GridConnectedTest", "connectedGrid", **connection)
            invoke("shell", "am", "force-stop", PACKAGE)
            instrument(
                "GridConnectedTest",
                "processRestored",
                grid_origin=details["grid_origin"],
                grid_ca=details["grid_ca"],
            )
            fixture.stop(core_process)
            instrument(
                "GridConnectedTest",
                "connectionLostWithdrawsPrivateState",
                grid_core_stopped="true",
            )
            fixture.start_core()
            instrument(
                "GridConnectedTest",
                "revokeAndLogout",
                grid_revoke="true",
                grid_ca=details["grid_ca"],
            )
            node_id = json.loads(base64.b64decode(details["grid_invitation"]))["node_id"]
            nodes = fixture.mobile.request("snapshot", {})["nodes"]
            if not any(
                node["id"] == node_id and node["revoked"] and node["status"] == "offline"
                for node in nodes
            ):
                raise RuntimeError("independent Core readback did not confirm Android revocation")
        finally:
            try:
                invoke("reverse", "--remove", "tcp:" + port)
            except RuntimeError:
                pass  # Emulator loss must not prevent Core/Worker fixture cleanup.
    print(
        json.dumps(
            {
                "status": "EMULATED",
                "serial": arguments.serial,
                "avd": avd,
                "transport": "actual trusted-CA HTTPS Core and independent scoped Worker",
                "owner_phone": "NOT_RUN",
                "owner_biometrics": "NOT_RUN",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
