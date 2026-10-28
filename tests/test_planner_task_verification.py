"""Private model-created task mutations reuse independent saved-resource verification."""

import json
import unittest
from dataclasses import asdict
from time import monotonic, sleep

from tests import test_planner_http_connectors as fixture


class PlannedTaskVerificationTests(unittest.TestCase):
    signature = fixture.HTTPPlanningTests.signature
    review = fixture.HTTPPlanningTests.review
    complete = fixture.HTTPPlanningTests.complete
    close = fixture.HTTPPlanningTests.close
    draft = fixture.HTTPPlanningTests.draft
    accept_change = fixture.HTTPPlanningTests.accept_change
    bind = fixture.HTTPPlanningTests.bind
    response = fixture.HTTPPlanningTests.response
    assert_private = fixture.HTTPPlanningTests.assert_private
    grant_full = fixture.HTTPPlanningTests.grant_full

    def setUp(self):
        fixture.HTTPPlanningTests.setUp(self)
        self.steps[0]["intent"]["parameters"]["arguments"]["body"] = {
            "title": self.marker,
            "notes": "Synthetic private notes",
            "due": "2026-10-28T00:00:00Z",
            "status": "needsAction",
        }
        self.response()

    def settle(self):
        deadline = monotonic() + 10
        while monotonic() < deadline:
            self.h.executive.tick()
            rows = self.h.store.all("task")
            if len(rows) == 2 and rows[-1]["state"] in {
                "verified",
                "partially_verified",
                "failed",
                "blocked",
                "unknown",
                "cancelled",
            }:
                self.assert_private()
                return rows[-1]["state"]
            sleep(0.02)
        self.fail("private task mutation did not settle")

    def run_ask(self):
        row = self.draft()
        self.complete(self.review(self.accept_change(row)))
        self.h.executive.tick()
        task = self.h.store.all("task")[-1]
        self.complete(self.review({"operation": "confirm_task", "id": task["id"], "value": {}}))
        return self.settle()

    def test_ask_creates_task_and_independently_verifies_private_fields(self):
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])
        self.assertTrue(self.api.calls[-1][1].endswith("/synthetic-resource"))
        self.assertIsNone(self.h.store.all("result")[-1]["value"])
        self.assertEqual({}, self.h.connector_plans.inputs)

    def test_google_undated_task_verifies_notes_and_absent_due_date(self):
        arguments = self.steps[0]["intent"]["parameters"]["arguments"]
        arguments["body"].pop("due")
        arguments["query"] = {}
        self.response()
        self.assertEqual("verified", self.run_ask())
        self.assertNotIn("due", self.api.calls[0][2])
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])

    def test_unrequested_due_date_in_saved_task_fails_verification(self):
        self.steps[0]["intent"]["parameters"]["arguments"]["body"].pop("due")
        self.api.transform = lambda method, data: {**data, "due": "2026-10-28T00:00:00Z"}
        self.response()
        self.assertEqual("failed", self.run_ask())

    def test_verified_read_in_an_effect_graph_unblocks_only_the_reviewed_task_mutation(self):
        self.read_then_create(changed=False)

    def test_changed_independent_read_blocks_the_dependent_task_mutation(self):
        self.read_then_create(changed=True)

    def read_then_create(self, *, changed):
        from oscar.jev import Intent
        from tests.test_planner_http_observations import HTTPObservationTests

        reader = self.mount.capability("google.tasks.list", account_id=self.account.id)
        path = "/tasks/v1/lists/selected-list/tasks"
        self.api.resources[path] = {"items": [{"title": "Selected synthetic task"}]}
        if changed:
            self.api.after_get = lambda: self.api.resources.update({path: {"items": []}})
        create = self.steps[0]
        create["depends_on"] = ["read"]
        read = {
            "id": "read",
            "node_id": reader.node_id,
            "capability_id": reader.id,
            "depends_on": [],
            "intent": asdict(
                Intent(
                    "Read selected tasks",
                    "capability",
                    capability_kind=reader.id,
                    parameters={"arguments": {"path": {"tasklist": "selected-list"}}},
                )
            ),
        }
        self.steps = [create, read]
        self.change["value"]["capabilities"].append(
            {"node_id": reader.node_id, "capability_id": reader.id}
        )
        self.response()
        row = self.draft()
        self.complete(self.review(self.accept_change(row)))
        deadline = monotonic() + 10
        while monotonic() < deadline:
            self.h.executive.tick()
            tasks = self.h.store.all("task")
            if len(tasks) >= 2 and tasks[1]["state"] in {"verified", "failed"}:
                observed = tasks[1]
                break
            sleep(0.02)
        else:
            self.fail("read prerequisite did not settle")
        self.assertEqual("failed" if changed else "verified", observed["state"])
        self.assertEqual(["GET", "GET"], [c[0] for c in self.api.calls])
        if changed:
            for _ in range(3):
                self.h.executive.tick()
            self.assertEqual(2, len(self.h.store.all("task")))
            return
        self.h.executive.tick()
        task = self.h.store.all("task")[-1]
        self.assertEqual("planned", task["state"])
        self.complete(self.review({"operation": "confirm_task", "id": task["id"], "value": {}}))
        self.assertEqual("verified", HTTPObservationTests.settle(self, 3)["state"])
        self.assertEqual(["GET", "GET", "POST", "GET"], [c[0] for c in self.api.calls])

    def test_signed_full_creates_and_verifies_without_per_action_reviews(self):
        from oscar.planner_authoring import PlannerAuthoring

        self.grant_full([self.account.id])
        result = PlannerAuthoring(self.h).conversation(
            "Write a synthetic task record",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        self.assertEqual("verified", self.settle())
        self.assertEqual([], self.h.store.all("assistance_review"))
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])

    def test_microsoft_task_uses_its_account_and_exact_saved_plain_text(self):
        self.microsoft_task()
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(
            "/v1.0/me/todo/lists/selected-list/tasks/synthetic-resource", self.api.calls[-1][1]
        )

    def test_microsoft_undated_task_verifies_notes_without_inventing_a_date(self):
        self.microsoft_task()
        self.steps[0]["intent"]["parameters"]["arguments"]["body"].pop("dueDateTime")
        self.response()
        self.assertEqual("verified", self.run_ask())
        self.assertNotIn("dueDateTime", self.api.calls[0][2])

    def test_microsoft_title_only_task_verifies_empty_notes_and_absent_due_date(self):
        self.microsoft_task()
        self.steps[0]["intent"]["parameters"]["arguments"]["body"] = {"title": self.marker}
        self.response()
        self.assertEqual("verified", self.run_ask())

    def test_microsoft_task_decoder_exposes_nested_note_and_date_fields(self):
        self.microsoft_task()
        cap = self.mount.capability("microsoft.todo.tasks.create", account_id=self.account.id)
        schema = self.h.connector_plans.contract(asdict(cap))["schema"]["properties"]["body"]
        fields = schema["properties"]
        self.assertEqual(["contentType", "content"], fields["body"]["required"])
        self.assertEqual(["text", "html"], fields["body"]["properties"]["contentType"]["enum"])
        self.assertEqual("string", fields["body"]["properties"]["content"]["type"])
        self.assertEqual(["dateTime", "timeZone"], fields["dueDateTime"]["required"])
        self.assertIn("Omit dueDateTime", schema["description"])

    def test_malformed_microsoft_task_notes_are_rejected_before_provider_effects(self):
        self.microsoft_task()
        for value in (
            "<div>notes</div>",
            None,
            {},
            {"contentType": "text", "content": 7},
            {"contentType": "markdown", "content": "notes"},
        ):
            with self.subTest(value=value):
                self.steps[0]["intent"]["parameters"]["arguments"]["body"]["body"] = value
                cap = self.mount.capability(
                    "microsoft.todo.tasks.create", account_id=self.account.id
                )
                pins = self.h.connector_plans.pins([asdict(cap)])
                with self.assertRaises(ValueError):
                    self.h.connector_plans.sanitize(
                        json.dumps({"steps": self.steps}), "invalid-draft", pins
                    )
                self.assertEqual([], self.api.calls)
                self.assertEqual({}, self.h.connector_plans.inputs)

    def test_malformed_microsoft_task_due_date_is_rejected_before_provider_effects(self):
        self.microsoft_task()
        for value in (
            None,
            "tomorrow",
            {},
            {"dateTime": 7, "timeZone": "UTC"},
            {"dateTime": "", "timeZone": "UTC"},
        ):
            with self.subTest(value=value):
                self.steps[0]["intent"]["parameters"]["arguments"]["body"]["dueDateTime"] = value
                cap = self.mount.capability(
                    "microsoft.todo.tasks.create", account_id=self.account.id
                )
                pins = self.h.connector_plans.pins([asdict(cap)])
                with self.assertRaises(ValueError):
                    self.h.connector_plans.sanitize(
                        json.dumps({"steps": self.steps}), "invalid-draft", pins
                    )
                self.assertEqual([], self.api.calls)

    def test_microsoft_extra_fields_keep_generic_partial_contract(self):
        self.microsoft_task()
        self.steps[0]["intent"]["parameters"]["arguments"]["body"]["categories"] = ["Synthetic"]
        self.response()
        self.assertEqual("partially_verified", self.run_ask())
        self.assertEqual(["POST"], [c[0] for c in self.api.calls])

    def cross_service_role_steps(self):
        """Synthetic source/destination accounts; no provider request is sent."""
        from copy import deepcopy

        from oscar.jev import Intent

        google = self.account
        google_create = deepcopy(self.steps[0])
        self.microsoft_task()
        reader = self.mount.capability("google.tasks.list", account_id=google.id)
        source = {
            "id": "source",
            "node_id": reader.node_id,
            "capability_id": reader.id,
            "depends_on": [],
            "intent": asdict(
                Intent(
                    "Read source records",
                    "capability",
                    capability_kind=reader.id,
                    parameters={"arguments": {"path": {"tasklist": "source-list"}}},
                )
            ),
        }
        destination = deepcopy(self.steps[0])
        destination_args = destination["intent"]["parameters"]["arguments"]
        destination_args["path"]["listId"] = "target-list"
        destination["depends_on"] = ["source"]
        goal = (
            'Copy records from Google account alias "Tasks" list ID "source-list" '
            'to Microsoft account alias "MS Tasks" list ID "target-list".'
        )
        return goal, source, destination, google_create

    def test_source_observation_stage_admitted_but_unbound_copy_requires_replan(self):
        goal, source, destination, _ = self.cross_service_role_steps()
        self.h.connector_plans.check_goal_accounts(goal, [source], observe=True)
        with self.assertRaisesRegex(PermissionError, "verified source observation stage"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        self.assertEqual([], self.api.calls)

    def test_owner_goal_rejects_provider_swap_before_effects(self):
        goal, source, _, google_create = self.cross_service_role_steps()
        with self.assertRaisesRegex(PermissionError, "source account"):
            self.h.connector_plans.check_goal_accounts(goal, [source, google_create])
        self.assertEqual([], self.api.calls)

    def test_owner_goal_rejects_wrong_destination_resource(self):
        goal, source, destination, _ = self.cross_service_role_steps()
        destination_args = destination["intent"]["parameters"]["arguments"]
        destination_args["path"]["listId"] = "other-list"
        with self.assertRaisesRegex(PermissionError, "resource ID"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        self.assertEqual([], self.api.calls)

    def test_owner_goal_rejects_source_only_and_partial_read_plan(self):
        goal, source, destination, _ = self.cross_service_role_steps()
        with self.assertRaisesRegex(PermissionError, "destination operation"):
            self.h.connector_plans.check_goal_accounts(goal, [source])
        from oscar.jev import Intent

        reader = self.mount.capability(
            "microsoft.todo.tasks.list", account_id=self.account.id
        )
        destination_read = {
            "id": "target-read",
            "node_id": reader.node_id,
            "capability_id": reader.id,
            "depends_on": [],
            "intent": asdict(
                Intent(
                    "Inspect target",
                    "capability",
                    capability_kind=reader.id,
                    parameters={"arguments": {"path": {"listId": "target-list"}}},
                )
            ),
        }
        with self.assertRaisesRegex(PermissionError, "destination operation"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination_read])
        self.assertEqual([], self.api.calls)

    def test_owner_goal_ambiguous_accounts_require_clarification(self):
        _, source, destination, _ = self.cross_service_role_steps()
        goal = (
            'Copy tasks using Google account alias "Tasks" '
            'and Microsoft account alias "MS Tasks".'
        )
        with self.assertRaisesRegex(ValueError, "Clarify"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        self.assertEqual([], self.api.calls)

    def test_ordinary_service_names_route_only_to_verified_accounts(self):
        _, source, destination, google_create = self.cross_service_role_steps()
        goal = "Please copy these tasks from Google Tasks into my Microsoft To Do work list."
        with self.assertRaisesRegex(PermissionError, "verified source observation stage"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        with self.assertRaises(PermissionError):
            self.h.connector_plans.check_goal_accounts(goal, [source, google_create])
        self.assertEqual([], self.api.calls)

    def test_ambiguous_ordinary_service_name_requires_account_clarification(self):
        from oscar.connectors import CredentialRef
        from oscar.planning_contract import resolved_owner_account_bindings

        google_manifest = self.manifest
        self.cross_service_role_steps()
        secondary = self.h.accounts.add(
            "google", "synthetic-other", "secondary", "Other Tasks", verified=True
        )
        self.vault.put("synthetic-other-token", reference="planning-other")
        self.h.accounts.bind(
            secondary.id,
            google_manifest.id,
            CredentialRef("planning-other"),
            {scope for cap in google_manifest.capabilities for scope in cap.scopes},
            google_manifest.base_url,
        )
        with self.assertRaisesRegex(ValueError, "Clarify"):
            resolved_owner_account_bindings(
                "Copy the tasks from Google Tasks to Microsoft To Do.",
                self.h.accounts.list_accounts(),
            )
        self.assertEqual([], self.api.calls)

    def test_copy_does_not_accept_wrong_operation_on_correct_destination(self):
        from copy import deepcopy

        goal, source, destination, _ = self.cross_service_role_steps()
        wrong = self.mount.capability(
            "microsoft.todo.tasks.update", account_id=self.account.id
        )
        changed = deepcopy(destination)
        changed["capability_id"] = wrong.id
        changed["node_id"] = wrong.node_id
        changed["intent"]["capability_kind"] = wrong.id
        with self.assertRaisesRegex(PermissionError, "destination operation must create"):
            self.h.connector_plans.check_goal_accounts(goal, [source, changed])
        self.assertEqual([], self.api.calls)

    def test_copy_rejects_unobserved_source_and_unordered_destination(self):
        goal, source, destination, _ = self.cross_service_role_steps()
        with self.assertRaisesRegex(PermissionError, "source observation"):
            self.h.connector_plans.check_goal_accounts(goal, [destination])
        destination["depends_on"] = []
        with self.assertRaisesRegex(PermissionError, "verified source observation stage"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        self.assertEqual([], self.api.calls)

    def test_unrelated_observation_cannot_authorize_source_transfer(self):
        goal, _, destination, _ = self.cross_service_role_steps()
        with self.assertRaises(PermissionError):
            self.h.connector_plans.check_goal_accounts(
                goal,
                [destination],
                source_observations={
                    "request_id": "unrelated",
                    "goal_id": "unrelated",
                    "pins": [],
                },
            )
        self.assertEqual([], self.api.calls)

    def test_owner_objective_contract_retains_owner_fields_not_model_fields(self):
        from oscar.planning_contract import owner_objective_contract

        self.cross_service_role_steps()
        goal = (
            "Copy tasks from Google Tasks to Microsoft To Do and preserve "
            "their titles, notes and due dates."
        )
        contract = owner_objective_contract(goal, self.h.accounts.list_accounts())
        self.assertIsNotNone(contract)
        self.assertEqual(goal, contract["objective"])
        self.assertEqual(contract, json.loads(json.dumps(contract)))
        self.assertEqual("copy", contract["operation"])
        self.assertEqual(("due", "title", "notes"), tuple(contract["required_fields"]))
        self.assertEqual(
            ("source", "destination"),
            tuple(account["role"] for account in contract["accounts"]),
        )
        self.assertNotEqual(
            contract["accounts"][0]["account_id"], contract["accounts"][1]["account_id"]
        )
        self.assertEqual([], self.api.calls)

    def test_move_sync_and_ambiguous_transfer_are_not_silent_copies(self):
        from oscar.planning_contract import owner_objective_contract

        self.cross_service_role_steps()
        for goal in (
            "Move tasks from Google Tasks to Microsoft To Do.",
            "Sync tasks from Google Tasks to Microsoft To Do.",
            "Migrate tasks from Google Tasks to Microsoft To Do.",
            "Transfer tasks from Google Tasks to Microsoft To Do.",
        ):
            with self.subTest(goal=goal):
                with self.assertRaisesRegex(ValueError, "Clarify"):
                    owner_objective_contract(goal, self.h.accounts.list_accounts())
        self.assertEqual([], self.api.calls)

    def test_unknown_accounts_cannot_silently_satisfy_task_transfer(self):
        from oscar.planning_contract import owner_objective_contract

        with self.assertRaisesRegex(ValueError, "source and destination"):
            owner_objective_contract(
                "Copy these tasks from my personal account into my work account.",
                self.h.accounts.list_accounts(),
            )

    def test_repeated_conflicting_owner_roles_are_not_silently_merged(self):
        goal, source, destination, _ = self.cross_service_role_steps()
        goal += ' Also copy back to Google account alias "Tasks".'
        with self.assertRaisesRegex(ValueError, "conflicting account roles"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        self.assertEqual([], self.api.calls)

    def test_owner_goal_same_provider_multi_account_routing(self):
        from copy import deepcopy

        from oscar.connectors import CredentialRef

        google = self.account
        source = deepcopy(self.steps[0])
        secondary = self.h.accounts.add(
            "google", "synthetic-secondary", "other", "Secondary", verified=True
        )
        self.vault.put("synthetic-secondary-token", reference="planning-secondary")
        self.h.accounts.bind(
            secondary.id,
            self.manifest.id,
            CredentialRef("planning-secondary"),
            self.scopes,
            self.manifest.base_url,
        )
        self.mount.refresh()
        target = self.mount.capability("google.tasks.create", account_id=secondary.id)
        destination = deepcopy(source)
        destination["node_id"] = target.node_id
        destination["capability_id"] = target.id
        destination["intent"]["capability_kind"] = target.id
        destination_args = destination["intent"]["parameters"]["arguments"]
        destination_args["path"]["tasklist"] = "target-list"
        source_reader = self.mount.capability("google.tasks.list", account_id=google.id)
        source["node_id"] = source_reader.node_id
        source["capability_id"] = source_reader.id
        source["intent"]["capability_kind"] = source_reader.id
        source["intent"]["parameters"] = {
            "arguments": {"path": {"tasklist": "source-list"}}
        }
        source["id"] = "read-source"
        destination["id"] = "copy-target"
        destination["depends_on"] = ["read-source"]
        goal = (
            'Copy from Google account alias "Tasks" list ID "source-list" '
            'to Google account alias "Secondary" list ID "target-list".'
        )
        with self.assertRaisesRegex(PermissionError, "verified source observation stage"):
            self.h.connector_plans.check_goal_accounts(goal, [source, destination])
        swapped = deepcopy(destination)
        swapped["node_id"] = self.cap.node_id
        swapped["capability_id"] = self.cap.id
        swapped["intent"]["capability_kind"] = self.cap.id
        with self.assertRaisesRegex(PermissionError, "source account"):
            self.h.connector_plans.check_goal_accounts(goal, [source, swapped])
        self.assertEqual([], self.api.calls)

    def microsoft_task(self):
        self.account = self.h.accounts.add(
            "microsoft", "synthetic-ms", "tasks", "MS Tasks", verified=True
        )
        self.manifest = next(m for m in fixture.account_manifests() if m.id == "microsoft.graph")
        self.scopes = {s for c in self.manifest.capabilities for s in c.scopes}
        self.vault.put("synthetic-ms-token", reference="planning-ms")
        self.account = self.h.accounts.bind(
            self.account.id,
            self.manifest.id,
            fixture.CredentialRef("planning-ms"),
            self.scopes,
            self.manifest.base_url,
        )
        cap = self.mount.capability("microsoft.todo.tasks.create", account_id=self.account.id)
        self.change["value"]["capabilities"][-1]["capability_id"] = cap.id
        self.steps[0]["capability_id"] = cap.id
        self.steps[0]["intent"]["capability_kind"] = cap.id
        self.steps[0]["intent"]["parameters"]["arguments"] = {
            "path": {"listId": "selected-list"},
            "body": {
                "title": self.marker,
                "body": {"contentType": "html", "content": "<div>Synthetic private notes</div>"},
                "dueDateTime": {"dateTime": "2026-10-28T00:00:00", "timeZone": "UTC"},
                "status": "notStarted",
            },
        }
        self.response()

    def test_changed_saved_fields_fail_verification(self):
        self.api.tamper = True
        self.assertEqual("failed", self.run_ask())
        self.assertEqual(2, len(self.api.calls))

    def test_changed_saved_resource_identity_fails_verification(self):
        self.api.transform = (
            lambda method, data: {**data, "id": "another-task"} if method == "GET" else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_missing_read_scope_preserves_partial_state(self):
        self.scopes = {"https://www.googleapis.com/auth/tasks"}
        self.bind()
        self.mount.refresh()
        self.assertEqual("partially_verified", self.run_ask())
        self.assertEqual(["POST"], [c[0] for c in self.api.calls])

    def test_owner_revocation_during_readback_withdraws_verification(self):
        self.api.after_get = lambda: self.h.grid.revoke(self.owner.node_id)
        self.assertEqual("partially_verified", self.run_ask())

    def test_read_policy_change_during_get_withdraws_verification(self):
        def deny():
            now = self.h.grid.clock()
            self.h.store.put(
                "personal_policy",
                "deny-read",
                {
                    "id": "deny-read",
                    "capability": "connectors:read",
                    "effect": "deny",
                    "source": "owner",
                    "created_at": now,
                    "updated_at": now,
                    "conditions": {},
                },
            )

        self.api.after_get = deny
        self.assertEqual("partially_verified", self.run_ask())

    def test_owner_read_scope_withdrawal_during_get_withdraws_verification(self):
        def withdraw():
            row = self.h.store.get("session", self.owner.id)
            self.h.store.put(
                "session",
                self.owner.id,
                {**row, "scopes": [s for s in row["scopes"] if s != "connectors:read"]},
            )

        self.api.after_get = withdraw
        self.assertEqual("partially_verified", self.run_ask())

    def test_executor_read_scope_withdrawal_during_get_withdraws_verification(self):
        def withdraw():
            row = self.h.store.get("session", self.mount.session.id)
            self.h.store.put(
                "session",
                self.mount.session.id,
                {**row, "scopes": [s for s in row["scopes"] if s != "connectors:read"]},
            )

        self.api.after_get = withdraw
        self.assertEqual("partially_verified", self.run_ask())

    def test_standing_revocation_during_get_withdraws_verification(self):
        from oscar.planner_authoring import PlannerAuthoring

        self.grant_full([self.account.id])
        self.api.after_get = lambda: self.authority.revoke(
            self.owner.node_id, self.owner.id, self.owner_scope, self.grants
        )
        PlannerAuthoring(self.h).conversation(
            "Write a synthetic task record",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertEqual("partially_verified", self.settle())

    def test_account_rotation_during_readback_withdraws_verification(self):
        self.api.after_get = self.bind
        self.assertEqual("partially_verified", self.run_ask())

    def test_private_expectation_tampering_during_readback_is_rejected(self):
        def change():
            row = next(iter(self.h.connector_plans.inputs.values()))
            row["verification_arguments"]["body"]["title"] = "changed"

        self.api.after_get = change
        self.assertEqual("partially_verified", self.run_ask())

    def test_lost_private_expectation_cannot_verify_from_post_response(self):
        def lose(method, data):
            if method == "POST":
                self.h.connector_plans.inputs.clear()
            return data

        self.api.transform = lose
        self.assertEqual("cancelled", self.run_ask())
        self.assertEqual(["POST"], [c[0] for c in self.api.calls])

    def test_uncertain_post_is_never_replayed(self):
        self.api.fail_after_post = True
        self.assertNotEqual("verified", self.run_ask())
        for _ in range(3):
            self.h.executive.tick()
        self.assertEqual(["POST"], [c[0] for c in self.api.calls])

    def test_extra_fields_keep_generic_partial_contract(self):
        self.steps[0]["intent"]["parameters"]["arguments"]["body"]["extra"] = True
        self.response()
        self.assertEqual("partially_verified", self.run_ask())
        self.assertEqual(["POST"], [c[0] for c in self.api.calls])

    def test_model_cannot_choose_the_verification_criterion(self):
        self.steps[0]["intent"]["criterion"] = {"kind": "connector_planned_task"}
        self.response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual([], self.api.calls)

    def test_unsupported_task_shapes_never_derive_success_fields(self):
        from oscar.communication import task_expectation

        arguments = self.steps[0]["intent"]["parameters"]["arguments"]
        for key, value in (
            ("due", "tomorrow"),
            ("due", "2026-10-28T12:00:00Z"),
            ("status", "completed"),
            ("title", {"unexpected": True}),
            ("notes", "bad\rline"),
        ):
            candidate = json.loads(json.dumps(arguments))
            candidate["body"][key] = value
            self.assertIsNone(task_expectation("google.tasks.create", candidate))
