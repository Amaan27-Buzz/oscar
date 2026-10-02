"""Evidence-backed core loop; planning, dispatch and independent verification stay separate."""

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from time import time
from typing import Any

from .capabilities import Cancelled, Verifier
from .contracts import (
    Action,
    Envelope,
    Epistemic,
    Evidence,
    Objective,
    Task,
    TaskState,
    new_id,
    record,
)
from .credentials import redact_runtime_secrets
from .grid import Grid, SessionHandle
from .jev import ExecutionClass, Intent, decide
from .storage import StateConflict, Store
from .transport import Transport, action_envelope, parse_result


class Runtime:
    def __init__(
        self,
        store: Store,
        grid: Grid,
        verifier: Verifier,
        on_verification: Callable[[Evidence], None] | None = None,
    ):
        self.store, self.grid, self.verifier = store, grid, verifier
        self.on_verification = on_verification

    def create(
        self, intent: Intent, initiator: str = "owner", retry_budget: int = 2, mode: str = "auto"
    ) -> Task:
        if not 0 <= retry_budget <= 5:
            raise ValueError("retry budget must be between zero and five")
        decision = decide(intent)
        criterion: dict[str, Any] = {"kind": "unavailable"}
        parameters: dict[str, Any] = {}
        kind = decision.capability_kind
        if intent.kind == "capability" and intent.parameters is not None:
            parameters = intent.parameters
            criterion = intent.criterion or {"kind": "unavailable"}
        elif kind == "file_write":
            criterion = {"kind": "file_exact", "path": intent.path, "content": intent.content}
            parameters = {"path": intent.path, "content": intent.content}
        elif kind == "addition":
            criterion = {"kind": "addition", "expression": intent.text}
            parameters = {"expression": intent.text}
        elif decision.execution_class == ExecutionClass.MODEL:
            kind = "model_reasoning"
            parameters = {"prompt": intent.text, "mode": mode}
        elif kind == "live_source":
            parameters = {"query": intent.text, "freshness": decision.freshness.value}
        material = json.dumps(
            {"description": intent.text, "parameters": parameters, "criterion": criterion},
            allow_nan=False,
        )
        if redact_runtime_secrets(material) != material:
            raise ValueError("credential material cannot enter durable objectives/plans")
        objective = Objective(new_id(), intent.text, initiator, criterion, time())
        task = Task(
            new_id(),
            objective.id,
            objective.correlation_id,
            retry_budget=retry_budget,
            decision=decision.execution_class,
        )
        with self.store.transaction():
            self.store.put("objective", objective.id, record(objective))
            self.store.put("task", task.id, record(task))
            self.store.put("plan", task.id, {"kind": kind, "parameters": parameters})
            self.store.audit(task.id, "jev_decision", record(decision))
        if decision.execution_class == ExecutionClass.ASK:
            return self.store.transition(task.id, TaskState.UNKNOWN, blocker=decision.reason)
        if not kind or not self.grid.search(kind):
            return self.store.transition(
                task.id,
                TaskState.BLOCKED,
                blocker=(
                    "live retrieval unavailable: UNKNOWN / potentially stale"
                    if kind == "live_source"
                    else "required capability is not advertised"
                ),
            )
        return task

    def run(self, task_id: str, transports: Mapping[str, tuple[Transport, SessionHandle]]) -> Task:
        task = self.store.task(task_id)
        if task.state != TaskState.PLANNED:
            return task
        plan = self.store.get("plan", task.id)
        candidates = [c for c in self.grid.search(plan["kind"]) if c.node_id in transports]
        if not candidates:
            return self.store.transition(
                task.id, TaskState.BLOCKED, blocker="no reachable executor"
            )
        capability = candidates[0]
        transport, session = transports[capability.node_id]
        try:
            task = self.store.transition(task.id, TaskState.EXECUTING, expected=TaskState.PLANNED)
        except StateConflict:
            return self.store.task(task.id)
        lease_id: str | None = None
        try:
            lease_id = self.grid.lease(task.id, capability.node_id, ttl=120)
            try:
                data = self.store.get("planned_action", task.id)
                action = Action(**data)
                if action.capability_id != capability.id:
                    raise StateConflict(
                        "recovery requires original executor or independent inspection"
                    )
            except KeyError:
                action = Action(
                    new_id(),
                    task.id,
                    task.correlation_id,
                    capability.id,
                    plan["parameters"],
                    task.id,
                    Objective(**self.store.get("objective", task.objective_id)).initiator,
                )
                self.store.put("planned_action", task.id, record(action))
                self.store.put("action", action.id, record(action))
            task = self.store.transition(
                task.id, TaskState.AWAITING_RESULT, expected_lease=lease_id
            )
            result = parse_result(
                record(transport.invoke(action_envelope(action, session, lease_id), session))
            )
            if (
                result.action_id != action.id
                or result.task_id != task.id
                or result.correlation_id != task.correlation_id
            ):
                raise ValueError("transport returned unrelated result")
            self.store.put("result", result.id, record(result))
            if result.artifact:
                self.store.put("artifact", result.artifact.id, record(result.artifact))
            self.store.audit(
                task.id,
                "executor_result",
                {
                    "result_id": result.id,
                    "status": result.status,
                    "success": result.success,
                    "executor": result.executor,
                    "correlation_id": result.correlation_id,
                },
            )
            self.grid.accept(
                Envelope(
                    "result",
                    session.node_id,
                    session.id,
                    task.id,
                    task.correlation_id,
                    lease_id,
                    {"result_id": result.id},
                    self.grid.clock(),
                ),
                session.token,
                "execute",
            )
            self.grid.release(lease_id)
            if self.store.task(task.id).cancelled:
                return self.store.task(task.id)
            self.store.transition(task.id, TaskState.RESULT_RECEIVED, expected_lease=lease_id)
            if not result.success:
                return self.store.transition(
                    task.id,
                    TaskState.BLOCKED
                    if result.error
                    and (
                        result.error.startswith(
                            ("freshness_unavailable", "connector_blocked:", "machine_blocked:")
                        )
                        or result.error
                        in {"route_unavailable", "network_policy_blocked", "network_failure"}
                    )
                    else TaskState.FAILED,
                    blocker=result.error or "executor reported failure",
                    expected_lease=lease_id,
                )
            self.store.transition(task.id, TaskState.VERIFYING, expected_lease=lease_id)
            objective = Objective(**self.store.get("objective", task.objective_id))
            verification = self.verifier.verify(objective, result)
            task = self.store.transition(
                task.id, verification.state, evidence=verification.evidence, expected_lease=lease_id
            )
            if self.on_verification:
                try:
                    self.on_verification(verification.evidence)
                except (KeyError, ValueError, StateConflict):
                    self.store.audit(task.id, "observation_link_unavailable", {"status": "UNKNOWN"})
            if (
                result.artifact
                and task.state == TaskState.VERIFIED
                and verification.evidence.artifact_id == result.artifact.id
            ):
                artifact = replace(
                    result.artifact,
                    status=Epistemic.VERIFIED,
                    content_hash=verification.evidence.content_hash,
                )
                self.store.put("artifact", artifact.id, record(artifact))
            return task
        except Cancelled:
            if lease_id is not None and self.store.task(task.id).lease_id != lease_id:
                return self.store.task(task.id)
            return self.cancel(task.id)
        except (StateConflict, PermissionError, OSError, ValueError):
            current = self.store.task(task.id)
            if lease_id is not None and current.lease_id != lease_id:
                return current
            if current.cancelled or current.state in {TaskState.BLOCKED, TaskState.FAILED}:
                return current
            if current.state == TaskState.VERIFYING:
                return self.store.transition(
                    task.id, TaskState.UNKNOWN, blocker="independent verification unavailable"
                )
            return self.store.transition(
                task.id,
                TaskState.BLOCKED,
                blocker="execution unavailable or outcome ambiguous; inspect ledger",
            )
        finally:
            current = self.store.task(task.id)
            if (
                lease_id is not None
                and current.lease_id == lease_id
                and current.state
                not in {
                    TaskState.EXECUTING,
                    TaskState.AWAITING_RESULT,
                }
            ):
                self.grid.release(lease_id)

    def cancel(
        self, task_id: str, transports: Mapping[str, tuple[Transport, SessionHandle]] | None = None
    ) -> Task:
        task = self.store.task(task_id)
        if task.state in {TaskState.VERIFIED, TaskState.FAILED, TaskState.CANCELLED}:
            return task
        task = self.store.transition(task_id, TaskState.CANCELLED)
        self.store.audit(task.id, "cancel_requested", {"correlation_id": task.correlation_id})
        if task.lease_id:
            lease = self.store.get("lease", task.lease_id)
            if transports and lease["node_id"] in transports and lease["active"]:
                transport, session = transports[lease["node_id"]]
                message = Envelope(
                    "cancel",
                    session.node_id,
                    session.id,
                    task.id,
                    task.correlation_id,
                    task.lease_id,
                    {},
                    self.grid.clock(),
                )
                try:
                    transport.control(message, session)
                    delivery = "REPORTED"
                except (StateConflict, PermissionError, ValueError, OSError):
                    delivery = "UNKNOWN"
                self.store.audit(task.id, "cancel_delivery", {"status": delivery})
            self.grid.release(task.lease_id)
        return task

    def reclaim(self, task_id: str) -> Task:
        task = self.store.task(task_id)
        if task.state not in {TaskState.BLOCKED, TaskState.UNKNOWN}:
            raise StateConflict("task is not reclaimable")
        if task.lease_id:
            lease = self.store.get("lease", task.lease_id)
            if lease["active"] and lease["expires_at"] > self.grid.clock():
                raise StateConflict("previous executor lease has not expired")
        if task.attempts >= task.retry_budget + 1:
            raise StateConflict("retry budget exhausted")
        return self.store.transition(task.id, TaskState.PLANNED)
