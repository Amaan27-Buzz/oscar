"""Fast typed intent/epistemic decisions. Never selects a model or executor."""

import re
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter


class DecisionRoute(StrEnum):
    KNOWN = "known"
    WORLD = "world"
    RECALL = "recall"
    VERIFY = "verify"
    REASON = "reason"
    REPORTED = "reported"
    SPECIALIST = "specialist"
    WORKER = "worker"
    UNKNOWN = "unknown"


class ExecutionClass(StrEnum):
    CAPABILITY = "deterministic_capability"
    RETRIEVAL = "retrieval_live_source"
    VERIFICATION = "verification"
    MODEL = "model_reasoning"
    SPECIALIST = "specialist_executor"
    WORKER = "worker"
    ASK = "ask_user"


@dataclass(frozen=True)
class Intent:
    text: str
    kind: str | None = None
    path: str | None = None
    content: str | None = None


@dataclass(frozen=True)
class Decision:
    route: DecisionRoute
    execution_class: ExecutionClass
    capability_kind: str | None
    reason: str
    latency_ms: float
    repair: str


def decide(intent: Intent) -> Decision:
    start = perf_counter()
    text = intent.text.lower().strip()
    route, execution, kind, reason = (
        DecisionRoute.UNKNOWN,
        ExecutionClass.ASK,
        None,
        "request is unsupported or ambiguous",
    )
    if intent.kind == "file_write" and intent.path is not None and intent.content is not None:
        route, execution, kind, reason = (
            DecisionRoute.KNOWN,
            ExecutionClass.CAPABILITY,
            "file_write",
            "explicit file objective",
        )
    elif re.fullmatch(r"(?:what is\s+)?\d{1,12}\s*\+\s*\d{1,12}\??", text):
        route, execution, kind, reason = (
            DecisionRoute.KNOWN,
            ExecutionClass.CAPABILITY,
            "addition",
            "bounded integer addition",
        )
    elif text.startswith(("did ", "verify ", "check whether ")):
        route, execution, kind, reason = (
            DecisionRoute.VERIFY,
            ExecutionClass.VERIFICATION,
            "live_verify",
            "requires authoritative check",
        )
    elif any(word in text for word in ("latest calendar", "calendar today", "current weather")):
        route, execution, kind, reason = (
            DecisionRoute.WORLD,
            ExecutionClass.RETRIEVAL,
            "live_source",
            "current facts require live source",
        )
    elif text.startswith(("recall ", "remember ")):
        route, execution, kind, reason = (
            DecisionRoute.RECALL,
            ExecutionClass.RETRIEVAL,
            "memory",
            "historical context is recalled",
        )
    elif text.startswith(("worker reports ", "tool reports ")):
        route, execution, kind, reason = (
            DecisionRoute.REPORTED,
            ExecutionClass.VERIFICATION,
            "live_verify",
            "testimony requires verification",
        )
    elif text.startswith(("fix ", "debug ", "implement ")):
        route, execution, kind, reason = (
            DecisionRoute.SPECIALIST,
            ExecutionClass.SPECIALIST,
            "coding",
            "repository work requires coding capability",
        )
    elif text.startswith(("monitor ", "delegate ")):
        route, execution, kind, reason = (
            DecisionRoute.WORKER,
            ExecutionClass.WORKER,
            "worker",
            "durable responsibility needs worker",
        )
    elif intent.kind == "reason" or text.startswith(("reason ", "analyze ", "explain ")):
        route, execution, kind, reason = (
            DecisionRoute.REASON,
            ExecutionClass.MODEL,
            None,
            "explicit reasoning request",
        )
    repair = (
        "ask for required details"
        if execution == ExecutionClass.ASK
        else "block if capability unavailable"
    )
    return Decision(route, execution, kind, reason, (perf_counter() - start) * 1000, repair)
