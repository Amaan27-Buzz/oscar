"""Confirm a reviewed synthetic live-model candidate, then independently test enforcement."""

import argparse
import json
from pathlib import Path

from oscar.contracts import TaskState
from oscar.grid import Grid, Node, NodeRole
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier, MachineWorker
from oscar.policy import PersonalPolicy
from oscar.policy_interpretation import OpenPolicyAuthoring
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import Dispatcher


def run(state: Path, root: Path, candidate_id: str) -> dict:
    store = Store(state)
    try:
        candidate = store.get("open_policy_candidate", candidate_id)
        assert candidate["state"] == "candidate"
        assert len(candidate["rules"]) == 1
        rule = candidate["rules"][0]
        assert (rule["capability"], rule["effect"], rule["conditions"]) == (
            "machine.files.write",
            "ask",
            {},
        )
        assert not rule["enabled"] and not rule["user_authoritative"]
        assert not PersonalPolicy(store).rules()

        # Only this isolated synthetic fixture is confirmed; no owner production policy changes.
        class NoModelConfirmation:
            def interpret(self, text):
                raise AssertionError("confirmation cannot invoke a model")

        OpenPolicyAuthoring(PersonalPolicy(store), NoModelConfirmation()).confirm(
            candidate_id,
            candidate["review_digest"],
            owner_authorized=True,
        )
    finally:
        store.close()
    store = Store(state)  # separate connection proves persisted policy
    try:
        root.mkdir(parents=True, exist_ok=False)
        grid = Grid(store)
        grants = ("heartbeat", "advertise", "execute", "cancel", "files:write", "files:read")
        grid.register(Node("policy-fixture", NodeRole.DESKTOP, grants))
        session = grid.pair("policy-fixture", grants)
        worker = MachineWorker(store, grid, session, MachineScope(root))
        grid.advertise(session, worker.capabilities())
        runtime = Runtime(store, grid, MachineVerifier(worker.files))
        task = runtime.create(
            Intent("synthetic policy proof", "file_write", "blocked.txt", "proof")
        )
        result = runtime.run(
            task.id,
            {
                session.node_id: (
                    Dispatcher(store, grid, session.node_id, worker.executors()),
                    session,
                ),
            },
        )
        assert result.state in {TaskState.BLOCKED, TaskState.FAILED}
        assert not (root / "blocked.txt").exists()
        outcome = next(r for r in store.all("result") if r["task_id"] == task.id)
        assert outcome["error"] == "machine_blocked:policy"
        assert outcome["status"] == "REPORTED"
        report = {
            "status": "VERIFIED",
            "fixture_only": True,
            "candidate_id": candidate_id,
            "task_id": task.id,
            "result_status": "REPORTED",
            "task_state": result.state,
            "checks": [
                "live native router candidate was inactive",
                "exact synthetic owner review",
                "policy survives database reopen",
                "Worker enforces ASK",
                "independent absent file",
            ],
        }
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.state, args.root.resolve(), args.candidate), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
