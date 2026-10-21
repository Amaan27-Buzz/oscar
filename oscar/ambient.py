"""Bounded authorized clock/calendar observations for the existing World Runtime."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .connectors import ConnectorFabric
from .continuity import ContextObservation
from .contracts import Epistemic
from .freshness import Authority, SourceRef


class ClockContextSource:
    id = "native-clock"

    def __init__(self, scope: str, timezone: str, clock: Callable[[], float]):
        self.scope, self.timezone, self.clock = scope, ZoneInfo(timezone), clock

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.scope:
            raise PermissionError("clock relationship mismatch")
        now = self.clock()
        local = datetime.fromtimestamp(now, self.timezone)
        return (
            ContextObservation(
                "clock.state",
                json.dumps({"datetime": local.isoformat(), "timezone": self.timezone.key}),
                scope,
                SourceRef("local://core/clock", Authority.LIVE_API, "local", now, 60),
                Epistemic.KNOWN,
            ),
        )


class CalendarContextSource:
    id = "native-calendar"

    def __init__(
        self,
        fabric: ConnectorFabric,
        scope: str,
        config: dict[str, Any],
        clock: Callable[[], float],
        guard: Callable[[], None],
    ):
        self.fabric, self.scope, self.config = fabric, scope, config
        self.clock, self.guard = clock, guard

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.scope:
            raise PermissionError("calendar relationship mismatch")
        value = self.config
        now = self.clock()
        start = datetime.fromtimestamp(now, UTC).isoformat().replace("+00:00", "Z")
        end = (
            datetime.fromtimestamp(now + value["horizon_seconds"], UTC)
            .isoformat()
            .replace("+00:00", "Z")
        )
        google = value["provider"] == "google"
        parameters = (
            {
                "path": {"calendarId": value["calendar_id"]},
                "query": {
                    "timeMin": start,
                    "timeMax": end,
                    "maxResults": "8",
                    "singleEvents": "true",
                    "orderBy": "startTime",
                },
            }
            if google
            else {
                "query": {
                    "$top": "8",
                    "$select": "id,subject,start,end,isCancelled",
                    "$filter": f"end/dateTime ge '{start}' and start/dateTime le '{end}'",
                }
            }
        )
        payload, source = self.fabric.read_context(
            value["instance_id"], value["capability"], parameters, self.guard
        )
        events = payload.get("items" if google else "value")
        if not isinstance(events, list) or len(events) > 8:
            raise ValueError("bounded calendar event response required")
        fields = (
            ("id", "summary", "start", "end", "status")
            if google
            else ("id", "subject", "start", "end", "isCancelled")
        )
        selected = []
        for event in events:
            if not isinstance(event, dict) or not all(k in event for k in ("id", "start", "end")):
                raise ValueError("calendar event identity and time required")
            item: dict[str, Any] = {}
            for key in fields:
                if key not in event:
                    continue
                field_value = event[key]
                if key in {"start", "end"}:
                    if not isinstance(field_value, dict):
                        raise ValueError("structured calendar time required")
                    stamp = {
                        k: v
                        for k, v in field_value.items()
                        if k in {"date", "dateTime", "timeZone"}
                    }
                    if not stamp or any(
                        not isinstance(v, str) or len(v) > 100 for v in stamp.values()
                    ):
                        raise ValueError("bounded calendar time fields required")
                    item[key] = stamp
                elif key == "isCancelled":
                    if type(field_value) is not bool:
                        raise ValueError("typed calendar cancellation required")
                    item[key] = field_value
                elif not isinstance(field_value, str) or not 1 <= len(field_value) <= 1000:
                    raise ValueError("bounded calendar text fields required")
                else:
                    item[key] = field_value
            selected.append(item)
        current = json.dumps(
            {
                "account_id": value["account_id"],
                "window_start": start,
                "window_end": end,
                "events": selected,
                "complete": not bool(payload.get("nextPageToken" if google else "@odata.nextLink")),
            },
            separators=(",", ":"),
        )
        if len(current.encode()) > 2048:
            raise ValueError("calendar observation exceeds current-state bound")
        return (ContextObservation("calendar.state", current, scope, source, Epistemic.REPORTED),)


def calendar_conflicts(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Only explicit timed events with qualified current provenance enter overlap detection."""
    events: list[tuple[float, float, str, str]] = []
    incomplete = False
    unknown_times = 0
    for source in sources:
        if source["adapter"] != "calendar":
            continue
        if source["state"] != "current":
            incomplete = True
            continue
        value = json.loads(source["value"])
        incomplete |= not value["complete"]
        for event in value["events"]:
            try:
                times = []
                for key in ("start", "end"):
                    stamp = event[key]
                    parsed = datetime.fromisoformat(stamp["dateTime"].replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=ZoneInfo(stamp["timeZone"]))
                    times.append(parsed.timestamp())
                if times[1] <= times[0] or not isinstance(event["id"], str):
                    raise ValueError("invalid interval")
                if event.get("status") != "cancelled" and not event.get("isCancelled", False):
                    events.append((times[0], times[1], source["id"], event["id"]))
            except (KeyError, TypeError, ValueError):
                unknown_times += 1
    overlaps: list[dict[str, Any]] = []
    total_overlaps = 0
    ordered = sorted(events)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if right[0] >= left[1]:
                break
            total_overlaps += 1
            if len(overlaps) < 16:
                overlaps.append(
                    {
                        "left": {"source_id": left[2], "event_id": left[3]},
                        "right": {"source_id": right[2], "event_id": right[3]},
                        "starts_at": max(left[0], right[0]),
                        "ends_at": min(left[1], right[1]),
                    }
                )
    return {
        "overlaps": overlaps,
        "incomplete": incomplete or unknown_times > 0,
        "unknown_event_times": unknown_times,
        "truncated": total_overlaps > 16,
        "actions": "requires separately reviewed capability and authority",
    }
