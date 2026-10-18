"""Offline credential delivery must precede durable Grid authorization."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oscar.cloud import CloudConfig, CloudCore, enroll_client
from oscar.grid import SessionHandle
from tests.test_cloud import configuration


class CloudEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.path = configuration(self.root)
        self.config = CloudConfig.load(self.path)
        self.core = CloudCore(self.config, initialize=True, start_services=False)
        self.addCleanup(self.core.close)
        self.node = "synthetic-enrollment-client"

    def sessions(self):
        return [s for s in self.core.harness.store.all("session") if s["node_id"] == self.node]

    def handle(self, path):
        data = json.loads(path.read_text())
        return SessionHandle(data["session_id"], data["node_id"], data["token"])

    def enroll(self, name="credential.json"):
        path = self.root / name
        enroll_client(self.core, self.node, path, 3600)
        return path

    def test_existing_output_is_preserved_without_creating_authority(self):
        path = self.root / "credential.json"
        path.write_text("previous private credential")
        with self.assertRaises(FileExistsError):
            self.enroll()
        self.assertEqual("previous private credential", path.read_text())
        self.assertEqual([], self.sessions())
        with self.assertRaises(KeyError):
            self.core.harness.store.get("node", self.node)

    @unittest.skipUnless(os.name == "posix", "POSIX directory permissions")
    def test_unwritable_or_shared_parent_rejected_before_authorization(self):
        parent = self.root / "output"
        parent.mkdir(mode=0o700)
        for mode in (0o500, 0o755):
            parent.chmod(mode)
            try:
                with self.assertRaises(PermissionError):
                    enroll_client(self.core, self.node, parent / "credential.json", 3600)
                self.assertEqual([], self.sessions())
                self.assertFalse((parent / "credential.json").exists())
            finally:
                parent.chmod(0o700)

    def test_partial_write_rolls_back_and_explicit_retry_succeeds(self):
        def partial(data, output):
            output.write('{"token":"incomplete')
            output.flush()
            raise OSError("synthetic disk failure")

        with patch("oscar.cloud.json.dump", side_effect=partial), self.assertRaises(OSError):
            self.enroll()
        self.assertEqual([], self.sessions())
        self.assertFalse(self.core.harness.store.get("node", self.node)["paired"])
        with self.assertRaises(KeyError):
            self.core.harness.store.get("cloud_client", self.node)
        with self.assertRaises(FileExistsError):
            self.enroll()
        path = self.enroll("retry.json")
        self.core.harness.grid.authenticate(self.handle(path), "cloud:inspect")
        events = [r["event"] for r in self.core.harness.store.ledger("")]
        self.assertIn("cloud_enrollment_failed", events)
        self.assertEqual(2, events.count("cloud_enrollment_attempt"))
        self.assertEqual(1, events.count("cloud_enrollment_delivered"))
        if os.name == "posix":
            self.assertEqual(0o600, path.stat().st_mode & 0o777)

    def test_session_creation_failure_and_retry(self):
        with patch.object(self.core.harness.grid, "pair", side_effect=OSError("synthetic")):
            with self.assertRaises(OSError):
                self.enroll()
        self.assertEqual([], self.sessions())
        path = self.enroll("retry.json")
        self.core.harness.grid.authenticate(self.handle(path), "cloud:probe")

    def test_sync_failure_preserves_preexisting_session_and_binding(self):
        previous = self.enroll()
        content = previous.read_bytes()
        before = self.sessions()
        with patch("oscar.cloud.os.fsync", side_effect=OSError("synthetic sync failure")):
            with self.assertRaises(OSError):
                self.enroll("replacement.json")
        self.assertEqual(content, previous.read_bytes())
        self.assertEqual(before, self.sessions())
        self.core.harness.grid.authenticate(self.handle(previous), "cloud:inspect")
        delivered_but_rolled_back = self.handle(self.root / "replacement.json")
        with self.assertRaises(KeyError):
            self.core.harness.grid.authenticate(delivered_but_rolled_back, "cloud:inspect")
        self.assertEqual(
            {"core_id": self.config.core_id},
            self.core.harness.store.get("cloud_client", self.node),
        )

    def test_interrupted_delivery_rolls_back_on_restart_and_preserves_old_session(self):
        previous = self.enroll()
        self.core.close()
        output = self.root / "interrupted.json"
        command = (
            "import os,sys; from pathlib import Path; "
            "from oscar.cloud import CloudConfig,CloudCore,enroll_client; "
            "c=CloudCore(CloudConfig.load(Path(sys.argv[1])),start_services=False); "
            "audit=c.harness.store.audit; "
            "c.harness.store.audit=lambda task,event,data: "
            "os._exit(79) if event=='cloud_enrollment_delivered' else audit(task,event,data); "
            "enroll_client(c,sys.argv[2],Path(sys.argv[3]),3600)"
        )
        result = subprocess.run(
            [sys.executable, "-c", command, str(self.path), self.node, str(output)],
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(79, result.returncode, result.stderr)
        self.core = CloudCore(self.config, start_services=False)
        self.addCleanup(self.core.close)
        self.assertEqual(1, len(self.sessions()))
        self.core.harness.grid.authenticate(self.handle(previous), "cloud:inspect")
        with self.assertRaises(KeyError):
            self.core.harness.grid.authenticate(self.handle(output), "cloud:inspect")
        retry = self.enroll("retry.json")
        self.core.harness.grid.authenticate(self.handle(retry), "cloud:inspect")

    @unittest.skipUnless(os.name == "posix", "POSIX nonsymlink descriptor traversal")
    def test_symlink_and_replaced_parent_do_not_redirect_private_output(self):
        outside = self.root / "outside"
        outside.mkdir(mode=0o700)
        link = self.root / "link"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            enroll_client(self.core, self.node, link / "credential.json", 3600)
        self.assertFalse((outside / "credential.json").exists())
        path = self.root / "credential.json"
        path.symlink_to(outside / "other.json")
        with self.assertRaises(ValueError):
            self.enroll()
        self.assertFalse((outside / "other.json").exists())
        self.assertEqual([], self.sessions())
        parent, moved = self.root / "private", self.root / "moved"
        parent.mkdir(mode=0o700)
        dump = json.dump

        def replace_parent(data, output):
            dump(data, output)
            parent.rename(moved)
            parent.symlink_to(outside, target_is_directory=True)

        with patch("oscar.cloud.json.dump", side_effect=replace_parent):
            with self.assertRaises(PermissionError):
                enroll_client(self.core, self.node, parent / "client.json", 3600)
        self.assertTrue((moved / "client.json").exists())
        self.assertFalse((outside / "client.json").exists())
        self.assertEqual([], self.sessions())

    def test_core_or_unrelated_identity_cannot_be_enrolled(self):
        with self.assertRaises(ValueError):
            enroll_client(self.core, self.config.core_id, self.root / "core.json", 3600)
        self.node = "synthetic-unrelated-node"
        from oscar.grid import Node, NodeRole

        self.core.harness.grid.register(Node(self.node, NodeRole.DESKTOP, ("execute",)))
        from oscar.storage import StateConflict

        with self.assertRaises(StateConflict):
            self.enroll()
        self.assertEqual([], self.sessions())
