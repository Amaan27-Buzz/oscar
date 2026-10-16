"""Headless Sentry decisions. No capture, notification delivery or action authority."""

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .contracts import record
from .jev import Intent, decide
from .memory_fabric import MemoryFabric
from .perception import PerceptionFabric
from .world_model import Observation, reference


class AwarenessMode(StrEnum):
    MANUAL = "manual"
    TRIGGER_ONLY = "trigger_only"
    SENTRY = "sentry"


class SentryState(StrEnum):
    PASSIVE = "passive"
    AWARE = "aware"
    GUARD = "guard"
    AWAY = "away"
    SLEEP = "sleep"


@dataclass(frozen=True)
class SentrySettings:
    mode: AwarenessMode = AwarenessMode.MANUAL
    state: SentryState = SentryState.PASSIVE
    source_ids: tuple[str, ...] = ()
    trigger_keys: tuple[str, ...] = ()
    min_confidence: float = 0.9
    cooldown_seconds: int = 60
    allow_interrupt: bool = False
    version: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.mode, AwarenessMode)
            or not isinstance(self.state, SentryState)
            or type(self.version) is not int
            or self.version != 1
            or type(self.allow_interrupt) is not bool
            or type(self.cooldown_seconds) is not int
            or not 1 <= self.cooldown_seconds <= 3600
            or type(self.min_confidence) not in {float, int}
            or not math.isfinite(self.min_confidence)
            or not 0 <= self.min_confidence <= 1
        ):
            raise ValueError("invalid Sentry settings")
        for values in (self.source_ids, self.trigger_keys):
            if not isinstance(values, tuple) or len(values) > 32 or len(set(values)) != len(values):
                raise ValueError("bounded Sentry sources/triggers required")
            for value in values:
                reference(value)


@dataclass(frozen=True)
class SentryDecision:
    outcome: str
    reason: str
    observation_id: str
    simulated: bool
    policy_ids: tuple[str, ...] = ()


class SentryRuntime:
    def __init__(self, fabric: PerceptionFabric, memory: MemoryFabric | None = None):
        if memory is not None and memory.archive is not fabric.world.archive:
            raise ValueError("Sentry must use the canonical Memory Fabric")
        self.fabric, self.world, self.memory = fabric, fabric.world, memory

    def configure(self, settings: SentrySettings, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("Sentry activation requires trusted owner authority")
        with self.world.store.transaction():
            for source_id in settings.source_ids:
                self.world.source(source_id)
            prior = self.world.store.all("sentry_settings")
            if len(prior) >= 64 and not any(
                r["relationship"] == self.world.relationship for r in prior
            ):
                raise ValueError("Sentry configuration bound")
            self.world.store.put(
                "sentry_settings",
                self.world.relationship,
                {
                    **record(settings),
                    "relationship": self.world.relationship,
                    "generation": next(
                        (
                            r["generation"]
                            for r in prior
                            if r["relationship"] == self.world.relationship
                        ),
                        0,
                    )
                    + 1,
                },
            )
            # Old queued decisions cannot acquire authority under a changed configuration.
            for row in self.world.store.all("sentry_cooldown"):
                if row["relationship"] == self.world.relationship:
                    self.world.store.delete("sentry_cooldown", row["id"])

    def settings(self) -> SentrySettings:
        return self.configuration()[0]

    def configuration(self) -> tuple[SentrySettings, int]:
        try:
            data = self.world.store.get("sentry_settings", self.world.relationship)
        except KeyError:
            return SentrySettings(), 0
        data.pop("relationship")
        generation = data.pop("generation")
        return SentrySettings(
            **{
                **data,
                "mode": AwarenessMode(data["mode"]),
                "state": SentryState(data["state"]),
                "source_ids": tuple(data["source_ids"]),
                "trigger_keys": tuple(data["trigger_keys"]),
            }
        ), generation

    def observe(self, observation: Observation, *, urgent: bool = False) -> SentryDecision:
        if type(urgent) is not bool:
            raise ValueError("typed urgency required")
        with self.world.store.lock:
            settings, generation = self.configuration()
            source = self.world.source(observation.source_id)
            simulated = bool(source["simulated"])

            def result(outcome: str, reason: str, ids: tuple[str, ...] = ()) -> SentryDecision:
                return SentryDecision(outcome, reason, observation.id, simulated, ids)

            if (
                settings.mode == AwarenessMode.MANUAL
                or observation.source_id not in settings.source_ids
            ):
                return result("ignored", "awareness disabled or source not selected")
            if (
                settings.mode == AwarenessMode.TRIGGER_ONLY
                and observation.key not in settings.trigger_keys
            ):
                return result("ignored", "outside selected triggers")
            disposition, _ = self.fabric.ingest(observation, sentry_generation=generation)
            if disposition == "duplicate":
                return result("ignored", "duplicate event")
            return self._evaluate(observation, settings, generation, simulated, urgent)

    def _evaluate(
        self,
        observation: Observation,
        settings: SentrySettings,
        generation: int,
        simulated: bool,
        urgent: bool,
    ) -> SentryDecision:
        def result(outcome: str, reason: str, ids: tuple[str, ...] = ()) -> SentryDecision:
            return SentryDecision(outcome, reason, observation.id, simulated, ids)

        # Serialize the final grant/configuration check with revocation and cooldown admission.
        with self.world.store.transaction():
            current = self.world.store.get("sentry_settings", self.world.relationship)
            source = self.world.source(observation.source_id)
            if (
                current["generation"] != generation
                or source["epoch"] != observation.epoch
                or not source["perceive"]
                or source["connected_until"] <= self.world.clock()
            ):
                return result("ignored", "source or Sentry configuration changed during ingestion")
            state = self.world.resolve(observation.entity_id, observation.key)
            if (
                state.state != "current"
                or observation.unavailable
                or observation not in state.observations
            ):
                return result("context", "conflicting, unavailable or stale state cannot escalate")
            if observation.confidence < settings.min_confidence:
                return result("context", "insufficient confidence for escalation")
            if observation.key not in settings.trigger_keys:
                return result("context", "quiet context update")
            if settings.state == SentryState.SLEEP and not urgent:
                return result("context", "sleep suppresses nonurgent interruption")
            if not settings.allow_interrupt or not source["act"]:
                return result("context", "perception is not interruption authority")
            now = self.world.clock()
            cooldown_id = self.world.source_key(observation.source_id) + ":" + observation.key
            try:
                prior = self.world.store.get("sentry_cooldown", cooldown_id)
                if now - prior["at"] < settings.cooldown_seconds:
                    return result("context", "false-trigger cooldown")
            except KeyError:
                pass
            permission = self.fabric.policy.evaluate(
                "sentry:interrupt",
                ("act",),
                frozenset({"act"}),
                {
                    "source_id": observation.source_id,
                    "state": settings.state.value,
                    "relationship": self.world.relationship,
                },
                now=now,
            )
            if not permission.allowed:
                return result("context", permission.reason, permission.rule_ids)
            self.world.store.put(
                "sentry_cooldown",
                cooldown_id,
                {
                    "id": cooldown_id,
                    "relationship": self.world.relationship,
                    "at": now,
                },
            )
            return result(
                "interrupt_proposed",
                "requires a separately authorized delivery capability",
                permission.rule_ids,
            )

    def context(self, entity_id: str, key: str) -> dict[str, Any]:
        """Controller routes current retrieval; historical evidence stays explicitly recalled."""
        reference(entity_id)
        reference(key)
        decision = decide(Intent("current status of project " + entity_id))
        state = self.world.resolve(entity_id, key)
        memories: list[dict[str, Any]] = []
        attempts: tuple[str, ...] = ()
        if self.memory:
            recall = self.memory.retrieve(self.world.relationship, entity_id + " " + key)
            assembled = self.memory.context(
                recall, objective=key, project=None, live={}, policy_ids=()
            )
            memories = assembled["memories"]
            attempts = recall.attempts
        return {
            "version": 1,
            "controller_route": decision.route,
            "current": record(state),
            "historical": memories,
            "retrieval_attempts": attempts,
            "memory_status": "RECALLED" if memories else "UNKNOWN",
        }
