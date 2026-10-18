"""Actual TLS sockets, independent Core/Worker processes, synthetic disposable authority."""

import base64
import ipaddress
import json
import os
import ssl
import subprocess
import sys
import unittest
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from uuid import uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from oscar.cloud import CloudConfig, CloudCore
from tests.test_cloud import configuration


def synthetic_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def public_key(key):
    return base64.b64encode(
        key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    ).decode()


def sign(key, payload):
    return key.sign(
        payload, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256()
    )


def save_key(path, key):
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    path.chmod(0o600)


class ConnectedAcceptanceTests(unittest.TestCase):
    def setUp(self):
        from oscar.remote_grid import create_invitation

        self.temp = TemporaryDirectory(prefix="oscar-connected-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = configuration(self.root)
        self.config = CloudConfig.load(self.path)
        self.url = f"https://127.0.0.1:{self.config.listen_port}"
        self.workspace = self.root / "disposable-workspace"
        self.workspace.mkdir()
        (self.workspace / "known.txt").write_text("source-backed read", encoding="utf-8")
        self.worker_key, self.client_key, self.owner_key = (synthetic_key() for _ in range(3))
        self.processes = []
        self.addCleanup(self.stop_all)
        self.certificate()
        core = CloudCore(self.config, initialize=True, start_services=False)
        try:
            self.invitations = {
                "desktop": create_invitation(
                    core,
                    "synthetic-desktop",
                    "desktop",
                    "synthetic-desktop-install",
                    public_key(self.worker_key),
                    workspace="disposable-workspace",
                    retain=True,
                ),
                "mobile": create_invitation(
                    core,
                    "synthetic-mobile",
                    "mobile",
                    "synthetic-mobile-install",
                    public_key(self.client_key),
                    retain=True,
                    owner_public_key=public_key(self.owner_key),
                ),
            }
        finally:
            core.close()

    def certificate(self):
        key = synthetic_key()
        save_key(self.root / "tls-key.pem", key)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
        now = datetime.now(UTC)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(hours=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
                ),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )
        self.ca = self.root / "tls-cert.pem"
        self.ca.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        self.context = ssl.create_default_context(cafile=str(self.ca))

    def launch(self, code, *arguments):
        log = (self.root / "process.log").open("a", encoding="utf-8")
        self.addCleanup(log.close)
        process = subprocess.Popen(
            [sys.executable, "-c", code, *map(str, arguments)], stdout=log, stderr=log
        )
        self.processes.append(process)
        return process

    def start_core(self):
        # Test-only TLS wrapping preserves the real Core and bounded HTTP request handler.
        process = self.launch(
            """import ssl, sys
from oscar.cloud_http import CloudHTTPServer
original = CloudHTTPServer.__init__
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(sys.argv.pop(1), sys.argv.pop(1))
def initialize(self, core):
    original(self, core)
    self.socket = context.wrap_socket(self.socket, server_side=True)
CloudHTTPServer.__init__ = initialize
from oscar.cloud import main
raise SystemExit(main())
""",
            self.ca,
            self.root / "tls-key.pem",
            "--config",
            self.path,
        )
        deadline = monotonic() + 20
        while monotonic() < deadline:
            if process.poll() is not None:
                self.fail(
                    "Core exited before readiness: " + (self.root / "process.log").read_text()
                )
            try:
                with urllib.request.urlopen(
                    self.url + "/readyz", context=self.context, timeout=1
                ) as response:
                    if response.status == 200:
                        return process
            except (OSError, urllib.error.URLError):
                pass
            sleep(0.05)
        self.fail("actual TLS Core readiness exceeded its bound")

    def enroll(self):
        from oscar.remote_client import GridClient

        self.desktop = GridClient(
            self.url,
            {},
            lambda value: sign(self.worker_key, value),
            ssl_context=self.context,
        )
        self.mobile = GridClient(
            self.url,
            {},
            lambda value: sign(self.client_key, value),
            ssl_context=self.context,
        )
        self.worker_session = self.desktop.enroll(self.invitations["desktop"])
        self.client_session = self.mobile.enroll(self.invitations["mobile"])

    def start_worker(self, *, crash_before_delivery=False):
        key_path = self.root / "worker-key.pem"
        save_key(key_path, self.worker_key)
        config = self.root / "worker.json"
        config.write_text(
            json.dumps(
                {
                    "url": self.url,
                    "session": self.worker_session,
                    "workspace": str(self.workspace),
                    "workspace_id": "disposable-workspace",
                    "journal": str(self.root / "worker-journal.sqlite"),
                    "key_file": str(key_path),
                    "ca_file": str(self.ca),
                    "synthetic": True,
                }
            ),
            encoding="utf-8",
        )
        config.chmod(0o600)
        code = "import runpy; runpy.run_module('oscar.remote_worker',run_name='__main__')"
        if crash_before_delivery:
            code = """import os, runpy
from oscar.remote_client import GridClient
original = GridClient.request
def request(self, operation, payload, request_id=None):
    if operation == 'deliver':
        os._exit(79)
    return original(self, operation, payload, request_id=request_id)
GridClient.request = request
runpy.run_module('oscar.remote_worker', run_name='__main__')
"""
        process = self.launch(code, "--config", config)
        deadline = monotonic() + 15
        while monotonic() < deadline:
            if process.poll() is not None:
                self.fail("Worker exited before task: " + (self.root / "process.log").read_text())
            snapshot = self.mobile.request("snapshot", {"cursor": 0})
            if any(
                n["id"] == "synthetic-desktop" and n["status"] == "online"
                for n in snapshot["nodes"]
            ):
                return process
            sleep(0.1)
        self.fail("actual Worker advertisement exceeded its bound")

    def stop(self, process):
        if process.poll() is None:
            if os.name == "nt":
                # A Windows venv launcher can own a child interpreter holding the volume lock.
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                    timeout=20,
                )
            else:
                process.terminate()
            process.wait(timeout=20)

    def stop_all(self):
        for process in reversed(self.processes):
            self.stop(process)

    def submit(self, kind, parameters, *, request_id=None):
        return self.mobile.request(
            "submit",
            {
                "text": "synthetic bounded acceptance",
                "kind": kind,
                "target": "synthetic-desktop",
                "parameters": parameters,
                "retain": True,
            },
            request_id=request_id,
        )

    def approve(self, task):
        challenge = self.mobile.request(
            "challenge", {"task_id": task["task_id"], "operation": "approve"}
        )
        return self.mobile.request(
            "complete",
            {
                "challenge_id": challenge["challenge_id"],
                "signature": base64.b64encode(
                    sign(self.owner_key, base64.b64decode(challenge["signing_payload"]))
                ).decode(),
            },
        )

    def wait_task(self, task_id, states=("verified",)):
        deadline = monotonic() + 25
        while monotonic() < deadline:
            task = self.mobile.request("inspect", {"task_id": task_id})
            if task["state"] in states:
                return task
            if task["state"] in {"failed", "cancelled", "unknown"}:
                self.fail("task did not verify: " + json.dumps(task))
            sleep(1)
        self.fail("bounded task deadline exceeded: " + json.dumps(task))

    def test_tls_enrollment_actual_worker_read_write_history_restart_and_cleanup(self):
        core = self.start_core()
        self.enroll()
        worker = self.start_worker()
        first = self.submit("file_read", {"path": "known.txt"})
        read = self.wait_task(first["task_id"])
        self.assertTrue(read["evidence"])
        identifier = uuid4().hex
        write = self.submit(
            "file_write",
            {"path": "created.txt", "content": "verified mutation"},
            request_id=identifier,
        )
        self.assertTrue(write["approval_required"])
        self.assertFalse((self.workspace / "created.txt").exists())
        self.approve(write)
        verified = self.wait_task(write["task_id"])
        self.assertEqual("verified mutation", (self.workspace / "created.txt").read_text())
        self.assertTrue(verified["evidence"])
        self.assertEqual(
            write["task_id"],
            self.submit(
                "file_write",
                {"path": "created.txt", "content": "verified mutation"},
                request_id=identifier,
            )["task_id"],
        )
        desktop = self.desktop.request("snapshot", {"cursor": 0})
        mobile = self.mobile.request("snapshot", {"cursor": 0})
        self.assertEqual(desktop["relationship_id"], mobile["relationship_id"])
        self.assertEqual(desktop["events"], mobile["events"])
        self.assertTrue(mobile["events"])
        self.assertEqual(
            [], self.mobile.request("snapshot", {"cursor": mobile["cursor"]})["events"]
        )
        self.stop(worker)
        self.stop(core)
        core = self.start_core()
        restored = self.mobile.request("snapshot", {"cursor": 0})
        self.assertEqual(mobile["relationship_id"], restored["relationship_id"])
        self.assertEqual(mobile["events"], restored["events"])
        self.assertEqual(
            "verified", self.mobile.request("inspect", {"task_id": write["task_id"]})["state"]
        )
        self.mobile.request("revoke", {})
        with self.assertRaises((PermissionError, urllib.error.HTTPError)):
            self.mobile.request("snapshot", {"cursor": 0})
        self.stop(core)
        logs = (self.root / "process.log").read_text()
        for session in (self.worker_session, self.client_session):
            self.assertNotIn(session["token"], logs)
        self.assertNotIn("verified mutation", logs)

    def test_worker_death_after_effect_core_restart_never_replays_mutation(self):
        core = self.start_core()
        self.enroll()
        worker = self.start_worker(crash_before_delivery=True)
        task = self.submit("file_write", {"path": "uncertain.txt", "content": "first effect"})
        self.approve(task)
        self.assertEqual(79, worker.wait(timeout=20))
        target = self.workspace / "uncertain.txt"
        self.assertEqual("first effect", target.read_text())
        self.stop(core)
        core = self.start_core()
        blocked = self.mobile.request("inspect", {"task_id": task["task_id"]})
        self.assertIn(blocked["state"], {"blocked", "unknown"})
        # Independent subsequent content makes a replay observable instead of idempotently hidden.
        target.write_text("external readback marker", encoding="utf-8")
        worker = self.start_worker()
        read = self.submit("file_read", {"path": "known.txt"})
        self.wait_task(read["task_id"])
        self.assertEqual("external readback marker", target.read_text())
        self.assertIn(
            self.mobile.request("inspect", {"task_id": task["task_id"]})["state"],
            {"blocked", "unknown"},
        )
        self.stop(worker)
        self.stop(core)


if __name__ == "__main__":
    unittest.main()
