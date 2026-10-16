"""Durable node/session/lease state; availability is derived from fresh advertisements."""

import hashlib
import hmac
import math
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from time import time
from typing import Any

from .contracts import PROTOCOL_VERSION, Capability, Envelope, TaskState, new_id, record
from .storage import StateConflict, Store


class NodeRole(StrEnum):
    MOBILE = "OSCAR Mobile"
    # Stored/wire compatibility for previously enrolled nodes; not an active product name.
    SUNDAY = "Sunday"
    CLOUD = "Cloud"
    DESKTOP = "Desktop"
    EDGE = "Edge"


class Availability(StrEnum):
    FULL = "FULL"
    CONNECTED = "CONNECTED"
    LOCAL = "LOCAL"
    REFLEX_ONLY = "REFLEX_ONLY"
    OFFLINE = "OFFLINE"


@dataclass
class Node:
    id: str
    role: NodeRole
    scopes: tuple[str, ...]
    status: str = "offline"
    paired: bool = False
    revoked: bool = False
    last_seen: float | None = None
    health: str = "unknown"
    capabilities: list[Capability] = field(default_factory=list)
    protocol_version: int = PROTOCOL_VERSION


class SessionHandle:
    """Opaque runtime handle, deliberately not a serializable dataclass."""

    __slots__ = ("id", "node_id", "token")

    def __init__(self, identifier: str, node_id: str, token: str):
        self.id, self.node_id, self.token = identifier, node_id, token

    def __getstate__(self) -> None:
        raise TypeError("session credentials must not be serialized")

    def __repr__(self) -> str:
        return f"SessionHandle(id={self.id!r}, node_id={self.node_id!r}, token=<redacted>)"


class Grid:
    def __init__(self, store: Store, clock: Callable[[], float] = time, heartbeat_ttl: float = 30):
        self.store, self.clock, self.heartbeat_ttl = store, clock, heartbeat_ttl

    def register(self, node: Node) -> None:
        try:
            self.store.get("node", node.id)
        except KeyError:
            self.store.put("node", node.id, record(node))
        else:
            raise StateConflict("node identity already registered")

    def pair(
        self,
        node_id: str,
        approved_scopes: tuple[str, ...],
        ttl: float = 3600,
        *,
        session_id: str | None = None,
    ) -> SessionHandle:
        """Trusted coordinator API: approved scope; inaccessible to remote peers."""
        if not 0 < ttl <= 86400:
            raise ValueError("invalid session lifetime")
        if session_id is not None and (
            not isinstance(session_id, str)
            or len(session_id) != 32
            or any(c not in "0123456789abcdef" for c in session_id)
        ):
            raise ValueError("opaque session identity required")
        with self.store.transaction():
            node = self.store.get("node", node_id)
            if node["revoked"] or not set(approved_scopes) <= set(node["scopes"]):
                raise PermissionError("pairing scope denied")
            identifier, token = session_id or new_id(), secrets.token_urlsafe(32)
            try:
                self.store.get("session", identifier)
            except KeyError:
                pass
            else:
                raise StateConflict("session identity already used; credentials cannot be replayed")
            self.store.put(
                "session",
                identifier,
                {
                    "id": identifier,
                    "node_id": node_id,
                    "token_digest": hashlib.sha256(token.encode()).hexdigest(),
                    "scopes": list(approved_scopes),
                    "expires_at": self.clock() + ttl,
                    "revoked": False,
                },
            )
            node["paired"] = True
            self.store.put("node", node_id, node)
            self.store.audit("", "paired", {"node_id": node_id, "session_id": identifier})
        return SessionHandle(identifier, node_id, token)

    def authenticate(self, session: SessionHandle, scope: str) -> None:
        data = self.store.get("session", session.id)
        node = self.store.get("node", session.node_id)
        digest = hashlib.sha256(session.token.encode()).hexdigest()
        if (
            data["node_id"] != session.node_id
            or data["revoked"]
            or node["revoked"]
            or not node["paired"]
            or data["expires_at"] <= self.clock()
            or not hmac.compare_digest(data["token_digest"], digest)
            or scope not in data["scopes"]
            or scope not in node["scopes"]
        ):
            raise PermissionError("session/scope denied")

    def heartbeat(self, session: SessionHandle, *, health: str = "healthy") -> None:
        if health not in {"healthy", "degraded"}:
            raise ValueError("invalid health")
        with self.store.transaction():
            self.authenticate(session, "heartbeat")
            node = self.store.get("node", session.node_id)
            node.update(
                status="online" if health == "healthy" else "degraded",
                health=health,
                last_seen=self.clock(),
            )
            self.store.put("node", session.node_id, node)

    def advertise(self, session: SessionHandle, capabilities: list[Capability]) -> None:
        with self.store.transaction():
            self.authenticate(session, "advertise")
            self.authenticate(session, "heartbeat")
            node = self.store.get("node", session.node_id)
            for capability in capabilities:
                if (
                    capability.node_id != session.node_id
                    or capability.version != PROTOCOL_VERSION
                    or not set(capability.permissions) <= set(node["scopes"])
                ):
                    raise PermissionError("capability advertisement denied")
            if len({c.id for c in capabilities}) != len(capabilities):
                raise ValueError("duplicate capability identifier")
            node.update(
                capabilities=[record(c) for c in capabilities],
                status="online",
                health="healthy",
                last_seen=self.clock(),
            )
            self.store.put("node", session.node_id, node)

    def nodes(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for data in self.store.all("node"):
            fresh = (
                data["last_seen"] is not None
                and self.clock() - data["last_seen"] <= self.heartbeat_ttl
            )
            if not fresh or data["revoked"]:
                data.update(status="offline", health="unknown", capabilities=[])
            data["active_leases"] = [
                lease["id"]
                for lease in self.store.all("lease")
                if lease["node_id"] == data["id"]
                and lease["active"]
                and lease["expires_at"] > self.clock()
            ]
            result.append(data)
        return result

    def search(self, kind: str) -> list[Capability]:
        capabilities: list[Capability] = []
        for node in self.nodes():
            if node["status"] not in {"online", "degraded"}:
                continue
            for data in node["capabilities"]:
                candidate = Capability.from_dict(data)
                if candidate.input_kind == kind:
                    capabilities.append(candidate)
        return sorted(capabilities, key=lambda c: (c.risk != "low", c.node_id, c.id))

    def availability(self) -> Availability:
        roles = {node["role"] for node in self.nodes() if node["status"] == "online"}
        mobile = bool(roles & {NodeRole.MOBILE, NodeRole.SUNDAY})
        if mobile and {NodeRole.CLOUD, NodeRole.DESKTOP, NodeRole.EDGE} <= roles:
            return Availability.FULL
        if NodeRole.CLOUD in roles:
            return Availability.CONNECTED
        if roles & {NodeRole.MOBILE, NodeRole.SUNDAY, NodeRole.DESKTOP}:
            return Availability.LOCAL
        if NodeRole.EDGE in roles:
            return Availability.REFLEX_ONLY
        return Availability.OFFLINE

    def claim_interaction(self, session: SessionHandle, resource: str) -> dict[str, Any]:
        """Core-owned, expiring surface ownership; does not authorize execution or capture."""
        self.authenticate(session, "heartbeat")
        if not isinstance(resource, str) or not 0 < len(resource) <= 120:
            raise ValueError("bounded interaction resource required")
        with self.store.transaction():
            try:
                lease = self.store.get("interaction_lease", resource)
                previous = self.store.get("session", lease["session"])
                node = self.store.get("node", lease["node"])
            except KeyError:
                lease, previous, node = {}, {}, {}
            live = (
                lease.get("expires", 0) > self.clock()
                and previous.get("expires_at", 0) > self.clock()
                and not previous.get("revoked", True)
                and not node.get("revoked", True)
            )
            if live and lease.get("task_id"):
                raise StateConflict("a text application already owns this interaction")
            if live and lease["session"] != session.id:
                raise StateConflict("another surface owns this interaction")
            generation = lease.get("generation", 0) + (0 if live else 1)
            lease = {
                "session": session.id,
                "node": session.node_id,
                "expires": self.clock() + 15,
                "generation": generation,
            }
            self.store.put("interaction_lease", resource, lease)
        return lease

    def lease(self, task_id: str, node_id: str, ttl: float = 20) -> str:
        if not 0 < ttl <= 300:
            raise ValueError("invalid lease lifetime")
        with self.store.transaction():
            task = self.store.task(task_id)
            live = any(
                n["id"] == node_id and n["status"] in {"online", "degraded"} for n in self.nodes()
            )
            if (
                not live
                or task.cancelled
                or task.state
                not in {
                    TaskState.EXECUTING,
                    TaskState.AWAITING_RESULT,
                }
            ):
                raise StateConflict("node/task unavailable for lease")
            if task.lease_id:
                old = self.store.get("lease", task.lease_id)
                if old["active"] and old["expires_at"] > self.clock():
                    raise StateConflict("task already has an active lease")
            identifier = new_id()
            self.store.put(
                "lease",
                identifier,
                {
                    "id": identifier,
                    "task_id": task_id,
                    "node_id": node_id,
                    "expires_at": self.clock() + ttl,
                    "active": True,
                },
            )
            task.lease_id = identifier
            self.store.put("task", task.id, record(task))
            self.store.audit(
                task.id,
                "lease_acquired",
                {
                    "lease_id": identifier,
                    "node_id": node_id,
                    "correlation_id": task.correlation_id,
                },
            )
        return identifier

    def accept(self, envelope: Envelope, token: str, scope: str) -> None:
        session = SessionHandle(envelope.session_id, envelope.node_id, token)
        with self.store.transaction():
            self.authenticate(session, scope)
            if not math.isfinite(envelope.sent_at) or abs(self.clock() - envelope.sent_at) > 60:
                raise PermissionError("message expired")
            task = self.store.task(envelope.task_id)
            lease = self.store.get("lease", envelope.lease_id)
            if (
                task.correlation_id != envelope.correlation_id
                or task.lease_id != envelope.lease_id
                or lease["task_id"] != task.id
                or lease["node_id"] != envelope.node_id
                or not lease["active"]
                or lease["expires_at"] <= self.clock()
                or (task.cancelled and envelope.kind != "cancel")
                or (
                    task.state not in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}
                    and not (envelope.kind == "cancel" and task.state == TaskState.CANCELLED)
                )
            ):
                raise PermissionError("stale or unrelated task lease")
            if not any(
                n["id"] == envelope.node_id and n["status"] in {"online", "degraded"}
                for n in self.nodes()
            ):
                raise PermissionError("target node unavailable")
            self.store.consume_nonce(envelope.session_id, envelope.nonce)
            self.store.audit(
                task.id,
                envelope.kind,
                {
                    "node_id": envelope.node_id,
                    "session_id": envelope.session_id,
                    "correlation_id": envelope.correlation_id,
                    "lease_id": envelope.lease_id,
                },
            )

    def progress(self, envelope: Envelope, token: str, fraction: float) -> None:
        if envelope.kind != "progress" or not 0 <= fraction <= 1:
            raise ValueError("invalid progress")
        self.accept(envelope, token, "execute")
        self.store.audit(envelope.task_id, "progress_observed", {"fraction": fraction})

    def renew(self, lease_id: str, session: SessionHandle, ttl: float = 30) -> None:
        """Only the current authenticated task owner can renew a still-live lease."""
        if not math.isfinite(ttl) or not 0 < ttl <= 300:
            raise ValueError("invalid lease lifetime")
        with self.store.transaction():
            self.authenticate(session, "execute")
            lease = self.store.get("lease", lease_id)
            task = self.store.task(lease["task_id"])
            if (
                not lease["active"]
                or lease["expires_at"] <= self.clock()
                or lease["node_id"] != session.node_id
                or task.lease_id != lease_id
                or task.state not in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}
            ):
                raise StateConflict("stale lease cannot be renewed")
            lease["expires_at"] = self.clock() + ttl
            self.store.put("lease", lease_id, lease)

    def release(self, lease_id: str) -> None:
        lease = self.store.get("lease", lease_id)
        lease["active"] = False
        self.store.put("lease", lease_id, lease)

    def disconnect(self, node_id: str, *, only_if_stale: bool = False) -> None:
        with self.store.transaction():
            node = self.store.get("node", node_id)
            if (
                only_if_stale
                and not node["revoked"]
                and node["last_seen"] is not None
                and self.clock() - node["last_seen"] <= self.heartbeat_ttl
            ):
                return
            node.update(status="offline", health="unknown", capabilities=[])
            self.store.put("node", node_id, node)
            leases = self.store.all("lease")
        for lease in leases:
            if lease["node_id"] == node_id and lease["active"]:
                task = self.store.task(lease["task_id"])
                if task.state in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}:
                    try:
                        self.store.transition(
                            task.id,
                            TaskState.BLOCKED,
                            blocker="executor disconnected",
                            expected_lease=lease["id"],
                        )
                    except StateConflict:
                        continue

    def reap(self) -> list[str]:
        for node in self.nodes():
            if node["status"] == "offline":
                self.disconnect(str(node["id"]), only_if_stale=True)
        expired = []
        for lease in self.store.all("lease"):
            if lease["active"] and lease["expires_at"] <= self.clock():
                self.release(lease["id"])
                task = self.store.task(lease["task_id"])
                if task.state in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}:
                    self.store.transition(
                        task.id, TaskState.BLOCKED, blocker="executor lease expired"
                    )
                self.store.audit(
                    task.id, "lease_expired", {"lease_id": lease["id"], "reclaimable": True}
                )
                expired.append(task.id)
        return expired

    def revoke(self, node_id: str) -> None:
        self.disconnect(node_id)
        node = self.store.get("node", node_id)
        node["revoked"] = True
        self.store.put("node", node_id, node)
        for lease in self.store.all("lease"):
            if lease["node_id"] == node_id and lease["active"]:
                task = self.store.task(lease["task_id"])
                if task.state == TaskState.BLOCKED:
                    self.store.transition(task.id, TaskState.CANCELLED)
                self.release(lease["id"])


def reconnect_delay(attempt: int, maximum: float = 30) -> float:
    if not 0 <= attempt <= 20:
        raise ValueError("reconnect retry budget exhausted")
    return float(min(maximum, 0.25 * 2**attempt))
