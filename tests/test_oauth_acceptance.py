import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from types import SimpleNamespace
from unittest.mock import patch

from oscar.connectors import ConnectorError
from oscar.oauth_device import GitHubDeviceFlow
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store
from scripts.verify_gate_b_oauth import (
    AcceptanceError,
    Reads,
    cleanup,
    disconnect,
    enroll,
    failure_record,
    federation,
    main,
    restart_read,
    run,
    save,
    snapshot,
)

from .test_oauth_device import TestVault


class HTTP:
    def __init__(self):
        self.calls = []
        self.private_fail = False
        self.bad_contract = False

    def request(self, manifest, spec, parameters, secret):
        self.calls.append((spec.name, parameters, bool(secret)))
        if spec.name == "github.repositories.get":
            if secret is not None:
                raise AssertionError("public source received private authentication")
            return {"full_name": "python/cpython"}, "https://api.github.com/repos/python/cpython"
        if self.private_fail:
            raise ConnectorError("network_failure")
        if secret != "synthetic-private-token":
            raise ConnectorError("auth_missing")
        if spec.name == "github.owner":
            return {
                "id": 1234,
                "login": "private-login",
                "name": "private-name",
            }, "https://api.github.com/user"
        return {
            "items": [
                {
                    "email": "private-mail@example.invalid",
                    "verified": not self.bad_contract,
                    "primary": True,
                }
            ]
        }, "https://api.github.com/user/emails"


class OAuthAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "oauth.sqlite")
        self.addCleanup(self.store.close)
        self.vault = TestVault()
        self.now = 1000.0
        self.responses = []
        self.requests = []
        self.http = HTTP()
        self.flow = GitHubDeviceFlow(self.store, self.vault, self.request, lambda: self.now)
        self.fixture = "a" * 32

    def request(self, path, fields):
        self.requests.append((path, dict(fields)))
        if path == "/login/device/code":
            return {
                "verification_uri": "https://github.com/login/device",
                "device_code": "synthetic-device-secret",
                "user_code": "ABCD-EFGH",
                "expires_in": 900,
                "interval": 5,
            }
        if self.responses:
            return self.responses.pop(0)
        return {
            "access_token": "synthetic-private-token",
            "token_type": "bearer",
            "scope": "user:email",
        }

    def wait(self, seconds):
        self.now += seconds

    def authorize(self):
        return enroll(
            self.flow, "registered_fixture_client", lambda: "AUTHORIZED", lambda _: None, self.wait
        )

    def test_no_poll_before_owner_confirmation_and_only_safe_challenge_display(self):
        displayed = []

        def refuse():
            self.assertEqual(1, len(self.requests))
            return "NO"

        with self.assertRaisesRegex(AcceptanceError, "oauth.owner_confirmation"):
            enroll(self.flow, "registered_fixture_client", refuse, displayed.append, self.wait)
        self.assertEqual(["https://github.com/login/device", "ABCD-EFGH"], displayed)
        self.assertEqual("user:email", self.requests[0][1]["scope"])
        self.assertEqual(1, len(self.requests))
        cleanup(self.root, self.vault)
        self.assertEqual({}, self.vault.values)

    def test_poll_interval_slow_down_and_minimum_scope(self):
        self.responses = [{"error": "authorization_pending"}, {"error": "slow_down"}]
        connection = self.authorize()
        self.assertEqual(1020, self.now)
        self.assertEqual(["user:email"], connection["scopes"])
        self.assertTrue(all("client_secret" not in fields for _, fields in self.requests))

    def test_expiry_is_named_and_no_exchange_after_expiry(self):
        self.responses = [{"error": "authorization_pending"}] * 720
        with self.assertRaisesRegex(AcceptanceError, "oauth.expired"):
            self.authorize()
        self.assertLessEqual(len(self.requests), 181)
        cleanup(self.root, self.vault)
        self.assertEqual({}, self.vault.values)

    def test_private_contract_metadata_restart_and_disconnect(self):
        connection = self.authorize()
        reads = Reads(self.store, self.vault, connection, self.http)
        initial = snapshot(reads, self.fixture)
        reads.close()
        self.assertEqual(1, initial["email_count_page1"])
        save(
            self.root,
            "checkpoint.json",
            {
                "fixture_id": self.fixture,
                "connection_id": connection["id"],
                "identity_sha256": initial["identity_sha256"],
            },
        )
        self.store.close()
        reopened = restart_read(self.root, self.vault, self.http)
        self.assertEqual(initial["identity_sha256"], reopened["identity_sha256"])
        self.store = Store(self.root / "oauth.sqlite")
        self.addCleanup(self.store.close)
        result = disconnect(self.store, self.vault, connection["id"])
        self.assertEqual("UNKNOWN_OWNER_ACTION_REQUIRED", result["remote_revocation"])
        self.assertEqual({}, self.vault.values)
        self.store.close()
        durable = b"".join(p.read_bytes() for p in self.root.rglob("*") if p.is_file())
        for private in (
            b"private-mail",
            b"private-login",
            b"private-name",
            b"synthetic-private-token",
            b"synthetic-device-secret",
        ):
            self.assertNotIn(private, durable)

    def test_federation_current_history_public_and_no_private_retention(self):
        connection = self.authorize()
        reads = Reads(self.store, self.vault, connection, self.http)
        try:
            result = federation(self.root, reads, self.fixture)
        finally:
            reads.close()
        self.assertEqual(1, result["now"]["value"])
        self.assertEqual("REPORTED", result["now"]["status"])
        self.assertEqual(-1, result["history"]["value"])
        self.assertEqual("RECALLED", result["history"]["status"])
        self.assertIn("archive event", result["conflict"])
        self.assertNotIn("private-mail", json.dumps(result))
        self.assertEqual(
            ("github.repositories.get", {"path": {"owner": "python", "repo": "cpython"}}, False),
            self.http.calls[-1],
        )
        self.assertNotIn(b"private-mail", (self.root / "archive.sqlite").read_bytes())

    def test_private_source_failure_cannot_pass_federation_using_stale_memory(self):
        connection = self.authorize()
        self.http.private_fail = True
        reads = Reads(self.store, self.vault, connection, self.http)
        try:
            with self.assertRaisesRegex(AcceptanceError, "private_read.github.emails"):
                federation(self.root, reads, self.fixture)
        finally:
            reads.close()

    def test_failed_contract_releases_private_payload(self):
        connection = self.authorize()
        self.http.bad_contract = True
        reads = Reads(self.store, self.vault, connection, self.http)
        # Oversized email list fails before any private output/persistence.
        with patch.object(
            self.http,
            "request",
            return_value=({"items": [{}] * 101}, "https://api.github.com/user/emails"),
        ):
            with self.assertRaisesRegex(AcceptanceError, "private_read.emails_bound"):
                reads.read("github.emails", self.fixture)
        self.assertEqual({}, reads.fabric.outcomes)
        reads.close()

    def test_missing_vault_entry_blocks_reopen_and_does_not_borrow_environment(self):
        connection = self.authorize()
        save(
            self.root,
            "checkpoint.json",
            {
                "fixture_id": self.fixture,
                "connection_id": connection["id"],
                "identity_sha256": "irrelevant",
            },
        )
        self.vault.delete(connection["credential_ref"])
        with patch.dict(
            os.environ, {"GITHUB_TOKEN": "borrowed-secret", "GH_TOKEN": "borrowed-secret"}
        ):
            with self.assertRaisesRegex(AcceptanceError, "oauth.connection_ready"):
                restart_read(self.root, self.vault, self.http)
        self.assertEqual([], self.http.calls)

    def test_disconnect_fails_if_vault_deletion_did_not_take_effect(self):
        connection = self.authorize()
        with patch.object(self.vault, "delete"):
            with self.assertRaisesRegex(AcceptanceError, "disconnect.credential_absent"):
                disconnect(self.store, self.vault, connection["id"])

    def test_disconnect_blocks_existing_connector_without_another_http_call(self):
        connection = self.authorize()
        reads = Reads(self.store, self.vault, connection, self.http)
        disconnect(self.store, self.vault, connection["id"])
        try:
            with self.assertRaisesRegex(AcceptanceError, "private_read.github.owner"):
                reads.read("github.owner", self.fixture)
            self.assertEqual([], self.http.calls)
        finally:
            reads.close()

    def test_complete_synthetic_harness_and_restart_command_filter_auth_environment(self):
        actual_enroll = enroll

        def flow_factory(store, vault):
            return GitHubDeviceFlow(store, vault, self.request, lambda: self.now)

        def child(argv, **kwargs):
            self.assertIn("--restart-read", argv)
            self.assertEqual(Path(__file__).resolve().parents[1], kwargs["cwd"])
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertNotIn("synthetic-private-token", str(argv))
            restart_read(self.root, self.vault, self.http)
            return SimpleNamespace(returncode=0)

        with (
            patch("scripts.verify_gate_b_oauth.GitHubDeviceFlow", side_effect=flow_factory),
            patch(
                "scripts.verify_gate_b_oauth.enroll",
                side_effect=lambda flow, client, confirm: actual_enroll(
                    flow, client, confirm, lambda _: None, self.wait
                ),
            ),
            patch("builtins.input", return_value="AUTHORIZED"),
            patch("oscar.connectors.HTTPSConnector.request", side_effect=self.http.request),
            patch("scripts.verify_gate_b_oauth.subprocess.run", side_effect=child),
            patch.dict(os.environ, {"GITHUB_TOKEN": "borrowed-secret"}),
        ):
            result = run(self.root, "registered_fixture_client", self.vault)
        self.assertEqual("PRIVATE_READ_LIFECYCLE_AND_FEDERATION_CHECKS_PASSED", result["status"])
        self.assertEqual("PARTIAL", result["gate_b"])
        self.assertEqual({}, self.vault.values)
        self.assertNotIn("private-mail", json.dumps(result))

    def test_existing_root_and_absent_authority_fail_before_network(self):
        for extra, expected in (
            ([], "precondition.explicit_owner_authority"),
            (["--owner-authorized"], "precondition.fresh_root"),
        ):
            with (
                patch("scripts.verify_gate_b_oauth.os.name", "nt"),
                patch.object(
                    sys,
                    "argv",
                    [
                        "harness",
                        "--root",
                        str(self.root),
                        "--client-id",
                        "registered_fixture_client",
                        *extra,
                    ],
                ),
                patch("scripts.verify_gate_b_oauth.WindowsCredentialStore") as vault,
            ):
                with self.assertRaisesRegex(AcceptanceError, expected):
                    main()
                vault.assert_not_called()

    def test_module_entrypoint_imports_without_starting_oauth(self):
        result = subprocess.run(
            [sys.executable, "-m", "scripts.verify_gate_b_oauth", "--help"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(0, result.returncode)
        self.assertIn(b"--client-id", result.stdout)

    def test_ambiguous_exchange_is_named_and_never_replayed(self):
        actual = self.request
        calls = []

        def interrupted(path, fields):
            calls.append(path)
            if path == "/login/oauth/access_token":
                raise OSError("private-token-and-email")
            return actual(path, fields)

        self.flow.request = interrupted
        with self.assertRaisesRegex(AcceptanceError, "oauth.exchange_ambiguous") as failure:
            self.authorize()
        self.assertEqual(2, len(calls))
        report = failure_record(self.root, failure.exception)
        self.assertEqual("oauth", report["phase"])
        self.assertEqual("oauth.exchange_ambiguous", report["check"])
        self.assertNotIn("private-token-and-email", json.dumps(report))
        cleanup(self.root, self.vault)

    def test_unexpected_exception_preserves_phase_without_private_exception_text(self):
        save(self.root, "progress.json", {"phase": "private_read.initial"})
        report = failure_record(self.root, RuntimeError("private-email-and-token"))
        self.assertEqual("private_read.initial", report["check"])
        self.assertNotIn("private-email-and-token", json.dumps(report))

    @unittest.skipUnless(os.name == "nt", "actual native Windows vault")
    def test_native_synthetic_connection_reopen_and_delete(self):
        vault = WindowsCredentialStore()
        self.now = time()
        flow = GitHubDeviceFlow(self.store, vault, self.request, lambda: self.now)
        try:
            connection = enroll(
                flow, "registered_fixture_client", lambda: "AUTHORIZED", lambda _: None, self.wait
            )
            reads = Reads(self.store, vault, connection, self.http)
            initial = snapshot(reads, self.fixture)
            reads.close()
            save(
                self.root,
                "checkpoint.json",
                {
                    "fixture_id": self.fixture,
                    "connection_id": connection["id"],
                    "identity_sha256": initial["identity_sha256"],
                },
            )
            self.store.close()
            child = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; "
                    "from scripts.verify_gate_b_oauth import restart_read; "
                    "from oscar.secure_credentials import WindowsCredentialStore; "
                    "from tests.test_oauth_acceptance import HTTP; "
                    "restart_read(Path(sys.argv[1]),WindowsCredentialStore(),HTTP())",
                    str(self.root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                timeout=15,
            )
            self.assertEqual(0, child.returncode, "synthetic process/vault reopen failed")
            self.store = Store(self.root / "oauth.sqlite")
            self.addCleanup(self.store.close)
            disconnect(self.store, WindowsCredentialStore(), connection["id"])
        finally:
            cleanup(self.root, vault)


if __name__ == "__main__":
    unittest.main()
