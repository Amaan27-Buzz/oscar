"""Opt-in dictation/dialogue using the canonical Desktop request path; no recordings."""

import json
import os
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from threading import Thread
from time import monotonic
from typing import Any

from .contracts import new_id
from .desktop import Desktop
from .grid import NodeRole, SessionHandle
from .voice_contracts import (
    VAD,
    AudioFrame,
    Origin,
    Playback,
    Recognizer,
    StopToken,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
    WakeDetector,
)
from .voice_identity import oscar_voice_profile
from .voice_runtime import AcousticDecision, SynthesisChain, VoiceSession


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
        wake: WakeDetector | None = None,
        vad: VAD | None = None,
        reference: Any = None,
        config_path: Path | None = None,
        muted: bool = True,
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
        self.wake, self.vad, self.reference = wake, vad, reference
        self.config_path, self.muted = config_path, muted
        self.listener_stop = StopToken()
        self.listener_seen = 0.0
        self.listener_thread: Thread | None = None
        self.acoustic: VoiceSession | None = None
        self.inventory: dict[int, dict[str, Any]] = {}
        self.inventory_owner: str | None = None
        self.device_factory: Callable[[int, int | None], tuple[Any, Any, Any]] | None = None
        self.wake_factory: Callable[[], tuple[WakeDetector, VAD]] | None = None
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
        if self.muted:
            raise PermissionError("microphone is muted")
        if self.listener_thread is not None and self.listener_thread.is_alive():
            raise VoiceError("continuous listening owns the microphone")
        validate_device = getattr(self.capture, "validate_device", None)
        if validate_device is not None:
            validate_device()
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
            self.acoustic = None
            self.owner, self.stop, self.recognition = session.id, StopToken(), StopToken()
            self.generation += 1
            generation, capture_stop, recognition = self.generation, self.stop, self.recognition
            self.view = {"state": "listening", "orb": "listening"}

            self.thread = Thread(
                target=self._turn,
                args=(session, context_id, mode, generation, capture_stop, recognition),
                daemon=True,
            )
            self.thread.start()
        return self.view

    def _turn(
        self,
        session: SessionHandle,
        context_id: str,
        mode: str,
        generation: int,
        capture_stop: StopToken,
        recognition: StopToken,
        supplied: tuple[AudioFrame, ...] | None = None,
    ) -> None:
        frames = []
        samples = 0
        result: dict[str, Any] | None = None
        try:
            stream: Iterable[AudioFrame] = (
                supplied if supplied is not None else self.capture.frames(capture_stop)
            )
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
            if supplied is None:
                self.capture.close()
            with self.core.lock:
                if generation != self.generation:
                    return
                self.view = {"state": "processing", "orb": "thinking"}
            transcript = self.recognizer.transcribe(tuple(frames), True, recognition)
            recognition.check()
            if supplied is not None:
                self.core.permission(
                    session,
                    "desktop.voice.awareness",
                    ("desktop:microphone", "desktop:voice:continuous"),
                )
                self.listener_stop.check()
            result = self.core.transcript(session, transcript, recognition, context_id, mode=mode)
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
                    self.view = (
                        {**result, "voice_state": "cancelled", "orb": "attentive"}
                        if result is not None
                        else {"state": "cancelled", "orb": "attentive"}
                    )
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
            if supplied is None:
                self.capture.close()

            if self.acoustic is not None and not self.listener_stop.event.is_set():
                with self.core.lock:
                    if self.acoustic.state in {"processing", "speaking"}:
                        self.acoustic.cancel()

    def settings(self, session: SessionHandle) -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        return {
            "muted": self.muted,
            "input_device": getattr(self.capture, "device", None),
            "output_device": getattr(self.playback, "device", None),
            "continuous_available": self.wake_factory is not None
            or (self.wake is not None and self.vad is not None),
            "continuous_active": self.listener_thread is not None
            and self.listener_thread.is_alive(),
            "continuous_granted": "desktop:voice:continuous" in self.core.grants(session),
            "persisted": self.config_path is not None,
        }

    def devices(self, session: SessionHandle) -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        from .voice_adapters import audio_identity, optional

        sd = optional("sounddevice")
        try:
            devices = sd.query_devices()
            if len(devices) > 256:
                raise VoiceError("audio device inventory exceeds bound")
            self.inventory = {index: audio_identity(sd, index) for index in range(len(devices))}
            self.inventory_owner = session.id
            return {
                "devices": [
                    {
                        "id": index,
                        "name": identity["name"],
                        "input": identity["input_channels"] > 0,
                        "output": identity["output_channels"] > 0,
                    }
                    for index, identity in self.inventory.items()
                ]
            }
        except Exception:
            raise VoiceError("audio device inventory unavailable") from None

    def configure(
        self,
        session: SessionHandle,
        *,
        muted: bool,
        input_device: int,
        output_device: int | None,
    ) -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        if (
            type(muted) is not bool
            or type(input_device) is not int
            or not 0 <= input_device <= 1024
            or (
                output_device is not None
                and (type(output_device) is not int or not 0 <= output_device <= 1024)
            )
        ):
            raise ValueError("explicit bounded audio settings required")
        if self.config_path is None or self.device_factory is None:
            raise VoiceError("persistent local audio configuration unavailable")
        # Muting must remain possible even after device inventory or native audio fails.
        from .voice_adapters import audio_identity, optional

        input_identity = getattr(self.capture, "expected_identity", None)
        output_identity = getattr(self.playback, "expected_identity", None)
        if (
            not muted
            or input_device != getattr(self.capture, "device", None)
            or output_device != getattr(self.playback, "device", None)
        ):
            if self.inventory_owner != session.id:
                raise VoiceError("find audio devices before selecting them")
            sd = optional("sounddevice")
            input_identity = self.inventory.get(input_device)
            output_identity = (
                self.inventory.get(output_device) if output_device is not None else None
            )
            if (
                input_identity is None
                or input_identity != audio_identity(sd, input_device)
                or input_identity["input_channels"] <= 0
                or (
                    output_device is not None
                    and (
                        output_identity is None
                        or output_identity != audio_identity(sd, output_device)
                        or output_identity["output_channels"] <= 0
                    )
                )
            ):
                raise VoiceError("audio inventory changed; find and select devices again")
        self.muted = True
        self.cancel(session)
        for thread in (self.listener_thread, self.thread):
            if thread is not None:
                thread.join(3)
                if thread.is_alive():
                    raise VoiceError("prior voice interaction is still stopping")
        unchanged = input_device == getattr(
            self.capture, "device", None
        ) and output_device == getattr(self.playback, "device", None)
        capture, synthesis, playback = (
            (self.capture, self.synthesis, self.playback)
            if unchanged
            else self.device_factory(input_device, output_device)
        )
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config.update(
            version=3,
            muted=muted,
            input_device=input_device,
            output_device=output_device,
            input_identity=input_identity,
            output_identity=output_identity,
        )
        descriptor, temporary = tempfile.mkstemp(dir=self.config_path.parent, prefix=".voice-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(config, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.config_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        with self.core.lock:
            self.capture, self.synthesis, self.playback = capture, synthesis, playback
            self.capture.expected_identity = input_identity
            self.capture.require_identity = True
            if self.playback is not None:
                output_adapter: Any = self.playback
                output_adapter.expected_identity = output_identity
                output_adapter.require_identity = True
            self.muted = muted
        return self.settings(session)

    def listen(self, session: SessionHandle) -> dict[str, Any]:
        self.core.permission(
            session, "desktop.voice.awareness", ("desktop:microphone", "desktop:voice:continuous")
        )
        if self.muted or not self.recognizer.local:
            raise PermissionError("continuous listening requires unmuted local audio")
        validate_device = getattr(self.capture, "validate_device", None)
        if validate_device is not None:
            validate_device()
        with self.core.lock:
            if (self.thread is not None and self.thread.is_alive()) or (
                self.listener_thread is not None and self.listener_thread.is_alive()
            ):
                raise VoiceError("voice interaction already owned")
            if self.wake is None or self.vad is None:
                if self.wake_factory is None:
                    raise VoiceError("local wake and VAD models unavailable")
                self.wake, self.vad = self.wake_factory()
            self.core.request(
                session,
                {
                    "version": 1,
                    "request_id": new_id(),
                    "operation": "claim",
                    "payload": {"resource": "voice"},
                },
            )
            self.owner = session.id
            self.listener_stop = StopToken()
            self.listener_seen = monotonic()
            self.acoustic = VoiceSession(self.wake, self.vad, self._interrupt_output, 15)
            self.view = {"state": "aware", "voice_state": "aware", "orb": "attentive"}
            self.listener_thread = Thread(target=self._listen, args=(session,), daemon=True)
            self.listener_thread.start()
        return self.settings(session)

    def _interrupt_output(self) -> None:
        self.recognition.cancel()
        if self.playback is not None:
            self.playback.cancel()

    def _listen(self, session: SessionHandle) -> None:
        assert self.acoustic is not None
        acoustic = self.acoustic
        renewed = monotonic()
        try:
            for frame in self.capture.frames(self.listener_stop):
                self.listener_stop.check()
                self.core.permission(
                    session,
                    "desktop.voice.awareness",
                    ("desktop:microphone", "desktop:voice:continuous"),
                )
                if self.muted or monotonic() - self.listener_seen > 10:
                    raise VoiceCancelled("microphone muted or control connection lost")
                if monotonic() - renewed >= 5:
                    self.core.request(
                        session,
                        {
                            "version": 1,
                            "request_id": new_id(),
                            "operation": "claim",
                            "payload": {"resource": "voice"},
                        },
                    )
                    renewed = monotonic()
                with self.core.lock:
                    speaking = acoustic.state == "speaking"
                    decision = (
                        self.reference.clean(frame, speaking)
                        if self.reference is not None
                        else AcousticDecision(
                            frame, "uncertain" if speaking else "human", "local_input"
                        )
                    )
                    frames = acoustic.feed(decision)
                    if frames is None:
                        continue
                # An interrupted turn may still be finishing an issued Core task.
                if self.thread is not None and self.thread.is_alive():
                    self.thread.join(3)
                    if self.thread.is_alive():
                        with self.core.lock:
                            acoustic.cancel()
                            self.view = {
                                **self.view,
                                "voice_state": "aware",
                                "message": "Prior task is still finishing; ask again",
                            }
                        continue
                with self.core.lock:
                    self.listener_stop.check()
                    self.core.permission(
                        session,
                        "desktop.voice.awareness",
                        ("desktop:microphone", "desktop:voice:continuous"),
                    )
                    self.generation += 1
                    self.recognition, self.stop = StopToken(), StopToken()
                    self.thread = Thread(
                        target=self._turn,
                        args=(
                            session,
                            "",
                            "Ask",
                            self.generation,
                            self.stop,
                            self.recognition,
                            frames,
                        ),
                        daemon=True,
                    )
                    self.thread.start()

        except (VoiceError, PermissionError, ValueError, OSError):
            pass
        finally:
            self.listener_stop.cancel()
            self._interrupt_output()
            acoustic.cancel(disable=True)
            self.capture.close()
            with self.core.lock:
                self.view = {
                    **self.view,
                    "voice_state": "off",
                    "continuous_active": False,
                    "message": "Continuous listening stopped; start explicitly to resume",
                }

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
        if self.acoustic is not None:
            with self.core.lock:
                self.acoustic.speaking()
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
        self.listener_stop.cancel()
        # Interrupt native synthesis/playback even while Core is finishing an issued task.
        self.stop.cancel()
        self.recognition.cancel()
        if self.playback is not None:
            self.playback.cancel()
        self.capture.close()
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
        self.listener_seen = monotonic()
        return {**self.view, "voice_settings": self.settings(session)}

    def close(self) -> None:
        self.listener_stop.cancel()
        self.stop.cancel()
        self.recognition.cancel()
        self.capture.close()
        if self.playback is not None:
            self.playback.cancel()
        if self.thread is not None:
            self.thread.join(3)
        if self.listener_thread is not None:
            self.listener_thread.join(3)


def grant_continuous_voice(core: Desktop, session_id: str) -> None:
    """Trusted local CLI opts one already enrolled Desktop session into perception."""
    if (
        not isinstance(session_id, str)
        or len(session_id) != 32
        or any(character not in "0123456789abcdef" for character in session_id)
    ):
        raise ValueError("exact enrolled Desktop session ID required")
    with core.store.transaction():
        session = core.store.get("session", session_id)
        node = core.store.get("node", session["node_id"])
        required = {"desktop:connect", "desktop:microphone"}
        if (
            node["role"] != NodeRole.DESKTOP
            or not node["paired"]
            or node["revoked"]
            or session["revoked"]
            or session["expires_at"] <= core.grid.clock()
            or not required <= set(node["scopes"]) & set(session["scopes"])
        ):
            raise PermissionError("live enrolled Desktop microphone session required")
        for kind, row in (("node", node), ("session", session)):
            row["scopes"] = list(dict.fromkeys([*row["scopes"], "desktop:voice:continuous"]))
            core.store.put(kind, row["id"], row)
        core.store.audit(
            "",
            "continuous_voice_granted",
            {
                "node_id": node["id"],
                "session_id": session_id,
                "source": "trusted-local-cli",
                "audio_started": False,
            },
        )


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
    if not isinstance(config, dict) or set(config) not in (
        {"version", "root", "input_device", "output_device"},
        {"version", "root", "input_device", "output_device", "muted"},
        {
            "version",
            "root",
            "input_device",
            "output_device",
            "muted",
            "input_identity",
            "output_identity",
        },
    ):
        raise ValueError("exact local voice configuration required")
    if (
        type(config["version"]) is not int
        or config["version"] not in {1, 2, 3}
        or (config["version"] in {2, 3} and type(config.get("muted")) is not bool)
        or (config["version"] != 3 and ("input_identity" in config or "output_identity" in config))
        or (config["version"] == 3 and not {"input_identity", "output_identity"} <= set(config))
        or (config["version"] == 1 and "muted" in config)
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
    for identity in (config.get("input_identity"), config.get("output_identity")):
        if identity is not None and (
            not isinstance(identity, dict)
            or set(identity) != {"name", "host_api", "input_channels", "output_channels"}
            or any(
                not isinstance(identity.get(key), str) or not 0 < len(identity[key]) <= 160
                for key in ("name", "host_api")
            )
            or any(
                type(identity.get(key)) is not int or not 0 <= identity[key] <= 256
                for key in ("input_channels", "output_channels")
            )
        ):
            raise ValueError("bounded selected audio identity required")
    root = Path(config["root"]).resolve()
    recognizer = FasterWhisper(root / "models/whisper-base.en")
    reference = PlaybackReference()

    def devices(input_device: int, output_device: int | None) -> tuple[Any, Any, Any]:
        capture = SoundDeviceCapture(input_device)
        if output_device is None:
            return capture, None, None
        quality = root / "quality"
        adapters: list[Synthesizer] = []
        if (quality / "kokoro-fp32.onnx").is_file() and (quality / "voices-hf.bin").is_file():
            adapters.append(KokoroSpeech(quality / "kokoro-fp32.onnx", quality / "voices-hf.bin"))
        if (quality / "piper-parallel.onnx").is_file():
            adapters.append(PiperSpeech(quality / "piper-parallel.onnx"))
        adapters.append(WindowsSpeech())
        return (
            capture,
            SynthesisChain(tuple(adapters)),
            SoundDevicePlayback(output_device, reference),
        )

    def wake_models() -> tuple[WakeDetector, VAD]:
        from .voice_adapters import SherpaWake, SileroVAD

        model = root / "models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"
        return (
            SherpaWake(model, root / "models/keywords.txt"),
            SileroVAD(root / "models/silero_vad.onnx"),
        )

    capture, synthesis, playback = devices(config["input_device"], config["output_device"])
    voice = DesktopVoice(
        core,
        capture,
        recognizer,
        synthesis=synthesis,
        playback=playback,
        profile=oscar_voice_profile(),
        reference=reference,
        config_path=path.resolve(),
        muted=config.get("muted", True),
    )
    voice.capture.require_identity = True
    voice.capture.expected_identity = config.get("input_identity")
    if voice.playback is not None:
        output_adapter: Any = voice.playback
        output_adapter.require_identity = True
        output_adapter.expected_identity = config.get("output_identity")
    voice.device_factory = devices
    model = root / "models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"
    if (
        model.is_dir()
        and (root / "models/keywords.txt").is_file()
        and (root / "models/silero_vad.onnx").is_file()
    ):
        voice.wake_factory = wake_models
    return voice
