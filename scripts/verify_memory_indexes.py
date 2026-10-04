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
from oscar.memory_indexes import GraphitiIndex, LocalEmbedding, LocalReranker, QdrantIndex


def run(root: Path, uri: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    archive = EventArchive(root / "archive.sqlite")
    writer = MemoryWriter(archive)
    embedding = LocalEmbedding(revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
    reranker = LocalReranker(revision="233902d25c440f23af6f7d6e94d2946bac0bee0a")
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
        assert fabric.rebuild("synthetic-owner") == ()
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
        # Independently inspect actual native temporal relationship properties.
        rows, _, _ = graph.loop.run_until_complete(
            graph.graph.driver.execute_query(
                "MATCH ()-[r:RELATES_TO {group_id:$group}]->() "
                "RETURN r.uuid AS id,r.valid_at AS starts,"
                "r.invalid_at AS ends,r.episodes AS events",
                group=group,
            )
        )
        by_id = {row["id"]: row for row in rows}
        assert by_id[old.id]["ends"] is not None and by_id[new.id]["ends"] is None
        assert old_event.id in by_id[old.id]["events"]
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
        assert "3-qdrant-hybrid" in degraded.unavailable and degraded.hits
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
            "source_event_ids": [old_event.id, new_event.id, note_event.id],
            "memory_ids": [old.id, new.id, note.id],
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
