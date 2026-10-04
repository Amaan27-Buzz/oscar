"""Explicit public-model setup. Never opens audio or enrolls a speaker."""

import argparse
import hashlib
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(".oscar/voice/models"))
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
    print("Public local models prepared; no microphone, playback or speaker enrollment performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
