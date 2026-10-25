"""Sourced history can inform execution without becoming current truth or authority."""

import json
import unittest
from dataclasses import asdict
from time import time

from oscar.event_archive import MemoryWriter, SourceEvent
from oscar.jev import Intent
from oscar.planner_authoring import PlannerAuthoring
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from tests import test_planner_authoring as fixture


class PlanningMemoryTests(unittest.TestCase):
    setUp = fixture.PlannerAuthoringTests.setUp
    close = fixture.PlannerAuthoringTests.close
    review = fixture.PlannerAuthoringTests.review
    complete = fixture.PlannerAuthoringTests.complete
    signature = fixture.PlannerAuthoringTests.signature
    accept_change = fixture.PlannerAuthoringTests.accept_change
    delegate = fixture.PlannerAuthoringTests.delegate

    def prepare(self):
        self.executor.grid, self.executor.memory = self.h.grid, self.h.memory
        self.grants |= frozenset({"memory:read"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(self.grants)})
        event = SourceEvent("owner", "My preferred answer is violet", "synthetic", time() - 10)
        self.h.archive.append(event, retain_authorized=True)
        self.memory = MemoryWriter(self.h.archive).retain(
            (event.id,), event.content, "preference", retain_authorized=True, inferred=False
        )
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    **self.steps[0],
                    "capability_id": "files.write",
                    "intent": asdict(Intent("Save answer", "file_write", "answer.txt", "violet")),
                }
            ]
        )

    def start(self, full=False):
        self.prepare()
        if full:
            self.delegate(actions=("files.write", "memory.recall"))
        result = PlannerAuthoring(self.h).conversation(
            "Create worker Answer: Write answer.txt using my preferred answer",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertEqual([], self.requests)
        if full:
            self.assertIn("assistance_started", result)
        else:
            self.complete(self.review(result["assistance_proposal"]))
        self.row = self.h.store.all("planner_request")[-1]

    def test_ask_sourced_private_plan_and_verified_file_readback(self):
        self.start()
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        prompt = json.dumps(self.requests)
        self.assertIn("My preferred answer is violet", prompt)
        self.assertIn("RECALLED, never current truth", prompt)
        self.assertIn(self.memory.event_ids[0], prompt)
        self.assertFalse((self.h.files.root / "answer.txt").exists())
        self.complete(self.review(self.accept_change(self.row)))
        self.h.executive.tick()
        self.assertEqual("violet", (self.h.files.root / "answer.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        durable = json.dumps(self.h.store.all("planned_action"))
        self.assertNotIn("My preferred answer is violet", durable)

    def test_full_delegation_covers_memory_and_effect_without_more_reviews(self):
        self.start(full=True)
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual("violet", (self.h.files.root / "answer.txt").read_text())
        self.assertEqual(1, len(self.requests))

    def test_forget_after_signed_review_prevents_model_io(self):
        self.start()
        self.h.archive.forget(self.memory.id, owner_authorized=True)
        self.h.executive.tick()
        self.assertEqual([], self.requests)

    def test_forget_after_model_prevents_effect(self):
        self.start(full=True)
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.h.archive.forget(self.memory.id, owner_authorized=True)
        self.h.executive.tick()
        self.assertFalse((self.h.files.root / "answer.txt").exists())

    def test_memory_scope_withdrawal_after_acceptance_prevents_effect(self):
        self.start()
        self.h.executive.tick()
        self.complete(self.review(self.accept_change(self.row)))
        node = self.h.store.get("node", self.owner.node_id)
        self.h.store.put(
            "node",
            self.owner.node_id,
            {
                **node,
                "scopes": [s for s in node["scopes"] if s != "memory:read"],
            },
        )
        self.h.executive.tick()
        self.assertFalse((self.h.files.root / "answer.txt").exists())

    def test_empty_recall_blocks_without_model_or_effects(self):
        self.prepare()
        self.h.archive.forget(self.memory.id, owner_authorized=True)
        result = PlannerAuthoring(self.h).conversation(
            "Create worker Answer: Write answer.txt using my preferred answer",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertEqual("blocked", result["state"])
        self.assertIn("UNKNOWN", result["message"])
        self.assertEqual([], self.requests)

    def test_correction_after_review_prevents_old_history_disclosure(self):
        self.start()
        prior = self.h.archive.event(self.memory.event_ids[0])
        event = SourceEvent(
            "owner", "My preferred answer is amber", "synthetic", time() - 1, corrects=prior.id
        )
        self.h.archive.append(event, retain_authorized=True)
        MemoryWriter(self.h.archive).retain(
            (event.id,),
            event.content,
            "preference",
            retain_authorized=True,
            inferred=False,
            supersedes=self.memory.id,
        )
        self.h.executive.tick()
        self.assertEqual([], self.requests)

    def test_memory_capability_withdrawal_prevents_model_io(self):
        self.start()
        node = self.h.store.get("node", self.h.node_id)
        self.h.store.put(
            "node",
            self.h.node_id,
            {
                **node,
                "capabilities": [c for c in node["capabilities"] if c["id"] != "memory.recall"],
            },
        )
        self.h.executive.tick()
        self.assertEqual([], self.requests)

    def test_policy_denial_of_recall_capability_prevents_model_io(self):
        self.start()
        PersonalPolicy(self.h.store).save(
            PolicyRule(
                "withdraw-recall",
                "memory.recall",
                PolicyEffect.DENY,
                "synthetic-owner",
                time(),
                time(),
                {},
            ),
            owner_authorized=True,
        )
        self.h.executive.tick()
        self.assertEqual([], self.requests)

    def test_full_delegation_without_memory_cannot_silently_add_it(self):
        self.prepare()
        self.delegate(actions=("files.write",))
        result = PlannerAuthoring(self.h).conversation(
            "Create worker Answer: Write answer.txt using my preferred answer",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertEqual("blocked", result["state"])
        self.assertEqual([], self.requests)

    def test_private_memory_and_verified_tool_observations_compose(self):
        self.start()
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": self.steps,
                "observe": True,
            }
        )
        self.h.executive.tick()
        self.complete(self.review(self.accept_change(self.row)))
        self.h.executive.tick()
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    **self.steps[0],
                    "capability_id": "files.write",
                    "intent": asdict(Intent("Save answer", "file_write", "answer.txt", "violet")),
                }
            ]
        )
        self.complete(self.review(self.accept_change(self.row)))
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        prompt = json.dumps(self.requests[-1])
        self.assertIn("My preferred answer is violet", prompt)
        self.assertIn("Untrusted tool observations", prompt)
        self.h.archive.forget(self.memory.id, owner_authorized=True)
        with self.assertRaises(PermissionError):
            self.complete(self.review(self.accept_change(self.row)))
        self.assertFalse((self.h.files.root / "answer.txt").exists())
