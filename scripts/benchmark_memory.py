"""Bounded local model comparison using the real OSCAR A-R evaluation."""

import argparse
import json
from pathlib import Path
from time import perf_counter

from evaluate_memory import run

from oscar.memory_indexes import FastEmbedding, FastReranker, LocalEmbedding, LocalReranker


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--cache", type=Path, help="preloaded model cache; uses offline mode")
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=False)
    cache = args.cache or args.root / "models"
    rows = []
    for name in ("torch-minilm", "onnx-bge", "onnx-minilm"):
        print("Starting " + name, flush=True)
        started = perf_counter()
        if name == "torch-minilm":
            embedding = LocalEmbedding(revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
            ranking = LocalReranker(revision="233902d25c440f23af6f7d6e94d2946bac0bee0a")
        else:
            model = (
                "BAAI/bge-small-en-v1.5"
                if name == "onnx-bge"
                else "sentence-transformers/all-MiniLM-L6-v2"
            )
            embedding = FastEmbedding(model, cache=str(cache), offline=args.cache is not None)
            ranking = FastReranker(cache=str(cache), offline=args.cache is not None)
        startup = perf_counter() - started
        started = perf_counter()
        report = run(args.root / name, embedding=embedding, ranking=ranking)
        elapsed = perf_counter() - started
        query = "What development editor did I choose?"
        texts = ["My development editor is Zed", "The archive uses SQLite WAL"]
        measurements = {}
        for label, operation in (
            ("dense", lambda embedding=embedding, texts=texts: embedding.embed(texts)),
            (
                "reranker",
                lambda ranking=ranking, query=query, texts=texts: ranking.rank(query, texts),
            ),
        ):
            samples = []
            for _ in range(5):
                started = perf_counter()
                operation()
                samples.append(perf_counter() - started)
            measurements[label + "_median_seconds"] = sorted(samples)[2]
        rows.append(
            {
                "candidate": name,
                "embedding": embedding.identity,
                "reranker": ranking.identity,
                "startup_seconds_including_download": startup,
                "evaluation_seconds": elapsed,
                "measurements": measurements,
                "evaluation": report,
                "cumulative_onnx_cache_bytes": sum(
                    p.stat().st_size for p in cache.rglob("*") if p.is_file()
                ),
            }
        )
        (args.root / "report.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(name + ": " + report["status"], flush=True)


if __name__ == "__main__":
    main()
