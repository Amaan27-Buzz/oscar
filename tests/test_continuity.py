import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.continuity import (
    ActiveContext,
    ContextObservation,
    LiveContextFederation,
    LocalMemory,
    MemoryItem,
    MemoryType,
)
from oscar.contracts import Epistemic, Evidence, record
from oscar.entities import Entity, EntityGraph, EntityRelation, EntityType
from oscar.freshness import Authority, SourceRef
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.storage import StateConflict, Store


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state.sqlite")
        self.now = time()
        self.memory = LocalMemory(
            self.store,
            clock=lambda: self.now,
            redact=lambda s: s.replace("synthetic-private-key", "<redacted>"),
        )
        self.source = SourceRef(
            "local://reference", Authority.CACHE, "local", self.now - 1000, evidence_id="proof"
        )
        self.item = MemoryItem(
            "m1",
            "repository.status",
            "old state",
            "project",
            MemoryType.PROJECT,
            self.source,
            self.now - 1000,
            retention_reason="explicit selected project summary",
        )

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_persistent_retrieval_is_scoped_and_recalled(self):
        self.memory.retain(self.item, retention_authorized=True)
        self.store.close()
        self.store = Store(self.root / "state.sqlite")
        memory = LocalMemory(self.store)
        recalled = memory.retrieve("repository", "project")
        self.assertEqual(1, len(recalled))
        self.assertEqual(Epistemic.RECALLED, recalled[0].evidence_state)
        self.assertEqual((), memory.retrieve("repository", "another-project"))

    def test_retention_credentials_delete_and_expiry(self):
        with self.assertRaises(PermissionError):
            self.memory.retain(self.item, retention_authorized=False)
        with self.assertRaises(ValueError):
            self.memory.retain(
                replace(self.item, content="synthetic-private-key"), retention_authorized=True
            )
        expired = replace(self.item, expires_at=self.now - 1)
        self.memory.retain(expired, retention_authorized=True)
        self.assertEqual((), self.memory.retrieve("", "project"))
        self.assertEqual(1, self.memory.purge_expired())
        self.memory.retain(self.item, retention_authorized=True)
        with self.assertRaises(PermissionError):
            self.memory.forget("m1", owner_authorized=False)
        self.memory.forget("m1", owner_authorized=True)
        self.assertEqual([], self.store.all("memory"))

    def test_historical_verification_requires_real_evidence_and_recall_downgrades(self):
        item = replace(
            self.item,
            evidence_state=Epistemic.VERIFIED,
            source=replace(self.source, observed_at=self.now),
        )
        with self.assertRaises(KeyError):
            self.memory.retain(item, retention_authorized=True)
        evidence = Evidence(
            "proof",
            "task",
            "correlation",
            "inspector",
            "direct comparison",
            self.now,
            True,
            Epistemic.VERIFIED,
            "matched",
            content_hash=hashlib.sha256(item.content.encode()).hexdigest(),
        )
        self.store.put("evidence", evidence.id, record(evidence))
        self.memory.retain(item, retention_authorized=True)
        self.assertEqual(
            Epistemic.RECALLED, self.memory.retrieve("repository", "project")[0].evidence_state
        )
        self.assertEqual(Epistemic.VERIFIED, self.store.get("memory", "m1")["evidence_state"])

    def test_live_authority_overrides_stale_memory(self):
        self.memory.retain(self.item, retention_authorized=True)
        live_source = SourceRef("local://repository", Authority.LIVE_API, "local", self.now, 5)
        live = ContextObservation(
            "repository.status", "actual state", "project", live_source, Epistemic.KNOWN
        )
        active = ActiveContext(
            "task", "project", (live,), self.memory.retrieve("repository", "project")
        )
        self.assertEqual("actual state", active.resolve("repository.status", self.now).value)
        self.assertEqual(
            Epistemic.RECALLED, active.resolve("repository.status", self.now + 10).state
        )
        self.assertEqual("old state", active.resolve("repository.status", self.now + 10).value)
        wrong_scope = replace(live, scope="another-project")
        self.assertEqual(
            "old state",
            replace(active, live=(wrong_scope,)).resolve("repository.status", self.now).value,
        )

    def test_current_api_response_outranks_stale_memory_without_status_upgrade(self):
        self.memory.retain(self.item, retention_authorized=True)
        live_source = SourceRef(
            "https://api.example.com/current", Authority.LIVE_API, "account", self.now, 5
        )
        live = ContextObservation(
            "repository.status",
            "current provider observation",
            "project",
            live_source,
            Epistemic.REPORTED,
        )
        active = ActiveContext(
            "task", "project", (live,), self.memory.retrieve("repository", "project")
        )
        resolved = active.resolve("repository.status", self.now)
        self.assertEqual("current provider observation", resolved.value)
        self.assertEqual(Epistemic.REPORTED, resolved.state)

    def test_recalled_or_reported_never_becomes_authoritative(self):
        live_source = SourceRef("local://claims", Authority.LIVE_API, "local", self.now)
        reported = ContextObservation(
            "status", "Worker says done", "project", live_source, Epistemic.REPORTED
        )
        active = ActiveContext("task", "project", (reported,), ())
        self.assertEqual(Epistemic.REPORTED, active.resolve("status", self.now).state)
        recalled = replace(reported, state=Epistemic.RECALLED)
        self.assertEqual(
            Epistemic.RECALLED, replace(active, live=(recalled,)).resolve("status", self.now).state
        )

    def test_federation_partial_failures_and_no_automatic_retention(self):
        source = self.source

        class Live:
            id = "fixture-live"

            def retrieve(self, query, scope):
                return (
                    ContextObservation(
                        "status", "selected reference", scope, source, Epistemic.REPORTED
                    ),
                )

        class Unavailable:
            id = "fixture-unavailable"

            def retrieve(self, query, scope):
                raise OSError("fixture")

        federation = LiveContextFederation(self.memory, (Live(), Unavailable()))
        context = federation.assemble("task", "status", "project")
        self.assertEqual(1, len(context.live))
        self.assertEqual(("fixture-unavailable:unavailable",), context.blockers)
        self.assertEqual([], self.store.all("memory"))

    def test_entity_identity_requires_evidence_and_preserves_unknown(self):
        graph = EntityGraph(self.store)
        graph.add(Entity("p1", EntityType.PERSON, "Same professor", self.now))
        graph.add(Entity("p2", EntityType.PERSON, "Same professor", self.now))
        self.assertEqual(2, len(self.store.all("entity")))
        with self.assertRaises(KeyError):
            graph.bind("p1", "gmail", "account", "address", "missing")
        evidence = Evidence(
            "identity-proof",
            "task",
            "correlation",
            "owner-identity",
            "explicit mapping",
            self.now,
            True,
            Epistemic.KNOWN,
            json.dumps(
                {
                    "entity_id": "p1",
                    "provider": "gmail",
                    "account": "account",
                    "native_id": "address",
                }
            ),
        )
        self.store.put("evidence", evidence.id, record(evidence))
        graph.bind("p1", "gmail", "account", "address", evidence.id)
        with self.assertRaises(ValueError):
            graph.bind("p2", "gmail", "account", "address", evidence.id)
        conflict = replace(
            evidence,
            id="p2-evidence",
            detail=json.dumps(
                {
                    "entity_id": "p2",
                    "provider": "gmail",
                    "account": "account",
                    "native_id": "address",
                }
            ),
        )
        self.store.put("evidence", conflict.id, record(conflict))
        with self.assertRaises(StateConflict):
            graph.bind("p2", "gmail", "account", "address", conflict.id)
        relation_evidence = replace(
            evidence,
            id="relation-evidence",
            detail=json.dumps({"subject": "p1", "relation": "related_to", "target": "p2"}),
        )
        self.store.put("evidence", relation_evidence.id, record(relation_evidence))
        graph.relate(EntityRelation("r1", "p1", "related_to", "p2", relation_evidence.id, self.now))
        graph.forget("p1", owner_authorized=True)
        self.assertEqual([], self.store.all("entity_identity"))
        self.assertEqual([], self.store.all("entity_relation"))
        self.assertEqual(1, len(self.store.all("entity")))

    def test_unrelated_verified_evidence_cannot_promote_memory(self):
        item = replace(
            self.item,
            evidence_state=Epistemic.VERIFIED,
            source=replace(self.source, observed_at=self.now),
        )
        proof = Evidence(
            "proof",
            "task",
            "correlation",
            "inspector",
            "file comparison",
            self.now,
            True,
            Epistemic.VERIFIED,
            "unrelated content",
            content_hash=hashlib.sha256(b"different file").hexdigest(),
        )
        self.store.put("evidence", proof.id, record(proof))
        with self.assertRaises(ValueError):
            self.memory.retain(item, retention_authorized=True)

    def test_context_and_retention_bounds(self):
        with self.assertRaises(ValueError):
            replace(self.item, content="x" * 16001)
        with self.assertRaises(ValueError):
            self.memory.retrieve("", "project", limit=100)
        with self.assertRaises(ValueError):
            replace(self.item, confidence=float("nan"))


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "state.sqlite")
        self.policy = PersonalPolicy(self.store)
        self.now = time()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def rule(self, identifier, capability, effect, conditions=None, **kwargs):
        rule = PolicyRule(
            identifier,
            capability,
            effect,
            "explicit owner",
            self.now,
            self.now,
            conditions or {},
            **kwargs,
        )
        self.policy.save(rule, owner_authorized=True)
        return rule

    def evaluate(self, capability="google.gmail.send", **kwargs):
        return self.policy.evaluate(
            capability,
            ("connectors:external-communication",),
            frozenset({"connectors:external-communication"}),
            **kwargs,
        )

    def test_never_send_without_asking(self):
        self.rule("ask-email", "google.gmail.send", PolicyEffect.ASK)
        self.assertFalse(self.evaluate().allowed)
        self.assertTrue(self.evaluate(confirmed=True).allowed)
        self.assertEqual(("ask-email",), self.evaluate().rule_ids)

    def test_most_specific_and_conflicting_policies(self):
        self.rule("broad", "google.*", PolicyEffect.ASK)
        self.rule("specific", "google.gmail.send", PolicyEffect.DENY, {"context": "university"})
        self.assertFalse(self.evaluate(context={"context": "university"}, confirmed=True).allowed)
        self.rule("conflict", "google.gmail.send", PolicyEffect.ALLOW, {"context": "university"})
        self.assertIn(
            "conflicting", self.evaluate(context={"context": "university"}, confirmed=True).reason
        )

    def test_hard_constraints_permission_confirmation_above_policy(self):
        self.rule("allow", "*", PolicyEffect.ALLOW)
        self.assertFalse(self.evaluate(hard_allowed=False, confirmed=True).allowed)
        self.assertFalse(self.evaluate(confirmation_required=True).allowed)
        decision = self.policy.evaluate("google.gmail.send", ("send",), frozenset(), confirmed=True)
        self.assertFalse(decision.allowed)

    def test_inferred_disabled_and_expired_rules(self):
        candidate = PolicyRule(
            "candidate",
            "*",
            PolicyEffect.ALLOW,
            "model candidate",
            self.now,
            self.now,
            {},
            user_authoritative=False,
        )
        with self.assertRaises(PermissionError):
            self.policy.save(candidate, owner_authorized=True)
        self.rule("disabled", "*", PolicyEffect.DENY, enabled=False)
        self.rule("expired", "*", PolicyEffect.DENY, expires_at=self.now - 1)
        self.assertTrue(self.evaluate().allowed)

    def test_structured_preference_and_persistence(self):
        self.rule("free", "models.*", PolicyEffect.PREFER, preference="free_first")
        decision = self.policy.evaluate("models.reason", (), frozenset())
        self.assertEqual("free_first", decision.preference)
        self.store.close()
        self.store = Store(Path(self.temp.name) / "state.sqlite")
        self.assertEqual("free_first", PersonalPolicy(self.store).rules()[0].preference)
        self.assertNotIn("memory", json.dumps(self.store.all("personal_policy")))
