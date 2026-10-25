"""Only a bound run-owned window reaches private control planning."""

import base64
import json
import os
import subprocess
import unittest
from dataclasses import replace
from pathlib import Path
from time import monotonic, sleep, time
from unittest.mock import patch

from oscar.credentials import CredentialPool
from oscar.harness import ModelExecutor
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_observations import validate_stage
from oscar.policy import PersonalPolicy
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.remote_machine import machine_readback
from oscar.router import Router
from oscar.windows_desktop import InstalledApp, WindowsDesktop
from tests import test_providers as provider_fixture
from tests import test_remote_machine as fixture
from tests.test_directory_observations import step
from tests.test_remote_grid import signature


class ControlObservationContractTests(unittest.TestCase):
    def test_exact_read_query_excludes_unbound_identity_and_effects(self):
        request = {"operation": "inspect_controls", "handle": 1, "pid": 2, "query": "Input"}
        value = step("machine.controls", "desktop_inspection", request=request)
        validate_stage([value])
        self.assertEqual(
            {"request": request}, machine_readback("machine.controls", {"request": request})
        )
        for invalid in (
            {"operation": "invoke"},
            {"handle": True},
            {"pid": 0},
            {"query": "x" * 81},
            {"runtime_id": "invented"},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_stage(
                    [step("machine.controls", "desktop_inspection", request={**request, **invalid})]
                )

    def test_projection_excludes_password_values_and_qualifies_limits(self):
        adapter = object.__new__(WindowsDesktop)
        adapter.permissions = frozenset({"desktop:capture", "screen:retain"})
        element = {
            "runtime_id": "1.2",
            "name": "Field",
            "type": "ControlType.Edit",
            "enabled": True,
            "offscreen": False,
            "password": True,
            "text": "SECRET",
        }
        request = {"operation": "inspect_controls", "handle": 1, "pid": 2, "query": ""}
        with patch.object(adapter, "observe", return_value=[element] * 12):
            result = adapter.inspect_controls(request)
            self.assertTrue(result["truncated"])
            self.assertEqual(8, len(result["controls"]))
            self.assertNotIn("SECRET", json.dumps(result))
            self.assertIn("bounded", result["coverage"])
            adapter.permissions = frozenset({"desktop:capture"})
            with self.assertRaises(PermissionError):
                adapter.inspect_controls(request)


@unittest.skipUnless(os.name == "nt", "selected synthetic Windows control acceptance")
class ControlObservationTests(unittest.TestCase):
    enroll = fixture.RemoteMachineExecutionTests.enroll
    start_worker = fixture.RemoteMachineExecutionTests.start_worker

    def setUp(self):
        create = fixture.create_invitation
        with patch.object(
            fixture,
            "create_invitation",
            side_effect=lambda *a, **kw: create(*a, **kw, screen_capture=True, screen_retain=True),
        ):
            fixture.RemoteMachineExecutionTests.setUp(self)

    def test_full_private_control_observation_and_independently_verified_edit(self):
        self.workflow()

    def test_retention_withdrawal_before_continuation_stops_disclosure_and_edit(self):
        self.workflow(withdraw=True)

    def workflow(self, withdraw=False):
        shell = str(
            Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        form = Path(__file__).with_name("fixtures") / "windows_form.ps1"
        process = subprocess.Popen(
            [shell, "-NoProfile", "-STA", "-File", str(form), "-Root", str(self.root)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        def stop():
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)

        self.addCleanup(stop)
        deadline = monotonic() + 15
        while not (self.root / "window.txt").exists() and monotonic() < deadline:
            sleep(0.05)
        self.assertTrue((self.root / "window.txt").exists())
        handle = int((self.root / "window.txt").read_text())
        caps = ("machine.controls", "machine.desktop")
        self.start_worker(caps, desktop=True)
        app = InstalledApp(
            "run-owned-form",
            "Synthetic form",
            None,
            shell,
            "native_exe",
            "run-owned-fixture",
            time(),
            True,
            ("observe_window",),
        )
        adapter = WindowsDesktop(
            permissions=self.worker.effects.remote_grants,
            allowed_apps=(app,),
            workspace=self.workspace,
        )
        self.worker.effects.desktop = adapter
        request = {
            "operation": "inspect_controls",
            "handle": handle,
            "pid": process.pid,
            "query": "Synthetic input",
        }
        with self.assertRaises(PermissionError):
            adapter.inspect_controls(request)
        adapter.bind(handle, process.pid, app.id)
        editor = adapter.inspect_controls(request)["controls"][0]
        p = provider_fixture.ProviderContractTests()
        p.setUp()
        self.addCleanup(p.doCleanups)
        h = self.core.harness
        provider = replace(p.provider, credential_envs={"synthetic": "SYNTHETIC_PLANNER"})
        model = ModelSpec(
            "fixture",
            "fixture-model",
            frozenset({"text"}),
            2,
            {"reasoning": 1},
            8192,
            4096,
            Funding.FREE,
            provenance="synthetic HTTP",
        )
        http = HTTPAdapter("openai")
        generate = http.generate
        calls = []

        def guarded_generate(*args, **kwargs):
            if calls and withdraw:
                owner = h.store.get("session", self.owner.handle.id)
                h.store.put(
                    "session",
                    owner["id"],
                    {**owner, "scopes": [v for v in owner["scopes"] if v != "screen:retain"]},
                )
            calls.append(True)
            return generate(*args, **kwargs)

        http.generate = guarded_generate
        h.dispatcher.executors["models.reason"] = ModelExecutor(
            Router(
                Registry([provider], [model]),
                CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic"}, h.store),
                {"openai": http},
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
                    {"node_id": s.node_id, "session_id": s.id, "capability_id": c}
                    for s, c in [
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
        observe = step("machine.controls", "desktop_inspection", request=request)
        final = step(
            "machine.desktop",
            "desktop_control",
            request={
                "operation": "set_text_checked",
                "handle": handle,
                "pid": process.pid,
                "runtime_id": editor["runtime_id"],
                "text": "SCOPED-731",
                "expected_text": "",
            },
        )
        p.scheduled = [
            (200, {**p.body, "choices": [{"message": {"content": json.dumps(v)}}]})
            for v in ({"steps": [observe], "observe": True}, {"steps": [final]})
        ]
        started = self.owner.request(
            "submit",
            {
                "text": "Create worker Edit: On device test-machine: "
                "First inspect Synthetic input "
                f"in the selected bound window handle {handle} pid {process.pid}, "
                "then replace its current empty text with SCOPED-731",
                "kind": "text",
                "target": h.node_id,
                "parameters": {},
                "retain": True,
            },
        )
        self.assertIn("assistance_started", started)
        self.assertEqual("full", started["assistance_started"]["mode"])
        deadline = monotonic() + 30
        while monotonic() < deadline:
            self.worker.step()
            row = h.store.all("planner_request")[0]
            if withdraw and any(t["state"] == "failed" for t in h.store.all("task")):
                break
            if (
                row.get("accepted_goal")
                and h.store.get("executive_goal", row["accepted_goal"])["state"] == "completed"
            ):
                break
            sleep(0.02)
        else:
            self.fail("selected-window observation/edit did not complete")
        if withdraw:
            self.assertEqual(2, len(calls))
            self.assertEqual(1, len(p.requests))
            self.assertEqual(
                "",
                adapter.observe(
                    {
                        "operation": "read",
                        "handle": handle,
                        "pid": process.pid,
                        "runtime_id": editor["runtime_id"],
                    }
                )["text"],
            )
            self.assertFalse(
                any(a["capability_id"] == "machine.desktop" for a in h.store.all("planned_action"))
            )
            return
        self.assertIn(editor["runtime_id"], json.dumps(p.requests[1]["body"]))
        self.assertIn("Synthetic input", json.dumps(p.requests[1]["body"]))
        current = adapter.observe(
            {
                "operation": "read",
                "handle": handle,
                "pid": process.pid,
                "runtime_id": editor["runtime_id"],
            }
        )
        self.assertEqual("SCOPED-731", current["text"])
        self.assertEqual("False", (self.root / "keyboard-focus.txt").read_text())
        self.assertEqual("private", h.store.all("route_history")[-1]["mode"])
