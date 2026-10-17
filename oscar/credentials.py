"""Credential material stays in an opaque runtime pool, never in metadata or persistence."""

import os
import re
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from threading import RLock
from time import time
from typing import Any
from weakref import WeakSet

from .models import Failure, ProviderSpec, RateLimits, StreamSink
from .storage import Store


@dataclass
class Slot:
    id: str
    provider: str
    present: bool
    validity: str = "unknown"
    health: str = "unknown"
    cooldown_until: float = 0
    concurrent: int = 0
    max_concurrent: int = 1
    last_use: float | None = None
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    remaining_requests: int | None = None
    remaining_tokens: int | None = None
    quota_observed_at: float | None = None
    reset_at: float | None = None
    latency_ms: float | None = None
    recent_errors: list[str] | None = None
    quota_pool: str = ""
    account_product: str = "general-api"

    def eligible(self, now: float, tokens: int = 0) -> bool:
        # Stale quota is unknown, never renewed to an invented full balance.
        stale = self.quota_observed_at is not None and now - self.quota_observed_at > 300
        if (self.reset_at is not None and now >= self.reset_at) or stale:
            self.remaining_requests, self.remaining_tokens = None, None
            self.quota_observed_at, self.reset_at = None, None
        return (
            self.present
            and self.validity != "invalid"
            and self.cooldown_until <= now
            and self.concurrent < self.max_concurrent
            and self.remaining_requests != 0
            and (self.remaining_tokens is None or self.remaining_tokens >= tokens)
        )


@dataclass
class Capacity:
    remaining_requests: int | None = None
    remaining_tokens: int | None = None
    request_limit: int | None = None
    token_limit: int | None = None
    requests_reset_at: float | None = None
    tokens_reset_at: float | None = None
    observed_at: float | None = None
    cooldown_until: float = 0
    source: str = "UNKNOWN"
    observed_slot: str | None = None

    def expire(self, now: float) -> None:
        if self.observed_at is not None and now - self.observed_at > 300:
            self.remaining_requests = self.remaining_tokens = None
        if self.requests_reset_at is not None and now >= self.requests_reset_at:
            self.remaining_requests = None
        if self.tokens_reset_at is not None and now >= self.tokens_reset_at:
            self.remaining_tokens = None


@dataclass
class QuotaPool:
    id: str
    provider: str
    account_product: str
    provenance: str
    concurrent: int = 0
    max_concurrent: int = 1


class CredentialPool:
    def __init__(
        self,
        providers: list[ProviderSpec],
        environ: Mapping[str, str] | None = None,
        store: Store | None = None,
        clock: Callable[[], float] = time,
    ):
        source = os.environ if environ is None else environ
        self._values: dict[str, str] = {}
        self._resolvers: dict[str, Callable[[], str]] = {}
        self.material = SecretMaterial()
        self.slots: dict[str, Slot] = {}
        self.store, self.clock, self.lock = store, clock, RLock()
        self.presence: dict[str, bool] = {}
        self.quota_pools: dict[str, QuotaPool] = {}
        self.capacities: dict[tuple[str, str], Capacity] = {}
        for provider in providers:
            if not provider.enabled:
                continue
            for identifier, variable in provider.credential_envs.items():
                present = bool(source.get(variable))
                self.presence[variable] = present
                if identifier in self.slots:
                    raise ValueError("masked credential slot must be globally unique")
                pool_id = provider.credential_pools.get(
                    identifier, provider.quota_pool or provider.id + "/" + provider.account_product
                )
                quota_pool = QuotaPool(
                    pool_id, provider.id, provider.account_product, provider.quota_pool_provenance
                )
                existing = self.quota_pools.get(pool_id)
                if existing and (existing.provider, existing.account_product) != (
                    provider.id,
                    provider.account_product,
                ):
                    raise ValueError("quota pool cannot mix providers/account products")
                self.quota_pools[pool_id] = quota_pool
                slot = Slot(
                    identifier,
                    provider.id,
                    present,
                    quota_pool=pool_id,
                    account_product=provider.account_product,
                )
                if present:
                    self._values[identifier] = source[variable]
                if store:
                    try:
                        saved = store.get("credential_state", identifier)
                        slot = Slot(
                            **{
                                **saved,
                                "present": present,
                                "concurrent": 0,
                                "quota_pool": pool_id,
                                "account_product": provider.account_product,
                            }
                        )
                    except KeyError:
                        pass
                self.slots[identifier] = slot
            if provider.local and not provider.credential_envs:
                identifier = provider.id + "-local"
                self.slots[identifier] = Slot(identifier, provider.id, True)
        if store:
            for data in store.all("quota_capacity"):
                if data["pool"] in self.quota_pools:
                    self.capacities[(data["pool"], data["model"])] = Capacity(**data["capacity"])

    def capacity(self, identifier: str, model: str = "") -> Capacity | None:
        slot = self.slots[identifier]
        capacity = self.capacities.get(
            (slot.quota_pool, model), self.capacities.get((slot.quota_pool, "*"))
        )
        if capacity:
            capacity.expire(self.clock())
        return capacity

    def eligible(self, identifier: str, tokens: int = 0, model: str = "") -> bool:
        if identifier in self._resolvers:
            self.secret_for_adapter(identifier)
        slot = self.slots[identifier]
        quota_pool = self.quota_pools.get(slot.quota_pool)
        capacity = self.capacity(identifier, model)
        account_capacity = self.capacity(identifier, "*")
        # Per-slot counters are retained as observations, not a second capacity pool.
        health_slot = (
            replace(slot, remaining_requests=None, remaining_tokens=None) if capacity else slot
        )
        return (
            health_slot.eligible(self.clock(), tokens)
            and (quota_pool is None or quota_pool.concurrent < quota_pool.max_concurrent)
            and (
                capacity is None
                or (
                    capacity.cooldown_until <= self.clock()
                    and capacity.remaining_requests != 0
                    and (capacity.remaining_tokens is None or capacity.remaining_tokens >= tokens)
                )
            )
            and (
                account_capacity is None
                or (
                    account_capacity.cooldown_until <= self.clock()
                    and account_capacity.remaining_requests != 0
                    and (
                        account_capacity.remaining_tokens is None
                        or account_capacity.remaining_tokens >= tokens
                    )
                )
            )
        )

    def observe_limits(self, identifier: str, model: str, limits: RateLimits) -> None:
        with self.lock:
            self._observe_limits(identifier, model, limits)

    def _observe_limits(self, identifier: str, model: str, limits: RateLimits) -> None:
        slot = self.slots[identifier]
        capacity = Capacity(
            limits.remaining_requests,
            limits.remaining_tokens,
            limits.request_limit,
            limits.token_limit,
            limits.requests_reset_at,
            limits.tokens_reset_at,
            self.clock(),
            source=limits.source,
            observed_slot=identifier,
        )
        previous = self.capacities.get((slot.quota_pool, model))
        if previous:
            previous.expire(self.clock())
        if (
            previous
            and previous.observed_slot != identifier
            and previous.observed_at is not None
            and self.clock() - previous.observed_at <= 300
        ):
            # Unknown account topology is grouped conservatively. Conflicting key
            # counters never become their sum or a guessed larger common balance.
            for field in ("remaining_requests", "remaining_tokens"):
                old, new = getattr(previous, field), getattr(capacity, field)
                if old is not None and new is not None:
                    setattr(capacity, field, min(old, new))
        self.capacities[(slot.quota_pool, model)] = capacity
        self.persist_capacity(slot.quota_pool, model)

    def persist_capacity(self, pool_id: str, model: str) -> None:
        if self.store:
            self.store.put(
                "quota_capacity",
                pool_id + "/" + model,
                {
                    "pool": pool_id,
                    "model": model,
                    "capacity": asdict(self.capacities[(pool_id, model)]),
                },
            )

    def invalidate_capacity(self, identifier: str, model: str) -> None:
        capacity = self.capacity(identifier, model)
        if capacity:
            capacity.remaining_requests = capacity.remaining_tokens = None
            capacity.observed_at = None
            pool_id = self.slots[identifier].quota_pool
            bucket = model if (pool_id, model) in self.capacities else "*"
            self.persist_capacity(pool_id, bucket)

    def __repr__(self) -> str:
        return f"CredentialPool(masked_slots={list(self.slots)!r})"

    def __getstate__(self) -> Any:
        raise TypeError("credential pools must not be serialized")

    def secret_for_adapter(self, slot_id: str) -> str:
        """Adapter-only boundary; callers must never log or serialize this value."""
        if slot_id in self._resolvers:
            with self.lock:
                try:
                    value = self._resolvers[slot_id]()
                except (KeyError, PermissionError, OSError):
                    value = ""
                if value:
                    self.material.remember(value)
                self.slots[slot_id].present = bool(value)
                return value
        return self._values.get(slot_id, "")

    def bind_resolver(self, slot_id: str, resolver: Callable[[], str]) -> None:
        """Native Vault reads stay live; deletion cannot fall back to an environment copy."""
        with self.lock:
            self.slots[slot_id].validity = "unknown"
            self._resolvers[slot_id] = resolver
            previous = self._values.pop(slot_id, "")
            if previous:
                self.material.remember(previous)
            self.secret_for_adapter(slot_id)

    def redact(self, text: str) -> str:
        for value in (*self._values.values(), *self.material.values):
            if value:
                text = text.replace(value, "<redacted>")
        return text

    def safe_stream(self, sink: StreamSink | None) -> "SafeStream":
        def hold() -> int:
            return max(
                (len(value) for value in (*self._values.values(), *self.material.values)), default=1
            )

        return SafeStream(sink, self.redact, hold)

    def reserve(self, identifier: str, tokens: int, model: str = "") -> bool:
        with self.lock:
            slot = self.slots[identifier]
            if not self.eligible(identifier, tokens, model):
                return False
            slot.concurrent += 1
            slot.last_use = self.clock()
            if slot.quota_pool in self.quota_pools:
                self.quota_pools[slot.quota_pool].concurrent += 1
            return True

    def release(self, identifier: str) -> None:
        with self.lock:
            slot = self.slots[identifier]
            slot.concurrent = max(0, slot.concurrent - 1)
            if slot.quota_pool in self.quota_pools:
                quota_pool = self.quota_pools[slot.quota_pool]
                quota_pool.concurrent = max(0, quota_pool.concurrent - 1)
            self.persist(identifier)

    def failed(self, identifier: str, category: Failure, cooldown: float, model: str = "") -> None:
        with self.lock:
            slot = self.slots[identifier]
            slot.recent_errors = ((slot.recent_errors or []) + [category.value])[-10:]
            if category == Failure.CREDENTIAL:
                slot.validity, slot.health = "invalid", "unavailable"
            elif category in {
                Failure.RATE_LIMIT,
                Failure.QUOTA,
                Failure.UNKNOWN_LIMIT,
                Failure.CAPACITY,
            }:
                slot.cooldown_until = self.clock() + min(
                    3600, max(300 if category == Failure.QUOTA else 1, cooldown)
                )
                slot.health = "degraded"
                if category == Failure.QUOTA:
                    # A balance/resource-package error is not a numeric request counter.
                    slot.remaining_requests = slot.remaining_tokens = None
                    slot.quota_observed_at = slot.reset_at = None
                bucket = (
                    "*"
                    if slot.provider in {"openrouter", "zai", "zai-coding", "ollama-cloud"}
                    else model
                )
                key = slot.quota_pool, bucket
                capacity = self.capacities.setdefault(key, Capacity())
                capacity.cooldown_until = slot.cooldown_until
                self.persist_capacity(*key)

    def persist(self, identifier: str) -> None:
        if self.store:
            self.store.put("credential_state", identifier, asdict(self.slots[identifier]))

    def safe_presence_lines(self) -> list[str]:
        return [
            f"{name} {'present' if present else 'missing'}"
            for name, present in self.presence.items()
        ]


class SafeStream:
    def __init__(
        self, sink: StreamSink | None, redact: Callable[[str], str], hold: Callable[[], int]
    ):
        self.sink, self.redact, self.hold = sink, redact, hold
        self.pending = ""
        self.emitted = False

    def __call__(self, chunk: str) -> None:
        if self.sink is None:
            return
        self.emitted = self.emitted or bool(chunk.strip())
        self.pending = self.redact(self.pending + chunk)
        hold = self.hold()
        if len(self.pending) > hold:
            self.sink(self.pending[:-hold])
            self.pending = self.pending[-hold:]

    def finish(self) -> None:
        if self.sink and self.pending:
            self.sink(self.redact(self.pending))
            self.pending = ""


class SecretMaterial:
    """Runtime-owned secret filter; weak registration does not extend credential lifetime."""

    def __init__(self) -> None:
        self.values: set[str] = set()
        _secret_material.add(self)

    def remember(self, value: str) -> None:
        if value not in self.values and len(self.values) >= 100:
            raise ValueError("runtime secret material bound exceeded")
        self.values.add(value)

    def clear(self) -> None:
        self.values.clear()


_secret_material: WeakSet[SecretMaterial] = WeakSet()


def redact_runtime_secrets(text: str) -> str:
    """Value-silent filtering of known platform-supplied secret variables, without file reads."""
    for name, value in os.environ.items():
        if value and any(term in name.upper() for term in ("TOKEN", "KEY", "SECRET", "PASSWORD")):
            text = text.replace(value, "<redacted>")
    for material in list(_secret_material):
        for value in material.values:
            text = text.replace(value, "<redacted>")
    return re.sub(
        r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})", "<redacted>", text
    )
