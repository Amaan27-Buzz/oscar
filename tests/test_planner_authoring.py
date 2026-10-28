"""Real synthetic HTTP provider through Router; two native signatures precede effects."""

import json
import unittest
from dataclasses import asdict, replace

from oscar.credentials import CredentialPool
from oscar.harness import ModelExecutor
from oscar.jev import Intent
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_authoring import PlannerAuthoring
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.router import Router
from tests import test_assistance as assistance_fixture
from tests import test_authority as authority_fixture
from tests import test_providers as provider_fixture


class PlannerAuthoringTests(unittest.TestCase):
    signature = assistance_fixture.AssistanceTests.signature
    review = assistance_fixture.AssistanceTests.review
    complete = assistance_fixture.AssistanceTests.complete

    def delegate(self, mode="full", actions=("math.add",)):
        payload = authority_fixture.StandingAuthorityTests.payload(
            self,
            mode,
            capabilities=[
                {"node_id": self.h.node_id, "session_id": self.h.session.id, "capability_id": c}
                for c in ("models.reason", *actions)
            ],
        )
        review = self.authority.challenge(
            self.owner.node_id, self.owner.id, self.owner_scope, self.grants, payload
        )
        return self.authority.complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            self.signature(review),
        )

    def conversation(self):
        return PlannerAuthoring(self.h).conversation(
            "Plan the requested calculation",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )

    def revoke(self):
        self.authority.revoke(self.owner.node_id, self.owner.id, self.owner_scope, self.grants)

    def test_full_access_progresses_once_without_per_action_reviews(self):
        self.delegate()
        self.assertIn("assistance_started", self.conversation())
        self.assertEqual([], self.requests)
        self.h.executive.tick()
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual(
            ["partially_verified", "verified"], [t["state"] for t in self.h.store.all("task")]
        )
        self.assertEqual("accepted", PlannerAuthoring(self.h).snapshot()[0]["state"])
        owners = self.h.store.all("executive_owner")
        self.assertEqual(2, len(owners))
        self.assertEqual(owners[0]["standing"], owners[1]["standing"])

    def test_full_access_model_plan_writes_and_independently_reads_back_real_file(self):
        self.delegate(actions=("files.write",))
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    **self.steps[0],
                    "capability_id": "files.write",
                    "intent": asdict(
                        Intent("Save explicit goal", "file_write", "result.txt", "Delegated result")
                    ),
                }
            ]
        )
        self.assertIn("assistance_started", self.conversation())
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual(
            "Delegated result", (self.h.files.root / "result.txt").read_text(encoding="utf-8")
        )
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual(2, len(self.h.store.all("task")))

    def test_expired_grant_does_not_accept_model_effects(self):
        self.delegate()
        self.conversation()
        self.h.executive.tick()
        self.now += 601
        self.h.executive.tick()
        self.assertEqual(1, len(self.h.store.all("executive_goal")))
        self.assertEqual("blocked", PlannerAuthoring(self.h).snapshot()[0]["state"])

    def test_ask_and_secure_keep_model_and_effect_reviews(self):
        for mode in ("ask", "secure"):
            if mode == "secure":
                self.delegate(mode)
            with self.subTest(mode=mode):
                self.assertIn("assistance_proposal", self.conversation())
                self.h.executive.tick()
                self.assertEqual([], self.requests)
                self.assertEqual([], self.h.store.all("planner_request"))

    def test_revocation_before_model_io_stops_planning(self):
        self.delegate()
        self.conversation()
        self.revoke()
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual([], self.requests)
        self.assertEqual(1, len(self.h.store.all("executive_goal")))

    def test_revocation_after_model_result_prevents_automatic_acceptance(self):
        self.delegate()
        self.conversation()
        self.h.executive.tick()
        self.revoke()
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual(1, len(self.h.store.all("executive_goal")))
        self.assertEqual("blocked", PlannerAuthoring(self.h).snapshot()[0]["state"])

    def test_revocation_after_acceptance_stops_effect_without_falling_back_to_ask(self):
        self.delegate()
        self.conversation()
        self.h.executive.tick()
        PlannerAuthoring(self.h).advance_delegated()
        self.assertEqual(2, len(self.h.store.all("executive_goal")))
        self.revoke()
        self.h.executive.tick()
        self.assertNotIn("verified", [t["state"] for t in self.h.store.all("task")])

    def test_replacement_grant_cannot_adopt_original_planning(self):
        self.delegate()
        self.conversation()
        self.h.executive.tick()
        self.revoke()
        self.delegate()
        self.h.executive.tick()
        self.assertEqual(1, len(self.h.store.all("executive_goal")))
        self.assertEqual("blocked", PlannerAuthoring(self.h).snapshot()[0]["state"])

    def test_model_cannot_add_effects_outside_standing_scope(self):
        self.delegate()
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    **self.steps[0],
                    "capability_id": "files.write",
                    "intent": asdict(Intent("Write", "file_write", "escape.txt", "unapproved")),
                }
            ]
        )
        self.conversation()
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual("blocked", PlannerAuthoring(self.h).snapshot()[0]["state"])
        self.assertFalse((self.h.files.root / "escape.txt").exists())

    def setUp(self):
        assistance_fixture.AssistanceTests.setUp(self)
        assistance_fixture.AssistanceTests.create(self)
        self.grants |= frozenset({"models"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            self.h.store.put(
                kind,
                identifier,
                {**self.h.store.get(kind, identifier), "scopes": sorted(self.grants)},
            )
        provider_fixture.ProviderContractTests.setUp(self)
        self.provider = replace(self.provider, credential_envs={"synthetic": "SYNTHETIC_PLANNER"})
        model = ModelSpec(
            "fixture",
            "fixture-model",
            frozenset({"text"}),
            2,
            {"reasoning": 1},
            8192,
            4096,
            Funding.FREE,
            provenance="synthetic HTTP fixture",
        )
        registry = Registry([self.provider], [model])
        pool = CredentialPool(
            [self.provider],
            {"SYNTHETIC_PLANNER": "synthetic-planner-key"},
            self.h.store,
            lambda: self.now,
        )
        router = Router(
            registry, pool, {"openai": HTTPAdapter("openai")}, self.h.store, lambda: self.now
        )
        self.executor = ModelExecutor(
            router,
            ModelRequest("template", "template", "", max_output_tokens=2048),
            RoutingPolicy(),
        )
        self.h.dispatcher.executors["models.reason"] = self.executor
        self.steps = [
            {
                "id": "sum",
                "intent": asdict(Intent("2 + 3")),
                "node_id": self.h.node_id,
                "capability_id": "math.add",
                "depends_on": [],
            }
        ]
        self.body["choices"][0]["message"]["content"] = json.dumps(self.steps)
        self.change = {
            "operation": "plan_draft",
            "id": "new",
            "value": {
                "name": "Reviewed planner",
                "goal": "Calculate the requested sum",
                "mode": "private",
                "capabilities": [
                    {"node_id": self.h.node_id, "capability_id": c}
                    for c in ("models.reason", "math.add")
                ],
            },
        }

    def close(self):
        provider_fixture.ProviderContractTests.close(self)

    def draft(self):
        review = self.review(self.change)
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("executive_worker"))
        self.complete(review)
        self.h.executive.tick()
        return self.h.store.all("planner_request")[0]

    def accept_change(self, row):
        return {
            "operation": "plan_accept",
            "id": row["id"],
            "value": {"start_at": None, "interval_seconds": None, "max_runs": 1, "priority": 0},
        }

    def test_two_exact_reviews_real_router_and_no_model_authority(self):
        row = self.draft()
        self.assertEqual(1, len(self.requests))
        self.assertEqual("partially_verified", self.h.store.all("task")[0]["state"])
        self.assertEqual("reported", PlannerAuthoring(self.h).snapshot()[0]["state"])
        review = self.review(self.accept_change(row))
        self.assertIn("math.add", review["review"])
        self.h.executive.tick()
        self.assertEqual(1, len(self.h.store.all("task")))
        self.complete(review)
        self.h.executive.tick()
        self.assertEqual(
            ["partially_verified", "verified"], [t["state"] for t in self.h.store.all("task")]
        )
        with self.assertRaises(PermissionError):
            self.complete(review)

    def test_model_graph_rejects_duplicate_missing_self_and_cyclic_dependencies(self):
        from copy import deepcopy

        first = self.steps[0]
        second = {**first, "id": "second"}
        for graph in (
            [first, first],
            [{**first, "depends_on": ["absent"]}],
            [{**first, "depends_on": [first["id"]]}],
            [{**first, "depends_on": ["second"]}, {**second, "depends_on": [first["id"]]}],
        ):
            with self.subTest(graph=graph):
                self.body["choices"][0]["message"]["content"] = json.dumps(deepcopy(graph))
                self.complete(self.review(self.change))
                self.h.executive.tick()
                with self.assertRaises(ValueError):
                    self.h.executive.result_plan(self.h.store.all("task")[-1]["id"])
        self.assertTrue(all(t["state"] == "partially_verified" for t in self.h.store.all("task")))

    def test_structured_ollama_plan_constrains_decoding_and_keeps_both_reviews(self):
        from oscar.planning_contract import executive_plan_schema

        router = self.executor.router
        router.registry.providers["fixture"] = replace(self.provider, adapter="ollama")
        router.registry.models = {
            key: replace(model, capabilities=frozenset({"text", "structured"}))
            for key, model in router.registry.models.items()
        }
        router.adapters = {"ollama": HTTPAdapter("ollama")}
        self.executor.template = replace(
            self.executor.template, required=frozenset({"text", "structured"})
        )
        self.body = {"message": {"content": json.dumps({"steps": self.steps})}, "done": True}
        row = self.draft()
        self.assertEqual(executive_plan_schema(), self.requests[0]["body"]["format"])
        self.assertEqual(["partially_verified"], [t["state"] for t in self.h.store.all("task")])
        review = self.review(self.accept_change(row))
        self.h.executive.tick()
        self.assertEqual(1, len(self.h.store.all("task")))
        self.complete(review)
        self.h.executive.tick()
        self.assertEqual(
            ["partially_verified", "verified"], [t["state"] for t in self.h.store.all("task")]
        )

    def test_decoding_does_not_replace_authoritative_instruction_length_limit(self):
        self.steps[0]["intent"]["text"] = "x" * 4097
        self.body["choices"][0]["message"]["content"] = json.dumps(self.steps)
        row = self.draft()
        with self.assertRaisesRegex(ValueError, "bounded step instruction"):
            self.review(self.accept_change(row))
        self.assertEqual(1, len(self.h.store.all("task")))

    def test_provider_drift_prevents_call_and_unavailable_route_creates_nothing(self):
        review = self.review(self.change)
        self.executor.router.registry.providers["fixture"] = replace(
            self.provider, base_url="http://127.0.0.1:1"
        )
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual([], self.requests)
        self.executor.router.pool.slots["synthetic"].present = False
        with self.assertRaises(PermissionError):
            self.review(self.change)
        self.assertEqual([], self.h.store.all("executive_worker"))

    def test_untrusted_scope_escalation_and_result_drift_are_rejected(self):
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    **self.steps[0],
                    "capability_id": "files.write",
                    "intent": asdict(Intent("Write", "file_write", "escape.txt", "unapproved")),
                }
            ]
        )
        row = self.draft()
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(row))
        self.assertFalse((self.h.files.root / "escape.txt").exists())

    def test_private_mode_excludes_public_source_before_review(self):
        self.executor.router.registry.providers["fixture"] = replace(
            self.provider, local=False, private=False
        )
        with self.assertRaises(PermissionError):
            self.review(self.change)
        self.assertEqual([], self.requests)

    def test_result_or_original_owner_scope_drift_invalidates_second_review(self):
        row = self.draft()
        review = self.review(self.accept_change(row))
        result = self.h.store.all("result")[0]
        self.h.store.put(
            "result", result["id"], {**result, "value": json.dumps(self.steps, indent=2)}
        )
        with self.assertRaises(PermissionError):
            self.complete(review)
        review = self.review(self.accept_change(row))
        owner = self.h.store.get("session", self.owner.id)
        self.h.store.put(
            "session",
            self.owner.id,
            {**owner, "scopes": [g for g in owner["scopes"] if g != "math"]},
        )
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual(1, len(self.h.store.all("executive_goal")))

    def test_provider_contract_change_after_approval_never_reaches_http(self):
        self.complete(self.review(self.change))
        self.executor.router.registry.providers["fixture"] = replace(
            self.provider, base_url="http://127.0.0.1:1"
        )
        self.h.executive.tick()
        self.assertEqual([], self.requests)

    def test_malformed_model_output_is_not_a_reviewable_plan(self):
        self.body["choices"][0]["message"]["content"] = '{"authority": "full"}'
        row = self.draft()
        with self.assertRaises(ValueError):
            self.review(self.accept_change(row))
        self.assertEqual(1, len(self.h.store.all("executive_goal")))

    def test_routing_configuration_change_after_result_invalidates_second_review(self):
        row = self.draft()
        review = self.review(self.accept_change(row))
        self.executor.policy = replace(self.executor.policy, allow_paid=True)
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual(1, len(self.h.store.all("executive_goal")))

    def test_config_change_after_planning_approval_blocks_before_model_io(self):
        self.complete(self.review(self.change))
        self.executor.policy = replace(self.executor.policy, allow_paid=True)
        self.h.executive.tick()
        self.assertEqual([], self.requests)

    def test_provider_source_change_after_result_requires_fresh_planning(self):
        row = self.draft()
        self.executor.router.registry.providers["fixture"] = replace(
            self.provider, provenance="reconfigured source"
        )
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(row))
        self.assertEqual(1, len(self.h.store.all("executive_goal")))
