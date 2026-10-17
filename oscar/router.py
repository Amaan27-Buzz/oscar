"""Adaptive model routing with explicit policy, capacity preservation and observed outcomes."""

import math
from collections.abc import Callable, Mapping
from dataclasses import replace
from time import monotonic, time

from .capabilities import Cancelled
from .contracts import Evidence, new_id
from .credentials import CredentialPool, Slot
from .discovery import HTTPDiscovery
from .models import (
    Failure,
    Funding,
    Mode,
    ModelRequest,
    ModelSpec,
    ProviderError,
    ProviderResponse,
    Route,
    RoutedResult,
    RoutingPolicy,
    StreamSink,
)
from .providers import Adapter
from .registry import Registry
from .storage import Store


class RouteUnavailable(Exception):
    pass


DEFAULT_POLICY = RoutingPolicy()


class Router:
    def __init__(
        self,
        registry: Registry,
        pool: CredentialPool,
        adapters: Mapping[str, Adapter],
        store: Store,
        clock: Callable[[], float] = time,
        discovery: HTTPDiscovery | None = None,
    ):
        self.registry, self.pool, self.adapters, self.store, self.clock = (
            registry,
            pool,
            adapters,
            store,
            clock,
        )
        self.discovery = discovery

    def refresh(
        self,
        request: ModelRequest,
        policy: RoutingPolicy = DEFAULT_POLICY,
        check_cancel: Callable[[], None] = lambda: None,
    ) -> None:
        """Explicit bounded I/O before execution; rank itself remains a pure cache read."""
        if self.discovery is None:
            return
        for provider in self.registry.providers.values():
            if not provider.enabled or not provider.discovery_required:
                continue
            if request.pinned_provider and request.pinned_provider != provider.id:
                continue
            if policy.allowed_providers is not None and provider.id not in policy.allowed_providers:
                continue
            if request.mode == Mode.LOCAL and not provider.local:
                continue
            if request.mode == Mode.PRIVATE and not (
                provider.local or provider.private or provider.id in policy.private_providers
            ):
                continue
            for slot in self.pool.slots.values():
                if (
                    slot.provider != provider.id
                    or not slot.present
                    or (request.pinned_slot and request.pinned_slot != slot.id)
                ):
                    continue
                check_cancel()
                inventory = self.registry.inventories.get((provider.id, slot.id))
                if inventory and inventory.source.current(self.clock()):
                    continue
                try:
                    fresh = self.discovery.inventory(
                        provider,
                        slot.id,
                        self.pool.secret_for_adapter(slot.id),
                        min(10, policy.timeout_seconds),
                    )
                    self.registry.apply_inventory(fresh)
                    account = self.discovery.account(
                        provider,
                        self.pool.secret_for_adapter(slot.id),
                        min(10, policy.timeout_seconds),
                    )
                    if account:
                        self.store.put(
                            "account_observation",
                            slot.id,
                            {
                                "source": account.source.identity,
                                "observed_at": account.source.observed_at,
                                "scope": account.source.scope,
                                "free_tier": account.free_tier,
                                "credit_cap_remaining": account.credit_cap_remaining,
                            },
                        )
                        if account.limits:
                            self.pool.observe_limits(slot.id, "*", account.limits)
                except ProviderError as error:
                    self.store.put(
                        "discovery_failure",
                        slot.id,
                        {
                            "provider": provider.id,
                            "slot": slot.id,
                            "observed_at": self.clock(),
                            "category": error.category.value,
                            "http_status": error.http_status,
                            "status": "UNKNOWN / potentially stale",
                        },
                    )
                    if error.category == Failure.CREDENTIAL:
                        self.pool.failed(slot.id, error.category, error.retry_after)

    def _health_blocked(self, provider: str, model: str) -> bool:
        for identifier in (provider, provider + "/" + model):
            try:
                if self.store.get("route_health", identifier)["until"] > self.clock():
                    return True
            except KeyError:
                pass
        return False

    def _observed(self, model: ModelSpec, task_class: str) -> tuple[float, float]:
        reliability = model.reliability if model.reliability is not None else 0.5
        latency = model.latency_ms if model.latency_ms is not None else 3000.0
        weight, successes, latency_weight, latencies = 0.0, 0.0, 0.0, 0.0
        for event in self.store.all("route_history")[-1000:]:
            if (
                event["provider"] != model.provider_id
                or event["model"] != model.id
                or event["task_class"] != task_class
            ):
                continue
            age = max(0, self.clock() - event["timestamp"])
            if age > 7 * 86400:
                continue
            w = 0.5 ** (age / 86400)
            weight += w
            successes += w * event["provider_response_success"]
            if event["provider_response_success"]:
                latency_weight += w
                latencies += w * event["latency_ms"]
        # Five-observation prior: one fast/failed call cannot become permanent truth.
        return (
            (5 * reliability + successes) / (5 + weight),
            (5 * latency + latencies) / (5 + latency_weight),
        )

    @staticmethod
    def scarcity(slot: Slot) -> float | None:
        if slot.remaining_requests is None:
            return None
        return 1 / max(1, slot.remaining_requests)

    def _objective_fit(self, model: ModelSpec, task_class: str) -> float:
        weight, successes = 0.0, 0.0
        for event in self.store.all("route_history")[-1000:]:
            age = max(0, self.clock() - event["timestamp"])
            if (
                event["provider"] != model.provider_id
                or event["model"] != model.id
                or event["task_class"] != task_class
                or event["verified_objective"] is None
                or age > 7 * 86400
            ):
                continue
            w = 0.5 ** (age / 86400)
            weight += w
            successes += w * event["verified_objective"]
        return (2.5 + successes) / (5 + weight)

    def rank(
        self,
        request: ModelRequest,
        policy: RoutingPolicy = DEFAULT_POLICY,
        excluded: set[tuple[str, str, str]] | None = None,
    ) -> list[Route]:
        routes: list[Route] = []
        candidates = (
            (self.registry.model_for_slot(m.provider_id, m.id, slot.id, self.clock()), slot)
            for m in self.registry.models.values()
            for slot in self.pool.slots.values()
            if slot.provider == m.provider_id
        )
        for model, slot in candidates:
            provider = self.registry.providers[model.provider_id]
            if (
                not provider.enabled
                or provider.adapter not in self.adapters
                or self._health_blocked(provider.id, model.id)
            ):
                continue
            if policy.allowed_providers is not None and provider.id not in policy.allowed_providers:
                continue
            if request.mode == Mode.LOCAL and not provider.local:
                continue
            if request.mode == Mode.PRIVATE and not (
                provider.local or provider.private or provider.id in policy.private_providers
            ):
                continue
            if request.pinned_provider and provider.id != request.pinned_provider:
                continue
            if request.pinned_model and model.id != request.pinned_model:
                continue
            if (
                model.retired
                or provider.allowed_tasks is not None
                and request.task_class not in provider.allowed_tasks
            ):
                continue
            if (
                not request.required <= model.capabilities
                or model.quality is None
                or model.quality < request.min_quality
            ):
                continue
            if (
                model.context_limit is None
                and not policy.allow_unknown_limits
                or model.context_limit is not None
                and model.context_limit < request.input_tokens + request.max_output_tokens
            ):
                continue
            if (model.output_limit is None and not policy.allow_unknown_limits) or (
                model.output_limit is not None and model.output_limit < request.max_output_tokens
            ):
                continue
            free = model.funding in {Funding.FREE, Funding.SUBSCRIPTION, Funding.LOCAL}
            if not free and not policy.allow_paid:
                continue
            if model.funding == Funding.UNKNOWN and not policy.allow_unknown_cost:
                continue
            cost = 0.0 if free else model.price_per_million
            if not free and cost is None and not policy.allow_unknown_cost:
                continue
            if (
                cost is not None
                and cost * (request.input_tokens + request.max_output_tokens) / 1_000_000
                > policy.max_paid_cost
            ):
                continue
            reliability, latency = self._observed(model, request.task_class)
            affinity = model.affinities.get(request.task_class, 0.0)
            identity = (provider.id, model.id, slot.id)
            if (
                slot.provider != provider.id
                or excluded
                and identity in excluded
                or request.pinned_slot
                and slot.id != request.pinned_slot
                or not self.pool.eligible(
                    slot.id, request.input_tokens + request.max_output_tokens, model.id
                )
            ):
                continue
            availability = self.registry.availability(provider.id, model.id, slot.id, self.clock())
            if availability not in {
                "configured fallback",
                "listed via credential; generation entitlement not implied",
            }:
                continue
            capacity = self.pool.capacity(slot.id, model.id)
            remaining = capacity.remaining_requests if capacity else slot.remaining_requests
            account_capacity = self.pool.capacity(slot.id, "*")
            if account_capacity and account_capacity.remaining_requests is not None:
                remaining = (
                    min(remaining, account_capacity.remaining_requests)
                    if remaining is not None
                    else account_capacity.remaining_requests
                )
            scarcity = None if remaining is None else 1 / max(1, remaining)
            # This is policy pressure, not a fabricated quota estimate/percentage.
            scarcity_penalty = 3 if scarcity is None else 30 * scarcity
            score = (
                40 * free
                + 10 * reliability
                + 5 * affinity
                + 10 * self._objective_fit(model, request.task_class)
            )
            score -= 2 * math.log1p(latency / 100) + scarcity_penalty
            score -= 5 * (model.quality - request.min_quality)
            score -= slot.concurrent * 5
            if request.mode == Mode.HEAVY:
                score += 20 * model.quality + 5 * affinity + scarcity_penalty
            elif request.mode == Mode.FAST:
                score -= 15 * math.log1p(latency / 100)
            elif request.mode == Mode.BALANCED:
                score += 6 * model.quality + 10 * reliability + 5 * affinity
            elif request.mode == Mode.CHEAP:
                score -= 100 * (cost if cost is not None else 10)
            elif request.mode == Mode.SPECIALIST:
                score += 60 * affinity
            reasons = (
                "required capabilities satisfied; context/output limits checked"
                if not policy.allow_unknown_limits
                else "explicit bounded diagnostic allowance for UNKNOWN limits",
                f"quality tier {model.quality} meets floor {request.min_quality}; "
                f"source: {model.provenance}",
                f"capacity class {model.funding.value}; quota "
                + ("UNKNOWN" if remaining is None else f"{remaining} confirmed requests remaining"),
                f"availability {availability}; inventory source "
                + (
                    f"{self.registry.inventories[(provider.id, slot.id)].source.identity}; "
                    "observed_at "
                    f"{self.registry.inventories[(provider.id, slot.id)].source.observed_at}; "
                    f"TTL {provider.inventory_ttl_seconds}s"
                    if (provider.id, slot.id) in self.registry.inventories
                    else "explicit configured fallback; current inventory UNKNOWN"
                ),
                f"account product {slot.account_product}; shared quota pool {slot.quota_pool}; "
                "credential count does not increase capacity",
                "ranking considers task affinity, decaying reliability/latency, and scarcity",
                "provider response health and verified objective outcomes remain separate",
                "preserve stronger/scarcer routes when sufficient alternatives exist",
                f"mode {request.mode.value}; explicit policy enforced",
            )
            routes.append(
                Route(
                    provider.id,
                    model.id,
                    slot.id,
                    request.mode,
                    score,
                    reasons,
                    remaining,
                    slot.quota_pool or None,
                )
            )

        def ordering(route: Route) -> tuple[float, float, float, str, str, str]:
            model = self.registry.model_for_slot(
                route.provider, route.model, route.slot, self.clock()
            )
            primary = 0.0
            free = model.funding in {Funding.FREE, Funding.SUBSCRIPTION, Funding.LOCAL}
            if request.mode in {Mode.FREE_FIRST, Mode.AUTO}:
                primary = 0.0 if free else 1.0
            elif request.mode == Mode.CHEAP:
                primary = (
                    0.0
                    if free
                    else (
                        model.price_per_million if model.price_per_million is not None else 1000.0
                    )
                )
            elif request.mode == Mode.HEAVY:
                primary = -float(model.quality or 0)
            elif request.mode == Mode.SPECIALIST:
                primary = -model.affinities.get(request.task_class, 0.0)
            return (
                primary,
                -route.score,
                self.pool.slots[route.slot].last_use or 0,
                route.provider,
                route.model,
                route.slot,
            )

        return sorted(routes, key=ordering)

    def _history(
        self,
        request: ModelRequest,
        route: Route,
        latency: float,
        attempt: int,
        success: bool,
        error: Failure | None,
        response: ProviderResponse | None,
        emitted: bool,
    ) -> str:
        identifier = new_id()
        # Whitelist only. Never serialize ModelRequest or ProviderResponse.
        self.store.put(
            "route_history",
            identifier,
            {
                "id": identifier,
                "task_id": request.task_id,
                "correlation_id": request.correlation_id,
                "task_class": request.task_class,
                "provider": route.provider,
                "model": route.model,
                "slot": route.slot,
                "quota_pool": route.quota_pool,
                "account_product": self.pool.slots[route.slot].account_product,
                "actual_model": response.actual_model if response else None,
                "actual_provider": response.actual_provider if response else None,
                "mode": request.mode.value,
                "reason": list(route.reasons),
                "timestamp": self.clock(),
                "latency_ms": latency,
                "attempt": attempt,
                "fallback": attempt > 1,
                "provider_response_success": success,
                "error": error.value if error else None,
                "output_emitted": emitted,
                "input_tokens": response.input_tokens if response else None,
                "output_tokens": response.output_tokens if response else None,
                "structured_ok": response.structured_ok if response else None,
                "tool_ok": response.tool_ok if response else None,
                "quota_remaining": route.quota_remaining,
                "verified_objective": None,
                "verification_evidence_id": None,
                "expected_cost": self._expected_cost(request, route),
            },
        )
        return identifier

    def _expected_cost(self, request: ModelRequest, route: Route) -> float | None:
        model = self.registry.model_for_slot(route.provider, route.model, route.slot, self.clock())
        if model.funding in {Funding.FREE, Funding.SUBSCRIPTION, Funding.LOCAL}:
            return 0.0
        if model.price_per_million is None:
            return None
        return (
            model.price_per_million * (request.input_tokens + request.max_output_tokens) / 1_000_000
        )

    def record_verification(self, history_id: str, matches: bool | None, evidence_id: str) -> None:
        history = self.store.get("route_history", history_id)
        evidence = self.store.get("evidence", evidence_id)
        if evidence["task_id"] != history["task_id"] or evidence["matches"] != matches:
            raise ValueError("verification evidence does not match route task")
        history.update(verified_objective=matches, verification_evidence_id=evidence_id)
        self.store.put("route_history", history_id, history)

    def observe_verification(self, evidence: Evidence) -> None:
        for history in self.store.all("route_history"):
            if (
                history["task_id"] == evidence.task_id
                and history["correlation_id"] == evidence.correlation_id
                and history["provider_response_success"]
            ):
                self.record_verification(history["id"], evidence.matches, evidence.id)

    def execute(
        self,
        request: ModelRequest,
        policy: RoutingPolicy = DEFAULT_POLICY,
        check_cancel: Callable[[], None] = lambda: None,
        sink: StreamSink | None = None,
    ) -> RoutedResult:
        excluded: set[tuple[str, str, str]] = set()
        prefer: tuple[str, str] | None = None
        last_error: ProviderError | None = None
        remaining_budget = policy.max_paid_cost
        self.refresh(request, policy, check_cancel)
        for attempt in range(1, policy.max_attempts + 1):
            check_cancel()
            routes = self.rank(request, replace(policy, max_paid_cost=remaining_budget), excluded)
            if prefer:
                routes.sort(key=lambda r: (r.provider, r.model) != prefer)
            selected = next(
                (
                    route
                    for route in routes
                    if self.pool.reserve(
                        route.slot, request.input_tokens + request.max_output_tokens, route.model
                    )
                ),
                None,
            )
            if selected is None:
                if last_error:
                    raise last_error
                raise RouteUnavailable(
                    "no route satisfies capability, availability and explicit policy"
                )
            route = selected
            provider = self.registry.providers[route.provider]
            slot = self.pool.slots[route.slot]
            remaining_budget = max(
                0.0, remaining_budget - (self._expected_cost(request, route) or 0)
            )
            slot.requests += 1
            started, emitted = monotonic(), False
            credential = self.pool.secret_for_adapter(route.slot)
            safe_stream = self.pool.safe_stream(sink)

            try:
                if not credential and provider.credential_envs:
                    raise ProviderError(Failure.CREDENTIAL)
                response = self.adapters[provider.adapter].generate(
                    provider,
                    route.model,
                    credential,
                    request,
                    policy.timeout_seconds,
                    check_cancel,
                    safe_stream if sink else None,
                )
                check_cancel()
                if not response.text.strip():
                    raise ProviderError(Failure.CAPABILITY, emitted=emitted)
                response = replace(
                    response,
                    text=self.pool.redact(response.text),
                    actual_model=self.pool.redact(response.actual_model)
                    if response.actual_model
                    else None,
                    actual_provider=self.pool.redact(response.actual_provider)
                    if response.actual_provider
                    else None,
                )
                emitted = safe_stream.emitted
                safe_stream.finish()
                elapsed = (monotonic() - started) * 1000
                slot.validity, slot.health = "valid", "healthy"
                slot.latency_ms = elapsed
                slot.input_tokens += response.input_tokens or 0
                slot.output_tokens += response.output_tokens or 0
                self.registry.observe_generation(
                    route.provider, route.model, route.slot, self.clock(), True
                )
                if response.rate_limits and (
                    response.rate_limits.remaining_requests is not None
                    or response.rate_limits.remaining_tokens is not None
                ):
                    self.pool.observe_limits(route.slot, route.model, response.rate_limits)
                else:
                    self.pool.invalidate_capacity(route.slot, route.model)
                if response.remaining_requests is not None or response.remaining_tokens is not None:
                    slot.remaining_requests, slot.remaining_tokens = (
                        response.remaining_requests,
                        response.remaining_tokens,
                    )
                    slot.quota_observed_at, slot.reset_at = self.clock(), response.reset_at
                else:
                    # A pre-consumption balance is no longer a current quota observation.
                    slot.remaining_requests, slot.remaining_tokens = None, None
                    slot.quota_observed_at, slot.reset_at = None, None
                history = self._history(
                    request, route, elapsed, attempt, True, None, response, emitted
                )
                return RoutedResult(route, response, attempt, history)
            except (ProviderError, Cancelled) as failure:
                error = (
                    failure
                    if isinstance(failure, ProviderError)
                    else ProviderError(Failure.CANCELLED, emitted=emitted)
                )
                last_error = error
                output_emitted = safe_stream.emitted or error.emitted
                self._history(
                    request,
                    route,
                    (monotonic() - started) * 1000,
                    attempt,
                    False,
                    error.category,
                    None,
                    output_emitted,
                )
                if error.rate_limits:
                    self.pool.observe_limits(route.slot, route.model, error.rate_limits)
                self.pool.failed(route.slot, error.category, error.retry_after, route.model)
                if error.category in {
                    Failure.MODEL,
                    Failure.ACCESS,
                    Failure.PRODUCT,
                    Failure.FUNDING,
                }:
                    self.registry.observe_generation(
                        route.provider,
                        route.model,
                        route.slot,
                        self.clock(),
                        False,
                        error.category.value,
                    )
                excluded.add((route.provider, route.model, route.slot))
                if error.category in {
                    Failure.CREDENTIAL,
                    Failure.RATE_LIMIT,
                    Failure.QUOTA,
                    Failure.UNKNOWN_LIMIT,
                }:
                    prefer = (route.provider, route.model)
                else:
                    prefer = None
                    scope = (
                        route.provider
                        if error.category
                        in {
                            Failure.PROVIDER,
                            Failure.NETWORK,
                            Failure.NETWORK_POLICY,
                        }
                        and not (
                            route.provider == "openrouter" and error.category == Failure.PROVIDER
                        )
                        else route.provider + "/" + route.model
                    )
                    self.store.put(
                        "route_health",
                        scope,
                        {
                            "until": self.clock() + min(3600, max(1, error.retry_after)),
                            "category": error.category.value,
                        },
                    )
                if output_emitted or error.category == Failure.CANCELLED:
                    raise ProviderError(error.category, emitted=output_emitted) from None
            finally:
                self.pool.release(route.slot)
        if last_error:
            raise last_error
        raise RouteUnavailable("bounded route attempts exhausted")
