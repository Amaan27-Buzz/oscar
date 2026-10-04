"""Deterministic user-authoritative rules, separate from permissions and inferred memory."""

import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from time import time

from .contracts import record
from .credentials import redact_runtime_secrets
from .storage import Store


class PolicyEffect(StrEnum):
    DENY = "deny"
    ASK = "ask"
    ALLOW = "allow"
    PREFER = "prefer"


@dataclass(frozen=True)
class PolicyRule:
    id: str
    capability: str
    effect: PolicyEffect
    source: str
    created_at: float
    updated_at: float
    conditions: dict[str, str]
    priority: int = 0
    enabled: bool = True
    user_authoritative: bool = True
    preference: str | None = None
    expires_at: float | None = None
    numeric_limits: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.source or not self.capability:
            raise ValueError("policy needs identity, scope and provenance")
        if "*" in self.capability[:-1]:
            raise ValueError("only trailing wildcard is supported")
        if (
            not all(math.isfinite(v) and v >= 0 for v in (self.created_at, self.updated_at))
            or self.expires_at is not None
            and not math.isfinite(self.expires_at)
            or type(self.priority) is not int
            or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in self.conditions.items()
            )
        ):
            raise ValueError("invalid structured policy contract")
        if self.updated_at < self.created_at:
            raise ValueError("invalid policy timestamps")
        if (
            not isinstance(self.numeric_limits, dict)
            or len(self.numeric_limits) > 8
            or any(
                not isinstance(k, str)
                or not k
                or len(k) > 100
                or type(v) not in {int, float}
                or not math.isfinite(v)
                or not 0 <= v <= 1_000_000
                for k, v in self.numeric_limits.items()
            )
        ):
            raise ValueError("invalid bounded numeric action constraints")


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    rule_ids: tuple[str, ...] = ()
    preference: str | None = None


class PersonalPolicy:
    def __init__(self, store: Store, redact: Callable[[str], str] = redact_runtime_secrets):
        self.store, self.redact = store, redact

    def save(self, rule: PolicyRule, *, owner_authorized: bool) -> None:
        if not owner_authorized or not rule.user_authoritative:
            raise PermissionError("candidates cannot become authoritative without owner authority")
        data = json.dumps(record(rule))
        if self.redact(data) != data:
            raise ValueError("credential material cannot enter Personal Policy")
        self.store.put("personal_policy", rule.id, record(rule))

    def rules(self) -> list[PolicyRule]:
        return [
            PolicyRule(**{**r, "effect": PolicyEffect(r["effect"])})
            for r in self.store.all("personal_policy")
        ]

    def evaluate(
        self,
        capability: str,
        permissions: tuple[str, ...],
        granted: frozenset[str],
        context: dict[str, str] | None = None,
        *,
        hard_allowed: bool = True,
        confirmed: bool = False,
        confirmation_required: bool = False,
        now: float | None = None,
    ) -> PolicyDecision:
        if not hard_allowed:
            return PolicyDecision(False, "hard safety/platform boundary")
        if not set(permissions) <= granted:
            return PolicyDecision(False, "required permission absent")
        if confirmation_required and not confirmed:
            return PolicyDecision(False, "explicit confirmation required")
        now = time() if now is None else now
        context = context or {}
        matches = [
            r
            for r in self.rules()
            if r.enabled
            and r.user_authoritative
            and (r.expires_at is None or now < r.expires_at)
            and (
                capability.startswith(r.capability[:-1])
                if r.capability.endswith("*")
                else capability == r.capability
            )
            and all(context.get(k) == v for k, v in r.conditions.items())
        ]
        if not matches:
            return PolicyDecision(True, "within granted scope")

        # Specificity precedes priority. Equal-ranking contradictory rules fail closed.
        def rank(r: PolicyRule) -> tuple[int, int, int]:
            return len(r.conditions), len(r.capability.rstrip("*")), r.priority

        best = max(rank(r) for r in matches)
        selected = [r for r in matches if rank(r) == best]
        ids = tuple(sorted(r.id for r in selected))
        effects = {r.effect for r in selected}
        if len(effects) > 1 or len({r.preference for r in selected}) > 1:
            return PolicyDecision(
                False, "conflicting explicit policies; resolve before action", ids
            )
        effect = selected[0].effect
        if effect == PolicyEffect.DENY:
            return PolicyDecision(False, "explicit policy denies action", ids)
        if effect == PolicyEffect.ASK and not confirmed:
            return PolicyDecision(False, "personal policy requires confirmation", ids)
        for rule in selected:
            for key, maximum in rule.numeric_limits.items():
                try:
                    actual = float(context[key])
                except (KeyError, ValueError):
                    return PolicyDecision(False, "action constraint evidence missing", ids)
                if not math.isfinite(actual) or abs(actual) > maximum:
                    return PolicyDecision(False, "action exceeds owner numeric constraint", ids)
        return PolicyDecision(True, "explicit policy applied", ids, selected[0].preference)
