"""Independent artifact verification for the isolated 10R.1 presentation study."""

import hashlib
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopPresenceTests(unittest.TestCase):
    def test_nine_captures_match_identity_dimensions_and_hashes(self) -> None:
        folder = ROOT / "docs/ui/desktop/explorations/10R.1"
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        images = manifest["images"]
        self.assertEqual(
            {(e["concept"], e["state"]) for e in images},
            {(c, s) for c in "abc" for s in ("idle", "active", "offline")},
        )
        self.assertEqual(len(images), 9)
        for entry in images:
            raw = (folder / entry["file"]).read_bytes()
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(
                struct.unpack(">II", raw[16:24]),
                (entry["logical_width"], entry["logical_height"]),
            )
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
        self.assertEqual(
            manifest["canonical_orb_sha256"],
            hashlib.sha256((ROOT / "assets/brand/oscar-orb.svg").read_bytes()).hexdigest(),
        )
        self.assertEqual(manifest["native_windows_acceptance"], "NOT_RUN")
        self.assertEqual(manifest["page_errors"], [])
        self.assertEqual(manifest["external_requests"], [])
        self.assertTrue((folder / "contact-sheet.png").is_file())
        self.assertTrue((folder / manifest["preview"]).is_file())
