"""Explicit public-model setup. Never opens audio or enrolls a speaker."""

import argparse
import hashlib
import json
import shutil
import tarfile
import urllib.request
from pathlib import Path

from oscar.voice_adapters import optional

KWS = "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01"
BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/"


def download(url: str, path: Path, bound: int) -> str:
    if path.exists():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    with urllib.request.urlopen(url, timeout=60) as response:
        body = response.read(bound + 1)
    if len(body) > bound:
        raise ValueError("model exceeds download bound")
    path.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def digest_file(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def quality_setup(root: Path) -> None:
    """Explicit network preparation, never inference-time fetch or audio capture."""
    hub = optional("huggingface_hub")
    np = optional("numpy")
    quality = (Path.cwd() / ".oscar/voice/quality").resolve()
    quality.mkdir(parents=True, exist_ok=True)
    manifest = []
    for repository, revision, destination, patterns in (
        (
            "dropbox-dash/faster-whisper-large-v3-turbo",
            "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf",
            "turbo",
            ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"],
        ),
        (
            "onnx-community/Kokoro-82M-v1.0-ONNX",
            "1939ad2a8e416c0acfeecc08a694d14ef25f2231",
            "kokoro-hf",
            ["onnx/model.onnx", "voices/bm_george.bin", "voices/bm_lewis.bin", "config.json"],
        ),
        (
            "rhasspy/piper-voices",
            "c10ece1aade47bb51c153c893d14e5bf8e5b7117",
            "piper-hf",
            [
                "en/en_GB/alba/medium/en_GB-alba-medium.onnx",
                "en/en_GB/alba/medium/en_GB-alba-medium.onnx.json",
                "en/en_GB/alba/medium/MODEL_CARD",
            ],
        ),
    ):
        resolved = str(hub.model_info(repository, revision=revision).sha)
        path = quality / destination
        hub.snapshot_download(
            repository, revision=resolved, local_dir=str(path), allow_patterns=patterns
        )
        hashes = {
            str(p.relative_to(path)): digest_file(p)
            for p in path.rglob("*")
            if p.is_file() and ".cache" not in p.parts
        }
        manifest.append({"source": repository, "revision": resolved, "sha256": hashes})
    shutil.copyfile(quality / "kokoro-hf/onnx/model.onnx", quality / "kokoro-fp32.onnx")
    voices = {
        name: np.fromfile(quality / f"kokoro-hf/voices/{name}.bin", dtype=np.float32).reshape(
            -1, 1, 256
        )
        for name in ("bm_george", "bm_lewis")
    }
    with (quality / "voices-hf.bin").open("wb") as output:
        np.savez(output, **voices)
    for suffix in (".onnx", ".onnx.json"):
        shutil.copyfile(
            quality / ("piper-hf/en/en_GB/alba/medium/en_GB-alba-medium" + suffix),
            quality / ("piper-parallel" + suffix),
        )
    (quality / "model-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Preferred local assets prepared; no playback or naturalness acceptance implied.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(".oscar/voice/models"))
    parser.add_argument(
        "--quality", action="store_true", help="explicitly prepare preferred neural assets"
    )
    args = parser.parse_args()
    root = args.root.resolve()
    allowed = (Path.cwd() / ".oscar/voice").resolve()
    if not root.is_relative_to(allowed):
        raise ValueError("voice model setup stays under ignored .oscar/voice")
    root.mkdir(parents=True, exist_ok=True)
    files = [
        (BASE + "kws-models/" + KWS + ".tar.bz2", root / "kws.tar.bz2", 25_000_000),
        (BASE + "asr-models/silero_vad.onnx", root / "silero_vad.onnx", 5_000_000),
        (
            BASE + "speaker-recongition-models/3dspeaker_speech_campplus_sv_en_voxceleb_16k.onnx",
            root / "speaker.onnx",
            40_000_000,
        ),
    ]
    manifest = []
    for url, path, bound in files:
        digest = download(url, path, bound)
        manifest.append({"source": url, "file": path.name, "sha256": digest})
    if not (root / KWS).exists():
        with tarfile.open(root / "kws.tar.bz2", "r:bz2") as archive:
            members = archive.getmembers()
            if sum(m.size for m in members) > 100_000_000:
                raise ValueError("model archive too large")
            archive.extractall(root, filter="data")
    # GigaSpeech SentencePiece tokens; no custom wake training or cloud wake.
    sp = optional("sentencepiece").SentencePieceProcessor(model_file=str(root / KWS / "bpe.model"))
    tokens = sp.encode("OSCAR", out_type=str)
    (root / "keywords.txt").write_text(" ".join(tokens) + " @OSCAR\n", encoding="utf-8")
    hub = optional("huggingface_hub")
    info = hub.model_info("Systran/faster-whisper-base.en")
    revision = str(info.sha)
    hub.snapshot_download(
        "Systran/faster-whisper-base.en", revision=revision, local_dir=str(root / "whisper-base.en")
    )
    manifest.append({"source": "Systran/faster-whisper-base.en", "revision": revision})
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if args.quality:
        quality_setup(root)
    print("Public local models prepared; no microphone, playback or speaker enrollment performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
