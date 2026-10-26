"""Private calendar mutations require independent matching saved-resource reads."""

import unittest
from copy import deepcopy

from tests import test_planner_http_connectors as fixture
from tests import test_planner_task_verification as tasks


class PlannedCalendarVerificationTests(unittest.TestCase):
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

    def bind(self):
        self.account = self.h.accounts.bind(
            self.account.id,
            self.manifest.id,
            fixture.CredentialRef(self.credential_ref),
            self.scopes,
            self.manifest.base_url,
        )

    def setUp(self):
        self.credential_ref = "planning-tasks"
        fixture.HTTPPlanningTests.setUp(self)
        self.grants |= frozenset({"connectors:external-communication"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            self.h.store.put(
                kind,
                identifier,
                {**self.h.store.get(kind, identifier), "scopes": sorted(self.grants)},
            )
        self.configure()

    def configure(self, provider="google", update=False):
        self.account = self.h.accounts.add(
            provider, "synthetic-calendar", "calendar", "Calendar", verified=True
        )
        self.manifest = next(
            m
            for m in fixture.account_manifests()
            if m.id == ("google.calendar" if provider == "google" else "microsoft.graph")
        )
        self.credential_ref = "planning-calendar-" + provider
        self.vault.put("synthetic-calendar-token-" + provider, reference=self.credential_ref)
        self.scopes = {s for c in self.manifest.capabilities for s in c.scopes}
        self.bind()
        operation = provider + ".calendar.events." + ("update" if update else "create")
        self.cap = self.mount.capability(operation, account_id=self.account.id)
        path = {"calendarId": "primary"} if provider == "google" else {}
        if update:
            path["eventId" if provider == "google" else "id"] = "selected-event"

        def point(hour):
            return (
                {"dateTime": f"2026-10-28T{hour}:00:00+05:30"}
                if provider == "google"
                else {"dateTime": f"2026-10-28T{hour}:00:00", "timeZone": "UTC"}
            )

        body = {"start": point("14"), "end": point("15")}
        if not update:
            body["summary" if provider == "google" else "subject"] = self.marker
        arguments = {"path": path, "body": body}
        if provider == "google" and update:
            arguments["if_match"] = '"source-version"'
            self.api.require_etag = True
        if provider == "google":
            arguments["query"] = {"sendUpdates": "none"}
        self.change["value"]["capabilities"][-1]["capability_id"] = self.cap.id
        self.steps[0]["capability_id"] = self.cap.id
        self.steps[0]["intent"].update(
            capability_kind=self.cap.id, parameters={"arguments": arguments}
        )
        if update:
            resource_path = (
                "/calendar/v3/calendars/primary/events/selected-event"
                if provider == "google"
                else "/v1.0/me/events/selected-event"
            )
            self.api.resources[resource_path] = {
                "id": "selected-event",
                "etag": '"source-version"',
                "summary" if provider == "google" else "subject": self.marker,
                "start": point("10"),
                "end": point("11"),
                "attendees": [],
            }
        self.response()

    def test_google_create_independently_verifies_timed_event(self):
        self.assertEqual("verified", self.run_ask())
        self.assertEqual(["POST", "GET"], [c[0] for c in self.api.calls])

    def test_google_time_only_move_preserves_unselected_fields(self):
        self.configure(update=True)
        before = deepcopy(next(iter(self.api.resources.values())))
        self.assertEqual("verified", self.run_ask())
        saved = next(iter(self.api.resources.values()))
        self.assertEqual(before["summary"], saved["summary"])
        self.assertEqual(before["attendees"], saved["attendees"])
        self.assertNotEqual(before["start"], saved["start"])
        self.assertEqual(["PATCH", "GET"], [c[0] for c in self.api.calls])

    def test_microsoft_create_independently_verifies_utc_event(self):
        self.configure("microsoft")
        self.assertEqual("verified", self.run_ask())

    def test_microsoft_time_only_move_has_exact_resource_readback(self):
        self.configure("microsoft", update=True)
        self.assertEqual("verified", self.run_ask())
        self.assertEqual("/v1.0/me/events/selected-event", self.api.calls[-1][1])

    def test_changed_saved_time_fails_verification(self):
        self.api.transform = (
            lambda method, data: {**data, "start": {"dateTime": "2026-10-28T16:00:00Z"}}
            if method == "GET"
            else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_read_authority_withdrawal_during_get_keeps_partial_state(self):
        def withdraw():
            row = self.h.store.get("session", self.owner.id)
            self.h.store.put(
                "session",
                self.owner.id,
                {**row, "scopes": [s for s in row["scopes"] if s != "connectors:read"]},
            )

        self.api.after_get = withdraw
        self.assertEqual("partially_verified", self.run_ask())

    def test_uncertain_move_is_never_replayed(self):
        self.configure(update=True)
        self.api.fail_after_post = True
        self.assertNotEqual("verified", self.run_ask())
        for _ in range(3):
            self.h.executive.tick()
        self.assertEqual(["PATCH"], [c[0] for c in self.api.calls])

    def test_signed_full_verifies_calendar_without_per_action_prompts(self):
        from oscar.planner_authoring import PlannerAuthoring

        self.grant_full([self.account.id])
        result = PlannerAuthoring(self.h).conversation(
            "Create selected synthetic calendar event",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        self.assertEqual("verified", self.settle())
        self.assertEqual([], self.h.store.all("executive_confirmation"))

    def test_changed_resource_identity_cannot_verify_a_move(self):
        self.configure(update=True)
        self.api.transform = (
            lambda method, data: {**data, "id": "another-event"} if method == "GET" else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_cancelled_saved_event_does_not_verify_requested_creation(self):
        self.api.transform = (
            lambda method, data: {**data, "status": "cancelled"} if method == "GET" else data
        )
        self.assertEqual("failed", self.run_ask())

    def test_unsupported_and_ambiguous_fields_do_not_gain_verification_contracts(self):
        from oscar.communication import calendar_expectation

        original = self.steps[0]["intent"]["parameters"]["arguments"]
        for extra in (
            {"recurrence": ["RRULE:FREQ=DAILY"]},
            {"start": {"dateTime": "2026-10-28T14:00:00"}},
            {"end": {"dateTime": "2026-10-27T15:00:00Z"}},
            {"attendees": {}},
            {"attendees": [{"email": "bad-address"}]},
            {"summary": "Synthetic\rtitle"},
        ):
            with self.subTest(extra=extra):
                value = {**original, "body": {**original["body"], **extra}}
                self.assertIsNone(calendar_expectation("google.calendar.events.create", value))
        self.assertIsNone(calendar_expectation("google.calendar.events.update", original))
        self.assertIsNone(
            calendar_expectation(
                "google.calendar.events.create",
                {**original, "query": {"sendUpdates": "unrecognized"}},
            )
        )

    def test_calendar_move_requires_separate_external_communication_scope(self):
        self.configure(update=True)
        self.grants -= frozenset({"connectors:external-communication"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            self.h.store.put(
                kind,
                identifier,
                {**self.h.store.get(kind, identifier), "scopes": sorted(self.grants)},
            )
        with self.assertRaises(PermissionError):
            self.draft()
        self.assertEqual([], self.api.calls)
        self.assertEqual([], self.h.store.all("executive_goal"))

    def test_consistent_calendar_id_cannot_substitute_for_event_identity(self):
        self.configure(update=True)
        self.api.transform = lambda method, data: {**data, "id": "primary"}
        self.assertEqual("partially_verified", self.run_ask())
        self.assertEqual(["PATCH"], [call[0] for call in self.api.calls])

    def test_changed_version_rejects_once_without_overwriting_or_readback(self):
        self.configure(update=True)
        resource = next(iter(self.api.resources.values()))
        resource.update(etag='"concurrent-version"', summary="Concurrent editor title")
        before = deepcopy(resource)
        self.assertEqual("failed", self.run_ask())
        for _ in range(3):
            self.h.executive.tick()
        self.assertEqual(before, resource)
        self.assertEqual(["PATCH"], [c[0] for c in self.api.calls])
        self.assertEqual("precondition_failed", self.h.store.all("result")[-1]["error"])

    def test_google_move_requires_one_strong_bounded_version_at_boundary(self):
        from oscar.connectors import endpoint
        from oscar.planner_connectors import ConnectorPlanning

        self.configure(update=True)
        spec = next(c for c in self.manifest.capabilities if c.name.endswith("events.update"))
        arguments = self.steps[0]["intent"]["parameters"]["arguments"]
        schema = ConnectorPlanning.http_schema(spec)
        self.assertIn("if_match", schema["required"])
        for tag in (
            None,
            "",
            "*",
            'W/"version"',
            '"a", "b"',
            '"a\r\nb"',
            '"' + "x" * 255 + '"',
            42,
        ):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                endpoint(spec, {**arguments, "if_match": tag})
        with self.assertRaises(ValueError):
            endpoint(spec, {key: value for key, value in arguments.items() if key != "if_match"})
        read = next(c for c in self.manifest.capabilities if c.name.endswith("events.get"))
        with self.assertRaises(ValueError):
            endpoint(read, {"path": arguments["path"], "if_match": '"version"'})
        self.assertEqual([], self.api.calls)

    def test_signed_full_conditional_move_verifies_without_action_review(self):
        from oscar.planner_authoring import PlannerAuthoring

        self.configure(update=True)
        self.grant_full([self.account.id])
        result = PlannerAuthoring(self.h).conversation(
            "Move selected synthetic calendar event",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        self.assertEqual("verified", self.settle())
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        self.assertEqual(["PATCH", "GET"], [c[0] for c in self.api.calls])

    def test_unconditional_google_move_cannot_stage_a_private_action(self):
        self.configure(update=True)
        del self.steps[0]["intent"]["parameters"]["arguments"]["if_match"]
        self.response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual({}, self.h.connectors.requests)
        self.assertEqual({}, self.h.connector_plans.inputs)
        self.assertEqual([], self.api.calls)
