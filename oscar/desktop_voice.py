"""Opt-in push-to-talk adapter using prepared Slice 08 executors; no recordings."""

from collections.abc import Iterable
from threading import Thread
from typing import Any

from .desktop import Desktop
from .grid import SessionHandle
from .voice_contracts import AudioFrame, Recognizer, StopToken, VoiceCancelled, VoiceError


class DesktopVoice:
    def __init__(self, core: Desktop, capture: Any, recognizer: Recognizer):
        self.core, self.capture, self.recognizer = core, capture, recognizer
        self.stop = StopToken()
        self.recognition = StopToken()
        self.generation = 0
        self.thread: Thread | None = None
        self.owner: str | None = None
        self.view: dict[str, Any] = {"state": "idle"}

    def start(self, session: SessionHandle, context_id: str = "") -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        if not self.recognizer.local:
            raise PermissionError("desktop dictation requires explicit local recognizer")
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
                try:
                    stream: Iterable[AudioFrame] = self.capture.frames(capture_stop)
                    try:
                        for frame in stream:
                            if capture_stop.event.is_set():
                                break
                            self.core.permission(session, "desktop.voice", ("desktop:microphone",))
                            frames.append(frame)
                            samples += len(frame.samples)
                            if samples >= 15 * 16000:
                                break
                    except VoiceCancelled:
                        recognition.check()
                    if not frames:
                        raise VoiceError("no dictation captured")
                    self.capture.close()
                    with self.core.lock:
                        if generation != self.generation:
                            return
                        self.view = {"state": "processing", "orb": "thinking"}
                    transcript = self.recognizer.transcribe(tuple(frames), True, recognition)
                    recognition.check()
                    with self.core.lock:
                        if generation == self.generation:
                            self.view = self.core.transcript(
                                session, transcript, recognition, context_id
                            )
                except (VoiceError, PermissionError, ValueError, OSError):
                    with self.core.lock:
                        if generation == self.generation:
                            self.view = {
                                "state": "blocked",
                                "epistemic": "UNKNOWN",
                                "message": "Voice capture/recognition unavailable; nothing applied",
                            }
                finally:
                    frames.clear()
                    self.capture.close()

            self.thread = Thread(target=turn, daemon=True)
            self.thread.start()
        return self.view

    def finish(self, session: SessionHandle) -> dict[str, Any]:
        with self.core.lock:
            if self.owner != session.id:
                raise PermissionError("voice turn belongs to another session")
            if self.thread and self.thread.is_alive():
                self.stop.cancel()
                self.view = {
                    "state": "processing",
                    "orb": "thinking",
                    "message": "Finalizing dictation",
                }
            return self.view

    def cancel(self, session: SessionHandle) -> dict[str, Any]:
        with self.core.lock:
            if self.owner not in {None, session.id}:
                raise PermissionError("voice turn belongs to another session")
            self.generation += 1
            self.stop.cancel()
            self.recognition.cancel()
            preview = self.view.get("preview_id")
            if preview:
                self.core.previews.pop(preview, None)
            self.view = {"state": "cancelled", "orb": "attentive"}
            return self.view

    def inspect(self, session: SessionHandle) -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        if self.owner not in {None, session.id}:
            raise PermissionError("voice turn belongs to another session")
        return self.view
