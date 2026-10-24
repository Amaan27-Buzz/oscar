"""Reviewed data handoffs; result text never becomes a capability or authority."""

import json
from copy import deepcopy
from typing import Any

from .contracts import TaskState
from .credentials import redact_runtime_secrets
from .storage import StateConflict, Store


def validate_inputs(step: dict[str, Any]) -> None:
    bindings = step.get("inputs", [])
    if not isinstance(bindings, list) or len(bindings) > 8:
        raise ValueError("at most eight explicit result handoffs per step")
    destinations = []
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"from_step", "select", "to"}:
            raise ValueError("exact result handoff required")
        source, selection, destination = (binding[k] for k in ("from_step", "select", "to"))
        if not isinstance(source, str) or source not in step["depends_on"]:
            raise ValueError("result handoff requires a direct earlier dependency")
        for path in (selection, destination):
            if (
                not isinstance(path, list)
                or len(path) > 8
                or any(
                    not (
                        isinstance(p, str) and 1 <= len(p) <= 80 or type(p) is int and 0 <= p < 100
                    )
                    for p in path
                )
            ):
                raise ValueError("bounded typed result path required")
        # Identities, destinations, commands and verification types stay literal.
        if not (
            destination == ["content"]
            and step["intent"].get("kind") == "file_write"
            or len(destination) >= 2
            and destination[0] in {"parameters", "criterion"}
            and destination[-1] in {"content", "text", "body", "message"}
        ):
            raise ValueError("result handoffs may replace only reviewed data text fields")
        if destination in destinations or not isinstance(at(step["intent"], destination), str):
            raise ValueError("unique existing string destination required")
        destinations.append(destination)


def at(value: Any, path: list[Any]) -> Any:
    for part in path:
        if isinstance(value, dict) and isinstance(part, str) and part in value:
            value = value[part]
        elif isinstance(value, list) and type(part) is int and 0 <= part < len(value):
            value = value[part]
        else:
            raise ValueError("result handoff path does not exist")
    return value


def verified_result(store: Store, task_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    task = store.task(task_id)
    action = store.get("planned_action", task_id)
    results = [
        r
        for r in store.all("result")
        if r["task_id"] == task_id
        and r["action_id"] == action["id"]
        and r["correlation_id"] == task.correlation_id
        and r["success"] is True
    ]
    evidence = [
        e
        for e in store.all("evidence")
        if e["task_id"] == task_id
        and e["correlation_id"] == task.correlation_id
        and e["matches"] is True
        and e["status"] == "VERIFIED"
    ]
    if (
        task.state != TaskState.VERIFIED
        or task.cancelled
        or len(results) != 1
        or len(evidence) != 1
    ):
        raise StateConflict("one independently verified result is required for handoff")
    return results[0], evidence[0]


def resolve_inputs(
    store: Store, goal: dict[str, Any], step: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    from .executive import digest

    intent = deepcopy(step["intent"])
    provenance = []
    for binding in step.get("inputs", []):
        matches = [
            r
            for r in store.all("executive_task")
            if r["goal_id"] == goal["id"]
            and r["occurrence"] == goal["run_index"]
            and r["relationship"] == goal["relationship"]
            and r["step_id"] == binding["from_step"]
        ]
        if len(matches) != 1:
            raise StateConflict("exact same-occurrence result is required")
        task_id = matches[0]["task_id"]
        result, evidence = verified_result(store, task_id)
        value = result["value"]
        if not isinstance(value, str) or len(value.encode("utf-8")) > 32768:
            raise ValueError("bounded exported result text required")
        if binding["select"]:
            value = at(json.loads(value), binding["select"])
        if type(value) in {int, bool}:
            value = json.dumps(value)
        if not isinstance(value, str) or len(value.encode("utf-8")) > 4096:
            raise ValueError("bounded scalar result text required")
        if redact_runtime_secrets(value) != value:
            raise ValueError("credential material cannot enter result handoffs")
        destination = binding["to"]
        at(intent, destination[:-1])[destination[-1]] = value
        provenance.append(
            {
                "task_id": task_id,
                "result_id": result["id"],
                "result_digest": digest(result),
                "evidence_id": evidence["id"],
                "evidence_digest": digest(evidence),
            }
        )
    return intent, provenance


def check_inputs(store: Store, binding: dict[str, Any]) -> None:
    from .executive import digest

    for pin in binding.get("inputs", []):
        try:
            result, evidence = verified_result(store, pin["task_id"])
        except (KeyError, StateConflict):
            raise PermissionError("reviewed result handoff unavailable") from None
        source = store.get("executive_task", pin["task_id"])
        if (
            any(source[k] != binding[k] for k in ("goal_id", "relationship", "occurrence"))
            or result["id"] != pin["result_id"]
            or digest(result) != pin["result_digest"]
            or evidence["id"] != pin["evidence_id"]
            or digest(evidence) != pin["evidence_digest"]
        ):
            raise PermissionError("reviewed result handoff changed")
