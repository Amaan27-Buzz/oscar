"""Replaceable local ML and actual OSS derived indexes. Canonical IDs are mandatory."""

import asyncio
import hashlib
import importlib
import json
import os
import re
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

    def rebuild(
        self, records: Sequence[MemoryRecord], *, relationship: str | None = None
    ) -> None: ...

    def query(self, query: str, relationship: str, *, limit: int = 20) -> list[str]: ...

    def forget(self, memory_ids: Sequence[str]) -> None: ...

    def close(self) -> None: ...

    def current_digest(self) -> str | None: ...


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


class FastEmbedding:
    """Replaceable CPU ONNX runtime; FastEmbed owns tokenization and model execution."""

    dimensions = 384

    def __init__(
        self,
        model: str = "BAAI/bge-small-en-v1.5",
        *,
        cache: str | None = None,
        offline: bool = True,
    ):
        module = importlib.import_module("fastembed")
        self.model = module.TextEmbedding(
            model_name=model,
            cache_dir=cache,
            threads=2,
            providers=["CPUExecutionProvider"],
            local_files_only=offline,
        )
        self.identity = f"fastembed:0.8.1:{model}:{fastembed_fingerprint(self.model)}"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not 1 <= len(texts) <= 1000 or any(len(text) > 64_000 for text in texts):
            raise ValueError("bounded embedding batch required")
        return [[float(v) for v in row] for row in self.model.passage_embed(list(texts))]

    def query(self, text: str) -> list[float]:
        if not 0 < len(text) <= 4000:
            raise ValueError("bounded embedding query required")
        return [float(v) for v in next(iter(self.model.query_embed(text)))]


class FastReranker:
    def __init__(self, *, cache: str | None = None, offline: bool = True):
        module = importlib.import_module("fastembed.rerank.cross_encoder")
        name = "Xenova/ms-marco-MiniLM-L-6-v2"
        self.model = module.TextCrossEncoder(
            model_name=name,
            cache_dir=cache,
            threads=2,
            providers=["CPUExecutionProvider"],
            local_files_only=offline,
        )
        self.identity = f"fastembed:0.8.1:{name}:{fastembed_fingerprint(self.model)}"

    def rank(self, query: str, texts: Sequence[str]) -> list[float]:
        if len(texts) > 100 or len(query) > 4000:
            raise ValueError("bounded reranking required")
        return [float(v) for v in self.model.rerank(query, list(texts))] if texts else []


def query_embedding(embedder: EmbeddingProvider, text: str) -> list[float]:
    if isinstance(embedder, FastEmbedding):
        return embedder.query(text)
    return embedder.embed([text])[0]


def fastembed_fingerprint(model: Any) -> str:
    """Pinned SDK adapter: fingerprint actual ONNX and tokenizer artifacts, not a model alias."""
    backend = model.model
    directory = Path(backend._model_dir)
    paths = [directory / backend.model_description.model_file]
    paths.extend(sorted(directory.glob("*.json")))
    checksums = []
    for path in paths:
        with path.open("rb") as stream:
            checksums.append(hashlib.file_digest(stream, "sha256").hexdigest())
    return hashlib.sha256("".join(checksums).encode()).hexdigest()


def digest(records: Sequence[MemoryRecord]) -> str:
    from dataclasses import asdict

    return hashlib.sha256(
        json.dumps(
            [asdict(r) for r in sorted(records, key=lambda r: r.id)], sort_keys=True
        ).encode()
    ).hexdigest()


class SparseEmbeddingProvider(Protocol):
    identity: str

    def embed(self, text: str) -> tuple[list[int], list[float]]: ...


class BM25Embedding:
    """Supported FastEmbed Qdrant BM25; corpus IDF is applied by Qdrant."""

    identity = "fastembed:Qdrant/bm25:0.8.1"

    def __init__(self) -> None:
        module = importlib.import_module("fastembed")
        self.model = module.SparseTextEmbedding(model_name="Qdrant/bm25")

    def embed(self, text: str) -> tuple[list[int], list[float]]:
        if not 0 < len(text) <= 64_000:
            raise ValueError("bounded sparse embedding required")
        vector = next(iter(self.model.embed([text])))
        return [int(i) for i in vector.indices], [float(v) for v in vector.values]


class QdrantIndex:
    identity = "qdrant-local-hybrid"

    def __init__(
        self,
        path: Path,
        collection: str,
        embedder: EmbeddingProvider,
        sparse_embedder: SparseEmbeddingProvider | None = None,
    ):
        if not re.fullmatch(r"oscar_[a-zA-Z0-9_]{1,80}", collection):
            raise ValueError("OSCAR-owned collection name required")
        module = importlib.import_module("qdrant_client")
        self.models = importlib.import_module("qdrant_client.models")
        self.client = module.QdrantClient(path=str(path))
        self.collection, self.embedder = collection, embedder
        self.sparse = sparse_embedder or BM25Embedding()
        self.identity = f"qdrant-bm25-v2:{collection}:{embedder.identity}:{self.sparse.identity}"
        self.generation: str | None = None

    def current_digest(self) -> str | None:
        if not self.client.collection_exists(self.collection):
            return None
        points = self.client.retrieve(
            self.collection,
            ids=[str(uuid5(NAMESPACE_URL, "OSCAR:projection:" + self.collection))],
        )
        if points and points[0].payload and points[0].payload.get("identity") == self.identity:
            return str(points[0].payload["digest"])
        return None

    def rebuild(self, records: Sequence[MemoryRecord], *, relationship: str | None = None) -> None:
        self.generation = None
        m = self.models
        relationships = {record.relationship_id for record in records}
        if relationship:
            if relationships and relationships != {relationship}:
                raise ValueError("rebuild relationship mismatch")
            relationships.add(relationship)
        if not relationships:
            raise ValueError("empty projection rebuild needs explicit relationship")
        if len(relationships) > 1:
            raise ValueError("one relationship per derived collection required")
        if self.client.collection_exists(self.collection):
            markers = self.client.retrieve(
                self.collection,
                ids=[str(uuid5(NAMESPACE_URL, "OSCAR:projection:" + self.collection))],
            )
            if markers and markers[0].payload:
                prior = markers[0].payload.get("relationship")
                if relationships and prior and prior not in relationships:
                    raise ValueError("collection belongs to another relationship")
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config={
                "dense": m.VectorParams(size=self.embedder.dimensions, distance=m.Distance.COSINE)
            },
            sparse_vectors_config={"lexical": m.SparseVectorParams(modifier=m.Modifier.IDF)},
        )
        for start in range(0, len(records), 100):
            batch = records[start : start + 100]
            vectors = self.embedder.embed([record.content for record in batch])
            points = []
            for record, dense in zip(batch, vectors, strict=True):
                indices, values = self.sparse.embed(record.content)
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
        self.client.upsert(
            self.collection,
            points=[
                m.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, "OSCAR:projection:" + self.collection)),
                    vector={},
                    payload={
                        "digest": self.generation,
                        "identity": self.identity,
                        "relationship": next(iter(relationships), None),
                    },
                )
            ],
            wait=True,
        )

    def query(self, query: str, relationship: str, *, limit: int = 20) -> list[str]:
        if not 1 <= limit <= 100:
            raise ValueError("bounded Qdrant query required")
        m = self.models
        indices, values = self.sparse.embed(query)
        restriction = m.Filter(
            must=[m.FieldCondition(key="relationship_id", match=m.MatchValue(value=relationship))]
        )
        response = self.client.query_points(
            self.collection,
            prefetch=[
                m.Prefetch(
                    query=query_embedding(self.embedder, query),
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
                    + [str(uuid5(NAMESPACE_URL, "OSCAR:projection:" + self.collection))]
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
        database: str = "neo4j",
    ):
        if not re.fullmatch(r"oscar_[a-zA-Z0-9_]{1,80}", group):
            raise ValueError("OSCAR-owned graph group required")
        os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "false"
        graphiti = importlib.import_module("graphiti_core")
        llm = importlib.import_module("graphiti_core.llm_client.client")
        embedding = importlib.import_module("graphiti_core.embedder.client")
        ranking = importlib.import_module("graphiti_core.cross_encoder.client")
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
                return query_embedding(embedder, text)

            async def create_batch(self, texts: list[str]) -> list[list[float]]:
                return embedder.embed(texts)

        class Ranking:
            async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
                return sorted(
                    zip(passages, reranker.rank(query, passages), strict=True),
                    key=lambda item: item[1],
                    reverse=True,
                )

        driver = importlib.import_module("graphiti_core.driver.neo4j_driver")
        self.graph = graphiti.Graphiti(
            uri,
            user,
            password,
            graph_driver=driver.Neo4jDriver(uri, user, password, database=database),
            llm_client=type(
                "SourceOnlyLLM",
                (llm.LLMClient,),
                {"_generate_response": SourceOnlyLLM._generate_response},
            )(None),
            embedder=type(
                "LocalGraphitiEmbeddings",
                (embedding.EmbedderClient,),
                {"create": Embeddings.create, "create_batch": Embeddings.create_batch},
            )(),
            cross_encoder=type(
                "LocalGraphitiRanking", (ranking.CrossEncoderClient,), {"rank": Ranking.rank}
            )(),
            store_raw_episode_content=False,
            max_coroutines=2,
        )
        self.group, self.embedder = group, embedder
        self.identity = f"graphiti-v2:{database}:{group}:{embedder.identity}:{reranker.identity}"
        self.loop = asyncio.new_event_loop()
        self.generation: str | None = None
        self.loop.run_until_complete(self.graph.build_indices_and_constraints())
        # Create schema tokens, not a freshness marker, before native scoped reads.
        self.loop.run_until_complete(
            self.graph.driver.execute_query(
                "CREATE (n:OSCARMemoryProjection:OSCARProjectionState "
                "{group_id:$group,identity:$identity,digest:''}) DELETE n",
                group=self.group,
                identity=self.identity,
            )
        )

    async def _rebuild(self, records: Sequence[MemoryRecord], relationship: str | None) -> None:
        relationships = {record.relationship_id for record in records}
        if relationship:
            if relationships and relationships != {relationship}:
                raise ValueError("rebuild relationship mismatch")
            relationships.add(relationship)
        if not relationships:
            raise ValueError("empty projection rebuild needs explicit relationship")
        if len(relationships) > 1:
            raise ValueError("one relationship per Graphiti projection group required")
        existing, _, _ = await self.graph.driver.execute_query(
            "MATCH ()-[r:RELATES_TO {group_id:$group}]->() "
            "WHERE properties(r)['oscar_projection_group']=$group "
            "RETURN DISTINCT properties(r)['relationship_id'] AS relationship",
            group=self.group,
        )
        if relationships and any(row["relationship"] not in relationships for row in existing):
            raise ValueError("group belongs to another relationship")
        # Namespaced UUIDs and a dedicated ownership label fence unrelated Graphiti data.
        foreign, _, _ = await self.graph.driver.execute_query(
            "MATCH (n:OSCARMemoryProjection {group_id:$group})-[r]-() "
            "WHERE properties(r)['oscar_projection_group'] IS NULL "
            "OR properties(r)['oscar_projection_group'] <> $group "
            "RETURN count(r) AS count",
            group=self.group,
        )
        if foreign and foreign[0]["count"]:
            raise RuntimeError("foreign relationships touch projection; rebuild blocked")
        await self.graph.driver.execute_query(
            "MATCH (n:OSCARMemoryProjection {group_id:$group}) DETACH DELETE n", group=self.group
        )
        await self.graph.driver.execute_query(
            "MATCH (n:OSCARProjectionState {group_id:$group}) DELETE n", group=self.group
        )
        owned_ids: list[str] = []

        def identifier(kind: str, value: str) -> str:
            return str(uuid5(NAMESPACE_URL, f"oscar:{self.group}:{kind}:{value}"))

        for record in records:
            now = datetime.now(UTC)
            episode_ids = []
            for event in record.event_ids:
                episode = self.nodes.EpisodicNode(
                    uuid=identifier("event", event),
                    name=event,
                    group_id=self.group,
                    source=self.nodes.EpisodeType.text,
                    source_description="OSCAR canonical event reference",
                    content="",
                    valid_at=datetime.fromtimestamp(record.valid_from, UTC),
                    entity_edges=[identifier("memory", record.id)],
                )
                await episode.save(self.graph.driver)
                await self.graph.driver.execute_query(
                    "MATCH (n {uuid:$id,group_id:$group}) SET n:OSCARMemoryProjection",
                    id=episode.uuid,
                    group=self.group,
                )
                episode_ids.append(episode.uuid)
                owned_ids.append(episode.uuid)
            subject_id = identifier(
                "entity", (record.entity_ids[0] if record.entity_ids else record.relationship_id)
            )
            subject = self.nodes.EntityNode(
                uuid=subject_id,
                name=subject_id,
                group_id=self.group,
                name_embedding=self.embedder.embed([subject_id])[0],
                summary="Canonical OSCAR identity reference",
            )
            target_id = identifier("object", record.id)
            target = self.nodes.EntityNode(
                uuid=target_id,
                name=record.content[:200],
                group_id=self.group,
                name_embedding=self.embedder.embed([record.content])[0],
                summary=record.content,
            )
            await subject.save(self.graph.driver)
            await target.save(self.graph.driver)
            owned_ids.extend([subject_id, target_id])
            # Stamp ownership before any subsequent failure can strand unowned projection nodes.
            await self.graph.driver.execute_query(
                "MATCH (n {group_id:$group}) WHERE n.uuid IN $ids SET n:OSCARMemoryProjection",
                group=self.group,
                ids=owned_ids,
            )
            edge = self.edges.EntityEdge(
                uuid=identifier("memory", record.id),
                group_id=self.group,
                source_node_uuid=subject_id,
                target_node_uuid=target_id,
                created_at=now,
                name=record.kind,
                fact=record.content,
                fact_embedding=self.embedder.embed([record.content])[0],
                episodes=episode_ids,
                valid_at=datetime.fromtimestamp(record.valid_from, UTC),
                reference_time=datetime.fromtimestamp(record.valid_from, UTC),
                invalid_at=datetime.fromtimestamp(record.valid_to, UTC)
                if record.valid_to is not None
                else None,
                attributes={
                    "memory_id": record.id,
                    "relationship_id": record.relationship_id,
                    "oscar_projection_group": self.group,
                },
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
                await self.graph.driver.execute_query(
                    "MATCH ()-[r:MENTIONS {uuid:$id,group_id:$group}]->() "
                    "SET r.oscar_projection_group=$group",
                    id=str(uuid5(NAMESPACE_URL, event + subject_id)),
                    group=self.group,
                )
        await self.graph.driver.execute_query(
            "CREATE (:OSCARProjectionState {group_id:$group,digest:$digest,identity:$identity})",
            group=self.group,
            digest=digest(records),
            identity=self.identity,
        )

    def rebuild(self, records: Sequence[MemoryRecord], *, relationship: str | None = None) -> None:
        self.generation = None
        self.loop.run_until_complete(self._rebuild(records, relationship))
        self.generation = digest(records)

    def current_digest(self) -> str | None:
        async def read() -> str | None:
            rows, _, _ = await self.graph.driver.execute_query(
                "MATCH (n:OSCARProjectionState {group_id:$group,identity:$identity}) "
                "RETURN n.digest AS digest",
                group=self.group,
                identity=self.identity,
            )
            return str(rows[0]["digest"]) if len(rows) == 1 else None

        return self.loop.run_until_complete(read())

    def query(self, query: str, relationship: str, *, limit: int = 20) -> list[str]:
        if not 1 <= limit <= 100:
            raise ValueError("bounded temporal query required")
        edges = self.loop.run_until_complete(
            self.graph.search(query, group_ids=[self.group], num_results=limit)
        )
        return [
            str(edge.attributes["memory_id"])
            for edge in edges
            if edge.attributes.get("relationship_id") == relationship
            and edge.attributes.get("oscar_projection_group") == self.group
        ]

    def forget(self, memory_ids: Sequence[str]) -> None:
        async def remove() -> None:
            await self.graph.driver.execute_query(
                "MATCH (s {group_id:$group})-[r:RELATES_TO]->(t {group_id:$group}) "
                "WHERE r.memory_id IN $ids "
                "AND properties(r)['oscar_projection_group']=$group DELETE r",
                group=self.group,
                ids=list(memory_ids),
            )
            await self.graph.driver.execute_query(
                "MATCH (n:OSCARMemoryProjection {group_id:$group}) WHERE NOT (n)--() DELETE n",
                group=self.group,
            )
            await self.graph.driver.execute_query(
                "MATCH (n:OSCARProjectionState {group_id:$group}) DELETE n", group=self.group
            )

        self.loop.run_until_complete(remove())
        self.generation = None

    def close(self) -> None:
        self.loop.run_until_complete(self.graph.close())
        self.loop.close()
