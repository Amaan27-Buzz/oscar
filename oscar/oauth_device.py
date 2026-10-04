"""Registered GitHub OAuth device enrollment; tokens live only in the native vault.

No borrowed CLI/browser tokens. One poll per explicit call, respecting server interval.
GitHub OAuth App device grants do not use a redirect/PKCE or support refresh tokens.
"""

import hashlib
import hmac
import json
import re
import secrets
from collections.abc import Callable
from time import time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from .connectors import AuthType, ConnectorCapability, ConnectorManifest, CredentialRef, RiskLevel
from .credentials import redact_runtime_secrets
from .http_client import NoRedirects
from .secure_credentials import SecretValue
from .storage import Store


class Vault(Protocol):
    def put(
        self, secret: str, *, expires_at: float | None = None, reference: str | None = None
    ) -> str: ...
    def read(self, reference: str, *, allow_expired: bool = False) -> SecretValue: ...
    def delete(self, reference: str) -> None: ...


class VaultResolver:
    def __init__(self, vault: Vault):
        self.vault = vault
        self.material: set[str] = set()

    def resolve(self, reference: CredentialRef) -> str | None:
        try:
            value = self.vault.read(reference.id).value
        except (KeyError, PermissionError):
            return None
        self.material.add(value)
        return value

    def redact(self, text: str) -> str:
        for secret in self.material:
            text = text.replace(secret, "<redacted>")
        return redact_runtime_secrets(text)

    def close(self) -> None:
        self.material.clear()


def post(path: str, fields: dict[str, str]) -> dict[str, Any]:
    if path not in {"/login/device/code", "/login/oauth/access_token"}:
        raise ValueError("fixed official OAuth endpoint required")
    request = Request(
        "https://github.com" + path,
        data=urlencode(fields).encode(),
        headers={"Accept": "application/json"},
        method="POST",
    )
    try:
        with build_opener(NoRedirects()).open(request, timeout=15) as response:
            raw = response.read(64_001)
        if len(raw) > 64_000:
            raise ValueError("OAuth response bound")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("invalid OAuth response")
        return data
    except (HTTPError, URLError, OSError, ValueError):
        raise RuntimeError("official OAuth endpoint unavailable or rejected") from None


class GitHubDeviceFlow:
    SCOPES = frozenset({"user:email", "gist"})

    def __init__(
        self,
        store: Store,
        vault: Vault,
        request: Callable[[str, dict[str, str]], dict[str, Any]] = post,
        clock: Callable[[], float] = time,
    ):
        self.store, self.vault, self.request, self.clock = store, vault, request, clock

    def begin(
        self,
        client_id: str,
        *,
        owner_authorized: bool,
        scopes: frozenset[str] = frozenset({"user:email"}),
    ) -> dict[str, Any]:
        if not owner_authorized:
            raise PermissionError("owner enrollment authority required")
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]{10,100}", client_id)
            or not scopes
            or not scopes <= self.SCOPES
        ):
            raise ValueError("registered client and minimum supported scopes required")
        data = self.request(
            "/login/device/code", {"client_id": client_id, "scope": " ".join(sorted(scopes))}
        )
        if (
            data.get("verification_uri") != "https://github.com/login/device"
            or not isinstance(data.get("device_code"), str)
            or not isinstance(data.get("user_code"), str)
            or type(data.get("expires_in")) is not int
            or not 1 <= data["expires_in"] <= 3600
            or type(data.get("interval")) is not int
            or not 1 <= data["interval"] <= 60
        ):
            raise ValueError("invalid official device challenge")
        nonce = secrets.token_urlsafe(32)
        identifier = secrets.token_hex(16)
        expires = self.clock() + data["expires_in"]
        reference = self.vault.put(data["device_code"], expires_at=expires)
        self.store.put(
            "oauth_pending",
            identifier,
            {
                "id": identifier,
                "client_id": client_id,
                "device_ref": reference,
                "nonce_digest": hashlib.sha256(nonce.encode()).hexdigest(),
                "expires_at": expires,
                "interval": data["interval"],
                "next_poll": self.clock() + data["interval"],
                "scopes": sorted(scopes),
                "state": "pending",
            },
        )
        # Owner code/nonce go only to the interactive caller; they are not stored/logged here.
        return {
            "id": identifier,
            "nonce": nonce,
            "url": data["verification_uri"],
            "user_code": data["user_code"],
            "expires_at": expires,
            "scopes": sorted(scopes),
        }

    def poll_once(self, identifier: str, nonce: str, *, owner_authorized: bool) -> dict[str, Any]:
        if not owner_authorized:
            raise PermissionError("owner confirmation required")
        now = self.clock()
        with self.store.transaction():
            pending = self.store.get("oauth_pending", identifier)
            if pending["state"] != "pending" or not hmac.compare_digest(
                pending["nonce_digest"], hashlib.sha256(nonce.encode()).hexdigest()
            ):
                raise PermissionError("device transaction identity mismatch or outcome ambiguous")
            if now >= pending["expires_at"]:
                pending["state"] = "expired"
            elif now < pending["next_poll"]:
                return {"state": "pending", "retry_after": pending["next_poll"] - now}
            else:
                pending["state"] = "polling"
                pending["next_poll"] = now + pending["interval"]
            self.store.put("oauth_pending", identifier, pending)
        if pending["state"] == "expired":
            self.vault.delete(pending["device_ref"])
            raise PermissionError("device authorization expired")
        try:
            data = self.request(
                "/login/oauth/access_token",
                {
                    "client_id": pending["client_id"],
                    "device_code": self.vault.read(pending["device_ref"]).value,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
        except Exception:
            pending["state"] = "ambiguous"
            self.store.put("oauth_pending", identifier, pending)
            raise RuntimeError("token exchange outcome ambiguous; no automatic replay") from None
        error = data.get("error")
        if error in {"authorization_pending", "slow_down"}:
            pending["state"] = "pending"
            if error == "slow_down":
                pending["interval"] += 5
                pending["next_poll"] = now + pending["interval"]
            self.store.put("oauth_pending", identifier, pending)
            return {"state": "pending", "retry_after": pending["interval"]}
        if error:
            self.vault.delete(pending["device_ref"])
            pending["state"] = "rejected"
            self.store.put("oauth_pending", identifier, pending)
            raise PermissionError("owner authorization rejected or unavailable")
        scopes = frozenset(re.split(r"[ ,]+", str(data.get("scope", "")))) - {""}
        if (
            not isinstance(data.get("access_token"), str)
            or not data["access_token"]
            or data.get("token_type", "").lower() != "bearer"
            or scopes != frozenset(pending["scopes"])
        ):
            pending["state"] = "unexpected_token_provider_review_required"
            self.store.put("oauth_pending", identifier, pending)
            raise PermissionError("unexpected OAuth token contract or scopes; enrollment blocked")
        expiry = data.get("expires_in")
        if expiry is not None and (type(expiry) is not int or not 0 < expiry <= 86400):
            raise ValueError("unsupported expiry contract")
        token_ref = self.vault.put(
            data["access_token"], expires_at=now + expiry if expiry else None
        )
        self.vault.delete(pending["device_ref"])
        pending["state"] = "authorized"
        connection = {
            "id": identifier,
            "client_id": pending["client_id"],
            "credential_ref": token_ref,
            "scopes": sorted(scopes),
            "expires_at": now + expiry if expiry else None,
            "refresh": "unsupported OAuth App grant",
            "state": "ready",
        }
        with self.store.transaction():
            self.store.put("oauth_pending", identifier, pending)
            self.store.put("oauth_connection", identifier, connection)
        return connection

    def disconnect(self, identifier: str, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("owner disconnect authority required")
        connection = self.store.get("oauth_connection", identifier)
        self.vault.delete(connection["credential_ref"])
        connection["state"] = "locally_disconnected_provider_revocation_pending"
        self.store.put("oauth_connection", identifier, connection)


def github_manifest() -> ConnectorManifest:
    return ConnectorManifest(
        "github-oauth",
        "GitHub",
        "https://api.github.com",
        (
            ConnectorCapability("github.owner", "GET", "/user", (), verification="unavailable"),
            ConnectorCapability("github.emails", "GET", "/user/emails", ("user:email",)),
            ConnectorCapability(
                "github.gist.create",
                "POST",
                "/gists",
                ("gist",),
                RiskLevel.WRITE,
                body_required=True,
            ),
            ConnectorCapability("github.gist.read", "GET", "/gists/{gist}", ("gist",)),
            ConnectorCapability(
                "github.gist.delete", "DELETE", "/gists/{gist}", ("gist",), RiskLevel.DESTRUCTIVE
            ),
        ),
        AuthType.OAUTH,
        headers=(("X-GitHub-Api-Version", "2026-03-10"),),
        provenance="https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps",
    )
