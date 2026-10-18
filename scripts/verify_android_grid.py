"""Actual native Android/Core/Worker TLS acceptance on an explicitly selected emulator."""

import argparse
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
        [str(adb), "devices", "-l"], capture_output=True, text=True, check=True, timeout=20
    ).stdout
    if not re.search(r"^" + re.escape(arguments.serial) + r"\s+device\b", inventory, re.MULTILINE):
        raise RuntimeError("explicit emulator is absent from the ADB device inventory")

    def invoke(*command: str, timeout: int = 30) -> str:
        process = subprocess.run(
            [str(adb), "-s", arguments.serial, *command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if process.returncode:
            # Instrumentation arguments contain a short-lived invitation: never echo them.
            raise RuntimeError("explicit emulator operation failed")
        return process.stdout

    if invoke("get-state").strip() != "device":
        raise RuntimeError("selected emulator is not online")
    if invoke("shell", "getprop", "ro.kernel.qemu").strip() != "1":
        raise RuntimeError("selected serial is not an emulator")
    avd = invoke("emu", "avd", "name").splitlines()[0]
    if not avd or avd == "OK":
        raise RuntimeError("selected emulator has no identifiable AVD")

    def instrument(class_name: str, method: str, **values: str) -> None:
        command = ["shell", "am", "instrument", "-w", "-r", "-e", "class"]
        command.append(PACKAGE + "." + class_name + "#" + method)
        for name, value in values.items():
            command.extend(["-e", name, str(value)])
        command.append(RUNNER)
        result = invoke(*command, timeout=180)
        logs = ROOT / ".oscar" / "d2-android"
        logs.mkdir(parents=True, exist_ok=True)
        log = logs / (method + ".log")
        # Retain assertion stacks privately without printing invitation material.
        invitation = values.get("grid_invitation")
        log.write_text(
            result.replace(invitation, "[invitation redacted]") if invitation else result
        )
        log.chmod(0o600)
        # JUnit assumptions/skips or a zero-test invocation cannot establish acceptance.
        if not re.search(r"OK \(1 test\)", result) or re.search(
            r"FAILURES|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -[34]", result
        ):
            raise RuntimeError(
                "native emulator check failed: " + method + "; private log: " + str(log)
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
        finally:
            invoke("reverse", "--remove", "tcp:" + port)
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
