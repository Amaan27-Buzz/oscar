import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oscar.connectors import CredentialRef
from oscar.oauth_device import GitHubDeviceFlow, VaultResolver
from oscar.secure_credentials import SecretValue
from oscar.storage import Store


class TestVault:
    def __init__(self):
        self.values = {}

    def put(self, secret, *, expires_at=None, reference=None):
        reference = reference or f"{len(self.values) + 1:032x}"
        self.values[reference] = secret
        return reference

    def read(self, reference, *, allow_expired=False):
        return SecretValue(self.values[reference])

    def delete(self, reference):
        self.values.pop(reference, None)


class DeviceFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "oauth.sqlite")
        self.vault = TestVault()
        self.now = 1000
        self.response = {"error": "authorization_pending"}
        self.calls = []
        self.flow = GitHubDeviceFlow(self.store, self.vault, self.request, lambda: self.now)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def request(self, path, fields):
        self.calls.append(path)
        if path == "/login/device/code":
            return {
                "verification_uri": "https://github.com/login/device",
                "device_code": "synthetic-device-credential",
                "user_code": "TEST-CODE",
                "expires_in": 900,
                "interval": 5,
            }
        return self.response

    def begin(self):
        return self.flow.begin("registered_fixture_client", owner_authorized=True)

    def test_owner_identity_scope_and_poll_interval(self):
        with self.assertRaises(PermissionError):
            self.flow.begin("registered_fixture_client", owner_authorized=False)
        with self.assertRaises(ValueError):
            self.flow.begin(
                "registered_fixture_client", owner_authorized=True, scopes=frozenset({"repo"})
            )
        challenge = self.begin()
        with self.assertRaises(PermissionError):
            self.flow.poll_once(challenge["id"], "wrong nonce", owner_authorized=True)
        self.assertEqual(
            "pending",
            self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)[
                "state"
            ],
        )
        self.assertEqual(1, len(self.calls))
        self.now += 5
        self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.assertEqual(2, len(self.calls))

    def test_slow_down_and_expiry_delete_device_credential(self):
        challenge = self.begin()
        self.now += 5
        self.response = {"error": "slow_down"}
        reply = self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.assertEqual(10, reply["retry_after"])
        self.now += 1000
        with self.assertRaisesRegex(PermissionError, "expired"):
            self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.assertEqual({}, self.vault.values)

    def test_token_only_vault_refs_restart_and_local_disconnect(self):
        challenge = self.begin()
        self.now += 5
        self.response = {
            "access_token": "synthetic-access-credential",
            "token_type": "bearer",
            "scope": "user:email",
        }
        connection = self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        durable = json.dumps(self.store.all("oauth_pending") + self.store.all("oauth_connection"))
        self.assertNotIn("synthetic-access-credential", durable)
        self.assertNotIn("synthetic-device-credential", durable)
        self.assertNotIn(challenge["nonce"], durable)
        resolver = VaultResolver(self.vault)
        value = resolver.resolve(CredentialRef(connection["credential_ref"]))
        self.assertEqual("<redacted>", resolver.redact(value))
        with self.assertRaises(PermissionError):
            self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.flow.disconnect(connection["id"], owner_authorized=True)
        self.assertIsNone(resolver.resolve(CredentialRef(connection["credential_ref"])))
        self.assertIn(
            "provider_revocation_pending",
            self.store.get("oauth_connection", connection["id"])["state"],
        )

    def test_scope_escalation_is_blocked(self):
        challenge = self.begin()
        self.now += 5
        self.response = {
            "access_token": "synthetic-access-credential",
            "token_type": "bearer",
            "scope": "repo,user:email",
        }
        with self.assertRaises(PermissionError):
            self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.assertEqual([], self.store.all("oauth_connection"))

    def test_interrupted_exchange_blocks_instead_of_replay(self):
        challenge = self.begin()
        self.now += 5

        def interrupted(*args):
            raise OSError("synthetic transport interruption")

        self.flow.request = interrupted
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.now += 100
        with self.assertRaises(PermissionError):
            self.flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        self.assertEqual("ambiguous", self.store.get("oauth_pending", challenge["id"])["state"])


if __name__ == "__main__":
    unittest.main()
