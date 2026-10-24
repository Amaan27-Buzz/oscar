"""Router contracts. Model metadata is replaceable data with explicit provenance."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .freshness import SourceRef


class Mode(StrEnum):
    AUTO = "auto"
    FAST = "fast"
    BALANCED = "balanced"
    HEAVY = "heavy"
    FREE_FIRST = "free_first"
    CHEAP = "cheap"
    LOCAL = "local"
    PRIVATE = "private"
    MANUAL = "manual"
    SPECIALIST = "specialist"


class Funding(StrEnum):
    FREE = "free"
    SUBSCRIPTION = "subscription"
    LOCAL = "local"
    PAID = "paid"
    UNKNOWN = "unknown"


class Failure(StrEnum):
    CREDENTIAL = "credential_failure"
    ACCESS = "access_denied"
    PRODUCT = "account_product_mismatch"
    CAPACITY = "temporary_capacity"
    UNKNOWN_LIMIT = "limit_cause_unknown"
    FUNDING = "funding_or_entitlement_unknown"
    MODEL = "model_failure"
    PROVIDER = "provider_failure"
    QUOTA = "quota_exhaustion"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network_failure"
    NETWORK_POLICY = "network_policy_blocked"
    CAPABILITY = "capability_mismatch"
    STRUCTURED = "structured_output_failure"
    CANCELLED = "cancelled"


class ProviderError(Exception):
    def __init__(
        self,
        category: Failure,
        *,
        retry_after: float = 30,
        emitted: bool = False,
        http_status: int | None = None,
        business_code: str | None = None,
        rate_limits: "RateLimits | None" = None,
    ):
        self.category, self.retry_after, self.emitted = category, retry_after, emitted
        self.http_status, self.business_code, self.rate_limits = (
            http_status,
            business_code,
            rate_limits,
        )
        super().__init__(category.value)


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    adapter: str
    base_url: str
    credential_envs: dict[str, str]
    local: bool = False
    private: bool = False
    enabled: bool = True
    provenance: str = "user configuration"
    discovery_required: bool = False
    inventory_ttl_seconds: float = 300
    account_product: str = "general-api"
    quota_pool: str | None = None
    credential_pools: dict[str, str] = field(default_factory=dict)
    quota_pool_provenance: str = "conservative shared pool; account identity UNKNOWN"
    allowed_tasks: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ModelSpec:
    provider_id: str
    id: str
    capabilities: frozenset[str]
    quality: int | None
    affinities: dict[str, float]
    context_limit: int | None = None
    output_limit: int | None = None
    funding: Funding = Funding.UNKNOWN
    price_per_million: float | None = None
    latency_ms: float | None = None
    reliability: float | None = None
    provenance: str = "unverified configuration"
    last_verified: float | None = None
    metadata_source: SourceRef | None = None
    funding_source: SourceRef | None = None
    retired: bool = False
    retirement_source: SourceRef | None = None


@dataclass(frozen=True)
class RateLimits:
    request_limit: int | None = None
    token_limit: int | None = None
    remaining_requests: int | None = None
    remaining_tokens: int | None = None
    requests_reset_at: float | None = None
    tokens_reset_at: float | None = None
    retry_after: float | None = None
    request_window: str = "UNKNOWN"
    token_window: str = "UNKNOWN"
    source: str = "response headers"
    request_reset_hint: str | None = None


@dataclass(frozen=True)
class DiscoveredModel:
    id: str
    capabilities: frozenset[str] = frozenset()
    context_limit: int | None = None
    output_limit: int | None = None
    funding: Funding = Funding.UNKNOWN
    active: bool | None = None


@dataclass(frozen=True)
class Inventory:
    provider: str
    slot: str
    source: SourceRef
    models: tuple[DiscoveredModel, ...]
    complete: bool = True
    pages: int = 1


@dataclass(frozen=True)
class ModelRequest:
    task_id: str
    correlation_id: str
    prompt: str = field(repr=False)
    task_class: str = "reasoning"
    required: frozenset[str] = frozenset({"text"})
    min_quality: int = 1
    input_tokens: int = 128
    max_output_tokens: int = 128
    mode: Mode = Mode.AUTO
    pinned_provider: str | None = None
    pinned_model: str | None = None
    pinned_slot: str | None = None
    ollama_think: bool | None = None

    @classmethod
    def from_config(cls, data: Any) -> "ModelRequest":
        allowed = {
            "mode",
            "pinned_provider",
            "pinned_model",
            "pinned_slot",
            "max_output_tokens",
            "ollama_think",
            "required",
        }
        if not isinstance(data, dict) or set(data) - allowed:
            raise ValueError("bounded model request configuration required")
        values = dict(data)
        if "required" in values:
            required = values["required"]
            if (
                not isinstance(required, list)
                or not 1 <= len(required) <= 2
                or any(not isinstance(v, str) for v in required)
                or len(set(required)) != len(required)
                or set(required) - {"text", "structured"}
                or "text" not in required
            ):
                raise ValueError("explicit supported model output requirements required")
            values["required"] = frozenset(required)
        if "mode" in values:
            values["mode"] = Mode(values["mode"])
        for key in ("pinned_provider", "pinned_model", "pinned_slot"):
            value = values.get(key)
            if value is not None and (
                not isinstance(value, str)
                or not 1 <= len(value) <= 256
                or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)
            ):
                raise ValueError("bounded model routing pin required")
        return cls("template", "template", "", **values)

    def __post_init__(self) -> None:
        if self.ollama_think is not None and type(self.ollama_think) is not bool:
            raise ValueError("Ollama thinking preference must be an explicit boolean")
        if (
            type(self.min_quality) is not int
            or not 1 <= self.min_quality <= 5
            or type(self.max_output_tokens) is not int
            or not 1 <= self.max_output_tokens <= 32768
        ):
            raise ValueError("invalid task quality/output budget")
        if (
            type(self.input_tokens) is not int
            or self.input_tokens < 0
            or not self.task_class
            or not self.required
        ):
            raise ValueError("invalid task requirements")
        object.__setattr__(self, "input_tokens", max(self.input_tokens, len(self.prompt.encode())))
        if self.mode == Mode.MANUAL and (not self.pinned_provider or not self.pinned_model):
            raise ValueError("manual routing requires provider and model")


@dataclass(frozen=True)
class RoutingPolicy:
    allow_paid: bool = False
    allow_unknown_cost: bool = False
    allowed_providers: frozenset[str] | None = None
    private_providers: frozenset[str] = frozenset()
    max_attempts: int = 4
    timeout_seconds: float = 15
    max_paid_cost: float = 0.01
    allow_unknown_limits: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.max_attempts <= 10 or not 0 < self.timeout_seconds <= 120:
            raise ValueError("invalid retry/time budget")
        if self.max_paid_cost < 0:
            raise ValueError("invalid monetary budget")


@dataclass(frozen=True)
class ProviderResponse:
    text: str = field(repr=False)
    input_tokens: int | None = None
    output_tokens: int | None = None
    remaining_requests: int | None = None
    remaining_tokens: int | None = None
    reset_at: float | None = None
    structured_ok: bool | None = None
    tool_ok: bool | None = None
    actual_model: str | None = None
    actual_provider: str | None = None
    rate_limits: RateLimits | None = None


@dataclass(frozen=True)
class Route:
    provider: str
    model: str
    slot: str
    mode: Mode
    score: float
    reasons: tuple[str, ...]
    quota_remaining: int | None
    quota_pool: str | None = None


@dataclass(frozen=True)
class RoutedResult:
    route: Route
    response: ProviderResponse
    attempts: int
    history_id: str
    status: str = "REPORTED"


StreamSink = Callable[[str], None]
