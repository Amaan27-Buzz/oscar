import base64
import json
import os
import secrets
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_state import backup_state, restore_state
from oscar.encrypted_credentials import EncryptedCredentialStore
from tests.test_cloud import configuration
from tests.test_connections import PrivateVault


class EncryptedCredentialTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.key = secrets.token_bytes(32)
        self.fallback = PrivateVault()
        self.vault = EncryptedCredentialStore(self.root / "vault", self.key, self.fallback)

    def test_large_token_survives_restart_without_plaintext_file_content(self):
        secret = "synthetic-large-access-token-" * 250
        reference = self.vault.put(secret)
        encrypted = (self.root / "vault" / reference).read_bytes()
        self.assertNotIn(secret[:50].encode(), encrypted)
        restored = EncryptedCredentialStore(self.root / "vault", self.key, self.fallback)
        self.assertEqual(secret, restored.read(reference).value)
        self.assertEqual("<redacted>", str(restored.read(reference)))
        restored.delete(reference)
        restored.delete(reference)
        with self.assertRaises(KeyError):
            restored.read(reference)

    def test_wrong_key_tampering_and_reference_substitution_fail_closed(self):
        reference = self.vault.put("synthetic-secret")
        path = self.root / "vault" / reference
        wrong = EncryptedCredentialStore(
            self.root / "vault", secrets.token_bytes(32), self.fallback
        )
        with self.assertRaises(PermissionError):
            wrong.read(reference)
        swapped = self.root / "vault" / "different-reference"
        swapped.write_bytes(path.read_bytes())
        swapped.chmod(0o600)
        with self.assertRaises(PermissionError):
            self.vault.read(swapped.name)
        path.write_bytes(path.read_bytes()[:-1] + b"x")
        with self.assertRaises(PermissionError):
            self.vault.read(reference)

    def test_expiry_and_opaque_paths_are_enforced(self):
        reference = self.vault.put("expired", expires_at=time() - 1)
        with self.assertRaises(PermissionError):
            self.vault.read(reference)
        self.assertEqual("expired", self.vault.read(reference, allow_expired=True).value)
        for invalid in ("../outside", "a/b", "", "a" * 129):
            with self.assertRaises(ValueError):
                self.vault.put("secret", reference=invalid)
        for expiry in (True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.vault.put("secret", expires_at=expiry)

    def test_cloud_composition_requires_key_and_persists_writable_account_vault(self):
        auth = self.root / "oauth.json"
        auth.write_text(
            json.dumps(
                {
                    "version": 1,
                    "providers": [
                        {
                            "provider": "google",
                            "client_id": "synthetic-client",
                            "redirect_uri": "http://127.0.0.1:48123/oauth/callback",
                            "service": "google.calendar",
                            "audience": "https://www.googleapis.com/",
                            "allowed_scopes": [
                                "openid",
                                "https://www.googleapis.com/auth/calendar.readonly",
                            ],
                        }
                    ],
                }
            )
        )
        with self.assertRaises(ValueError):
            CloudConfig.load(configuration(self.root, auth_config=str(auth)))
        config = CloudConfig.load(
            configuration(self.root, auth_config=str(auth), credential_key_ref="account-key")
        )
        key = config.secret_dir / "account-key"
        key.write_text(
            json.dumps({"secret": base64.b64encode(self.key).decode(), "expires_at": None})
        )
        key.chmod(0o600)
        with closing(CloudCore(config, initialize=True, start_services=False)) as core:
            self.assertEqual("google", core.harness.auth.catalog()[0]["provider"])
            reference = core.harness.auth.vault.put("synthetic-account-token")
        backup_state(config.data_dir, self.root / "backup")
        restore_state(self.root / "backup", self.root / "restored")
        restored = EncryptedCredentialStore(
            self.root / "restored/account-credentials", self.key, self.fallback
        )
        self.assertEqual("synthetic-account-token", restored.read(reference).value)
        with closing(CloudCore(config, start_services=False)) as core:
            self.assertEqual(
                "synthetic-account-token", core.harness.auth.vault.read(reference).value
            )
            core.harness.auth.vault.delete(reference)

    @unittest.skipIf(os.name == "nt", "POSIX permissions and unprivileged symlinks")
    def test_public_files_and_symlink_substitution_are_rejected(self):
        reference = self.vault.put("synthetic-private-token")
        path = self.root / "vault" / reference
        path.chmod(0o644)
        with self.assertRaises(PermissionError):
            self.vault.read(reference)
        path.chmod(0o600)
        target = self.root / "outside"
        target.write_bytes(path.read_bytes())
        target.chmod(0o600)
        path.unlink()
        path.symlink_to(target)
        with self.assertRaises(PermissionError):
            self.vault.read(reference)
        with self.assertRaises(PermissionError):
            self.vault.put("replacement", reference=reference)
        self.assertTrue(target.exists())
