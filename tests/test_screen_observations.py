"""Private image readback and actual run-owned native visual input."""

import base64
import hashlib
import json
import os
import struct
import subprocess
import unittest
import zlib
from dataclasses import replace
from pathlib import Path
from time import monotonic, sleep, time
from types import SimpleNamespace
from unittest.mock import Mock

from oscar.contracts import ArtifactRef, Objective, Result
from oscar.credentials import CredentialPool
from oscar.harness import ModelExecutor
from oscar.models import Funding, Mode, ModelRequest, ModelSpec, ProviderError, RoutingPolicy
from oscar.planner_observations import validate_stage
from oscar.policy import PersonalPolicy
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.remote_grid import RemoteVerifier
from oscar.remote_machine import RemoteMachine
from oscar.router import Router
from oscar.screen_image import CHUNK_BYTES, ScreenImage
from oscar.windows_desktop import InstalledApp, WindowsDesktop
from tests import test_control_observations as control_fixture
from tests import test_providers as provider_fixture
from tests.support import RouterRig
from tests.test_directory_observations import step
from tests.test_remote_grid import signature


def png(width=64, height=48):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    # Incompressible synthetic pixels exercise more than one authenticated transport chunk.
    raw = b"".join(b"\0" + os.urandom(width * 4) for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


class ScreenObservationContractTests(unittest.TestCase):
    def test_capture_validation_preserves_existing_native_geometry_limit(self):
        width, height = 4096, 2160

        def chunk(kind, data):
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data))
            )

        data = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" * (width * 3 + 1)) * height))
            + chunk(b"IEND", b"")
        )
        image = ScreenImage(data, width, height, hashlib.sha256(data).hexdigest())
        self.assertEqual((width, height), (image.width, image.height))
        with self.assertRaises(ValueError):
            ScreenImage(data, width, height + 1, image.sha256)

    def test_private_image_generate_wire_and_strict_structured_output(self):
        fixture = provider_fixture.ProviderContractTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        data = png()
        image = ScreenImage(data, 64, 48, hashlib.sha256(data).hexdigest())
        request = replace(
            fixture.request,
            mode=Mode.PRIVATE,
            images=(image,),
            required=frozenset({"text", "structured", "vision"}),
            ollama_think=False,
        )
        fixture.body = {
            "response": '{"x":12,"y":24}',
            "done": True,
            "prompt_eval_count": 24,
            "eval_count": 10,
        }
        result = fixture.generate("ollama", request=request)
        self.assertTrue(result.structured_ok)
        self.assertEqual(24, result.input_tokens)
        self.assertEqual("/generate", fixture.requests[0]["path"])
        body = fixture.requests[0]["body"]
        self.assertNotIn("messages", body)
        self.assertEqual(request.prompt, body["prompt"])
        self.assertEqual(data, base64.b64decode(body["images"][0]))
        fixture.body["response"] = '```json\n{"x":12,"y":24}\n```'
        with self.assertRaises(ProviderError):
            fixture.generate("ollama", request=request)

    def test_vision_routes_require_local_ollama_local_funding_and_capability(self):
        rig = RouterRig()
        self.addCleanup(rig.close)
        data = png()
        image = ScreenImage(data, 64, 48, hashlib.sha256(data).hexdigest())
        request = replace(
            rig.request, mode=Mode.PRIVATE, images=(image,), required=frozenset({"text", "vision"})
        )
        provider = replace(
            rig.registry.providers["plentiful"],
            adapter="ollama",
            local=True,
            discovery_required=False,
        )
        model = replace(
            rig.registry.models[("plentiful", "small")],
            capabilities=frozenset({"text", "vision"}),
            funding=Funding.LOCAL,
        )
        rig.registry.providers[provider.id] = provider
        rig.registry.models[(model.provider_id, model.id)] = model
        rig.router.adapters["ollama"] = rig.adapter
        self.assertTrue(rig.router.rank(request))
        for invalid in (
            replace(provider, local=False, private=True),
            replace(provider, adapter="openai"),
        ):
            rig.registry.providers[provider.id] = invalid
            self.assertEqual([], rig.router.rank(request))
            rig.registry.providers[provider.id] = replace(invalid, discovery_required=True)
            rig.router.discovery = Mock()
            rig.router.refresh(request)
            rig.router.discovery.inventory.assert_not_called()
        rig.registry.providers[provider.id] = provider
        for invalid in (
            replace(model, funding=Funding.FREE),
            replace(model, capabilities=frozenset({"text"})),
            replace(model, context_limit=1024),
        ):
            rig.registry.models[(model.provider_id, model.id)] = invalid
            self.assertEqual([], rig.router.rank(request))

    def test_exact_chunk_destination_and_offset_are_enforced(self):
        worker = object.__new__(RemoteMachine)
        action = SimpleNamespace(
            capability_id="machine.screen",
            parameters={
                "request": {"operation": "screenshot", "handle": 1, "pid": 2, "path": "frame.png"}
            },
        )
        delivery = {
            "kind": "readback",
            "approved": True,
            "parameters": {"path": "frame.png", "offset": 0},
        }
        worker.validate_effect(action, delivery)
        for invalid in (
            {"offset": True},
            {"offset": -1},
            {"offset": 1},
            {"offset": 1_002_000},
            {"path": "other.png"},
            {"length": 1},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(PermissionError):
                worker.validate_effect(
                    action, {**delivery, "parameters": {**delivery["parameters"], **invalid}}
                )

    def test_image_cache_binds_metadata_expires_and_clears_at_shutdown(self):
        data = png()
        image = ScreenImage(data, 64, 48, hashlib.sha256(data).hexdigest())
        clock = [10]
        executor = ModelExecutor(
            Mock(),
            ModelRequest("task", "correlation", ""),
            RoutingPolicy(),
            grid=SimpleNamespace(clock=lambda: clock[0]),
        )
        text = json.dumps(
            [
                {
                    "task_id": "capture",
                    "media_type": "image/png",
                    "value": json.dumps(
                        {
                            "width": image.width,
                            "height": image.height,
                            "sha256": image.sha256,
                            "bytes": len(data),
                        }
                    ),
                }
            ]
        )
        executor.retain_image("capture", image)
        self.assertEqual((image,), executor.observation_images(text))
        with self.assertRaises(PermissionError):
            executor.observation_images(text.replace(image.sha256, "0" * 64))
        clock[0] = 131
        with self.assertRaises(PermissionError):
            executor.observation_images(text)
        self.assertEqual({}, executor._images)
        executor.retain_image("capture", image)
        executor.release_images()
        with self.assertRaises(PermissionError):
            executor.observation_images(text)

    def test_png_integrity_geometry_and_private_model_boundary(self):
        data = png()
        image = ScreenImage(data, 64, 48, hashlib.sha256(data).hexdigest())
        request = ModelRequest(
            "task",
            "correlation",
            "Describe",
            mode=Mode.PRIVATE,
            required=frozenset({"text", "vision"}),
            images=(image,),
        )
        self.assertGreaterEqual(request.input_tokens, 64 * 48)
        self.assertNotIn(str(data), repr(request))
        for invalid in (data[:-1], data + b"extra", data[:40] + b"x" + data[41:]):
            with self.subTest(size=len(invalid)), self.assertRaises(ValueError):
                ScreenImage(invalid, 64, 48, hashlib.sha256(invalid).hexdigest())
        with self.assertRaises(ValueError):
            ScreenImage(data, 63, 48, image.sha256)
        with self.assertRaises(ValueError):
            replace(request, mode=Mode.AUTO)
        with self.assertRaises(ValueError):
            replace(request, required=frozenset({"text"}))
        for kind in ("openai", "google", "ollama"):
            with self.subTest(kind=kind), self.assertRaises(ProviderError):
                HTTPAdapter(kind)._request(
                    SimpleNamespace(local=False),
                    "model",
                    "",
                    request,
                    False,
                )

    def test_capture_stage_rejects_aliases_unbound_identity_and_effects(self):
        request = {"operation": "screenshot", "handle": 1, "pid": 2, "path": "frame.png"}
        validate_stage([step("machine.screen", "screen_capture", request=request)])
        for invalid in (
            {"path": "../secret"},
            {"handle": True},
            {"pid": 0},
            {"operation": "visual_click"},
            {"url": "https://example.com"},
        ):
            with self.subTest(invalid=invalid), self.assertRaises((ValueError, PermissionError)):
                validate_stage(
                    [step("machine.screen", "screen_capture", request={**request, **invalid})]
                )

    def test_independent_multichunk_readback_rejects_changed_bytes(self):
        data = png()
        frame = {
            "width": 64,
            "height": 48,
            "sha256": hashlib.sha256(data).hexdigest(),
            "path": "frame.png",
            "bytes": len(data),
        }
        self.assertGreater(len(data), CHUNK_BYTES)
        executor = object.__new__(ModelExecutor)
        executor.retain_image = Mock()
        remote = SimpleNamespace(
            store=SimpleNamespace(
                get=lambda *_: {"parameters": {"request": {"path": "frame.png"}}}
            ),
            h=SimpleNamespace(dispatcher=SimpleNamespace(executors={"models.reason": executor})),
        )
        original = SimpleNamespace(files=None, clock=time)
        verifier = RemoteVerifier(remote, original)
        objective = Objective(
            "objective",
            "task",
            "Capture selected window",
            {"kind": "remote_machine", "image": True},
            time(),
        )
        result = Result(
            "result",
            "action",
            "task",
            "correlation",
            "machine.screen",
            True,
            artifact=ArtifactRef(
                "artifact",
                "task",
                "machine.screen",
                "screenshot",
                "workspace:test",
                time(),
                content_hash=frame["sha256"],
            ),
            value=json.dumps(frame),
        )
        offsets = []

        def exchange(task, kind, *, offset):
            offsets.append(offset)
            return {"content": base64.b64encode(data[offset : offset + CHUNK_BYTES]).decode()}

        remote.exchange = exchange
        verified = verifier.verify(objective, result)
        self.assertEqual("verified", verified.state)
        self.assertEqual(list(range(0, len(data), CHUNK_BYTES)), offsets)
        self.assertEqual(frame["sha256"], verified.evidence.content_hash)
        data = data[:-1] + bytes([data[-1] ^ 1])
        with self.assertRaises(ValueError):
            verifier.verify(objective, result)
        self.assertEqual(1, executor.retain_image.call_count)


@unittest.skipUnless(os.name == "nt", "actual synthetic Windows capture and visual input")
class NativeScreenObservationTests(unittest.TestCase):
    enroll = control_fixture.ControlObservationTests.enroll
    start_worker = control_fixture.ControlObservationTests.start_worker
    setUp = control_fixture.ControlObservationTests.setUp

    def test_private_verified_image_drives_native_click(self):
        self.workflow()

    def test_revoked_retention_stops_image_disclosure_and_click(self):
        self.workflow(withdraw=True)

    def workflow(self, withdraw=False):
        shell = str(
            Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        process = subprocess.Popen(
            [
                shell,
                "-NoProfile",
                "-STA",
                "-File",
                str(Path(__file__).with_name("fixtures") / "windows_visual.ps1"),
                "-Root",
                str(self.workspace),
            ],
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
        while not (self.workspace / "window.txt").exists() and monotonic() < deadline:
            sleep(0.05)
        handle = int((self.workspace / "window.txt").read_text())
        caps = ("machine.screen", "machine.visual")
        self.start_worker(caps, desktop=True)
        native_errors = []
        run_command = self.worker.effects.run_command

        def inspect_command(*args, **kwargs):
            result = run_command(*args, **kwargs)
            if result[0]:
                native_errors.append(result[1])
            return result

        self.worker.effects.run_command = inspect_command
        app = InstalledApp(
            "run-owned-canvas",
            "Synthetic canvas",
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
        adapter.bind(handle, process.pid, app.id)
        tree = adapter.observe({"operation": "tree", "handle": handle, "pid": process.pid})
        adapter.observe(
            {
                "operation": "focus",
                "handle": handle,
                "pid": process.pid,
                "runtime_id": tree[0]["runtime_id"],
            }
        )
        self.worker.effects.desktop = adapter
        marker = self.workspace / "clicks.txt"
        baseline = int(marker.read_text()) if marker.exists() else 0
        p = provider_fixture.ProviderContractTests()
        p.setUp()
        self.addCleanup(p.doCleanups)
        provider = replace(
            p.provider, adapter="ollama", credential_envs={"synthetic": "SYNTHETIC_PLANNER"}
        )
        model = ModelSpec(
            "fixture",
            "fixture-model",
            frozenset({"text", "vision"}),
            2,
            {"reasoning": 1},
            262144,
            4096,
            Funding.LOCAL,
            provenance="synthetic HTTP",
        )
        h = self.core.harness
        observe = step(
            "machine.screen",
            "screen_capture",
            request={
                "operation": "screenshot",
                "handle": handle,
                "pid": process.pid,
                "path": "plan.png",
            },
        )
        http = HTTPAdapter("ollama")
        generate, calls = http.generate, []

        def guarded_generate(provider, model, secret, request, *args, **kwargs):
            if calls and withdraw:
                owner = h.store.get("session", self.owner.handle.id)
                h.store.put(
                    "session",
                    owner["id"],
                    {**owner, "scopes": [v for v in owner["scopes"] if v != "screen:retain"]},
                )
            plan = {"steps": [observe], "observe": True}
            if calls:
                self.assertEqual(1, len(request.images))
                frame = request.images[0]
                final = step(
                    "machine.visual",
                    "visual_control",
                    request={
                        "operation": "visual_click",
                        "handle": handle,
                        "pid": process.pid,
                        "sha256": frame.sha256,
                        "width": frame.width,
                        "height": frame.height,
                        "x": int(frame.width * 0.4),
                        "y": int(frame.height * 0.4),
                    },
                )
                plan = {"steps": [final]}
            p.body = {
                **(
                    {"response": json.dumps(plan)}
                    if request.images
                    else {"message": {"content": json.dumps(plan)}}
                ),
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 10,
            }
            calls.append(request)
            return generate(provider, model, secret, request, *args, **kwargs)

        http.generate = guarded_generate
        executor = ModelExecutor(
            Router(
                Registry([provider], [model]),
                CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic"}, h.store),
                {"ollama": http},
                h.store,
            ),
            ModelRequest("template", "template", ""),
            RoutingPolicy(),
            grid=h.grid,
        )
        h.dispatcher.executors["models.reason"] = executor
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
        self.owner.request(
            "submit",
            {
                "text": "Create worker Visual: On device test-machine: First capture the selected "
                f"bound window handle {handle} pid {process.pid}, then click the blue rectangle",
                "kind": "text",
                "target": h.node_id,
                "parameters": {},
                "retain": True,
            },
        )
        deadline = monotonic() + 35
        while monotonic() < deadline:
            self.worker.step()
            actions = h.store.all("planned_action")
            visual = [a for a in actions if a["capability_id"] == "machine.visual"]
            if withdraw and any(t["state"] == "failed" for t in h.store.all("task")):
                break
            if visual and h.store.task(visual[0]["task_id"]).state in {
                "partially_verified",
                "failed",
            }:
                break
            sleep(0.02)
        else:
            self.fail(
                "image planning did not finish: "
                + json.dumps(
                    {
                        "tasks": [(t["state"], t.get("blocker")) for t in h.store.all("task")],
                        "results": [
                            (r["executor"], r["success"], r.get("error"))
                            for r in h.store.all("result")
                        ],
                        "requests": len(p.requests),
                        "native_errors": native_errors,
                    }
                )
            )
        if withdraw:
            self.assertEqual(1, len(p.requests))
            self.assertFalse(visual)
        else:
            self.assertEqual([], native_errors)
            self.assertEqual("partially_verified", h.store.task(visual[0]["task_id"]).state)
            self.assertEqual(2, len(p.requests))
            images = p.requests[1]["body"]["images"]
            self.assertEqual(
                (self.workspace / "plan.png").read_bytes(), base64.b64decode(images[0])
            )
            self.assertEqual(baseline + 1, int(marker.read_text()))
            self.assertEqual("private", h.store.all("route_history")[-1]["mode"])
            self.assertNotIn(images[0], json.dumps(h.store.all("route_history")))
            self.assertNotIn(images[0], json.dumps(h.store.all("planned_action")))
