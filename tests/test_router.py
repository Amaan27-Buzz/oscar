import json
import pickle
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from oscar.capabilities import Cancelled
from oscar.credentials import CredentialPool
from oscar.models import (
    Failure,
    Funding,
    Mode,
    ProviderError,
    ProviderResponse,
    ProviderSpec,
    RoutingPolicy,
)
from oscar.registry import Registry
from oscar.router import RouteUnavailable

from .support import RouterRig


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.r = RouterRig()
        self.addCleanup(self.r.close)

    def route(self, **kwargs):
        return self.r.router.rank(replace(self.r.request, **kwargs))[0]

    def test_auto_is_explainable_and_uses_sufficient_model(self):
        route = self.route()
        self.assertEqual((route.provider, route.model), ("plentiful", "small"))
        self.assertTrue(route.reasons)
        self.assertIn("quality tier 2", " ".join(route.reasons))

    def test_free_first_preserves_scarce_high_value_route(self):
        self.assertEqual(self.route(mode=Mode.FREE_FIRST).provider, "plentiful")

    def test_difficult_task_justifies_scarce_strength(self):
        self.assertEqual(
            self.route(mode=Mode.FREE_FIRST, min_quality=4, task_class="reasoning").provider,
            "scarce",
        )

    def test_free_first_never_ignores_required_capability(self):
        self.assertEqual(
            self.route(mode=Mode.FREE_FIRST, required=frozenset({"rare"})).provider, "scarce"
        )

    def test_fast_favors_latency_and_respects_quality_floor(self):
        self.assertEqual(self.route(mode=Mode.FAST).provider, "plentiful")
        self.assertEqual(self.route(mode=Mode.FAST, min_quality=4).provider, "scarce")

    def test_balanced_responds_to_health_capacity_and_latency(self):
        first = self.route(mode=Mode.BALANCED)
        self.assertEqual(first.provider, "plentiful")
        for slot in self.r.pool.slots.values():
            if slot.provider == "plentiful":
                slot.cooldown_until = self.r.clock() + 30
        self.assertEqual(self.route(mode=Mode.BALANCED).provider, "scarce")

    def test_heavy_chooses_stronger_eligible_model(self):
        self.assertEqual(self.route(mode=Mode.HEAVY).model, "strong")

    def test_local_never_silently_uses_cloud(self):
        request = replace(self.r.request, mode=Mode.LOCAL)
        self.assertEqual(self.r.router.rank(request), [])
        with self.assertRaises(RouteUnavailable):
            self.r.router.execute(request)
        self.assertEqual(self.r.adapter.calls, [])

    def test_private_restrictions_cannot_be_bypassed_by_pin(self):
        request = replace(self.r.request, mode=Mode.PRIVATE, pinned_provider="plentiful")
        self.assertEqual(self.r.router.rank(request), [])
        policy = RoutingPolicy(private_providers=frozenset({"plentiful"}))
        self.assertEqual(self.r.router.rank(request, policy)[0].provider, "plentiful")

    def test_manual_can_pin_model_and_optional_slot(self):
        route = self.route(
            mode=Mode.MANUAL,
            pinned_provider="scarce",
            pinned_model="strong",
            pinned_slot="scarce-1",
        )
        self.assertEqual(
            (route.provider, route.model, route.slot), ("scarce", "strong", "scarce-1")
        )
        request = replace(
            self.r.request, mode=Mode.MANUAL, pinned_provider="scarce", pinned_model="strong"
        )
        self.assertEqual(
            self.r.router.rank(request, RoutingPolicy(allowed_providers=frozenset({"plentiful"}))),
            [],
        )

    def test_manual_requires_provider_and_model(self):
        with self.assertRaises(ValueError):
            replace(self.r.request, mode=Mode.MANUAL)

    def test_specialist_task_affinity_matters(self):
        self.assertEqual(
            self.route(mode=Mode.SPECIALIST, task_class="reasoning").provider, "scarce"
        )

    def test_cheap_minimizes_known_cost_without_unknown_advantage(self):
        r = self.r
        models = [
            replace(
                m,
                funding=Funding.PAID,
                price_per_million=1 if m.provider_id == "plentiful" else 100,
            )
            for m in r.registry.models.values()
        ]
        r.registry.replace_models(models)
        self.assertEqual(r.router.rank(r.request), [])
        policy = RoutingPolicy(allow_paid=True, max_paid_cost=1)
        self.assertEqual(
            r.router.rank(replace(r.request, mode=Mode.CHEAP), policy)[0].provider, "plentiful"
        )

    def test_unknown_price_is_not_free(self):
        r = self.r
        r.registry.replace_models(
            [
                replace(m, funding=Funding.UNKNOWN, price_per_million=None)
                for m in r.registry.models.values()
            ]
        )
        self.assertEqual(r.router.rank(r.request), [])
        self.assertEqual(r.router.rank(r.request, RoutingPolicy(allow_paid=True)), [])

    def test_free_first_eligible_free_pool_precedes_paid_regardless_of_soft_score(self):
        r = self.r
        models = [
            replace(m, latency_ms=10**12)
            if m.provider_id == "plentiful"
            else replace(m, funding=Funding.PAID, price_per_million=0.01, latency_ms=1)
            for m in r.registry.models.values()
        ]
        r.registry.replace_models(models)
        route = r.router.rank(
            replace(r.request, mode=Mode.FREE_FIRST), RoutingPolicy(allow_paid=True)
        )[0]
        self.assertEqual(route.provider, "plentiful")

    def test_paid_fallback_cost_budget_is_cumulative(self):
        r = self.r
        r.registry.replace_models(
            [
                replace(m, funding=Funding.PAID, price_per_million=1)
                for m in r.registry.models.values()
            ]
        )
        r.adapter.steps = [ProviderError(Failure.RATE_LIMIT)] * 4
        with self.assertRaises(ProviderError):
            r.router.execute(r.request, RoutingPolicy(allow_paid=True, max_paid_cost=0.0003))
        self.assertEqual(len(r.adapter.calls), 1)

    def test_failed_objective_does_not_become_success_from_provider_200(self):
        from oscar.contracts import Epistemic, Evidence, new_id, record

        r = self.r
        routed = r.router.execute(r.request)
        model = r.registry.models[(routed.route.provider, routed.route.model)]
        initial_fit = r.router._objective_fit(model, r.request.task_class)
        evidence = Evidence(
            new_id(),
            r.request.task_id,
            r.request.correlation_id,
            "independent-test",
            "objective state mismatch",
            r.clock(),
            False,
            Epistemic.KNOWN,
            "objective did not match",
        )
        r.store.put("evidence", evidence.id, record(evidence))
        r.router.observe_verification(evidence)
        self.assertLess(r.router._objective_fit(model, r.request.task_class), initial_fit)
        event = r.store.get("route_history", routed.history_id)
        self.assertTrue(event["provider_response_success"])
        self.assertFalse(event["verified_objective"])

    def test_unknown_quota_stays_unknown(self):
        r = self.r
        for slot in r.pool.slots.values():
            slot.remaining_requests = None
        result = r.router.execute(r.request)
        self.assertIsNone(result.route.quota_remaining)
        self.assertIsNone(r.pool.slots[result.route.slot].remaining_requests)
        self.assertIn("quota UNKNOWN", " ".join(result.route.reasons))
        self.assertIsNone(r.store.all("route_history")[0]["quota_remaining"])

    def test_stale_quota_and_reset_become_unknown(self):
        r = self.r
        slot = r.pool.slots["plentiful-1"]
        slot.remaining_requests, slot.reset_at = 0, r.clock() + 10
        self.assertFalse(slot.eligible(r.clock()))
        r.clock.now += 11
        self.assertTrue(slot.eligible(r.clock()))
        self.assertIsNone(slot.remaining_requests)
        slot.remaining_requests, slot.quota_observed_at = 0, r.clock()
        r.clock.now += 301
        self.assertTrue(slot.eligible(r.clock()))
        self.assertIsNone(slot.remaining_requests)

    def test_invalid_credential_fails_over_without_killing_provider(self):
        r = self.r
        r.adapter.steps = [ProviderError(Failure.CREDENTIAL), ProviderResponse("ok")]
        result = r.router.execute(r.request)
        self.assertEqual(result.route.slot, "plentiful-2")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(r.pool.slots["plentiful-1"].validity, "invalid")
        self.assertEqual(r.pool.slots["plentiful-2"].validity, "valid")

    def test_rate_limit_alternate_key_and_next_request_reranks(self):
        r = self.r
        r.adapter.steps = [ProviderError(Failure.RATE_LIMIT), ProviderResponse("ok")]
        result = r.router.execute(r.request)
        self.assertEqual(result.route.slot, "plentiful-2")
        self.assertEqual(self.route().slot, "plentiful-2")
        r.pool.slots["plentiful-2"].cooldown_until = r.clock() + 30
        self.assertEqual(self.route().provider, "scarce")

    def test_provider_failure_cross_provider_reranks(self):
        r = self.r
        r.adapter.steps = [ProviderError(Failure.PROVIDER), ProviderResponse("ok")]
        result = r.router.execute(r.request)
        self.assertEqual(result.route.provider, "scarce")
        self.assertEqual(r.adapter.calls, [("plentiful", "small"), ("scarce", "strong")])
        self.assertTrue(r.store.all("route_history")[1]["fallback"])

    def test_fallback_budget_stops(self):
        r = self.r
        r.adapter.steps = [ProviderError(Failure.RATE_LIMIT)] * 10
        with self.assertRaises(ProviderError):
            r.router.execute(r.request, RoutingPolicy(max_attempts=2))
        self.assertEqual(len(r.adapter.calls), 2)
        self.assertTrue(all(s.concurrent == 0 for s in r.pool.slots.values()))

    def test_manual_does_not_cross_pinned_provider_after_failure(self):
        r = self.r
        r.adapter.steps = [ProviderError(Failure.PROVIDER)]
        request = replace(
            r.request, mode=Mode.MANUAL, pinned_provider="plentiful", pinned_model="small"
        )
        with self.assertRaises(ProviderError):
            r.router.execute(request)
        self.assertEqual(len(r.adapter.calls), 1)

    def test_streaming_does_not_splice_after_meaningful_output(self):
        r = self.r

        def interrupted(check, sink):
            sink("meaningful partial generation " * 3)
            raise ProviderError(Failure.NETWORK, emitted=True)

        r.adapter.steps = [interrupted, ProviderResponse("second provider")]
        chunks = []
        with self.assertRaises(ProviderError) as caught:
            r.router.execute(r.request, sink=chunks.append)
        self.assertTrue(caught.exception.emitted)
        self.assertEqual(len(r.adapter.calls), 1)
        self.assertNotIn("second provider", "".join(chunks))

    def test_streaming_redacts_secrets_across_chunks(self):
        r = self.r

        def generated(check, sink):
            sink("synthetic-value-")
            sink("alpha plus output")
            return ProviderResponse("synthetic-value-alpha plus output")

        r.adapter.steps = [generated]
        chunks = []
        result = r.router.execute(r.request, sink=chunks.append)
        self.assertNotIn("synthetic-value-alpha", "".join(chunks))
        self.assertNotIn("synthetic-value-alpha", result.response.text)

    def test_cancellation_stops_attempt_and_releases_reservation(self):
        r = self.r

        def cancel(check, sink):
            raise Cancelled("synthetic cancellation")

        r.adapter.steps = [cancel]
        with self.assertRaises(ProviderError) as caught:
            r.router.execute(r.request)
        self.assertEqual(caught.exception.category, Failure.CANCELLED)
        self.assertEqual(len(r.adapter.calls), 1)
        self.assertEqual(r.pool.slots["plentiful-1"].concurrent, 0)

    def test_content_free_history_has_all_required_fields(self):
        r = self.r
        routed = r.router.execute(r.request)
        event = r.store.get("route_history", routed.history_id)
        for key in ("provider", "model", "slot", "mode", "reason", "latency_ms", "fallback"):
            self.assertIn(key, event)
        encoded = json.dumps(event)
        for private in (
            "private prompt fixture",
            "reported synthetic answer",
            "synthetic-value-alpha",
        ):
            self.assertNotIn(private, encoded)
        self.assertIsNone(event["verified_objective"])
        self.assertEqual(routed.status, "REPORTED")

    def test_learning_is_smoothed_and_stale_observations_decay(self):
        r = self.r
        model = r.registry.models[("plentiful", "small")]
        initial = r.router._observed(model, "extraction")
        r.router.execute(r.request)
        updated = r.router._observed(model, "extraction")
        self.assertLess(abs(updated[0] - initial[0]), 0.05)
        r.clock.now += 8 * 86400
        self.assertEqual(r.router._observed(model, "extraction"), initial)

    def test_concurrency_is_reserved_atomically(self):
        r = self.r
        self.assertTrue(r.pool.reserve("plentiful-1", 10))
        self.assertFalse(r.pool.reserve("plentiful-1", 10))
        self.assertEqual(self.route().slot, "plentiful-2")
        r.pool.release("plentiful-1")

    def test_observed_usage_and_quota_persist_without_material(self):
        r = self.r
        r.adapter.steps = [ProviderResponse("ok", 12, 3, 19, 400)]
        result = r.router.execute(r.request)
        metadata = r.store.get("credential_state", result.route.slot)
        self.assertEqual(metadata["remaining_requests"], 19)
        self.assertEqual(metadata["input_tokens"], 12)
        self.assertNotIn("synthetic-value-alpha", json.dumps(metadata))
        loaded = CredentialPool(
            list(r.registry.providers.values()), {"FIXTURE_A": "replacement"}, r.store, r.clock
        )
        self.assertEqual(loaded.slots["plentiful-1"].remaining_requests, 19)
        self.assertEqual(loaded.slots["plentiful-1"].concurrent, 0)

    def test_model_inventory_is_replaceable_including_ollama_account_data(self):
        manifest = Registry.load(Path("config/development-models.json"))
        ollama = [m for m in manifest.models.values() if m.provider_id == "ollama-cloud"]
        self.assertTrue(ollama)
        self.assertTrue(manifest.providers["ollama-cloud"].discovery_required)
        self.assertTrue(all(m.funding == Funding.UNKNOWN for m in ollama))
        replacement = replace(ollama[0], id="future-model-v2")
        manifest.replace_models([replacement])
        self.assertEqual(list(manifest.models), [("ollama-cloud", "future-model-v2")])

    def test_unknown_quality_or_context_never_gets_advantage(self):
        r = self.r
        r.registry.replace_models([replace(m, quality=None) for m in r.registry.models.values()])
        self.assertEqual(r.router.rank(r.request), [])

    def test_verified_outcome_requires_correlated_evidence(self):
        from oscar.contracts import Epistemic, Evidence, new_id, record

        r = self.r
        routed = r.router.execute(r.request)
        evidence = Evidence(
            new_id(),
            r.request.task_id,
            r.request.correlation_id,
            "independent-test",
            "fixture contract verification",
            r.clock(),
            True,
            Epistemic.VERIFIED,
            "independent sentinel matched",
        )
        r.store.put("evidence", evidence.id, record(evidence))
        r.router.observe_verification(evidence)
        self.assertTrue(r.store.get("route_history", routed.history_id)["verified_objective"])
        with self.assertRaises(ValueError):
            r.router.record_verification(routed.history_id, False, evidence.id)

    def test_request_input_budget_accounts_for_actual_prompt_bytes(self):
        request = replace(self.r.request, prompt="x" * 9000, input_tokens=1)
        self.assertEqual(self.r.router.rank(request), [])

    def test_observed_cooldown_expires_and_allows_reranking(self):
        r = self.r
        r.adapter.steps = [ProviderError(Failure.PROVIDER), ProviderResponse("ok")]
        r.router.execute(r.request)
        self.assertEqual(self.route().provider, "scarce")
        r.clock.now += 31
        self.assertEqual(self.route().provider, "plentiful")

    def test_local_endpoint_contract_can_be_registered_without_cloud_fallback(self):
        r = self.r
        local = ProviderSpec(
            "local-node", "test", "http://127.0.0.1:1234", {}, local=True, private=True
        )
        model = replace(
            next(iter(r.registry.models.values())), provider_id=local.id, funding=Funding.LOCAL
        )
        registry = Registry([local], [model])
        pool = CredentialPool([local], {}, clock=r.clock)
        from oscar.router import Router

        router = Router(registry, pool, {"test": r.adapter}, r.store, r.clock)
        result = router.execute(replace(r.request, mode=Mode.LOCAL))
        self.assertEqual(result.route.provider, "local-node")
        self.assertEqual(result.route.slot, "local-node-local")


class CredentialTests(unittest.TestCase):
    def test_presence_is_only_name_and_present_or_missing(self):
        provider = ProviderSpec(
            "fixture",
            "test",
            "https://example.invalid",
            {"fixture-1": "FIXTURE_A", "fixture-2": "FIXTURE_B"},
        )
        pool = CredentialPool([provider], {"FIXTURE_A": "synthetic-private-value"})
        self.assertEqual(pool.safe_presence_lines(), ["FIXTURE_A present", "FIXTURE_B missing"])
        self.assertTrue(pool.slots["fixture-1"].present)
        self.assertFalse(pool.slots["fixture-2"].present)
        self.assertNotIn("synthetic-private-value", repr(pool))
        self.assertNotIn("synthetic-private-value", json.dumps(asdict(pool.slots["fixture-1"])))
        with self.assertRaises(TypeError):
            pickle.dumps(pool)

    def test_all_seventeen_real_slot_names_are_metadata_only(self):
        registry = Registry.load(Path("config/development-models.json"))
        pool = CredentialPool(list(registry.providers.values()), {})
        self.assertEqual(len(pool.slots), 17)
        self.assertTrue(all(not s.present for s in pool.slots.values()))
