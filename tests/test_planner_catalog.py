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

    def conversation(self, goal="Write Welcome to OSCAR to catalog-note.txt"):
        return PlannerAuthoring(self.h).conversation(
            goal,
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

    def test_effect_review_shows_used_capabilities_but_binds_the_full_catalog(self):
        from oscar.assistance import Assistance
        from oscar.mobile import fingerprint

        proposal = self.conversation()["assistance_proposal"]
        self.complete(self.review(proposal))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        change = self.accept_change(row)
        state = PlannerAuthoring(self.h).material(
            "plan_accept", row["id"], change["value"], self.grants
        )
        material = Assistance(self.h).material(change, self.grants, self.owner.node_id)
        displayed = material["review"]["current"]
        self.assertEqual(["files.write"], [c["id"] for c in displayed["capabilities"]])
        self.assertEqual(
            fingerprint(state["capabilities"]), displayed["capability_catalog"]["digest"]
        )
        self.assertEqual(len(state["capabilities"]), displayed["capability_catalog"]["count"])
        review = self.review(change)
        other = next(a for a in self.h.store.all("connected_account") if a["id"] != self.account.id)
        self.h.accounts.disconnect(other["id"])
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())

    def test_decoder_kinds_follow_reviewed_catalog_without_exposing_the_planner_as_an_action(self):
        from unittest.mock import patch

        proposal = self.conversation()["assistance_proposal"]
        self.complete(self.review(proposal))
        with patch.object(
            self.executor.router, "execute", wraps=self.executor.router.execute
        ) as execute:
            self.h.executive.tick()
        request = execute.call_args.args[0]
        self.assertNotIn("models.reason", request.executive_native_capabilities)
        self.assertEqual("file_write", request.executive_native_kinds["files.write"])
        self.assertEqual("addition", request.executive_native_kinds["math.add"])
        self.assertFalse(
            set(request.executive_native_kinds) & set(request.executive_connector_schemas)
        )

    def test_shared_capability_id_keeps_both_device_pins_but_one_decoder_hint(self):
        self.shared_capability("file_write")

    def test_shared_id_with_different_contracts_does_not_choose_one_device_kind(self):
        self.shared_capability("addition")

    def shared_capability(self, input_kind):
        from unittest.mock import patch

        from oscar.contracts import Capability
        from oscar.grid import Node, NodeRole

        scopes = ("heartbeat", "advertise", "execute", "files:write")
        self.h.grid.register(Node("second-device", NodeRole.DESKTOP, scopes))
        session = self.h.grid.pair("second-device", scopes)
        cap = next(
            c
            for node in self.h.grid.nodes()
            if node["id"] == self.h.node_id
            for c in node["capabilities"]
            if c["id"] == "files.write"
        )
        self.h.grid.advertise(
            session,
            [Capability(**{**cap, "node_id": session.node_id, "input_kind": input_kind})],
        )
        self.h.executive.targets[session.node_id] = (self.h.dispatcher, session)
        proposal = self.conversation(
            "Across devices " + self.h.node_id + ", second-device: Prepare a welcome file"
        )["assistance_proposal"]
        self.complete(self.review(proposal))
        with patch.object(
            self.executor.router, "execute", wraps=self.executor.router.execute
        ) as execute:
            self.h.executive.tick()
        request = execute.call_args.args[0]
        self.assertEqual(1, request.executive_native_capabilities.count("files.write"))
        if input_kind == "file_write":
            self.assertEqual("file_write", request.executive_native_kinds["files.write"])
        else:
            self.assertNotIn("files.write", request.executive_native_kinds)
        self.assertEqual("partially_verified", self.h.store.all("task")[-1]["state"])
        worker = self.h.store.all("executive_worker")[-1]
        self.assertEqual(
            {self.h.node_id, "second-device"},
            {p["node_id"] for p in worker["capabilities"] if p["capability_id"] == "files.write"},
        )
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", self.settle())
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())

    def test_adaptive_conversation_can_handoff_a_verified_result_within_its_new_plan(self):
        self.handoff_literal("42", matches=True)

    def test_unordered_model_graph_is_reviewed_and_executes_its_exact_verified_handoff(self):
        self.handoff_literal("42", matches=True, reverse=True)

    def test_wrong_verified_result_cannot_replace_the_owner_literal_or_create_a_file(self):
        self.handoff_literal("43", matches=False)

    def handoff_literal(self, literal, *, matches, reverse=False):
        goal = (
            'Calculate 17 + 25, then save its actual result to catalog-note.txt with exact text "'
            + literal
            + '" using inputs.'
        )
        written = json.loads(self.body["choices"][0]["message"]["content"])["steps"][0]
        written["intent"]["content"] = ""
        written["depends_on"] = ["calculate"]
        written["inputs"] = [{"from_step": "calculate", "select": [], "to": ["content"]}]
        calculate = {
            "id": "calculate",
            "node_id": self.h.node_id,
            "capability_id": "math.add",
            "depends_on": [],
            "intent": asdict(Intent("17 + 25")),
        }
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {"steps": [written, calculate] if reverse else [calculate, written]}
        )
        proposal = self.conversation(goal)["assistance_proposal"]
        state = PlannerAuthoring(self.h).material(
            "plan_draft", "new", proposal["value"], self.grants
        )
        prompt = state["step"]["intent"]["parameters"]["prompt"]
        self.assertIn("IN THIS RESPONSE, you MUST add inputs", prompt)
        self.assertIn("Past observation-stage results", prompt)
        from oscar.planning_contract import executive_plan_schema

        self.assertIn(
            "inputs",
            executive_plan_schema()["oneOf"][0]["properties"]["steps"]["items"]["required"],
        )
        self.complete(self.review(proposal))
        self.h.executive.tick()
        change = self.accept_change(self.h.store.all("planner_request")[-1])
        if reverse:
            state = PlannerAuthoring(self.h).material(
                "plan_accept", change["id"], change["value"], self.grants
            )
            self.assertEqual(["calculate", "save"], [s["id"] for s in state["steps"]])
            self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        self.complete(self.review(change))
        for _ in range(5):
            self.h.executive.tick()
        rows = self.h.store.all("task")
        if not matches:
            self.assertEqual(2, len(rows))
            self.assertEqual("verified", rows[-1]["state"])
            self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
            self.assertEqual("waiting_for_verified_input", self.h.executive.health)
            return
        self.assertEqual(3, len(rows))
        self.assertTrue(all(t["state"] == "verified" for t in rows[1:]))
        self.assertEqual("42", (self.h.files.root / "catalog-note.txt").read_text())
        file_task = next(
            t
            for t in self.h.store.all("task")
            if self.h.store.get("plan", t["id"])["kind"] == "file_write"
        )
        self.assertEqual(1, len(self.h.store.get("plan", file_task["id"])["executive"]["inputs"]))

    def test_long_goal_with_connected_catalog_stays_within_durable_frame(self):
        goal = "Write Welcome to OSCAR to catalog-note.txt. " + "Keep the requested content. " * 14
        self.assertLessEqual(len(goal), 480)
        proposal = self.conversation(goal)
        self.complete(self.review(proposal["assistance_proposal"]))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", self.settle())
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())

    def test_changed_exact_literal_never_becomes_a_reviewable_effect(self):
        proposal = self.conversation('Write catalog-note.txt with exact text "Welcome to OSCAR."')
        self.complete(self.review(proposal["assistance_proposal"]))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        from oscar.storage import StateConflict

        self.assertEqual("invalid_model_plan", self.h.store.all("result")[-1]["error"])
        with self.assertRaisesRegex(StateConflict, "Planning stopped"):
            self.review(self.accept_change(row))
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        self.assertEqual([], self.api.calls)

    def test_signed_full_blocks_changed_exact_literal_without_any_file_effect(self):
        self.delegate_catalog()
        result = self.conversation('Write catalog-note.txt with exact text "Welcome to OSCAR."')
        self.assertIn("assistance_started", result)
        for _ in range(5):
            self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        self.assertTrue(row.get("autonomy_blocked"))
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        self.assertEqual([], self.api.calls)
        self.assertEqual([], self.h.store.all("executive_confirmation"))

    def test_matching_escaped_literal_is_written_and_independently_verified(self):
        literal = 'Welcome to OSCAR.\n"Café" '
        response = json.loads(self.body["choices"][0]["message"]["content"])
        response["steps"][0]["intent"]["content"] = literal
        self.body["choices"][0]["message"]["content"] = json.dumps(response)
        proposal = self.conversation(
            "Write catalog-note.txt with exact content: " + json.dumps(literal)
        )
        from oscar.planning_contract import executive_plan_schema

        schema = executive_plan_schema(goal="Write exact text " + json.dumps(literal))
        content = schema["oneOf"][0]["properties"]["steps"]["items"]["properties"]["intent"][
            "properties"
        ]["content"]
        self.assertEqual([None, literal], content["enum"])
        self.complete(self.review(proposal["assistance_proposal"]))
        self.h.executive.tick()
        self.complete(self.review(self.accept_change(self.h.store.all("planner_request")[-1])))
        self.assertEqual("verified", self.settle())
        self.assertEqual(
            literal, (self.h.files.root / "catalog-note.txt").read_text(encoding="utf-8")
        )

    def test_explicit_literal_rejects_ambiguous_targets_and_content_handoffs(self):
        from oscar.executive import validate_file_literal

        step = {"intent": {"kind": "file_write", "content": "A."}}
        for goal, steps in (
            ('Save exact text "A."', [step, step]),
            ('Save exact text "A." and exact content "A."', [step]),
            ("Save exact text A.", [step]),
            ("Save exact text 42", [step]),
        ):
            with self.subTest(goal=goal), self.assertRaises(ValueError):
                validate_file_literal(goal, steps)
        from oscar.planning_contract import exact_file_literal

        for text in ("", 'Describe exact text "quoted" with exact content', "\nA. "):
            self.assertEqual(text, exact_file_literal("Save exact text " + json.dumps(text)))
        validate_file_literal("Save the computed result", [step])
        validate_file_literal('Observe exact text "A."', [{"intent": {"kind": "file_read"}}])

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
            self.assertEqual(expected["account"], shared["accounts"][pin["account_id"]])
            self.assertNotIn("account", pin)
            self.assertEqual(
                expected["operation"], pin.get("operation", pin["capability_id"].rsplit(":", 1)[-1])
            )
            endpoint = dict(pin["endpoint"])
            if "origin_ref" in endpoint:
                endpoint["origin"] = shared["endpoint_origins"][endpoint.pop("origin_ref")]
            self.assertEqual(expected["endpoint"], endpoint)
            self.assertNotIn("node_id", pin)
            self.assertEqual(expected["node_id"], shared["node_id"])
        self.assertGreater(referenced, 1)

    def test_account_labels_are_current_without_disclosing_credential_or_subject(self):
        proposal = self.conversation()["assistance_proposal"]
        state = PlannerAuthoring(self.h).material(
            "plan_draft", "new", proposal["value"], self.grants
        )
        descriptors = [
            PlannerAuthoring.descriptor(c, self.h.connector_plans)
            for c in state["capabilities"]
            if c["output_kind"] == "connector-reference"
        ]
        self.assertGreater(len(descriptors), 1)
        for descriptor in descriptors:
            account = self.h.accounts.get(descriptor["account_id"])
            self.assertEqual(
                {"alias": account.alias, "provider": account.provider}, descriptor["account"]
            )
            self.assertNotIn("subject", descriptor["account"])
            self.assertNotIn("credential", descriptor["account"])

    def test_account_rename_after_review_blocks_model_disclosure(self):
        proposal = self.conversation()["assistance_proposal"]
        reviewed = self.review(proposal)
        self.h.accounts.rename(self.account.id, "Renamed synthetic account")
        with self.assertRaises(PermissionError):
            self.complete(reviewed)
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("executive_worker"))

    def use_ollama(self):
        from oscar.providers import HTTPAdapter

        self.executor.router.adapters["ollama"] = HTTPAdapter("ollama")
        registry = self.executor.router.registry
        registry.providers = {
            key: replace(provider, adapter="ollama") for key, provider in registry.providers.items()
        }
        self.body["message"] = self.body["choices"][0]["message"]
        self.body["done"] = True

    def test_ollama_root_plan_uses_decoder_without_duplicate_schema(self):
        self.use_ollama()
        proposal = self.conversation()["assistance_proposal"]
        state = PlannerAuthoring(self.h).material(
            "plan_draft", "new", proposal["value"], self.grants
        )
        self.assertNotIn("Response JSON schema:", state["step"]["intent"]["parameters"]["prompt"])
        self.assertLess(len(json.dumps([state["step"]], separators=(",", ":"))), 32768)
        self.complete(self.review(proposal))
        self.h.executive.tick()
        self.assertIn("$defs", self.requests[0]["body"]["format"])

    def test_explicit_account_aliases_ignore_quoted_data_and_preserve_case(self):
        from oscar.planning_contract import exact_account_aliases

        self.assertEqual(
            {"google": {"Work"}, "microsoft": {"Team"}},
            exact_account_aliases(
                'Use Google account alias "Work" and Microsoft account alias "Team".'
            ),
        )
        self.assertEqual(
            {}, exact_account_aliases(r'Write exact text "Google account alias \"Work\""')
        )
        self.assertEqual(
            {"google": {'A"B'}}, exact_account_aliases(r'using Google account alias "A\"B"')
        )
        for text in (
            "Google account alias Work",
            "Google account alias 42",
            'Google account alias ""',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                exact_account_aliases(text)

    def test_explicit_account_alias_narrows_the_conversation_catalog(self):
        self.h.accounts.rename(self.account.id, "Personal")
        other = self.h.accounts.add("google", "synthetic-other", "other", "Work", verified=True)
        self.vault.put("synthetic-other-token", reference="planning-other")
        self.h.accounts.bind(
            other.id,
            self.manifest.id,
            CredentialRef("planning-other"),
            self.scopes,
            self.manifest.base_url,
        )
        self.mount.refresh()
        proposal = self.conversation('Create a task using Google account alias "Work".')[
            "assistance_proposal"
        ]
        caps = PlannerAuthoring(self.h).capabilities(proposal["value"]["capabilities"], self.grants)
        google = [
            d
            for c in caps
            if (d := self.h.connector_plans.descriptor(c)) and d["account"]["provider"] == "google"
        ]
        self.assertTrue(google)
        self.assertEqual({other.id}, {d["account_id"] for d in google})
        self.assertTrue(any(c["id"] == "files.write" for c in caps))

    def test_explicit_account_alias_cannot_choose_between_duplicate_accounts(self):
        other = self.h.accounts.add("google", "synthetic-other", "other", "Tasks", verified=True)
        self.vault.put("synthetic-other-token", reference="planning-other")
        self.h.accounts.bind(
            other.id,
            self.manifest.id,
            CredentialRef("planning-other"),
            self.scopes,
            self.manifest.base_url,
        )
        self.mount.refresh()
        result = self.conversation('Create a task using Google account alias "Tasks".')
        self.assertNotIn("assistance_proposal", result)
        self.assertEqual([], self.requests)
        self.assertEqual([], self.api.calls)

    def test_account_goal_guard_rejects_a_different_alias_without_effects(self):
        with self.assertRaisesRegex(PermissionError, "selected account"):
            self.h.connector_plans.check_goal_accounts('Google account alias "Work"', self.steps)
        self.assertEqual([], self.api.calls)
        self.h.connector_plans.check_goal_accounts('Google account alias "Tasks"', self.steps)

    def test_two_explicit_aliases_preserve_both_accounts_without_inventing_step_roles(self):
        other = self.h.accounts.add("google", "synthetic-other", "other", "Work", verified=True)
        self.vault.put("synthetic-other-token", reference="planning-other")
        self.h.accounts.bind(
            other.id,
            self.manifest.id,
            CredentialRef("planning-other"),
            self.scopes,
            self.manifest.base_url,
        )
        self.mount.refresh()
        result = self.conversation(
            'Create tasks using Google account alias "Tasks" and Google account alias "Work".'
        )
        caps = PlannerAuthoring(self.h).capabilities(
            result["assistance_proposal"]["value"]["capabilities"], self.grants
        )
        ids = {
            d["account_id"]
            for c in caps
            if (d := self.h.connector_plans.descriptor(c)) and d["account"]["provider"] == "google"
        }
        self.assertEqual({self.account.id, other.id}, ids)

    def test_malformed_microsoft_task_draft_is_corrected_before_any_provider_effect(self):
        from copy import deepcopy

        account = self.h.accounts.select("microsoft", "microsoft.graph", alias="Work")
        cap = self.mount.capability("microsoft.todo.tasks.create", account_id=account.id)
        self.steps[0].update(capability_id=cap.id, node_id=cap.node_id)
        self.steps[0]["intent"] = asdict(
            Intent(
                "Create selected Microsoft task",
                "capability",
                capability_kind=cap.id,
                parameters={
                    "arguments": {
                        "path": {"listId": "selected-list"},
                        "body": {
                            "title": "Synthetic title",
                            "body": {"contentType": "text", "content": "Synthetic notes"},
                        },
                    }
                },
            )
        )
        self.response()
        self.use_ollama()
        good = deepcopy(self.body)
        bad = deepcopy(good)
        plan = json.loads(bad["message"]["content"])
        plan["steps"][0]["intent"]["parameters"]["arguments"]["body"]["body"] = "Synthetic notes"
        bad["message"]["content"] = json.dumps(plan)
        self.scheduled.extend([(200, bad), (200, good)])
        proposal = self.conversation(
            'Create the requested task using Microsoft account alias "Work".'
        )["assistance_proposal"]
        self.complete(self.review(proposal))
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual([], self.api.calls)
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.h.executive.tick()
        task = self.h.store.all("task")[-1]
        self.complete(self.review({"operation": "confirm_task", "id": task["id"], "value": {}}))
        self.assertEqual("verified", self.settle())
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])

    def test_exact_file_literal_is_corrected_before_effect_review(self):
        from copy import deepcopy

        self.use_ollama()
        good = deepcopy(self.body)
        bad = deepcopy(good)
        plan = json.loads(bad["message"]["content"])
        plan["steps"][0]["intent"]["content"] = "Unrequested text"
        bad["message"]["content"] = json.dumps(plan)
        self.scheduled.extend([(200, bad), (200, good)])
        proposal = self.conversation('Write catalog-note.txt with exact text "Welcome to OSCAR".')[
            "assistance_proposal"
        ]
        self.complete(self.review(proposal))
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", self.settle())
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())

    def test_unselected_account_draft_is_corrected_before_any_provider_effect(self):
        from copy import deepcopy

        other = self.h.accounts.add("google", "synthetic-other", "other", "Personal", verified=True)
        self.vault.put("synthetic-other-token", reference="planning-other")
        self.h.accounts.bind(
            other.id,
            self.manifest.id,
            CredentialRef("planning-other"),
            self.scopes,
            self.manifest.base_url,
        )
        self.mount.refresh()
        wrong_cap = self.mount.capability("google.tasks.create", account_id=other.id)
        self.response()
        self.use_ollama()
        good = deepcopy(self.body)
        bad = deepcopy(good)
        plan = json.loads(bad["message"]["content"])
        step = plan["steps"][0]
        step["capability_id"] = wrong_cap.id
        step["intent"]["capability_kind"] = wrong_cap.id
        bad["message"]["content"] = json.dumps(plan)
        self.scheduled.extend([(200, bad), (200, good)])
        proposal = self.conversation(
            'Create the requested task using Google account alias "Tasks".'
        )["assistance_proposal"]
        self.complete(self.review(proposal))
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual([], self.api.calls)
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.h.executive.tick()
        task = self.h.store.all("task")[-1]
        self.complete(self.review({"operation": "confirm_task", "id": task["id"], "value": {}}))
        self.assertEqual("verified", self.settle())
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])
        objective = self.h.store.get("objective", task["objective_id"])
        self.assertEqual(self.account.id, objective["criterion"]["connector_account"]["id"])

    def test_explicit_provider_selection_rejects_another_provider(self):
        microsoft = next(a for a in self.h.accounts.list_accounts() if a.provider == "microsoft")
        cap = self.mount.capability("microsoft.todo.tasks.create", account_id=microsoft.id)
        steps = [{**self.steps[0], "capability_id": cap.id, "node_id": cap.node_id}]
        with self.assertRaisesRegex(PermissionError, "selected account"):
            self.h.connector_plans.check_goal_accounts('Google account alias "Tasks"', steps)
        self.assertEqual([], self.api.calls)

    def repair_fixture(self, *, second_valid=True, attempts=4, full=False, adapter="ollama"):
        from copy import deepcopy

        from oscar.models import Funding

        self.use_ollama()
        registry = self.executor.router.registry
        registry.providers = {
            key: replace(provider, private=True, adapter=adapter)
            for key, provider in registry.providers.items()
        }
        registry.models = {
            key: replace(model, funding=Funding.LOCAL if adapter == "ollama" else Funding.FREE)
            for key, model in registry.models.items()
        }
        self.executor.policy = replace(self.executor.policy, max_attempts=attempts)
        good = deepcopy(self.body)
        bad = deepcopy(good)
        document = json.loads(bad["message"]["content"])
        document["observe"] = True
        bad["message"]["content"] = json.dumps(document)
        self.scheduled.extend([(200, bad), (200, good if second_valid else bad)])
        self.assertEqual(2, self.executor.planning_configuration()["draft_attempts"])
        if full:
            self.delegate_catalog()
            self.assertIn("assistance_started", self.conversation())
        else:
            proposal = self.conversation()["assistance_proposal"]
            self.complete(self.review(proposal))

    def test_local_draft_corrects_observation_effect_mix_before_signed_effect_review(self):
        self.repair_fixture()
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual([], self.api.calls)
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        histories = self.h.store.all("route_history")
        self.assertFalse(histories[0]["planning_draft_valid"])
        self.assertEqual(histories[0]["id"], histories[1]["planning_repair_of"])
        self.assertTrue(histories[1]["planning_draft_valid"])
        prompts = [request["body"]["messages"][0]["content"] for request in self.requests]
        self.assertIn("previous draft failed native plan validation", prompts[1])
        self.assertTrue(prompts[1].startswith(prompts[0]))
        row = self.h.store.all("planner_request")[-1]
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", self.settle())
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())

    def test_local_draft_correction_stops_after_one_rejected_repair(self):
        self.repair_fixture(second_valid=False)
        for _ in range(4):
            self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual("invalid_model_plan", self.h.store.all("result")[-1]["error"])
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        self.assertEqual({}, self.h.connector_plans.inputs)

    def test_local_draft_correction_respects_total_route_attempt_limit(self):
        self.repair_fixture(attempts=1)
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual("invalid_model_plan", self.h.store.all("result")[-1]["error"])

    def test_local_draft_correction_rechecks_account_withdrawal_before_inference(self):
        from unittest.mock import patch

        self.repair_fixture()
        adapter = self.executor.router.adapters["ollama"]
        generate = adapter.generate

        def withdraw(*args, **kwargs):
            response = generate(*args, **kwargs)
            self.h.accounts.disconnect(self.account.id)
            return response

        with patch.object(adapter, "generate", side_effect=withdraw):
            self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())

    def test_local_draft_correction_does_not_repeat_a_clarification(self):
        self.repair_fixture()
        self.scheduled[0][1]["message"]["content"] = json.dumps({"clarification": "Which file?"})
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertTrue(self.h.store.all("route_history")[-1]["planning_draft_valid"])

    def test_local_draft_correction_progresses_under_signed_full_without_action_prompts(self):
        self.repair_fixture(full=True)
        for _ in range(5):
            self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "catalog-note.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.assertEqual([], self.h.store.all("executive_confirmation"))

    def test_local_draft_correction_repeats_model_context_admission(self):
        from unittest.mock import patch

        self.repair_fixture()
        adapter = self.executor.router.adapters["ollama"]
        generate = adapter.generate

        def shrink_context(*args, **kwargs):
            response = generate(*args, **kwargs)
            request = args[3]
            registry = self.executor.router.registry
            registry.models = {
                key: replace(model, context_limit=request.input_tokens + request.max_output_tokens)
                for key, model in registry.models.items()
            }
            return response

        with patch.object(adapter, "generate", side_effect=shrink_context):
            self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual("route_unavailable", self.h.store.all("result")[-1]["error"])

    def test_local_draft_correction_rejects_alias_path_without_normalizing_it(self):
        self.repair_fixture()
        document = json.loads(self.scheduled[0][1]["message"]["content"])
        document["observe"] = False
        document["steps"][0]["intent"]["path"] = "./catalog-note.txt"
        self.scheduled[0][1]["message"]["content"] = json.dumps(document)
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())
        row = self.h.store.all("planner_request")[-1]
        review = self.review(self.accept_change(row))
        self.assertIn("catalog-note.txt", review["review"])
        self.complete(review)
        self.assertEqual("verified", self.settle())

    def test_local_draft_correction_discards_private_inputs_from_invalid_graph(self):
        from copy import deepcopy

        self.repair_fixture()
        private_step = deepcopy(self.steps[0])
        self.scheduled[0][1]["message"]["content"] = json.dumps(
            {"steps": [private_step, private_step]}
        )
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual({}, self.h.connector_plans.inputs)
        self.assertEqual({}, self.h.connectors.requests)
        self.assertEqual([], self.api.calls)
        self.assert_private()

    def test_local_draft_correction_stops_on_task_cancellation(self):
        from unittest.mock import patch

        self.repair_fixture()
        adapter = self.executor.router.adapters["ollama"]
        generate = adapter.generate

        def cancel(*args, **kwargs):
            response = generate(*args, **kwargs)
            self.h.runtime.cancel(args[3].task_id)
            return response

        with patch.object(adapter, "generate", side_effect=cancel):
            self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual("cancelled", self.h.store.all("task")[-1]["state"])
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())

    def test_free_openai_draft_uses_same_bounded_correction_without_paid_fallback(self):
        self.repair_fixture(adapter="openai")
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.assertEqual(
            1, sum(bool(h.get("planning_repair_of")) for h in self.h.store.all("route_history"))
        )
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())

    def test_draft_correction_cannot_follow_a_changed_provider_origin(self):
        from unittest.mock import patch

        self.repair_fixture()
        adapter = self.executor.router.adapters["ollama"]
        generate = adapter.generate

        def change_origin(*args, **kwargs):
            response = generate(*args, **kwargs)
            registry = self.executor.router.registry
            registry.providers = {
                key: replace(provider, base_url=provider.base_url + "/changed")
                for key, provider in registry.providers.items()
            }
            return response

        with patch.object(adapter, "generate", side_effect=change_origin):
            self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertFalse((self.h.files.root / "catalog-note.txt").exists())

    def test_live_preflight_names_later_effects_without_admitting_them(self):
        self.use_ollama()
        proposal = self.conversation("Create catalog-note.txt using current selected task data")[
            "assistance_proposal"
        ]
        material = PlannerAuthoring(self.h).material(
            "plan_draft", proposal["id"], proposal["value"], self.grants
        )
        parameters = material["step"]["intent"]["parameters"]
        prompt = parameters["prompt"]
        self.assertTrue(
            prompt.startswith("Current stage: select one relevant read-only observation")
        )
        self.assertIn("required reader argument", prompt)
        self.assertIn("only the read-only preflight", prompt)
        later = json.loads(prompt.split("are rechecked in continuation): ", 1)[1].split("\n", 1)[0])
        self.assertIn("files.write", later)
        self.assertIn("microsoft.todo.tasks.create", later)
        self.assertNotIn("google.tasks.list", later)
        self.assertNotIn("models.reason", later)
        self.assertNotIn("files.write", parameters["observation_only"])
        self.assertFalse(
            any(c.endswith(":microsoft.todo.tasks.create") for c in parameters["observation_only"])
        )
        self.assertEqual([], self.requests)
        self.assertEqual([], self.api.calls)

    def test_large_live_catalog_continuation_review_binds_the_omitted_model_prompt(self):
        self.large_live_continuation()

    def test_ollama_live_continuation_uses_its_decoder_without_a_duplicate_schema(self):
        self.large_live_continuation(ollama=True)

    def large_live_continuation(self, *, ollama=False):
        from tests.test_planner_http_observations import HTTPObservationTests

        if ollama:
            self.use_ollama()
        reader = self.mount.capability("google.tasks.list", account_id=self.account.id)
        self.api.resources["/tasks/v1/lists/selected-list/tasks"] = {
            "items": [{"title": self.marker}]
        }
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": [
                    {
                        "id": "read",
                        "capability_id": reader.id,
                        "arguments": {"path": {"tasklist": "selected-list"}},
                    }
                ],
                "observe": True,
            }
        )
        proposal = self.conversation("Create catalog-note.txt using current selected task data")[
            "assistance_proposal"
        ]
        self.complete(self.review(proposal))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[0]
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", HTTPObservationTests.settle(self, 2)["state"])
        continuation = self.review(self.accept_change(row))
        self.assertLess(len(continuation["review"].encode()), 24000)
        self.assertIn("model_input_digest", continuation["review"])
        if ollama:
            material = PlannerAuthoring(self.h).material(
                "plan_accept", row["id"], self.accept_change(row)["value"], self.grants
            )
            self.assertNotIn(
                "Response JSON schema:", material["steps"][0]["intent"]["parameters"]["prompt"]
            )
            self.assertIn("$defs", self.requests[0]["body"]["format"])
        original = self.h.store.get("planner_request", row["id"])
        from copy import deepcopy

        changed = deepcopy(original)
        changed["planning_step"]["intent"]["parameters"]["prompt"] += " Unreviewed change"
        self.h.store.put("planner_request", row["id"], changed)
        with self.assertRaises(PermissionError):
            self.complete(continuation)
        self.assertEqual(1, len(self.requests))
        self.h.store.put("planner_request", row["id"], original)
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": [
                    {
                        "id": "save",
                        "node_id": self.h.node_id,
                        "capability_id": "files.write",
                        "depends_on": [],
                        "inputs": [],
                        "intent": asdict(
                            Intent(
                                "Save observed task", "file_write", "catalog-note.txt", self.marker
                            )
                        ),
                    }
                ],
            }
        )
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("partially_verified", HTTPObservationTests.settle(self, 3)["state"])
        self.complete(self.review(self.accept_change(row)))
        self.assertEqual("verified", HTTPObservationTests.settle(self, 4)["state"])
        self.assertEqual(self.marker, (self.h.files.root / "catalog-note.txt").read_text())

    def test_duplicate_account_labels_preserve_distinct_ids_and_ambiguity(self):
        other = self.h.accounts.add(
            "google", "synthetic-other", "tasks-other", self.account.alias, verified=True
        )
        self.vault.put("synthetic-other-token", reference="planning-other")
        self.h.accounts.bind(
            other.id,
            self.manifest.id,
            CredentialRef("planning-other"),
            self.scopes,
            self.manifest.base_url,
        )
        self.mount.refresh()
        proposal = self.conversation()["assistance_proposal"]
        state = PlannerAuthoring(self.h).material(
            "plan_draft", "new", proposal["value"], self.grants
        )
        prompt = state["step"]["intent"]["parameters"]["prompt"]
        shared_text = prompt.split("Shared connector fields (", 1)[1].split("): ", 1)[1]
        shared, _ = json.JSONDecoder().raw_decode(shared_text)
        self.assertEqual(shared["accounts"][self.account.id], shared["accounts"][other.id])
        with self.assertRaisesRegex(PermissionError, "ambiguous"):
            self.h.accounts.select("google", self.manifest.id, alias=self.account.alias)

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
