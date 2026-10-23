import hashlib
import json
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from unittest.mock import patch

from oscar.cloud import CloudConfig, CloudCore
from oscar.event_archive import MemoryWriter, SourceEvent
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.local_memory import LocalMemory, LocalMemoryConfig
from oscar.memory_fabric import MemoryFabric
from oscar.memory_indexes import digest
from tests.test_cloud import configuration


class FixtureIndex:
    identity = "synthetic-local-index"

    def __init__(self, *args, **kwargs):
        self.records = []
        self.digest = None
        self.builds = 0
        self.closed = False
        self.fail = False

    def rebuild(self, records, *, relationship=None):
        if self.fail:
            raise OSError("synthetic unavailable")
        self.records = list(records)
        self.digest = digest(records)
        self.builds += 1

    def current_digest(self):
        return self.digest

    def query(self, query, relationship, *, limit=20):
        if self.fail:
            raise OSError("synthetic unavailable")
        return [r.id for r in self.records if r.relationship_id == relationship][:limit]

    def forget(self, ids):
        self.records = [r for r in self.records if r.id not in ids]
        self.digest = None

    def close(self):
        self.closed = True


class LocalMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = {
            "version": 1,
            "authorized_local_projection": True,
            "relationship_id": "owner",
            "model_cache": str(self.root / "models"),
            "bm25_model_dir": str(self.root / "bm25"),
            "qdrant_path": str(self.root / "derived"),
        }
        self.config = LocalMemoryConfig.parse(self.data)
        for name, replacement in (
            ("FastEmbedding", object()),
            ("FastReranker", None),
            ("BM25Embedding", object()),
        ):
            self.addCleanup(patch.stopall)
            patch("oscar.local_memory." + name, return_value=replacement).start()
        patch("oscar.local_memory.QdrantIndex", FixtureIndex).start()

    def harness(self, **kwargs):
        h = Harness(
            self.root / "core.sqlite",
            self.root / "files",
            Path("config/development-models.json"),
            memory_config=self.config,
            credential_environ={},
            start_services=False,
            **kwargs,
        )
        self.addCleanup(h.close)
        return h

    def retain(self, h, text="Amber kestrel waits beside the cedar"):
        event = SourceEvent("owner", text, "synthetic-authorized", time() - 1)
        h.archive.append(event, retain_authorized=True)
        return MemoryWriter(h.archive).retain(
            (event.id,),
            text,
            "episodic",
            retain_authorized=True,
            inferred=False,
        )

    def test_default_never_constructs_optional_models(self):
        with patch("oscar.local_memory.FastEmbedding", side_effect=AssertionError("unexpected")):
            with Harness(
                self.root / "default.sqlite",
                self.root / "files",
                Path("config/development-models.json"),
                start_services=False,
            ) as h:
                self.assertIs(type(h.memory), MemoryFabric)

    def test_strict_configuration_and_literal_loopback_only(self):
        for updates in (
            {"authorized_local_projection": False},
            {"version": True},
            {"model_cache": "relative"},
            {"qdrant_path": r"\\server\network-share\derived"},
            {"unknown": 1},
            {"relationship_id": ""},
            {
                "neo4j": {
                    "uri": "bolt://external.example:7687",
                    "user": "neo4j",
                    "password_env": "GRAPH_PASSWORD",
                    "database": "neo4j",
                }
            },
            {
                "neo4j": {
                    "uri": "bolt://localhost:7687",
                    "user": "neo4j",
                    "password_env": "GRAPH_PASSWORD",
                    "database": "neo4j",
                }
            },
        ):
            with self.subTest(updates=updates), self.assertRaises((ValueError, PermissionError)):
                LocalMemoryConfig.parse({**self.data, **updates})
        path = self.root / "memory.json"
        path.write_text(json.dumps(self.data), encoding="utf-8")
        self.assertEqual(self.config, LocalMemoryConfig.load(path))
        path.write_text('{"version":1,"version":1}', encoding="utf-8")
        with self.assertRaises(ValueError):
            LocalMemoryConfig.load(path)

    def test_configured_preflight_generation_deletion_and_close(self):
        h = self.harness()
        memory = self.retain(h)
        self.assertIsInstance(h.runtime.memory, LocalMemory)
        task = h.runtime.create(
            Intent(
                "What did I choose earlier?",
                kind="file_write",
                path="synthetic.txt",
                content="fixture",
            )
        )
        self.assertEqual(memory.id, h.runtime.active_context[task.id]["memories"][0]["memory_id"])
        index = h.memory.vector
        self.assertEqual(1, index.builds)
        h.memory.retrieve("owner", "unrelated query")
        self.assertEqual(1, index.builds)
        h.memory.forget(memory.id, owner_authorized=True, forget_sources=True)
        self.assertEqual([], index.records)
        self.assertEqual((), h.memory.retrieve("owner", "unrelated query").hits)
        self.assertEqual(2, index.builds)
        h.close()
        self.assertTrue(index.closed)

    def test_projection_is_exact_relationship_and_canonical_filter_rejects_stale(self):
        h = self.harness()
        memory = self.retain(h)
        h.memory.retrieve("owner", "chosen earlier")
        with self.assertRaises(PermissionError):
            h.memory.retrieve("someone-else", "chosen earlier")
        h.archive.forget(memory.id, owner_authorized=True)
        h.memory.vector.fail = True
        recall = h.memory.retrieve("owner", "Amber")
        self.assertEqual((), recall.hits)
        self.assertTrue(any("OUTDATED" in item for item in recall.unavailable))
        self.assertEqual("failed", h.memory.status()["semantic"])

    def test_model_failure_keeps_normal_canonical_runtime(self):
        with patch("oscar.local_memory.FastEmbedding", side_effect=OSError("private detail")):
            h = self.harness()
        memory = self.retain(h)
        self.assertEqual(memory.id, h.memory.retrieve("owner", "Amber").hits[0].memory.id)
        state = h.memory.status()
        self.assertEqual("unavailable", state["semantic"])
        self.assertEqual("local_models_unavailable", state["diagnostic"])
        self.assertNotIn("private detail", json.dumps(state))

    def test_bound_prevents_partial_export(self):
        h = self.harness()
        for _ in range(33):
            self.retain(h, "x" * 62_000)
        h.memory.retrieve("owner", "unmatched")
        self.assertEqual(0, h.memory.vector.builds)
        self.assertEqual("projection_bound_exceeded", h.memory.status()["diagnostic"])

    def test_cloud_accepts_same_config_and_truthful_health(self):
        path = configuration(self.root, local_memory=self.data)
        config = CloudConfig.load(path)
        with closing(CloudCore(config, initialize=True, start_services=False)) as core:
            h = core.harness
            self.retain(h)
            self.assertEqual("outdated", core.status()["memory"]["semantic"])
            h.memory.retrieve("owner", "Amber")
            self.assertEqual("current", core.status()["memory"]["semantic"])
        with closing(CloudCore(config, start_services=False)) as restarted:
            self.assertIsInstance(restarted.harness.memory, LocalMemory)
            self.assertTrue(restarted.harness.memory.retrieve("owner", "Amber").hits)

    def test_bm25_explicit_offline_snapshot_is_forwarded(self):
        from oscar.memory_indexes import BM25Embedding

        folder = self.root / "bm25"
        folder.mkdir()
        (folder / "english.txt").write_text("synthetic stopwords")
        with patch("oscar.memory_indexes.importlib.import_module") as module:
            adapter = BM25Embedding(model_path=folder, offline=True)
            module.return_value.SparseTextEmbedding.assert_called_once_with(
                model_name="Qdrant/bm25",
                local_files_only=True,
                specific_model_path=str(folder),
            )
            self.assertTrue(
                adapter.identity.endswith(
                    hashlib.sha256((folder / "english.txt").read_bytes()).hexdigest()
                )
            )

    def test_existing_core_read_scope_requires_explicit_local_reenrollment(self):
        h = self.harness()
        node = h.store.get("node", h.node_id)
        h.store.put(
            "node",
            h.node_id,
            {
                **node,
                "scopes": [scope for scope in node["scopes"] if scope != "memory:read"],
            },
        )
        h.close()
        legacy = self.harness()
        self.assertNotIn("memory:read", legacy.store.get("node", legacy.node_id)["scopes"])
        self.assertEqual([], legacy.grid.search("memory"))
        legacy.close()
        approved = self.harness(execution_enrollment_authorized=True)
        self.assertIn("memory:read", approved.store.get("node", approved.node_id)["scopes"])
        self.assertEqual(["memory.recall"], [cap.id for cap in approved.grid.search("memory")])

    def test_close_attempts_both_indexes_and_still_closes_archive(self):
        h = self.harness()
        graph = FixtureIndex()
        h.memory.graph = graph
        with patch.object(h.memory.vector, "close", side_effect=OSError("synthetic close fault")):
            with self.assertRaisesRegex(RuntimeError, "local derived memory close failed"):
                h.close()
        self.assertTrue(graph.closed)
        self.assertTrue(h.memory.closed)


if __name__ == "__main__":
    unittest.main()
