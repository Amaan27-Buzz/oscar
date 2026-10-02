"""Opt-in real Tavily-slot and Jev/provider-inventory/search acceptance evidence."""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from typing import Any
from urllib.parse import urlparse

from oscar.contracts import TaskState
from oscar.freshness import SourceRef
from oscar.harness import Harness
from oscar.jev import ExecutionClass, Intent, decide
from oscar.models import ProviderError
from oscar.retrieval import RetrievalRequest
from oscar.search import OFFICIAL_DOMAINS, domain_matches
from oscar.transport import HTTPTransport, ReferenceServer

OBJECTIVE = (
    "What are the currently supported models and relevant free/developer access "
    "constraints for OSCAR's configured intelligence providers right now?"
)


def search_acceptance(harness: Harness) -> dict[str, Any]:
    source = harness.search
    observation_start = len(harness.store.all("search_observation"))
    slots: list[dict[str, Any]] = []
    for slot in source.pool.slots.values():
        row: dict[str, Any] = {"slot": slot.id, "present": slot.present}
        if not slot.present:
            row.update(status="BLOCKED", reason="credential absent")
        else:
            try:
                result = source.search(
                    RetrievalRequest(
                        "Groq currently supported models free developer access rate limits",
                        domains=OFFICIAL_DOMAINS["groq"],
                        result_limit=1,
                    ),
                    slot.id,
                    lambda: None,
                )
                row.update(
                    status="OBSERVED" if result.facts else "PARTIAL",
                    sources=[asdict(f.source) for f in result.facts],
                )
            except ProviderError as error:
                row.update(
                    status="UNAVAILABLE",
                    category=error.category.value,
                    http_status=error.http_status,
                )
        slots.append(row)
    # This verifier owns an isolated, sequential Harness. Snapshot the boundary so
    # slot diagnostics cannot masquerade as searches performed by the objective.
    objective_observation_start = len(harness.store.all("search_observation"))
    # Real reference transport → executor → native HTTPS inventories + Tavily.
    # Do not interpret a partially verified retrieval task as verified factual truth.
    harness.grid.heartbeat(harness.session)
    decision = decide(Intent(OBJECTIVE))
    with ReferenceServer(harness.dispatcher) as server:
        task = harness.runtime.create(Intent(OBJECTIVE), retry_budget=0)
        task = harness.runtime.run(
            task.id, {harness.node_id: (HTTPTransport(server.url, timeout=120), harness.session)}
        )

    def current_source(record: dict[str, Any]) -> bool:
        try:
            return SourceRef(**record["source"]).current(harness.router.clock())
        except (KeyError, TypeError, ValueError):
            return False

    evidence = [
        e
        for e in harness.store.all("retrieval_evidence")
        if e.get("task_id") == task.id
        and e.get("correlation_id") == task.correlation_id
        and current_source(e)
    ]
    observations = harness.store.all("search_observation")
    preflight_observations = observations[observation_start:objective_observation_start]
    objective_observations = observations[objective_observation_start:]
    native = [
        e
        for e in evidence
        if e["source"]["scope"] == "account" and e["source"]["authority"] == "live_api"
    ]
    native_covered = {
        provider.id
        for provider in harness.registry.providers.values()
        if provider.enabled
        and provider.discovery_required
        and any(
            urlparse(e["source"]["identity"]).hostname == urlparse(provider.base_url).hostname
            for e in native
        )
    }
    web = [
        e
        for e in evidence
        if e["source"]["scope"] == "provider"
        and e["source"]["authority"] == "official_docs"
        and e.get("retrieval_method") == "official_page"
    ]
    # Indexed snippets, prior tasks and retirement seeds cannot substitute for a
    # successful live search and direct official-page reads during this objective.
    real_search = any(
        o.get("status") == "REPORTED"
        and o.get("http_status") == 200
        and o.get("retained_sources", 0) > 0
        for o in objective_observations
    )
    covered = {
        provider
        for provider, domains in OFFICIAL_DOMAINS.items()
        if any(
            domain_matches(urlparse(e["source"]["identity"]).hostname or "", domains) for e in web
        )
    }
    action_ids = {
        a["id"]
        for a in harness.store.all("action")
        if a.get("task_id") == task.id
        and a.get("correlation_id") == task.correlation_id
        and a.get("capability_id") == "sources.retrieve"
    }
    reported_results = [
        r
        for r in harness.store.all("result")
        if r.get("task_id") == task.id
        and r.get("correlation_id") == task.correlation_id
        and r.get("action_id") in action_ids
        and r.get("executor") == "sources.retrieve"
        and r.get("success") is True
        and r.get("status") == "REPORTED"
        and isinstance(r.get("value"), str)
        and bool(r["value"].strip())
    ]
    successful_result = len(reported_results) == 1
    accepted = (
        decision.execution_class == ExecutionClass.RETRIEVAL
        and task.state == TaskState.PARTIALLY_VERIFIED
        and successful_result
        and set(OFFICIAL_DOMAINS) <= native_covered
        and real_search
        and set(OFFICIAL_DOMAINS) <= covered
    )
    report: dict[str, Any] = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "objective": OBJECTIVE,
        "scope": "Final Gate A freshness/search; no model-generation matrix or Slice 05",
        "acceptance": "PASS" if accepted else "PARTIAL",
        "decision": asdict(decision),
        "task_state": task.state,
        "tavily_slots": slots,
        "search_observations": observations,
        "slot_preflight_observations": preflight_observations,
        "objective_search_observations": objective_observations,
        "sources": evidence,
        "official_web_coverage": sorted(covered),
        "native_provider_coverage": sorted(native_covered),
        "native_inventory_sources": len(native),
        "actual_live_tavily": real_search,
        "objective_result_reported_success": successful_result,
        "generation_calls": len(harness.store.all("route_history")),
        "authority_resolution": "Account API outranks web for account listing; applicable "
        "official retirement evidence overrides residual catalog listing. Conflicts are "
        "explicit; web excerpts cannot change routing entitlement or funding.",
        "limitations": [
            "Retrieved official pages remain REPORTED evidence, not general factual "
            "verification. Index-only snippets do not satisfy official-page acceptance; "
            "account funding/credits remain UNKNOWN unless separately exposed."
        ]
        + (
            []
            if real_search
            else [
                "No successful live Tavily search during this objective: actual "
                "live objective search UNVERIFIED; official access-constraint synthesis BLOCKED."
            ]
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--manifest", type=Path, default=Path("config/development-models.json"))
    parser.add_argument("--report", type=Path, default=Path(".oscar/final-gate-a-search.json"))
    args = parser.parse_args()
    if not args.run_live:
        parser.error("network traffic requires --run-live")
    Path(".oscar").mkdir(exist_ok=True)
    directory = Path(mkdtemp(prefix="gate-a-search-", dir=".oscar"))
    with Harness(directory / "state.sqlite", directory / "workspace", args.manifest) as harness:
        report = search_acceptance(harness)
        encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if (
            harness.pool.redact(encoded) != encoded
            or harness.search.pool.redact(encoded) != encoded
        ):
            raise ValueError("secret-safety failed; report suppressed")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded)
        args.report.chmod(0o600)
        print(
            json.dumps(
                {
                    key: report[key]
                    for key in (
                        "acceptance",
                        "tavily_slots",
                        "native_inventory_sources",
                        "actual_live_tavily",
                        "generation_calls",
                        "task_state",
                    )
                }
            )
        )
        return int(report["acceptance"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
