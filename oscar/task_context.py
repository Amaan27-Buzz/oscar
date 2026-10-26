"""Read-only connected task observations; provider date precision is preserved."""

import json
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from .ambient import qualified_instant
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


def task_attention(sources: list[dict[str, Any]], now: float) -> dict[str, Any]:
    """Rank only reported open tasks; date-only urgency needs one current selected timezone."""
    zones = set()
    for source in sources:
        if source["adapter"] == "time" and source["state"] == "current":
            zones.add(json.loads(source["value"])["timezone"])
    try:
        zone = ZoneInfo(next(iter(zones))) if len(zones) == 1 else None
    except (KeyError, ValueError):
        zone = None
    today = datetime.fromtimestamp(now, zone).date() if zone else None
    expires = min(
        (
            e["fresh_until"]
            for s in sources
            if s["adapter"] in {"time", "connected_tasks"} and s["state"] == "current"
            for e in s.get("evidence", [])
        ),
        default=now,
    )
    if today is not None and zone is not None:
        try:
            expires = min(
                expires,
                qualified_instant(
                    {
                        "dateTime": (today + timedelta(days=1)).isoformat() + "T00:00:00",
                        "timeZone": zone.key,
                    }
                ),
            )
        except (KeyError, ValueError):
            expires = now
    ranked = []
    incomplete, unknown = False, 0
    for source in sources:
        if source["adapter"] != "connected_tasks":
            continue
        if source["state"] != "current":
            incomplete = True
            continue
        value = json.loads(source["value"])
        incomplete |= not value["complete"]
        for task in value["tasks"]:
            status = task.get("status")
            if status == "completed":
                continue
            if status not in {
                "needsAction",
                "notStarted",
                "inProgress",
                "waitingOnOthers",
                "deferred",
            }:
                incomplete = True
                continue
            reason, order = "no_due_date", ""
            try:
                if "scheduled_date" in task or "due_date" in task:
                    due_date = date.fromisoformat(task.get("scheduled_date", task.get("due_date")))
                    if today is None:
                        raise ValueError("selected timezone required for date-only urgency")
                    reason = (
                        "scheduled_earlier"
                        if due_date < today
                        else "scheduled_today"
                        if due_date == today
                        else "scheduled_later"
                    )
                    order = due_date.isoformat()
                elif "due_time" in task:
                    instant = qualified_instant(task["due_time"])
                    local_date = datetime.fromtimestamp(instant, zone).date() if zone else None
                    if instant > now:
                        expires = min(expires, instant)
                    reason = (
                        "overdue"
                        if instant <= now
                        else "due_today"
                        if local_date == today and today is not None
                        else "upcoming"
                    )
                    order = datetime.fromtimestamp(instant, UTC).isoformat()
            except (KeyError, TypeError, ValueError, OverflowError):
                unknown += 1
                reason = (
                    "scheduled_unknown"
                    if "scheduled_date" in task or "due_date" in task
                    else "due_unknown"
                )
            if reason not in {"overdue", "due_today"} and task.get("importance") == "high":
                reason = "high_importance"
            rank = {
                "overdue": 0,
                "due_today": 1,
                "high_importance": 2,
                "scheduled_today": 3,
                "scheduled_earlier": 4,
                "upcoming": 5,
                "scheduled_later": 5,
            }.get(reason, 6)
            ranked.append((rank, order, source["id"], task["id"], reason))
    ranked.sort()
    return {
        "tasks": [{"source_id": s, "task_id": t, "reason": r} for _, _, s, t, r in ranked[:8]],
        "incomplete": incomplete,
        "unknown_due_times": unknown,
        "truncated": len(ranked) > 8,
        "timezone": zone.key if zone else None,
        "fresh_until": expires,
    }


def binding(world: "WorldRuntime", value: dict[str, Any]) -> tuple[Any, Any, Any]:
    h = world.runtime.connections
    if h is None:
        raise PermissionError("connected task source unavailable")
    project_accounts(h)
    account = h.accounts.check(value["account_id"], value["account_generation"])
    matches = [
        (instance, spec)
        for instance in h.connectors.instances.values()
        if instance.account_id == account.id
        and instance.account_generation == account.generation
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
        "filter": (
            "first eight tasks; no automatic pagination or mutation; "
            "attention is read-only and source-bound"
        ),
        "precision": (
            "Google due is a scheduled day, not a deadline; "
            "Microsoft due time and timezone are provider-reported"
        ),
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
            "path": {"tasklist" if google else "listId": self.row["native_config"]["task_list_id"]},
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
        identities = set()
        for task in tasks:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str):
                raise ValueError("task identity required")
            if task["id"] in identities:
                raise ValueError("duplicate provider task identity")
            identities.add(task["id"])
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
                    item["scheduled_date"] = parsed.date().isoformat()
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
