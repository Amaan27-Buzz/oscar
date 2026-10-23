import json
import unittest
from dataclasses import replace

from oscar.event_archive import EventArchive
from oscar.memory_fabric import MemoryFabric
from oscar.perception import PerceptionSource
from oscar.policy import PolicyEffect, PolicyRule
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
from oscar.world_model import Observation, ObservationKind
from oscar.world_runtime import WorldRuntime
from tests.support import Rig


class SentryDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.archive = EventArchive(self.r.root / "archive.sqlite")
        self.r.runtime.memory = MemoryFabric(self.archive)
        self.world = WorldRuntime(self.r.runtime, self.r.files)
        self.source = PerceptionSource(
            "selected",
            ("project",),
            ("status",),
            (ObservationKind.PROJECT,),
            perceive=True,
            act=True,
        )
        self.epoch = self.world.fabric.register(self.source, owner_authorized=True)
        self.world.fabric.connect("selected", self.epoch, lease_seconds=300)
        self.settings = SentrySettings(
            AwarenessMode.SENTRY,
            SentryState.AWARE,
            ("selected",),
            ("status",),
            cooldown_seconds=1,
            allow_interrupt=True,
        )
        self.world.sentry.configure(self.settings, owner_authorized=True)
        self.policy()

    def policy(self, effect=PolicyEffect.ALLOW, capability="sentry:deliver"):
        self.world.fabric.policy.save(
            PolicyRule(
                "delivery",
                capability,
                effect,
                "synthetic-owner",
                self.r.clock(),
                self.r.clock(),
                {},
            ),
            owner_authorized=True,
        )

    def event(self, sequence=1, value="synthetic private value"):
        return Observation(
            f"observation:{sequence}",
            "selected",
            self.epoch,
            sequence,
            "project",
            "status",
            ObservationKind.PROJECT,
            value,
            self.r.clock(),
            self.r.clock() + 120,
            1,
        )

    def tearDown(self):
        self.world.close()
        self.archive.close()
        self.r.close()

    def test_core_projection_does_not_retain_content_or_replay_poll_restart(self):
        self.world.delivery.observe(self.event())
        alert = self.world.alerts()[0]
        self.assertEqual("observation:1", alert["observation_id"])
        self.assertNotIn("synthetic private value", json.dumps(alert))
        self.assertEqual(
            0, self.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        self.r.clock.now += 2
        self.world.delivery.observe(self.event(2))
        self.assertEqual(alert["id"], self.world.alerts()[0]["id"])
        restarted = WorldRuntime(self.r.runtime, self.r.files)
        self.r.clock.now += 2
        restarted.delivery.observe(self.event(3))
        self.assertEqual([], restarted.alerts())
        self.r.clock.now += 2
        restarted.delivery.observe(self.event(4, "changed"))
        self.assertEqual(1, len(restarted.alerts()))
        restarted.close()

    def test_projection_rechecks_revocation_configuration_policy_and_expiry(self):
        for change in (
            "source",
            "settings",
            "policy",
            "policy_conflict",
            "interrupt_policy",
            "expired",
            "sleep",
            "conflict",
        ):
            with self.subTest(change=change):
                self.world.sentry.configure(self.settings, owner_authorized=True)
                self.policy()
                self.r.store.delete("personal_policy", "interrupt")
                self.r.store.delete("personal_policy", "conflict")
                self.epoch = self.world.fabric.register(self.source, owner_authorized=True)
                self.world.fabric.connect("selected", self.epoch, lease_seconds=300)
                self.r.clock.now += 2
                self.world.delivery.observe(self.event(1, change))
                self.assertEqual(1, len(self.world.alerts()))
                if change == "source":
                    self.world.fabric.revoke("selected", owner_authorized=True)
                elif change in {"settings", "sleep"}:
                    self.world.sentry.configure(
                        replace(
                            self.settings,
                            state=SentryState.SLEEP if change == "sleep" else SentryState.GUARD,
                        ),
                        owner_authorized=True,
                    )
                elif change == "policy":
                    self.policy(PolicyEffect.DENY)
                elif change == "policy_conflict":
                    self.r.store.put(
                        "personal_policy",
                        "conflict",
                        {
                            **self.r.store.get("personal_policy", "delivery"),
                            "id": "conflict",
                            "effect": "deny",
                        },
                    )
                elif change == "interrupt_policy":
                    self.r.store.put(
                        "personal_policy",
                        "interrupt",
                        {
                            **self.r.store.get("personal_policy", "delivery"),
                            "id": "interrupt",
                            "capability": "sentry:interrupt",
                            "effect": "deny",
                        },
                    )
                elif change == "expired":
                    self.r.clock.now += 61
                else:
                    other = replace(self.source, id="other")
                    epoch = self.world.fabric.register(other, owner_authorized=True)
                    self.world.fabric.connect("other", epoch, lease_seconds=300)
                    self.world.fabric.ingest(
                        replace(
                            self.event(),
                            id="different",
                            source_id="other",
                            epoch=epoch,
                            value="conflicting",
                        )
                    )
                self.assertEqual([], self.world.alerts())
                if change == "conflict":
                    self.world.fabric.revoke("other", owner_authorized=True)

    def test_no_explicit_delivery_grant_no_action_sleep_and_nontrigger_stay_quiet(self):
        self.r.store.delete("personal_policy", "delivery")
        self.world.delivery.observe(self.event())
        self.assertEqual([], self.world.alerts())
        self.policy()
        for settings, source in (
            (replace(self.settings, state=SentryState.SLEEP), self.source),
            (replace(self.settings, trigger_keys=()), self.source),
            (self.settings, replace(self.source, act=False)),
        ):
            self.world.sentry.configure(settings, owner_authorized=True)
            self.epoch = self.world.fabric.register(source, owner_authorized=True)
            self.world.fabric.connect("selected", self.epoch, lease_seconds=300)
            self.world.delivery.observe(self.event())
            self.assertEqual([], self.world.alerts())

    def test_actual_file_poll_consumes_sentry_decision(self):
        self.r.files.root.joinpath("status.txt").write_text("changed current file")
        self.world.configure_source(
            self.source,
            "files",
            "project",
            owner_authorized=True,
            selected_paths={"status": "status.txt"},
            interval_seconds=1,
        )
        self.assertEqual(1, self.world.tick()["polled"])
        self.assertEqual(1, len(self.world.alerts()))
