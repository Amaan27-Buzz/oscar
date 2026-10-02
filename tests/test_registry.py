import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oscar.registry import Registry


class RegistryBoundaryTests(unittest.TestCase):
    def test_endpoints_do_not_contain_credentials_and_local_flags_are_enforced(self):
        data = json.loads(Path("config/local-template.json").read_text())
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            for change in (
                {"base_url": "https://example.com/v1", "local": True},
                {"base_url": "https://user:password@example.com/v1"},
                {"base_url": "http://example.com/v1", "local": False},
                {"local": "false"},
                {"base_url": "http://127.0.0.1/v1?api_key=synthetic"},
            ):
                manifest = {**data, "providers": [{**data["providers"][0], **change}], "models": []}
                path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    Registry.load(path)

    def test_local_runtime_template_is_disabled_and_has_no_assumed_models(self):
        registry = Registry.load(Path("config/local-template.json"))
        self.assertEqual(registry.models, {})
        self.assertTrue(all(not p.enabled for p in registry.providers.values()))
