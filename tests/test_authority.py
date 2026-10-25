"""Synthetic owner signatures exercise actual Runtime/Dispatcher authority."""

import base64
import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.authority import StandingAuthority, delegated_confirmation
from oscar.capabilities import FileExecutor
from oscar.connectors import RiskLevel
from oscar.contracts import TaskState
from oscar.grid import Grid, Node, NodeRole, SessionHandle
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.mcp_client import MCPServerConfig, executable_digest
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.storage import Store


class StandingAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.now = 1_800_000_000.0
        self.h = Harness(
            root / "core.sqlite",
            root / "files",
            Path("config/development-models.json"),
            clock=lambda: self.now,
            start_services=False,
        )
        self.addCleanup(self.h.close)
        self.authority = StandingAuthority(self.h.store, self.h.grid)
        self.policy = PersonalPolicy(self.h.store)
        self.owner_scope = "grid:approve"
        self.h.grid.register(
            Node("synthetic-owner", NodeRole.MOBILE, ("heartbeat", self.owner_scope))
        )
        self.owner = self.h.grid.pair("synthetic-owner", ("heartbeat", self.owner_scope))
        self.h.grid.heartbeat(self.owner)
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public = base64.b64encode(
            self.key.public_key().public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).decode()
        self.h.store.put(
            "sunday_key",
            self.owner.node_id,
            {"session_id": self.owner.id, "public_key": self.public},
        )
        self.capabilities = self.h.store.get("node", self.h.node_id)["capabilities"]
        self.capability = next(cap for cap in self.capabilities if cap["id"] == "files.write")
        self.grants = frozenset({self.owner_scope})

    def payload(self, mode="full", **changes):
        return {
            "mode": mode,
            "lifetime_seconds": 600,
            "capabilities": [
                {
                    "node_id": self.h.node_id,
                    "session_id": self.h.session.id,
                    "capability_id": self.capability["id"],
                }
            ],
            "account_ids": [],
            "resolve_ask_rules": sorted(
                rule.id for rule in self.policy.rules() if rule.enabled and rule.effect == "ask"
            )
            if mode == "full"
            else [],
            **changes,
        }

    def review(self, payload=None):
        return self.authority.challenge(
            self.owner.node_id,
            self.owner.id,
            self.owner_scope,
            self.grants,
            payload or self.payload(),
        )

    def signature(self, review):
        return {
            "challenge_id": review["challenge_id"],
            "signature": base64.b64encode(
                self.key.sign(
                    base64.b64decode(review["signing_payload"]),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                    hashes.SHA256(),
                )
            ).decode(),
        }

    def activate(self, mode="full", **changes):
        review = self.review(self.payload(mode, **changes))
        return self.complete(review)

    def complete(self, review, **changes):
        return self.authority.complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            {**self.signature(review), **changes},
        )

    def task(self):
        return self.h.runtime.create(
            Intent(
                "Write independently verified result",
                "file_write",
                "result.txt",
                "signed owner delegation",
            )
        )

    def rule(self, effect=PolicyEffect.ASK):
        self.policy.save(
            PolicyRule(
                "explicit-rule", "files.write", effect, "synthetic owner", self.now, self.now, {}
            ),
            owner_authorized=True,
        )

    def test_signed_full_runtime_executes_without_per_action_receipt_and_verifies(self):
        self.rule()
        self.activate()
        task = self.task()
        result = self.h.runtime.run(task.id, self.h.executive.targets)
        self.assertEqual(TaskState.VERIFIED, result.state)
        self.assertEqual(b"signed owner delegation", self.h.files.read("result.txt"))
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        pin = self.h.store.get("task_authority", task.id)
        self.assertEqual(1, pin["epoch"])
        self.assertEqual(1, pin["task_generation"])
        self.assertTrue(
            delegated_confirmation(
                self.h.store, self.h.grid, task.id, self.capability, self.h.session
            )
        )

    def test_secure_ordinary_and_protected_are_different(self):
        high = {**self.capability, "risk": "high"}
        node = self.h.store.get("node", self.h.node_id)
        self.h.store.put(
            "node",
            self.h.node_id,
            {
                **node,
                "capabilities": [
                    high if cap["id"] == high["id"] else cap for cap in node["capabilities"]
                ],
            },
        )
        self.capability = high
        self.activate("secure")
        self.assertFalse(self.authority.permits(high, self.h.session))
        self.activate("full")
        self.assertTrue(self.authority.permits(high, self.h.session))
        self.capability = self.capabilities[0]
        self.activate("secure")
        self.assertTrue(self.authority.permits(self.capability, self.h.session))

    def test_ask_and_expired_authority_never_supply_standing_confirmation(self):
        self.assertFalse(self.authority.permits(self.capability, self.h.session))
        self.activate()
        self.now += 601
        self.assertEqual("ask", self.authority.snapshot()["mode"])
        self.assertFalse(self.authority.permits(self.capability, self.h.session))

    def test_replay_wrong_signature_wrong_session_and_expiry_denied(self):
        review = self.review()
        with self.assertRaises(PermissionError):
            self.complete(review, signature=base64.b64encode(b"forged").decode())
        self.complete(review)
        with self.assertRaises(PermissionError):
            self.complete(review)
        review = self.review()
        with self.assertRaises(PermissionError):
            self.authority.complete(
                self.owner.node_id,
                self.h.session.id,
                self.public,
                self.owner_scope,
                self.grants,
                self.signature(review),
            )
        self.now += 31
        with self.assertRaises(PermissionError):
            self.complete(review)

    def test_changed_policy_and_scope_before_activation_are_denied(self):
        review = self.review()
        self.rule()
        with self.assertRaises((ValueError, PermissionError)):
            self.complete(review)
        with self.assertRaises(ValueError):
            self.review(self.payload(resolve_ask_rules=[]))
        self.activate()
        self.rule(PolicyEffect.DENY)
        self.assertFalse(self.authority.permits(self.capability, self.h.session))
        self.activate()
        self.assertFalse(self.authority.permits(self.capability, self.h.session))

    def test_exact_capability_device_session_and_token_bindings(self):
        self.activate()
        self.assertFalse(
            self.authority.permits({**self.capability, "risk": "critical"}, self.h.session)
        )
        self.assertFalse(self.authority.permits(self.capability, self.owner))
        stolen = SessionHandle(self.h.session.id, self.h.node_id, "invalid")
        self.assertFalse(self.authority.permits(self.capability, stolen))
        node = self.h.store.get("node", self.h.node_id)
        self.h.store.put("node", self.h.node_id, {**node, "scopes": []})
        self.assertFalse(self.authority.permits(self.capability, self.h.session))

    def test_account_generation_and_cross_account_task_are_fenced(self):
        account = self.h.accounts.add("fixture", "tenant", "subject", "one", verified=True)
        self.activate(account_ids=[account.id])
        task = self.task()
        self.authority.bind(task.id, self.capability, self.h.session)
        self.h.accounts.disconnect(account.id)
        with self.assertRaises(PermissionError):
            self.authority.check_task(task.id, self.capability, self.h.session)
        self.activate()
        other = self.h.accounts.add("fixture", "tenant", "other", "two", verified=True)
        plan = self.h.store.get("plan", task.id)
        self.h.store.delete("task_authority", task.id)
        self.h.store.put(
            "plan", task.id, {**plan, "parameters": {**plan["parameters"], "account_id": other.id}}
        )
        with self.assertRaises(PermissionError):
            self.authority.bind(task.id, self.capability, self.h.session)

    def test_connector_objective_account_pin_is_checked_before_binding(self):
        account = self.h.accounts.add("fixture", "tenant", "subject", "one", verified=True)
        self.activate(account_ids=[account.id])
        task = self.task()
        objective = self.h.store.get("objective", task.objective_id)
        for pin in (
            {"id": "another-account", "generation": account.generation},
            {"id": account.id, "generation": account.generation + 1},
        ):
            self.h.store.put(
                "objective",
                task.objective_id,
                {**objective, "criterion": {"kind": "unavailable", "connector_account": pin}},
            )
            with self.assertRaises(PermissionError):
                self.authority.bind(task.id, self.capability, self.h.session)
            self.assertEqual([], self.h.store.all("task_authority"))
        self.h.store.put(
            "objective",
            task.objective_id,
            {
                **objective,
                "criterion": {
                    "kind": "unavailable",
                    "connector_account": {"id": account.id, "generation": account.generation},
                },
            },
        )
        self.assertIsNotNone(self.authority.bind(task.id, self.capability, self.h.session))

    def test_revoke_immediately_before_effect_does_not_write(self):
        self.activate()
        task = self.task()
        original = FileExecutor(self.h.files)

        def withdraw(action, cancellation):
            self.authority.revoke(self.owner.node_id, self.owner.id, self.owner_scope, self.grants)
            return original(action, cancellation)

        self.h.dispatcher.executors["files.write"] = withdraw
        result = self.h.runtime.run(task.id, self.h.executive.targets)
        self.assertEqual(TaskState.CANCELLED, result.state)
        self.assertFalse(self.h.files.exists("result.txt"))
        self.assertEqual(2, self.authority.snapshot()["epoch"])

    def test_downgrade_never_rebinds_old_task_to_new_epoch(self):
        self.activate()
        task = self.task()
        self.authority.bind(task.id, self.capability, self.h.session)
        self.authority.revoke(self.owner.node_id, self.owner.id, self.owner_scope, self.grants)
        self.activate()
        with self.assertRaises(PermissionError):
            self.authority.bind(task.id, self.capability, self.h.session)
        self.assertEqual(
            TaskState.BLOCKED, self.h.runtime.run(task.id, self.h.executive.targets).state
        )

    def test_restart_preserves_signature_and_revoked_identity_stays_revoked(self):
        self.activate()
        reopened = Store(Path(self.temporary.name) / "core.sqlite")
        self.addCleanup(reopened.close)
        restored = StandingAuthority(reopened, Grid(reopened, lambda: self.now))
        self.assertTrue(restored.permits(self.capability, self.h.session))
        self.h.grid.revoke(self.owner.node_id)
        self.assertEqual("ask", restored.snapshot()["mode"])
        self.assertFalse(restored.permits(self.capability, self.h.session))

    @unittest.skipUnless(importlib.util.find_spec("mcp"), "install oscar-brain[mcp]")
    def test_full_access_actual_mcp_write_has_no_per_action_confirmation(self):
        account = self.h.accounts.add("fixture", "synthetic", "writer", "writer", verified=True)
        command = str(Path(sys.executable).resolve())
        script = str(Path(__file__).parent.resolve() / "fixtures" / "mcp_workspace.py")
        self.h.plugins.register(
            MCPServerConfig(
                "writer",
                "writer",
                account.id,
                command=command,
                arguments=("-I", script, str(self.h.files.root), account.id),
                cwd=self.temporary.name,
                reviewed_files=(
                    (command, executable_digest(command)),
                    (script, executable_digest(script)),
                ),
            ),
            {"read_file": RiskLevel.READ, "write_file": RiskLevel.WRITE},
            owner_reviewed=True,
        )
        self.h.plugins.connect("writer")
        mount = self.h.mount_connectors(
            "synthetic-plugins", ("connectors:read", "connectors:write"), owner_authorized=True
        )
        capability = mount.capability("mcp.write_file", account_id=account.id)
        selected = [
            {
                "node_id": mount.node_id,
                "session_id": mount.session.id,
                "capability_id": capability.id,
            }
        ]
        self.activate(capabilities=selected, account_ids=[account.id])
        request_ref = self.h.connectors.stage(
            {
                "path": {"name": "write_file"},
                "body": {"path": "delegated.txt", "content": "Actual MCP standing delegation"},
            }
        )
        task = self.h.runtime.create(
            Intent(
                "Save through authorized MCP",
                "capability",
                capability_kind=capability.id,
                parameters={"request_ref": request_ref},
                criterion={
                    "kind": "file_exact",
                    "path": "delegated.txt",
                    "content": "Actual MCP standing delegation",
                },
            )
        )
        result = self.h.runtime.run(task.id, self.h.executive.targets)
        self.assertEqual(TaskState.VERIFIED, result.state)
        self.assertEqual(b"Actual MCP standing delegation", self.h.files.read("delegated.txt"))
        self.assertEqual([], self.h.store.all("executive_confirmation"))
        self.assertEqual("full", self.h.store.get("task_authority", task.id)["mode"])


class DesktopDelegationTests(unittest.TestCase):
    from tests import test_desktop as desktop_fixture

    setUp = desktop_fixture.DesktopTests.setUp
    call = desktop_fixture.DesktopTests.call
    ask = desktop_fixture.DesktopTests.ask

    def activate(self):
        policy = PersonalPolicy(self.h.store)
        payload = {
            "mode": "full",
            "lifetime_seconds": 600,
            "capabilities": [
                {
                    "node_id": self.h.node_id,
                    "session_id": self.h.session.id,
                    "capability_id": "math.add",
                }
            ],
            "account_ids": [],
            "resolve_ask_rules": sorted(
                r.id for r in policy.rules() if r.enabled and r.effect == "ask"
            ),
        }
        review = self.call("authority_challenge", payload)
        signature = self.key.sign(
            base64.b64decode(review["signing_payload"]),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        return self.call(
            "authority_complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": base64.b64encode(signature).decode(),
            },
        )

    def test_native_surface_full_executes_without_per_action_review_then_revocation_restores_ask(
        self,
    ):
        self.assertEqual("planned", self.ask()["state"])
        self.activate()
        result = self.ask("4 + 5")
        self.assertEqual(
            ("verified", "9", False),
            (result["state"], result["value"], result["approval_required"]),
        )
        self.assertEqual([], self.h.store.all("sunday_challenge"))
        self.call("authority_revoke", {})
        self.assertEqual("planned", self.ask("5 + 6")["state"])

    def test_expired_standing_delegation_cannot_execute_a_new_surface_request(self):
        self.activate()
        self.now[0] += 601
        self.h.grid.heartbeat(self.h.session)
        self.h.grid.heartbeat(self.session)
        self.assertEqual("planned", self.ask("8 + 9")["state"])
