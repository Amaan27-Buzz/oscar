"""Bounded turn lifecycle, provider fallback and lease-based voice arbitration."""

from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from math import isfinite
from time import monotonic

from .voice_contracts import (
    VAD,
    AudioChunk,
    AudioFrame,
    Origin,
    Recognizer,
    StopToken,
    Synthesizer,
    Transcript,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
    WakeDetector,
)


class RecognitionChain:
    def __init__(self, adapters: tuple[Recognizer, ...], local_only: bool = True):
        self.adapters, self.local_only = adapters, local_only
        self.used: str | None = None

    def transcribe(
        self, frames: tuple[AudioFrame, ...], final: bool, stop: StopToken
    ) -> Transcript:
        for adapter in self.adapters:
            stop.check()
            if self.local_only and not adapter.local:
                continue
            try:
                result = adapter.transcribe(frames, final, stop)
                stop.check()
                self.used = adapter.id
                return result
            except VoiceCancelled:
                raise
            except VoiceError:
                continue
        raise VoiceError("STT unavailable under privacy policy")


class SynthesisChain:
    def __init__(self, adapters: tuple[Synthesizer, ...]):
        self.adapters = adapters

    def synthesize(
        self, text: str, profile: VoiceProfile, utterance_id: str, stop: StopToken
    ) -> Iterable[AudioChunk]:
        ordered = (profile.provider,) + profile.fallback
        for provider in dict.fromkeys(ordered):
            adapter = next((a for a in self.adapters if a.id == provider), None)
            if adapter is None or profile.local_only and not adapter.local:
                continue
            emitted = False
            try:
                binding = next((b for b in profile.voice_bindings if b[0] == provider), None)
                applied = replace(
                    profile,
                    provider=provider,
                    preferred_voice=binding[1] if binding else profile.preferred_voice,
                    model=binding[2] if binding else profile.model,
                )
                for chunk in adapter.synthesize(text, applied, utterance_id, stop):
                    stop.check()
                    emitted = True
                    yield chunk
                if not emitted:
                    raise VoiceError("empty synthesis")
                return
            except VoiceCancelled:
                raise
            except VoiceError:
                # Never replay already audible words through another provider.
                if emitted:
                    raise VoiceError("partial synthesis failed; no audible replay") from None
        raise VoiceError("TTS unavailable under privacy policy")


@dataclass(frozen=True)
class AcousticDecision:
    frame: AudioFrame
    classification: str  # human / self_output / uncertain
    source: str


@dataclass(frozen=True)
class AcousticEvent:
    kind: str
    at: float
    node_id: str
    source: str
    status: str


class VoiceSession:
    """Audio event lifecycle; no task authorization or room-audio persistence."""

    def __init__(
        self, wake: WakeDetector, vad: VAD, interrupt: Callable[[], None], max_seconds: float = 20
    ):
        if not 1 <= max_seconds <= 30:
            raise ValueError("invalid capture bound")
        self.wake, self.vad, self.interrupt = wake, vad, interrupt
        self.max_seconds = max_seconds
        self.state = "aware"
        self.frames: list[AudioFrame] = []
        self.preroll: deque[AudioFrame] = deque(maxlen=10)
        self.events: deque[AcousticEvent] = deque(maxlen=128)
        self.started: float | None = None
        self.last_speech: float | None = None
        self.last_frame = -1.0
        self.human_frames = 0

    def _event(self, kind: str, frame: AudioFrame, source: str) -> None:
        self.events.append(
            AcousticEvent(
                kind,
                frame.timestamp,
                frame.node_id,
                source,
                "SIMULATED" if frame.origin == Origin.SIMULATED else "REPORTED",
            )
        )

    def activate(self) -> None:
        if self.state == "off":
            raise PermissionError("acoustic awareness disabled")
        self.interrupt()
        self.frames.clear()
        self.started = self.last_speech = None
        self.state = "listening"

    def speaking(self) -> None:
        self.frames.clear()
        self.preroll.clear()
        self.started = self.last_speech = None
        self.human_frames = 0
        self.state = "speaking"
        self.wake.reset()
        self.vad.reset()

    def cancel(self, *, disable: bool = False) -> None:
        self.interrupt()
        self.frames.clear()
        self.preroll.clear()
        self.started = self.last_speech = None
        self.human_frames = 0
        self.wake.reset()
        self.vad.reset()
        self.state = "off" if disable else "aware"

    def feed(self, decision: AcousticDecision) -> tuple[AudioFrame, ...] | None:
        frame = decision.frame
        if frame.timestamp <= self.last_frame:
            raise ValueError("out-of-order audio")
        self.last_frame = frame.timestamp
        if self.state == "off":
            return None
        if frame.origin == Origin.PLAYBACK or decision.classification != "human":
            self.human_frames = 0
            self._event("self_output_suppressed", frame, decision.source)
            return None
        speech = self.vad.speech(frame)
        if self.state == "speaking":
            self.preroll.append(frame)
            self.human_frames = self.human_frames + 1 if speech else 0
            if self.human_frames < 3:
                return None
            self.interrupt()
            self._event("barge_in", frame, decision.source)
            self.state = "listening"
            self.frames = list(self.preroll)[:-1]
            self.started = self.frames[0].timestamp if self.frames else frame.timestamp
        self.preroll.append(frame)
        if self.state == "aware":
            if speech:
                self._event("speech_present", frame, "local_vad")
            if not self.wake.detect(frame):
                return None
            self.state = "listening"
            self.frames = list(self.preroll)
            self.started = frame.timestamp
            self._event("wake", frame, "local_wake")
            return None
        if self.state != "listening":
            return None
        if self.started is None:
            self.started = frame.timestamp
        self.frames.append(frame)
        if speech:
            if self.last_speech is None:
                self._event("speech_started", frame, "local_vad")
            self.last_speech = frame.timestamp
        ended = self.last_speech is not None and frame.timestamp - self.last_speech >= 0.6
        bounded = (
            frame.timestamp - self.started >= self.max_seconds
            or sum(len(f.samples) for f in self.frames) >= self.max_seconds * 16000
        )
        if ended or bounded:
            result = tuple(self.frames) if self.last_speech is not None else None
            self._event("speech_ended" if ended else "capture_timeout", frame, "local_vad")
            self.frames.clear()
            self.preroll.clear()
            self.started = self.last_speech = None
            self.state = "processing" if result else "aware"
            return result
        return None


@dataclass(frozen=True)
class WakeClaim:
    node_id: str
    timestamp: float
    quality: float
    proximity: float
    priority: int = 0

    def __post_init__(self) -> None:
        if (
            not self.node_id
            or not isfinite(self.timestamp)
            or any(not isfinite(v) or not 0 <= v <= 1 for v in (self.quality, self.proximity))
            or not -100 <= self.priority <= 100
        ):
            raise ValueError("invalid wake claim")


class VoiceArbiter:
    """Single coordinator reference lease. Grid must authenticate claims upstream."""

    def __init__(self, eligible: Callable[[str], bool], clock: Callable[[], float] = monotonic):
        self.eligible, self.clock = eligible, clock
        self.owner: str | None = None
        self.expires = 0.0
        self.generation = 0

    def choose(self, claims: tuple[WakeClaim, ...]) -> tuple[str | None, int]:
        now = self.clock()
        if self.owner and now < self.expires and self.eligible(self.owner):
            return self.owner, self.generation
        candidates = [
            c for c in claims if abs(now - c.timestamp) <= 0.25 and self.eligible(c.node_id)
        ]
        self.owner = None
        if candidates:
            winner = sorted(
                candidates,
                key=lambda c: (-c.priority, -c.proximity, -c.quality, c.timestamp, c.node_id),
            )[0]
            self.owner, self.expires = winner.node_id, now + 10
            self.generation += 1
        return self.owner, self.generation

    def renew(self, node: str, generation: int) -> bool:
        if (
            node != self.owner
            or generation != self.generation
            or self.clock() >= self.expires
            or not self.eligible(node)
        ):
            return False
        self.expires = self.clock() + 10
        return True

    def handoff(self, node: str, target: str, generation: int) -> bool:
        if not self.renew(node, generation) or not self.eligible(target):
            return False
        self.owner = target
        self.generation += 1
        return True
