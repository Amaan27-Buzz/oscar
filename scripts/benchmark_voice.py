"""Opt-in local fixture benchmark: no device opens, network or model downloads."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import threading
import wave
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from statistics import median
from time import perf_counter

from oscar.voice_adapters import (
    FasterWhisper,
    KokoroSpeech,
    PiperSpeech,
    SherpaEmbedding,
    WindowsSpeech,
    optional,
    read_wave,
)
from oscar.voice_contracts import (
    AudioFrame,
    Origin,
    StopToken,
    Transcript,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
)

TEXTS = (
    "Oscar. The connection is restored. Your task is still waiting for approval.",
    "Please move the review to Thursday at half past three. Do not send the invitation yet.",
    "The temperature is twenty one degrees Celsius. The offline node cannot accept a new task.",
    "I checked the result. One requirement is verified; the remaining two are unknown.",
)


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def errors(expected: str, actual: str) -> tuple[int, int]:
    a, b = words(expected), words(actual)
    row = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        nxt = [i]
        for j, right in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j - 1] + (left != right)))
        row = nxt
    return row[-1], len(a)


class ParakeetReference:
    """Existing sherpa executor, only an explicit local benchmark candidate."""

    def __init__(self, model: Path):
        files = {part: model / (part + ".int8.onnx") for part in ("encoder", "decoder", "joiner")}
        if any(not p.is_file() for p in files.values()) or not (model / "tokens.txt").is_file():
            raise VoiceError("Parakeet local assets missing")
        self.engine = optional("sherpa_onnx").OfflineRecognizer.from_transducer(
            **{name: str(path) for name, path in files.items()},
            tokens=str(model / "tokens.txt"),
            model_type="nemo_transducer",
            num_threads=4,
        )

    def transcribe(self, frames: tuple, final: bool, stop: StopToken) -> Transcript:
        stop.check()
        stream = self.engine.create_stream()
        audio = optional("numpy").asarray([v for f in frames for v in f.samples], dtype="float32")
        stream.accept_waveform(16000, audio)
        self.engine.decode_stream(stream)
        stop.check()
        return Transcript(
            str(stream.result.text).strip(),
            final,
            None,
            None,
            frames[0].timestamp,
            frames[-1].timestamp + len(frames[-1].samples) / 16000,
            "sherpa-parakeet-v3-reference",
        )


class Resources:
    """Sample process CPU/RSS and whole-GPU utilization; GPU includes other processes."""

    def __init__(self) -> None:
        self.done = threading.Event()
        self.rows: list[dict[str, float]] = []
        self.process = optional("psutil").Process()
        self.thread = threading.Thread(target=self.poll, daemon=True)

    def poll(self) -> None:
        self.process.cpu_percent()
        while not self.done.is_set():
            row = {
                "rss_mb": self.process.memory_info().rss / 1e6,
                "process_cpu_percent": self.process.cpu_percent(),
            }
            try:
                data = (
                    subprocess.check_output(
                        [
                            "nvidia-smi",
                            "--query-gpu=memory.used,utilization.gpu",
                            "--format=csv,noheader,nounits",
                        ],
                        text=True,
                        timeout=3,
                        creationflags=0x08000000 if os.name == "nt" else 0,
                    )
                    .strip()
                    .split(",")
                )
                row.update(gpu_memory_mib=float(data[0]), gpu_util_percent=float(data[1]))
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            self.rows.append(row)
            self.done.wait(0.1)

    def start(self) -> None:
        self.thread.start()

    def finish(self) -> dict[str, float]:
        self.done.set()
        self.thread.join(timeout=4)
        return {
            "peak_" + k: max(r[k] for r in self.rows if k in r)
            for k in {k for r in self.rows for k in r}
        }


def wav(chunks: list, path: Path) -> None:
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(chunks[0].rate)
        out.writeframes(b"".join(c.pcm for c in chunks))


def assess_samples(root: Path, model: Path, device: str, compute: str) -> int:
    """Reference roundtrip/consistency metrics cannot verify human naturalness."""
    from oscar.voice_identity import cosine

    np = optional("numpy")
    stt = FasterWhisper(model, device=device, compute_type=compute)
    speaker = Path(".oscar/voice/models/speaker.onnx")
    with speaker.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    embedding = SherpaEmbedding(speaker, digest)
    reports = []
    for provider, voice in (
        ("kokoro", "oscar-reference"),
        ("piper", "alba"),
        ("windows-system-speech", "local-system"),
    ):
        vectors, rows = [], []
        total_errors = total_words = 0
        for i, text in enumerate(TEXTS):
            with wave.open(str(root / f"{provider}-{voice}-{i}.wav"), "rb") as audio:
                if audio.getnchannels() != 1 or audio.getsampwidth() != 2:
                    raise ValueError("reference PCM format required")
                rate = audio.getframerate()
                values = (
                    np.frombuffer(audio.readframes(audio.getnframes()), dtype="<i2").astype(
                        "float32"
                    )
                    / 32768
                )
            peak = float(np.max(np.abs(values)))
            rms = float(np.sqrt(np.mean(values * values)))
            values = np.interp(
                np.arange(int(len(values) * 16000 / rate)) * rate / 16000,
                np.arange(len(values)),
                values,
            )
            frames = tuple(
                AudioFrame(
                    tuple(float(v) for v in values[j : j + 512]),
                    j / 16000,
                    "synthetic-quality",
                    origin=Origin.SIMULATED,
                )
                for j in range(0, len(values), 512)
            )
            result = stt.transcribe(frames, True, StopToken())
            wrong, count = errors(text, result.text)
            total_errors += wrong
            total_words += count
            vectors.append(embedding.extract(frames, StopToken()))
            rows.append(
                {
                    "fixture": i,
                    "transcript_status": "REPORTED",
                    "transcript": result.text,
                    "word_errors": wrong,
                    "words": count,
                    "peak": peak,
                    "rms": rms,
                }
            )
        consistency = [cosine(a, b) for i, a in enumerate(vectors) for b in vectors[i + 1 :]]
        reports.append(
            {
                "provider": provider,
                "roundtrip_wer": total_errors / total_words,
                "speaker_cosine_mean": sum(consistency) / len(consistency),
                "rows": rows,
            }
        )
    report = {
        "evidence_class": "REFERENCE / OWNER_NATURALNESS_ACCEPTANCE_NOT_RUN",
        "interpretation": (
            "roundtrip errors mix ASR and TTS; synthetic speaker cosine "
            "is not perceptual identity or authorization"
        ),
        "raw_embeddings_retained": False,
        "reports": reports,
    }
    (root / "sample-quality.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps({"metrics": [{k: v for k, v in row.items() if k != "rows"} for row in reports]})
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("fixtures", "stt", "tts", "assess"))
    parser.add_argument("--model", type=Path)
    parser.add_argument("--voices", type=Path)
    parser.add_argument(
        "--public-jfk", type=Path, help="optional hash-bound public recorded fixture"
    )
    parser.add_argument("--provider", default="faster-whisper")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--compute", default="int8")
    parser.add_argument("--voice", default="bm_george")
    parser.add_argument("--rate", type=float, default=0.95)
    parser.add_argument("--root", type=Path, default=Path(".oscar/voice/quality"))
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    if args.kind == "stt" and args.provider not in {"faster-whisper", "parakeet"}:
        parser.error("unsupported reference STT provider")
    if args.kind == "tts" and args.provider not in {"kokoro", "piper", "windows-system-speech"}:
        parser.error("unsupported reference TTS provider")
    if args.provider == "parakeet" and args.device != "cpu":
        parser.error("Parakeet reference binding is CPU only")
    root = args.root.resolve()
    if not root.is_relative_to((Path.cwd() / ".oscar/voice").resolve()):
        raise ValueError("benchmark output stays in ignored voice storage")
    root.mkdir(parents=True, exist_ok=True)
    fixtures = root / "fixtures"
    fixtures.mkdir(exist_ok=True)
    profile = VoiceProfile(preferred_voice=args.voice, provider=args.provider, rate=args.rate)
    if args.kind == "assess":
        return assess_samples(root, args.model, args.device, args.compute)
    if args.kind == "fixtures":
        manifest = []
        for i, text in enumerate(TEXTS):
            path = fixtures / f"{i}.wav"
            chunks = list(
                WindowsSpeech().synthesize(
                    text,
                    VoiceProfile(
                        preferred_voice="local-system",
                        provider="windows-system-speech",
                        model="installed-voice",
                    ),
                    str(i),
                    StopToken(),
                )
            )
            wav(chunks, path)
            manifest.append(
                {
                    "file": path.name,
                    "text": text,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        if args.public_jfk:
            body = args.public_jfk.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            if digest != "59dfb9a4acb36fe2a2affc14bacbee2920ff435cb13cc314a08c13f66ba7860e":
                raise ValueError("public fixture checksum mismatch")
            (fixtures / "jfk.wav").write_bytes(body)
            manifest.append(
                {
                    "file": "jfk.wav",
                    "text": "And so my fellow Americans ask not what your country can do for you "
                    "ask what you can do for your country",
                    "sha256": digest,
                    "source": "https://github.com/ggml-org/whisper.cpp/blob/master/samples/jfk.wav",
                }
            )
        (fixtures / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print("Original synthetic fixtures generated; no playback.")
        return 0
    report = {
        "evidence_class": "REFERENCE / OWNER_NATURALNESS_ACCEPTANCE_NOT_RUN",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "provider": args.provider,
        "device": args.device,
        "compute": args.compute,
        "speaking_rate": args.rate,
        "model": str(args.model),
        "microphone": "NOT_RUN",
        "playback": "NOT_RUN",
        "offline": "local assets only; HF_HUB_OFFLINE=1",
        "resource_scope": "process RSS/CPU, whole GPU sampled; not kernel peak",
        "rows": [],
    }
    report["observed_at"] = datetime.now(UTC).isoformat()
    report["fixture_manifest_sha256"] = hashlib.sha256(
        (fixtures / "manifest.json").read_bytes()
    ).hexdigest()
    report["source_sha256"] = {
        name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
        for name in (
            "scripts/benchmark_voice.py",
            "oscar/voice_adapters.py",
            "oscar/voice_contracts.py",
            "oscar/voice_identity.py",
        )
    }
    report["packages"] = {}
    for name in (
        "faster-whisper",
        "ctranslate2",
        "sherpa-onnx",
        "onnxruntime",
        "onnxruntime-gpu",
        "kokoro-onnx",
        "piper-tts",
        "numpy",
    ):
        try:
            report["packages"][name] = version(name)
        except PackageNotFoundError:
            pass
    rows = report["rows"]
    resources = Resources()
    resources.start()
    try:
        start = perf_counter()
        if args.kind == "stt":
            engine = (
                ParakeetReference(args.model)
                if args.provider == "parakeet"
                else FasterWhisper(args.model, device=args.device, compute_type=args.compute)
            )
        elif args.provider == "kokoro":
            engine = KokoroSpeech(args.model, args.voices, device=args.device)
        elif args.provider == "piper":
            engine = PiperSpeech(args.model)
        else:
            engine = WindowsSpeech()
        report["load_ms"] = (perf_counter() - start) * 1000
        fixtures_data = json.loads((fixtures / "manifest.json").read_text())
        if args.kind == "tts":
            fixtures_data = [item for item in fixtures_data if "source" not in item]
        total_errors = total_words = 0
        for repeat in range(3):
            for i, item in enumerate(fixtures_data):
                start = perf_counter()
                if args.kind == "stt":
                    frames = read_wave((fixtures / item["file"]).read_bytes())
                    start = perf_counter()
                    result = engine.transcribe(frames, True, StopToken())
                    elapsed = (perf_counter() - start) * 1000
                    wrong, count = errors(item["text"], result.text)
                    if repeat == 0:
                        total_errors += wrong
                        total_words += count
                    partial_start = perf_counter()
                    engine.transcribe(frames[: max(1, len(frames) // 2)], False, StopToken())
                    partial_ms = (perf_counter() - partial_start) * 1000
                    rows.append(
                        {
                            "repeat": repeat,
                            "fixture": i,
                            "final_ms": elapsed,
                            "partial_ms": partial_ms,
                            "transcript": result.text,
                            "word_errors": wrong,
                            "reference_words": count,
                        }
                    )
                else:
                    stream = iter(engine.synthesize(item["text"], profile, str(i), StopToken()))
                    first = next(stream)
                    first_ms = (perf_counter() - start) * 1000
                    chunks = [first, *stream]
                    elapsed = (perf_counter() - start) * 1000
                    seconds = sum(len(c.pcm) / 2 / c.rate for c in chunks)
                    rows.append(
                        {
                            "repeat": repeat,
                            "fixture": i,
                            "first_audio_ms": first_ms,
                            "total_ms": elapsed,
                            "audio_seconds": seconds,
                            "rtf": elapsed / 1000 / seconds,
                        }
                    )
                    if repeat == 0:
                        wav(chunks, root / f"{args.provider}-{args.voice}-{i}.wav")
        if args.kind == "stt":
            report["fixture_wer"] = total_errors / total_words
            report["warm_final_median_ms"] = median(r["final_ms"] for r in rows if r["repeat"] > 0)
            report["warm_partial_median_ms"] = median(
                r["partial_ms"] for r in rows if r["repeat"] > 0
            )
        else:
            report["warm_first_audio_median_ms"] = median(
                r["first_audio_ms"] for r in rows if r["repeat"] > 0
            )
            report["warm_rtf_median"] = median(r["rtf"] for r in rows if r["repeat"] > 0)
        token = StopToken()
        token.cancel()
        try:
            if args.kind == "stt":
                engine.transcribe(frames, True, token)
            else:
                next(iter(engine.synthesize(TEXTS[0], profile, "cancel", token)))
            report["pre_cancel"] = "FAILED"
        except VoiceCancelled:
            report["pre_cancel"] = "VERIFIED"
        if args.kind == "stt":
            token = StopToken()
            timer = threading.Timer(0.01, token.cancel)
            timer.start()
            start = perf_counter()
            try:
                engine.transcribe(frames, True, token)
                report["inflight_cancel"] = "COMPLETED_BEFORE_CANCEL_OR_FAILED"
            except VoiceCancelled:
                report["inflight_cancel"] = "VERIFIED_RESULT_DISCARDED"
            finally:
                timer.cancel()
                timer.join()
            report["inflight_cancel_ms"] = (perf_counter() - start) * 1000
        if args.kind == "tts":
            token = StopToken()
            stream = iter(engine.synthesize(TEXTS[0], profile, "mid-cancel", token))
            next(stream)
            token.cancel()
            start = perf_counter()
            try:
                next(stream)
                report["chunk_cancel"] = "FAILED"
            except VoiceCancelled:
                report["chunk_cancel"] = "VERIFIED"
            report["chunk_cancel_ms"] = (perf_counter() - start) * 1000
        report["status"] = "REFERENCE_EXECUTED"
    except Exception as exc:
        report["status"] = "FAILED"
        report["failure_type"] = type(exc).__name__
        report["failure"] = str(exc)[:200]
    finally:
        report["resources"] = resources.finish()
    if args.model and args.model.exists():
        report["model_bytes"] = (
            sum(
                p.stat().st_size
                for p in args.model.rglob("*")
                if p.is_file()
                and ".cache" not in p.parts
                and p.suffix != ".part"
                and not any(part.endswith("-parts") for part in p.parts)
            )
            if args.model.is_dir()
            else args.model.stat().st_size
        )
    model_name = args.model.name if args.model else "system"
    output = root / f"{args.kind}-{args.provider}-{model_name}-{args.device}-{args.compute}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    return 0 if report["status"] == "REFERENCE_EXECUTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
