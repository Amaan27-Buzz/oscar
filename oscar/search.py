"""Bounded Tavily implementation of the replaceable live-retrieval boundary.

Only source excerpts/references are returned; provider answers and raw pages are
disabled. Search never writes model availability or account entitlement.
"""

import json
import math
from collections.abc import Callable, Mapping
from dataclasses import asdict
from datetime import datetime
from http.client import HTTPException
from time import monotonic, time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener

from .capabilities import Cancelled
from .contracts import new_id
from .credentials import CredentialPool
from .freshness import Authority, SourceRef
from .http_client import NoRedirects
from .models import Failure, ProviderError, ProviderSpec
from .providers import error_category, rate_limits
from .public_sources import read_official_page
from .retrieval import (
    ConstraintAssessment,
    RetrievalRequest,
    RetrievalResult,
    RetrievedFact,
    access_constraint_topics,
)
from .storage import Store

OFFICIAL_DOMAINS = {
    "groq": ("console.groq.com",),
    "openrouter": ("openrouter.ai",),
    "google": ("ai.google.dev",),
    "nvidia": ("build.nvidia.com", "docs.api.nvidia.com"),
    "zai": ("docs.z.ai",),
    "ollama-cloud": ("docs.ollama.com", "ollama.com"),
}


def domain_matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


class TavilySource:
    def __init__(
        self,
        store: Store,
        environ: Mapping[str, str] | None = None,
        clock: Callable[[], float] = time,
        redact: Callable[[str], str] = lambda value: value,
    ):
        self.store, self.clock, self.redact = store, clock, redact
        self.provider = ProviderSpec(
            "tavily",
            "tavily",
            "https://api.tavily.com",
            {f"tavily-{i}": f"TAVILY_API_KEY_{i}" for i in range(1, 4)},
            account_product="search",
            quota_pool="tavily/search-account-unknown",
        )
        self.pool = CredentialPool([self.provider], environ, store, clock)
        self.opener = build_opener(NoRedirects())
        self.page_reader = read_official_page

    def supports(self, request: RetrievalRequest) -> bool:
        return True

    def search(
        self,
        request: RetrievalRequest,
        slot: str,
        check_cancel: Callable[[], None],
        timeout: float = 15,
    ) -> RetrievalResult:
        """One bounded call; explicit slots allow real per-slot acceptance testing."""
        check_cancel()
        if not self.pool.reserve(slot, 0, "*"):
            raise ProviderError(Failure.CAPACITY)
        observation_id = new_id()
        observation: dict[str, Any] = {
            "id": observation_id,
            "domains": request.domains,
            "slot": slot,
            "quota_pool": self.pool.slots[slot].quota_pool,
            "endpoint": self.provider.base_url + "/search",
            "observed_at": self.clock(),
            "search_depth": "basic",
            "max_results": request.result_limit,
            "credits": None,
            "status": "UNKNOWN",
        }
        deadline = monotonic() + min(15, timeout)
        try:
            payload: dict[str, Any] = {
                "query": request.query,
                "search_depth": "basic",
                "auto_parameters": False,
                "max_results": request.result_limit,
                "include_answer": False,
                "include_raw_content": False,
                "include_usage": True,
                "include_published_date": True,
            }
            if request.domains:
                payload.update(
                    include_domains=list(request.domains), include_domains_mode="restrict"
                )
            if request.time_range:
                payload["time_range"] = request.time_range
            headers = {
                "Authorization": "Bearer " + self.pool.secret_for_adapter(slot),
                "Content-Type": "application/json",
                "User-Agent": "OSCAR/0.1",
            }
            with self.opener.open(
                Request(self.provider.base_url + "/search", json.dumps(payload).encode(), headers),
                timeout=min(15, timeout),
            ) as response:
                observation["http_status"] = response.status
                response_limits = rate_limits(response.headers, "tavily", self.clock())
                observation["rate_limits"] = asdict(response_limits)
                raw = response.read(500_001)
            check_cancel()
            if len(raw) > 500_000:
                raise ProviderError(Failure.CAPABILITY)
            data = json.loads(raw)
            if (
                not isinstance(data, dict)
                or "error" in data
                or not isinstance(data.get("results"), list)
            ):
                raise ProviderError(Failure.CAPABILITY)
            usage = data.get("usage", {})
            credits = usage.get("credits") if isinstance(usage, dict) else None
            if (
                isinstance(credits, int | float)
                and not isinstance(credits, bool)
                and math.isfinite(credits)
                and credits >= 0
            ):
                observation["credits"] = credits
            if any(
                getattr(response_limits, name) is not None
                for name in (
                    "request_limit",
                    "token_limit",
                    "remaining_requests",
                    "remaining_tokens",
                    "requests_reset_at",
                    "tokens_reset_at",
                    "retry_after",
                )
            ):
                self.pool.observe_limits(slot, "*", response_limits)
                if response_limits.retry_after:
                    capacity = self.pool.capacity(slot, "*")
                    if capacity:
                        capacity.cooldown_until = self.clock() + response_limits.retry_after
                        self.pool.persist_capacity(self.pool.slots[slot].quota_pool, "*")
            else:
                self.pool.invalidate_capacity(slot, "*")
            facts: list[RetrievedFact] = []
            omitted = 0
            page_failures = 0
            for item in data["results"][: request.result_limit]:
                if not isinstance(item, dict):
                    raise ProviderError(Failure.CAPABILITY)
                url, content = item.get("url"), item.get("content")
                if not isinstance(url, str) or not isinstance(content, str):
                    raise ProviderError(Failure.CAPABILITY)
                parsed = urlparse(url)
                host = parsed.hostname or ""
                if (
                    parsed.scheme != "https"
                    or not host
                    or parsed.username
                    or parsed.password
                    or parsed.query
                    or parsed.fragment
                    or (request.domains and not domain_matches(host, request.domains))
                    or self.pool.redact(url) != url
                    or self.redact(url) != url
                ):
                    omitted += 1
                    continue
                official = domain_matches(
                    host, tuple(d for ds in OFFICIAL_DOMAINS.values() for d in ds)
                )
                # Forum/community material on an official host is not official documentation.
                official = official and not any(
                    x in parsed.path.lower() for x in ("/forum", "/community")
                )
                text = self.redact(self.pool.redact(content))[:1500]
                method = "search_excerpt"
                if official and monotonic() < deadline:
                    check_cancel()
                    try:
                        text = self.page_reader(
                            url,
                            min(5, deadline - monotonic()),
                            redact=lambda value: self.redact(self.pool.redact(value)),
                        )
                        method = "official_page"
                    except ProviderError:
                        page_failures += 1
                    check_cancel()
                published = item.get("published_date")
                if isinstance(published, str):
                    try:
                        datetime.fromisoformat(published.replace("Z", "+00:00"))
                    except ValueError:
                        published = None
                if not isinstance(published, str):
                    published = None
                if isinstance(published, str) and (
                    self.pool.redact(published) != published or self.redact(published) != published
                ):
                    published = None
                title = item.get("title")
                title = (
                    self.redact(self.pool.redact(title))[:500] if isinstance(title, str) else None
                )
                evidence_id = new_id()
                observation.setdefault("source_metadata", []).append(
                    {
                        "evidence_id": evidence_id,
                        "identity": url,
                        "title_returned": isinstance(item.get("title"), str),
                        "title": title,
                        "published_at": published,
                        "retrieval_method": method,
                        "access_topics": access_constraint_topics(text)
                        if method == "official_page"
                        else (),
                    }
                )
                facts.append(
                    RetrievedFact(
                        (
                            "Official page excerpt (REPORTED, not account entitlement): "
                            if method == "official_page"
                            else "Indexed excerpt; current source UNKNOWN / potentially stale: "
                        )
                        + text,
                        SourceRef(
                            url,
                            Authority.OFFICIAL_DOCS
                            if method == "official_page"
                            else Authority.SECONDARY,
                            "provider",
                            self.clock(),
                            published_at=published[:100] if isinstance(published, str) else None,
                            title=title,
                            source_provider="tavily",
                            evidence_id=evidence_id,
                            provider_id=next(
                                (
                                    p
                                    for p, ds in OFFICIAL_DOMAINS.items()
                                    if domain_matches(host, ds)
                                ),
                                None,
                            ),
                        ),
                        retrieval_method=method,
                    )
                )
            observation.update(
                status="REPORTED",
                retained_sources=len(facts),
                omitted_sources=omitted,
                official_pages=sum(f.retrieval_method == "official_page" for f in facts),
                page_failures=page_failures,
            )
            health = self.pool.slots[slot]
            health.validity, health.health = "valid", "healthy"
            health.requests += 1
            limitations: tuple[str, ...] = (
                "Web excerpts describe provider-wide support/access, not account listing, "
                "generation or funding. Publication dates are search-provider estimates; "
                "current observation does not prove every excerpt was recently updated.",
            )
            if omitted:
                limitations += ("Unsafe/query-bearing or out-of-domain source references omitted.",)
            if any(f.retrieval_method == "search_excerpt" for f in facts):
                limitations += (
                    "Index excerpts are discovery hints; current official page content "
                    "was not established for these references and remains UNKNOWN.",
                )
            return RetrievalResult(tuple(facts), limitations=limitations)
        except HTTPError as error:
            error.close()
            limits = rate_limits(error.headers, "tavily", self.clock())
            category = (
                Failure.QUOTA
                if error.code in {432, 433}
                else Failure.RATE_LIMIT
                if error.code == 429
                else error_category(error.code, error.headers)
            )
            failure = ProviderError(
                category,
                http_status=error.code,
                retry_after=limits.retry_after or 30,
                rate_limits=limits,
            )
            self.pool.failed(slot, category, failure.retry_after, "*")
            # Do not shorten an explicit provider Retry-After to the generic pool's cap.
            if category in {Failure.QUOTA, Failure.RATE_LIMIT} and failure.retry_after > 3600:
                self.pool.slots[slot].cooldown_until = self.clock() + failure.retry_after
                capacity = self.pool.capacity(slot, "*")
                if capacity:
                    capacity.cooldown_until = self.pool.slots[slot].cooldown_until
                    self.pool.persist_capacity(self.pool.slots[slot].quota_pool, "*")
            observation.update(
                status="UNAVAILABLE",
                http_status=error.code,
                category=category.value,
                rate_limits=asdict(limits),
            )
            raise failure from None
        except (URLError, HTTPException, OSError):
            observation.update(status="UNAVAILABLE", category=Failure.NETWORK.value)
            raise ProviderError(Failure.NETWORK) from None
        except (ValueError, TypeError, AttributeError):
            observation.update(status="UNAVAILABLE", category=Failure.CAPABILITY.value)
            raise ProviderError(Failure.CAPABILITY) from None
        except ProviderError as failure:
            observation.update(status="UNAVAILABLE", category=failure.category.value)
            raise
        except Cancelled:
            observation.update(status="CANCELLED")
            raise
        finally:
            try:
                self.store.put("search_observation", observation_id, observation)
            finally:
                self.pool.release(slot)

    def retrieve(
        self, request: RetrievalRequest, check_cancel: Callable[[], None]
    ) -> RetrievalResult:
        # The configured-provider objective needs coverage, not a search ranking
        # dominated by one vendor. Bound total results and calls; each source keeps
        # the same replaceable retrieval contract and original observation time.
        constraint_objective = (
            "model" in request.query.lower()
            and "configured" in request.query.lower()
            and any(word in request.query.lower() for word in ("access", "free", "constraint"))
        )
        deadline = monotonic() + (90 if constraint_objective else 30)
        if constraint_objective:
            return self._retrieve_constraints(request, check_cancel, deadline)
        if "model" in request.query.lower() and "configured" in request.query.lower():
            facts: list[RetrievedFact] = []
            limitations: list[str] = []
            covered = 0
            for provider, domains in OFFICIAL_DOMAINS.items():
                selected = tuple(
                    d for d in domains if not request.domains or domain_matches(d, request.domains)
                )
                if not selected:
                    continue
                if covered >= request.result_limit:
                    break
                covered += 1
                subrequest = RetrievalRequest(
                    f"{provider} current supported API models free developer access constraints "
                    "rate limits general API subscription pricing deprecations",
                    request.freshness,
                    selected,
                    1,
                    request.time_range,
                )
                result = self._retrieve_one(subrequest, check_cancel, deadline)
                facts.extend(result.facts)
                limitations.extend(result.limitations)
                if not result.facts:
                    limitations.append(provider + ": public access constraints UNKNOWN.")
            return RetrievalResult(tuple(facts), limitations=tuple(dict.fromkeys(limitations)))
        return self._retrieve_one(request, check_cancel, deadline)

    def _retrieve_constraints(
        self, request: RetrievalRequest, check_cancel: Callable[[], None], deadline: float
    ) -> RetrievalResult:
        facts: list[RetrievedFact] = []
        assessments: list[ConstraintAssessment] = []
        labels = {
            "google": "Google AI Studio Gemini",
            "nvidia": "NVIDIA NIM API",
            "zai": "Z.ai API",
            "ollama-cloud": "Ollama Cloud",
        }
        for provider, domains in OFFICIAL_DOMAINS.items():
            selected = tuple(
                d for d in domains if not request.domains or domain_matches(d, request.domains)
            )
            if not selected or len(assessments) >= request.result_limit:
                continue
            label = labels.get(provider, provider)
            relevant: list[RetrievedFact] = []
            attempts: list[str] = []
            # Exactly two query stages; each stage has at most three credential attempts.
            # Successful but irrelevant results do not end the constraint lookup.
            for stage, query in enumerate(
                (
                    f"{label} API free tier developer rate limits official",
                    f"{label} API pricing free credits subscription usage limits "
                    "official documentation",
                )
            ):
                check_cancel()
                start = len(self.store.all("search_observation"))
                result = self._retrieve_one(
                    RetrievalRequest(query, request.freshness, selected, 2, request.time_range),
                    check_cancel,
                    deadline,
                )
                observations = self.store.all("search_observation")[start:]
                for observation in observations:
                    observation.update(
                        provider_id=provider,
                        query_stage=stage,
                        purpose="official_access_constraints",
                    )
                    self.store.put("search_observation", observation["id"], observation)
                    attempts.append(observation["id"])
                relevant = [
                    f
                    for f in result.facts
                    if f.retrieval_method == "official_page"
                    and f.source.current(self.clock())
                    and access_constraint_topics(f.text)
                ]
                if relevant:
                    break
            facts.extend(relevant[:1])
            assessments.append(
                ConstraintAssessment(
                    provider,
                    "REPORTED" if relevant else "UNKNOWN",
                    self.clock(),
                    tuple(attempts),
                    tuple(f.source.evidence_id or "" for f in relevant[:1]),
                    "Relevant directly read official constraint excerpt; "
                    "remaining account quota/funding UNKNOWN."
                    if relevant
                    else "No relevant directly readable official constraint page after bounded "
                    "official-source attempts; public constraints UNKNOWN / potentially stale.",
                )
            )
        return RetrievalResult(
            tuple(facts),
            limitations=(
                "Public plan policies are not account entitlement; "
                "missing account funding/quota remains UNKNOWN.",
            ),
            assessments=tuple(assessments),
        )

    def _retrieve_one(
        self, request: RetrievalRequest, check_cancel: Callable[[], None], deadline: float
    ) -> RetrievalResult:
        slots = sorted(self.pool.slots.values(), key=lambda s: (s.requests, s.id))
        for slot in slots:  # At most three attempts; a shared cooldown stops sibling rotation.
            if monotonic() >= deadline:
                return RetrievalResult((), "UNKNOWN", ("Search time budget reached: UNKNOWN.",))
            if not self.pool.eligible(slot.id, model="*"):
                continue
            try:
                return self.search(request, slot.id, check_cancel, deadline - monotonic())
            except ProviderError:
                continue
        return RetrievalResult((), "UNKNOWN", ("Tavily unavailable: UNKNOWN / potentially stale.",))
