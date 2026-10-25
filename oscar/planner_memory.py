"""Private planning recall keeps only canonical source references in durable plans."""

import json
from typing import Any

from .contracts import record
from .credentials import redact_runtime_secrets
from .executive import digest
from .grid import Grid
from .memory_executor import recall_context
from .memory_fabric import MemoryFabric
from .policy import PersonalPolicy
from .storage import Store


def retrieve(memory: MemoryFabric, relationship: str, query: str) -> tuple[dict[str, Any], str]:
    context = recall_context(memory, relationship, query)
    values = [
        {k: item[k] for k in ("memory_id", "event_ids", "content", "status", "source_status")}
        for item in context["memories"]
    ]
    if not values:
        raise PermissionError("UNKNOWN: no supported historical evidence for this objective")
    text = json.dumps(values, sort_keys=True)
    if len(text.encode()) > 8192 or redact_runtime_secrets(text) != text:
        raise PermissionError("planning recall exceeds private disclosure bounds")
    sources = sorted({event for value in values for event in value["event_ids"]})
    return {
        "relationship": relationship,
        "query": query,
        "digest": digest(values),
        "event_ids": sources,
        "source_digest": digest([record(memory.archive.event(e)) for e in sources]),
    }, text


def context(
    store: Store, grid: Grid, memory: MemoryFabric | None, refs: dict[str, Any], task_id: str
) -> str:
    if memory is None:
        raise PermissionError("authoritative planning memory unavailable")
    binding = store.get("plan", task_id)["executive"]
    goal = store.get("executive_goal", binding["goal_id"])
    if goal.get("memory_refs") != refs or refs["relationship"] != binding["relationship"]:
        raise PermissionError("planning memory owner or references changed")
    owner = store.get("executive_owner", goal["id"])
    worker = store.get("executive_worker", binding["worker_id"])
    capabilities = [
        c
        for c in grid.search("memory")
        if c.id == "memory.recall"
        and {"node_id": c.node_id, "capability_id": c.id, "contract": digest(record(c))}
        in worker["capabilities"]
    ]
    if len(capabilities) != 1:
        raise PermissionError("reviewed memory capability unavailable or changed")
    target = store.get("node", capabilities[0].node_id)
    execution = store.get("core_execution", target["id"])["session_id"]
    executor = store.get("session", execution)
    if (
        executor["revoked"]
        or executor["expires_at"] <= grid.clock()
        or "memory:read" not in (set(executor["scopes"]) & set(target["scopes"]))
    ):
        raise PermissionError("planning memory executor authority withdrawn")
    session, node = store.get("session", owner["session"]), store.get("node", owner["node"])
    if session["revoked"] or node["revoked"] or session["expires_at"] <= grid.clock():
        raise PermissionError("planning recall owner unavailable")
    grants = frozenset(session["scopes"]) & frozenset(node["scopes"])
    for identifier in ("memory.read", "memory.recall", "memory:read"):
        for allowed, scope in (
            (grants, {"node": owner["node"], "source": "executive"}),
            (frozenset(executor["scopes"]) & frozenset(target["scopes"]), {"node": target["id"]}),
        ):
            if (
                not PersonalPolicy(store)
                .evaluate(
                    identifier,
                    ("memory:read",),
                    allowed,
                    {**scope, "relationship": binding["relationship"]},
                )
                .allowed
            ):
                raise PermissionError("planning recall permission or policy withdrawn")
    current, text = retrieve(memory, refs["relationship"], refs["query"])
    if current != refs:
        raise PermissionError("planning memory changed; retrieve and review again")
    return text
