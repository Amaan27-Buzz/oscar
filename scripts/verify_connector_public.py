"""Opt-in unauthenticated public GitHub read; no private account verification claim."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.capabilities import Cancellation
from oscar.connector_providers import github_manifest
from oscar.connectors import ConnectorFabric, ConnectorInstance, EnvironmentSecrets
from oscar.contracts import Action, Epistemic, Task, new_id, record
from oscar.policy import PersonalPolicy
from oscar.storage import Store


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-public", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.run_public:
        parser.error("explicit --run-public required for public network traffic")
    with TemporaryDirectory() as temporary:
        store = Store(Path(temporary) / "state.sqlite")
        try:
            manifest = github_manifest(public=True)
            fabric = ConnectorFabric(store, EnvironmentSecrets({}), PersonalPolicy(store))
            fabric.install(ConnectorInstance("public", manifest))
            task = Task(new_id(), new_id(), new_id())
            store.put("task", task.id, record(task))
            action = Action(
                new_id(),
                task.id,
                task.correlation_id,
                "public:github.repositories.get",
                {"path": {"owner": "python", "repo": "cpython"}},
                task.id,
                "owner",
            )
            outcome = fabric.execute(
                "public",
                "github.repositories.get",
                action,
                Cancellation(store, task.id),
                frozenset({"connectors:read"}),
            )
            matched = (
                outcome.result.success and outcome.payload.get("full_name") == "python/cpython"
            )
            assert outcome.result.status == Epistemic.REPORTED
            report = {
                "status": "VERIFIED" if matched else "BLOCKED",
                "scope": "public unauthenticated GitHub repository response contract only",
                "source_url": outcome.source.identity if outcome.source else None,
                "observed_at": outcome.source.observed_at if outcome.source else time(),
                "evidence_id": outcome.source.evidence_id if outcome.source else None,
                "execution_status": outcome.result.status,
                "contract_matches": matched,
                "error": outcome.result.error,
                "limitations": [
                    "private/authenticated GitHub unverified",
                    "provider data remains REPORTED",
                    "no writes or user-account actions performed",
                ],
            }
        finally:
            store.close()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if matched else 2


if __name__ == "__main__":
    raise SystemExit(main())
