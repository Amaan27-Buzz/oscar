"""Native structured connector boundary; Grid remains the executable Capability Catalog.

Private payloads stay in task-scoped transient outcomes. The ledger keeps metadata only.
Secret resolution is runtime-only. Platform vaults/OAuth enrollment are separate adapters.
"""

import base64
import hashlib
import json
import math
import os
import re
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from time import time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, build_opener

from .capabilities import Cancellation, Verifier
from .contracts import (
    Action,
    Capability,
    Epistemic,
    Evidence,
    Objective,
    Result,
    TaskState,
    Verification,
    new_id,
)
from .credentials import redact_runtime_secrets
from .freshness import Authority, SourceRef
from .grid import Grid, SessionHandle
from .http_client import NoRedirects
from .policy import PersonalPolicy
from .storage import Store


class RiskLevel(StrEnum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    FINANCIAL = "financial"
    SECURITY = "security-sensitive"
    COMMUNICATION = "external-communication"


class AuthType(StrEnum):
    NONE = "none"
    OAUTH = "oauth2"
    API_KEY = "api-key"
    SESSION = "session-token"
    MCP = "mcp-session"


class ConnectionState(StrEnum):
    READY = "ready"
    AUTH_MISSING = "auth_missing"
    SCOPE_MISSING = "scope_missing"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class CredentialRef:
    id: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9_.-]{1,80}", self.id):
            raise ValueError("credential reference must be an opaque identifier")


class SecretResolver(Protocol):
    def resolve(self, reference: CredentialRef) -> str | None: ...
    def redact(self, value: str) -> str: ...


class EnvironmentSecrets:
    """References select platform-supplied environment values; this is not a vault."""

    def __init__(self, bindings: Mapping[str, str], environ: Mapping[str, str] | None = None):
        self.bindings = dict(bindings)
        source = os.environ if environ is None else environ
        self._values = {k: source[v] for k, v in bindings.items() if source.get(v)}

    def resolve(self, reference: CredentialRef) -> str | None:
        return self._values.get(reference.id)

    def redact(self, value: str) -> str:
        for secret in self._values.values():
            value = value.replace(secret, "<redacted>")
        return redact_runtime_secrets(value)

    def __repr__(self) -> str:
        return "EnvironmentSecrets(<runtime-only>)"


class AuthSession(Protocol):
    """Provider enrollment adapter owns OAuth refresh/device flow/MCP authentication.

    Refresh never persists tokens through OSCAR domain serializers.
    """

    def refresh(self, reference: CredentialRef) -> None: ...
    def revoke(self, reference: CredentialRef) -> None: ...


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")
    return verifier, challenge.decode()


@dataclass(frozen=True)
class ConnectorCapability:
    name: str
    method: str
    path: str
    scopes: tuple[str, ...]
    risk: RiskLevel = RiskLevel.READ
    query_fields: tuple[str, ...] = ()
    body_required: bool = False
    verification: str = "unavailable"
    readback: str | None = None
    freshness_seconds: float = 60
    response_kind: str = "json"
    read_request: bool = False

    @property
    def permissions(self) -> tuple[str, ...]:
        return ("connectors:" + self.risk.value,)

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9_.-]+", self.name):
            raise ValueError("invalid namespaced capability")
        if self.method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
            raise ValueError("unsupported method")
        if not self.path.startswith("/") or "?" in self.path or ".." in self.path:
            raise ValueError("invalid endpoint template")
        if self.method != "GET" and self.risk == RiskLevel.READ and not self.read_request:
            # Read-only searches/freebusy use POST with an explicit exception at manifest authoring.
            if not self.name.endswith(("search", "query", "freebusy")):
                raise ValueError("mutation cannot be classified as read")
        if not math.isfinite(self.freshness_seconds) or self.freshness_seconds < 0:
            raise ValueError("invalid freshness")


@dataclass(frozen=True)
class ConnectorManifest:
    id: str
    provider: str
    base_url: str
    capabilities: tuple[ConnectorCapability, ...]
    auth: AuthType = AuthType.OAUTH
    version: int = 1
    events: tuple[str, ...] = ("polling",)
    rate_limit: str = "provider/account dependent; UNKNOWN until observed"
    headers: tuple[tuple[str, str], ...] = ()
    provenance: str = ""

    def __post_init__(self) -> None:
        url = urlparse(self.base_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("provider origin must be HTTPS without credentials or path")
        if self.version != 1 or len({c.name for c in self.capabilities}) != len(self.capabilities):
            raise ValueError("invalid connector manifest")
        if any(k.lower() in {"authorization", "cookie", "host"} for k, _ in self.headers):
            raise ValueError("secret headers cannot be manifest metadata")


@dataclass(frozen=True)
class ConnectorInstance:
    id: str
    manifest: ConnectorManifest
    credential: CredentialRef | None = None
    granted_scopes: frozenset[str] = frozenset()
    available: bool = True
    session_ready: bool = False


@dataclass(frozen=True)
class ConnectorOutcome:
    result: Result
    source: SourceRef | None
    payload: dict[str, Any] = field(default_factory=dict, repr=False)
    state: ConnectionState = ConnectionState.READY
    instance_id: str = ""
    granted: frozenset[str] = frozenset()
    confirmed: bool = False
    context: dict[str, str] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ConnectorEvent:
    instance_id: str
    provider_event_id: str
    source: SourceRef
    entity_refs: tuple[str, ...] = ()
    cursor: str | None = field(default=None, repr=False)
    mechanism: str = "polling"


class ConnectorError(Exception):
    pass


class ConnectorHTTP(Protocol):
    def request(
        self,
        manifest: ConnectorManifest,
        spec: ConnectorCapability,
        parameters: dict[str, Any],
        secret: str | None,
    ) -> tuple[dict[str, Any], str]: ...


def endpoint(spec: ConnectorCapability, parameters: dict[str, Any]) -> tuple[str, bytes | None]:
    if set(parameters) - {"path", "query", "body"}:
        raise ValueError("unsupported connector input fields")
    paths = parameters.get("path", {})
    query = parameters.get("query", {})
    if not isinstance(paths, dict) or not isinstance(query, dict):
        raise ValueError("path/query must be objects")
    fields = set(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", spec.path))
    if set(paths) != fields or set(query) - set(spec.query_fields):
        raise ValueError("input does not match endpoint contract")
    path = spec.path
    for key, value in paths.items():
        if not isinstance(value, str) or not value or value in {".", ".."} or len(value) > 500:
            raise ValueError("invalid resource identifier")
        path = path.replace("{" + key + "}", quote(value, safe=""))
    if any(type(v) not in {str, int, bool} for v in query.values()):
        raise ValueError("query values must be bounded scalars")
    body = parameters.get("body")
    if spec.body_required and not isinstance(body, dict):
        raise ValueError("JSON body required")
    if not spec.body_required and body is not None:
        raise ValueError("body is not supported by this endpoint")
    encoded = json.dumps(body, allow_nan=False).encode() if body is not None else None
    if encoded is not None and len(encoded) > 1_000_000:
        raise ValueError("connector input exceeds bound")
    suffix = "?" + urlencode(query) if query else ""
    if len(suffix) > 8000:
        raise ValueError("connector query exceeds bound")
    return path + suffix, encoded


class HTTPSConnector:
    """One bounded request; never retries writes or follows credential-bearing redirects."""

    def __init__(self, timeout: float = 15):
        if not 0 < timeout <= 60:
            raise ValueError("invalid timeout")
        self.timeout = timeout

    def request(
        self,
        manifest: ConnectorManifest,
        spec: ConnectorCapability,
        parameters: dict[str, Any],
        secret: str | None,
    ) -> tuple[dict[str, Any], str]:
        if spec.name == "google.drive.download":
            parameters = {**parameters, "query": {**parameters.get("query", {}), "alt": "media"}}
        if spec.name == "google.drive.export" and not parameters.get("query", {}).get("mimeType"):
            raise ValueError("export requires an explicit supported MIME type")
        path, body = endpoint(spec, parameters)
        headers = dict(manifest.headers)
        headers.update({"Accept": "application/json", "Content-Type": "application/json"})
        if secret:
            if "\r" in secret or "\n" in secret:
                raise ConnectorError("invalid_credential")
            headers["Authorization"] = "Bearer " + secret
        request = Request(
            manifest.base_url.rstrip("/") + path, data=body, headers=headers, method=spec.method
        )
        try:
            with build_opener(NoRedirects()).open(request, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ConnectorError("response_bound")
            if spec.response_kind == "bytes":
                payload: dict[str, Any] = {"base64": base64.b64encode(raw).decode()}
            else:
                payload = json.loads(raw) if raw else {}
            if isinstance(payload, list):
                payload = {"items": payload}
            if not isinstance(payload, dict):
                raise ConnectorError("invalid_contract")
            if payload.get("ok") is False or payload.get("error"):
                raise ConnectorError("provider_rejected")
            return payload, manifest.base_url.rstrip("/") + path.split("?")[0]
        except HTTPError as error:
            category = {401: "auth_missing", 403: "access_denied", 429: "rate_limited"}.get(
                error.code, "http_failure"
            )
            raise ConnectorError(category) from None
        except (URLError, OSError, TimeoutError):
            raise ConnectorError("network_failure") from None
        except (ValueError, TypeError):
            raise ConnectorError("invalid_contract") from None


class ConnectorFabric:
    def __init__(
        self,
        store: Store,
        secrets: SecretResolver,
        policy: PersonalPolicy,
        http: ConnectorHTTP | None = None,
    ):
        self.store, self.secrets, self.policy = store, secrets, policy
        self.http = http or HTTPSConnector()
        self.instances: dict[str, ConnectorInstance] = {}
        self.outcomes: dict[str, ConnectorOutcome] = {}
        self.requests: dict[str, dict[str, Any]] = {}

    def stage(self, parameters: dict[str, Any]) -> str:
        """Return a transient input reference; private bodies never enter durable Action/plan."""
        serialized = json.dumps(parameters, allow_nan=False)
        if self.secrets.redact(serialized) != serialized or len(serialized) > 1_000_000:
            raise ValueError("unsafe or oversized connector input")
        if len(self.requests) >= 100 or len(self.outcomes) >= 100:
            raise ValueError("active connector context bound; release completed requests")
        reference = new_id()
        self.requests[reference] = json.loads(serialized)
        return reference

    def release_request(self, reference: str) -> None:
        self.requests.pop(reference, None)

    def install(self, instance: ConnectorInstance) -> None:
        if instance.id in self.instances:
            raise ValueError("connector instance already installed")
        self.instances[instance.id] = instance

    def state(self, instance: ConnectorInstance, spec: ConnectorCapability) -> ConnectionState:
        if not instance.available:
            return ConnectionState.UNAVAILABLE
        if instance.manifest.auth == AuthType.MCP:
            return ConnectionState.READY if instance.session_ready else ConnectionState.AUTH_MISSING
        if instance.manifest.auth != AuthType.NONE and (
            instance.credential is None or not self.secrets.resolve(instance.credential)
        ):
            return ConnectionState.AUTH_MISSING
        if not set(spec.scopes) <= instance.granted_scopes:
            return ConnectionState.SCOPE_MISSING
        return ConnectionState.READY

    def capabilities(self, node_id: str, *, eligible_only: bool = True) -> list[Capability]:
        return [
            Capability(
                instance.id + ":" + spec.name,
                spec.name,
                "Structured " + instance.manifest.provider + " " + spec.risk.value,
                "connector",
                node_id,
                spec.permissions,
                spec.name,
                "connector-reference",
                "low" if spec.risk == RiskLevel.READ else "high",
            )
            for instance in self.instances.values()
            for spec in instance.manifest.capabilities
            if not eligible_only or self.state(instance, spec) == ConnectionState.READY
        ]

    def advertise(self, grid: Grid, session: SessionHandle) -> None:
        # Composition root combines other capabilities before advertising when sharing a node.
        grid.advertise(session, self.capabilities(session.node_id))

    def execute(
        self,
        instance_id: str,
        name: str,
        action: Action,
        cancellation: Cancellation,
        granted: frozenset[str],
        *,
        confirmed: bool = False,
        context: dict[str, str] | None = None,
    ) -> ConnectorOutcome:
        if len(self.outcomes) >= 100:
            raise ValueError("active connector outcome bound; release completed results")
        instance = self.instances[instance_id]
        spec = next(c for c in instance.manifest.capabilities if c.name == name)
        state = self.state(instance, spec)
        decision = self.policy.evaluate(
            name,
            spec.permissions,
            granted,
            context,
            confirmed=confirmed,
            confirmation_required=spec.risk != RiskLevel.READ,
        )
        cancellation.check()
        error: str | None = None
        payload: dict[str, Any] = {}
        source: SourceRef | None = None
        if state != ConnectionState.READY:
            error = "connector_blocked:" + state.value
        elif not decision.allowed:
            error = "connector_blocked:policy"
        else:
            secret = self.secrets.resolve(instance.credential) if instance.credential else None
            # Check credential material before any output/storage boundary.
            if self.secrets.redact(json.dumps(action.parameters)) != json.dumps(action.parameters):
                raise ValueError("credential material cannot enter connector inputs")
            endpoint(spec, action.parameters)
            try:
                payload, identity = self.http.request(
                    instance.manifest, spec, action.parameters, secret
                )
                cleaned = self.secrets.redact(json.dumps(payload))
                payload = json.loads(cleaned)
                source = SourceRef(
                    identity,
                    Authority.LIVE_API,
                    "account" if instance.manifest.auth != AuthType.NONE else "provider",
                    time(),
                    spec.freshness_seconds,
                    evidence_id=new_id(),
                )
            except ConnectorError as failure:
                category = str(failure)
                error = (
                    category
                    if category
                    in {
                        "auth_missing",
                        "access_denied",
                        "rate_limited",
                        "http_failure",
                        "network_failure",
                        "invalid_contract",
                        "response_bound",
                        "provider_rejected",
                        "invalid_credential",
                        "mcp_tool_failed",
                    }
                    else "connector_failure"
                )
        result = Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            error is None,
            error=error,
        )
        outcome = ConnectorOutcome(
            result, source, payload, state, instance.id, granted, confirmed, context or {}
        )
        self.outcomes[result.id] = outcome
        self.store.audit(
            action.task_id,
            "connector_result",
            {
                "instance_id": instance.id,
                "capability": name,
                "result_id": result.id,
                "status": Epistemic.REPORTED,
                "success": result.success,
                "error": error,
                "risk": spec.risk.value,
                "policy_rules": list(decision.rule_ids),
                "evidence_id": source.evidence_id if source else None,
                "observed_at": source.observed_at if source else time(),
                "correlation_id": action.correlation_id,
            },
        )
        return outcome

    def executor(
        self,
        instance_id: str,
        name: str,
        granted: frozenset[str],
        *,
        confirmed: Callable[[Action], bool] = lambda _: False,
    ) -> Callable[[Action, Cancellation], Result]:
        def invoke(action: Action, cancellation: Cancellation) -> Result:
            if set(action.parameters) != {"request_ref"}:
                raise ValueError("durable connector actions must use transient input references")
            try:
                parameters = self.requests[action.parameters["request_ref"]]
            except KeyError:
                return Result(
                    new_id(),
                    action.id,
                    action.task_id,
                    action.correlation_id,
                    action.capability_id,
                    False,
                    error="connector_blocked:input_expired",
                )
            transient = replace(action, parameters=parameters)
            return self.execute(
                instance_id, name, transient, cancellation, granted, confirmed=confirmed(action)
            ).result

        return invoke

    def forget_outcome(self, result_id: str) -> None:
        self.outcomes.pop(result_id, None)

    def ingest(self, event: ConnectorEvent, *, authenticated: bool) -> bool:
        if not authenticated:
            raise PermissionError("provider event authentication required")
        instance = self.instances[event.instance_id]
        if event.mechanism not in instance.manifest.events:
            raise ValueError("unsupported event mechanism")
        # Event bodies/cursors remain transient; this receipt is not durable content retention.
        key = hashlib.sha256(
            (event.instance_id + ":" + event.provider_event_id).encode()
        ).hexdigest()
        with self.store.transaction():
            try:
                self.store.get("connector_event_receipt", key)
                return False
            except KeyError:
                self.store.put(
                    "connector_event_receipt",
                    key,
                    {
                        "instance_id": event.instance_id,
                        "observed_at": event.source.observed_at,
                        "evidence_id": event.source.evidence_id,
                        "mechanism": event.mechanism,
                    },
                )
        return True


class ConnectorVerifier(Verifier):
    """Only explicit expected fields and an independently authorized GET can prove a write."""

    def __init__(self, base: Verifier, fabric: ConnectorFabric):
        super().__init__(base.files, base.clock)
        self.base, self.fabric = base, fabric

    def verify(self, objective: Objective, result: Result) -> Verification:
        if objective.criterion.get("kind") != "connector_fields":
            return self.base.verify(objective, result)
        criterion = objective.criterion
        matches: bool | None = None
        detail = "authoritative read-back unavailable"
        try:
            outcome = self.fabric.outcomes[result.id]
            if outcome.instance_id != criterion["instance_id"]:
                raise ConnectorError("readback_account_mismatch")
            instance = self.fabric.instances[criterion["instance_id"]]
            read = next(
                c for c in instance.manifest.capabilities if c.name == criterion["read_capability"]
            )
            if read.method != "GET" or self.fabric.state(instance, read) != ConnectionState.READY:
                raise ConnectorError("readback_unavailable")
            policy = self.fabric.policy.evaluate(
                read.name,
                read.permissions,
                outcome.granted,
                outcome.context,
                confirmed=outcome.confirmed,
            )
            if not policy.allowed:
                raise ConnectorError("readback_permission_missing")
            if not criterion.get("expected") or not outcome.result.success:
                raise ConnectorError("completion_fields_missing")
            params = criterion["read_parameters"]
            # Correlate the requested resource with the actual mutation response.
            response_id = outcome.payload.get("id")
            if not response_id or response_id not in params.get("path", {}).values():
                raise ConnectorError("readback_resource_mismatch")
            secret = (
                self.fabric.secrets.resolve(instance.credential) if instance.credential else None
            )
            payload, _ = self.fabric.http.request(instance.manifest, read, params, secret)
            matches = payload.get("id") == response_id and all(
                payload.get(k) == v for k, v in criterion["expected"].items()
            )
            detail = "expected fields match" if matches else "read-back fields differ"
        except (KeyError, StopIteration, ConnectorError, ValueError):
            pass
        state = (
            TaskState.PARTIALLY_VERIFIED
            if matches is None
            else (TaskState.VERIFIED if matches else TaskState.FAILED)
        )
        evidence = Evidence(
            new_id(),
            result.task_id,
            result.correlation_id,
            "connector-independent-readback",
            "authoritative GET expected fields",
            self.clock(),
            matches,
            Epistemic.VERIFIED if matches else Epistemic.REPORTED,
            detail,
        )
        return Verification(state, evidence)
