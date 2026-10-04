"""Local Memory Fabric foundation: selected retention, bounded retrieval and live-source precedence.

Personal Policy and World Model remain distinct. MemoryBackend is a replaceable
OSCAR-owned retrieval boundary; production semantic/temporal indexes are added by
Gate B without changing the authority rules in this local adapter.
"""

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import StrEnum
from time import time
from typing import Any, Protocol

from .contracts import Epistemic, record
from .credentials import redact_runtime_secrets
from .freshness import Authority, SourceRef
from .storage import Store


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    PROJECT = "project"
    DEVICE = "device"
    PROCEDURAL = "procedural"
    PROFILE = "profile"
    RELATIONSHIP = "relationship"
    SEMANTIC = "semantic"
    COMMUNICATION = "communication"
    WORKER = "worker"


@dataclass(frozen=True)
class MemoryItem:
    id: str
    key: str
    content: str
    scope: str
    kind: MemoryType
    source: SourceRef
    created_at: float
    evidence_state: Epistemic = Epistemic.RECALLED
    confidence: float | None = None
    expires_at: float | None = None
    entity_refs: tuple[str, ...] = ()
    retention_reason: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.key or not self.scope or not self.retention_reason:
            raise ValueError("memory requires identity, scope and explicit retention provenance")
        if len(self.content.encode()) > 16_000:
            raise ValueError("retain selected summaries/references, not entire private archives")
        if self.confidence is not None and (
            not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1
        ):
            raise ValueError("invalid confidence")
        if not math.isfinite(self.created_at) or self.created_at < 0:
            raise ValueError("invalid created time")
        if self.expires_at is not None and (
            not math.isfinite(self.expires_at) or self.expires_at <= self.created_at
        ):
            raise ValueError("invalid retention expiry")


class MemoryBackend(Protocol):
    def retain(self, item: MemoryItem, *, retention_authorized: bool) -> None: ...

    def retrieve(self, query: str, scope: str, limit: int = 8) -> tuple[MemoryItem, ...]: ...

    def forget(self, identifier: str, *, owner_authorized: bool) -> None: ...


class LocalMemory:
    def __init__(
        self,
        store: Store,
        *,
        clock: Callable[[], float] = time,
        redact: Callable[[str], str] = redact_runtime_secrets,
    ):
        self.store, self.clock, self.redact = store, clock, redact

    def retain(self, item: MemoryItem, *, retention_authorized: bool) -> None:
        if not retention_authorized:
            raise PermissionError("retrieval is not permission to retain")
        if self.redact(json.dumps(record(item))) != json.dumps(record(item)):
            raise ValueError("credential material cannot enter memory")
        if item.evidence_state == Epistemic.VERIFIED:
            if not item.source.evidence_id:
                raise ValueError("verified historical memory requires correlated evidence")
            evidence = self.store.get("evidence", item.source.evidence_id)
            if (
                evidence["status"] != Epistemic.VERIFIED
                or evidence["matches"] is not True
                or evidence["content_hash"] != hashlib.sha256(item.content.encode()).hexdigest()
                or item.source.observed_at != evidence["observed_at"]
            ):
                raise ValueError("memory cannot upgrade unrelated evidence or testimony")
        self.store.put("memory", item.id, record(item))

    def retrieve(self, query: str, scope: str, limit: int = 8) -> tuple[MemoryItem, ...]:
        if not 1 <= limit <= 32 or len(query) > 1000 or not scope:
            raise ValueError("retrieval needs explicit scope and bounded query/limit")
        terms = set(query.lower().split())
        candidates: list[tuple[int, float, MemoryItem]] = []
        for data in self.store.all("memory"):
            if data["scope"] != scope:
                continue
            if data["expires_at"] is not None and data["expires_at"] <= self.clock():
                continue
            source = SourceRef(
                **{**data["source"], "authority": Authority(data["source"]["authority"])}
            )
            item = MemoryItem(
                **{
                    **data,
                    "kind": MemoryType(data["kind"]),
                    "source": source,
                    "evidence_state": Epistemic(data["evidence_state"]),
                    "entity_refs": tuple(data["entity_refs"]),
                }
            )
            score = sum(term in (item.key + " " + item.content).lower() for term in terms)
            if terms and not score:
                continue
            candidates.append((score, item.created_at, item))
        candidates.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        # Historic verification is retained as provenance; recall presentation is always RECALLED.
        return tuple(
            replace(entry[2], evidence_state=Epistemic.RECALLED) for entry in candidates[:limit]
        )

    def forget(self, identifier: str, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("forget requires owner authority")
        self.store.delete("memory", identifier)

    def purge_expired(self) -> int:
        expired = [
            d["id"]
            for d in self.store.all("memory")
            if d["expires_at"] is not None and d["expires_at"] <= self.clock()
        ]
        with self.store.transaction():
            for identifier in expired:
                self.store.delete("memory", identifier)
        return len(expired)


@dataclass(frozen=True)
class ContextObservation:
    key: str
    value: str
    scope: str
    source: SourceRef
    state: Epistemic
    entity_refs: tuple[str, ...] = ()


class LiveContextSource(Protocol):
    id: str

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]: ...


@dataclass(frozen=True)
class ActiveContext:
    task_id: str
    scope: str
    live: tuple[ContextObservation, ...]
    memories: tuple[MemoryItem, ...]
    blockers: tuple[str, ...] = ()

    def resolve(self, key: str, now: float) -> ContextObservation | None:
        # Recalled/model-prior state never becomes live solely through a new timestamp.
        authoritative = [
            o
            for o in self.live
            if o.key == key
            and o.scope == self.scope
            and o.source.current(now)
            and o.source.authority in {Authority.LIVE_API, Authority.OFFICIAL_DOCS}
            and o.state in {Epistemic.KNOWN, Epistemic.VERIFIED, Epistemic.REPORTED}
        ]
        if authoritative:
            return min(
                authoritative,
                key=lambda o: (o.source.authority != Authority.LIVE_API, -o.source.observed_at),
            )
        recalled = next((m for m in self.memories if m.key == key and m.scope == self.scope), None)
        if recalled:
            return ContextObservation(
                key,
                recalled.content,
                self.scope,
                recalled.source,
                Epistemic.INFERRED
                if recalled.evidence_state == Epistemic.INFERRED
                else Epistemic.RECALLED,
                recalled.entity_refs,
            )
        # Unverified live testimony can be shown with its explicit state, not called truth.
        reported = [
            o for o in self.live if o.key == key and o.scope == self.scope and o.source.current(now)
        ]
        return max(reported, key=lambda o: o.source.observed_at) if reported else None


class LiveContextFederation:
    def __init__(
        self,
        memory: MemoryBackend,
        sources: tuple[LiveContextSource, ...],
        *,
        redact: Callable[[str], str] = redact_runtime_secrets,
    ):
        if len({s.id for s in sources}) != len(sources) or len(sources) > 16:
            raise ValueError("duplicate or oversized live source configuration")
        self.memory, self.sources, self.redact = memory, sources, redact

    def assemble(self, task_id: str, query: str, scope: str, limit: int = 8) -> ActiveContext:
        if not task_id or not scope or len(query) > 1000:
            raise ValueError("active context needs task, scope and bounded query")
        observations: list[ContextObservation] = []
        blockers = []
        for source in self.sources:
            try:
                retrieved = source.retrieve(query, scope)
                if len(retrieved) > 32:
                    raise ValueError("live context result bound")
                for observation in retrieved:
                    if observation.scope != scope or len(observation.value.encode()) > 16_000:
                        raise ValueError("context scope/size rejected")
                    observations.append(replace(observation, value=self.redact(observation.value)))
            except (OSError, ValueError, PermissionError, KeyError):
                blockers.append(source.id + ":unavailable")
        return ActiveContext(
            task_id,
            scope,
            tuple(observations),
            self.memory.retrieve(query, scope, limit),
            tuple(blockers),
        )


class StateContextSource:
    """Reference live Grid and Worker/task state, content-free and scope-bound."""

    id = "native-grid-worker-state"

    def __init__(
        self, store: Store, grid_snapshot: Callable[[], list[dict[str, Any]]], allowed_scope: str
    ):
        self.store, self.grid_snapshot, self.allowed_scope = store, grid_snapshot, allowed_scope

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.allowed_scope:
            raise PermissionError("state context scope denied")
        source = SourceRef("local://grid-worker-state", Authority.LIVE_API, "local", time(), 5)
        snapshots = [
            {
                "node_id": n["id"],
                "status": n["status"],
                "capabilities": [c["name"] for c in n["capabilities"]],
            }
            for n in self.grid_snapshot()
        ]

        return (
            ContextObservation("grid.state", json.dumps(snapshots), scope, source, Epistemic.KNOWN),
        )
