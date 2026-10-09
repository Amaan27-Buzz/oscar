"""Independent identity/provenance checks for the owner-review capture packet."""

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LivingReviewTests(unittest.TestCase):
    def test_artifact_hashes_and_evidence_boundaries(self) -> None:
        folder = ROOT / "docs/ui/desktop/presence"
        receipt = json.loads((folder / "receipt.json").read_text())
        entries = receipt["files"]
        self.assertEqual(
            {e["file"] for e in entries},
            {p.name for p in folder.iterdir() if p.suffix in {".png", ".gif"}},
        )
        for entry in entries:
            self.assertEqual(
                hashlib.sha256((folder / entry["file"]).read_bytes()).hexdigest(), entry["sha256"]
            )
        self.assertEqual(
            hashlib.sha256((ROOT / "assets/brand/oscar-orb.svg").read_bytes()).hexdigest(),
            receipt["canonical_svg_sha256"],
        )
        self.assertTrue(
            all(
                e["evidence"] == "SYNTHETIC_STATE_REAL_CHROMIUM_RENDER"
                for e in receipt["browser"]["images"]
            )
        )
        self.assertEqual(receipt["native"]["owner_acceptance"], "NOT RUN")
        self.assertEqual(receipt["native"]["physical_voice"], "NOT RUN")
        self.assertEqual(receipt["native"]["compact"]["logical_width"], 132)
        self.assertEqual(receipt["native"]["expanded"]["logical_height"], 384)


if __name__ == "__main__":
    unittest.main()
