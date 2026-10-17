"""Reproducible local Core baseline/candidate benchmark; no accounts, paid calls or devices."""

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tracemalloc
import zipfile
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter, process_time, sleep


def sample(root: Path, iterations: int) -> dict:
    sys.path.insert(0, str(root))
    from oscar.harness import Harness
    from oscar.jev import Intent
    from oscar.transport import HTTPTransport, ReferenceServer

    tracemalloc.start()
    cpu, wall = process_time(), perf_counter()
    durations: dict[str, list[float]] = {}
    with TemporaryDirectory(prefix="oscar-group03-benchmark-") as folder:
        directory = Path(folder)
        start = perf_counter()
        with Harness(
            directory / "core.sqlite", directory / "files", root / "config/development-models.json"
        ) as h:
            startup_ms = (perf_counter() - start) * 1000
            idle_cpu, idle_wall = process_time(), perf_counter()
            sleep(2.1)
            idle_cpu_seconds = process_time() - idle_cpu
            idle_wall_seconds = perf_counter() - idle_wall
            targets = {h.node_id: (h.dispatcher, h.session)}
            for _ in range(3):
                assert (
                    h.runtime.run(h.runtime.create(Intent("2 + 2")).id, targets).state == "verified"
                )
            with ReferenceServer(h.dispatcher) as server:
                remote = {h.node_id: (HTTPTransport(server.url), h.session)}
                for operation in ("arithmetic_local", "file_local", "arithmetic_loopback_http"):
                    values = []
                    for index in range(iterations):
                        start = perf_counter()
                        intent = (
                            Intent(
                                "Write benchmark",
                                "file_write",
                                f"proof-{index}.txt",
                                "exact benchmark bytes",
                            )
                            if operation == "file_local"
                            else Intent("2 + 2")
                        )
                        task = h.runtime.create(intent)
                        assert (
                            h.runtime.run(
                                task.id, remote if operation.endswith("http") else targets
                            ).state
                            == "verified"
                        )
                        if operation == "file_local":
                            assert h.files.read(f"proof-{index}.txt") == b"exact benchmark bytes"
                        values.append((perf_counter() - start) * 1000)
                    durations[operation] = values
            common_cpu_seconds = process_time() - cpu
            common_elapsed_seconds = perf_counter() - wall
            common_peak = tracemalloc.get_traced_memory()[1]
            if hasattr(h.runtime, "presence"):
                from oscar.adaptive import task_view

                values = []
                for _ in range(iterations):
                    start = perf_counter()
                    view = h.runtime.presence.snapshot()
                    assert view["expression"]["operation"] == "idle"
                    task_view(
                        {
                            "task_id": task.id,
                            "generation": task.attempts,
                            "state": "verified",
                            "evidence_ids": ["benchmark-evidence"],
                        },
                        round(h.grid.clock() * 1000),
                        ["result_evidence"],
                    )
                    values.append((perf_counter() - start) * 1000)
                durations["presence_and_typed_view"] = values
            if hasattr(h.runtime, "executive"):
                executive = h.runtime.executive
                worker = executive.worker(
                    "Benchmark", [(h.node_id, "math.add")], ("math",), owner_authorized=True
                )
                values = []
                for _ in range(iterations):
                    start = perf_counter()
                    goal = executive.propose(
                        worker,
                        "Verified arithmetic",
                        [
                            {
                                "id": "sum",
                                "intent": asdict(Intent("2 + 2")),
                                "depends_on": [],
                                "node_id": h.node_id,
                                "capability_id": "math.add",
                            }
                        ],
                    )
                    executive.accept(goal["id"], goal["review_digest"], owner_authorized=True)
                    executive.tick()
                    while (
                        h.store.get("executive_goal", goal["id"])["state"] != "completed"
                        and perf_counter() - start < 5
                    ):
                        sleep(0.002)
                        executive.tick()
                    assert h.store.get("executive_goal", goal["id"])["state"] == "completed"
                    values.append((perf_counter() - start) * 1000)
                durations["reviewed_executive_goal"] = values
        assert not any(p.name.startswith("proof-") for p in root.iterdir())
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics = {
        name: {
            "samples": len(values),
            "median_ms": round(statistics.median(values), 3),
            "p95_ms": round(sorted(values)[math.ceil(0.95 * len(values)) - 1], 3),
        }
        for name, values in durations.items()
    }
    return {
        "startup_ms": round(startup_ms, 3),
        "idle_cpu_seconds": round(idle_cpu_seconds, 4),
        "idle_wall_seconds": round(idle_wall_seconds, 3),
        "common_cpu_seconds": round(common_cpu_seconds, 3),
        "common_elapsed_seconds": round(common_elapsed_seconds, 3),
        "common_peak_python_allocated_bytes": common_peak,
        "cpu_seconds": round(process_time() - cpu, 3),
        "elapsed_seconds": round(perf_counter() - wall, 3),
        "peak_python_allocated_bytes": peak,
        "operations": metrics,
        "source_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted((root / "oscar").glob("*.py")))
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-root", type=Path)
    parser.add_argument("--baseline", default="5899798a3200173547ee3493689e20222fe3d1b1")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/evidence/group03/end-to-end-benchmark.json")
    )
    args = parser.parse_args()
    if not 10 <= args.iterations <= 100:
        parser.error("iterations must be between 10 and 100")
    if args.sample_root:
        print(json.dumps(sample(args.sample_root.resolve(), args.iterations)))
        return
    root = Path(__file__).resolve().parents[1]
    baseline = subprocess.check_output(
        ["git", "rev-parse", "--verify", args.baseline + "^{commit}"], cwd=root, text=True
    ).strip()
    cache = root / ".oscar"
    cache.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="group03-baseline-", dir=cache) as folder:
        extracted = Path(folder).resolve()
        assert extracted.is_relative_to(cache.resolve())
        archive = extracted / "source.zip"
        with archive.open("wb") as destination:
            subprocess.run(
                ["git", "archive", "--format=zip", baseline],
                cwd=root,
                stdout=destination,
                check=True,
            )
        with zipfile.ZipFile(archive) as bundle:
            assert all(
                not Path(i.filename).is_absolute() and ".." not in Path(i.filename).parts
                for i in bundle.infolist()
            )
            bundle.extractall(extracted)
        measurements = {}
        for label, source in (("baseline", extracted), ("candidate", root)):
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--sample-root",
                    str(source),
                    "--iterations",
                    str(args.iterations),
                ],
                cwd=source,
                env=dict(os.environ),
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )
            measurements[label] = json.loads(completed.stdout)
    report = {
        "version": 1,
        "baseline_sha": baseline,
        "candidate_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "evidence": "REAL_LOCAL_SQLITE_FILES_AND_AUTHENTICATED_LOOPBACK_HTTP",
        "limitations": (
            "One instrumented process per revision on this laptop; warm-up3, "
            "tracemalloc enabled, warm caches and concurrent machine load uncontrolled. "
            "Python allocations, not total RSS or battery. No physical device, network "
            "provider, camera/audio or production load measurement. Candidate source "
            "hash includes current uncommitted Python files."
        ),
        **measurements,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
