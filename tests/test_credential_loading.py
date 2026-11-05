"""Legacy configuration stays byte-for-byte intact and outside child process env."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from oscar.credential_loading import existing_provider_environment, import_missing_vault_bindings
from oscar.models import ProviderSpec


class ExistingConfigurationTests(unittest.TestCase):
    def test_secure_import_preserves_existing_and_revoked_bindings(self):
        from tests.test_setup_runtime import SetupTests

        fixture = SetupTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        setup = fixture.setup
        spec = ProviderSpec(
            "fixture", "openai", "https://example.test", {"fixture-slot": "FIXTURE"}
        )
        import_missing_vault_bindings(setup, [spec], {"FIXTURE": "synthetic-first"})
        import_missing_vault_bindings(setup, [spec], {"FIXTURE": "synthetic-replacement"})
        self.assertEqual(fixture.pool.secret_for_adapter("fixture-slot"), "synthetic-first")
        setup.revoke_provider("fixture-slot", owner_authorized=True)
        import_missing_vault_bindings(setup, [spec], {"FIXTURE": "synthetic-replacement"})
        self.assertEqual(fixture.pool.secret_for_adapter("fixture-slot"), "")

    def test_only_registered_credentials_load_without_interpolation_or_mutation(self):
        provider = ProviderSpec(
            "fixture", "openai", "https://example.test", {"slot": "FIXTURE_KEY"}
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing-config"
            original = b'FIXTURE_KEY="synthetic-${UNCHANGED}"\r\nOTHER=not-a-provider\r\n'
            path.write_bytes(original)
            with patch.dict(os.environ, {"UNCHANGED": "expanded"}, clear=True):
                loaded = existing_provider_environment(path, [provider])
                self.assertEqual(loaded, {"FIXTURE_KEY": "synthetic-${UNCHANGED}"})
                self.assertNotIn("FIXTURE_KEY", os.environ)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_missing_configuration_does_not_create_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "absent"
            self.assertEqual(existing_provider_environment(path, []), {})
            self.assertFalse(path.exists())
