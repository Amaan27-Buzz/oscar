import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from oscar.capabilities import FileExecutor
from oscar.executive import Executive
from oscar.grid import Grid, SessionHandle
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.storage import StateConflict, Store
from tests.support import Clock, Rig


class InternalSessionTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.addCleanup(self.r.close)
        self.r.session = self.r.grid.pair("test-node", self.r.scopes, internal=True)
        self.r.transports["test-node"] = (self.r.dispatcher, self.r.session)

    def test_scheduled_verified_execution_at_one_two_eight_and_twenty_four_hours(self):
        r = self.r
        executive = Executive(r.runtime, r.transports)
        self.addCleanup(executive.close)
        worker = executive.worker(
            "Uptime", [("test-node", "file")], ("files:write",), owner_authorized=True
        )
        goal = executive.propose(
            worker,
            "Hourly exact file",
            [
                {
                    "id": "file",
                    "intent": asdict(Intent("Write", "file_write", "hourly.txt", "exact")),
                    "depends_on": [],
                    "node_id": "test-node",
                    "capability_id": "file",
                }
            ],
            interval_seconds=3600,
            max_runs=25,
        )
        executive.accept(goal["id"], goal["review_digest"], owner_authorized=True)
        old = SessionHandle(r.session.id, r.session.node_id, r.session.token)
        start = r.clock()
        for minute in range(0, 24 * 60 + 1, 5):
            r.clock.now = start + minute * 60
            r.grid.maintain_internal(r.session)
            executive.tick()
            if minute in {60, 120, 480, 1440}:
                self.assertEqual(
                    minute // 60 + 1, r.store.get("executive_goal", goal["id"])["run_index"]
                )
                self.assertEqual(minute // 60 + 1, len(r.store.all("action")))
                self.assertTrue(all(t["state"] == "verified" for t in r.store.all("task")))
                r.grid.authenticate(r.session, "files:write")
        self.assertEqual(b"exact", r.files.read("hourly.txt"))
        self.assertEqual(
            25,
            r.store.db.execute("SELECT count(*) FROM dedup WHERE state='completed'").fetchone()[0],
        )
        self.assertGreaterEqual(r.store.get("session", r.session.id)["generation"], 24)
        with self.assertRaises(PermissionError):
            r.grid.maintain_internal(old)
        row = r.store.get("session", r.session.id)
        waiting = executive.propose(
            worker,
            "Denied after revocation",
            [
                {
                    "id": "file",
                    "intent": asdict(Intent("Write", "file_write", "denied.txt", "never")),
                    "depends_on": [],
                    "node_id": "test-node",
                    "capability_id": "file",
                }
            ],
        )
        executive.accept(waiting["id"], waiting["review_digest"], owner_authorized=True)
        r.store.put("session", r.session.id, {**row, "revoked": True})
        with self.assertRaises(PermissionError):
            r.grid.maintain_internal(r.session)
        r.clock.now += 3600
        executive.tick()
        self.assertEqual(25, len(r.store.all("action")))
        self.assertFalse((r.files.root / "denied.txt").exists())
        self.assertNotEqual("completed", r.store.get("executive_goal", waiting["id"])["state"])

    def test_rotation_preserves_only_already_leased_work(self):
        r = self.r
        r.clock.now += 2699
        captured = SessionHandle(r.session.id, r.session.node_id, r.session.token)
        r.grid.heartbeat(captured)
        writes = []
        original = FileExecutor(r.files)

        def execute(action, cancellation):
            r.clock.now += 1
            r.grid.maintain_internal(r.session)
            cancellation.check()
            writes.append(action.id)
            return original(action, cancellation)

        r.dispatcher.executors["file"] = execute
        task = r.file_task()
        outcome = r.runtime.run(task.id, {"test-node": (r.dispatcher, captured)})
        self.assertEqual("verified", outcome.state)
        self.assertEqual(1, len(writes))
        with self.assertRaises(PermissionError):
            r.grid.authenticate(captured, "execute")
        r.grid.authenticate(r.session, "execute")
        self.assertEqual("verified", r.runtime.run(task.id, r.transports).state)
        self.assertEqual(1, len(writes))

    def test_competing_rotation_cannot_reuse_an_old_credential(self):
        r = self.r
        second = Store(r.root / "state.sqlite")
        self.addCleanup(second.close)
        copy = SessionHandle(r.session.id, r.session.node_id, r.session.token)
        r.clock.now += 2700

        def rotate(grid, handle):
            try:
                grid.maintain_internal(handle)
                return True
            except PermissionError:
                return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(
                    lambda pair: rotate(*pair), [(r.grid, r.session), (Grid(second, r.clock), copy)]
                )
            )
        self.assertEqual([False, True], sorted(results))
        self.assertEqual(1, r.store.get("session", copy.id)["generation"])

    def test_expiry_revocation_scopes_and_enrollment_limit_fail_closed(self):
        r = self.r
        r.clock.now += 3600
        with self.assertRaises(PermissionError):
            r.grid.maintain_internal(r.session)
        with self.assertRaises(PermissionError):
            r.grid.pair("test-node", r.scopes, internal=True)
        current = r.grid.pair("test-node", ("heartbeat", "math"), internal=True, reenroll=True)
        with self.assertRaises(PermissionError):
            r.grid.authenticate(current, "files:write")
        row = r.store.get("session", current.id)
        r.store.put("session", current.id, {**row, "renew_until": r.clock()})
        with self.assertRaises(PermissionError):
            r.grid.maintain_internal(current)
        r.grid.revoke("test-node")
        with self.assertRaises(PermissionError):
            r.grid.pair("test-node", r.scopes, internal=True, reenroll=True)

    def test_rotation_drain_bound_never_silently_truncates_active_authority(self):
        r = self.r
        r.clock.now += 2700
        with r.store.transaction():
            for index in range(257):
                r.store.put(
                    "lease",
                    f"synthetic-{index}",
                    {
                        "id": f"synthetic-{index}",
                        "node_id": "test-node",
                        "active": True,
                        "expires_at": r.clock() + 120,
                    },
                )
        with self.assertRaises(StateConflict):
            r.grid.maintain_internal(r.session)
        self.assertEqual(0, r.store.get("session", r.session.id)["generation"])
        r.grid.authenticate(r.session, "execute")

    def test_real_harness_restart_and_expired_enrollment_recovery(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            clock = Clock()
            args = root / "core.sqlite", root / "files", Path("config/development-models.json")
            with Harness(*args, clock=clock) as first:
                task = first.runtime.create(Intent("Write", "file_write", "proof.txt", "once"))
                self.assertEqual(
                    "verified",
                    first.runtime.run(
                        task.id, {first.node_id: (first.dispatcher, first.session)}
                    ).state,
                )
                old = first.session
            with Harness(*args, clock=clock) as restarted:
                with self.assertRaises(PermissionError):
                    restarted.grid.authenticate(old, "execute")
                self.assertEqual(1, len(restarted.store.all("action")))
                self.assertEqual(b"once", restarted.files.read("proof.txt"))
            clock.now += 3601
            with self.assertRaises(PermissionError):
                Harness(*args, clock=clock)
            with Harness(*args, clock=clock, execution_enrollment_authorized=True) as authorized:
                authorized.grid.authenticate(authorized.session, "execute")
                self.assertEqual(1, len(authorized.store.all("action")))
