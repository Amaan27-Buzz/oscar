"""Model-authored private native account requests over real synthetic HTTP."""

import importlib.util
import json
import unittest
from dataclasses import asdict
from time import monotonic, sleep
from unittest.mock import patch

from oscar.assistance import Assistance
from oscar.connector_mount import account_manifests
from oscar.connectors import CredentialRef
from oscar.jev import Intent
from oscar.oauth_device import VaultResolver
from oscar.planner_authoring import PlannerAuthoring
from tests import test_planner_authoring as fixture
from tests import test_planner_connectors as connector_fixture
from tests.test_communication import Provider
from tests.test_connections import PrivateVault


class HTTPPlanningTests(unittest.TestCase):
    signature = fixture.PlannerAuthoringTests.signature
    review = fixture.PlannerAuthoringTests.review
    complete = fixture.PlannerAuthoringTests.complete
    close = fixture.PlannerAuthoringTests.close
    draft = fixture.PlannerAuthoringTests.draft
    accept_change = fixture.PlannerAuthoringTests.accept_change
    assert_private = connector_fixture.MCPPlanningTests.assert_private
    grant_full = connector_fixture.MCPPlanningTests.grant_full

    def setUp(self):
        fixture.PlannerAuthoringTests.setUp(self)
        self.api = Provider()
        self.addCleanup(self.api.close)
        transport = patch("oscar.connectors.build_opener", return_value=self.api.opener())
        transport.start()
        self.addCleanup(transport.stop)
        self.vault = PrivateVault()
        self.vault.put("synthetic-http-planning-token", reference="planning-tasks")
        self.h.connectors.secrets = VaultResolver(self.vault)
        self.account = self.h.accounts.add("google", "synthetic", "tasks", "Tasks", verified=True)
        self.manifest = next(m for m in account_manifests() if m.id == "google.tasks")
        self.scopes = {s for c in self.manifest.capabilities for s in c.scopes}
        self.bind()
        self.mount = self.h.ensure_connections()
        self.cap = self.mount.capability("google.tasks.create", account_id=self.account.id)
        self.grants |= frozenset({"connectors:read", "connectors:write"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            self.h.store.put(
                kind,
                identifier,
                {
                    **self.h.store.get(kind, identifier),
                    "scopes": sorted(self.grants),
                },
            )
        self.executor.connector_plans = self.h.connector_plans
        self.executor.grid = self.h.grid
        self.marker = "Synthetic private HTTP title a3257"
        self.steps = [
            {
                "id": "create",
                "node_id": self.mount.node_id,
                "capability_id": self.cap.id,
                "depends_on": [],
                "intent": asdict(
                    Intent(
                        "Invoke requested endpoint",
                        "capability",
                        capability_kind=self.cap.id,
                        parameters={
                            "arguments": {
                                "path": {"tasklist": "selected-list"},
                                "body": {"title": self.marker},
                            }
                        },
                    )
                ),
            }
        ]
        self.change["value"].update(
            goal="Write a synthetic record",
            capabilities=[
                {"node_id": self.h.node_id, "capability_id": "models.reason"},
                {"node_id": self.mount.node_id, "capability_id": self.cap.id},
            ],
        )
        self.response()

    def bind(self):
        self.account = self.h.accounts.bind(
            self.account.id,
            self.manifest.id,
            CredentialRef("planning-tasks"),
            self.scopes,
            self.manifest.base_url,
        )

    def response(self):
        self.body["choices"][0]["message"]["content"] = json.dumps({"steps": self.steps})

    def finish(self):
        deadline = monotonic() + 10
        while monotonic() < deadline:
            self.h.executive.tick()
            if len(self.h.store.all("task")) == 2 and self.h.store.all("task")[-1]["state"] in {
                "partially_verified",
                "failed",
                "blocked",
                "unknown",
            }:
                break
            sleep(0.02)
        self.assertEqual("partially_verified", self.h.store.all("task")[-1]["state"])
        self.assertEqual(1, len(self.api.calls))
        self.assert_private()

    def test_ask_reviews_exact_endpoint_and_private_body_before_real_http_effect(self):
        row = self.draft()
        self.assertEqual([], self.api.calls)
        plan = self.review(self.accept_change(row))
        self.assertIn(self.marker, plan["review"])
        self.assertIn("selected-list", plan["review"])
        self.assert_private()
        self.complete(plan)
        self.h.executive.tick()
        pending = Assistance(self.h).snapshot(self.grants)["pending_actions"]
        self.assertEqual(1, len(pending))
        self.assertEqual([], self.api.calls)
        action = self.review(
            {"operation": "confirm_task", "id": pending[0]["task_id"], "value": {}}
        )
        self.assertIn(self.marker, action["review"])
        self.complete(action)
        self.finish()
        self.assertEqual(
            ("POST", "/tasks/v1/lists/selected-list/tasks", {"title": self.marker}),
            self.api.calls[0],
        )
        self.assertEqual(
            self.marker,
            self.api.resources["/tasks/v1/lists/selected-list/tasks/synthetic-resource"]["title"],
        )
        self.assertEqual("Bearer synthetic-http-planning-token", self.api.requests[0][1])

    def test_full_calls_only_the_delegated_account_without_action_reviews(self):
        self.grant_full([self.account.id])
        result = PlannerAuthoring(self.h).conversation(
            "Write a synthetic record",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        self.finish()
        self.assertEqual([], self.h.store.all("assistance_review"))
        self.assertEqual([], self.h.store.all("executive_confirmation"))

    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "optional schema validator absent")
    def test_compact_decoder_uses_selected_connector_arguments_and_native_ids(self):
        from jsonschema import Draft202012Validator

        from oscar.planning_contract import executive_plan_schema

        schema = executive_plan_schema(
            connector_schemas={
                self.cap.id: self.h.connector_plans.contract(asdict(self.cap))["schema"]
            },
            native_capabilities=("files.write",),
        )
        validator = Draft202012Validator(schema)
        self.compact_response()
        self.assertTrue(validator.is_valid({"steps": self.steps}))
        self.steps[0]["arguments"]["path"] = {}
        self.assertFalse(validator.is_valid({"steps": self.steps}))
        canonical = {
            "id": "write",
            "node_id": self.mount.node_id,
            "capability_id": self.cap.id,
            "depends_on": [],
            "inputs": [],
            "intent": asdict(Intent("Write", "capability", capability_kind=self.cap.id)),
        }
        self.assertFalse(validator.is_valid({"steps": [canonical]}))
        self.assertEqual(
            ["files.write"],
            schema["oneOf"][0]["properties"]["steps"]["items"]["oneOf"][-1]["properties"][
                "capability_id"
            ]["enum"],
        )

    def compact_response(self):
        step = self.steps[0]
        self.steps = [
            {
                "id": step["id"],
                "capability_id": step["capability_id"],
                "arguments": step["intent"]["parameters"]["arguments"],
                "depends_on": [],
            }
        ]
        self.response()

    def test_compact_effect_preserves_ask_review_and_private_arguments(self):
        self.compact_response()
        self.test_ask_reviews_exact_endpoint_and_private_body_before_real_http_effect()

    def test_compact_effect_preserves_full_account_delegation(self):
        self.compact_response()
        self.test_full_calls_only_the_delegated_account_without_action_reviews()

    def test_compact_effect_cannot_select_an_unreviewed_account(self):
        self.compact_response()
        self.steps[0]["capability_id"] = "native-account-" + "f" * 24 + ":google.tasks.create"
        self.response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual([], self.api.calls)
        self.assertEqual({}, self.h.connector_plans.inputs)

    def test_full_missing_account_cannot_fall_back_to_native_ask(self):
        self.grant_full([])
        PlannerAuthoring(self.h).conversation(
            "Write a synthetic record",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        deadline = monotonic() + 10
        while monotonic() < deadline:
            self.h.executive.tick()
            if self.h.executive.health == "waiting_for_authority":
                break
            sleep(0.02)
        self.assertEqual(1, len(self.requests))
        self.assertEqual("planned", self.h.store.all("task")[-1]["state"])
        self.assertEqual("waiting_for_authority", self.h.executive.health)
        self.assertEqual([], self.api.calls)
        self.assertEqual([], self.h.connector_plans.pending(self.grants))
        with self.assertRaises(PermissionError):
            self.review(
                {"operation": "confirm_task", "id": self.h.store.all("task")[-1]["id"], "value": {}}
            )

    def test_read_only_endpoint_uses_fixed_get_without_body_or_action_confirmation(self):
        self.cap = self.mount.capability("google.tasks.list", account_id=self.account.id)
        self.steps[0]["capability_id"] = self.cap.id
        self.steps[0]["intent"]["capability_kind"] = self.cap.id
        self.steps[0]["intent"]["parameters"]["arguments"] = {
            "path": {"tasklist": "selected-list"},
            "query": {"maxResults": 10},
        }
        self.change["value"]["capabilities"][-1]["capability_id"] = self.cap.id
        self.response()
        row = self.draft()
        self.complete(self.review(self.accept_change(row)))
        self.finish()
        self.assertEqual(("GET", "/tasks/v1/lists/selected-list/tasks", None), self.api.calls[0])
        self.assertEqual(
            "/tasks/v1/lists/selected-list/tasks?maxResults=10", self.api.requests[0][0]
        )
        self.assertEqual([], self.h.store.all("executive_confirmation"))

    def test_model_cannot_supply_origin_headers_or_unreviewed_transport_fields(self):
        self.steps[0]["intent"]["parameters"]["arguments"]["url"] = "https://example.invalid"
        self.response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual({}, self.h.connectors.requests)
        self.assertEqual([], self.api.calls)
        self.assert_private()

    def test_endpoint_rejects_missing_resource_ids_and_unknown_query_fields(self):
        self.steps[0]["intent"]["parameters"]["arguments"] = {
            "path": {},
            "query": {"credential": "not-an-endpoint-field"},
            "body": {"title": self.marker},
        }
        self.response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual([], self.api.calls)
        self.assert_private()

    def test_account_rotation_after_signed_review_blocks_http_effect(self):
        row = self.draft()
        review = self.review(self.accept_change(row))
        self.bind()
        self.mount.refresh()
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual([], self.api.calls)
        self.assert_private()
