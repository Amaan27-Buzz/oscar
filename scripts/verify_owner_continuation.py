"""Real separate owner/control/Core/Worker processes; synthetic long task only."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from time import sleep, time
from typing import Any

from oscar.capabilities import ScopedFiles
from oscar.contracts import TaskState
from oscar.grid import Grid, Node, NodeRole, SessionHandle
from oscar.jev import Intent
from oscar.machine import MachineVerifier
from oscar.owner_control import OwnerControl
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import HTTPTransport
from scripts.verify_worker_reference import SCOPES, WorkerProcess


def phase(root: Path, stage: str, payload: dict[str, Any]) -> dict[str, Any]:
    store = Store(root / "core.sqlite")
    grid = Grid(store)
    target = SessionHandle(**payload["target"])
    owner = SessionHandle(**payload["owner"])
    transport = HTTPTransport(payload["url"], timeout=20)
    runtime = Runtime(store, grid, MachineVerifier(ScopedFiles(root / "workspace")))
    control = OwnerControl(store, grid, owner, target, transport, runtime)
    try:
        if stage == "run":
            task = runtime.run(payload["task_id"], {target.node_id: (transport, target)})
            return {"pid": os.getpid(), "state": task.state}
        if stage == "recover":
            runtime.reclaim(payload["task_id"])
            task = runtime.run(payload["task_id"], {target.node_id: (transport, target)})
            assert task.state == TaskState.VERIFIED
            return {"pid": os.getpid(), "state": task.state}
        if stage == "cancel":
            control.control(payload["task_id"], "cancel")
        elif stage == "pause":
            ack = control.control(payload["task_id"], "pause")
            assert ack["pause_semantics"] == "before-next-subprocess"
        elif stage == "resume":
            control.control(payload["task_id"], "resume")
        return {"pid": os.getpid(), **control.inspect(payload["task_id"])}
    finally:
        store.close()


def run(root: Path) -> dict[str, Any]:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / "workspace").mkdir()
    store = Store(root / "core.sqlite")
    grid = Grid(store)
    target_id = "continuing-machine"
    grid.register(Node(target_id, NodeRole.DESKTOP, SCOPES))
    target = grid.pair(target_id, SCOPES)
    owner_scopes = tuple(
        "control:" + op + ":" + target_id
        for op in ("inspect", "pause", "resume", "cancel", "revoke")
    )
    grid.register(Node("owner-control-process", NodeRole.DESKTOP, owner_scopes))
    owner = grid.pair("owner-control-process", owner_scopes)
    worker = WorkerProcess(root / "core.sqlite", root / "workspace", target, discover_agents=False)
    env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "TEMP", "TMP") if k in os.environ}
    runtime = Runtime(store, grid, MachineVerifier(ScopedFiles(root / "workspace")))
    processes = []

    def client(stage: str, task_id: str, *, background: bool = False) -> Any:
        payload = {
            "target": {"identifier": target.id, "node_id": target.node_id, "token": target.token},
            "owner": {"identifier": owner.id, "node_id": owner.node_id, "token": owner.token},
            "url": worker.ready["url"],
            "task_id": task_id,
        }
        argv = [
            sys.executable,
            "-m",
            "scripts.verify_owner_continuation",
            "--root",
            str(root),
            "--phase",
            stage,
        ]
        if background:
            process = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            assert process.stdin
            process.stdin.write(json.dumps(payload))
            process.stdin.close()
            processes.append(process)
            return process
        completed = subprocess.run(
            argv, input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=25
        )
        if completed.returncode:
            raise RuntimeError("owner continuation phase failed: " + completed.stderr[-1500:])
        return json.loads(completed.stdout)

    def wait_started(task_id: str) -> None:
        for _ in range(300):
            try:
                if store.get("worker_checkpoint", task_id)["step"] == "process-running":
                    return
            except KeyError:
                pass
            sleep(0.02)
        raise AssertionError("bounded task failed to begin")

    try:
        task = runtime.create(
            Intent(
                "synthetic long continuation proof",
                "capability",
                capability_kind="terminal_command",
                parameters={
                    "argv": [
                        sys.executable,
                        "-c",
                        "import time; from pathlib import Path; time.sleep(8); "
                        "Path('proof.txt').open('x').write('exactly-once')",
                    ],
                    "timeout": 20,
                },
                criterion={"kind": "file_exact", "path": "proof.txt", "content": "exactly-once"},
            )
        )
        coordinator = client("run", task.id, background=True)
        wait_started(task.id)
        first = client("inspect", task.id)
        assert first["checkpoint"]["step"] == "process-running"
        coordinator.terminate()
        coordinator.wait(timeout=5)
        # The first control process is already gone. Neither exit revokes the Worker lease.
        for _ in range(600):
            if (root / "workspace/proof.txt").exists():
                break
            sleep(0.02)
        else:
            raise AssertionError("Worker did not continue after Core/control exit")
        while True:
            row = store.db.execute(
                "SELECT state FROM dedup WHERE action_id=?",
                (store.get("planned_action", task.id)["id"],),
            ).fetchone()
            if row and row[0] == "completed":
                break
            if time() - first["checkpoint"]["observed_at"] > 20:
                raise AssertionError("Worker did not durably finish result")
            sleep(0.05)
        second = client("inspect", task.id)
        assert second["pid"] != first["pid"]
        # Natural lease expiry; never take ownership away from an executing Worker.
        while grid.store.get("lease", store.task(task.id).lease_id or "")["expires_at"] > time():
            sleep(0.25)
        grid.reap()
        recovered = client("recover", task.id)
        assert recovered["pid"] != coordinator.pid
        assert (root / "workspace/proof.txt").read_text() == "exactly-once"
        assert len([e for e in store.ledger(task.id) if e["event"] == "machine_execution"]) == 1
        cancel_task = runtime.create(
            Intent(
                "bounded owner cancellation",
                "capability",
                capability_kind="terminal_command",
                parameters={
                    "argv": [sys.executable, "-c", "import time; time.sleep(15)"],
                    "timeout": 20,
                },
            )
        )
        active = client("run", cancel_task.id, background=True)
        wait_started(cancel_task.id)
        client("pause", cancel_task.id)
        client("resume", cancel_task.id)
        cancelled = client("cancel", cancel_task.id)
        active.wait(timeout=8)
        assert cancelled["state"] == TaskState.CANCELLED
        OwnerControl(store, grid, owner, target, worker.transport, runtime).revoke()
        try:
            grid.authenticate(target, "execute")
        except PermissionError:
            pass
        else:
            raise AssertionError("revoked Worker still authenticated")
        return {
            "status": "VERIFIED",
            "observed_at": time(),
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "worker_pid": worker.process.pid,
            "first_control_pid": first["pid"],
            "second_control_pid": second["pid"],
            "original_core_pid": coordinator.pid,
            "recovery_core_pid": recovered["pid"],
            "cancel_task_id": cancel_task.id,
            "checks": [
                "separate scoped owner processes",
                "Core terminated while Worker continued under unchanged lease",
                "completed result survives natural lease expiry and Core restart",
                "one consequential execution, independently exact file",
                "target-scoped pause/resume/cancel/revoke",
            ],
            "limitations": [
                "shared SQLite and loopback HTTP; no public TLS/cloud",
                "Windows pause is before next subprocess; running process is not frozen",
            ],
        }
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            for stream in (process.stdout, process.stderr):
                if stream:
                    stream.close()
        worker.close()
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--phase", choices=("run", "recover", "inspect", "cancel", "pause", "resume")
    )
    args = parser.parse_args()
    report = phase(args.root, args.phase, json.load(sys.stdin)) if args.phase else run(args.root)
    if not args.phase:
        (args.root / "report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
