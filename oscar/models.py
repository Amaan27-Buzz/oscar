"""Router contracts. Model metadata is replaceable data with explicit provenance."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum


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
    def __init__(self, category: Failure, *, retry_after: float = 30, emitted: bool = False):
        self.category, self.retry_after, self.emitted = category, retry_after, emitted
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

    def __post_init__(self) -> None:
        if not 1 <= self.min_quality <= 5 or not 1 <= self.max_output_tokens <= 32768:
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


@dataclass(frozen=True)
class Route:
    provider: str
    model: str
    slot: str
    mode: Mode
    score: float
    reasons: tuple[str, ...]
    quota_remaining: int | None


@dataclass(frozen=True)
class RoutedResult:
    route: Route
    response: ProviderResponse
    attempts: int
    history_id: str
    status: str = "REPORTED"


StreamSink = Callable[[str], None]
