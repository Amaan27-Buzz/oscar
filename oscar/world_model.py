"""Bounded current-state projection; retained observations live only in Event Archive."""

import hashlib
import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from time import time
from typing import Any

from .contracts import Epistemic, record
from .credentials import redact_runtime_secrets
from .event_archive import EventArchive
from .storage import Store


class ObservationKind(StrEnum):
    PERSON = "person"
    DEVICE = "device"
    APPLICATION = "application"
    PROJECT = "project"
    TASK = "task"
    SCHEDULE = "schedule"
    COMMUNICATION = "communication"
    ENVIRONMENT = "environment"
    CONNECTIVITY = "connectivity"
    SENSOR = "sensor"


def reference(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[\w.:/-]{1,160}", value, re.ASCII):
        raise ValueError("bounded stable reference required")


@dataclass(frozen=True)
class Observation:
    id: str
    source_id: str
    epoch: int
    sequence: int
    entity_id: str
    key: str
    kind: ObservationKind
    value: str
    observed_at: float
    fresh_until: float
    confidence: float
    evidence_id: str | None = None
    unavailable: bool = False
    version: int = 1

    def __post_init__(self) -> None:
        for value in (self.id, self.source_id, self.entity_id, self.key):
            reference(value)
        if self.evidence_id is not None:
            reference(self.evidence_id)
        if (
            type(self.version) is not int
            or self.version != 1
            or not isinstance(self.kind, ObservationKind)
            or type(self.epoch) is not int
            or not 1 <= self.epoch <= 2**53
            or type(self.sequence) is not int
            or not 1 <= self.sequence <= 2**53
            or type(self.unavailable) is not bool
            or not isinstance(self.value, str)
            or not 1 <= len(self.value.encode()) <= 2048
            or any(
                type(n) not in {int, float} or not math.isfinite(n)
                for n in (self.observed_at, self.fresh_until, self.confidence)
            )
            or not 0 <= self.confidence <= 1
            or not 0 <= self.observed_at < self.fresh_until <= self.observed_at + 3600
        ):
            raise ValueError("invalid versioned observation")
        payload = json.dumps(record(self), sort_keys=True)
        EventArchive._safe(payload)

    @classmethod
    def parse(cls, payload: str) -> "Observation":
        if not isinstance(payload, str) or len(payload.encode()) > 16000:
            raise ValueError("bounded observation payload required")
        data = json.loads(payload)
        return cls(**{**data, "kind": ObservationKind(data["kind"])})

    def archive_id(self, relationship: str) -> str:
        return hashlib.sha256(
            json.dumps([relationship, self.source_id, self.epoch, self.id]).encode()
        ).hexdigest()


@dataclass(frozen=True)
class WorldState:
    entity_id: str
    key: str
    state: str
    observations: tuple[Observation, ...] = ()
    simulated: bool = False
    epistemic: Epistemic = Epistemic.UNKNOWN

    @property
    def value(self) -> str | None:
        return self.observations[0].value if self.state == "current" else None


class WorldModel:
    def __init__(
        self,
        store: Store,
        archive: EventArchive,
        relationship: str,
        *,
        clock: Callable[[], float] = time,
    ):
        reference(relationship)
        self.store, self.archive, self.relationship, self.clock = (
            store,
            archive,
            relationship,
            clock,
        )
        self.volatile: dict[str, Observation] = {}

    def source_key(self, source_id: str) -> str:
        reference(source_id)
        return json.dumps([self.relationship, source_id])

    def source(self, source_id: str) -> dict[str, Any]:
        source = self.store.get("perception_source", self.source_key(source_id))
        if (
            source.get("id") != source_id
            or source.get("relationship") != self.relationship
            or type(source.get("epoch")) is not int
            or source["epoch"] < 1
            or any(
                type(source.get(key)) is not bool
                for key in ("perceive", "retain", "act", "simulated")
            )
            or type(source.get("connected_until")) not in {int, float}
            or not math.isfinite(source["connected_until"])
        ):
            raise ValueError("corrupt source authority metadata")
        return source

    def resolve(self, entity_id: str, key: str) -> WorldState:
        reference(entity_id)
        reference(key)
        with self.store.lock:
            if self.store.db.in_transaction:
                return self._resolve(entity_id, key)
            with self.store.transaction():
                return self._resolve(entity_id, key)

    def _resolve(self, entity_id: str, key: str) -> WorldState:
        now = self.clock()
        candidates: list[tuple[Observation, dict[str, Any]]] = []
        stale, unavailable = False, False
        rows = [
            json.loads(row[0])
            for row in self.store.db.execute(
                "SELECT data FROM records WHERE kind='world_current' "
                "AND json_extract(data,'$.relationship')=? "
                "AND json_extract(data,'$.entity_id')=? AND json_extract(data,'$.key')=?",
                (self.relationship, entity_id, key),
            )
        ]
        for row in rows:
            try:
                source = self.source(row["source_id"])
            except (KeyError, ValueError, TypeError):
                unavailable = True
                continue
            if not source["perceive"] or source["epoch"] != row["epoch"]:
                continue
            if not source["connected_until"] or float(source["connected_until"]) <= now:
                unavailable = True
                continue
            try:
                if row["event_id"]:
                    event = self.archive.event(row["event_id"])
                    if (
                        event.relationship_id != self.relationship
                        or event.kind != "perception_observation"
                    ):
                        raise ValueError("canonical observation envelope mismatch")
                    observation = Observation.parse(event.content)
                    if observation.archive_id(self.relationship) != event.id:
                        raise ValueError("canonical observation identity mismatch")
                else:
                    observation = self.volatile[row["id"]]
                if (
                    observation.source_id != row["source_id"]
                    or observation.entity_id != entity_id
                    or observation.key != key
                    or observation.epoch != row["epoch"]
                    or observation.id != row["observation_id"]
                    or observation.sequence != row["sequence"]
                ):
                    raise ValueError("current projection identity mismatch")
            except (KeyError, ValueError, TypeError):
                unavailable = True
                continue
            if not observation.observed_at <= now < observation.fresh_until:
                stale = True
            elif observation.unavailable:
                unavailable = True
            else:
                candidates.append((observation, source))
        if not candidates:
            return WorldState(
                entity_id, key, "unavailable" if unavailable else "stale" if stale else "unknown"
            )
        # Fixture signals cannot displace a real source, even when they are newer.
        real = [c for c in candidates if not c[1]["simulated"]]
        selected = real or candidates
        observations = tuple(sorted((c[0] for c in selected), key=lambda o: o.source_id))
        conflict = len({o.value for o in observations}) > 1
        return WorldState(
            entity_id,
            key,
            "conflicting" if conflict else "current",
            observations,
            simulated=not bool(real),
            epistemic=Epistemic.UNKNOWN if conflict else Epistemic.REPORTED,
        )

    def purge(self) -> int:
        """Remove expired/forgotten current pointers, never create historical copies."""
        removed = 0
        with self.store.transaction():
            for row in self.store.all("world_current"):
                if row["relationship"] != self.relationship:
                    continue
                missing = False
                if row["event_id"]:
                    try:
                        self.archive.event(row["event_id"])
                    except KeyError:
                        missing = True
                if row["fresh_until"] <= self.clock() or missing:
                    self.store.delete("world_current", row["id"])
                    self.volatile.pop(row["id"], None)
                    removed += 1
        return removed

    def safe(self, payload: str) -> None:
        if redact_runtime_secrets(payload) != payload:
            raise ValueError("credential-bearing source metadata rejected")
