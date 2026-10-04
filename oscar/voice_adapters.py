"""Optional local model/audio adapters; no microphone opens on import or preflight."""

import io
import json
import subprocess
import tempfile
import wave
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from threading import Lock
from time import monotonic, sleep
from typing import Any

from .voice_contracts import (
    AudioChunk,
    AudioFrame,
    Origin,
    StopToken,
    Transcript,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
)
from .voice_runtime import AcousticDecision


def optional(name: str) -> Any:
    try:
        return import_module(name)
    except ImportError:
        raise VoiceError("optional voice runtime unavailable: " + name) from None


def samples(frames: tuple[AudioFrame, ...]) -> Any:
    np = optional("numpy")
    return np.asarray([v for f in frames for v in f.samples], dtype="float32")


class SherpaWake:
    def __init__(self, model: Path, keywords: Path):
        s = optional("sherpa_onnx")

        def part(prefix: str) -> str:
            paths = sorted(model.glob(prefix + "*.int8.onnx"))
            if not paths:
                raise VoiceError("wake model missing")
            return str(paths[0])

        self.engine = s.KeywordSpotter(
            tokens=str(model / "tokens.txt"),
            encoder=part("encoder"),
            decoder=part("decoder"),
            joiner=part("joiner"),
            keywords_file=str(keywords),
            num_threads=2,
            provider="cpu",
        )
        self.stream = self.engine.create_stream()

    def detect(self, frame: AudioFrame) -> bool:
        self.stream.accept_waveform(frame.rate, samples((frame,)))
        detected = False
        while self.engine.is_ready(self.stream):
            self.engine.decode_stream(self.stream)
            if self.engine.get_result(self.stream):
                detected = True
                self.engine.reset_stream(self.stream)
        return detected

    def reset(self) -> None:
        self.engine.reset_stream(self.stream)


class SileroVAD:
    def __init__(self, model: Path):
        s = optional("sherpa_onnx")
        config = s.VadModelConfig()
        config.silero_vad.model = str(model)
        config.silero_vad.threshold = 0.5
        config.silero_vad.min_speech_duration = 0.1
        config.silero_vad.min_silence_duration = 0.3
        config.sample_rate = 16000
        self.engine = s.VoiceActivityDetector(config, buffer_size_in_seconds=2)

    def speech(self, frame: AudioFrame) -> bool:
        self.engine.accept_waveform(samples((frame,)))
        result = bool(self.engine.is_speech_detected())
        while not self.engine.empty():
            self.engine.pop()  # never retain ambient segments
        return result

    def reset(self) -> None:
        self.engine.reset()


class FasterWhisper:
    id = "faster-whisper"
    local = True

    def __init__(self, model: Path):
        if not model.is_dir():
            raise VoiceError("STT local model missing; no implicit download")
        try:
            self.engine = optional("faster_whisper").WhisperModel(
                str(model), device="cpu", compute_type="int8", cpu_threads=4, local_files_only=True
            )
        except Exception:
            raise VoiceError("local STT model unavailable or incomplete") from None

    def transcribe(
        self, frames: tuple[AudioFrame, ...], final: bool, stop: StopToken
    ) -> Transcript:
        stop.check()
        if not frames:
            raise VoiceError("empty STT input")
        try:
            segments, info = self.engine.transcribe(
                samples(frames), beam_size=1, vad_filter=False, condition_on_previous_text=False
            )
            text = []
            for segment in segments:
                stop.check()
                text.append(str(segment.text))
            stop.check()
            return Transcript(
                "".join(text).strip()[:4096],
                final,
                str(info.language),
                None,
                frames[0].timestamp,
                frames[-1].timestamp + len(frames[-1].samples) / 16000,
                self.id,
            )
        except VoiceCancelled:
            raise
        except Exception:
            raise VoiceError("local STT inference failed") from None


class SherpaEmbedding:
    def __init__(self, model: Path, model_id: str):
        s = optional("sherpa_onnx")
        config = s.SpeakerEmbeddingExtractorConfig(model=str(model), num_threads=2, provider="cpu")
        if not config.validate():
            raise VoiceError("speaker model invalid")
        self.engine = s.SpeakerEmbeddingExtractor(config)
        self.model_id = model_id

    def extract(self, frames: tuple[AudioFrame, ...], stop: StopToken) -> tuple[float, ...]:
        stop.check()
        if sum(len(f.samples) for f in frames) < 16000:
            raise VoiceError("speaker sample too short")
        if any(f.origin == Origin.PLAYBACK for f in frames):
            raise VoiceError("self output excluded from speaker evidence")
        stream = self.engine.create_stream()
        stream.accept_waveform(16000, samples(frames))
        stream.input_finished()
        if not self.engine.is_ready(stream):
            raise VoiceError("speaker evidence uncertain")
        result = tuple(float(v) for v in self.engine.compute(stream))
        stop.check()
        return result


class WindowsSpeech:
    id = "windows-system-speech"
    local = True

    def synthesize(
        self, text: str, profile: VoiceProfile, utterance_id: str, stop: StopToken
    ) -> Iterable[AudioChunk]:
        stop.check()
        script = Path(__file__).resolve().parents[1] / "scripts/voice_sapi.ps1"
        with tempfile.TemporaryDirectory(prefix="oscar-tts-") as directory:
            path = Path(directory) / "output.wav"
            payload = json.dumps(
                {
                    "text": text[:4096],
                    "path": str(path),
                    "voice": profile.preferred_voice,
                    "rate": round((profile.rate - 1) * 5),
                }
            )
            process = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000,
            )
            try:
                assert process.stdin is not None
                process.stdin.write(payload.encode("utf-8"))
                process.stdin.close()
                deadline = monotonic() + 20
                while process.poll() is None:
                    stop.check()
                    if monotonic() > deadline:
                        raise VoiceError("local TTS timeout")
                    sleep(0.02)
                if process.returncode != 0 or not path.exists():
                    raise VoiceError("installed voice unavailable")
                with wave.open(str(path), "rb") as audio:
                    if audio.getnchannels() != 1 or audio.getsampwidth() != 2:
                        raise VoiceError("unsupported local TTS format")
                    rate = audio.getframerate()
                    while pcm := audio.readframes(rate // 4):
                        stop.check()
                        yield AudioChunk(pcm, rate, self.id, profile.preferred_voice, utterance_id)
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=3)


class PiperSpeech:
    id = "piper"
    local = True

    def __init__(self, model: Path):
        self.voice = optional("piper").PiperVoice.load(str(model))

    def synthesize(
        self, text: str, profile: VoiceProfile, utterance_id: str, stop: StopToken
    ) -> Iterable[AudioChunk]:
        p = optional("piper")
        config = p.SynthesisConfig(length_scale=1 / profile.rate)
        try:
            for chunk in self.voice.synthesize(text, syn_config=config):
                stop.check()
                yield AudioChunk(
                    bytes(chunk.audio_int16_bytes),
                    int(chunk.sample_rate),
                    self.id,
                    profile.preferred_voice,
                    utterance_id,
                )
        except VoiceCancelled:
            raise
        except Exception:
            raise VoiceError("Piper synthesis failed") from None


class PlaybackReference:
    """Conservative scalar echo reference, not a room-calibrated/full AEC claim."""

    def __init__(self) -> None:
        self.lock = Lock()
        self.history: list[tuple[float, tuple[float, ...]]] = []

    def add(self, pcm: bytes, rate: int, at: float) -> None:
        np = optional("numpy")
        audio = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
        if rate != 16000:
            audio = np.interp(
                np.arange(int(len(audio) * 16000 / rate)) * rate / 16000,
                np.arange(len(audio)),
                audio,
            )
        with self.lock:
            self.history.append((at, tuple(float(v) for v in audio)))
            self.history = [(t, a) for t, a in self.history if at - t < 1]

    def clean(self, frame: AudioFrame, speaking: bool) -> AcousticDecision:
        np = optional("numpy")
        with self.lock:
            history = tuple(self.history)
        relevant = [(t, a) for t, a in history if -0.1 <= frame.timestamp - t <= 0.5]
        if not relevant:
            return AcousticDecision(
                frame, "uncertain" if speaking else "human", "playback_reference"
            )
        raw = np.asarray(frame.samples, dtype="float32")
        best = 0.0
        residual = raw
        energy = float(np.dot(raw, raw)) + 1e-9
        at = relevant[0][0]
        size = max(int((t - at) * 16000) + len(a) for t, a in relevant)
        ref = np.zeros(size, dtype="float32")
        for t, a in relevant:
            offset = int((t - at) * 16000)
            ref[offset : offset + len(a)] = a
        # Bounded reference-delay search, including frames crossing output writes.
        for delay in range(0, 3201, 16):
            index = int((frame.timestamp - at) * 16000) - delay
            if index < 0 or index + len(raw) > len(ref):
                continue
            segment = ref[index : index + len(raw)]
            power = float(np.dot(segment, segment)) + 1e-9
            cross = float(np.dot(raw, segment))
            explained = cross * cross / (energy * power)
            if explained > best:
                best = explained
                residual = raw - segment * (cross / power)
        residual = np.clip(residual, -1, 1)
        cleaned = AudioFrame(
            tuple(float(v) for v in residual), frame.timestamp, frame.node_id, origin=frame.origin
        )
        if best > 0.85:
            return AcousticDecision(cleaned, "self_output", "playback_reference")
        # No confidently matched echo is not proof of human speech while rendering.
        if best < 0.05:
            return AcousticDecision(cleaned, "uncertain", "playback_reference")
        return AcousticDecision(cleaned, "human", "playback_reference_residual")


class SoundDeviceCapture:
    def __init__(self, device: int, node_id: str = "windows-voice"):
        self.device, self.node_id = device, node_id
        self.stream: Any = None

    def frames(self, stop: StopToken) -> Iterable[AudioFrame]:
        sd = optional("sounddevice")
        try:
            with sd.InputStream(
                device=self.device, channels=1, samplerate=16000, dtype="float32", blocksize=512
            ) as stream:
                self.stream = stream
                while not stop.event.is_set():
                    data, overflow = stream.read(512)
                    if overflow:
                        raise VoiceError("capture overflow; turn invalidated")
                    yield AudioFrame(
                        tuple(float(x) for x in data[:, 0]),
                        monotonic() - len(data) / 16000,
                        self.node_id,
                    )
        except VoiceError:
            raise
        except Exception:
            raise VoiceError("audio capture unavailable or disconnected") from None
        finally:
            self.stream = None

    def close(self) -> None:
        if self.stream is not None:
            self.stream.abort()


class SoundDevicePlayback:
    def __init__(self, device: int, reference: PlaybackReference):
        self.device, self.reference = device, reference
        self.stream: Any = None
        self.lock = Lock()

    def play(self, chunk: AudioChunk, stop: StopToken) -> None:
        with self.lock:
            stop.check()
            self._play(chunk, stop)

    def _play(self, chunk: AudioChunk, stop: StopToken) -> None:
        sd, np = optional("sounddevice"), optional("numpy")
        audio = np.frombuffer(chunk.pcm, dtype="<i2")
        try:
            with sd.RawOutputStream(
                device=self.device, samplerate=chunk.rate, channels=1, dtype="int16", blocksize=0
            ) as stream:
                self.stream = stream
                for offset in range(0, len(audio), chunk.rate // 32):
                    stop.check()
                    pcm = audio[offset : offset + chunk.rate // 32].tobytes()
                    self.reference.add(pcm, chunk.rate, monotonic())
                    if stream.write(pcm):
                        raise VoiceError("playback underflow")
        except VoiceCancelled:
            raise
        except VoiceError:
            raise
        except Exception:
            raise VoiceError("audio playback unavailable or disconnected") from None
        finally:
            self.stream = None

    def cancel(self) -> None:
        if self.stream is not None:
            self.stream.abort()


def read_wave(
    data: bytes, node: str = "reference", origin: Origin = Origin.SIMULATED
) -> tuple[AudioFrame, ...]:
    np = optional("numpy")
    with wave.open(io.BytesIO(data), "rb") as audio:
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getframerate() != 16000:
            raise VoiceError("reference requires mono PCM16/16k WAV")
        raw = audio.readframes(min(audio.getnframes(), 16000 * 30))
    values = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768
    return tuple(
        AudioFrame(tuple(float(v) for v in values[i : i + 512]), i / 16000, node, origin=origin)
        for i in range(0, len(values), 512)
    )
