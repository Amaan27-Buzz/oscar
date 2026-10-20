"""Real SDK/process interoperability; synthetic identities, independent file readback."""

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oscar.capabilities import Cancellation, Cancelled
from oscar.connector_providers import mcp_capability_name
from oscar.connectors import ConnectorFabric, EnvironmentSecrets, RiskLevel
from oscar.contracts import Action, Task, new_id, record
from oscar.mcp_client import (
    MCPPlugins,
    MCPServerConfig,
    executable_digest,
    validate_destination,
    validate_schema,
)
from oscar.policy import PersonalPolicy
from oscar.storage import Store

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@unittest.skipUnless(importlib.util.find_spec("mcp"), "install oscar-brain[mcp]")
class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "core.sqlite")
        self.fabric = ConnectorFabric(
            self.store, EnvironmentSecrets({}), PersonalPolicy(self.store)
        )
        self.accounts = {"knowledge": 1, "writer": 1}

        def authorize(identifier, generation):
            if self.accounts.get(identifier) != generation:
                raise PermissionError("account revoked/replaced")

        self.plugins = MCPPlugins(self.store, self.fabric, authorize)
        self.authorize = authorize
        self.task = Task(new_id(), new_id(), new_id())
        self.store.put("task", self.task.id, record(self.task))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def config(self, identifier, script, *arguments, **options):
        command = str(Path(sys.executable).resolve())
        fixture = str(FIXTURES / script)
        return MCPServerConfig(
            identifier,
            identifier,
            identifier,
            command=command,
            arguments=("-I", fixture, *arguments),
            cwd=str(self.root),
            reviewed_files=(
                (command, executable_digest(command)),
                (fixture, executable_digest(fixture)),
            ),
            **options,
        )

    def invoke(self, instance, name, arguments, *, confirmed=False):
        action = Action(
            new_id(),
            self.task.id,
            self.task.correlation_id,
            instance + ":" + mcp_capability_name(name),
            {"path": {"name": name}, "body": arguments},
            new_id(),
            "owner",
        )
        return self.fabric.execute(
            instance,
            mcp_capability_name(name),
            action,
            Cancellation(self.store, self.task.id),
            frozenset({"connectors:read", "connectors:write"}),
            confirmed=confirmed,
        )

    def test_two_real_servers_ask_independent_readback_and_restart(self):
        knowledge = self.config(
            "knowledge", "mcp_knowledge.py", "knowledge", read_resources=True, get_prompts=True
        )
        writer = self.config("writer", "mcp_workspace.py", str(self.root / "workspace"), "writer")
        self.plugins.register(knowledge, {"lookup": RiskLevel.READ}, owner_reviewed=True)
        self.plugins.register(
            writer,
            {"read_file": RiskLevel.READ, "write_file": RiskLevel.WRITE},
            owner_reviewed=True,
        )
        with patch.dict(os.environ, {"OSCAR_MCP_TEST_SECRET": "must-not-reach-server"}):
            status = self.plugins.connect("knowledge")
        self.assertEqual("2026-07-28", status["metadata"]["protocol_version"])
        self.plugins.connect("writer")
        read = self.invoke("knowledge", "lookup", {"topic": "fixture"})
        self.assertTrue(read.result.success)
        body = read.payload["structuredContent"]
        self.assertEqual("knowledge", body["account_id"])
        self.assertFalse(body["secret_inherited"])
        self.assertNotEqual(os.getpid(), body["pid"])
        self.assertEqual(1, len(self.plugins.discovery("knowledge", "resources")["resources"]))
        resource = self.invoke(
            "knowledge", "oscar.resources.read", {"uri": "knowledge://fixture/fact"}
        )
        self.assertIn("Synthetic resource fact", resource.payload["contents"][0]["text"])
        prompt = self.invoke(
            "knowledge",
            "oscar.prompts.get",
            {"name": "research", "arguments": {"topic": "fixture"}},
        )
        self.assertIn("fixture", json.dumps(prompt.payload))
        denied = self.invoke("writer", "write_file", {"path": "result.txt", "content": "research"})
        self.assertFalse(denied.result.success)
        target = self.root / "workspace/result.txt"
        self.assertFalse(target.exists())
        written = self.invoke(
            "writer", "write_file", {"path": "result.txt", "content": "research"}, confirmed=True
        )
        self.assertTrue(written.result.success)
        self.assertEqual("writer", written.payload["structuredContent"]["account_id"])
        self.assertEqual("research", target.read_text())
        self.assertEqual("REPORTED", written.result.status)
        self.assertNotIn("research", json.dumps(self.store.all("mcp_installation")))
        # Stable per-instance capability prevents crossing account/server execution.
        with self.assertRaises(StopIteration):
            self.invoke(
                "knowledge", "write_file", {"path": "other.txt", "content": "x"}, confirmed=True
            )
        self.plugins.disconnect("knowledge")
        self.assertFalse(
            any(c.id.startswith("knowledge:") for c in self.fabric.capabilities("node"))
        )
        self.plugins.connect("knowledge")
        self.assertTrue(self.invoke("knowledge", "lookup", {"topic": "again"}).result.success)
        self.plugins.enable("writer", False)
        self.assertFalse(any(c.id.startswith("writer:") for c in self.fabric.capabilities("node")))
        with self.assertRaises(PermissionError):
            self.plugins.connect("writer")
        self.plugins.close()
        restarted = MCPPlugins(self.store, self.fabric, self.authorize)
        self.assertEqual({}, restarted.sessions)
        self.assertTrue(all(s["health"] == "disconnected" for s in restarted.snapshot()))
        restarted.remove("knowledge")
        restarted.remove("writer")
        self.assertEqual([], restarted.snapshot())

    def test_schema_account_and_executable_rechecks(self):
        config = self.config("knowledge", "mcp_knowledge.py", "knowledge")
        self.plugins.register(config, {"lookup": RiskLevel.READ}, owner_reviewed=True)
        self.plugins.connect("knowledge")
        self.assertFalse(self.invoke("knowledge", "lookup", {"topic": 42}).result.success)
        self.plugins.sessions["knowledge"].schemas["lookup"] = "changed"
        with self.assertRaises(PermissionError):
            self.invoke("knowledge", "lookup", {"topic": "fixture"})
        self.accounts["knowledge"] = 2
        self.assertFalse(self.invoke("knowledge", "lookup", {"topic": "fixture"}).result.success)
        self.assertEqual([], self.fabric.capabilities("node"))
        self.assertEqual("disconnected", self.plugins.inspect("knowledge")["health"])
        self.plugins.disconnect("knowledge")
        bad = replace(
            config, id="other", account_id="writer", reviewed_files=((config.command, "wrong"),)
        )
        with self.assertRaises(ValueError):
            self.plugins.register(bad, {"lookup": RiskLevel.READ}, owner_reviewed=True)

    def test_real_streamable_http_loopback_and_cleanup(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        process = subprocess.Popen(
            [sys.executable, "-I", str(FIXTURES / "mcp_knowledge.py"), "knowledge", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        break
                except OSError:
                    time.sleep(0.05)
            origin = f"http://127.0.0.1:{port}"
            config = MCPServerConfig(
                "knowledge", "HTTP fixture", "knowledge", url=origin + "/mcp", fixture_origin=origin
            )
            self.plugins.register(config, {"lookup": RiskLevel.READ}, owner_reviewed=True)
            self.plugins.connect("knowledge")
            result = self.invoke("knowledge", "lookup", {"topic": "http"})
            self.assertTrue(result.result.success)
            self.assertEqual("knowledge", result.payload["structuredContent"]["account_id"])
            self.plugins.remove("knowledge")
        finally:
            process.terminate()
            process.wait(timeout=10)

    def test_timeout_cancellation_and_reconnect(self):
        # Use the normal startup budget; the tool delay must exceed the RPC deadline.
        config = self.config("knowledge", "mcp_knowledge.py", "knowledge")
        self.plugins.register(
            config, {"delay": RiskLevel.READ, "lookup": RiskLevel.READ}, owner_reviewed=True
        )
        self.plugins.connect("knowledge")
        delayed = self.invoke("knowledge", "delay", {"seconds": 30})
        self.assertFalse(delayed.result.success)
        self.assertEqual("mcp_timeout", delayed.result.error)
        self.assertTrue(
            self.invoke("knowledge", "lookup", {"topic": "after-timeout"}).result.success
        )
        failures = []

        def invoke():
            try:
                self.invoke("knowledge", "delay", {"seconds": 30})
            except Cancelled:
                failures.append("cancelled")

        worker = threading.Thread(target=invoke)
        worker.start()
        time.sleep(0.3)
        self.store.put("task", self.task.id, record(replace(self.task, cancelled=True)))
        worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(["cancelled"], failures)
        self.plugins.disconnect("knowledge")
        self.store.put("task", self.task.id, record(self.task))
        self.plugins.connect("knowledge")
        self.assertTrue(
            self.invoke("knowledge", "lookup", {"topic": "after-reconnect"}).result.success
        )

    def test_real_schema_change_and_fresh_core_recovery(self):
        marker = self.root / "schema-change"
        config = self.config("knowledge", "mcp_changing.py", str(marker))
        self.plugins.register(config, {"lookup": RiskLevel.READ}, owner_reviewed=True)
        self.plugins.connect("knowledge")
        self.assertTrue(self.invoke("knowledge", "lookup", {"topic": "original"}).result.success)
        self.plugins.disconnect("knowledge")
        marker.touch()
        with self.assertRaises(PermissionError):
            self.plugins.connect("knowledge")
        self.assertEqual({}, self.plugins.sessions)
        program = (
            "from pathlib import Path;from oscar.storage import Store;"
            "from oscar.connectors import ConnectorFabric,EnvironmentSecrets;"
            "from oscar.policy import PersonalPolicy;from oscar.mcp_client import MCPPlugins;"
            f"s=Store(Path({str(self.root / 'core.sqlite')!r}));"
            "f=ConnectorFabric(s,EnvironmentSecrets({}),PersonalPolicy(s));p=MCPPlugins(s,f);"
            "assert not p.sessions;assert p.snapshot()[0]['health']=='disconnected';s.close()"
        )
        subprocess.run([sys.executable, "-c", program], check=True, timeout=10)

    def test_case_sensitive_tools_and_two_accounts_same_tool(self):
        self.plugins.register(
            self.config("knowledge", "mcp_knowledge.py", "knowledge"),
            {"lookup": RiskLevel.READ, "MixedCase": RiskLevel.READ},
            owner_reviewed=True,
        )
        self.plugins.register(
            self.config("writer", "mcp_knowledge.py", "writer"),
            {"lookup": RiskLevel.READ},
            owner_reviewed=True,
        )
        self.plugins.connect("knowledge")
        self.plugins.connect("writer")
        first = self.invoke("knowledge", "lookup", {"topic": "same"})
        second = self.invoke("writer", "lookup", {"topic": "same"})
        self.assertEqual("knowledge", first.payload["structuredContent"]["account_id"])
        self.assertEqual("writer", second.payload["structuredContent"]["account_id"])
        self.assertNotEqual(
            first.payload["structuredContent"]["pid"], second.payload["structuredContent"]["pid"]
        )
        self.assertTrue(self.invoke("knowledge", "MixedCase", {"topic": "case"}).result.success)

    def test_trusted_cli_review_digest_before_registration(self):
        from oscar.accounts import AccountRegistry

        account = AccountRegistry(self.store).add(
            "mcp-fixture", "synthetic", "cli", "CLI fixture", verified=True
        )
        config = replace(
            self.config("knowledge", "mcp_knowledge.py", "knowledge"),
            account_id=account.id,
            account_generation=account.generation,
        )
        registration = self.root / "registration.json"
        registration.write_text(
            json.dumps({"config": asdict(config), "reviewed": {"lookup": ["read"]}})
        )
        command = [
            sys.executable,
            "-m",
            "oscar.mcp_cli",
            "--state",
            str(self.root / "core.sqlite"),
            "register",
            "--registration",
            str(registration),
        ]
        preview = json.loads(subprocess.check_output(command, text=True, timeout=10))
        self.assertTrue(preview["review_required"])
        self.assertEqual([], self.plugins.snapshot())
        accepted = json.loads(
            subprocess.check_output(
                [*command, "--approve-digest", preview["digest"]], text=True, timeout=10
            )
        )
        self.assertEqual("disconnected", accepted["health"])
        self.assertEqual("knowledge", self.plugins.snapshot()[0]["id"])

    def test_unexpected_process_loss_withdraws_live_capabilities(self):
        config = self.config("knowledge", "mcp_knowledge.py", "knowledge")
        self.plugins.register(config, {"lookup": RiskLevel.READ}, owner_reviewed=True)
        self.plugins.connect("knowledge")
        pid = self.invoke("knowledge", "lookup", {"topic": "process"}).payload["structuredContent"][
            "pid"
        ]
        self.assertNotEqual(os.getpid(), pid)
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 3
        while self.fabric.capabilities("node") and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertEqual([], self.fabric.capabilities("node"))
        self.assertEqual("disconnected", self.plugins.inspect("knowledge")["health"])

    def test_failed_connect_cannot_restore_removed_installation(self):
        config = self.config("knowledge", "mcp_knowledge.py", "knowledge")
        self.plugins.register(config, {"lookup": RiskLevel.READ}, owner_reviewed=True)

        def removed(*args):
            self.store.delete("mcp_installation", config.id)
            raise OSError("synthetic launch failure after concurrent removal")

        with patch("oscar.mcp_client.MCPClient", side_effect=removed):
            with self.assertRaises(OSError):
                self.plugins.connect(config.id)
        with self.assertRaises(KeyError):
            self.store.get("mcp_installation", config.id)
        self.assertNotIn(config.id, self.plugins.sessions)
        self.assertEqual([], self.fabric.capabilities("node"))


class DestinationTests(unittest.TestCase):
    def test_local_metadata_redirect_credentials_denied(self):
        for url in (
            "http://127.0.0.1/mcp",
            "https://169.254.169.254/mcp",
            "https://user:secret@example.com/mcp",
            "file:///private",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_destination(url)
        self.assertEqual(
            ("http://127.0.0.1:5678", "127.0.0.1"),
            validate_destination("http://127.0.0.1:5678/mcp", "http://127.0.0.1:5678"),
        )

    def test_schema_refs_and_dns_rebinding_denied(self):
        from oscar.connectors import ConnectorError

        for key in ("$ref", "$dynamicRef", "$recursiveRef"):
            with self.assertRaises(ConnectorError):
                validate_schema({"type": "object", key: "https://169.254.169.254/private"})
        with (
            patch(
                "socket.getaddrinfo",
                return_value=[
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
                ],
            ),
            self.assertRaises(ValueError),
        ):
            validate_destination("https://rebound.example/mcp")


if __name__ == "__main__":
    unittest.main()
