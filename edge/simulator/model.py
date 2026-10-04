"""Deterministic fault transport around the compiled Pico firmware controller."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from oscar.edge_protocol import Frame, Kind

ROOT = Path(__file__).resolve().parents[2]


def reference_binary() -> Path:
    override = os.environ.get("OSCAR_EDGE_REFERENCE")
    if override:
        return Path(override)
    build = ROOT / ".tmp/edge-host"
    subprocess.run(
        ["cmake", "-S", str(ROOT / "edge/simulator"), "-B", str(build)],
        check=True,
        capture_output=True,
    )
    subprocess.run(["cmake", "--build", str(build), "--config", "Release"], check=True)
    return build / ("Release/edge_reference.exe" if os.name == "nt" else "edge_reference")


@dataclass
class Observation:
    reply: Frame | None
    output: bool
    stopped: bool
    connected: bool
    writes: int


class Pico:
    def __init__(self, binary: Path):
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )

    def step(
        self,
        now: int,
        raw: bytes = b"",
        *,
        input: bool = True,
        sensor: int = 123,
        interlock: bool = False,
        reset: bool = False,
    ) -> Observation:
        assert self.process.stdin and self.process.stdout
        self.process.stdin.write(
            f"{now} {int(input)} {sensor} {int(interlock)} "
            f"{'reset' if reset else raw.hex() or '-'}\n"
        )
        self.process.stdin.flush()
        parts = self.process.stdout.readline().split()
        if len(parts) != 5:
            raise RuntimeError("reference controller failed")
        return Observation(
            Frame.decode(bytes.fromhex(parts[0])) if parts[0] != "-" else None,
            bool(int(parts[1])),
            bool(int(parts[2])),
            bool(int(parts[3])),
            int(parts[4]),
        )

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        self.process.wait(timeout=5)
        if self.process.stdout:
            self.process.stdout.close()


class Gateway:
    """Host fault model for stop-and-wait, bounded retries and offline withdrawal."""

    def __init__(self, pico: Pico):
        self.pico, self.boot, self.sequence, self.now = pico, 100, 1, 0
        self.core = self.link = True
        self.healthy = False
        self.dropped_events = 0
        self.events: list[Frame] = []

    def send(
        self,
        kind: Kind,
        channel: int = 0,
        value: int = 0,
        *,
        drop: int = 0,
        corrupt: bool = False,
        delay_ack: bool = False,
        duplicate: bool = False,
    ) -> Observation:
        if not self.core and kind not in {Kind.SAFE_STATE, Kind.E_STOP}:
            raise PermissionError("Core offline; no fresh mutation")
        self.sequence += 1
        frame = Frame(kind, self.boot, self.sequence, channel, value)
        wire = frame.encode()
        if corrupt:
            wire = wire[:-1] + bytes([wire[-1] ^ 1])
        result = self.pico.step(self.now)
        for attempt in range(3):
            result = self.pico.step(self.now, wire if self.link and attempt >= drop else b"")
            if duplicate:
                result = self.pico.step(self.now, wire)
            if result.reply is not None and not (delay_ack and attempt == 0):
                self.healthy = result.reply.kind == Kind.ACK
                return result
            self.now += 100
        self.healthy = False
        return result

    def connect(self) -> Observation:
        return self.send(Kind.HELLO, value=1)

    def loss(self, *, core: bool = False, link: bool = False) -> Observation:
        if core:
            self.core = False
        if link:
            self.link = False
        self.now += 1500
        self.healthy = False
        return self.pico.step(self.now)

    def reset(self) -> Observation:
        self.boot += 1
        self.sequence = 1
        self.healthy = False
        return self.connect()

    def forward(self, event: Frame) -> None:
        if len(self.events) >= 8:
            self.dropped_events += 1
        else:
            self.events.append(event)
