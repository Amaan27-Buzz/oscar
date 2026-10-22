"""Bounded authorized ambient observations for the existing World Runtime."""

import hashlib
import json
import math
import zlib
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from zoneinfo import ZoneInfo

from .connectors import ConnectorFabric
from .continuity import ContextObservation
from .contracts import Epistemic
from .freshness import Authority, SourceRef
from .http_client import NoRedirects

WEATHER_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
WEATHER_CREDIT = "MET Norway · CC BY 4.0"


def weather_request(
    latitude: float, longitude: float, modified: str | None
) -> tuple[int, dict[str, str], dict[str, Any]]:
    """One fixed-provider read; both compressed and decoded bodies are bounded."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "OSCAR/0.1 (https://github.com/Amaan27-Buzz/oscar)",
    }
    if modified:
        headers["If-Modified-Since"] = modified
    request = Request(
        WEATHER_URL + "?" + urlencode({"lat": f"{latitude:.4f}", "lon": f"{longitude:.4f}"}),
        headers=headers,
    )
    deadline = monotonic() + 5
    try:
        with build_opener(NoRedirects()).open(request, timeout=2) as response:
            raw = bytearray()
            while True:
                if monotonic() >= deadline:
                    raise TimeoutError("weather response deadline")
                chunk = response.read1(65536)
                if not chunk:
                    break
                raw.extend(chunk)
                if len(raw) > 262144:
                    raise ValueError("weather response bound")
            if monotonic() >= deadline:
                raise TimeoutError("weather response deadline")
            metadata = {k.lower(): v for k, v in response.headers.items()}
            encoding = metadata.get("content-encoding", "identity")
            if encoding == "gzip":
                decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
                decoded = decoder.decompress(bytes(raw), 262145)
                if not decoder.eof or decoder.unused_data or len(decoded) > 262144:
                    raise ValueError("weather decoded response bound")
            elif encoding == "identity":
                decoded = bytes(raw)
            else:
                raise ValueError("unsupported weather encoding")
            if not metadata.get("content-type", "").lower().startswith("application/json"):
                raise ValueError("weather JSON response required")
            payload = json.loads(decoded)
            if not isinstance(payload, dict):
                raise ValueError("weather response object required")
            return response.status, metadata, payload
    except HTTPError as error:
        with error:
            if error.code in {304, 429, 503}:
                return error.code, {k.lower(): v for k, v in error.headers.items()}, {}
        raise OSError("weather provider unavailable") from None
    except (URLError, HTTPException, zlib.error) as error:
        raise OSError("weather provider unavailable") from error


class WeatherContextSource:
    id = "native-weather"

    def __init__(
        self,
        scope: str,
        config: dict[str, Any],
        clock: Callable[[], float],
        cache: dict[str, Any],
    ):
        self.scope, self.config, self.clock, self.cache = scope, config, clock, cache

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.scope:
            raise PermissionError("weather relationship mismatch")
        now, cache, config = self.clock(), self.cache, self.config
        if now >= cache.get("next_request", 0):
            cache["next_request"] = now + config["interval_seconds"]
            status, headers, payload = weather_request(
                config["latitude"], config["longitude"], cache.get("modified")
            )
            received = self.clock()
            if status in {429, 503}:
                retry = headers.get("retry-after", "3600")
                try:
                    deadline = received + int(retry)
                except ValueError:
                    deadline = parsedate_to_datetime(retry).timestamp()
                if not math.isfinite(deadline):
                    raise ValueError("weather retry deadline required")
                cache["next_request"] = max(cache["next_request"], deadline)
                raise OSError("weather provider temporarily unavailable")
            try:
                expires = parsedate_to_datetime(headers["expires"])
                if expires.tzinfo is None:
                    raise ValueError("timezone-qualified weather expiry required")
                expiry = expires.timestamp()
            except (KeyError, TypeError, ValueError, OverflowError) as error:
                raise ValueError("weather provider expiry required") from error
            if not received < expiry <= received + 86400:
                raise ValueError("weather response expired or unbounded")
            if status == 200:
                selected = self.select(payload, received)
            elif status == 304 and cache.get("selected"):
                selected = cache["selected"]
            else:
                raise ValueError("weather current response required")
            modified = headers.get("last-modified", cache.get("modified"))
            if modified is not None:
                parsedate_to_datetime(modified)
                if len(modified) > 100 or "\r" in modified or "\n" in modified:
                    raise ValueError("bounded weather modification time required")
            cache.update(
                selected=selected,
                observed_at=received,
                expires=expiry,
                modified=modified,
                next_request=max(received + config["interval_seconds"], expiry),
            )
        current = cache["selected"]
        forecast = next(
            (item for item in current["forecast"] if -3600 <= now - item["timestamp"] < 3600),
            None,
        )
        if forecast is None or not 0 <= now - current["updated_timestamp"] <= 21600:
            raise ValueError("weather forecast stale or outside the current window")
        until = min(cache["expires"], cache["observed_at"] + 3600, forecast["timestamp"] + 3600)
        if until <= now:
            raise ValueError("weather evidence expired")
        value = json.dumps(
            {
                "place": config["place"],
                "latitude": config["latitude"],
                "longitude": config["longitude"],
                "updated_at": current["updated_at"],
                "forecast_time": forecast["time"],
                "temperature_c": forecast["temperature_c"],
                "wind_mps": forecast["wind_mps"],
                "humidity_percent": forecast["humidity_percent"],
                "credit": WEATHER_CREDIT,
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "kind": "forecast",
            },
            separators=(",", ":"),
        )
        source = SourceRef(
            WEATHER_URL,
            Authority.LIVE_API,
            "provider",
            cache["observed_at"],
            until - cache["observed_at"],
            published_at=current["updated_at"],
            title="MET Norway Locationforecast",
            source_provider="MET Norway",
            evidence_id=hashlib.sha256(
                json.dumps(
                    [
                        WEATHER_URL,
                        config["latitude"],
                        config["longitude"],
                        cache["observed_at"],
                        current["updated_at"],
                        forecast["time"],
                    ]
                ).encode()
            ).hexdigest(),
        )
        return (ContextObservation("weather.state", value, scope, source, Epistemic.REPORTED),)

    @staticmethod
    def select(payload: dict[str, Any], now: float) -> dict[str, Any]:
        try:
            properties = payload["properties"]
            meta = properties["meta"]
            units = meta["units"]
            if any(
                units.get(key) != unit
                for key, unit in {
                    "air_temperature": "celsius",
                    "wind_speed": "m/s",
                    "relative_humidity": "%",
                }.items()
            ):
                raise ValueError("weather units mismatch")
            updated = datetime.fromisoformat(meta["updated_at"].replace("Z", "+00:00"))
            if updated.tzinfo is None or not 0 <= now - updated.timestamp() <= 21600:
                raise ValueError("weather model update stale or future")
            series = properties["timeseries"]
            if not isinstance(series, list) or not 1 <= len(series) <= 256:
                raise ValueError("bounded weather timeseries required")
            selected: list[dict[str, Any]] = []
            previous = float("-inf")
            for item in series:
                stamp = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
                if stamp.tzinfo is None or stamp.timestamp() <= previous:
                    raise ValueError("ordered timezone-qualified weather times required")
                previous = stamp.timestamp()
                if not now - 3600 < previous <= now + 28800:
                    continue
                details = item["data"]["instant"]["details"]
                values = {}
                for key, target, minimum, maximum in (
                    ("air_temperature", "temperature_c", -100, 70),
                    ("wind_speed", "wind_mps", 0, 150),
                    ("relative_humidity", "humidity_percent", 0, 100),
                ):
                    value = details[key]
                    if type(value) not in {int, float} or not math.isfinite(value):
                        raise ValueError("finite weather measurements required")
                    if not minimum <= value <= maximum:
                        raise ValueError("weather measurement outside supported range")
                    values[target] = value
                if len(selected) < 10:
                    selected.append({"time": item["time"], "timestamp": previous, **values})
            if not selected:
                raise ValueError("current weather forecast missing")
            return {
                "updated_at": meta["updated_at"],
                "updated_timestamp": updated.timestamp(),
                "forecast": selected,
            }
        except (KeyError, TypeError, AttributeError, OverflowError) as error:
            raise ValueError("invalid weather provider response") from error


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
