"""Opt-in post-Gate-A correction verification using current account inventory first."""

import argparse
import json
import os
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from time import time
from typing import Any
from urllib.error import HTTPError

from oscar.cli import grid_proof, proof
from oscar.contracts import Epistemic, Evidence, new_id, record
from oscar.harness import Harness
from oscar.models import Funding, Mode, ModelRequest, ProviderError, RoutingPolicy
from oscar.router import RouteUnavailable


class HTTPStatuses:
    """Only categorical status is retained, never requests, credentials or bodies."""

    def __init__(self, opener: Any):
        self.opener = opener
        self.statuses: list[int] = []

    def open(self, *args: Any, **kwargs: Any) -> Any:
        try:
            response = self.opener.open(*args, **kwargs)
            self.statuses.append(response.status)
            return response
        except HTTPError as error:
            self.statuses.append(error.code)
            raise


class Verification:
    def __init__(self, manifest: Path, directory: Path, unknown_cost: bool):
        self.directory, self.unknown_cost = directory, unknown_cost
        self.h = Harness(directory / "live.sqlite", directory / "workspace", manifest)
        self.seed_keys = set(self.h.registry.models)
        self.checks: list[dict[str, Any]] = []
        self.inventories: list[dict[str, Any]] = []
        self.operations: list[dict[str, Any]] = []
        self.accounts: list[dict[str, Any]] = []
        self.previous: list[dict[str, Any]] = []
        self.previous_source: str | None = None
        self.statuses: dict[str, HTTPStatuses] = {}
        for kind, adapter in self.h.adapters.items():
            observer = HTTPStatuses(adapter.opener)
            adapter.opener = observer  # type: ignore[assignment]
            self.statuses[kind] = observer

    def check(self, name: str, matches: bool) -> None:
        self.checks.append({"check": name, "status": "PASS" if matches else "FAIL"})

    def account(self, provider_id: str, slot: str) -> None:
        discovery = self.h.router.discovery
        assert discovery is not None
        provider = self.h.registry.providers[provider_id]
        try:
            observation = discovery.account(provider, self.h.pool.secret_for_adapter(slot))
        except ProviderError:
            return
        if observation:
            self.accounts.append({"provider": provider_id, "slot": slot, **asdict(observation)})
            if observation.limits:
                self.h.pool.observe_limits(slot, "*", observation.limits)

    def discover(self) -> None:
        discovery = self.h.router.discovery
        assert discovery is not None
        for provider in self.h.registry.providers.values():
            if not provider.enabled:
                continue
            for slot in self.h.pool.slots.values():
                if slot.provider != provider.id:
                    continue
                row: dict[str, Any] = {"provider": provider.id, "slot": slot.id}
                if not slot.present:
                    row.update(status="BLOCKED", reason="credential absent")
                else:
                    try:
                        inventory = discovery.inventory(
                            provider, slot.id, self.h.pool.secret_for_adapter(slot.id), 12
                        )
                        self.h.registry.apply_inventory(inventory)
                        relevant = [
                            m
                            for m in inventory.models
                            if provider.id != "openrouter" or m.funding == Funding.FREE
                        ]
                        row.update(
                            status="OBSERVED",
                            source=asdict(inventory.source),
                            complete=inventory.complete,
                            pages=inventory.pages,
                            returned_model_count=len(inventory.models),
                            retained_model_ids=sorted(m.id for m in relevant),
                            retained_scope="full inventory"
                            if provider.id != "openrouter"
                            else "currently zero-priced subset of account-filtered inventory",
                            account_visibility="listed via credential; generation not implied",
                        )
                        self.account(provider.id, slot.id)
                    except ProviderError as error:
                        row.update(
                            status="UNKNOWN",
                            category=error.category.value,
                            http_status=error.http_status,
                        )
                self.inventories.append(row)
                print(
                    json.dumps({k: v for k, v in row.items() if k != "retained_model_ids"}),
                    flush=True,
                )

    def run(self, name: str, request: ModelRequest, policy: RoutingPolicy) -> dict[str, Any]:
        starts = {kind: len(observer.statuses) for kind, observer in self.statuses.items()}
        row: dict[str, Any] = {
            "scenario": name,
            "observed_at": time(),
            "mode": request.mode.value,
            "max_output_tokens": request.max_output_tokens,
            "allow_unknown_cost": policy.allow_unknown_cost,
            "allow_unknown_limits": policy.allow_unknown_limits,
            "scope": "generation contract only; no model-quality/funding proof",
        }
        try:
            result = self.h.router.execute(request, policy)
            if "structured" in request.required:
                parsed = json.loads(result.response.text)
                matched = (
                    isinstance(parsed, dict) and set(parsed) == {"ok"} and parsed["ok"] is True
                )
            else:
                matched = result.response.text.strip() == "OSCAR_PROVIDER_OK"
            self.check(
                name + " remains REPORTED before independent comparison",
                result.status == "REPORTED",
            )
            event = self.h.store.get("route_history", result.history_id)
            self.check(name + " objective starts unknown", event["verified_objective"] is None)
            evidence = Evidence(
                new_id(),
                request.task_id,
                request.correlation_id,
                "independent sentinel comparison",
                "exact bounded generation response comparison",
                time(),
                matched,
                Epistemic.VERIFIED if matched else Epistemic.KNOWN,
                "Generation contract comparison only; general objective quality remains unknown.",
            )
            self.h.store.put("evidence", evidence.id, record(evidence))
            self.h.router.observe_verification(evidence)
            row.update(
                status="VERIFIED" if matched else "PARTIAL",
                sentinel_matches=matched,
                provider=result.route.provider,
                model=result.route.model,
                slot=result.route.slot,
                quota_pool=result.route.quota_pool,
                reasons=list(result.route.reasons),
                actual_model=result.response.actual_model,
                actual_provider=result.response.actual_provider,
                rate_limits=asdict(result.response.rate_limits)
                if result.response.rate_limits
                else None,
                input_tokens=result.response.input_tokens,
                output_tokens=result.response.output_tokens,
            )
            self.account(result.route.provider, result.route.slot)
        except ProviderError as error:
            row.update(
                status="UNAVAILABLE",
                category=error.category.value,
                http_status=error.http_status,
                business_code=error.business_code,
                rate_limits=asdict(error.rate_limits) if error.rate_limits else None,
            )
        except RouteUnavailable:
            row.update(status="BLOCKED", category="route_unavailable")
        events = [e for e in self.h.store.all("route_history") if e["task_id"] == request.task_id]
        if events and not row.get("provider"):
            row.update(
                {field: events[-1][field] for field in ("provider", "model", "slot", "quota_pool")}
            )
        row["attempts"] = len(events)
        row["attempt_trace"] = [
            {
                field: event[field]
                for field in (
                    "provider",
                    "model",
                    "slot",
                    "quota_pool",
                    "attempt",
                    "provider_response_success",
                    "error",
                    "timestamp",
                )
            }
            for event in events
        ]
        row["http_statuses"] = {
            kind: observer.statuses[starts[kind] :]
            for kind, observer in self.statuses.items()
            if len(observer.statuses) > starts[kind]
        }
        self.check(name + " attempts bounded", len(events) <= policy.max_attempts)
        self.check(
            name + " pool/slot reservations released",
            all(s.concurrent == 0 for s in self.h.pool.slots.values())
            and all(p.concurrent == 0 for p in self.h.pool.quota_pools.values()),
        )
        self.operations.append(row)
        print(json.dumps({k: v for k, v in row.items() if k not in {"reasons"}}), flush=True)
        return row

    @staticmethod
    def request(**changes: Any) -> ModelRequest:
        return replace(
            ModelRequest(new_id(), new_id(), "Reply exactly OSCAR_PROVIDER_OK"), **changes
        )

    def probes(self) -> None:
        for provider in self.h.registry.providers.values():
            if not provider.enabled:
                continue
            seeds = sorted(
                [
                    m
                    for key, m in self.h.registry.models.items()
                    if key in self.seed_keys
                    and m.provider_id == provider.id
                    and m.quality is not None
                ],
                key=lambda m: (m.quality or 99, m.id),
            )
            for slot in self.h.pool.slots.values():
                if slot.provider != provider.id or not slot.present:
                    continue
                model = next(
                    (
                        m
                        for m in seeds
                        if self.h.registry.availability(provider.id, m.id, slot.id, time())
                        == "listed via credential; generation entitlement not implied"
                    ),
                    None,
                )
                if model is None:
                    self.operations.append(
                        {
                            "scenario": "slot " + slot.id,
                            "status": "BLOCKED",
                            "reason": "no current seed candidate in account inventory",
                        }
                    )
                    continue
                if any(
                    o.get("provider") == provider.id
                    and o.get("slot") == slot.id
                    and o.get("model") == model.id
                    for o in self.previous
                ):
                    continue
                unknown = model.funding == Funding.UNKNOWN
                if unknown and not self.unknown_cost:
                    self.operations.append(
                        {
                            "scenario": "slot " + slot.id,
                            "status": "BLOCKED",
                            "reason": "explicit unknown-cost diagnostic flag required",
                        }
                    )
                    continue
                self.run(
                    "slot " + slot.id,
                    self.request(
                        mode=Mode.MANUAL,
                        pinned_provider=provider.id,
                        pinned_model=model.id,
                        pinned_slot=slot.id,
                        max_output_tokens=512,
                    ),
                    RoutingPolicy(
                        max_attempts=1,
                        timeout_seconds=30,
                        allow_paid=unknown,
                        allow_unknown_cost=unknown,
                        allow_unknown_limits=self.unknown_cost,
                    ),
                )
            # One small probe per additional curated task-fit candidate, not the whole catalog.
            if (
                provider.id not in {"groq", "google", "nvidia", "ollama-cloud"}
                or not self.unknown_cost
            ):
                continue
            selected_slot = next(
                (s for s in self.h.pool.slots.values() if s.provider == provider.id and s.present),
                None,
            )
            if selected_slot is None:
                continue
            extras = seeds[1:] if provider.id in {"groq", "google", "nvidia"} else seeds[-1:]
            for model in extras:
                if any(
                    o.get("provider") == provider.id
                    and o.get("slot") == selected_slot.id
                    and o.get("model") == model.id
                    for o in self.previous
                ):
                    continue
                self.run(
                    "candidate " + provider.id + "/" + model.id,
                    self.request(
                        mode=Mode.MANUAL,
                        pinned_provider=provider.id,
                        pinned_model=model.id,
                        pinned_slot=selected_slot.id,
                        max_output_tokens=512,
                    ),
                    RoutingPolicy(
                        max_attempts=1,
                        timeout_seconds=30,
                        allow_paid=True,
                        allow_unknown_cost=True,
                        allow_unknown_limits=True,
                    ),
                )

    def routing(self) -> None:
        for mode in (Mode.AUTO, Mode.FAST, Mode.BALANCED, Mode.HEAVY, Mode.FREE_FIRST):
            row = self.run(
                "routing " + mode.value,
                self.request(
                    prompt='Return only a JSON object with the single field "ok" set to true.',
                    required=frozenset({"text", "structured"}),
                    mode=mode,
                    min_quality=4 if mode == Mode.HEAVY else 1,
                    max_output_tokens=512,
                ),
                RoutingPolicy(max_attempts=3, timeout_seconds=30),
            )
            self.check("current live " + mode.value, row.get("sentinel_matches") is True)
        row = self.run("local refuses cloud", self.request(mode=Mode.LOCAL), RoutingPolicy())
        self.check("local has no hosted traffic", row["attempts"] == 0 and not row["http_statuses"])
        self.check(
            "unknown funding excluded by default",
            all(
                self.h.registry.models[(route.provider, route.model)].funding != Funding.UNKNOWN
                for route in self.h.router.rank(self.request())
            ),
        )
        self.check(
            "all Groq slots conservatively share one quota pool",
            len({s.quota_pool for s in self.h.pool.slots.values() if s.provider == "groq"}) == 1,
        )
        self.check(
            "Z.ai quota failure does not imply invalid credential",
            all(s.validity != "invalid" for s in self.h.pool.slots.values() if s.provider == "zai"),
        )
        for key, model in self.h.registry.models.items():
            if key not in self.seed_keys:
                continue
            pinned = self.request(mode=Mode.MANUAL, pinned_provider=key[0], pinned_model=key[1])
            for route in self.h.router.rank(
                pinned,
                RoutingPolicy(allow_paid=True, allow_unknown_cost=True, allow_unknown_limits=True),
            ):
                self.check(
                    "eligible route current " + route.slot + "/" + model.id,
                    self.h.registry.availability(route.provider, route.model, route.slot, time())
                    == "listed via credential; generation entitlement not implied"
                    and not model.retired,
                )
        missing = {"llama-3.1-8b-instant", "llama-3.3-70b-versatile", "qwen/qwen3.6-27b"}
        groq_lists = [i for i in self.inventories if i["provider"] == "groq"]
        self.check(
            "retired Free/Developer Groq IDs absent in current inventories",
            all(not missing.intersection(i.get("retained_model_ids", [])) for i in groq_lists),
        )

    def report(self) -> dict[str, Any]:
        history = json.dumps(self.h.store.all("route_history"))
        self.check(
            "route telemetry excludes credential material", self.h.pool.redact(history) == history
        )
        self.check(
            "route telemetry excludes prompt and answer",
            "Reply exactly OSCAR_PROVIDER_OK" not in history
            and "OSCAR_PROVIDER_OK" not in history
            and "Return only a JSON object with the single field" not in history,
        )
        return {
            "recorded_at": datetime.now(UTC).isoformat(),
            "scope": "Post-Gate-A Club A correction; Slice 05 not started",
            "checks": self.checks,
            "inventories": self.inventories,
            "accounts": self.accounts,
            "operations": self.operations,
            "previous_evidence": self.previous_source,
            "previous_verified_generations": self.previous,
            "quota_pools": [asdict(p) for p in self.h.pool.quota_pools.values()],
            "conflicts": self.h.registry.conflicts,
            "tavily": "UNVERIFIED; keys absent"
            if not any(os.environ.get(f"TAVILY_API_KEY_{i}") for i in range(1, 4))
            else "UNVERIFIED; live adapter acceptance not executed by this model-provider suite",
            "zai_coding": "UNVERIFIED / disabled; supported-tool entitlement not established",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--allow-unknown-cost-diagnostics", action="store_true")
    parser.add_argument("--manifest", type=Path, default=Path("config/development-models.json"))
    parser.add_argument("--report", type=Path, default=Path(".oscar/post-gate-a-live.json"))
    parser.add_argument(
        "--previous-evidence",
        type=Path,
        help="Retain successful probes from this correction pass; recheck inventories",
    )
    parser.add_argument(
        "--routing-only",
        action="store_true",
        help="Refresh inventory and retest modes; retain earlier probes without repeating them",
    )
    args = parser.parse_args()
    if not args.run_live:
        parser.error("hosted traffic requires --run-live")
    if args.routing_only and not args.previous_evidence:
        parser.error("--routing-only requires explicit --previous-evidence")
    Path(".oscar").mkdir(exist_ok=True)
    directory = Path(mkdtemp(prefix="freshness-review-", dir=".oscar"))
    suite = Verification(args.manifest, directory, args.allow_unknown_cost_diagnostics)
    if args.previous_evidence:
        previous = json.loads(args.previous_evidence.read_text())
        suite.previous = [
            o
            for o in previous["operations"] + previous.get("previous_verified_generations", [])
            if o.get("sentinel_matches") is True
        ]
        suite.previous_source = str(args.previous_evidence)
    try:
        suite.discover()
        if not args.routing_only:
            suite.probes()
        suite.routing()
        # The reference node does not heartbeat while provider-only probes run.
        suite.h.grid.heartbeat(suite.h.session)
        suite.check("Core exact-file independent proof", proof(suite.h)["status"] == "VERIFIED")
        grid = grid_proof(suite.h)
        suite.check(
            "Grid lease-expiry proof",
            grid["lease_active"] is False
            and grid["state_after_expiry"] == "blocked"
            and bool(grid["objective_preserved"]),
        )
        data = suite.report()
        encoded = json.dumps(data, indent=2, allow_nan=False) + "\n"
        if suite.h.pool.redact(encoded) != encoded:
            raise ValueError("secret-safety failed; report suppressed")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded)
        args.report.chmod(0o600)
        failed = sum(c["status"] == "FAIL" for c in suite.checks)
        print(
            json.dumps(
                {
                    "checks": len(suite.checks),
                    "failed": failed,
                    "verified_generations": sum(
                        o.get("sentinel_matches") is True for o in suite.operations
                    ),
                }
            )
        )
        return int(failed > 0)
    finally:
        suite.h.close()


if __name__ == "__main__":
    raise SystemExit(main())
