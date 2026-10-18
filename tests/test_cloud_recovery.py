"""Actual stopped-service recovery and explicit local renewal boundaries."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.cloud import CloudConfig, CloudCore
from oscar.contracts import TaskState, new_id
from oscar.grid import SessionHandle
from oscar.jev import Intent
from oscar.storage import StateConflict


class CloudRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        secrets = root / "secrets"
        secrets.mkdir(mode=0o700)
        self.config = CloudConfig(
            "recovery-cloud-test",
            root / "state",
            Path("config/development-models.json").resolve(),
            secrets,
            "127.0.0.1",
            8765,
            "loopback",
            ("127.0.0.1",),
        )

    def core(self, **arguments):
        core = CloudCore(self.config, start_services=False, **arguments)
        self.addCleanup(core.close)
        return core

    def test_pre_lease_crash_cannot_remain_falsely_executing(self):
        first = self.core(initialize=True)
        task = first.harness.runtime.create(Intent("2 + 3"))
        first.harness.store.transition(task.id, TaskState.EXECUTING)
        self.assertIsNone(first.harness.store.task(task.id).lease_id)
        first.close()
        restarted = self.core()
        recovered = restarted.harness.store.task(task.id)
        self.assertEqual(TaskState.BLOCKED, recovered.state)
        self.assertIn("before execution lease", recovered.blocker)
        self.assertEqual([], restarted.harness.store.all("action"))

    def test_expired_execution_requires_explicit_offline_renewal_without_running_schedules(self):
        first = self.core(initialize=True)
        h = first.harness
        worker = h.executive.worker(
            "Due math", [(h.node_id, "math.add")], ("math",), owner_authorized=True
        )
        goal = h.executive.decompose(worker, "2 + 3")
        h.executive.accept(goal["id"], goal["review_digest"], owner_authorized=True)
        credential = h.store.get("session", h.session.id)
        h.store.put("session", h.session.id, {**credential, "expires_at": time() - 1})
        first.close()
        with self.assertRaises(PermissionError):
            self.core()
        renewed = self.core(renew_execution=True)
        renewed.harness.grid.authenticate(renewed.harness.session, "execute")
        self.assertFalse(renewed.harness.execution_session.thread.is_alive())
        self.assertIsNone(renewed.harness.executive.thread)
        self.assertEqual(0, renewed.harness.store.get("executive_goal", goal["id"])["run_index"])
        self.assertEqual([], renewed.harness.store.all("action"))

    def test_incomplete_probe_archive_reports_conflict(self):
        core = self.core(initialize=True)
        h = core.harness
        task = h.runtime.create(Intent("2 + 3"))
        request_id = new_id()
        h.store.put(
            "cloud_probe",
            "diagnostic-test:" + request_id,
            {
                "task_id": task.id,
                "event_id": new_id(),
                "expression": "2 + 3",
                "occurred_at": time(),
            },
        )
        with self.assertRaises(StateConflict):
            core.inspect_probe(SessionHandle(new_id(), "diagnostic-test", "synthetic"), request_id)


if __name__ == "__main__":
    unittest.main()
