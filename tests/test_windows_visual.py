"""Selected synthetic window pixels and real input; no owner window capture."""

import base64
import hashlib
import json
import os
import subprocess
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep, time
from unittest.mock import patch

from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import InteractiveWorker
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import Dispatcher
from oscar.windows_desktop import InstalledApp, WindowsDesktop


class VisualContractTests(unittest.TestCase):
    def test_capture_does_not_imply_retention_and_remote_contracts_match(self):
        from oscar.remote_machine import REMOTE_MACHINE_CAPABILITIES, validate_remote_machine
        from oscar.windows_files import WindowsScopedFiles

        for path in (None, 7, [], "../escape", "NUL.png"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                WindowsScopedFiles.parts(path)

        worker = object.__new__(InteractiveWorker)

        def grant(permission):
            if permission == "screen:retain":
                raise PermissionError("no retention")

        with patch.object(worker, "check_permission", side_effect=grant):
            self.assertTrue(worker.capture_granted())
            self.assertFalse(worker.capture_granted(retain=True))
        capture = REMOTE_MACHINE_CAPABILITIES["machine.screen"]
        control = REMOTE_MACHINE_CAPABILITIES["machine.visual"]
        self.assertIn("screen:retain", capture[1])
        self.assertNotIn("screen:retain", control[1])
        for kind in (capture[0], control[0]):
            self.assertEqual({"request": {}}, validate_remote_machine(kind, {"request": {}}))
            with self.assertRaises(ValueError):
                validate_remote_machine(kind, {"request": {}, "shell": True})

    def test_capture_grant_and_exact_visual_material(self):
        adapter = object.__new__(WindowsDesktop)
        adapter.permissions = frozenset({"machine:host", "desktop:control"})
        adapter.targets, adapter.target_apps = {1: 2}, {1: "fixture"}
        adapter.shell = "selected-shell.exe"
        request = {"operation": "screenshot", "handle": 1, "pid": 2}
        with self.assertRaises(PermissionError):
            adapter.command(request)
        adapter.permissions |= {"desktop:capture"}
        with patch.object(adapter, "bind"):
            self.assertTrue(adapter.command(request))
            click = {
                **request,
                "operation": "visual_click",
                "sha256": "a" * 64,
                "width": 100,
                "height": 100,
                "x": 50,
                "y": 50,
            }
            self.assertTrue(adapter.command(click))
            for extra in (
                {"x": True},
                {"x": 100},
                {"y": -1},
                {"width": 4097},
                {"sha256": "wrong"},
                {"handle": True},
                {"extra": "ignored"},
            ):
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    adapter.command({**click, **extra})


@unittest.skipUnless(os.name == "nt", "actual Windows synthetic-window acceptance")
class WindowsVisualTests(unittest.TestCase):
    def remote_workflow(self, root, adapter, shell, target):
        from oscar.cloud import CloudConfig, CloudCore
        from oscar.remote_grid import create_invitation
        from oscar.remote_machine import RemoteEffects, RemoteMachine
        from tests.test_cloud import configuration
        from tests.test_remote_grid import DirectClient, keypair, signature

        remote = root / "remote"
        remote.mkdir()
        workspace = remote / "effects"
        workspace.mkdir()
        transport_key, public = keypair()
        owner_key, owner_public = keypair()
        with closing(CloudCore(CloudConfig.load(configuration(remote)), initialize=True)) as core:
            clients = []
            for role, node in (("desktop", "visual-desktop"), ("mobile", "visual-controller")):
                invite = create_invitation(
                    core,
                    node,
                    role,
                    "installation-" + node,
                    public,
                    workspace="visual-workspace" if role == "desktop" else "",
                    retain=True,
                    owner_public_key=owner_public,
                    machine_control=True,
                    screen_capture=True,
                    screen_retain=True,
                )
                session = core.remote.enroll(
                    {
                        "version": 2,
                        "challenge_id": invite["challenge_id"],
                        "signature": signature(
                            transport_key, base64.b64decode(invite["signing_payload"])
                        ),
                    }
                )
                clients.append(DirectClient(core, session))
            desktop, owner = clients

            def effects(client, scope, guard, **kwargs):
                actual = RemoteEffects(client, scope, guard)
                # Register only this run-owned fixture; retain native effects and Core checks.
                actual.desktop = adapter
                return actual

            with patch("oscar.remote_machine.RemoteEffects", side_effect=effects):
                worker = RemoteMachine(
                    desktop,
                    MachineScope(workspace, True, (shell,)),
                    "visual-workspace",
                    remote / "journal.sqlite",
                    capabilities=("machine.screen", "machine.visual"),
                )
            with closing(worker):
                worker.advertise()

                def execute(kind, request):
                    task = owner.request(
                        "submit",
                        {
                            "text": "Only synthetic visual fixture",
                            "kind": kind,
                            "target": "visual-desktop",
                            "parameters": {"request": request},
                            "retain": True,
                        },
                    )
                    review = owner.request(
                        "challenge", {"task_id": task["task_id"], "operation": "approve"}
                    )
                    owner.request(
                        "complete",
                        {
                            "challenge_id": review["challenge_id"],
                            "signature": signature(
                                owner_key, base64.b64decode(review["signing_payload"])
                            ),
                        },
                    )
                    deadline = monotonic() + 15
                    while monotonic() < deadline:
                        worker.step()
                        view = owner.request("inspect", {"task_id": task["task_id"]})
                        if view["state"] in {"verified", "partially_verified", "failed", "blocked"}:
                            return view
                        sleep(0.02)
                    self.fail("synthetic remote visual task did not finish")

                captured = execute(
                    "screen_capture", {"operation": "screenshot", **target, "path": "remote.png"}
                )
                self.assertEqual("partially_verified", captured["state"])
                result = [
                    r
                    for r in core.harness.store.all("result")
                    if r["task_id"] == captured["task_id"]
                ][-1]
                frame = json.loads(result["value"])
                self.assertEqual(
                    frame["sha256"],
                    hashlib.sha256((workspace / "remote.png").read_bytes()).hexdigest(),
                )
                click = {
                    "operation": "visual_click",
                    **target,
                    "sha256": frame["sha256"],
                    "width": frame["width"],
                    "height": frame["height"],
                    "x": int(frame["width"] * 0.4),
                    "y": int(frame["height"] * 0.4),
                }
                self.assertEqual("partially_verified", execute("visual_control", click)["state"])
                self.assertEqual("2", (root / "clicks.txt").read_text())
                worker.step()
                self.assertEqual("2", (root / "clicks.txt").read_text())
                self.assertEqual({}, worker.effects.outputs)

    def test_actual_capture_visual_fallback_and_no_replay(self):
        shell = str(
            Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        with TemporaryDirectory(prefix="oscar-synthetic-visual-") as temporary:
            root = Path(temporary)
            process = subprocess.Popen(
                [
                    shell,
                    "-NoProfile",
                    "-STA",
                    "-File",
                    str(Path(__file__).with_name("fixtures") / "windows_visual.ps1"),
                    "-Root",
                    str(root),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            try:
                deadline = monotonic() + 20
                while not (root / "window.txt").exists() and monotonic() < deadline:
                    if process.poll() is not None:
                        self.fail(f"synthetic window unavailable: {process.communicate()[1]!r}")
                    sleep(0.05)
                target = {"handle": int((root / "window.txt").read_text()), "pid": process.pid}
                with closing(Store(root / "core.sqlite")) as store:
                    grid = Grid(store)
                    grants = (
                        "heartbeat",
                        "advertise",
                        "execute",
                        "cancel",
                        "machine:host",
                        "desktop:control",
                        "desktop:capture",
                        "screen:retain",
                        "files:read",
                        "files:write",
                    )
                    grid.register(Node("synthetic-windows", NodeRole.DESKTOP, grants))
                    session = grid.pair("synthetic-windows", grants)
                    worker = InteractiveWorker(
                        store, grid, session, MachineScope(root, True, (shell,))
                    )
                    app = InstalledApp(
                        "synthetic-visual",
                        "Synthetic visual window",
                        None,
                        shell,
                        "native_exe",
                        "owned-fixture",
                        time(),
                        True,
                        ("observe_window",),
                    )
                    worker.desktop = WindowsDesktop(
                        permissions=frozenset(grants), allowed_apps=(app,)
                    )
                    worker.desktop.bind(**target, app_id=app.id)
                    grid.advertise(session, worker.capabilities())
                    runtime = Runtime(store, grid, MachineVerifier(worker.files))
                    transports = {
                        session.node_id: (
                            Dispatcher(store, grid, session.node_id, worker.executors()),
                            session,
                        )
                    }

                    def execute(kind, request):
                        task = runtime.create(
                            Intent(
                                "Operate only synthetic window",
                                "capability",
                                capability_kind=kind,
                                parameters={"request": request},
                            )
                        )
                        return runtime.run(task.id, transports)

                    captured = execute(
                        "screen_capture",
                        {"operation": "screenshot", **target, "path": "selected.png"},
                    )
                    self.assertEqual("partially_verified", captured.state, store.all("result"))
                    results = [r for r in store.all("result") if r["task_id"] == captured.id]
                    frame = json.loads(results[-1]["value"])
                    png = (root / "selected.png").read_bytes()
                    self.assertEqual(frame["sha256"], hashlib.sha256(png).hexdigest())
                    self.assertGreaterEqual(frame["width"], 320)
                    self.assertAlmostEqual(frame["width"] / frame["height"], 1.6, places=2)
                    x, y = int(frame["width"] * 0.4), int(frame["height"] * 0.4)
                    self.assertNotIn("png", frame)
                    observer = root / "inspect.ps1"
                    observer.write_text(
                        "param([string]$Path,[int]$X,[int]$Y)\n"
                        "Add-Type -AssemblyName System.Drawing\n"
                        "$image=[Drawing.Bitmap]::new($Path)\ntry {"
                        "$p=$image.GetPixel($X,$Y);"
                        "Write-Output ($p.R.ToString()+','+$p.G+','+$p.B+','+$p.A)"
                        "} finally {$image.Dispose()}"
                    )
                    pixel = subprocess.check_output(
                        [
                            shell,
                            "-NoProfile",
                            "-File",
                            str(observer),
                            str(root / "selected.png"),
                            str(x),
                            str(y),
                        ],
                        text=True,
                        timeout=15,
                    )
                    self.assertEqual("19,167,229,255", pixel.strip())
                    original_hash = frame["sha256"]
                    overwrite = execute(
                        "screen_capture",
                        {"operation": "screenshot", **target, "path": "selected.png"},
                    )
                    self.assertEqual("failed", overwrite.state)
                    self.assertEqual(
                        original_hash,
                        hashlib.sha256((root / "selected.png").read_bytes()).hexdigest(),
                    )
                    click = {
                        "operation": "visual_click",
                        **target,
                        "sha256": original_hash,
                        "width": frame["width"],
                        "height": frame["height"],
                        "x": x,
                        "y": y,
                    }
                    for extra in ({"sha256": "0" * 64}, {"width": frame["width"] + 1}):
                        self.assertEqual(
                            "failed", execute("visual_control", {**click, **extra}).state
                        )
                        self.assertFalse((root / "clicks.txt").exists())
                    clicked = execute("visual_control", click)
                    self.assertEqual("partially_verified", clicked.state, store.all("result"))
                    deadline = monotonic() + 3
                    while not (root / "clicks.txt").exists() and monotonic() < deadline:
                        sleep(0.05)
                    self.assertEqual("1", (root / "clicks.txt").read_text())
                    runtime.run(clicked.id, transports)
                    self.assertEqual("1", (root / "clicks.txt").read_text())
                    self.assertEqual("failed", execute("visual_control", click).state)
                    self.assertEqual("1", (root / "clicks.txt").read_text())
                    bypass = execute("desktop_control", {"operation": "screenshot", **target})
                    self.assertEqual("failed", bypass.state)
                    self.remote_workflow(root, worker.desktop, shell, target)
                    worker.desktop.permissions -= {"desktop:capture"}
                    self.assertNotIn("machine.screen", {c.id for c in worker.capabilities()})
                    self.assertNotIn("machine.visual", {c.id for c in worker.capabilities()})
            finally:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
                if process.stderr:
                    process.stderr.close()
