import importlib.util
import json
import os
import sys
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import parse_qs

from oscar.accounts import AccountRegistry
from oscar.browser_profiles import BrowserProfiles
from oscar.browser_worker import run, validate
from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import InteractiveWorker
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import Dispatcher


class ProfileBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state.sqlite")
        self.addCleanup(self.store.close)
        self.accounts = AccountRegistry(self.store)
        self.account = self.accounts.add("fixture", "tenant", "alpha", "Same", verified=True)
        self.profiles = BrowserProfiles(self.accounts, self.root / "profiles")

    def parameters(self, account=None):
        account = account or self.account
        return {"request": {}, "account_id": account.id, "account_generation": account.generation}

    def test_alias_cannot_change_or_select_profile(self):
        key = self.profiles.check(self.parameters())
        self.accounts.rename(self.account.id, "New name")
        self.assertEqual(key, self.profiles.check(self.parameters()))
        other = self.accounts.add("fixture", "tenant", "beta", "Same", verified=True)
        self.assertNotEqual(key, self.profiles.check(self.parameters(other)))
        with self.assertRaises(PermissionError):
            self.profiles.check({**self.parameters(), "profile": str(self.root)})

    def test_disconnect_and_replacement_fence_old_profile(self):
        self.accounts.disconnect(self.account.id)
        with self.assertRaises(PermissionError):
            self.profiles.check(self.parameters())

    def test_profiles_never_live_in_artifact_workspace(self):
        with self.assertRaises(PermissionError):
            with self.profiles.open(self.parameters(), self.root):
                self.fail("profile readable through artifact workspace")

    def test_new_operations_remain_typed(self):
        for step in [
            {"operation": "switch_tab", "index": True},
            {"operation": "upload", "selector": "input", "path": "../private"},
            {"operation": "evaluate", "script": "document.cookie"},
        ]:
            with self.assertRaises(ValueError):
                validate(
                    {
                        "origins": ["https://example.com"],
                        "steps": [step],
                        "timeout": 5,
                        "max_text": 100,
                    }
                )


@unittest.skipUnless(importlib.util.find_spec("playwright"), "optional installed Playwright")
class RealProfileTests(unittest.TestCase):
    parameters = ProfileBindingTests.parameters

    def setUp(self):
        ProfileBindingTests.setUp(self)
        owner = self
        self.download_requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                data = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
                identity = data["identity"][0]
                self.send_response(303)
                self.send_header(
                    "Set-Cookie",
                    "fixture=" + identity + "; Max-Age=3600; HttpOnly; SameSite=Strict",
                )
                self.send_header("Location", "/result")
                self.end_headers()

            def do_GET(self):
                owner.download_requests.append((self.path, self.headers.get("Cookie", "")))
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/sink")
                    self.end_headers()
                    return
                if self.path == "/download" and self.headers.get("Cookie", "") not in {
                    "fixture=alpha",
                    "fixture=beta",
                }:
                    self.send_response(401)
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                if self.path == "/oversized":
                    self.wfile.write(b"x" * 2000)
                elif self.path == "/binary":
                    self.wfile.write(bytes(range(256)))
                elif self.path == "/download":
                    self.wfile.write(b"synthetic-agenda")
                else:
                    self.wfile.write(
                        (
                            "<html><title>Account fixture</title><body>"
                            + self.headers.get("Cookie", "anonymous")
                            + '<form method="post"><label for="identity">Identity</label>'
                            '<input id="identity" name="identity"><select id="choice">'
                            '<option value="a">A</option><option value="b">B</option></select>'
                            '<input id="upload" type="file">'
                            '<button id="submit">Continue</button></form>'
                            '<a id="download" href="/download">Download</a>'
                            '<a id="large" href="/oversized">Large</a>'
                            '<a id="binary" href="/binary">Binary</a>'
                            '<a id="redirect" href="/redirect">Redirect</a></body></html>'
                        ).encode()
                    )

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        Thread(target=self.server.serve_forever, daemon=True).start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "upload.txt").write_text("synthetic-upload")
        self.grid = Grid(self.store)
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
        self.grid.register(Node("browser-profile-fixture", NodeRole.DESKTOP, grants))
        session = self.grid.pair("browser-profile-fixture", grants)
        self.worker = InteractiveWorker(
            self.store,
            self.grid,
            session,
            MachineScope(workspace, True, (sys.executable,), max_timeout=120),
            browser=True,
            browser_profiles=self.profiles,
        )
        if not self.worker.browser_python:
            self.fail("browser launch failed: " + json.dumps(self.worker.browser_probe))
        self.grid.advertise(session, self.worker.capabilities())
        self.runtime = Runtime(self.store, self.grid, MachineVerifier(self.worker.files))
        self.transports = {
            session.node_id: (
                Dispatcher(self.store, self.grid, session.node_id, self.worker.executors()),
                session,
            )
        }

    def execute_browser(self, account, steps):
        parameters = {
            **self.parameters(account),
            "request": {
                "origins": [self.origin],
                "steps": steps,
                "timeout": 30,
                "max_text": 1000,
            },
        }
        task = self.runtime.create(
            Intent(
                "Synthetic account-bound browser operation",
                "capability",
                capability_kind="browser",
                parameters=parameters,
            )
        )
        completed = self.runtime.run(task.id, self.transports)
        self.assertEqual("partially_verified", completed.state, completed.blocker)
        result = next(r for r in self.store.all("result") if r["task_id"] == task.id)
        return json.loads(self.worker.outputs[result["action_id"]])

    def test_real_two_accounts_forms_tabs_artifacts_restart_and_revocation(self):
        second = self.accounts.add("fixture", "tenant", "beta", "Same", verified=True)
        navigation = {"operation": "navigate", "url": self.origin}
        first = self.execute_browser(
            self.account,
            [
                navigation,
                {"operation": "fill", "selector": "#identity", "text": "alpha"},
                {"operation": "select", "selector": "#choice", "value": "b"},
                {"operation": "upload", "selector": "#upload", "path": "upload.txt"},
                {"operation": "submit", "selector": "#submit"},
                {"operation": "wait", "selector": "#download"},
                {"operation": "scroll", "selector": "#download"},
                {"operation": "inspect"},
                {"operation": "accessibility", "selector": "body"},
                {"operation": "screenshot", "path": "proof.png"},
                {
                    "operation": "download",
                    "selector": "#download",
                    "path": "agenda.txt",
                    "max_bytes": 100,
                },
                {"operation": "new_tab"},
                navigation,
                {"operation": "switch_tab", "index": 0},
                {"operation": "close_tab"},
                {"operation": "inspect"},
            ],
        )
        self.assertIn("fixture=alpha", first["observations"][0]["text"])
        self.assertTrue(first["observations"][1]["accessibility"])
        self.assertEqual(b"synthetic-agenda", self.worker.files.read("agenda.txt"))
        self.assertIn(("/download", "fixture=alpha"), self.download_requests)
        self.assertTrue(self.worker.files.read("proof.png").startswith(b"\x89PNG"))
        anonymous = self.execute_browser(second, [navigation, {"operation": "inspect"}])
        self.assertIn("anonymous", anonymous["observations"][0]["text"])
        self.execute_browser(
            second,
            [
                navigation,
                {"operation": "fill", "selector": "#identity", "text": "beta"},
                {"operation": "submit", "selector": "#submit"},
                {"operation": "inspect"},
                {
                    "operation": "download",
                    "selector": "#download",
                    "path": "beta-agenda.txt",
                    "max_bytes": 100,
                },
            ],
        )
        self.assertIn(("/download", "fixture=beta"), self.download_requests)
        self.assertEqual(b"synthetic-agenda", self.worker.files.read("beta-agenda.txt"))
        # Every plan launches a new Chromium process; disk profile is the only session continuity.
        for account, name in [(self.account, "alpha"), (second, "beta")]:
            observed = self.execute_browser(account, [navigation, {"operation": "inspect"}])
            self.assertIn("fixture=" + name, observed["observations"][0]["text"])
        self.accounts.disconnect(self.account.id)
        with self.assertRaises(PermissionError):
            self.profiles.check(self.parameters())
        if os.name == "nt":
            import psutil

            for process in psutil.process_iter(["name"]):
                if "chrom" in (process.info["name"] or "").lower():
                    try:
                        command = process.cmdline()
                    except psutil.NoSuchProcess:
                        continue
                    self.assertNotIn(str(self.profiles.root), " ".join(command or []))

    def test_actual_browser_download_rejects_missing_auth_oversize_redirect_and_overwrite(self):
        from playwright.sync_api import Error

        workspace = self.root / "workspace"
        for selector in ("#download", "#large", "#redirect"):
            with self.subTest(selector=selector):
                request = {
                    "origins": [self.origin],
                    "timeout": 15,
                    "max_text": 100,
                    "steps": [
                        {"operation": "navigate", "url": self.origin},
                        {
                            "operation": "download",
                            "selector": selector,
                            "path": "rejected.bin",
                            "max_bytes": 10,
                        },
                    ],
                }
                with self.assertRaisesRegex(
                    Error, "download rejected|download bound exceeded|Failed to fetch"
                ):
                    run(request, workspace)
                self.assertFalse((workspace / "rejected.bin").exists())
        self.assertFalse(any(path == "/sink" for path, _ in self.download_requests))
        request["steps"][-1].update(selector="#binary", path="binary.bin", max_bytes=256)
        run(request, workspace)
        self.assertEqual(bytes(range(256)), (workspace / "binary.bin").read_bytes())
        request["steps"][-1].update(selector="#redirect", max_bytes=10)
        (workspace / "preserved.bin").write_bytes(b"original")
        request["steps"][-1]["path"] = "preserved.bin"
        before = sum(path == "/redirect" for path, _ in self.download_requests)
        with self.assertRaises(ValueError):
            run(request, workspace)
        self.assertEqual(b"original", (workspace / "preserved.bin").read_bytes())
        self.assertEqual(before, sum(path == "/redirect" for path, _ in self.download_requests))


if __name__ == "__main__":
    unittest.main()
