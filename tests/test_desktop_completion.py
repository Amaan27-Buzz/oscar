"""Core integration regressions for the software-first Desktop composition."""

import unittest
from threading import Event, Thread
from time import time

from oscar.contracts import Capability, Epistemic, Result, new_id
from oscar.desktop_context import ContextSource
from oscar.desktop_voice import DesktopVoice
from oscar.event_archive import MemoryWriter, SourceEvent
from oscar.grid import Node, NodeRole
from oscar.memory_executor import MemoryExecutor
from oscar.memory_fabric import MemoryFabric
from oscar.storage import StateConflict
from oscar.transport import Dispatcher
from oscar.voice_contracts import AudioFrame, Origin, Transcript

from . import test_desktop


class AskCompletionTests(unittest.TestCase):
    def setUp(self):
        self.base = test_desktop.DesktopTests()
        self.base.setUp()
        self.addCleanup(self.base.tearDown)
        self.h, self.core = self.base.h, self.base.core

    def test_discarded_plan_withdraws_approval_but_keeps_safe_denial(self):
        task = self.base.ask("2 + 3")
        self.assertIn("approve", task["actions"])
        self.base.call("discard", {})
        view = self.core.inspect(self.base.session, task["task_id"])
        self.assertNotIn("approve", view["actions"])
        self.assertIn("deny", view["actions"])
        with self.assertRaises(StateConflict):
            self.core.challenge(
                self.base.session, {"task_id": task["task_id"], "operation": "approve"}
            )

    def test_discard_is_session_scoped_for_planned_active_and_finished_tasks(self):
        own_planned = self.base.ask()["task_id"]
        own_active = self.base.ask()["task_id"]
        self.h.store.transition(own_active, "executing")
        original = self.base.session
        self.base.session = self.h.grid.pair(original.node_id, self.base.scopes)
        other_planned = self.base.ask()["task_id"]
        other_active = self.base.ask()["task_id"]
        self.h.store.transition(other_active, "executing")
        other_finished = self.base.ask()["task_id"]
        self.h.runtime.run(other_finished, self.core.targets)
        unknown_session = self.base.ask()["task_id"]
        record = self.h.store.get("desktop_task", unknown_session)
        record.pop("session_id")
        self.h.store.put("desktop_task", unknown_session, record)
        other_private = {
            identifier: dict(self.h.store.transient[identifier])
            for identifier in (other_planned, other_active, other_finished, unknown_session)
        }
        self.base.session = original
        self.base.call("discard", {})
        self.assertNotIn(own_planned, self.h.store.transient)
        self.assertTrue(self.h.store.transient[own_active]["discarded"])
        for identifier, private in other_private.items():
            with self.subTest(task_id=identifier):
                self.assertEqual(private, self.h.store.transient.get(identifier))
        self.assertEqual("verified", self.h.store.task(other_finished).state)

    def test_evidence_metadata_is_inspectable_without_private_paths_or_input(self):
        task = self.base.ask("2 + 3")
        self.base.confirm(task["task_id"])
        view = self.core.inspect(self.base.session, task["task_id"])
        self.assertTrue(view["evidence"])
        self.assertTrue(view["evidence"][0]["matches"])
        self.assertEqual(
            {"id", "source", "method", "observed_at", "matches", "status"}, set(view["evidence"][0])
        )
        self.assertEqual([], view["artifacts"])

    def test_follow_up_uses_only_same_session_successful_core_working_context(self):
        self.h.dispatcher.executors["models.reason"] = lambda action, cancel: Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            True,
            value="A reference model result",
        )
        first = self.base.ask("Explain an isolated reference")
        self.base.confirm(first["task_id"])
        second = self.base.ask("Explain the result more plainly")
        parameters = self.h.store.transient[second["task_id"]]["parameters"]
        self.assertIn("A reference model result", parameters["prompt"])
        self.assertIn(first["task_id"], parameters["prompt"])
        self.assertEqual("private", parameters["mode"])
        self.assertNotIn("A reference model result", str(self.h.store.all("plan")))
        self.base.call("discard", {})
        third = self.base.ask("Explain another isolated reference")
        self.assertNotIn(
            "Previous Core task", self.h.store.transient[third["task_id"]]["parameters"]["prompt"]
        )

    def test_long_response_has_an_explicit_core_truncation_flag(self):
        self.h.dispatcher.executors["models.reason"] = lambda action, cancel: Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            True,
            value="reference " * 1200,
        )
        task = self.base.ask("Explain a long reference")
        self.base.confirm(task["task_id"])
        view = self.core.inspect(self.base.session, task["task_id"])
        self.assertEqual(8192, len(view["response"]))
        self.assertTrue(view["response_truncated"])
        self.assertEqual("REPORTED", view["response_status"])

    def test_replacement_session_sees_task_metadata_but_not_prior_private_response(self):
        self.h.dispatcher.executors["models.reason"] = lambda action, cancel: Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            True,
            value="private-session-sentinel",
        )
        task = self.base.ask("Explain a reference")
        self.base.confirm(task["task_id"])
        replacement = self.h.grid.pair(self.base.session.node_id, self.base.scopes)
        view = self.core.inspect(replacement, task["task_id"])
        self.assertEqual(task["task_id"], view["task_id"])
        self.assertIsNone(view.get("response"))
        self.assertIsNone(view.get("value"))
        self.assertNotIn("private-session-sentinel", str(view))

    def test_replacement_session_key_does_not_grant_prior_private_review(self):
        task = self.base.ask("Explain private-review-sentinel")
        replacement = self.h.grid.pair(self.base.session.node_id, self.base.scopes)
        self.core.register_owner_key(replacement, self.base.encoded, owner_authorized=True)
        self.assertNotIn("approve", self.core.inspect(replacement, task["task_id"])["actions"])
        with self.assertRaises(StateConflict):
            self.core.challenge(replacement, {"task_id": task["task_id"], "operation": "approve"})
        denial = self.core.challenge(replacement, {"task_id": task["task_id"], "operation": "deny"})
        self.assertEqual("{}", denial["review"])
        self.assertNotIn("private-review-sentinel", str(denial))

    def test_exact_review_is_complete_or_rejected_before_challenge_creation(self):
        import json

        task = self.base.ask()
        private = self.h.store.transient[task["task_id"]]
        private["parameters"] = {"context": "x" * 8192, "instruction": "y" * 4096}
        review = self.core.challenge(
            self.base.session, {"task_id": task["task_id"], "operation": "approve"}
        )
        self.assertEqual(private["parameters"], json.loads(review["review"]))
        count = len(self.h.store.all("sunday_challenge"))
        private["parameters"] = {"context": "漢" * 8192}
        with self.assertRaisesRegex(ValueError, "Exact review exceeds"):
            self.core.challenge(
                self.base.session, {"task_id": task["task_id"], "operation": "approve"}
            )
        self.assertEqual(count, len(self.h.store.all("sunday_challenge")))

    def test_worker_output_truncation_describes_the_selected_source(self):
        self.h.dispatcher.executors["models.reason"] = lambda action, cancel: Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            True,
            value="short",
        )
        task = self.base.ask("Explain a worker output reference")
        self.base.confirm(task["task_id"])
        result = self.h.store.transient[task["task_id"]]["result"]
        self.core.worker_outputs[self.h.node_id] = {result.action_id: "x" * 9000}
        view = self.core.inspect(self.base.session, task["task_id"])
        self.assertEqual(8192, len(view["response"]))
        self.assertTrue(view["response_truncated"])

    def test_sourced_memory_uses_existing_fabric_and_forget_withdraws_recall(self):
        archive = self.h.archive
        memory = MemoryFabric(archive)
        event = SourceEvent(
            "owner",
            "Project Cedar uses typed controls",
            "synthetic-owner",
            time(),
            status=Epistemic.KNOWN,
        )
        archive.append(event, retain_authorized=True)
        retained = MemoryWriter(archive).retain(
            (event.id,),
            event.content,
            "semantic",
            retain_authorized=True,
            inferred=False,
        )
        self.h.runtime.memory = memory
        worker_scopes = ("heartbeat", "advertise", "execute", "memory:read", "cancel")
        self.h.grid.register(Node("recall-worker", NodeRole.CLOUD, worker_scopes))
        worker = self.h.grid.pair("recall-worker", worker_scopes)
        self.h.grid.advertise(
            worker,
            [
                Capability(
                    "memory.recall",
                    "Recall",
                    "Source-backed archive retrieval",
                    "retrieval",
                    worker.node_id,
                    ("memory:read",),
                    "memory",
                    "text",
                )
            ],
        )
        dispatcher = Dispatcher(
            self.h.store,
            self.h.grid,
            worker.node_id,
            {"memory.recall": MemoryExecutor(memory, "owner")},
        )
        self.core.targets[worker.node_id] = (dispatcher, worker)
        scopes = (
            *self.base.scopes,
            "memory:read",
            "control:inspect:recall-worker",
            "control:approve:recall-worker",
            "control:cancel:recall-worker",
        )
        self.h.grid.register(Node("recall-owner", NodeRole.DESKTOP, scopes))
        self.base.session = self.h.grid.pair("recall-owner", scopes)
        self.core.register_owner_key(self.base.session, self.base.encoded, owner_authorized=True)
        task = self.base.ask("Recall Project Cedar")
        self.base.confirm(task["task_id"])
        view = self.core.inspect(self.base.session, task["task_id"])
        self.assertEqual(event.content, view["response"])
        self.assertEqual("RECALLED", view["response_status"])
        self.assertEqual([event.id], view["source_event_ids"])
        self.assertNotEqual("verified", view["state"])
        memory.forget(retained.id, owner_authorized=True)
        forgotten = self.core.inspect(self.base.session, task["task_id"])
        self.assertEqual("UNKNOWN", forgotten["response_status"])
        self.assertNotIn(event.content, forgotten["response"])

    def test_missing_recall_capability_never_falls_back_to_a_model_prior(self):
        task = self.base.ask("Recall an earlier project decision")
        self.assertEqual("blocked", task["state"])
        self.assertNotIn("task_id", task)
        self.assertEqual([], self.h.store.all("action"))

    def test_focused_dictation_preview_discloses_complete_checked_replacement(self):
        context = self.base.attach(text="Before ")
        preview = self.base.ask("spoken", "Dictate", context)
        self.assertEqual("Before ", preview["focused_before"])
        self.assertEqual("Before spoken", preview["focused_after"])
        self.assertEqual("spoken", preview["after"])
        self.assertEqual(self.core.previews[preview["preview_id"]]["expires"], preview["expires"])
        self.assertEqual("Dictate", preview["mode"])

    def test_window_identity_is_not_an_editable_text_selection(self):
        context = self.base.attach(source=ContextSource.FOREGROUND)
        with self.assertRaises(PermissionError):
            self.base.ask("shorten", "Edit", context)
        self.assertEqual([], self.h.store.all("action"))

    def test_discarded_active_private_result_cannot_resurface_after_completion(self):
        task = self.base.ask("Explain a reference")
        self.h.store.transition(task["task_id"], "executing")
        self.base.call("discard", {})
        self.assertTrue(self.h.store.transient[task["task_id"]]["discarded"])
        self.h.runtime.cancel(task["task_id"])
        self.assertNotIn(task["task_id"], self.h.store.transient)

    def test_discard_during_execution_keeps_verification_but_releases_private_result(self):
        entered, release = Event(), Event()
        executor = self.h.dispatcher.executors["math.add"]

        def held(action, cancellation):
            entered.set()
            self.assertTrue(release.wait(3))
            return executor(action, cancellation)

        self.h.dispatcher.executors["math.add"] = held
        task = self.base.ask("2 + 3")
        thread = Thread(target=self.h.runtime.run, args=(task["task_id"], self.core.targets))
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            self.base.call("discard", {})
        finally:
            release.set()
            thread.join(3)
        self.assertEqual("verified", self.h.store.task(task["task_id"]).state)
        self.assertNotIn(task["task_id"], self.h.store.transient)
        self.assertIsNone(self.core.inspect(self.base.session, task["task_id"]).get("value"))

    def voice_fixture(self):
        class Capture:
            closed = False
            calls = 0

            def frames(self, stop):
                self.calls += 1
                yield AudioFrame((0.1,) * 1600, time(), "reference", origin=Origin.SIMULATED)
                stop.event.wait(3)

            def close(self):
                self.closed = True

        class Recognizer:
            local = True
            started, release = Event(), Event()

            def transcribe(self, frames, final, stop):
                self.started.set()
                self.release.wait(3)
                return Transcript("spoken reference", True, "en", None, 0, 1, "SIMULATED")

        capture, recognizer = Capture(), Recognizer()
        self.core.voice = DesktopVoice(self.core, capture, recognizer)
        return capture, recognizer

    def test_voice_finish_publishes_processing_then_preview_not_a_phantom_listening_state(self):
        capture, recognizer = self.voice_fixture()
        self.base.call("voice", {"operation": "start", "context_id": ""})
        self.assertEqual("processing", self.base.call("voice", {"operation": "stop"})["state"])
        self.assertTrue(recognizer.started.wait(2))
        recognizer.release.set()
        self.core.voice.thread.join(3)
        preview = self.base.call("voice", {"operation": "inspect"})
        self.assertEqual("spoken reference", preview["after"])
        self.assertEqual(
            preview["preview_id"], self.base.call("voice", {"operation": "stop"})["preview_id"]
        )
        self.assertTrue(capture.closed)

    def test_voice_cancellation_fences_delayed_recognition_and_is_session_bound(self):
        capture, recognizer = self.voice_fixture()
        self.base.call("voice", {"operation": "start", "context_id": ""})
        self.base.call("voice", {"operation": "stop"})
        self.assertTrue(recognizer.started.wait(2))
        other = self.h.grid.pair(self.base.session.node_id, self.base.scopes)
        with self.assertRaises(PermissionError):
            self.core.voice.cancel(other)
        self.assertEqual("cancelled", self.base.call("voice", {"operation": "cancel"})["state"])
        recognizer.release.set()
        self.core.voice.thread.join(3)
        self.assertEqual({}, self.core.previews)
        self.assertEqual("cancelled", self.core.voice.view["state"])
        self.assertTrue(capture.closed)

    def test_microphone_denial_never_opens_capture(self):
        capture, _ = self.voice_fixture()
        session = self.h.store.get("session", self.base.session.id)
        session["scopes"].remove("desktop:microphone")
        self.h.store.put("session", self.base.session.id, session)
        with self.assertRaises(PermissionError):
            self.base.call("voice", {"operation": "start", "context_id": ""})
        self.assertEqual(0, capture.calls)
