"""Versioned domain contracts shared by execution, transport and verification."""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

PROTOCOL_VERSION = 1


def new_id() -> str:
    return uuid4().hex


class Epistemic(StrEnum):
    KNOWN = "KNOWN"
    INFERRED = "INFERRED"
    RECALLED = "RECALLED"
    REPORTED = "REPORTED"
    VERIFIED = "VERIFIED"
    UNKNOWN = "UNKNOWN"


class TaskState(StrEnum):
    PLANNED = "planned"
    EXECUTING = "executing"
    AWAITING_RESULT = "awaiting_result"
    RESULT_RECEIVED = "result_received"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


TERMINAL = {TaskState.VERIFIED, TaskState.FAILED, TaskState.CANCELLED}
TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PLANNED: {TaskState.EXECUTING, TaskState.BLOCKED, TaskState.UNKNOWN},
    TaskState.EXECUTING: {TaskState.AWAITING_RESULT, TaskState.BLOCKED, TaskState.FAILED},
    TaskState.AWAITING_RESULT: {TaskState.RESULT_RECEIVED, TaskState.BLOCKED, TaskState.FAILED},
    TaskState.RESULT_RECEIVED: {TaskState.VERIFYING, TaskState.BLOCKED, TaskState.FAILED},
    TaskState.VERIFYING: {
        TaskState.VERIFIED,
        TaskState.PARTIALLY_VERIFIED,
        TaskState.FAILED,
        TaskState.UNKNOWN,
    },
    TaskState.BLOCKED: {TaskState.PLANNED, TaskState.UNKNOWN},
    TaskState.PARTIALLY_VERIFIED: {TaskState.VERIFYING},
    TaskState.UNKNOWN: {TaskState.PLANNED},
}


@dataclass(frozen=True)
class Objective:
    id: str
    description: str
    initiator: str
    criterion: dict[str, Any]
    created_at: float
    correlation_id: str = field(default_factory=new_id)


@dataclass
class Task:
    id: str
    objective_id: str
    correlation_id: str
    state: TaskState = TaskState.PLANNED
    attempts: int = 0
    retry_budget: int = 2
    cancelled: bool = False
    blocker: str | None = None
    lease_id: str | None = None
    decision: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(**{**data, "state": TaskState(data["state"])})


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    summary: str
    execution_class: str
    node_id: str
    permissions: tuple[str, ...]
    input_kind: str
    output_kind: str
    risk: str = "low"
    version: int = PROTOCOL_VERSION
    reversible: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Capability":
        return cls(**{**data, "permissions": tuple(data["permissions"])})


@dataclass(frozen=True)
class Action:
    id: str
    task_id: str
    correlation_id: str
    capability_id: str
    parameters: dict[str, Any]
    idempotency_key: str
    initiator: str


@dataclass(frozen=True)
class ArtifactRef:
    id: str
    task_id: str
    producer: str
    kind: str
    location: str
    created_at: float
    status: Epistemic = Epistemic.REPORTED
    content_hash: str | None = None
    access_scope: str = "owner"


@dataclass(frozen=True)
class Result:
    id: str
    action_id: str
    task_id: str
    correlation_id: str
    executor: str
    success: bool
    value: str | None = None
    error: str | None = None
    status: Epistemic = Epistemic.REPORTED
    artifact: ArtifactRef | None = None


@dataclass(frozen=True)
class Evidence:
    id: str
    task_id: str
    correlation_id: str
    source: str
    method: str
    observed_at: float
    matches: bool | None
    status: Epistemic
    detail: str
    artifact_id: str | None = None
    content_hash: str | None = None


@dataclass(frozen=True)
class Verification:
    state: TaskState
    evidence: Evidence


@dataclass(frozen=True)
class Envelope:
    kind: str
    node_id: str
    session_id: str
    task_id: str
    correlation_id: str
    lease_id: str
    payload: dict[str, Any]
    sent_at: float
    nonce: str = field(default_factory=new_id)
    version: int = PROTOCOL_VERSION

    @classmethod
    def parse(cls, data: dict[str, Any]) -> "Envelope":
        expected = set(cls.__dataclass_fields__)
        if set(data) != expected:
            raise ValueError("invalid envelope fields")
        for key in expected - {"payload", "sent_at", "version"}:
            if not isinstance(data[key], str) or not data[key] or len(data[key]) > 128:
                raise ValueError("invalid envelope identifier")
        if data["version"] != PROTOCOL_VERSION or type(data["version"]) is not int:
            raise ValueError("unsupported protocol version")
        if data["kind"] not in {"action", "progress", "result", "cancel", "heartbeat"}:
            raise ValueError("unsupported message kind")
        if not isinstance(data["payload"], dict) or type(data["sent_at"]) not in {int, float}:
            raise ValueError("invalid envelope payload/time")
        return cls(**data)


def record(value: Any) -> dict[str, Any]:
    """Only domain records; credential material never enters this serializer."""
    return dict(asdict(value))
