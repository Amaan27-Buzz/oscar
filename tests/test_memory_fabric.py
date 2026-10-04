import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.contracts import Epistemic
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.jev import DecisionRoute, Intent, decide
from oscar.memory_fabric import HistoricalClaim, MemoryFabric


class FabricTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "archive.sqlite"
        self.archive = EventArchive(self.path)
        self.writer = MemoryWriter(self.archive)
        self.fabric = MemoryFabric(self.archive)
        self.start = time() - 100

    def tearDown(self):
        self.archive.close()
        self.temp.cleanup()

    def memory(
        self,
        content,
        *,
        relationship="owner",
        project=None,
        at=None,
        inferred=False,
        correction=None,
        supersedes=None,
    ):
        event = SourceEvent(
            relationship,
            content,
            "synthetic-owner",
            at or self.start,
            project_id=project,
            corrects=correction,
        )
        self.archive.append(event, retain_authorized=True)
        memory = self.writer.retain(
            (event.id,),
            content,
            "preference",
            project=project,
            retain_authorized=True,
            inferred=inferred,
            supersedes=supersedes,
        )
        return event, memory

    def test_wal_exact_and_fts_survive_reopen(self):
        event, memory = self.memory("Archive decision: editor is VS Code")
        self.assertEqual("wal", self.archive.db.execute("PRAGMA journal_mode").fetchone()[0])
        self.archive.close()
        self.archive = EventArchive(self.path)
        self.assertEqual(event, self.archive.event(event.id))
        self.assertIn(memory.id, self.archive.fts("owner", "VS Code"))

    def test_pre_forget_evidence_cannot_resurrect_claim(self):
        event, memory = self.memory("Unique forgotten historical fact")
        recalled = self.fabric.retrieve("owner", memory.content)
        self.fabric.forget(memory.id, owner_authorized=True)
        claim = HistoricalClaim(memory.content, (event.id,), (memory.id,), Epistemic.RECALLED, 0.9)
        self.assertEqual(Epistemic.UNKNOWN, self.fabric.check_claim(claim, recalled))

    def test_long_gap_older_than_thousand_derived_records(self):
        _, old = self.memory("Pine Lantern archived objective", project="old-project")
        for index in range(1001):
            self.memory(f"New unrelated entry {index}", project="new-project")
        recalled = self.fabric.retrieve("owner", "Pine Lantern", project="old-project")
        self.assertEqual(old.id, recalled.hits[0].memory.id)

    def test_source_inference_cannot_be_promoted_by_extractor_flag(self):
        for state in (Epistemic.INFERRED, Epistemic.UNKNOWN):
            event = SourceEvent(
                "owner", "Uncertain synthetic claim " + state, "fixture", self.start, status=state
            )
            self.archive.append(event, retain_authorized=True)
            memory = self.writer.retain(
                (event.id,), event.content, "semantic", inferred=False, retain_authorized=True
            )
            self.assertEqual(state, memory.status)
            retrieved = self.fabric.retrieve("owner", event.content)
            claim = HistoricalClaim(
                event.content, (event.id,), (memory.id,), Epistemic.RECALLED, 0.5
            )
            self.assertEqual(state, self.fabric.check_claim(claim, retrieved))

    def test_temporal_correction_preserves_original(self):
        old_event, old = self.memory("My editor is VS Code")
        new_event, new = self.memory(
            "My editor is Zed", at=self.start + 50, correction=old_event.id, supersedes=old.id
        )
        self.assertEqual([new.id], [m.id for m in self.archive.memories("owner")])
        self.assertEqual(
            [old.id], [m.id for m in self.archive.memories("owner", at=self.start + 10)]
        )
        self.assertEqual("My editor is VS Code", self.archive.event(old_event.id).content)
        self.assertEqual(old_event.id, self.archive.event(new_event.id).corrects)

    def test_missing_correction_link_cannot_supersede(self):
        _, old = self.memory("My editor is VS Code")
        with self.assertRaises(ValueError):
            self.memory("My editor is Zed", at=self.start + 50, supersedes=old.id)
        self.assertEqual(old.id, self.archive.memories("owner")[0].id)

    def test_project_scope_cannot_be_generalized(self):
        event = SourceEvent(
            "owner", "This OSCAR design is too rounded", "owner", self.start, project_id="OSCAR"
        )
        self.archive.append(event, retain_authorized=True)
        with self.assertRaises(ValueError):
            self.writer.retain(
                (event.id,), "Owner hates all rounded UI", "preference", retain_authorized=True
            )
        scoped = self.writer.retain(
            (event.id,),
            "OSCAR design may need less rounding",
            "preference",
            retain_authorized=True,
            project="OSCAR",
        )
        self.assertEqual(Epistemic.INFERRED, scoped.status)
        self.assertEqual([], self.archive.memories("owner", project="OTHER"))

    def test_extractor_cannot_self_promote_summary(self):
        event, _ = self.memory("This design is too rounded")
        with self.assertRaises(ValueError):
            self.writer.retain(
                (event.id,),
                "I dislike rounded UI",
                "preference",
                retain_authorized=True,
                inferred=False,
            )

    def test_perception_is_not_retention_and_credentials_rejected(self):
        with self.assertRaises(PermissionError):
            self.archive.append(
                SourceEvent("owner", "ordinary", "owner", self.start), retain_authorized=False
            )
        with self.assertRaises(ValueError):
            self.archive.append(
                SourceEvent("owner", "ghp_" + "a" * 36, "owner", self.start), retain_authorized=True
            )

    def test_same_name_entities_stay_ambiguous(self):
        event, _ = self.memory("Two people named Alex are distinct")
        first = self.archive.add_entity("owner", "Alex", "person", event.id)
        second = self.archive.add_entity("owner", "Alex", "person", event.id)
        self.assertNotEqual(first, second)
        recall = self.fabric.retrieve("owner", "What did Alex say?", entity_alias="Alex")
        self.assertEqual((), recall.hits)
        self.assertEqual(2, len(recall.ambiguous_entities))

    def test_alias_requires_evidence_and_no_similarity_merge(self):
        event, _ = self.memory("OSCAR is also called the assistant")
        entity = self.archive.add_entity("owner", "OSCAR", "project", event.id)
        with self.assertRaises(PermissionError):
            self.archive.alias(entity, "the assistant", event.id, owner_confirmed=False)
        self.archive.alias(entity, "the assistant", event.id, owner_confirmed=True)
        self.assertEqual((entity,), self.archive.resolve("owner", "the assistant"))
        self.assertEqual((), self.archive.resolve("owner", "Oscar project"))

    def test_miss_escalates_bounded_before_unknown(self):
        recall = self.fabric.retrieve("owner", "What is my favourite Martian meal?")
        self.assertEqual((), recall.hits)
        self.assertEqual("7-UNKNOWN", recall.attempts[-1])
        self.assertIn("5-query-expansion", recall.attempts)
        self.assertIn("6-bounded-archive", recall.attempts)
        self.assertLessEqual(len(recall.attempts), 8)

    def test_recalled_claim_needs_current_path_exact_support(self):
        event, memory = self.memory("My editor is Zed")
        recall = self.fabric.retrieve("owner", "My editor")
        claim = HistoricalClaim(memory.content, (event.id,), (memory.id,), Epistemic.RECALLED, 1)
        self.assertEqual(Epistemic.RECALLED, self.fabric.check_claim(claim, recall))
        self.assertEqual(
            Epistemic.UNKNOWN,
            self.fabric.check_claim(
                replace(claim, text="I remember your secret banking password"), recall
            ),
        )
        self.assertEqual(
            Epistemic.UNKNOWN,
            self.fabric.check_claim(replace(claim, status=Epistemic.VERIFIED), recall),
        )
        self.assertEqual(
            Epistemic.UNKNOWN,
            self.fabric.check_claim(replace(claim, event_ids=("unrelated",)), recall),
        )

    def test_inference_stays_inferred_in_claim_verifier(self):
        event, memory = self.memory("Possible preference for Zed", inferred=True)
        recall = self.fabric.retrieve("owner", "Zed")
        claim = HistoricalClaim(memory.content, (event.id,), (memory.id,), Epistemic.RECALLED, 1)
        self.assertEqual(Epistemic.INFERRED, self.fabric.check_claim(claim, recall))

    def test_stale_derived_results_cannot_resurrect_forgotten_memory(self):
        _, memory = self.memory("Forget this violet decision")

        class StaleIndex:
            identity = "synthetic-stale-index"

            def query(self, *args, **kwargs):
                return [memory.id]

            def forget(self, ids):
                raise OSError("synthetic deletion outage")

        self.fabric.vector = StaleIndex()
        self.assertEqual(
            (StaleIndex.identity,), self.fabric.forget(memory.id, owner_authorized=True)
        )
        self.assertEqual((), self.fabric.retrieve("owner", "violet").hits)
        self.assertEqual([], self.archive.fts("owner", "violet"))

    def test_forget_source_removes_all_derivations(self):
        event, memory = self.memory("Forget selected source")
        self.writer.retain(
            (event.id,), "Derived selected source", "semantic", retain_authorized=True
        )
        self.fabric.forget(memory.id, owner_authorized=True, forget_sources=True)
        self.assertEqual([], self.archive.memories("owner"))
        with self.assertRaises(KeyError):
            self.archive.event(event.id)

    def test_relationship_and_project_filters(self):
        _, ours = self.memory("Zed project decision", project="OSCAR")
        self.memory("Zed private other relationship", relationship="other")
        self.assertEqual(
            [ours.id],
            [hit.memory.id for hit in self.fabric.retrieve("owner", "Zed", project="OSCAR").hits],
        )

    def test_expired_context_not_recalled(self):
        event = SourceEvent(
            "owner", "Temporary meeting room", "owner", self.start, expires_at=time() - 1
        )
        self.archive.append(event, retain_authorized=True)
        with self.assertRaises(KeyError):
            self.archive.event(event.id)

    def test_event_id_cannot_be_overwritten_or_resurrected(self):
        event, memory = self.memory("immutable original")
        with self.assertRaises(ValueError):
            self.archive.append(replace(event, content="rewritten"), retain_authorized=True)
        self.fabric.forget(memory.id, owner_authorized=True, forget_sources=True)
        with self.assertRaises(ValueError):
            self.archive.append(event, retain_authorized=True)

    def test_consolidation_merges_evidence_without_deleting_events(self):
        first, _ = self.memory("same scoped decision")
        second, _ = self.memory("same scoped decision", at=self.start + 1)
        self.assertEqual(1, self.writer.consolidate("owner"))
        self.assertEqual(0, self.writer.consolidate("owner"))
        self.assertEqual({first.id, second.id}, set(self.archive.memories("owner")[0].event_ids))
        self.assertEqual(first, self.archive.event(first.id))
        self.assertEqual(second, self.archive.event(second.id))

    def test_every_turn_jev_preflight_and_forced_reasoning(self):
        for text in (
            "continue that",
            "same as before",
            "what did I decide?",
            "my usual editor",
            "reason about my project",
            "explain what Alex chose earlier",
        ):
            decision = decide(Intent(text, kind="reason"))
            self.assertTrue(decision.memory_required, text)
            self.assertEqual(DecisionRoute.RECALL, decision.route, text)
        self.assertFalse(decide(Intent("2 + 2")).memory_required)
        self.assertTrue(
            decide(Intent("Explain Sunday", kind="reason"), ("Sunday",)).memory_required
        )

    def test_background_batches_resume_and_preserve_original_events(self):
        events = [self.memory("same retained scoped evidence")[0] for _ in range(6)]
        first = self.writer.consolidate_step("owner", batch_size=2)
        self.assertFalse(first["complete"])
        self.assertEqual(1, first["merged"])
        self.archive.close()
        self.archive = EventArchive(self.path)
        self.writer = MemoryWriter(self.archive)
        self.assertEqual(2, self.writer.consolidate_step("owner", batch_size=2)["merged"])
        final = self.writer.consolidate_step("owner", batch_size=2)
        self.assertTrue(final["complete"])
        self.assertEqual(3, final["merged"])
        self.assertEqual(final, self.writer.consolidate_step("owner", batch_size=2))
        for event in events:
            self.assertEqual(event, self.archive.event(event.id))
        self.assertEqual(3, len(self.archive.memories("owner")))

    def test_background_batch_failure_cannot_commit_cursor_without_mutation(self):
        import sqlite3

        for _ in range(2):
            self.memory("same retained scoped evidence")
        self.archive.db.execute(
            "CREATE TRIGGER fault BEFORE UPDATE ON archive_memories "
            "BEGIN SELECT RAISE(ABORT, 'synthetic fault'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.writer.consolidate_step("owner", batch_size=2)
        self.assertEqual(
            0,
            self.archive.db.execute(
                "SELECT COUNT(*) FROM archive_metadata WHERE key LIKE 'consolidation:%'"
            ).fetchone()[0],
        )
        self.archive.db.execute("DROP TRIGGER fault")
        self.assertEqual(1, self.writer.consolidate_step("owner", batch_size=2)["merged"])

    def test_context_keeps_inference_and_rechecks_forget_and_total_bound(self):
        _, memory = self.memory("derived interpretation", inferred=True)
        evidence = self.fabric.retrieve("owner", "derived interpretation")
        context = self.fabric.context(
            evidence, objective="recall", project=None, live={}, policy_ids=()
        )
        self.assertEqual(Epistemic.INFERRED, context["memories"][0]["status"])
        self.fabric.forget(memory.id, owner_authorized=True, forget_sources=True)
        self.assertEqual(
            [],
            self.fabric.context(evidence, objective="recall", project=None, live={}, policy_ids=())[
                "memories"
            ],
        )
        with self.assertRaises(ValueError):
            self.fabric.context(
                evidence,
                objective="recall",
                project=None,
                live={"oversized": "a" * 13000},
                policy_ids=(),
            )


if __name__ == "__main__":
    unittest.main()
