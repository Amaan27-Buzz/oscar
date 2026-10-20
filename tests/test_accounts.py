"""Synthetic account-backed filesystem provider; no external accounts or credentials."""

import json
import os
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from oscar.accounts import AccountRegistry
from oscar.capabilities import Cancellation
from oscar.connectors import (
    ConnectionState,
    ConnectorCapability,
    ConnectorFabric,
    ConnectorInstance,
    ConnectorManifest,
    CredentialRef,
    EnvironmentSecrets,
    RiskLevel,
)
from oscar.contracts import Action, Task, new_id, record
from oscar.policy import PersonalPolicy
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store


class AccountFiles:
    """Trusted synthetic provider authenticates tokens to separate backing directories."""

    def __init__(self, root):
        self.root = root
        self.calls = []

    def request(self, manifest, spec, parameters, secret):
        subject = {"synthetic-token-a": "a", "synthetic-token-b": "b"}[secret]
        path = self.root / subject
        self.calls.append(subject)
        if spec.method == "PUT":
            path.write_text(parameters["body"]["value"], encoding="utf8")
        return {"id": subject, "value": path.read_text(encoding="utf8")}, manifest.base_url


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state.sqlite")
        self.now = 1000
        self.registry = AccountRegistry(self.store, lambda: self.now)
        self.manifest = ConnectorManifest(
            "fixture.files",
            "fixture",
            "https://fixture.invalid",
            (
                ConnectorCapability("fixture.read", "GET", "/document", ("read",)),
                ConnectorCapability(
                    "fixture.write",
                    "PUT",
                    "/document",
                    ("write",),
                    RiskLevel.WRITE,
                    body_required=True,
                ),
            ),
        )
        self.http = AccountFiles(self.root)
        self.secrets = EnvironmentSecrets(
            {"a": "A", "b": "B"}, {"A": "synthetic-token-a", "B": "synthetic-token-b"}
        )
        self.fabric = ConnectorFabric(
            self.store, self.secrets, PersonalPolicy(self.store), self.http, accounts=self.registry
        )
        self.accounts = []
        for key in ("a", "b"):
            (self.root / key).write_text("document-" + key, encoding="utf8")
            account = self.registry.add("fixture", "tenant", key, "Alias " + key, verified=True)
            account = self.registry.bind(
                account.id,
                self.manifest.id,
                CredentialRef(key),
                {"read", "write"},
                self.manifest.base_url,
            )
            self.accounts.append(account)
            self.fabric.install(
                ConnectorInstance(
                    key,
                    self.manifest,
                    CredentialRef(key),
                    frozenset({"read", "write"}),
                    account_id=account.id,
                    account_generation=account.generation,
                    account_audience=self.manifest.base_url,
                )
            )
        self.task = Task(new_id(), new_id(), new_id())
        self.store.put("task", self.task.id, record(self.task))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def execute(self, key, *, write=None, confirmed=False):
        name = "fixture.write" if write is not None else "fixture.read"
        action = Action(
            new_id(),
            self.task.id,
            self.task.correlation_id,
            key + ":" + name,
            {"body": {"value": write}} if write is not None else {},
            new_id(),
            "owner",
        )
        return self.fabric.execute(
            key,
            name,
            action,
            Cancellation(self.store, self.task.id),
            frozenset({"connectors:read", "connectors:write"}),
            confirmed=confirmed,
        )

    def test_two_accounts_actually_execute_independent_tools(self):
        self.assertEqual("document-a", self.execute("a").payload["value"])
        self.assertEqual("document-b", self.execute("b").payload["value"])
        self.assertFalse(self.execute("a", write="updated").result.success)
        self.assertTrue(self.execute("a", write="updated", confirmed=True).result.success)
        self.assertEqual("updated", self.execute("a").payload["value"])
        self.assertEqual("document-b", self.execute("b").payload["value"])
        ledger = json.dumps(self.store.ledger(self.task.id))
        self.assertIn(self.accounts[0].id, ledger)
        self.assertNotIn("synthetic-token", ledger)
        self.assertNotIn("document-b", ledger)

    def test_alias_rename_default_and_material_ambiguity(self):
        with self.assertRaisesRegex(PermissionError, "ambiguous"):
            self.registry.select("fixture", self.manifest.id)
        self.registry.set_default(self.accounts[1].id, self.manifest.id)
        self.assertEqual(self.accounts[1].id, self.registry.select("fixture", self.manifest.id).id)
        renamed = self.registry.rename(self.accounts[0].id, "Any arbitrary label")
        self.assertEqual(self.accounts[0].generation, renamed.generation)
        self.assertEqual(
            renamed.id, self.registry.select("fixture", self.manifest.id, alias=renamed.alias).id
        )
        self.assertTrue(self.execute("a").result.success)
        self.registry.rename(self.accounts[1].id, renamed.alias)
        with self.assertRaisesRegex(PermissionError, "ambiguous"):
            self.registry.select("fixture", self.manifest.id, alias=renamed.alias)

    def test_scope_withdrawal_and_revocation_fence_installed_session(self):
        account = self.accounts[0]
        changed = self.registry.withdraw_scopes(account.id, self.manifest.id, {"write"})
        self.assertFalse(self.execute("a").result.success)
        self.fabric.instances["a"] = replace(
            self.fabric.instances["a"], account_generation=changed.generation
        )
        self.assertTrue(self.execute("a").result.success)
        self.assertFalse(self.execute("a", write="forbidden", confirmed=True).result.success)
        self.registry.disconnect(account.id)
        self.assertFalse(self.execute("a").result.success)
        self.assertTrue(self.execute("b").result.success)

    def test_cross_account_provider_audience_and_organization_denial(self):
        a, b = self.accounts
        with self.assertRaises(PermissionError):
            self.registry.bind(b.id, self.manifest.id, CredentialRef("a"), {"read"}, "wrong")
        for changed in (
            replace(self.fabric.instances["a"], credential=CredentialRef("b")),
            replace(self.fabric.instances["a"], account_id=b.id),
            replace(self.fabric.instances["a"], account_audience="https://unrelated.invalid"),
        ):
            self.assertEqual(
                ConnectionState.AUTH_MISSING,
                self.fabric.state(changed, self.manifest.capabilities[0]),
            )
        account = self.registry.bind(
            a.id,
            self.manifest.id,
            CredentialRef("a"),
            {"read", "write"},
            self.manifest.base_url,
            denied_capabilities={"fixture.write"},
        )
        self.fabric.instances["a"] = replace(
            self.fabric.instances["a"], account_generation=account.generation
        )
        self.assertTrue(self.execute("a").result.success)
        self.assertFalse(self.execute("a", write="forbidden", confirmed=True).result.success)

    def test_expiry_and_wrong_generation_stop_before_provider(self):
        account = self.registry.bind(
            self.accounts[0].id,
            self.manifest.id,
            CredentialRef("a"),
            {"read"},
            self.manifest.base_url,
            expires_at=1001,
        )
        self.fabric.instances["a"] = replace(
            self.fabric.instances["a"], account_generation=account.generation
        )
        self.now = 1001
        self.assertFalse(self.execute("a").result.success)
        self.assertEqual([], self.http.calls)

    def test_revocation_during_secret_resolution_is_rechecked_before_dispatch(self):
        original = self.secrets.resolve
        calls = 0

        def revoke_on_dispatch(reference):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.registry.disconnect(self.accounts[0].id)
            return original(reference)

        self.secrets.resolve = revoke_on_dispatch
        self.assertFalse(self.execute("a").result.success)
        self.assertEqual([], self.http.calls)

    def test_provider_tenant_collision_and_operational_identity(self):
        a = self.accounts[0]
        other = self.registry.add("fixture", "other-tenant", a.subject, a.alias, verified=True)
        self.assertNotEqual(a.id, other.id)
        oscar = self.registry.operational_identity()
        self.assertIsNone(oscar.operational_email)
        own = self.registry.add(
            "fixture", "tenant", "oscar", "Operations", identity_class="oscar-owned", verified=True
        )
        self.assertNotEqual(a.id, own.id)
        with self.assertRaises(PermissionError):
            self.registry.add(
                "fixture",
                "tenant",
                a.subject,
                "Impersonation",
                identity_class="oscar-owned",
                verified=True,
            )
        with self.assertRaises(PermissionError):
            self.registry.add("fixture", "tenant", "unverified", "Any", verified=False)

    def test_restart_replacement_preserves_identity_but_fences_old_connection(self):
        oscar = self.registry.operational_identity()
        old = self.accounts[0]
        self.store.close()
        self.store = Store(self.root / "state.sqlite")
        self.registry = AccountRegistry(self.store, lambda: self.now)
        self.assertEqual(oscar, self.registry.operational_identity())
        self.assertEqual(old, self.registry.get(old.id))
        replacement = self.registry.bind(
            old.id, self.manifest.id, CredentialRef("replacement"), {"read"}, self.manifest.base_url
        )
        self.assertEqual(old.id, replacement.id)
        with self.assertRaises(PermissionError):
            self.registry.check(old.id, old.generation)
        with self.assertRaises(PermissionError):
            self.registry.bind(
                self.accounts[1].id,
                self.manifest.id,
                CredentialRef("a"),
                {"read"},
                self.manifest.base_url,
            )
        with self.assertRaises(PermissionError):
            self.registry.bind(
                old.id,
                self.manifest.id,
                CredentialRef("third"),
                {"read"},
                self.manifest.base_url,
                expected_generation=old.generation,
            )

    @unittest.skipUnless(os.name == "nt", "native Windows broker interoperability")
    def test_two_native_vault_accounts_execute_after_independent_process_restart(self):
        vault = WindowsCredentialStore()
        references = []
        try:
            for account in self.accounts:
                reference = vault.put("synthetic-token-" + account.subject)
                references.append(reference)
                self.registry.bind(
                    account.id,
                    self.manifest.id,
                    CredentialRef(reference),
                    {"read"},
                    self.manifest.base_url,
                )
            self.store.close()
            script = """
import sys
from pathlib import Path
from oscar.accounts import AccountRegistry
from oscar.capabilities import Cancellation
from oscar.connectors import (ConnectorFabric, ConnectorInstance, ConnectorCapability,
    ConnectorManifest, CredentialRef)
from oscar.contracts import Action, Task, new_id, record
from oscar.oauth_device import VaultResolver
from oscar.policy import PersonalPolicy
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store
from tests.test_accounts import AccountFiles
store = Store(sys.argv[1])
registry = AccountRegistry(store)
manifest = ConnectorManifest('fixture.files', 'fixture', 'https://fixture.invalid',
    (ConnectorCapability('fixture.read', 'GET', '/document', ('read',)),))
fabric = ConnectorFabric(store, VaultResolver(WindowsCredentialStore()), PersonalPolicy(store),
    AccountFiles(Path(sys.argv[2])), accounts=registry)
task = Task(new_id(), new_id(), new_id())
store.put('task', task.id, record(task))
for account in registry.list_accounts():
    binding = account.services[manifest.id]
    fabric.install(ConnectorInstance(account.id, manifest, CredentialRef(binding.credential_ref),
        frozenset(binding.scopes), account_id=account.id, account_generation=account.generation,
        account_audience=binding.audience))
    action = Action(new_id(), task.id, task.correlation_id, account.id + ':fixture.read',
        {}, new_id(), 'owner')
    outcome = fabric.execute(account.id, 'fixture.read', action, Cancellation(store, task.id),
        frozenset({'connectors:read'}))
    assert outcome.result.success
    assert outcome.payload['value'] == 'document-' + account.subject
store.close()
print('two native account executions after restart PASS')
"""
            process = subprocess.run(
                [sys.executable, "-c", script, str(self.root / "state.sqlite"), str(self.root)],
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual(
                "two native account executions after restart PASS", process.stdout.strip()
            )
        finally:
            for reference in references:
                vault.delete(reference)
            self.store = Store(self.root / "state.sqlite")
