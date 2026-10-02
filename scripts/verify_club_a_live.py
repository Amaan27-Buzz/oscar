"""Opt-in hosted verification of the existing Club A runtime; no secrets or content in reports."""

import argparse
import json
import os
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from time import time
from typing import Any, cast
from urllib.error import HTTPError

from oscar.cli import grid_proof, proof
from oscar.contracts import Epistemic, Evidence, TaskState, new_id, record
from oscar.credentials import CredentialPool
from oscar.harness import Harness, ModelExecutor
from oscar.jev import Intent
from oscar.models import Mode, ModelRequest, ProviderError, RoutingPolicy
from oscar.registry import Registry
from oscar.router import Router, RouteUnavailable
from oscar.storage import Store


class HTTPStatuses:
    """Observe HTTP status only; retain neither authentication nor request/response bodies."""

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
        self.routers = [self.h.router]
        self.prompts: set[str] = set()
        self.responses: set[str] = set()
        self.checks: list[dict[str, Any]] = []
        self.operations: list[dict[str, Any]] = []
        self.inventories: list[dict[str, Any]] = []
        self.statuses: dict[str, HTTPStatuses] = {}
        for kind, adapter in self.h.adapters.items():
            observer = HTTPStatuses(adapter.opener)
            adapter.opener = observer  # type: ignore[assignment]
            self.statuses[kind] = observer

    def check(self, name: str, passed: bool, **detail: Any) -> None:
        self.checks.append({"check": name, "status": "PASS" if passed else "FAIL", **detail})

    def isolated(
        self,
        name: str,
        providers: list[Any],
        models: list[Any],
        environ: dict[str, str] | None = None,
    ) -> Router:
        store = Store(self.directory / (name + ".sqlite"))
        registry = Registry(providers, models)
        pool = CredentialPool(providers, environ=environ, store=store)
        router = Router(registry, pool, self.h.adapters, store)
        self.routers.append(router)
        return router

    def request(self, **changes: Any) -> ModelRequest:
        request = ModelRequest(
            new_id(), new_id(), "Reply exactly OSCAR_PROVIDER_OK", max_output_tokens=128
        )
        return replace(request, **changes)

    def run(
        self,
        name: str,
        request: ModelRequest,
        router: Router | None = None,
        policy: RoutingPolicy | None = None,
        source: str = "live provider",
    ) -> dict[str, Any]:
        router = router or self.h.router
        policy = policy or RoutingPolicy(max_attempts=4, timeout_seconds=30)
        self.prompts.add(request.prompt)
        candidates = router.rank(request, policy)
        observer_start = {kind: len(o.statuses) for kind, o in self.statuses.items()}
        row: dict[str, Any] = {
            "scenario": name,
            "source": source,
            "mode": request.mode.value,
            "quality_floor": request.min_quality,
            "max_attempts": policy.max_attempts,
            "max_output_tokens": request.max_output_tokens,
            "unknown_cost_allowed": policy.allow_unknown_cost,
            "initial_route": (
                {
                    "provider": candidates[0].provider,
                    "model": candidates[0].model,
                    "slot": candidates[0].slot,
                    "quota_remaining": candidates[0].quota_remaining,
                    "reasons": list(candidates[0].reasons),
                }
                if candidates
                else None
            ),
        }
        try:
            result = router.execute(request, policy)
            event = router.store.get("route_history", result.history_id)
            self.check(name + " response stays REPORTED", result.status == "REPORTED")
            self.check(name + " objective initially unknown", event["verified_objective"] is None)
            self.responses.add(result.response.text)
            matches = result.response.text.strip() == "OSCAR_PROVIDER_OK"
            evidence = Evidence(
                new_id(),
                request.task_id,
                request.correlation_id,
                "independent-comparison",
                "exact response comparison; generation contract only",
                time(),
                matches,
                Epistemic.VERIFIED if matches else Epistemic.KNOWN,
                "expected token matched" if matches else "expected token differed",
            )
            router.store.put("evidence", evidence.id, record(evidence))
            router.observe_verification(evidence)
            self.check(
                name + " verification linked",
                router.store.get("route_history", result.history_id)["verified_objective"]
                == matches,
            )
            slot = router.pool.slots[result.route.slot]
            row.update(
                status="VERIFIED" if matches else "PARTIALLY_VERIFIED",
                scope="generation contract only; model quality is not benchmarked",
                provider_response_success=True,
                response_status=result.status,
                sentinel_matches=matches,
                provider=result.route.provider,
                model=result.route.model,
                slot=result.route.slot,
                attempts=result.attempts,
                remaining_requests=slot.remaining_requests,
                remaining_tokens=slot.remaining_tokens,
                input_tokens=result.response.input_tokens,
                output_tokens=result.response.output_tokens,
            )
            if (
                result.response.remaining_requests is None
                and result.response.remaining_tokens is None
            ):
                self.check(
                    name + " absent quota stays unknown",
                    slot.remaining_requests is None and slot.remaining_tokens is None,
                )
        except ProviderError as error:
            row.update(
                status="UNAVAILABLE", reason=error.category.value, provider_response_success=False
            )
        except RouteUnavailable:
            row.update(
                status="UNAVAILABLE", reason="route_unavailable", provider_response_success=False
            )
        events = [e for e in router.store.all("route_history") if e["task_id"] == request.task_id]
        row["history"] = [
            {
                k: e[k]
                for k in (
                    "provider",
                    "model",
                    "slot",
                    "attempt",
                    "fallback",
                    "error",
                    "provider_response_success",
                    "quota_remaining",
                    "verified_objective",
                    "latency_ms",
                )
            }
            for e in events
        ]
        row["http_statuses"] = {
            kind: o.statuses[observer_start[kind] :]
            for kind, o in self.statuses.items()
            if len(o.statuses) > observer_start[kind]
        }
        self.check(name + " attempts bounded", len(events) <= policy.max_attempts)
        self.check(
            name + " reservations released",
            all(s.concurrent == 0 for s in router.pool.slots.values()),
        )
        self.operations.append(row)
        print(json.dumps(row, allow_nan=False), flush=True)
        return row

    def hosted_slots(self) -> None:
        for provider in self.h.registry.providers.values():
            models = sorted(
                (m for m in self.h.registry.models.values() if m.provider_id == provider.id),
                key=lambda m: (m.quality or 99, m.id),
            )
            for slot in [s for s in self.h.pool.slots.values() if s.provider == provider.id]:
                row: dict[str, Any] = {
                    "provider": provider.id,
                    "slot": slot.id,
                    "scope": "returned inventory page; not credential validation",
                }
                if not slot.present:
                    row.update(status="UNAVAILABLE", reason="credential absent")
                else:
                    try:
                        ids = self.h.adapters[provider.adapter].discover(
                            provider, self.h.pool.secret_for_adapter(slot.id), timeout=12
                        )
                        row.update(
                            status="REACHABLE",
                            returned_model_count=len(ids),
                            configured_models={m.id: m.id in ids for m in models},
                        )
                    except ProviderError as error:
                        row.update(status="UNAVAILABLE", reason=error.category.value)
                self.inventories.append(row)
                if not slot.present or not models:
                    continue
                if provider.id in {"nvidia", "zai"} and not self.unknown_cost:
                    self.operations.append(
                        {
                            "scenario": "slot " + slot.id,
                            "status": "BLOCKED",
                            "reason": "unknown cost requires explicit diagnostic flag",
                        }
                    )
                    continue
                policy = RoutingPolicy(
                    max_attempts=1,
                    timeout_seconds=30,
                    allow_paid=provider.id in {"nvidia", "zai"},
                    allow_unknown_cost=provider.id in {"nvidia", "zai"},
                )
                self.run(
                    "slot " + slot.id,
                    self.request(
                        mode=Mode.MANUAL,
                        pinned_provider=provider.id,
                        pinned_model=models[0].id,
                        pinned_slot=slot.id,
                        max_output_tokens=512 if provider.id == "nvidia" else 128,
                    ),
                    policy=policy,
                )

    def fallback(self) -> None:
        registry = self.h.registry
        opened = registry.providers["openrouter"]
        model = min(
            (m for m in registry.models.values() if m.provider_id == opened.id),
            key=lambda m: m.quality or 99,
        )
        slot = next(
            s
            for s in self.h.pool.slots.values()
            if s.provider == opened.id and s.validity == "valid"
        )
        single = replace(opened, credential_envs={slot.id: opened.credential_envs[slot.id]})
        invalid = "openrouter-0-invalid-fixture"
        provider = replace(
            single,
            credential_envs={
                invalid: "OSCAR_INVALID_TOKEN_FIXTURE",
                **single.credential_envs,
            },
        )
        environ = {variable: os.environ[variable] for variable in single.credential_envs.values()}
        environ["OSCAR_INVALID_TOKEN_FIXTURE"] = "oscar-deliberately-invalid-credential"
        router = self.isolated("credential-failover", [provider], [model], environ)
        row = self.run(
            "credential failover",
            self.request(
                mode=Mode.MANUAL,
                pinned_provider=opened.id,
                pinned_model=model.id,
            ),
            router,
            RoutingPolicy(max_attempts=2, timeout_seconds=30),
            "deliberately invalid test credential rejected by live endpoint; real alternate slot",
        )
        events = row["history"]
        self.check(
            "live credential failover",
            len(events) == 2
            and events[0]["slot"] == invalid
            and events[0]["error"] == "credential_failure"
            and events[1]["slot"] == slot.id
            and row.get("sentinel_matches") is True,
        )

        groq = registry.providers["groq"]
        groq = replace(groq, credential_envs={"groq-1": groq.credential_envs["groq-1"]})
        small = min(
            (m for m in registry.models.values() if m.provider_id == "groq"),
            key=lambda m: m.quality or 99,
        )
        providers, models = [groq, single], [small, model]
        router = self.isolated("cross-provider", providers, models)
        row = self.run(
            "cross-provider fallback",
            self.request(),
            router,
            RoutingPolicy(max_attempts=2, timeout_seconds=30),
        )
        events = row["history"]
        self.check(
            "live cross-provider fallback",
            len(events) == 2
            and events[0]["provider"] != events[1]["provider"]
            and not events[0]["provider_response_success"]
            and events[1]["fallback"]
            and row.get("sentinel_matches") is True,
        )
        router = self.isolated("fallback-bound", providers, models)
        row = self.run(
            "one-attempt bound",
            self.request(),
            router,
            RoutingPolicy(max_attempts=1, timeout_seconds=30),
        )
        self.check(
            "live fallback stops at bound",
            len(row["history"]) == 1 and not row["provider_response_success"],
        )

    def modes_and_scarcity(self) -> None:
        if self.unknown_cost:
            self.observed_rate_rerank()
        for mode in (Mode.AUTO, Mode.FREE_FIRST, Mode.FAST, Mode.BALANCED, Mode.HEAVY):
            request = self.request(
                mode=mode,
                min_quality=4 if mode == Mode.HEAVY else 1,
                max_output_tokens=512 if mode == Mode.HEAVY else 128,
            )
            row = self.run("routing " + mode.value, request)
            self.check("live " + mode.value + " routing", row.get("sentinel_matches") is True)
        before = len(self.h.store.all("route_history"))
        row = self.run("local refuses cloud", self.request(mode=Mode.LOCAL))
        self.check(
            "Local never calls cloud",
            row.get("reason") == "route_unavailable"
            and len(self.h.store.all("route_history")) == before
            and not row["http_statuses"],
        )

        registry = self.h.registry
        providers, models = [], []
        for pid, mid in (("google", "gemini-3.1-flash-lite"), ("ollama-cloud", "gemma4:31b")):
            provider = registry.providers[pid]
            slot = next(
                s for s in self.h.pool.slots.values() if s.provider == pid and s.validity == "valid"
            )
            providers.append(
                replace(
                    provider,
                    credential_envs={
                        "fixture-" + pid: provider.credential_envs[slot.id],
                    },
                )
            )
            models.append(registry.models[(pid, mid)])
        router = self.isolated("scarcity-fixture", providers, models)
        request = self.request(mode=Mode.FREE_FIRST, min_quality=2)
        google, ollama = (
            router.pool.slots["fixture-google"],
            router.pool.slots["fixture-ollama-cloud"],
        )
        for s in (google, ollama):
            s.quota_observed_at = time()
        google.remaining_requests, ollama.remaining_requests = 2, 500
        plentiful = router.rank(request)[0]
        google.remaining_requests, ollama.remaining_requests = 500, 2
        reversed_route = router.rank(request)[0]
        self.check(
            "scarcity changes choice with other metadata unchanged",
            plentiful.provider == "ollama-cloud" and reversed_route.provider == "google",
            source="synthetic 2/500 request balances; NOT observed account quota",
        )
        google.remaining_requests, ollama.remaining_requests = 2, 500
        row = self.run(
            "scarcity preserves constrained alternative",
            request,
            router,
            source="synthetic quota fixture; selected provider request is real HTTPS",
        )
        self.check(
            "scarcity choice reaches real provider",
            row.get("sentinel_matches") is True and row.get("provider") == "ollama-cloud",
        )

    def observed_rate_rerank(self) -> None:
        # Reuse actual rate-limit observations, without generating traffic to exhaust an account.
        registry = self.h.registry
        observed = self.h.pool.slots["zai-1"]
        if "rate_limit" not in (observed.recent_errors or []) or observed.cooldown_until <= time():
            return
        providers, models = [], []
        for pid, sid in (("zai", "zai-1"), ("openrouter", "openrouter-1")):
            provider = registry.providers[pid]
            providers.append(
                replace(provider, credential_envs={sid: provider.credential_envs[sid]})
            )
            models.append(
                min(
                    (m for m in registry.models.values() if m.provider_id == pid),
                    key=lambda m: m.quality or 99,
                )
            )
        router = self.isolated("observed-rate-limit", providers, models)
        policy = RoutingPolicy(
            allow_paid=True, allow_unknown_cost=True, max_attempts=1, timeout_seconds=30
        )
        request = self.request(mode=Mode.HEAVY)
        before = router.rank(request, policy)[0].provider
        router.pool.slots[observed.id] = replace(observed)
        after = router.rank(request, policy)[0].provider
        self.check(
            "actual rate limit changes next eligible route",
            before == "zai" and after == "openrouter",
            source="copied actual HTTP 429 slot observation; no invented balance",
        )
        row = self.run(
            "rerank after actual rate limit",
            request,
            router,
            policy,
            "actual HTTP 429 observation; subsequent alternative HTTPS call is real",
        )
        self.check(
            "observed rate rerank reaches alternate provider",
            row.get("sentinel_matches") is True and row.get("provider") == "openrouter",
        )

    def core_and_truth(self) -> None:
        self.h.grid.heartbeat(self.h.session)
        data = proof(self.h)
        self.check(
            "core exact file, fake rejection and deterministic Jev", data["status"] == "VERIFIED"
        )
        real_file = cast(dict[str, Any], data["real_file"])
        artifacts = real_file["artifacts"]
        self.check(
            "authoritative exact file bytes",
            len(artifacts) == 1
            and Path(artifacts[0]["location"]).read_bytes() == b"OSCAR verified bytes\n",
        )
        good = next(
            row
            for row in self.operations
            if row.get("sentinel_matches") and row.get("provider") == "google"
        )
        template = self.request(
            mode=Mode.MANUAL,
            pinned_provider=good["provider"],
            pinned_model=good["model"],
            pinned_slot=good["slot"],
            max_output_tokens=256,
        )
        self.h.dispatcher.executors["models.reason"] = ModelExecutor(
            self.h.router, template, RoutingPolicy(max_attempts=2, timeout_seconds=30)
        )
        intent = Intent("Reason about one small storage tradeoff in two sentences.", kind="reason")
        self.prompts.add(intent.text)
        task = self.h.runtime.create(intent)
        task = self.h.runtime.run(task.id, {self.h.node_id: (self.h.dispatcher, self.h.session)})
        results = [r for r in self.h.store.all("result") if r["task_id"] == task.id]
        self.check(
            "real model objective without verifier remains partial",
            task.state == TaskState.PARTIALLY_VERIFIED
            and len(results) == 1
            and results[0]["status"] == "REPORTED",
            task_state=task.state,
            result_status=results[0]["status"] if results else None,
            provider=good["provider"],
            model=good["model"],
            slot=good["slot"],
        )
        grid = grid_proof(self.h)
        self.check(
            "Grid loss preserves objective and expires lease",
            grid["objective_preserved"] is True
            and grid["state_after_expiry"] == TaskState.BLOCKED
            and not grid["lease_active"],
        )

    def finish(self) -> dict[str, Any]:
        successful = {r["provider"] for r in self.operations if r.get("sentinel_matches")}
        self.check("multiple real providers", len(successful) >= 2, providers=sorted(successful))
        slots = {
            r["slot"]
            for r in self.operations
            if r.get("sentinel_matches") and r["scenario"].startswith("slot ")
        }
        self.check("multiple real slots", len(slots) >= 2, masked_slots=sorted(slots))
        for router in self.routers:
            history = json.dumps(router.store.all("route_history"))
            self.check(
                "route history excludes credentials and content",
                router.pool.redact(history) == history
                and not any(s and s in history for s in self.prompts | self.responses),
            )
        for router in self.routers[1:]:
            router.store.close()
        self.h.close()
        material = [
            value.encode()
            for provider in self.h.registry.providers.values()
            for name in provider.credential_envs.values()
            if (value := os.environ.get(name))
        ]
        leaked = any(
            value in p.read_bytes()
            for p in self.directory.rglob("*")
            if p.is_file()
            for value in material
        )
        self.check("runtime artifacts exclude provider secrets", not leaked)
        return {
            "version": 1,
            "recorded_at": datetime.now(UTC).isoformat(),
            "continued_from": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "scope": "Club A verification only; reference Grid; no Slice 05",
            "unknown_cost_diagnostics": self.unknown_cost,
            "inventories": self.inventories,
            "operations": self.operations,
            "checks": self.checks,
            "status": "PASS" if all(c["status"] == "PASS" for c in self.checks) else "FAIL",
            "limitations": [
                "Inventory reachability alone does not validate credentials "
                "or generation availability.",
                "No quality benchmarks, quota estimates or funding guarantees are inferred.",
                "Scarcity counterfactual uses synthetic metadata; HTTPS execution is real.",
                "Public rendezvous, independent network stores "
                "and physical nodes remain unverified.",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true", required=True)
    parser.add_argument(
        "--allow-unknown-cost-diagnostics",
        action="store_true",
        help="Allow bounded NVIDIA/Z.ai probes without asserting they are free.",
    )
    parser.add_argument("--manifest", type=Path, default=Path("config/development-models.json"))
    parser.add_argument("--report", type=Path, default=Path(".oscar/club-a-live.json"))
    args = parser.parse_args()
    Path(".oscar").mkdir(exist_ok=True, mode=0o700)
    directory = Path(mkdtemp(prefix="club-a-live-", dir=".oscar"))
    suite = Verification(args.manifest, directory, args.allow_unknown_cost_diagnostics)
    try:
        suite.hosted_slots()
        suite.fallback()
        suite.modes_and_scarcity()
        suite.core_and_truth()
    except (StopIteration, KeyError, ValueError, OSError):
        suite.check(
            "remaining scenarios available",
            False,
            reason="required live route or state unavailable; diagnostics suppressed",
        )
    report = suite.finish()
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if any(router.pool.redact(encoded) != encoded for router in suite.routers):
        print("FAIL: unsafe report suppressed")
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.report.write_text(encoded)
    args.report.chmod(0o600)
    print(
        json.dumps(
            {
                "status": report["status"],
                "report": str(args.report),
                "checks": len(report["checks"]),
                "failed_checks": [c["check"] for c in report["checks"] if c["status"] == "FAIL"],
            }
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
