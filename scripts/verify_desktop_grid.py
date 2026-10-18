"""Real Windows CNG/DPAPI, native HTTPS client and independent scoped Worker acceptance."""

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path
from time import monotonic, sleep


def verify(binary: Path) -> dict[str, object]:
    from oscar.cloud import CloudCore
    from oscar.remote_grid import create_invitation
    from tests.test_connected_acceptance import ConnectedAcceptanceTests

    if os.name != "nt":
        raise OSError("actual Windows acceptance requires Windows")
    fixture = ConnectedAcceptanceTests()
    fixture.setUp()
    state = fixture.root / "native-connection.dat"

    def native(operation: str, *arguments: object) -> dict[str, object]:
        result = subprocess.run(
            [str(binary), "--grid-fixture-" + operation, str(state), *map(str, arguments)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode:
            raise AssertionError("native fixture failed: " + result.stderr[-2000:])
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise AssertionError("native projection object required")
        return value

    try:
        identity = native("identity", fixture.url)
        core = CloudCore(fixture.config, start_services=False)
        try:
            invitation = create_invitation(
                core,
                "synthetic-native-desktop",
                "desktop",
                str(identity["installation_id"]),
                str(identity["public_key"]),
                workspace="disposable-workspace",
                retain=True,
                owner_public_key=str(identity["owner_public_key"]),
            )
        finally:
            core.close()
        invitation_path = fixture.root / "native-invitation.json"
        invitation_path.write_text(json.dumps(invitation), encoding="utf-8")
        fixture.start_core()
        fixture.enroll()
        assert native("enroll", invitation_path, fixture.ca)["enrolled"] is True
        worker = fixture.launch(
            "import runpy; runpy.run_module('oscar.remote_worker',run_name='__main__')",
            "--connection",
            state,
            "--workspace",
            fixture.workspace,
            "--workspace-id",
            "disposable-workspace",
            "--journal",
            fixture.root / "native-claims.sqlite",
            "--fixture-ca",
            fixture.ca,
        )
        deadline = monotonic() + 20
        while monotonic() < deadline:
            if worker.poll() is not None:
                raise AssertionError(
                    "native-key Worker failed: " + (fixture.root / "process.log").read_text()
                )
            snapshot = fixture.mobile.request("snapshot", {"cursor": 0})
            if any(
                node["id"] == "synthetic-native-desktop" and node["status"] == "online"
                for node in snapshot["nodes"]
            ):
                break
            sleep(0.1)
        else:
            raise AssertionError("native-key Worker did not advertise")

        def submit(kind: str, parameters: dict[str, str]) -> dict[str, object]:
            return fixture.mobile.request(
                "submit",
                {
                    "text": "synthetic native connected acceptance",
                    "kind": kind,
                    "target": "synthetic-native-desktop",
                    "parameters": parameters,
                    "retain": True,
                },
            )

        read = submit("file_read", {"path": "known.txt"})
        fixture.wait_task(read["task_id"])
        write = submit(
            "file_write",
            {"path": "native-proof.txt", "content": "CNG authenticated actual Windows effect\n"},
        )
        assert write["approval_required"] is True
        assert not (fixture.workspace / "native-proof.txt").exists()
        native("approve", fixture.ca, write["task_id"])
        verified = fixture.wait_task(write["task_id"])
        assert verified["evidence"]
        assert (
            fixture.workspace / "native-proof.txt"
        ).read_text() == "CNG authenticated actual Windows effect\n"
        projection = native("snapshot", fixture.ca)
        assert any(
            task["task_id"] == write["task_id"] and task["state"] == "verified"
            for task in projection["tasks"]
        )
        assert projection["conversation"]["turns"]
        assert b"token" not in state.read_bytes()
        fixture.stop(worker)
        return {
            "status": "SOFTWARE_VERIFIED",
            "host": platform.system(),
            "native": "actual built Rust CNG signing and DPAPI credential process reopen",
            "transport": "trusted local CA HTTPS, certificate verification enabled",
            "execution": "independent Python Worker opens the same nonexportable CNG key",
            "effects": "actual scoped file read + exact approved write + independent Core readback",
            "projection": "native snapshot sees verified task and canonical conversation",
            "owner_confirmation": "synthetic fixture; physical owner confirmation NOT_RUN",
            "hosted_internet": "NOT_RUN",
            "physical_android": "NOT_RUN",
        }
    finally:
        fixture.stop_all()
        if state.exists():
            native("cleanup")
        fixture.doCleanups()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary", type=Path, default=Path("desktop/src-tauri/target/debug/oscar-desktop.exe")
    )
    arguments = parser.parse_args()
    try:
        result = verify(arguments.binary.resolve())
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, AssertionError, subprocess.SubprocessError) as error:
        print(
            json.dumps(
                {"status": "FAILED", "category": type(error).__name__, "message": str(error)}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
