import base64
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.connections import Connections, snapshot
from oscar.connectors import CredentialRef
from oscar.harness import Harness
from oscar.secure_credentials import SecretValue, WindowsCredentialStore
from oscar.storage import Store


class PrivateVault:
    def __init__(self):
        self.values = {}

    def put(self, secret, *, expires_at=None, reference=None):
        self.values[reference] = secret
        return reference

    def read(self, reference, *, allow_expired=False):
        return SecretValue(self.values[reference])

    def delete(self, reference):
        self.values.pop(reference, None)


class ConnectionManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.vault = PrivateVault()
        self.h = Harness(
            root / "state.sqlite",
            root / "files",
            Path("config/development-models.json"),
            start_services=False,
            vault=self.vault,
        )
        self.addCleanup(self.h.close)
        self.manager = Connections(self.h)
        self.account = self.h.accounts.add("fixture", "tenant", "a", "Original", verified=True)
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public = base64.b64encode(
            self.key.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode()
        self.scope = "grid:approve"
        self.grants = frozenset({self.scope})

    def review(self, operation="rename_account", value="Renamed", identifier=None):
        return self.manager.challenge(
            "owner-node",
            "session",
            self.scope,
            self.grants,
            {
                "operation": operation,
                "id": identifier or self.account.id,
                "value": value,
            },
        )

    def signed(self, review):
        signature = self.key.sign(
            base64.b64decode(review["signing_payload"]),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        return {
            "challenge_id": review["challenge_id"],
            "signature": base64.b64encode(signature).decode(),
        }

    def complete(self, review, **changes):
        return self.manager.complete(
            "owner-node",
            "session",
            self.public,
            self.scope,
            self.grants,
            {**self.signed(review), **changes},
        )

    def test_exact_signed_review_updates_real_registry_and_blocks_replay(self):
        review = self.review()
        self.assertEqual("Original", self.h.accounts.get(self.account.id).alias)
        result = self.complete(review)
        self.assertEqual("Renamed", result["connections"]["accounts"][0]["alias"])
        with self.assertRaises(PermissionError):
            self.complete(review)

    def test_native_snapshot_bounds_metadata_and_marks_omissions(self):
        for index in range(100):
            self.h.accounts.add("fixture", "tenant", str(index), "A" * 500, verified=True)
        projected = snapshot(self.h)
        self.assertLessEqual(len(json.dumps(projected).encode()), 40_000)
        self.assertTrue(projected["truncated"])
        self.assertEqual(101, projected["accounts_total"])
        self.assertLess(len(projected["accounts"]), projected["accounts_total"])

    def test_changed_account_expiry_session_and_forged_signature_deny(self):
        review = self.review()
        self.h.accounts.rename(self.account.id, "Other")
        with self.assertRaises(PermissionError):
            self.complete(review)
        review = self.review()
        with self.assertRaises(PermissionError):
            self.complete(review, signature=base64.b64encode(b"forged").decode())
        with self.assertRaises(PermissionError):
            self.manager.complete(
                "owner-node",
                "other-session",
                self.public,
                self.scope,
                self.grants,
                self.signed(review),
            )

    def test_disable_preserves_remote_revocation_unknown_and_no_credentials_in_snapshot(self):
        self.h.accounts.bind(
            self.account.id,
            "fixture",
            CredentialRef("opaque-ref"),
            ["read"],
            "https://fixture.invalid",
        )
        self.assertNotIn("opaque-ref", json.dumps(snapshot(self.h)))
        result = self.complete(self.review("disconnect_account", ""))
        account = result["connections"]["accounts"][0]
        self.assertEqual("disconnected", account["status"])
        self.assertIn("UNKNOWN", account["remote_revocation"])
        self.assertEqual("Ask", result["connections"]["access"])
        self.assertEqual("deleted", account["local_credentials"])

    def test_signed_mutation_and_review_consumption_roll_back_together(self):
        review = self.review()
        with patch.object(self.h.store, "audit", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                self.complete(review)
        self.assertEqual("Original", self.h.accounts.get(self.account.id).alias)
        self.assertFalse(self.h.store.get("connection_review", review["challenge_id"])["used"])
        self.complete(review)
        self.assertEqual("Renamed", self.h.accounts.get(self.account.id).alias)

    def bound_credentials(self):
        access, refresh = "a" * 32, "b" * 32
        self.vault.put("synthetic-access", reference=access)
        self.vault.put("synthetic-refresh", reference=refresh)
        account = self.h.accounts.bind(
            self.account.id, "fixture", CredentialRef(access), ["read"], "https://fixture.invalid"
        )
        self.h.store.put(
            "auth_broker_connection",
            "synthetic-connection",
            {
                "id": "synthetic-connection",
                "account_id": account.id,
                "generation": account.generation,
                "credential_ref": access,
                "refresh_ref": refresh,
                "state": "ready",
            },
        )
        return access, refresh

    def test_signed_disconnect_commits_fence_before_independent_vault_deletion(self):
        access, refresh = self.bound_credentials()
        original_delete = self.vault.delete

        def delete(reference):
            self.assertFalse(self.h.store.db.in_transaction)
            independent = Store(Path(self.temp.name) / "state.sqlite")
            try:
                row = independent.get("connected_account", self.account.id)
                self.assertEqual("disconnected", row["status"])
            finally:
                independent.close()
            original_delete(reference)

        with patch.object(self.vault, "delete", side_effect=delete):
            review = self.review("disconnect_account", "")
            result = self.complete(review)
        self.assertEqual("verified", result["status"])
        for reference in (access, refresh):
            with self.assertRaises(KeyError):
                self.vault.read(reference)
        self.assertIn("unknown", result["message"])
        self.assertNotIn("synthetic-access", json.dumps(result))
        self.assertNotIn("synthetic-refresh", json.dumps(self.h.store.all("connected_account")))
        with self.assertRaises(PermissionError):
            self.complete(review)

    def test_unverified_deletion_preserves_fence_and_reports_partial(self):
        self.bound_credentials()
        with patch.object(self.vault, "delete"):
            result = self.complete(self.review("disconnect_account", ""))
        self.assertEqual("partially_verified", result["status"])
        account = self.h.accounts.get(self.account.id)
        self.assertEqual("disconnected", account.status)
        self.assertEqual("deletion_failed", account.local_credentials)
        self.assertIn("could not be verified", result["message"])

    def test_unavailable_vault_reports_partial_without_restoring_account(self):
        self.h.auth = None
        result = self.complete(self.review("disconnect_account", ""))
        self.assertEqual("partially_verified", result["status"])
        self.assertEqual(
            "deletion_unavailable", self.h.accounts.get(self.account.id).local_credentials
        )

    def test_current_policy_rechecked_before_consume_or_mutation(self):
        from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule

        review = self.review()
        PersonalPolicy(self.h.store).save(
            PolicyRule("withdraw", "connections.manage", PolicyEffect.DENY, "owner", 1, 1, {}),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.complete(review)
        self.assertEqual("Original", self.h.accounts.get(self.account.id).alias)
        self.assertFalse(self.h.store.get("connection_review", review["challenge_id"])["used"])

    def plugin(self):
        from oscar.connectors import RiskLevel
        from oscar.mcp_client import MCPServerConfig, executable_digest

        command = str(Path(sys.executable).resolve())
        fixture = str(Path("tests/fixtures/mcp_knowledge.py").resolve())
        config = MCPServerConfig(
            "fixture-plugin",
            "Fixture",
            self.account.id,
            self.account.generation,
            command=command,
            arguments=("-I", fixture, self.account.id),
            cwd=self.temp.name,
            reviewed_files=(
                (command, executable_digest(command)),
                (fixture, executable_digest(fixture)),
            ),
        )
        self.h.plugins.register(config, {"lookup": RiskLevel.READ}, owner_reviewed=True)
        return config

    def test_signed_plugin_connect_runs_sdk_after_review_transaction(self):
        import threading

        config = self.plugin()
        original_connect = self.h.plugins.connect

        def connect(identifier, *, expected_config):
            self.assertEqual(config, expected_config)
            self.assertFalse(self.h.store.db.in_transaction)
            # Another thread can acquire Store's lock while SDK work is in progress.
            finished = threading.Event()
            thread = threading.Thread(
                target=lambda: (self.h.store.get("mcp_installation", identifier), finished.set())
            )
            thread.start()
            self.assertTrue(finished.wait(2))
            thread.join()
            original_connect(identifier, expected_config=expected_config)

        with patch.object(self.h.plugins, "connect", side_effect=connect):
            result = self.complete(self.review("connect_plugin", "", config.id))
        self.assertEqual("verified", result["status"])
        self.assertIn(config.id, self.h.plugins.sessions)

    def test_signed_plugin_disable_and_remove_metadata_commit_before_sdk_cleanup(self):
        config = self.plugin()
        original_disconnect = self.h.plugins.disconnect

        def disconnect(identifier, *, expected_config):
            self.assertFalse(self.h.store.db.in_transaction)
            self.assertEqual(config, expected_config)
            original_disconnect(identifier, expected_config=expected_config)

        with patch.object(self.h.plugins, "disconnect", side_effect=disconnect):
            self.complete(self.review("disable_plugin", "", config.id))
            self.assertFalse(self.h.store.get("mcp_installation", config.id)["enabled"])
            self.complete(self.review("enable_plugin", "", config.id))
            self.assertTrue(self.h.store.get("mcp_installation", config.id)["enabled"])
            self.complete(self.review("remove_plugin", "", config.id))
            with self.assertRaises(KeyError):
                self.h.store.get("mcp_installation", config.id)

    @unittest.skipUnless(os.name == "nt", "Windows native vault")
    def test_harness_native_default_signed_disconnect_deletes_synthetic_target(self):
        from uuid import uuid4

        native = Harness(
            Path(self.temp.name) / "native.sqlite",
            Path(self.temp.name) / "native-files",
            Path("config/development-models.json"),
            start_services=False,
        )
        self.addCleanup(native.close)
        self.assertIsNotNone(native.auth)
        self.assertIsInstance(native.auth.vault, WindowsCredentialStore)
        self.h, self.manager = native, Connections(native)
        self.account = native.accounts.add("fixture", "tenant", "native", "Native", verified=True)
        reference = uuid4().hex
        vault = native.auth.vault
        self.addCleanup(vault.delete, reference)
        vault.put("synthetic-native-only", reference=reference)
        native.accounts.bind(
            self.account.id, "fixture", CredentialRef(reference), ["read"], "fixture"
        )
        result = self.complete(self.review("disconnect_account", ""))
        self.assertEqual("verified", result["status"])
        self.assertEqual("deleted", native.accounts.get(self.account.id).local_credentials)
        with self.assertRaises(KeyError):
            vault.read(reference, allow_expired=True)

    def test_no_authority_or_unknown_operation_cannot_create_review(self):
        with self.assertRaises(PermissionError):
            self.manager.challenge(
                "owner-node",
                "session",
                self.scope,
                frozenset(),
                {
                    "operation": "rename_account",
                    "id": self.account.id,
                    "value": "Other",
                },
            )
        with self.assertRaises(ValueError):
            self.review("activate_full_access")


if __name__ == "__main__":
    unittest.main()
