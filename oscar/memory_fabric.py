"""Bounded multi-path recall, context assembly and evidence-bound claim checking."""

import json
import re
from dataclasses import dataclass
from time import time
from typing import Any

from .contracts import Epistemic
from .event_archive import EventArchive, MemoryRecord
from .memory_indexes import DerivedIndex, Reranker, digest


@dataclass(frozen=True)
class RecallHit:
    memory: MemoryRecord
    paths: tuple[str, ...]
    score: float
    rerank_score: float | None
    status: Epistemic = Epistemic.RECALLED


@dataclass(frozen=True)
class RecallSet:
    hits: tuple[RecallHit, ...]
    attempts: tuple[str, ...]
    unavailable: tuple[str, ...]
    ambiguous_entities: tuple[str, ...] = ()


@dataclass(frozen=True)
class HistoricalClaim:
    text: str
    event_ids: tuple[str, ...]
    memory_ids: tuple[str, ...]
    status: Epistemic
    confidence: float


def memory_preflight(text: str, known_names: tuple[str, ...] = ()) -> bool:
    """Conservative cheap preflight. Positive means retrieval before a personal claim."""
    normalized = " ".join(text.casefold().split())
    if re.fullmatch(r"(?:what is )?\d{1,12}\s*\+\s*\d{1,12}\??", normalized):
        return False
    markers = (
        "recall",
        "remember",
        "earlier",
        "previous",
        "last time",
        "continue",
        "same as before",
        "that project",
        "that task",
        "decide",
        "decision",
        "preference",
        "usual",
        "correction",
        "unfinished",
        "relationship",
        "artifact",
        "my ",
        "our ",
        " i ",
        "we ",
        "person",
        "project",
        "repository",
        "history",
        "before",
        "preferred",
        "habit",
        "said",
    )
    return any(marker in " " + normalized for marker in markers) or any(
        re.search(r"(?<!\w)" + re.escape(name.casefold()) + r"(?!\w)", normalized)
        for name in known_names
        if name
    )


class MemoryFabric:
    def __init__(
        self,
        archive: EventArchive,
        *,
        vector: DerivedIndex | None = None,
        graph: DerivedIndex | None = None,
        reranker: Reranker | None = None,
    ):
        self.archive, self.vector, self.graph, self.reranker = archive, vector, graph, reranker
        self.active: dict[str, tuple[str, ...]] = {}
        self.structured: dict[str, tuple[str, ...]] = {}

    def retrieve(
        self,
        relationship: str,
        query: str,
        *,
        project: str | None = None,
        entity_alias: str | None = None,
        at: float | None = None,
        limit: int = 10,
    ) -> RecallSet:
        if not relationship or not 0 < len(query) <= 4000 or not 1 <= limit <= 20:
            raise ValueError("bounded scoped retrieval required")
        attempts, unavailable = [], []
        entities = self.archive.resolve(relationship, entity_alias) if entity_alias else ()
        if len(entities) > 1:
            return RecallSet((), ("entity-resolution",), (), entities)
        records = self.archive.memories(
            relationship,
            project=project,
            entity=entities[0] if entities else None,
            at=at,
            limit=10_000,
        )
        allowed = {memory.id: memory for memory in records}
        paths: dict[str, list[str]] = {}
        scores: dict[str, float] = {}

        def accept(ids: list[str] | tuple[str, ...], path: str) -> None:
            for rank, identifier in enumerate(ids[:100]):
                if identifier in allowed:
                    paths.setdefault(identifier, []).append(path)
                    scores[identifier] = scores.get(identifier, 0) + 1 / (60 + rank)

        for name, context in (("0-active", self.active), ("1-structured", self.structured)):
            attempts.append(name)
            accept(context.get(relationship, ()), name)
        attempts.append("2-archive-fts")
        accept(self.archive.fts(relationship, query, limit=100), "archive-fts")
        for name, index in (("3-qdrant-hybrid", self.vector), ("4-graphiti-temporal", self.graph)):
            attempts.append(name)
            if index is None:
                unavailable.append(name)
                continue
            try:
                accept(index.query(query, relationship, limit=50), name)
            except Exception:
                # Provider failure is explicit; archive candidates still undergo provenance checks.
                unavailable.append(name)
        attempts.append("5-query-expansion")
        expansions = [query]
        if entity_alias:
            expansions.append(entity_alias)
        if project:
            expansions.append(project)
        tokens = re.findall(r"\w+", query)
        expansions.extend(token for token in tokens if len(token) > 3)
        for expanded in expansions[:8]:
            accept(self.archive.fts(relationship, expanded, limit=20), "expanded-archive")
        attempts.append("6-bounded-archive")
        query_tokens = set(re.findall(r"\w+", query.casefold())) - {
            "what",
            "which",
            "did",
            "was",
            "the",
            "you",
            "and",
            "that",
            "with",
            "remember",
            "recall",
            "before",
            "have",
            "said",
            "about",
            "does",
            "were",
            "when",
            "from",
        }
        # Deep reconstruction generates candidates, never an unsupported answer.
        accept(
            [
                memory.id
                for memory in records
                if query_tokens & set(re.findall(r"\w+", memory.content.casefold()))
            ][:100],
            "deep-archive",
        )
        ordered = sorted(paths, key=lambda identifier: scores[identifier], reverse=True)[:100]
        ranking: dict[str, float] = {}
        if self.reranker and ordered:
            try:
                values = self.reranker.rank(
                    query, [allowed[identifier].content for identifier in ordered]
                )
                ranking = dict(zip(ordered, values, strict=True))
                ordered.sort(key=lambda identifier: ranking[identifier], reverse=True)
            except Exception:
                unavailable.append("reranker")
        hits = tuple(
            RecallHit(
                allowed[identifier],
                tuple(paths[identifier]),
                scores[identifier],
                ranking.get(identifier),
            )
            for identifier in ordered[:limit]
        )
        if not hits:
            attempts.append("7-UNKNOWN")
        return RecallSet(hits, tuple(attempts), tuple(unavailable))

    def check_claim(self, claim: HistoricalClaim, evidence: RecallSet) -> Epistemic:
        if not 0 <= claim.confidence <= 1 or claim.status not in {
            Epistemic.RECALLED,
            Epistemic.INFERRED,
        }:
            return Epistemic.UNKNOWN
        support = [hit.memory for hit in evidence.hits if hit.memory.id in claim.memory_ids]
        if not support or set(claim.memory_ids) != {memory.id for memory in support}:
            return Epistemic.UNKNOWN
        source_states = []
        # Evidence captured before forget/expiry is no longer admissible.
        for memory in support:
            row = self.archive.db.execute(
                "SELECT forgotten FROM archive_memories WHERE id=?", (memory.id,)
            ).fetchone()
            if not row or row[0] or memory.expires_at is not None and memory.expires_at <= time():
                return Epistemic.UNKNOWN
            try:
                for identifier in memory.event_ids:
                    source_states.append(self.archive.event(identifier).status)
            except KeyError:
                return Epistemic.UNKNOWN
        events = {identifier for memory in support for identifier in memory.event_ids}
        if not claim.event_ids or not set(claim.event_ids) <= events:
            return Epistemic.UNKNOWN
        # This verifier proves exact sourced assertions only, not arbitrary model entailment.
        if not any(claim.text == memory.content for memory in support):
            return Epistemic.UNKNOWN
        if Epistemic.UNKNOWN in source_states or any(
            memory.status == Epistemic.UNKNOWN for memory in support
        ):
            return Epistemic.UNKNOWN
        if Epistemic.INFERRED in source_states or any(
            memory.status == Epistemic.INFERRED for memory in support
        ):
            return Epistemic.INFERRED
        return Epistemic.RECALLED

    def context(
        self,
        evidence: RecallSet,
        *,
        objective: str,
        project: str | None,
        live: dict[str, Any],
        policy_ids: tuple[str, ...],
        max_chars: int = 12_000,
    ) -> dict[str, Any]:
        if not 1000 <= max_chars <= 32_000:
            raise ValueError("bounded context required")
        selected: list[dict[str, Any]] = []
        context = {
            "objective": objective,
            "project": project,
            "memories": selected,
            "live": live,
            "policy_ids": policy_ids,
            "assembled_at": time(),
        }
        if len(json.dumps(context)) > max_chars:
            raise ValueError("objective/live/policy context exceeds bound")
        for hit in evidence.hits:
            state = self.check_claim(
                HistoricalClaim(
                    hit.memory.content,
                    hit.memory.event_ids,
                    (hit.memory.id,),
                    Epistemic.RECALLED,
                    1,
                ),
                evidence,
            )
            if state == Epistemic.UNKNOWN:
                continue
            selected.append(
                {
                    "memory_id": hit.memory.id,
                    "event_ids": hit.memory.event_ids,
                    "content": hit.memory.content,
                    "status": state,
                    "source_status": hit.memory.status,
                    "valid_from": hit.memory.valid_from,
                    "valid_to": hit.memory.valid_to,
                }
            )
            if len(json.dumps(context)) > max_chars:
                selected.pop()
        return context

    def rebuild(self, relationship: str) -> tuple[str, ...]:
        records = self.archive.memories(relationship, include_history=True, limit=10_000)
        failed = []
        for index in (self.vector, self.graph):
            if index is None:
                continue
            try:
                index.rebuild(records)
                with self.archive.db:
                    self.archive.db.execute(
                        "INSERT OR REPLACE INTO archive_metadata VALUES(?,?)",
                        (index.identity + ":generation", digest(records)),
                    )
            except Exception:
                failed.append(index.identity)
                with self.archive.db:
                    self.archive.db.execute(
                        "DELETE FROM archive_metadata WHERE key=?",
                        (index.identity + ":generation",),
                    )
        return tuple(failed)

    def forget(
        self, memory_id: str, *, owner_authorized: bool, forget_sources: bool = False
    ) -> tuple[str, ...]:
        self.archive.forget(
            memory_id, owner_authorized=owner_authorized, forget_sources=forget_sources
        )
        identifiers = [
            row[0] for row in self.archive.db.execute("SELECT id FROM archive_tombstones")
        ]
        failed = []
        for index in (self.vector, self.graph):
            if index is None:
                continue
            try:
                index.forget(identifiers)
            except Exception:
                failed.append(index.identity)
        # Canonical admission filter also fences stale/deletion-failed derived results.
        return tuple(failed)
