"""Actual outbound machine execution, with no second local Core or authority database."""

import base64
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep, time

from oscar.cloud import CloudConfig, CloudCore
from oscar.machine import MachineScope
from oscar.remote_grid import create_invitation
from oscar.remote_machine import (
    RemoteEffects,
    RemoteMachine,
    machine_readback,
    validate_remote_machine,
)
from oscar.remote_worker import RemoteCancellation
from tests.test_cloud import configuration
from tests.test_remote_grid import DirectClient, keypair, signature


class RemoteMachineContractTests(unittest.TestCase):
    def test_running_poll_is_bounded_but_effect_boundaries_and_revocation_are_fresh(self):
        from unittest.mock import Mock, patch

        effects = object.__new__(RemoteEffects)
        effects._last_running_check = 0.0
        guard = Mock()
        action = Mock()
        cancellation = RemoteCancellation(guard)
        with patch("oscar.remote_machine.monotonic", return_value=10) as clock:
            effects.check_running(action, cancellation)
            for instant in (10.02, 10.5, 10.99):
                clock.return_value = instant
                effects.check_running(action, cancellation)
            self.assertEqual(1, guard.call_count)
            effects.check(action, cancellation)  # A new effect never inherits the polling cache.
            self.assertEqual(2, guard.call_count)
            clock.return_value = 11
            effects.check_running(action, cancellation)
            self.assertEqual(3, guard.call_count)
            guard.side_effect = PermissionError("revoked")
            clock.return_value = 12
            with self.assertRaises(PermissionError):
                effects.check_running(action, cancellation)
            self.assertEqual(11, effects._last_running_check)
        with self.assertRaises(PermissionError):
            effects.check(action, Mock())

    def test_readback_derives_only_the_exact_reviewed_destination(self):
        request = {
            "operation": "set_text_checked",
            "handle": 123,
            "pid": 456,
            "runtime_id": "selected",
            "text": "reviewed",
            "expected_text": "old",
        }
        self.assertEqual(
            {"operation": "read", "handle": 123, "pid": 456, "runtime_id": "selected"},
            machine_readback("machine.desktop", {"request": request}),
        )
        self.assertIsNone(machine_readback("machine.command", {"request": request}))
        self.assertIsNone(
            machine_readback("machine.desktop", {"request": {**request, "extra": True}})
        )
        self.assertIsNone(machine_readback("machine.desktop", {"request": {"operation": "invoke"}}))
        self.assertEqual(
            {"operation": "clipboard_read"},
            machine_readback(
                "machine.clipboard",
                {"request": {"operation": "clipboard_write", "text": "reviewed"}},
            ),
        )

    def test_exact_bounded_arguments_and_browser_plan(self):
        parameters = {"argv": ["C:/trusted/python.exe", "--version"], "timeout": 5}
        self.assertEqual(parameters, validate_remote_machine("terminal_command", parameters))
        plan = {
            "origins": ["http://127.0.0.1:8765"],
            "steps": [{"operation": "navigate", "url": "http://127.0.0.1:8765/"}],
            "timeout": 10,
            "max_text": 1000,
        }
        self.assertEqual({"request": plan}, validate_remote_machine("browser", {"request": plan}))
        for kind, invalid in (
            ("terminal_command", {"argv": []}),
            ("terminal_command", {"argv": ["trusted"], "timeout": float("nan")}),
            ("terminal_command", {"argv": ["trusted"], "shell": True}),
            ("browser", {"request": plan, "account_id": "other"}),
            ("powershell", {"request": "arbitrary shell text"}),
            ("executable_discovery", {"private": "parameter"}),
        ):
            with self.subTest(kind=kind, invalid=invalid), self.assertRaises(ValueError):
                validate_remote_machine(kind, invalid)

    def test_process_artifact_readback_is_only_the_exact_bounded_reviewed_path(self):
        parameters = {
            "argv": ["C:/trusted/python.exe", "--version"],
            "verification": {"path": "result.txt", "content": "42"},
        }
        self.assertEqual(parameters, validate_remote_machine("terminal_command", parameters))
        self.assertEqual({"path": "result.txt"}, machine_readback("machine.command", parameters))
        self.assertEqual(
            {"path": "result.txt"}, machine_readback("machine.agent.codex", parameters)
        )
        for expected in (
            None,
            {"path": "../outside", "content": "42"},
            {"path": "C:/outside", "content": "42"},
            {"path": "result.txt", "content": "x" * 8193},
            {"path": "result.txt", "content": "42", "command": "unreviewed"},
        ):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                validate_remote_machine(
                    "terminal_command", {**parameters, "verification": expected}
                )

    def test_browser_cross_origin_and_script_steps_still_reject(self):
        plan = {
            "origins": ["https://example.com"],
            "steps": [{"operation": "navigate", "url": "https://other.example/"}],
            "timeout": 10,
            "max_text": 1000,
        }
        with self.assertRaises(PermissionError):
            validate_remote_machine("browser", {"request": plan})
        plan["steps"] = [{"operation": "evaluate", "script": "document.cookie"}]
        with self.assertRaises(ValueError):
            validate_remote_machine("browser", {"request": plan})

    def test_browser_readback_is_exact_read_only_and_cannot_expand_origins(self):
        plan = {
            "origins": ["https://example.com"],
            "steps": [{"operation": "navigate", "url": "https://example.com/form"}],
            "timeout": 30,
            "max_text": 1000,
        }
        parameters = {
            "request": plan,
            "account_id": "account",
            "account_generation": 2,
            "verification": {
                "url": "https://example.com/receipt",
                "selector": "#receipt",
                "text": "Saved",
            },
        }
        validate_remote_machine("browser", parameters)
        readback = machine_readback("machine.browser", parameters)
        self.assertEqual("account", readback["account_id"])
        self.assertEqual(2, readback["account_generation"])
        self.assertEqual(
            ["navigate", "read_text"], [step["operation"] for step in readback["request"]["steps"]]
        )
        self.assertEqual(15, readback["request"]["timeout"])
        for change in (
            {"url": "https://other.example/"},
            {"selector": ""},
            {"text": "x" * 8193},
            {"script": "unreviewed"},
        ):
            with self.subTest(change=change), self.assertRaises((ValueError, PermissionError)):
                validate_remote_machine(
                    "browser",
                    {**parameters, "verification": {**parameters["verification"], **change}},
                )


class RemoteMachineExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core = CloudCore(CloudConfig.load(configuration(self.root)), initialize=True)
        self.addCleanup(self.core.close)
        self.transport_key, self.transport_public = keypair()
        self.owner_key, self.owner_public = keypair()
        self.desktop = self.enroll("test-machine", "desktop")
        self.owner = self.enroll("test-controller", "mobile")
        self.workspace = self.root / "effects"
        self.workspace.mkdir()
        self.worker = None

    def enroll(self, node, role):
        invite = create_invitation(
            self.core,
            node,
            role,
            "installation-" + node,
            self.transport_public,
            workspace="test-effects" if role == "desktop" else "",
            retain=True,
            owner_public_key=self.owner_public,
            machine_control=True,
        )
        session = self.core.remote.enroll(
            {
                "version": 2,
                "challenge_id": invite["challenge_id"],
                "signature": signature(
                    self.transport_key, base64.b64decode(invite["signing_payload"])
                ),
            }
        )
        return DirectClient(self.core, session)

    def start_worker(self, capabilities, *, browser=False, desktop=False, profiles=False):
        executables = [str(Path(sys.executable).resolve())]
        if os.name == "nt":
            executables.append(
                str(
                    Path(os.environ["SystemRoot"])
                    / "System32/WindowsPowerShell/v1.0/powershell.exe"
                )
            )
        self.worker = RemoteMachine(
            self.desktop,
            MachineScope(self.workspace, True, tuple(executables), max_output=8192),
            "test-effects",
            self.root / "execution.sqlite",
            capabilities=capabilities,
            browser=browser,
            desktop=desktop,
            profile_root=self.root / "private-profiles" if profiles else None,
        )
        self.addCleanup(self.worker.close)
        self.worker.advertise()

    def submit(self, kind, parameters):
        return self.owner.request(
            "submit",
            {
                "text": "Execute the reviewed synthetic machine objective",
                "kind": kind,
                "target": "test-machine",
                "parameters": parameters,
                "retain": True,
            },
        )

    def approve(self, task):
        review = self.owner.request(
            "challenge", {"task_id": task["task_id"], "operation": "approve"}
        )
        return self.owner.request(
            "complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": signature(self.owner_key, base64.b64decode(review["signing_payload"])),
            },
        )

    def finish(self, task):
        deadline = time() + 35
        while time() < deadline:
            self.worker.step()
            view = self.owner.request("inspect", {"task_id": task["task_id"]})
            if view["state"] in {
                "verified",
                "partially_verified",
                "failed",
                "blocked",
                "unknown",
                "cancelled",
            }:
                return view
            sleep(0.02)
        self.fail("canonical remote task did not complete")

    def test_actual_native_command_keeps_unverified_objective_partial(self):
        self.start_worker(("machine.command",))
        task = self.submit(
            "terminal_command",
            {
                "argv": [
                    str(Path(sys.executable).resolve()),
                    "-I",
                    "-c",
                    "from pathlib import Path; "
                    "Path('effect.txt').write_text('synthetic remote effect')",
                ],
                "timeout": 10,
            },
        )
        self.assertFalse((self.workspace / "effect.txt").exists())
        self.assertEqual("planned", task["state"])
        self.approve(task)
        final = self.finish(task)
        self.assertEqual("partially_verified", final["state"])
        self.assertEqual("synthetic remote effect", (self.workspace / "effect.txt").read_text())
        self.assertIsNone(self.worker.effects.store)
        self.assertIsNone(self.worker.effects.grid)
        self.assertEqual({}, self.worker.effects.outputs)
        self.assertEqual(
            1, self.worker.journal.execute("SELECT count(*) FROM execution_claim").fetchone()[0]
        )

    def artifact_parameters(self, expected="42"):
        return {
            "argv": [
                str(Path(sys.executable).resolve()),
                "-I",
                "-c",
                "from pathlib import Path; Path('effect.txt').write_text('42')",
            ],
            "timeout": 10,
            "verification": {"path": "effect.txt", "content": expected},
        }

    def test_remote_process_exact_artifact_uses_separate_read_and_core_comparison(self):
        self.start_worker(("machine.command", "machine.files.read"))
        task = self.submit("terminal_command", self.artifact_parameters())
        self.assertFalse((self.workspace / "effect.txt").exists())
        self.approve(task)
        self.assertEqual("verified", self.finish(task)["state"])
        self.assertEqual("42", (self.workspace / "effect.txt").read_text())
        deliveries = [
            r
            for r in self.core.harness.store.all("remote_delivery")
            if r["task_id"] == task["task_id"]
        ]
        self.assertEqual({"action", "readback"}, {r["kind"] for r in deliveries})
        evidence = [
            r for r in self.core.harness.store.all("evidence") if r["task_id"] == task["task_id"]
        ]
        self.assertEqual("remote-scoped-filesystem", evidence[-1]["source"])
        self.assertTrue(evidence[-1]["matches"])
        for _ in range(2):
            self.worker.step()
        self.assertEqual(
            1, self.worker.journal.execute("SELECT count(*) FROM execution_claim").fetchone()[0]
        )

    def test_wrong_remote_process_artifact_fails_without_process_replay(self):
        self.start_worker(("machine.command", "machine.files.read"))
        task = self.submit("terminal_command", self.artifact_parameters("different"))
        self.approve(task)
        self.assertEqual("failed", self.finish(task)["state"])
        self.assertEqual("42", (self.workspace / "effect.txt").read_text())
        self.worker.step()
        self.assertEqual(
            1, self.worker.journal.execute("SELECT count(*) FROM execution_claim").fetchone()[0]
        )

    def test_reader_withdrawal_after_effect_preserves_uncertainty_and_never_replays(self):
        self.start_worker(("machine.command", "machine.files.read"))
        original = self.worker.execute_effect

        def withdraw(action, cancellation):
            result = original(action, cancellation)
            self.worker.allowed -= {"machine.files.read"}
            return result

        self.worker.execute_effect = withdraw
        task = self.submit("terminal_command", self.artifact_parameters())
        self.approve(task)
        with self.assertRaises(PermissionError):
            self.finish(task)
        self.assertEqual("42", (self.workspace / "effect.txt").read_text())
        self.assertNotEqual("verified", self.core.harness.store.task(task["task_id"]).state)
        self.assertEqual(
            1, self.worker.journal.execute("SELECT count(*) FROM execution_claim").fetchone()[0]
        )

    def test_process_artifact_requires_separately_advertised_read_permission(self):
        self.start_worker(("machine.command",))
        with self.assertRaises(PermissionError):
            self.submit("terminal_command", self.artifact_parameters())
        self.assertFalse((self.workspace / "effect.txt").exists())

    def test_process_artifact_requires_requester_read_permission_and_standing_coverage(self):
        from oscar.contracts import Capability

        self.start_worker(("machine.command", "machine.files.read"))
        remote = self.core.remote
        command = next(c for c in self.core.harness.grid.search("terminal_command"))
        self.assertIsInstance(command, Capability)
        with self.assertRaisesRegex(PermissionError, "standing delegation"):
            remote.artifact_permission(
                self.owner.handle.id,
                self.desktop.handle,
                command,
                self.artifact_parameters(),
                delegated=True,
            )
        store = self.core.harness.store
        row = store.get("session", self.owner.handle.id)
        store.put(
            "session", row["id"], {**row, "scopes": [s for s in row["scopes"] if s != "files:read"]}
        )
        with self.assertRaises(PermissionError):
            self.submit("terminal_command", self.artifact_parameters())
        self.assertFalse((self.workspace / "effect.txt").exists())

    def activate_artifact_delegation(self, *, reader=True, coding=False, planner=False):
        from oscar.policy import PersonalPolicy

        payload = {
            "mode": "full",
            "lifetime_seconds": 600,
            "account_ids": [],
            "capabilities": [
                {
                    "node_id": session.node_id,
                    "session_id": session.id,
                    "capability_id": name,
                }
                for session, name in (
                    [(self.desktop.handle, "machine.agent.codex" if coding else "machine.command")]
                    + ([(self.desktop.handle, "machine.files.read")] if reader else [])
                    + ([(self.core.harness.session, "models.reason")] if planner else [])
                )
            ],
            "resolve_ask_rules": sorted(
                r.id
                for r in PersonalPolicy(self.core.harness.store).rules()
                if r.enabled and r.effect == "ask"
            ),
        }
        review = self.owner.request("authority_challenge", payload)
        self.owner.request(
            "authority_complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": signature(self.owner_key, base64.b64decode(review["signing_payload"])),
            },
        )

    def test_artifact_permission_obeys_permission_specific_owner_and_executor_denials(self):
        from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule

        self.start_worker(("machine.command", "machine.files.read"))
        policy = PersonalPolicy(self.core.harness.store)
        for node in (self.owner.handle.node_id, self.desktop.handle.node_id):
            with self.subTest(node=node):
                now = time()
                policy.save(
                    PolicyRule(
                        "deny-reader",
                        "files:read",
                        PolicyEffect.DENY,
                        "synthetic owner",
                        now,
                        now,
                        {"node": node},
                    ),
                    owner_authorized=True,
                )
                with self.assertRaises(PermissionError):
                    self.submit("terminal_command", self.artifact_parameters())
        self.assertFalse((self.workspace / "effect.txt").exists())
        self.assertEqual([], self.core.harness.store.all("remote_delivery"))

    def test_standing_delegation_covers_process_and_independent_reader(self):
        self.start_worker(("machine.command", "machine.files.read"))
        self.activate_artifact_delegation()
        task = self.submit("terminal_command", self.artifact_parameters())
        self.assertEqual("verified", self.finish(task)["state"])
        self.assertEqual([], self.core.harness.store.all("executive_confirmation"))

    def test_standing_process_authority_does_not_silently_borrow_reader(self):
        self.start_worker(("machine.command", "machine.files.read"))
        self.activate_artifact_delegation(reader=False)
        with self.assertRaisesRegex(PermissionError, "standing delegation"):
            self.submit("terminal_command", self.artifact_parameters())
        self.assertFalse((self.workspace / "effect.txt").exists())
        self.assertEqual([], self.core.harness.store.all("remote_delivery"))

    def test_owner_signed_remote_coding_worker_verifies_before_dependent_read(self):
        import shutil
        from dataclasses import asdict
        from unittest.mock import patch

        from oscar.jev import Intent

        original = shutil.which
        # Synthetic agent binding: a real Python child, no provider credentials or agent launch.
        with patch(
            "oscar.machine.shutil.which",
            side_effect=lambda name: sys.executable if name == "codex" else original(name),
        ):
            self.start_worker(("machine.agent.codex", "machine.files.read"))
        parameters = self.artifact_parameters()
        parameters["arguments"] = parameters.pop("argv")[1:]
        steps = []
        for identifier, capability, intent in (
            (
                "code",
                "machine.agent.codex",
                Intent(
                    "Produce exact requested artifact",
                    "capability",
                    capability_kind="coding",
                    parameters=parameters,
                    criterion={"kind": "file_exact", "path": "effect.txt", "content": "42"},
                ),
            ),
            (
                "read",
                "machine.files.read",
                Intent(
                    "Read verified artifact",
                    "capability",
                    capability_kind="file_read",
                    parameters={"path": "effect.txt"},
                ),
            ),
        ):
            steps.append(
                {
                    "id": identifier,
                    "node_id": self.desktop.handle.node_id,
                    "capability_id": capability,
                    "intent": asdict(intent),
                    "depends_on": [] if identifier == "code" else ["code"],
                }
            )
        change = {
            "operation": "create",
            "id": "new",
            "value": {
                "name": "Remote coding artifact",
                "goal": "Produce effect.txt with exact bytes 42",
                "steps": steps,
                "start_at": time(),
                "interval_seconds": None,
                "max_runs": 1,
                "priority": 0,
                "conditions": [],
            },
        }
        review = self.owner.request("assistance_challenge", change)
        self.assertFalse((self.workspace / "effect.txt").exists())
        self.owner.request(
            "assistance_complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": signature(self.owner_key, base64.b64decode(review["signing_payload"])),
            },
        )
        store = self.core.harness.store
        goal = store.all("executive_goal")[-1]["id"]
        deadline = time() + 12
        while time() < deadline and store.get("executive_goal", goal)["state"] != "completed":
            self.worker.step()
            sleep(0.02)
        self.assertEqual("completed", store.get("executive_goal", goal)["state"])
        tasks = self.core.harness.executive._tasks(goal)
        self.assertEqual(["verified", "verified"], [store.task(t).state for t in tasks])
        self.assertEqual("42", (self.workspace / "effect.txt").read_text())

    def test_phone_objective_model_creates_remote_coding_worker_and_verifies_artifact(self):
        self.remote_model_workflow()

    def test_delegated_phone_objective_autonomously_creates_remote_coding_worker(self):
        self.remote_model_workflow(full=True)

    def test_phone_model_delegates_general_terminal_work_and_verifies_result(self):
        self.remote_model_workflow(terminal=True)

    def test_full_phone_model_autonomously_delegates_general_terminal_work(self):
        self.remote_model_workflow(full=True, terminal=True)

    def test_phone_observes_remote_file_then_privately_replans_and_verifies_effect(self):
        self.remote_model_workflow(terminal=True, adaptive=True)

    def test_full_phone_observation_privately_replans_without_per_action_prompts(self):
        self.remote_model_workflow(full=True, terminal=True, adaptive=True)

    def remote_model_workflow(self, full=False, terminal=False, adaptive=False):
        import json
        import shutil
        from dataclasses import asdict, replace
        from unittest.mock import patch

        from oscar.credentials import CredentialPool
        from oscar.harness import ModelExecutor
        from oscar.jev import Intent
        from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
        from oscar.providers import HTTPAdapter
        from oscar.registry import Registry
        from oscar.router import Router
        from tests.test_providers import ProviderContractTests

        fixture = ProviderContractTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        h = self.core.harness
        provider = replace(fixture.provider, credential_envs={"synthetic": "SYNTHETIC_PLANNER"})
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
        pool = CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic-key"}, h.store)
        h.dispatcher.executors["models.reason"] = ModelExecutor(
            Router(Registry([provider], [model]), pool, {"openai": HTTPAdapter("openai")}, h.store),
            ModelRequest("template", "template", "", max_output_tokens=2048),
            RoutingPolicy(),
            grid=h.grid,
        )
        original = shutil.which
        with patch(
            "oscar.machine.shutil.which",
            side_effect=lambda name: sys.executable if name == "codex" else original(name),
        ):
            self.start_worker(
                ("machine.command" if terminal else "machine.agent.codex", "machine.files.read")
            )
        parameters = self.artifact_parameters()
        if not terminal:
            parameters["arguments"] = parameters.pop("argv")[1:]
        fixture.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    "id": "code",
                    "node_id": "test-machine",
                    "capability_id": "machine.command" if terminal else "machine.agent.codex",
                    "depends_on": [],
                    "intent": asdict(
                        Intent(
                            "Implement exact requested artifact",
                            "capability",
                            capability_kind="terminal_command" if terminal else "coding",
                            parameters=parameters,
                            criterion={"kind": "file_exact", "path": "effect.txt", "content": "42"},
                        )
                    ),
                }
            ]
        )
        if adaptive:
            from copy import deepcopy

            (self.workspace / "input.txt").write_text("41", encoding="utf-8")
            final_body = deepcopy(fixture.body)
            fixture.body["choices"][0]["message"]["content"] = json.dumps(
                {
                    "observe": True,
                    "steps": [
                        {
                            "id": "read",
                            "node_id": "test-machine",
                            "capability_id": "machine.files.read",
                            "depends_on": [],
                            "intent": asdict(
                                Intent(
                                    "Read input",
                                    "capability",
                                    capability_kind="file_read",
                                    parameters={"path": "input.txt"},
                                )
                            ),
                        }
                    ],
                }
            )
            fixture.scheduled = [(200, deepcopy(fixture.body)), (200, final_body)]

        def ask(text):
            return self.owner.request(
                "submit",
                {
                    "text": text,
                    "kind": "text",
                    "target": h.node_id,
                    "parameters": {},
                    "retain": True,
                },
            )

        def approve(change):
            review = self.owner.request("assistance_challenge", change)
            self.owner.request(
                "assistance_complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": signature(
                        self.owner_key, base64.b64decode(review["signing_payload"])
                    ),
                },
            )

        if full:
            self.activate_artifact_delegation(coding=not terminal, planner=True)
        proposed = ask(
            "Create worker Remote code: On device test-machine: "
            'Implement effect.txt containing "42"'
        )
        if full:
            self.assertEqual("full", proposed["assistance_started"]["mode"])
        else:
            self.assertEqual([], fixture.requests)
            approve(proposed["assistance_proposal"])
        deadline = time() + 8

        def planner_ready():
            rows = h.store.all("planner_request")
            tasks = h.executive._tasks(rows[0]["goal_id"]) if rows else []
            return bool(tasks) and h.store.task(tasks[-1]).state in {
                "verified",
                "partially_verified",
            }

        while time() < deadline and (not fixture.requests or adaptive and not planner_ready()):
            if not full and not adaptive:
                h.executive.tick()
            sleep(0.02)
        self.assertEqual(1, len(fixture.requests))
        if not full:
            self.assertFalse((self.workspace / "effect.txt").exists())
            approve(ask("Proceed with the plan")["assistance_proposal"])
        if adaptive:
            deadline = time() + 12
            while time() < deadline:
                self.worker.step()
                row = h.store.all("planner_request")[0]
                observed = row.get("observation_goal")
                if observed and h.store.get("executive_goal", observed)["state"] == "completed":
                    break
                sleep(0.02)
            self.assertTrue(observed)
            self.assertEqual("completed", h.store.get("executive_goal", observed)["state"])
            if not full:
                self.assertEqual(1, len(fixture.requests))
                approve(ask("Proceed with the plan")["assistance_proposal"])
            deadline = time() + 8
            while time() < deadline and (len(fixture.requests) < 2 or not planner_ready()):
                sleep(0.02)
            self.assertEqual(2, len(fixture.requests))
            prompt = json.dumps(fixture.requests[-1]["body"])
            self.assertIn("Untrusted tool observations", prompt)
            self.assertIn("41", prompt)
            self.assertIn("evidence_id", prompt)
            if not full:
                self.assertFalse((self.workspace / "effect.txt").exists())
                approve(ask("Proceed with the plan")["assistance_proposal"])
        deadline = time() + 12
        goal = None
        while time() < deadline:
            self.worker.step()
            goal = h.store.all("planner_request")[0].get("accepted_goal")
            if goal and h.store.get("executive_goal", goal)["state"] == "completed":
                break
            sleep(0.02)
        self.assertIsNotNone(goal)
        self.assertEqual("completed", h.store.get("executive_goal", goal)["state"])
        self.assertEqual("42", (self.workspace / "effect.txt").read_text())
        tasks = h.executive._tasks(goal)
        self.assertEqual(["verified"], [h.store.task(t).state for t in tasks])
        self.assertEqual(
            2 if adaptive else 1,
            self.worker.journal.execute("SELECT count(*) FROM execution_claim").fetchone()[0],
        )

    def test_unenrolled_executable_and_local_policy_cannot_be_borrowed(self):
        self.start_worker(("machine.command",))
        task = self.submit("terminal_command", {"argv": ["C:/not-enabled/program.exe"]})
        self.approve(task)
        self.assertEqual("failed", self.finish(task)["state"])
        self.worker.local_authorize = lambda action: False
        task = self.submit(
            "terminal_command", {"argv": [str(Path(sys.executable).resolve()), "--version"]}
        )
        self.approve(task)
        with self.assertRaises(PermissionError):
            deadline = time() + 5
            while time() < deadline:
                if self.worker.step():
                    self.fail("local deny executed")
                sleep(0.02)

    def test_cancellation_stops_actual_process_before_later_effect(self):
        from threading import Thread

        self.start_worker(("machine.command",))
        task = self.submit(
            "terminal_command",
            {
                "argv": [
                    str(Path(sys.executable).resolve()),
                    "-I",
                    "-c",
                    "import time; from pathlib import Path; "
                    "Path('started.txt').write_text('started'); time.sleep(10); "
                    "Path('late.txt').write_text('must not happen')",
                ],
                "timeout": 20,
            },
        )
        errors = []

        def cancel():
            try:
                deadline = time() + 15
                while not (self.workspace / "started.txt").exists() and time() < deadline:
                    sleep(0.02)
                if not (self.workspace / "started.txt").exists():
                    raise AssertionError("native command never started")
                self.owner.request("cancel", {"task_id": task["task_id"]})
            except Exception as error:
                errors.append(error)

        thread = Thread(target=cancel)
        thread.start()
        try:
            self.approve(task)
            deadline = time() + 20
            while time() < deadline:
                try:
                    if self.worker.step():
                        break
                except PermissionError:
                    break
                sleep(0.02)
        finally:
            thread.join(timeout=15)
        self.assertFalse(thread.is_alive())
        self.assertEqual([], errors)
        self.assertFalse((self.workspace / "late.txt").exists())
        self.assertEqual(
            "cancelled", self.owner.request("inspect", {"task_id": task["task_id"]})["state"]
        )

    def test_unknown_journal_claim_is_never_reexecuted(self):
        from oscar.contracts import Action, record
        from oscar.mobile import fingerprint
        from oscar.storage import StateConflict

        self.start_worker(("machine.command",))
        task = self.submit(
            "terminal_command",
            {
                "argv": [
                    str(Path(sys.executable).resolve()),
                    "-I",
                    "-c",
                    "from pathlib import Path; Path('ambiguous.txt').write_text('unsafe replay')",
                ]
            },
        )
        self.approve(task)
        deadline, delivery = time() + 5, None
        while delivery is None and time() < deadline:
            delivery = self.desktop.request("poll", {})["delivery"]
            sleep(0.02)
        self.assertIsNotNone(delivery)
        action = Action(**delivery["action"])
        self.worker.journal.execute(
            "INSERT INTO execution_claim(action_id,fingerprint) VALUES (?,?)",
            (action.id, fingerprint(record(action))),
        )
        for _ in range(2):
            with self.assertRaises(StateConflict):
                self.worker.execute(delivery)
        self.assertFalse((self.workspace / "ambiguous.txt").exists())

    @unittest.skipUnless(os.name == "nt", "actual Windows owned app fixture")
    def test_actual_windows_form_over_remote_grid(self):
        import subprocess

        from oscar.windows_desktop import InstalledApp, WindowsDesktop

        shell = str(
            Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        fixture = Path(__file__).with_name("fixtures") / "windows_form.ps1"
        process = subprocess.Popen(
            [shell, "-NoProfile", "-STA", "-File", str(fixture), "-Root", str(self.workspace)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            deadline = time() + 20
            while not (self.workspace / "window.txt").exists() and time() < deadline:
                if process.poll() is not None:
                    self.fail(f"synthetic app exited: {process.communicate()[1]!r}")
                sleep(0.1)
            handle = int((self.workspace / "window.txt").read_text())
            self.assertEqual("False", (self.workspace / "keyboard-focus.txt").read_text())
            self.start_worker(("machine.desktop",), desktop=True)
            app = InstalledApp(
                "synthetic-form",
                "Synthetic form",
                None,
                shell,
                "native_exe",
                "run-owned-fixture",
                time(),
                True,
                ("observe_window",),
            )
            self.worker.effects.desktop = WindowsDesktop(
                permissions=self.worker.effects.remote_grants,
                allowed_apps=(app,),
                workspace=self.workspace,
            )
            desktop = self.worker.effects.desktop
            desktop.bind(handle, process.pid, app.id)
            target = {"handle": handle, "pid": process.pid}
            tree = desktop.observe({"operation": "tree", **target})
            editor = next(e for e in tree if e["name"] == "Synthetic input")
            button = next(e for e in tree if e["name"] == "Submit synthetic form")
            text = "Remote Grid native UIA proof"
            task = self.submit(
                "desktop_control",
                {
                    "request": {
                        "operation": "set_text_checked",
                        **target,
                        "runtime_id": editor["runtime_id"],
                        "text": text,
                        "expected_text": "",
                    }
                },
            )
            self.approve(task)
            self.assertEqual("verified", self.finish(task)["state"])
            self.assertEqual(
                text,
                desktop.observe(
                    {"operation": "read", **target, "runtime_id": editor["runtime_id"]}
                )["text"],
            )
            task = self.submit(
                "desktop_control",
                {
                    "request": {
                        "operation": "invoke",
                        **target,
                        "runtime_id": button["runtime_id"],
                    }
                },
            )
            self.approve(task)
            self.assertEqual("partially_verified", self.finish(task)["state"])
            deadline = time() + 5
            while not (self.workspace / "submitted.txt").exists() and time() < deadline:
                sleep(0.05)
            self.assertEqual(text, (self.workspace / "submitted.txt").read_text())
            with self.assertRaises(PermissionError):
                desktop.observe({"operation": "tree", **target, "pid": process.pid + 1})
            desktop.observe({"operation": "close", **target})
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            if process.stderr:
                process.stderr.close()

    @unittest.skipUnless(importlib.util.find_spec("playwright"), "optional installed Chromium")
    def test_revoked_browser_account_cannot_reopen_private_profile(self):
        self.start_worker(("machine.browser",), browser=True, profiles=True)
        account = self.core.harness.accounts.add(
            "fixture", "synthetic", "subject", "Synthetic", verified=True
        )
        task = self.submit(
            "browser",
            {
                "account_id": account.id,
                "account_generation": account.generation,
                "request": {
                    "origins": ["http://127.0.0.1:8765"],
                    "steps": [{"operation": "navigate", "url": "http://127.0.0.1:8765/"}],
                    "timeout": 5,
                    "max_text": 100,
                },
            },
        )
        self.approve(task)
        deadline, delivery = time() + 5, None
        while delivery is None and time() < deadline:
            delivery = self.desktop.request("poll", {})["delivery"]
            sleep(0.02)
        self.assertIsNotNone(delivery)
        self.core.harness.accounts.disconnect(account.id)
        with self.assertRaises(PermissionError):
            self.worker.execute(delivery)
        self.assertFalse((self.root / "private-profiles").exists())

    @unittest.skipUnless(importlib.util.find_spec("playwright"), "optional installed Chromium")
    def test_actual_browser_form_and_artifact_over_remote_grid(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        observed, cookies = [], []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                cookies.append(self.headers.get("Cookie", ""))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b'<html><body><form method="post"><input id="message" name="message">'
                    b'<button id="submit">Save synthetic form</button></form></body></html>'
                )

            def do_POST(self):
                observed.append(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(200)
                self.send_header(
                    "Set-Cookie",
                    "synthetic=remote-profile; Max-Age=3600; HttpOnly; SameSite=Strict",
                )
                self.end_headers()
                self.wfile.write(b"<html><body>Saved synthetic form</body></html>")

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        Thread(target=server.serve_forever, daemon=True).start()
        self.start_worker(("machine.browser",), browser=True, profiles=True)
        account = self.core.harness.accounts.add(
            "fixture", "synthetic", "browser-subject", "Synthetic", verified=True
        )
        origin = "http://127.0.0.1:" + str(server.server_port)
        task = self.submit(
            "browser",
            {
                "account_id": account.id,
                "account_generation": account.generation,
                "request": {
                    "origins": [origin],
                    "steps": [
                        {"operation": "navigate", "url": origin + "/"},
                        {
                            "operation": "fill",
                            "selector": "#message",
                            "text": "remote synthetic proof",
                        },
                        {"operation": "submit", "selector": "#submit"},
                        {"operation": "screenshot", "path": "proof.png"},
                    ],
                    "timeout": 30,
                    "max_text": 1000,
                },
            },
        )
        self.assertEqual([], observed)
        self.approve(task)
        self.assertEqual("partially_verified", self.finish(task)["state"])
        self.assertEqual([b"message=remote+synthetic+proof"], observed)
        self.assertTrue((self.workspace / "proof.png").read_bytes().startswith(b"\x89PNG"))
        task = self.submit(
            "browser",
            {
                "account_id": account.id,
                "account_generation": account.generation,
                "request": {
                    "origins": [origin],
                    "steps": [{"operation": "navigate", "url": origin + "/"}],
                    "timeout": 15,
                    "max_text": 1000,
                },
            },
        )
        self.approve(task)
        self.assertEqual("partially_verified", self.finish(task)["state"])
        self.assertIn("synthetic=remote-profile", cookies)
        self.assertTrue(any((self.root / "private-profiles").iterdir()))
        self.assertFalse(any("Cookies" in str(p) for p in self.workspace.rglob("*")))


if __name__ == "__main__":
    unittest.main()
