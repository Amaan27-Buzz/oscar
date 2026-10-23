"""Bounded native owner controls over the canonical Memory Fabric."""

import json
from dataclasses import asdict
from time import time
from typing import TYPE_CHECKING, Any

from .contracts import Epistemic
from .event_archive import MemoryRecord, MemoryWriter, SourceEvent
from .mobile import fingerprint
from .policy import PersonalPolicy

if TYPE_CHECKING:
    from .harness import Harness


class MemoryManagement:
    def __init__(self, harness: "Harness", node: str | None = None):
        self.h = harness
        self.fabric = harness.runtime.memory
        self.relationship = harness.runtime.relationship_id
        self.node = node

    def context(self, grants: frozenset[str]) -> dict[str, str]:
        return {
            "relationship": self.relationship,
            "source": "remote-grid" if "grid:connect" in grants else "desktop",
            **({"node": self.node} if self.node else {}),
        }

    def permitted(self, grants: frozenset[str], *, manage: bool = False) -> bool:
        policy = PersonalPolicy(self.h.store)
        context = self.context(grants)
        return (
            self.fabric is not None
            and policy.evaluate("memory.read", ("memory:read",), grants, context).allowed
            and (
                not manage
                or policy.evaluate(
                    "memory.manage", ("memory:manage",), grants, context, confirmed=True
                ).allowed
            )
        )

    def snapshot(self, grants: frozenset[str]) -> dict[str, Any]:
        for identifier, data in self.h.store.db.execute(
            "SELECT id,data FROM records WHERE kind='assistance_review'"
        ).fetchall():
            review = json.loads(data)
            if (
                review.get("memory_relationship") == self.relationship
                and review.get("expires_at_ms", 0) <= self.h.grid.clock() * 1000
            ):
                self.h.store.put("assistance_review", identifier, {"used": True})
        result: dict[str, Any] = {"available": False, "records": [], "truncated": False}
        if not self.permitted(grants):
            return result
        assert self.fabric is not None
        archive = self.fabric.archive
        result |= {"available": True, "generation": archive.generation(self.relationship)}
        for memory in archive.memories(self.relationship, limit=21):
            item = {
                "id": memory.id,
                "content": memory.content[:2000],
                "excerpt": len(memory.content) > 2000,
                "kind": memory.kind,
                "status": memory.status,
                "source_event_ids": list(memory.event_ids),
                "digest": fingerprint(asdict(memory)),
                "can_manage": self.permitted(grants, manage=True),
                "can_correct": self.permitted(grants, manage=True)
                and self.retention_scope(memory, grants) is not None,
            }
            if (
                len(result["records"]) == 20
                or len(json.dumps(result | {"next": item}).encode()) > 12000
            ):
                result["truncated"] = True
                break
            result["records"].append(item)
        if archive.generation(self.relationship) != result["generation"]:
            return {"available": False, "records": [], "truncated": False}
        return result

    def memory(self, identifier: str) -> MemoryRecord:
        if self.fabric is None:
            raise PermissionError("canonical memory unavailable")
        row = self.fabric.archive.db.execute(
            "SELECT payload FROM archive_memories WHERE id=? AND relationship=? AND forgotten=0",
            (identifier, self.relationship),
        ).fetchone()
        if not row:
            raise PermissionError("memory is unavailable in this relationship")
        data = json.loads(row[0])
        memory = MemoryRecord(
            **{
                **data,
                "event_ids": tuple(data["event_ids"]),
                "entity_ids": tuple(data["entity_ids"]),
                "status": Epistemic(data["status"]),
            }
        )
        if (
            memory.valid_to is not None
            or memory.expires_at is not None
            and memory.expires_at <= time()
        ):
            raise PermissionError("current unexpired memory required")
        for identifier in memory.event_ids:
            if self.fabric.archive.event(identifier).relationship_id != self.relationship:
                raise PermissionError("memory provenance belongs to another relationship")
        return memory

    def retention_scope(self, memory: MemoryRecord, grants: frozenset[str]) -> str | None:
        assert self.fabric is not None
        kinds = {self.fabric.archive.event(i).kind for i in memory.event_ids}
        scopes = ["retain"]
        if kinds <= {"conversation_owner", "conversation_oscar"}:
            scopes.append("desktop:conversation:retain")
        if all(
            self.fabric.archive.event(i).source.startswith("remote-grid:") for i in memory.event_ids
        ):
            scopes.append("archive:retain")
        return next(
            (
                scope
                for scope in scopes
                if PersonalPolicy(self.h.store)
                .evaluate(
                    "memory.retain",
                    (scope,),
                    grants,
                    self.context(grants),
                    confirmed=True,
                )
                .allowed
                and PersonalPolicy(self.h.store)
                .evaluate(
                    {
                        "desktop:conversation:retain": "desktop.conversation.retain",
                        "archive:retain": "core.archive.retain",
                    }.get(scope, "memory.retain"),
                    (scope,),
                    grants,
                    self.context(grants),
                    confirmed=True,
                )
                .allowed
            ),
            None,
        )

    def material(
        self, operation: str, identifier: str, value: dict[str, Any], grants: frozenset[str]
    ) -> dict[str, Any]:
        if not self.permitted(grants, manage=True):
            raise PermissionError("separate canonical memory read and management grants required")
        memory = self.memory(identifier)
        assert self.fabric is not None
        if operation == "memory_forget":
            if (
                set(value) != {"digest", "forget_sources"}
                or type(value["forget_sources"]) is not bool
            ):
                raise ValueError("exact memory and explicit source deletion choice required")
        elif operation == "memory_correct":
            if set(value) != {"digest", "content", "retain"} or value["retain"] is not True:
                raise ValueError("exact correction and explicit retention approval required")
            if not isinstance(value["content"], str) or not 1 <= len(value["content"]) <= 2000:
                raise ValueError("bounded exact replacement statement required")
            self.fabric.archive._safe(value["content"])
            if self.retention_scope(memory, grants) is None:
                raise PermissionError(
                    "correction requires a current source-appropriate retention grant"
                )
        else:
            raise ValueError("unsupported memory operation")
        if value["digest"] != fingerprint(asdict(memory)):
            raise PermissionError("memory content changed; refresh before reviewing")
        if len(memory.content.encode()) > 10000:
            raise ValueError("this memory exceeds the native exact-review bound")
        sources = [asdict(self.fabric.archive.event(i)) for i in memory.event_ids]
        affected = [identifier]
        if operation == "memory_forget" and value["forget_sources"]:
            affected = [
                row[0]
                for row in self.fabric.archive.db.execute(
                    "SELECT id,payload FROM archive_memories WHERE relationship=? AND forgotten=0",
                    (self.relationship,),
                )
                if set(json.loads(row[1])["event_ids"]) & set(memory.event_ids)
            ]
            if len(affected) > 100:
                raise ValueError("source deletion exceeds bounded native review")
        result = {
            "relationship_id": self.relationship,
            "generation": self.fabric.archive.generation(self.relationship),
            "memory": asdict(memory),
            "source_digests": {s["id"]: fingerprint(s) for s in sources},
            "affected_memory_ids": sorted(affected),
            "source_deletion": value.get("forget_sources", False),
            "retention_scope": self.retention_scope(memory, grants)
            if operation == "memory_correct"
            else None,
        }
        return dict(json.loads(json.dumps(result)))

    def complete(
        self,
        operation: str,
        identifier: str,
        value: dict[str, Any],
        expected: dict[str, Any],
        grants: frozenset[str],
    ) -> dict[str, Any]:
        assert self.fabric is not None
        archive = self.fabric.archive
        with archive.transaction():
            # The archive transaction takes SQLite's write lock before this comparison.
            current = self.material(operation, identifier, value, grants)
            if current != expected:
                raise PermissionError("canonical memory changed since the signed review")
            memory = self.memory(identifier)
            if operation == "memory_forget":
                archive.forget(
                    identifier, owner_authorized=True, forget_sources=value["forget_sources"]
                )
            else:
                source = archive.event(memory.event_ids[0])
                correction = SourceEvent(
                    self.relationship,
                    value["content"],
                    "remote-grid:memory-correction"
                    if source.source.startswith("remote-grid:")
                    else "owner:memory-correction",
                    time(),
                    kind="conversation_owner"
                    if source.kind.startswith("conversation_")
                    else "owner_turn"
                    if source.source.startswith("remote-grid:")
                    else "memory_correction",
                    project_id=memory.project_id,
                    entity_ids=memory.entity_ids,
                    status=Epistemic.REPORTED,
                    sensitivity=memory.sensitivity,
                    corrects=source.id,
                    expires_at=memory.expires_at,
                    context_key=memory.context_key,
                )
                archive.append(correction, retain_authorized=True)
                MemoryWriter(archive).retain(
                    (correction.id,),
                    value["content"],
                    memory.kind,
                    retain_authorized=True,
                    inferred=False,
                    project=memory.project_id,
                    entities=memory.entity_ids,
                    supersedes=memory.id,
                )
                if not any(
                    item.supersedes == memory.id and item.content == value["content"]
                    for item in archive.memories(self.relationship)
                ):
                    raise RuntimeError("canonical correction readback failed")
            if operation == "memory_forget":
                for affected in expected["affected_memory_ids"]:
                    row = archive.db.execute(
                        "SELECT forgotten,payload FROM archive_memories WHERE id=?", (affected,)
                    ).fetchone()
                    if (
                        row != (1, "{}")
                        or archive.db.execute(
                            "SELECT 1 FROM archive_fts WHERE memory_id=?", (affected,)
                        ).fetchone()
                    ):
                        raise RuntimeError("canonical forgetting readback failed")
        failed: list[str] = []
        if operation == "memory_forget":
            failed = list(self.fabric.forget_derived())
        self.h.runtime.active_context.clear()
        return {
            "status": "partially_verified" if failed else "verified",
            "failed_indexes": failed,
            "message": "Core memory updated. Derived index deletion remains unverified; "
            "canonical recall excludes forgotten records."
            if failed
            else "Core memory forgotten."
            if operation == "memory_forget"
            else "Core memory corrected; the earlier statement remains historical.",
        }
