"""Real SDK tool execution from model plans; arguments never enter durable records."""

import base64
import importlib.util
import json
import sys
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from time import monotonic, sleep

from oscar.connectors import RiskLevel
from oscar.contracts import TaskState
from oscar.jev import Intent
from oscar.mcp_client import MCPServerConfig, executable_digest
from oscar.planner_authoring import PlannerAuthoring
from tests import test_authority as authority_fixture
from tests import test_planner_authoring as fixture


@unittest.skipUnless(importlib.util.find_spec("mcp"), "install oscar-brain[mcp]")
class MCPPlanningTests(unittest.TestCase):
    signature = fixture.PlannerAuthoringTests.signature
    review = fixture.PlannerAuthoringTests.review
    complete = fixture.PlannerAuthoringTests.complete
    close = fixture.PlannerAuthoringTests.close
    draft = fixture.PlannerAuthoringTests.draft
    accept_change = fixture.PlannerAuthoringTests.accept_change

    def setUp(self):
        fixture.PlannerAuthoringTests.setUp(self)
        self.account = self.h.accounts.add(
            "fixture", "synthetic", "writer", "writer", verified=True
        )
        command = str(Path(sys.executable).resolve())
        script = str(Path(__file__).parent.resolve() / "fixtures/mcp_workspace.py")
        self.h.plugins.register(
            MCPServerConfig(
                "writer",
                "Synthetic writer",
                self.account.id,
                self.account.generation,
                command=command,
                arguments=("-I", script, str(self.h.files.root), self.account.id),
                reviewed_files=(
                    (command, executable_digest(command)),
                    (script, executable_digest(script)),
                ),
            ),
            {"write_file": RiskLevel.WRITE, "read_file": RiskLevel.READ},
            owner_reviewed=True,
        )
        self.h.plugins.connect("writer")
        self.mount = self.h.mount_connectors(
            "planning-connectors",
            ("connectors:read", "connectors:write"),
            owner_authorized=True,
        )
        self.cap = self.mount.capability("mcp.write_file", account_id=self.account.id)
        self.grants |= frozenset({"connectors:read", "connectors:write"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            self.h.store.put(
                kind,
                identifier,
                {
                    **self.h.store.get(kind, identifier),
                    "scopes": sorted(self.grants),
                },
            )
        self.executor.connector_plans = self.h.connector_plans
        self.executor.grid = self.h.grid
        self.marker = "Private synthetic connector body 6e813"
        self.steps = [
            {
                "id": "write",
                "node_id": self.mount.node_id,
                "capability_id": self.cap.id,
                "depends_on": [],
                "intent": asdict(
                    Intent(
                        "Write requested artifact",
                        "capability",
                        capability_kind=self.cap.id,
                        parameters={"arguments": {"path": "mcp-plan.txt", "content": self.marker}},
                    )
                ),
            }
        ]
        self.set_response()
        self.change["value"].update(
            goal="Write a synthetic note",
            capabilities=[
                {"node_id": self.h.node_id, "capability_id": "models.reason"},
                {"node_id": self.mount.node_id, "capability_id": self.cap.id},
            ],
        )

    def set_response(self):
        self.body["choices"][0]["message"]["content"] = json.dumps({"steps": self.steps})

    def assert_private(self):
        rows = self.h.store.db.execute("SELECT kind,data FROM records").fetchall()
        self.assertNotIn(self.marker, json.dumps(rows))
        for row in self.h.store.all("assistance_review"):
            if row.get("payload"):
                self.assertNotIn(self.marker, base64.b64decode(row["payload"]).decode())

    def test_structured_compact_mcp_keeps_review_and_private_execution(self):
        self.executor.router.registry.models = {
            k: replace(m, capabilities=frozenset({"text", "structured"}))
            for k, m in self.executor.router.registry.models.items()
        }
        self.executor.template = replace(
            self.executor.template, required=frozenset({"text", "structured"})
        )
        self.steps = [
            {
                "id": "write",
                "capability_id": self.cap.id,
                "depends_on": [],
                "arguments": {"path": "mcp-plan.txt", "content": self.marker},
            }
        ]
        self.set_response()
        self.test_ask_exact_private_review_real_tool_and_consumed_reference()

    def test_reference_schema_decoder_falls_back_without_relocating_mcp_validation(self):
        from jsonschema import Draft202012Validator

        from oscar.planning_contract import executive_plan_schema

        original = {
            "type": "object",
            "properties": {"count": {"$ref": "#/$defs/count"}},
            "$defs": {"count": {"type": "integer", "minimum": 1}},
            "required": ["count"],
            "additionalProperties": False,
        }
        schema = executive_plan_schema(
            connector_schemas={self.cap.id: original}, native_capabilities=()
        )
        self.assertEqual({"a0": {"type": "object"}}, schema["$defs"])
        self.assertTrue(Draft202012Validator(original).is_valid({"count": 1}))
        self.assertFalse(Draft202012Validator(original).is_valid({"count": 0}))
        document = {
            "steps": [
                {
                    "id": "invoke",
                    "capability_id": self.cap.id,
                    "depends_on": [],
                    "arguments": {"count": 0},
                }
            ]
        }
        self.assertTrue(Draft202012Validator(schema).is_valid(document))
        from unittest.mock import patch

        pins = self.h.connector_plans.pins([asdict(self.cap)])
        current = self.h.connector_plans.current(pins[0])
        with patch.object(
            self.h.connector_plans, "current", return_value={**current, "schema": original}
        ):
            with self.assertRaisesRegex(ValueError, "reviewed schema"):
                self.h.connector_plans.sanitize(json.dumps(document), "synthetic-plan", pins)
        self.assertEqual({}, self.h.connector_plans.inputs)
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())

    def test_ask_exact_private_review_real_tool_and_consumed_reference(self):
        row = self.draft()
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())
        self.assert_private()
        review = self.review(self.accept_change(row))
        self.assertIn(self.marker, review["review"])
        saved = self.h.store.get("assistance_review", review["challenge_id"])
        self.assertIn("payload_digest", saved)
        self.assertNotIn("payload", saved)
        self.assert_private()
        self.complete(review)
        self.h.executive.tick()
        pending = self.h.store.all("task")[-1]
        self.assertEqual("planned", pending["state"])
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())
        from oscar.assistance import Assistance

        projection = Assistance(self.h).snapshot(self.grants)
        self.assertEqual(pending["id"], projection["pending_actions"][0]["task_id"])
        action = self.review({"operation": "confirm_task", "id": pending["id"], "value": {}})
        self.assertIn(self.marker, action["review"])
        self.assert_private()
        self.complete(action)
        self.assertEqual([], Assistance(self.h).snapshot(self.grants)["pending_actions"])
        self.finish_effect()
        self.assertEqual({}, self.h.connectors.requests)
        self.assert_private()

    def finish_effect(self):
        deadline = monotonic() + 10
        while monotonic() < deadline:
            self.h.executive.tick()
            if len(self.h.store.all("task")) == 2 and self.h.store.all("task")[-1]["state"] not in {
                "planned",
                "executing",
                "awaiting_result",
                "result_received",
                "verifying",
            }:
                break
            sleep(0.05)
        self.assertTrue(
            (self.h.files.root / "mcp-plan.txt").exists(),
            [{k: t.get(k) for k in ("state", "blocker")} for t in self.h.store.all("task")],
        )
        self.assertEqual(self.marker, (self.h.files.root / "mcp-plan.txt").read_text())
        self.assertEqual("partially_verified", self.h.store.all("task")[-1]["state"])

    def grant_full(self, account_ids):
        payload = authority_fixture.StandingAuthorityTests.payload(
            self,
            "full",
            capabilities=[
                {
                    "node_id": self.h.node_id,
                    "session_id": self.h.session.id,
                    "capability_id": "models.reason",
                },
                {
                    "node_id": self.mount.node_id,
                    "session_id": self.mount.session.id,
                    "capability_id": self.cap.id,
                },
            ],
            account_ids=account_ids,
        )
        review = self.authority.challenge(
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
            self.signature(review),
        )

    def test_signed_full_creates_worker_and_calls_real_tool_without_action_reviews(self):
        self.grant_full([self.account.id])
        result = PlannerAuthoring(self.h).conversation(
            "Write a synthetic note",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        self.finish_effect()
        self.assertEqual([], self.h.store.all("assistance_review"))
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        self.assertEqual(1, len(self.requests))
        self.assert_private()

    def test_expired_input_or_lost_private_review_cannot_execute(self):
        row = self.draft()
        review = self.review(self.accept_change(row))
        self.h.store.transient.clear()
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.now += 121
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(row))
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())

    def test_changed_arguments_block_review(self):
        row = self.draft()
        ref = next(iter(self.h.connectors.requests))
        self.h.connectors.requests[ref]["body"]["content"] = "Changed"
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(row))
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())

    def test_invalid_schema_and_forged_reference_fail_before_persistence(self):
        self.steps[0]["intent"]["parameters"] = {"request_ref": self.marker}
        self.set_response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual({}, self.h.connectors.requests)
        self.assert_private()

    def test_revocation_after_signed_plan_blocks_tool_effect(self):
        row = self.draft()
        self.complete(self.review(self.accept_change(row)))
        self.h.plugins.disconnect("writer")
        for _ in range(3):
            self.h.executive.tick()
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())
        self.assert_private()

    def test_account_generation_change_blocks_review(self):
        row = self.draft()
        self.h.accounts.disconnect(self.account.id)
        with self.assertRaises((PermissionError, KeyError, StopIteration)):
            self.review(self.accept_change(row))
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())

    def test_expiry_change_after_acceptance_never_executes(self):
        row = self.draft()
        self.complete(self.review(self.accept_change(row)))
        self.now += 121
        for _ in range(3):
            self.h.executive.tick()
        self.mount.refresh()
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())
        self.assertEqual({}, self.h.connectors.requests)

    def test_changed_tool_schema_requires_new_installation_review(self):
        row = self.draft()
        client = self.h.plugins.sessions["writer"]
        tool = next(t for t in client.tools if t["name"] == "write_file")
        tool["inputSchema"]["properties"]["content"]["type"] = "integer"
        with self.assertRaises(PermissionError):
            self.review(self.accept_change(row))
        cap = next(
            c
            for c in self.h.store.get("node", self.mount.node_id)["capabilities"]
            if c["id"] == self.cap.id
        )
        self.assertIsNone(self.h.connector_plans.descriptor(cap))
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())

    def test_bad_later_step_releases_all_preceding_private_arguments(self):
        self.steps.append(
            {
                **self.steps[0],
                "id": "bad",
                "intent": asdict(
                    Intent(
                        "Bad arguments",
                        "capability",
                        capability_kind=self.cap.id,
                        parameters={"arguments": {"path": 3, "content": self.marker}},
                    )
                ),
            }
        )
        self.set_response()
        self.draft()
        self.assertEqual("failed", self.h.store.all("task")[-1]["state"])
        self.assertEqual({}, self.h.connectors.requests)
        self.assertEqual({}, self.h.connector_plans.inputs)
        self.assert_private()

    def test_consumed_inflight_guard_survives_reap_and_terminal_cleans_it(self):
        row = self.draft()
        task_id = self.h.executive._tasks(row["goal_id"])[0]
        steps = self.h.executive.result_plan(task_id)["steps"]
        with self.assertRaises(PermissionError):
            self.h.connector_plans.review(steps, "another-planner-task")
        task = self.h.runtime.create(Intent(**steps[0]["intent"]))
        ref = steps[0]["intent"]["parameters"]["request_ref"]
        self.h.connector_plans.check(ref)
        self.h.connectors.release_request(ref)
        self.h.connector_plans.reap()
        self.assertIn(ref, self.h.connector_plans.inputs)
        self.h.store.transition(task.id, TaskState.CANCELLED)
        self.assertNotIn(ref, self.h.connector_plans.inputs)

    def test_expired_private_review_reaped_and_repeating_schedule_rejected(self):
        row = self.draft()
        change = self.accept_change(row)
        change["value"]["max_runs"] = 2
        with self.assertRaises(ValueError):
            self.review(change)
        review = self.review(self.accept_change(row))
        self.now += 31
        self.h.connector_plans.reap()
        self.assertNotIn("assistance-review:" + review["challenge_id"], self.h.store.transient)
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())

    def test_full_capability_grant_cannot_borrow_an_undelegated_account(self):
        self.grant_full([])
        result = PlannerAuthoring(self.h).conversation(
            "Write a synthetic note",
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
        )
        self.assertIn("assistance_started", result)
        for _ in range(5):
            self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual("planned", self.h.store.all("task")[-1]["state"])
        self.assertEqual("waiting_for_authority", self.h.executive.health)
        self.assertEqual([], self.h.connector_plans.pending(self.grants))
        with self.assertRaises(PermissionError):
            self.review(
                {"operation": "confirm_task", "id": self.h.store.all("task")[-1]["id"], "value": {}}
            )
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())
        self.assert_private()

    def test_native_action_review_rechecks_private_input_scope_expiry_and_replay(self):
        row = self.draft()
        self.complete(self.review(self.accept_change(row)))
        self.h.executive.tick()
        task_id = self.h.store.all("task")[-1]["id"]
        change = {"operation": "confirm_task", "id": task_id, "value": {}}
        from oscar.assistance import Assistance

        self.assertEqual([], self.h.connector_plans.pending(frozenset()))
        with self.assertRaises(PermissionError):
            Assistance(self.h).material(change, frozenset())
        review = self.review(change)
        ref = next(iter(self.h.connectors.requests))
        self.h.connectors.requests[ref]["body"]["content"] = "Changed"
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.h.connectors.requests[ref]["body"]["content"] = self.marker
        self.now += 31
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.h.grid.maintain_internal(self.mount.session)
        self.mount.refresh()
        fresh = self.review(change)
        self.complete(fresh)
        with self.assertRaises(PermissionError):
            self.complete(fresh)
        self.now += 90
        self.assertEqual([], self.h.connector_plans.pending(self.grants))
        for _ in range(3):
            self.h.executive.tick()
        self.assertFalse((self.h.files.root / "mcp-plan.txt").exists())
        self.assert_private()
