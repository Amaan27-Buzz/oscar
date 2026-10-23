"""Selected Android metadata enters the existing World Model through device authority."""

import json
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .grid import SessionHandle
from .sentry import AwarenessMode
from .world_model import Observation, ObservationKind

if TYPE_CHECKING:
    from .world_runtime import WorldRuntime


def binding(world: "WorldRuntime", node: str, session: str) -> dict[str, Any]:
    store = world.store
    device = store.get("remote_device", node)
    current = store.get("session", session)
    node_state = store.get("node", node)
    if (
        device["role"] != "mobile"
        or device["session_id"] != session
        or device["owner_id"] != world.world.relationship
        or current["node_id"] != node
        or current["id"] != session
        or node_state["id"] != node
        or current["revoked"]
        or node_state["revoked"]
        or current["expires_at"] <= world.world.clock()
        or "android:perceive" not in current["scopes"]
        or "android:perceive" not in node_state["scopes"]
    ):
        raise PermissionError("current enrolled Android perception session required")
    return current


def review(world: "WorldRuntime", value: dict[str, Any]) -> dict[str, Any]:
    binding(world, value["node_id"], value["session_id"])
    packages = value["packages"]
    if (
        not isinstance(packages, list)
        or not 1 <= len(packages) <= 8
        or any(
            not isinstance(package, str)
            or not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package)
            or len(package) > 100
            for package in packages
        )
        or len(set(packages)) != len(packages)
        or value["entity_id"] != "phone:" + value["node_id"]
        or value["interval_seconds"] != 5
    ):
        raise ValueError("one exact phone session and at most eight selected packages required")
    return {
        "key": "phone.state",
        "kind": "device",
        "ttl_seconds": 15,
        "fields": ["selected notification counts", "selected media playback states"],
        "source": "Authenticated Android metadata; not an inference about attention",
    }


def withdraw(world: "WorldRuntime", session: str) -> None:
    for row in world.store.all("perception_poll"):
        if row["relationship"] != world.world.relationship or row["adapter"] != "android":
            continue
        if row["native_config"]["session_id"] == session:
            try:
                # Revocation must fence the current epoch even if a subscription row is stale.
                epoch = world.world.source(row["id"])["epoch"]
                world.fabric.disconnect(row["id"], epoch)
            except (KeyError, ValueError, PermissionError):
                continue


def recheck(world: "WorldRuntime") -> None:
    settings = world.sentry.settings()
    for row in world.store.all("perception_poll"):
        if row["relationship"] != world.world.relationship or row["adapter"] != "android":
            continue
        try:
            binding(world, row["native_config"]["node_id"], row["native_config"]["session_id"])
            if (
                settings.mode == AwarenessMode.MANUAL
                or row["id"] not in settings.source_ids
                or settings.mode == AwarenessMode.TRIGGER_ONLY
                and "phone.state" not in settings.trigger_keys
            ):
                raise PermissionError("phone source no longer selected")
        except (KeyError, ValueError, PermissionError):
            try:
                world.fabric.disconnect(row["id"], world.world.source(row["id"])["epoch"])
            except (KeyError, ValueError, PermissionError):
                continue


def _validate(
    world: "WorldRuntime",
    rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    current: dict[str, Any],
    payload: dict[str, Any],
) -> tuple[dict[str, Any], Observation | None]:
    if set(payload) == {"withdraw", "epoch"}:
        matches = [row for row in rows if row["id"] == payload["withdraw"]]
        if (
            len(matches) != 1
            or type(payload["epoch"]) is not int
            or payload["epoch"] != world.world.source(matches[0]["id"])["epoch"]
        ):
            raise PermissionError("Android withdrawal source or generation changed")
        return matches[0], None
    rows = selected
    if set(payload) != {"source_id", "epoch", "sequence", "observed_at_ms", "value"}:
        raise ValueError("exact bounded Android observation required")
    matches = [row for row in rows if row["id"] == payload["source_id"]]
    if len(matches) != 1:
        raise PermissionError("Android source not selected or session changed")
    row = matches[0]
    source = world.world.source(row["id"])
    if not source["perceive"]:
        raise PermissionError("Android source perception denied")
    now = world.world.clock()
    observed = payload["observed_at_ms"]
    if (
        type(observed) is not int
        or not now * 1000 - 5000 <= observed <= now * 1000
        or type(payload["epoch"]) is not int
        or payload["epoch"] != source["epoch"]
        or type(payload["sequence"]) is not int
        or payload["sequence"] != source["last_sequence"] + 1
    ):
        raise PermissionError("Android observation is stale, reordered or reconfigured")
    value = payload["value"]
    if not isinstance(value, dict) or set(value) != {
        "notifications",
        "media",
        "notifications_available",
        "media_available",
    }:
        raise ValueError("only notification counts and media states are accepted")
    if any(
        type(value[name + "_available"]) is not bool for name in ("notifications", "media")
    ) or not any(value[name + "_available"] for name in ("notifications", "media")):
        raise ValueError("independent metadata availability required")
    for kind, field, bound in (("notifications", "count", 32), ("media", "state", 11)):
        values = value[kind]
        if (
            not isinstance(values, list)
            or len(values) > 8
            or values
            and not value[kind + "_available"]
        ):
            raise ValueError("bounded selected Android metadata required")
        seen = set()
        for item in values:
            if (
                not isinstance(item, dict)
                or set(item) != {"package", field}
                or item["package"] not in row["native_config"]["packages"]
                or item["package"] in seen
                or type(item[field]) is not int
                or not 0 <= item[field] <= bound
            ):
                raise ValueError("metadata outside selected Android contract")
            seen.add(item["package"])
    observation = Observation(
        f"phone-{payload['epoch']}-{payload['sequence']}",
        row["id"],
        payload["epoch"],
        payload["sequence"],
        row["entity_id"],
        "phone.state",
        ObservationKind.DEVICE,
        json.dumps(value, separators=(",", ":")),
        observed / 1000,
        min(observed / 1000 + 15, current["expires_at"]),
        1.0,
    )
    for capability, permission in (
        ("perception:ingest", "perceive"),
        ("perception:retain", "retain"),
    ):
        if permission == "retain" and not source["retain"]:
            continue
        decision = world.fabric.policy.evaluate(
            capability,
            (permission,),
            frozenset({permission}),
            {"source_id": row["id"], "relationship": world.world.relationship},
            now=now,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
    return row, observation


def request(
    world: "WorldRuntime",
    session: SessionHandle,
    payload: dict[str, Any],
    guard: Callable[[], None],
) -> dict[str, Any]:
    with world.store.transaction():
        guard()
        current = binding(world, session.node_id, session.id)
        settings = world.sentry.settings()
        rows = [
            row
            for row in world.store.all("perception_poll")
            if row["relationship"] == world.world.relationship
            and row["adapter"] == "android"
            and row["native_config"]["node_id"] == session.node_id
            and row["native_config"]["session_id"] == session.id
        ]
        selected = [
            row
            for row in rows
            if row["id"] in settings.source_ids
            and settings.mode != AwarenessMode.MANUAL
            and (
                settings.mode != AwarenessMode.TRIGGER_ONLY
                or "phone.state" in settings.trigger_keys
            )
        ]
        if not payload:
            return {
                "observed_at_ms": int(world.world.clock() * 1000),
                "sources": [
                    {
                        "id": row["id"],
                        "epoch": source["epoch"],
                        "sequence": source["last_sequence"] + 1,
                        "packages": row["native_config"]["packages"],
                    }
                    for row in selected[:8]
                    if (source := world.world.source(row["id"]))["perceive"]
                ],
            }
        if "batch" in payload:
            items = payload["batch"]
            if (
                set(payload) != {"batch"}
                or not isinstance(items, list)
                or not 1 <= len(items) <= 8
                or any(not isinstance(item, dict) for item in items)
            ):
                raise ValueError("one bounded Android metadata batch required")
        else:
            items = [payload]
        # Validate every bound source before any connection, current value or archive write.
        prepared = [_validate(world, rows, selected, current, item) for item in items]
        if len({row["id"] for row, _ in prepared}) != len(prepared):
            raise ValueError("one Android update per source required")
        guard()
        for row, observation in prepared:
            if observation is None:
                world.fabric.disconnect(
                    row["id"], world.world.source(row["id"])["epoch"], guard=guard
                )
                continue
            world.fabric.connect(row["id"], observation.epoch, lease_seconds=15, guard=guard)
            world.delivery.observe(observation, guard=guard)
            world.store.put(
                "perception_poll",
                world.world.source_key(row["id"]),
                {**row, "state": "operational", "last_success": world.world.clock()},
            )
        return {"accepted": True}
