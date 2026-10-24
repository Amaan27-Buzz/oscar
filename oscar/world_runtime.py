"""Core-owned bounded perception polling and canonical retention maintenance."""

import json
import math
import sqlite3
from functools import partial
from threading import Event, RLock, Thread
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .ambient import (
    CALENDAR_CAPABILITIES,
    WEATHER_URL,
    CalendarContextSource,
    ClockContextSource,
    WeatherContextSource,
    calendar_conflicts,
)
from .capabilities import ScopedFiles
from .connectors import ConnectorError
from .context_sources import FileContextSource
from .continuity import ContextObservation, LiveContextSource, StateContextSource
from .contracts import Epistemic, Task, new_id
from .freshness import Authority, SourceRef
from .perception import PerceptionFabric, PerceptionSource
from .perception_adapters import ContextPerceptionAdapter
from .policy import PersonalPolicy
from .sentry import AwarenessMode, SentryRuntime
from .sentry_delivery import SentryDelivery
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
        self.delivery = SentryDelivery(self.sentry)
        self.instance = new_id()
        self.stop_event, self.wake = Event(), Event()
        self.lock = RLock()
        self.thread: Thread | None = None
        self.next_maintenance = 0.0
        self.health = "idle"
        self.tasks_changed = Event()
        self.weather_cache: dict[str, dict[str, Any]] = {}
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
        native_config: dict[str, Any] | None = None,
    ) -> int:
        if not owner_authorized:
            raise PermissionError("source setup requires trusted owner authority")
        reference(entity_id)
        if (
            adapter not in {
                "grid", "tasks", "files", "time", "calendar", "weather", "android",
                "connected_tasks",
            }
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
        elif adapter in {"time", "calendar", "weather", "android", "connected_tasks"}:
            if native_config is None or paths:
                raise ValueError("reviewed native source configuration required")
            reviewed = self.review_source(native_config)
            if source.keys != (reviewed["key"],) or source.kinds != (
                ObservationKind(reviewed["kind"]),
            ):
                raise ValueError("source contract differs from reviewed native source")
        elif paths or source.keys != (("grid.state",) if adapter == "grid" else ("tasks.state",)):
            raise ValueError("source keys do not match native adapter")
        self.world.safe(json.dumps(paths))
        self.world.safe(json.dumps(native_config))
        with self.store.transaction():
            if native_config is not None:
                self.review_source(native_config)
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
                    "native_config": native_config,
                    "interval": interval_seconds,
                    "next_at": 0.0,
                    "failures": 0,
                    "state": "configured",
                    "last_success": None,
                },
            )
        self.wake.set()
        return epoch

    def review_source(self, value: dict[str, Any]) -> dict[str, Any]:
        common = {"id", "adapter", "entity_id", "interval_seconds", "retain", "retention_seconds"}
        adapter = value.get("adapter")
        extras = {
            "time": {"timezone"},
            "calendar": {"account_id", "account_generation", "calendar_id", "horizon_seconds"},
            "connected_tasks": {"account_id", "account_generation", "task_list_id"},
            "weather": {"latitude", "longitude", "place"},
            "android": {"node_id", "session_id", "packages"},
        }
        if adapter not in extras or set(value) != common | extras[adapter]:
            raise ValueError("exact native context configuration required")
        for key in ("id", "entity_id"):
            reference(value[key])
        if (
            type(value["interval_seconds"]) is not int
            or not 5 <= value["interval_seconds"] <= 3600
            or type(value["retain"]) is not bool
            or type(value["retention_seconds"]) is not int
            or not 1 <= value["retention_seconds"] <= 604800
        ):
            raise ValueError("bounded poll interval and independent retention required")
        try:
            self.world.source(value["id"])
        except KeyError:
            pass
        else:
            raise ValueError("source identifier already registered")
        material = {"configuration": value, "perceive": True, "act": False}
        if adapter == "connected_tasks":
            from .task_context import review

            return material | review(self, value)
        if adapter == "android":
            from .phone_context import review

            return material | review(self, value)
        if adapter == "weather":
            for key, limit in (("latitude", 90), ("longitude", 180)):
                coordinate = value[key]
                if (
                    type(coordinate) not in {int, float}
                    or not math.isfinite(coordinate)
                    or not -limit <= coordinate <= limit
                    or round(coordinate, 4) != coordinate
                ):
                    raise ValueError("finite coordinates with at most four decimals required")
            if (
                value["interval_seconds"] < 600
                or not isinstance(value["place"], str)
                or not 1 <= len(value["place"].strip()) <= 80
                or not value["place"].isprintable()
            ):
                raise ValueError("explicit place and weather interval >= ten minutes required")
            return material | {
                "key": "weather.state",
                "kind": "environment",
                "ttl_seconds": 3600,
                "fields": [
                    "place",
                    "latitude",
                    "longitude",
                    "updated_at",
                    "forecast_time",
                    "temperature_c",
                    "wind_mps",
                    "humidity_percent",
                ],
                "source": "MET Norway Locationforecast",
                "endpoint": WEATHER_URL,
                "disclosure": "MET Norway receives selected coordinates and Core network address",
                "freshness": "Earlier of provider expiry, retrieval + one hour, forecast hour end",
                "claim": "Provider forecast; no local sensor observation or severe weather alert",
            }
        if adapter == "time":
            try:
                ZoneInfo(value["timezone"])
            except (ZoneInfoNotFoundError, TypeError, ValueError) as error:
                raise ValueError("installed IANA timezone required") from error
            return material | {
                "key": "clock.state",
                "kind": "environment",
                "ttl_seconds": 60,
                "fields": ["datetime", "timezone"],
                "source": "Core system clock",
            }
        if (
            type(value["account_generation"]) is not int
            or type(value["horizon_seconds"]) is not int
            or not 300 <= value["horizon_seconds"] <= 604800
            or not isinstance(value["calendar_id"], str)
            or not 1 <= len(value["calendar_id"]) <= 160
        ):
            raise ValueError("exact account generation and bounded calendar window required")
        h = self.runtime.connections
        if h is None:
            raise PermissionError("connected account source unavailable")
        from .connector_mount import project_accounts
        from .connectors import ConnectionState, endpoint

        project_accounts(h)
        account = h.accounts.check(value["account_id"], value["account_generation"])
        name = CALENDAR_CAPABILITIES.get(account.provider, "")
        matches = [
            (instance, spec)
            for instance in h.connectors.instances.values()
            if instance.account_id == account.id
            and instance.account_generation == account.generation
            and instance.manifest.provider in {"google", "microsoft"}
            for spec in instance.manifest.capabilities
            if spec.name == name and h.connectors.state(instance, spec) == ConnectionState.READY
        ]
        if (
            len(matches) != 1
            or account.provider == "microsoft"
            and value["calendar_id"] != "primary"
        ):
            raise PermissionError("one authorized calendar read binding required")
        instance, spec = matches[0]
        endpoint(
            spec,
            {"path": {"calendarId": value["calendar_id"]}} if account.provider == "google" else {},
        )
        return material | {
            "key": "calendar.state",
            "kind": "schedule",
            "ttl_seconds": spec.freshness_seconds,
            "account_alias": account.alias,
            "account_id": account.id,
            "account_generation": account.generation,
            "provider": account.provider,
            "instance_id": instance.id,
            "service": instance.manifest.id,
            "capability": name,
            "fields": ["id", "summary", "start", "end", "status"]
            if account.provider == "google"
            else ["id", "subject", "start", "end", "isCancelled"],
            "filter": "now through now + horizon_seconds; at most 8 events; pagination explicit",
        }

    def configure_native_source(self, value: dict[str, Any], *, owner_authorized: bool) -> int:
        if not owner_authorized:
            raise PermissionError("source setup requires signed owner authority")
        reviewed = self.review_source(value)
        source = PerceptionSource(
            value["id"],
            (value["entity_id"],),
            (reviewed["key"],),
            (ObservationKind(reviewed["kind"]),),
            simulated=False,
            perceive=True,
            retain=value["retain"],
            act=False,
            retention_seconds=value["retention_seconds"],
        )
        return self.configure_source(
            source,
            value["adapter"],
            value["entity_id"],
            owner_authorized=True,
            interval_seconds=value["interval_seconds"],
            native_config=value,
        )

    def set_source_grants(
        self, identifier: str, value: dict[str, Any], *, owner_authorized: bool
    ) -> int:
        if not owner_authorized:
            raise PermissionError("source grant change requires signed owner authority")
        if set(value) != {"perceive", "retain", "act"} or any(
            type(flag) is not bool for flag in value.values()
        ):
            raise ValueError("separate explicit source grants required")
        with self.store.transaction():
            prior = self.world.source(identifier)
            source = PerceptionSource(
                identifier,
                tuple(prior["entities"]),
                tuple(prior["keys"]),
                tuple(ObservationKind(kind) for kind in prior["kinds"]),
                simulated=prior["simulated"],
                **value,
                retention_seconds=prior["retention_seconds"],
                events_per_minute=prior["events_per_minute"],
            )
            epoch = self.fabric.register(source, owner_authorized=True)
            try:
                row = self.store.get("perception_poll", self.world.source_key(identifier))
            except KeyError:
                pass
            else:
                self.store.put(
                    "perception_poll",
                    self.world.source_key(identifier),
                    {
                        **row,
                        "epoch": epoch,
                        "state": "configured",
                        "next_at": 0.0,
                        "failures": 0,
                        "last_success": None,
                    },
                )
        self.wake.set()
        return epoch

    def source_review(self, identifier: str) -> dict[str, Any]:
        """Lease refreshes are not changes to an owner's reviewed source contract."""
        with self.store.transaction():
            source = self.world.source(identifier)
            material = {
                key: source[key]
                for key in (
                    "id",
                    "relationship",
                    "epoch",
                    "entities",
                    "keys",
                    "kinds",
                    "simulated",
                    "perceive",
                    "retain",
                    "act",
                    "retention_seconds",
                    "events_per_minute",
                    "version",
                )
            }
            try:
                row = self.store.get("perception_poll", self.world.source_key(identifier))
            except KeyError:
                subscription = None
            else:
                subscription = {
                    key: row.get(key)
                    for key in (
                        "adapter",
                        "entity_id",
                        "paths",
                        "native_config",
                        "interval",
                        "epoch",
                    )
                }
            return {"source": material, "subscription": subscription}

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
        elif kind == "time":
            source = ClockContextSource(
                self.world.relationship, row["native_config"]["timezone"], self.world.clock
            )
            observation_kind = ObservationKind.ENVIRONMENT
        elif kind == "weather":
            source = WeatherContextSource(
                self.world.relationship,
                row["native_config"],
                self.world.clock,
                self.weather_cache.setdefault(row["id"], {}),
            )
            observation_kind = ObservationKind.ENVIRONMENT
        elif kind == "connected_tasks":
            from .task_context import ConnectedTaskSource

            source = ConnectedTaskSource(self, row)
            observation_kind = ObservationKind.TASK
        elif kind == "calendar":
            config = row["native_config"]
            h = self.runtime.connections
            if h is None:
                raise PermissionError("connected calendar unavailable")
            from .connector_mount import project_accounts
            from .connectors import ConnectionState

            project_accounts(h)
            account = h.accounts.check(config["account_id"], config["account_generation"])
            matches = [
                instance
                for instance in h.connectors.instances.values()
                if instance.account_id == account.id
                and instance.account_generation == account.generation
                and any(
                    spec.name == CALENDAR_CAPABILITIES.get(account.provider, "")
                    and h.connectors.state(instance, spec) == ConnectionState.READY
                    for spec in instance.manifest.capabilities
                )
            ]
            if len(matches) != 1:
                raise PermissionError("calendar binding unavailable or ambiguous")

            def guard() -> None:
                self._guard()
                h.accounts.check(config["account_id"], config["account_generation"])
                current = self.world.source(row["id"])
                if current["epoch"] != row["epoch"] or not current["perceive"]:
                    raise PermissionError("calendar perception revoked")

            source = CalendarContextSource(
                h.connectors,
                self.world.relationship,
                config
                | {
                    "instance_id": matches[0].id,
                    "provider": account.provider,
                    "capability": CALENDAR_CAPABILITIES.get(account.provider, ""),
                },
                self.world.clock,
                guard,
            )
            observation_kind = ObservationKind.SCHEDULE
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
            for row in self.store.all("perception_poll"):
                if row["relationship"] != self.world.relationship or row["adapter"] not in {
                    "calendar", "connected_tasks"
                }:
                    continue
                try:
                    self._adapter(row)
                except (KeyError, ValueError, PermissionError):
                    counts["failed"] += 1
                    if row["state"] != "unavailable":
                        try:
                            self.fabric.disconnect(row["id"], row["epoch"], guard=self._guard)
                        except PermissionError:
                            continue
                        row.update(state="unavailable", next_at=now + row["interval"])
                        self._save_poll(row)
            from .phone_context import recheck

            recheck(self)
            tasks_changed = self.tasks_changed.is_set()
            self.tasks_changed.clear()
            rows = [
                r
                for r in self.store.all("perception_poll")
                if r["relationship"] == self.world.relationship
                and r["adapter"] != "android"
                and (r["next_at"] <= now or tasks_changed and r["adapter"] == "tasks")
            ]
            for row in sorted(rows, key=lambda r: r["next_at"])[:8]:
                try:
                    source = self.world.source(row["id"])
                    if source["epoch"] != row["epoch"] or not source["perceive"]:
                        raise PermissionError("source revoked or reconfigured")
                    settings, generation = self.sentry.configuration()
                    is_file = row["adapter"] == "files"
                    ambient = row["adapter"] in {"files", "calendar", "weather", "connected_tasks"}
                    paths = row["paths"]
                    if is_file and settings.mode == AwarenessMode.TRIGGER_ONLY:
                        paths = {k: v for k, v in paths.items() if k in settings.trigger_keys}
                    if ambient and (
                        settings.mode == AwarenessMode.MANUAL
                        or row["id"] not in settings.source_ids
                        or is_file
                        and not paths
                        or not is_file
                        and settings.mode == AwarenessMode.TRIGGER_ONLY
                        and {
                            "weather": "weather.state",
                            "calendar": "calendar.state",
                            "connected_tasks": "connected_tasks.state",
                        }[row["adapter"]]
                        not in settings.trigger_keys
                    ):
                        self.fabric.disconnect(row["id"], row["epoch"], guard=self._guard)
                        row.update(
                            state="paused",
                            next_at=now + (30 if row["adapter"] == "weather" else row["interval"]),
                        )
                        self._save_poll(row)
                        continue
                    self.fabric.connect(
                        row["id"],
                        row["epoch"],
                        lease_seconds=60 if row["adapter"] == "weather" else 30,
                        guard=self._guard,
                    )
                    adapter = self._adapter({**row, "paths": paths})
                    guard = partial(self._guard, generation=generation if ambient else None)
                    adapter.acquisition_guard = guard
                    if ambient:
                        adapter.observer = partial(self.delivery.observe, guard=guard)
                    adapter.poll()
                    counts["polled"] += 1
                    row.update(
                        state="operational",
                        last_success=now,
                        failures=0,
                        next_at=now + (30 if row["adapter"] == "weather" else row["interval"]),
                    )
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    PermissionError,
                    StateConflict,
                    sqlite3.Error,
                    ConnectorError,
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
        from .phone_context import recheck

        recheck(self)
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
                    "adapter": row["adapter"],
                    "entity_id": row["entity_id"],
                    "interval_seconds": row["interval"],
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

    def alerts(self) -> list[dict[str, Any]]:
        from .phone_context import recheck

        recheck(self)
        return self.delivery.snapshot()

    def brief(self) -> dict[str, Any]:
        """Caller must hold world:read; metadata snapshots never include private context."""
        from .phone_context import recheck

        with self.store.transaction():
            recheck(self)
            rows = [
                r
                for r in self.store.all("perception_poll")
                if r["relationship"] == self.world.relationship
                and r["adapter"] in {
                    "time", "calendar", "tasks", "weather", "android", "connected_tasks"
                }
            ]
            sources = []
            for row in rows[:8]:
                key = {
                    "time": "clock.state",
                    "calendar": "calendar.state",
                    "tasks": "tasks.state",
                    "connected_tasks": "connected_tasks.state",
                    "weather": "weather.state",
                    "android": "phone.state",
                }[row["adapter"]]
                available = True
                if row["adapter"] in {"calendar", "connected_tasks"}:
                    try:
                        self._adapter(row)
                    except (KeyError, ValueError, PermissionError):
                        available = False
                state = self.world.resolve(row["entity_id"], key)
                sources.append(
                    {
                        "id": row["id"],
                        "epoch": row["epoch"],
                        "adapter": row["adapter"],
                        "entity_id": row["entity_id"],
                        "key": key,
                        "state": state.state if available else "unavailable",
                        "value": state.value if available else None,
                        "epistemic": state.epistemic.value
                        if available
                        else Epistemic.UNKNOWN.value,
                        "evidence": [
                            {
                                "id": o.evidence_id,
                                "observed_at": o.observed_at,
                                "fresh_until": o.fresh_until,
                            }
                            for o in state.observations
                        ]
                        if available
                        else [],
                        "account_id": (row.get("native_config") or {}).get("account_id"),
                        "account_generation": (row.get("native_config") or {}).get(
                            "account_generation"
                        ),
                    }
                )
            return {
                "version": 1,
                "relationship_id": self.world.relationship,
                "observed_at": self.world.clock(),
                "sources": sources,
                "sources_total": len(rows),
                "truncated": len(rows) > 8,
                "schedule": calendar_conflicts(sources),
                "delivery": "passive read-only briefing",
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
