"""Trusted local source commissioning and untrusted, policy-bounded event ingestion."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .contracts import record
from .event_archive import SourceEvent
from .policy import PersonalPolicy
from .storage import StateConflict
from .world_model import Observation, ObservationKind, WorldModel, WorldState, reference


@dataclass(frozen=True)
class PerceptionSource:
    id: str
    entities: tuple[str, ...]
    keys: tuple[str, ...]
    kinds: tuple[ObservationKind, ...]
    simulated: bool = True
    perceive: bool = False
    retain: bool = False
    act: bool = False
    retention_seconds: int = 3600
    events_per_minute: int = 60
    version: int = 1

    def __post_init__(self) -> None:
        reference(self.id)
        for values in (self.entities, self.keys, self.kinds):
            if not isinstance(values, tuple) or not 1 <= len(values) <= 32:
                raise ValueError("bounded exact source scope required")
            if len(set(values)) != len(values):
                raise ValueError("duplicate source scope")
        for value in (*self.entities, *self.keys):
            reference(value)
        if (
            any(not isinstance(k, ObservationKind) for k in self.kinds)
            or any(
                type(b) is not bool for b in (self.simulated, self.perceive, self.retain, self.act)
            )
            or type(self.version) is not int
            or self.version != 1
            or type(self.retention_seconds) is not int
            or not 1 <= self.retention_seconds <= 604800
            or type(self.events_per_minute) is not int
            or not 1 <= self.events_per_minute <= 600
        ):
            raise ValueError("invalid source contract")


class PerceptionFabric:
    MAX_SOURCES = 64
    MAX_CURRENT = 512
    MAX_HISTORY = 2048

    def __init__(self, world: WorldModel, policy: PersonalPolicy):
        if policy.store is not world.store:
            raise ValueError("perception and policy must share authoritative Store")
        self.world, self.store, self.policy = world, world.store, policy

    def register(self, source: PerceptionSource, *, owner_authorized: bool) -> int:
        if not owner_authorized:
            raise PermissionError("source registration requires trusted owner authority")
        identifier = self.world.source_key(source.id)
        self.world.safe(json.dumps(record(source)))
        with self.store.transaction():
            try:
                previous = self.world.source(source.id)
                epoch = int(previous["epoch"]) + 1
            except KeyError:
                if len(self.store.all("perception_source")) >= self.MAX_SOURCES:
                    raise StateConflict("source registration bound reached") from None
                epoch = 1
            self._discard_current(source.id)
            self.store.put(
                "perception_source",
                identifier,
                {
                    **record(source),
                    "relationship": self.world.relationship,
                    "epoch": epoch,
                    "last_sequence": 0,
                    "last_observed_at": 0.0,
                    "connected_until": 0.0,
                    "window": 0,
                    "count": 0,
                    "receipts": {},
                },
            )
        self._forget_volatile(source.id, epoch)
        return epoch

    def connect(
        self,
        source_id: str,
        epoch: int,
        *,
        lease_seconds: int = 60,
        guard: Callable[[], None] | None = None,
    ) -> None:
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            raise ValueError("bounded source lease required")
        with self.store.transaction():
            if guard:
                guard()
            source = self.world.source(source_id)
            if source["epoch"] != epoch or not source["perceive"]:
                raise PermissionError("source generation revoked or perception denied")
            self.store.put(
                "perception_source",
                self.world.source_key(source_id),
                {
                    **source,
                    "connected_until": self.world.clock() + lease_seconds,
                },
            )

    def disconnect(
        self, source_id: str, epoch: int, *, guard: Callable[[], None] | None = None
    ) -> None:
        with self.store.transaction():
            if guard:
                guard()
            source = self.world.source(source_id)
            if source["epoch"] != epoch:
                raise PermissionError("stale source cannot disconnect a new generation")
            self.store.put(
                "perception_source",
                self.world.source_key(source_id),
                {
                    **source,
                    "connected_until": 0.0,
                },
            )

    def revoke(self, source_id: str, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("revocation requires trusted owner authority")
        with self.store.transaction():
            source = self.world.source(source_id)
            self._discard_current(source_id)
            self.store.put(
                "perception_source",
                self.world.source_key(source_id),
                {
                    **source,
                    "epoch": int(source["epoch"]) + 1,
                    "perceive": False,
                    "retain": False,
                    "act": False,
                    "connected_until": 0.0,
                    "receipts": {},
                },
            )

        self._forget_volatile(source_id, int(source["epoch"]) + 1)

    def _discard_current(self, source_id: str) -> None:
        for row in self.store.all("world_current"):
            if row["relationship"] == self.world.relationship and row["source_id"] == source_id:
                self.store.delete("world_current", row["id"])

    def _forget_volatile(self, source_id: str, epoch: int) -> None:
        with self.store.lock:
            for identifier, observation in list(self.world.volatile.items()):
                if observation.source_id == source_id and observation.epoch < epoch:
                    self.world.volatile.pop(identifier, None)

    def _admit(self, source_id: str, epoch: int | None = None) -> dict[str, Any]:
        source = self.world.source(source_id)
        now = self.world.clock()
        if (
            epoch is not None
            and source["epoch"] != epoch
            or not source["perceive"]
            or float(source["connected_until"]) <= now
        ):
            raise PermissionError("source disconnected, expired or revoked")
        decision = self.policy.evaluate(
            "perception:ingest",
            ("perceive",),
            frozenset({"perceive"}),
            {"source_id": source_id, "relationship": self.world.relationship},
            now=now,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return source

    def acquisition_epoch(self, source_id: str) -> int:
        """Check before acquiring input; ingestion rechecks this same generation afterward."""
        with self.store.transaction():
            return int(self._admit(source_id)["epoch"])

    def ingest(
        self,
        observation: Observation,
        *,
        sentry_generation: int | None = None,
        guard: Callable[[], None] | None = None,
    ) -> tuple[str, WorldState]:
        # Reparse at the trust boundary, including dataclasses altered by untrusted code.
        payload = json.dumps(record(observation), sort_keys=True)
        observation = Observation.parse(payload)
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        with self.store.transaction():
            if guard:
                guard()
            source = self._admit(observation.source_id, observation.epoch)
            now = self.world.clock()
            if sentry_generation is not None:
                settings = self.store.get("sentry_settings", self.world.relationship)
                if (
                    settings["generation"] != sentry_generation
                    or settings["mode"] == "manual"
                    or observation.source_id not in settings["source_ids"]
                    or settings["mode"] == "trigger_only"
                    and observation.key not in settings["trigger_keys"]
                ):
                    raise PermissionError("Sentry configuration changed before acquisition")
            if (
                observation.entity_id not in source["entities"]
                or observation.key not in source["keys"]
                or observation.kind not in source["kinds"]
            ):
                raise PermissionError("observation outside registered source scope")
            receipts = dict(source["receipts"])
            if observation.id in receipts:
                if receipts[observation.id] != fingerprint:
                    raise StateConflict("observation identity reused with changed content")
                return "duplicate", self.world.resolve(observation.entity_id, observation.key)
            if (
                observation.sequence <= source["last_sequence"]
                or observation.observed_at < source["last_observed_at"]
            ):
                raise StateConflict("out-of-order observation")
            if not observation.observed_at <= now < observation.fresh_until:
                raise ValueError("stale or future-dated observation")
            window = int(now // 60)
            count = source["count"] if window == source["window"] else 0
            if count >= source["events_per_minute"]:
                raise StateConflict("source rate limit; bounded synchronous backpressure")
            identifier = json.dumps(
                [
                    self.world.relationship,
                    observation.source_id,
                    observation.entity_id,
                    observation.key,
                ]
            )
            try:
                self.store.get("world_current", identifier)
            except KeyError:
                if len(self.store.all("world_current")) >= self.MAX_CURRENT:
                    raise StateConflict("current-state bound; purge expired projections") from None
            event_id = None
            if source["retain"]:
                retain = self.policy.evaluate(
                    "perception:retain",
                    ("retain",),
                    frozenset({"retain"}),
                    {"source_id": observation.source_id, "relationship": self.world.relationship},
                    now=now,
                )
                if not retain.allowed:
                    raise PermissionError(retain.reason)
                event_id = observation.archive_id(self.world.relationship)
                archive = self.world.archive
                if (
                    archive.db.execute(
                        "SELECT count(*) FROM archive_events WHERE relationship=? "
                        "AND forgotten=0 AND id<>? "
                        "AND json_extract(payload,'$.kind')='perception_observation'",
                        (self.world.relationship, event_id),
                    ).fetchone()[0]
                    >= self.MAX_HISTORY
                ):
                    raise StateConflict("retained observation bound; expire or forget sources")
                archive.append(
                    SourceEvent(
                        self.world.relationship,
                        payload,
                        "local://perception/" + observation.source_id,
                        observation.observed_at,
                        kind="perception_observation",
                        entity_ids=(observation.entity_id,),
                        sensitivity="synthetic" if source["simulated"] else "personal",
                        id=event_id,
                        turn_id=event_id,
                        episode_id=event_id,
                        expires_at=observation.observed_at + int(source["retention_seconds"]),
                        context_key=observation.entity_id + ":" + observation.key,
                    ),
                    retain_authorized=True,
                )
            self.store.put(
                "world_current",
                identifier,
                {
                    "id": identifier,
                    "relationship": self.world.relationship,
                    "source_id": observation.source_id,
                    "entity_id": observation.entity_id,
                    "key": observation.key,
                    "epoch": observation.epoch,
                    "sequence": observation.sequence,
                    "observation_id": observation.id,
                    "fresh_until": observation.fresh_until,
                    "event_id": event_id,
                },
            )
            receipts[observation.id] = fingerprint
            while len(receipts) > 128:
                receipts.pop(next(iter(receipts)))
            self.store.put(
                "perception_source",
                self.world.source_key(observation.source_id),
                {
                    **source,
                    "last_sequence": observation.sequence,
                    "last_observed_at": observation.observed_at,
                    "window": window,
                    "count": count + 1,
                    "receipts": receipts,
                },
            )
        if event_id is None:
            with self.store.lock:
                # Publish only committed content, and never resurrect a concurrently revoked row.
                try:
                    pointer = self.store.get("world_current", identifier)
                except KeyError:
                    pointer = {}
                if (
                    pointer.get("observation_id") == observation.id
                    and pointer.get("epoch") == observation.epoch
                ):
                    while len(self.world.volatile) >= self.MAX_CURRENT:
                        self.world.volatile.pop(next(iter(self.world.volatile)))
                    self.world.volatile[identifier] = observation
        return "accepted", self.world.resolve(observation.entity_id, observation.key)
