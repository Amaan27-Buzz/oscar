import json
import socket
import unittest
from dataclasses import replace
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import CloudHTTPServer
from oscar.contracts import new_id
from oscar.grid import Node, NodeRole
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.storage import StateConflict


def configuration(root, **updates):
    secrets = root / "secrets"
    secrets.mkdir(mode=0o700, exist_ok=True)
    manifest = root / "models.json"
    manifest.write_text(json.dumps({"version": 1, "providers": [], "models": []}))
    with socket.socket() as available:
        available.bind(("127.0.0.1", 0))
        port = available.getsockname()[1]
    data = {
        "version": 1,
        "environment": "production",
        "core_id": "synthetic-cloud-core",
        "data_dir": str(root / "data"),
        "manifest": str(manifest),
        "secret_dir": str(secrets),
        "listen_host": "127.0.0.1",
        "listen_port": port,
        "ingress": "loopback",
        "allowed_hosts": ["127.0.0.1"],
        "provider_secrets": {},
        **updates,
    }
    path = root / "cloud.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def enroll(core, name="synthetic-client", scopes=None, ttl=3600):
    scopes = scopes or ("cloud:inspect", "cloud:probe", "math", "archive:retain")
    h = core.harness
    h.grid.register(Node(name, NodeRole.CLOUD, scopes))
    handle = h.grid.pair(name, scopes, ttl=ttl)
    h.store.put("cloud_client", name, {"core_id": core.config.core_id})
    return handle


def auth_headers(session, **overrides):
    return {
        "Authorization": "Bearer " + session.token,
        "X-Oscar-Node": session.node_id,
        "X-Oscar-Session": session.id,
        "X-Oscar-Nonce": new_id(),
        "X-Oscar-Time": str(time()),
        "Content-Type": "application/json",
        **overrides,
    }


def request(config, path, *, session=None, body=None, headers=None, method=None):
    connection = HTTPConnection("127.0.0.1", config.listen_port, timeout=5)
    supplied = auth_headers(session) if session else {}
    supplied.update(headers or {})
    raw = json.dumps(body).encode() if body is not None else None
    try:
        connection.request(
            method or ("POST" if body is not None else "GET"), path, body=raw, headers=supplied
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = configuration(self.root)
        self.config = CloudConfig.load(self.path)

    def start(self):
        self.core = CloudCore(self.config, initialize=True)
        self.addCleanup(self.core.close)
        self.session = enroll(self.core)
        self.server = CloudHTTPServer(self.core)
        self.server.start()
        self.addCleanup(self.server.close)

    def test_configuration_rejects_unsafe_corrupt_and_incompatible_input(self):
        original = json.loads(self.path.read_text())
        cases = [
            {"version": 2},
            {"version": True},
            {"environment": "development"},
            {"listen_host": "0.0.0.0", "ingress": "loopback"},
            {"listen_port": True},
            {"listen_port": 80},
            {"data_dir": "relative"},
            {"allowed_hosts": ["*"]},
            {"core_id": "OWNER-MUST-SUPPLY-ID"},
            {"secret_dir": original["data_dir"]},
            {"provider_secrets": {"api_key": "secret"}},
            {"unknown": "value"},
        ]
        for change in cases:
            with self.subTest(change=change):
                self.path.write_text(json.dumps({**original, **change}))
                with self.assertRaises((ValueError, TypeError)):
                    CloudConfig.load(self.path)
        self.path.write_text('{"version":1,"version":1}')
        with self.assertRaises(ValueError):
            CloudConfig.load(self.path)
        self.path.write_text('{"version":')
        with self.assertRaises(ValueError):
            CloudConfig.load(self.path)
        self.assertFalse(self.config.data_dir.exists())

    def test_real_http_core_archive_idempotency_and_degraded_retrieval(self):
        self.start()
        self.assertEqual(200, request(self.config, "/readyz")[0])
        code, view = request(self.config, "/v1/status", session=self.session)
        self.assertEqual(200, code)
        self.assertEqual("unavailable", view["memory"]["semantic"])
        self.assertEqual("unavailable", view["capabilities"]["windows_uia"])
        self.assertEqual("unavailable", view["providers"])
        body = {"request_id": new_id(), "expression": "19 + 23"}
        first = request(self.config, "/v1/probes", session=self.session, body=body)
        second = request(self.config, "/v1/probes", session=self.session, body=body)
        self.assertEqual(200, first[0], first)
        self.assertEqual(first, second)
        self.assertEqual("verified", first[1]["state"])
        self.assertEqual(42, first[1]["value"])
        h = self.core.harness
        self.assertEqual(1, len(h.store.all("task")))
        self.assertEqual(1, len(h.archive.memories(h.runtime.relationship_id)))
        self.assertEqual("19 + 23", h.archive.event(first[1]["event_id"]).content)
        self.assertTrue(h.runtime.memory.retrieve(h.runtime.relationship_id, "19").hits)
        code, _ = request(
            self.config, "/v1/probes", session=self.session, body={**body, "expression": "1 + 1"}
        )
        self.assertEqual(409, code)

    def test_invalid_revoked_expired_scope_and_replayed_credentials(self):
        self.start()
        endpoint = "/v1/status"
        self.assertEqual(401, request(self.config, endpoint)[0])
        self.assertEqual(
            401,
            request(
                self.config,
                endpoint,
                session=self.session,
                headers={"Authorization": "Bearer " + "x" * 43},
            )[0],
        )
        self.assertEqual(
            401,
            request(
                self.config,
                endpoint,
                session=self.session,
                headers={"X-Oscar-Time": str(time() - 90)},
            )[0],
        )
        replay = auth_headers(self.session)
        self.assertEqual(200, request(self.config, endpoint, headers=replay)[0])
        self.assertEqual(409, request(self.config, endpoint, headers=replay)[0])
        expired = enroll(self.core, "expired-client", ttl=0.001)
        row = self.core.harness.store.get("session", expired.id)
        self.core.harness.store.put("session", expired.id, {**row, "expires_at": time() - 1})
        self.assertEqual(401, request(self.config, endpoint, session=expired)[0])
        self.core.harness.grid.revoke(self.session.node_id)
        self.assertEqual(401, request(self.config, endpoint, session=self.session)[0])
        other = enroll(self.core, "unbound-client")
        self.core.harness.store.delete("cloud_client", other.node_id)
        self.assertEqual(401, request(self.config, endpoint, session=other)[0])

    def test_retention_grants_policy_and_cross_client_isolation(self):
        self.start()
        body = {"request_id": new_id(), "expression": "1 + 2"}
        limited = enroll(self.core, "limited-client", ("cloud:probe", "math"))
        self.assertEqual(401, request(self.config, "/v1/probes", session=limited, body=body)[0])
        code, _ = request(self.config, "/v1/probes", session=self.session, body=body)
        self.assertEqual(200, code)
        other = enroll(self.core, "another-client")
        self.assertEqual(
            401, request(self.config, "/v1/probes/" + body["request_id"], session=other)[0]
        )
        PersonalPolicy(self.core.harness.store).save(
            PolicyRule(
                "block-probe", "math.add", PolicyEffect.DENY, "synthetic test", time(), time(), {}
            ),
            owner_authorized=True,
        )
        self.assertEqual(
            401,
            request(
                self.config,
                "/v1/probes",
                session=self.session,
                body={**body, "request_id": new_id()},
            )[0],
        )

    def test_legacy_privileged_routes_limits_and_proxy_tls_fail_closed(self):
        self.start()
        for endpoint in ("/execute", "/pair", "/approve", "/mobile", "/debug", "/v1/enroll"):
            self.assertEqual(404, request(self.config, endpoint, session=self.session)[0])
        self.assertEqual(400, request(self.config, "/v1/status?token=private")[0])
        self.assertEqual(400, request(self.config, "/v1/status", headers={"Host": "evil.test"})[0])
        self.assertEqual(
            413,
            request(self.config, "/v1/probes", session=self.session, body={"padding": "x" * 5000})[
                0
            ],
        )
        self.assertEqual(
            400,
            request(
                self.config,
                "/v1/probes",
                session=self.session,
                body={"request_id": new_id(), "expression": "write file"},
            )[0],
        )
        self.core.config = replace(self.config, ingress="tls-proxy")
        self.assertEqual(401, request(self.config, "/v1/status", session=self.session)[0])
        self.assertEqual(
            200,
            request(
                self.config,
                "/v1/status",
                session=self.session,
                headers={"X-Forwarded-Proto": "https"},
            )[0],
        )
        self.server.arrivals.extend([time()] * 120)
        self.assertEqual(429, request(self.config, "/v1/status", session=self.session)[0])

    def test_shutdown_releases_resources_and_directory_lock(self):
        core = CloudCore(self.config, initialize=True)
        h = core.harness
        with self.assertRaises(StateConflict):
            CloudCore(self.config)
        core.close()
        self.assertFalse(h.execution_session.thread.is_alive())
        self.assertFalse(h.executive.thread.is_alive())
        self.assertFalse(h.world.thread.is_alive())
        restarted = CloudCore(self.config)
        restarted.close()

    def test_expired_internal_execution_is_unready_without_misreporting_client_auth(self):
        self.start()
        h = self.core.harness
        row = h.store.get("session", h.session.id)
        h.store.put("session", h.session.id, {**row, "expires_at": time() - 1})
        self.assertEqual(503, request(self.config, "/readyz")[0])
        code, status = request(self.config, "/v1/status", session=self.session)
        self.assertEqual(200, code)
        self.assertFalse(status["ready"])
        self.assertEqual("unavailable", status["capabilities"]["integer_addition"])

    def test_deep_json_and_duplicate_framing_are_rejected(self):
        self.start()
        connection = HTTPConnection("127.0.0.1", self.config.listen_port, timeout=5)
        self.addCleanup(connection.close)
        connection.request(
            "POST",
            "/v1/probes",
            body="[" * 1500 + "0" + "]" * 1500,
            headers=auth_headers(self.session),
        )
        response = connection.getresponse()
        self.assertEqual(400, response.status)
        response.read()
        connection.close()
        connection = HTTPConnection("127.0.0.1", self.config.listen_port, timeout=5)
        self.addCleanup(connection.close)
        connection.putrequest("POST", "/v1/probes")
        connection.putheader("Content-Length", "2")
        connection.putheader("Content-Length", "4")
        connection.endheaders(b"{}")
        response = connection.getresponse()
        self.assertEqual(400, response.status)
        response.read()


if __name__ == "__main__":
    unittest.main()
