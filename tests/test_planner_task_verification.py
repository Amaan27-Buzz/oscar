"""Private model-created task mutations reuse independent saved-resource verification."""

import json
import unittest
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
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(
            "/v1.0/me/todo/lists/selected-list/tasks/synthetic-resource", self.api.calls[-1][1]
        )

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
