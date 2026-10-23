"""Canonical retained history. Derived stores never own events or permission."""

import hashlib
import json
import math
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock, local
from time import time
from typing import Any
from urllib.parse import urlsplit

from .contracts import Epistemic, new_id
from .credentials import redact_runtime_secrets


@dataclass(frozen=True)
class SourceEvent:
    relationship_id: str
    content: str
    source: str
    occurred_at: float
    kind: str = "owner_turn"
    project_id: str | None = None
    entity_ids: tuple[str, ...] = ()
    status: Epistemic = Epistemic.REPORTED
    sensitivity: str = "synthetic"
    retention: str = "selected"
    id: str = field(default_factory=new_id)
    turn_id: str = field(default_factory=new_id)
    episode_id: str = field(default_factory=new_id)
    objective_id: str | None = None
    task_id: str | None = None
    artifact_id: str | None = None
    corrects: str | None = None
    expires_at: float | None = None
    context_key: str | None = None


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    relationship_id: str
    event_ids: tuple[str, ...]
    content: str
    kind: str
    project_id: str | None
    entity_ids: tuple[str, ...]
    status: Epistemic
    valid_from: float
    valid_to: float | None = None
    supersedes: str | None = None
    sensitivity: str = "synthetic"
    expires_at: float | None = None
    context_key: str | None = None


class EventArchive:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._closed = False
        self._thread = local()
        self._connections: set[sqlite3.Connection] = set()
        self._connection_lock = RLock()
        if self.db.execute("PRAGMA user_version").fetchone()[0] not in {0, 1}:
            self.close()
            raise ValueError("unsupported archive schema; explicit migration required")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS archive_events (
                id TEXT PRIMARY KEY, relationship TEXT NOT NULL, payload TEXT NOT NULL,
                forgotten INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS archive_memories (
                id TEXT PRIMARY KEY, relationship TEXT NOT NULL, payload TEXT NOT NULL,
                forgotten INTEGER NOT NULL DEFAULT 0);
            CREATE VIRTUAL TABLE IF NOT EXISTS archive_fts USING fts5(
                memory_id UNINDEXED, relationship UNINDEXED, content);
            CREATE TABLE IF NOT EXISTS archive_entities (
                id TEXT PRIMARY KEY, relationship TEXT NOT NULL, name TEXT NOT NULL,
                kind TEXT NOT NULL, source_event TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS archive_aliases (
                relationship TEXT NOT NULL, alias TEXT NOT NULL, entity_id TEXT NOT NULL,
                source_event TEXT NOT NULL,
                PRIMARY KEY(relationship,alias,entity_id));
            CREATE TABLE IF NOT EXISTS archive_tombstones (
                id TEXT PRIMARY KEY, forgotten_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS archive_metadata (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS archive_generations (
                relationship TEXT PRIMARY KEY, generation INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS archive_index_state (
                relationship TEXT NOT NULL, identity TEXT NOT NULL, generation INTEGER,
                digest TEXT, state TEXT NOT NULL, updated_at REAL NOT NULL,
                PRIMARY KEY(relationship,identity));
        """)
        # Transactional triggers also cover consolidation, corrections and forgotten rows.
        for table in ("events", "memories", "entities", "aliases"):
            for operation in ("INSERT", "UPDATE", "DELETE"):
                reference = "OLD" if operation == "DELETE" else "NEW"
                self.db.executescript(f"""
                    CREATE TRIGGER IF NOT EXISTS generation_{table}_{operation}
                    AFTER {operation} ON archive_{table} BEGIN
                        INSERT INTO archive_generations VALUES({reference}.relationship,1)
                        ON CONFLICT(relationship) DO UPDATE SET generation=generation+1;
                    END;
                """)
        self.db.execute("""
            INSERT OR IGNORE INTO archive_generations
            SELECT DISTINCT relationship,1 FROM archive_events
        """)
        self.db.execute("PRAGMA user_version=1")
        self.db.commit()

    def generation(self, relationship: str) -> int:
        row = self.db.execute(
            "SELECT generation FROM archive_generations WHERE relationship=?", (relationship,)
        ).fetchone()
        return int(row[0]) if row else 0

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Compose canonical mutations without an inner operation committing its caller."""
        nested = self.db.in_transaction
        name = "archive_" + new_id().replace("-", "")
        self.db.execute("SAVEPOINT " + name if nested else "BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("RELEASE " + name if nested else "COMMIT")
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK TO " + name if nested else "ROLLBACK")
                if nested:
                    self.db.execute("RELEASE " + name)
            raise

    def index_state(self, relationship: str, identity: str) -> str:
        row = self.db.execute(
            "SELECT generation,state FROM archive_index_state WHERE relationship=? AND identity=?",
            (relationship, identity),
        ).fetchone()
        if not row or row[0] != self.generation(relationship):
            return "OUTDATED"
        return str(row[1])

    @property
    def db(self) -> sqlite3.Connection:
        if self._closed:
            raise sqlite3.ProgrammingError("archive is closed")
        if not hasattr(self._thread, "connection"):
            # Each request thread owns its transaction; cross-thread close is shutdown-only.
            connection = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("PRAGMA foreign_keys=ON")
            self._thread.connection = connection
            with self._connection_lock:
                self._connections.add(connection)
        current_connection: sqlite3.Connection = self._thread.connection
        return current_connection

    def close_thread(self) -> None:
        if hasattr(self._thread, "connection"):
            with self._connection_lock:
                self._connections.discard(self._thread.connection)
                self._thread.connection.close()
                del self._thread.connection

    def close(self) -> None:
        self._closed = True
        with self._connection_lock:
            for connection in self._connections:
                connection.close()
            self._connections.clear()
        if hasattr(self._thread, "connection"):
            del self._thread.connection

    @staticmethod
    def _safe(content: str) -> None:
        if (
            not content
            or len(content) > 64_000
            or "\x00" in content
            or redact_runtime_secrets(content) != content
            or re.search(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})", content)
        ):
            raise ValueError("invalid or credential-bearing retained content")

    def append(self, event: SourceEvent, *, retain_authorized: bool) -> str:
        if not retain_authorized:
            raise PermissionError("perception does not grant retention")
        self._safe(event.content)
        if (
            not event.relationship_id
            or not event.source
            or event.retention != "selected"
            or event.sensitivity not in {"synthetic", "ordinary", "personal"}
            or not math.isfinite(event.occurred_at)
            or event.expires_at is not None
            and not math.isfinite(event.expires_at)
        ):
            raise ValueError("invalid event scope/retention")
        if event.corrects:
            prior = self.event(event.corrects)
            if prior.relationship_id != event.relationship_id:
                raise ValueError("correction cannot cross relationships")
        payload = json.dumps(asdict(event), sort_keys=True)
        source = urlsplit(event.source)
        if (
            source.username
            or source.password
            or source.query
            or source.fragment
            or len(payload.encode()) > 100_000
            or len(event.entity_ids) > 64
            or redact_runtime_secrets(payload) != payload
        ):
            raise ValueError("credential material cannot enter event metadata")
        with self.transaction():
            existing = self.db.execute(
                "SELECT payload,forgotten FROM archive_events WHERE id=?", (event.id,)
            ).fetchone()
            if existing:
                if existing != (payload, 0):
                    raise ValueError("event identity is immutable")
            else:
                self.db.execute(
                    "INSERT INTO archive_events(id,relationship,payload) VALUES(?,?,?)",
                    (event.id, event.relationship_id, payload),
                )
        return event.id

    def purge_expired_events(self, relationship: str, *, limit: int = 1000) -> int:
        """Expire canonical payloads and dependent memories; no secure-erasure claim."""
        if not relationship or type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("bounded scoped expiry required")
        with self.db:
            targets = {
                row[0]
                for row in self.db.execute(
                    "SELECT id FROM archive_events WHERE relationship=? AND forgotten=0 "
                    "AND json_extract(payload,'$.expires_at')<=? LIMIT ?",
                    (relationship, time(), limit),
                )
            }
            if not targets:
                return 0
            # Admission already rejects expired support; remove its retained copies as well.
            for identifier, payload in self.db.execute(
                "SELECT id,payload FROM archive_memories WHERE relationship=? AND forgotten=0",
                (relationship,),
            ).fetchall():
                if targets.intersection(json.loads(payload)["event_ids"]):
                    self.db.execute(
                        "UPDATE archive_memories SET forgotten=1,payload='{}' WHERE id=?",
                        (identifier,),
                    )
                    self.db.execute("DELETE FROM archive_fts WHERE memory_id=?", (identifier,))
                    self.db.execute(
                        "INSERT OR IGNORE INTO archive_tombstones VALUES(?,?)", (identifier, time())
                    )
            for identifier in targets:
                self.db.execute(
                    "UPDATE archive_events SET forgotten=1,payload='{}' WHERE id=?", (identifier,)
                )
                self.db.execute("DELETE FROM archive_aliases WHERE source_event=?", (identifier,))
                for (entity,) in self.db.execute(
                    "SELECT id FROM archive_entities WHERE source_event=?", (identifier,)
                ).fetchall():
                    self.db.execute("DELETE FROM archive_aliases WHERE entity_id=?", (entity,))
                self.db.execute("DELETE FROM archive_entities WHERE source_event=?", (identifier,))
        return len(targets)

    def event(self, event_id: str) -> SourceEvent:
        row = self.db.execute(
            "SELECT payload FROM archive_events WHERE id=? AND forgotten=0", (event_id,)
        ).fetchone()
        if not row:
            raise KeyError(event_id)
        data = json.loads(row[0])
        if data["expires_at"] is not None and data["expires_at"] <= time():
            raise KeyError("event expired")
        return SourceEvent(
            **{**data, "entity_ids": tuple(data["entity_ids"]), "status": Epistemic(data["status"])}
        )

    def conversation(
        self, relationship: str, *, before: int = 0, limit: int = 40
    ) -> dict[str, Any]:
        """Page canonical conversation events; cursors never cross relationship scope."""
        if not relationship or type(before) is not int or before < 0 or not 1 <= limit <= 40:
            raise ValueError("bounded conversation page required")
        rows = self.db.execute(
            "SELECT rowid,id FROM archive_events WHERE relationship=? AND forgotten=0 "
            "AND json_extract(payload,'$.kind') IN ('conversation_owner','conversation_oscar') "
            "AND (json_extract(payload,'$.expires_at') IS NULL "
            "OR json_extract(payload,'$.expires_at')>?) "
            "AND (?=0 OR rowid<?) ORDER BY rowid DESC LIMIT ?",
            (relationship, time(), before, before, limit + 1),
        ).fetchall()
        selected = rows[:limit]
        events = [self.event(identifier) for _, identifier in reversed(selected)]
        return {"events": events, "before": selected[-1][0] if len(rows) > limit else None}

    def memories(
        self,
        relationship: str,
        *,
        project: str | None = None,
        entity: str | None = None,
        at: float | None = None,
        limit: int = 1000,
        include_history: bool = False,
    ) -> list[MemoryRecord]:
        if not 1 <= limit <= 10_000:
            raise ValueError("memory bound required")
        rows = self.db.execute(
            "SELECT payload FROM archive_memories WHERE relationship=? AND forgotten=0 "
            "ORDER BY rowid DESC LIMIT ?",
            (relationship, limit),
        )
        result = []
        instant = time() if at is None else at
        for (payload,) in rows:
            d = json.loads(payload)
            memory = MemoryRecord(
                **{
                    **d,
                    "event_ids": tuple(d["event_ids"]),
                    "entity_ids": tuple(d["entity_ids"]),
                    "status": Epistemic(d["status"]),
                }
            )
            if project is not None and memory.project_id != project:
                continue
            if entity is not None and entity not in memory.entity_ids:
                continue
            if memory.expires_at is not None and memory.expires_at <= time():
                continue
            if not include_history and (
                memory.valid_from > instant
                or (memory.valid_to is not None and instant >= memory.valid_to)
            ):
                continue
            try:
                for identifier in memory.event_ids:
                    self.event(identifier)
            except KeyError:
                continue
            result.append(memory)
        return result

    def fts(self, relationship: str, query: str, *, limit: int = 20) -> list[str]:
        if not 1 <= limit <= 100:
            raise ValueError("FTS bound required")
        tokens = re.findall(r"\w+", query, re.UNICODE)[:24]
        if not tokens:
            return []
        expression = " OR ".join('"' + token + '"' for token in tokens)
        return [
            row[0]
            for row in self.db.execute(
                "SELECT memory_id FROM archive_fts WHERE archive_fts MATCH ? AND relationship=? "
                "ORDER BY rank LIMIT ?",
                (expression, relationship, limit),
            )
        ]

    def add_entity(self, relationship: str, name: str, kind: str, source_event: str) -> str:
        event = self.event(source_event)
        self._safe(name)
        if event.relationship_id != relationship or len(name) > 200:
            raise ValueError("entity source mismatch")
        identifier = new_id()
        with self.db:
            self.db.execute(
                "INSERT INTO archive_entities VALUES(?,?,?,?,?)",
                (identifier, relationship, name, kind, source_event),
            )
            self.db.execute(
                "INSERT INTO archive_aliases VALUES(?,?,?,?)",
                (relationship, name.casefold(), identifier, source_event),
            )
        return identifier

    def alias(self, entity: str, alias: str, source_event: str, *, owner_confirmed: bool) -> None:
        if not owner_confirmed:
            raise PermissionError("alias mapping requires explicit identity evidence")
        self._safe(alias)
        row = self.db.execute(
            "SELECT relationship FROM archive_entities WHERE id=?", (entity,)
        ).fetchone()
        if not row or self.event(source_event).relationship_id != row[0]:
            raise ValueError("alias source mismatch")
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO archive_aliases VALUES(?,?,?,?)",
                (row[0], alias.casefold(), entity, source_event),
            )

    def resolve(self, relationship: str, alias: str) -> tuple[str, ...]:
        return tuple(
            row[0]
            for row in self.db.execute(
                "SELECT entity_id FROM archive_aliases WHERE relationship=? AND alias=?",
                (relationship, alias.casefold()),
            )
        )

    def forget(
        self, memory_id: str, *, owner_authorized: bool, forget_sources: bool = False
    ) -> None:
        if not owner_authorized:
            raise PermissionError("forget requires owner authority")
        row = self.db.execute(
            "SELECT payload FROM archive_memories WHERE id=?", (memory_id,)
        ).fetchone()
        if not row:
            raise KeyError(memory_id)
        sources = json.loads(row[0])["event_ids"] if forget_sources else []
        with self.transaction():
            targets = {memory_id}
            if sources:
                for identifier, payload in self.db.execute(
                    "SELECT id,payload FROM archive_memories WHERE forgotten=0"
                ):
                    if set(json.loads(payload)["event_ids"]) & set(sources):
                        targets.add(identifier)
                for source in sources:
                    self.db.execute(
                        "UPDATE archive_events SET forgotten=1,payload='{}' WHERE id=?", (source,)
                    )
                    self.db.execute("DELETE FROM archive_aliases WHERE source_event=?", (source,))
                    entities = [
                        r[0]
                        for r in self.db.execute(
                            "SELECT id FROM archive_entities WHERE source_event=?", (source,)
                        )
                    ]
                    for entity in entities:
                        self.db.execute("DELETE FROM archive_aliases WHERE entity_id=?", (entity,))
                    self.db.execute("DELETE FROM archive_entities WHERE source_event=?", (source,))
            for identifier in targets:
                self.db.execute(
                    "UPDATE archive_memories SET forgotten=1,payload='{}' WHERE id=?", (identifier,)
                )
                self.db.execute("DELETE FROM archive_fts WHERE memory_id=?", (identifier,))
                self.db.execute(
                    "INSERT OR IGNORE INTO archive_tombstones VALUES(?,?)", (identifier, time())
                )
        # WAL/backups/physical media are not securely erased by this operation.


class MemoryWriter:
    KINDS = {
        "episodic",
        "semantic",
        "preference",
        "decision",
        "entity_relationship",
        "procedural_candidate",
        "temporary_context",
    }

    def __init__(self, archive: EventArchive):
        self.archive = archive

    def retain(
        self,
        event_ids: tuple[str, ...],
        content: str,
        kind: str,
        *,
        retain_authorized: bool,
        inferred: bool = True,
        project: str | None = None,
        entities: tuple[str, ...] = (),
        supersedes: str | None = None,
    ) -> MemoryRecord:
        if not retain_authorized:
            raise PermissionError("memory candidates need retention authority")
        if not 1 <= len(event_ids) <= 32 or kind not in self.KINDS:
            raise ValueError("bounded supported memory candidate required")
        self.archive._safe(content)
        events = [self.archive.event(identifier) for identifier in event_ids]
        relationship = events[0].relationship_id
        if any(e.relationship_id != relationship or e.project_id != project for e in events):
            raise ValueError("memory cannot broaden source relationship/project scope")
        if any(e.context_key != events[0].context_key for e in events):
            raise ValueError("memory cannot combine different structured context keys")
        if not inferred and any(content != e.content for e in events):
            raise ValueError("non-inferred extraction must preserve exact source statement")
        if any(entity not in e.entity_ids for e in events for entity in entities):
            raise ValueError("candidate entity lacks source evidence")
        starts = max(e.occurred_at for e in events)
        memory = MemoryRecord(
            new_id(),
            relationship,
            event_ids,
            content,
            kind,
            project,
            entities,
            Epistemic.INFERRED
            if inferred or any(e.status == Epistemic.INFERRED for e in events)
            else Epistemic.UNKNOWN
            if any(e.status == Epistemic.UNKNOWN for e in events)
            else Epistemic.REPORTED,
            starts,
            supersedes=supersedes,
            sensitivity=events[0].sensitivity,
            expires_at=min(
                (e.expires_at for e in events if e.expires_at is not None), default=None
            ),
            context_key=events[0].context_key,
        )
        with self.archive.transaction():
            if supersedes:
                row = self.archive.db.execute(
                    "SELECT payload FROM archive_memories WHERE id=? AND forgotten=0", (supersedes,)
                ).fetchone()
                if not row:
                    raise KeyError(supersedes)
                old = json.loads(row[0])
                if (
                    old["relationship_id"] != relationship
                    or old["project_id"] != project
                    or set(old["entity_ids"]) != set(entities)
                    or old["valid_to"] is not None
                    or starts <= old["valid_from"]
                ):
                    raise ValueError("invalid scoped temporal correction")
                if not any(e.corrects in old["event_ids"] for e in events):
                    raise ValueError("supersession requires linked source correction")
                old["valid_to"] = starts
                self.archive.db.execute(
                    "UPDATE archive_memories SET payload=? WHERE id=?",
                    (json.dumps(old), supersedes),
                )
            self.archive.db.execute(
                "INSERT INTO archive_memories(id,relationship,payload) VALUES(?,?,?)",
                (memory.id, relationship, json.dumps(asdict(memory))),
            )
            self.archive.db.execute(
                "INSERT INTO archive_fts VALUES(?,?,?)", (memory.id, relationship, content)
            )
        return memory

    def consolidate(self, relationship: str, *, limit: int = 100) -> int:
        """Bounded idempotent evidence merge, preserving originals and inference status."""
        records = self.archive.memories(relationship, limit=limit)
        return self._merge(records)

    def consolidate_step(
        self, relationship: str, *, batch_size: int = 100, restart: bool = False
    ) -> dict[str, int | bool]:
        """One atomic background batch. A durable cursor resumes after process loss.

        Deduplication is deliberately batch-local; no unsupported global summary/alias merge.
        A completed pass requires explicit restart to process later retained events.
        """
        if type(batch_size) is not int or not 1 <= batch_size <= 100:
            raise ValueError("bounded consolidation batch required")
        key = "consolidation:" + hashlib.sha256(relationship.encode()).hexdigest()
        row = self.archive.db.execute(
            "SELECT value FROM archive_metadata WHERE key=?", (key,)
        ).fetchone()
        job = (
            json.loads(row[0])
            if row and not restart
            else {
                "cursor": 0,
                "upper": self.archive.db.execute(
                    "SELECT COALESCE(MAX(rowid),0) FROM archive_memories WHERE relationship=?",
                    (relationship,),
                ).fetchone()[0],
                "merged": 0,
                "complete": False,
            }
        )
        if job["complete"]:
            return job
        rows = self.archive.db.execute(
            "SELECT rowid,payload FROM archive_memories WHERE relationship=? AND forgotten=0 "
            "AND rowid>? AND rowid<=? ORDER BY rowid LIMIT ?",
            (relationship, job["cursor"], job["upper"], batch_size),
        ).fetchall()
        records = []
        for _cursor, payload in rows:
            data = json.loads(payload)
            if data.get("valid_to") is not None or (
                data.get("expires_at") is not None and data["expires_at"] <= time()
            ):
                continue
            records.append(
                MemoryRecord(
                    **{
                        **data,
                        "event_ids": tuple(data["event_ids"]),
                        "entity_ids": tuple(data["entity_ids"]),
                        "status": Epistemic(data["status"]),
                    }
                )
            )
        job["cursor"] = rows[-1][0] if rows else job["upper"]
        job["complete"] = job["cursor"] >= job["upper"] or len(rows) < batch_size
        self._merge(records, checkpoint=(key, job))
        return job

    def _merge(
        self,
        records: list[MemoryRecord],
        *,
        checkpoint: tuple[str, dict[str, int | bool]] | None = None,
    ) -> int:
        seen: dict[tuple[str, str | None, str, Epistemic], MemoryRecord] = {}
        merged = 0
        with self.archive.db:
            for memory in reversed(records):
                key = (memory.content, memory.project_id, memory.kind, memory.status)
                previous = seen.get(key)
                if (
                    previous
                    and previous.entity_ids == memory.entity_ids
                    and previous.context_key == memory.context_key
                    and previous.sensitivity == memory.sensitivity
                    and previous.expires_at == memory.expires_at
                ):
                    data = asdict(previous)
                    data["event_ids"] = sorted(set(previous.event_ids + memory.event_ids))
                    if len(data["event_ids"]) > 32:
                        continue
                    self.archive.db.execute(
                        "UPDATE archive_memories SET payload=? WHERE id=?",
                        (json.dumps(data), previous.id),
                    )
                    self.archive.db.execute(
                        "UPDATE archive_memories SET forgotten=1 WHERE id=?", (memory.id,)
                    )
                    self.archive.db.execute(
                        "DELETE FROM archive_fts WHERE memory_id=?", (memory.id,)
                    )
                    seen[key] = MemoryRecord(**{**data, "event_ids": tuple(data["event_ids"])})
                    merged += 1
                else:
                    seen[key] = memory
            if merged:
                self.archive.db.execute(
                    "DELETE FROM archive_metadata WHERE key LIKE '%:generation'"
                )
            if checkpoint:
                checkpoint_key, job = checkpoint
                job["merged"] += merged
                self.archive.db.execute(
                    "INSERT OR REPLACE INTO archive_metadata VALUES(?,?)",
                    (checkpoint_key, json.dumps(job)),
                )
        return merged
