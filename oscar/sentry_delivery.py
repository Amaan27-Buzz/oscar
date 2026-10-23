"""Transient, separately authorized Sentry notices; never an observation archive."""

import hashlib
import json
from collections.abc import Callable
from typing import Any

from .policy import PolicyEffect
from .sentry import AwarenessMode, SentryRuntime, SentryState
from .world_model import Observation


class SentryDelivery:
    def __init__(self, sentry: SentryRuntime):
        self.sentry, self.world = sentry, sentry.world
        self.pending: dict[str, dict[str, Any]] = {}

    @staticmethod
    def digest(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def permission(self, source_id: str, state: str) -> tuple[str, ...]:
        policy = self.sentry.fabric.policy
        decision = policy.evaluate(
            "sentry:deliver",
            ("act",),
            frozenset({"act"}),
            {"source_id": source_id, "state": state, "relationship": self.world.relationship},
            now=self.world.clock(),
        )
        # Delivery is an independent owner grant, not the policy engine's no-rule default.
        return (
            decision.rule_ids
            if decision.allowed
            and any(
                rule.id in decision.rule_ids and rule.effect == PolicyEffect.ALLOW
                for rule in policy.rules()
            )
            else ()
        )

    def observe(self, observation: Observation, *, guard: Callable[[], None] | None = None) -> None:
        with self.world.store.transaction():
            decision = self.sentry.observe(observation, guard=guard)
            if decision.outcome != "interrupt_proposed":
                return
            settings, generation = self.sentry.configuration()
            policies = self.permission(observation.source_id, settings.state.value)
            if not policies:
                return
            key = json.dumps(
                [
                    self.world.relationship,
                    observation.source_id,
                    observation.entity_id,
                    observation.key,
                ]
            )
            digest = self.digest(observation.value)
            try:
                prior = self.world.store.get("sentry_notice_receipt", key)
            except KeyError:
                prior = {}
            if prior.get("digest") == digest:
                return
            if not prior and len(self.world.store.all("sentry_notice_receipt")) >= 512:
                return
            identifier = self.digest(key + observation.id)
            self.world.store.put(
                "sentry_notice_receipt",
                key,
                {
                    "relationship": self.world.relationship,
                    "digest": digest,
                },
            )
            self.pending[key] = {
                "id": identifier,
                "source_id": observation.source_id,
                "source_epoch": observation.epoch,
                "generation": generation,
                "observation_id": observation.id,
                "key": observation.key,
                "entity_id": observation.entity_id,
                "digest": digest,
                "fresh_until": min(observation.fresh_until, self.world.clock() + 60),
                "simulated": decision.simulated,
                "policy_ids": list(policies),
            }
            while len(self.pending) > 16:
                del self.pending[next(iter(self.pending))]

    def snapshot(self) -> list[dict[str, Any]]:
        with self.world.store.transaction():
            settings, generation = self.sentry.configuration()
            visible = []
            for key, alert in list(self.pending.items()):
                try:
                    source = self.world.source(alert["source_id"])
                except (KeyError, ValueError):
                    del self.pending[key]
                    continue
                state = self.world.resolve(alert["entity_id"], alert["key"])
                allowed = self.permission(alert["source_id"], settings.state.value)
                interruption = self.sentry.fabric.policy.evaluate(
                    "sentry:interrupt",
                    ("act",),
                    frozenset({"act"}),
                    {
                        "source_id": alert["source_id"],
                        "state": settings.state.value,
                        "relationship": self.world.relationship,
                    },
                    now=self.world.clock(),
                )
                if (
                    alert["fresh_until"] <= self.world.clock()
                    or settings.mode == AwarenessMode.MANUAL
                    or settings.state == SentryState.SLEEP
                    or not settings.allow_interrupt
                    or generation != alert["generation"]
                    or alert["source_id"] not in settings.source_ids
                    or alert["key"] not in settings.trigger_keys
                    or not source["perceive"]
                    or not source["act"]
                    or source["epoch"] != alert["source_epoch"]
                    or source["connected_until"] <= self.world.clock()
                    or state.state != "current"
                    or state.value is None
                    or self.digest(state.value) != alert["digest"]
                    or set(allowed) != set(alert["policy_ids"])
                    or not interruption.allowed
                ):
                    del self.pending[key]
                    continue
                visible.append({k: v for k, v in alert.items() if k not in {"digest", "entity_id"}})
            return visible
