"""Scoped directory discovery feeds private planning, never arbitrary process output."""

import base64
import json
import unittest
from dataclasses import asdict, replace
from time import monotonic, sleep
from unittest.mock import patch

from oscar.credentials import CredentialPool
from oscar.harness import ModelExecutor
from oscar.jev import Intent
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_authoring import PlannerAuthoring
from oscar.planner_observations import validate_stage
from oscar.policy import PersonalPolicy
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.remote_machine import machine_readback
from oscar.router import Router
from tests import test_providers as provider_fixture
from tests import test_remote_machine as fixture
from tests.test_remote_grid import signature


def step(capability="machine.files.list", kind="directory_list", **parameters):
    return {
        "id": "discover",
        "node_id": "test-machine",
        "capability_id": capability,
        "depends_on": [],
        "intent": asdict(
            Intent(
                "Discover scoped files", "capability", capability_kind=kind, parameters=parameters
            )
        ),
    }


class DirectoryObservationTests(unittest.TestCase):
    setUp = fixture.RemoteMachineExecutionTests.setUp
    enroll = fixture.RemoteMachineExecutionTests.enroll
    start_worker = fixture.RemoteMachineExecutionTests.start_worker
    submit = fixture.RemoteMachineExecutionTests.submit
    approve = fixture.RemoteMachineExecutionTests.approve
    finish = fixture.RemoteMachineExecutionTests.finish

    def test_typed_bounded_queries_exclude_commands_and_unknown_fields(self):
        for cap, kind, parameters in (
            ("machine.files.list", "directory_list", {}),
            ("machine.files.search", "file_search", {"pattern": ".txt", "cwd": "notes"}),
        ):
            validate_stage([step(cap, kind, **parameters)])
            self.assertEqual({"cwd": ".", **parameters}, machine_readback(cap, parameters))
            for invalid in (
                {"shell": "read"},
                {"cwd": False},
                {"cwd": "x" * 241},
                {"pattern": "x" * 201},
                {"pattern": 1},
            ):
                with self.subTest(cap=cap, invalid=invalid), self.assertRaises(ValueError):
                    validate_stage([step(cap, kind, **{**parameters, **invalid})])

    def test_authenticated_search_has_independent_readback_and_detects_drift(self):
        self.start_worker(("machine.files.search",))
        (self.workspace / "source.txt").write_text("314")
        task = self.submit("file_search", {"cwd": ".", "pattern": ".txt"})
        self.assertEqual("verified", self.finish(task)["state"])
        task = self.submit("file_search", {"cwd": ".", "pattern": ".txt"})
        readback = self.worker.readback_effect

        def changed(action, delivery):
            (self.workspace / "late.txt").write_text("changed")
            return readback(action, delivery)

        with patch.object(self.worker, "readback_effect", side_effect=changed):
            self.assertEqual("failed", self.finish(task)["state"])

    def test_outside_directory_and_oversized_names_fail_closed(self):
        self.start_worker(("machine.files.list",))
        for cwd in ("../", str(self.root)):
            task = self.submit("directory_list", {"cwd": cwd})
            self.assertEqual("failed", self.finish(task)["state"])
        for i in range(30):
            (self.workspace / (str(i) + "x" * 150)).write_text("")
        task = self.submit("directory_list", {"cwd": "."})
        self.assertEqual("failed", self.finish(task)["state"])

    def test_full_worker_discovers_reads_and_saves_without_action_reviews(self):
        self.workflow()

    def test_current_information_worker_observes_live_files_before_effects(self):
        self.workflow(current=True)

    def test_current_information_worker_cannot_skip_observation(self):
        self.workflow(current=True, skip=True)

    def workflow(self, current=False, skip=False):
        caps = ("machine.files.list", "machine.files.read", "machine.files.write")
        self.start_worker(caps)
        (self.workspace / "notes").mkdir()
        (self.workspace / "notes/source-314.txt").write_text("Source value 314")
        provider_case = provider_fixture.ProviderContractTests()
        provider_case.setUp()
        self.addCleanup(provider_case.doCleanups)
        h = self.core.harness
        provider = replace(
            provider_case.provider, credential_envs={"synthetic": "SYNTHETIC_PLANNER"}
        )
        model = ModelSpec(
            "fixture",
            "fixture-model",
            frozenset({"text"}),
            2,
            {"reasoning": 1},
            8192,
            4096,
            Funding.FREE,
            provenance="synthetic HTTP fixture",
        )
        h.dispatcher.executors["models.reason"] = ModelExecutor(
            Router(
                Registry([provider], [model]),
                CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic"}, h.store),
                {"openai": HTTPAdapter("openai")},
                h.store,
            ),
            ModelRequest("template", "template", ""),
            RoutingPolicy(),
            grid=h.grid,
        )
        review = self.owner.request(
            "authority_challenge",
            {
                "mode": "full",
                "lifetime_seconds": 600,
                "account_ids": [],
                "capabilities": [
                    {"node_id": session.node_id, "session_id": session.id, "capability_id": cap}
                    for session, cap in [
                        *((self.desktop.handle, c) for c in caps),
                        (h.session, "models.reason"),
                    ]
                ],
                "resolve_ask_rules": sorted(
                    r.id for r in PersonalPolicy(h.store).rules() if r.enabled and r.effect == "ask"
                ),
            },
        )
        self.owner.request(
            "authority_complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": signature(self.owner_key, base64.b64decode(review["signing_payload"])),
            },
        )
        first = step(cwd="notes")
        second = {
            **step("machine.files.read", "file_read", path="notes/source-314.txt"),
            "id": "read",
        }
        final = {
            **step(),
            "id": "save",
            "capability_id": "machine.files.write",
            "intent": asdict(Intent("Save discovered source", "file_write", "answer.txt", "314")),
        }
        responses = (
            {"steps": [first], "observe": True},
            {"steps": [second], "observe": True},
            {"steps": [final]},
        )
        if skip:
            responses = ({"steps": [final]},)
        provider_case.scheduled = [
            (200, {**provider_case.body, "choices": [{"message": {"content": json.dumps(value)}}]})
            for value in responses
        ]
        goal = (
            "Create worker Discover: On device test-machine: First inspect "
            + ("current files in notes, " if current else "notes, ")
            + "read its source file, then save its numeric value as answer.txt"
        )
        if current:
            manual = {
                "name": "Live files",
                "goal": goal,
                "mode": "private",
                "capabilities": [
                    {"node_id": s.node_id, "capability_id": c}
                    for s, c in [
                        *((self.desktop.handle, c) for c in caps),
                        (h.session, "models.reason"),
                    ]
                ],
            }
            material = PlannerAuthoring(h).material(
                "plan_draft", "new", manual, frozenset(self.owner.session["scopes"])
            )
            self.assertTrue(material["adaptive"])
            self.assertIn("Adaptive stages", material["privacy"])
            with self.assertRaises(PermissionError):
                PlannerAuthoring(h).material(
                    "plan_draft",
                    "new",
                    {**manual, "adaptive": False},
                    frozenset(self.owner.session["scopes"]),
                )
        result = self.owner.request(
            "submit",
            {
                "text": goal,
                "kind": "text",
                "target": h.node_id,
                "parameters": {},
                "retain": True,
            },
        )
        self.assertEqual("full", result["assistance_started"]["mode"])
        deadline = monotonic() + 20
        while monotonic() < deadline:
            self.worker.step()
            if skip and h.store.all("planner_request")[0].get("autonomy_blocked"):
                break
            if (self.workspace / "answer.txt").exists():
                row = h.store.all("planner_request")[0]
                if h.store.get("executive_goal", row["accepted_goal"])["state"] == "completed":
                    break
            sleep(0.02)
        else:
            self.fail("canonical discovery/read/effect workflow did not complete")
        if current:
            self.assertIn(
                "Controller live preflight", json.dumps(provider_case.requests[0]["body"])
            )
            prompt = provider_case.requests[0]["body"]["messages"][0]["content"]
            self.assertNotIn('"capability_id": "machine.files.write"', prompt)
            self.assertTrue(
                h.store.all("planner_request")[0]["planning_step"]["intent"]["parameters"][
                    "observation_only"
                ]
            )
        if skip:
            self.assertEqual(1, len(provider_case.requests))
            self.assertFalse((self.workspace / "answer.txt").exists())
            self.assertFalse(
                any(
                    a["capability_id"] == "machine.files.write"
                    for a in h.store.all("planned_action")
                )
            )
            return
        self.assertEqual("314", (self.workspace / "answer.txt").read_text())
        self.assertEqual(3, len(provider_case.requests))
        if current:
            prompt = provider_case.requests[1]["body"]["messages"][0]["content"]
            self.assertIn('"capability_id": "machine.files.write"', prompt)
            self.assertNotIn("Controller live preflight", prompt)
        self.assertIn("source-314.txt", json.dumps(provider_case.requests[1]["body"]))
        self.assertIn("observed_at", json.dumps(provider_case.requests[1]["body"]))
        self.assertIn("expires_at", json.dumps(provider_case.requests[1]["body"]))
        self.assertIn("Source value 314", json.dumps(provider_case.requests[2]["body"]))
        self.assertEqual(
            ["private", "private"], [r["mode"] for r in h.store.all("route_history")][1:]
        )
        self.assertEqual(1, len(h.store.all("executive_worker")))
