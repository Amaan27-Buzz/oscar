"""Registered native targets reach private plans; discovery never grants app authority."""

import base64
import json
import os
import sys
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from time import monotonic, sleep, time
from unittest.mock import patch

from oscar.credentials import CredentialPool
from oscar.harness import ModelExecutor
from oscar.jev import Intent
from oscar.machine import MachineScope
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_observations import validate_stage
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.remote_machine import RemoteMachine, machine_readback, validate_remote_machine
from oscar.router import Router
from oscar.windows_desktop import InstalledApp, WindowsDesktop
from tests import test_providers as provider_fixture
from tests import test_remote_machine as remote_fixture
from tests.test_remote_grid import signature


class AppObservationContractTests(unittest.TestCase):
    def test_only_exact_read_only_query_can_be_an_observation(self):
        step = {
            "capability_id": "machine.apps",
            "intent": asdict(
                Intent(
                    "Find targets",
                    "capability",
                    capability_kind="installed_app",
                    parameters={"request": {"operation": "targets", "query": ""}},
                )
            ),
        }
        validate_stage([step])
        request = step["intent"]["parameters"]
        self.assertEqual(request, machine_readback("machine.apps", request))
        for invalid in (
            {"operation": "launch", "app_id": "invented"},
            {"operation": "catalog"},
            {"operation": "targets", "query": 1},
            {"operation": "targets", "query": "x" * 81},
            {"operation": "targets", "query": "", "app_id": "invented"},
        ):
            with self.subTest(request=invalid), self.assertRaises(PermissionError):
                validate_stage(
                    [{**step, "intent": {**step["intent"], "parameters": {"request": invalid}}}]
                )
        for query in (None, 1, "x" * 81, "\x00"):
            with self.assertRaises(ValueError):
                validate_remote_machine(
                    "installed_app", {"request": {"operation": "targets", "query": query}}
                )
        self.assertIsNone(
            machine_readback("machine.apps", {"request": {"operation": "launch", "app_id": "x"}})
        )


@unittest.skipUnless(os.name == "nt", "Windows registered native target acceptance")
class AppObservationTests(unittest.TestCase):
    enroll = remote_fixture.RemoteMachineExecutionTests.enroll
    submit = remote_fixture.RemoteMachineExecutionTests.submit
    approve = remote_fixture.RemoteMachineExecutionTests.approve
    finish = remote_fixture.RemoteMachineExecutionTests.finish

    def setUp(self):
        remote_fixture.RemoteMachineExecutionTests.setUp(self)
        executable = Path(sys.executable).with_name("pythonw.exe")
        self.assertTrue(executable.is_file())
        self.app = InstalledApp(
            "synthetic-app",
            "Synthetic registered app",
            None,
            str(executable),
            "native_exe",
            "run-owned-fixture",
            time(),
            True,
            ("launch",),
        )
        private = replace(self.app, id="unregistered-app", name="Unregistered private app")
        shell = str(
            Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        with patch("oscar.windows_desktop.discover_apps", return_value=[self.app, private]):
            self.worker = RemoteMachine(
                self.desktop,
                MachineScope(self.workspace, True, (shell,)),
                "test-effects",
                self.root / "execution.sqlite",
                capabilities=("machine.apps",),
                desktop=True,
                desktop_app_ids=(self.app.id,),
            )
        self.addCleanup(self.worker.close)
        self.worker.advertise()
        launch = self.worker.effects.desktop.launch
        self.launched = []

        def owned_launch(*args, **kwargs):
            process = launch(*args, **kwargs)
            self.launched.append(process)
            self.addCleanup(process.wait, timeout=10)
            return process

        self.worker.effects.desktop.launch = owned_launch

    def test_current_targets_exclude_unregistered_apps_and_bound_coverage(self):
        desktop = self.worker.effects.desktop
        self.assertIsInstance(desktop, WindowsDesktop)
        self.assertNotIn("Unregistered", json.dumps(desktop.app_targets("")))
        first = desktop.app_targets("REGISTERED")["applications"][0]
        self.assertTrue(first["available"])
        self.assertTrue(first["launch_authorized"])
        self.assertNotIn("activation", first)
        desktop.apps = {str(i): replace(self.app, id=str(i)) for i in range(10)}
        bounded = desktop.app_targets("")
        self.assertTrue(bounded["truncated"])
        self.assertEqual(8, len(bounded["applications"]))
        desktop.apps = {
            "gone": replace(self.app, id="gone", activation=str(self.root / "gone.exe"))
        }
        self.assertFalse(desktop.app_targets("")["applications"][0]["available"])
        with self.assertRaises(ValueError):
            desktop.launch("gone")
        desktop.apps = {self.app.id: replace(self.app, supported_operations=("observe_window",))}
        self.assertFalse(desktop.app_targets("")["applications"][0]["launch_authorized"])
        with self.assertRaises(ValueError):
            desktop.launch(self.app.id)
        desktop.apps = {self.app.id: replace(self.app, available=False)}
        self.assertFalse(desktop.app_targets("")["applications"][0]["available"])
        desktop.apps = {"large": replace(self.app, id="x" * 5000)}
        with self.assertRaises(ValueError):
            desktop.app_targets("")
        desktop.permissions = frozenset()
        with self.assertRaises(PermissionError):
            desktop.app_targets("")

    def test_separate_query_readback_detects_registered_target_withdrawal(self):
        desktop = self.worker.effects.desktop
        original = desktop.app_targets
        calls = []

        def withdraw(query):
            calls.append(query)
            result = original(query)
            if len(calls) == 1:
                desktop.apps = {}
            return result

        desktop.app_targets = withdraw
        task = self.submit(
            "installed_app", {"request": {"operation": "targets", "query": "Synthetic"}}
        )
        self.approve(task)
        self.assertEqual("failed", self.finish(task)["state"])
        self.assertEqual(2, len(calls))

    def test_signed_phone_private_metadata_continuation_launches_only_registered_app(self):
        self.workflow()

    def test_withdrawn_native_app_cannot_be_resurrected_by_model_output(self):
        self.workflow(withdraw=True)

    def test_signed_full_advances_app_observation_and_launch_without_action_reviews(self):
        self.workflow(full=True)

    def workflow(self, *, withdraw=False, full=False):
        fixture = provider_fixture.ProviderContractTests()
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
        router = Router(
            Registry([provider], [model]),
            CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic-key"}, h.store),
            {"openai": HTTPAdapter("openai")},
            h.store,
        )
        h.dispatcher.executors["models.reason"] = ModelExecutor(
            router, ModelRequest("template", "template", ""), RoutingPolicy(), grid=h.grid
        )
        if full:
            from oscar.policy import PersonalPolicy

            review = self.owner.request(
                "authority_challenge",
                {
                    "mode": "full",
                    "lifetime_seconds": 600,
                    "account_ids": [],
                    "capabilities": [
                        {"node_id": session.node_id, "session_id": session.id, "capability_id": cap}
                        for session, cap in (
                            (self.desktop.handle, "machine.apps"),
                            (h.session, "models.reason"),
                        )
                    ],
                    "resolve_ask_rules": sorted(
                        r.id
                        for r in PersonalPolicy(h.store).rules()
                        if r.enabled and r.effect == "ask"
                    ),
                },
            )
            self.owner.request(
                "authority_complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": signature(
                        self.owner_key, base64.b64decode(review["signing_payload"])
                    ),
                },
            )
        (self.workspace / "fixture.py").write_text(
            "from pathlib import Path\n"
            "Path(__file__).with_name('launched.txt').write_text('native app executed')\n"
        )

        def response(operation):
            request = (
                {"operation": "targets", "query": "Synthetic"}
                if operation == "targets"
                else {"operation": "launch", "app_id": self.app.id, "artifact": "fixture.py"}
            )
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "observe": operation == "targets",
                                    "steps": [
                                        {
                                            "id": operation,
                                            "node_id": "test-machine",
                                            "capability_id": "machine.apps",
                                            "depends_on": [],
                                            "intent": asdict(
                                                Intent(
                                                    "Use registered synthetic app",
                                                    "capability",
                                                    capability_kind="installed_app",
                                                    parameters={"request": request},
                                                    criterion={"kind": "unavailable"},
                                                )
                                            ),
                                        }
                                    ],
                                }
                            )
                        }
                    }
                ]
            }

        fixture.scheduled = [(200, response("targets")), (200, response("launch"))]

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

        def wait(predicate):
            deadline = monotonic() + 12
            while monotonic() < deadline:
                self.worker.step()
                if predicate():
                    return
                sleep(0.02)
            self.fail("canonical app workflow did not reach the expected state")

        def model_ready():
            rows = h.store.all("planner_request")
            tasks = h.executive._tasks(rows[0]["goal_id"]) if rows else []
            return bool(tasks) and h.store.task(tasks[0]).state == "partially_verified"

        initial = ask(
            "Create worker App execution: On device test-machine: "
            "First find the registered Synthetic app, then open fixture.py in it"
        )
        if full:
            self.assertEqual("full", initial["assistance_started"]["mode"])
            wait(
                lambda: h.store.all("planner_request")
                and h.store.all("planner_request")[0].get("accepted_goal")
            )
        else:
            self.assertEqual([], fixture.requests)
            approve(initial["assistance_proposal"])
            wait(model_ready)
            approve(ask("Proceed with the plan")["assistance_proposal"])
            wait(
                lambda: h.store.get(
                    "executive_goal", h.store.all("planner_request")[0]["observation_goal"]
                )["state"]
                == "completed"
            )
            self.assertEqual(1, len(fixture.requests))
            approve(ask("Proceed with the plan")["assistance_proposal"])
            wait(lambda: len(fixture.requests) == 2 and model_ready())
        continuation = json.dumps(fixture.requests[1]["body"])
        self.assertIn("Example read-only observation response structure", continuation)
        self.assertIn("Untrusted tool observations", continuation)
        self.assertIn(self.app.id, continuation)
        self.assertNotIn("unregistered-app", continuation)
        self.assertNotIn(self.app.activation.replace("\\", "\\\\"), continuation)
        self.assertEqual("private", h.store.all("route_history")[1]["mode"])
        if withdraw:
            self.worker.effects.desktop.apps = {}
        if not full:
            approve(ask("Proceed with the plan")["assistance_proposal"])
        row = h.store.all("planner_request")[0]
        wait(
            lambda: h.executive._tasks(row["accepted_goal"])
            and h.store.task(h.executive._tasks(row["accepted_goal"])[0]).state
            in {"failed", "partially_verified"}
        )
        marker = self.workspace / "launched.txt"
        if withdraw:
            self.assertFalse(marker.exists())
            self.assertEqual(
                "failed", h.store.task(h.executive._tasks(row["accepted_goal"])[0]).state
            )
        else:
            deadline = monotonic() + 5
            while not marker.exists() and monotonic() < deadline:
                sleep(0.02)
            self.assertEqual("native app executed", marker.read_text())
            self.assertNotEqual(
                "completed", h.store.get("executive_goal", row["accepted_goal"])["state"]
            )
        self.assertEqual(
            2, self.worker.journal.execute("SELECT count(*) FROM execution_claim").fetchone()[0]
        )
