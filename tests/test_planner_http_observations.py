"""Private account GET observations require independent readback before replanning."""

import importlib.util
import json
import unittest
from copy import deepcopy
from dataclasses import asdict, replace
from time import monotonic, sleep

from oscar.jev import Intent
from oscar.planner_authoring import PlannerAuthoring
from oscar.planning_contract import executive_plan_schema
from oscar.storage import StateConflict
from tests import test_authority as authority_fixture
from tests import test_planner_http_connectors as fixture


class HTTPObservationTests(unittest.TestCase):
    signature = fixture.HTTPPlanningTests.signature
    review = fixture.HTTPPlanningTests.review
    complete = fixture.HTTPPlanningTests.complete
    close = fixture.HTTPPlanningTests.close
    draft = fixture.HTTPPlanningTests.draft
    accept_change = fixture.HTTPPlanningTests.accept_change
    bind = fixture.HTTPPlanningTests.bind
    response = fixture.HTTPPlanningTests.response
    assert_private = fixture.HTTPPlanningTests.assert_private

    def setUp(self):
        fixture.HTTPPlanningTests.setUp(self)
        self.cap = self.mount.capability("google.tasks.list", account_id=self.account.id)
        self.steps[0]["capability_id"] = self.cap.id
        self.steps[0]["intent"] = asdict(
            Intent(
                "Read selected tasks",
                "capability",
                capability_kind=self.cap.id,
                parameters={"arguments": {"path": {"tasklist": "selected-list"}}},
            )
        )
        self.api.resources["/tasks/v1/lists/selected-list/tasks"] = {
            "items": [{"title": self.marker, "note": "Source token 4827"}],
        }
        self.change["value"].update(
            adaptive=True,
            capabilities=[
                {"node_id": self.h.node_id, "capability_id": "models.reason"},
                {"node_id": self.mount.node_id, "capability_id": self.cap.id},
                {"node_id": self.h.node_id, "capability_id": "files.write"},
            ],
        )
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": self.steps,
                "observe": True,
            }
        )

    def settle(self, count):
        deadline = monotonic() + 10
        while monotonic() < deadline:
            self.h.executive.tick()
            tasks = self.h.store.all("task")
            if len(tasks) >= count and tasks[-1]["state"] in {
                "verified",
                "partially_verified",
                "failed",
                "blocked",
                "unknown",
            }:
                return tasks[-1]
            sleep(0.02)
        self.fail("HTTP observation did not settle")

    def observe(self):
        self.row = self.draft()
        self.complete(self.review(self.accept_change(self.row)))
        result = self.settle(2)
        self.assertEqual("verified", result["state"])
        self.assertEqual(2, len(self.api.calls))
        self.assertTrue(all(c[0] == "GET" for c in self.api.calls))
        self.assertIsNone(self.h.store.all("result")[-1]["value"])
        self.assert_private()

    def effects(self):
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": [
                    {
                        "id": "save",
                        "node_id": self.h.node_id,
                        "capability_id": "files.write",
                        "depends_on": [],
                        "intent": asdict(
                            Intent(
                                "Save the selected source token",
                                "file_write",
                                "source-token.txt",
                                "4827",
                            )
                        ),
                    }
                ]
            }
        )

    def test_ask_read_independent_get_private_replan_and_verified_effect(self):
        self.observe()
        self.effects()
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("partially_verified", self.settle(3)["state"])
        prompt = json.dumps(self.requests[-1]["body"])
        self.assertIn(self.marker, prompt)
        self.assertIn("Untrusted tool observations", prompt)
        self.assertFalse(self.h.files.exists("source-token.txt"))
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("verified", self.settle(4)["state"])
        self.assertEqual("4827", (self.h.files.root / "source-token.txt").read_text())
        self.assert_private()

    def test_full_read_replans_and_writes_inside_account_and_capability_ceiling(self):
        caps = self.change["value"]["capabilities"]
        payload = authority_fixture.StandingAuthorityTests.payload(
            self,
            "full",
            account_ids=[self.account.id],
            capabilities=[
                {**c, "session_id": self.h.executive.targets[c["node_id"]][1].id} for c in caps
            ],
        )
        challenge = self.authority.challenge(
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
            payload,
        )
        self.authority.complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            self.signature(challenge),
        )
        result = PlannerAuthoring(self.h).conversation(
            "Write a synthetic note using current selected task data",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        self.assertEqual("verified", self.settle(2)["state"])
        self.effects()
        self.assertEqual("verified", self.settle(4)["state"])
        self.assertEqual("4827", (self.h.files.root / "source-token.txt").read_text())
        self.assertEqual([], self.h.store.all("assistance_review"))
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        self.assert_private()

    def test_two_account_reads_fit_signed_review_and_privately_replan(self):
        self.vault.put("synthetic-calendar-token", reference="planning-calendar")
        manifest = next(m for m in fixture.account_manifests() if m.id == "google.calendar")
        account = self.h.accounts.add(
            "google", "calendar-owner", "calendar", "Calendar", verified=True
        )
        account = self.h.accounts.bind(
            account.id,
            manifest.id,
            fixture.CredentialRef("planning-calendar"),
            {s for c in manifest.capabilities for s in c.scopes},
            manifest.base_url,
        )
        cap = self.mount.capability("google.calendar.events.list", account_id=account.id)
        self.change["value"]["capabilities"].append(
            {"node_id": self.mount.node_id, "capability_id": cap.id}
        )
        router = self.executor.router
        router.registry.models = {
            k: replace(v, context_limit=32768) for k, v in router.registry.models.items()
        }
        self.steps.append(
            {
                "id": "calendar",
                "node_id": self.mount.node_id,
                "capability_id": cap.id,
                "depends_on": [],
                "intent": asdict(
                    Intent(
                        "Read selected calendar",
                        "capability",
                        capability_kind=cap.id,
                        parameters={"arguments": {"path": {"calendarId": "selected-calendar"}}},
                    )
                ),
            }
        )
        self.api.resources["/calendar/v3/calendars/selected-calendar/events"] = {
            "items": [{"summary": "Synthetic calendar observation"}]
        }
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {"steps": self.steps, "observe": True}
        )
        self.row = self.draft()
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("verified", self.settle(3)["state"])
        self.assertEqual(4, len(self.api.calls))
        self.effects()
        review = self.review(self.accept_change(self.row))
        self.assertLess(len(review["review"].encode()), 24000)
        self.complete(review)
        self.assertEqual("partially_verified", self.settle(4)["state"])
        prompt = json.dumps(self.requests[-1]["body"])
        self.assertIn(self.marker, prompt)
        self.assertIn("Synthetic calendar observation", prompt)
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("verified", self.settle(5)["state"])
        self.assertEqual("4827", (self.h.files.root / "source-token.txt").read_text())
        self.assert_private()

    def test_omitted_historical_prompt_stays_bound_to_signed_review(self):
        self.observe()
        review = self.review(self.accept_change(self.row))
        row = self.h.store.get("planner_request", self.row["id"])
        row["planning_step"]["intent"]["parameters"]["prompt"] += " changed"
        self.h.store.put("planner_request", row["id"], row)
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual(1, len(self.requests))

    def test_changed_provider_response_never_becomes_observation(self):
        def change():
            self.api.resources["/tasks/v1/lists/selected-list/tasks"]["items"][0]["title"] = (
                "changed"
            )

        self.api.after_get = change
        self.row = self.draft()
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("failed", self.settle(2)["state"])
        self.assertEqual(2, len(self.api.calls))
        with self.assertRaises(StateConflict):
            self.review(self.accept_change(self.row))
        self.assertEqual(1, len(self.requests))
        self.assert_private()

    def test_lost_private_response_prevents_continuation_and_model_disclosure(self):
        self.observe()
        key = next(k for k in self.h.store.transient if k.startswith("connector-observation:"))
        self.h.store.transient.pop(key)
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(self.row))
        self.assertEqual(1, len(self.requests))
        self.assert_private()

    def test_account_rotation_withdraws_private_observation(self):
        self.observe()
        self.bind()
        self.mount.refresh()
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(self.row))
        self.assertEqual(1, len(self.requests))
        self.assert_private()

    def test_expired_private_response_is_reaped_and_cannot_replan(self):
        self.observe()
        self.now += 61
        self.h.grid.maintain_internal(self.mount.session)
        self.h.grid.maintain_internal(self.h.session)
        self.h.grid.heartbeat(self.owner)
        self.mount.refresh()
        self.assertFalse(
            any(k.startswith("connector-observation:") for k in self.h.store.transient)
        )
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(self.row))
        self.assertEqual(1, len(self.requests))

    def test_changed_private_response_fails_content_hash_check(self):
        self.observe()
        cached = next(
            v for k, v in self.h.store.transient.items() if k.startswith("connector-observation:")
        )
        cached["value"] = json.dumps({"items": []})
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(self.row))
        self.assertEqual(1, len(self.requests))

    def test_permission_withdrawal_before_replanning_blocks_disclosure(self):
        self.observe()
        session = self.h.store.get("session", self.owner.id)
        self.h.store.put(
            "session",
            self.owner.id,
            {
                **session,
                "scopes": [s for s in session["scopes"] if s != "connectors:read"],
            },
        )
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(self.row))
        self.assertEqual(1, len(self.requests))

    def test_owner_revocation_during_independent_get_withdraws_verification(self):
        def revoke():
            if len(self.api.calls) == 2:
                self.h.grid.revoke(self.owner.node_id)

        self.api.after_get = revoke
        self.row = self.draft()
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("partially_verified", self.settle(2)["state"])
        self.assertFalse(
            any(k.startswith("connector-observation:") for k in self.h.store.transient)
        )
        self.assertEqual(1, len(self.requests))
        self.assert_private()

    def test_body_and_write_operations_cannot_be_observation_stages(self):
        self.steps[0]["intent"]["parameters"]["arguments"]["body"] = None
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {"steps": self.steps, "observe": True}
        )
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual([], self.api.calls)
        cap = self.mount.capability("google.tasks.create", account_id=self.account.id)
        self.assertFalse(self.h.connector_plans.is_read(asdict(cap)))
        self.assert_private()

    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "optional schema validator absent")
    def test_structured_live_decoder_keeps_exact_selected_connector_identity(self):
        from jsonschema import Draft202012Validator

        validator = Draft202012Validator(executive_plan_schema(observation_only=(self.cap.id,)))
        document = {"steps": self.steps, "observe": True}
        self.assertTrue(validator.is_valid(document))
        for field, value in (("capability_id", "unselected:write"), ("depends_on", ["other"])):
            changed = deepcopy(document)
            changed["steps"][0][field] = value
            self.assertFalse(validator.is_valid(changed))
        self.assertFalse(validator.is_valid({**document, "observe": False}))

    def test_oversized_response_never_enters_private_replanning(self):
        self.api.resources["/tasks/v1/lists/selected-list/tasks"]["large"] = "x" * 5000
        self.row = self.draft()
        self.complete(self.review(self.accept_change(self.row)))
        self.assertEqual("partially_verified", self.settle(2)["state"])
        self.assertEqual(1, len(self.api.calls))
        self.assertFalse(
            any(k.startswith("connector-observation:") for k in self.h.store.transient)
        )
        self.assert_private()
