"""Evidence-backed core loop; planning, dispatch and independent verification stay separate."""

import hashlib
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
from .memory_fabric import MemoryFabric
from .storage import StateConflict, Store
from .transport import Transport, action_envelope, parse_result


class Runtime:
    def __init__(
        self,
        store: Store,
        grid: Grid,
        verifier: Verifier,
        on_verification: Callable[[Evidence], None] | None = None,
        memory: MemoryFabric | None = None,
        relationship_id: str = "owner",
    ):
        self.store, self.grid, self.verifier = store, grid, verifier
        self.on_verification = on_verification
        self.memory, self.relationship_id = memory, relationship_id
        self.active_context: dict[str, dict[str, Any]] = {}
        self.store.task_resources.add(self)

    def task_transitioned(self, task: Task) -> None:
        if task.state not in {
            TaskState.PLANNED,
            TaskState.EXECUTING,
            TaskState.AWAITING_RESULT,
            TaskState.RESULT_RECEIVED,
            TaskState.VERIFYING,
            TaskState.PARTIALLY_VERIFIED,
        }:
            self.active_context.pop(task.id, None)

    def create(
        self,
        intent: Intent,
        initiator: str = "owner",
        retry_budget: int = 2,
        mode: str = "auto",
        *,
        transient: bool = False,
    ) -> Task:
        if not 0 <= retry_budget <= 5:
            raise ValueError("retry budget must be between zero and five")
        names = (
            tuple(
                row[0]
                for row in self.memory.archive.db.execute(
                    "SELECT alias FROM archive_aliases WHERE relationship=? LIMIT 1000",
                    (self.relationship_id,),
                )
            )
            if self.memory
            else ()
        )
        decision = decide(intent, names)
        recall = (
            self.memory.retrieve(self.relationship_id, intent.text)
            if (self.memory and decision.memory_required)
            else None
        )
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
        private_parameters = parameters
        if transient:
            if len(self.store.transient) >= 100:
                raise StateConflict("transient task bound reached; discard finished interactions")
            self.store.transient[task.id] = {
                "parameters": parameters,
                "objective": objective,
            }
            parameters = {"transient_digest": hashlib.sha256(material.encode()).hexdigest()}
            objective = replace(
                objective,
                description="Private desktop interaction",
                criterion={"kind": "unavailable"},
            )
        with self.store.transaction():
            self.store.put("objective", objective.id, record(objective))
            self.store.put("task", task.id, record(task))
            self.store.put("plan", task.id, {"kind": kind, "parameters": parameters})
            self.store.audit(task.id, "jev_decision", record(decision))
            self.store.audit(
                task.id,
                "memory_preflight",
                {
                    "required": decision.memory_required,
                    "retrieved": recall is not None,
                    "memory_ids": [hit.memory.id for hit in recall.hits] if recall else [],
                    "event_ids": sorted(
                        {event for hit in recall.hits for event in hit.memory.event_ids}
                    )
                    if recall
                    else [],
                    "attempts": list(recall.attempts) if recall else [],
                    "status": Epistemic.RECALLED if recall and recall.hits else Epistemic.UNKNOWN,
                },
            )
        if recall and self.memory:
            while len(self.active_context) >= 100:
                self.active_context.pop(next(iter(self.active_context)))
            self.active_context[task.id] = self.memory.context(
                recall,
                objective=intent.text,
                project=None,
                live={},
                policy_ids=(),
            )
        self.verifier.bind_task(task.id, private_parameters)
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
        if "transient_digest" in plan["parameters"] and task.id not in self.store.transient:
            return self.store.transition(
                task.id,
                TaskState.BLOCKED,
                blocker="private context expired; create a fresh request",
            )
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
            private = self.store.transient.get(task.id)
            persisted = (
                replace(
                    result,
                    value=None,
                    artifact=None,
                    error="private executor failed" if result.error else None,
                )
                if private
                else result
            )
            self.store.put("result", result.id, record(persisted))
            if private and "result" in private:
                result = private["result"]
            if result.artifact and not private:
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
                    blocker=("private executor failed" if private else result.error)
                    or "executor reported failure",
                    expected_lease=lease_id,
                )
            self.store.transition(task.id, TaskState.VERIFYING, expected_lease=lease_id)
            objective = Objective(**self.store.get("objective", task.objective_id))
            if private:
                objective = private["objective"]
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
                and not private
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
            ownership = plan.get("interaction")
            if ownership:
                with self.store.transaction():
                    interaction = self.store.get("interaction_lease", ownership["resource"])
                    if interaction.get("task_id") == task.id:
                        interaction["expires"] = 0
                        self.store.put("interaction_lease", ownership["resource"], interaction)
            # A different Store/process may have completed or cancelled the task.
            for resources in list(self.store.task_resources):
                resources.task_transitioned(current)
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
        self,
        task_id: str,
        transports: Mapping[str, tuple[Transport, SessionHandle]] | None = None,
        *,
        expected_node: str | None = None,
    ) -> Task:
        task = self.store.task(task_id)
        if task.state in {TaskState.VERIFIED, TaskState.FAILED, TaskState.CANCELLED}:
            return task
        task = self.store.transition(task_id, TaskState.CANCELLED, expected_node=expected_node)
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
