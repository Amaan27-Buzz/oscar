import json
import unittest
from dataclasses import asdict
from unittest.mock import patch

from oscar.assistance import Assistance
from oscar.jev import Intent
from tests import test_authority as fixture


class AssistanceTests(unittest.TestCase):
    setUp = fixture.StandingAuthorityTests.setUp
    signature = fixture.StandingAuthorityTests.signature

    def test_conversation_schedule_still_needs_exact_signed_plan_and_current_scope(self):
        self.create()
        change = Assistance.conversation_change("every day for 3 runs: 2 + 3")
        self.assertIsNotNone(change)
        review = self.review(change)
        self.assertEqual([], self.h.store.all("executive_goal"))
        self.assertIn("math.add", review["review"])
        result = self.complete(review)
        self.assertEqual("enabled", result["executive"]["goals"][0]["state"])
        self.assertEqual(1, len(self.h.store.all("executive_goal")))
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertIsNone(Assistance.conversation_change("What did we decide?"))
        with self.assertRaises(ValueError):
            Assistance.conversation_change("every day: 2 + 3")

    def create(self, **changes):
        grants = self.grants | frozenset({"math", "files:write", "heartbeat"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(grants)})
        self.grants = grants
        return {
            "operation": "create",
            "id": "new",
            "value": {
                "name": "Weekly calculation",
                "goal": "Calculate the reviewed total",
                "steps": [
                    {
                        "id": "total",
                        "intent": asdict(Intent("2 + 2")),
                        "node_id": self.h.node_id,
                        "capability_id": "math.add",
                        "depends_on": [],
                    }
                ],
                "start_at": self.now,
                "interval_seconds": None,
                "max_runs": 1,
                "priority": 0,
                "conditions": [],
                **changes,
            },
        }

    def review(self, change):
        return Assistance(self.h).challenge(
            self.owner.node_id, self.owner.id, self.owner_scope, self.grants, change
        )

    def complete(self, review):
        return Assistance(self.h).complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            self.signature(review),
        )

    def test_signed_creation_runs_existing_executive_and_replay_is_rejected(self):
        review = self.review(self.create())
        result = self.complete(review)
        self.assertEqual("enabled", result["executive"]["goals"][0]["state"])
        self.assertEqual(1, self.h.executive.tick())
        self.assertEqual("verified", self.h.store.all("task")[0]["state"])
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual(1, len(self.h.store.all("executive_worker")))

    def test_failed_creation_rolls_back_worker_goal_and_review_consumption(self):
        review = self.review(self.create(max_runs=2))
        with self.assertRaises(ValueError):
            self.complete(review)
        self.assertEqual([], self.h.store.all("executive_worker"))
        self.assertEqual([], self.h.store.all("executive_goal"))
        self.assertFalse(self.h.store.get("assistance_review", review["challenge_id"])["used"])

    def test_capability_or_session_changes_fence_review(self):
        review = self.review(self.create())
        row = self.h.store.get("session", self.owner.id)
        self.h.store.put("session", self.owner.id, {**row, "revoked": True})
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual([], self.h.store.all("executive_worker"))

    def test_goal_controls_recheck_review_and_cancel_only_after_commit(self):
        self.complete(self.review(self.create(start_at=self.now + 100)))
        goal = self.h.store.all("executive_goal")[0]
        pause = self.review({"operation": "pause", "id": goal["id"], "value": {}})
        self.complete(pause)
        self.assertEqual("paused", self.h.store.get("executive_goal", goal["id"])["state"])
        self.complete(self.review({"operation": "resume", "id": goal["id"], "value": {}}))
        task = self.h.runtime.create(Intent("2 + 2"))
        self.h.store.put(
            "executive_task",
            task.id,
            {
                "task_id": task.id,
                "goal_id": goal["id"],
                "relationship": self.h.runtime.relationship_id,
            },
        )

        def cancel(identifier, targets):
            self.assertFalse(self.h.store.db.in_transaction)
            self.assertEqual(task.id, identifier)

        with patch.object(self.h.runtime, "cancel", side_effect=cancel) as cancelled:
            self.complete(self.review({"operation": "delete", "id": goal["id"], "value": {}}))
        cancelled.assert_called_once()
        self.assertFalse(self.h.store.all("executive_worker")[0]["enabled"])
        self.assertEqual("cancelled", self.h.store.get("executive_goal", goal["id"])["state"])

    def test_nested_savepoint_failure_does_not_erase_outer_state(self):
        store = self.h.store
        with store.transaction():
            store.put("fixture", "outer", {"value": 1})
            with self.assertRaises(ValueError), store.transaction():
                store.put("fixture", "inner", {"value": 2})
                raise ValueError("abort inner")
            self.assertEqual({"value": 1}, store.get("fixture", "outer"))
        with self.assertRaises(KeyError):
            store.get("fixture", "inner")
        with self.assertRaises(ValueError), store.transaction():
            with store.transaction():
                store.put("fixture", "nested", {"value": 3})
            raise ValueError("abort outer")
        with self.assertRaises(KeyError):
            store.get("fixture", "nested")

    def test_sentry_configuration_is_signed_and_stale_review_cannot_reapply(self):
        change = {
            "operation": "sentry",
            "id": "awareness",
            "value": {
                "mode": "manual",
                "state": "passive",
                "source_ids": [],
                "trigger_keys": [],
                "allow_interrupt": False,
            },
        }
        first, stale = self.review(change), self.review(change)
        self.complete(first)
        with self.assertRaises(PermissionError):
            self.complete(stale)
        self.assertEqual(1, self.h.world.sentry.configuration()[1])

    def test_source_review_preserves_separate_grants_and_fences_stale_configuration(self):
        from oscar.perception import PerceptionSource
        from oscar.world_model import ObservationKind

        source = PerceptionSource(
            "synthetic-source", ("owner",), ("activity",), (ObservationKind.APPLICATION,)
        )
        self.h.world.fabric.register(source, owner_authorized=True)
        change = {
            "operation": "source",
            "id": source.id,
            "value": {"perceive": True, "retain": False, "act": False},
        }
        first, stale = self.review(change), self.review(change)
        self.complete(first)
        current = self.h.world.world.source(source.id)
        self.assertTrue(current["perceive"])
        self.assertFalse(current["retain"])
        self.assertFalse(current["act"])
        self.assertEqual(2, current["epoch"])
        self.assertEqual(["activity"], current["keys"])
        with self.assertRaises(PermissionError):
            self.complete(stale)

    def test_large_catalog_is_bounded_and_explicitly_incomplete(self):
        node = self.h.store.get("node", self.h.node_id)
        capabilities = [
            {**self.capability, "id": "synthetic-" + str(i), "permissions": ["x" * 200]}
            for i in range(400)
        ]
        self.h.store.put("node", self.h.node_id, {**node, "capabilities": capabilities})
        snapshot = Assistance(self.h).snapshot()
        self.assertTrue(snapshot["truncated"])
        self.assertEqual(400, snapshot["capabilities_total"])
        self.assertLessEqual(len(snapshot["capabilities"]), 256)
        self.assertLessEqual(len(json.dumps(snapshot).encode()), 40000)

    def test_natural_instructions_compile_to_exact_review_without_creating_work(self):
        self.create()  # Explicit synthetic owner capability grants.
        change = Assistance.natural_change("Every day for 3 runs: 2 + 2\n3 + 3", "Daily totals")
        review = self.review(change)
        presentation = json.loads(review["review"])
        proposal = presentation["proposal"]
        self.assertEqual(change, presentation["change"])
        self.assertEqual(86400, proposal["value"]["interval_seconds"])
        self.assertEqual(3, proposal["value"]["max_runs"])
        self.assertEqual(["step-1"], proposal["value"]["steps"][1]["depends_on"])
        self.assertEqual([], self.h.store.all("executive_worker"))
        self.assertEqual(0, self.h.executive.tick())
        self.complete(review)
        self.assertEqual(2, self.h.executive.tick())
        self.assertEqual(["verified", "verified"], [t["state"] for t in self.h.store.all("task")])

    def test_natural_authoring_refuses_inferred_arguments_and_unbounded_recurrence(self):
        self.create()
        for text in ("Every day: 2 + 2", "Every day for 101 runs: 2 + 2"):
            with self.assertRaises(ValueError):
                Assistance.natural_change(text)
        with self.assertRaises(ValueError):
            self.review(Assistance.natural_change("Handle my finances"))
        with self.assertRaises(PermissionError):
            change = Assistance.natural_change("2 + 2")
            change["value"]["node_id"] = "unavailable-node"
            self.review(change)
        self.assertEqual([], self.h.store.all("executive_goal"))

    def test_native_procedure_requires_separate_retention_and_reviewed_verified_replay(self):
        self.complete(self.review(self.create()))
        self.h.executive.tick()
        source = self.h.store.all("executive_goal")[0]
        learn = {"operation": "learn", "id": source["id"], "value": {"retain": True}}
        with self.assertRaises(PermissionError):
            self.review(learn)
        self.grants |= frozenset({"retain"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(self.grants)})
        review = self.review(learn)
        self.assertEqual([], self.h.store.all("executive_workflow"))
        self.complete(review)
        procedure = Assistance(self.h).snapshot()["procedures"][0]
        self.assertEqual("candidate", procedure["state"])
        reuse = self.review(
            {
                "operation": "reuse",
                "id": procedure["id"],
                "value": {
                    "start_at": self.now,
                    "interval_seconds": None,
                    "max_runs": 1,
                    "priority": 0,
                },
            }
        )
        self.assertEqual(source["steps"], json.loads(reuse["review"])["proposal"]["value"]["steps"])
        self.complete(reuse)
        replay = self.h.store.all("executive_goal")[-1]
        self.assertEqual(
            self.owner.id, self.h.store.get("executive_owner", replay["id"])["session"]
        )
        self.h.executive.tick()
        self.complete(
            self.review(
                {
                    "operation": "evaluate",
                    "id": procedure["id"],
                    "value": {
                        "retain": True,
                        "replay_goal_id": replay["id"],
                    },
                }
            )
        )
        self.assertEqual(
            "exact_replay_verified", Assistance(self.h).snapshot()["procedures"][0]["state"]
        )
        self.now += 604801
        self.assertEqual([], Assistance(self.h).snapshot()["procedures"])
        with self.assertRaises((KeyError, PermissionError)):
            self.review(
                {
                    "operation": "reuse",
                    "id": procedure["id"],
                    "value": {
                        "start_at": None,
                        "interval_seconds": None,
                        "max_runs": 1,
                        "priority": 0,
                    },
                }
            )

    def test_resume_displays_full_plan_and_renews_current_signed_owner_binding(self):
        self.complete(self.review(self.create(start_at=self.now + 100)))
        goal = self.h.store.all("executive_goal")[0]
        self.complete(self.review({"operation": "pause", "id": goal["id"], "value": {}}))
        old = self.h.store.get("session", self.owner.id)
        self.h.store.put("session", self.owner.id, {**old, "revoked": True})
        self.owner = self.h.grid.pair(self.owner.node_id, tuple(self.grants))
        self.h.grid.heartbeat(self.owner)
        self.h.store.put(
            "sunday_key",
            self.owner.node_id,
            {
                "session_id": self.owner.id,
                "public_key": self.public,
            },
        )
        review = self.review({"operation": "resume", "id": goal["id"], "value": {}})
        self.assertEqual(goal["steps"], json.loads(review["review"])["current"]["goal"]["steps"])
        self.complete(review)
        self.assertEqual(self.owner.id, self.h.store.get("executive_owner", goal["id"])["session"])

    def test_retention_receipt_recovers_without_duplicate_archive_append(self):
        self.complete(self.review(self.create()))
        self.h.executive.tick()
        self.grants |= frozenset({"retain"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(self.grants)})
        goal = self.h.store.all("executive_goal")[0]
        review = self.review({"operation": "learn", "id": goal["id"], "value": {"retain": True}})
        with patch.object(self.h.store, "audit", side_effect=OSError("synthetic commit failure")):
            with self.assertRaises(OSError):
                self.complete(review)
        self.assertEqual([], self.h.store.all("executive_workflow"))
        self.assertFalse(self.h.store.get("assistance_review", review["challenge_id"])["used"])
        self.now += 1
        self.complete(review)
        candidates = self.h.archive.db.execute(
            "SELECT COUNT(*) FROM archive_events "
            "WHERE json_extract(payload,'$.kind')='workflow_candidate'"
        ).fetchone()[0]
        self.assertEqual(1, candidates)
        self.assertEqual(1, len(Assistance(self.h).snapshot()["procedures"]))

    def test_live_source_lease_refresh_does_not_stale_exact_grant_review(self):
        from oscar.perception import PerceptionSource
        from oscar.world_model import ObservationKind

        source = PerceptionSource(
            "synthetic-live",
            ("owner",),
            ("activity",),
            (ObservationKind.APPLICATION,),
            perceive=True,
        )
        epoch = self.h.world.fabric.register(source, owner_authorized=True)
        self.h.world.fabric.connect(source.id, epoch)
        review = self.review(
            {
                "operation": "source",
                "id": source.id,
                "value": {
                    "perceive": False,
                    "retain": False,
                    "act": False,
                },
            }
        )
        self.now += 1
        self.h.world.fabric.connect(source.id, epoch)
        self.complete(review)
        self.assertFalse(self.h.world.world.source(source.id)["perceive"])

    def test_clock_source_requires_exact_signed_review_and_keeps_retention_separate(self):
        change = {
            "operation": "source_create",
            "id": "reviewed-clock",
            "value": {
                "id": "reviewed-clock",
                "adapter": "time",
                "entity_id": "owner",
                "interval_seconds": 5,
                "retain": False,
                "retention_seconds": 60,
                "timezone": "UTC",
            },
        }
        review = self.review(change)
        with self.assertRaises(KeyError):
            self.h.world.world.source("reviewed-clock")
        material = json.loads(review["review"])["current"]
        self.assertEqual(["datetime", "timezone"], material["fields"])
        self.complete(review)
        source = self.h.world.world.source("reviewed-clock")
        self.assertTrue(source["perceive"])
        self.assertFalse(source["retain"])
        self.assertFalse(source["act"])

    def test_connected_tasks_require_signed_source_and_account_drift_rejects_review(self):
        from oscar.connectors import CredentialRef
        from oscar.oauth_device import VaultResolver
        from tests.test_connections import PrivateVault

        vault = PrivateVault()
        vault.put("synthetic-token", reference="synthetic-tasks")
        self.h.connectors.secrets = VaultResolver(vault)
        account = self.h.accounts.add("google", "synthetic", "tasks", "Tasks", verified=True)
        scopes = ("https://www.googleapis.com/auth/tasks.readonly",)
        account = self.h.accounts.bind(
            account.id, "google.tasks", CredentialRef("synthetic-tasks"), scopes,
            "https://www.googleapis.com",
        )
        change = {"operation": "source_create", "id": "reviewed-tasks", "value": {
            "id": "reviewed-tasks", "adapter": "connected_tasks", "entity_id": "tasks",
            "interval_seconds": 30, "retain": False, "retention_seconds": 3600,
            "account_id": account.id, "account_generation": account.generation,
            "task_list_id": "selected-list",
        }}
        review = self.review(change)
        with self.assertRaises(KeyError):
            self.h.world.world.source("reviewed-tasks")
        self.assertEqual("google.tasks.list", json.loads(review["review"])["current"]["capability"])
        self.h.accounts.bind(
            account.id, "google.tasks", CredentialRef("synthetic-tasks"), scopes,
            "https://www.googleapis.com",
        )
        with self.assertRaises(PermissionError):
            self.complete(review)
        change["value"]["account_generation"] = self.h.accounts.get(account.id).generation
        self.complete(self.review(change))
        source = self.h.world.world.source("reviewed-tasks")
        self.assertTrue(source["perceive"])
        self.assertFalse(source["retain"])
        self.assertFalse(source["act"])
