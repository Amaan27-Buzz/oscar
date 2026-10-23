"""Sustained real TLS Core/Worker effects with synthetic authority and process metrics."""

import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import monotonic, sleep

from tests.test_connected_acceptance import ConnectedAcceptanceTests


def run(seconds: int, interval: float) -> dict:
    import psutil

    assert 10 <= seconds <= 1800 and 1 <= interval <= 30
    root = Path(__file__).resolve().parents[1]

    def inputs():
        paths = [
            *sorted((root / "oscar").glob("*.py")),
            Path(__file__),
            root / "tests/test_connected_acceptance.py",
            root / "tests/test_cloud.py",
        ]
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    pinned = inputs()
    fixture = ConnectedAcceptanceTests()
    samples, latencies, task_ids, restarts = [], [], [], []
    result = None
    try:
        fixture.setUp()
        core = fixture.start_core()
        fixture.enroll()
        worker = fixture.start_worker()
        started = monotonic()
        restarted_worker = restarted_core = False
        while monotonic() - started < seconds:
            before = monotonic()
            content = "Synthetic sustained effect " + str(len(task_ids))
            task = fixture.submit("file_write", {"path": "soak-proof.txt", "content": content})
            assert task["task_id"] not in task_ids
            fixture.approve(task)
            verified = fixture.wait_task(task["task_id"])
            assert verified["state"] == "verified"
            assert (fixture.workspace / "soak-proof.txt").read_text() == content
            task_ids.append(task["task_id"])
            latencies.append(round((monotonic() - before) * 1000, 2))
            sample = {"elapsed_seconds": round(monotonic() - started, 2)}
            for label, process in (("core", core), ("worker", worker)):
                assert process.poll() is None, label + " exited during sustained operation"
                parent = psutil.Process(process.pid)
                tree = [parent, *parent.children(recursive=True)]
                sample[label] = {
                    "processes": len(tree),
                    "rss_bytes": sum(p.memory_info().rss for p in tree),
                    "threads": sum(p.num_threads() for p in tree),
                    "handles": sum(p.num_handles() for p in tree)
                    if platform.system() == "Windows"
                    else None,
                    "cpu_seconds": round(sum(sum(p.cpu_times()[:2]) for p in tree), 3),
                }
            sample["sqlite_bytes"] = sum(p.stat().st_size for p in fixture.root.rglob("*.sqlite*"))
            samples.append(sample)
            if sample["elapsed_seconds"] >= seconds / 3 and not restarted_worker:
                fixture.stop(worker)
                worker = fixture.start_worker()
                restarted_worker = True
                restarts.append("worker")
            if sample["elapsed_seconds"] >= seconds * 2 / 3 and not restarted_core:
                fixture.stop(worker)
                fixture.stop(core)
                core = fixture.start_core()
                worker = fixture.start_worker()
                restored = fixture.mobile.request("inspect", {"task_id": task_ids[-1]})
                assert restored["state"] == "verified"
                assert (fixture.workspace / "soak-proof.txt").read_text() == content
                restarted_core = True
                restarts.append("core-and-worker")
            sleep(min(interval, max(0, seconds - (monotonic() - started))))
        assert inputs() == pinned, "Runtime source changed during sustained acceptance"
        assert len(task_ids) >= 2 and restarted_core and restarted_worker
        result = {
            "status": "SOFTWARE_VERIFIED",
            "platform": platform.platform(),
            "duration_seconds": round(monotonic() - started, 2),
            "requested_seconds": seconds,
            "verified_effects": len(task_ids),
            "independent_file_readbacks": len(task_ids),
            "latencies_ms": latencies,
            "samples": samples,
            "restarts": restarts,
            "source_sha256": pinned,
            "psutil_version": psutil.__version__,
            "limits": "Synthetic loopback TLS and scoped filesystem workload only; retained task "
            "history intentionally grows. No leak-free, multi-day, hosted, browser, audio, "
            "battery, physical-device or owner-activation claim.",
        }
    finally:
        assert fixture.doCleanups(), "Disposable process/credential cleanup failed"
        if hasattr(fixture, "root"):
            assert not fixture.root.exists(), "Disposable credentials/runtime remain"
    assert result is not None
    result["cleanup"] = "Fixture processes stopped and disposable credentials/workspace removed"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.seconds, args.interval)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "duration_seconds", "verified_effects")}))


if __name__ == "__main__":
    main()
