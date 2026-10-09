"""Opt-in push-to-talk adapter using prepared Slice 08 executors; no recordings."""

from collections.abc import Iterable
from threading import Thread
from typing import Any

from .desktop import Desktop
from .grid import SessionHandle
from .voice_contracts import AudioFrame, Recognizer, StopToken, VoiceError


class DesktopVoice:
    def __init__(self, core: Desktop, capture: Any, recognizer: Recognizer):
        self.core, self.capture, self.recognizer = core, capture, recognizer
        self.stop = StopToken()
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
            self.owner, self.stop = session.id, StopToken()
            self.view = {"state": "listening", "orb": "listening"}

            def turn() -> None:
                frames = []
                samples = 0
                try:
                    stream: Iterable[AudioFrame] = self.capture.frames(self.stop)
                    for frame in stream:
                        if self.stop.event.is_set():
                            break
                        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
                        frames.append(frame)
                        samples += len(frame.samples)
                        if samples >= 15 * 16000:
                            break
                    if not frames:
                        raise VoiceError("no dictation captured")
                    token = StopToken()
                    transcript = self.recognizer.transcribe(tuple(frames), True, token)
                    self.view = self.core.transcript(session, transcript, token, context_id)
                except (VoiceError, PermissionError, ValueError, OSError):
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
        if self.owner != session.id:
            raise PermissionError("voice turn belongs to another session")
        self.stop.cancel()
        return {"state": "processing", "orb": "thinking", "message": "Finalizing dictation"}

    def inspect(self, session: SessionHandle) -> dict[str, Any]:
        self.core.permission(session, "desktop.voice", ("desktop:microphone",))
        if self.owner not in {None, session.id}:
            raise PermissionError("voice turn belongs to another session")
        return self.view
