import json
import unittest
from datetime import UTC, datetime

from oscar.connectors import CredentialRef
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
from oscar.task_context import task_attention
from tests import test_ambient as ambient


class ConnectedTaskTests(unittest.TestCase):
    enable = ambient.AmbientTests.enable

    def connect(self, provider="google"):
        account = self.h.accounts.add(provider, "synthetic", provider, provider, verified=True)
        credential = "synthetic-" + provider
        self.vault.put("synthetic-access-only", reference=credential)
        self.account = self.h.accounts.bind(
            account.id,
            "google.tasks" if provider == "google" else "microsoft.graph",
            CredentialRef(credential),
            ("https://www.googleapis.com/auth/tasks.readonly",)
            if provider == "google"
            else ("Tasks.Read",),
            "https://www.googleapis.com" if provider == "google" else "https://graph.microsoft.com",
        )
        self.config.update(account_id=self.account.id, account_generation=self.account.generation)

    def setUp(self):
        ambient.AmbientTests.setUp(self)
        self.config.update(
            id="task-source",
            adapter="connected_tasks",
            entity_id="selected-tasks",
            task_list_id="selected-list",
        )
        del self.config["calendar_id"], self.config["horizon_seconds"]
        self.payload = {
            "items": [
                {
                    "id": "task-1",
                    "title": "Synthetic task",
                    "status": "needsAction",
                    "due": "2027-01-16T00:00:00Z",
                    "notes": "unselected private marker",
                }
            ]
        }

    def state(self):
        return self.world.world.resolve("selected-tasks", "connected_tasks.state")

    def test_read_is_selected_volatile_read_only_and_date_only(self):
        review = self.world.review_source(self.config)
        self.assertEqual("google.tasks.list", review["capability"])
        self.assertFalse(review["act"])
        self.assertEqual([], self.calls)
        self.enable()
        self.assertEqual(1, self.world.tick()["polled"])
        state = self.state()
        self.assertEqual("REPORTED", state.epistemic)
        data = json.loads(state.value)
        self.assertEqual("2027-01-16", data["tasks"][0]["scheduled_date"])
        self.assertNotIn("due_time", data["tasks"][0])
        self.assertNotIn("unselected private marker", state.value)
        self.assertEqual({"tasklist": "selected-list"}, self.calls[0][1]["path"])
        self.assertEqual({"maxResults": "8"}, self.calls[0][1]["query"])
        self.assertEqual(
            0, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        self.assertNotIn(
            "Synthetic task", str(self.h.store.db.execute("SELECT data FROM records").fetchall())
        )
        self.assertFalse(self.world.world.source("task-source")["act"])
        brief = self.world.brief()
        self.assertEqual("connected_tasks.state", brief["sources"][0]["key"])
        self.assertEqual("scheduled_unknown", brief["attention"]["tasks"][0]["reason"])
        self.now += 61
        self.assertIsNone(self.world.brief()["sources"][0]["value"])
        self.assertEqual([], self.world.brief()["attention"]["tasks"])

    def test_manual_trigger_gating_and_no_authority_before_setup(self):
        with self.assertRaises(PermissionError):
            self.world.configure_native_source(self.config, owner_authorized=False)
        self.world.configure_native_source(self.config, owner_authorized=True)
        self.world.tick()
        self.assertEqual([], self.calls)
        self.world.sentry.configure(
            SentrySettings(
                AwarenessMode.TRIGGER_ONLY,
                SentryState.AWARE,
                ("task-source",),
                trigger_keys=("unrelated",),
            ),
            owner_authorized=True,
        )
        self.now += 31
        self.world.tick()
        self.assertEqual([], self.calls)

    def test_account_rotation_withdraws_immediately_without_provider_io(self):
        self.enable()
        self.world.tick()
        self.connect()
        self.assertIsNone(self.world.brief()["sources"][0]["value"])
        self.now += 1
        self.world.tick()
        self.assertEqual("unavailable", self.state().state)
        self.assertEqual(1, len(self.calls))

    def test_source_revocation_during_io_discards_selected_output(self):
        self.enable()
        original = self.h.connectors.http.request

        def revoke(*args):
            response = original(*args)
            self.world.fabric.revoke("task-source", owner_authorized=True)
            return response

        self.h.connectors.http.request = revoke
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertNotEqual("current", self.state().state)
        self.assertEqual({}, self.world.world.volatile)

    def test_microsoft_preserves_provider_time_and_pagination_without_following(self):
        self.connect("microsoft")
        due = {"dateTime": "2027-01-16T09:30:00", "timeZone": "India Standard Time"}
        self.payload = {
            "value": [
                {
                    "id": "ms-task",
                    "title": "Synthetic Graph task",
                    "status": "notStarted",
                    "importance": "high",
                    "dueDateTime": due,
                    "body": {"content": "private body"},
                }
            ],
            "@odata.nextLink": "https://example.invalid/private-page",
        }
        self.enable()
        self.assertEqual(1, self.world.tick()["polled"])
        value = json.loads(self.state().value)
        self.assertEqual(due, value["tasks"][0]["due_time"])
        self.assertEqual("high", value["tasks"][0]["importance"])
        self.assertFalse(value["complete"])
        self.assertNotIn("private", self.state().value)
        self.assertEqual(1, len(self.calls))
        self.assertEqual("microsoft.todo.tasks.list", self.calls[0][0].name)
        self.assertEqual({"listId": "selected-list"}, self.calls[0][1]["path"])
        self.assertEqual({"$top": "8"}, self.calls[0][1]["query"])

    def test_google_empty_and_paged_list_and_malformed_data_fail_closed(self):
        self.payload = {"kind": "tasks#tasks"}
        self.enable()
        self.world.tick()
        self.assertEqual([], json.loads(self.state().value)["tasks"])
        self.payload = {"items": [], "nextPageToken": "private-token"}
        self.now += 31
        self.world.tick()
        self.assertFalse(json.loads(self.state().value)["complete"])
        for payload in (
            {},
            {"items": [{}]},
            {"items": [{"id": "x", "due": "2027-01-01"}]},
            {"items": [{"id": str(i), "title": "x" * 1024} for i in range(8)]},
            {"items": [{"id": str(i)} for i in range(9)]},
            {"items": [{"id": "duplicate"}, {"id": "duplicate"}]},
        ):
            with self.subTest(payload=str(payload)[:60]):
                self.payload = payload
                self.now += 301
                self.assertEqual(1, self.world.tick()["failed"])
                self.assertNotEqual("current", self.state().state)

    def test_exact_scope_and_no_extra_configuration(self):
        for changes in ({"account_generation": True}, {"task_list_id": ""}, {"act": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.world.review_source(self.config | changes)
        self.h.accounts.bind(
            self.account.id,
            "google.tasks",
            CredentialRef("synthetic-google"),
            ("https://www.googleapis.com/auth/tasks",),
            "https://www.googleapis.com",
        )
        self.config["account_generation"] = self.h.accounts.get(self.account.id).generation
        with self.assertRaises(PermissionError):
            self.world.review_source(self.config)

    def test_provider_loss_withdraws_and_only_selected_retention_enters_archive(self):
        self.config.update(retain=True, retention_seconds=60)
        self.enable()
        self.world.tick()
        contents = str(self.h.archive.db.execute("SELECT payload FROM archive_events").fetchall())
        self.assertIn("Synthetic task", contents)
        self.assertNotIn("unselected private marker", contents)
        self.failure = True
        self.now += 31
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertIsNone(self.world.brief()["sources"][0]["value"])


class TaskAttentionTests(unittest.TestCase):
    now = datetime(2027, 1, 15, 20, tzinfo=UTC).timestamp()

    def source(self, tasks, **changes):
        return {
            "id": "tasks",
            "adapter": "connected_tasks",
            "state": "current",
            "evidence": [{"fresh_until": self.now + 120}],
            "value": json.dumps({"tasks": tasks, "complete": True}),
            **changes,
        }

    def clock(self, zone="Asia/Kolkata", **changes):
        return {
            "id": "clock",
            "adapter": "time",
            "state": "current",
            "evidence": [{"fresh_until": self.now + 120}],
            "value": json.dumps({"timezone": zone}),
            **changes,
        }

    def test_reported_importance_precedes_scheduled_days_without_changing_tasks(self):
        tasks = [
            {"id": "undated", "status": "needsAction"},
            {"id": "tomorrow", "status": "needsAction", "due_date": "2027-01-17"},
            {"id": "important", "status": "notStarted", "importance": "high"},
            {"id": "today", "status": "needsAction", "due_date": "2027-01-16"},
            {"id": "late", "status": "needsAction", "due_date": "2027-01-15"},
            {"id": "done", "status": "completed", "due_date": "2020-01-01"},
        ]
        source = self.source(tasks)
        before = json.dumps(source)
        result = task_attention([source, self.clock()], self.now)
        self.assertEqual(
            ["important", "today", "late", "tomorrow", "undated"],
            [t["task_id"] for t in result["tasks"]],
        )
        self.assertEqual(
            [
                "high_importance",
                "scheduled_today",
                "scheduled_earlier",
                "scheduled_later",
                "no_due_date",
            ],
            [t["reason"] for t in result["tasks"]],
        )
        self.assertEqual(before, json.dumps(source))
        self.assertEqual("Asia/Kolkata", result["timezone"])

    def test_date_only_does_not_become_midnight_or_borrow_an_ambiguous_timezone(self):
        source = self.source([{"id": "date", "status": "needsAction", "due_date": "2027-01-15"}])
        for clocks in (
            [],
            [self.clock(state="stale")],
            [self.clock(), self.clock("UTC")],
            [self.clock("Unknown/Zone")],
        ):
            with self.subTest(clocks=clocks):
                result = task_attention([source, *clocks], self.now)
                self.assertEqual("scheduled_unknown", result["tasks"][0]["reason"])
                self.assertEqual(1, result["unknown_due_times"])
                self.assertIsNone(result["timezone"])

    def test_offset_deadline_is_comparable_without_a_clock_timezone(self):
        source = self.source(
            [
                {
                    "id": "timed",
                    "status": "inProgress",
                    "due_time": {
                        "dateTime": "2027-01-15T19:59:00+00:00",
                        "timeZone": "UTC",
                    },
                }
            ]
        )
        result = task_attention([source], self.now)
        self.assertEqual("overdue", result["tasks"][0]["reason"])
        self.assertEqual(0, result["unknown_due_times"])

    def test_derived_attention_expires_at_deadline_midnight_or_evidence_expiry(self):
        deadline = datetime(2027, 1, 15, 20, 1, tzinfo=UTC).timestamp()
        source = self.source(
            [
                {
                    "id": "timed",
                    "status": "notStarted",
                    "due_time": {
                        "dateTime": "2027-01-15T20:01:00Z",
                        "timeZone": "UTC",
                    },
                }
            ]
        )
        self.assertEqual(deadline, task_attention([source], self.now)["fresh_until"])
        self.assertEqual("overdue", task_attention([source], deadline)["tasks"][0]["reason"])
        midnight = datetime(2027, 1, 16, tzinfo=UTC).timestamp()
        clock = self.clock("UTC", evidence=[{"fresh_until": midnight + 60}])
        source = self.source([], evidence=[{"fresh_until": midnight + 60}])
        self.assertEqual(midnight, task_attention([source, clock], midnight - 10)["fresh_until"])
        source["evidence"][0]["fresh_until"] = midnight - 5
        self.assertEqual(
            midnight - 5, task_attention([source, clock], midnight - 10)["fresh_until"]
        )

    def test_dst_ambiguity_missing_timezone_and_unmapped_windows_zone_stay_unknown(self):
        for stamp in (
            {"dateTime": "2026-11-01T01:30:00", "timeZone": "America/New_York"},
            {"dateTime": "2026-03-08T02:30:00", "timeZone": "America/New_York"},
            {"dateTime": "2027-01-15T19:00:00", "timeZone": "India Standard Time"},
            {"dateTime": "2027-01-15T19:00:00"},
        ):
            with self.subTest(stamp=stamp):
                result = task_attention(
                    [self.source([{"id": "unknown", "status": "notStarted", "due_time": stamp}])],
                    self.now,
                )
                self.assertEqual("due_unknown", result["tasks"][0]["reason"])
                self.assertEqual(1, result["unknown_due_times"])

    def test_withdrawal_partial_lists_unknown_status_and_total_bounds_remain_visible(self):
        source = self.source([{"id": str(i), "status": "needsAction"} for i in range(8)])
        another = self.source(
            [
                {"id": "more", "status": "needsAction"},
                {"id": "unknown", "status": "provider-new-status"},
            ],
            id="other",
        )
        result = task_attention(
            [source, another, self.source([], id="lost", state="unavailable")], self.now
        )
        self.assertEqual(8, len(result["tasks"]))
        self.assertTrue(result["truncated"])
        self.assertTrue(result["incomplete"])
        self.assertEqual([], task_attention([self.source([], state="stale")], self.now)["tasks"])

    def test_scheduled_google_day_is_not_a_deadline(self):
        source = self.source(
            [
                {"id": "planned", "status": "needsAction", "scheduled_date": "2027-01-15"},
                {
                    "id": "deadline",
                    "status": "notStarted",
                    "due_time": {"dateTime": "2027-01-15T19:00:00Z", "timeZone": "UTC"},
                },
            ]
        )
        result = task_attention([source, self.clock()], self.now)
        self.assertEqual(["deadline", "planned"], [item["task_id"] for item in result["tasks"]])
        self.assertEqual(
            ["overdue", "scheduled_earlier"], [item["reason"] for item in result["tasks"]]
        )

    def test_legacy_google_date_only_report_does_not_become_overdue(self):
        source = self.source([{"id": "legacy", "status": "needsAction", "due_date": "2027-01-15"}])
        self.assertEqual(
            "scheduled_earlier",
            task_attention([source, self.clock()], self.now)["tasks"][0]["reason"],
        )
