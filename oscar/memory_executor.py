"""Read-only sourced recall capability; Core rechecks provenance before presentation."""

from typing import TYPE_CHECKING, Any

from .capabilities import Cancellation
from .contracts import Action, Result, new_id
from .memory_fabric import MemoryFabric

if TYPE_CHECKING:
    from .runtime import Runtime


def authorize_recall(runtime: "Runtime", task_id: str, viewer_session: str | None = None) -> None:
    store = runtime.store
    try:
        row = store.get("remote_task", task_id)
        node_id, session_id, source = row["requester"], row["requester_session"], "remote-grid"
        binding = store.get("remote_device", node_id)
        if binding["session_id"] != session_id or binding["owner_id"] != runtime.relationship_id:
            raise PermissionError("recall device binding withdrawn")
    except KeyError:
        row = store.get("desktop_task", task_id)
        association = store.get("sunday_task", task_id)
        node_id, session_id, source = association["node_id"], row["session_id"], "desktop"
    session, node = store.get("session", session_id), store.get("node", node_id)
    if (
        viewer_session is not None
        and viewer_session != session_id
        or session["node_id"] != node_id
        or session["revoked"]
        or node["revoked"]
        or session["expires_at"] <= runtime.grid.clock()
    ):
        raise PermissionError("recall session unavailable")
    from .policy import PersonalPolicy

    grants = frozenset(session["scopes"]) & frozenset(node["scopes"])
    if (
        not PersonalPolicy(store)
        .evaluate(
            "memory.read",
            ("memory:read",),
            grants,
            {"node": node_id, "source": source, "relationship": runtime.relationship_id},
        )
        .allowed
    ):
        raise PermissionError("recall read grant or policy withdrawn")


def recall_context(memory: MemoryFabric, relationship: str, query: str) -> dict[str, Any]:
    evidence = memory.retrieve(relationship, query)
    context = memory.context(
        evidence, objective=query, project=None, live={}, policy_ids=(), max_chars=8192
    )
    context["memories"] = [item for item in context["memories"] if item["content"] != query]
    while len({event for item in context["memories"] for event in item["event_ids"]}) > 32:
        context["memories"].pop()
    return context


def recall_text(context: dict[str, Any]) -> str:
    return "\n\n".join(item["content"] for item in context["memories"])


class MemoryExecutor:
    def __init__(self, memory: MemoryFabric, relationship: str, runtime: "Runtime | None" = None):
        self.memory, self.relationship = memory, relationship
        self.runtime = runtime

    def __call__(self, action: Action, cancellation: Cancellation) -> Result:
        if set(action.parameters) != {"query"} or not isinstance(action.parameters["query"], str):
            raise ValueError("bounded recall query required")
        query = action.parameters["query"]
        if not 0 < len(query) <= 4096:
            raise ValueError("bounded recall query required")
        cancellation.check()
        if self.runtime is not None:
            authorize_recall(self.runtime, action.task_id)
        context = recall_context(self.memory, self.relationship, query)
        text = recall_text(context)
        cancellation.check()
        if self.runtime is not None:
            authorize_recall(self.runtime, action.task_id)
        return Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            bool(text),
            value=text or None,
            error=None if text else "freshness_unavailable: no supported historical evidence",
        )
