"""Integrated real network Worker + policy + verified memory + current context acceptance."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from typing import Any

from oscar.capabilities import ScopedFiles
from oscar.context_sources import FileContextSource
from oscar.continuity import (
    LiveContextFederation,
    LocalMemory,
    MemoryItem,
    MemoryType,
    StateContextSource,
)
from oscar.contracts import Epistemic, TaskState
from oscar.freshness import Authority, SourceRef
from oscar.grid import Grid, Node, NodeRole
from oscar.jev import Intent
from oscar.machine import MachineVerifier
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.runtime import Runtime
from oscar.storage import Store
from scripts.verify_worker_reference import SCOPES, WorkerProcess, initialize_repository


def run_integrated(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / "repository"
    workspace.mkdir()
    initial = initialize_repository(workspace)
    state = root / "core.sqlite"
    store = Store(state)
    grid = Grid(store)
    grid.register(Node("integrated-worker", NodeRole.DESKTOP, SCOPES))
    session = grid.pair("integrated-worker", SCOPES)
    worker = WorkerProcess(state, workspace, session)
    try:
        policy = PersonalPolicy(store)
        now = time()
        policy.save(
            PolicyRule(
                "repository-work",
                "machine.repository",
                PolicyEffect.DENY,
                "explicit owner structured editor",
                now,
                now,
                {},
            ),
            owner_authorized=True,
        )
        runtime = Runtime(store, grid, MachineVerifier(ScopedFiles(workspace)))
        intent = Intent(
            "create project artifact through approved machine capability",
            "capability",
            capability_kind="repository_task",
            parameters={
                "path": "verified.txt",
                "content": "verified project outcome\n",
                "message": "integrated artifact",
            },
            criterion={
                "kind": "git_file_exact",
                "path": "verified.txt",
                "content": "verified project outcome\n",
                "initial_head": initial,
            },
        )
        blocked = runtime.create(intent)
        transports = {session.node_id: (worker.transport, session)}
        assert runtime.run(blocked.id, transports).state == TaskState.BLOCKED
        assert not (workspace / "verified.txt").exists()
        policy.save(
            PolicyRule(
                "repository-work",
                "machine.repository",
                PolicyEffect.ALLOW,
                "explicit owner structured editor",
                now,
                time(),
                {},
            ),
            owner_authorized=True,
        )
        # A new objective after policy approval; old denied result remains historical testimony.
        task = runtime.create(intent)
        assert runtime.run(task.id, transports).state == TaskState.VERIFIED
        evidence = next(e for e in store.all("evidence") if e["task_id"] == task.id)
        result = next(r for r in store.all("result") if r["task_id"] == task.id)
        assert result["status"] == Epistemic.REPORTED and evidence["status"] == Epistemic.VERIFIED
        memory = LocalMemory(store)
        source = SourceRef(
            "local://verified-project-artifact",
            Authority.LIVE_API,
            "local",
            evidence["observed_at"],
            5,
            evidence_id=evidence["id"],
        )
        memory.retain(
            MemoryItem(
                "project-outcome",
                "project.artifact",
                "verified project outcome\n",
                "reference-project",
                MemoryType.PROJECT,
                source,
                time(),
                Epistemic.VERIFIED,
                retention_reason="explicit selected verified outcome",
            ),
            retention_authorized=True,
        )
        files = ScopedFiles(workspace)
        federation = LiveContextFederation(
            memory,
            (
                FileContextSource(files, "reference-project", {"project.artifact": "verified.txt"}),
                StateContextSource(store, grid.nodes, "reference-project"),
            ),
        )
        context = federation.assemble(task.id, "project", "reference-project")
        assert context.memories[0].evidence_state == Epistemic.RECALLED
        # A genuine subsequent external file change must outrank that verified historical memory.
        (workspace / "verified.txt").write_bytes(b"current changed artifact\n")
        changed = federation.assemble(task.id, "project", "reference-project")
        resolved = changed.resolve("project.artifact", time())
        assert resolved and resolved.value == "current changed artifact\n"
        assert resolved.state == Epistemic.KNOWN
        assert changed.memories[0].content == "verified project outcome\n"
        memory.forget("project-outcome", owner_authorized=True)
        assert not memory.retrieve("project", "reference-project")
        return {
            "status": "VERIFIED",
            "scope": "integrated local/reference Club B foundation",
            "gate_b": "PARTIAL",
            "observed_at": time(),
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "checks": [
                "Jev structured objective",
                "existing Capability Catalog/Dispatcher",
                "target Personal Policy denial then explicit approval",
                "separate HTTP Worker",
                "real Git/file artifact",
                "Core independent verification + ledger evidence",
                "verified selected project retention",
                "later recall remains RECALLED",
                "actual changed file overrides historical memory",
                "forget live record",
            ],
            "limitations": [
                "Windows/browser/computer-use unverified",
                "natural-language policy absent",
                "Supermemory live integration unverified",
                "shared SQLite loopback reference",
            ],
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
        report = run_integrated(args.state_root)
    else:
        with TemporaryDirectory() as temporary:
            report = run_integrated(Path(temporary))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
