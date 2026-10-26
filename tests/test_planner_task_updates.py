"""Account-bound status changes require independent current saved-resource reads."""

import unittest

from oscar.communication import task_expectation, task_notes
from tests import test_planner_http_connectors as fixture
from tests import test_planner_task_verification as tasks


class PlannedTaskUpdateTests(unittest.TestCase):
    signature = fixture.HTTPPlanningTests.signature
    review = fixture.HTTPPlanningTests.review
    complete = fixture.HTTPPlanningTests.complete
    close = fixture.HTTPPlanningTests.close
    draft = fixture.HTTPPlanningTests.draft
    accept_change = fixture.HTTPPlanningTests.accept_change
    response = fixture.HTTPPlanningTests.response
    assert_private = fixture.HTTPPlanningTests.assert_private
    grant_full = fixture.HTTPPlanningTests.grant_full
    settle = tasks.PlannedTaskVerificationTests.settle
    run_ask = tasks.PlannedTaskVerificationTests.run_ask
    bind = fixture.HTTPPlanningTests.bind

    def setUp(self):
        fixture.HTTPPlanningTests.setUp(self)
        self.configure()

    def configure(self, provider="google", status="completed"):
        if provider == "microsoft":
            self.account = self.h.accounts.add(
                "microsoft", "synthetic", "tasks", "Work", verified=True
            )
            self.manifest = next(
                m for m in fixture.account_manifests() if m.id == "microsoft.graph"
            )
            self.scopes = {s for c in self.manifest.capabilities for s in c.scopes}
            self.vault.put("synthetic-ms-update", reference="planning-ms-update")
            self.account = self.h.accounts.bind(
                self.account.id,
                self.manifest.id,
                fixture.CredentialRef("planning-ms-update"),
                self.scopes,
                self.manifest.base_url,
            )
        operation = "google.tasks.update" if provider == "google" else "microsoft.todo.tasks.update"
        self.cap = self.mount.capability(operation, account_id=self.account.id)
        path = (
            {"tasklist": "selected-list", "task": "selected-task"}
            if provider == "google"
            else {"listId": "selected-list", "id": "selected-task"}
        )
        self.change["value"]["capabilities"][-1]["capability_id"] = self.cap.id
        self.steps[0]["capability_id"] = self.cap.id
        self.steps[0]["intent"].update(
            capability_kind=self.cap.id,
            parameters={"arguments": {"path": path, "body": {"status": status}}},
        )
        self.resource = (
            "/tasks/v1/lists/selected-list/tasks/selected-task"
            if provider == "google"
            else "/v1.0/me/todo/lists/selected-list/tasks/selected-task"
        )
        self.api.resources[self.resource] = {
            "id": "selected-task",
            "title": self.marker,
            "status": "needsAction" if provider == "google" else "notStarted",
        }
        self.response()

    def test_google_completion_is_verified_by_get_and_preserves_title(self):
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(["PATCH", "GET"], [c[0] for c in self.api.calls])
        self.assertEqual("completed", self.api.resources[self.resource]["status"])
        self.assertEqual(self.marker, self.api.resources[self.resource]["title"])

    def test_microsoft_completion_has_exact_current_resource_readback(self):
        self.configure("microsoft")
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(self.resource, self.api.calls[-1][1])

    def test_microsoft_progress_change_is_supported(self):
        self.configure("microsoft", "inProgress")
        self.assertEqual("verified", self.run_ask())

    def test_google_reopen_is_supported(self):
        self.configure(status="needsAction")
        self.api.resources[self.resource]["status"] = "completed"
        self.assertEqual("verified", self.run_ask())

    def test_wrong_saved_status_fails(self):
        self.api.transform = (
            lambda method, data: {**data, "status": "needsAction"} if method == "GET" else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_wrong_saved_identity_fails(self):
        self.api.transform = (
            lambda method, data: {**data, "id": "foreign-task"} if method == "GET" else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_revocation_during_get_withdraws_verification(self):
        self.api.after_get = lambda: self.h.grid.revoke(self.owner.node_id)
        self.assertEqual("partially_verified", self.run_ask())

    def test_uncertain_completion_is_not_replayed(self):
        self.api.fail_after_post = True
        self.assertNotEqual("verified", self.run_ask())
        for _ in range(3):
            self.h.executive.tick()
        self.assertEqual(["PATCH"], [c[0] for c in self.api.calls])

    def test_deleted_saved_task_does_not_verify(self):
        self.api.transform = (
            lambda method, data: {**data, "deleted": True} if method == "GET" else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_extra_and_unknown_status_fields_cannot_gain_private_verification(self):
        for body in (
            {"status": "unknown"},
            {"status": True},
            {"status": "completed", "title": "Other"},
            {},
        ):
            with self.subTest(body=body):
                self.assertIsNone(
                    task_expectation("google.tasks.update", {"path": {}, "body": body})
                )

    def test_signed_full_completes_without_action_prompts(self):
        from oscar.planner_authoring import PlannerAuthoring

        self.grant_full([self.account.id])
        PlannerAuthoring(self.h).conversation(
            "Complete selected synthetic task",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertEqual("verified", self.settle())
        self.assertEqual([], self.h.store.all("executive_confirmation"))

    def test_html_literal_notes_are_decoded_without_executing_or_ignoring_markup(self):
        self.assertEqual(
            "<script> &\nnext",
            task_notes(
                {"contentType": "html", "content": "<div>&lt;script&gt; &amp;<br>next</div>"}
            ),
        )
        self.assertEqual(
            "Text",
            task_notes(
                {"contentType": "html", "content": "<html><body><div>Text</div></body></html>"}
            ),
        )
        for content in (
            "<script>Text</script>",
            '<div style="display:none">Text</div>',
            "<div>A</div><div>B</div>",
            "<div>unclosed",
            "<![unsupported]>",
            "<!--hidden-->Text",
        ):
            with self.subTest(content=content), self.assertRaises(ValueError):
                task_notes({"contentType": "html", "content": content})

    def test_microsoft_html_notes_are_verified_from_independent_saved_body(self):
        self.configure("microsoft")
        cap = self.mount.capability("microsoft.todo.tasks.create", account_id=self.account.id)
        self.change["value"]["capabilities"][-1]["capability_id"] = cap.id
        self.steps[0]["capability_id"] = cap.id
        self.steps[0]["intent"].update(
            capability_kind=cap.id,
            parameters={
                "arguments": {
                    "path": {"listId": "selected-list"},
                    "body": {
                        "title": self.marker,
                        "body": {
                            "contentType": "html",
                            "content": "<div>&lt;script&gt; &amp;<br>next</div>",
                        },
                        "dueDateTime": {"dateTime": "2026-10-28T00:00:00", "timeZone": "UTC"},
                        "status": "notStarted",
                    },
                }
            },
        )
        self.response()
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(["POST", "GET"], [call[0] for call in self.api.calls])

    def test_unsupported_note_markup_never_becomes_literal_text(self):
        with self.assertRaises(ValueError):
            task_notes({"contentType": None, "content": "Text"})
        with self.assertRaises(ValueError):
            task_notes({"contentType": "html", "content": "<![CDATA[Text]]>"})

    def test_consistent_wrong_resource_id_matching_list_cannot_verify(self):
        self.api.transform = lambda method, data: {**data, "id": "selected-list"}
        self.assertNotEqual("verified", self.run_ask())
