"""Evidence references and freshness decisions shared by retrieval and model discovery."""

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse


class Authority(StrEnum):
    LIVE_API = "live_api"
    OFFICIAL_DOCS = "official_docs"
    DEPRECATION = "official_deprecation"
    SECONDARY = "secondary"
    CACHE = "cache"
    PRIOR = "model_prior"


class Freshness(StrEnum):
    STATIC = "stable"
    CURRENT = "freshness_sensitive"
    LIVE = "live_state"
    UNKNOWN = "unknown_freshness"


@dataclass(frozen=True)
class SourceRef:
    identity: str
    authority: Authority
    scope: str
    observed_at: float
    ttl_seconds: float = 300
    refreshable: bool = True
    published_at: str | None = None

    def __post_init__(self) -> None:
        parsed = urlparse(self.identity)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("evidence identity must not contain credentials or query material")
        if self.scope not in {"account", "provider", "local"}:
            raise ValueError("invalid evidence scope")
        if not all(math.isfinite(n) and n >= 0 for n in (self.observed_at, self.ttl_seconds)):
            raise ValueError("invalid evidence time")

    def current(self, now: float) -> bool:
        return 0 <= now - self.observed_at <= self.ttl_seconds


def classify(text: str) -> Freshness:
    """Conservative grammar, not a claim of general intent understanding."""
    if re.search(
        r"\b(latest|current(?:ly)?|today|now|available|price|version|status|limit)s?\b", text
    ):
        return Freshness.CURRENT
    if re.search(
        r"\b(weather|flight|delayed|outage|inventory|quota|balance|deprecated|retired)\b"
        r"|\bmodels?\b.*\bsupport(?:ed|s)?\b|\bsupport(?:ed|s)?\b.*\bmodels?\b",
        text,
    ):
        return Freshness.LIVE
    return Freshness.UNKNOWN


def prefer_source(claim: str, left: SourceRef, right: SourceRef) -> SourceRef:
    """Authority is claim-specific; account entitlement and retirement are separate facts."""
    order = {
        Authority.LIVE_API: 0,
        Authority.OFFICIAL_DOCS: 1,
        Authority.DEPRECATION: 2,
        Authority.SECONDARY: 3,
        Authority.CACHE: 4,
        Authority.PRIOR: 5,
    }

    def rank(source: SourceRef) -> tuple[int, int, float]:
        if claim == "retirement" and source.authority == Authority.DEPRECATION:
            authority = -1
        else:
            authority = order[source.authority]
        account = int(claim == "account_availability" and source.scope != "account")
        return account, authority, -source.observed_at

    return min((left, right), key=rank)
