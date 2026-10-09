"""Offline capture inventory contracts; pixels are not compared to golden screenshots."""

import hashlib
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopBaselineTests(unittest.TestCase):
    def test_complete_baseline_manifest_matches_pngs(self) -> None:
        folder = ROOT / "docs/ui/desktop/baseline"
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        images = manifest["images"]
        required = {
            0,
            1,
            2,
            3,
            *range(10, 16),
            *range(20, 25),
            *range(30, 35),
            *range(40, 46),
            *range(50, 53),
            *range(60, 63),
            *range(70, 77),
            80,
            81,
            *range(90, 96),
        }
        self.assertTrue(required <= {int(e["file"].split("-")[0]) for e in images})
        self.assertEqual(len(images), len({e["file"] for e in images}))
        self.assertEqual({e["file"] for e in images}, {p.name for p in folder.glob("*.png")})
        for entry in images:
            raw = (folder / entry["file"]).read_bytes()
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(
                struct.unpack(">II", raw[16:24]),
                (entry["physical_width"], entry["physical_height"]),
            )
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
            self.assertTrue(entry["fixture_source"])
            self.assertIn(entry["capture"], {"automated", "manual"})
            self.assertTrue(entry["evidence"].startswith(("SIMULATED", "REFERENCE", "EMULATED")))
        self.assertEqual(
            manifest["canonical_orb_sha256"],
            hashlib.sha256((ROOT / "assets/brand/oscar-orb.svg").read_bytes()).hexdigest(),
        )

    def test_manifest_has_no_production_credential_fields(self) -> None:
        text = (ROOT / "docs/ui/desktop/baseline/manifest.json").read_text(encoding="utf-8")
        for field in ('"token"', '"private_key"', '"signing_payload"', '"session"', '"password"'):
            self.assertNotIn(field, text)
