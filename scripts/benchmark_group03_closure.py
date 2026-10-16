"""Comparable local closure benchmark: cold/warm, normal/quiet Core, SQL writes and RSS."""

import argparse
import cProfile
import ctypes
import hashlib
import json
import math
import os
import platform
import pstats
import statistics
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter, process_time, sleep


def rss() -> dict[str, int] | None:
    if os.name != "nt":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t)
            for name in ("peak", "working", "qpp", "qp", "qnp", "qn", "page", "peakpage")
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32")
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    get_memory = ctypes.WinDLL("psapi").GetProcessMemoryInfo
    get_memory.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    if not get_memory(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError("process RSS query failed")
    return {"rss_bytes": counters.working, "peak_working_set_bytes": counters.peak}


def metrics(values: list[float]) -> dict:
    assert values
    return {
        "samples": len(values),
        "successes": len(values),
        "errors": 0,
        "p50_ms": round(statistics.median(values), 4),
        "p95_ms": round(sorted(values)[math.ceil(len(values) * 0.95) - 1], 4),
    }


def sample(root: Path, iterations: int, quiet: bool, idle_seconds: float = 3) -> dict:
    sys.path.insert(0, str(root))
    from oscar.harness import Harness
    from oscar.jev import Intent
    from oscar.perception import PerceptionSource
    from oscar.transport import HTTPTransport, ReferenceServer
    from oscar.world_model import ObservationKind

    with TemporaryDirectory(prefix="oscar-closure-bench-") as folder:
        directory = Path(folder)
        start = perf_counter()
        with Harness(
            directory / "core.sqlite", directory / "files", root / "config/development-models.json"
        ) as h:
            startup_ms = (perf_counter() - start) * 1000
            h.world.configure_source(
                PerceptionSource(
                    "benchmark-grid",
                    ("core",),
                    ("grid.state",),
                    (ObservationKind.DEVICE,),
                    simulated=False,
                    perceive=True,
                ),
                "grid",
                "core",
                owner_authorized=True,
            )
            h.world.tick()
            assert h.world.world.resolve("core", "grid.state").state == "current"
            if quiet:
                h.executive.close()
                h.world.close()
                if hasattr(h, "execution_session"):
                    h.execution_session.close()
            counts = {"writes": 0, "presence_writes": 0, "begin_immediate": 0}

            def trace(sql: str) -> None:
                if sql.startswith(("INSERT", "UPDATE", "DELETE")):
                    counts["writes"] += 1
                    counts["presence_writes"] += int("'core_presence'" in sql)
                counts["begin_immediate"] += int(sql == "BEGIN IMMEDIATE")

            h.store.db.set_trace_callback(trace)
            targets = {h.node_id: (h.dispatcher, h.session)}

            def run(operation: str, index: int, target: dict) -> None:
                intent = (
                    Intent("2 + 2")
                    if operation != "file"
                    else Intent(
                        "Write benchmark", "file_write", f"proof-{index}.txt", "exact closure proof"
                    )
                )
                assert h.runtime.run(h.runtime.create(intent).id, target).state == "verified"
                if operation == "file":
                    assert h.files.read(f"proof-{index}.txt") == b"exact closure proof"

            start = perf_counter()
            run("arithmetic", -1, targets)
            cold_task_ms = (perf_counter() - start) * 1000
            idle_counts = dict(counts)
            cpu, wall = process_time(), perf_counter()
            sleep(idle_seconds)
            idle = {
                "cpu_seconds": process_time() - cpu,
                "wall_seconds": perf_counter() - wall,
                "sql_writes": counts["writes"] - idle_counts["writes"],
                **(rss() or {}),
            }
            operations = {}
            cpu, wall = process_time(), perf_counter()
            before = dict(counts)
            with ReferenceServer(h.dispatcher) as server:
                remote = {h.node_id: (HTTPTransport(server.url), h.session)}
                for operation in ("arithmetic", "file", "loopback_http"):
                    target = remote if operation == "loopback_http" else targets
                    for index in range(3):
                        run(operation, -index - 10, target)
                    values = []
                    for index in range(iterations):
                        start = perf_counter()
                        run(operation, index, target)
                        values.append((perf_counter() - start) * 1000)
                    operations[operation] = values
            common = {
                "cpu_seconds": process_time() - cpu,
                "wall_seconds": perf_counter() - wall,
                "sql_writes": counts["writes"] - before["writes"],
                "begin_immediate": counts["begin_immediate"] - before["begin_immediate"],
                **(rss() or {}),
            }
            from oscar.executive import Executive

            executive = Executive(h.runtime, targets)
            worker = executive.worker(
                "Benchmark", [(h.node_id, "math.add")], ("math",), owner_authorized=True
            )
            values = []
            for _ in range(iterations):
                start = perf_counter()
                goal = executive.decompose(worker, "2 + 2")
                executive.accept(goal["id"], goal["review_digest"], owner_authorized=True)
                executive.tick()
                while h.store.get("executive_goal", goal["id"])["state"] != "completed":
                    assert perf_counter() - start < 5
                    sleep(0.002)
                    executive.tick()
                values.append((perf_counter() - start) * 1000)
            operations["reviewed_executive_goal"] = values
            executive.close()
            first = h.runtime.presence.snapshot()["expression"]
            before = dict(counts)
            values = []
            for _ in range(200):
                start = perf_counter()
                event = h.runtime.presence.snapshot()["expression"]
                assert event["transitionId"] == first["transitionId"]
                assert event["generation"] > first["generation"]
                values.append((perf_counter() - start) * 1000)
            operations["presence_unchanged"] = values
            unchanged_writes = counts["presence_writes"] - before["presence_writes"]

            def poll(_: int) -> tuple[float, int]:
                start = perf_counter()
                event = h.runtime.presence.snapshot()["expression"]
                return (perf_counter() - start) * 1000, event["generation"]

            with ThreadPoolExecutor(max_workers=8) as pool:
                concurrent = list(pool.map(poll, range(200)))
            assert len({generation for _, generation in concurrent}) == 200
            operations["presence_eight_subscribers"] = [duration for duration, _ in concurrent]
            values = []
            for _ in range(10):
                task = h.runtime.create(Intent("2 + 2"))
                start = perf_counter()
                waiting = h.runtime.presence.snapshot()["expression"]
                assert (
                    waiting["operation"] == "waiting"
                    and waiting["transitionId"] != first["transitionId"]
                )
                values.append((perf_counter() - start) * 1000)
                assert h.runtime.run(task.id, targets).state == "verified"
                first = h.runtime.presence.snapshot()["expression"]
                assert first["operation"] == "idle"
            operations["presence_transition_projection"] = values
            profile = cProfile.Profile()
            profile.enable()
            for _ in range(15):
                run("arithmetic", 0, targets)
            profile.disable()
            stats = pstats.Stats(profile)
            hot = sorted(stats.stats.items(), key=lambda pair: pair[1][3], reverse=True)[:18]
            functions = [
                {
                    "function": f"{Path(key[0]).name}:{key[1]}:{key[2]}",
                    "calls": value[1],
                    "cumulative_seconds": round(value[3], 6),
                }
                for key, value in hot
            ]
            h.store.db.set_trace_callback(None)
            return {
                "startup_ms": startup_ms,
                "cold_first_task_ms": cold_task_ms,
                "idle": idle,
                "common": common,
                "operations": operations,
                "unchanged_presence_writes": unchanged_writes,
                "profile": functions,
                "final_process_memory": rss(),
                "source_sha256": hashlib.sha256(
                    b"".join(p.read_bytes() for p in sorted((root / "oscar").glob("*.py")))
                ).hexdigest(),
            }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-root", type=Path)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--idle-seconds", type=float, default=3)
    parser.add_argument("--mode", choices=("both", "normal", "quiet"), default="both")
    parser.add_argument("--baseline", default="d2e686c7d8c2f67dea13d1551d52b5759831d279")
    parser.add_argument(
        "--output", type=Path, default=Path("docs/evidence/group03/closure-benchmark.json")
    )
    args = parser.parse_args()
    if not 10 <= args.iterations <= 100 or not 1 <= args.repeats <= 4:
        parser.error("bounded sample/repetition counts required")
    if not 3 <= args.idle_seconds <= 60:
        parser.error("idle measurement must last 3-60 seconds")
    if args.sample_root:
        print(
            json.dumps(
                sample(args.sample_root.resolve(), args.iterations, args.quiet, args.idle_seconds)
            )
        )
        return
    root = Path(__file__).resolve().parents[1]
    baseline = subprocess.check_output(
        ["git", "rev-parse", "--verify", args.baseline + "^{commit}"], text=True
    ).strip()
    with TemporaryDirectory(prefix="group03-closure-baseline-", dir=root / ".oscar") as folder:
        extracted = Path(folder).resolve()
        assert extracted.is_relative_to((root / ".oscar").resolve())
        archive = extracted / "source.zip"
        with archive.open("wb") as destination:
            subprocess.run(
                ["git", "archive", "--format=zip", baseline, "oscar", "config"],
                stdout=destination,
                check=True,
            )
        with zipfile.ZipFile(archive) as bundle:
            assert all(
                not Path(i.filename).is_absolute() and ".." not in Path(i.filename).parts
                for i in bundle.infolist()
            )
            bundle.extractall(extracted)
        runs = {"baseline": {"normal": [], "quiet": []}, "candidate": {"normal": [], "quiet": []}}
        for repeat in range(args.repeats):
            order = [("baseline", extracted), ("candidate", root)]
            if repeat % 2:
                order.reverse()
            for label, source in order:
                for quiet in (False, True):
                    if args.mode != "both" and args.mode != ("quiet" if quiet else "normal"):
                        continue
                    command = [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--sample-root",
                        str(source),
                        "--iterations",
                        str(args.iterations),
                        "--idle-seconds",
                        str(args.idle_seconds),
                    ]
                    if quiet:
                        command.append("--quiet")
                    result = subprocess.run(
                        command, cwd=source, capture_output=True, text=True, check=True, timeout=180
                    )
                    runs[label]["quiet" if quiet else "normal"].append(json.loads(result.stdout))
        summary = {
            label: {
                mode: {
                    operation: metrics(
                        [value for run in samples for value in run["operations"][operation]]
                    )
                    for operation in samples[0]["operations"]
                }
                for mode, samples in modes.items()
                if samples
            }
            for label, modes in runs.items()
        }
        report = {
            "version": 1,
            "baseline_sha": baseline,
            "candidate_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "idle_seconds": args.idle_seconds,
            "mode": args.mode,
            "summary": summary,
            "runs": runs,
            "limits": (
                "Real disposable local SQLite/files/loopback; three warm-ups per operation. "
                "SQL trace enabled equally; no tracemalloc. Separate fresh processes, "
                "alternating revision order, authorized local Grid source with normal "
                "vs stopped background services. "
                "Cold samples are Harness startup/first task, not OS cold cache. "
                "RSS is Windows working set, not all-system memory/battery. "
                "Laptop cache/load and thermal state uncontrolled. "
                "Baseline extraction includes only runtime/config to reduce unrelated asset I/O. "
                "No model/provider/device performance claim."
            ),
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"baseline_sha": baseline, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
