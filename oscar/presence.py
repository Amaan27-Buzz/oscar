"""One Core presence projection; renderers never create operational truth or authority."""

import hashlib
import json
from typing import TYPE_CHECKING, Any

from .contracts import TaskState, new_id

if TYPE_CHECKING:
    from .runtime import Runtime


class PresenceRuntime:
    def __init__(self, runtime: "Runtime"):
        self.runtime, self.store = runtime, runtime.store

    def snapshot(self) -> dict[str, Any]:
        relationship = self.runtime.relationship_id
        now = round(self.runtime.grid.clock() * 1000)
        with self.store.transaction():
            ids = {
                r["id"]
                for r in self.store.all("task_relationship")
                if r["relationship"] == relationship
            }
            tasks = [t for t in self.store.all("task") if t["id"] in ids]
            nodes = {n["id"]: n["status"] for n in self.runtime.grid.nodes()}
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
                    if (
                        not lease
                        or lease["expires_at"] <= now / 1000
                        or nodes.get(lease["node_id"]) != "online"
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
            transition = prior["transition"] if prior["signature"] == signature else new_id()
            generation = prior["generation"] + 1
            self.store.put(
                "core_presence",
                relationship,
                {
                    "source": prior["source"],
                    "generation": generation,
                    "transition": transition,
                    "signature": signature,
                },
            )
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
