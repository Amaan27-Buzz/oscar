"""Read-only connected task observations; provider date precision is preserved."""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .connector_mount import project_accounts
from .connectors import ConnectionState, endpoint
from .continuity import ContextObservation
from .contracts import Epistemic

if TYPE_CHECKING:
    from .world_runtime import WorldRuntime

CAPABILITIES = {
    "google": "google.tasks.list",
    "microsoft": "microsoft.todo.tasks.list",
}
KEY = "connected_tasks.state"


def binding(world: "WorldRuntime", value: dict[str, Any]) -> tuple[Any, Any, Any]:
    h = world.runtime.connections
    if h is None:
        raise PermissionError("connected task source unavailable")
    project_accounts(h)
    account = h.accounts.check(value["account_id"], value["account_generation"])
    matches = [
        (instance, spec)
        for instance in h.connectors.instances.values()
        if instance.account_id == account.id and instance.account_generation == account.generation
        and instance.manifest.provider == account.provider
        for spec in instance.manifest.capabilities
        if spec.name == CAPABILITIES.get(account.provider, "")
        and h.connectors.state(instance, spec) == ConnectionState.READY
    ]
    if len(matches) != 1:
        raise PermissionError("one current authorized task read binding required")
    instance, spec = matches[0]
    return h, account, (instance, spec)


def review(world: "WorldRuntime", value: dict[str, Any]) -> dict[str, Any]:
    if (
        type(value["account_generation"]) is not int
        or not isinstance(value["task_list_id"], str)
        or not 1 <= len(value["task_list_id"]) <= 160
    ):
        raise ValueError("exact account generation and task list required")
    _, account, (instance, spec) = binding(world, value)
    path = {"tasklist" if account.provider == "google" else "listId": value["task_list_id"]}
    endpoint(spec, {"path": path})
    return {
        "key": KEY,
        "kind": "task",
        "ttl_seconds": spec.freshness_seconds,
        "account_id": account.id,
        "account_alias": account.alias,
        "account_generation": account.generation,
        "provider": account.provider,
        "instance_id": instance.id,
        "service": instance.manifest.id,
        "capability": spec.name,
        "fields": ["id", "title", "status", "due"]
        if account.provider == "google"
        else ["id", "title", "status", "dueDateTime", "importance"],
        "filter": "first eight tasks; no automatic pagination, prioritization or mutation",
        "precision": "Google due is date-only; Microsoft time and timezone are provider-reported",
    }


class ConnectedTaskSource:
    id = "native-connected-tasks"

    def __init__(self, world: "WorldRuntime", row: dict[str, Any]):
        self.world, self.row = world, row
        self.h, self.account, self.connection = binding(world, row["native_config"])

    def guard(self) -> None:
        self.world._guard()
        value = self.row["native_config"]
        self.h.accounts.check(value["account_id"], value["account_generation"])
        current = self.world.world.source(self.row["id"])
        if current["epoch"] != self.row["epoch"] or not current["perceive"]:
            raise PermissionError("task perception revoked")

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.world.world.relationship:
            raise PermissionError("task source relationship mismatch")
        instance, spec = self.connection
        google = self.account.provider == "google"
        parameters = {
            "path": {
                "tasklist" if google else "listId": self.row["native_config"]["task_list_id"]
            },
            "query": {"maxResults" if google else "$top": "8"},
        }
        payload, source = self.h.connectors.read_context(
            instance.id, spec.name, parameters, self.guard
        )
        tasks = payload.get("items" if google else "value")
        if google and tasks is None and payload.get("kind") == "tasks#tasks":
            tasks = []
        if not isinstance(tasks, list) or len(tasks) > 8:
            raise ValueError("bounded provider task list required")
        selected = []
        for task in tasks:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str):
                raise ValueError("task identity required")
            item: dict[str, Any] = {}
            for key in ("id", "title", "status", *(("importance",) if not google else ())):
                if key not in task:
                    continue
                value = task[key]
                if not isinstance(value, str) or len(value) > 1024 or key == "id" and not value:
                    raise ValueError("bounded provider task fields required")
                item[key] = value
            due = task.get("due" if google else "dueDateTime")
            if due is not None:
                if google:
                    if not isinstance(due, str) or len(due) > 100:
                        raise ValueError("provider due date required")
                    parsed = datetime.fromisoformat(due.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError("qualified provider date required")
                    item["due_date"] = parsed.date().isoformat()
                else:
                    if not isinstance(due, dict) or any(
                        not isinstance(due.get(k), str) or not 1 <= len(due[k]) <= 100
                        for k in ("dateTime", "timeZone")
                    ):
                        raise ValueError("provider time and timezone required")
                    datetime.fromisoformat(due["dateTime"].replace("Z", "+00:00"))
                    item["due_time"] = {key: due[key] for key in ("dateTime", "timeZone")}
            selected.append(item)
        current = json.dumps(
            {
                "account_id": self.account.id,
                "task_list_id": self.row["native_config"]["task_list_id"],
                "tasks": selected,
                "complete": not bool(payload.get("nextPageToken" if google else "@odata.nextLink")),
            },
            separators=(",", ":"),
        )
        if len(current.encode()) > 2048:
            raise ValueError("task observation exceeds current-state bound")
        return (ContextObservation(KEY, current, scope, source, Epistemic.REPORTED),)
