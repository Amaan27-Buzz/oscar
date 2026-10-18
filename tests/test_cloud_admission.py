import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from unittest.mock import patch

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import CloudHTTPServer
from tests.test_cloud import configuration, enroll, request


class CloudAdmissionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.config = CloudConfig.load(configuration(Path(temp.name)))
        self.core = CloudCore(self.config, initialize=True)
        self.addCleanup(self.core.close)
        self.session = enroll(self.core)
        self.server = CloudHTTPServer(self.core)
        self.server.start()
        self.addCleanup(self.server.close)

    def test_unauthenticated_pressure_preserves_authenticated_allowance(self):
        with patch.object(
            self.core.harness.grid,
            "authenticate",
            wraps=self.core.harness.grid.authenticate,
        ) as authenticate:
            for _ in range(121):
                self.assertEqual(401, request(self.config, "/v1/status")[0])
                self.assertEqual(
                    401,
                    request(
                        self.config,
                        "/v1/status",
                        session=self.session,
                        headers={"Authorization": "Bearer malformed"},
                    )[0],
                )
            self.assertFalse(
                any(call.args[0].id == self.session.id for call in authenticate.call_args_list)
            )
        for _ in range(121):
            self.assertEqual(
                401,
                request(
                    self.config,
                    "/v1/status",
                    session=self.session,
                    headers={"Authorization": "Bearer " + "x" * 43},
                )[0],
            )
        self.assertFalse(self.server.arrivals)
        self.assertFalse(self.server.client_arrivals)
        self.assertEqual(200, request(self.config, "/v1/status", session=self.session)[0])

    def test_authenticated_node_limit_leaves_capacity_for_another_client(self):
        other = enroll(self.core, name="synthetic-second")
        with self.server.rate_lock:
            self.server.arrivals.extend([monotonic()] * 60)
            self.server.client_arrivals[self.session.node_id] = self.server.arrivals.copy()
        self.assertEqual(429, request(self.config, "/v1/status", session=self.session)[0])
        self.assertEqual(
            0, self.core.harness.store.db.execute("SELECT COUNT(*) FROM nonces").fetchone()[0]
        )
        self.assertEqual(200, request(self.config, "/v1/status", session=other)[0])
        self.assertEqual(61, len(self.server.arrivals))

    def test_shared_bound_and_expired_client_buckets(self):
        with self.server.rate_lock:
            self.server.arrivals.extend([monotonic()] * 120)
        self.assertEqual(429, request(self.config, "/v1/status", session=self.session)[0])
        self.assertFalse(self.server.client_arrivals)
        with self.server.rate_lock:
            self.server.arrivals.clear()
            self.server.arrivals.append(monotonic() - 61)
            self.server.client_arrivals["expired-client"] = self.server.arrivals.copy()
        self.assertEqual(200, request(self.config, "/v1/status", session=self.session)[0])
        self.assertNotIn("expired-client", self.server.client_arrivals)
