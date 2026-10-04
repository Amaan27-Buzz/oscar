"""A-R local synthetic evaluation; measured fixture results are not general hallucination rates."""

import argparse
import json
from pathlib import Path
from time import perf_counter, time
from typing import Any

from oscar.capabilities import ScopedFiles
from oscar.context_sources import FileContextSource
from oscar.continuity import LiveContextFederation
from oscar.contracts import Epistemic
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.fabric_backend import FabricBackend
from oscar.jev import Intent, decide
from oscar.memory_fabric import HistoricalClaim, MemoryFabric
from oscar.memory_indexes import (
    EmbeddingProvider,
    FastEmbedding,
    FastReranker,
    GraphitiIndex,
    QdrantIndex,
    Reranker,
    query_embedding,
)


def run(
    root: Path,
    *,
    embedding: EmbeddingProvider | None = None,
    ranking: Reranker | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    archive = EventArchive(root / "archive.sqlite")
    writer = MemoryWriter(archive)
    embedder = embedding or FastEmbedding()
    reranker = ranking or FastReranker()
    vector = QdrantIndex(root / "vectors", "oscar_evaluation", embedder)
    group = "oscar_eval_" + str(int(time()))
    graph = GraphitiIndex("bolt://127.0.0.1:17687", "neo4j", "", group, embedder, reranker)
    fabric = MemoryFabric(archive, vector=vector, graph=graph, reranker=reranker)
    owner = "synthetic-continuous-owner"
    now = time()
    rows = []
    hits = []
    retrieval_metrics: dict[str, list[dict[str, Any]]] = {"dense": [], "lexical": []}

    def remember(
        text: str,
        *,
        project: str = "study",
        when: float | None = None,
        correction: Any = None,
        supersedes: Any = None,
        inferred: bool = False,
        entities: tuple[str, ...] = (),
        key: str | None = None,
    ) -> tuple[Any, Any]:
        event = SourceEvent(
            owner,
            text,
            "synthetic-owner",
            when or now - 100,
            project_id=project,
            entity_ids=entities,
            corrects=correction.id if correction else None,
            context_key=key,
        )
        archive.append(event, retain_authorized=True)
        memory = writer.retain(
            (event.id,),
            text,
            "preference",
            project=project,
            entities=entities,
            inferred=inferred,
            retain_authorized=True,
            supersedes=supersedes.id if supersedes else None,
        )
        return event, memory

    def case(letter: str, name: str, passed: bool, **details: Any) -> None:
        rows.append(
            {"case": letter, "name": name, "status": "PASS" if passed else "FAIL", **details}
        )

    def recall(query: str, wanted: Any, *, project: str = "study", at: float | None = None) -> Any:
        result = fabric.retrieve(owner, query, project=project, at=at, limit=5)
        found = wanted.id in [hit.memory.id for hit in result.hits]
        hits.append(found)
        m = vector.models
        eligible = archive.memories(owner, project=project, at=at, limit=10_000)
        restriction = m.Filter(
            must=[
                m.FieldCondition(
                    key="memory_id", match=m.MatchAny(any=[record.id for record in eligible])
                )
            ]
        )
        indices, values = vector.sparse.embed(query)
        for path, value in (
            ("dense", query_embedding(embedder, query)),
            ("lexical", m.SparseVector(indices=indices, values=values)),
        ):
            started = perf_counter()
            candidates = vector.client.query_points(
                vector.collection,
                query=value,
                using=path,
                query_filter=restriction,
                limit=5,
                with_payload=True,
            ).points
            retrieval_metrics[path].append(
                {
                    "hit": wanted.id in [p.payload["memory_id"] for p in candidates if p.payload],
                    "query_seconds": perf_counter() - started,
                }
            )
        return result

    try:
        old_event, old = remember("My preferred programming editor is VS Code", when=now - 900)
        new_event, new = remember(
            "My preferred programming editor is Zed",
            when=now - 800,
            correction=old_event,
            supersedes=old,
        )
        _, offline = remember("When travelling without internet I use local models")
        _, distant = remember(
            "The archive project codename is Pine Lantern", when=now - 3 * 365 * 86400
        )
        _, scoped = remember("This project prefers square buttons", project="other-project")
        _, inferred = remember("I may prefer silent reminders", inferred=True)
        _, live_memory = remember("legacy-build", key="project.build")
        # Many retained episodes under one identity, with explicit fixture retention.
        for index in range(128):
            archive.append(
                SourceEvent(
                    owner,
                    f"Selected synthetic episode {index}",
                    "fixture-selection",
                    now - 700 + index,
                    project_id="study",
                ),
                retain_authorized=True,
            )
        for index in range(32):
            remember(
                f"Project inventory item {index}: tagged fixture asset {index}", project="inventory"
            )
        source = SourceEvent(
            owner, "Two distinct people both named Alex", "fixture-owner", now - 500
        )
        archive.append(source, retain_authorized=True)
        alex = archive.add_entity(owner, "Alex", "person", source.id)
        other_alex = archive.add_entity(owner, "Alex", "person", source.id)
        alike = archive.add_entity(owner, "Alexa", "person", source.id)
        archive.alias(alex, "Alex study partner", source.id, owner_confirmed=True)
        assert fabric.rebuild(owner) == ()
        a = recall("My preferred programming editor is Zed", new)
        case("A", "exact", a.hits[0].memory.id == new.id)
        b = recall("Which AI runs during offline journeys?", offline)
        case(
            "B",
            "semantic paraphrase",
            offline.id in [h.memory.id for h in b.hits],
            paths=next((h.paths for h in b.hits if h.memory.id == offline.id), ()),
        )
        c = recall("Pine Lantern", distant)
        case("C", "three-year gap", distant.id in [h.memory.id for h in c.hits])
        case("D", "temporal current", old.id not in [h.memory.id for h in a.hits])
        e = recall("programming editor", old, at=now - 850)
        case("E", "historical", e.hits[0].memory.id == old.id)
        case("F", "correction provenance", archive.event(new_event.id).corrects == old_event.id)
        (root / "workspace").mkdir()
        (root / "workspace/build.txt").write_text("modern-build")
        federation = LiveContextFederation(
            FabricBackend(fabric, owner),
            (
                FileContextSource(
                    ScopedFiles(root / "workspace"), "study", {"project.build": "build.txt"}
                ),
            ),
        )
        context = federation.assemble("synthetic-context", "legacy-build", "study")
        current = context.resolve("project.build", time())
        case(
            "G",
            "live source outranks recalled archive",
            current is not None
            and current.value == "modern-build"
            and archive.event(live_memory.event_ids[0]).content == "legacy-build",
        )
        ambiguous = fabric.retrieve(owner, "Alex", entity_alias="Alex")
        case(
            "H",
            "ambiguous alias",
            set(ambiguous.ambiguous_entities) == {alex, other_alex} and not ambiguous.hits,
        )
        case(
            "I",
            "similar names distinct",
            archive.resolve(owner, "Alexa") == (alike,)
            and archive.resolve(owner, "Alex study partner") == (alex,),
        )
        wrong_project = fabric.retrieve(owner, "square buttons", project="study")
        case("J", "project scope", scoped.id not in [h.memory.id for h in wrong_project.hits])
        negative = fabric.retrieve("unknown-relationship", "owner pet nickname")
        case("K", "negative retrieval", not negative.hits and "7-UNKNOWN" in negative.attempts)
        expanded = fabric.retrieve(owner, "Pine Lantern", project="study")
        case(
            "L",
            "empty active/structured triggers escalation",
            not fabric.active
            and not fabric.structured
            and distant.id in [h.memory.id for h in expanded.hits]
            and "5-query-expansion" in expanded.attempts,
        )
        m = recall(inferred.content, inferred)
        inferred_claim = HistoricalClaim(
            inferred.content, inferred.event_ids, (inferred.id,), Epistemic.RECALLED, 0.5
        )
        case(
            "M",
            "inference remains INFERRED",
            fabric.check_claim(inferred_claim, m) == Epistemic.INFERRED,
        )
        unsupported = []
        for text in (
            "Owner uses Vim",
            "Owner pet is Ember",
            "Owner prefers cloud only",
            "Owner studied at Hogwarts",
            "Owner likes every rounded design",
            "Owner authorized all calendar writes",
        ):
            claim = HistoricalClaim(text, new.event_ids, (new.id,), Epistemic.RECALLED, 0.99)
            unsupported.append(fabric.check_claim(claim, a) == Epistemic.UNKNOWN)
        case("N", "plausible unsupported claims", all(unsupported), rejected=len(unsupported))
        assert fabric.forget(new.id, owner_authorized=True, forget_sources=True) == ()
        case(
            "O",
            "forget",
            new.id not in archive.fts(owner, "Zed")
            and new.id not in vector.query("Zed", owner)
            and new.id not in graph.query("Zed", owner),
        )
        # Destroy both derived projections, leaving canonical source events untouched.
        vector.client.delete_collection(vector.collection)
        graph.loop.run_until_complete(
            graph.graph.driver.execute_query(
                "MATCH (n {group_id:$group}) DETACH DELETE n", group=group
            )
        )
        rebuilt = fabric.rebuild(owner)
        case(
            "P",
            "both native indexes rebuild",
            not rebuilt
            and offline.id in vector.query("offline journeys", owner)
            and offline.id in graph.query("travelling internet local models", owner),
        )
        vector.close()
        archive.close()
        archive = EventArchive(root / "archive.sqlite")
        vector = QdrantIndex(root / "vectors", "oscar_evaluation", embedder)
        fabric = MemoryFabric(archive, vector=vector, graph=graph, reranker=reranker)
        case(
            "Q",
            "restart reopen",
            archive.event(old_event.id).content == old.content
            and distant.id in vector.query("Pine Lantern", owner),
        )
        episode_count = archive.db.execute(
            "SELECT count(DISTINCT json_extract(payload,'$.episode_id')) "
            "FROM archive_events WHERE forgotten=0 AND relationship=?",
            (owner,),
        ).fetchone()[0]
        case(
            "R",
            "one relationship across episodes",
            episode_count >= 160 and decide(Intent("continue that project")).memory_required,
            episodes=episode_count,
        )
        false_claims = len(unsupported) - sum(unsupported)
        return {
            "status": "VERIFIED" if all(r["status"] == "PASS" for r in rows) else "PARTIAL",
            "observed_at": time(),
            "cases": rows,
            "metrics": {
                "component_retrieval": {
                    path: {
                        "top5_hit_rate": sum(r["hit"] for r in values) / len(values),
                        "queries": len(values),
                        "query_seconds": [r["query_seconds"] for r in values],
                    }
                    for path, values in retrieval_metrics.items()
                },
                "positive_top5_hit_rate": sum(hits) / len(hits),
                "positive_queries": len(hits),
                "unsupported_claim_acceptance_rate": false_claims / len(unsupported),
                "unsupported_claim_queries": len(unsupported),
                "temporal_cases_passed": sum(
                    r["status"] == "PASS" for r in rows if r["case"] in {"D", "E", "F"}
                ),
                "entity_error_cases": sum(
                    r["status"] != "PASS" for r in rows if r["case"] in {"H", "I"}
                ),
            },
            "limitations": [
                "small synthetic dataset; no universal hallucination claim",
                "exact sourced assertion verifier; arbitrary model paraphrases remain UNKNOWN",
                "reopen evidence here; separate process continuity evaluated independently",
                "Neo4j loopback synthetic fixture without auth; no private records",
            ],
        }
    finally:
        graph.close()
        vector.close()
        archive.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.root)
    (args.root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
