"""Real result handoff and independent file readback, including restart and drift."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from oscar.capabilities import FileExecutor, Verifier, addition_executor
from oscar.contracts import Capability
from oscar.credentials import SecretMaterial
from oscar.executive import Executive, authorize_step
from oscar.executive_inputs import resolve_inputs
from oscar.grid import Node, NodeRole
from oscar.storage import StateConflict
from oscar.transport import Dispatcher
from tests import test_executive as fixture


class ExecutiveInputTests(unittest.TestCase):
    setUp = fixture.ExecutiveTests.setUp
    tearDown = fixture.ExecutiveTests.tearDown
    step = fixture.ExecutiveTests.step
    goal = fixture.ExecutiveTests.goal

    def steps(self):
        return [
            self.step(),
            {
                **self.step("proof", dependency=["sum"], file=True),
                "inputs": [{"from_step": "sum", "select": [], "to": ["content"]}],
            },
        ]

    def test_actual_result_copied_not_placeholder_and_restart_never_replays(self):
        goal = self.goal(self.steps())
        self.assertEqual(2, self.e.tick())
        self.assertEqual(b"4", self.r.files.read("proof.txt"))
        rows = self.r.store.all("executive_task")
        binding = next(row for row in rows if row["step_id"] == "proof")
        pin = binding["inputs"][0]
        self.assertEqual(
            next(row["task_id"] for row in rows if row["step_id"] == "sum"), pin["task_id"]
        )
        self.assertEqual("VERIFIED", self.r.store.get("evidence", pin["evidence_id"])["status"])
        restarted = Executive(self.r.runtime, self.r.transports)
        self.assertEqual(0, restarted.tick())
        self.assertEqual(2, len(self.r.store.all("task")))
        self.assertEqual("completed", self.r.store.get("executive_goal", goal["id"])["state"])

    def test_temporary_worker_lifecycle_preserves_history_without_lifetime_job_limit(self):
        for index in range(65):
            worker = self.e.worker(
                "Task " + str(index),
                [("test-node", "math")],
                ("math",),
                owner_authorized=True,
                temporary=True,
            )
            proposal = self.e.propose(worker, "Calculate once", [self.step()])
            self.e.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
            self.e.tick()
            self.assertFalse(self.r.store.get("executive_worker", worker)["enabled"])
            self.assertEqual(
                "completed", self.r.store.get("executive_goal", proposal["id"])["state"]
            )
        self.assertEqual(65, len(self.r.store.all("task")))
        self.assertTrue(self.r.store.get("executive_worker", self.worker)["enabled"])

    def test_temporary_worker_waits_for_other_active_responsibilities(self):
        worker = self.e.worker(
            "Two responsibilities",
            [("test-node", "math")],
            ("math",),
            owner_authorized=True,
            temporary=True,
        )
        second = self.e.propose(worker, "Pending review", [self.step()])
        first = self.e.propose(worker, "Ready", [self.step()])
        self.e.accept(first["id"], first["review_digest"], owner_authorized=True)
        self.e.tick()
        self.assertTrue(self.r.store.get("executive_worker", worker)["enabled"])
        self.e.accept(second["id"], second["review_digest"], owner_authorized=True)
        self.e.tick()
        self.assertFalse(self.r.store.get("executive_worker", worker)["enabled"])

    def test_recurring_results_are_pinned_to_each_occurrence(self):
        self.goal(self.steps(), interval_seconds=10, max_runs=2)
        self.e.tick()
        self.r.clock.now += 11
        self.e.tick()
        copies = [r for r in self.r.store.all("executive_task") if r["step_id"] == "proof"]
        self.assertEqual([0, 1], sorted(r["occurrence"] for r in copies))
        self.assertNotEqual(copies[0]["inputs"][0]["task_id"], copies[1]["inputs"][0]["task_id"])

    def test_source_drift_before_dispatch_blocks_and_does_not_replay(self):
        self.goal(self.steps())
        original = self.r.runtime.run

        def change_source(task_id, targets):
            plan = self.r.store.get("plan", task_id)
            if plan["kind"] == "file_write":
                pin = plan["executive"]["inputs"][0]
                result = self.r.store.get("result", pin["result_id"])
                self.r.store.put("result", result["id"], {**result, "value": "changed"})
            return original(task_id, targets)

        with patch.object(self.r.runtime, "run", side_effect=change_source):
            self.e.tick()
        self.assertFalse((self.r.files.root / "proof.txt").exists())
        for _ in range(2):
            self.e.tick()
        self.assertEqual(2, len(self.r.store.all("task")))
        self.assertFalse((self.r.files.root / "proof.txt").exists())

    def test_failed_source_never_releases_copy(self):
        self.goal(self.steps())
        self.r.dispatcher.executors["math"] = lambda action, cancel: replace(
            addition_executor(action, cancel), value="wrong"
        )
        self.e.tick()
        self.assertEqual(["failed"], [t["state"] for t in self.r.store.all("task")])
        self.assertFalse((self.r.files.root / "proof.txt").exists())

    def test_review_rejects_authority_and_destination_interpolation(self):
        for destination in (
            ["path"],
            ["kind"],
            ["text"],
            ["parameters", "argv", 0],
            ["parameters", "account_id"],
            ["criterion", "kind"],
        ):
            steps = self.steps()
            steps[1]["inputs"][0]["to"] = destination
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                self.e.propose(self.worker, "Bad handoff", steps)
        for bad in (None, {}, [{}], [{"from_step": "missing", "select": [], "to": ["content"]}]):
            steps = self.steps()
            steps[1]["inputs"] = bad
            with self.subTest(inputs=bad), self.assertRaises(ValueError):
                self.e.propose(self.worker, "Bad handoff", steps)
        steps = self.steps()
        steps[1]["inputs"] *= 2
        with self.assertRaises(ValueError):
            self.e.propose(self.worker, "Duplicate handoff", steps)

    def test_missing_ambiguous_private_and_oversize_values_are_blocked(self):
        goal = self.goal([self.step()])
        self.e.tick()
        step = self.steps()[1]
        result = self.r.store.all("result")[0]
        material = SecretMaterial()
        material.remember("synthetic-private-result-credential")
        for value in (None, "x" * 4097, "synthetic-private-result-credential"):
            self.r.store.put("result", result["id"], {**result, "value": value})
            with self.subTest(value_type=type(value)), self.assertRaises(ValueError):
                resolve_inputs(self.r.store, goal, step)
        self.r.store.put("result", result["id"], result)
        self.r.store.put("result", "duplicate", {**result, "id": "duplicate"})
        with self.assertRaises(StateConflict):
            resolve_inputs(self.r.store, goal, step)

    def test_json_scalar_selection_and_rejection_of_missing_paths(self):
        goal = self.goal([self.step()])
        self.e.tick()
        result = self.r.store.all("result")[0]
        self.r.store.put(
            "result", result["id"], {**result, "value": '{"items":[{"text":"bounded"}]}'}
        )
        step = self.steps()[1]
        step["inputs"][0]["select"] = ["items", 0, "text"]
        intent, _ = resolve_inputs(self.r.store, goal, step)
        self.assertEqual("bounded", intent["content"])
        for path in (["items", True], ["missing"], ["items", 1], ["items"]):
            step["inputs"][0]["select"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                resolve_inputs(self.r.store, goal, step)

    def test_cross_device_copy_uses_selected_executor_and_current_scope(self):
        scopes = ("execute", "heartbeat", "advertise", "files:write")
        self.r.grid.register(Node("destination", NodeRole.DESKTOP, scopes))
        session = self.r.grid.pair("destination", scopes)
        cap = Capability(
            "remote.write",
            "Write",
            "Selected destination",
            "deterministic",
            "destination",
            ("files:write",),
            "file_write",
            "file",
        )
        self.r.grid.advertise(session, [cap])
        remote_files = type(self.r.files)(self.r.root / "destination")
        dispatcher = Dispatcher(
            self.r.store, self.r.grid, "destination", {"remote.write": FileExecutor(remote_files)}
        )
        self.e.targets["destination"] = (dispatcher, session)
        self.worker = self.e.worker(
            "Distributed copy",
            [("test-node", "math"), ("destination", "remote.write")],
            ("math", "files:write"),
            owner_authorized=True,
        )
        steps = self.steps()
        steps[1].update(node_id="destination", capability_id="remote.write")

        self.r.runtime.verifier = Verifier(remote_files)
        self.goal(steps)
        self.e.tick()
        self.assertEqual(b"4", remote_files.read("proof.txt"))
        self.assertFalse((self.r.files.root / "proof.txt").exists())
        target_task = next(r for r in self.r.store.all("executive_task") if r["step_id"] == "proof")
        plan = self.r.store.get("plan", target_task["task_id"])
        self.r.store.put(
            "task",
            target_task["inputs"][0]["task_id"],
            {**self.r.store.get("task", target_task["inputs"][0]["task_id"]), "cancelled": True},
        )
        with self.assertRaises(PermissionError):
            authorize_step(
                self.r.store,
                self.r.grid,
                target_task["task_id"],
                self.r.store.get("node", "destination")["capabilities"][0],
                session,
            )
        self.assertIn("inputs", plan["executive"])
