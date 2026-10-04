"""Native Grid Edge adapter. Device testimony remains REPORTED/SIMULATED.

The trusted Core queues only policy-approved logical test capabilities. Exchange
rechecks node scope, expiry, boot identity and policy; no offline command backlog.
"""

from dataclasses import dataclass
from typing import Any

from .contracts import Capability, new_id
from .edge_protocol import Frame, Kind
from .grid import Grid, SessionHandle
from .policy import PersonalPolicy

KINDS = {
    "edge.gpio.read": Kind.GPIO_READ,
    "edge.gpio.write": Kind.GPIO_WRITE,
    "edge.sensor.read": Kind.SENSOR_SAMPLE,
    "edge.display": Kind.DISPLAY,
    "edge.reflex.status": Kind.HEALTH,
    "edge.reflex.test": Kind.REFLEX_TRIGGER,
    "edge.health": Kind.HEALTH,
    "edge.stop": Kind.E_STOP,
}
MUTATIONS = {Kind.GPIO_WRITE, Kind.DISPLAY, Kind.REFLEX_TRIGGER, Kind.E_STOP}


@dataclass
class Pending:
    id: str
    frame: Frame
    expires: float
    granted: frozenset[str]
    confirmed: bool
    capability: str


class EdgeBridge:
    def __init__(self, grid: Grid, policy: PersonalPolicy, node_id: str):
        self.grid, self.policy, self.node_id = grid, policy, node_id
        self.boot: int | None = None
        self.sequence = 1
        self.pending: Pending | None = None
        self.healthy = False
        self.last_receipt: bytes | None = None

    def capabilities(self) -> list[Capability]:
        return [
            Capability(
                id=f"{self.node_id}:{name}",
                name=name,
                summary="Configured harmless Edge test channel; physical evidence required",
                execution_class="edge",
                node_id=self.node_id,
                permissions=(name,),
                input_kind=name,
                output_kind="edge.observation",
                risk="physical" if kind in MUTATIONS else "low",
                reversible=kind in {Kind.GPIO_WRITE, Kind.DISPLAY},
            )
            for name, kind in KINDS.items()
        ]

    def _allowed(self, pending: Pending) -> bool:
        decision = self.policy.evaluate(
            pending.capability,
            (pending.capability,),
            pending.granted,
            context={"node_id": self.node_id, "channel": str(pending.frame.channel)},
            confirmed=pending.confirmed,
            confirmation_required=pending.frame.kind in MUTATIONS,
            now=self.grid.clock(),
        )
        return decision.allowed

    def queue(
        self,
        capability: str,
        channel: int,
        value: int,
        *,
        granted: frozenset[str],
        confirmed: bool = False,
    ) -> str:
        if (
            not self.healthy
            or self.boot is None
            or not any(c.node_id == self.node_id for c in self.grid.search(capability))
        ):
            raise PermissionError("Edge unavailable")
        if self.pending is not None:
            raise ValueError("Edge queue full; one in-flight command")
        kind = KINDS[capability]
        if (
            (kind in {Kind.GPIO_WRITE, Kind.DISPLAY} and (channel != 1 or value not in {0, 1}))
            or (kind == Kind.GPIO_READ and (channel not in {0, 1} or value != 0))
            or (kind == Kind.SENSOR_SAMPLE and (channel != 2 or value != 0))
            or (kind in {Kind.HEALTH, Kind.E_STOP, Kind.REFLEX_TRIGGER} and (channel or value))
        ):
            raise ValueError("unconfigured physical channel/value")
        self.sequence += 1
        frame = Frame(kind, self.boot, self.sequence, channel, value)
        frame.encode()
        pending = Pending(new_id(), frame, self.grid.clock() + 1, granted, confirmed, capability)
        if not self._allowed(pending):
            raise PermissionError("Edge permission/policy denied")
        self.pending = pending
        self.grid.store.audit(
            "",
            "edge_queued",
            {
                "action_id": pending.id,
                "node_id": self.node_id,
                "capability": capability,
                "sequence": self.sequence,
                "status": "planned",
            },
        )
        return pending.id

    def exchange(
        self,
        session: SessionHandle,
        boot: int,
        healthy: bool,
        receipt: bytes | None = None,
        *,
        simulated: bool = False,
    ) -> bytes | None:
        if session.node_id != self.node_id or type(boot) is not int or not 0 < boot <= 0xFFFFFFFF:
            raise PermissionError("Edge identity denied")
        self.grid.authenticate(session, "heartbeat")
        self.grid.authenticate(session, "advertise")
        if self.boot != boot:
            self._discard("gateway reboot; prior result unknown")
            self.boot, self.sequence = boot, 1
            self.last_receipt = None
        self.healthy = healthy
        self.grid.advertise(session, self.capabilities() if healthy else [])
        self.grid.heartbeat(session, health="healthy" if healthy else "degraded")
        pending = self.pending
        if receipt is not None:
            frame = Frame.decode(receipt)
            if self.last_receipt == receipt:
                return None
            if (
                pending is None
                or frame.session != boot
                or frame.sequence != pending.frame.sequence
                or frame.channel != pending.frame.channel
                or frame.kind not in {Kind.ACK, Kind.ERROR}
            ):
                raise ValueError("unrelated Edge receipt")
            self.grid.store.audit(
                "",
                "edge_receipt",
                {
                    "action_id": pending.id,
                    "node_id": self.node_id,
                    "status": "reported" if frame.kind == Kind.ACK else "failed",
                    "evidence": "SIMULATED" if simulated else "REPORTED",
                    "value": frame.value,
                    "sequence": frame.sequence,
                    "verification": "physical readback required",
                },
            )
            self.pending = None
            self.last_receipt = receipt
            return None
        if pending is None:
            return None
        if not healthy or self.grid.clock() >= pending.expires or not self._allowed(pending):
            self._discard("expired/degraded/policy denied; result unknown")
            return None
        self.grid.authenticate(session, pending.capability)
        return pending.frame.encode()

    def _discard(self, reason: str) -> None:
        if self.pending:
            self.grid.store.audit(
                "",
                "edge_unknown",
                {
                    "action_id": self.pending.id,
                    "reason": reason,
                    "status": "unknown",
                },
            )
        self.pending = None

    def event(self, session: SessionHandle, raw: bytes, *, simulated: bool = False) -> None:
        self.grid.authenticate(session, "heartbeat")
        if session.node_id != self.node_id:
            raise PermissionError("event identity denied")
        frame = Frame.decode(raw)
        if frame.kind != Kind.EVENT or frame.session != self.boot or frame.channel not in {0, 1, 2}:
            raise ValueError("unrelated Edge event")
        key = f"{self.node_id}:{frame.session}:{frame.sequence}"
        try:
            prior = self.grid.store.get("edge_event_seen", key)
        except KeyError:
            pass
        else:
            if prior["frame"] != raw.hex():
                raise ValueError("conflicting Edge event replay")
            return
        self.grid.store.put("edge_event_seen", key, {"frame": raw.hex()})
        self.grid.store.audit(
            "",
            "edge_event",
            {
                "node_id": self.node_id,
                "channel": frame.channel,
                "value": frame.value,
                "evidence": "SIMULATED" if simulated else "REPORTED",
            },
        )

    def state(self) -> dict[str, Any]:
        node = next(n for n in self.grid.nodes() if n["id"] == self.node_id)
        return {
            "node": node,
            "gateway_boot": self.boot,
            "pico": "reported healthy"
            if self.healthy and node["status"] == "online"
            else "unknown/degraded",
        }
