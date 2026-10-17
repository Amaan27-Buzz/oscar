"""Core-owned bounded perception polling and canonical retention maintenance."""

import json
import sqlite3
from functools import partial
from threading import Event, RLock, Thread
from typing import TYPE_CHECKING, Any

from .capabilities import ScopedFiles
from .context_sources import FileContextSource
from .continuity import ContextObservation, LiveContextSource, StateContextSource
from .contracts import Epistemic, Task, new_id
from .freshness import Authority, SourceRef
from .perception import PerceptionFabric, PerceptionSource
from .perception_adapters import ContextPerceptionAdapter
from .policy import PersonalPolicy
from .sentry import AwarenessMode, SentryRuntime
from .storage import StateConflict
from .world_model import ObservationKind, WorldModel, reference

if TYPE_CHECKING:
    from .runtime import Runtime


class TaskContextSource:
    id = "native-task-state"

    def __init__(self, runtime: "Runtime"):
        self.runtime = runtime

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.runtime.relationship_id:
            raise PermissionError("task relationship mismatch")
        store = self.runtime.store
        ids = {r["id"] for r in store.all("task_relationship") if r["relationship"] == scope}
        tasks = [{"id": t["id"], "state": t["state"]} for t in store.all("task") if t["id"] in ids][
            -16:
        ]
        return (
            ContextObservation(
                "tasks.state",
                json.dumps(tasks),
                scope,
                SourceRef(
                    "local://core/tasks", Authority.LIVE_API, "local", self.runtime.grid.clock(), 10
                ),
                Epistemic.KNOWN,
            ),
        )


class WorldRuntime:
    def __init__(self, runtime: "Runtime", files: ScopedFiles):
        if runtime.memory is None:
            raise ValueError("World Runtime requires the canonical Event Archive")
        self.runtime, self.store, self.files = runtime, runtime.store, files
        self.world = WorldModel(
            self.store,
            runtime.memory.archive,
            runtime.relationship_id,
            clock=lambda: runtime.grid.clock(),
        )
        self.fabric = PerceptionFabric(self.world, PersonalPolicy(self.store))
        self.sentry = SentryRuntime(self.fabric, runtime.memory)
        self.instance = new_id()
        self.stop_event, self.wake = Event(), Event()
        self.lock = RLock()
        self.thread: Thread | None = None
        self.next_maintenance = 0.0
        self.health = "idle"
        self.tasks_changed = Event()
        self.store.task_resources.add(self)

    def task_transitioned(self, task: Task) -> None:
        self.tasks_changed.set()
        self.wake.set()

    def configure_source(
        self,
        source: PerceptionSource,
        adapter: str,
        entity_id: str,
        *,
        owner_authorized: bool,
        interval_seconds: int = 5,
        selected_paths: dict[str, str] | None = None,
    ) -> int:
        if not owner_authorized:
            raise PermissionError("source setup requires trusted owner authority")
        reference(entity_id)
        if (
            adapter not in {"grid", "tasks", "files"}
            or type(interval_seconds) is not int
            or not 1 <= interval_seconds <= 3600
            or entity_id not in source.entities
        ):
            raise ValueError("supported bounded source subscription required")
        paths = selected_paths or {}
        if adapter == "files":
            if not 1 <= len(paths) <= 16 or set(paths) != set(source.keys):
                raise ValueError("exact selected file scope required")
            for key, path in paths.items():
                reference(key)
                self.files.parts(path) if hasattr(self.files, "parts") else reference(path)
        elif paths or source.keys != (("grid.state",) if adapter == "grid" else ("tasks.state",)):
            raise ValueError("source keys do not match native adapter")
        self.world.safe(json.dumps(paths))
        with self.lock:
            epoch = self.fabric.register(source, owner_authorized=True)
            self.store.put(
                "perception_poll",
                self.world.source_key(source.id),
                {
                    "id": source.id,
                    "relationship": self.world.relationship,
                    "epoch": epoch,
                    "adapter": adapter,
                    "entity_id": entity_id,
                    "paths": paths,
                    "interval": interval_seconds,
                    "next_at": 0.0,
                    "failures": 0,
                    "state": "configured",
                    "last_success": None,
                },
            )
        self.wake.set()
        return epoch

    def _adapter(self, row: dict[str, Any]) -> ContextPerceptionAdapter:
        kind = row["adapter"]
        source: LiveContextSource
        if kind == "grid":
            source = StateContextSource(
                self.store, self.runtime.grid.nodes, self.world.relationship, clock=self.world.clock
            )
            observation_kind = ObservationKind.DEVICE
        elif kind == "tasks":
            source = TaskContextSource(self.runtime)
            observation_kind = ObservationKind.TASK
        elif kind == "files":
            source = FileContextSource(
                self.files, self.world.relationship, row["paths"], clock=self.world.clock
            )
            observation_kind = ObservationKind.PROJECT
        else:
            raise ValueError("unregistered perception adapter")
        return ContextPerceptionAdapter(
            self.fabric, source, row["id"], row["entity_id"], observation_kind
        )

    def _guard(self, generation: int | None = None) -> None:
        lease = self.store.get("world_runner", self.world.relationship)
        if lease["owner"] != self.instance or lease["until"] <= self.world.clock():
            raise StateConflict("perception runner lease lost")
        if generation is not None and self.sentry.configuration()[1] != generation:
            raise PermissionError("Sentry configuration changed during acquisition")

    def _save_poll(self, row: dict[str, Any]) -> None:
        with self.store.transaction():
            self._guard()
            current = self.store.get("perception_poll", self.world.source_key(row["id"]))
            if current["epoch"] != row["epoch"]:
                raise StateConflict("source schedule generation changed")
            self.store.put("perception_poll", self.world.source_key(row["id"]), row)

    def tick(self) -> dict[str, int]:
        with self.lock:
            now = self.world.clock()
            with self.store.transaction():
                try:
                    lease = self.store.get("world_runner", self.world.relationship)
                except KeyError:
                    lease = {}
                if lease.get("until", 0) > now and lease.get("owner") != self.instance:
                    return {"polled": 0, "failed": 0, "expired": 0}
                if lease.get("owner") != self.instance or lease.get("until", 0) - now <= 10:
                    self.store.put(
                        "world_runner",
                        self.world.relationship,
                        {"owner": self.instance, "until": now + 30},
                    )
            counts = {"polled": 0, "failed": 0, "expired": 0}
            tasks_changed = self.tasks_changed.is_set()
            self.tasks_changed.clear()
            rows = [
                r
                for r in self.store.all("perception_poll")
                if r["relationship"] == self.world.relationship
                and (r["next_at"] <= now or tasks_changed and r["adapter"] == "tasks")
            ]
            for row in sorted(rows, key=lambda r: r["next_at"])[:8]:
                try:
                    source = self.world.source(row["id"])
                    if source["epoch"] != row["epoch"] or not source["perceive"]:
                        raise PermissionError("source revoked or reconfigured")
                    settings, generation = self.sentry.configuration()
                    is_file = row["adapter"] == "files"
                    paths = row["paths"]
                    if is_file and settings.mode == AwarenessMode.TRIGGER_ONLY:
                        paths = {k: v for k, v in paths.items() if k in settings.trigger_keys}
                    if is_file and (
                        settings.mode == AwarenessMode.MANUAL
                        or row["id"] not in settings.source_ids
                        or not paths
                    ):
                        self.fabric.disconnect(row["id"], row["epoch"], guard=self._guard)
                        row.update(state="paused", next_at=now + row["interval"])
                        self._save_poll(row)
                        continue
                    self.fabric.connect(
                        row["id"], row["epoch"], lease_seconds=30, guard=self._guard
                    )
                    adapter = self._adapter({**row, "paths": paths})
                    guard = partial(self._guard, generation=generation if is_file else None)
                    adapter.acquisition_guard = guard
                    if is_file:
                        adapter.observer = partial(self.sentry.observe, guard=guard)
                    adapter.poll()
                    counts["polled"] += 1
                    row.update(
                        state="operational",
                        last_success=now,
                        failures=0,
                        next_at=now + row["interval"],
                    )
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    PermissionError,
                    StateConflict,
                    sqlite3.Error,
                ):
                    counts["failed"] += 1
                    try:
                        self.fabric.disconnect(row["id"], row["epoch"], guard=self._guard)
                    except StateConflict:
                        return counts
                    except (KeyError, ValueError, PermissionError):
                        pass
                    failures = min(row["failures"] + 1, 10)
                    row.update(
                        state="unavailable",
                        failures=failures,
                        next_at=now + min(300, row["interval"] * 2**failures),
                    )
                try:
                    self._save_poll(row)
                except StateConflict:
                    return counts
            self._guard()
            if now >= self.next_maintenance:
                counts["expired"] = self.world.archive.purge_expired_events(
                    self.world.relationship, limit=128
                )
                self.world.purge()
                self.next_maintenance = now + 30
            return counts

    def snapshot(self) -> dict[str, Any]:
        now = self.world.clock()
        sources = []
        for row in self.store.all("perception_poll"):
            if row["relationship"] != self.world.relationship:
                continue
            source = self.world.source(row["id"])
            connected = bool(
                source["perceive"]
                and source["epoch"] == row["epoch"]
                and source["connected_until"] > now
            )
            sources.append(
                {
                    "id": row["id"],
                    "configured": True,
                    "connected": connected,
                    "operational": connected and row["state"] == "operational",
                    "state": row["state"] if connected else "unavailable",
                    "simulated": source["simulated"],
                    "last_success": row["last_success"],
                }
            )
        return {
            "version": 1,
            "awareness": self.sentry.settings().mode.value,
            "environmental_capture": "unavailable",
            "sources": sources,
            "running": bool(self.thread and self.thread.is_alive()),
            "health": self.health,
        }

    def start(self) -> None:
        if self.thread is not None:
            raise StateConflict("World Runtime already started")
        self.thread = Thread(target=self._run, name="oscar-world", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        failures = 0
        try:
            while not self.stop_event.is_set():
                try:
                    counts = self.tick()
                    self.health = "degraded" if counts["failed"] else "operational"
                    failures = 0
                except (OSError, ValueError, StateConflict, sqlite3.OperationalError):
                    # No source payloads or provider exceptions enter diagnostic history.
                    failures += 1
                    self.health = "degraded"
                    if failures >= 5:
                        self.health = "unavailable"
                        return
                    self.stop_event.wait(min(30, 2**failures))
                except sqlite3.DatabaseError:
                    self.health = "unavailable"
                    return
                self.world.archive.close_thread()
                self.wake.wait(0.5)
                self.wake.clear()
        finally:
            self.world.archive.close_thread()

    def close(self) -> None:
        self.stop_event.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                raise StateConflict("perception acquisition has not stopped")
        with self.store.transaction():
            try:
                lease = self.store.get("world_runner", self.world.relationship)
            except KeyError:
                lease = {}
            if lease.get("owner") == self.instance:
                for row in self.store.all("perception_poll"):
                    if row["relationship"] != self.world.relationship:
                        continue
                    try:
                        source = self.world.source(row["id"])
                        if source["epoch"] == row["epoch"]:
                            self.store.put(
                                "perception_source",
                                self.world.source_key(row["id"]),
                                {**source, "connected_until": 0.0},
                            )
                            self.store.put(
                                "perception_poll",
                                self.world.source_key(row["id"]),
                                {**row, "next_at": 0.0},
                            )
                    except (KeyError, ValueError):
                        continue
                self.store.delete("world_runner", self.world.relationship)
