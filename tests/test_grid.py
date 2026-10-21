import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from threading import Event, current_thread

from oscar.contracts import Envelope, TaskState, new_id, record
from oscar.grid import Availability, Grid, Node, NodeRole, SessionHandle, reconnect_delay
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

    def test_remote_executor_expires_while_control_surface_remains_connected(self):
        r = self.r
        r.grid.advertise(r.session, r.caps, executor=True)
        task, _, envelope = r.leased_action()
        r.grid.renew(envelope.lease_id, r.session, ttl=120)
        r.clock.now += 31
        r.grid.heartbeat(r.session)
        self.assertEqual("online", r.grid.nodes()[0]["status"])
        self.assertEqual([], r.grid.search("file_write"))
        with self.assertRaises(StateConflict):
            r.grid.renew(envelope.lease_id, r.session)
        with self.assertRaises(PermissionError):
            r.grid.accept(replace(envelope, sent_at=r.clock()), r.session.token, "execute")
        unleased = r.file_task("next.txt")
        self.assertEqual(TaskState.BLOCKED, unleased.state)
        with self.assertRaises(StateConflict):
            r.grid.lease(task.id, "test-node")
        r.grid.executor_heartbeat(r.session)
        self.assertEqual(TaskState.BLOCKED, r.store.task(task.id).state)
        self.assertFalse(r.store.get("lease", envelope.lease_id)["active"])
        self.assertEqual(["file"], [c.id for c in r.grid.search("file_write")])
        with self.assertRaises(PermissionError):
            r.grid.accept(replace(envelope, sent_at=r.clock()), r.session.token, "execute")

    def test_remote_executor_session_cannot_be_replaced_by_ui_heartbeat(self):
        r = self.r
        r.grid.advertise(r.session, r.caps, executor=True)
        replacement = r.grid.pair("test-node", r.scopes)
        with self.assertRaises(PermissionError):
            r.grid.executor_heartbeat(replacement)
        old = r.store.get("session", r.session.id)
        r.store.put("session", r.session.id, {**old, "revoked": True})
        r.grid.heartbeat(replacement)
        self.assertEqual([], r.grid.search("file_write"))
        with self.assertRaises(PermissionError):
            r.grid.executor_heartbeat(r.session)
        r.grid.advertise(replacement, r.caps, executor=True)
        self.assertEqual(["file"], [c.id for c in r.grid.search("file_write")])

    def test_background_disconnect_cannot_overwrite_concurrent_pairing(self):
        self.r.grid.register(Node("pairing", NodeRole.DESKTOP, ("heartbeat",)))
        other = Store(self.r.root / "state.sqlite")
        self.addCleanup(other.close)
        entered, release, paired = Event(), Event(), Event()
        original = self.r.store.get
        intercepted = []

        def hold(kind, identifier):
            row = original(kind, identifier)
            if (
                kind == "node"
                and identifier == "pairing"
                and current_thread().name.startswith("disconnect")
                and not intercepted
            ):
                intercepted.append(True)
                entered.set()
                if not release.wait(2):
                    raise OSError("test synchronization expired")
            return row

        self.r.store.get = hold

        def pair():
            Grid(other, self.r.clock).pair("pairing", ("heartbeat",))
            paired.set()

        with (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="disconnect") as disconnecting,
            ThreadPoolExecutor(max_workers=1) as pairing,
        ):
            first = disconnecting.submit(self.r.grid.disconnect, "pairing")
            self.assertTrue(entered.wait(1))
            second = pairing.submit(pair)
            paired.wait(0.2)
            release.set()
            first.result(timeout=3)
            second.result(timeout=3)
        self.assertTrue(self.r.store.get("node", "pairing")["paired"])

    def test_stale_reaper_snapshot_does_not_disconnect_a_recovered_node(self):
        self.r.clock.now += 31
        stale = self.r.grid.nodes()
        self.r.grid.heartbeat(self.r.session)
        self.r.grid.advertise(self.r.session, self.r.caps)
        self.r.grid.disconnect(stale[0]["id"], only_if_stale=True)
        self.assertEqual(3, len(self.r.grid.nodes()[0]["capabilities"]))

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

    def test_disconnect_does_not_block_a_new_lease_after_reconnect(self):
        r = self.r
        old_task, _, _ = r.leased_action()
        original = r.store.transaction
        recovered = []

        @contextmanager
        def reconnect_after_commit():
            with original():
                yield
            r.store.transaction = original
            r.grid.advertise(r.session, r.caps)
            recovered.append(r.leased_action()[0])

        r.store.transaction = reconnect_after_commit
        r.grid.disconnect("test-node")
        self.assertEqual(TaskState.BLOCKED, r.store.task(old_task.id).state)
        self.assertEqual(TaskState.AWAITING_RESULT, r.store.task(recovered[0].id).state)

    def test_missing_heartbeat_makes_node_offline_and_task_blocked(self):
        task, _, _ = self.r.leased_action()
        self.r.clock.now += 31
        self.r.grid.reap()
        self.assertEqual(self.r.grid.nodes()[0]["status"], "offline")
        self.assertEqual(self.r.store.task(task.id).state, TaskState.BLOCKED)

    def test_reaper_fences_task_before_releasing_expired_ownership(self):
        r = self.r
        task, _, _ = r.leased_action()
        r.clock.now += 21
        original = r.grid.release
        observed = []

        def release(lease_id):
            observed.append(r.store.task(task.id).state)
            original(lease_id)

        r.grid.release = release
        r.grid.reap()
        self.assertEqual([TaskState.BLOCKED], observed)

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

    def test_mobile_role_preserves_legacy_availability(self):
        r = self.r
        for role in (NodeRole.CLOUD, NodeRole.MOBILE, NodeRole.EDGE):
            node_id = role.value.lower().replace(" ", "-")
            r.grid.register(Node(node_id, role, ("heartbeat",)))
            r.grid.heartbeat(r.grid.pair(node_id, ("heartbeat",)))
        self.assertEqual(r.grid.availability(), Availability.FULL)
