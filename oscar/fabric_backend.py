"""Production Memory Fabric retrieval behind the existing live-context backend boundary."""

from .continuity import MemoryItem, MemoryType
from .contracts import Epistemic
from .freshness import Authority, SourceRef
from .memory_fabric import MemoryFabric


class FabricBackend:
    def __init__(self, fabric: MemoryFabric, relationship: str):
        self.fabric, self.relationship = fabric, relationship

    def retain(self, item: MemoryItem, *, retention_authorized: bool) -> None:
        raise PermissionError("retain canonical source events through Memory Writer")

    def retrieve(self, query: str, scope: str, limit: int = 8) -> tuple[MemoryItem, ...]:
        evidence = self.fabric.retrieve(self.relationship, query, project=scope, limit=limit)
        return tuple(
            MemoryItem(
                memory.id,
                memory.context_key,
                memory.content,
                scope,
                MemoryType.PROJECT,
                SourceRef(
                    "archive://" + memory.event_ids[0], Authority.CACHE, "local", memory.valid_from
                ),
                memory.valid_from,
                evidence_state=Epistemic.INFERRED
                if memory.status == Epistemic.INFERRED
                else Epistemic.RECALLED,
                expires_at=memory.expires_at,
                entity_refs=memory.entity_ids,
                retention_reason="source-authorized selected event",
            )
            for hit in evidence.hits
            if (memory := hit.memory).context_key and len(memory.content.encode()) <= 16_000
        )

    def forget(self, identifier: str, *, owner_authorized: bool) -> None:
        self.fabric.forget(identifier, owner_authorized=owner_authorized, forget_sources=True)
