"""Opt-in useful Codex objective on a disposable repository, independently verified."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from time import time
from typing import Any

from oscar.capabilities import ScopedFiles, Verifier
from oscar.contracts import Epistemic, Evidence, Objective, Result, TaskState, Verification, new_id
from oscar.grid import Grid, Node, NodeRole
from oscar.jev import Intent
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import HTTPTransport
from scripts.verify_worker_reference import SCOPES, LostResult, WorkerProcess, initialize_repository

BUG = '''def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals without modifying the input."""
    merged = []
    for start, end in sorted(intervals):
        if start > end:
            raise ValueError("reversed interval")
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged
'''

CHECK = """import runpy, sys
merge = runpy.run_path(sys.argv[1])["merge_intervals"]
cases = [([], []), ([(1, 10), (2, 3)], [(1, 10)]),
 ([(1, 2), (2, 4)], [(1, 4)]), ([(9, 10), (1, 3)], [(1, 3), (9, 10)]),
 ([(1, 10), (2, 3), (4, 5)], [(1, 10)]), ([(1, 2), (1, 2)], [(1, 2)]),
 ([(-5, 0), (-3, 2)], [(-5, 2)]), ([(1, 8), (2, 4), (7, 12)], [(1, 12)])]
for data, expected in cases:
    original = list(data)
    assert merge(data) == expected
    assert data == original
try:
    merge([(3, 1)])
except ValueError:
    pass
else:
    raise AssertionError("reversed intervals must be rejected")
print("9 independent cases pass")
"""


def git_read(workspace: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.hooksPath=" + os.devnull, *args],
        cwd=workspace,
        text=True,
        timeout=10,
    ).strip()


class CodingInspector(Verifier):
    def verify(self, objective: Objective, result: Result) -> Verification:
        actual = self.files.read("intervals.py")
        tested = subprocess.run(
            [sys.executable, "-I", "-c", CHECK, str(self.files.root / "intervals.py")],
            capture_output=True,
            timeout=10,
            env={
                k: os.environ[k] for k in ("SystemRoot", "PATH", "TEMP", "TMP") if k in os.environ
            },
        )
        matches = (
            result.success
            and actual != BUG.encode()
            and tested.returncode == 0
            and git_read(self.files.root, "diff", "--name-only") == "intervals.py"
            and not git_read(self.files.root, "ls-files", "--others", "--exclude-standard")
            and not git_read(self.files.root, "diff", "--cached", "--name-only")
            and git_read(self.files.root, "rev-parse", "HEAD")
            == objective.criterion["initial_head"]
        )
        return Verification(
            TaskState.VERIFIED if matches else TaskState.FAILED,
            Evidence(
                new_id(),
                result.task_id,
                result.correlation_id,
                "independent-coding-inspector",
                "Git scope/baseline + independent isolated Python behavioral checks",
                time(),
                matches,
                Epistemic.VERIFIED if matches else Epistemic.KNOWN,
                "nine cases, unchanged input, rejected reversed intervals; sole diff intervals.py",
                content_hash=hashlib.sha256(actual).hexdigest(),
            ),
        )


def run(root: Path, executable: str, codex_home: Path) -> dict[str, Any]:
    root = root.absolute()
    root.mkdir(parents=True, exist_ok=False)
    workspace = root / "repository"
    workspace.mkdir()
    initialize_repository(workspace)
    (workspace / "intervals.py").write_bytes(BUG.encode())
    subprocess.run(["git", "add", "intervals.py"], cwd=workspace, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=OSCAR test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=" + os.devnull,
            "commit",
            "-qm",
            "interval merge regression fixture",
        ],
        cwd=workspace,
        check=True,
    )
    baseline = git_read(workspace, "rev-parse", "HEAD")
    assert (
        subprocess.run(
            [sys.executable, "-I", "-c", CHECK, str(workspace / "intervals.py")],
            capture_output=True,
            timeout=10,
        ).returncode
        != 0
    )
    state = root / "state.sqlite"
    store = Store(state)
    grid = Grid(store)
    grid.register(Node("codex-worker", NodeRole.DESKTOP, SCOPES))
    session = grid.pair("codex-worker", SCOPES)
    worker = WorkerProcess(
        state,
        workspace,
        session,
        executables=(executable,),
        codex_home=codex_home,
        discover_agents=False,
    )
    try:
        assert "codex" in worker.ready["agents"]
        worker.transport = HTTPTransport(worker.ready["url"], timeout=350)
        runtime = Runtime(store, grid, CodingInspector(ScopedFiles(workspace)))
        prompt = (
            "Fix the nested-interval regression in intervals.py: merge_intervals loses the "
            "larger end when a later interval is contained within it. Preserve overlap/touch "
            "merging, input immutability and reversed-interval rejection. "
            "Change only intervals.py. "
            "Do not commit, create files, install anything or read outside this disposable repo."
        )
        task = runtime.create(
            Intent(
                "fix nested interval merge regression",
                "capability",
                capability_kind="coding",
                parameters={
                    "arguments": [
                        "exec",
                        "--ignore-user-config",
                        "--ephemeral",
                        "--sandbox",
                        "danger-full-access",
                        "--color",
                        "never",
                        "--output-last-message",
                        str(root / "specialist-last-message.txt"),
                        prompt,
                    ],
                    "timeout": 120,
                },
                criterion={"kind": "independent_coding_checks", "initial_head": baseline},
            )
        )
        # Actual useful execution completes, then its response is deliberately lost.
        blocked = runtime.run(
            task.id, {session.node_id: (LostResult(worker.transport, grid), session)}
        )
        assert blocked.state == TaskState.BLOCKED
        dedup = store.db.execute(
            "SELECT state FROM dedup WHERE action_id=?",
            (store.get("planned_action", task.id)["id"],),
        ).fetchone()
        assert dedup and dedup[0] == "completed"
        before = hashlib.sha256((workspace / "intervals.py").read_bytes()).hexdigest()
        worker.close()
        store.close()
        store = Store(state)
        grid = Grid(store)
        session = grid.pair("codex-worker", SCOPES)
        worker = WorkerProcess(
            state,
            workspace,
            session,
            executables=(executable,),
            codex_home=codex_home,
            discover_agents=False,
        )
        runtime = Runtime(store, grid, CodingInspector(ScopedFiles(workspace)))
        runtime.reclaim(task.id)
        verified = runtime.run(task.id, {session.node_id: (worker.transport, session)})
        assert verified.state == TaskState.VERIFIED
        assert before == hashlib.sha256((workspace / "intervals.py").read_bytes()).hexdigest()
        assert len([e for e in store.ledger(task.id) if e["event"] == "machine_execution"]) == 1
        assert all(r["status"] == Epistemic.REPORTED for r in store.all("result"))
        failed = runtime.create(
            Intent(
                "reject invalid Codex coding invocation",
                "capability",
                capability_kind="coding",
                parameters={"arguments": ["exec", "--oscar-invalid-argument"], "timeout": 10},
            )
        )
        assert (
            runtime.run(failed.id, {session.node_id: (worker.transport, session)}).state
            == TaskState.FAILED
        )
        assert before == hashlib.sha256((workspace / "intervals.py").read_bytes()).hexdigest()
        return {
            "status": "VERIFIED",
            "platform": sys.platform,
            "observed_at": time(),
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "objective": "repair nested interval merge while preserving contract",
            "initial_head": baseline,
            "artifact_sha256": before,
            "result_status": "REPORTED",
            "verification_status": verified.state.value,
            "checks": [
                "baseline independently fails",
                "real authenticated Codex mutation",
                "nine independent behavior cases pass",
                "Git sole-file diff and baseline",
                "lost-result restart/reconnect/recovery",
                "one execution, identical hash",
                "real invalid Codex task FAILED without mutation",
            ],
            "workspace": str(workspace),
            "state_path": str(state),
        }
    finally:
        worker.close()
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--codex", required=True)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.state_root, args.codex, args.codex_home)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
