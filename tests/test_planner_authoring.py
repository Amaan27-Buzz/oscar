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
from tests import test_providers as provider_fixture


class PlannerAuthoringTests(unittest.TestCase):
    signature = assistance_fixture.AssistanceTests.signature
    review = assistance_fixture.AssistanceTests.review
    complete = assistance_fixture.AssistanceTests.complete

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
