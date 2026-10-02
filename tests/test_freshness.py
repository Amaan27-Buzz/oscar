"""Regression contracts for stale inventories, claim authority and live retrieval routing."""

import json
import unittest
from dataclasses import replace
from pathlib import Path

from oscar.capabilities import Cancellation
from oscar.contracts import Action, Task, new_id, record
from oscar.credentials import CredentialPool
from oscar.freshness import Authority, Freshness, SourceRef, prefer_source
from oscar.jev import ExecutionClass, Intent, decide
from oscar.models import DiscoveredModel, Failure, Funding, Inventory, ProviderError, RateLimits
from oscar.registry import Registry
from oscar.retrieval import (
    ProviderInventorySource,
    RetrievalExecutor,
    RetrievalRequest,
    RetrievalResult,
    RetrievedFact,
)
from oscar.router import Router, RouteUnavailable

from .support import RouterRig


class FreshInventoryTests(unittest.TestCase):
    def setUp(self):
        self.r = RouterRig()
        self.addCleanup(self.r.close)
        self.r.registry.providers["plentiful"] = replace(
            self.r.registry.providers["plentiful"], discovery_required=True
        )

    def inventory(self, ids=("model-new",), slot="plentiful-1", complete=True):
        return Inventory(
            "plentiful",
            slot,
            SourceRef(
                "https://plentiful.invalid/models", Authority.LIVE_API, "account", self.r.clock()
            ),
            tuple(DiscoveredModel(id, frozenset({"text"}), 8192, 1024, Funding.FREE) for id in ids),
            complete,
        )

    def test_a_stale_seed_absent_live_new_model_considered(self):
        r = self.r
        r.registry.apply_inventory(self.inventory())
        request = replace(r.request, min_quality=1, pinned_provider="plentiful")
        routes = r.router.rank(request)
        self.assertEqual({route.model for route in routes}, {"model-new"})
        self.assertEqual(
            r.registry.availability("plentiful", "small", "plentiful-1", r.clock()), "unavailable"
        )
        self.assertTrue(r.registry.conflicts)
        self.assertIn("inventory source", " ".join(routes[0].reasons))

    def test_e_live_api_wins_over_cached_availability_without_erasing_history(self):
        r = self.r
        old = r.registry.models[("plentiful", "small")]
        r.registry.apply_inventory(self.inventory(()))
        self.assertIn(("plentiful", "small"), r.registry.models)
        self.assertEqual(r.router.rank(replace(r.request, pinned_provider="plentiful")), [])
        self.assertEqual(old.provenance, r.registry.models[("plentiful", "small")].provenance)

    def test_account_absence_is_per_slot_not_provider_wide(self):
        r = self.r
        r.registry.apply_inventory(self.inventory((), "plentiful-1"))
        r.registry.apply_inventory(self.inventory(("small",), "plentiful-2"))
        self.assertEqual(
            r.router.rank(replace(r.request, pinned_provider="plentiful"))[0].slot, "plentiful-2"
        )

    def test_incomplete_page_does_not_claim_absent_model_unavailable(self):
        self.r.registry.apply_inventory(self.inventory((), complete=False))
        self.assertEqual(
            self.r.registry.availability("plentiful", "small", "plentiful-1", self.r.clock()),
            "UNKNOWN / incomplete inventory",
        )

    def test_expired_inventory_never_reactivates_seed_without_live_source(self):
        r = self.r
        r.registry.apply_inventory(self.inventory(("small",)))
        r.clock.now += 301
        with self.assertRaises(RouteUnavailable):
            r.router.execute(replace(r.request, pinned_provider="plentiful"))
        self.assertEqual(r.adapter.calls, [])

    def test_retired_even_if_live_listing_contains_identifier(self):
        r = self.r
        r.registry.models[("plentiful", "small")] = replace(
            r.registry.models[("plentiful", "small")], retired=True
        )
        r.registry.apply_inventory(self.inventory(("small",)))
        self.assertEqual(r.router.rank(replace(r.request, pinned_provider="plentiful")), [])

    def test_manifest_retirement_survives_newer_api_listing(self):
        registry = Registry.load(Path("config/development-models.json"))
        model_id = "gemini-3.1-flash-lite-preview"
        registry.apply_inventory(
            Inventory(
                "google",
                "google-1",
                SourceRef(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    Authority.LIVE_API,
                    "account",
                    self.r.clock(),
                ),
                (DiscoveredModel(model_id, frozenset({"text"}), 1048576, 65536),),
            )
        )
        model = registry.models[("google", model_id)]
        self.assertEqual(
            registry.availability("google", model_id, "google-1", self.r.clock()), "retired"
        )
        self.assertEqual(model.retirement_source.authority, Authority.DEPRECATION)
        self.assertEqual(model.metadata_source.authority, Authority.LIVE_API)

    def test_aggregator_backing_failure_does_not_disable_other_models(self):
        r = self.r
        provider = replace(
            r.registry.providers["plentiful"], id="openrouter", discovery_required=False
        )
        models = [
            replace(r.registry.models[("plentiful", "small")], provider_id="openrouter"),
            replace(
                r.registry.models[("plentiful", "small")],
                provider_id="openrouter",
                id="another-current-model",
            ),
        ]
        registry = Registry([provider], models)
        pool = CredentialPool(
            [provider], {"FIXTURE_A": "synthetic-a", "FIXTURE_B": "synthetic-b"}, clock=r.clock
        )
        router = Router(registry, pool, {"test": r.adapter}, r.store, r.clock)
        r.adapter.steps = [ProviderError(Failure.PROVIDER)]
        result = router.execute(r.request)
        self.assertEqual(result.attempts, 2)
        self.assertNotEqual(r.adapter.calls[0][1], r.adapter.calls[1][1])
        self.assertEqual(result.route.provider, "openrouter")

    def test_late_old_inventory_cannot_override_new_snapshot(self):
        fresh = self.inventory(("model-new",))
        old = replace(
            self.inventory(("small",)),
            source=replace(fresh.source, observed_at=self.r.clock() - 10),
        )
        self.r.registry.apply_inventory(fresh)
        self.r.registry.apply_inventory(old)
        self.assertEqual(self.r.registry.inventories[("plentiful", "plentiful-1")], fresh)

    def test_generation_is_separate_from_visibility_and_funding(self):
        r = self.r
        model = r.registry.models[("plentiful", "small")]
        r.registry.models[("plentiful", "small")] = replace(model, funding=Funding.UNKNOWN)
        r.registry.apply_inventory(self.inventory(("small",)))
        r.registry.observe_generation("plentiful", "small", "plentiful-1", r.clock(), True)
        self.assertEqual(r.registry.models[("plentiful", "small")].funding, Funding.UNKNOWN)
        self.assertEqual(r.registry.models[("plentiful", "small")].last_verified, r.clock())

    def test_new_listing_cannot_override_current_generation_access_denial(self):
        r = self.r
        r.registry.apply_inventory(self.inventory(("small",)))
        r.registry.observe_generation(
            "plentiful", "small", "plentiful-1", r.clock(), False, Failure.FUNDING.value
        )
        r.clock.now += 1
        r.registry.apply_inventory(self.inventory(("small",)))
        self.assertEqual(
            r.registry.availability("plentiful", "small", "plentiful-1", r.clock()),
            "unavailable",
        )

    def test_account_limits_cannot_borrow_larger_sibling_inventory(self):
        r = self.r
        small = self.inventory(("small",), "plentiful-1")
        large = self.inventory(("small",), "plentiful-2")
        small = replace(
            small, models=(replace(small.models[0], context_limit=1024, output_limit=64),)
        )
        r.registry.apply_inventory(small)
        r.registry.apply_inventory(large)
        routes = r.router.rank(
            replace(r.request, pinned_provider="plentiful", max_output_tokens=128)
        )
        self.assertEqual({route.slot for route in routes}, {"plentiful-2"})

    def test_account_pricing_does_not_borrow_zero_price_from_another_key(self):
        r = self.r
        provider = replace(r.registry.providers["plentiful"], id="openrouter")
        model = replace(r.registry.models[("plentiful", "small")], provider_id="openrouter")
        registry = Registry([provider], [model])
        pool = CredentialPool(
            [provider], {"FIXTURE_A": "synthetic-a", "FIXTURE_B": "synthetic-b"}, clock=r.clock
        )
        paid = replace(
            self.inventory(("small",)),
            provider="openrouter",
            models=(DiscoveredModel("small", frozenset({"text"}), 8192, 1024, Funding.UNKNOWN),),
        )
        free = replace(
            paid, slot="plentiful-2", models=(replace(paid.models[0], funding=Funding.FREE),)
        )
        registry.apply_inventory(paid)
        registry.apply_inventory(free)
        router = Router(registry, pool, {"test": r.adapter}, r.store, r.clock)
        self.assertEqual({route.slot for route in router.rank(r.request)}, {"plentiful-2"})
        self.assertEqual(router.rank(replace(r.request, pinned_slot="plentiful-1")), [])

    def test_expired_seed_limits_not_refreshed_by_fieldless_inventory(self):
        r = self.r
        model = r.registry.models[("plentiful", "small")]
        source = SourceRef(
            "https://official.invalid/model", Authority.OFFICIAL_DOCS, "provider", r.clock() - 301
        )
        r.registry.replace_models(
            [
                replace(m, metadata_source=source) if m is model else m
                for m in r.registry.models.values()
            ]
        )
        inv = self.inventory(("small",))
        inv = replace(inv, models=(replace(inv.models[0], context_limit=None, output_limit=None),))
        r.registry.apply_inventory(inv)
        self.assertEqual(r.router.rank(replace(r.request, pinned_provider="plentiful")), [])

    def test_failed_refresh_does_not_execute_stale_seed(self):
        r = self.r

        class UnavailableDiscovery:
            def inventory(self, *args):
                raise ProviderError(Failure.NETWORK)

        r.router.discovery = UnavailableDiscovery()
        with self.assertRaises(RouteUnavailable):
            r.router.execute(replace(r.request, pinned_provider="plentiful"))
        self.assertEqual(r.adapter.calls, [])
        self.assertEqual(
            r.store.all("discovery_failure")[0]["status"], "UNKNOWN / potentially stale"
        )

    def test_current_provider_failure_reranks_to_current_alternative(self):
        r = self.r
        r.registry.apply_inventory(self.inventory(("small",)))
        r.adapter.steps = [ProviderError(Failure.PROVIDER)]
        result = r.router.execute(r.request)
        self.assertEqual(result.route.provider, "scarce")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(r.adapter.calls, [("plentiful", "small"), ("scarce", "strong")])

    def test_snapshot_and_probe_survive_restart_without_secrets(self):
        r = self.r
        registry = Registry(
            list(r.registry.providers.values()), list(r.registry.models.values()), r.store
        )
        registry.apply_inventory(self.inventory(("small",)))
        registry.observe_generation(
            "plentiful", "small", "plentiful-1", r.clock(), False, "access_denied"
        )
        restored = Registry(
            list(registry.providers.values()), list(registry.models.values()), r.store
        )
        self.assertEqual(
            restored.availability("plentiful", "small", "plentiful-1", r.clock()), "unavailable"
        )
        data = json.dumps(r.store.all("model_inventory"))
        self.assertEqual(r.pool.redact(data), data)

    def test_authority_depends_on_claim_scope(self):
        cache = SourceRef("seed", Authority.CACHE, "account", self.r.clock())
        live = self.inventory().source
        self.assertEqual(prefer_source("account_availability", cache, live), live)
        retirement = SourceRef(
            "official-retirement", Authority.DEPRECATION, "provider", self.r.clock()
        )
        self.assertEqual(prefer_source("retirement", live, retirement), retirement)


class FreshnessRoutingTests(unittest.TestCase):
    def test_b_current_intent_requires_retrieval_even_when_forced_reason(self):
        for text in (
            "what models are available now?",
            "What models does Groq support?",
            "what's the latest OpenAI model?",
            "what's today's weather?",
            "is my flight delayed?",
            "what is the current price?",
            "explain the currently supported provider models",
        ):
            with self.subTest(text=text):
                decision = decide(Intent(text, "reason"))
                self.assertEqual(decision.execution_class, ExecutionClass.RETRIEVAL)
                self.assertIn(decision.freshness, {Freshness.CURRENT, Freshness.LIVE})

    def test_c_static_question_needs_no_search(self):
        decision = decide(Intent("what is 2+2?"))
        self.assertEqual(decision.execution_class, ExecutionClass.CAPABILITY)
        self.assertEqual(decision.freshness, Freshness.STATIC)
        self.assertEqual(
            decide(Intent("explain integer addition")).execution_class, ExecutionClass.MODEL
        )

    def test_d_unavailable_search_returns_unknown_not_model_prior(self):
        r = RouterRig()
        self.addCleanup(r.close)
        action = Action(
            new_id(),
            new_id(),
            new_id(),
            "search",
            {"query": "what models are available now?", "freshness": Freshness.CURRENT},
            "test",
            "owner",
        )
        r.store.put(
            "task", action.task_id, record(Task(action.task_id, "objective", action.correlation_id))
        )
        result = RetrievalExecutor(r.router, ())(action, Cancellation(r.store, action.task_id))
        self.assertFalse(result.success)
        self.assertIn("UNKNOWN / potentially stale", result.error)
        self.assertEqual(r.adapter.calls, [])
        self.assertEqual(r.store.all("route_history"), [])

    def test_retrieval_budget_is_bounded(self):
        with self.assertRaises(ValueError):
            RetrievalRequest("current models", result_limit=1000)

    def test_current_evidence_preserves_sources_conflicts_not_query_in_telemetry(self):
        r = RouterRig()
        self.addCleanup(r.close)
        query = "what models are available now? private objective marker"
        source = SourceRef(
            "https://official.invalid/models", Authority.LIVE_API, "account", r.clock()
        )

        class NativeSource:
            def supports(self, request):
                return True

            def retrieve(self, request, check_cancel):
                check_cancel()
                return RetrievalResult(
                    (RetrievedFact("model-new listed", source, ("seed absent",)),)
                )

        action = Action(
            new_id(),
            new_id(),
            new_id(),
            "search",
            {"query": query, "freshness": Freshness.CURRENT},
            "test",
            "owner",
        )
        r.store.put(
            "task", action.task_id, record(Task(action.task_id, "objective", action.correlation_id))
        )
        result = RetrievalExecutor(r.router, (NativeSource(),))(
            action, Cancellation(r.store, action.task_id)
        )
        self.assertTrue(result.success)
        self.assertIn(source.identity, result.value)
        saved = r.store.all("retrieval_evidence")[0]
        self.assertEqual(saved["status"], "REPORTED")
        self.assertEqual(saved["conflicts"], ["seed absent"])
        self.assertNotIn(query, json.dumps(saved))
        self.assertEqual(r.adapter.calls, [])

    def test_native_inventory_retrieval_actively_refreshes_current_cache(self):
        r = RouterRig()
        self.addCleanup(r.close)
        r.registry.providers["plentiful"] = replace(
            r.registry.providers["plentiful"], discovery_required=True
        )
        calls = []

        class NativeDiscovery:
            def inventory(self, provider, slot, secret):
                calls.append(slot)
                return Inventory(
                    provider.id,
                    slot,
                    SourceRef(
                        provider.base_url + "/models", Authority.LIVE_API, "account", r.clock()
                    ),
                    (DiscoveredModel("model-new", frozenset({"text"})),),
                )

        r.router.discovery = NativeDiscovery()
        source = ProviderInventorySource(r.router)
        request = RetrievalRequest("currently configured provider models")
        first = source.retrieve(request, lambda: None)
        second = source.retrieve(request, lambda: None)
        self.assertEqual(calls, ["plentiful-1", "plentiful-1"])
        self.assertIn("model-new", first.facts[0].text)
        self.assertEqual(first.facts[0].source, second.facts[0].source)
        self.assertTrue(first.limitations)
        self.assertEqual(r.adapter.calls, [])

    def test_manifest_funding_does_not_invent_account_entitlement(self):
        registry = Registry.load(Path("config/development-models.json"))
        for model in registry.models.values():
            if model.provider_id != "openrouter":
                self.assertEqual(model.funding, Funding.UNKNOWN)
        coding = registry.providers["zai-coding"]
        self.assertFalse(coding.enabled)
        self.assertEqual(coding.allowed_tasks, ("coding",))
        self.assertNotEqual(coding.quota_pool, registry.providers["zai"].quota_pool)


class SharedQuotaTests(unittest.TestCase):
    def setUp(self):
        self.r = RouterRig()
        self.addCleanup(self.r.close)
        provider = replace(
            self.r.registry.providers["plentiful"],
            credential_pools={},
            quota_pool="plentiful/shared",
        )
        self.pool = CredentialPool(
            [provider], {"FIXTURE_A": "synthetic-a", "FIXTURE_B": "synthetic-b"}, clock=self.r.clock
        )

    def test_multiple_keys_do_not_multiply_observed_capacity_or_concurrency(self):
        self.pool.observe_limits(
            "plentiful-1", "small", RateLimits(remaining_requests=7, remaining_tokens=100)
        )
        self.assertIs(
            self.pool.capacity("plentiful-1", "small"), self.pool.capacity("plentiful-2", "small")
        )
        self.assertEqual(len(self.pool.quota_pools), 1)
        self.assertTrue(self.pool.reserve("plentiful-1", 10, "small"))
        self.assertFalse(self.pool.reserve("plentiful-2", 10, "small"))
        self.pool.release("plentiful-1")
        self.assertTrue(self.pool.reserve("plentiful-2", 10, "small"))
        self.pool.release("plentiful-2")

    def test_shared_rate_limit_blocks_other_key_but_not_other_model_bucket(self):
        self.pool.failed("plentiful-1", Failure.RATE_LIMIT, 30, "small")
        self.assertFalse(self.pool.eligible("plentiful-2", 1, "small"))
        self.assertTrue(self.pool.eligible("plentiful-2", 1, "different-model"))

    def test_conflicting_key_counters_use_conservative_minimum_not_sum(self):
        self.pool.observe_limits("plentiful-1", "small", RateLimits(remaining_requests=7))
        self.pool.observe_limits("plentiful-2", "small", RateLimits(remaining_requests=40))
        self.assertEqual(self.pool.capacity("plentiful-2", "small").remaining_requests, 7)

    def test_expired_common_counter_not_overridden_by_old_slot_counter(self):
        now = self.r.clock()
        slot = self.pool.slots["plentiful-1"]
        slot.remaining_tokens, slot.quota_observed_at = 0, now
        self.pool.observe_limits(
            "plentiful-1", "small", RateLimits(remaining_tokens=0, tokens_reset_at=now + 5)
        )
        self.r.clock.now += 6
        self.assertTrue(self.pool.eligible("plentiful-1", 1, "small"))
        self.pool.observe_limits("plentiful-2", "small", RateLimits(remaining_tokens=80))
        self.assertEqual(self.pool.capacity("plentiful-1", "small").remaining_tokens, 80)

    def test_account_cooldown_cannot_be_hidden_by_model_observation(self):
        provider = replace(
            self.r.registry.providers["plentiful"],
            id="openrouter",
            credential_pools={},
            quota_pool="openrouter/shared",
        )
        pool = CredentialPool(
            [provider], {"FIXTURE_A": "synthetic-a", "FIXTURE_B": "synthetic-b"}, clock=self.r.clock
        )
        pool.observe_limits("plentiful-1", "small", RateLimits())
        pool.failed("plentiful-1", Failure.UNKNOWN_LIMIT, 30, "small")
        self.assertFalse(pool.eligible("plentiful-2", 1, "small"))
        self.assertFalse(pool.eligible("plentiful-2", 1, "other"))
        self.r.clock.now += 31
        self.assertTrue(pool.eligible("plentiful-2", 1, "small"))

    def test_balance_error_does_not_invent_numeric_remaining_requests(self):
        self.pool.failed("plentiful-1", Failure.QUOTA, 30, "small")
        self.assertIsNone(self.pool.slots["plentiful-1"].remaining_requests)
        self.assertIsNone(self.pool.capacity("plentiful-1", "small").remaining_requests)
        self.assertFalse(self.pool.eligible("plentiful-2", 1, "small"))

    def test_expired_request_and_token_counters_are_separate_and_unknown(self):
        now = self.r.clock()
        self.pool.observe_limits(
            "plentiful-1",
            "small",
            RateLimits(
                remaining_requests=7,
                remaining_tokens=100,
                requests_reset_at=now + 100,
                tokens_reset_at=now + 5,
            ),
        )
        self.r.clock.now += 6
        capacity = self.pool.capacity("plentiful-2", "small")
        self.assertEqual(capacity.remaining_requests, 7)
        self.assertIsNone(capacity.remaining_tokens)
        self.r.clock.now += 301
        self.assertIsNone(self.pool.capacity("plentiful-1", "small").remaining_requests)

    def test_access_denial_does_not_invalidate_credential(self):
        self.pool.failed("plentiful-1", Failure.ACCESS, 30, "small")
        self.assertEqual(self.pool.slots["plentiful-1"].validity, "unknown")
