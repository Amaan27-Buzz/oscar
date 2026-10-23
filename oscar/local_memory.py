"""Explicit local derived-memory composition; canonical history remains authoritative."""

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Any
from urllib.parse import urlsplit

from .event_archive import EventArchive
from .memory_fabric import MemoryFabric, RecallSet
from .memory_indexes import BM25Embedding, FastEmbedding, FastReranker, GraphitiIndex, QdrantIndex


@dataclass(frozen=True)
class LocalMemoryConfig:
    relationship_id: str
    model_cache: Path
    bm25_model_dir: Path
    qdrant_path: Path
    neo4j: dict[str, str] | None = None

    @classmethod
    def load(cls, path: Path) -> "LocalMemoryConfig":
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 8192:
            raise ValueError("bounded selected memory configuration required")
        from .cloud import strict_object

        return cls.parse(
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)
        )

    @classmethod
    def parse(cls, data: Any) -> "LocalMemoryConfig":
        fields = {
            "version",
            "authorized_local_projection",
            "relationship_id",
            "model_cache",
            "bm25_model_dir",
            "qdrant_path",
        }
        if not isinstance(data, dict) or set(data) - fields - {"neo4j"} or not fields <= set(data):
            raise ValueError("exact local memory configuration required")
        if type(data["version"]) is not int or data["version"] != 1:
            raise ValueError("unsupported local memory configuration")
        if data["authorized_local_projection"] is not True:
            raise PermissionError("explicit authorization for local derived copies required")
        if not isinstance(data["relationship_id"], str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,128}", data["relationship_id"]
        ):
            raise ValueError("exact relationship required")
        paths = []
        for name in ("model_cache", "bm25_model_dir", "qdrant_path"):
            value = data[name]
            if (
                not isinstance(value, str)
                or not Path(value).is_absolute()
                or value.startswith(("\\\\", "//"))
            ):
                raise ValueError("absolute selected local paths required")
            path = Path(value)
            if path == path.parent or any(p.is_symlink() for p in (path, *path.parents)):
                raise ValueError("local memory paths cannot traverse symlinks")
            paths.append(path)
        graph = data.get("neo4j")
        if graph is not None:
            if not isinstance(graph, dict) or set(graph) != {
                "uri",
                "user",
                "password_env",
                "database",
            }:
                raise ValueError("exact local Neo4j configuration required")
            if any(not isinstance(value, str) for value in graph.values()):
                raise ValueError("bounded local Neo4j fields required")
            uri = urlsplit(graph["uri"])
            if (
                uri.scheme != "bolt"
                or uri.hostname not in {"127.0.0.1", "::1"}
                or uri.username
                or uri.password
                or uri.path
                or uri.query
                or uri.fragment
                or uri.port is None
                or not 1024 <= uri.port <= 65535
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", graph["user"])
                or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,100}", graph["password_env"])
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", graph["database"])
            ):
                raise ValueError("literal loopback Neo4j and opaque password reference required")
        return cls(
            data["relationship_id"],
            paths[0],
            paths[1],
            paths[2],
            dict(graph) if graph is not None else None,
        )


class LocalMemory(MemoryFabric):
    """One generation-driven rebuild before recall, with bounded failure backoff."""

    def __init__(
        self, archive: EventArchive, config: LocalMemoryConfig, secrets: Mapping[str, str]
    ):
        super().__init__(archive)
        self.config = config
        self.lock = RLock()
        self.closed = False
        self.next_attempt = 0.0
        self.failure: str | None = None
        self._generation: int | None = None
        name = (
            "oscar_"
            + hashlib.sha256(
                (str(archive.path.resolve()) + ":" + config.relationship_id).encode()
            ).hexdigest()[:32]
        )
        try:
            embedding = FastEmbedding(cache=str(config.model_cache), offline=True)
            self.reranker = FastReranker(cache=str(config.model_cache), offline=True)
        except Exception:
            self.failure = "local_models_unavailable"
            return
        try:
            sparse = BM25Embedding(model_path=config.bm25_model_dir, offline=True)
            self.vector = QdrantIndex(config.qdrant_path, name, embedding, sparse)
        except Exception:
            self.failure = "semantic_unavailable"
        if config.neo4j:
            graph = config.neo4j
            try:
                password = secrets[graph["password_env"]]
                if not password:
                    raise ValueError("mounted Neo4j credential required")
                self.graph = GraphitiIndex(
                    graph["uri"],
                    graph["user"],
                    password,
                    name,
                    embedding,
                    self.reranker,
                    database=graph["database"],
                )
            except Exception:
                self.failure = "temporal_unavailable"

    def maintain(self) -> None:
        with self.lock:
            if self.closed:
                return
            relationship = self.config.relationship_id
            generation = self.archive.generation(relationship)
            if self._generation == generation or monotonic() < self.next_attempt:
                return
            self.next_attempt = monotonic() + 30
            count, size = self.archive.db.execute(
                "SELECT count(*),COALESCE(sum(length(payload)),0) FROM archive_memories "
                "WHERE relationship=? AND forgotten=0",
                (relationship,),
            ).fetchone()
            if count > 1000 or size > 2_000_000:
                self.failure = "projection_bound_exceeded"
                return
            try:
                failed = super().rebuild(relationship)
                if generation != self.archive.generation(relationship):
                    identifiers = [
                        row[0]
                        for row in self.archive.db.execute("SELECT id FROM archive_tombstones")
                    ]
                    for index in (self.vector, self.graph):
                        if index is not None and identifiers:
                            index.forget(identifiers)
                    self.failure = "concurrent_archive_update"
                    return
                if failed:
                    self.failure = "derived_rebuild_failed"
                    return
                self._generation = generation
                self.next_attempt = 0
                if self.vector is not None and (not self.config.neo4j or self.graph is not None):
                    self.failure = None
            except Exception:
                self.failure = "derived_rebuild_failed"

    def retrieve(self, relationship: str, query: str, **kwargs: Any) -> RecallSet:
        with self.lock:
            if relationship != self.config.relationship_id:
                raise PermissionError("configured derived relationship mismatch")
            self.maintain()
            return super().retrieve(relationship, query, **kwargs)

    def rebuild(self, relationship: str) -> tuple[str, ...]:
        with self.lock:
            if relationship != self.config.relationship_id or self.closed:
                raise PermissionError("configured derived relationship unavailable")
            count, size = self.archive.db.execute(
                "SELECT count(*),COALESCE(sum(length(payload)),0) FROM archive_memories "
                "WHERE relationship=? AND forgotten=0",
                (relationship,),
            ).fetchone()
            if count > 1000 or size > 2_000_000:
                raise ValueError("configured local projection exceeds bound")
            self._generation = None
            return super().rebuild(relationship)

    def forget_derived(self) -> tuple[str, ...]:
        with self.lock:
            self._generation = None
            self.next_attempt = 0
            return super().forget_derived()

    def status(self) -> dict[str, Any]:
        with self.lock:

            def state(index: Any) -> str:
                if index is None or self.closed:
                    return "unavailable"
                state = self.archive.index_state(
                    self.config.relationship_id, index.identity
                ).lower()
                if state == "current":
                    row = self.archive.db.execute(
                        "SELECT digest FROM archive_index_state "
                        "WHERE relationship=? AND identity=?",
                        (self.config.relationship_id, index.identity),
                    ).fetchone()
                    try:
                        if not row or index.current_digest() != row[0]:
                            return "outdated"
                    except Exception:
                        return "unavailable"
                return state

            return {
                "canonical": "sqlite-wal-fts5",
                "semantic": state(self.vector),
                "temporal": state(self.graph),
                "reranker": "available" if self.reranker and not self.closed else "unavailable",
                "diagnostic": self.failure,
            }

    def close(self) -> None:
        with self.lock:
            if self.closed:
                return
            self.closed = True
            failures = []
            for index in (self.vector, self.graph):
                if index is not None:
                    try:
                        index.close()
                    except Exception as error:
                        failures.append(error)
            if failures:
                raise RuntimeError("local derived memory close failed") from failures[0]
