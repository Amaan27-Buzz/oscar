import json
import os
import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.cloud_state import (
    ARCHIVE_NAME,
    IDENTITY_NAME,
    MANIFEST_NAME,
    STATE_NAME,
    DataDirectoryLock,
    backup_state,
    initialize_identity,
    restore_state,
    validate_state,
)
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.memory_fabric import MemoryFabric
from oscar.storage import StateConflict, Store


class CloudStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        with DataDirectoryLock(self.data):
            initialize_identity(self.data, "test-cloud-core", initialize=True)

    def test_explicit_initialization_and_matching_canonical_identity(self):
        with DataDirectoryLock(self.data):
            self.assertEqual("test-cloud-core", initialize_identity(self.data, "test-cloud-core"))
            with self.assertRaises(StateConflict):
                initialize_identity(self.data, "other-cloud-core")
        store = Store(self.data / STATE_NAME)
        self.addCleanup(store.close)
        self.assertEqual([], store.all("node"))
        self.assertEqual([], store.all("policy"))
        store.put("cloud_identity", "core", {"id": "different-core"})
        with self.assertRaises(StateConflict):
            validate_state(self.data)

    def test_incomplete_and_nonempty_volumes_never_silently_reinitialize(self):
        empty = self.root / "empty"
        with DataDirectoryLock(empty):
            with self.assertRaises(StateConflict):
                initialize_identity(empty, "explicit-core")
            (empty / "unknown-content").write_text("preserve", encoding="utf-8")
            with self.assertRaises(StateConflict):
                initialize_identity(empty, "explicit-core", initialize=True)
        (self.data / ARCHIVE_NAME).unlink()
        with self.assertRaises(StateConflict):
            initialize_identity(self.data, "test-cloud-core", initialize=True)
        self.assertFalse((self.data / ARCHIVE_NAME).exists())

    def test_single_writer_and_backup_refuse_running_core(self):
        with DataDirectoryLock(self.data):
            with self.assertRaises(StateConflict):
                with DataDirectoryLock(self.data):
                    self.fail("a second Core acquired same data directory")
            with self.assertRaises(StateConflict):
                backup_state(self.data, self.root / "backup")
        with DataDirectoryLock(self.data):
            self.assertEqual("test-cloud-core", validate_state(self.data))

    def test_archive_schema_rejects_future_version_without_modification(self):
        path = self.root / "future.sqlite"
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("PRAGMA user_version=900")
        with self.assertRaises(ValueError):
            EventArchive(path)
        with closing(sqlite3.connect(path)) as connection:
            self.assertEqual(900, connection.execute("PRAGMA user_version").fetchone()[0])
            self.assertEqual([], connection.execute("SELECT name FROM sqlite_master").fetchall())

    def test_backup_restore_real_archive_retrieval_and_all_durable_state(self):
        archive = EventArchive(self.data / ARCHIVE_NAME)
        self.addCleanup(archive.close)
        event = SourceEvent("synthetic-owner", "Project aurora uses SQLite", "test", time())
        archive.append(event, retain_authorized=True)
        memory = MemoryWriter(archive).retain(
            (event.id,), event.content, "semantic", retain_authorized=True, inferred=False
        )
        store = Store(self.data / STATE_NAME)
        store.put("executive_worker", "worker", {"id": "worker", "enabled": True})
        store.put("executive_goal", "schedule", {"id": "schedule", "next_at": 12345})
        store.put("dedup-proof", "action", {"state": "uncertain"})
        workspace = self.data / "workspace"
        workspace.mkdir()
        (workspace / "receipt-wal").write_bytes(b"retained exact artifact")
        store.close()
        archive.close()
        backup = self.root / "backup"
        backup_state(self.data, backup)
        restored = self.root / "restored"
        restore_state(backup, restored)
        self.assertEqual("test-cloud-core", validate_state(restored))
        self.assertFalse((restored / MANIFEST_NAME).exists())
        self.assertEqual(
            b"retained exact artifact", (restored / "workspace/receipt-wal").read_bytes()
        )
        archive = EventArchive(restored / ARCHIVE_NAME)
        self.addCleanup(archive.close)
        self.assertEqual(event.content, archive.event(event.id).content)
        self.assertEqual([memory.id], archive.fts("synthetic-owner", "aurora"))
        recall = MemoryFabric(archive).retrieve("synthetic-owner", "Project aurora")
        self.assertTrue(recall.hits)
        self.assertIn("qdrant", " ".join(recall.unavailable).lower())
        store = Store(restored / STATE_NAME)
        self.addCleanup(store.close)
        self.assertEqual(12345, store.get("executive_goal", "schedule")["next_at"])
        self.assertEqual("uncertain", store.get("dedup-proof", "action")["state"])

    def test_real_process_crash_keeps_commits_rolls_back_transaction_and_releases_lock(self):
        script = """
import os, sys
from pathlib import Path
from time import time
from oscar.cloud_state import DataDirectoryLock, STATE_NAME, ARCHIVE_NAME
from oscar.storage import Store
from oscar.event_archive import EventArchive, SourceEvent
with DataDirectoryLock(Path(sys.argv[1])):
    store = Store(Path(sys.argv[1]) / STATE_NAME)
    archive = EventArchive(Path(sys.argv[1]) / ARCHIVE_NAME)
    store.put('proof', 'committed', {'value': 'durable'})
    archive.append(SourceEvent('synthetic', 'Committed before crash', 'test', time(),
                               id='crash-event'), retain_authorized=True)
    store.db.execute('BEGIN IMMEDIATE')
    store.put('proof', 'uncommitted', {'value': 'must roll back'})
    os._exit(23)
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.data)], timeout=20)
        self.assertEqual(23, result.returncode)
        with DataDirectoryLock(self.data):
            self.assertEqual("test-cloud-core", validate_state(self.data))
        backup = self.root / "crash-backup"
        backup_state(self.data, backup)
        restored = self.root / "crash-restored"
        restore_state(backup, restored)
        store = Store(restored / STATE_NAME)
        self.addCleanup(store.close)
        self.assertEqual("durable", store.get("proof", "committed")["value"])
        with self.assertRaises(KeyError):
            store.get("proof", "uncommitted")
        archive = EventArchive(restored / ARCHIVE_NAME)
        self.addCleanup(archive.close)
        self.assertEqual("Committed before crash", archive.event("crash-event").content)

    def _scheduled_file(self):
        due = time() + 600
        with DataDirectoryLock(self.data):
            with Harness(
                self.data / STATE_NAME,
                self.data / "workspace",
                Path("config/development-models.json"),
            ) as harness:
                worker = harness.executive.worker(
                    "Synthetic recovery proof",
                    [(harness.node_id, "files.write")],
                    ("files:write",),
                    owner_authorized=True,
                )
                goal = harness.executive.propose(
                    worker,
                    "Write synthetic recovery receipt",
                    [
                        {
                            "id": "receipt",
                            "intent": asdict(
                                Intent("Write proof", "file_write", "proof.txt", "one mutation")
                            ),
                            "depends_on": [],
                            "node_id": harness.node_id,
                            "capability_id": "files.write",
                        }
                    ],
                    start_at=due,
                )
                harness.executive.accept(goal["id"], goal["review_digest"], owner_authorized=True)
        return due, goal["id"]

    def _run_scheduled_process(self, data, due, crash=False):
        script = """
import os, sys
from pathlib import Path
from oscar.cloud_state import DataDirectoryLock, STATE_NAME
from oscar.harness import Harness
data = Path(sys.argv[1])
due = float(sys.argv[2])
crash = sys.argv[3] == 'True'
with DataDirectoryLock(data):
    with Harness(data / STATE_NAME, data / 'workspace',
                 Path('config/development-models.json'), clock=lambda: due - 1) as h:
        # Stop the automatic loop so the deliberate crash is placed after actual I/O.
        h.executive.close()
        h.executive.stop.clear()
        if crash:
            original = h.dispatcher.executors['files.write']
            def uncertain(action, cancellation):
                original(action, cancellation)
                with (data / 'mutation-count').open('ab') as receipt:
                    receipt.write(b'once\\n')
                    receipt.flush()
                    os.fsync(receipt.fileno())
                os._exit(24)
            h.dispatcher.executors['files.write'] = uncertain
        h.grid.clock = lambda: due + 1
        h.executive.tick()
"""
        return subprocess.run(
            [sys.executable, "-c", script, str(data), str(due), str(crash)],
            capture_output=True,
            timeout=25,
        )

    def test_restored_real_worker_schedule_executes_once_across_process_restarts(self):
        due, goal_id = self._scheduled_file()
        backup = self.root / "scheduled-backup"
        restored = self.root / "scheduled-restored"
        backup_state(self.data, backup)
        restore_state(backup, restored)
        for _ in range(2):
            result = self._run_scheduled_process(restored, due)
            self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(b"one mutation", (restored / "workspace/proof.txt").read_bytes())
        store = Store(restored / STATE_NAME)
        self.addCleanup(store.close)
        self.assertEqual(1, len(store.all("task")))
        self.assertEqual("verified", store.all("task")[0]["state"])
        self.assertEqual("completed", store.get("executive_goal", goal_id)["state"])

    def test_real_mutation_then_process_death_never_automatically_replays(self):
        due, _ = self._scheduled_file()
        crashed = self._run_scheduled_process(self.data, due, crash=True)
        self.assertEqual(24, crashed.returncode, crashed.stderr.decode())
        restarted = self._run_scheduled_process(self.data, due + 180)
        self.assertEqual(0, restarted.returncode, restarted.stderr.decode())
        self.assertEqual(b"once\n", (self.data / "mutation-count").read_bytes())
        store = Store(self.data / STATE_NAME)
        self.addCleanup(store.close)
        self.assertEqual(1, len(store.all("task")))
        self.assertEqual("blocked", store.all("task")[0]["state"])
        self.assertEqual(1, len(store.all("planned_action")))
        self.assertEqual("started", store.db.execute("SELECT state FROM dedup").fetchone()[0])

    def test_corrupt_backup_and_existing_restore_destination_are_preserved(self):
        backup = self.root / "backup"
        backup_state(self.data, backup)
        with self.assertRaises(FileExistsError):
            restore_state(backup, self.data)
        destination = self.root / "restored"
        (backup / IDENTITY_NAME).write_text("corrupt", encoding="utf-8")
        with self.assertRaises(ValueError):
            restore_state(backup, destination)
        self.assertFalse(destination.exists())
        self.assertEqual("test-cloud-core", validate_state(self.data))

    def test_manifest_inventory_and_nested_backup_rejected(self):
        with self.assertRaises(ValueError):
            backup_state(self.data, self.data / "recursive-backup")
        backup = self.root / "backup"
        backup_state(self.data, backup)
        manifest_path = backup / MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["../escape"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            restore_state(backup, self.root / "restored")
        self.assertFalse((self.root / "escape").exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink API unavailable")
    def test_backup_does_not_follow_external_symlinks(self):
        external = self.root / "private"
        external.write_text("private", encoding="utf-8")
        try:
            (self.data / "external").symlink_to(external)
        except OSError:
            self.skipTest("host cannot create symlinks")
        with self.assertRaises(StateConflict):
            backup_state(self.data, self.root / "backup")
        self.assertEqual("private", external.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
