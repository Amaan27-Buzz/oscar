"""Privacy-safe bounded failure receipts must not become unauthenticated DB writes."""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import FAILURE_CATEGORIES, CloudHTTPServer
from tests.test_cloud import configuration, request


class CloudDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.config = CloudConfig.load(configuration(Path(temp.name)))
        self.core = CloudCore(self.config, initialize=True, start_services=False)
        self.addCleanup(self.core.close)
        self.server = CloudHTTPServer(self.core)
        self.server.start()
        self.addCleanup(self.server.close)

    def test_suppression_capped_counters_and_fixed_categories(self):
        with patch("oscar.cloud.diagnostic") as diagnostic:
            with patch("oscar.cloud_http.monotonic", side_effect=[1000, 1001, 1060, 1061]):
                self.server.observe_failure(400)
                self.server.observe_failure(400)
                self.server.observe_failure(400)
                self.server.failure_counts["invalid_request"] = 2**31 - 1
                self.server.observe_failure(400)
            self.assertEqual(2**31 - 1, self.server.failure_counts["invalid_request"])
            self.assertEqual(
                [
                    {"category": "invalid_request", "count": 1},
                    {"category": "invalid_request", "count": 3},
                ],
                [call.kwargs for call in diagnostic.call_args_list],
            )
            with patch("oscar.cloud_http.monotonic", return_value=1100):
                for code in range(400, 600):
                    self.server.observe_failure(code)
                self.server.handle_error(object(), ("private-address", 1234))
            self.assertLessEqual(len(self.server.failure_counts), len(FAILURE_CATEGORIES) + 1)
            self.assertLessEqual(len(self.server.failure_reported), len(FAILURE_CATEGORIES) + 1)
            self.assertEqual(2, self.server.failure_counts["internal_error"])

    def test_invalid_pressure_is_sanitized_without_canonical_writes(self):
        store = self.core.harness.store

        def state_counts():
            return tuple(
                store.db.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
                for name in ("records", "audit", "nonces")
            )

        before = state_counts()
        private = "synthetic-private-request-must-not-be-logged"
        captured = io.StringIO()
        with redirect_stdout(captured), patch("oscar.cloud_http.monotonic", return_value=1000):
            for _ in range(20):
                self.assertEqual(
                    401,
                    request(
                        self.config,
                        "/v2/grid/request",
                        body={"text": private},
                        headers={"Content-Type": "application/json", "Authorization": private},
                    )[0],
                )
            self.assertEqual(404, request(self.config, "/" + private)[0])
        self.assertEqual(before, state_counts())
        self.assertFalse(self.server.grid_arrivals)
        self.assertFalse(self.server.client_arrivals)
        self.assertEqual(20, self.server.failure_counts["authentication_denied"])
        self.assertNotIn(private, captured.getvalue())
        receipts = [json.loads(line) for line in captured.getvalue().splitlines()]
        self.assertEqual(2, len(receipts))
        for receipt in receipts:
            self.assertEqual({"event", "category", "count"}, set(receipt))
            self.assertEqual("http_request_failed", receipt["event"])
