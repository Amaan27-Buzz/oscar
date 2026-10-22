"""Actual prepared local models, synthetic input and memory-only output; opens no audio device."""

import base64
import io
import json
import os
import subprocess
import tempfile
import wave
from dataclasses import replace
from pathlib import Path
from queue import Empty, Queue
from threading import Event
from time import perf_counter

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.contracts import new_id
from oscar.desktop import Desktop
from oscar.desktop_voice import DesktopVoice, grant_continuous_voice
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.mobile import MobileServer
from oscar.policy import PersonalPolicy
from oscar.voice_adapters import (
    FasterWhisper,
    PlaybackReference,
    SherpaWake,
    SileroVAD,
    WindowsSpeech,
    optional,
    read_wave,
)
from oscar.voice_contracts import AudioFrame, Origin, StopToken, VoiceProfile
from oscar.voice_identity import oscar_voice_profile
from oscar.voice_runtime import AcousticDecision, VoiceSession
from scripts.voice_owner import synthesis_models
from scripts.voice_setup import KWS


def synthetic_audio(text):
    profile = VoiceProfile(
        preferred_voice="local-system", provider="windows-system-speech", model="installed-voice"
    )
    chunks = tuple(WindowsSpeech().synthesize(text, profile, new_id(), StopToken()))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        assert all(chunk.rate == 16000 for chunk in chunks)
        audio.writeframes(b"".join(chunk.pcm for chunk in chunks))
    return read_wave(buffer.getvalue())


class Frames:
    def __init__(self, frames):
        self.audio = frames

    def frames(self, stop):
        for frame in self.audio:
            stop.check()
            yield frame

    def close(self):
        pass


class QueuedFrames:
    def __init__(self, frames):
        self.audio = Queue()
        for frame in frames:
            self.audio.put(frame)

    def frames(self, stop):
        while not stop.event.is_set():
            try:
                yield self.audio.get(timeout=0.02)
            except Empty:
                continue

    def close(self):
        pass


class MeasuredRecognizer:
    local = True

    def __init__(self, recognizer):
        self.recognizer, self.id = recognizer, recognizer.id
        self.transcript, self.elapsed = None, 0

    def transcribe(self, frames, final, stop):
        started = perf_counter()
        self.transcript = self.recognizer.transcribe(frames, final, stop)
        self.elapsed = perf_counter() - started
        return self.transcript


class MemoryPlayback:
    """Synthetic output sink; PCM reached this sink, never a physical loudspeaker."""

    def __init__(self, *, hold=False):
        self.reference = PlaybackReference()
        self.chunks, self.times = [], []
        self.entered, self.cancelled = Event(), Event()
        self.hold = hold

    def play(self, chunk, stop):
        stop.check()
        at = 100 + sum(len(c.pcm) / (2 * c.rate) for c in self.chunks)
        self.reference.add(chunk.pcm, chunk.rate, at)
        self.chunks.append(chunk)
        self.times.append(at)
        self.entered.set()
        if self.hold:
            stop.event.wait(20)
            stop.check()

    def finish(self, utterance):
        assert self.chunks and all(c.utterance_id == utterance for c in self.chunks)

    def cancel(self):
        self.cancelled.set()


def main():
    model_root = Path(".oscar/voice/models")
    wake = SherpaWake(model_root / KWS, model_root / "keywords.txt")
    vad = SileroVAD(model_root / "silero_vad.onnx")
    recognizer = MeasuredRecognizer(FasterWhisper(model_root / "whisper-base.en"))
    synthesis = synthesis_models()
    report = {
        "classification": "ACTUAL_LOCAL_MODELS_SYNTHETIC_AUDIO_CORE_INTEGRATION",
        "microphone": "NOT_RUN",
        "speaker_playback": "NOT_RUN",
        "physical_barge_in_and_room_aec": "NOT_RUN",
        "owner_voice_match": "NOT_RUN",
        "native_product_bridge": "NOT_RUN",
        "cases": [],
    }
    with tempfile.TemporaryDirectory(prefix="oscar-voice-integration-") as directory:
        root = Path(directory)
        with Harness(
            root / "core.db",
            root / "workspace",
            Path("config/development-models.json"),
            start_services=False,
        ) as harness:
            target = harness.node_id
            scopes = (
                "heartbeat",
                "desktop:connect",
                "desktop:inspect",
                "desktop:text",
                "desktop:microphone",
                "desktop:conversation:read",
                "desktop:conversation:retain",
                "math",
                "files:write",
                "control:inspect:" + target,
                "control:approve:" + target,
                "control:cancel:" + target,
            )
            harness.grid.register(Node("synthetic-voice-owner", NodeRole.DESKTOP, scopes))
            owner = harness.grid.pair("synthetic-voice-owner", scopes)
            core = Desktop(
                harness.runtime,
                PersonalPolicy(harness.store),
                {target: (harness.dispatcher, harness.session)},
            )
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public = base64.b64encode(
                key.public_key().public_bytes(
                    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
                )
            ).decode()
            core.register_owner_key(owner, public, owner_authorized=True)

            def call(operation, payload):
                return core.request(
                    owner,
                    {
                        "version": 1,
                        "request_id": new_id(),
                        "operation": operation,
                        "payload": payload,
                    },
                )

            review = call(
                "authority_challenge",
                {
                    "mode": "full",
                    "lifetime_seconds": 600,
                    "capabilities": [
                        {
                            "node_id": target,
                            "session_id": harness.session.id,
                            "capability_id": cap,
                        }
                        for cap in ("math.add", "files.write")
                    ],
                    "account_ids": [],
                    "resolve_ask_rules": [],
                },
            )
            signature = key.sign(
                base64.b64decode(review["signing_payload"]),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
            call(
                "authority_complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": base64.b64encode(signature).decode(),
                },
            )
            captured = []
            for phrase in (
                "Oscar. What is two plus three?",
                "Oscar. Please write agenda with text ready for review.",
            ):
                wake.reset()
                vad.reset()
                front = VoiceSession(wake, vad, lambda: None)
                audio = synthetic_audio(phrase)
                silence_at = audio[-1].timestamp + len(audio[-1].samples) / 16000
                audio += tuple(
                    AudioFrame(
                        (0.0,) * 512, silence_at + i * 0.032, "synthetic", origin=Origin.SIMULATED
                    )
                    for i in range(60)
                )
                completed = None
                started = perf_counter()
                for frame in audio:
                    completed = front.feed(
                        AcousticDecision(frame, "human", "known_synthetic_input")
                    )
                    if completed:
                        break
                assert completed, "actual wake/VAD did not complete the synthetic utterance"
                events = list(dict.fromkeys(event.kind for event in front.events))
                assert "wake" in events and "speech_ended" in events
                captured.append(completed)
                sink = MemoryPlayback()
                core.voice = DesktopVoice(
                    core,
                    Frames(completed),
                    recognizer,
                    mode="Ask",
                    muted=False,
                    synthesis=synthesis,
                    playback=sink,
                    profile=oscar_voice_profile(),
                )
                core.voice.start(owner)
                core.voice.thread.join(90)
                assert not core.voice.thread.is_alive(), "voice pipeline timed out"
                view = core.voice.inspect(owner)
                assert view["state"] == "verified", view
                assert view["voice_output"] == "reported" and sink.chunks
                if "agenda" in phrase:
                    content = harness.files.read("agenda").decode()
                    assert "ready for review" in content.lower(), content
                else:
                    assert view["value"] == "5", view
                report["cases"].append(
                    {
                        "source_phrase": phrase,
                        "transcript": recognizer.transcript.text,
                        "task_state": view["state"],
                        "evidence_count": len(view["evidence"]),
                        "wake_vad_events": events,
                        "stt_seconds": round(recognizer.elapsed, 3),
                        "total_seconds": round(perf_counter() - started, 3),
                        "response_provider": sink.chunks[0].provider,
                        "response_pcm_bytes": sum(len(chunk.pcm) for chunk in sink.chunks),
                    }
                )
            turns = core.conversation(owner)["turns"]
            assert len(turns) >= 3 and all(turn["retained"] for turn in turns)
            report["canonical_conversation_turns"] = len(turns)

            # Interrupt actual synthesis into the memory sink using actual VAD on synthetic speech.
            sink = MemoryPlayback(hold=True)
            core.voice = DesktopVoice(
                core,
                Frames(captured[0]),
                recognizer,
                mode="Ask",
                muted=False,
                synthesis=synthesis,
                playback=sink,
                profile=oscar_voice_profile(),
            )
            core.voice.start(owner)
            assert sink.entered.wait(30), "speech output did not begin"
            task_id = core.voice.view["task_id"]
            front = VoiceSession(wake, vad, lambda: core.voice.cancel(owner))
            front.speaking()
            np = optional("numpy")
            chunk = sink.chunks[0]
            pcm = np.frombuffer(chunk.pcm, dtype="<i2").astype("float32") / 32768
            if chunk.rate != 16000:
                pcm = np.interp(
                    np.arange(int(len(pcm) * 16000 / chunk.rate)) * chunk.rate / 16000,
                    np.arange(len(pcm)),
                    pcm,
                )
            frame = AudioFrame(tuple(float(v) for v in pcm[:512]), sink.times[0], "synthetic-echo")
            decision = sink.reference.clean(frame, True)
            assert decision.classification == "self_output", decision.classification
            front.feed(decision)
            assert not sink.cancelled.is_set()
            interrupt_started = perf_counter()
            for i, frame in enumerate(captured[0]):
                front.feed(
                    AcousticDecision(
                        replace(frame, timestamp=200 + i * 0.032),
                        "human",
                        "known_synthetic_interruption",
                    )
                )
                if sink.cancelled.is_set():
                    break
            assert sink.cancelled.is_set(), "actual VAD did not interrupt synthetic playback"
            core.voice.thread.join(10)
            assert not core.voice.thread.is_alive()
            assert core.voice.view["voice_state"] == "cancelled"
            assert core.voice.view["state"] == "verified"
            assert harness.store.task(task_id).state == "verified"
            report["self_output_suppression"] = "PASS_SYNTHETIC_EXACT_REFERENCE"
            report["barge_in"] = "PASS_ACTUAL_VAD_KNOWN_SYNTHETIC_HUMAN_INPUT"
            report["synthetic_barge_in_processing_ms"] = round(
                (perf_counter() - interrupt_started) * 1000, 3
            )
            report["issued_task_not_replayed_or_reversed"] = True
            # Same product continuous loop, with actual local wake/VAD/STT and no audio devices.
            wake.reset()
            vad.reset()
            audio = synthetic_audio("Oscar. What is two plus three?")
            silence_at = audio[-1].timestamp + len(audio[-1].samples) / 16000
            audio += tuple(
                AudioFrame(
                    (0.0,) * 512, silence_at + i * 0.032, "synthetic", origin=Origin.SIMULATED
                )
                for i in range(60)
            )
            grant_continuous_voice(core, owner.id)
            core.voice = DesktopVoice(
                core, QueuedFrames(audio), recognizer, muted=False, wake=wake, vad=vad
            )
            before = len(harness.store.all("task"))
            core.voice.listen(owner)
            deadline = perf_counter() + 90
            while perf_counter() < deadline:
                view = core.voice.inspect(owner)
                if view.get("state") == "verified" and len(harness.store.all("task")) > before:
                    break
                Event().wait(0.1)
            else:
                raise AssertionError("actual continuous local model path did not verify")
            assert view["value"] == "5"
            assert "wake" in [event.kind for event in core.voice.acoustic.events]
            core.voice.cancel(owner)
            core.voice.close()
            assert not core.voice.listener_thread.is_alive()
            report["continuous_wake_dialogue"] = "PASS_ACTUAL_LOCAL_MODELS_SYNTHETIC_INPUT"
            report["continuous_cancel"] = "PASS_LISTENER_STOPPED_NO_REPLAY"
            call("authority_revoke", {})
            # Production Rust Bridge and HTTP client; fixed synthetic capture opens no device.
            core.voice = DesktopVoice(
                core,
                Frames(captured[0]),
                recognizer,
                muted=False,
                synthesis=synthesis,
                playback=MemoryPlayback(),
                profile=oscar_voice_profile(),
            )
            with MobileServer(core) as server:
                bootstrap = root / "synthetic-native-bootstrap.json"
                bootstrap.write_text(
                    json.dumps(
                        {
                            "url": server.url,
                            "node": owner.node_id,
                            "session": owner.id,
                            "token": owner.token,
                            "reference": True,
                        }
                    ),
                    encoding="utf-8",
                )
                bootstrap.chmod(0o600)
                env = {**os.environ, "OSCAR_VOICE_REFERENCE_BOOTSTRAP": str(bootstrap)}
                native = subprocess.run(
                    [
                        "cargo",
                        "+1.99.0",
                        "test",
                        "--manifest-path",
                        "desktop/src-tauri/Cargo.toml",
                        "core::tests::synthetic_voice_loopback_bridge",
                        "--",
                        "--ignored",
                        "--exact",
                        "--nocapture",
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=240,
                )
                Path(".oscar/software-voice-native-bridge.log").write_text(
                    native.stdout + native.stderr, encoding="utf-8"
                )
                assert native.returncode == 0, "native bridge failed; inspect private local log"
                assert "1 passed" in native.stdout, "native bridge test was not executed"
                report["native_product_bridge"] = (
                    "PASS_PRODUCTION_RUST_BRIDGE_LOOPBACK_SYNTHETIC_AUDIO"
                )
                report["native_webview_and_audio_devices"] = "NOT_RUN"
            core.voice.close()
            assert not harness.store.all("executive_goal"), "declined automation created a goal"
    path = Path(".oscar/software-voice-reference.json")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
