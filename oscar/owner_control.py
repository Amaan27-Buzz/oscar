"""Scoped owner supervision of existing Grid/runtime state, not another coordinator."""

from typing import Any

from .contracts import Envelope, TaskState
from .grid import Grid, SessionHandle
from .runtime import Runtime
from .storage import Store
from .transport import Transport


class OwnerControl:
    def __init__(
        self,
        store: Store,
        grid: Grid,
        owner: SessionHandle,
        target: SessionHandle,
        transport: Transport,
        runtime: Runtime,
    ):
        self.store, self.grid, self.owner = store, grid, owner
        self.target, self.transport, self.runtime = target, transport, runtime

    def authorize(self, operation: str) -> None:
        self.grid.authenticate(self.owner, "control:" + operation + ":" + self.target.node_id)

    def inspect(self, task_id: str) -> dict[str, Any]:
        self.authorize("inspect")
        task = self.store.task(task_id)
        lease = self.store.get("lease", task.lease_id or "")
        if lease["node_id"] != self.target.node_id:
            raise PermissionError("task is outside control target")
        try:
            checkpoint = self.store.get("worker_checkpoint", task_id)
        except KeyError:
            checkpoint = None
        node = next(n for n in self.grid.nodes() if n["id"] == self.target.node_id)
        return {
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "state": task.state,
            "executor": self.target.node_id,
            "node_status": node["status"],
            "checkpoint": checkpoint,
            "blocker": task.blocker,
            "lease_active": lease["active"],
            "result_ids": [r["id"] for r in self.store.all("result") if r["task_id"] == task.id],
        }

    def control(self, task_id: str, operation: str) -> dict[str, Any]:
        if operation not in {"pause", "resume", "cancel"}:
            raise ValueError("unsupported owner control")
        self.authorize(operation)
        self.inspect(task_id)
        task = self.store.task(task_id)
        if operation == "cancel":
            task = self.runtime.cancel(
                task_id, {self.target.node_id: (self.transport, self.target)}
            )
            return {"task_id": task_id, "state": task.state}
        if task.state not in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}:
            raise ValueError("pause/resume requires active execution")
        return self.transport.control(
            Envelope(
                operation,
                self.target.node_id,
                self.target.id,
                task.id,
                task.correlation_id,
                task.lease_id or "",
                {},
                self.grid.clock(),
            ),
            self.target,
        )

    def revoke(self) -> None:
        self.authorize("revoke")
        self.grid.revoke(self.target.node_id)
