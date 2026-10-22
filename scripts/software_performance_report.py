"""Render the existing closure benchmark's samples; refuses mixed candidate sources."""

import argparse
import json
from pathlib import Path


def render(source: Path, output: Path) -> None:
    report = json.loads(source.read_text(encoding="utf-8"))
    for label in ("baseline", "candidate"):
        runs = report["runs"][label]["normal"]
        assert runs and len({r["source_sha256"] for r in runs}) == 1, (
            "source changed during sampling"
        )
        assert all(r["operations"] for r in runs)
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    output.mkdir(parents=True, exist_ok=True)
    rows = [
        "| Operation | Samples | Baseline p50 / p95 ms | Candidate p50 / p95 ms |",
        "| --- | ---: | ---: | ---: |",
    ]
    operations = ("arithmetic", "file", "loopback_http", "reviewed_executive_goal")
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for operation, axis in zip(operations, axes.flat, strict=True):
        base = report["summary"]["baseline"]["normal"][operation]
        current = report["summary"]["candidate"]["normal"][operation]
        rows.append(
            f"| {operation} | {current['samples']} | {base['p50_ms']} / {base['p95_ms']} "
            f"| {current['p50_ms']} / {current['p95_ms']} |"
        )
        for label in ("baseline", "candidate"):
            values = [
                v for r in report["runs"][label]["normal"] for v in r["operations"][operation]
            ]
            assert values and all(type(v) in (int, float) and v >= 0 for v in values)
            axis.plot(range(1, len(values) + 1), values, label=label, linewidth=1)
        axis.set(title=operation.replace("_", " "), xlabel="Sample order", ylabel="Milliseconds")
        axis.legend()
        axis.grid(alpha=0.2)
    figure.suptitle("OSCAR local software performance — verified operations")
    figure.savefig(output / "performance.png", dpi=150)
    plt.close(figure)
    (output / "performance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "performance.md").write_text(
        "# Local performance acceptance\n\n"
        + "\n".join(rows)
        + "\n\n![Ordered samples](performance.png)\n\n"
        + report["limits"]
        + "\n\nCandidate source hashes in JSON identify the measured working tree. "
        "The candidate HEAD alone does not identify uncommitted source. "
        "No Internet, real account, device battery, room audio or sustained-use claim.\n",
        encoding="utf-8",
    )
    assert all(
        (output / name).stat().st_size > 100
        for name in ("performance.json", "performance.md", "performance.png")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.source, args.output)


if __name__ == "__main__":
    main()
