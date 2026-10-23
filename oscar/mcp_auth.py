"""Reviewed resource OAuth; tokens confer resource access, never person identity.

SDK discovery primitives are reused, while code/refresh exchanges remain one-shot.
"""

import hashlib
import hmac
import math
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urlsplit

from .accounts import Account
from .connectors import CredentialRef, pkce_pair
from .mcp_client import validate_destination

if TYPE_CHECKING:
    from .auth_broker import AuthBroker


def https_endpoint(value: Any) -> str:
    """Bounded exact endpoint: query-bearing authorization endpoints are unsupported."""
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 500
        or any(c.isspace() or ord(c) < 32 for c in value)
    ):
        raise ValueError("bounded fixed HTTPS MCP endpoint required")
    u = urlsplit(value)
    if (
        u.scheme != "https"
        or not u.hostname
        or u.username is not None
        or u.password is not None
        or u.query
        or u.fragment
    ):
        raise ValueError("fixed HTTPS MCP endpoint without query required")
    return value


def string_list(value: Any) -> list[str]:
    if (
        not isinstance(value, list)
        or len(value) > 100
        or any(not isinstance(s, str) or not s or len(s) > 500 for s in value)
    ):
        raise ValueError("bounded typed MCP metadata list required")
    return value


@dataclass(frozen=True)
class MCPProvider:
    id: str
    client_id: str
    redirect_uri: str
    resource: str
    issuer: str
    allowed_scopes: tuple[str, ...]
    provider: str = "mcp-resource"

    @property
    def service(self) -> str:
        return "mcp:" + self.id

    def __post_init__(self) -> None:
        for endpoint in (self.resource, self.issuer):
            https_endpoint(endpoint)
        u = urlsplit(self.redirect_uri)
        if (
            u.scheme != "http"
            or u.hostname != "127.0.0.1"
            or not u.port
            or u.port < 1024
            or u.username
            or u.query
            or u.fragment
        ):
            raise ValueError("exact native loopback callback required")
        for value in (self.id, self.client_id):
            if (
                not isinstance(value, str)
                or not 1 <= len(value) <= 200
                or any(ord(c) < 32 for c in value)
            ):
                raise ValueError("bounded registered MCP client required")
        if not 1 <= len(self.allowed_scopes) <= 100 or any(
            not isinstance(s, str) or not s or len(s) > 500 or any(c.isspace() for c in s)
            for s in self.allowed_scopes
        ):
            raise ValueError("explicit bounded MCP scope ceiling required")


class MCPAuthorization:
    def __init__(self, broker: "AuthBroker"):
        self.b = broker

    def request(self, url: str, fields: dict[str, str] | None = None) -> Any:
        """No redirects, environment proxy, retries, token logging or DNS rebinding."""
        import httpx2

        _, address = validate_destination(url)
        original = urlsplit(url)

        class Pinned(httpx2.BaseTransport):
            def handle_request(self, request: Any) -> Any:
                request.headers["host"] = original.netloc
                request.extensions["sni_hostname"] = original.hostname
                request.url = request.url.copy_with(host=address)
                with httpx2.HTTPTransport(trust_env=False, retries=0) as transport:
                    response = transport.handle_request(request)
                    # Consume before closing the private transport, with a strict bound.
                    raw = b""
                    for part in response.iter_bytes():
                        raw += part
                        if len(raw) > 128_000:
                            raise ValueError("MCP OAuth response bound")
                    return httpx2.Response(
                        response.status_code, headers=response.headers, content=raw, request=request
                    )

        with httpx2.Client(
            transport=Pinned(), trust_env=False, follow_redirects=False, timeout=15
        ) as client:
            return client.request(
                "POST" if fields is not None else "GET",
                url,
                data=fields,
                headers={"Accept": "application/json"},
            )

    def discover(self, provider: MCPProvider) -> dict[str, Any]:
        from mcp.client.auth.utils import (
            build_oauth_authorization_server_metadata_discovery_urls,
            build_protected_resource_metadata_discovery_urls,
            extract_resource_metadata_from_www_auth,
            extract_scope_from_www_auth,
        )

        challenge = self.request(provider.resource)
        if challenge.status_code not in {200, 401, 403, 405}:
            raise PermissionError("MCP resource discovery unavailable")
        metadata_url = extract_resource_metadata_from_www_auth(challenge)
        prm = None
        for url in build_protected_resource_metadata_discovery_urls(
            metadata_url, provider.resource
        ):
            response = self.request(url)
            if response.status_code in {404, 405}:
                continue
            if response.status_code != 200:
                raise PermissionError("MCP resource metadata unavailable")
            prm = response.json()
            break
        if (
            not isinstance(prm, dict)
            or prm.get("resource") != provider.resource
            or provider.issuer not in string_list(prm.get("authorization_servers"))
        ):
            raise PermissionError("MCP resource/issuer metadata binding rejected")
        metadata = None
        for url in build_oauth_authorization_server_metadata_discovery_urls(
            provider.issuer, provider.resource
        ):
            response = self.request(url)
            if response.status_code in {404, 405}:
                continue
            if response.status_code != 200:
                raise PermissionError("MCP authorization metadata unavailable")
            metadata = response.json()
            break
        if (
            not isinstance(metadata, dict)
            or metadata.get("issuer") != provider.issuer
            or "S256" not in string_list(metadata.get("code_challenge_methods_supported"))
        ):
            raise PermissionError("exact MCP issuer and PKCE S256 required")
        for key in ("authorization_endpoint", "token_endpoint"):
            validate_destination(https_endpoint(metadata.get(key)))
        for key, required in (
            ("token_endpoint_auth_methods_supported", "none"),
            ("response_types_supported", "code"),
            ("grant_types_supported", "authorization_code"),
        ):
            if key in metadata and required not in string_list(metadata[key]):
                raise PermissionError("registered MCP public code client unsupported")
        if type(metadata.get("authorization_response_iss_parameter_supported", False)) is not bool:
            raise ValueError("typed MCP issuer response support required")
        scopes = extract_scope_from_www_auth(challenge)
        recommended = scopes.split() if scopes else prm.get("scopes_supported", [])
        recommended = string_list(recommended)
        if not set(recommended) <= set(provider.allowed_scopes):
            raise PermissionError("MCP resource permissions exceed configured ceiling")
        return {"metadata": metadata, "recommended": recommended}

    def begin(
        self, p: MCPProvider, scopes: frozenset[str], alias: str, account_id: str | None = None
    ) -> dict[str, Any]:
        b = self.b
        b.accounts._text(alias)
        if not scopes or not scopes <= set(p.allowed_scopes):
            raise PermissionError("explicit MCP resource permissions required")
        previous = b.accounts.get(account_id) if account_id else None
        if previous and (
            previous.identity_class != "resource-grant"
            or previous.tenant != p.issuer
            or p.service not in previous.services
            or previous.services[p.service].audience != p.resource
        ):
            raise PermissionError("resource grant identity mismatch")
        discovery = self.discover(p)
        if not set(discovery["recommended"]) <= scopes or not scopes <= set(p.allowed_scopes):
            raise PermissionError("select the MCP resource's required permissions")
        metadata = discovery["metadata"]
        verifier, challenge = pkce_pair()
        state, identifier, reference = (
            secrets.token_urlsafe(32),
            secrets.token_hex(16),
            secrets.token_hex(16),
        )
        pending = {
            "id": identifier,
            "provider_id": p.id,
            "resource_grant": True,
            "configuration": b._fingerprint(p),
            "metadata": metadata,
            "account_id": account_id,
            "generation": previous.generation if previous else None,
            "alias": alias,
            "scopes": sorted(scopes),
            "verifier_ref": reference,
            "state_digest": hashlib.sha256(state.encode()).hexdigest(),
            "expires_at": b.clock() + 300,
            "state": "pending",
        }
        fields = {
            "client_id": p.client_id,
            "redirect_uri": p.redirect_uri,
            "response_type": "code",
            "scope": " ".join(sorted(scopes)),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": p.resource,
        }
        authorization_url = metadata["authorization_endpoint"] + "?" + urlencode(fields)
        if len(authorization_url) > 8000:
            raise ValueError("MCP authorization exceeds native browser URL bound")
        b.vault.put(verifier, expires_at=pending["expires_at"], reference=reference)
        try:
            b.store.put("auth_code_pending", identifier, pending)
        except Exception:
            b.vault.delete(reference)
            raise
        return {
            "id": identifier,
            "url": authorization_url,
            "redirect_uri": p.redirect_uri,
            "expires_at": pending["expires_at"],
            "authorization_kind": "mcp-resource",
            "authorization_endpoint": metadata["authorization_endpoint"],
            "issuer": p.issuer,
            "resource": p.resource,
            "issuer_required": metadata.get(
                "authorization_response_iss_parameter_supported", False
            ),
        }

    def complete(
        self,
        identifier: str,
        state: str,
        code: str,
        issuer: str | None,
        authority_check: Callable[[], None] | None,
    ) -> Account:
        b = self.b
        with b.store.transaction():
            if authority_check:
                authority_check()
            pending = b.store.get("auth_code_pending", identifier)
            p = b.providers[pending["provider_id"]]
            assert isinstance(p, MCPProvider)
            if (
                pending["state"] != "pending"
                or pending["expires_at"] <= b.clock()
                or not hmac.compare_digest(
                    pending["state_digest"], hashlib.sha256(state.encode()).hexdigest()
                )
                or pending["configuration"] != b._fingerprint(p)
            ):
                raise PermissionError("current MCP authorization required")
            if (issuer is not None and issuer != p.issuer) or (
                pending["metadata"].get("authorization_response_iss_parameter_supported")
                and issuer is None
            ):
                raise PermissionError("MCP authorization issuer mismatch")
            b.store.put("auth_code_pending", identifier, {**pending, "state": "exchanging"})
        try:
            response = self.request(
                pending["metadata"]["token_endpoint"],
                {
                    "grant_type": "authorization_code",
                    "client_id": p.client_id,
                    "redirect_uri": p.redirect_uri,
                    "code": code,
                    "resource": p.resource,
                    "code_verifier": b.vault.read(pending["verifier_ref"]).value,
                },
            )
            if response.status_code != 200:
                raise PermissionError("MCP token exchange rejected")
            return self.accept(identifier, pending, p, response.json(), authority_check)
        except Exception:
            b.store.put(
                "auth_code_pending",
                identifier,
                {**pending, "state": "blocked_reauthorization_required"},
            )
            raise RuntimeError(
                "MCP authorization interrupted or rejected; start a fresh review"
            ) from None
        finally:
            b.vault.delete(pending["verifier_ref"])

    def accept(
        self,
        identifier: str,
        pending: dict[str, Any],
        p: MCPProvider,
        data: dict[str, Any],
        authority_check: Callable[[], None] | None,
    ) -> Account:
        b = self.b
        token, refresh = data.get("access_token"), data.get("refresh_token")
        expiry = data.get("expires_in")
        if not isinstance(expiry, int | float) or isinstance(expiry, bool):
            raise ValueError("finite MCP token expiry required")
        scopes = data.get("scope", " ".join(pending["scopes"]))
        if (
            not isinstance(data.get("token_type"), str)
            or data["token_type"].lower() != "bearer"
            or not isinstance(token, str)
            or not 1 <= len(token) <= 32000
            or any(ord(c) < 33 for c in token)
            or not math.isfinite(expiry)
            or not 0 < expiry <= 86400 * 365
            or not isinstance(scopes, str)
            or set(scopes.split()) != set(pending["scopes"])
            or refresh is not None
            and (
                not isinstance(refresh, str)
                or not 1 <= len(refresh) <= 32000
                or any(ord(c) < 33 for c in refresh)
            )
        ):
            raise ValueError("bounded exact MCP token grant required")
        credential, refresh_ref = secrets.token_hex(16), secrets.token_hex(16) if refresh else ""
        b.material.remember(token)
        if refresh:
            b.material.remember(refresh)
        previous_connections: list[dict[str, Any]] = []
        try:
            b.vault.put(token, expires_at=b.clock() + expiry, reference=credential)
            if refresh:
                b.vault.put(refresh, reference=refresh_ref)
            with b.store.transaction():
                if authority_check:
                    authority_check()
                if pending.get("account_id"):
                    account = b.accounts.get(pending["account_id"])
                    if account.generation != pending["generation"]:
                        raise PermissionError("resource grant changed during authorization")
                    previous_connections = [
                        c
                        for c in b.store.all("auth_broker_connection")
                        if c["account_id"] == account.id
                        and c["id"] != identifier
                        and c.get("resource_grant")
                    ]
                else:
                    account = b.accounts.add_resource_grant(p.issuer, p.resource, pending["alias"])
                account = b.accounts.bind(
                    account.id,
                    p.service,
                    CredentialRef(credential),
                    scopes.split(),
                    p.resource,
                    expires_at=b.clock() + expiry,
                    expected_generation=account.generation,
                )
                b.store.put(
                    "auth_broker_connection",
                    identifier,
                    {
                        "id": identifier,
                        "resource_grant": True,
                        "provider_id": p.id,
                        "configuration": b._fingerprint(p),
                        "account_id": account.id,
                        "generation": account.generation,
                        "credential_ref": credential,
                        "refresh_ref": refresh_ref,
                        "scopes": sorted(scopes.split()),
                        "metadata": pending["metadata"],
                        "state": "ready",
                    },
                )
                if "verifier_ref" in pending:
                    b.store.put("auth_code_pending", identifier, {**pending, "state": "complete"})
                for previous in previous_connections:
                    b.store.put(
                        "auth_broker_connection",
                        previous["id"],
                        {**previous, "state": "superseded"},
                    )
        except Exception:
            b.vault.delete(credential)
            if refresh_ref:
                b.vault.delete(refresh_ref)
            raise
        for previous in previous_connections:
            for key in ("credential_ref", "refresh_ref"):
                if previous.get(key):
                    b.vault.delete(previous[key])
        return account

    def refresh(self, identifier: str, authority_check: Callable[[], None] | None) -> Account:
        b = self.b
        with b.store.transaction():
            if authority_check:
                authority_check()
            row = b.store.get("auth_broker_connection", identifier)
            p = b.providers[row["provider_id"]]
            assert isinstance(p, MCPProvider)
            account = b.accounts.check(row["account_id"], row["generation"])
            if (
                row["state"] != "ready"
                or not row["refresh_ref"]
                or row["configuration"] != b._fingerprint(p)
            ):
                raise PermissionError("current refreshable resource grant required")
            b.store.put("auth_broker_connection", identifier, {**row, "state": "refreshing"})
        try:
            response = self.request(
                row["metadata"]["token_endpoint"],
                {
                    "grant_type": "refresh_token",
                    "client_id": p.client_id,
                    "resource": p.resource,
                    "refresh_token": b.vault.read(row["refresh_ref"]).value,
                },
            )
            if response.status_code != 200:
                raise PermissionError("MCP refresh rejected")
            data = response.json()
            if not data.get("refresh_token"):
                data["refresh_token"] = b.vault.read(row["refresh_ref"]).value
            return self.accept(
                identifier, {**row, "alias": account.alias}, p, data, authority_check
            )
        except Exception:
            b._fail_connection(identifier)
            raise RuntimeError("MCP refresh interrupted; reauthorization required") from None
        finally:
            b.vault.delete(row["credential_ref"])
            b.vault.delete(row["refresh_ref"])
