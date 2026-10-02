"""Real separate-process/network reference Worker acceptance; no user-machine claims."""

import argparse
import json
import os
import selectors
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep, time
from typing import Any

from oscar.capabilities import ScopedFiles
from oscar.contracts import Envelope, Result, TaskState
from oscar.grid import Grid, Node, NodeRole, SessionHandle
from oscar.jev import Intent
from oscar.machine import AGENT_EXECUTABLES, MachineVerifier
from oscar.runtime import Runtime
from oscar.storage import StateConflict, Store
from oscar.transport import HTTPTransport

SCOPES = (
    "heartbeat",
    "advertise",
    "execute",
    "cancel",
    "pause",
    "files:read",
    "files:write",
    "machine:host",
)


class WorkerProcess:
    def __init__(self, state: Path, workspace: Path, session: SessionHandle):
        git = shutil.which("git")
        assert git is not None
        # Bootstrap over inherited pipe; child inherits no provider/GitHub credentials.
        env = {k: os.environ[k] for k in ("PATH", "LANG") if k in os.environ}
        agent_args = []
        for executable in AGENT_EXECUTABLES.values():
            if installed := shutil.which(executable):
                agent_args.extend(["--executable", installed])
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "oscar.machine_node",
                "--state",
                str(state),
                "--workspace",
                str(workspace),
                "--trusted-host",
                "--executable",
                git,
                "--executable",
                sys.executable,
                *agent_args,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            text=True,
        )
        assert self.process.stdin and self.process.stdout
        self.process.stdin.write(
            json.dumps({"id": session.id, "node_id": session.node_id, "token": session.token})
            + "\n"
        )
        self.process.stdin.flush()
        self.process.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            if not selector.select(timeout=10):
                self.close()
                raise RuntimeError("reference worker startup timeout")
        line = self.process.stdout.readline(8192)
        if not line:
            self.close()
            raise RuntimeError("reference worker startup failed")
        self.ready: dict[str, Any] = json.loads(line)
        self.transport = HTTPTransport(self.ready["url"], timeout=5)

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        if self.process.stdout:
            self.process.stdout.close()


class LostResult:
    """Actual HTTP request executes; response is lost before Core accepts the result."""

    def __init__(self, transport: HTTPTransport, grid: Grid):
        self.transport, self.grid = transport, grid

    def invoke(self, envelope: Envelope, session: SessionHandle) -> Result:
        self.transport.invoke(envelope, session)
        self.grid.disconnect(session.node_id)
        raise StateConflict("simulated transient response loss after actual network execution")

    def control(self, envelope: Envelope, session: SessionHandle) -> dict[str, Any]:
        return self.transport.control(envelope, session)


def initialize_repository(workspace: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Reference",
            "-c",
            "user.email=r@example.invalid",
            "-c",
            "core.hooksPath=" + os.devnull,
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-qm",
            "initial",
        ],
        cwd=workspace,
        check=True,
    )
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=workspace, text=True).strip()


def run_reference(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / "repository"
    workspace.mkdir()
    initial = initialize_repository(workspace)
    state = root / "core.sqlite"
    store = Store(state)
    grid = Grid(store)
    grid.register(Node("network-worker", NodeRole.DESKTOP, SCOPES))
    session = grid.pair("network-worker", SCOPES)
    worker = WorkerProcess(state, workspace, session)
    try:
        runtime = Runtime(store, grid, MachineVerifier(ScopedFiles(workspace)))
        intent = Intent(
            "create and commit exact reference artifact",
            "capability",
            capability_kind="repository_task",
            parameters={
                "path": "result.txt",
                "content": "reference verified\n",
                "message": "reference artifact",
            },
            criterion={
                "kind": "git_file_exact",
                "path": "result.txt",
                "content": "reference verified\n",
                "initial_head": initial,
            },
        )
        task = runtime.create(intent)
        blocked = runtime.run(
            task.id, {session.node_id: (LostResult(worker.transport, grid), session)}
        )
        assert blocked.state == TaskState.BLOCKED
        assert store.get("worker_checkpoint", task.id)["fraction"] == 1
        assert (workspace / "result.txt").read_text() == "reference verified\n"
        commit_before_replay = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=workspace, text=True
        ).strip()
        checkpoint = store.get("worker_checkpoint", task.id)
        worker.close()
        store.close()
        # Both processes and Core composition restart against durable state.
        store = Store(state)
        grid = Grid(store)
        session = grid.pair("network-worker", SCOPES)
        worker = WorkerProcess(state, workspace, session)
        runtime = Runtime(store, grid, MachineVerifier(ScopedFiles(workspace)))
        assert store.get("worker_checkpoint", task.id) == checkpoint
        runtime.reclaim(task.id)
        verified = runtime.run(task.id, {session.node_id: (worker.transport, session)})
        assert verified.state == TaskState.VERIFIED
        assert (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=workspace, text=True).strip()
            == commit_before_replay
        )
        assert len([e for e in store.ledger(task.id) if e["event"] == "machine_execution"]) == 1
        assert any(e["event"] == "progress_observed" for e in store.ledger(task.id))
        assert all(r["status"] == "REPORTED" for r in store.all("result"))
        assert any(e["status"] == "VERIFIED" for e in store.all("evidence"))
        agent_tests = []
        if worker.ready["agents"]:
            version_task = runtime.create(
                Intent(
                    "installed coding agent version",
                    "capability",
                    capability_kind="coding",
                    parameters={"arguments": ["--version"], "timeout": 10},
                )
            )
            version_task = runtime.run(
                version_task.id, {session.node_id: (worker.transport, session)}
            )
            version_result = next(r for r in store.all("result") if r["task_id"] == version_task.id)
            assert version_result["success"]
            agent_tests.append(
                {
                    "capability": version_result["executor"],
                    "test": "--version subprocess only; no model task",
                    "success": True,
                }
            )
        # Native HTTP pause/resume/cancel against an actually running separate-process command.
        long = runtime.create(
            Intent(
                "reference long-running job",
                "capability",
                capability_kind="terminal_command",
                parameters={
                    "argv": [sys.executable, "-c", "import time; time.sleep(20)"],
                    "timeout": 30,
                },
            )
        )
        transports = {session.node_id: (worker.transport, session)}
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(runtime.run, long.id, transports)
            for _ in range(100):
                try:
                    store.get("worker_checkpoint", long.id)
                    break
                except KeyError:
                    sleep(0.02)
            for kind in ("pause", "resume"):
                current = store.task(long.id)
                envelope = Envelope(
                    kind,
                    session.node_id,
                    session.id,
                    current.id,
                    current.correlation_id,
                    current.lease_id or "",
                    {},
                    time(),
                )
                ack = worker.transport.control(envelope, session)
                assert ack["kind"] == kind
            runtime.cancel(long.id, transports)
            assert running.result(timeout=5).state == TaskState.CANCELLED
        # Real mid-command process/node loss leaves ambiguous side effects BLOCKED.
        lost = runtime.create(
            Intent(
                "reference crash ambiguity",
                "capability",
                capability_kind="terminal_command",
                parameters={
                    "argv": [sys.executable, "-c", "import time; time.sleep(20)"],
                    "timeout": 30,
                },
            )
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(runtime.run, lost.id, transports)
            for _ in range(100):
                if store.task(lost.id).state == TaskState.AWAITING_RESULT:
                    try:
                        store.get("worker_checkpoint", lost.id)
                        break
                    except KeyError:
                        pass
                sleep(0.02)
            grid.disconnect(session.node_id)
            assert running.result(timeout=5).state == TaskState.BLOCKED
        runtime.reclaim(lost.id)
        # Started dedup entry remains ambiguous; replay is prohibited by the existing Dispatcher.
        dedup = store.db.execute(
            "SELECT state FROM dedup WHERE action_id=?",
            (store.get("planned_action", lost.id)["id"],),
        ).fetchone()
        assert dedup and dedup[0] == "started"
        # Do not leave reclaimed task apparently pending when no safe retry is permitted.
        store.transition(
            lost.id, TaskState.BLOCKED, blocker="crash outcome ambiguous; inspect before replay"
        )
        return {
            "status": "VERIFIED",
            "scope": "reference network Worker verification",
            "observed_at": time(),
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "artifact_commit": commit_before_replay,
            "capabilities": worker.ready["capabilities"],
            "coding_agents_advertised": worker.ready["agents"],
            "coding_agent_tests": agent_tests,
            "checks": [
                "separate Core/Worker processes",
                "real loopback HTTP",
                "file/Git work",
                "durable progress/checkpoint",
                "lost response + Core/Worker restart",
                "reconnect/reclaim + idempotent completed replay",
                "independent bytes/Git tree",
                "HTTP pause/resume/cancel",
                "mid-command node loss BLOCKED; replay ambiguous",
            ],
            "limitations": [
                "shared SQLite reference authority",
                "loopback-only transport",
                "user Windows laptop unverified",
                "coding-agent invocation unverified",
                "public TLS/rendezvous and independent stores unverified",
            ],
            "state_path": str(state),
            "workspace": str(workspace),
        }
    finally:
        worker.close()
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--state-root", type=Path)
    args = parser.parse_args()
    if args.state_root:
        report = run_reference(args.state_root)
    else:
        with TemporaryDirectory() as temporary:
            report = run_reference(Path(temporary))
            report["state_path"] = "temporary reference state removed"
            report["workspace"] = "temporary reference workspace removed"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
