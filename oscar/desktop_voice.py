"""Opt-in dictation/dialogue using the canonical Desktop request path; no recordings."""

import json
from collections.abc import Iterable
from pathlib import Path
from threading import Thread
from typing import Any

from .contracts import new_id
from .desktop import Desktop
from .grid import SessionHandle
from .voice_contracts import (
    AudioFrame,
    Origin,
    Playback,
    Recognizer,
    StopToken,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
)
from .voice_identity import oscar_voice_profile
from .voice_runtime import SynthesisChain


class DesktopVoice:
    def __init__(
        self,
        core: Desktop,
        capture: Any,
        recognizer: Recognizer,
        *,
        mode: str = "Dictate",
        synthesis: SynthesisChain | None = None,
        playback: Playback | None = None,
        profile: VoiceProfile | None = None,
    ):
        if mode not in {"Dictate", "Ask"}:
            raise ValueError("voice supports Dictate or Ask")
        if (synthesis is None) != (playback is None):
            raise ValueError("speech requires synthesis and playback together")
        if profile is not None and not profile.local_only:
            raise PermissionError("Desktop voice requires local synthesis")
        self.core, self.capture, self.recognizer = core, capture, recognizer
        self.mode, self.synthesis, self.playback = mode, synthesis, playback
        self.profile = profile
        self.stop = StopToken()
        self.recognition = StopToken()
        self.generation = 0
        self.thread: Thread | None = None
        self.owner: str | None = None
        self.view: dict[str, Any] = {"state": "idle"}

    def start(
        self, session: SessionHandle, context_id: str = "", *, mode: str | None = None
    ) -> dict[str, Any]:
        mode = self.mode if mode is None else mode
        if mode not in {"Dictate", "Ask"}:
            raise ValueError("voice supports Dictate or Ask")
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        if not self.recognizer.local:
            raise PermissionError("Desktop voice requires explicit local recognizer")
        with self.core.lock:
            if self.thread and self.thread.is_alive():
                raise VoiceError("voice interaction already owned")
            self.core.request(
                session,
                {
                    "version": 1,
                    "request_id": "voice-claim",
                    "operation": "claim",
                    "payload": {"resource": "voice"},
                },
            )
            self.owner, self.stop, self.recognition = session.id, StopToken(), StopToken()
            self.generation += 1
            generation, capture_stop, recognition = self.generation, self.stop, self.recognition
            self.view = {"state": "listening", "orb": "listening"}

            def turn() -> None:
                frames = []
                samples = 0
                result: dict[str, Any] | None = None
                try:
                    stream: Iterable[AudioFrame] = self.capture.frames(capture_stop)
                    try:
                        for frame in stream:
                            if capture_stop.event.is_set():
                                break
                            self.core.permission(session, "desktop.voice", ("desktop:microphone",))
                            if frame.origin == Origin.PLAYBACK:
                                continue
                            frames.append(frame)
                            samples += len(frame.samples)
                            if samples >= 15 * 16000:
                                break
                    except VoiceCancelled:
                        recognition.check()
                    if not frames:
                        raise VoiceError("no speech captured")
                    self.capture.close()
                    with self.core.lock:
                        if generation != self.generation:
                            return
                        self.view = {"state": "processing", "orb": "thinking"}
                    transcript = self.recognizer.transcribe(tuple(frames), True, recognition)
                    recognition.check()
                    result = self.core.transcript(
                        session, transcript, recognition, context_id, mode=mode
                    )
                    recognition.check()
                    with self.core.lock:
                        if generation != self.generation:
                            return
                        self.view = {
                            **result,
                            "voice_state": "processing"
                            if mode == "Ask" and self.synthesis is not None
                            else "idle",
                        }
                    if mode == "Ask" and self.synthesis is not None:
                        self.speak(session, result, recognition, generation)
                except VoiceCancelled:
                    with self.core.lock:
                        if generation == self.generation:
                            self.view = {"state": "cancelled", "orb": "attentive"}
                except (VoiceError, PermissionError, ValueError, OSError):
                    with self.core.lock:
                        if generation == self.generation:
                            self.view = (
                                {
                                    **result,
                                    "voice_state": "idle",
                                    "voice_output": "failed",
                                    "orb": "attentive",
                                }
                                if result is not None
                                else {
                                    "state": "blocked",
                                    "epistemic": "UNKNOWN",
                                    "message": "Voice unavailable; inspect Core before retrying",
                                    "voice_state": "idle",
                                }
                            )
                finally:
                    frames.clear()
                    self.capture.close()

            self.thread = Thread(target=turn, daemon=True)
            self.thread.start()
        return self.view

    def speak(
        self, session: SessionHandle, result: dict[str, Any], stop: StopToken, generation: int
    ) -> None:
        if self.synthesis is None or self.playback is None:
            return
        setup = self.core.runtime.setup
        profile = self.profile or (setup.voice_profile() if setup else oscar_voice_profile())
        if not profile.local_only:
            raise PermissionError("Desktop voice requires local synthesis")
        state = result.get("state", "unknown")
        if result.get("approval_required") or state == "planned":
            text = "This request needs owner approval before execution."
        else:
            response = result.get("response") or result.get("value") or result.get("message")
            text = f"The request is {state}."
            if isinstance(response, str) and response:
                text += " " + response[:4096]
        utterance = new_id()
        try:
            for chunk in self.synthesis.synthesize(text, profile, utterance, stop):
                stop.check()
                self.core.permission(session, "desktop.voice", ("desktop:microphone",))
                with self.core.lock:
                    if generation != self.generation:
                        raise VoiceCancelled("obsolete voice output")
                    self.view = {
                        **result,
                        "voice_state": "speaking",
                        "orb": "speaking",
                    }
                self.playback.play(chunk, stop)
            stop.check()
            finish = getattr(self.playback, "finish", None)
            if finish is not None:
                finish(utterance)
            with self.core.lock:
                if generation == self.generation:
                    self.view = {
                        **result,
                        "voice_state": "idle",
                        "voice_output": "reported",
                        "orb": "attentive",
                    }
        except (VoiceError, PermissionError, ValueError, OSError):
            self.playback.cancel()
            raise

    def finish(self, session: SessionHandle) -> dict[str, Any]:
        with self.core.lock:
            if self.owner != session.id:
                raise PermissionError("voice turn belongs to another session")
            if self.thread and self.thread.is_alive() and self.view.get("state") == "listening":
                self.stop.cancel()
                self.view = {
                    "state": "processing",
                    "orb": "thinking",
                    "message": "Finalizing speech",
                }
            return self.view

    def cancel(self, session: SessionHandle) -> dict[str, Any]:
        if self.owner not in {None, session.id}:
            raise PermissionError("voice turn belongs to another session")
        # Interrupt native synthesis/playback even while Core is finishing an issued task.
        self.stop.cancel()
        self.recognition.cancel()
        if self.playback is not None:
            self.playback.cancel()
        with self.core.lock:
            if self.owner not in {None, session.id}:
                raise PermissionError("voice turn belongs to another session")
            self.generation += 1
            self.stop.cancel()
            self.recognition.cancel()
            preview = self.view.get("preview_id")
            if preview:
                self.core.previews.pop(preview, None)
            self.view = (
                {
                    **self.view,
                    "voice_state": "cancelled",
                    "orb": "attentive",
                    "message": "Speech cancelled; inspect the issued task",
                }
                if self.view.get("task_id")
                else {"state": "cancelled", "voice_state": "cancelled", "orb": "attentive"}
            )
            return self.view

    def inspect(self, session: SessionHandle) -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        if self.owner not in {None, session.id}:
            raise PermissionError("voice turn belongs to another session")
        if (
            self.view.get("voice_state") == "idle"
            and self.thread is not None
            and self.thread.is_alive()
        ):
            return {**self.view, "voice_state": "processing"}
        return self.view

    def close(self) -> None:
        self.stop.cancel()
        self.recognition.cancel()
        self.capture.close()
        if self.playback is not None:
            self.playback.cancel()
        if self.thread is not None:
            self.thread.join(3)


def configured_voice(core: Desktop, path: Path) -> DesktopVoice:
    """Trusted local configuration prepares adapters; explicit VoiceStart opens the input."""
    from .voice_adapters import (
        FasterWhisper,
        KokoroSpeech,
        PiperSpeech,
        PlaybackReference,
        SoundDeviceCapture,
        SoundDevicePlayback,
        WindowsSpeech,
    )
    from .voice_contracts import Synthesizer

    if path.stat().st_size > 16384:
        raise ValueError("voice configuration exceeds bound")
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or set(config) != {
        "version",
        "root",
        "input_device",
        "output_device",
    }:
        raise ValueError("exact local voice configuration required")
    if (
        type(config["version"]) is not int
        or config["version"] != 1
        or not isinstance(config["root"], str)
        or not 0 < len(config["root"]) <= 1024
        or type(config["input_device"]) is not int
        or not 0 <= config["input_device"] <= 1024
        or (
            config["output_device"] is not None
            and (
                type(config["output_device"]) is not int or not 0 <= config["output_device"] <= 1024
            )
        )
    ):
        raise ValueError("bounded local model root and explicit audio devices required")
    root = Path(config["root"]).resolve()
    recognizer = FasterWhisper(root / "models/whisper-base.en")
    capture = SoundDeviceCapture(config["input_device"])
    if config["output_device"] is None:
        return DesktopVoice(core, capture, recognizer)
    quality = root / "quality"
    adapters: list[Synthesizer] = []
    if (quality / "kokoro-fp32.onnx").is_file() and (quality / "voices-hf.bin").is_file():
        adapters.append(KokoroSpeech(quality / "kokoro-fp32.onnx", quality / "voices-hf.bin"))
    if (quality / "piper-parallel.onnx").is_file():
        adapters.append(PiperSpeech(quality / "piper-parallel.onnx"))
    adapters.append(WindowsSpeech())
    return DesktopVoice(
        core,
        capture,
        recognizer,
        synthesis=SynthesisChain(tuple(adapters)),
        playback=SoundDevicePlayback(config["output_device"], PlaybackReference()),
        profile=oscar_voice_profile(),
    )
