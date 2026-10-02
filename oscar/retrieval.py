"""Provider-agnostic search/live retrieval contract and a real native inventory source.

No model prior is used as a fallback. Tavily can implement RetrievalProvider without
changing Jev, execution or evidence contracts. Source text is task data, never route telemetry.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Protocol
from urllib.parse import urlparse

from .capabilities import Cancellation
from .contracts import Action, Result, new_id
from .freshness import Freshness, SourceRef
from .models import ProviderError
from .router import Router


@dataclass(frozen=True)
class RetrievalRequest:
    query: str = field(repr=False)
    freshness: Freshness = Freshness.CURRENT
    domains: tuple[str, ...] = ()
    result_limit: int = 8
    time_range: str | None = None
    depth: str = "bounded"

    def __post_init__(self) -> None:
        if not 1 <= self.result_limit <= 20 or self.depth != "bounded":
            raise ValueError("invalid retrieval budget")


@dataclass(frozen=True)
class RetrievedFact:
    text: str = field(repr=False)
    source: SourceRef
    conflicts: tuple[str, ...] = ()
    retrieval_method: str = "direct"


@dataclass(frozen=True)
class RetrievalResult:
    facts: tuple[RetrievedFact, ...]
    status: str = "REPORTED"
    limitations: tuple[str, ...] = ()


class RetrievalProvider(Protocol):
    def supports(self, request: RetrievalRequest) -> bool: ...

    def retrieve(
        self, request: RetrievalRequest, check_cancel: Callable[[], None]
    ) -> RetrievalResult: ...


class ProviderInventorySource:
    def __init__(self, router: Router):
        self.router = router

    def supports(self, request: RetrievalRequest) -> bool:
        text = request.query.lower()
        return "model" in text and any(
            x in text
            for x in (
                "groq",
                "openrouter",
                "nvidia",
                "google",
                "gemini",
                "z.ai",
                "ollama",
                "configured",
                "provider",
            )
        )

    def retrieve(
        self, request: RetrievalRequest, check_cancel: Callable[[], None]
    ) -> RetrievalResult:
        facts: list[RetrievedFact] = []
        missing: list[str] = []
        query = request.query.lower()
        for provider in self.router.registry.providers.values():
            if not provider.enabled or not provider.discovery_required:
                continue
            if not any(
                x in query
                for x in (
                    provider.id,
                    "configured",
                    "providers",
                    "gemini" if provider.id == "google" else provider.id,
                    "z.ai" if provider.id == "zai" else provider.id,
                )
            ):
                continue
            host = urlparse(provider.base_url).hostname or ""
            if request.domains and not any(
                host == domain or host.endswith("." + domain) for domain in request.domains
            ):
                continue
            check_cancel()
            slots = [
                s
                for s in self.router.pool.slots.values()
                if s.provider == provider.id and s.present
            ]
            if not slots:
                missing.append(provider.id + ": no configured live credential")
                continue
            # A request for current truth actively retrieves even when the routing TTL
            # would otherwise permit a short-lived cache. Native reads cost no tokens.
            retrieved = False
            for slot in slots:
                check_cancel()
                if self.router.discovery is None:
                    break
                try:
                    inventory = self.router.discovery.inventory(
                        provider, slot.id, self.router.pool.secret_for_adapter(slot.id)
                    )
                    self.router.registry.apply_inventory(inventory)
                except ProviderError:
                    continue
                if not inventory.complete or not inventory.source.current(self.router.clock()):
                    continue
                ids = ", ".join(
                    m.id
                    for m in inventory.models
                    if m.active is not False
                    and not self.router.registry.models[(provider.id, m.id)].retired
                )
                facts.append(
                    RetrievedFact(
                        f"{provider.id}: {ids}. Listed via {slot.id}; "
                        "account generation/funding is not implied.",
                        inventory.source,
                        tuple(
                            c["model"] + ": " + c["resolution"]
                            for c in self.router.registry.conflicts
                            if c["provider"] == provider.id and c["slot"] == slot.id
                        ),
                    )
                )
                retired = [
                    self.router.registry.models[(provider.id, m.id)]
                    for m in inventory.models
                    if self.router.registry.models[(provider.id, m.id)].retired
                ]
                if retired and retired[0].retirement_source is not None:
                    facts.append(
                        RetrievedFact(
                            f"{provider.id}: officially retired IDs remain listed: "
                            + ", ".join(m.id for m in retired)
                            + "; excluded from routing. "
                            "Retirement is distinct from catalog visibility.",
                            retired[0].retirement_source,
                        )
                    )
                retrieved = True
                break
            if not retrieved:
                missing.append(provider.id + ": current inventory UNKNOWN / potentially stale")
        return RetrievalResult(
            tuple(facts[: request.result_limit]),
            limitations=tuple(missing)
            + (
                "This native source establishes inventory observations only; "
                "public access constraints require current official documentation/search.",
            ),
        )


class RetrievalExecutor:
    def __init__(self, router: Router, providers: tuple[RetrievalProvider, ...]):
        self.router, self.providers = router, providers

    def __call__(self, action: Action, cancellation: Cancellation) -> Result:
        request = RetrievalRequest(
            action.parameters["query"], Freshness(action.parameters["freshness"])
        )
        facts: list[RetrievedFact] = []
        limitations: list[str] = []
        for provider in self.providers:
            cancellation.check()
            if provider.supports(request):
                result = provider.retrieve(request, cancellation.check)
                facts.extend(f for f in result.facts if f.source.current(self.router.clock()))
                limitations.extend(result.limitations)
        if not facts:
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                action.capability_id,
                False,
                error="freshness_unavailable: UNKNOWN / potentially stale",
            )
        for fact in facts:
            self.router.store.put(
                "retrieval_evidence",
                new_id(),
                {
                    "task_id": action.task_id,
                    "correlation_id": action.correlation_id,
                    "source": asdict(fact.source),
                    "status": "REPORTED",
                    "conflicts": fact.conflicts,
                    "retrieval_method": fact.retrieval_method,
                },
            )
        # Deterministic evidence synthesis keeps claim scopes separate. Web text
        # cannot authorize an account route or overturn native visibility; conflicts
        # remain visible instead of being hidden behind a single confidence score.
        answer = (
            "Current evidence-qualified answer. Account listing, provider support, "
            "generation and funding are separate claims. Account APIs govern listing; "
            "applicable official retirement notices govern retirement. "
            "Web excerpts are REPORTED source material, not verified account entitlement.\n"
        )
        for scope, label in (
            ("account", "Account-visible inventory"),
            ("provider", "Provider-wide documentation/source evidence"),
            ("local", "Current local evidence"),
        ):
            scoped = [f for f in facts if f.source.scope == scope]
            if not scoped:
                continue
            answer += (
                label
                + ":\n"
                + "\n".join(
                    f"{f.text}\nSource: {f.source.identity}; authority: {f.source.authority}; "
                    f"observed_at: {f.source.observed_at}; scope: {f.source.scope}"
                    + ("\nConflicting evidence: " + "; ".join(f.conflicts) if f.conflicts else "")
                    for f in scoped
                )
                + "\n"
            )
        if limitations:
            answer += "\nLimitations: " + "; ".join(limitations)
        return Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            True,
            value=self.router.pool.redact(answer),
        )
