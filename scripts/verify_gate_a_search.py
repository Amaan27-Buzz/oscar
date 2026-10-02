"""Opt-in real Tavily-slot and Jev/provider-inventory/search acceptance evidence."""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from typing import Any
from urllib.parse import urlparse

from oscar.contracts import Task, TaskState
from oscar.freshness import SourceRef
from oscar.harness import Harness
from oscar.jev import Decision, ExecutionClass, Intent, decide
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
    run_started_at = harness.router.clock()
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
    objective_started_at = harness.router.clock()
    # Real reference transport → executor → native HTTPS inventories + Tavily.
    # Do not interpret a partially verified retrieval task as verified factual truth.
    harness.grid.heartbeat(harness.session)
    decision = decide(Intent(OBJECTIVE))
    with ReferenceServer(harness.dispatcher) as server:
        task = harness.runtime.create(Intent(OBJECTIVE), retry_budget=0)
        task = harness.runtime.run(
            task.id, {harness.node_id: (HTTPTransport(server.url, timeout=120), harness.session)}
        )

    return evaluate_search_acceptance(
        harness,
        task,
        decision,
        slots,
        observation_start,
        objective_observation_start,
        objective_started_at,
        run_started_at,
    )


def evaluate_search_acceptance(
    harness: Harness,
    task: Task,
    decision: Decision,
    slots: list[dict[str, Any]],
    observation_start: int,
    objective_observation_start: int,
    objective_started_at: float,
    run_started_at: float,
) -> dict[str, Any]:
    """Inspect an acceptance run's authoritative state; performs no network calls."""

    def current_source(record: dict[str, Any]) -> bool:
        try:
            source_ref = SourceRef(**record["source"])
            return (
                source_ref.current(harness.router.clock())
                and source_ref.observed_at >= objective_started_at
                and record.get("status") == "REPORTED"
            )
        except (KeyError, TypeError, ValueError):
            return False

    all_evidence = [
        e
        for e in harness.store.all("retrieval_evidence")
        if e.get("task_id") == task.id and e.get("correlation_id") == task.correlation_id
    ]
    evidence = [e for e in all_evidence if current_source(e)]
    observations = harness.store.all("search_observation")
    preflight_observations = observations[observation_start:objective_observation_start]
    objective_observations = observations[objective_observation_start:]
    native = [
        e
        for e in evidence
        if e["source"]["scope"] == "account" and e["source"]["authority"] == "live_api"
    ]
    inventories = harness.store.all("model_inventory")
    native_covered = {
        provider.id
        for provider in harness.registry.providers.values()
        if provider.enabled
        and provider.discovery_required
        and any(
            e["source"].get("provider_id") == provider.id
            and e.get("retrieval_method") == "direct"
            and urlparse(e["source"]["identity"]).hostname == urlparse(provider.base_url).hostname
            and any(
                i.get("provider") == provider.id
                and i.get("complete") is True
                and i["source"]["identity"] == e["source"]["identity"]
                and i["source"]["observed_at"] == e["source"]["observed_at"]
                for i in inventories
            )
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
        and o.get("task_id") == task.id
        and o.get("correlation_id") == task.correlation_id
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

    def correlated(record: dict[str, Any]) -> bool:
        return (
            record.get("task_id") == task.id and record.get("correlation_id") == task.correlation_id
        )

    required_slots = {f"tavily-{i}" for i in range(1, 4)}
    preflights_passed = required_slots == {
        row["slot"]
        for row in slots
        if row.get("present")
        and row.get("status") == "OBSERVED"
        and any(
            o.get("slot") == row["slot"]
            and o.get("http_status") == 200
            and o.get("status") == "REPORTED"
            and run_started_at <= o.get("observed_at", -1) <= harness.router.clock()
            for o in preflight_observations
        )
    }
    objective_attempts = {
        o["id"]: o
        for o in objective_observations
        if o.get("id")
        and correlated(o)
        and objective_started_at <= o.get("observed_at", -1) <= harness.router.clock()
    }
    assessments = [
        a
        for a in harness.store.all("constraint_assessment")
        if correlated(a)
        and objective_started_at <= a.get("observed_at", -1) <= harness.router.clock()
    ]
    evidence_by_id = {e["source"].get("evidence_id"): e for e in evidence}
    resolutions: dict[str, str] = {}
    for provider, domains in OFFICIAL_DOMAINS.items():
        rows = [a for a in assessments if a.get("provider") == provider]
        if len(rows) != 1:
            continue
        assessment = rows[0]
        ids = assessment.get("attempt_ids", [])
        attempts = [objective_attempts[i] for i in ids if i in objective_attempts]
        if (
            not attempts
            or len(attempts) != len(ids)
            or len(attempts) > 6
            or not all(
                o.get("provider_id") == provider
                and o.get("purpose") == "official_access_constraints"
                and o.get("query_stage") in {0, 1}
                and o.get("domains")
                and all(d in domains for d in o["domains"])
                for o in attempts
            )
        ):
            continue
        refs = assessment.get("evidence_ids", [])
        relevant = [evidence_by_id[i] for i in refs if i in evidence_by_id]
        if assessment.get("status") == "REPORTED" and refs and len(relevant) == len(refs):
            if all(
                e in web
                and e.get("access_topics")
                and e["source"].get("provider_id") == provider
                and any(
                    m.get("evidence_id") == e["source"].get("evidence_id")
                    for o in attempts
                    for m in o.get("source_metadata", [])
                )
                and domain_matches(urlparse(e["source"]["identity"]).hostname or "", domains)
                for e in relevant
            ):
                resolutions[provider] = "REPORTED"
        elif (
            assessment.get("status") == "UNKNOWN"
            and not refs
            and {o["query_stage"] for o in attempts} == {0, 1}
            and assessment.get("reason")
        ):
            resolutions[provider] = "UNKNOWN"

    metadata_retained = all(
        e["source"].get("evidence_id") and e["source"].get("source_provider") for e in evidence
    )
    # Check source metadata against the adapter's current observations, including
    # preflights. Only retained evidence is required in synthesis; irrelevant hits
    # remain acquisition provenance, not substantive source claims.
    retained_sources = [e["source"] for e in evidence] + [
        s for row in slots for s in row.get("sources", [])
    ]
    for src in retained_sources:
        if src.get("source_provider") != "tavily":
            continue
        matches = [
            m
            for o in preflight_observations + list(objective_attempts.values())
            for m in o.get("source_metadata", [])
            if m.get("evidence_id") == src.get("evidence_id")
        ]
        if len(matches) != 1:
            metadata_retained = False
            continue
        meta = matches[0]
        if (
            meta.get("identity") != src["identity"]
            or meta.get("title") != src.get("title")
            or meta.get("published_at") != src.get("published_at")
            or meta.get("title_returned")
            and src.get("title") is None
        ):
            metadata_retained = False

    syntheses = [s for s in harness.store.all("retrieval_synthesis") if correlated(s)]
    synthesis_semantics = len(syntheses) == 1
    if synthesis_semantics:
        synthesis = syntheses[0]
        claims = {c["provider"]: c for c in synthesis.get("claims", [])}
        synthesis_semantics = (
            synthesis.get("status") == "REPORTED"
            and synthesis.get("conflicts_preserved") is True
            and set(claims) == set(OFFICIAL_DOMAINS)
            and set(synthesis.get("evidence_ids", []))
            == {e["source"].get("evidence_id") for e in all_evidence}
            and all(
                c.get("provider_global_support", "").startswith(
                    "REPORTED" if resolutions.get(p) == "REPORTED" else "UNKNOWN"
                )
                and c.get("account_visible_availability") == "REPORTED live API listing"
                and c.get("generation_probed_state", "").startswith("UNKNOWN")
                and c.get("account_funding", "").startswith("UNKNOWN")
                and c.get("account_quota", "").startswith("UNKNOWN")
                and c.get("public_access_constraints") == resolutions.get(p)
                for p, c in claims.items()
            )
        )
    visible_provenance = successful_result and all(
        e["source"]["identity"] in reported_results[0]["value"]
        and e["source"].get("evidence_id", "") in reported_results[0]["value"]
        and all(conflict in reported_results[0]["value"] for conflict in e.get("conflicts", []))
        for e in all_evidence
    )
    checks = {
        "current_run_three_authenticated_preflights": preflights_passed,
        "six_current_correlated_native_inventories": set(OFFICIAL_DOMAINS) <= native_covered,
        "objective_search_executed": real_search,
        "source_metadata_retained": metadata_retained,
        "visible_provenance_and_conflicts": visible_provenance,
        "six_evidenced_constraint_resolutions": set(resolutions) == set(OFFICIAL_DOMAINS),
        "qualified_synthesis_and_separate_claim_scopes": synthesis_semantics,
        "reported_successful_objective": successful_result,
        "freshness_routed_and_no_unsupported_verification": (
            decision.execution_class == ExecutionClass.RETRIEVAL
            and task.state == TaskState.PARTIALLY_VERIFIED
            and all(e.get("status") == "REPORTED" for e in all_evidence)
        ),
        "no_model_generations": len(harness.store.all("route_history")) == 0,
    }
    accepted = all(checks.values())
    report: dict[str, Any] = {
        "recorded_at": datetime.fromtimestamp(harness.router.clock(), UTC).isoformat(),
        "run_started_at": run_started_at,
        "objective_started_at": objective_started_at,
        "objective": OBJECTIVE,
        "scope": "Final Gate A freshness/search; no model-generation matrix or Slice 05",
        "acceptance": "PASS" if accepted else "PARTIAL",
        "decision": asdict(decision),
        "acceptance_checks": checks,
        "constraint_assessments": assessments,
        "constraint_coverage": resolutions,
        "synthesis": syntheses,
        "objective_result": reported_results,
        "task_state": task.state,
        "tavily_slots": slots,
        "search_observations": observations,
        "slot_preflight_observations": preflight_observations,
        "objective_search_observations": objective_observations,
        "sources": evidence,
        "historical_sources": [e for e in all_evidence if not current_source(e)],
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
