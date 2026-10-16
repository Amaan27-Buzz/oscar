import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from time import monotonic, sleep

from oscar.capabilities import Cancellation
from oscar.contracts import new_id
from oscar.event_archive import EventArchive
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.memory_fabric import MemoryFabric
from oscar.mobile import Mobile
from oscar.perception import PerceptionSource
from oscar.policy import PersonalPolicy
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
from oscar.world_model import ObservationKind
from oscar.world_runtime import WorldRuntime
from tests.support import Rig


class WorldRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.archive = EventArchive(self.r.root / "archive.sqlite")
        self.r.runtime.memory = MemoryFabric(self.archive)
        self.world = WorldRuntime(self.r.runtime, self.r.files)
        self.r.runtime.world = self.world
        self.source = PerceptionSource(
            "grid-source",
            ("core",),
            ("grid.state",),
            (ObservationKind.DEVICE,),
            simulated=False,
            perceive=True,
        )

    def tearDown(self):
        self.world.close()
        self.archive.close()
        self.r.close()

    def test_normal_runtime_query_and_core_source_lifecycle(self):
        self.world.configure_source(self.source, "grid", "core", owner_authorized=True)
        self.assertEqual(1, self.world.tick()["polled"])
        result = self.r.runtime.current("core", "grid.state")
        self.assertEqual("world", result["controller_route"])
        self.assertEqual(
            "online", json.loads(result["current"]["observations"][0]["value"])[0]["status"]
        )
        self.r.grid.disconnect("test-node")
        self.r.clock.now += 6
        self.world.tick()
        state = self.world.world.resolve("core", "grid.state")
        self.assertEqual("offline", json.loads(state.value)[0]["status"])
        self.r.grid.advertise(self.r.session, self.r.caps)
        self.r.clock.now += 6
        self.world.tick()
        self.assertTrue(self.world.snapshot()["sources"][0]["operational"])

    def test_task_signals_are_relationship_scoped_and_content_free(self):
        source = PerceptionSource(
            "tasks-source", ("core",), ("tasks.state",), (ObservationKind.TASK,), perceive=True
        )
        self.world.configure_source(source, "tasks", "core", owner_authorized=True)
        task = self.r.runtime.create(Intent("2 + 3"))
        self.r.store.put("task_relationship", "foreign", {"id": "foreign", "relationship": "other"})
        self.world.tick()
        data = json.loads(self.world.world.resolve("core", "tasks.state").value)
        self.assertEqual([{"id": task.id, "state": "planned"}], data)
        self.assertNotIn("2 + 3", str(data))

    def test_failed_source_does_not_block_healthy_source_and_backoff_is_bounded(self):
        self.world.configure_source(self.source, "grid", "core", owner_authorized=True)
        source = PerceptionSource(
            "file-source", ("project",), ("file.state",), (ObservationKind.PROJECT,), perceive=True
        )
        self.world.configure_source(
            source,
            "files",
            "project",
            owner_authorized=True,
            selected_paths={"file.state": "absent.txt"},
        )
        self.world.sentry.configure(
            SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, ("file-source",)),
            owner_authorized=True,
        )
        counts = self.world.tick()
        self.assertEqual(1, counts["failed"])
        self.assertEqual(1, counts["polled"])
        self.assertEqual("current", self.world.world.resolve("core", "grid.state").state)
        self.assertFalse(self.world.snapshot()["sources"][1]["operational"])
        self.r.files.write(
            "absent.txt",
            "restored",
            Cancellation(self.r.store, self.r.runtime.create(Intent("2 + 3")).id),
        )
        self.r.clock.now += 11
        self.world.tick()
        self.assertEqual("restored", self.world.world.resolve("project", "file.state").value)

    def test_awareness_off_does_not_acquire_selected_files(self):
        source = PerceptionSource(
            "file-source",
            ("project",),
            ("file.state",),
            (ObservationKind.PROJECT,),
            perceive=True,
            retain=True,
        )
        self.world.configure_source(
            source,
            "files",
            "project",
            owner_authorized=True,
            selected_paths={"file.state": "absent.txt"},
        )
        self.assertEqual(0, self.world.tick()["failed"])
        self.assertEqual("unknown", self.world.world.resolve("project", "file.state").state)
        self.assertEqual(
            0, self.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )

    def test_revoke_during_acquisition_discards_output_and_does_not_reconnect(self):
        self.world.configure_source(self.source, "grid", "core", owner_authorized=True)
        factory = self.world._adapter

        def adapter(row):
            result = factory(row)
            original = result.source.retrieve

            def retrieve(query, scope):
                observations = original(query, scope)
                self.world.fabric.revoke(row["id"], owner_authorized=True)
                return observations

            result.source.retrieve = retrieve
            return result

        self.world._adapter = adapter
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertEqual("unknown", self.world.world.resolve("core", "grid.state").state)
        self.r.clock.now += 301
        self.assertEqual(1, self.world.tick()["failed"])

    def test_background_shutdown_releases_lease_and_never_leaves_source_connected(self):
        self.world.configure_source(self.source, "grid", "core", owner_authorized=True)
        self.world.start()
        deadline = monotonic() + 3
        while (
            monotonic() < deadline
            and self.world.world.resolve("core", "grid.state").state != "current"
        ):
            sleep(0.01)
        self.assertEqual("current", self.world.world.resolve("core", "grid.state").state)
        self.world.close()
        self.assertFalse(self.world.thread.is_alive())
        self.assertEqual("unavailable", self.world.world.resolve("core", "grid.state").state)

    def test_persistent_cli_sources_resume_and_current_query_uses_controller(self):
        args = [
            sys.executable,
            "-m",
            "oscar",
            "--state",
            str(self.r.root / "cli.sqlite"),
            "--workspace",
            str(self.r.root / "cli-workspace"),
        ]
        first = subprocess.run(
            [*args, "watch-core", "grid"], check=True, capture_output=True, text=True, timeout=20
        )
        self.assertTrue(json.loads(first.stdout)["sources"][0]["configured"])
        second = subprocess.run(
            [*args, "world", "--entity", "core", "--key", "grid.state"],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        result = json.loads(second.stdout)
        self.assertEqual("world", result["controller_route"])
        self.assertEqual("current", result["current"]["state"])

    def test_lost_runner_cannot_disconnect_or_overwrite_successor(self):
        self.world.configure_source(self.source, "grid", "core", owner_authorized=True)
        successor = WorldRuntime(self.r.runtime, self.r.files)
        factory = self.world._adapter

        def adapter(row):
            result = factory(row)
            original = result.source.retrieve

            def retrieve(query, scope):
                observations = original(query, scope)
                self.r.clock.now += 31
                successor.tick()
                return observations

            result.source.retrieve = retrieve
            return result

        self.world._adapter = adapter
        self.assertEqual(1, self.world.tick()["failed"])
        self.assertEqual("current", successor.world.resolve("core", "grid.state").state)
        self.assertTrue(successor.snapshot()["sources"][0]["operational"])
        self.world.close()
        self.assertEqual("current", successor.world.resolve("core", "grid.state").state)
        successor.close()

    def test_trigger_only_filters_files_before_acquisition(self):
        source = PerceptionSource(
            "file-source",
            ("project",),
            ("selected", "excluded"),
            (ObservationKind.PROJECT,),
            perceive=True,
        )
        self.world.configure_source(
            source,
            "files",
            "project",
            owner_authorized=True,
            selected_paths={"selected": "selected.txt", "excluded": "never.txt"},
        )
        (self.r.files.root / "selected.txt").write_text("safe fixture")
        self.world.sentry.configure(
            SentrySettings(
                AwarenessMode.TRIGGER_ONLY, SentryState.AWARE, ("file-source",), ("selected",)
            ),
            owner_authorized=True,
        )
        read = self.r.files.read
        calls = []

        def inspect(path):
            calls.append(path)
            return read(path)

        self.r.files.read = inspect
        self.assertEqual(1, self.world.tick()["polled"])
        self.assertEqual(["selected.txt"], calls)

    def test_transient_sqlite_lock_does_not_kill_background_loop(self):
        tick = self.world.tick
        calls = []

        def locked_once():
            calls.append(1)
            if len(calls) == 1:
                raise sqlite3.OperationalError("database is locked")
            return tick()

        self.world.tick = locked_once
        self.world.start()
        deadline = monotonic() + 4
        while monotonic() < deadline and len(calls) < 2:
            sleep(0.01)
        self.assertGreaterEqual(len(calls), 2)
        self.assertTrue(self.world.thread.is_alive())

    def test_harness_owns_one_archive_and_closes_background_runtime(self):
        with Harness(
            self.r.root / (new_id() + ".sqlite"),
            self.r.root / "workspace2",
            Path("config/development-models.json"),
        ) as h:
            self.assertIs(h.archive, h.runtime.memory.archive)
            self.assertIs(h.archive, h.runtime.world.world.archive)
            thread = h.runtime.world.thread
        self.assertFalse(thread.is_alive())

    def test_store_close_itself_stops_owned_threads_and_archive_handles(self):
        h = Harness(
            self.r.root / "close.sqlite",
            self.r.root / "close-workspace",
            Path("config/development-models.json"),
        )
        h.store.close()
        self.assertFalse(h.world.thread.is_alive())
        h.close()

    def test_surface_current_query_requires_its_own_grant(self):
        self.world.configure_source(self.source, "grid", "core", owner_authorized=True)
        core = Mobile(self.r.runtime, PersonalPolicy(self.r.store), self.r.transports)
        scopes = ("heartbeat", "mobile:connect", "mobile:inspect")
        self.r.grid.register(Node("mobile-reader", NodeRole.MOBILE, (*scopes, "world:read")))
        session = self.r.grid.pair("mobile-reader", scopes)
        request = {
            "version": 1,
            "request_id": "query",
            "operation": "world",
            "payload": {"entity_id": "core", "key": "grid.state"},
        }
        with self.assertRaises(PermissionError):
            core.request(session, request)
        session = self.r.grid.pair("mobile-reader", (*scopes, "world:read"))
        self.assertEqual("current", core.request(session, request)["current"]["state"])
        self.r.grid.revoke("mobile-reader")
        with self.assertRaises(PermissionError):
            core.request(session, request)

    def test_expiry_maintenance_and_single_runner_lease(self):
        from dataclasses import replace

        source = replace(self.source, retain=True, retention_seconds=1)
        self.world.configure_source(source, "grid", "core", owner_authorized=True)
        self.world.tick()
        second = WorldRuntime(self.r.runtime, self.r.files)
        self.assertEqual(0, second.tick()["polled"])
        self.world.close()
        self.assertEqual(1, second.tick()["polled"])
        second.close()
        with self.archive.db:
            self.archive.db.execute(
                "UPDATE archive_events SET payload=json_set(payload,'$.expires_at',0)"
            )
        self.world.next_maintenance = 0
        self.world.tick()
        self.assertGreater(
            self.archive.db.execute(
                "SELECT count(*) FROM archive_events WHERE forgotten=1"
            ).fetchone()[0],
            0,
        )
