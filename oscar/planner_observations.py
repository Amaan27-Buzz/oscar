"""Bounded verified tool observations for private, authority-checked replanning."""

import json
from typing import Any

from .contracts import record
from .credentials import redact_runtime_secrets
from .executive import digest
from .executive_inputs import verified_result
from .grid import Grid
from .policy import PersonalPolicy
from .storage import StateConflict, Store


def validate_stage(steps: list[dict[str, Any]]) -> None:
    if not 1 <= len(steps) <= 4:
        raise ValueError("one to four read-only observations per stage")
    for step in steps:
        intent = step["intent"]
        if step.get("inputs") or not (
            step["capability_id"] == "machine.files.read"
            and intent.get("kind") == "capability"
            and intent.get("capability_kind") == "file_read"
            and isinstance(intent.get("parameters"), dict)
            and set(intent["parameters"]) == {"path"}
            or step["capability_id"] == "math.add"
            and intent.get("kind") is None
            or step["capability_id"] == "machine.apps"
            and intent.get("kind") == "capability"
            and intent.get("capability_kind") == "installed_app"
            and isinstance(intent.get("parameters"), dict)
            and set(intent["parameters"]) == {"request"}
            and isinstance(intent["parameters"]["request"], dict)
            and set(intent["parameters"]["request"]) == {"operation", "query"}
            and intent["parameters"]["request"]["operation"] == "targets"
            and isinstance(intent["parameters"]["request"]["query"], str)
            and len(intent["parameters"]["request"]["query"]) <= 80
            and "\x00" not in intent["parameters"]["request"]["query"]
        ):
            raise PermissionError("observation stages cannot contain effects or model calls")


def references(store: Store, row: dict[str, Any]) -> dict[str, Any]:
    goal = store.get("executive_goal", row["observation_goal"])
    if goal["state"] != "completed":
        raise StateConflict("verified observations are still pending")
    validate_stage(goal["steps"])
    tasks = [
        r
        for r in store.all("executive_task")
        if r["goal_id"] == goal["id"]
        and r["occurrence"] == 0
        and r["relationship"] == row["relationship"]
    ]
    if len(tasks) != len(goal["steps"]):
        raise StateConflict("one exact result per observation required")
    pins = []
    for step in goal["steps"]:
        matches = [r for r in tasks if r["step_id"] == step["id"]]
        if len(matches) != 1:
            raise StateConflict("unique observation step required")
        result, evidence = verified_result(store, matches[0]["task_id"])
        pins.append(
            {
                "task_id": result["task_id"],
                "result_id": result["id"],
                "result_digest": digest(result),
                "evidence_id": evidence["id"],
                "evidence_digest": digest(evidence),
            }
        )
    return {"request_id": row["id"], "goal_id": goal["id"], "pins": pins}


def context(store: Store, grid: Grid, refs: dict[str, Any], *, task_id: str | None = None) -> str:
    if not isinstance(refs, dict) or set(refs) != {"request_id", "goal_id", "pins"}:
        raise PermissionError("exact observation provenance required")
    row = store.get("planner_request", refs["request_id"])
    if not row.get("adaptive") or row.get("autonomy_blocked"):
        raise PermissionError("adaptive observation disclosure unavailable")
    stage = row.get("observation_stages", {}).get(refs["goal_id"])
    if not stage:
        raise PermissionError("reviewed observation stage required")
    row = {**row, **stage}
    if row.get("observation_expires", 0) <= grid.clock():
        raise PermissionError("observations expired; request a fresh observation stage")
    # The last observation remains bound after its continuation draft replaces goal_id.
    if row.get("observation_goal") != refs["goal_id"] or references(store, row) != refs:
        raise PermissionError("observation provenance changed")
    goal = store.get("executive_goal", refs["goal_id"])
    owner = store.get("executive_owner", goal["id"])
    if task_id is not None:
        binding = store.get("plan", task_id).get("executive")
        if not binding or binding["relationship"] != row["relationship"]:
            raise PermissionError("observations require their reviewed Executive continuation")
        destination = store.get("executive_goal", binding["goal_id"])
        destination_owner = store.get("executive_owner", destination["id"])
        if destination.get("observations") != refs or any(
            destination_owner.get(k) != owner.get(k)
            for k in ("node", "session", "scope", "public_key", "standing")
        ):
            raise PermissionError("observation continuation owner or references changed")
    session = store.get("session", owner["session"])
    node = store.get("node", owner["node"])
    if session["revoked"] or node["revoked"] or session["expires_at"] <= grid.clock():
        raise PermissionError("observation owner unavailable")
    from .authority import StandingAuthority

    authority = StandingAuthority(store, grid, row["relationship"])
    if (
        authority._owner(
            owner["node"], owner["session"], owner["scope"], frozenset({owner["scope"]})
        )
        != owner["public_key"]
    ):
        raise PermissionError("observation owner changed")
    if owner.get("standing"):
        current = authority._active()
        if (
            current["mode"] != "full"
            or {k: current[k] for k in ("grant_id", "epoch")} != owner["standing"]
        ):
            raise PermissionError("observation delegation changed")
    grants = frozenset(session["scopes"]) & frozenset(node["scopes"])
    values = []
    for step, pin in zip(goal["steps"], refs["pins"], strict=True):
        matches = [
            c
            for c in row["observation_contracts"]
            if c["node_id"] == step["node_id"] and c["id"] == step["capability_id"]
        ]
        if len(matches) != 1:
            raise PermissionError("exact observation contract required")
        expected = matches[0]
        capabilities = [
            c
            for c in grid.search(expected["input_kind"])
            if c.node_id == step["node_id"] and c.id == step["capability_id"]
        ]
        if len(capabilities) != 1 or digest(record(capabilities[0])) != digest(expected):
            raise PermissionError("observation capability unavailable or changed")
        cap = capabilities[0]
        target = store.get("node", cap.node_id)
        execution = target.get("executor_session")
        if execution is None:
            execution = store.get("core_execution", cap.node_id)["session_id"]
        executor = store.get("session", execution)
        executor_grants = frozenset(executor["scopes"]) & frozenset(target["scopes"])
        if (
            executor["revoked"]
            or executor["expires_at"] <= grid.clock()
            or not set(cap.permissions) <= executor_grants
        ):
            raise PermissionError("observation executor authority changed")
        for identifier in (cap.id, *cap.permissions):
            if (
                not PersonalPolicy(store)
                .evaluate(
                    identifier,
                    cap.permissions,
                    grants,
                    {"node": owner["node"], "target": cap.node_id},
                    confirmed=True,
                )
                .allowed
            ):
                raise PermissionError("observation disclosure denied by current policy")
            if (
                not PersonalPolicy(store)
                .evaluate(
                    identifier,
                    cap.permissions,
                    executor_grants,
                    {"node": cap.node_id},
                    confirmed=True,
                )
                .allowed
            ):
                raise PermissionError("observation executor denied by current policy")
        result, evidence = verified_result(store, pin["task_id"])
        value = result["value"]
        if not isinstance(value, str) or len(value.encode()) > 4096:
            raise ValueError("observation exceeds bounded text disclosure")
        if redact_runtime_secrets(value) != value:
            raise PermissionError("credential material cannot enter model observations")
        values.append(
            {
                "step_id": step["id"],
                "task_id": pin["task_id"],
                "evidence_id": evidence["id"],
                "value": value,
            }
        )
    text = json.dumps(values)
    if len(text.encode()) > 16384:
        raise ValueError("observation context exceeds disclosure bound")
    return text
