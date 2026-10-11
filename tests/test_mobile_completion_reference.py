"""Actual isolated HTTP/Core/Grid reference, no owner authorization claim."""

import importlib.util
import unittest

from scripts.mobile_completion_reference import run


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "optional reference RSA executor")
class MobileCompletionReferenceTests(unittest.TestCase):
    def test_real_http_readback_desktop_origin_and_denial(self):
        report = run()
        self.assertTrue(report["http_core_math_readback"])
        self.assertTrue(report["desktop_origin_shared_task"])
        self.assertTrue(report["signed_reference_denial_without_execution"])
        self.assertEqual(report["owner_biometric_pin"], "NOT_RUN")
