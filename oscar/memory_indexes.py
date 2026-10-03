"""Replaceable local ML and actual OSS derived indexes. Canonical IDs are mandatory."""

import asyncio
import hashlib
import importlib
import json
import os
import re
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from .event_archive import MemoryRecord


class EmbeddingProvider(Protocol):
    identity: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class Reranker(Protocol):
    identity: str

    def rank(self, query: str, texts: Sequence[str]) -> list[float]: ...


class DerivedIndex(Protocol):
    identity: str

    def rebuild(self, records: Sequence[MemoryRecord]) -> None: ...

    def query(self, query: str, relationship: str, *, limit: int = 20) -> list[str]: ...

    def forget(self, memory_ids: Sequence[str]) -> None: ...

    def close(self) -> None: ...


class LocalEmbedding:
    dimensions = 384

    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        *,
        revision: str | None = None,
        offline: bool = True,
    ):
        module = importlib.import_module("sentence_transformers")
        self.model = module.SentenceTransformer(
            model, revision=revision, local_files_only=offline, device="cpu"
        )
        self.identity = f"sentence-transformers:{model}:{revision or 'installed-snapshot'}"
        self.dimensions = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not 1 <= len(texts) <= 1000 or any(len(text) > 64_000 for text in texts):
            raise ValueError("bounded embedding batch required")
        vectors = self.model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        ).tolist()
        return [[float(value) for value in vector] for vector in vectors]


class LocalReranker:
    def __init__(
        self,
        model: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
        *,
        revision: str | None = None,
        offline: bool = True,
    ):
        module = importlib.import_module("sentence_transformers")
        self.model = module.CrossEncoder(
            model, revision=revision, local_files_only=offline, device="cpu", max_length=512
        )
        self.identity = f"cross-encoder:{model}:{revision or 'installed-snapshot'}"

    def rank(self, query: str, texts: Sequence[str]) -> list[float]:
        if len(texts) > 100 or len(query) > 4000:
            raise ValueError("bounded reranking required")
        if not texts:
            return []
        return [
            float(value)
            for value in self.model.predict(
                [(query, text) for text in texts], show_progress_bar=False
            )
        ]


def digest(records: Sequence[MemoryRecord]) -> str:
    from dataclasses import asdict

    return hashlib.sha256(
        json.dumps(
            [asdict(r) for r in sorted(records, key=lambda r: r.id)], sort_keys=True
        ).encode()
    ).hexdigest()


def sparse(text: str) -> tuple[list[int], list[float]]:
    counts = Counter(re.findall(r"\w+", text.casefold()))
    values: dict[int, float] = {}
    for token, count in counts.items():
        index = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "little")
        values[index] = values.get(index, 0) + float(count)
    ordered = sorted(values)
    return ordered, [values[index] for index in ordered]


class QdrantIndex:
    identity = "qdrant-local-hybrid"

    def __init__(self, path: Path, collection: str, embedder: EmbeddingProvider):
        if not re.fullmatch(r"oscar_[a-zA-Z0-9_]{1,80}", collection):
            raise ValueError("OSCAR-owned collection name required")
        module = importlib.import_module("qdrant_client")
        self.models = importlib.import_module("qdrant_client.models")
        self.client = module.QdrantClient(path=str(path))
        self.collection, self.embedder = collection, embedder
        self.generation: str | None = None

    def rebuild(self, records: Sequence[MemoryRecord]) -> None:
        m = self.models
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config={
                "dense": m.VectorParams(size=self.embedder.dimensions, distance=m.Distance.COSINE)
            },
            sparse_vectors_config={"lexical": m.SparseVectorParams()},
        )
        for start in range(0, len(records), 100):
            batch = records[start : start + 100]
            vectors = self.embedder.embed([record.content for record in batch])
            points = []
            for record, dense in zip(batch, vectors, strict=True):
                indices, values = sparse(record.content)
                points.append(
                    m.PointStruct(
                        id=str(uuid5(NAMESPACE_URL, record.id)),
                        vector={
                            "dense": dense,
                            "lexical": m.SparseVector(indices=indices, values=values),
                        },
                        payload={
                            "memory_id": record.id,
                            "relationship_id": record.relationship_id,
                            "project_id": record.project_id,
                            "entity_ids": list(record.entity_ids),
                            "kind": record.kind,
                            "status": record.status,
                            "sensitivity": record.sensitivity,
                            "valid_from": record.valid_from,
                            "valid_to": record.valid_to,
                            "event_ids": list(record.event_ids),
                        },
                    )
                )
            self.client.upsert(self.collection, points=points, wait=True)
        self.generation = digest(records)

    def query(self, query: str, relationship: str, *, limit: int = 20) -> list[str]:
        if not 1 <= limit <= 100:
            raise ValueError("bounded Qdrant query required")
        m = self.models
        indices, values = sparse(query)
        restriction = m.Filter(
            must=[m.FieldCondition(key="relationship_id", match=m.MatchValue(value=relationship))]
        )
        response = self.client.query_points(
            self.collection,
            prefetch=[
                m.Prefetch(
                    query=self.embedder.embed([query])[0],
                    using="dense",
                    filter=restriction,
                    limit=limit,
                ),
                m.Prefetch(
                    query=m.SparseVector(indices=indices, values=values),
                    using="lexical",
                    filter=restriction,
                    limit=limit,
                ),
            ],
            query=m.FusionQuery(fusion=m.Fusion.RRF),
            query_filter=restriction,
            limit=limit,
            with_payload=True,
        )
        return [str(point.payload["memory_id"]) for point in response.points if point.payload]

    def forget(self, memory_ids: Sequence[str]) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete(
                self.collection,
                points_selector=self.models.PointIdsList(
                    points=[str(uuid5(NAMESPACE_URL, identifier)) for identifier in memory_ids]
                ),
                wait=True,
            )
        self.generation = None

    def close(self) -> None:
        self.client.close()


class GraphitiIndex:
    """Graphiti native records/search; deterministic source ingestion, no LLM identity merges.

    Model extraction is deliberately disabled here. OSCAR's Memory Writer owns candidates.
    Graphiti's public Entity/Episode/Edge APIs and search run against real Neo4j.
    """

    identity = "graphiti-neo4j-temporal"

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        group: str,
        embedder: EmbeddingProvider,
        reranker: Reranker,
    ):
        if not re.fullmatch(r"oscar_[a-zA-Z0-9_]{1,80}", group):
            raise ValueError("OSCAR-owned graph group required")
        os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "false"
        graphiti = importlib.import_module("graphiti_core")
        self.nodes = importlib.import_module("graphiti_core.nodes")
        self.edges = importlib.import_module("graphiti_core.edges")

        class SourceOnlyLLM:
            def set_tracer(self, tracer: Any) -> None:
                self.tracer = tracer

            async def _generate_response(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
                raise RuntimeError("model extraction requires an explicit separate capability")

        class Embeddings:
            async def create(self, input_data: Any) -> list[float]:
                text = input_data if isinstance(input_data, str) else " ".join(input_data)
                return embedder.embed([text])[0]

            async def create_batch(self, texts: list[str]) -> list[list[float]]:
                return embedder.embed(texts)

        class Ranking:
            async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
                return sorted(
                    zip(passages, reranker.rank(query, passages), strict=True),
                    key=lambda item: item[1],
                    reverse=True,
                )

        self.graph = graphiti.Graphiti(
            uri,
            user,
            password,
            llm_client=SourceOnlyLLM(),
            embedder=Embeddings(),
            cross_encoder=Ranking(),
            store_raw_episode_content=False,
            max_coroutines=2,
        )
        self.group, self.embedder = group, embedder
        self.loop = asyncio.new_event_loop()
        self.generation: str | None = None
        self.loop.run_until_complete(self.graph.build_indices_and_constraints())

    async def _rebuild(self, records: Sequence[MemoryRecord]) -> None:
        # Only this adapter's group is reset, never a database-wide clear.
        await self.graph.driver.execute_query(
            "MATCH (n {group_id:$group}) DETACH DELETE n", group=self.group
        )
        for record in records:
            now = datetime.now(UTC)
            episode_ids = []
            for event in record.event_ids:
                episode = self.nodes.EpisodicNode(
                    uuid=event,
                    name=event,
                    group_id=self.group,
                    source=self.nodes.EpisodeType.text,
                    source_description="OSCAR canonical event reference",
                    content="",
                    valid_at=datetime.fromtimestamp(record.valid_from, UTC),
                    entity_edges=[record.id],
                )
                await episode.save(self.graph.driver)
                episode_ids.append(event)
            subject_id = (
                record.entity_ids[0]
                if record.entity_ids
                else str(uuid5(NAMESPACE_URL, record.relationship_id))
            )
            subject = self.nodes.EntityNode(
                uuid=subject_id,
                name=subject_id,
                group_id=self.group,
                name_embedding=self.embedder.embed([subject_id])[0],
                summary="Canonical OSCAR identity reference",
            )
            target_id = str(uuid5(NAMESPACE_URL, "object:" + record.id))
            target = self.nodes.EntityNode(
                uuid=target_id,
                name=record.content[:200],
                group_id=self.group,
                name_embedding=self.embedder.embed([record.content])[0],
                summary=record.content,
            )
            await subject.save(self.graph.driver)
            await target.save(self.graph.driver)
            edge = self.edges.EntityEdge(
                uuid=record.id,
                group_id=self.group,
                source_node_uuid=subject_id,
                target_node_uuid=target_id,
                created_at=now,
                name=record.kind,
                fact=record.content,
                fact_embedding=self.embedder.embed([record.content])[0],
                episodes=episode_ids,
                valid_at=datetime.fromtimestamp(record.valid_from, UTC),
                invalid_at=datetime.fromtimestamp(record.valid_to, UTC)
                if record.valid_to is not None
                else None,
                attributes={"memory_id": record.id, "relationship_id": record.relationship_id},
            )
            await edge.save(self.graph.driver)
            for event in episode_ids:
                await self.edges.EpisodicEdge(
                    uuid=str(uuid5(NAMESPACE_URL, event + subject_id)),
                    group_id=self.group,
                    source_node_uuid=event,
                    target_node_uuid=subject_id,
                    created_at=now,
                ).save(self.graph.driver)

    def rebuild(self, records: Sequence[MemoryRecord]) -> None:
        self.loop.run_until_complete(self._rebuild(records))
        self.generation = digest(records)

    def query(self, query: str, relationship: str, *, limit: int = 20) -> list[str]:
        if not 1 <= limit <= 100:
            raise ValueError("bounded temporal query required")
        edges = self.loop.run_until_complete(
            self.graph.search(query, group_ids=[self.group], num_results=limit)
        )
        return [
            str(edge.uuid)
            for edge in edges
            if edge.attributes.get("relationship_id") == relationship
        ]

    def forget(self, memory_ids: Sequence[str]) -> None:
        async def remove() -> None:
            await self.graph.driver.execute_query(
                "MATCH (s {group_id:$group})-[r:RELATES_TO]->(t {group_id:$group}) "
                "WHERE r.uuid IN $ids DELETE r",
                group=self.group,
                ids=list(memory_ids),
            )
            await self.graph.driver.execute_query(
                "MATCH (n {group_id:$group}) WHERE NOT (n)--() DELETE n", group=self.group
            )

        self.loop.run_until_complete(remove())
        self.generation = None

    def close(self) -> None:
        self.loop.run_until_complete(self.graph.close())
        self.loop.close()
