"""Synthetic owners manage canonical records through the existing signed transport."""

import json
import unittest
from contextlib import contextmanager
from dataclasses import asdict
from time import time
from unittest.mock import patch

from oscar.assistance import Assistance
from oscar.desktop import Desktop
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.grid import NodeRole
from oscar.memory_management import MemoryManagement
from oscar.mobile import fingerprint
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from tests import test_authority as fixture


class MemoryManagementTests(unittest.TestCase):
    setUp = fixture.StandingAuthorityTests.setUp
    signature = fixture.StandingAuthorityTests.signature

    def grant(self, *scopes):
        self.grants |= frozenset(scopes)
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(self.grants)})

    def retain(self, text="The synthetic project is named Copper", relationship=None, **changes):
        event = SourceEvent(
            relationship or self.h.runtime.relationship_id,
            text,
            "owner:test",
            time() - 10,
            sensitivity="personal",
            **{"kind": "conversation_owner", **changes},
        )
        self.h.archive.append(event, retain_authorized=True)
        return MemoryWriter(self.h.archive).retain(
            (event.id,), text, "episodic", retain_authorized=True, inferred=False
        )

    def change(self, memory, operation="memory_forget", **value):
        return {
            "operation": operation,
            "id": memory.id,
            "value": {"digest": fingerprint(asdict(memory)), **value},
        }

    def review(self, change):
        return Assistance(self.h).challenge(
            self.owner.node_id, self.owner.id, self.owner_scope, self.grants, change
        )

    def complete(self, review):
        return Assistance(self.h).complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            self.signature(review),
        )

    def test_inspect_requires_actual_read_scope_and_remains_bounded(self):
        self.retain()
        self.assertEqual([], Assistance(self.h).snapshot()["memory"]["records"])
        self.assertFalse(Assistance(self.h).snapshot(self.grants)["memory"]["available"])
        self.grant("memory:read")
        for index in range(22):
            self.retain(str(index) + " bounded synthetic memory")
        projection = Assistance(self.h).snapshot(self.grants)["memory"]
        self.assertTrue(projection["available"])
        self.assertTrue(projection["truncated"])
        self.assertLessEqual(len(projection["records"]), 20)
        self.assertFalse(any(row["can_manage"] for row in projection["records"]))
        self.assertLess(len(json.dumps(projection).encode()), 12000)

    def test_correct_is_signed_temporal_and_requires_independent_retention(self):
        memory = self.retain()
        self.grant("memory:read", "memory:manage")
        change = self.change(
            memory, "memory_correct", content="The project is named Silver", retain=True
        )
        with self.assertRaises(PermissionError):
            self.review(change)
        self.grant("desktop:conversation:retain")
        review = self.review(change)
        self.assertEqual([memory.id], self.h.archive.fts(self.h.runtime.relationship_id, "Copper"))
        result = self.complete(review)
        self.assertEqual("verified", result["status"])
        current = self.h.archive.memories(self.h.runtime.relationship_id)
        self.assertEqual(["The project is named Silver"], [item.content for item in current])
        self.assertEqual(memory.id, current[0].supersedes)
        recalled = self.h.runtime.memory.retrieve(self.h.runtime.relationship_id, "Silver")
        self.assertTrue(recalled.retrieval_succeeded)
        old = self.h.archive.memories(self.h.runtime.relationship_id, include_history=True)
        self.assertEqual(2, len(old))
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertNotIn("payload", self.h.store.get("assistance_review", review["challenge_id"]))

    def test_forget_propagates_sources_fts_derived_failures_and_restart(self):
        memory = self.retain()
        self.grant("memory:read", "memory:manage")

        class BrokenIndex:
            identity = "synthetic-vector"

            def forget(self, identifiers):
                raise OSError("synthetic unavailable index")

        self.h.runtime.memory.vector = BrokenIndex()
        result = self.complete(self.review(self.change(memory, forget_sources=True)))
        self.assertEqual("partially_verified", result["status"])
        self.assertEqual(["synthetic-vector"], result["failed_indexes"])
        self.assertEqual([], self.h.archive.fts(self.h.runtime.relationship_id, "Copper"))
        with self.assertRaises(KeyError):
            self.h.archive.event(memory.event_ids[0])
        archive = EventArchive(self.h.archive.path)
        try:
            self.assertEqual([], archive.memories(self.h.runtime.relationship_id))
            self.assertEqual([], archive.fts(self.h.runtime.relationship_id, "Copper"))
        finally:
            archive.close()

    def test_cross_relationship_and_digest_generation_drift_rejected(self):
        memory = self.retain()
        foreign = self.retain("Private synthetic other relationship", relationship="other-owner")
        self.grant("memory:read", "memory:manage")
        with self.assertRaises(PermissionError):
            self.review(self.change(foreign, forget_sources=True))
        wrong = self.change(memory, forget_sources=True)
        wrong["value"]["digest"] = "0" * 64
        with self.assertRaises(PermissionError):
            self.review(wrong)
        review = self.review(self.change(memory, forget_sources=True))
        self.retain("Another retained event changes the signed generation")
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual(memory.content, self.h.archive.event(memory.event_ids[0]).content)

    def test_canonical_correction_failure_rolls_back_but_review_never_replays(self):
        memory = self.retain()
        self.grant("memory:read", "memory:manage", "desktop:conversation:retain")
        review = self.review(
            self.change(memory, "memory_correct", content="Replacement statement", retain=True)
        )
        before = self.h.archive.generation(self.h.runtime.relationship_id)
        with patch.object(MemoryWriter, "retain", side_effect=OSError("synthetic storage failure")):
            result = self.complete(review)
        self.assertEqual("unknown", result["status"])
        self.assertEqual(before, self.h.archive.generation(self.h.runtime.relationship_id))
        self.assertEqual(
            [memory.id], [m.id for m in self.h.archive.memories(self.h.runtime.relationship_id)]
        )
        self.assertEqual(
            1, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        with self.assertRaises(PermissionError):
            self.complete(review)

    def test_revocation_between_review_consumption_and_archive_write_prevents_mutation(self):
        for change in ("session", "node", "scopes"):
            with self.subTest(change=change):
                memory = self.retain()
                self.grant("memory:read", "memory:manage")
                review = self.review(self.change(memory, forget_sources=True))
                transaction = self.h.store.transaction
                revoked = False

                @contextmanager
                def revoke_after_consumption(
                    transaction=transaction, review=review, change=change, **kwargs
                ):
                    nonlocal revoked
                    with transaction(**kwargs):
                        yield
                    if (
                        not revoked
                        and not self.h.store.db.in_transaction
                        and self.h.store.get("assistance_review", review["challenge_id"])["used"]
                    ):
                        revoked = True
                        kind = "node" if change == "node" else "session"
                        identifier = self.owner.node_id if kind == "node" else self.owner.id
                        row = self.h.store.get(kind, identifier)
                        self.h.store.put(
                            kind,
                            identifier,
                            {**row, "scopes": []}
                            if change == "scopes"
                            else {**row, "revoked": True},
                        )

                kind = "node" if change == "node" else "session"
                identifier = self.owner.node_id if kind == "node" else self.owner.id
                original = self.h.store.get(kind, identifier)
                try:
                    with patch.object(self.h.store, "transaction", revoke_after_consumption):
                        result = self.complete(review)
                    self.assertTrue(revoked)
                    self.assertEqual("unknown", result["status"])
                    self.assertEqual(
                        memory.content, self.h.archive.event(memory.event_ids[0]).content
                    )
                    with self.assertRaises(PermissionError):
                        self.complete(review)
                finally:
                    self.h.store.put(kind, identifier, original)

    def test_forgetting_memory_alone_preserves_source_and_expires_review_payload(self):
        memory = self.retain()
        self.grant("memory:read", "memory:manage")
        stale = self.review(self.change(memory, forget_sources=True))
        self.now += 31
        MemoryManagement(self.h).snapshot(self.grants)
        self.assertNotIn("payload", self.h.store.get("assistance_review", stale["challenge_id"]))
        review = self.review(self.change(memory, forget_sources=False))
        self.assertEqual("verified", self.complete(review)["status"])
        self.assertEqual(memory.content, self.h.archive.event(memory.event_ids[0]).content)

    def test_retention_scope_does_not_broaden_semantic_sources(self):
        memory = self.retain(kind="note")
        self.grant("memory:read", "memory:manage", "desktop:conversation:retain")
        with self.assertRaises(PermissionError):
            self.review(self.change(memory, "memory_correct", content="Replacement", retain=True))

    def test_policy_read_and_source_retention_denials_remain_authoritative(self):
        memory = self.retain()
        self.grant("memory:read", "memory:manage", "desktop:conversation:retain")
        policy = PersonalPolicy(self.h.store)
        policy.save(
            PolicyRule(
                "deny-retain",
                "desktop.conversation.retain",
                PolicyEffect.DENY,
                "synthetic owner",
                time(),
                time(),
                {"node": self.owner.node_id},
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.review(self.change(memory, "memory_correct", content="Replacement", retain=True))
        policy.save(
            PolicyRule(
                "deny-read",
                "memory.read",
                PolicyEffect.DENY,
                "synthetic owner",
                time(),
                time(),
                {"node": self.owner.node_id},
            ),
            owner_authorized=True,
        )
        self.assertFalse(
            Assistance(self.h).snapshot(self.grants, self.owner.node_id)["memory"]["available"]
        )
        with self.assertRaises(PermissionError):
            self.review(self.change(memory, forget_sources=False))

    def test_generic_native_transport_reloads_canonical_conversation_after_forget(self):
        memory = self.retain()
        self.owner_scope = "control:approve:" + self.h.node_id
        self.grant(
            self.owner_scope,
            "desktop:connect",
            "desktop:text",
            "desktop:inspect",
            "desktop:conversation:read",
            "memory:read",
            "memory:manage",
        )
        row = self.h.store.get("node", self.owner.node_id)
        self.h.store.put("node", self.owner.node_id, {**row, "role": NodeRole.DESKTOP})
        desktop = Desktop(
            self.h.runtime,
            PersonalPolicy(self.h.store),
            {self.h.node_id: (self.h.dispatcher, self.h.session)},
        )

        def call(operation, payload):
            return desktop.request(
                self.owner,
                {
                    "version": 1,
                    "operation": operation,
                    "request_id": "synthetic-memory-" + operation,
                    "payload": payload,
                },
            )

        self.assertEqual(memory.content, call("conversation", {"before": 0})["turns"][0]["text"])
        review = call("assistance_challenge", self.change(memory, forget_sources=True))
        result = call("assistance_complete", self.signature(review))
        self.assertEqual("verified", result["status"])
        self.assertTrue(result["memory_changed"])
        self.assertEqual([], call("conversation", {"before": 0})["turns"])


if __name__ == "__main__":
    unittest.main()
