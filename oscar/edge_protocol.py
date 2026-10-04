"""OSCAR Edge wire v1; numeric kinds checked against edge/protocol/edge.h."""

import binascii
import struct
from dataclasses import dataclass
from enum import IntEnum

VERSION = 1
FRAME_SIZE = 20


class Kind(IntEnum):
    HELLO = 1
    HEALTH = 2
    CAPABILITIES = 3
    GPIO_READ = 4
    GPIO_WRITE = 5
    SENSOR_SAMPLE = 6
    EVENT = 7
    SAFE_STATE = 8
    REFLEX_TRIGGER = 9
    E_STOP = 10
    ACK = 11
    ERROR = 12
    DISPLAY = 13


@dataclass(frozen=True)
class Frame:
    kind: Kind
    session: int
    sequence: int
    channel: int = 0
    value: int = 0

    def encode(self) -> bytes:
        if (
            not isinstance(self.kind, Kind)
            or any(
                type(v) is not int for v in (self.session, self.sequence, self.channel, self.value)
            )
            or not 0 < self.session <= 0xFFFFFFFF
            or not 0 < self.sequence <= 0xFFFFFFFF
            or not 0 <= self.channel <= 0xFFFF
            or not 0 <= self.value <= 0xFFFFFFFF
        ):
            raise ValueError("invalid Edge frame")
        raw = struct.pack(
            "<2sBBIIHI",
            b"OE",
            VERSION,
            self.kind,
            self.session,
            self.sequence,
            self.channel,
            self.value,
        )
        return raw + struct.pack("<H", binascii.crc_hqx(raw, 0xFFFF))

    @classmethod
    def decode(cls, raw: bytes) -> "Frame":
        if len(raw) != FRAME_SIZE:
            raise ValueError("Edge frame bound")
        magic, version, kind, session, sequence, channel, value, crc = struct.unpack(
            "<2sBBIIHIH", raw
        )
        if magic != b"OE" or version != VERSION or crc != binascii.crc_hqx(raw[:18], 0xFFFF):
            raise ValueError("Edge frame integrity/version")
        frame = cls(Kind(kind), session, sequence, channel, value)
        frame.encode()
        return frame
