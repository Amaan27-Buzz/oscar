"""Actual scoped filesystem effects and execution-only crash/replay fencing."""

import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from unittest.mock import patch

from oscar.contracts import Action, new_id, record
from oscar.mobile import fingerprint
from oscar.remote_worker import RemoteWorker
from oscar.storage import StateConflict


class FixtureClient:
    session = {"node_id": "desktop", "session_id": "current-session"}

    def __init__(self):
        self.authorized = True
        self.delivery = None
        self.receipts = []

    def request(self, operation, payload, request_id=None):
        if operation == "check":
            if not self.authorized:
                raise PermissionError("fixture revoked")
            return {"authorized": True}
        if operation == "poll":
            return {"delivery": self.delivery}
        if operation == "deliver":
            self.receipts.append(payload)
        return {}


class RemoteWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.client = FixtureClient()
        self.worker = RemoteWorker(
            self.client, self.workspace, "disposable", self.root / "claims.sqlite"
        )

    def tearDown(self):
        self.worker.close()
        self.temp.cleanup()

    def test_registration_recovery_never_accepts_a_claimed_delivery_or_coerced_flag(self):
        for response in (
            {"delivery": {}, "advertise_required": True},
            {"delivery": None, "advertise_required": "true"},
            {"delivery": None, "advertise_required": True, "extra": True},
        ):
            with (
                self.subTest(response=response),
                patch.object(self.client, "request", return_value=response),
                patch.object(self.worker, "advertise") as advertise,
                patch.object(self.worker, "execute") as execute,
                self.assertRaises(PermissionError),
            ):
                self.worker.step()
            advertise.assert_not_called()
            execute.assert_not_called()

    def delivery(self, write=True):
        action = Action(
            new_id(),
            new_id(),
            new_id(),
            "machine.files.write" if write else "machine.files.read",
            {"path": "proof.txt", **({"content": "actual\n"} if write else {})},
            new_id(),
            "owner",
        )
        deadline = int(time() * 1000) + 60_000
        return {
            "id": new_id(),
            "kind": "action",
            "node_id": "desktop",
            "session_id": "current-session",
            "task_id": action.task_id,
            "action": record(action),
            "lease_id": new_id(),
            "deadline_ms": deadline,
            "workspace": "disposable",
            "approved": write,
            "parameters": action.parameters,
            "review_digest": fingerprint(
                {
                    "action": record(action),
                    "target": "desktop",
                    "workspace": "disposable",
                    "deadline_ms": deadline,
                }
            ),
        }

    def test_actual_write_read_independent_readback_and_duplicate_no_effect(self):
        delivery = self.delivery()
        result = self.worker.execute(delivery)
        self.assertTrue(result["success"])
        self.assertEqual("actual\n", (self.workspace / "proof.txt").read_text())
        self.assertNotIn(str(self.workspace), json.dumps(result))
        (self.workspace / "proof.txt").write_text("independent change")
        self.assertEqual(result, self.worker.execute(delivery))
        self.assertEqual("independent change", (self.workspace / "proof.txt").read_text())
        delivery["kind"] = "readback"
        delivery["parameters"] = {"path": "proof.txt"}
        self.assertEqual({"content": "independent change"}, self.worker.execute(delivery))
        read = self.worker.execute(self.delivery(False))
        self.assertEqual("independent change", read["value"])

    def test_target_session_scope_digest_expiry_and_ask_rejected(self):
        for field, value in (
            ("node_id", "other"),
            ("session_id", "old"),
            ("workspace", "outside"),
            ("deadline_ms", 1),
            ("approved", False),
            ("review_digest", "tampered"),
        ):
            with self.subTest(field=field):
                delivery = self.delivery()
                delivery[field] = value
                with self.assertRaises(PermissionError):
                    self.worker.execute(delivery)
                self.assertFalse((self.workspace / "proof.txt").exists())

    def test_revocation_before_replace_preserves_original(self):
        (self.workspace / "proof.txt").write_text("before")
        with patch.object(self.worker.files, "write", wraps=self.worker.files.write) as write:
            self.client.authorized = False
            with self.assertRaises(PermissionError):
                self.worker.execute(self.delivery())
            write.assert_not_called()
        self.assertEqual("before", (self.workspace / "proof.txt").read_text())

    def test_claim_survives_process_reopen_and_never_replays_uncertain_write(self):
        delivery = self.delivery()
        with patch.object(self.worker.files, "write", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                self.worker.execute(delivery)
        self.worker.close()
        self.worker = RemoteWorker(
            self.client, self.workspace, "disposable", self.root / "claims.sqlite"
        )
        with self.assertRaisesRegex(StateConflict, "UNKNOWN"):
            self.worker.execute(delivery)
        self.assertFalse((self.workspace / "proof.txt").exists())

    def test_changed_canonical_action_or_readback_target_rejected(self):
        delivery = self.delivery()
        self.worker.execute(delivery)
        changed = copy.deepcopy(delivery)
        changed["kind"] = "readback"
        changed["parameters"] = {"path": "other.txt"}
        with self.assertRaises(PermissionError):
            self.worker.execute(changed)
        changed = copy.deepcopy(delivery)
        changed["action"]["parameters"]["content"] = "changed"
        with self.assertRaises(PermissionError):
            self.worker.execute(changed)

    def test_scope_escape_never_modifies_outside(self):
        delivery = self.delivery()
        delivery["action"]["parameters"]["path"] = "../outside.txt"
        delivery["review_digest"] = fingerprint(
            {
                "action": delivery["action"],
                "target": "desktop",
                "workspace": "disposable",
                "deadline_ms": delivery["deadline_ms"],
            }
        )
        with self.assertRaises((PermissionError, ValueError)):
            self.worker.execute(delivery)
        self.assertFalse((self.root / "outside.txt").exists())

    def test_journal_cannot_be_remote_writable(self):
        with self.assertRaises(ValueError):
            RemoteWorker(
                self.client, self.workspace, "disposable", self.workspace / "claims.sqlite"
            )

    def test_local_policy_is_independent_of_cloud_approval(self):
        self.worker.local_authorize = lambda action: False
        with self.assertRaisesRegex(PermissionError, "local Personal Policy"):
            self.worker.execute(self.delivery())
        self.assertFalse((self.workspace / "proof.txt").exists())


if __name__ == "__main__":
    unittest.main()
