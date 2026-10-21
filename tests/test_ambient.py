import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from oscar.connectors import ConnectorError, CredentialRef
from oscar.harness import Harness
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
from tests.test_connections import PrivateVault


class AmbientTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1_800_000_000.0
        self.vault = PrivateVault()
        root = Path(self.temp.name)
        self.h = Harness(
            root / "core.sqlite",
            root / "files",
            Path("config/development-models.json"),
            clock=lambda: self.now,
            start_services=False,
            vault=self.vault,
        )
        self.addCleanup(self.h.close)
        self.world = self.h.world
        self.config = {
            "id": "calendar-source",
            "adapter": "calendar",
            "entity_id": "owner-calendar",
            "interval_seconds": 30,
            "retain": False,
            "retention_seconds": 3600,
            "calendar_id": "primary",
            "horizon_seconds": 86400,
        }
        self.calls = []
        self.payload = {
            "items": [
                {
                    "id": "event-1",
                    "summary": "Synthetic appointment",
                    "start": {"dateTime": "2027-01-15T09:00:00Z"},
                    "end": {"dateTime": "2027-01-15T09:30:00Z"},
                    "description": "unselected private marker",
                }
            ]
        }
        self.failure = False

        def request(manifest, spec, parameters, secret):
            self.calls.append((spec, parameters, secret))
            if self.failure:
                raise ConnectorError("network_failure")
            return dict(self.payload), manifest.base_url + "/synthetic-calendar"

        self.h.connectors.http = SimpleNamespace(request=request)
        self.patch = patch("oscar.connectors.time", lambda: self.now)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.connect()

    def connect(self, provider="google"):
        account = self.h.accounts.add(provider, "synthetic", provider, provider, verified=True)
        credential = "synthetic-" + provider
        self.vault.put("synthetic-access-only", reference=credential)
        self.account = self.h.accounts.bind(
            account.id,
            "google.calendar" if provider == "google" else "microsoft.graph",
            CredentialRef(credential),
            ("https://www.googleapis.com/auth/calendar.events.readonly",)
            if provider == "google"
            else ("Calendars.Read",),
            "https://www.googleapis.com" if provider == "google" else "https://graph.microsoft.com",
        )
        self.config.update(account_id=self.account.id, account_generation=self.account.generation)

    def enable(self):
        self.world.configure_native_source(self.config, owner_authorized=True)
        self.world.sentry.configure(
            SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, (self.config["id"],)),
            owner_authorized=True,
        )

    def test_calendar_reads_current_binding_and_separates_retention_and_action(self):
        review = self.world.review_source(self.config)
        self.assertEqual("google.calendar.events.list", review["capability"])
        self.assertFalse(review["act"])
        self.assertEqual([], self.calls)
        self.enable()
        self.assertEqual(1, self.world.tick()["polled"])
        current = self.world.world.resolve("owner-calendar", "calendar.state")
        self.assertEqual("current", current.state)
        self.assertEqual("REPORTED", current.epistemic)
        self.assertNotIn("unselected private marker", current.value)
        self.assertTrue(json.loads(current.value)["complete"])
        self.assertEqual("8", self.calls[0][1]["query"]["maxResults"])
        self.assertEqual("synthetic-access-only", self.calls[0][2])
        self.assertEqual(
            0, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        self.assertFalse(self.world.world.source(self.config["id"])["act"])
        durable = str(self.h.store.db.execute("SELECT data FROM records").fetchall())
        self.assertNotIn("Synthetic appointment", durable)

    def test_manual_awareness_never_reads_provider(self):
        self.world.configure_native_source(self.config, owner_authorized=True)
        self.world.tick()
        self.assertEqual([], self.calls)
        self.assertEqual(
            "unknown", self.world.world.resolve("owner-calendar", "calendar.state").state
        )

    def test_account_change_withdraws_before_next_due_poll(self):
        self.enable()
        self.world.tick()
        self.h.accounts.bind(
            self.account.id,
            "google.calendar",
            CredentialRef("synthetic-google"),
            ("https://www.googleapis.com/auth/calendar.events.readonly",),
            "https://www.googleapis.com",
        )
        self.now += 1
        self.world.tick()
        self.assertEqual(1, len(self.calls))
        self.assertEqual(
            "unavailable", self.world.world.resolve("owner-calendar", "calendar.state").state
        )

    def test_source_revocation_during_io_discards_response(self):
        self.enable()
        original = self.h.connectors.http.request

        def revoke(*args):
            response = original(*args)
            self.world.fabric.revoke(self.config["id"], owner_authorized=True)
            return response

        self.h.connectors.http.request = revoke
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertEqual(
            "unknown", self.world.world.resolve("owner-calendar", "calendar.state").state
        )
        self.assertEqual({}, self.world.world.volatile)

    def test_policy_denial_and_provider_loss_never_preserve_current_claim(self):
        self.enable()
        policy = PersonalPolicy(self.h.store)
        rule = PolicyRule(
            "deny",
            "connectors:read",
            PolicyEffect.DENY,
            "owner",
            self.now,
            self.now,
            {"purpose": "perception"},
        )
        policy.save(rule, owner_authorized=True)
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertEqual([], self.calls)
        policy.save(replace(rule, enabled=False), owner_authorized=True)
        self.now += 61
        self.world.tick()
        self.assertEqual(
            "current", self.world.world.resolve("owner-calendar", "calendar.state").state
        )
        self.failure = True
        self.now += 31
        self.world.tick()
        self.assertEqual(
            "unavailable", self.world.world.resolve("owner-calendar", "calendar.state").state
        )

    def test_pagination_and_oversize_are_explicit(self):
        self.payload["nextPageToken"] = "synthetic-page"
        self.enable()
        self.world.tick()
        value = self.world.world.resolve("owner-calendar", "calendar.state").value
        self.assertFalse(json.loads(value)["complete"])
        self.payload["items"][0]["summary"] = "x" * 3000
        self.now += 31
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertEqual(
            "unavailable", self.world.world.resolve("owner-calendar", "calendar.state").state
        )

    def test_real_clock_explicit_timezone_freshness_and_no_auto_retention(self):
        config = {
            "id": "clock-source",
            "adapter": "time",
            "entity_id": "core",
            "interval_seconds": 5,
            "retain": False,
            "retention_seconds": 60,
            "timezone": "Asia/Kolkata",
        }
        self.world.configure_native_source(config, owner_authorized=True)
        self.world.tick()
        value = json.loads(self.world.world.resolve("core", "clock.state").value)
        self.assertTrue(value["datetime"].endswith("+05:30"))
        self.assertEqual("Asia/Kolkata", value["timezone"])
        with self.assertRaises(ValueError):
            self.world.review_source(config)
        with self.assertRaises(PermissionError):
            self.world.configure_native_source(config | {"id": "other"}, owner_authorized=False)

    def test_microsoft_primary_calendar_and_selected_fields(self):
        self.connect("microsoft")
        self.payload = {
            "value": [
                {
                    "id": "ms-1",
                    "subject": "Synthetic meeting",
                    "start": {"dateTime": "2027-01-15T09:00:00", "timeZone": "UTC"},
                    "end": {"dateTime": "2027-01-15T09:30:00", "timeZone": "UTC"},
                }
            ],
            "@odata.nextLink": "synthetic-page",
        }
        with self.assertRaises(PermissionError):
            self.world.review_source(self.config | {"calendar_id": "other"})
        self.enable()
        self.assertEqual(1, self.world.tick()["polled"])
        current = json.loads(self.world.world.resolve("owner-calendar", "calendar.state").value)
        self.assertFalse(current["complete"])
        self.assertIn("$filter", self.calls[0][1]["query"])

    def test_brief_uses_current_sources_with_provenance_and_honest_conflicts(self):
        event = self.payload["items"][0]
        self.payload["items"].append(event | {"id": "overlapping"})
        self.enable()
        self.world.tick()
        brief = self.world.brief()
        self.assertEqual(1, len(brief["schedule"]["overlaps"]))
        self.assertFalse(brief["schedule"]["incomplete"])
        self.assertEqual("REPORTED", brief["sources"][0]["epistemic"])
        self.assertTrue(brief["sources"][0]["evidence"][0]["id"])
        self.assertEqual(self.account.generation, brief["sources"][0]["account_generation"])
        self.now += 61
        stale = self.world.brief()
        self.assertNotEqual("current", stale["sources"][0]["state"])
        self.assertIsNone(stale["sources"][0]["value"])
        self.assertEqual([], stale["schedule"]["overlaps"])
        self.assertTrue(stale["schedule"]["incomplete"])

    def test_brief_account_revocation_is_immediate_without_poll(self):
        self.enable()
        self.world.tick()
        self.h.accounts.bind(
            self.account.id,
            "google.calendar",
            CredentialRef("synthetic-google"),
            ("https://www.googleapis.com/auth/calendar.events.readonly",),
            "https://www.googleapis.com",
        )
        brief = self.world.brief()
        self.assertEqual("unavailable", brief["sources"][0]["state"])
        self.assertIsNone(brief["sources"][0]["value"])
        self.assertEqual(1, len(self.calls))

    def test_source_grant_epoch_rebind_resumes_polling_without_losing_bound_account(self):
        self.enable()
        self.world.tick()
        self.world.set_source_grants(
            self.config["id"],
            {"perceive": False, "retain": False, "act": False},
            owner_authorized=True,
        )
        self.assertEqual(
            "unknown", self.world.world.resolve("owner-calendar", "calendar.state").state
        )
        self.world.tick()
        self.assertEqual(1, len(self.calls))
        epoch = self.world.set_source_grants(
            self.config["id"],
            {"perceive": True, "retain": False, "act": False},
            owner_authorized=True,
        )
        self.world.tick()
        self.assertEqual(2, len(self.calls))
        self.assertEqual(epoch, self.world.brief()["sources"][0]["epoch"])
        self.assertEqual(
            "current", self.world.world.resolve("owner-calendar", "calendar.state").state
        )

    def test_calendar_read_path_cannot_be_used_for_mutations(self):
        self.world.review_source(self.config)
        instance = next(iter(self.h.connectors.instances.values()))
        with self.assertRaises(PermissionError):
            self.h.connectors.read_context(
                instance.id,
                "google.calendar.events.create",
                {"path": {"calendarId": "primary"}, "body": {}},
                lambda: None,
            )
        self.assertEqual([], self.calls)

    def test_only_separately_retained_selected_fields_enter_archive_and_expire(self):
        self.config.update(retain=True, retention_seconds=60)
        self.enable()
        self.world.tick()
        contents = str(self.h.archive.db.execute("SELECT payload FROM archive_events").fetchall())
        self.assertIn("Synthetic appointment", contents)
        self.assertNotIn("unselected private marker", contents)
        self.world.set_source_grants(
            self.config["id"],
            {"perceive": False, "retain": True, "act": False},
            owner_authorized=True,
        )
        self.now += 61
        with patch("oscar.event_archive.time", lambda: self.now):
            self.world.tick()
        self.assertEqual(
            0,
            self.h.archive.db.execute(
                "SELECT count(*) FROM archive_events WHERE forgotten=0"
            ).fetchone()[0],
        )
