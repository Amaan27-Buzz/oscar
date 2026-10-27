"""A connected account catalog must not prevent a bounded conversation Worker."""

import json
import unittest
from dataclasses import asdict, replace

from oscar.connector_mount import account_manifests
from oscar.connectors import CredentialRef
from oscar.jev import Intent
from oscar.planner_authoring import PlannerAuthoring
from tests import test_planner_http_connectors as fixture
from tests import test_planner_task_verification as tasks


class PlanningCatalogTests(unittest.TestCase):
    bind = fixture.HTTPPlanningTests.bind
    response = fixture.HTTPPlanningTests.response
    signature = fixture.HTTPPlanningTests.signature
    review = fixture.HTTPPlanningTests.review
    complete = fixture.HTTPPlanningTests.complete
    close = fixture.HTTPPlanningTests.close
    accept_change = fixture.HTTPPlanningTests.accept_change
    grant_full = fixture.HTTPPlanningTests.grant_full
    assert_private = fixture.HTTPPlanningTests.assert_private
    settle = tasks.PlannedTaskVerificationTests.settle

    def setUp(self):
        fixture.HTTPPlanningTests.setUp(self)
        manifest = next(m for m in account_manifests() if m.id == "microsoft.graph")
        account = self.h.accounts.add(
            "microsoft", "synthetic-catalog", "work", "Work", verified=True
        )
        self.vault.put("synthetic-only", reference="catalog-work")
        self.h.accounts.bind(
            account.id,
            manifest.id,
            CredentialRef("catalog-work"),
            {s for c in manifest.capabilities for s in c.scopes},
            manifest.base_url,
        )
        self.mount.refresh()
        self.grants |= frozenset({"connectors:external-communication", "connectors:destructive"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(self.grants)})
        self.executor.router.registry.models = {
            k: replace(m, context_limit=32768, capabilities=frozenset({"text", "structured"}))
            for k, m in self.executor.router.registry.models.items()
        }
        self.executor.template = replace(
            self.executor.template, required=frozenset({"text", "structured"})
        )
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": [
                    {
                        "id": "save",
                        "node_id": self.h.node_id,
                        "capability_id": "files.write",
                        "depends_on": [],
                        "intent": asdict(
                            Intent(
                                "Write the requested note",
                                "file_write",
                                "catalog-note.txt",
                                "Welcome to OSCAR",
                            )
                        ),
                    }
                ]
            }
        )

    def conversation(self):
        return PlannerAuthoring(self.h).conversation(
            "Write Welcome to OSCAR to catalog-note.txt",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )

    def test_large_connected_catalog_signed_ask_verifies_a_file_without_provider_calls(self):
        proposal = self.conversation()
        self.assertIn("assistance_proposal", proposal)
        self.assertGreater(len(proposal["assistance_proposal"]["value"]["capabilities"]), 16)
        self.assertEqual([], self.requests)
        self.complete(self.review(proposal["assistance_proposal"]))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", self.settle())
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())
        self.assertEqual([], self.api.calls)

    def test_shared_model_schemas_reconstruct_every_exact_connector_contract(self):
        planning = PlannerAuthoring(self.h)
        proposal = self.conversation()["assistance_proposal"]
        state = planning.material("plan_draft", "new", proposal["value"], self.grants)
        prompt = state["step"]["intent"]["parameters"]["prompt"]
        decoder = json.JSONDecoder()
        pins, _ = decoder.raw_decode(prompt.split("Use only these capabilities: ", 1)[1])
        shared_text = prompt.split("Shared connector fields (", 1)[1].split("): ", 1)[1]
        shared, _ = decoder.raw_decode(shared_text)
        referenced = 0
        for pin in pins:
            if pin.get("transport") not in {"https", "mcp"}:
                continue
            cap = next(c for c in state["capabilities"] if c["id"] == pin["capability_id"])
            expected = planning.descriptor(cap, self.h.connector_plans)
            if "argument_schema_ref" in pin:
                schema = shared["argument_schemas"][pin["argument_schema_ref"]]
                referenced += 1
            else:
                schema = pin["argument_schema"]
            self.assertEqual(expected["argument_schema"], schema)
            self.assertEqual(expected["account_id"], pin["account_id"])
            self.assertEqual(expected["endpoint"], pin["endpoint"])
        self.assertGreater(referenced, 1)

    def test_omitted_prompt_change_invalidates_signed_catalog_review(self):
        from unittest.mock import patch

        proposal = self.conversation()["assistance_proposal"]
        reviewed = self.review(proposal)
        self.assertIn("model_input_digest", reviewed["review"])
        original = PlannerAuthoring.descriptor

        def changed(cap, connectors=None):
            result = original(cap, connectors)
            if result.get("transport") == "https":
                result["intent_rule"] += " Changed synthetic model instruction."
            return result

        with patch.object(PlannerAuthoring, "descriptor", side_effect=changed):
            with self.assertRaises(PermissionError):
                self.complete(reviewed)
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("executive_worker"))

    def test_large_catalog_can_create_and_read_back_the_selected_account_task(self):
        self.steps[0]["intent"]["parameters"]["arguments"]["body"] = {
            "title": self.marker,
            "notes": "Selected catalog task",
            "status": "needsAction",
            "due": "2026-10-28T00:00:00Z",
        }
        self.response()
        proposal = self.conversation()["assistance_proposal"]
        self.complete(self.review(proposal))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.h.executive.tick()
        task = self.h.store.all("task")[-1]
        self.complete(self.review({"operation": "confirm_task", "id": task["id"], "value": {}}))
        self.assertEqual("verified", self.settle())
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])
        self.assertTrue(all(c[1].startswith("/tasks/v1/") for c in self.api.calls))

    def test_manual_worker_and_effect_step_bounds_remain_sixteen(self):
        proposal = self.conversation()["assistance_proposal"]
        caps = proposal["value"]["capabilities"]
        pairs = [(c["node_id"], c["capability_id"]) for c in caps]
        with self.assertRaises(ValueError):
            self.h.executive.worker("Manual", pairs, tuple(self.grants), owner_authorized=True)
        worker = self.h.executive.worker(
            "Planner",
            pairs,
            tuple(self.grants),
            owner_authorized=True,
            temporary=True,
        )
        steps = [
            {
                "id": "step-" + str(i),
                "node_id": self.h.node_id,
                "capability_id": "files.write",
                "depends_on": [],
                "intent": asdict(Intent("Write", "file_write", str(i), "value")),
            }
            for i in range(17)
        ]
        with self.assertRaises(ValueError):
            self.h.executive.propose(worker, "Too many effects", steps)
        excessive = [(self.h.node_id, "absent-" + str(i)) for i in range(129)]
        with self.assertRaises(ValueError):
            self.h.executive.worker(
                "Too large",
                excessive,
                tuple(self.grants),
                owner_authorized=True,
                temporary=True,
            )
        with self.assertRaises(ValueError):
            PlannerAuthoring(self.h).capabilities(
                [{"node_id": n, "capability_id": c} for n, c in excessive], self.grants
            )

    def delegate_catalog(self):
        from tests.test_authority import StandingAuthorityTests

        proposal = self.conversation()["assistance_proposal"]
        payload = StandingAuthorityTests.payload(
            self,
            "full",
            capabilities=[
                {
                    **c,
                    "session_id": self.h.executive.targets[c["node_id"]][1].id,
                }
                for c in proposal["value"]["capabilities"]
            ],
            account_ids=[a["id"] for a in self.h.store.all("connected_account")],
        )
        review = self.authority.challenge(
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
            payload,
        )
        self.authority.complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            self.signature(review),
        )

    def test_signed_full_uses_large_catalog_without_per_action_reviews(self):
        self.delegate_catalog()
        self.assertIn("assistance_started", self.conversation())
        self.assertEqual("verified", self.settle())
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        self.assertEqual([], self.h.store.all("assistance_review"))
        self.assertEqual([], self.api.calls)

    def test_revoked_full_catalog_cannot_execute_the_model_suggestion(self):
        self.delegate_catalog()
        self.assertIn("assistance_started", self.conversation())
        self.h.executive.tick()
        self.authority.revoke(self.owner.node_id, self.owner.id, self.owner_scope, self.grants)
        for _ in range(3):
            self.h.executive.tick()
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        self.assertEqual([], self.api.calls)

    def test_state_change_during_full_input_restoration_cannot_execute(self):
        from copy import deepcopy
        from unittest.mock import patch

        review = self.review(self.conversation()["assistance_proposal"])
        original = PlannerAuthoring.material
        calls = 0

        def changed(planning, *args, **kwargs):
            nonlocal calls
            state = original(planning, *args, **kwargs)
            calls += 1
            if calls == 2:
                state = deepcopy(state)
                state["step"]["intent"]["parameters"]["prompt"] += " Changed during restoration."
            return state

        with patch.object(PlannerAuthoring, "material", new=changed):
            with self.assertRaisesRegex(PermissionError, "restoring exact reviewed input"):
                self.complete(review)
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("executive_worker"))
