"""Acceptance must distinguish a real capacity block from a false success."""

import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO
from types import SimpleNamespace

from oscar.credentials import CredentialPool
from oscar.freshness import Authority, SourceRef
from oscar.models import DiscoveredModel, Failure, Inventory, Mode, ProviderError, ProviderResponse
from scripts.verify_club_a_live import Verification
from scripts.verify_gate_a_routing import focused_routing

from .support import RouterRig


class FixtureVerification(Verification):
    def __init__(self, rig):
        self.h = SimpleNamespace(
            router=rig.router, registry=rig.registry, pool=rig.pool, store=rig.store
        )
        self.checks = []
        self.operations = []
        self.statuses = {}

    def account(self, provider_id, slot):
        pass


class FocusedRoutingAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.r = RouterRig()
        self.addCleanup(self.r.close)
        for provider_id, provider in list(self.r.registry.providers.items()):
            self.r.registry.providers[provider_id] = replace(provider, discovery_required=True)
        self.refresh_inventories()

    def run_acceptance(self, modes=None):
        with redirect_stdout(StringIO()):
            suite = FixtureVerification(self.r)
            return focused_routing(suite) if modes is None else focused_routing(suite, modes)

    def refresh_inventories(self):
        for slot in self.r.pool.slots.values():
            models = [
                DiscoveredModel(
                    model.id,
                    model.capabilities,
                    model.context_limit,
                    model.output_limit,
                    model.funding,
                )
                for model in self.r.registry.models.values()
                if model.provider_id == slot.provider
            ]
            self.r.registry.apply_inventory(
                Inventory(
                    slot.provider,
                    slot.id,
                    SourceRef(
                        "https://" + slot.provider + ".invalid/models",
                        Authority.LIVE_API,
                        "account",
                        self.r.clock(),
                    ),
                    tuple(models),
                )
            )

    def test_only_three_unresolved_modes_generate(self):
        self.r.adapter.steps = [
            ProviderResponse('{"ok":true}'),
            ProviderResponse("OSCAR_PROVIDER_OK"),
            ProviderResponse('{"ok":true}'),
        ]
        report = self.run_acceptance()
        self.assertEqual(len(self.r.adapter.calls), 3)
        self.assertEqual(
            [row["mode"] for row in report["operations"]],
            ["balanced", "heavy", "free_first"],
        )
        self.assertTrue(
            all(row["disposition"] == "VERIFIED_GENERATION" for row in report["operations"])
        )
        self.assertTrue(all(check["status"] == "PASS" for check in report["checks"]))

    def test_shared_cooldown_falls_back_to_unrelated_provider(self):
        provider = self.r.registry.providers["plentiful"]
        self.r.registry.providers["plentiful"] = replace(
            provider, credential_pools={}, quota_pool="plentiful/shared"
        )
        self.r.registry.models[("plentiful", "small")] = replace(
            self.r.registry.models[("plentiful", "small")], quality=5, affinities={"reasoning": 1}
        )
        self.r.registry.models[("scarce", "strong")] = replace(
            self.r.registry.models[("scarce", "strong")], quality=4
        )
        self.r.pool = CredentialPool(
            list(self.r.registry.providers.values()),
            {"FIXTURE_A": "synthetic-a", "FIXTURE_B": "synthetic-b", "FIXTURE_C": "synthetic-c"},
            self.r.store,
            self.r.clock,
        )
        self.r.router.pool = self.r.pool
        self.r.adapter.steps = [
            ProviderError(Failure.UNKNOWN_LIMIT, retry_after=60, http_status=429),
            ProviderResponse('{"ok":true}'),
            ProviderResponse("OSCAR_PROVIDER_OK"),
            ProviderResponse('{"ok":true}'),
        ]
        report = self.run_acceptance()
        first = report["operations"][0]
        self.assertEqual(first["attempts"], 2)
        self.assertEqual(first["provider"], "scarce")
        self.assertEqual(first["attempt_trace"][0]["error"], "limit_cause_unknown")
        self.assertFalse(self.r.pool.eligible("plentiful-2", 1, "small"))
        self.assertTrue(self.r.pool.eligible("scarce-1", 1, "strong"))
        self.assertTrue(all(row["acceptance"] == "PASS" for row in report["operations"]))
        self.assertEqual(self.r.adapter.calls.count(("plentiful", "small")), 1)

    def test_no_eligible_default_policy_route_is_truthful_block(self):
        for slot in self.r.pool.slots.values():
            slot.cooldown_until = self.r.clock() + 60
        report = self.run_acceptance()
        self.assertEqual(self.r.adapter.calls, [])
        self.assertTrue(
            all(row["disposition"] == "EXPECTED_BLOCKED" for row in report["operations"])
        )
        self.assertTrue(all(row["acceptance"] == "PASS" for row in report["operations"]))
        self.assertTrue(all(row["status"] == "BLOCKED" for row in report["operations"]))

    def test_mismatched_generation_never_becomes_acceptance_success(self):
        self.r.adapter.steps = [ProviderResponse('{"ok":false}')] * 3
        report = self.run_acceptance()
        self.assertTrue(all(row["acceptance"] == "FAIL" for row in report["operations"]))
        self.assertTrue(all(row["disposition"] == "UNRESOLVED" for row in report["operations"]))

    def test_bounded_failure_with_eligible_route_remains_unresolved(self):
        provider = self.r.registry.providers["plentiful"]
        self.r.registry.providers["plentiful"] = replace(
            provider,
            credential_envs={**provider.credential_envs, "plentiful-3": "FIXTURE_D"},
        )
        self.r.pool = CredentialPool(
            list(self.r.registry.providers.values()),
            {
                "FIXTURE_A": "synthetic-a",
                "FIXTURE_B": "synthetic-b",
                "FIXTURE_C": "synthetic-c",
                "FIXTURE_D": "synthetic-d",
            },
            self.r.store,
            self.r.clock,
        )
        self.r.router.pool = self.r.pool
        self.refresh_inventories()
        self.r.adapter.steps = [
            *([ProviderError(Failure.CREDENTIAL, http_status=401)] * 3),
            ProviderResponse("OSCAR_PROVIDER_OK"),
            ProviderResponse('{"ok":true}'),
        ]
        report = self.run_acceptance((Mode.BALANCED,))
        first = report["operations"][0]
        self.assertEqual(first["attempts"], 3)
        self.assertGreater(first["eligible_after"], 0)
        self.assertEqual(first["acceptance"], "FAIL")
        self.assertEqual(first["disposition"], "UNRESOLVED")

    def test_heavy_only_uses_current_text_capability_without_structured_prior(self):
        self.r.registry.models[("scarce", "strong")] = replace(
            self.r.registry.models[("scarce", "strong")], capabilities=frozenset({"text"})
        )
        self.refresh_inventories()
        self.r.adapter.steps = [ProviderResponse("OSCAR_PROVIDER_OK")]
        report = self.run_acceptance((Mode.HEAVY,))
        self.assertEqual(len(self.r.adapter.calls), 1)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["mode"], "heavy")
        self.assertEqual(report["operations"][0]["disposition"], "VERIFIED_GENERATION")

    def test_focused_modes_cannot_expand_to_other_live_modes(self):
        with self.assertRaises(ValueError):
            self.run_acceptance((Mode.AUTO,))
        with self.assertRaises(ValueError):
            self.run_acceptance((Mode.HEAVY, Mode.HEAVY))
        self.assertEqual(self.r.adapter.calls, [])
