"""Read-only sourced recall capability; Core rechecks provenance before presentation."""

from typing import Any

from .capabilities import Cancellation
from .contracts import Action, Result, new_id
from .memory_fabric import MemoryFabric


def recall_text(context: dict[str, Any]) -> str:
    return "\n\n".join(item["content"] for item in context["memories"])


class MemoryExecutor:
    def __init__(self, memory: MemoryFabric, relationship: str):
        self.memory, self.relationship = memory, relationship

    def __call__(self, action: Action, cancellation: Cancellation) -> Result:
        if set(action.parameters) != {"query"} or not isinstance(action.parameters["query"], str):
            raise ValueError("bounded recall query required")
        query = action.parameters["query"]
        if not 0 < len(query) <= 4096:
            raise ValueError("bounded recall query required")
        cancellation.check()
        evidence = self.memory.retrieve(self.relationship, query)
        context = self.memory.context(
            evidence, objective=query, project=None, live={}, policy_ids=(), max_chars=8192
        )
        text = recall_text(context)
        cancellation.check()
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
