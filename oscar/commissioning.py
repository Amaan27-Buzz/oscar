"""Recoverable trusted-local commissioning; Grid and native vaults retain authority."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .contracts import new_id, record
from .credentials import redact_runtime_secrets
from .grid import Grid, SessionHandle
from .storage import StateConflict
from .world_model import reference


@dataclass(frozen=True)
class CommissioningPlan:
    node_id: str
    scopes: tuple[str, ...]
    perceive: bool = False
    retain: bool = False
    act: bool = False
    simulated: bool = True
    version: int = 1

    def __post_init__(self) -> None:
        reference(self.node_id)
        if (
            type(self.version) is not int
            or self.version != 1
            or not isinstance(self.scopes, tuple)
            or not 1 <= len(self.scopes) <= 32
            or len(set(self.scopes)) != len(self.scopes)
            or "heartbeat" not in self.scopes
            or any(
                type(b) is not bool for b in (self.perceive, self.retain, self.act, self.simulated)
            )
        ):
            raise ValueError("invalid commissioning plan")
        for scope in self.scopes:
            reference(scope)
        material = json.dumps(record(self))
        if redact_runtime_secrets(material) != material:
            raise ValueError("credential material cannot enter commissioning records")
        if "execute" in self.scopes and not self.act:
            raise PermissionError("execution scope requires an independent action grant")


class Commissioning:
    def __init__(self, grid: Grid, relationship: str):
        reference(relationship)
        if redact_runtime_secrets(relationship) != relationship:
            raise ValueError("credential material cannot become a relationship identity")
        self.grid, self.store, self.relationship = grid, grid.store, relationship

    @staticmethod
    def _digest(enrollment: dict[str, Any]) -> str:
        material = {
            key: value
            for key, value in enrollment.items()
            if key not in {"review_digest", "state", "pairing_until"}
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()

    def initialize(self, *, owner_authorized: bool) -> str:
        if not owner_authorized:
            raise PermissionError("Core initialization requires trusted owner authority")
        with self.store.transaction():
            try:
                identity = self.store.get("core_identity", "core")
                if identity["relationship"] != self.relationship:
                    raise PermissionError("Core identity belongs to another relationship")
            except KeyError:
                identity = {"id": new_id(), "relationship": self.relationship, "version": 1}
                self.store.put("core_identity", "core", identity)
            return str(identity["id"])

    def _get(self, enrollment_id: str) -> dict[str, Any]:
        reference(enrollment_id)
        enrollment = self.store.get("commissioning", enrollment_id)
        identity = self.store.get("core_identity", "core")
        if (
            identity["relationship"] != self.relationship
            or enrollment["relationship"] != self.relationship
            or enrollment["core_id"] != identity["id"]
        ):
            raise PermissionError("enrollment/Core identity mismatch")
        return enrollment

    def begin(
        self, plan: CommissioningPlan, *, owner_authorized: bool, ttl_seconds: int = 600
    ) -> dict[str, Any]:
        if not owner_authorized:
            raise PermissionError("commissioning requires trusted owner authority")
        if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 3600:
            raise ValueError("bounded enrollment lifetime required")
        # Revalidate plans before persisting or granting anything.
        plan = CommissioningPlan(**{**record(plan), "scopes": tuple(plan.scopes)})
        core_id = self.initialize(owner_authorized=True)
        with self.store.transaction():
            node = self.store.get("node", plan.node_id)
            if node["revoked"] or not set(plan.scopes) <= set(node["scopes"]):
                raise PermissionError("commissioning cannot broaden device scopes")
            if len(self.store.all("commissioning")) >= 128:
                raise StateConflict("commissioning record bound reached")
            if any(
                e["node_id"] == plan.node_id and e["state"] not in {"revoked", "expired", "blocked"}
                for e in self.store.all("commissioning")
            ):
                raise StateConflict("device already has an active commissioning record")
            enrollment = {
                "id": new_id(),
                "core_id": core_id,
                "relationship": self.relationship,
                **record(plan),
                "created_at": self.grid.clock(),
                "expires_at": self.grid.clock() + ttl_seconds,
                "state": "review_pending",
                "session_id": new_id(),
                "pairing_until": 0.0,
            }
            enrollment["review_digest"] = self._digest(enrollment)
            self.store.put("commissioning", enrollment["id"], enrollment)
        return enrollment

    def pair(
        self, enrollment_id: str, review_digest: str, *, owner_authorized: bool
    ) -> SessionHandle:
        if not owner_authorized:
            raise PermissionError("exact owner enrollment approval required")
        with self.store.transaction():
            enrollment = self._get(enrollment_id)
            if (
                enrollment["state"] != "review_pending"
                or enrollment["review_digest"] != review_digest
                or self._digest(enrollment) != review_digest
                or enrollment["expires_at"] <= self.grid.clock()
            ):
                raise StateConflict("expired, changed or already consumed enrollment review")
            enrollment.update(state="pairing", pairing_until=self.grid.clock() + 30)
            self.store.put("commissioning", enrollment_id, enrollment)
        # Separate durable intent identifies our session even if the coordinator dies after pairing.
        session = self.grid.pair(
            enrollment["node_id"], tuple(enrollment["scopes"]), session_id=enrollment["session_id"]
        )
        changed = False
        with self.store.transaction():
            current = self._get(enrollment_id)
            node = self.store.get("node", current["node_id"])
            if current["state"] != "pairing" or node["revoked"]:
                data = self.store.get("session", session.id)
                self.store.put("session", session.id, {**data, "revoked": True})
                changed = True
            else:
                self.store.put("commissioning", enrollment_id, {**current, "state": "paired"})
        if changed:
            raise StateConflict("commissioning changed during pairing")
        return session

    def inspect(self, enrollment_id: str, session: SessionHandle | None = None) -> dict[str, Any]:
        with self.store.transaction():
            enrollment = self._get(enrollment_id)
            operational = False
            capabilities = []
            if session is not None:
                if (
                    session.id != enrollment["session_id"]
                    or session.node_id != enrollment["node_id"]
                ):
                    raise PermissionError("device session does not match enrollment")
                self.grid.authenticate(session, "heartbeat")
                nodes = [n for n in self.grid.nodes() if n["id"] == session.node_id]
                if (
                    nodes
                    and enrollment["state"] == "paired"
                    and nodes[0]["status"] in {"online", "degraded"}
                ):
                    operational = True
                    current_session = self.store.get("session", session.id)
                    granted = (
                        set(enrollment["scopes"])
                        & set(current_session["scopes"])
                        & set(nodes[0]["scopes"])
                    )
                    capabilities = [
                        c["id"]
                        for c in nodes[0]["capabilities"]
                        if set(c["permissions"]) <= granted
                    ]
            return {
                "version": 1,
                "id": enrollment_id,
                "core_id": enrollment["core_id"],
                "node_id": enrollment["node_id"],
                "state": enrollment["state"],
                "configured": enrollment["state"] == "paired",
                "operational": operational,
                "simulated": enrollment["simulated"],
                "capability_ids": capabilities,
                "requested_grants": {k: enrollment[k] for k in ("perceive", "retain", "act")},
                "remaining": [
                    "provider",
                    "persona",
                    "voice",
                    "policy",
                    "sentry",
                    "device_acceptance",
                ],
            }

    def recover(self) -> int:
        recovered = 0
        with self.store.transaction():
            for row in self.store.all("commissioning"):
                if row["relationship"] != self.relationship:
                    continue
                enrollment = self._get(row["id"])
                if (
                    enrollment["state"] == "review_pending"
                    and enrollment["expires_at"] <= self.grid.clock()
                ):
                    self.store.put("commissioning", row["id"], {**enrollment, "state": "expired"})
                    recovered += 1
                if (
                    enrollment["state"] == "pairing"
                    and enrollment["pairing_until"] <= self.grid.clock()
                ):
                    try:
                        session = self.store.get("session", enrollment["session_id"])
                    except KeyError:
                        session = None
                    if session is not None:
                        if session["node_id"] != enrollment["node_id"]:
                            raise StateConflict("corrupt commissioning session target")
                        self.store.put("session", session["id"], {**session, "revoked": True})
                    self.store.put("commissioning", row["id"], {**enrollment, "state": "blocked"})
                    recovered += 1
        return recovered

    def revoke(self, enrollment_id: str, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("commissioning revocation requires trusted owner authority")
        with self.store.transaction():
            enrollment = self._get(enrollment_id)
            try:
                session = self.store.get("session", enrollment["session_id"])
            except KeyError:
                session = None
            if session is not None:
                if session["node_id"] != enrollment["node_id"]:
                    raise StateConflict("corrupt commissioning session target")
                self.store.put("session", session["id"], {**session, "revoked": True})
            self.store.put("commissioning", enrollment_id, {**enrollment, "state": "revoked"})
            self.store.audit(
                "",
                "commissioning_revoked",
                {"enrollment_id": enrollment_id, "node_id": enrollment["node_id"]},
            )
