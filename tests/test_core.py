import os
import unittest
from dataclasses import replace
from unittest.mock import patch

from oscar.cli import fake_executor
from oscar.contracts import Epistemic, Result, TaskState, new_id, record
from oscar.jev import DecisionRoute, ExecutionClass, Intent, decide
from oscar.storage import StateConflict, Store
from oscar.transport import HTTPTransport, ReferenceServer

from .support import Rig


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.rig = Rig()
        self.addCleanup(self.rig.close)

    def test_file_objective_result_evidence_ledger_artifact(self):
        r = self.rig
        task = r.file_task()
        result = r.runtime.run(task.id, r.transports)
        self.assertEqual(result.state, TaskState.VERIFIED)
        self.assertEqual(r.files.read("proof.txt"), b"exact bytes\n")
        reported = r.store.all("result")[0]
        self.assertEqual(reported["status"], "REPORTED")
        self.assertTrue(r.store.all("evidence")[0]["matches"])
        self.assertEqual(r.store.all("artifact")[0]["status"], "VERIFIED")
        transitions = [e["to"] for e in r.store.ledger(task.id) if e["event"] == "transition"]
        self.assertEqual(
            transitions,
            ["executing", "awaiting_result", "result_received", "verifying", "verified"],
        )
        for record_type in ("action", "result", "evidence"):
            self.assertEqual(r.store.all(record_type)[0]["correlation_id"], task.correlation_id)

    def test_fake_success_is_mandatorily_rejected(self):
        r = self.rig
        r.dispatcher.executors["file"] = fake_executor
        task = r.file_task()
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.FAILED)
        self.assertEqual(r.store.all("result")[0]["status"], "REPORTED")
        self.assertFalse(r.store.all("evidence")[0]["matches"])
        self.assertFalse((r.files.root / "proof.txt").exists())

    def test_wrong_file_contents_are_not_verified(self):
        r = self.rig
        original = r.dispatcher.executors["file"]

        def wrong(action, cancellation):
            return original(
                replace(action, parameters={"path": "proof.txt", "content": "wrong"}), cancellation
            )

        r.dispatcher.executors["file"] = wrong
        task = r.file_task()
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.FAILED)

    def test_verifier_cannot_inspect_is_partial(self):
        r = self.rig
        task = r.file_task()
        with patch.object(r.files, "read", side_effect=PermissionError):
            result = r.runtime.run(task.id, r.transports)
        self.assertEqual(result.state, TaskState.PARTIALLY_VERIFIED)
        self.assertIsNone(r.store.all("evidence")[0]["matches"])
        self.assertEqual(r.store.all("artifact")[0]["status"], "REPORTED")

    def test_http_reference_executes_real_file(self):
        r = self.rig
        with ReferenceServer(r.dispatcher) as server:
            task = r.file_task()
            result = r.runtime.run(task.id, {"test-node": (HTTPTransport(server.url), r.session)})
        self.assertEqual(result.state, TaskState.VERIFIED)
        self.assertEqual(r.files.read("proof.txt"), b"exact bytes\n")

    def test_model_success_stays_reported_and_partial(self):
        r = self.rig

        def model(action, cancellation):
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                "model",
                True,
                "claims done",
            )

        r.dispatcher.executors["model"] = model
        task = r.runtime.create(Intent("reason about this architecture"))
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.PARTIALLY_VERIFIED)
        self.assertEqual(r.store.all("result")[0]["status"], "REPORTED")

    def test_unavailable_model_route_is_blocked(self):
        r = self.rig

        def model(action, cancellation):
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                "model",
                False,
                error="route_unavailable",
            )

        r.dispatcher.executors["model"] = model
        task = r.runtime.create(Intent("reason about architecture"))
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.BLOCKED)

    def test_arithmetic_never_invokes_model(self):
        r = self.rig

        def forbidden(*args):
            self.fail("deterministic path called a model")

        r.dispatcher.executors["model"] = forbidden
        for expression, expected in [
            ("what is 2 + 2?", "4"),
            ("999999999999+1", "1000000000000"),
            ("0+0", "0"),
        ]:
            task = r.runtime.create(Intent(expression))
            self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.VERIFIED)
            self.assertEqual(r.store.all("result")[-1]["value"], expected)

    def test_unknown_and_missing_live_capability_do_not_guess(self):
        r = self.rig
        self.assertEqual(r.runtime.create(Intent("unsupported request")).state, TaskState.UNKNOWN)
        self.assertEqual(
            r.runtime.create(Intent("what does my latest calendar say?")).state, TaskState.BLOCKED
        )
        self.assertEqual(
            r.runtime.create(Intent("fix this repository bug")).state, TaskState.BLOCKED
        )

    def test_cancel_before_execution_prevents_side_effect(self):
        r = self.rig
        task = r.file_task()
        r.runtime.cancel(task.id)
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.CANCELLED)
        self.assertFalse((r.files.root / "proof.txt").exists())

    def test_cancel_during_execution_never_verifies_late_result(self):
        r = self.rig

        def cancelling(action, cancellation):
            r.runtime.cancel(action.task_id)
            cancellation.check()
            self.fail("cancel did not propagate")

        r.dispatcher.executors["file"] = cancelling
        task = r.file_task()
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.CANCELLED)
        self.assertFalse(r.store.all("evidence"))

    def test_idempotency_at_target_prevents_duplicate_write(self):
        r = self.rig
        _, action, envelope = r.leased_action()
        original = r.dispatcher.executors["file"]
        calls = []

        def counted(action, cancellation):
            calls.append(action.id)
            return original(action, cancellation)

        r.dispatcher.executors["file"] = counted
        first = r.dispatcher.invoke(envelope, r.session)
        second = r.dispatcher.invoke(replace(envelope, nonce=new_id()), r.session)
        self.assertEqual(first.id, second.id)
        self.assertEqual(calls, [action.id])

    def test_replay_rejected(self):
        r = self.rig
        _, _, envelope = r.leased_action()
        r.dispatcher.invoke(envelope, r.session)
        with self.assertRaises(StateConflict):
            r.dispatcher.invoke(envelope, r.session)

    def test_crash_ambiguity_is_not_reexecuted(self):
        r = self.rig
        _, _, envelope = r.leased_action()
        calls = []

        def uncertain(action, cancellation):
            calls.append(action.id)
            raise OSError("synthetic crash after possible side effect")

        r.dispatcher.executors["file"] = uncertain
        with self.assertRaises(OSError):
            r.dispatcher.invoke(envelope, r.session)
        with self.assertRaises(StateConflict):
            r.dispatcher.invoke(replace(envelope, nonce=new_id()), r.session)
        self.assertEqual(len(calls), 1)

    def test_changed_idempotent_action_is_rejected(self):
        r = self.rig
        _, action, envelope = r.leased_action()
        r.dispatcher.invoke(envelope, r.session)
        changed = replace(action, parameters={"path": "other.txt", "content": "changed"})
        r.store.put("action", changed.id, record(changed))
        with self.assertRaises(StateConflict):
            r.dispatcher.invoke(
                replace(envelope, nonce=new_id(), payload=record(changed)), r.session
            )

    def test_reopen_store_preserves_objective_task_and_ledger(self):
        r = self.rig
        task = r.file_task()
        r.runtime.run(task.id, r.transports)
        reopened = Store(r.root / "state.sqlite")
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.task(task.id).state, TaskState.VERIFIED)
        self.assertEqual(
            reopened.get("objective", task.objective_id)["criterion"]["path"], "proof.txt"
        )
        self.assertTrue(reopened.ledger(task.id))

    def test_future_schema_is_not_silently_downgraded(self):
        import sqlite3

        path = self.rig.root / "future.sqlite"
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA user_version=2")
        connection.close()
        with self.assertRaises(StateConflict):
            Store(path)
        connection = sqlite3.connect(path)
        self.addCleanup(connection.close)
        self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_retry_budget_is_bounded(self):
        r = self.rig
        task = r.runtime.create(Intent("Write", "file_write", "x.txt", "x"), retry_budget=0)
        r.store.transition(task.id, TaskState.EXECUTING)
        r.store.transition(task.id, TaskState.BLOCKED)
        with self.assertRaises(StateConflict):
            r.runtime.reclaim(task.id)

    def test_cannot_upgrade_directly_to_verified(self):
        task = self.rig.file_task()
        with self.assertRaises(StateConflict):
            self.rig.store.transition(task.id, TaskState.VERIFIED)

    def test_target_rechecks_scope(self):
        r = self.rig
        _, _, envelope = r.leased_action()
        reduced = r.grid.pair("test-node", ("heartbeat", "execute"))
        with self.assertRaises(PermissionError):
            r.dispatcher.invoke(replace(envelope, session_id=reduced.id), reduced)
        self.assertFalse((r.files.root / "proof.txt").exists())

    def test_path_traversal_and_symlink_parents_fail_closed(self):
        r = self.rig
        outside = r.root / "outside"
        outside.mkdir()
        os.symlink(outside, r.files.root / "link")
        for path in ("../escape", "/tmp/escape", "link/escape", "a/../../escape"):
            task = r.file_task(path)
            self.assertNotEqual(r.runtime.run(task.id, r.transports).state, TaskState.VERIFIED)
        self.assertFalse((outside / "escape").exists())

    def test_executor_forged_verified_claim_is_rejected(self):
        r = self.rig

        def forged(action, cancellation):
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                "file",
                True,
                status=Epistemic.VERIFIED,
            )

        r.dispatcher.executors["file"] = forged
        task = r.file_task()
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.BLOCKED)

    def test_result_after_lease_expiry_never_verifies(self):
        r = self.rig
        original = r.dispatcher.executors["file"]

        def slow(action, cancellation):
            result = original(action, cancellation)
            r.clock.now += 121
            return result

        r.dispatcher.executors["file"] = slow
        task = r.file_task()
        self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.BLOCKED)
        self.assertFalse(r.store.all("evidence"))

    def test_cancel_propagates_over_authenticated_http(self):
        r = self.rig
        task, _, _ = r.leased_action()
        with ReferenceServer(r.dispatcher) as server:
            transports = {"test-node": (HTTPTransport(server.url), r.session)}
            self.assertEqual(r.runtime.cancel(task.id, transports).state, TaskState.CANCELLED)
        self.assertEqual(r.store.ledger(task.id)[-1]["status"], "REPORTED")
        self.assertFalse(r.store.get("lease", r.store.task(task.id).lease_id)["active"])

    def test_cancellation_delivery_failure_stays_cancelled(self):
        r = self.rig
        task, _, _ = r.leased_action()
        with patch.object(r.dispatcher, "control", side_effect=StateConflict):
            r.runtime.cancel(task.id, r.transports)
        self.assertEqual(r.store.task(task.id).state, TaskState.CANCELLED)
        self.assertEqual(r.store.ledger(task.id)[-1]["status"], "UNKNOWN")

    def test_artifact_hash_is_bound_to_the_verification_read(self):
        r = self.rig
        original = r.files.read
        calls = []

        def read_once(path):
            calls.append(path)
            return original(path)

        task = r.file_task()
        with patch.object(r.files, "read", side_effect=read_once):
            result = r.runtime.run(task.id, r.transports)
        self.assertEqual(result.state, TaskState.VERIFIED)
        self.assertEqual(calls, ["proof.txt"])
        self.assertEqual(
            r.store.all("evidence")[0]["content_hash"], r.store.all("artifact")[0]["content_hash"]
        )

    def test_verified_objective_cannot_upgrade_an_unrelated_reported_artifact(self):
        from time import time

        from oscar.contracts import ArtifactRef

        r = self.rig
        for capability, intent in [
            ("file", Intent("write", "file_write", "proof.txt", "exact bytes\n")),
            ("math", Intent("2+2")),
        ]:
            original = r.dispatcher.executors[capability]

            def wrong_artifact(action, cancellation, original=original):
                result = original(action, cancellation)
                artifact = ArtifactRef(
                    new_id(),
                    action.task_id,
                    action.capability_id,
                    "file",
                    str(r.files.root / "unrelated-missing.txt"),
                    time(),
                )
                return replace(result, artifact=artifact)

            r.dispatcher.executors[capability] = wrong_artifact
            task = r.runtime.create(intent)
            self.assertEqual(r.runtime.run(task.id, r.transports).state, TaskState.VERIFIED)
            self.assertEqual(r.store.all("artifact")[-1]["status"], "REPORTED")
            self.assertIsNone(r.store.all("evidence")[-1]["artifact_id"])
            r.dispatcher.executors[capability] = original

    def test_action_preserves_actual_initiator(self):
        r = self.rig
        task = r.runtime.create(
            Intent("write", "file_write", "x.txt", "x"), initiator="developer-test"
        )
        r.runtime.run(task.id, r.transports)
        self.assertEqual(r.store.all("action")[0]["initiator"], "developer-test")

    def test_concurrent_runners_claim_task_once_without_blocking_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        r = self.rig
        task = r.file_task()
        barrier = Barrier(2)
        original_search = r.grid.search

        def search(kind):
            result = original_search(kind)
            barrier.wait(timeout=3)
            return result

        original_execute = r.dispatcher.executors["file"]
        executions = []

        def counted(action, cancellation):
            executions.append(action.id)
            return original_execute(action, cancellation)

        r.dispatcher.executors["file"] = counted
        with (
            patch.object(r.grid, "search", side_effect=search),
            ThreadPoolExecutor(max_workers=2) as threads,
        ):
            results = list(threads.map(lambda _: r.runtime.run(task.id, r.transports), range(2)))
        self.assertEqual(r.store.task(task.id).state, TaskState.VERIFIED)
        self.assertTrue(any(result.state == TaskState.VERIFIED for result in results))
        self.assertEqual(len(executions), 1)

    def test_stale_runner_cannot_block_or_release_a_new_lease(self):
        r = self.rig
        original_execute = r.dispatcher.executors["file"]
        new_leases = []

        def late(action, cancellation):
            result = original_execute(action, cancellation)
            r.clock.now += 121
            r.grid.reap()
            r.grid.advertise(r.session, r.caps)
            r.runtime.reclaim(action.task_id)
            r.store.transition(action.task_id, TaskState.EXECUTING)
            new_leases.append(r.grid.lease(action.task_id, "test-node", ttl=120))
            r.store.transition(action.task_id, TaskState.AWAITING_RESULT)
            return result

        r.dispatcher.executors["file"] = late
        task = r.file_task()
        r.runtime.run(task.id, r.transports)
        self.assertEqual(r.store.task(task.id).state, TaskState.AWAITING_RESULT)
        self.assertTrue(r.store.get("lease", new_leases[0])["active"])
        self.assertFalse(r.store.all("evidence"))
        self.assertEqual(r.store.all("result")[0]["status"], "REPORTED")


class JevTests(unittest.TestCase):
    def test_typed_decisions_for_all_routes(self):
        examples = [
            ("2+2", DecisionRoute.KNOWN, ExecutionClass.CAPABILITY),
            ("what does my latest calendar say?", DecisionRoute.WORLD, ExecutionClass.RETRIEVAL),
            ("recall our plan", DecisionRoute.RECALL, ExecutionClass.RETRIEVAL),
            ("did that email actually send?", DecisionRoute.VERIFY, ExecutionClass.VERIFICATION),
            ("reason about this architecture", DecisionRoute.REASON, ExecutionClass.MODEL),
            ("worker reports done", DecisionRoute.REPORTED, ExecutionClass.VERIFICATION),
            ("fix this repository bug", DecisionRoute.SPECIALIST, ExecutionClass.SPECIALIST),
            ("monitor my build", DecisionRoute.WORKER, ExecutionClass.WORKER),
            ("ambiguous", DecisionRoute.UNKNOWN, ExecutionClass.ASK),
        ]
        for text, route, execution in examples:
            with self.subTest(text=text):
                decision = decide(Intent(text))
                self.assertEqual(decision.route, route)
                self.assertEqual(decision.execution_class, execution)
                self.assertGreaterEqual(decision.latency_ms, 0)

    def test_incomplete_file_intent_asks_for_details(self):
        self.assertEqual(
            decide(Intent("write this file", "file_write")).execution_class, ExecutionClass.ASK
        )

    def test_arbitrary_expression_does_not_execute_python(self):
        self.assertEqual(
            decide(Intent("__import__('os').system('anything')")).route, DecisionRoute.UNKNOWN
        )
