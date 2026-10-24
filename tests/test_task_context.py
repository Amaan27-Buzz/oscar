import json
import unittest

from oscar.connectors import CredentialRef
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
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
        self.assertEqual("2027-01-16", data["tasks"][0]["due_date"])
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
        self.now += 61
        self.assertIsNone(self.world.brief()["sources"][0]["value"])

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
