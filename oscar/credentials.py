"""Credential material stays in an opaque runtime pool, never in metadata or persistence."""

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from threading import RLock
from time import time
from typing import Any

from .models import Failure, ProviderSpec, StreamSink
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
        self.slots: dict[str, Slot] = {}
        self.store, self.clock, self.lock = store, clock, RLock()
        self.presence: dict[str, bool] = {}
        for provider in providers:
            for identifier, variable in provider.credential_envs.items():
                present = bool(source.get(variable))
                self.presence[variable] = present
                if identifier in self.slots:
                    raise ValueError("masked credential slot must be globally unique")
                slot = Slot(identifier, provider.id, present)
                if present:
                    self._values[identifier] = source[variable]
                if store:
                    try:
                        saved = store.get("credential_state", identifier)
                        slot = Slot(**{**saved, "present": present, "concurrent": 0})
                    except KeyError:
                        pass
                self.slots[identifier] = slot
            if provider.local and not provider.credential_envs:
                identifier = provider.id + "-local"
                self.slots[identifier] = Slot(identifier, provider.id, True)

    def __repr__(self) -> str:
        return f"CredentialPool(masked_slots={list(self.slots)!r})"

    def __getstate__(self) -> Any:
        raise TypeError("credential pools must not be serialized")

    def secret_for_adapter(self, slot_id: str) -> str:
        """Adapter-only boundary; callers must never log or serialize this value."""
        return self._values.get(slot_id, "")

    def redact(self, text: str) -> str:
        for value in self._values.values():
            if value:
                text = text.replace(value, "<redacted>")
        return text

    def safe_stream(self, sink: StreamSink | None) -> "SafeStream":
        hold = max((len(value) for value in self._values.values()), default=1)
        return SafeStream(sink, self.redact, hold)

    def reserve(self, identifier: str, tokens: int) -> bool:
        with self.lock:
            slot = self.slots[identifier]
            if not slot.eligible(self.clock(), tokens):
                return False
            slot.concurrent += 1
            slot.last_use = self.clock()
            return True

    def release(self, identifier: str) -> None:
        with self.lock:
            slot = self.slots[identifier]
            slot.concurrent = max(0, slot.concurrent - 1)
            self.persist(identifier)

    def failed(self, identifier: str, category: Failure, cooldown: float) -> None:
        with self.lock:
            slot = self.slots[identifier]
            slot.recent_errors = ((slot.recent_errors or []) + [category.value])[-10:]
            if category == Failure.CREDENTIAL:
                slot.validity, slot.health = "invalid", "unavailable"
            elif category in {Failure.RATE_LIMIT, Failure.QUOTA}:
                slot.cooldown_until = self.clock() + min(3600, max(1, cooldown))
                slot.health = "degraded"
                if category == Failure.QUOTA:
                    slot.remaining_requests, slot.quota_observed_at = 0, self.clock()

    def persist(self, identifier: str) -> None:
        if self.store:
            from dataclasses import asdict

            self.store.put("credential_state", identifier, asdict(self.slots[identifier]))

    def safe_presence_lines(self) -> list[str]:
        return [
            f"{name} {'present' if present else 'missing'}"
            for name, present in self.presence.items()
        ]


class SafeStream:
    def __init__(self, sink: StreamSink | None, redact: Callable[[str], str], hold: int):
        self.sink, self.redact, self.hold = sink, redact, hold
        self.pending = ""
        self.emitted = False

    def __call__(self, chunk: str) -> None:
        if self.sink is None:
            return
        self.emitted = self.emitted or bool(chunk.strip())
        self.pending = self.redact(self.pending + chunk)
        if len(self.pending) > self.hold:
            self.sink(self.pending[: -self.hold])
            self.pending = self.pending[-self.hold :]

    def finish(self) -> None:
        if self.sink and self.pending:
            self.sink(self.redact(self.pending))
            self.pending = ""
