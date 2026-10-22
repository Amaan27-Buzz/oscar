import gzip
import io
import json
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from email.message import Message
from email.utils import formatdate
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError

from oscar.ambient import WEATHER_URL, WeatherContextSource, weather_request
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


class WeatherTests(unittest.TestCase):
    setUp = AmbientTests.setUp
    connect = AmbientTests.connect
    enable = AmbientTests.enable

    def weather(self, **changes):
        self.config = {
            "id": "weather-source",
            "adapter": "weather",
            "entity_id": "weather:oslo",
            "interval_seconds": 600,
            "retain": False,
            "retention_seconds": 60,
            "place": "Oslo public reference",
            "latitude": 59.9139,
            "longitude": 10.7522,
            **changes,
        }
        stamp = self.now - self.now % 3600
        self.weather_payload = {
            "properties": {
                "meta": {
                    "updated_at": self.iso(self.now - 600),
                    "units": {
                        "air_temperature": "celsius",
                        "wind_speed": "m/s",
                        "relative_humidity": "%",
                    },
                },
                "timeseries": [
                    {
                        "time": self.iso(stamp + i * 3600),
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": 12.5,
                                    "wind_speed": 3,
                                    "relative_humidity": 62,
                                    "unselected": "private marker never retained",
                                }
                            }
                        },
                    }
                    for i in range(9)
                ],
            },
        }
        self.weather_calls = []

        def request(*args):
            self.weather_calls.append(args)
            return (
                200,
                {
                    "expires": formatdate(self.now + 1200, usegmt=True),
                    "last-modified": formatdate(self.now - 600, usegmt=True),
                },
                (self.weather_payload),
            )

        mock = patch("oscar.ambient.weather_request", side_effect=request)
        mock.start()
        self.addCleanup(mock.stop)
        return request

    @staticmethod
    def iso(stamp):
        return datetime.fromtimestamp(stamp, UTC).isoformat().replace("+00:00", "Z")

    def test_weather_signed_contract_strict_coordinates_and_no_account_or_url(self):
        self.weather()
        review = self.world.review_source(self.config)
        self.assertEqual(WEATHER_URL, review["endpoint"])
        self.assertFalse(review["act"])
        self.assertIn("Core network address", review["disclosure"])
        for change in (
            {"latitude": True},
            {"latitude": float("nan")},
            {"longitude": 181},
            {"latitude": 1.23456},
            {"place": "bad\nplace"},
            {"interval_seconds": 30},
            {"url": "http://127.0.0.1"},
            {"account_id": self.account.id},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.world.review_source(self.config | change)
        self.assertEqual([], self.weather_calls)

    def test_weather_uses_authorized_awareness_and_retains_only_selected_fields(self):
        self.weather(retain=True)
        self.world.configure_native_source(self.config, owner_authorized=True)
        self.world.tick()
        self.assertEqual([], self.weather_calls)
        self.world.sentry.configure(
            SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, (self.config["id"],)),
            owner_authorized=True,
        )
        self.now += 601
        self.world.tick()
        current = self.world.world.resolve("weather:oslo", "weather.state")
        self.assertEqual("current", current.state)
        value = json.loads(current.value)
        self.assertEqual("forecast", value["kind"])
        self.assertEqual(12.5, value["temperature_c"])
        self.assertIn("CC BY 4.0", value["credit"])
        self.assertEqual("REPORTED", current.epistemic)
        contents = str(self.h.archive.db.execute("SELECT payload FROM archive_events").fetchall())
        self.assertIn("temperature_c", contents)
        self.assertNotIn("private marker", contents)
        self.assertFalse(self.world.world.source(self.config["id"])["act"])
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

    def test_weather_cache_honors_provider_expiry_without_inflating_observation_time(self):
        self.weather()
        self.enable()
        self.world.tick()
        observed = self.world.brief()["sources"][0]["evidence"][0]["observed_at"]
        self.h.accounts.disconnect(self.account.id)
        self.now += 601
        self.world.tick()
        self.assertEqual(1, len(self.weather_calls))
        source = self.world.brief()["sources"][0]
        self.assertIsNone(source["account_id"])
        self.assertEqual(observed, source["evidence"][0]["observed_at"])
        self.now += 601
        with patch(
            "oscar.ambient.weather_request",
            return_value=(304, {"expires": formatdate(self.now + 1200, usegmt=True)}, {}),
        ) as request:
            self.world.tick()
        self.assertTrue(request.call_args.args[2])
        self.assertEqual(self.now, self.world.brief()["sources"][0]["evidence"][0]["observed_at"])

    def test_weather_expiry_never_causes_early_network_retry_and_throttle_is_honored(self):
        self.weather()
        source = WeatherContextSource("owner", self.config, lambda: self.now, {})
        with patch(
            "oscar.ambient.weather_request",
            return_value=(
                200,
                {"expires": formatdate(self.now + 60, usegmt=True)},
                self.weather_payload,
            ),
        ) as request:
            first = source.retrieve("weather", "owner")[0]
            self.assertEqual(60, first.source.ttl_seconds)
            self.now += 61
            with self.assertRaises(ValueError):
                source.retrieve("weather", "owner")
            self.assertEqual(1, request.call_count)
        self.now += 600
        with patch(
            "oscar.ambient.weather_request", return_value=(429, {"retry-after": "7200"}, {})
        ) as request:
            with self.assertRaises(OSError):
                source.retrieve("weather", "owner")
            self.now += 601
            with self.assertRaises(ValueError):
                source.retrieve("weather", "owner")
            self.assertEqual(1, request.call_count)

    def test_weather_cached_value_remains_current_between_network_refreshes(self):
        self.weather()
        self.enable()
        self.world.tick()
        self.now += 31
        self.world.tick()
        self.assertEqual("current", self.world.brief()["sources"][0]["state"])
        self.assertEqual(1, len(self.weather_calls))

    def test_weather_source_policy_denial_never_reads_network(self):
        self.weather()
        self.enable()
        rule = PolicyRule(
            "deny-weather",
            "perception:ingest",
            PolicyEffect.DENY,
            "owner",
            self.now,
            self.now,
            {"source_id": self.config["id"]},
        )
        PersonalPolicy(self.h.store).save(rule, owner_authorized=True)
        self.world.tick()
        self.assertEqual([], self.weather_calls)
        self.assertNotEqual("current", self.world.brief()["sources"][0]["state"])

    def test_weather_revoke_during_io_and_network_failure_withdraw_current_values(self):
        original = self.weather()
        self.enable()

        def revoke(*args):
            result = original(*args)
            self.world.fabric.revoke(self.config["id"], owner_authorized=True)
            return result

        with patch("oscar.ambient.weather_request", side_effect=revoke):
            self.assertEqual(1, self.world.tick()["failed"])
        self.assertEqual({}, self.world.world.volatile)
        self.assertEqual("unknown", self.world.world.resolve("weather:oslo", "weather.state").state)

    def test_weather_loss_stale_model_malformed_and_expired_provider_data_fail_closed(self):
        self.weather()
        self.enable()
        self.world.tick()
        self.assertEqual("current", self.world.brief()["sources"][0]["state"])
        self.now += 1201
        with patch("oscar.ambient.weather_request", side_effect=TimeoutError("synthetic")):
            self.assertEqual(1, self.world.tick()["failed"])
        self.assertNotEqual("current", self.world.brief()["sources"][0]["state"])
        for alter in ("stale", "future", "unit", "nan", "shape"):
            payload = deepcopy(self.weather_payload)
            if alter == "stale":
                payload["properties"]["meta"]["updated_at"] = self.iso(self.now - 21601)
            elif alter == "future":
                payload["properties"]["meta"]["updated_at"] = self.iso(self.now + 1)
            elif alter == "unit":
                payload["properties"]["meta"]["units"]["air_temperature"] = "fahrenheit"
            elif alter == "nan":
                payload["properties"]["timeseries"][0]["data"]["instant"]["details"][
                    "air_temperature"
                ] = float("nan")
            else:
                payload["properties"]["timeseries"] = [None]
            with self.subTest(alter=alter), self.assertRaises(ValueError):
                WeatherContextSource.select(payload, self.now)
        with patch(
            "oscar.ambient.weather_request",
            return_value=(
                200,
                {"expires": formatdate(self.now - 1, usegmt=True)},
                self.weather_payload,
            ),
        ):
            source = WeatherContextSource("owner", self.config, lambda: self.now, {})
            with self.assertRaises(ValueError):
                source.retrieve("weather", "owner")

    def test_weather_http_fixed_endpoint_compression_bounds_redirect_and_deadline(self):
        class Response(io.BytesIO):
            status = 200

            def __init__(self, raw, encoding="identity"):
                super().__init__(raw)
                self.headers = {"Content-Type": "application/json", "Content-Encoding": encoding}

        opener = SimpleNamespace(open=lambda *args, **kwargs: Response(b'{"ok":true}'))
        with patch("oscar.ambient.build_opener", return_value=opener):
            self.assertEqual({"ok": True}, weather_request(59.9139, 10.7522, None)[2])
        request = unittest.mock.Mock(return_value=Response(gzip.compress(b'{"ok":true}'), "gzip"))
        with patch("oscar.ambient.build_opener", return_value=SimpleNamespace(open=request)):
            self.assertEqual({"ok": True}, weather_request(59.9139, 10.7522, None)[2])
        req = request.call_args.args[0]
        self.assertEqual(WEATHER_URL + "?lat=59.9139&lon=10.7522", req.full_url)
        self.assertIn("github.com/Amaan27-Buzz/oscar", req.get_header("User-agent"))
        for raw, encoding in ((b"x" * 262145, "identity"), (gzip.compress(b"x" * 262145), "gzip")):
            with patch(
                "oscar.ambient.build_opener",
                return_value=SimpleNamespace(
                    open=lambda *args, raw=raw, encoding=encoding, **kwargs: Response(raw, encoding)
                ),
            ):
                with self.assertRaises(ValueError):
                    weather_request(0, 0, None)
        with (
            patch("oscar.ambient.build_opener", return_value=opener),
            patch("oscar.ambient.monotonic", side_effect=[0, 0, 6]),
        ):
            with self.assertRaises(TimeoutError):
                weather_request(0, 0, None)
        headers = Message()
        headers["Location"] = "http://127.0.0.1/private"
        with patch(
            "oscar.ambient.build_opener",
            return_value=SimpleNamespace(
                open=unittest.mock.Mock(
                    side_effect=HTTPError(WEATHER_URL, 302, "redirect", headers, None)
                )
            ),
        ):
            with self.assertRaises(OSError):
                weather_request(0, 0, None)


class WeatherReviewTests(unittest.TestCase):
    from tests.test_assistance import AssistanceTests as Fixture

    setUp = Fixture.setUp
    signature = Fixture.signature
    review = Fixture.review
    complete = Fixture.complete

    def test_weather_provider_coordinates_and_retention_are_signed_before_setup(self):
        change = {
            "operation": "source_create",
            "id": "reviewed-weather",
            "value": {
                "id": "reviewed-weather",
                "adapter": "weather",
                "entity_id": "weather:london",
                "interval_seconds": 600,
                "retain": False,
                "retention_seconds": 3600,
                "latitude": 51.5074,
                "longitude": -0.1278,
                "place": "London public reference",
            },
        }
        with patch("oscar.ambient.weather_request") as request:
            review = self.review(change)
            material = json.loads(review["review"])["current"]
            self.assertEqual(WEATHER_URL, material["endpoint"])
            self.assertEqual(51.5074, material["configuration"]["latitude"])
            with self.assertRaises(KeyError):
                self.h.world.world.source("reviewed-weather")
            self.complete(review)
            request.assert_not_called()
        source = self.h.world.world.source("reviewed-weather")
        self.assertTrue(source["perceive"])
        self.assertFalse(source["retain"])
        self.assertFalse(source["act"])
