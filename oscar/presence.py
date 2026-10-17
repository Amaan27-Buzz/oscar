"""One Core presence projection; renderers never create operational truth or authority."""

import hashlib
import json
import sqlite3
from typing import TYPE_CHECKING, Any

from .contracts import TaskState, new_id
from .storage import StateConflict

if TYPE_CHECKING:
    from .runtime import Runtime


class PresenceRuntime:
    def __init__(self, runtime: "Runtime"):
        self.runtime, self.store = runtime, runtime.store
        self.publisher = new_id()
        self.relationship = ""
        self.generation = self.ceiling = 0

    def snapshot(self) -> dict[str, Any]:
        with self.store.lock:
            for attempt in range(3):
                try:
                    return self._snapshot()
                except sqlite3.OperationalError as error:
                    if error.sqlite_errorcode != sqlite3.SQLITE_BUSY_SNAPSHOT or attempt == 2:
                        raise
        raise StateConflict("Presence read could not obtain a consistent snapshot")

    def _snapshot(self) -> dict[str, Any]:
        relationship = self.runtime.relationship_id
        now = round(self.runtime.grid.clock() * 1000)
        with self.store.transaction(write=False):
            tasks = [
                json.loads(row[0])
                for row in self.store.db.execute(
                    "SELECT t.data FROM records t INDEXED BY tasks_by_state "
                    "JOIN records r ON r.kind='task_relationship' "
                    "AND r.id=t.id WHERE t.kind='task' "
                    "AND json_extract(r.data,'$.relationship')=? "
                    "AND json_extract(t.data,'$.state') IN ('unknown','verifying','executing',"
                    "'awaiting_result','result_received','planned','blocked')",
                    (relationship,),
                )
            ]
            states = set()
            for task in tasks:
                state = task["state"]
                if state in {
                    TaskState.EXECUTING,
                    TaskState.AWAITING_RESULT,
                    TaskState.RESULT_RECEIVED,
                    TaskState.VERIFYING,
                }:
                    lease = self.store.get("lease", task["lease_id"]) if task["lease_id"] else None
                    node = self.store.get("node", lease["node_id"]) if lease else None
                    if (
                        not lease
                        or lease["expires_at"] <= now / 1000
                        or not node
                        or node["revoked"]
                        or node["status"] != "online"
                        or node["last_seen"] is None
                        or now / 1000 - node["last_seen"] > self.runtime.grid.heartbeat_ttl
                        or (
                            state in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}
                            and not lease["active"]
                        )
                    ):
                        state = TaskState.UNKNOWN
                states.add(state)
            operation = "idle"
            for state, expression in (
                (TaskState.UNKNOWN, "unknown"),
                (TaskState.VERIFYING, "verifying"),
                (TaskState.EXECUTING, "executing"),
                (TaskState.AWAITING_RESULT, "executing"),
                (TaskState.RESULT_RECEIVED, "processing"),
                (TaskState.PLANNED, "waiting"),
                (TaskState.BLOCKED, "waiting"),
            ):
                if state in states:
                    operation = expression
                    break
            reduced, visible = False, True
            if self.runtime.setup:
                try:
                    preferences = self.runtime.setup.profile("preferences")
                    reduced, visible = preferences["reduced_motion"], preferences["show_presence"]
                except KeyError:
                    pass
            delivery = "focused" if operation in {"executing", "verifying"} else "composed"
            if self.runtime.world and self.runtime.world.sentry.settings().state.value == "sleep":
                delivery = "resting"
            signature = hashlib.sha256(
                json.dumps([operation, delivery, reduced, visible]).encode()
            ).hexdigest()
            try:
                prior = self.store.get("core_presence", relationship)
            except KeyError:
                prior = {
                    "source": new_id(),
                    "generation": 0,
                    "transition": new_id(),
                    "signature": "",
                }
            changed = prior["signature"] != signature
            transition = new_id() if changed else prior["transition"]
            if self.relationship != relationship:
                self.generation = self.ceiling = 0
                self.relationship = relationship
            if self.ceiling and prior.get("publisher") != self.publisher:
                raise StateConflict("Presence publisher replaced; stale runtime rejected")
            generation, ceiling = self.generation + 1, self.ceiling
            reserve = generation > ceiling
            if reserve:
                generation = prior["generation"] + 1
                ceiling = prior["generation"] + 1024
            if changed or reserve:
                # Reserve publications against crash replay; gestures retain their transition ID.
                self.store.put(
                    "core_presence",
                    relationship,
                    {
                        "source": prior["source"],
                        "generation": ceiling,
                        "state_generation": prior.get("state_generation", 0) + int(changed),
                        "publisher": self.publisher,
                        "transition": transition,
                        "signature": signature,
                    },
                )
        self.generation, self.ceiling = generation, ceiling
        return {
            "version": 1,
            "visible": visible,
            "expression": {
                "version": 1,
                "source": {"kind": "core", "id": "presence:" + prior["source"]},
                "generation": generation,
                "transitionId": transition,
                "eventTime": now,
                "expiresAt": now + 30_000,
                "kind": "state",
                "priority": "normal",
                "operation": operation,
                "delivery": delivery,
                "availability": "available",
                "muted": False,
                "attention": "owner" if operation == "waiting" else "none",
                "reducedMotion": reduced,
            },
        }
