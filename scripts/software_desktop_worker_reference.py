"""Actual native supervisor and disposable installed runtime, synthetic TLS/CNG authority only."""

import json
import os
import shutil
import subprocess
import venv
from pathlib import Path
from time import monotonic, sleep

from oscar.cloud import CloudCore
from oscar.remote_grid import create_invitation
from tests.test_connected_acceptance import ConnectedAcceptanceTests


def run() -> dict:
    repo = Path(__file__).resolve().parents[1]
    binary = repo / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    if not binary.is_file():
        raise FileNotFoundError("Build the current native debug Desktop first")
    fixture = ConnectedAcceptanceTests()
    state = None
    process = None
    try:
        fixture.setUp()
        state = fixture.root / "native-connection.dat"

        def native(*args):
            result = subprocess.run(
                [str(binary), *map(str, args)], capture_output=True, text=True,
                timeout=30, check=True,
            )
            return json.loads(result.stdout)

        identity = native("--grid-fixture-identity", state, fixture.url)
        core = CloudCore(fixture.config, start_services=False)
        try:
            invitation = create_invitation(
                core, "synthetic-native-worker", "desktop", identity["installation_id"],
                identity["public_key"], workspace="native-execution-workspace", retain=True,
                owner_public_key=identity["owner_public_key"], machine_control=True,
            )
        finally:
            core.close()
        invitation_path = fixture.root / "native-invitation.json"
        invitation_path.write_text(json.dumps(invitation), encoding="utf-8")
        fixture.start_core()
        fixture.enroll()
        native("--grid-fixture-enroll", state, invitation_path, fixture.ca)

        runtime = fixture.root / "installed-runtime"
        venv.EnvBuilder(with_pip=False, system_site_packages=True).create(runtime)
        # Install the current package into only this disposable interpreter's normal site-packages.
        shutil.copytree(repo / "oscar", runtime / "Lib/site-packages/oscar",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        config = {
            "python": str(runtime / "Scripts/python.exe"),
            "workspace": str(fixture.workspace),
            "capabilities": ["machine.files.read", "machine.files.write"],
            "trusted_host_execution": False, "allowed_executables": [], "desktop_app_ids": [],
        }
        config_path = fixture.root / "native-worker-scope.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        environment = {**os.environ, "SSL_CERT_FILE": str(fixture.ca)}
        process = subprocess.Popen(
            [str(binary), "--grid-fixture-worker", str(state), str(fixture.ca), str(config_path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=environment,
        )
        fixture.processes.append(process)
        assert process.stdout is not None and process.stdin is not None
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            ready = pool.submit(process.stdout.readline)
            try:
                observed = json.loads(ready.result(timeout=30))
            except Exception:
                fixture.stop(process)
                assert process.stderr is not None
                raise AssertionError(
                    "Synthetic native startup failed: " + process.stderr.read(4096)
                ) from None
        assert observed == {"worker": "online", "scope": "synthetic"}, observed
        task = fixture.mobile.request("submit", {
            "text": "Synthetic native supervisor acceptance", "kind": "file_write",
            "target": "synthetic-native-worker", "parameters": {
                "path": "native-supervised.txt", "content": "native child; canonical Core readback",
            }, "retain": True,
        })
        fixture.approve(task)
        verified = fixture.wait_task(task["task_id"])
        assert verified["state"] == "verified"
        assert (fixture.workspace / "native-supervised.txt").read_text() == (
            "native child; canonical Core readback"
        )
        process.stdin.write("stop\n")
        process.stdin.flush()
        output, _ = process.communicate(timeout=10)
        assert process.returncode == 0
        assert json.loads(output) == {"worker": "stopped"}
        deadline = monotonic() + 5
        while monotonic() < deadline:
            nodes = fixture.mobile.request("snapshot", {"cursor": 0})["nodes"]
            node = next(node for node in nodes if node["id"] == "synthetic-native-worker")
            if not node["capabilities"]:
                break
            sleep(0.1)
        else:
            raise AssertionError("Stopped Worker retained live capabilities")
        return {
            "status": "SOFTWARE_VERIFIED", "transport": "actual loopback TLS",
            "identity": "synthetic Windows CNG and DPAPI",
            "runtime": "current package installed into disposable isolated Python site-packages",
            "checks": ["native supervisor startup", "actual enrolled workspace binding",
                       "signed Ask file write", "independent Core readback", "separate file bytes",
                       "cooperative stop", "capability withdrawal"],
            "owner_activation": "NOT_RUN", "physical_device": "NOT_RUN",
            "hosted_deployment": "NOT_RUN",
        }
    finally:
        if process is not None:
            fixture.stop(process)
        if state is not None and state.exists():
            subprocess.run([str(binary), "--grid-fixture-cleanup", str(state)],
                           capture_output=True, timeout=10, check=True)
        if not fixture.doCleanups():
            raise AssertionError("Synthetic native fixture cleanup failed")
        if hasattr(fixture, "root") and fixture.root.exists():
            raise AssertionError("Disposable installed runtime and credentials were not removed")


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
