import importlib.util
import json
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread
from time import sleep, time
from unittest.mock import patch

from oscar.browser_worker import bounded_download, validate, write_artifact
from oscar.contracts import TaskState
from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import InteractiveWorker
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier, MachineWorker
from oscar.powershell import command, discover
from oscar.runtime import Runtime
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store
from oscar.transport import Dispatcher


class BrowserBoundaryTests(unittest.TestCase):
    def plan(self, steps):
        return {"origins": ["https://example.com"], "steps": steps, "timeout": 5, "max_text": 1000}

    def test_browser_rejects_credential_urls_and_foreign_navigation(self):
        for url in ("https://user:password@example.com", "file:///secret", "http://foreign.test"):
            with self.assertRaises((ValueError, PermissionError)):
                validate(self.plan([{"operation": "navigate", "url": url}]))

    def test_no_raw_javascript_arbitrary_actions_or_unbounded_download(self):
        for step in (
            {"operation": "evaluate", "script": "fetch('/secret')"},
            {"operation": "download", "selector": "a", "path": "../escape", "max_bytes": 10},
            {"operation": "download", "selector": "a", "path": "test", "max_bytes": 10**9},
        ):
            with self.assertRaises(ValueError):
                validate(self.plan([step]))

    def test_artifacts_reject_windows_devices_and_preserve_existing_files(self):
        for name in ("NUL", "CON.png", "COM1.txt", "a\\b", "trailing.", "trailing "):
            with self.assertRaises(ValueError):
                validate(self.plan([{"operation": "screenshot", "path": name}]))
        with TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "proof.png"
            write_artifact(artifact, b"original")
            with self.assertRaises(FileExistsError):
                write_artifact(artifact, b"replacement")
            self.assertEqual(b"original", artifact.read_bytes())
            with self.assertRaises(ValueError):
                write_artifact(Path(temporary) / "too-big", b"a" * 4_000_001)

    def test_download_enforces_bounds_before_network_and_before_creation(self):
        from io import BytesIO

        with TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "download"
            with self.assertRaises(ValueError):
                bounded_download("https://example.com", artifact, [], -1, 1)
            with patch("oscar.browser_worker.build_opener") as opener:
                opener.return_value.open.return_value = BytesIO(b"oversized")
                with self.assertRaisesRegex(ValueError, "bound exceeded"):
                    bounded_download("https://example.com", artifact, ["https://example.com"], 3, 1)
            self.assertFalse(artifact.exists())

    def test_existing_link_is_never_followed(self):
        with TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "link"
            target = Path(temporary) / "missing-target"
            try:
                artifact.symlink_to(target)
            except OSError:
                self.skipTest("host does not grant symbolic-link creation")
            with self.assertRaises(FileExistsError):
                write_artifact(artifact, b"unsafe")
            self.assertFalse(target.exists())


@unittest.skipUnless(os.name == "nt", "actual Windows native acceptance")
class PowerShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "runtime.sqlite")
        self.grid = Grid(self.store)
        scopes = (
            "heartbeat",
            "advertise",
            "execute",
            "cancel",
            "machine:host",
            "files:read",
            "files:write",
        )
        self.grid.register(Node("windows", NodeRole.DESKTOP, scopes))
        self.session = self.grid.pair("windows", scopes)
        self.manifest = discover()
        self.assertIsNotNone(self.manifest)
        self.worker = MachineWorker(
            self.store,
            self.grid,
            self.session,
            MachineScope(self.root, True, (self.manifest.executable,)),
        )
        self.grid.advertise(self.session, self.worker.capabilities())
        self.runtime = Runtime(self.store, self.grid, MachineVerifier(self.worker.files))
        self.transports = {
            "windows": (
                Dispatcher(self.store, self.grid, "windows", self.worker.executors()),
                self.session,
            )
        }

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def task(self, request, timeout=10, criterion=None):
        return self.runtime.create(
            Intent(
                "typed PowerShell acceptance",
                "capability",
                capability_kind="powershell",
                parameters={"request": request, "timeout": timeout},
                criterion=criterion,
            )
        )

    def test_real_utf8_artifact_independently_verified(self):
        text = "OSCAR independent UTF-8 proof: café\n"
        task = self.task(
            {"operation": "write_utf8", "path": "proof.txt", "content": text},
            criterion={"kind": "file_exact", "path": "proof.txt", "content": text},
        )
        self.assertEqual(TaskState.VERIFIED, self.runtime.run(task.id, self.transports).state)
        self.assertEqual(text.encode(), (self.root / "proof.txt").read_bytes())
        result = next(r for r in self.store.all("result") if r["task_id"] == task.id)
        self.assertEqual("REPORTED", result["status"])
        self.assertNotIn(text, result["value"])

    def test_powershell_profiles_and_provider_environment_excluded(self):
        with patch.dict(os.environ, {"OSCAR_PROVIDER_TEST_SECRET": "synthetic"}):
            task = self.task({"operation": "environment"})
            self.runtime.run(task.id, self.transports)
        action = self.store.get("planned_action", task.id)
        output = json.loads(self.worker.outputs[action["id"]])
        self.assertNotIn("OSCAR_PROVIDER_TEST_SECRET", output["names"])
        self.assertEqual(self.root.resolve(), Path(output["cwd"]).resolve())
        self.assertRegex(output["version"], r"^\d+\.\d+")

    def test_typed_shell_escape_and_traversal_rejected(self):
        for request in (
            {"operation": "script", "script": "Remove-Item *"},
            {"operation": "write_utf8", "path": "../escape", "content": "a"},
        ):
            with self.assertRaises(ValueError):
                command(self.manifest, request, self.root)

    def test_actual_timeout(self):
        task = self.task({"operation": "wait", "milliseconds": 10_000}, timeout=0.4)
        result = self.runtime.run(task.id, self.transports)
        self.assertEqual(TaskState.FAILED, result.state)
        self.assertEqual("command_timeout", result.blocker)

    def test_actual_cancellation(self):
        task = self.task({"operation": "wait", "milliseconds": 10_000})
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.runtime.run, task.id, self.transports)
            sleep(0.4)
            self.runtime.cancel(task.id)
            self.assertEqual(TaskState.CANCELLED, future.result(timeout=5).state)


@unittest.skipUnless(os.name == "nt", "actual native Credential Manager")
class NativeCredentialTests(unittest.TestCase):
    def test_native_rotation_expiry_restart_delete_and_redacted_representation(self):
        vault = WindowsCredentialStore()
        ref = vault.put("synthetic-first", expires_at=time() + 60)
        try:
            self.assertEqual("synthetic-first", vault.read(ref).value)
            self.assertNotIn("synthetic-first", repr(vault.read(ref)))
            vault.put("synthetic-rotated", reference=ref, expires_at=time() + 60)
            process = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from oscar.secure_credentials import "
                    "WindowsCredentialStore; assert WindowsCredentialStore().read("
                    "sys.stdin.readline()."
                    "strip()).value == 'synthetic-rotated'; print('native restart PASS')",
                ],
                input=ref + "\n",
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(0, process.returncode)
            self.assertEqual("native restart PASS", process.stdout.strip())
            vault.put("synthetic-expired", reference=ref, expires_at=time() - 1)
            with self.assertRaises(PermissionError):
                vault.read(ref)
        finally:
            vault.delete(ref)
        with self.assertRaises(KeyError):
            vault.read(ref)
        vault.delete(ref)

    def test_cannot_access_unrelated_credential_targets(self):
        with self.assertRaises(ValueError):
            WindowsCredentialStore().read("Microsoft:user-credential")


@unittest.skipUnless(
    os.name == "nt" and importlib.util.find_spec("playwright"),
    "actual Windows with optional Playwright installation",
)
class BrowserLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.visited = Event()
        visited = self.visited

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                visited.set()
                self.send_response(200)
                self.end_headers()
                if self.path == "/download":
                    self.wfile.write(b"synthetic-download")
                else:
                    self.wfile.write(
                        b"<html><title>Scoped fixture</title><body>bounded synthetic fixture"
                        b'<a id="download" href="/download">download</a></body></html>'
                    )

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        Thread(target=self.server.serve_forever, daemon=True).start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.store = Store(self.root / "state.sqlite")
        self.addCleanup(self.store.close)
        grid = Grid(self.store)
        grants = (
            "advertise",
            "heartbeat",
            "execute",
            "cancel",
            "machine:host",
            "files:read",
            "files:write",
            "browser:control",
        )
        grid.register(Node("browser-fixture", NodeRole.DESKTOP, grants))
        session = grid.pair("browser-fixture", grants)
        worker = InteractiveWorker(
            self.store,
            grid,
            session,
            MachineScope(self.root, True, (sys.executable,)),
            browser=True,
        )
        if not worker.browser_python:
            self.skipTest("selected interpreter has no installed Chromium")
        grid.advertise(session, worker.capabilities())
        self.runtime = Runtime(self.store, grid, MachineVerifier(worker.files))
        self.transports = {
            session.node_id: (
                Dispatcher(self.store, grid, session.node_id, worker.executors()),
                session,
            )
        }

    def task(self, timeout):
        plan = {
            "origins": [self.origin],
            "steps": [
                {"operation": "navigate", "url": self.origin},
                {"operation": "wait", "selector": "#never-present"},
            ],
            "timeout": timeout,
            "max_text": 100,
        }
        return self.runtime.create(
            Intent(
                "bounded browser interruption",
                "capability",
                capability_kind="browser",
                parameters={"request": plan, "timeout": timeout},
            )
        )

    def test_cancel_after_real_browser_has_reached_fixture(self):
        task = self.task(20)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.runtime.run, task.id, self.transports)
            self.assertTrue(self.visited.wait(10), "Chromium must actually reach the local fixture")
            self.runtime.cancel(task.id, self.transports)
            self.assertEqual(TaskState.CANCELLED, future.result(timeout=5).state)
        self.assertEqual(TaskState.CANCELLED, self.runtime.run(task.id, self.transports).state)

    def test_timeout_after_real_navigation(self):
        task = self.task(3)
        result = self.runtime.run(task.id, self.transports)
        self.assertTrue(self.visited.is_set())
        self.assertEqual(TaskState.FAILED, result.state)
        self.assertEqual("command_timeout", result.blocker)

    def test_real_worker_keeps_download_and_screenshot_in_artifact_workspace(self):
        plan = {
            "origins": [self.origin],
            "steps": [
                {"operation": "navigate", "url": self.origin},
                {"operation": "inspect"},
                {
                    "operation": "download",
                    "selector": "#download",
                    "path": "proof.txt",
                    "max_bytes": 100,
                },
                {"operation": "screenshot", "path": "proof.png"},
            ],
            "timeout": 15,
            "max_text": 100,
        }
        task = self.runtime.create(
            Intent(
                "scoped browser artifacts",
                "capability",
                capability_kind="browser",
                parameters={"request": plan},
            )
        )
        result = self.runtime.run(task.id, self.transports)
        self.assertEqual(TaskState.PARTIALLY_VERIFIED, result.state)
        self.assertTrue(self.visited.is_set())
        self.assertEqual(b"synthetic-download", (self.root / "proof.txt").read_bytes())
        self.assertTrue((self.root / "proof.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        original = (self.root / "proof.png").read_bytes()
        failed = self.runtime.create(
            Intent(
                "reject artifact overwrite",
                "capability",
                capability_kind="browser",
                parameters={"request": plan},
            )
        )
        failure = self.runtime.run(failed.id, self.transports)
        self.assertEqual(TaskState.FAILED, failure.state)
        self.assertEqual("browser.plan_execution", failure.blocker)
        self.assertEqual(original, (self.root / "proof.png").read_bytes())


if __name__ == "__main__":
    unittest.main()
