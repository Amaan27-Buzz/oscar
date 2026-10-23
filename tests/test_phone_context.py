import base64
import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oscar.cloud import CloudConfig, CloudCore
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.phone_context import request, withdraw
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.remote_grid import create_invitation
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
from tests.test_cloud import configuration
from tests.test_remote_grid import DirectClient, keypair, signature


class PhoneContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1_800_000_000.0
        root = Path(self.temp.name)
        self.h = Harness(
            root / "core.sqlite",
            root / "files",
            Path("config/development-models.json"),
            clock=lambda: self.now,
            start_services=False,
        )
        self.addCleanup(self.h.close)
        self.world = self.h.world
        self.h.grid.register(Node("test-phone", NodeRole.MOBILE, ("android:perceive",)))
        self.session = self.h.grid.pair("test-phone", ("android:perceive",))
        self.h.store.put(
            "remote_device",
            "test-phone",
            {
                "role": "mobile",
                "session_id": self.session.id,
                "owner_id": self.h.runtime.relationship_id,
            },
        )
        self.config = {
            "id": "phone-context",
            "adapter": "android",
            "entity_id": "phone:test-phone",
            "interval_seconds": 5,
            "retain": False,
            "retention_seconds": 3600,
            "node_id": "test-phone",
            "session_id": self.session.id,
            "packages": ["example.selected"],
        }
        self.world.configure_native_source(self.config, owner_authorized=True)
        self.world.sentry.configure(
            SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, ("phone-context",)),
            owner_authorized=True,
        )

    def call(self, payload):
        return request(
            self.world,
            self.session,
            payload,
            lambda: self.h.grid.authenticate(self.session, "android:perceive"),
        )

    def payload(self):
        source = self.call({})["sources"][0]
        return {
            "source_id": source["id"],
            "epoch": source["epoch"],
            "sequence": source["sequence"],
            "observed_at_ms": int(self.now * 1000),
            "value": {
                "notifications_available": True,
                "media_available": True,
                "notifications": [{"package": "example.selected", "count": 2}],
                "media": [{"package": "example.selected", "state": 3}],
            },
        }

    def test_selected_metadata_is_current_volatile_and_expires(self):
        before = self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        self.assertTrue(self.call(self.payload())["accepted"])
        state = self.world.world.resolve("phone:test-phone", "phone.state")
        self.assertEqual(2, json.loads(state.value)["notifications"][0]["count"])
        self.assertFalse(state.simulated)
        self.assertNotIn('"count":2', str(self.h.store.all("world_current")))
        self.assertEqual(
            before, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        self.assertEqual("phone.state", self.world.brief()["sources"][0]["key"])
        self.assertEqual(0, self.world.tick()["polled"])
        self.now += 16
        self.assertNotEqual(
            "current", self.world.world.resolve("phone:test-phone", "phone.state").state
        )

    def configure_eight(self):
        identifiers = ["phone-context", *[f"phone-{index}" for index in range(1, 8)]]
        for identifier in identifiers[1:]:
            self.world.configure_native_source(
                self.config | {"id": identifier}, owner_authorized=True
            )
        self.world.sentry.configure(
            SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, tuple(identifiers)),
            owner_authorized=True,
        )
        value = self.payload()["value"]
        return [
            {
                "source_id": source["id"],
                "epoch": source["epoch"],
                "sequence": source["sequence"],
                "observed_at_ms": int(self.now * 1000),
                "value": copy.deepcopy(value),
            }
            for source in self.call({})["sources"]
        ]

    def test_eight_source_batch_updates_and_withdraws_without_extending_ttl(self):
        items = self.configure_eight()
        self.assertEqual(8, len(items))
        self.assertTrue(self.call({"batch": items})["accepted"])
        for item in items:
            source = self.world.world.source(item["source_id"])
            self.assertEqual(1, source["last_sequence"])
            self.assertEqual(self.now + 15, source["connected_until"])
        with self.assertRaises(PermissionError):
            self.call({"batch": items})
        self.assertTrue(
            self.call(
                {
                    "batch": [
                        {"withdraw": item["source_id"], "epoch": item["epoch"]} for item in items
                    ]
                }
            )["accepted"]
        )
        for item in items:
            self.assertEqual(0, self.world.world.source(item["source_id"])["connected_until"])

    def test_batch_validates_every_item_before_connection_or_retention(self):
        items = self.configure_eight()
        self.world.set_source_grants(
            items[0]["source_id"],
            {"perceive": True, "retain": True, "act": False},
            owner_authorized=True,
        )
        items[0]["epoch"] = self.world.world.source(items[0]["source_id"])["epoch"]
        before = self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        invalid = [
            {"batch": []},
            {"batch": items + [items[0]]},
            {"batch": [items[0], items[0]]},
            {"batch": items, "extra": True},
            {"batch": items[:-1] + [None]},
            {"batch": items[:-1] + [items[-1] | {"epoch": 999}]},
            {"batch": items[:-1] + [items[-1] | {"sequence": 0}]},
            {"batch": items[:-1] + [items[-1] | {"source_id": "another-phone"}]},
            {"batch": items[:-1] + [items[-1] | {"value": {"private_text": "rejected"}}]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises((ValueError, PermissionError)):
                self.call(payload)
            for item in items:
                source = self.world.world.source(item["source_id"])
                self.assertEqual(0, source["last_sequence"])
                self.assertEqual(0, source["connected_until"])
            self.assertFalse(self.world.world.volatile)
            self.assertEqual(
                before,
                self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0],
            )

    def test_later_batch_retention_denial_prevents_earlier_volatile_update(self):
        items = self.configure_eight()
        self.world.set_source_grants(
            items[-1]["source_id"],
            {"perceive": True, "retain": True, "act": False},
            owner_authorized=True,
        )
        items[-1]["epoch"] = self.world.world.source(items[-1]["source_id"])["epoch"]
        PersonalPolicy(self.h.store).save(
            PolicyRule(
                "deny-retention",
                "perception:retain",
                PolicyEffect.DENY,
                "owner",
                self.now,
                self.now,
                {},
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.call({"batch": items})
        self.assertFalse(self.world.world.volatile)
        self.assertEqual(0, self.world.world.source(items[0]["source_id"])["last_sequence"])

    def test_batch_rechecks_authority_before_first_effect(self):
        items = self.configure_eight()
        checks = 0

        def guard():
            nonlocal checks
            checks += 1
            if checks == 2:
                current = self.h.store.get("session", self.session.id)
                self.h.store.put("session", self.session.id, {**current, "revoked": True})
            self.h.grid.authenticate(self.session, "android:perceive")

        with self.assertRaises(PermissionError):
            request(self.world, self.session, {"batch": items}, guard)
        self.assertEqual(2, checks)
        self.assertFalse(self.world.world.volatile)
        for item in items:
            self.assertEqual(0, self.world.world.source(item["source_id"])["last_sequence"])

    def test_schema_scope_time_sequence_and_epoch_fail_closed(self):
        valid = self.payload()
        invalid = [
            {"observed_at_ms": int(self.now * 1000) + 1},
            {"observed_at_ms": int(self.now * 1000) - 5001},
            {"observed_at_ms": float("nan")},
            {"sequence": 0},
            {"epoch": 999},
            {"value": {"notifications": [{"package": "example.other", "count": 1}], "media": []}},
            {"value": {"notifications": [], "media": [], "title": "private"}},
            {
                "value": {
                    "notifications": [{"package": "example.selected", "count": 33}],
                    "media": [],
                }
            },
        ]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises((ValueError, PermissionError)):
                self.call(copy.deepcopy(valid) | change)
        self.call(valid)
        with self.assertRaises(PermissionError):
            self.call(valid)
        self.world.set_source_grants(
            "phone-context",
            {"perceive": True, "retain": False, "act": False},
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.call(valid | {"sequence": 2})

    def test_session_binding_awareness_grants_and_withdrawal(self):
        payload = self.payload()
        self.call(payload)
        withdraw(self.world, self.session.id)
        self.assertNotEqual(
            "current", self.world.world.resolve("phone:test-phone", "phone.state").state
        )
        self.world.sentry.configure(SentrySettings(), owner_authorized=True)
        self.assertTrue(
            self.call({"withdraw": "phone-context", "epoch": payload["epoch"]})["accepted"]
        )
        self.assertEqual([], self.call({})["sources"])
        with self.assertRaises(PermissionError):
            self.call(payload | {"sequence": 2})
        device = self.h.store.get("remote_device", "test-phone")
        self.h.store.put("remote_device", "test-phone", {**device, "session_id": "other"})
        with self.assertRaises(PermissionError):
            self.call({})

    def test_separate_retention_policy_and_source_authority(self):
        self.world.set_source_grants(
            "phone-context", {"perceive": True, "retain": True, "act": False}, owner_authorized=True
        )
        PersonalPolicy(self.h.store).save(
            PolicyRule(
                "deny-retention",
                "perception:retain",
                PolicyEffect.DENY,
                "owner",
                self.now,
                self.now,
                {},
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.call(self.payload())
        self.assertNotEqual(
            "current", self.world.world.resolve("phone:test-phone", "phone.state").state
        )

    def test_local_withdrawal_and_explicit_sentry_delivery(self):
        self.world.set_source_grants(
            "phone-context",
            {"perceive": True, "retain": False, "act": True},
            owner_authorized=True,
        )
        self.world.sentry.configure(
            SentrySettings(
                AwarenessMode.SENTRY,
                SentryState.AWARE,
                ("phone-context",),
                ("phone.state",),
                allow_interrupt=True,
            ),
            owner_authorized=True,
        )
        self.call(self.payload())
        self.assertEqual([], self.world.alerts())
        for capability in ("sentry:interrupt", "sentry:deliver"):
            PersonalPolicy(self.h.store).save(
                PolicyRule(
                    capability,
                    capability,
                    PolicyEffect.ALLOW,
                    "owner",
                    self.now,
                    self.now,
                    {},
                ),
                owner_authorized=True,
            )
        self.now += 61
        payload = self.payload()
        self.call(payload)
        self.assertEqual(1, len(self.world.alerts()))
        self.call({"withdraw": "phone-context", "epoch": payload["epoch"]})
        self.assertEqual([], self.world.alerts())
        self.assertNotEqual(
            "current", self.world.world.resolve("phone:test-phone", "phone.state").state
        )

    def test_source_review_requires_current_android_scope_and_bounded_selection(self):
        for changes in (
            {"packages": ["example.selected"] * 2},
            {"node_id": "other"},
            {"session_id": "other"},
            {"entity_id": "other"},
        ):
            with (
                self.subTest(changes=changes),
                self.assertRaises((ValueError, KeyError, PermissionError)),
            ):
                self.world.review_source(self.config | {"id": "other-source"} | changes)
        current = self.h.store.get("session", self.session.id)
        self.h.store.put("session", self.session.id, {**current, "revoked": True})
        with self.assertRaises(PermissionError):
            self.call({})
        self.world.tick()
        self.assertNotEqual(
            "current", self.world.world.resolve("phone:test-phone", "phone.state").state
        )

    def test_trigger_removal_withdraws_current_context_and_notices_before_next_tick(self):
        self.world.set_source_grants(
            "phone-context",
            {"perceive": True, "retain": False, "act": True},
            owner_authorized=True,
        )
        for capability in ("sentry:interrupt", "sentry:deliver"):
            PersonalPolicy(self.h.store).save(
                PolicyRule(
                    capability, capability, PolicyEffect.ALLOW, "owner", self.now, self.now, {}
                ),
                owner_authorized=True,
            )
        for count, read in enumerate(("brief", "snapshot", "alerts"), start=1):
            with self.subTest(read=read):
                self.world.sentry.configure(
                    SentrySettings(
                        AwarenessMode.TRIGGER_ONLY,
                        SentryState.AWARE,
                        ("phone-context",),
                        ("phone.state",),
                        allow_interrupt=True,
                    ),
                    owner_authorized=True,
                )
                payload = self.payload()
                payload["value"]["notifications"][0]["count"] = count
                self.call(payload)
                self.assertEqual(1, len(self.world.alerts()))
                self.world.sentry.configure(
                    SentrySettings(
                        AwarenessMode.TRIGGER_ONLY,
                        SentryState.AWARE,
                        ("phone-context",),
                        (),
                        allow_interrupt=True,
                    ),
                    owner_authorized=True,
                )
                getattr(self.world, read)()
                self.assertLessEqual(
                    self.world.world.source("phone-context")["connected_until"], self.now
                )
                self.assertIsNone(self.world.brief()["sources"][0]["value"])
                self.assertEqual([], self.world.alerts())
                self.assertEqual([], self.call({})["sources"])
                self.now += 61

    def test_node_scope_withdrawal_hides_brief_before_next_tick_and_stale_row_cleanup(self):
        self.call(self.payload())
        node = self.h.store.get("node", self.session.node_id)
        self.h.store.put("node", self.session.node_id, {**node, "scopes": []})
        self.assertIsNone(self.world.brief()["sources"][0]["value"])
        self.assertFalse(self.world.snapshot()["sources"][0]["connected"])
        with self.assertRaises(PermissionError):
            self.call({})
        row = self.h.store.get("perception_poll", self.world.world.source_key("phone-context"))
        self.h.store.put(
            "perception_poll", self.world.world.source_key("phone-context"), {**row, "epoch": 999}
        )
        withdraw(self.world, self.session.id)
        self.assertLessEqual(self.world.world.source("phone-context")["connected_until"], self.now)


class PhoneContextRemoteTests(unittest.TestCase):
    def test_authenticated_operation_rejects_other_session_and_withdraws_on_rotation(self):
        with TemporaryDirectory() as folder:
            core = CloudCore(CloudConfig.load(configuration(Path(folder))), initialize=True)
            try:
                key, public = keypair()
                clients = []
                for node, permitted in (("phone-permitted", True), ("phone-ungranted", False)):
                    invitation = create_invitation(
                        core, node, "mobile", node, public, android_control=permitted
                    )
                    issued = core.remote.enroll(
                        {
                            "version": 2,
                            "challenge_id": invitation["challenge_id"],
                            "signature": signature(
                                key, base64.b64decode(invitation["signing_payload"])
                            ),
                        }
                    )
                    clients.append(DirectClient(core, issued))
                permitted, ungranted = clients
                world = core.harness.world
                world.configure_native_source(
                    {
                        "id": "phone-context",
                        "adapter": "android",
                        "entity_id": "phone:phone-permitted",
                        "interval_seconds": 5,
                        "retain": False,
                        "retention_seconds": 3600,
                        "node_id": permitted.handle.node_id,
                        "session_id": permitted.handle.id,
                        "packages": ["example.selected"],
                    },
                    owner_authorized=True,
                )
                world.sentry.configure(
                    SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, ("phone-context",)),
                    owner_authorized=True,
                )
                with self.assertRaises(PermissionError):
                    ungranted.request("phone_context", {})
                prepared = permitted.request("phone_context", {})
                source = prepared["sources"][0]
                permitted.request(
                    "phone_context",
                    {
                        "source_id": source["id"],
                        "epoch": source["epoch"],
                        "sequence": source["sequence"],
                        "observed_at_ms": prepared["observed_at_ms"],
                        "value": {
                            "notifications_available": True,
                            "notifications": [],
                            "media_available": False,
                            "media": [],
                        },
                    },
                )
                self.assertEqual(
                    "current", world.world.resolve("phone:phone-permitted", "phone.state").state
                )
                permitted.request("rotate", {})
                self.assertNotEqual(
                    "current", world.world.resolve("phone:phone-permitted", "phone.state").state
                )
                with self.assertRaises(PermissionError):
                    permitted.request("phone_context", {})
            finally:
                core.close()
