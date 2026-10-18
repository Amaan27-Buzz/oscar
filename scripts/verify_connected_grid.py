"""Run actual TLS Core/Worker process acceptance with disposable synthetic authority."""

import argparse
import base64
import json
import platform
import unittest
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def android_core_fixture(identity: dict):
    """Yield actual TLS Core and Worker authority for one disposable emulator."""
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    from oscar.cloud import CloudCore
    from oscar.remote_grid import create_invitation
    from tests.test_connected_acceptance import ConnectedAcceptanceTests

    fixture = ConnectedAcceptanceTests()
    fixture.setUp()
    try:
        core_process = fixture.start_core()
        fixture.enroll()
        worker = fixture.start_worker()
        task = fixture.submit(
            "file_write", {"path": "android-readback.txt", "content": "actual scoped Worker effect"}
        )
        fixture.approve(task)
        fixture.wait_task(task["task_id"])
        assert (
            fixture.workspace / "android-readback.txt"
        ).read_text() == "actual scoped Worker effect"
        fixture.stop(worker)
        fixture.stop(core_process)
        core = CloudCore(fixture.config, start_services=False)
        try:
            invitation = create_invitation(
                core,
                "synthetic-emulated-android",
                "mobile",
                identity["installation_id"],
                identity["public_key"],
                retain=True,
            )
        finally:
            core.close()
        core_process = fixture.start_core()
        fixture.start_worker()
        certificate = x509.load_pem_x509_certificate(fixture.ca.read_bytes())
        details = {
            "grid_origin": fixture.url,
            "grid_port": fixture.config.listen_port,
            "grid_invitation": base64.b64encode(json.dumps(invitation).encode()).decode(),
            "grid_ca": base64.b64encode(
                certificate.public_bytes(serialization.Encoding.DER)
            ).decode(),
            "grid_task": task["task_id"],
            "grid_target": "synthetic-desktop",
            "grid_path": "android-readback.txt",
            "evidence": "synthetic actual TLS Core and scoped filesystem Worker",
            "worker_host": platform.system(),
        }
        yield fixture, core_process, details
    finally:
        fixture.doCleanups()


def android_fixture(identity_path: Path, output: Path) -> int:
    """Keep a fixture alive until its controlling process closes stdin."""
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    with android_core_fixture(identity) as (_, _, details):
        with output.open("x", encoding="utf-8") as destination:
            json.dump(details, destination)
        output.chmod(0o600)
        print(
            json.dumps({"fixture": str(output), "status": "ready", "phone": "NOT_RUN"}), flush=True
        )
        input()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android-identity", type=Path)
    parser.add_argument("--fixture-output", type=Path)
    arguments = parser.parse_args()
    if arguments.android_identity:
        if not arguments.fixture_output:
            parser.error("--fixture-output is required for an Android fixture")
        return android_fixture(arguments.android_identity, arguments.fixture_output)
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_connected_acceptance")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "status": "verified" if result.wasSuccessful() else "failed",
                "platform": platform.system(),
                "architecture": platform.machine(),
                "transport": "trusted-local-ca TLS over loopback sockets",
                "processes": "independent Core and scoped filesystem Worker",
                "owner_phone": "NOT_RUN",
                "hosted_internet": "NOT_RUN",
            }
        )
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
