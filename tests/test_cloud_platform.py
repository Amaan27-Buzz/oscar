"""Real shared Core composition and bounded, read-only Linux secret injection."""

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oscar.cloud import CloudConfig
from oscar.credentials import redact_runtime_secrets
from oscar.grid import NodeRole
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.secure_credentials import InjectedCredentialStore
from oscar.storage import StateConflict
from tests.test_cloud import configuration


class CloudPlatformTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.secrets = self.root / "secrets"
        self.secrets.mkdir(mode=0o700)
        self.vault = InjectedCredentialStore(self.secrets, clock=lambda: 100)

    def test_proxy_configuration_requires_packaged_core_port_before_initialization(self):
        for host in ("127.0.0.1", "0.0.0.0"):
            with self.subTest(host=host):
                path = configuration(
                    self.root, listen_host=host, listen_port=8081, ingress="tls-proxy"
                )
                with self.assertRaisesRegex(ValueError, "listen_port 8080"):
                    CloudConfig.load(path)
                self.assertFalse((self.root / "data").exists())
                path = configuration(
                    self.root, listen_host=host, listen_port=8080, ingress="tls-proxy"
                )
                self.assertEqual(8080, CloudConfig.load(path).listen_port)

    def test_separate_loopback_configuration_supports_explicit_alternative_port(self):
        path = configuration(self.root, listen_port=8081, ingress="loopback")
        config = CloudConfig.load(path)
        self.assertEqual("127.0.0.1", config.listen_host)
        self.assertEqual(8081, config.listen_port)
        path = configuration(self.root, listen_host="0.0.0.0", ingress="loopback")
        with self.assertRaisesRegex(ValueError, "non-loopback Core"):
            CloudConfig.load(path)

    def secret(self, reference="provider", value="synthetic-private-value", expiry=None):
        path = self.secrets / reference
        path.write_text(json.dumps({"secret": value, "expires_at": expiry}), encoding="utf-8")
        path.chmod(0o600)
        return path

    def test_mount_replacement_removal_expiry_and_redaction(self):
        path = self.secret()
        value = self.vault.read("provider")
        self.assertEqual("synthetic-private-value", value.value)
        self.assertNotIn(value.value, repr(value))
        self.assertNotIn(value.value, str(value))
        self.secret(value="synthetic-replacement")
        self.assertEqual("synthetic-replacement", self.vault.read("provider").value)
        self.secret(expiry=99)
        with self.assertRaises(PermissionError):
            self.vault.read("provider")
        self.assertEqual(value.value, self.vault.read("provider", allow_expired=True).value)
        path.unlink()
        with self.assertRaises(KeyError):
            self.vault.read("provider")
        self.assertEqual("<redacted>", redact_runtime_secrets(value.value))

    def test_mount_does_not_enroll_or_revoke_credentials(self):
        self.secret()
        with self.assertRaises(PermissionError):
            self.vault.put("synthetic", reference="provider")
        with self.assertRaises(PermissionError):
            self.vault.delete("provider")
        self.assertEqual("synthetic-private-value", self.vault.read("provider").value)

    def test_strict_references_schema_and_payload_bound(self):
        for reference in ("../provider", "/provider", "x/y", "", "a" * 129):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                self.vault.read(reference)
        path = self.secret()
        for payload in (
            "x",
            "{}",
            '{"secret": "synthetic", "expires_at": true}',
            '{"secret": "synthetic", "expires_at": NaN}',
            '{"secret": 123, "expires_at": null}',
            '{"secret": "", "expires_at": null}',
            '{"secret": "synthetic", "expires_at": -1}',
            "x" * 4097,
        ):
            with self.subTest(payload=payload[:32]), self.assertRaises(ValueError):
                path.write_text(payload, encoding="utf-8")
                self.vault.read("provider")

    @unittest.skipUnless(os.name == "posix", "POSIX owner/mode and symlink enforcement")
    def test_private_modes_and_regular_files_required(self):
        path = self.secret()
        path.chmod(0o644)
        with self.assertRaises(PermissionError):
            self.vault.read("provider")
        path.chmod(0o600)
        link = self.secrets / "alias"
        link.symlink_to(path)
        with self.assertRaises(PermissionError):
            self.vault.read("alias")
        self.secrets.chmod(0o755)
        with self.assertRaises(PermissionError):
            InjectedCredentialStore(self.secrets)
        self.secrets.chmod(0o700)

    def test_shared_core_injections_keep_native_capabilities_unavailable(self):
        self.secret()
        with (
            patch.dict(os.environ, {"GROQ_API_KEY_1": "ambient", "TAVILY_API_KEY_1": "ambient"}),
            Harness(
                self.root / "core.sqlite",
                self.root / "files",
                Path("config/development-models.json"),
                node_id="persistent-cloud",
                credential_environ={},
                vault=self.vault,
            ) as h,
        ):
            self.assertEqual("persistent-cloud", h.node_id)
            self.assertIs(h.runtime.setup.vault, self.vault)
            self.assertFalse(h.pool.slots["groq-1"].present)
            self.assertFalse(h.search.pool.slots["tavily-1"].present)
            self.assertEqual(
                {"files.write", "math.add", "models.reason", "sources.retrieve"},
                set(h.dispatcher.executors),
            )
            self.assertIs(h.archive, h.runtime.memory.archive)
            self.assertIs(h.executive, h.runtime.executive)
            self.assertEqual(NodeRole.CLOUD, h.store.get("node", h.node_id)["role"])
            task = h.runtime.create(Intent("2 + 3", "addition"))
            result = h.runtime.run(task.id, {h.node_id: (h.dispatcher, h.session)})
            self.assertEqual("verified", result.state)
        self.assertFalse(h.execution_session.thread.is_alive())
        self.assertFalse(h.executive.thread.is_alive())
        self.assertFalse(h.world.thread.is_alive())

    def test_deferred_services_can_close_without_start_or_start_once(self):
        arguments = (
            self.root / "core.sqlite",
            self.root / "files",
            Path("config/development-models.json"),
        )
        with Harness(*arguments, credential_environ={}, start_services=False) as h:
            self.assertFalse(h.execution_session.thread.is_alive())
            self.assertIsNone(h.world.thread)
            self.assertIsNone(h.executive.thread)
        with Harness(*arguments, credential_environ={}, start_services=False) as h:
            h.start()
            self.assertTrue(h.execution_session.thread.is_alive())
            self.assertTrue(h.world.thread.is_alive())
            self.assertTrue(h.executive.thread.is_alive())
            with self.assertRaises(StateConflict):
                h.start()


if __name__ == "__main__":
    unittest.main()
