"""Bounded opt-in Groq transcription; audio stays in memory and keys stay opaque."""

import io
import json
import os
import struct
import wave
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener
from uuid import uuid4

from .http_client import NoRedirects
from .models import Failure
from .providers import rate_limits
from .voice_contracts import AudioFrame, Origin, StopToken, Transcript, VoiceError

if TYPE_CHECKING:
    from .desktop import Desktop
    from .harness import Harness


class GroqRecognizer:
    id = "groq/whisper-large-v3-turbo"
    local = False
    model = "whisper-large-v3-turbo"

    def __init__(self, harness: "Harness"):
        self.h = harness
        self.opener = build_opener(NoRedirects())

    def ready(self) -> str:
        for slot in self.h.pool.slots.values():
            if (
                slot.provider == "groq"
                and self.h.router._confirmed_free_plan(slot.id)
                and self.h.pool.eligible(slot.id, model=self.model)
            ):
                return slot.id
        raise VoiceError("Groq transcription needs a current confirmed Free-plan Vault binding")

    def transcribe(
        self, frames: tuple[AudioFrame, ...], final: bool, stop: StopToken
    ) -> Transcript:
        stop.check()
        if not final or not frames or any(f.origin == Origin.PLAYBACK for f in frames):
            raise VoiceError("Final human audio required")
        count = sum(len(frame.samples) for frame in frames)
        if count > 15 * 16000:
            raise VoiceError("Transcription is limited to fifteen seconds")
        audio = io.BytesIO()
        with wave.open(audio, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(
                b"".join(
                    struct.pack("<h", round(value * 32767))
                    for frame in frames
                    for value in frame.samples
                )
            )
        boundary = "oscar-" + uuid4().hex
        body = bytearray()
        for name, value in (("model", self.model), ("response_format", "json")):
            body.extend(
                (
                    f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
                    f"\r\n\r\n{value}\r\n"
                ).encode()
            )
        body.extend(
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
                'filename="turn.wav"\r\nContent-Type: audio/wav\r\n\r\n'
            ).encode()
        )
        body.extend(audio.getvalue())
        body.extend(f"\r\n--{boundary}--\r\n".encode())
        slot = self.ready()
        if not self.h.pool.reserve(slot, 0, self.model):
            raise VoiceError("Transcription capacity unavailable")
        try:
            stop.check()
            # Resolve again immediately before transport; revocation cannot use an old key.
            if not self.h.router._confirmed_free_plan(slot):
                raise VoiceError("Free-plan confirmation expired or revoked")
            secret = self.h.pool.secret_for_adapter(slot)
            if not secret:
                raise VoiceError("Transcription credential unavailable")
            request = Request(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                bytes(body),
                headers={
                    "Authorization": "Bearer " + secret,
                    "User-Agent": "OSCAR/0.1",
                    "Content-Type": "multipart/form-data; boundary=" + boundary,
                },
                method="POST",
            )
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(32769)
                self.h.pool.observe_limits(
                    slot, self.model, rate_limits(response.headers, "groq", self.h.grid.clock())
                )
            stop.check()
            if len(raw) > 32768:
                raise VoiceError("Transcription response exceeds bound")
            result = json.loads(raw)
            text = result.get("text") if isinstance(result, dict) else None
            if not isinstance(text, str) or not text.strip() or len(text) > 4096:
                raise VoiceError("No bounded speech transcript returned")
            return Transcript(
                text.strip(),
                True,
                None,
                None,
                frames[0].timestamp,
                frames[-1].timestamp + len(frames[-1].samples) / 16000,
                self.id,
            )
        except HTTPError as error:
            code = error.code
            self.h.pool.observe_limits(
                slot, self.model, rate_limits(error.headers, "groq", self.h.grid.clock())
            )
            error.close()
            self.h.pool.failed(
                slot, Failure.RATE_LIMIT if code == 429 else Failure.ACCESS, 30, self.model
            )
            raise VoiceError(
                f"Cloud transcription rejected (HTTP {code}); no automatic retry or paid fallback"
            ) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise VoiceError("Cloud transcription unavailable; no automatic retry") from None
        finally:
            self.h.pool.release(slot)


def mount_cloud_voice(core: "Desktop", h: "Harness", data: Path) -> None:
    """Prepare installed audio only; enrollment and capture remain explicit UI actions."""
    if os.name != "nt":
        return
    from .desktop_voice import DesktopVoice
    from .voice_adapters import (
        PlaybackReference,
        SoundDeviceCapture,
        SoundDevicePlayback,
        WindowsSpeech,
        optional,
    )
    from .voice_identity import oscar_voice_profile
    from .voice_runtime import SynthesisChain

    optional("sounddevice")  # Import is not device enumeration or stream creation.
    path = data / "voice-settings.json"
    if not path.exists():
        with path.open("x", encoding="utf-8") as handle:
            json.dump(
                {"version": 3, "muted": True, "input_device": 0, "output_device": None}, handle
            )
    if path.is_symlink() or path.stat().st_size > 4096:
        raise VoiceError("Bounded local voice preferences required")
    settings = json.loads(path.read_text(encoding="utf-8"))
    input_device, output_device = settings.get("input_device"), settings.get("output_device")
    if (
        type(input_device) is not int
        or not 0 <= input_device <= 1024
        or type(settings.get("muted")) is not bool
        or output_device is not None
        and (type(output_device) is not int or not 0 <= output_device <= 1024)
    ):
        raise VoiceError("Select supported voice devices in audio preferences")
    reference = PlaybackReference()

    def devices(
        input_id: int, output_id: int | None
    ) -> tuple[SoundDeviceCapture, SynthesisChain | None, SoundDevicePlayback | None]:
        return (
            SoundDeviceCapture(input_id, "oscar-local-desktop"),
            SynthesisChain((WindowsSpeech(),)) if output_id is not None else None,
            SoundDevicePlayback(output_id, reference) if output_id is not None else None,
        )

    capture, synthesis, playback = devices(input_device, output_device)
    capture.expected_identity = settings.get("input_identity")
    capture.require_identity = True
    if playback is not None:
        playback.expected_identity = settings.get("output_identity")
        playback.require_identity = True
    voice = DesktopVoice(
        core,
        capture,
        GroqRecognizer(h),
        mode="Ask",
        synthesis=synthesis,
        playback=playback,
        profile=oscar_voice_profile(),
        config_path=path,
        muted=settings["muted"],
        reference=reference,
    )
    voice.device_factory = devices
    core.voice = voice
    h.store.close_callbacks.insert(0, voice.close)
