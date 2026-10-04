"""Opt-in real local Qdrant/Graphiti/Neo4j acceptance using synthetic retained events."""

import argparse
import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

from oscar.contracts import Epistemic
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.memory_fabric import HistoricalClaim, MemoryFabric
from oscar.memory_indexes import FastEmbedding, FastReranker, GraphitiIndex, QdrantIndex


def run(root: Path, uri: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    archive = EventArchive(root / "archive.sqlite")
    writer = MemoryWriter(archive)
    embedding = FastEmbedding()
    reranker = FastReranker()
    vector = QdrantIndex(root / "qdrant", "oscar_acceptance", embedding)
    group = "oscar_" + hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:20]
    graph = GraphitiIndex(uri, "neo4j", "", group, embedding, reranker)
    fabric = MemoryFabric(archive, vector=vector, graph=graph, reranker=reranker)
    start = time() - 1000
    checks = []

    def retain(
        content: str, *, at: float, corrects: str | None = None, supersedes: str | None = None
    ) -> tuple[SourceEvent, Any]:
        event = SourceEvent(
            "synthetic-owner",
            content,
            "fixture-owner",
            at,
            project_id="synthetic-project",
            corrects=corrects,
        )
        archive.append(event, retain_authorized=True)
        memory = writer.retain(
            (event.id,),
            content,
            "preference",
            project="synthetic-project",
            inferred=False,
            retain_authorized=True,
            supersedes=supersedes,
        )
        return event, memory

    try:
        old_event, old = retain("My preferred source code editor is VS Code", at=start)
        new_event, new = retain(
            "My preferred source code editor is Zed",
            at=start + 100,
            corrects=old_event.id,
            supersedes=old.id,
        )
        note_event, note = retain(
            "When travelling without internet I use local models", at=start + 200
        )
        identifier_event, identifier_memory = retain(
            "Project build identifier OSCAR_GATEB_7F31", at=start + 220
        )
        assert fabric.rebuild("synthetic-owner") == ()
        m = vector.models
        indices, values = vector.sparse.query("OSCAR_GATEB_7F31")
        exact = vector.client.query_points(
            vector.collection,
            query=m.SparseVector(indices=indices, values=values),
            using="lexical",
            limit=5,
            with_payload=True,
        ).points
        assert identifier_memory.id in [p.payload["memory_id"] for p in exact if p.payload]
        assert identifier_memory.id in vector.query("OSCAR_GATEB_7F31", "synthetic-owner")
        assert (
            vector.client.get_collection(vector.collection)
            .config.params.sparse_vectors["lexical"]
            .modifier
            == m.Modifier.IDF
        )
        checks.append("exact rare build identifier uses native BM25 plus configured Qdrant IDF")
        other = GraphitiIndex(uri, "neo4j", "", group + "_other", embedding, reranker)
        try:
            records = archive.memories("synthetic-owner", include_history=True)
            other.rebuild(records)
            other_digest = other.current_digest()
            sentinel = "oscar-sentinel-" + group
            graph.loop.run_until_complete(
                graph.graph.driver.execute_query(
                    "CREATE (:Entity {uuid:$id,group_id:$group,name:'unrelated sentinel'})",
                    id=sentinel,
                    group=group,
                )
            )
            assert fabric.rebuild("synthetic-owner") == ()
            assert other.current_digest() == other_digest
            assert new.id in other.query("preferred code editor", "synthetic-owner")
            rows, _, _ = graph.loop.run_until_complete(
                graph.graph.driver.execute_query(
                    "MATCH (n {uuid:$id}) RETURN n.name AS name",
                    id=sentinel,
                )
            )
            assert rows[0]["name"] == "unrelated sentinel"
            graph.loop.run_until_complete(
                graph.graph.driver.execute_query(
                    "MATCH (n:OSCARMemoryProjection {group_id:$group}),(s {uuid:$id}) "
                    "WITH n,s LIMIT 1 CREATE (n)-[:RELATES_TO {uuid:$edge,group_id:$group}]->(s)",
                    id=sentinel,
                    edge=sentinel + "_edge",
                    group=group,
                )
            )
            try:
                graph.rebuild(records)
            except RuntimeError:
                pass
            else:
                raise AssertionError("foreign relationship must block destructive rebuild")
            graph.loop.run_until_complete(
                graph.graph.driver.execute_query(
                    "MATCH ()-[r {uuid:$id}]->() DELETE r",
                    id=sentinel + "_edge",
                )
            )
            graph.loop.run_until_complete(
                graph.graph.driver.execute_query(
                    "MATCH (n {uuid:$id}) DELETE n",
                    id=sentinel,
                )
            )
            checks.append("rebuild preserves second group and unrelated same-group node")
        finally:
            other.close()
        assert new.id in vector.query("Which programming editor do I favour?", "synthetic-owner")
        assert not vector.query("editor", "unrelated-owner")
        checks.append("real Qdrant dense+sparse RRF paraphrase and relationship filter")
        graph_ids = graph.query("preferred source code editor", "synthetic-owner")
        assert new.id in graph_ids, graph_ids
        checks.append("real Graphiti native hybrid search against Neo4j")
        current = fabric.retrieve(
            "synthetic-owner", "preferred code editor", project="synthetic-project"
        )
        assert current.hits[0].memory.id == new.id
        historical = fabric.retrieve("synthetic-owner", "preferred code editor", at=start + 50)
        assert historical.hits[0].memory.id == old.id
        assert all(hit.status == Epistemic.RECALLED for hit in current.hits + historical.hits)
        checks.append("canonical time filters distinguish current Zed and historical VS Code")
        assert any(
            hit.memory.id == note.id
            for hit in fabric.retrieve("synthetic-owner", "offline AI on journeys").hits
        )
        checks.append("real local embedding/reranker paraphrase candidates with source IDs")
        claim = HistoricalClaim(new.content, (new_event.id,), (new.id,), Epistemic.RECALLED, 0.9)
        assert fabric.check_claim(claim, current) == Epistemic.RECALLED
        unsupported = HistoricalClaim(
            "Owner uses Vim", (new_event.id,), (new.id,), Epistemic.RECALLED, 1
        )
        assert fabric.check_claim(unsupported, current) == Epistemic.UNKNOWN
        checks.append("unsupported personal claim UNKNOWN; retrieved claim remains RECALLED")

        def unavailable(*args: Any, **kwargs: Any) -> Any:
            raise OSError("injected local ML outage")

        original_rank = reranker.rank
        reranker.rank = unavailable  # type: ignore[method-assign]
        try:
            degraded = fabric.retrieve("synthetic-owner", "source code editor")
            assert degraded.hits and "reranker" in degraded.unavailable
        finally:
            reranker.rank = original_rank  # type: ignore[method-assign]
        original_embed, original_query = embedding.embed, embedding.query
        embedding.embed = unavailable  # type: ignore[method-assign]
        embedding.query = unavailable  # type: ignore[method-assign]
        try:
            degraded = fabric.retrieve("synthetic-owner", "source code editor")
            assert degraded.hits and "3-qdrant-hybrid" in degraded.unavailable
            assert "4-graphiti-temporal" in degraded.unavailable
        finally:
            embedding.embed = original_embed  # type: ignore[method-assign]
            embedding.query = original_query  # type: ignore[method-assign]
        checks.append(
            "independent injected reranker and embedding failures preserve archive recall"
        )
        # Independently inspect actual native temporal relationship properties.
        rows, _, _ = graph.loop.run_until_complete(
            graph.graph.driver.execute_query(
                "MATCH ()-[r:RELATES_TO {group_id:$group}]->() "
                "RETURN r.memory_id AS id,r.reference_time AS reference_time,r.valid_at AS starts,"
                "r.invalid_at AS ends,r.episodes AS events",
                group=group,
            )
        )
        by_id = {row["id"]: row for row in rows}
        assert by_id[old.id]["ends"] is not None and by_id[new.id]["ends"] is None
        rows, _, _ = graph.loop.run_until_complete(
            graph.graph.driver.execute_query(
                "MATCH (n:Episodic {group_id:$group}) WHERE n.uuid IN $ids RETURN n.name AS event",
                group=group,
                ids=by_id[old.id]["events"],
            )
        )
        assert old_event.id in [r["event"] for r in rows]
        assert all(row["reference_time"] is not None for row in by_id.values())
        checks.append("independent Neo4j query confirms source episode IDs and validity interval")
        vector.close()
        archive.close()
        archive = EventArchive(root / "archive.sqlite")
        vector = QdrantIndex(root / "qdrant", "oscar_acceptance", embedding)
        fabric = MemoryFabric(archive, vector=vector, graph=graph, reranker=reranker)
        assert new.id in vector.query("source code editor", "synthetic-owner")
        assert archive.event(new_event.id).corrects == old_event.id
        checks.append("canonical archive and Qdrant reopen preserve one relationship")
        # Drift is injected only into the synthetic, adapter-owned derived collection.
        vector.client.delete_collection(vector.collection)
        degraded = fabric.retrieve("synthetic-owner", "source code editor")
        assert "3-qdrant-hybrid:OUTDATED" in degraded.unavailable and degraded.hits
        assert fabric.rebuild("synthetic-owner") == ()
        assert new.id in vector.query("source code editor", "synthetic-owner")
        checks.append("deleted derived collection gives explicit fallback and canonical rebuild")
        assert fabric.forget(new.id, owner_authorized=True, forget_sources=True) == ()
        assert new.id not in vector.query("source code editor", "synthetic-owner")
        assert new.id not in graph.query("source code editor", "synthetic-owner")
        assert fabric.check_claim(claim, current) == Epistemic.UNKNOWN
        assert fabric.rebuild("synthetic-owner") == ()
        assert all(
            hit.memory.id != new.id for hit in fabric.retrieve("synthetic-owner", "Zed").hits
        )
        checks.append(
            "forget fences cached evidence, deletes native index entries, survives rebuild"
        )
        return {
            "status": "VERIFIED",
            "observed_at": time(),
            "relationship": "synthetic-owner",
            "source_event_ids": [old_event.id, new_event.id, note_event.id, identifier_event.id],
            "memory_ids": [old.id, new.id, note.id, identifier_memory.id],
            "graph_group": group,
            "embedding": embedding.identity,
            "reranker": reranker.identity,
            "checks": checks,
            "limitations": [
                "synthetic local fixture only",
                "Neo4j fixture has loopback ports and no authentication; never load private data",
                "exact claim validation; arbitrary paraphrased entailment remains UNKNOWN",
                "forget is not secure disk erasure",
            ],
        }
    finally:
        graph.close()
        vector.close()
        archive.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--uri", default="bolt://127.0.0.1:17687")
    args = parser.parse_args()
    report = run(args.root, args.uri)
    (args.root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
