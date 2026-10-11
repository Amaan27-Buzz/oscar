"""Core integration regressions for the software-first Desktop composition."""

import unittest
from time import time

from oscar.contracts import Capability, Epistemic, Result, new_id
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.grid import Node, NodeRole
from oscar.memory_executor import MemoryExecutor
from oscar.memory_fabric import MemoryFabric
from oscar.transport import Dispatcher

from . import test_desktop


class AskCompletionTests(unittest.TestCase):
    def setUp(self):
        self.base = test_desktop.DesktopTests()
        self.base.setUp()
        self.addCleanup(self.base.tearDown)
        self.h, self.core = self.base.h, self.base.core

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

    def test_sourced_memory_uses_existing_fabric_and_forget_withdraws_recall(self):
        archive = EventArchive(self.base.root / "archive.db")
        self.addCleanup(archive.close)
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
