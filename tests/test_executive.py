import json
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Event
from time import time

from oscar.capabilities import FileExecutor, Verifier
from oscar.contracts import Result, new_id
from oscar.event_archive import EventArchive
from oscar.executive import Executive
from oscar.grid import Grid
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.memory_fabric import MemoryFabric
from oscar.perception import PerceptionSource
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.runtime import Runtime
from oscar.storage import StateConflict, Store
from oscar.world_model import ObservationKind
from oscar.world_runtime import WorldRuntime
from tests.support import Rig


class ExecutiveTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.archive = None
        self.world = None
        self.e = Executive(self.r.runtime, dict(self.r.transports))
        self.worker = self.e.worker(
            "Local responsibility",
            [("test-node", "file"), ("test-node", "math")],
            ("files:write", "math"),
            owner_authorized=True,
        )

    def tearDown(self):
        self.e.close()
        if self.world:
            self.world.close()
        if self.archive:
            self.archive.close()
        self.r.close()

    def install_world(self):
        self.archive = EventArchive(self.r.root / "archive.sqlite")
        self.r.runtime.memory = MemoryFabric(self.archive)
        self.world = WorldRuntime(self.r.runtime, self.r.files)
        self.r.runtime.world = self.world

    def step(self, identifier="sum", *, dependency=None, file=False):
        return {
            "id": identifier,
            "intent": asdict(
                Intent("Write exact proof", "file_write", identifier + ".txt", "verified bytes")
                if file
                else Intent("2 + 2")
            ),
            "depends_on": dependency or [],
            "node_id": "test-node",
            "capability_id": "file" if file else "math",
        }

    def goal(self, steps=None, **kwargs):
        proposal = self.e.propose(
            self.worker, "Bounded local goal", steps or [self.step()], **kwargs
        )
        self.e.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
        return proposal

    def test_dependency_graph_uses_real_tasks_files_and_verification(self):
        goal = self.goal([self.step(), self.step("proof", dependency=["sum"], file=True)])
        self.assertEqual(2, self.e.tick())
        self.assertEqual(b"verified bytes", self.r.files.read("proof.txt"))
        self.assertEqual(["verified", "verified"], [r["state"] for r in self.r.store.all("task")])
        self.assertEqual("completed", self.r.store.get("executive_goal", goal["id"])["state"])
        self.assertEqual(0, self.e.tick())
        self.assertEqual(2, len(self.r.store.all("task")))

    def test_exact_review_and_dag_validation(self):
        proposal = self.e.propose(self.worker, "Pending", [self.step()])
        self.assertEqual(0, self.e.tick())
        with self.assertRaises(PermissionError):
            self.e.accept(proposal["id"], proposal["review_digest"], owner_authorized=False)
        with self.assertRaises(StateConflict):
            self.e.accept(proposal["id"], "wrong", owner_authorized=True)
        with self.assertRaises(ValueError):
            self.e.propose(self.worker, "Cycle", [self.step(dependency=["sum"])])
        changed = {**self.step(), "capability_id": "model"}
        with self.assertRaises(PermissionError):
            self.e.propose(self.worker, "Broader", [changed])

    def test_recurring_restart_missed_times_and_max_runs(self):
        goal = self.goal(interval_seconds=10, max_runs=2)
        self.e.tick()
        self.r.clock.now += 101
        other = Executive(self.r.runtime, self.r.transports)
        self.assertEqual(1, other.tick())
        self.assertEqual(2, len(self.r.store.all("task")))
        self.assertEqual("completed", self.r.store.get("executive_goal", goal["id"])["state"])
        self.assertEqual(0, other.tick())

    def test_crash_after_atomic_admission_recovers_same_task(self):
        self.goal()
        original = self.r.runtime.create

        def crash(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError("injected admission crash")

        self.r.runtime.create = crash
        with self.assertRaises(OSError):
            self.e.tick()
        self.assertEqual(1, len(self.r.store.all("executive_task")))
        self.r.runtime.create = original
        self.e.tick()
        self.assertEqual(1, len(self.r.store.all("task")))
        self.assertEqual("verified", self.r.store.all("task")[0]["state"])

    def test_two_database_runners_do_not_duplicate_tasks_or_mutations(self):
        self.goal([self.step("proof", file=True)])
        store = Store(self.r.root / "state.sqlite")
        try:
            grid = Grid(store, self.r.clock)
            runtime = Runtime(store, grid, Verifier(self.r.files))
            other = Executive(runtime, self.r.transports)
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(lambda e: e.tick(), [self.e, other]))
            self.assertEqual(1, len(store.all("task")))
            self.assertEqual("verified", store.all("task")[0]["state"])
            self.assertEqual(
                1,
                len(
                    [
                        r
                        for r in store.ledger(store.all("task")[0]["id"])
                        if r["event"] == "action_authorized"
                    ]
                ),
            )
        finally:
            store.close()

    def test_policy_ask_requires_exact_next_attempt_confirmation(self):
        now = self.r.clock()
        policy = PersonalPolicy(self.r.store)
        policy.save(
            PolicyRule("ask", "math", PolicyEffect.ASK, "owner", now, now, {}),
            owner_authorized=True,
        )
        self.goal()
        self.e.tick()
        task = self.r.store.all("task")[0]
        self.assertEqual("planned", task["state"])
        review = self.e.review_task(task["id"])
        self.e.confirm_task(task["id"], review["digest"], owner_authorized=True)
        self.e.tick()
        self.assertEqual("verified", self.r.store.task(task["id"]).state)

    def test_policy_change_during_acquisition_stops_file_mutation(self):
        self.goal([self.step("proof", file=True)])
        original = self.r.dispatcher.executors["file"]

        def change(action, cancellation):
            now = self.r.clock()
            PersonalPolicy(self.r.store).save(
                PolicyRule("deny-file", "file", PolicyEffect.DENY, "owner", now, now, {}),
                owner_authorized=True,
            )
            return original(action, cancellation)

        self.r.dispatcher.executors["file"] = change
        self.e.tick()
        self.assertFalse(self.r.files.exists("proof.txt"))

    def test_renewed_task_lease_keeps_worker_reserved_after_slot_timer(self):
        self.goal()
        self.goal()
        entered, release = Event(), Event()
        original = self.r.dispatcher.executors["math"]
        calls = []

        def long_running(action, cancellation):
            calls.append(action.id)
            entered.set()
            if not release.wait(5):
                raise OSError("test timed out")
            return original(action, cancellation)

        self.r.dispatcher.executors["math"] = long_running
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.e.tick)
            try:
                self.assertTrue(entered.wait(3))
                first = self.r.store.all("task")[0]
                self.r.clock.now += 110
                self.r.grid.renew(first["lease_id"], self.r.session, ttl=240)
                self.r.clock.now += 20
                other = Executive(self.r.runtime, self.r.transports)
                other.tick()
                self.assertEqual(1, len(calls))
            finally:
                release.set()
            future.result(timeout=5)

    def test_revocation_during_execution_prevents_file_mutation(self):
        self.goal([self.step("proof", file=True)])
        original = self.r.dispatcher.executors["file"]

        def revoke(action, cancellation):
            self.e.revoke_worker(self.worker, owner_authorized=True)
            return original(action, cancellation)

        self.r.dispatcher.executors["file"] = revoke
        self.e.tick()
        self.assertFalse(self.r.files.exists("proof.txt"))
        self.assertEqual("cancelled", self.r.store.all("task")[0]["state"])

    def test_withdrawal_during_execution_prevents_file_mutation(self):
        self.goal([self.step("proof", file=True)])
        original = self.r.dispatcher.executors["file"]

        def withdraw(action, cancellation):
            self.r.grid.advertise(self.r.session, [])
            return original(action, cancellation)

        self.r.dispatcher.executors["file"] = withdraw
        self.e.tick()
        self.assertFalse(self.r.files.exists("proof.txt"))

    def test_ambiguous_completed_mutation_is_never_automatically_replayed(self):
        self.goal([self.step("proof", file=True)])
        calls = []
        original = FileExecutor(self.r.files)

        def lose_result(action, cancellation):
            calls.append(action.id)
            original(action, cancellation)
            raise OSError("injected result loss")

        self.r.dispatcher.executors["file"] = lose_result
        self.e.tick()
        task = self.r.store.all("task")[0]
        self.e.tick()
        self.e.retry(task["id"], owner_authorized=True)
        self.e.tick()
        self.assertEqual(1, len(calls))
        self.assertEqual(1, len(self.r.store.all("task")))
        self.assertEqual("blocked", self.r.store.task(task["id"]).state)
        self.assertEqual(b"verified bytes", self.r.files.read("proof.txt"))

    def test_deadline_and_pause_cancel_do_not_fabricate_completion(self):
        goal = self.goal(start_at=self.r.clock() + 10, deadline=self.r.clock() + 20)
        self.e.control(goal["id"], "pause", owner_authorized=True)
        self.assertEqual(0, self.e.tick())
        self.e.control(goal["id"], "resume", owner_authorized=True)
        self.r.clock.now += 21
        self.e.tick()
        self.assertEqual("expired", self.r.store.get("executive_goal", goal["id"])["state"])
        self.assertEqual([], self.r.store.all("task"))

    def test_creation_key_cannot_be_reused_for_different_work(self):
        first = self.r.runtime.create(Intent("2 + 2"), creation_key="one")
        self.assertEqual(first.id, self.r.runtime.create(Intent("2 + 2"), creation_key="one").id)
        with self.assertRaises(StateConflict):
            self.r.runtime.create(Intent("3 + 3"), creation_key="one")

    def test_model_planning_uses_reported_results_and_never_auto_approves_steps(self):
        worker = self.e.worker(
            "Planner",
            [("test-node", "model"), ("test-node", "math")],
            ("models", "math"),
            owner_authorized=True,
        )

        def model(action, cancellation):
            cancellation.check()
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                "synthetic-model-fixture",
                True,
                value=json.dumps([self.step()]),
            )

        self.r.dispatcher.executors["model"] = model
        draft = self.e.draft_plan(worker, "Calculate a result")
        self.assertEqual(0, self.e.tick())
        self.e.accept(draft["id"], draft["review_digest"], owner_authorized=True)
        self.e.tick()
        task = self.r.store.all("task")[0]
        self.assertEqual("partially_verified", task["state"])
        candidate = self.e.propose_from_result(worker, "Calculate a result", task["id"])
        self.assertEqual("proposed", candidate["state"])
        self.assertEqual(task["id"], candidate["planner_task_id"])
        self.e.tick()
        self.assertEqual(1, len(self.r.store.all("task")))
        self.e.accept(candidate["id"], candidate["review_digest"], owner_authorized=True)
        self.e.tick()
        self.assertEqual("completed", self.r.store.get("executive_goal", candidate["id"])["state"])

    def test_offline_wait_does_not_grow_ledger_and_recovers_same_task(self):
        self.goal()
        self.e.targets = {}
        self.r.grid.disconnect("test-node")
        self.e.tick()
        task = self.r.store.all("task")[0]
        entries = len(self.r.store.ledger(task["id"]))
        for _ in range(3):
            self.e.tick()
        self.assertEqual(entries, len(self.r.store.ledger(task["id"])))
        self.e.targets = self.r.transports
        self.r.grid.advertise(self.r.session, self.r.caps)
        self.e.tick()
        self.assertEqual("verified", self.r.store.task(task["id"]).state)
        self.assertEqual(1, len(self.r.store.all("task")))

    def test_current_context_conditions_wait_on_unknown_and_recheck_revocation(self):
        self.install_world()
        worker = self.e.worker(
            "Conditional",
            [("test-node", "file")],
            ("files:write", "world:read"),
            owner_authorized=True,
        )
        self.world.configure_source(
            PerceptionSource(
                "local-grid",
                ("core",),
                ("grid.state",),
                (ObservationKind.DEVICE,),
                simulated=False,
                perceive=True,
            ),
            "grid",
            "core",
            owner_authorized=True,
        )
        self.world.tick()
        value = self.world.world.resolve("core", "grid.state").value
        goal = self.e.propose(
            worker,
            "Scoped condition",
            [self.step("conditional", file=True)],
            conditions=[{"entity_id": "core", "key": "grid.state", "equals": value}],
        )
        self.e.accept(goal["id"], goal["review_digest"], owner_authorized=True)
        self.r.clock.now += 6
        self.assertEqual(0, self.e.tick())
        self.assertEqual([], self.r.store.all("task"))
        self.world.tick()
        original = self.r.dispatcher.executors["file"]

        def revoke(action, cancellation):
            self.world.fabric.revoke("local-grid", owner_authorized=True)
            return original(action, cancellation)

        self.r.dispatcher.executors["file"] = revoke
        self.e.tick()
        self.assertFalse(self.r.files.exists("conditional.txt"))
        self.assertEqual("cancelled", self.r.store.all("task")[0]["state"])
        self.assertEqual(0, self.e.tick())
        self.assertEqual("waiting_for_context", self.e.health)

    def test_replanning_needs_a_new_review_and_cannot_replace_dispatched_work(self):
        prior = self.goal(start_at=self.r.clock() + 100)
        revision = self.e.replan(prior["id"], start_at=self.r.clock(), owner_authorized=True)
        self.assertEqual("enabled", self.r.store.get("executive_goal", prior["id"])["state"])
        self.e.accept(revision["id"], revision["review_digest"], owner_authorized=True)
        self.assertEqual("cancelled", self.r.store.get("executive_goal", prior["id"])["state"])
        self.e.tick()
        with self.assertRaises(StateConflict):
            self.e.replan(revision["id"], owner_authorized=True)
        self.assertEqual(1, self.e.snapshot()["brief"]["verified_runs"])

    def test_learning_requires_retention_and_independently_verified_replay(self):
        self.install_world()
        goal = self.goal()
        self.e.tick()
        with self.assertRaises(PermissionError):
            self.e.learn(goal["id"], owner_authorized=True, retain_authorized=False)
        workflow = self.e.learn(goal["id"], owner_authorized=True, retain_authorized=True)
        event = self.archive.event(workflow["event_id"])
        self.assertEqual("REPORTED", event.status)
        replay = self.e.reuse(workflow["id"], self.worker, owner_authorized=True)
        with self.assertRaises(StateConflict):
            self.e.evaluate_workflow(
                workflow["id"], replay["id"], owner_authorized=True, retain_authorized=True
            )
        self.e.accept(replay["id"], replay["review_digest"], owner_authorized=True)
        self.e.tick()
        evaluation = self.e.evaluate_workflow(
            workflow["id"], replay["id"], owner_authorized=True, retain_authorized=True
        )
        self.assertEqual("VERIFIED", self.archive.event(evaluation).status)
        self.r.store.delete("executive_workflow", workflow["id"])
        self.assertEqual(1, self.e.rebuild_workflows(owner_authorized=True))
        self.assertEqual(
            evaluation,
            self.r.store.get("executive_workflow", workflow["id"])["evaluation_event_id"],
        )
        self.assertEqual(
            "proposed", self.e.reuse(workflow["id"], self.worker, owner_authorized=True)["state"]
        )
        now = self.r.clock()
        PersonalPolicy(self.r.store).save(
            PolicyRule(
                "no-learning",
                "memory.retain",
                PolicyEffect.DENY,
                "owner",
                now,
                now,
                {"source": "executive"},
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.e.learn(goal["id"], owner_authorized=True, retain_authorized=True)
        self.r.runtime.relationship_id = "other"
        with self.assertRaises(PermissionError):
            self.e.reuse(workflow["id"], self.worker, owner_authorized=True)

    def test_cancellation_during_admission_leaves_no_orphan_work(self):
        goal = self.goal()
        original = self.r.runtime.create

        def cancel_before_commit(*args, **kwargs):
            self.e.control(goal["id"], "cancel", owner_authorized=True)
            return original(*args, **kwargs)

        self.r.runtime.create = cancel_before_commit
        self.e.tick()
        self.assertEqual([], self.r.store.all("task"))
        self.assertEqual("cancelled", self.r.store.get("executive_goal", goal["id"])["state"])

    def test_bounded_decomposition_is_reviewed_before_execution(self):
        proposal = self.e.decompose(self.worker, "2 + 2 then 3 + 3")
        self.assertEqual(["step-1"], proposal["steps"][1]["depends_on"])
        self.assertEqual(0, self.e.tick())
        self.e.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
        self.assertEqual(2, self.e.tick())
        with self.assertRaises(ValueError):
            self.e.decompose(self.worker, "Send a message")

    def test_real_core_process_restart_runs_scheduled_local_executor(self):
        state = self.r.root / "persistent.sqlite"
        workspace = self.r.root / "persistent-files"
        with Harness(state, workspace, Path("config/development-models.json")) as h:
            e = h.runtime.executive
            worker = e.worker(
                "Restart proof",
                [(h.node_id, "files.write")],
                ("files:write",),
                owner_authorized=True,
            )
            step = {
                **self.step("after-restart", file=True),
                "node_id": h.node_id,
                "capability_id": "files.write",
            }
            proposal = e.propose(worker, "Write after restart", [step], start_at=time() + 1)
            e.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "oscar",
                "--state",
                str(state),
                "--workspace",
                str(workspace),
                "serve",
                "--seconds",
                "3",
            ],
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(0, result.returncode)
        self.assertEqual(b"verified bytes", (workspace / "after-restart.txt").read_bytes())
        with Harness(state, workspace, Path("config/development-models.json")) as h:
            self.assertEqual("completed", h.store.get("executive_goal", proposal["id"])["state"])
            self.assertEqual(1, len(h.store.all("task")))
