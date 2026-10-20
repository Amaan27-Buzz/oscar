"""Real loopback OAuth protocol server with synthetic signed OIDC and private test vault."""

import base64
import hashlib
import json
import threading
import unittest
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.accounts import AccountRegistry
from oscar.auth_broker import AuthBroker, google_provider, microsoft_provider
from oscar.secure_credentials import SecretValue
from oscar.storage import Store


def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


class PrivateVault:
    def __init__(self):
        self.values = {}

    def put(self, secret, *, expires_at=None, reference=None):
        assert reference is not None
        self.values[reference] = secret
        return reference

    def read(self, reference, *, allow_expired=False):
        return SecretValue(self.values[reference])

    def delete(self, reference):
        self.values.pop(reference, None)


class OAuthFixture:
    def __init__(self):
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.provider = None
        self.expected = {}
        self.subject = "synthetic-subject"
        self.changes = {}
        self.error = None
        self.scopes = None
        self.calls = []
        self.refreshes = 0
        self.before_response = None
        self.omit_refresh = False
        self.omit_identity = False
        self.omit_scopes = False
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                numbers = fixture.key.public_key().public_numbers()
                payload = {
                    "keys": [
                        {
                            "kty": "RSA",
                            "kid": "fixture-key",
                            "alg": "RS256",
                            "n": b64(numbers.n.to_bytes(256)),
                            "e": b64(numbers.e.to_bytes(3)),
                        }
                    ]
                }
                self.respond(payload)

            def do_POST(self):
                data = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
                fixture.calls.append(data["grant_type"][0])
                if fixture.error:
                    self.respond({"error": fixture.error})
                    return
                if data["grant_type"] == ["authorization_code"]:
                    verifier = data["code_verifier"][0]
                    if (
                        b64(hashlib.sha256(verifier.encode()).digest())
                        != fixture.expected["code_challenge"][0]
                        or data["redirect_uri"] != fixture.expected["redirect_uri"]
                        or data["client_id"] != fixture.expected["client_id"]
                        or data["code"] != ["synthetic-code"]
                    ):
                        self.respond({"error": "invalid_grant"})
                        return
                else:
                    if data["refresh_token"] != ["synthetic-refresh"]:
                        self.respond({"error": "invalid_grant"})
                        return
                    fixture.refreshes += 1
                claims = {
                    "iss": fixture.provider.issuer,
                    "aud": fixture.provider.client_id,
                    "sub": fixture.subject,
                    "iat": 1000,
                    "exp": 2000,
                    "nonce": fixture.expected["nonce"][0],
                }
                if fixture.provider.provider == "microsoft":
                    claims.update(tid=fixture.provider.tenant, oid=fixture.subject)
                claims.update(fixture.changes)
                token = b64(json.dumps({"alg": "RS256", "kid": "fixture-key"}).encode())
                token += "." + b64(json.dumps(claims).encode())
                token += "." + b64(
                    fixture.key.sign(token.encode(), padding.PKCS1v15(), hashes.SHA256())
                )
                if fixture.before_response:
                    fixture.before_response()
                self.respond(
                    {
                        "access_token": "synthetic-access-" + str(fixture.refreshes),
                        "refresh_token": "synthetic-refresh",
                        "token_type": "Bearer",
                        "expires_in": 300,
                        "id_token": token,
                        "scope": fixture.scopes or fixture.expected["scope"][0],
                    }
                )

            def respond(self, payload):
                if "access_token" in payload:
                    for flag, key in (
                        (fixture.omit_refresh, "refresh_token"),
                        (fixture.omit_identity, "id_token"),
                        (fixture.omit_scopes, "scope"),
                    ):
                        if flag:
                            payload.pop(key, None)
                data = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def request(self, official_url, fields):
        # Only the fixture transport redirects fixed provider endpoints to this isolated server.
        request = Request(
            "http://127.0.0.1:" + str(self.server.server_port) + "/fixture",
            data=urlencode(fields).encode() if fields is not None else None,
        )
        with urlopen(request, timeout=3) as response:
            return json.loads(response.read())

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        assert not self.thread.is_alive()


class AuthBrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "oauth.sqlite")
        self.vault = PrivateVault()
        self.now = 1000
        self.accounts = AccountRegistry(self.store, lambda: self.now)
        self.fixture = OAuthFixture()
        self.provider = google_provider(
            "synthetic-client",
            "http://127.0.0.1:3456/callback",
            "google.calendar",
            "https://www.googleapis.com",
        )
        self.broker = self.make_broker()

    def tearDown(self):
        self.fixture.close()
        self.store.close()
        self.temp.cleanup()

    def make_broker(self):
        self.fixture.provider = self.provider
        return AuthBroker(
            self.accounts,
            self.vault,
            [self.provider],
            request=self.fixture.request,
            clock=lambda: self.now,
        )

    def begin(self, **kwargs):
        result = self.broker.begin(
            self.provider.id,
            frozenset({"calendar.read"}),
            owner_authorized=True,
            alias="Arbitrary label",
            **kwargs,
        )
        self.fixture.expected = parse_qs(urlparse(result["url"]).query)
        return result

    def complete(self, begin):
        return self.broker.complete(
            begin["id"], self.fixture.expected["state"][0], "synthetic-code", owner_authorized=True
        )

    def test_real_http_pkce_signed_google_oidc_scope_binding_and_secret_hygiene(self):
        begin = self.begin()
        self.assertEqual(["S256"], self.fixture.expected["code_challenge_method"])
        self.assertEqual(["select_account"], self.fixture.expected["prompt"])
        account = self.complete(begin)
        self.assertEqual("synthetic-subject", account.subject)
        self.assertEqual("google", account.provider)
        self.assertEqual(("calendar.read", "openid"), account.services["google.calendar"].scopes)
        self.assertEqual(
            "synthetic-access-0",
            self.vault.read(account.services["google.calendar"].credential_ref).value,
        )
        serialized = json.dumps(
            self.store.all("auth_code_pending")
            + self.store.all("auth_broker_connection")
            + self.store.all("connected_account")
        )
        self.assertNotIn("synthetic-access", serialized)
        self.assertNotIn("synthetic-refresh", serialized)
        self.assertNotIn("code_verifier", serialized)
        self.assertNotIn(self.fixture.expected["state"][0], serialized)
        self.assertNotIn(self.fixture.expected["nonce"][0], serialized)
        with self.assertRaises(PermissionError):
            self.complete(begin)

    def test_microsoft_tenant_issuer_and_stable_oid(self):
        self.provider = microsoft_provider(
            "synthetic-client",
            "http://127.0.0.1:3456/callback",
            "12345678-1234-1234-1234-123456789abc",
        )
        self.broker = self.make_broker()
        account = self.complete(self.begin())
        self.assertEqual(self.provider.tenant, account.tenant)
        self.assertEqual("synthetic-subject", account.subject)
        self.assertIn("microsoft.graph", account.services)

    def test_callback_state_nonce_signature_issuer_audience_and_expiry_fail_closed(self):
        begin = self.begin()
        with self.assertRaises(PermissionError):
            self.broker.complete(begin["id"], "wrong", "synthetic-code", owner_authorized=True)
        self.assertEqual([], self.fixture.calls)
        for change in (
            {"nonce": "wrong"},
            {"iss": "https://attacker.invalid"},
            {"aud": "other-client"},
            {"exp": 1000},
            {"iat": 10000},
        ):
            with self.subTest(change=change):
                self.fixture.changes = change
                with self.assertRaises(RuntimeError):
                    self.complete(self.begin())
        self.fixture.changes = {}
        begin = self.begin()
        original_request = self.broker.request

        def wrong_key(url, fields):
            value = original_request(url, fields)
            if fields is None:
                key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                value["keys"][0]["n"] = b64(key.public_key().public_numbers().n.to_bytes(256))
            return value

        self.broker.request = wrong_key
        with self.assertRaises(RuntimeError):
            self.complete(begin)
        self.assertEqual([], self.accounts.list_accounts())

    def test_expired_state_configuration_change_provider_error_and_no_automatic_replay(self):
        begin = self.begin()
        self.now += 301
        with self.assertRaises(PermissionError):
            self.complete(begin)
        self.assertEqual([], self.fixture.calls)
        self.now = 1000
        begin = self.begin()
        self.broker.providers[self.provider.id] = replace(self.provider, client_id="changed")
        with self.assertRaises(PermissionError):
            self.complete(begin)
        self.broker.providers[self.provider.id] = self.provider
        self.fixture.error = "access_denied"
        with self.assertRaises(RuntimeError):
            self.complete(begin)
        calls = len(self.fixture.calls)
        with self.assertRaises(PermissionError):
            self.complete(begin)
        self.assertEqual(calls, len(self.fixture.calls))

    def test_refresh_rotation_scope_withdrawal_and_disconnect_delete_native_refs(self):
        begin = self.begin()
        first = self.complete(begin)
        old_ref = first.services[self.provider.service].credential_ref
        self.fixture.scopes = "openid"
        current = self.broker.refresh(begin["id"], owner_authorized=True)
        self.assertGreater(current.generation, first.generation)
        self.assertNotIn(old_ref, self.vault.values)
        self.assertEqual(("openid",), current.services[self.provider.service].scopes)
        self.assertEqual(
            "synthetic-access-1",
            self.vault.read(current.services[self.provider.service].credential_ref).value,
        )
        self.broker = self.make_broker()
        disconnected = self.broker.disconnect(current.id, owner_authorized=True)
        self.assertEqual("disconnected", disconnected.status)
        self.assertEqual("UNKNOWN_OWNER_ACTION_REQUIRED", disconnected.remote_revocation)
        self.assertEqual({}, self.vault.values)
        with self.assertRaises(PermissionError):
            self.broker.refresh(begin["id"], owner_authorized=True)

    def test_scope_upgrade_rejects_wrong_account_and_unrequested_scope_expansion(self):
        account = self.complete(self.begin())
        self.fixture.subject = "another-account"
        with self.assertRaises(RuntimeError):
            self.complete(self.begin(account_id=account.id))
        self.fixture.subject = account.subject
        self.fixture.scopes = "openid calendar.read unauthorized.write"
        with self.assertRaises(RuntimeError):
            self.complete(self.begin(account_id=account.id))
        self.assertEqual(account.generation, self.accounts.get(account.id).generation)

    def test_fresh_scope_upgrade_keeps_prior_scope_and_private_refresh_without_incremental_flag(
        self,
    ):
        first = self.complete(self.begin())
        old_refresh = self.store.all("auth_broker_connection")[0]["refresh_ref"]
        self.fixture.omit_refresh = True
        begin = self.broker.begin(
            self.provider.id,
            frozenset({"calendar.write"}),
            owner_authorized=True,
            alias="Renamed independently",
            account_id=first.id,
        )
        self.fixture.expected = parse_qs(urlparse(begin["url"]).query)
        self.assertNotIn("include_granted_scopes", self.fixture.expected)
        self.assertEqual(
            {"calendar.read", "calendar.write", "openid"},
            set(self.fixture.expected["scope"][0].split()),
        )
        upgraded = self.complete(begin)
        self.assertEqual(first.id, upgraded.id)
        self.assertNotIn(old_refresh, self.vault.values)
        connection = self.store.get("auth_broker_connection", begin["id"])
        self.assertEqual("synthetic-refresh", self.vault.read(connection["refresh_ref"]).value)

    def test_refresh_without_identity_token_keeps_verified_binding_and_missing_scope_uses_requested(
        self,
    ):
        begin = self.begin()
        first = self.complete(begin)
        self.fixture.omit_identity = True
        self.fixture.omit_refresh = True
        self.fixture.omit_scopes = True
        account = self.broker.refresh(begin["id"], owner_authorized=True)
        self.assertEqual(first.subject, account.subject)
        self.assertEqual(
            first.services[self.provider.service].scopes,
            account.services[self.provider.service].scopes,
        )

    def test_access_token_identity_hash_pairing_and_initial_missing_identity_rejected(self):
        self.fixture.changes = {"at_hash": "not-the-access-token"}
        with self.assertRaises(RuntimeError):
            self.complete(self.begin())
        self.fixture.changes = {}
        self.fixture.omit_identity = True
        with self.assertRaises(RuntimeError):
            self.complete(self.begin())
        self.assertEqual([], self.accounts.list_accounts())

    def test_partial_native_vault_failure_cleans_unbound_access_credential(self):
        original_put = self.vault.put

        def fail_refresh(secret, **kwargs):
            if secret == "synthetic-refresh":
                raise OSError("synthetic native vault failure")
            return original_put(secret, **kwargs)

        self.vault.put = fail_refresh
        with self.assertRaises(RuntimeError):
            self.complete(self.begin())
        self.assertEqual({}, self.vault.values)
        self.assertEqual(
            "blocked_reauthorization_required", self.store.all("auth_broker_connection")[0]["state"]
        )

    def test_revoke_during_exchange_cannot_resurrect_bound_account(self):
        account = self.complete(self.begin())
        begin = self.begin(account_id=account.id)
        self.fixture.before_response = lambda: self.accounts.disconnect(account.id)
        with self.assertRaises(RuntimeError):
            self.complete(begin)
        self.assertEqual("disconnected", self.accounts.get(account.id).status)

    def test_interrupted_exchange_restart_never_replays_code_or_rotating_refresh(self):
        begin = self.begin()

        def interrupted(url, fields):
            raise TimeoutError("synthetic interrupted exchange")

        self.broker.request = interrupted
        with self.assertRaises(RuntimeError):
            self.complete(begin)
        self.broker = self.make_broker()
        with self.assertRaises(PermissionError):
            self.complete(begin)
        self.assertEqual([], self.fixture.calls)
        begin = self.begin()
        account = self.complete(begin)
        connection = self.store.get("auth_broker_connection", begin["id"])
        connection["state"] = "refreshing"
        self.store.put("auth_broker_connection", begin["id"], connection)
        self.broker = self.make_broker()
        self.assertEqual("disconnected", self.accounts.get(account.id).status)
        self.assertEqual({}, self.vault.values)

    def test_native_configuration_and_owner_authority_required(self):
        with self.assertRaises(ValueError):
            google_provider("id", "https://untrusted.invalid/callback", "service", "audience")
        with self.assertRaises(ValueError):
            microsoft_provider("id", "http://127.0.0.1:1234/callback", "common")
        with self.assertRaises(PermissionError):
            self.broker.begin(self.provider.id, frozenset(), alias="label", owner_authorized=False)
        with self.assertRaises(PermissionError):
            self.broker.disconnect("missing", owner_authorized=False)
