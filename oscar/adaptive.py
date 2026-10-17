"""Bounded trusted presentation primitives. No scripts, arbitrary layouts or execution claims."""

import json
from typing import Any

from .credentials import redact_runtime_secrets

COMPONENTS = frozenset({"prose", "task_progress", "result_evidence"})


def validate_view(value: dict[str, Any]) -> dict[str, Any]:
    if (
        set(value)
        != {
            "version",
            "view_id",
            "task_id",
            "revision",
            "observed_at_ms",
            "expires_at_ms",
            "fallback",
            "components",
            "actions",
        }
        or value["version"] != 1
        or type(value["version"]) is not int
    ):
        raise ValueError("unsupported adaptive envelope")
    material = json.dumps(value, allow_nan=False)
    if len(material) > 8192 or redact_runtime_secrets(material) != material:
        raise ValueError("bounded non-secret descriptor required")
    for key in ("view_id", "task_id", "fallback"):
        if not isinstance(value[key], str) or not 1 <= len(value[key]) <= (
            512 if key == "fallback" else 80
        ):
            raise ValueError("bounded adaptive identity/fallback required")
    for key in ("revision", "observed_at_ms", "expires_at_ms"):
        if type(value[key]) is not int or not 0 <= value[key] <= 2**53 - 1:
            raise ValueError("invalid adaptive revision/time")
    if not 0 < value["expires_at_ms"] - value["observed_at_ms"] <= 30_000:
        raise ValueError("bounded view lease required")
    if not isinstance(value["components"], list) or not 1 <= len(value["components"]) <= 8:
        raise ValueError("bounded components required")
    for component in value["components"]:
        if (
            not isinstance(component, dict)
            or set(component) != {"type", "text", "source_ids"}
            or component["type"] not in COMPONENTS
            or not isinstance(component["text"], str)
            or not 1 <= len(component["text"]) <= 1024
        ):
            raise ValueError("untrusted component rejected")
        refs = component["source_ids"]
        if (
            not isinstance(refs, list)
            or len(refs) > 20
            or any(not isinstance(r, str) or not 1 <= len(r) <= 80 for r in refs)
        ):
            raise ValueError("bounded evidence references required")
    if value["actions"] != [{"type": "inspect_task", "task_id": value["task_id"]}]:
        raise ValueError("only a typed Core inspection intention is supported")
    return value


def task_view(task: dict[str, Any], now: int, supported: list[str]) -> dict[str, Any]:
    if (
        not isinstance(supported, list)
        or len(supported) > 8
        or any(type(c) is not str for c in supported)
    ):
        raise ValueError("bounded component negotiation required")
    state = task["state"]
    label = "Verified outcome" if state == "verified" else "Task state: " + state
    kind = "result_evidence" if state == "verified" else "task_progress"
    kind = kind if kind in supported else "prose"
    refs = task.get("evidence_ids", [])[:20]
    return validate_view(
        {
            "version": 1,
            "view_id": "task-" + task["task_id"],
            "task_id": task["task_id"],
            "revision": task["generation"],
            "observed_at_ms": now,
            "expires_at_ms": now + 30_000,
            "fallback": label,
            "components": [{"type": kind, "text": label, "source_ids": refs}],
            "actions": [{"type": "inspect_task", "task_id": task["task_id"]}],
        }
    )
