"""Opt-in focused Gate A routing acceptance; never runs the provider probe matrix."""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from time import time
from typing import Any

from oscar.models import Funding, Mode, ModelRequest, Route, RoutingPolicy

from .verify_club_a_live import Verification

FOCUSED_MODES = (Mode.BALANCED, Mode.HEAVY, Mode.FREE_FIRST)


def _current_free_routes(suite: Verification, routes: list[Route]) -> bool:
    registry = suite.h.registry
    now = suite.h.router.clock()
    return all(
        registry.availability(route.provider, route.model, route.slot, now)
        == "listed via credential; generation entitlement not implied"
        and not registry.model_for_slot(route.provider, route.model, route.slot, now).retired
        and registry.model_for_slot(route.provider, route.model, route.slot, now).funding
        in {Funding.FREE, Funding.SUBSCRIPTION, Funding.LOCAL}
        for route in routes
    )


def focused_routing(suite: Verification, modes: tuple[Mode, ...] = FOCUSED_MODES) -> dict[str, Any]:
    """Accept generation or an evidenced policy/capacity block; never manufacture a route."""
    if (
        not modes
        or len(set(modes)) != len(modes)
        or any(mode not in FOCUSED_MODES for mode in modes)
    ):
        raise ValueError("only the unresolved Gate A modes may be requested, once each")
    for mode in modes:
        request = suite.request(
            prompt="Reply exactly OSCAR_PROVIDER_OK"
            if mode == Mode.HEAVY
            else 'Return only a JSON object with the single field "ok" set to true.',
            required=frozenset({"text"})
            if mode == Mode.HEAVY
            else frozenset({"text", "structured"}),
            mode=mode,
            min_quality=4 if mode == Mode.HEAVY else 1,
            max_output_tokens=512,
        )
        policy = RoutingPolicy(max_attempts=3, timeout_seconds=30)
        suite.h.router.refresh(request, policy)
        before = suite.h.router.rank(request, policy)
        row = suite.run("final routing " + mode.value, request, policy)
        after = suite.h.router.rank(request, policy)
        expected_block = (
            row["status"] in {"BLOCKED", "UNAVAILABLE"}
            and not after
            and row.get("category") != "cancelled"
        )
        matches = row.get("sentinel_matches") is True
        row.update(
            acceptance="PASS" if matches or expected_block else "FAIL",
            disposition="VERIFIED_GENERATION"
            if matches
            else "EXPECTED_BLOCKED"
            if expected_block
            else "UNRESOLVED",
            eligible_before=len(before),
            eligible_after=len(after),
            eligible_providers_before=sorted({route.provider for route in before}),
            eligible_providers_after=sorted({route.provider for route in after}),
            block_semantics="No currently eligible route under unchanged default funding, "
            "capability and capacity policy; this does not diagnose invalid credentials."
            if expected_block
            else None,
        )
        if not matches:
            row["block_diagnostics"] = block_diagnostics(suite, request, policy)
        suite.check("final " + mode.value + " truthful acceptance", matches or expected_block)
        suite.check(
            "final " + mode.value + " eligible routes current and funding authorized",
            _current_free_routes(suite, before + after),
        )
        _check_shared_cooldowns(suite, request)
    return routing_report(suite)


def block_diagnostics(
    suite: Verification, request: ModelRequest, policy: RoutingPolicy
) -> dict[str, Any]:
    """Bounded cached evidence behind a block; never refresh or probe from this audit."""
    registry, pool, now = suite.h.registry, suite.h.pool, suite.h.router.clock()
    candidates = sorted(
        (
            model
            for model in registry.models.values()
            if model.quality is not None
            and model.quality >= request.min_quality
            and not model.retired
            and registry.providers[model.provider_id].enabled
        ),
        key=lambda model: (model.funding != Funding.FREE, model.provider_id, model.id),
    )
    observations: list[dict[str, Any]] = []
    for candidate in candidates[:20]:
        for slot in pool.slots.values():
            if slot.provider != candidate.provider_id or not slot.present:
                continue
            model = registry.model_for_slot(slot.provider, candidate.id, slot.id, now)
            inventory = registry.inventories.get((slot.provider, slot.id))
            availability = registry.availability(slot.provider, model.id, slot.id, now)
            missing_capabilities = sorted(request.required - model.capabilities)
            exclusions: list[str] = []
            if missing_capabilities:
                exclusions.append("required capability not currently established")
            free = model.funding in {Funding.FREE, Funding.SUBSCRIPTION, Funding.LOCAL}
            if not free and not policy.allow_paid:
                exclusions.append("paid/UNKNOWN funding excluded by policy")
            if model.funding == Funding.UNKNOWN and not policy.allow_unknown_cost:
                exclusions.append("account funding UNKNOWN")
            if model.context_limit is None and not policy.allow_unknown_limits:
                exclusions.append("context limit UNKNOWN")
            elif model.context_limit is not None and model.context_limit < (
                request.input_tokens + request.max_output_tokens
            ):
                exclusions.append("context budget insufficient")
            if model.output_limit is None and not policy.allow_unknown_limits:
                exclusions.append("output limit UNKNOWN")
            elif model.output_limit is not None and model.output_limit < request.max_output_tokens:
                exclusions.append("output budget insufficient")
            if availability not in {
                "listed via credential; generation entitlement not implied",
                "configured fallback",
            }:
                exclusions.append("current account availability not established")
            if not pool.eligible(
                slot.id, request.input_tokens + request.max_output_tokens, model.id
            ):
                exclusions.append("credential/shared-pool capacity currently unavailable")
            if suite.h.router._health_blocked(slot.provider, model.id):
                exclusions.append("provider/model health cooldown")
            observations.append(
                {
                    "provider": slot.provider,
                    "model": model.id,
                    "slot": slot.id,
                    "quota_pool": slot.quota_pool,
                    "quality": model.quality,
                    "capabilities": sorted(model.capabilities),
                    "missing_capabilities": missing_capabilities,
                    "funding": model.funding.value,
                    "context_limit": model.context_limit,
                    "output_limit": model.output_limit,
                    "availability": availability,
                    "inventory_source": asdict(inventory.source) if inventory else None,
                    "known_exclusions": exclusions,
                }
            )
    return {
        "observed_at": now,
        "scope": "Cached point-in-time diagnostics; no new network or generation calls",
        "required_capabilities": sorted(request.required),
        "minimum_quality": request.min_quality,
        "max_output_tokens": request.max_output_tokens,
        "candidate_model_count": len(candidates),
        "retained_model_limit": 20,
        "truncated": len(candidates) > 20,
        "candidate_observations": observations,
    }


def _check_shared_cooldowns(suite: Verification, request: ModelRequest) -> None:
    now = suite.h.router.clock()
    for (pool_id, model), capacity in suite.h.pool.capacities.items():
        if capacity.cooldown_until <= now:
            continue
        # '*' is an account-wide bucket. A distinct model cannot hide that cooldown.
        model_probe = model if model != "*" else "account-cooldown-audit"
        members = [slot for slot in suite.h.pool.slots.values() if slot.quota_pool == pool_id]
        suite.check(
            "active shared cooldown excludes all members " + pool_id + "/" + model,
            all(
                not suite.h.pool.eligible(
                    slot.id, request.input_tokens + request.max_output_tokens, model_probe
                )
                for slot in members
            ),
        )


def routing_report(suite: Verification) -> dict[str, Any]:
    now = suite.h.router.clock()
    history = json.dumps(suite.h.store.all("route_history"))
    suite.check(
        "final routing history excludes credentials", suite.h.pool.redact(history) == history
    )
    suite.check(
        "final routing history excludes prompt and response",
        "Return only a JSON object with the single field" not in history
        and '"ok": true' not in history,
    )
    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "scope": "Final Gate A focused routing; no provider generation matrix or Slice 05",
        "funding_policy": "Default; paid and UNKNOWN funding excluded",
        "checks": suite.checks,
        "operations": suite.operations,
        "inventory_sources": [
            {
                "provider": inventory.provider,
                "slot": inventory.slot,
                "source": asdict(inventory.source),
                "complete": inventory.complete,
                "model_count": len(inventory.models),
            }
            for inventory in suite.h.registry.inventories.values()
        ],
        "account_observations": suite.h.store.all("account_observation"),
        "quota_pools": [asdict(pool) for pool in suite.h.pool.quota_pools.values()],
        "current_cooldowns": [
            {"quota_pool": pool_id, "model_bucket": model, **asdict(capacity)}
            for (pool_id, model), capacity in suite.h.pool.capacities.items()
            if capacity.cooldown_until > now
        ],
        "current_route_health": _current_health(suite, now),
        "conflicts": suite.h.registry.conflicts,
    }


def _current_health(suite: Verification, now: float) -> list[dict[str, Any]]:
    scopes = set(suite.h.registry.providers)
    scopes.update(provider + "/" + model for provider, model in suite.h.registry.models)
    observations: list[dict[str, Any]] = []
    for scope in sorted(scopes):
        try:
            entry = suite.h.store.get("route_health", scope)
        except KeyError:
            continue
        if entry["until"] > now:
            observations.append({"scope": scope, **entry})
    return observations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--manifest", type=Path, default=Path("config/development-models.json"))
    parser.add_argument("--report", type=Path, default=Path(".oscar/final-gate-a-routing.json"))
    parser.add_argument(
        "--mode",
        action="append",
        choices=[mode.value for mode in FOCUSED_MODES],
        help="Run only this unresolved mode; may be repeated for distinct modes",
    )
    args = parser.parse_args()
    if not args.run_live:
        parser.error("hosted traffic requires --run-live")
    Path(".oscar").mkdir(exist_ok=True)
    directory = Path(mkdtemp(prefix="gate-a-routing-", dir=".oscar"))
    suite = Verification(args.manifest, directory, False)
    try:
        modes = tuple(Mode(mode) for mode in args.mode) if args.mode else FOCUSED_MODES
        report = focused_routing(suite, modes)
        encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if suite.h.pool.redact(encoded) != encoded:
            raise ValueError("secret-safety failed; report suppressed")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded)
        args.report.chmod(0o600)
        failed = sum(check["status"] == "FAIL" for check in suite.checks)
        print(json.dumps({"recorded_at": time(), "checks": len(suite.checks), "failed": failed}))
        return int(failed > 0)
    finally:
        suite.h.close()


if __name__ == "__main__":
    raise SystemExit(main())
