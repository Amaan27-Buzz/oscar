"""Windows owner acceptance: explicit capture; reference/preflight never open devices."""

import argparse
import hashlib
import json
import platform
import queue
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Thread
from time import monotonic, perf_counter

from oscar.contracts import Epistemic, TaskState, new_id
from oscar.harness import Harness
from oscar.policy import PersonalPolicy
from oscar.voice_adapters import (
    FasterWhisper,
    KokoroSpeech,
    PiperSpeech,
    PlaybackReference,
    SherpaEmbedding,
    SherpaWake,
    SileroVAD,
    SoundDeviceCapture,
    SoundDevicePlayback,
    WindowsSpeech,
    audio_settings,
    optional,
    read_wave,
)
from oscar.voice_contracts import (
    AudioFrame,
    Recognizer,
    StopToken,
    Synthesizer,
    Transcript,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
    VoiceResponse,
)
from oscar.voice_core import VoiceCore
from oscar.voice_identity import PersonaProfile, VoiceMap, VoiceMatch, oscar_voice_profile
from oscar.voice_runtime import RecognitionChain, SynthesisChain, VoiceSession
from scripts.voice_setup import KWS

ROOT = Path(".oscar/voice")


def models() -> tuple[SherpaWake, SileroVAD, RecognitionChain, SherpaEmbedding]:
    root = ROOT / "models"
    digest = hashlib.sha256((root / "speaker.onnx").read_bytes()).hexdigest()
    recognizers: list[Recognizer] = []
    preferred = ROOT / "quality/turbo"
    if (preferred / "model.bin").is_file():
        try:
            recognizers.append(FasterWhisper(preferred, device="cuda", compute_type="float16"))
        except VoiceError:
            print("Preferred GPU STT unavailable; explicit CPU fallback.")
    recognizers.append(FasterWhisper(root / "whisper-base.en"))
    return (
        SherpaWake(root / KWS, root / "keywords.txt"),
        SileroVAD(root / "silero_vad.onnx"),
        RecognitionChain(tuple(recognizers)),
        SherpaEmbedding(root / "speaker.onnx", digest),
    )


def synthesis_models() -> SynthesisChain:
    """Only prepared assets; emergency System.Speech does not become primary identity."""
    adapters: list[Synthesizer] = []
    quality = ROOT / "quality"
    neural = quality / "kokoro-fp32.onnx"
    if neural.is_file() and (quality / "voices-hf.bin").is_file():
        try:
            adapters.append(KokoroSpeech(neural, quality / "voices-hf.bin"))
        except VoiceError:
            print("Kokoro unavailable; explicit neural fallback.")
    if (quality / "piper-parallel.onnx").is_file():
        try:
            adapters.append(PiperSpeech(quality / "piper-parallel.onnx"))
        except VoiceError:
            print("Piper unavailable; emergency platform fallback.")
    return SynthesisChain(tuple(adapters) + (WindowsSpeech(),))


def preflight() -> int:
    sd = optional("sounddevice")
    hosts = sd.query_hostapis()
    for index, device in enumerate(sd.query_devices()):
        host = hosts[device["hostapi"]]["name"]
        if "WASAPI" in host:
            print(
                index,
                device["name"],
                "input",
                device["max_input_channels"],
                "output",
                device["max_output_channels"],
                "WASAPI",
            )
            settings = audio_settings(sd, index)
            try:
                if device["max_input_channels"]:
                    sd.check_input_settings(
                        device=index,
                        channels=1,
                        dtype="float32",
                        samplerate=16000,
                        extra_settings=settings,
                    )
                if device["max_output_channels"]:
                    sd.check_output_settings(
                        device=index,
                        channels=1,
                        dtype="int16",
                        samplerate=16000,
                        extra_settings=settings,
                    )
                print("  shared-mode 16k mono format: supported (no stream opened)")
            except Exception:
                print("  shared-mode 16k mono format: unavailable; choose another endpoint")
    models()
    print("Local models load. Device inventory only; microphone/playback NOT RUN.")
    return 0


def reference() -> int:
    wake, vad, stt, embedding = models()
    token = StopToken()
    profile = VoiceProfile(
        preferred_voice="local-system", provider="windows-system-speech", model="installed-voice"
    )
    started = perf_counter()
    iterator = iter(
        WindowsSpeech().synthesize("Oscar. What is two plus three?", profile, "reference", token)
    )
    first = next(iterator)
    first_audio_ms = (perf_counter() - started) * 1000
    chunks = [first, *iterator]
    tts_ms = (perf_counter() - started) * 1000
    import io
    import wave

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"".join(c.pcm for c in chunks))
    frames = read_wave(buffer.getvalue())
    latencies: dict[str, float] = {"tts_total_ms": tts_ms, "first_tts_audio_ms": first_audio_ms}
    wake_at = None
    vad_at = None
    started = perf_counter()
    for frame in frames:
        if vad.speech(frame) and vad_at is None:
            vad_at = frame.timestamp
        if wake.detect(frame) and wake_at is None:
            wake_at = frame.timestamp
    latencies["wake_vad_inference_total_ms"] = (perf_counter() - started) * 1000
    started = perf_counter()
    partial = stt.transcribe(frames[: len(frames) // 2], False, token)
    latencies["partial_stt_ms"] = (perf_counter() - started) * 1000
    started = perf_counter()
    final = stt.transcribe(frames, True, token)
    latencies["final_stt_ms"] = (perf_counter() - started) * 1000
    started = perf_counter()
    vector = embedding.extract(frames, token)
    latencies["speaker_embedding_ms"] = (perf_counter() - started) * 1000
    replay_match = "NOT_ENROLLED"
    if (ROOT / "enrollment.json").is_file():
        enrolled = json.loads((ROOT / "enrollment.json").read_text())
        verifier = VoiceMatch(embedding.model_id)
        if enrolled["model_id"] == embedding.model_id and enrolled.get("match_confirmed"):
            verifier.enroll("owner", tuple(enrolled["vector"]), confirmed=True)
            replay_match = verifier.verify(vector, source_model=embedding.model_id).outcome
    started = perf_counter()
    with Harness(
        ROOT / "reference.db", ROOT / "reference-workspace", Path("config/development-models.json")
    ) as harness:
        core = VoiceCore(
            harness.runtime,
            PersonalPolicy(harness.store),
            {harness.node_id: (harness.dispatcher, harness.session)},
        )
        result = core.handle(final, token, granted=frozenset({"math"}))
    latencies["core_handoff_ms"] = (perf_counter() - started) * 1000
    response_started = perf_counter()
    response_stream = iter(
        synthesis_models().synthesize(
            result.text, oscar_voice_profile(), "reference-response", StopToken()
        )
    )
    response_chunk = next(response_stream)
    latencies["response_first_audio_ms"] = (perf_counter() - response_started) * 1000
    response_chunks = [response_chunk, *response_stream]
    latencies["response_synthesis_total_ms"] = (perf_counter() - response_started) * 1000
    report = {
        "evidence_class": "REFERENCE_MODEL_EXECUTION_SYNTHETIC_AUDIO",
        "microphone": "NOT_RUN",
        "speaker_playback": "NOT_RUN",
        "response_tts_provider": response_chunk.provider,
        "response_pcm_bytes": sum(len(c.pcm) for c in response_chunks),
        "owner_voice": "NOT_RUN",
        "source_audio": "Windows System.Speech synthetic original acceptance phrase",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "models": json.loads((ROOT / "models/manifest.json").read_text()),
        "latency": latencies,
        "wake_at_audio_seconds": wake_at,
        "speech_at_audio_seconds": vad_at,
        "partial_observed": bool(partial.text),
        "final_transcript": final.text,
        "embedding_dimensions": len(vector),
        "synthetic_reference_match": replay_match,
        "task_state": result.state,
        "epistemic": result.epistemic,
        "task_id": result.task_id,
        "barge_in_stop_ms": None,
        "real_device_performance": "UNKNOWN",
    }
    (ROOT / "reference-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return (
        0
        if wake_at is not None and vad_at is not None and result.state == TaskState.VERIFIED
        else 1
    )


def enroll(device: int) -> int:
    print("Enrollment retains a sensitive local embedding, not raw speech. No spoof resistance.")
    if input("Type ENROLL to capture five seconds of your voice: ") != "ENROLL":
        return 1
    _, _, _, embedding = models()
    capture, token = SoundDeviceCapture(device), StopToken()
    frames = []
    started = monotonic()
    try:
        for frame in capture.frames(token):
            frames.append(frame)
            if monotonic() - started >= 5:
                token.cancel()
                break
    finally:
        capture.close()
    vector = embedding.extract(tuple(frames), StopToken())
    match = VoiceMatch(embedding.model_id)
    match.enroll("owner", vector, confirmed=True)
    linked = input("Type LINK to separately link this profile to Voice Map: ") == "LINK"
    ROOT.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        account = subprocess.check_output(["whoami"], text=True).strip()
        subprocess.run(
            ["icacls", str(ROOT), "/inheritance:r", "/grant:r", account + ":(OI)(CI)F"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    path = ROOT / "enrollment.json"
    path.write_text(
        json.dumps(
            {
                "model_id": embedding.model_id,
                "vector": vector,
                "match_confirmed": True,
                "map_confirmed": linked,
            }
        ),
        encoding="utf-8",
    )
    print(
        "Enrollment stored locally. Thresholds uncalibrated; physical speaker acceptance pending."
    )
    return 0


def run(device: int, output: int, seconds: int, allowed: bool, require_match: bool = False) -> int:
    if not allowed:
        raise PermissionError("run requires --allow-harmless-math owner grant")
    wake, vad, stt, embedding = models()
    match, map_ = VoiceMatch(embedding.model_id), VoiceMap(embedding.model_id)
    enrollment_path = ROOT / "enrollment.json"
    enrollment_snapshot = enrollment_path.read_bytes() if enrollment_path.is_file() else None
    if (ROOT / "enrollment.json").is_file():
        data = json.loads((ROOT / "enrollment.json").read_text())
        if data["model_id"] != embedding.model_id:
            raise VoiceError("enrollment model changed; owner re-enrollment required")
        if data.get("match_confirmed"):
            match.enroll("owner", tuple(data["vector"]), confirmed=True)
        if data.get("map_confirmed"):
            map_.link("owner", tuple(data["vector"]), confirmed=True)
    capture, reference_ = SoundDeviceCapture(device), PlaybackReference()
    playback = SoundDevicePlayback(output, reference_)
    output_token, input_token, lifetime = StopToken(), StopToken(), StopToken()
    inputs: queue.Queue[AudioFrame | VoiceError] = queue.Queue(maxsize=16)
    results: queue.Queue[tuple[int, Transcript | VoiceResponse | VoiceError]] = queue.Queue(
        maxsize=8
    )
    commands: queue.Queue[str] = queue.Queue(maxsize=4)
    generation = 0
    capture_failure: list[VoiceError] = []

    def interrupt() -> None:
        nonlocal output_token, input_token, generation
        output_token.cancel()
        input_token.cancel()
        playback.cancel()
        generation += 1
        output_token, input_token = StopToken(), StopToken()

    synthesis = synthesis_models()
    session = VoiceSession(wake, vad, interrupt)

    def capture_worker() -> None:
        try:
            for frame in capture.frames(lifetime):
                inputs.put(frame, timeout=0.5)
        except (VoiceError, queue.Full):
            capture_failure.append(VoiceError("capture disconnected or overflowed"))
            lifetime.cancel()
            try:
                inputs.put_nowait(VoiceError("capture disconnected or overflowed"))
            except queue.Full:
                pass

    def keyboard() -> None:
        while not lifetime.event.is_set():
            try:
                command = input().strip().lower()
            except EOFError:
                lifetime.cancel()
                return
            try:
                commands.put_nowait(command)
            except queue.Full:
                pass
            if command == "q":
                return

    def inference(frames: tuple[AudioFrame, ...], final: bool, turn: int, token: StopToken) -> None:
        nonlocal map_
        try:
            transcript = stt.transcribe(frames, final, token)
            if final:
                current_enrollment = (
                    enrollment_path.read_bytes() if enrollment_path.is_file() else None
                )
                if current_enrollment != enrollment_snapshot:
                    match.forget("owner")
                    map_ = VoiceMap(embedding.model_id)
                evidence = None
                try:
                    vector = embedding.extract(frames, token)
                    evidence = match.verify(vector, source_model=embedding.model_id)
                    perception = map_.observe((vector,), source_model=embedding.model_id)
                    print(
                        "Voice Match:",
                        evidence.outcome,
                        "score:",
                        evidence.score,
                        "Voice Map:",
                        tuple(p.outcome for p in perception),
                        "NO AUTHORITY GRANTED",
                    )
                except VoiceError:
                    print("Voice Match/Map: uncertain; NO AUTHORITY GRANTED")
                with Harness(
                    ROOT / "owner-tasks.db",
                    ROOT / "owner-workspace",
                    Path("config/development-models.json"),
                ) as harness:
                    core = VoiceCore(
                        harness.runtime,
                        PersonalPolicy(harness.store),
                        {harness.node_id: (harness.dispatcher, harness.session)},
                    )
                    response = core.handle(
                        transcript,
                        token,
                        granted=frozenset({"math"}),
                        require_match=require_match,
                        speaker=evidence,
                    )
                results.put_nowait((turn, response))
            else:
                results.put_nowait((turn, transcript))
        except VoiceCancelled:
            return
        except (VoiceError, queue.Full):
            try:
                results.put_nowait((turn, VoiceError("voice inference failed")))
            except queue.Full:
                pass

    def speak(response: VoiceResponse, token: StopToken) -> None:
        expressive, profile = PersonaProfile().express(
            response, oscar_voice_profile(), serious=response.state != TaskState.VERIFIED
        )
        utterance_id = new_id()
        try:
            for chunk in synthesis.synthesize(expressive.text, profile, utterance_id, token):
                playback.play(chunk, token)
        except VoiceCancelled:
            pass
        except VoiceError:
            print("TTS/playback failed; text result remains available.")
        finally:
            try:
                playback.finish(utterance_id)
            except VoiceError:
                print("Playback completion unverified; text result remains available.")

    Thread(target=capture_worker, daemon=True).start()
    Thread(target=keyboard, daemon=True).start()
    deadline = monotonic() + seconds
    partial_at = monotonic()
    speaking_thread: Thread | None = None
    print(
        "Say OSCAR, then 'what is two plus three'. "
        "Enter p manual, b barge-in test, c cancel, q stop."
    )
    print(
        "No raw audio/transcript retention. Harmless arithmetic tasks retain normal Core evidence."
    )
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = None
        try:
            while monotonic() < deadline and not lifetime.event.is_set():
                try:
                    command = commands.get_nowait()
                    if command == "q":
                        break
                    if command == "p":
                        session.activate()
                    if command == "c":
                        session.cancel()
                    if command == "b":
                        session.cancel()
                        response = VoiceResponse(
                            "Oscar is speaking for the barge in test. Please interrupt me "
                            "while these words are playing. This is a harmless audio test. "
                            "I should stop speaking and listen when your speech is detected. "
                            "Oscar must never wake on its own output or enroll that output "
                            "as a human speaker. The owner must observe the actual result.",
                            "",
                            TaskState.PARTIALLY_VERIFIED,
                            Epistemic.REPORTED,
                        )
                        session.speaking()
                        speaking_thread = Thread(
                            target=speak, args=(response, output_token), daemon=True
                        )
                        speaking_thread.start()
                except queue.Empty:
                    pass
                if speaking_thread is not None and not speaking_thread.is_alive():
                    speaking_thread = None
                    if session.state == "speaking":
                        session.state = "aware"
                try:
                    turn, result = results.get_nowait()
                    if turn == generation:
                        if isinstance(result, VoiceResponse):
                            print(result.text, result.state, result.epistemic, result.task_id)
                            session.speaking()
                            speaking_thread = Thread(
                                target=speak, args=(result, output_token), daemon=True
                            )
                            speaking_thread.start()
                        elif isinstance(result, Transcript):
                            print("partial:", result.text)
                        else:
                            print("Voice inference blocked.")
                            session.cancel()
                except queue.Empty:
                    pass
                try:
                    frame = inputs.get(timeout=0.1)
                except queue.Empty:
                    continue
                if isinstance(frame, VoiceError):
                    raise frame
                finished = session.feed(reference_.clean(frame, session.state == "speaking"))
                for event in session.events:
                    if event.at == frame.timestamp and event.kind in {
                        "wake",
                        "speech_started",
                        "speech_ended",
                        "barge_in",
                        "capture_timeout",
                    }:
                        print("acoustic:", event.kind, event.status)
                if finished:
                    pending = executor.submit(inference, finished, True, generation, input_token)
                elif (
                    session.state == "listening"
                    and len(session.frames) > 30
                    and monotonic() - partial_at > 1
                    and (pending is None or pending.done())
                ):
                    pending = executor.submit(
                        inference, tuple(session.frames), False, generation, input_token
                    )
                    partial_at = monotonic()
        finally:
            lifetime.cancel()
            session.cancel(disable=True)
            capture.close()
            if speaking_thread is not None:
                speaking_thread.join(timeout=3)
    if capture_failure:
        raise capture_failure[0]
    print(
        "Stopped. Owner microphone/barge-in/Match acceptance needs observed results; "
        "no PASS inferred."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "reference", "enroll", "forget", "run"))
    parser.add_argument("--input", type=int)
    parser.add_argument("--output", type=int)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--allow-harmless-math", action="store_true")
    parser.add_argument("--require-voice-match", action="store_true")
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    if args.command == "preflight":
        return preflight()
    if args.command == "reference":
        return reference()
    if args.command == "forget":
        (ROOT / "enrollment.json").unlink(missing_ok=True)
        print("Live enrollment file removed; no secure erasure/backups claim.")
        return 0
    if args.input is None or not 1 <= args.seconds <= 600:
        parser.error("explicit input device and bounded duration required")
    if args.command == "enroll":
        return enroll(args.input)
    if args.output is None:
        parser.error("explicit output device required")
    return run(
        args.input, args.output, args.seconds, args.allow_harmless_math, args.require_voice_match
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VoiceError, PermissionError, FileNotFoundError):
        print("BLOCKED: voice runtime/model/permission unavailable; see docs/VOICE-CORE.md.")
        raise SystemExit(1) from None
