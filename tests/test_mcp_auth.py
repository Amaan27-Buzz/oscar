"""Synthetic resource/AS HTTP servers; native signatures and real private vault binding."""

import hashlib
import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from oscar.auth_broker import AuthBroker
from oscar.capabilities import Cancellation
from oscar.connector_providers import mcp_capability_name
from oscar.contracts import Action, Task, new_id, record
from oscar.mcp_auth import MCPProvider
from tests import test_connections as connection_fixture


@unittest.skipUnless(importlib.util.find_spec("mcp"), "install oscar-brain[mcp]")
class MCPAuthorizationTests(unittest.TestCase):
    setUp = connection_fixture.ConnectionManagementTests.setUp
    enroll_owner = connection_fixture.ConnectionManagementTests.enroll_owner
    review = connection_fixture.ConnectionManagementTests.review
    signed = connection_fixture.ConnectionManagementTests.signed
    complete = connection_fixture.ConnectionManagementTests.complete

    def fixture(self):
        import httpx2

        self.provider = MCPProvider(
            "resource-fixture",
            "registered-client",
            "http://127.0.0.1:48123/oauth/callback",
            "https://mcp.example.com/mcp",
            "https://auth.example.com/tenant",
            ("files:read", "files:write"),
        )
        self.metadata = {
            "issuer": self.provider.issuer,
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
            "code_challenge_methods_supported": ["S256"],
            "authorization_response_iss_parameter_supported": True,
        }
        self.prm = {
            "resource": self.provider.resource,
            "authorization_servers": [self.provider.issuer],
            "scopes_supported": ["files:read"],
        }
        self.calls, self.tokens, self.expected = [], [], {}
        self.before_token = None
        self.token_error = False
        self.challenge_metadata = True
        self.sdk_calls = []
        self.token_override = {}
        self.revocations = []
        self.revocation_error = False
        self.before_revoke = None
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self, status, data, headers=None):
                raw = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                fixture.calls.append(self.path)
                if self.path == "/mcp":
                    if "text/event-stream" in self.headers.get("Accept", ""):
                        self.respond(405, {})
                        return
                    if self.headers.get("Authorization") in fixture.tokens:
                        self.respond(200, {"fact": "Synthetic authorized resource"})
                    else:
                        header = 'Bearer scope="files:read"'
                        if fixture.challenge_metadata:
                            header += ', resource_metadata="https://mcp.example.com/metadata"'
                        self.respond(401, {}, {"WWW-Authenticate": header})
                elif self.path in {"/metadata", "/.well-known/oauth-protected-resource/mcp"}:
                    self.respond(200, fixture.prm)
                elif self.path == "/.well-known/oauth-authorization-server/tenant":
                    self.respond(200, fixture.metadata)
                else:
                    self.respond(404, {})

            def do_POST(self):
                if self.path == "/mcp":
                    if self.headers.get("Authorization") not in fixture.tokens:
                        self.respond(401, {})
                        return
                    message = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    method = message["method"]
                    fixture.sdk_calls.append(method)
                    if "id" not in message:
                        self.respond(202, {})
                        return
                    if method == "initialize":
                        result = {
                            "protocolVersion": message["params"]["protocolVersion"],
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "Synthetic authorized MCP", "version": "1"},
                        }
                    elif method == "tools/list":
                        result = {
                            "tools": [
                                {
                                    "name": "lookup",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {"topic": {"type": "string"}},
                                        "required": ["topic"],
                                    },
                                }
                            ]
                        }
                    elif method == "tools/call":
                        result = {
                            "content": [{"type": "text", "text": "Synthetic authorized fact"}],
                            "structuredContent": {"fact": "Synthetic authorized fact"},
                            "isError": False,
                        }
                    else:
                        self.respond(400, {})
                        return
                    self.respond(200, {"jsonrpc": "2.0", "id": message["id"], "result": result})
                    return
                fields = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
                if self.path == "/revoke":
                    fixture.revocations.append(fields)
                    if fixture.before_revoke:
                        fixture.before_revoke()
                    self.respond(503 if fixture.revocation_error else 200, {})
                    return
                fixture.calls.append(fields)
                if fixture.before_token:
                    fixture.before_token()
                if fixture.token_error:
                    self.respond(400, {"error": "invalid_grant"})
                    return
                if fields.get("resource") != [fixture.provider.resource] or fields.get(
                    "client_id"
                ) != [fixture.provider.client_id]:
                    self.respond(400, {})
                    return
                if fields["grant_type"] == ["authorization_code"]:
                    from tests.test_auth_broker import b64

                    if (
                        b64(hashlib.sha256(fields["code_verifier"][0].encode()).digest())
                        != fixture.expected["code_challenge"][0]
                        or fields.get("code") != ["synthetic-code"]
                        or fields.get("redirect_uri") != [fixture.provider.redirect_uri]
                    ):
                        self.respond(400, {})
                        return
                token = "synthetic-mcp-access-" + str(len(fixture.tokens))
                fixture.tokens.append("Bearer " + token)
                self.respond(
                    200,
                    {
                        "access_token": token,
                        "refresh_token": "synthetic-rotated-" + str(len(fixture.tokens)),
                        "token_type": "Bearer",
                        "expires_in": 300,
                        "scope": "files:read",
                        **fixture.token_override,
                    },
                )

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.local = "http://127.0.0.1:" + str(self.server.server_port)
        self.h.auth = AuthBroker(self.h.accounts, self.vault, [self.provider])

        def request(url, fields=None):
            with httpx2.Client(trust_env=False, follow_redirects=False) as client:
                return client.request(
                    "POST" if fields is not None else "GET",
                    self.local + urlsplit(url).path,
                    data=fields,
                )

        self.h.auth.mcp.request = request
        guard = patch("oscar.mcp_auth.validate_destination", return_value=(self.local, "127.0.0.1"))
        guard.start()
        self.addCleanup(guard.stop)

    def begin(self, account_id=None):
        value = json.dumps(
            {
                "alias": "Synthetic resource access",
                "identity_class": "resource-grant",
                "scopes": ["files:read"],
                **({"account_id": account_id} if account_id else {}),
            }
        )
        count = len(self.calls)
        review = self.review("begin_account", value, self.provider.id)
        self.assertEqual(count, len(self.calls))
        enrollment = self.complete(review)["enrollment"]
        self.expected = parse_qs(urlsplit(enrollment["url"]).query)
        self.assertEqual([self.provider.resource], self.expected["resource"])
        self.assertEqual(["S256"], self.expected["code_challenge_method"])
        return {
            "id": enrollment["id"],
            "state": self.expected["state"][0],
            "code": "synthetic-code",
            "iss": self.provider.issuer,
        }

    def callback(self, payload):
        return self.manager.oauth_callback(
            "owner-node", self.session_id, self.scope, self.grants, payload
        )

    def grant(self):
        payload = self.begin()
        self.callback(payload)
        account = [
            a for a in self.h.accounts.list_accounts() if a.identity_class == "resource-grant"
        ][0]
        return payload, account

    def test_signed_native_flow_exact_resource_token_refresh_and_disconnect(self):
        import httpx2

        self.fixture()
        payload, account = self.grant()
        self.assertEqual("mcp-resource", account.provider)
        self.assertNotEqual("synthetic-subject", account.subject)
        self.assertEqual("UNKNOWN", account.remote_revocation)
        binding = account.services[self.provider.service]
        secret = self.vault.read(binding.credential_ref).value
        response = httpx2.get(
            self.local + "/mcp", headers={"Authorization": "Bearer " + secret}, trust_env=False
        )
        self.assertEqual("Synthetic authorized resource", response.json()["fact"])
        registration = {
            "config": {
                "id": "authorized-resource",
                "name": "Resource",
                "account_id": account.id,
                "account_generation": account.generation,
                "url": self.provider.resource,
            },
            "reviewed": {"lookup": ["read"]},
        }
        with patch("oscar.mcp_client.validate_destination", return_value=(self.local, "127.0.0.1")):
            self.complete(
                self.review("register_plugin", json.dumps(registration), "authorized-resource")
            )
        config = self.h.plugins._config(self.h.store.get("mcp_installation", "authorized-resource"))
        self.assertEqual(binding.credential_ref, config.credential_ref)
        self.h.plugins._authorize(config.id, config)
        # Only the trusted test transport maps the fixed HTTPS resource to this local HTTP server.
        # The real MCP SDK, bearer headers, session initialization and tool RPC remain exercised.
        original_send = httpx2.AsyncHTTPTransport.handle_async_request

        async def send(transport, request):
            request.url = request.url.copy_with(scheme="http", port=self.server.server_port)
            return await original_send(transport, request)

        with (
            patch("oscar.mcp_client.validate_destination", return_value=(self.local, "127.0.0.1")),
            patch.object(httpx2.AsyncHTTPTransport, "handle_async_request", send),
        ):
            self.complete(self.review("connect_plugin", "", config.id))
            task = Task(new_id(), new_id(), new_id())
            self.h.store.put("task", task.id, record(task))
            action = Action(
                new_id(),
                task.id,
                task.correlation_id,
                config.id + ":" + mcp_capability_name("lookup"),
                {"path": {"name": "lookup"}, "body": {"topic": "authorized"}},
                new_id(),
                "owner",
            )
            result = self.h.connectors.execute(
                config.id,
                mcp_capability_name("lookup"),
                action,
                Cancellation(self.h.store, task.id),
                frozenset({"connectors:read"}),
            )
            self.assertTrue(result.result.success)
            self.assertEqual(
                "Synthetic authorized fact", result.payload["structuredContent"]["fact"]
            )
        self.assertIn("tools/call", self.sdk_calls)
        self.complete(self.review("refresh_account", self.provider.service, account.id))
        refreshed = self.h.accounts.get(account.id)
        self.assertGreater(refreshed.generation, account.generation)
        with self.assertRaises(PermissionError):
            self.h.plugins._authorize(config.id, config)
        with self.assertRaises(KeyError):
            self.vault.read(binding.credential_ref)
        with self.assertRaises(PermissionError):
            self.callback(payload)
        self.complete(self.review("disconnect_account", "", account.id))
        self.assertEqual("disconnected", self.h.accounts.get(account.id).status)
        self.assertFalse(self.vault.values)
        self.assertNotIn("synthetic-mcp-access", json.dumps(self.h.store.all("connected_account")))

    def test_reauthorization_preserves_grant_and_fences_old_credentials(self):
        self.fixture()
        _, account = self.grant()
        old = account.services[self.provider.service].credential_ref
        payload = self.begin(account.id)
        self.callback(payload)
        current = self.h.accounts.get(account.id)
        self.assertGreater(current.generation, account.generation)
        self.assertEqual(
            1,
            len(
                [a for a in self.h.accounts.list_accounts() if a.identity_class == "resource-grant"]
            ),
        )
        with self.assertRaises(KeyError):
            self.vault.read(old)
        self.assertEqual(2, len(self.vault.values))
        self.h.auth.recover()
        self.assertEqual("connected", self.h.accounts.get(account.id).status)

    def test_signed_disconnect_requests_both_token_revocations_after_local_withdrawal(self):
        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        self.metadata["revocation_endpoint_auth_methods_supported"] = ["none"]
        _, account = self.grant()

        def withdrawn():
            self.assertEqual("disconnected", self.h.accounts.get(account.id).status)
            self.assertTrue(self.vault.values)

        self.before_revoke = withdrawn
        review = self.review("disconnect_account", "", account.id)
        self.assertEqual([], self.revocations)
        self.complete(review)
        self.assertEqual(
            ["refresh_token", "access_token"], [r["token_type_hint"][0] for r in self.revocations]
        )
        self.assertTrue(
            all(set(r) == {"client_id", "token", "token_type_hint"} for r in self.revocations)
        )
        self.assertTrue(all(r["client_id"] == [self.provider.client_id] for r in self.revocations))
        current = self.h.accounts.get(account.id)
        self.assertEqual("PROVIDER_ACCEPTED_NOT_INDEPENDENTLY_VERIFIED", current.remote_revocation)
        self.assertEqual("deleted", current.local_credentials)
        self.assertFalse(self.vault.values)
        self.h.auth.finish_disconnect(current)
        self.h.auth.recover()
        self.assertEqual(2, len(self.revocations))
        self.assertNotIn(
            "synthetic-mcp-access", json.dumps(self.h.store.all("auth_broker_connection"))
        )

    def test_remote_revoke_failure_still_deletes_local_tokens_and_never_retries(self):
        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        _, account = self.grant()
        self.revocation_error = True
        self.complete(self.review("disconnect_account", "", account.id))
        current = self.h.accounts.get(account.id)
        self.assertEqual("UNKNOWN_OWNER_ACTION_REQUIRED", current.remote_revocation)
        self.assertFalse(self.vault.values)
        self.h.auth.finish_disconnect(current)
        self.assertEqual(2, len(self.revocations))

    def test_partial_provider_acceptance_remains_unknown(self):
        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        _, account = self.grant()

        def reject_second():
            self.revocation_error = len(self.revocations) == 2

        self.before_revoke = reject_second
        self.complete(self.review("disconnect_account", "", account.id))
        self.assertEqual(2, len(self.revocations))
        self.assertFalse(self.vault.values)
        self.assertEqual(
            "UNKNOWN_OWNER_ACTION_REQUIRED", self.h.accounts.get(account.id).remote_revocation
        )

    def test_changed_client_configuration_cannot_receive_old_tokens(self):
        from dataclasses import replace

        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        _, account = self.grant()
        self.h.auth.providers[self.provider.id] = replace(self.provider, client_id="changed-client")
        self.complete(self.review("disconnect_account", "", account.id))
        self.assertEqual([], self.revocations)
        self.assertFalse(self.vault.values)
        self.assertEqual(
            "UNKNOWN_OWNER_ACTION_REQUIRED", self.h.accounts.get(account.id).remote_revocation
        )

    def test_revocation_transport_exception_does_not_preserve_local_credentials(self):
        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        _, account = self.grant()
        request = self.h.auth.mcp.request

        def unavailable(url, fields=None):
            if url.endswith("/revoke"):
                raise RuntimeError("synthetic transport loss")
            return request(url, fields)

        self.h.auth.mcp.request = unavailable
        self.complete(self.review("disconnect_account", "", account.id))
        self.assertFalse(self.vault.values)
        self.assertEqual(
            "UNKNOWN_OWNER_ACTION_REQUIRED", self.h.accounts.get(account.id).remote_revocation
        )

    def test_interrupted_revocation_recovery_deletes_tokens_without_remote_replay(self):
        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        _, account = self.grant()

        def interrupted(url, fields=None):
            raise KeyboardInterrupt("synthetic process interruption")

        self.h.auth.mcp.request = interrupted
        with self.assertRaises(KeyboardInterrupt):
            self.complete(self.review("disconnect_account", "", account.id))
        self.assertTrue(self.vault.values)
        with patch.object(self.h.auth.mcp, "request", side_effect=AssertionError("remote replay")):
            self.h.auth.recover()
        self.assertFalse(self.vault.values)
        self.assertEqual("disconnected", self.h.accounts.get(account.id).status)

    def test_public_client_cannot_borrow_confidential_revocation_credentials(self):
        self.fixture()
        self.metadata["revocation_endpoint"] = "https://auth.example.com/revoke"
        self.metadata["revocation_endpoint_auth_methods_supported"] = ["client_secret_basic"]
        _, account = self.grant()
        self.complete(self.review("disconnect_account", "", account.id))
        self.assertEqual([], self.revocations)
        self.assertFalse(self.vault.values)
        self.assertEqual(
            "UNKNOWN_OWNER_ACTION_REQUIRED", self.h.accounts.get(account.id).remote_revocation
        )

    def test_query_endpoints_and_untyped_or_incompatible_metadata_are_rejected(self):
        self.fixture()
        for key, invalid in (
            ("authorization_endpoint", "https://auth.example.com/authorize?client_id=other"),
            ("token_endpoint", "https://auth.example.com/token?resource=other"),
            ("revocation_endpoint", "http://auth.example.com/revoke"),
            ("revocation_endpoint", "https://auth.example.com/revoke?token=untrusted"),
            ("revocation_endpoint_auth_methods_supported", "none"),
            ("code_challenge_methods_supported", "S256"),
            ("authorization_response_iss_parameter_supported", 1),
            ("token_endpoint_auth_methods_supported", ["client_secret_basic"]),
            ("response_types_supported", ["token"]),
        ):
            with self.subTest(key=key):
                original = dict(self.metadata)
                self.metadata[key] = invalid
                with self.assertRaises((ValueError, PermissionError)):
                    self.begin()
                self.metadata.clear()
                self.metadata.update(original)
        self.prm["authorization_servers"] = self.provider.issuer
        with self.assertRaises(ValueError):
            self.begin()
        self.assertEqual([], self.h.store.all("auth_code_pending"))

    def test_wrong_or_missing_issuer_rejected_before_code_exchange(self):
        self.fixture()
        for issuer in (None, "https://attacker.example", self.provider.issuer + "/"):
            payload = self.begin()
            if issuer is None:
                payload.pop("iss")
            else:
                payload["iss"] = issuer
            with self.assertRaises(PermissionError):
                self.callback(payload)
        self.assertFalse(any(isinstance(c, dict) for c in self.calls))

    def test_mismatched_resource_issuer_and_missing_pkce_fail_closed(self):
        self.fixture()
        for container, key, invalid in (
            (self.prm, "resource", "https://other.example/mcp"),
            (self.metadata, "issuer", "https://other.example"),
            (self.metadata, "code_challenge_methods_supported", ["plain"]),
        ):
            original = container[key]
            container[key] = invalid
            with self.assertRaises(PermissionError):
                self.begin()
            container[key] = original
        self.assertEqual([], self.h.store.all("auth_code_pending"))

    def test_withdrawn_owner_after_token_response_cannot_bind_or_replay(self):
        self.fixture()
        payload = self.begin()
        self.before_token = lambda: self.h.store.put(
            "session",
            self.session_id,
            {**self.h.store.get("session", self.session_id), "revoked": True},
        )
        with self.assertRaises(RuntimeError):
            self.callback(payload)
        self.assertFalse(self.vault.values)
        self.assertFalse(
            any(a.identity_class == "resource-grant" for a in self.h.accounts.list_accounts())
        )
        with self.assertRaises(PermissionError):
            self.callback(payload)
        self.assertEqual(1, len([c for c in self.calls if isinstance(c, dict)]))

    def test_wrong_state_or_node_and_changed_configuration_cannot_exchange(self):
        from dataclasses import replace

        self.fixture()
        payload = self.begin()
        with self.assertRaises(PermissionError):
            self.manager.oauth_callback(
                "other-node", self.session_id, self.scope, self.grants, payload
            )
        self.h.auth.providers[self.provider.id] = replace(self.provider, client_id="changed-client")
        with self.assertRaises(PermissionError):
            self.callback(payload)
        self.h.auth.providers[self.provider.id] = self.provider
        payload = self.begin()
        payload["state"] = "wrong-state"
        with self.assertRaises(PermissionError):
            self.callback(payload)
        self.assertFalse(any(isinstance(c, dict) for c in self.calls))

    def test_token_scope_escalation_rejected_without_person_or_resource_binding(self):
        self.fixture()
        payload = self.begin()
        self.token_override = {"scope": "files:read files:write"}
        with self.assertRaises(RuntimeError):
            self.callback(payload)
        self.assertFalse(self.vault.values)
        self.assertFalse(
            any(a.identity_class == "resource-grant" for a in self.h.accounts.list_accounts())
        )

    def test_interrupted_code_and_ambiguous_refresh_never_replay(self):
        self.fixture()
        payload = self.begin()
        pending = self.h.store.get("auth_code_pending", payload["id"])
        self.h.store.put("auth_code_pending", payload["id"], {**pending, "state": "exchanging"})
        count = len(self.calls)
        self.h.auth.recover()
        self.assertEqual(count, len(self.calls))
        self.assertFalse(self.vault.values)
        with self.assertRaises(PermissionError):
            self.callback(payload)
        _, account = self.grant()
        request = self.h.auth.mcp.request

        def ambiguous(url, fields=None):
            request(url, fields)
            raise OSError("synthetic connection lost after rotating token consumption")

        self.h.auth.mcp.request = ambiguous
        with self.assertRaises(RuntimeError):
            self.complete(self.review("refresh_account", self.provider.service, account.id))
        count = len(self.calls)
        self.h.auth.recover()
        self.assertEqual(count, len(self.calls))
        self.assertEqual("disconnected", self.h.accounts.get(account.id).status)
        self.assertFalse(self.vault.values)

    def test_configuration_and_person_identity_boundary(self):
        from oscar.auth_broker import load_providers

        self.fixture()
        config = self.h.archive.path.parent / "mcp-app.json"
        config.write_text(
            json.dumps(
                {
                    "version": 1,
                    "providers": [
                        {
                            "provider": "mcp-resource",
                            "id": self.provider.id,
                            "client_id": self.provider.client_id,
                            "redirect_uri": self.provider.redirect_uri,
                            "issuer": self.provider.issuer,
                            "resource": self.provider.resource,
                            "allowed_scopes": list(self.provider.allowed_scopes),
                        }
                    ],
                }
            )
        )
        self.assertEqual([self.provider], load_providers(config))
        value = json.dumps(
            {"alias": "Person", "identity_class": "owner-delegated", "scopes": ["files:read"]}
        )
        with self.assertRaises(PermissionError):
            self.review("begin_account", value, self.provider.id)
        with self.assertRaises(ValueError):
            self.h.accounts.add(
                "mcp-resource",
                self.provider.issuer,
                "invented-person",
                "Person",
                verified=True,
                identity_class="resource-grant",
            )

    def test_failed_rotating_refresh_is_consumed_and_not_replayed_on_recovery(self):
        self.fixture()
        _, account = self.grant()
        self.token_error = True
        review = self.review("refresh_account", self.provider.service, account.id)
        with self.assertRaises(RuntimeError):
            self.complete(review)
        self.assertEqual("disconnected", self.h.accounts.get(account.id).status)
        self.assertFalse(self.vault.values)
        calls = len(self.calls)
        self.h.auth.recover()
        self.assertEqual(calls, len(self.calls))
        with self.assertRaises(PermissionError):
            self.complete(review)

    def test_well_known_discovery_and_client_credential_reference_injection(self):
        self.fixture()
        self.challenge_metadata = False
        _, account = self.grant()
        self.assertIn("/.well-known/oauth-protected-resource/mcp", self.calls)
        registration = {
            "config": {
                "id": "resource",
                "name": "Resource",
                "account_id": account.id,
                "account_generation": account.generation,
                "url": self.provider.resource,
                "credential_ref": "native-supplied-reference",
            },
            "reviewed": {"lookup": ["read"]},
        }
        with self.assertRaises(PermissionError):
            self.review("register_plugin", json.dumps(registration), "resource")
