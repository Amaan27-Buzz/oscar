"""Inspect durable authority after enrollment failures, process loss and races."""

import base64
import json
import sqlite3
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oscar.cloud import CloudConfig, CloudCore
from oscar.remote_grid import create_invitation
from tests.test_cloud import configuration
from tests.test_remote_grid import DirectClient, keypair, signature


class RemoteEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = configuration(self.root)
        self.config = CloudConfig.load(self.config_path)
        self.core = CloudCore(self.config, initialize=True)
        self.key, self.public = keypair()

    def tearDown(self):
        self.core.close()
        self.tmp.cleanup()

    def proof(self, *, recover=False):
        invite = create_invitation(
            self.core,
            "atomic-mobile",
            "mobile",
            "atomic-installation",
            self.public,
            recover=recover,
        )
        return {
            "version": 2,
            "challenge_id": invite["challenge_id"],
            "signature": signature(self.key, base64.b64decode(invite["signing_payload"])),
        }

    def restart(self):
        self.core.close()
        self.core = CloudCore(self.config)

    def test_screen_capture_and_retention_need_separate_desktop_consent(self):
        for capture, retain in ((False, False), (True, False), (True, True)):
            invite = create_invitation(
                self.core,
                "screen-desktop",
                "desktop",
                "screen-installation",
                self.public,
                workspace="screen-workspace",
                machine_control=True,
                screen_capture=capture,
                screen_retain=retain,
            )
            row = self.core.harness.store.get("remote_invitation", invite["challenge_id"])
            self.assertEqual(capture, "desktop:capture" in row["binding"]["scopes"])
            self.assertEqual(retain, "screen:retain" in row["binding"]["scopes"])
        for options in (
            {"screen_retain": True},
            {"screen_capture": "yes"},
            {"screen_capture": True, "machine_control": False},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                create_invitation(
                    self.core,
                    "denied-desktop",
                    "desktop",
                    "denied-installation",
                    self.public,
                    workspace="screen-workspace",
                    **options,
                )

    def authority(self):
        store = self.core.harness.store
        return {
            kind: [
                row
                for row in store.all(kind)
                if row.get("node_id", row.get("id")) == "atomic-mobile"
            ]
            for kind in ("node", "session", "remote_device")
        }

    def assert_burned(self, proof):
        with self.assertRaises(KeyError):
            self.core.harness.store.get("remote_invitation", proof["challenge_id"])
        with self.assertRaises(KeyError):
            self.core.remote.enroll(proof)

    def test_failed_initial_and_replacement_enrollment_preserve_committed_authority(self):
        for recover in (False, True):
            if recover:
                old = self.core.remote.enroll(self.proof())
            for phase in ("pair", "node", "session", "remote_device"):
                with self.subTest(recover=recover, phase=phase):
                    proof = self.proof(recover=recover)
                    if recover:
                        self.core.harness.grid.disconnect("atomic-mobile")
                    before = self.authority()
                    store = self.core.harness.store
                    original = store.put

                    def fail(kind, identifier, value, original=original, phase=phase):
                        original(kind, identifier, value)
                        if kind == phase:
                            raise OSError("synthetic durable write failure")

                    if phase == "pair":
                        guard = patch.object(self.core.harness.grid, "pair", side_effect=OSError)
                    else:
                        guard = patch.object(store, "put", side_effect=fail)
                    with guard, self.assertRaises(OSError):
                        self.core.remote.enroll(proof)
                    self.assert_burned(proof)
                    self.assertEqual(self.authority(), before)
                    self.restart()
                    self.assertEqual(self.authority(), before)
                    if recover:
                        DirectClient(self.core, old).request("snapshot", {})

    def test_process_crashes_before_commit_rollback_and_lost_reply_requires_owner_recovery(self):
        # os._exit bypasses Python rollback/finalizers and exercises SQLite WAL recovery.
        child = """
import json, os, sys
from unittest.mock import patch
from oscar.cloud import CloudConfig, CloudCore
core = CloudCore(CloudConfig.load(__import__('pathlib').Path(sys.argv[1])))
proof = json.loads(sys.argv[2])
phase = sys.argv[3]
original = core.harness.store.put
def write(kind, identifier, value):
    original(kind, identifier, value)
    if kind == phase:
        os._exit(73)
if phase == 'burn':
    core.harness.grid.pair = lambda *a, **k: os._exit(73)
elif phase == 'reply':
    core.remote.session_view = lambda *a: os._exit(73)
else:
    core.harness.store.put = write
core.remote.enroll(proof)
os._exit(74)
"""
        for recover, phase in product(
            (False, True), ("burn", "node", "session", "remote_device", "reply")
        ):
            with self.subTest(recover=recover, phase=phase):
                proof = self.proof(recover=recover)
                if recover:
                    self.core.harness.grid.disconnect("atomic-mobile")
                before = self.authority()
                self.core.close()
                process = subprocess.run(
                    [sys.executable, "-c", child, str(self.config_path), json.dumps(proof), phase],
                    capture_output=True,
                    timeout=30,
                )
                self.assertEqual(process.returncode, 73, process.stderr.decode())
                self.core = CloudCore(self.config)
                self.assert_burned(proof)
                state = self.authority()
                if phase == "reply":
                    self.assertEqual(len(state["node"]), 1)
                    self.assertEqual(len(state["session"]), len(before["session"]) + 1)
                    current = [row for row in state["session"] if not row["revoked"]]
                    self.assertEqual(len(current), 1)
                    self.assertEqual(state["remote_device"][0]["session_id"], current[0]["id"])
                    self.assertNotIn("token", current[0])
                    old_id = current[0]["id"]
                    fresh = self.core.remote.enroll(self.proof(recover=True))
                    self.assertNotEqual(fresh["session_id"], old_id)
                    self.assertTrue(self.core.harness.store.get("session", old_id)["revoked"])
                else:
                    self.assertEqual(state, before)

    def test_commit_failure_rolls_back_authority_and_connection_remains_usable(self):
        old = self.core.remote.enroll(self.proof())
        proof = self.proof(recover=True)
        before = self.authority()
        db = self.core.harness.store.db

        def authorize(operation, argument, *_):
            if operation == sqlite3.SQLITE_TRANSACTION and argument == "COMMIT":
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        pair = self.core.harness.grid.pair

        def fail_commit(*args, **kwargs):
            db.set_authorizer(authorize)
            return pair(*args, **kwargs)

        try:
            with (
                patch.object(self.core.harness.grid, "pair", side_effect=fail_commit),
                self.assertRaises(sqlite3.DatabaseError),
            ):
                self.core.remote.enroll(proof)
        finally:
            db.set_authorizer(None)
        self.assertFalse(db.in_transaction)
        self.assertEqual(self.authority(), before)
        self.assert_burned(proof)
        self.restart()
        self.assertEqual(self.authority(), before)
        DirectClient(self.core, old).request("snapshot", {})

    def test_recovery_and_rotation_race_fences_every_old_session(self):
        old = self.core.remote.enroll(self.proof())
        proof = self.proof(recover=True)
        client = DirectClient(self.core, old)

        def rotate():
            try:
                return client.request("rotate", {})
            except PermissionError:
                return None

        with ThreadPoolExecutor(2) as executor:
            rotation = executor.submit(rotate)
            enrollment = executor.submit(self.core.remote.enroll, proof)
            rotated, fresh = rotation.result(), enrollment.result()
        DirectClient(self.core, fresh).request("snapshot", {})
        for stale in (old, rotated):
            if stale:
                with self.assertRaises(PermissionError):
                    DirectClient(self.core, stale).request("snapshot", {})
        self.assertEqual(sum(not row["revoked"] for row in self.authority()["session"]), 1)

    def test_revocation_invalidates_pending_recovery_even_if_cleanup_crashes(self):
        session = self.core.remote.enroll(self.proof())
        proof = self.proof(recover=True)
        with patch.object(self.core.harness.grid, "revoke", side_effect=OSError):
            with self.assertRaises(OSError):
                DirectClient(self.core, session).request("revoke", {})
        self.restart()
        self.assert_burned(proof)
        state = self.authority()
        self.assertTrue(state["node"][0]["revoked"])
        self.assertTrue(all(row["revoked"] for row in state["session"]))
        with self.assertRaises(PermissionError):
            DirectClient(self.core, session).request("snapshot", {})
        fresh = self.core.remote.enroll(self.proof(recover=True))
        DirectClient(self.core, fresh).request("snapshot", {})
