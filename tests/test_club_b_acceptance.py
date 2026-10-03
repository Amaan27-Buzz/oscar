"""Genuine subprocess/network acceptances run in CI without credentials or user hardware."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.verify_club_b import run_integrated
from scripts.verify_worker_reference import run_reference


class ClubBAcceptanceTests(unittest.TestCase):
    def test_separate_process_network_worker_continuation(self):
        with TemporaryDirectory() as temporary:
            report = run_reference(Path(temporary))
        self.assertEqual("VERIFIED", report["status"])
        self.assertIn("reference network Worker verification", report["scope"])

    def test_integrated_worker_policy_memory_live_context(self):
        with TemporaryDirectory() as temporary:
            report = run_integrated(Path(temporary))
        self.assertEqual("VERIFIED", report["status"])
        self.assertEqual("PARTIAL", report["gate_b"])
