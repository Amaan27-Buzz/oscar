import json
import unittest
from dataclasses import replace

from oscar.capabilities import FileExecutor
from oscar.commissioning import Commissioning, CommissioningPlan
from oscar.contracts import TaskState
from oscar.grid import Grid
from oscar.jev import Intent
from oscar.storage import StateConflict, Store
from tests.support import Rig


class CommissioningTests(unittest.TestCase):
    def setUp(self):
        self.rig = Rig()
        self.commissioning = Commissioning(self.rig.grid, "synthetic-owner")
        self.plan = CommissioningPlan(
            "test-node", ("heartbeat", "advertise", "math"), perceive=True, retain=False, act=False
        )

    def tearDown(self):
        self.rig.close()

    def begin(self, **kwargs):
        return self.commissioning.begin(self.plan, owner_authorized=True, **kwargs)

    def test_initialization_is_idempotent_and_relationship_bound(self):
        identity = self.commissioning.initialize(owner_authorized=True)
        self.assertEqual(identity, self.commissioning.initialize(owner_authorized=True))
        with self.assertRaises(PermissionError):
            Commissioning(self.rig.grid, "another-owner").initialize(owner_authorized=True)
        with self.assertRaises(PermissionError):
            self.commissioning.initialize(owner_authorized=False)

    def test_configured_is_not_operational_before_advertisement_or_without_handle(self):
        enrollment = self.begin()
        view = self.commissioning.inspect(enrollment["id"])
        self.assertFalse(view["configured"])
        self.assertFalse(view["operational"])
        session = self.commissioning.pair(
            enrollment["id"], enrollment["review_digest"], owner_authorized=True
        )
        self.rig.grid.disconnect("test-node")
        self.assertFalse(self.commissioning.inspect(enrollment["id"], session)["operational"])
        self.rig.grid.advertise(session, self.rig.caps)
        view = self.commissioning.inspect(enrollment["id"], session)
        self.assertTrue(view["configured"])
        self.assertTrue(view["operational"])
        self.assertTrue(view["simulated"])
        self.assertEqual(["math"], view["capability_ids"])
        self.assertEqual(
            {"perceive": True, "retain": False, "act": False}, view["requested_grants"]
        )
        self.assertIn("voice", view["remaining"])
        self.assertFalse(self.commissioning.inspect(enrollment["id"])["operational"])
        data = self.rig.store.get("session", session.id)
        self.rig.store.put("session", session.id, {**data, "scopes": ["heartbeat"]})
        self.assertEqual(
            [], self.commissioning.inspect(enrollment["id"], session)["capability_ids"]
        )

    def test_exact_review_expiry_and_replay_are_enforced(self):
        enrollment = self.begin(ttl_seconds=2)
        for authorized, digest in ((False, enrollment["review_digest"]), (True, "wrong")):
            with self.assertRaises((PermissionError, StateConflict)):
                self.commissioning.pair(enrollment["id"], digest, owner_authorized=authorized)
        self.rig.clock.now += 3
        with self.assertRaises(StateConflict):
            self.commissioning.pair(
                enrollment["id"], enrollment["review_digest"], owner_authorized=True
            )
        self.assertEqual(1, self.commissioning.recover())
        self.assertEqual("expired", self.commissioning.inspect(enrollment["id"])["state"])

    def test_review_binds_exact_scopes_and_core_device_identity(self):
        enrollment = self.begin()
        self.rig.store.put(
            "commissioning",
            enrollment["id"],
            {**enrollment, "scopes": ["heartbeat", "execute", "math"]},
        )
        with self.assertRaises(StateConflict):
            self.commissioning.pair(
                enrollment["id"], enrollment["review_digest"], owner_authorized=True
            )

    def test_scope_expansion_and_inferred_action_authority_are_rejected(self):
        with self.assertRaises(PermissionError):
            self.commissioning.begin(
                replace(self.plan, scopes=("heartbeat", "unavailable")), owner_authorized=True
            )
        with self.assertRaises(PermissionError):
            replace(self.plan, scopes=("heartbeat", "execute"))
        with self.assertRaises(PermissionError):
            self.commissioning.begin(self.plan, owner_authorized=False)
        for kwargs in ({"version": True}, {"perceive": 1}, {"scopes": ["heartbeat"]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.plan, **kwargs)
        with self.assertRaises(ValueError):
            replace(self.plan, scopes=("heartbeat", "ghp_" + "x" * 30))

    def test_pending_setup_resumes_after_actual_store_restart_without_tokens(self):
        enrollment = self.begin()
        path = self.rig.store.db.execute("PRAGMA database_list").fetchone()[2]
        self.rig.store.close()
        self.rig.store = Store(path)
        self.rig.grid = Grid(self.rig.store, self.rig.clock)
        self.commissioning = Commissioning(self.rig.grid, "synthetic-owner")
        self.assertEqual("review_pending", self.commissioning.inspect(enrollment["id"])["state"])
        session = self.commissioning.pair(
            enrollment["id"], enrollment["review_digest"], owner_authorized=True
        )
        self.rig.grid.authenticate(session, "math")
        durable = json.dumps(self.rig.store.all("commissioning") + self.rig.store.all("session"))
        self.assertNotIn(session.token, durable)
        self.assertNotIn("token", json.dumps(self.rig.store.all("commissioning")))

    def test_partial_pairing_failure_revokes_owned_session_without_replay(self):
        enrollment = self.begin()
        put = self.rig.store.put

        def fail_after_pair(kind, identifier, value):
            if kind == "commissioning" and value["state"] == "paired":
                raise OSError("synthetic interruption after Grid pairing")
            put(kind, identifier, value)

        self.rig.store.put = fail_after_pair
        with self.assertRaises(OSError):
            self.commissioning.pair(
                enrollment["id"], enrollment["review_digest"], owner_authorized=True
            )
        self.rig.store.put = put
        self.assertEqual(0, self.commissioning.recover())
        self.rig.clock.now += 31
        self.assertEqual(1, self.commissioning.recover())
        self.assertTrue(self.rig.store.get("session", enrollment["session_id"])["revoked"])
        self.assertEqual("blocked", self.commissioning.inspect(enrollment["id"])["state"])
        with self.assertRaises(StateConflict):
            self.commissioning.pair(
                enrollment["id"], enrollment["review_digest"], owner_authorized=True
            )

    def test_revocation_between_pairing_and_finalization_cannot_leave_usable_session(self):
        enrollment = self.begin()
        pair = self.rig.grid.pair

        def revoke_between(*args, **kwargs):
            # Emulate another coordinator revoking the pending review before pair commits.
            self.commissioning.revoke(enrollment["id"], owner_authorized=True)
            return pair(*args, **kwargs)

        self.rig.grid.pair = revoke_between
        with self.assertRaises(StateConflict):
            self.commissioning.pair(
                enrollment["id"], enrollment["review_digest"], owner_authorized=True
            )
        self.assertTrue(self.rig.store.get("session", enrollment["session_id"])["revoked"])

    def test_revocation_denies_execution_without_affecting_unrelated_session(self):
        self.plan = replace(
            self.plan, act=True, scopes=("heartbeat", "advertise", "execute", "math")
        )
        enrollment = self.begin()
        session = self.commissioning.pair(
            enrollment["id"], enrollment["review_digest"], owner_authorized=True
        )
        self.rig.grid.advertise(session, [self.rig.caps[1]])
        task = self.rig.runtime.create(Intent("2 + 3"))
        result = self.rig.runtime.run(task.id, {"test-node": (self.rig.dispatcher, session)})
        self.assertEqual(TaskState.VERIFIED, result.state)
        self.commissioning.revoke(enrollment["id"], owner_authorized=True)
        with self.assertRaises(PermissionError):
            self.rig.grid.authenticate(session, "execute")
        self.rig.grid.authenticate(self.rig.session, "execute")
        self.assertEqual("revoked", self.commissioning.inspect(enrollment["id"])["state"])

    def test_cross_device_handle_relationship_and_duplicate_pairing_rejected(self):
        enrollment = self.begin()
        with self.assertRaises(PermissionError):
            self.commissioning.inspect(enrollment["id"], self.rig.session)
        with self.assertRaises(PermissionError):
            Commissioning(self.rig.grid, "other").inspect(enrollment["id"])
        session = self.commissioning.pair(
            enrollment["id"], enrollment["review_digest"], owner_authorized=True
        )
        with self.assertRaises(StateConflict):
            self.commissioning.pair(
                enrollment["id"], enrollment["review_digest"], owner_authorized=True
            )
        with self.assertRaises(StateConflict):
            self.rig.grid.pair("test-node", ("heartbeat",), session_id=session.id)
        self.rig.grid.authenticate(session, "heartbeat")

    def test_inflight_revocation_stops_executor_before_file_mutation(self):
        self.plan = replace(
            self.plan, act=True, scopes=("heartbeat", "advertise", "execute", "files:write")
        )
        enrollment = self.begin()
        session = self.commissioning.pair(
            enrollment["id"], enrollment["review_digest"], owner_authorized=True
        )
        self.rig.grid.advertise(session, [self.rig.caps[0]])
        original = FileExecutor(self.rig.files)

        def revoke_before_write(action, cancellation):
            self.commissioning.revoke(enrollment["id"], owner_authorized=True)
            cancellation.check()
            return original(action, cancellation)

        self.rig.dispatcher.executors["file"] = revoke_before_write
        task = self.rig.file_task("revoked.txt", "must not exist")
        result = self.rig.runtime.run(task.id, {"test-node": (self.rig.dispatcher, session)})
        self.assertNotEqual(TaskState.VERIFIED, result.state)
        self.assertFalse((self.rig.files.root / "revoked.txt").exists())
        self.rig.grid.authenticate(self.rig.session, "execute")
