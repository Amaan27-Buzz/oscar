"""Current OSCAR roadmap/document entrypoint consistency (historical evidence untouched)."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class CanonicalSliceDocumentationTests(unittest.TestCase):
    def test_roadmap_has_exactly_one_active_numbered_slice_00_through_20(self) -> None:
        roadmap = read("docs/ROADMAP.md")
        active = roadmap.split("## Review clubs / checkpoints", 1)[0]
        identifiers = [int(n) for n in re.findall(r"^## Slice (\d{2}) —", active, re.M)]
        self.assertEqual(identifiers, list(range(21)))

    def test_expression_and_ui_dependencies(self) -> None:
        expression = read("docs/EXPRESSION-CORE.md")
        for required in ("## 11.1", "## 11.2", "## 11.3", "Slice 12", "Slice 13"):
            self.assertIn(required, expression)
        self.assertIn("## Slice 12", read("docs/ROADMAP.md"))
        self.assertIn("## Slice 13", read("docs/ROADMAP.md"))
        self.assertIn("## Slice 16", read("docs/ROADMAP.md"))
        self.assertIn("Slice 20 Unified Alpha", read("docs/POST-ALPHA-EVOLUTION.md"))

    def test_active_entrypoints_link_canonical_plan(self) -> None:
        for filename in (
            "README.md",
            "AGENTS.md",
            "docs/PRODUCT.md",
            "docs/ARCHITECTURE.md",
            "docs/AGENT-CONTEXT.md",
            "docs/BUILD-GATES.md",
            "DESIGN.md",
            "TASTE.md",
            "docs/MOBILE-UI-REDESIGN.md",
            "docs/UI-AVATAR.md",
            "skills/oscar-ui/SKILL.md",
            "skills/oscar-slice/SKILL.md",
        ):
            with self.subTest(path=filename):
                self.assertIn("SLICE-NUMBERING.md", read(filename))

    def test_old_current_checkpoint_not_authoritative(self) -> None:
        for filename in (
            "README.md",
            "AGENTS.md",
            "docs/PRODUCT.md",
            "docs/ARCHITECTURE.md",
            "docs/BUILD-GATES.md",
            "docs/AGENT-CONTEXT.md",
            "docs/DECISIONS.md",
            "docs/POST-ALPHA-EVOLUTION.md",
        ):
            with self.subTest(path=filename):
                self.assertNotIn("## Current Slice 09 — 2026-10-06", read(filename))
        self.assertIn("Historical", read("docs/SLICE-NUMBERING.md"))


if __name__ == "__main__":
    unittest.main()
