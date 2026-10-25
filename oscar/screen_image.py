"""Bounded native PNG observations; bytes never become task text or authority."""

import hashlib
import struct
import zlib
from dataclasses import dataclass, field

CHUNK_BYTES = 6000
MAX_IMAGE_BYTES = 1_000_000


@dataclass(frozen=True)
class ScreenImage:
    data: bytes = field(repr=False)
    width: int
    height: int
    sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.data, bytes)
            or not 45 <= len(self.data) <= MAX_IMAGE_BYTES
            or self.data[:8] != b"\x89PNG\r\n\x1a\n"
            or type(self.width) is not int
            or type(self.height) is not int
            or not 1 <= self.width <= 4096
            or not 1 <= self.height <= 2160
            or hashlib.sha256(self.data).hexdigest() != self.sha256
        ):
            raise ValueError("bounded exact native PNG required")
        offset, compressed, ended, channels = 8, bytearray(), False, 0
        while offset < len(self.data):
            if len(self.data) - offset < 12:
                raise ValueError("truncated PNG chunk header")
            length = int.from_bytes(self.data[offset : offset + 4], "big")
            kind = self.data[offset + 4 : offset + 8]
            end = offset + 12 + length
            if end > len(self.data):
                raise ValueError("truncated PNG chunk")
            payload = self.data[offset + 8 : end - 4]
            crc = int.from_bytes(self.data[end - 4 : end], "big")
            if zlib.crc32(kind + payload) != crc:
                raise ValueError("PNG chunk checksum mismatch")
            if offset == 8:
                if kind != b"IHDR" or length != 13:
                    raise ValueError("PNG header required")
                width, height, depth, color, compression, filtering, interlace = struct.unpack(
                    ">IIBBBBB", payload
                )
                if (width, height) != (self.width, self.height) or (
                    depth != 8 or color not in {2, 6} or compression or filtering or interlace
                ):
                    raise ValueError("exact non-interlaced RGB/RGBA PNG required")
                channels = 3 if color == 2 else 4
            elif kind == b"IDAT":
                compressed.extend(payload)
            elif kind == b"IEND":
                if length or end != len(self.data):
                    raise ValueError("exact PNG ending required")
                ended = True
            elif kind == b"IHDR" or not kind[0] & 32:
                raise ValueError("unsupported PNG critical chunk")
            offset = end
        size = self.height * (1 + channels * self.width)
        decoder = zlib.decompressobj()
        try:
            pixels = decoder.decompress(compressed, size + 1)
        except zlib.error as exc:
            raise ValueError("invalid PNG pixels") from exc
        if (
            not ended
            or len(pixels) != size
            or not decoder.eof
            or decoder.unused_data
            or any(pixels[i] > 4 for i in range(0, size, 1 + channels * self.width))
        ):
            raise ValueError("bounded complete PNG pixels required")
