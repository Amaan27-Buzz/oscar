"""OSCAR-owned audio contracts. Optional runtimes remain below these boundaries."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from threading import Event
from typing import Protocol

from .contracts import Epistemic, TaskState


class VoiceError(RuntimeError):
    """Bounded adapter failure category, without private audio or provider payloads."""


class VoiceCancelled(VoiceError):
    pass


class StopToken:
    def __init__(self) -> None:
        self.event = Event()

    def cancel(self) -> None:
        self.event.set()

    def check(self) -> None:
        if self.event.is_set():
            raise VoiceCancelled("cancelled")


class Origin(StrEnum):
    MICROPHONE = "microphone"
    PLAYBACK = "oscar_playback"
    SIMULATED = "SIMULATED"


@dataclass(frozen=True)
class AudioFrame:
    samples: tuple[float, ...]
    timestamp: float
    node_id: str
    rate: int = 16000
    origin: Origin = Origin.MICROPHONE

    def __post_init__(self) -> None:
        if (
            self.rate != 16000
            or not 0 < len(self.samples) <= 16000
            or not isfinite(self.timestamp)
            or self.timestamp < 0
            or not self.node_id
            or any(not isfinite(v) or abs(v) > 1 for v in self.samples)
        ):
            raise ValueError("invalid bounded mono 16k audio frame")


@dataclass(frozen=True)
class Transcript:
    text: str
    final: bool
    language: str | None
    confidence: float | None
    start: float
    end: float
    source: str
    status: str = Epistemic.REPORTED

    def __post_init__(self) -> None:
        if (
            len(self.text) > 4096
            or not self.source
            or not isfinite(self.start)
            or not isfinite(self.end)
            or self.start < 0
            or self.end < self.start
            or self.confidence is not None
            and (not isfinite(self.confidence) or not 0 <= self.confidence <= 1)
        ):
            raise ValueError("invalid transcript metadata")


@dataclass(frozen=True)
class VoiceProfile:
    identity: str = "oscar"
    preferred_voice: str = "oscar-reference"
    provider: str = "kokoro"
    model: str = "kokoro-82m-v1.0"
    rate: float = 1.0
    style: str = "steady"
    mode: str = "balanced"
    local_only: bool = True
    interruptible: bool = True
    fallback: tuple[str, ...] = ("piper",)
    voice_bindings: tuple[tuple[str, str, str], ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        if not self.identity or not isfinite(self.rate) or not 0.5 <= self.rate <= 2:
            raise ValueError("invalid voice identity/rate")
        if self.mode not in {"fast", "balanced", "quality", "quiet", "serious"}:
            raise ValueError("invalid speaking mode")
        if len({provider for provider, _, _ in self.voice_bindings}) != len(self.voice_bindings):
            raise ValueError("duplicate Voice Identity provider binding")


@dataclass(frozen=True)
class AudioChunk:
    pcm: bytes
    rate: int
    provider: str
    voice: str
    utterance_id: str
    status: str = Epistemic.REPORTED

    def __post_init__(self) -> None:
        if (
            self.rate < 8000
            or self.rate > 48000
            or not self.pcm
            or len(self.pcm) % 2
            or len(self.pcm) > self.rate * 2 * 30
            or not self.provider
            or not self.utterance_id
        ):
            raise ValueError("invalid bounded PCM16 synthesis chunk")


@dataclass(frozen=True)
class VoiceResponse:
    text: str
    task_id: str
    state: TaskState
    epistemic: Epistemic
    evidence_ids: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class Capture(Protocol):
    def frames(self, stop: StopToken) -> Iterable[AudioFrame]: ...
    def close(self) -> None: ...


class VAD(Protocol):
    def speech(self, frame: AudioFrame) -> bool: ...
    def reset(self) -> None: ...


class WakeDetector(Protocol):
    def detect(self, frame: AudioFrame) -> bool: ...
    def reset(self) -> None: ...


class Recognizer(Protocol):
    id: str
    local: bool

    def transcribe(
        self, frames: tuple[AudioFrame, ...], final: bool, stop: StopToken
    ) -> Transcript: ...


class Synthesizer(Protocol):
    id: str
    local: bool

    def synthesize(
        self, text: str, profile: VoiceProfile, utterance_id: str, stop: StopToken
    ) -> Iterable[AudioChunk]: ...


class Playback(Protocol):
    def play(self, chunk: AudioChunk, stop: StopToken) -> None: ...
    def cancel(self) -> None: ...


class EmbeddingExtractor(Protocol):
    model_id: str

    def extract(self, frames: tuple[AudioFrame, ...], stop: StopToken) -> tuple[float, ...]: ...
