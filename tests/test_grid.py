import unittest
from dataclasses import replace

from oscar.contracts import Envelope, TaskState, new_id, record
from oscar.grid import Availability, Node, NodeRole, SessionHandle, reconnect_delay
from oscar.storage import StateConflict, Store

from .support import Rig


class GridTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.addCleanup(self.r.close)

    def test_reference_node_advertises_searchable_real_capability(self):
        capabilities = self.r.grid.search("file_write")
        self.assertEqual([c.id for c in capabilities], ["file"])
        node = self.r.grid.nodes()[0]
        self.assertEqual(node["role"], "Desktop")
        self.assertTrue(node["paired"])
        self.assertEqual(node["protocol_version"], 1)
        self.assertIsNotNone(node["last_seen"])

    def test_disconnect_preserves_task_and_expires_lease(self):
        r = self.r
        task, _, envelope = r.leased_action()
        r.grid.disconnect("test-node")
        self.assertEqual(r.store.task(task.id).state, TaskState.BLOCKED)
        self.assertEqual(r.grid.search("file_write"), [])
        self.assertTrue(r.store.get("objective", task.objective_id))
        with self.assertRaises(StateConflict):
            r.runtime.reclaim(task.id)
        r.clock.now += 21
        self.assertEqual(r.grid.reap(), [task.id])
        self.assertFalse(r.store.get("lease", envelope.lease_id)["active"])
        self.assertEqual(r.store.task(task.id).state, TaskState.BLOCKED)
        self.assertEqual(r.runtime.reclaim(task.id).state, TaskState.PLANNED)

    def test_missing_heartbeat_makes_node_offline_and_task_blocked(self):
        task, _, _ = self.r.leased_action()
        self.r.clock.now += 31
        self.r.grid.reap()
        self.assertEqual(self.r.grid.nodes()[0]["status"], "offline")
        self.assertEqual(self.r.store.task(task.id).state, TaskState.BLOCKED)

    def test_reconnect_requires_readvertisement(self):
        r = self.r
        r.grid.disconnect("test-node")
        r.grid.heartbeat(r.session)
        self.assertEqual(r.grid.search("file_write"), [])
        r.grid.advertise(r.session, r.caps)
        self.assertEqual(len(r.grid.search("file_write")), 1)

    def test_revoke_denies_sessions_and_removes_live_capabilities(self):
        r = self.r
        r.grid.revoke("test-node")
        with self.assertRaises(PermissionError):
            r.grid.heartbeat(r.session)
        self.assertEqual(r.grid.search("file_write"), [])

    def test_revoke_cancels_owned_work_and_releases_lease(self):
        r = self.r
        task, _, envelope = r.leased_action()
        r.grid.revoke("test-node")
        self.assertEqual(r.store.task(task.id).state, TaskState.CANCELLED)
        self.assertFalse(r.store.get("lease", envelope.lease_id)["active"])

    def test_wrong_token_rejected_without_echo(self):
        r = self.r
        invalid = SessionHandle(r.session.id, r.session.node_id, "synthetic-invalid-token")
        with self.assertRaises(PermissionError) as caught:
            r.grid.heartbeat(invalid)
        self.assertEqual(str(caught.exception), "session/scope denied")
        self.assertNotIn(r.session.token, repr(r.session))
        import pickle
        from dataclasses import asdict

        with self.assertRaises(TypeError):
            asdict(r.session)
        with self.assertRaises(TypeError):
            pickle.dumps(r.session)

    def test_expired_session_cannot_heartbeat(self):
        self.r.clock.now += 3601
        with self.assertRaises(PermissionError):
            self.r.grid.heartbeat(self.r.session)

    def test_pairing_cannot_expand_scope(self):
        with self.assertRaises(PermissionError):
            self.r.grid.pair("test-node", ("owner:unrestricted",))

    def test_advertisement_cannot_claim_another_identity(self):
        r = self.r
        forged = replace(r.caps[0], node_id="other-node")
        with self.assertRaises(PermissionError):
            r.grid.advertise(r.session, [forged])

    def test_lease_is_single_owner_and_bounded(self):
        r = self.r
        task, _, _ = r.leased_action()
        with self.assertRaises(StateConflict):
            r.grid.lease(task.id, "test-node")
        with self.assertRaises(ValueError):
            r.grid.lease(task.id, "test-node", ttl=999999)

    def test_expired_lease_cannot_execute(self):
        r = self.r
        _, _, envelope = r.leased_action()
        r.clock.now += 21
        with self.assertRaises(PermissionError):
            r.dispatcher.invoke(replace(envelope, sent_at=r.clock()), r.session)
        self.assertFalse((r.files.root / "proof.txt").exists())

    def test_mismatched_correlation_is_rejected(self):
        r = self.r
        _, _, envelope = r.leased_action()
        with self.assertRaises(PermissionError):
            r.dispatcher.invoke(replace(envelope, correlation_id=new_id()), r.session)

    def test_untrusted_protocol_version_time_and_fields(self):
        _, _, envelope = self.r.leased_action()
        data = record(envelope)
        for changed in (
            {**data, "version": 99},
            {**data, "unexpected": "bad"},
            {**data, "task_id": []},
        ):
            with self.assertRaises(ValueError):
                Envelope.parse(changed)
        for timestamp in (float("nan"), float("inf"), self.r.clock() - 61):
            with self.assertRaises(PermissionError):
                self.r.grid.accept(
                    replace(envelope, sent_at=timestamp, nonce=new_id()),
                    self.r.session.token,
                    "execute",
                )

    def test_progress_is_correlated_and_replay_protected(self):
        r = self.r
        task, _, envelope = r.leased_action()
        progress = replace(envelope, kind="progress", nonce=new_id(), payload={"fraction": 0.5})
        r.grid.progress(progress, r.session.token, 0.5)
        self.assertEqual(r.store.ledger(task.id)[-1]["fraction"], 0.5)
        with self.assertRaises(StateConflict):
            r.grid.progress(progress, r.session.token, 0.5)

    def test_durable_node_and_lease_after_coordinator_restart(self):
        r = self.r
        task, _, envelope = r.leased_action()
        second = Store(r.root / "state.sqlite")
        self.addCleanup(second.close)
        self.assertTrue(second.get("node", "test-node")["paired"])
        self.assertEqual(second.get("lease", envelope.lease_id)["task_id"], task.id)

    def test_all_five_availability_levels(self):
        r = self.r
        self.assertEqual(r.grid.availability(), Availability.LOCAL)
        for role in (NodeRole.CLOUD, NodeRole.SUNDAY, NodeRole.EDGE):
            node_id = role.value.lower()
            r.grid.register(Node(node_id, role, ("heartbeat",)))
            r.grid.heartbeat(r.grid.pair(node_id, ("heartbeat",)))
        self.assertEqual(r.grid.availability(), Availability.FULL)
        r.grid.disconnect("test-node")
        self.assertEqual(r.grid.availability(), Availability.CONNECTED)
        r.grid.disconnect("cloud")
        self.assertEqual(r.grid.availability(), Availability.LOCAL)
        r.grid.disconnect("sunday")
        self.assertEqual(r.grid.availability(), Availability.REFLEX_ONLY)
        r.grid.disconnect("edge")
        self.assertEqual(r.grid.availability(), Availability.OFFLINE)

    def test_reconnect_backoff_has_a_budget(self):
        self.assertEqual(reconnect_delay(0), 0.25)
        self.assertEqual(reconnect_delay(10), 30)
        with self.assertRaises(ValueError):
            reconnect_delay(21)
