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
from typing import TYPE_CHECKING, Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, build_opener

from .capabilities import Cancellation, Cancelled, Executor, Verifier
from .contracts import (
    Action,
    Capability,
    Epistemic,
    Evidence,
    Objective,
    Result,
    Task,
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

if TYPE_CHECKING:
    from .accounts import AccountRegistry


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
    consequences: tuple[RiskLevel, ...] = ()
    communication_trigger: str | None = None
    resource_name_prefix: str | None = None
    resource_id_field: str = "id"
    any_scopes: tuple[str, ...] = ()

    @property
    def permissions(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys("connectors:" + r.value for r in (self.risk, *self.consequences))
        )

    @property
    def catalog_permissions(self) -> tuple[str, ...]:
        # Grid authenticates before resolving the private parameter reference.
        # Advertise the ceiling so a weaker session cannot borrow executor grants.
        if self.communication_trigger:
            return tuple(dict.fromkeys((*self.permissions, "connectors:external-communication")))
        return self.permissions

    def action_permissions(self, parameters: dict[str, Any]) -> tuple[str, ...]:
        permissions = self.permissions
        if self.communication_trigger == "calendar":
            query = parameters.get("query", {})
            body = parameters.get("body", {})
            # Attendee changes can send mail even when notifications are suppressed.
            if query.get("sendUpdates", "none") != "none" or body.get("attendees"):
                permissions = (*permissions, "connectors:external-communication")
        return tuple(dict.fromkeys(permissions))

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
        if self.risk == RiskLevel.READ and (self.consequences or self.communication_trigger):
            raise ValueError("read capability cannot declare mutation consequences")
        if self.communication_trigger not in {None, "calendar"}:
            raise ValueError("unknown communication trigger")
        if self.resource_name_prefix is not None and (
            not isinstance(self.resource_name_prefix, str)
            or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*/", self.resource_name_prefix)
        ):
            raise ValueError("single resource collection prefix required")
        if not math.isfinite(self.freshness_seconds) or self.freshness_seconds < 0:
            raise ValueError("invalid freshness")
        if (
            not isinstance(self.resource_id_field, str)
            or self.resource_id_field not in {"id", "iid"}
            or (self.resource_id_field != "id" and self.resource_name_prefix is not None)
        ):
            raise ValueError("one declared resource identity convention required")
        if (
            not isinstance(self.any_scopes, tuple)
            or len(self.any_scopes) > 8
            or any(
                not isinstance(s, str) or not 1 <= len(s) <= 500 or any(c.isspace() for c in s)
                for s in self.any_scopes
            )
        ):
            raise ValueError("bounded explicit alternative scopes required")


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
    account_id: str | None = None
    account_generation: int | None = None
    account_audience: str | None = None


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
    capability_name: str = ""
    executed_instance: ConnectorInstance | None = field(default=None, repr=False)
    resource_path: dict[str, Any] = field(default_factory=dict, repr=False)


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
                next_page = (
                    response.headers.get("X-Next-Page") if manifest.provider == "gitlab" else None
                )
            if len(raw) > 2_000_000:
                raise ConnectorError("response_bound")
            if spec.response_kind == "bytes":
                payload: dict[str, Any] = {"base64": base64.b64encode(raw).decode()}
            else:
                payload = json.loads(raw) if raw else {}
            if isinstance(payload, list):
                payload = {"items": payload}
                if manifest.provider == "gitlab":
                    valid_page = isinstance(next_page, str) and (
                        next_page == "" or re.fullmatch(r"[1-9][0-9]{0,4}", next_page)
                    )
                    payload["pagination"] = {
                        "next_page": int(next_page) if valid_page and next_page else None,
                        "complete": next_page == "" if valid_page else None,
                    }
            if not isinstance(payload, dict):
                raise ConnectorError("invalid_contract")
            if payload.get("ok") is False or payload.get("error"):
                raise ConnectorError("provider_rejected")
            return payload, manifest.base_url.rstrip("/") + path.split("?")[0]
        except HTTPError as error:
            category = {401: "auth_missing", 403: "access_denied", 429: "rate_limited"}.get(
                error.code, "http_failure"
            )
            error.close()
            raise ConnectorError(category) from None
        except (URLError, OSError, TimeoutError):
            raise ConnectorError("network_failure") from None
        except (ValueError, TypeError):
            raise ConnectorError("invalid_contract") from None


_ACTIVE_CONTEXT_STATES = frozenset(
    {
        TaskState.PLANNED,
        TaskState.EXECUTING,
        TaskState.AWAITING_RESULT,
        TaskState.RESULT_RECEIVED,
        TaskState.VERIFYING,
    }
)


class ConnectorFabric:
    def __init__(
        self,
        store: Store,
        secrets: SecretResolver,
        policy: PersonalPolicy,
        http: ConnectorHTTP | None = None,
        *,
        accounts: "AccountRegistry | None" = None,
    ):
        self.store, self.secrets, self.policy = store, secrets, policy
        self.http = http or HTTPSConnector()
        self.accounts = accounts
        self.instances: dict[str, ConnectorInstance] = {}
        self.outcomes: dict[str, ConnectorOutcome] = {}
        self.requests: dict[str, dict[str, Any]] = {}
        self.request_owners: dict[str, str] = {}
        self.request_guards: dict[str, Callable[[], object]] = {}
        self.store.task_resources.add(self)

    def task_transitioned(self, task: Task) -> None:
        if task.state not in _ACTIVE_CONTEXT_STATES:
            self.release_task(task.id)

    def _reap_completed(self) -> None:
        # Admission also covers transitions committed by another Store/process.
        tasks = set(self.request_owners.values()) | {
            outcome.result.task_id for outcome in self.outcomes.values()
        }
        for task_id in tasks:
            self.task_transitioned(self.store.task(task_id))

    def stage(self, parameters: dict[str, Any]) -> str:
        """Return a transient input reference; private bodies never enter durable Action/plan."""
        self._reap_completed()
        serialized = json.dumps(parameters, allow_nan=False)
        if self.secrets.redact(serialized) != serialized or len(serialized) > 1_000_000:
            raise ValueError("unsafe or oversized connector input")
        if len(self.requests) >= 100 or len(self.outcomes) >= 100:
            raise ValueError("active connector context bound; release completed requests")
        reference = new_id()
        self.requests[reference] = json.loads(serialized)
        return reference

    def bind_task(self, task_id: str, parameters: dict[str, Any]) -> None:
        reference = parameters.get("request_ref")
        if reference not in self.requests:
            return  # Restart/expired input remains unavailable, never recreated.
        if reference in self.request_owners:
            raise ValueError("connector request already belongs to a task")
        self.request_owners[reference] = task_id

    def release_task(self, task_id: str) -> None:
        for reference, owner in list(self.request_owners.items()):
            if owner == task_id:
                self.release_request(reference)
        for result_id, outcome in list(self.outcomes.items()):
            if outcome.result.task_id == task_id:
                self.forget_outcome(result_id)

    def release_request(self, reference: str) -> None:
        self.requests.pop(reference, None)
        self.request_owners.pop(reference, None)
        self.request_guards.pop(reference, None)

    def install(self, instance: ConnectorInstance) -> None:
        if instance.id in self.instances:
            raise ValueError("connector instance already installed")
        if instance.account_id is not None:
            if (
                instance.account_generation is None
                or (
                    instance.manifest.auth == AuthType.MCP
                    and not callable(getattr(self.http, "connection_state", None))
                )
                or (
                    instance.manifest.auth != AuthType.MCP
                    and (
                        self.accounts is None
                        or instance.account_audience is None
                        or instance.credential is None
                    )
                )
            ):
                raise ValueError("complete trusted account binding required")
        self.instances[instance.id] = instance

    def state(self, instance: ConnectorInstance, spec: ConnectorCapability) -> ConnectionState:
        if not instance.available:
            return ConnectionState.UNAVAILABLE
        observed = None
        connection_state = getattr(self.http, "connection_state", None)
        if connection_state:
            observed = connection_state(instance)
            if observed is not None and observed != ConnectionState.READY:
                return ConnectionState(observed)
        if instance.account_id is not None:
            # MCP's trusted transport checks its private session/account binding itself.
            if instance.manifest.auth == AuthType.MCP:
                return (
                    ConnectionState.READY
                    if observed == ConnectionState.READY and instance.session_ready
                    else ConnectionState.AUTH_MISSING
                )
            try:
                if self.accounts is None or instance.account_generation is None:
                    return ConnectionState.AUTH_MISSING
                self.accounts.check(
                    instance.account_id,
                    instance.account_generation,
                    service=instance.manifest.id,
                    provider=instance.manifest.provider,
                    audience=instance.account_audience,
                    scopes=spec.scopes,
                    capability=spec.name,
                    credential=instance.credential,
                )
            except (KeyError, PermissionError):
                return ConnectionState.AUTH_MISSING
        if instance.manifest.auth == AuthType.MCP:
            return ConnectionState.READY if instance.session_ready else ConnectionState.AUTH_MISSING
        if instance.manifest.auth != AuthType.NONE and (
            instance.credential is None or not self.secrets.resolve(instance.credential)
        ):
            return ConnectionState.AUTH_MISSING
        if not set(spec.scopes) <= instance.granted_scopes or (
            spec.any_scopes and not set(spec.any_scopes) & instance.granted_scopes
        ):
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
                spec.catalog_permissions,
                spec.name,
                "connector-reference",
                "low" if spec.risk == RiskLevel.READ else "high",
            )
            for instance in tuple(self.instances.values())
            for spec in instance.manifest.capabilities
            if not eligible_only or self.state(instance, spec) == ConnectionState.READY
        ]

    def advertise(self, grid: Grid, session: SessionHandle) -> None:
        # Composition root combines other capabilities before advertising when sharing a node.
        grid.advertise(session, self.capabilities(session.node_id))

    def read_context(
        self,
        instance_id: str,
        name: str,
        parameters: dict[str, Any],
        guard: Callable[[], None],
    ) -> tuple[dict[str, Any], SourceRef]:
        """A separately granted perception read never acquires mutation/task authority."""
        instance = self.instances[instance_id]
        spec = next(c for c in instance.manifest.capabilities if c.name == name)
        if (
            instance.account_id is None
            or spec.method != "GET"
            or spec.risk != RiskLevel.READ
            or spec.permissions != ("connectors:read",)
            or spec.body_required
            or "body" in parameters
        ):
            raise PermissionError("ambient context requires an account-bound read-only GET")

        class ReadCancellation(Cancellation):
            def __init__(self) -> None:
                pass

            def check(inner_self) -> None:
                guard()
                if self.instances.get(instance_id) != instance:
                    raise PermissionError("connector binding changed during perception")
                if self.state(instance, spec) != ConnectionState.READY:
                    raise PermissionError("connector account or scope unavailable")
                for capability in (name, "connectors:read"):
                    if not self.policy.evaluate(
                        capability,
                        ("connectors:read",),
                        frozenset({"connectors:read"}),
                        {"account_id": instance.account_id or "", "purpose": "perception"},
                    ).allowed:
                        raise PermissionError("personal policy denies ambient retrieval")

        cancellation = ReadCancellation()
        cancellation.check()
        payload, source = self._request(instance, spec, parameters, cancellation)
        cancellation.check()
        return payload, source

    def _request(
        self,
        instance: ConnectorInstance,
        spec: ConnectorCapability,
        parameters: dict[str, Any],
        cancellation: Cancellation,
    ) -> tuple[dict[str, Any], SourceRef]:
        secret = self.secrets.resolve(instance.credential) if instance.credential else None
        if self.secrets.redact(json.dumps(parameters)) != json.dumps(parameters):
            raise ValueError("credential material cannot enter connector inputs")
        endpoint(spec, parameters)
        if self.state(instance, spec) != ConnectionState.READY:
            raise ConnectorError("auth_missing")
        cancellable = getattr(self.http, "request_cancellable", None)
        if cancellable:
            payload, identity = cancellable(
                instance.manifest, spec, parameters, secret, cancellation
            )
        else:
            payload, identity = self.http.request(instance.manifest, spec, parameters, secret)
        cancellation.check()
        if (
            self.instances.get(instance.id) != instance
            or self.state(instance, spec) != ConnectionState.READY
        ):
            raise ConnectorError("auth_missing")
        payload = json.loads(self.secrets.redact(json.dumps(payload)))
        return payload, SourceRef(
            identity,
            Authority.LIVE_API,
            "account" if instance.manifest.auth != AuthType.NONE else "provider",
            time(),
            spec.freshness_seconds,
            evidence_id=new_id(),
        )

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
        self._reap_completed()
        if len(self.outcomes) >= 100:
            raise ValueError("active connector outcome bound; release completed results")
        instance = self.instances[instance_id]
        spec = next(c for c in instance.manifest.capabilities if c.name == name)
        from .authority import check_task_account

        check_task_account(
            self.store, action.task_id, instance.account_id, instance.account_generation
        )
        if action.capability_id != instance_id + ":" + name:
            raise ValueError("connector executor identity mismatch")
        state = self.state(instance, spec)
        private = self.store.transient.get(action.task_id, {})
        objective = private.get("objective")
        account_pin = objective.criterion.get("connector_account") if objective else None
        if account_pin is not None and account_pin != {
            "id": instance.account_id,
            "generation": instance.account_generation,
        }:
            state = ConnectionState.AUTH_MISSING
        reviewed = private.get("review_parameters")
        if reviewed is not None and (
            reviewed.get("capability") != name or reviewed.get("parameters") != action.parameters
        ):
            raise PermissionError("connector input differs from exact owner review")
        permissions = spec.action_permissions(action.parameters)
        decision = self.policy.evaluate(
            name,
            permissions,
            granted,
            context,
            confirmed=confirmed,
            confirmation_required=spec.risk != RiskLevel.READ,
        )
        consequences = [
            self.policy.evaluate(permission, (permission,), granted, context, confirmed=confirmed)
            for permission in permissions
        ]
        cancellation.check()
        error: str | None = None
        payload: dict[str, Any] = {}
        source: SourceRef | None = None
        if state != ConnectionState.READY:
            error = "connector_blocked:" + state.value
        elif not decision.allowed or any(not d.allowed for d in consequences):
            error = "connector_blocked:policy"
        else:
            try:

                def authorize() -> None:
                    cancellation.check()
                    if private.get("connector_guard"):
                        private["connector_guard"]()
                    check_task_account(
                        self.store, action.task_id, instance.account_id, instance.account_generation
                    )
                    if self.instances.get(instance_id) != instance:
                        raise PermissionError("connector binding changed")
                    for operation, required in [
                        (name, permissions),
                        *[(p, (p,)) for p in permissions],
                    ]:
                        if not self.policy.evaluate(
                            operation,
                            required,
                            granted,
                            context,
                            confirmed=confirmed,
                            confirmation_required=operation == name and spec.risk != RiskLevel.READ,
                        ).allowed:
                            raise PermissionError("connector policy changed")

                guarded = Cancellation(self.store, action.task_id, authorize)
                guarded.check()
                payload, source = self._request(instance, spec, action.parameters, guarded)
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
                        "mcp_timeout",
                        "mcp_disconnected",
                        "mcp_request_failed",
                        "mcp_tool_removed",
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
            value=json.dumps(payload, ensure_ascii=False)[:8192]
            if error is None and action.task_id in self.store.transient
            else None,
        )
        outcome = ConnectorOutcome(
            result,
            source,
            payload,
            state,
            instance.id,
            granted,
            confirmed,
            context or {},
            name,
            instance,
            dict(action.parameters.get("path", {})),
        )
        with self.store.lock:
            if result.success and self.store.task(action.task_id).state in _ACTIVE_CONTEXT_STATES:
                self.outcomes[result.id] = outcome
        self.store.audit(
            action.task_id,
            "connector_result",
            {
                "instance_id": instance.id,
                "account_id": instance.account_id,
                "account_generation": instance.account_generation,
                "capability": name,
                "result_id": result.id,
                "status": Epistemic.REPORTED,
                "success": result.success,
                "error": error,
                "risk": spec.risk.value,
                "permissions": list(permissions),
                "policy_rules": sorted({r for d in [decision, *consequences] for r in d.rule_ids}),
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
    ) -> Executor:
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
            reference = action.parameters["request_ref"]
            owner = self.request_owners.get(reference)
            if owner != action.task_id:
                raise ValueError("connector input is not bound to this task")
            guard = self.request_guards.get(reference)
            if guard:
                guard()
                original = cancellation

                def check() -> None:
                    original.check()
                    guard()

                cancellation = Cancellation(self.store, action.task_id, check)
            # Consume before dispatch: every success/error/cancel path releases input.
            self.release_request(reference)
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
    """Independent account GET readback for writes and private read observations."""

    def __init__(
        self,
        base: Verifier,
        fabric: ConnectorFabric,
        observation_verifier: Callable[[Objective, Result, ConnectorOutcome | None], Verification]
        | None = None,
    ):
        super().__init__(base.files, base.clock)
        self.base, self.fabric = base, fabric
        self.observation_verifier = observation_verifier

    def bind_task(self, task_id: str, parameters: dict[str, Any]) -> None:
        self.fabric.bind_task(task_id, parameters)
        self.base.bind_task(task_id, parameters)

    def verify(self, objective: Objective, result: Result) -> Verification:
        try:
            return self._verify(objective, result)
        finally:
            self.fabric.forget_outcome(result.id)

    def _verify(self, objective: Objective, result: Result) -> Verification:
        if objective.criterion.get("kind") == "connector_observation" and self.observation_verifier:
            return self.observation_verifier(objective, result, self.fabric.outcomes.get(result.id))
        if objective.criterion.get("kind") not in {"connector_fields", "connector_communication"}:
            return self.base.verify(objective, result)
        criterion = objective.criterion
        matches: bool | None = None
        detail = "authoritative read-back unavailable"
        try:
            outcome = self.fabric.outcomes[result.id]
            if outcome.instance_id != criterion["instance_id"]:
                raise ConnectorError("readback_account_mismatch")
            instance = self.fabric.instances[outcome.instance_id]
            if (
                result != outcome.result
                or objective.correlation_id != result.correlation_id
                or instance != outcome.executed_instance
                or result.executor != instance.id + ":" + outcome.capability_name
            ):
                raise ConnectorError("readback_executor_mismatch")
            mutation = next(
                c for c in instance.manifest.capabilities if c.name == outcome.capability_name
            )
            if not mutation.readback or mutation.risk == RiskLevel.READ:
                raise ConnectorError("readback_undeclared")
            if criterion.get("read_capability", mutation.readback) != mutation.readback:
                raise ConnectorError("readback_capability_mismatch")
            read = next(c for c in instance.manifest.capabilities if c.name == mutation.readback)
            if (
                read.method != "GET"
                or read.risk != RiskLevel.READ
                or self.fabric.state(instance, read) != ConnectionState.READY
            ):
                raise ConnectorError("readback_unavailable")
            policy = self.fabric.policy.evaluate(
                read.name,
                read.permissions,
                outcome.granted,
                outcome.context,
                confirmed=outcome.confirmed,
            )
            if not policy.allowed or any(
                not self.fabric.policy.evaluate(
                    permission,
                    (permission,),
                    outcome.granted,
                    outcome.context,
                    confirmed=outcome.confirmed,
                ).allowed
                for permission in read.permissions
            ):
                raise ConnectorError("readback_permission_missing")
            if not criterion.get("expected") or not outcome.result.success:
                raise ConnectorError("completion_fields_missing")
            # Correlate the requested resource with the actual mutation response.
            identity_field = mutation.resource_id_field
            response_id = outcome.payload.get(identity_field)
            response_identity = response_id
            if identity_field == "iid":
                if type(response_id) is not int or not 1 <= response_id < 2**63:
                    raise ConnectorError("readback_resource_mismatch")
                response_id = str(response_id)
            if mutation.resource_name_prefix:
                identity_field = "name"
                response_identity = outcome.payload.get("name")
                if not isinstance(response_identity, str) or not re.fullmatch(
                    re.escape(mutation.resource_name_prefix) + r"[A-Za-z0-9_-]{1,128}",
                    response_identity,
                ):
                    raise ConnectorError("readback_resource_mismatch")
                response_id = response_identity.removeprefix(mutation.resource_name_prefix)
            expected_path = dict(outcome.resource_path)
            read_keys = set(re.findall(r"\{(.*?)\}", read.path))
            resource_keys = read_keys - expected_path.keys()
            if len(resource_keys) == 1:
                expected_path[next(iter(resource_keys))] = response_id
            communication = criterion["kind"] == "connector_communication"
            params: dict[str, Any] = (
                criterion["read_parameters"] if not communication else {"path": expected_path}
            )
            if communication and mutation.name.startswith("google.gmail."):
                params["query"] = {"format": "raw"}
            if (
                not response_id
                or len(resource_keys) > 1
                or params.get("path") != expected_path
                or response_id not in expected_path.values()
            ):
                raise ConnectorError("readback_resource_mismatch")
            endpoint(read, params)

            def authorize_readback() -> None:
                from .authority import check_task_account

                check_task_account(
                    self.fabric.store,
                    result.task_id,
                    instance.account_id,
                    instance.account_generation,
                )
                private = self.fabric.store.transient.get(result.task_id, {})
                if private.get("connector_guard"):
                    private["connector_guard"]()
                if (
                    self.fabric.instances.get(instance.id) != instance
                    or self.fabric.state(instance, read) != ConnectionState.READY
                ):
                    raise PermissionError("readback account changed")
                for operation, required in [
                    (read.name, read.permissions),
                    *[(p, (p,)) for p in read.permissions],
                ]:
                    if not self.fabric.policy.evaluate(
                        operation,
                        required,
                        outcome.granted,
                        outcome.context,
                        confirmed=outcome.confirmed,
                    ).allowed:
                        raise PermissionError("readback policy changed")

            cancellation = Cancellation(self.fabric.store, result.task_id, authorize_readback)
            cancellation.check()
            payload, _ = self.fabric._request(instance, read, params, cancellation)
            identity_matches = (
                type(payload.get(identity_field)) is type(response_identity)
                and payload.get(identity_field) == response_identity
            )
            if communication:
                from .communication import matches as communication_matches

                if criterion["operation"] != mutation.name:
                    raise ConnectorError("readback_operation_mismatch")
                matches = identity_matches and communication_matches(
                    mutation.name, payload, criterion["expected"]
                )
            else:
                matches = identity_matches and all(
                    payload.get(k) == v for k, v in criterion["expected"].items()
                )
            detail = "expected fields match" if matches else "read-back fields differ"
        except (
            KeyError,
            StopIteration,
            ConnectorError,
            ValueError,
            Cancelled,
            PermissionError,
            TypeError,
        ):
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
