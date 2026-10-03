"""Separate coordinator OS-process restart, Worker reconnect and local memory/policy proof."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from time import time
from typing import Any

from oscar.capabilities import ScopedFiles
from oscar.context_sources import FileContextSource
from oscar.continuity import LiveContextFederation, LocalMemory, MemoryItem, MemoryType
from oscar.contracts import Epistemic, TaskState
from oscar.freshness import Authority, SourceRef
from oscar.grid import Grid, Node, NodeRole, SessionHandle
from oscar.jev import Intent
from oscar.machine import MachineVerifier
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.policy_authoring import PolicyAuthoring
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import HTTPTransport
from scripts.verify_worker_reference import SCOPES, LostResult, WorkerProcess, initialize_repository


def phase(root: Path, stage: str, bootstrap: dict[str, Any]) -> dict[str, Any]:
    store = Store(root / "core.sqlite")
    grid = Grid(store)
    session = SessionHandle(
        bootstrap["session"]["id"], bootstrap["session"]["node_id"], bootstrap["session"]["token"]
    )
    transport = HTTPTransport(bootstrap["url"])
    files = ScopedFiles(root / "repository")
    runtime = Runtime(store, grid, MachineVerifier(files))
    memory = LocalMemory(store)
    policy = PersonalPolicy(store)
    try:
        if stage == "start":
            task = runtime.create(
                Intent(
                    "commit selected local project outcome",
                    "capability",
                    capability_kind="repository_task",
                    parameters={
                        "path": "result.txt",
                        "content": "project outcome\n",
                        "message": "local continuation proof",
                    },
                    criterion={
                        "kind": "git_file_exact",
                        "path": "result.txt",
                        "content": "project outcome\n",
                        "initial_head": bootstrap["initial_head"],
                    },
                )
            )
            assert (
                runtime.run(
                    task.id, {session.node_id: (LostResult(transport, grid), session)}
                ).state
                == TaskState.BLOCKED
            )
            candidate = PolicyAuthoring(policy).propose("Never send messages without asking me.")
            PolicyAuthoring(policy).confirm(
                candidate["id"], candidate["review_digest"], owner_authorized=True
            )
            memory.retain(
                MemoryItem(
                    "project-history",
                    "project.artifact",
                    "historical project outcome",
                    "local-project",
                    MemoryType.PROJECT,
                    SourceRef("local://selected-project", Authority.CACHE, "local", time()),
                    time(),
                    retention_reason="explicit fixture owner selected retention",
                ),
                retention_authorized=True,
            )
            return {
                "task_id": task.id,
                "pid": os.getpid(),
                "status": "BLOCKED",
                "checkpoint": store.get("worker_checkpoint", task.id),
            }
        task_id = bootstrap["task_id"]
        runtime.reclaim(task_id)
        assert (
            runtime.run(task_id, {session.node_id: (transport, session)}).state
            == TaskState.VERIFIED
        )
        assert len([e for e in store.ledger(task_id) if e["event"] == "machine_execution"]) == 1
        assert all(r["status"] == Epistemic.REPORTED for r in store.all("result"))
        recalled = memory.retrieve("project", "local-project")
        assert len(recalled) == 1 and recalled[0].evidence_state == Epistemic.RECALLED
        # Independent real filesystem update after verified Git recovery.
        (files.root / "result.txt").write_bytes(b"live changed project\n")
        context = LiveContextFederation(
            memory, (FileContextSource(files, "local-project", {"project.artifact": "result.txt"}),)
        ).assemble(task_id, "project", "local-project")
        live = context.resolve("project.artifact", time())
        assert live and live.value == "live changed project\n" and live.state == Epistemic.KNOWN
        permission = "connectors:external-communication"
        assert not policy.evaluate(permission, (permission,), frozenset({permission})).allowed
        assert policy.evaluate(
            permission, (permission,), frozenset({permission}), confirmed=True
        ).allowed
        assert not policy.evaluate(permission, (permission,), frozenset(), confirmed=True).allowed
        now = time()
        policy.save(
            PolicyRule(
                "conflict", permission, PolicyEffect.ALLOW, "explicit test owner", now, now, {}
            ),
            owner_authorized=True,
        )
        assert (
            "conflicting"
            in policy.evaluate(
                permission, (permission,), frozenset({permission}), confirmed=True
            ).reason
        )
        memory.forget("project-history", owner_authorized=True)
        assert not memory.retrieve("project", "local-project")
        return {
            "task_id": task_id,
            "pid": os.getpid(),
            "status": "VERIFIED",
            "checks": [
                "completed result reused once after coordinator OS-process restart",
                "Worker OS-process restart and reconnect",
                "independent Git/file evidence",
                "selected project memory persisted and stays RECALLED",
                "live filesystem overrides stale memory",
                "owner-confirmed policy persisted",
                "policy cannot grant permissions",
                "conflicting policies BLOCK",
                "forget removes live OSCAR row; no secure-erasure claim",
            ],
        }
    finally:
        store.close()


def run(root: Path) -> dict[str, Any]:
    root = root.absolute()
    root.mkdir(parents=True, exist_ok=False)
    workspace = root / "repository"
    workspace.mkdir()
    initial = initialize_repository(workspace)
    state = root / "core.sqlite"
    store = Store(state)
    grid = Grid(store)
    grid.register(Node("continuation-worker", NodeRole.DESKTOP, SCOPES))
    session = grid.pair("continuation-worker", SCOPES)
    worker = WorkerProcess(state, workspace, session, discover_agents=False)
    try:

        def coordinator(stage: str, extra: dict[str, Any]) -> dict[str, Any]:
            payload = {
                "session": {"id": session.id, "node_id": session.node_id, "token": session.token},
                "url": worker.ready["url"],
                **extra,
            }
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.verify_local_continuation",
                    "--phase",
                    stage,
                    "--state-root",
                    str(root),
                ],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=30,
                env={
                    k: os.environ[k]
                    for k in ("PATH", "SystemRoot", "TEMP", "TMP")
                    if k in os.environ
                },
            )
            if result.returncode:
                raise RuntimeError("coordinator proof failed: " + result.stderr[-1500:])
            return json.loads(result.stdout)  # type: ignore[no-any-return]

        started = coordinator("start", {"initial_head": initial})
        worker.close()
        store.close()
        store = Store(state)
        grid = Grid(store)
        session = grid.pair("continuation-worker", SCOPES)
        worker = WorkerProcess(state, workspace, session, discover_agents=False)
        recovered = coordinator("recover", {"task_id": started["task_id"]})
        assert started["pid"] != recovered["pid"]
        assert store.get("worker_checkpoint", started["task_id"]) == started["checkpoint"]
        return {
            "status": "VERIFIED",
            "platform": sys.platform,
            "observed_at": time(),
            "start_coordinator_pid": started["pid"],
            "recovery_coordinator_pid": recovered["pid"],
            **recovered,
            "limitations": [
                "shared SQLite authority, loopback transport",
                "Supermemory not configured/exercised",
                "live-record forget is not secure disk erasure",
            ],
        }
    finally:
        worker.close()
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--phase", choices=("start", "recover"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = (
        phase(args.state_root, args.phase, json.load(sys.stdin))
        if args.phase
        else run(args.state_root)
    )
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
