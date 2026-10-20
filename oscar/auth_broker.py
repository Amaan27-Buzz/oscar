"""Shared public-client OAuth code/PKCE broker with verified OIDC account binding.

Tokens and PKCE material use the existing Vault protocol. Store records are metadata.
The existing accepted GitHub device adapter remains unchanged and separately usable.
"""

import base64
import hashlib
import hmac
import json
import math
import re
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass
from time import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener

from .accounts import Account, AccountRegistry
from .connectors import CredentialRef, pkce_pair
from .credentials import SecretMaterial
from .http_client import NoRedirects
from .oauth_device import Vault


@dataclass(frozen=True)
class OAuthProvider:
    id: str
    provider: str
    client_id: str
    redirect_uri: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    issuer: str
    service: str
    audience: str
    tenant: str = ""
    client_secret_ref: str | None = None

    def __post_init__(self) -> None:
        for endpoint in (self.authorization_endpoint, self.token_endpoint, self.jwks_uri):
            url = urlparse(endpoint)
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.query
                or url.fragment
            ):
                raise ValueError("fixed HTTPS OAuth endpoints required")
        redirect = urlparse(self.redirect_uri)
        if (
            redirect.scheme != "http"
            or redirect.hostname not in {"127.0.0.1", "[::1]", "::1"}
            or redirect.username
            or redirect.query
            or redirect.fragment
            or redirect.port is None
        ):
            raise ValueError("explicit native loopback redirect and port required")
        for value in (self.id, self.client_id, self.service, self.audience, self.issuer):
            if not isinstance(value, str) or not value or len(value) > 1000:
                raise ValueError("bounded OAuth configuration required")


def google_provider(
    client_id: str,
    redirect_uri: str,
    service: str,
    audience: str,
    *,
    client_secret_ref: str | None = None,
) -> OAuthProvider:
    return OAuthProvider(
        "google:" + service,
        "google",
        client_id,
        redirect_uri,
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token",
        "https://www.googleapis.com/oauth2/v3/certs",
        "https://accounts.google.com",
        service,
        audience,
        client_secret_ref=client_secret_ref,
    )


def microsoft_provider(
    client_id: str,
    redirect_uri: str,
    tenant: str,
    service: str = "microsoft.graph",
) -> OAuthProvider:
    if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", tenant):
        raise ValueError("explicit Microsoft tenant ID required")
    tenant = tenant.lower()
    origin = "https://login.microsoftonline.com/" + tenant
    return OAuthProvider(
        "microsoft:" + service,
        "microsoft",
        client_id,
        redirect_uri,
        origin + "/oauth2/v2.0/authorize",
        origin + "/oauth2/v2.0/token",
        origin + "/discovery/v2.0/keys",
        origin + "/v2.0",
        service,
        "https://graph.microsoft.com",
        tenant,
    )


def oauth_request(url: str, fields: dict[str, str] | None) -> dict[str, Any]:
    """Private trusted transport. Never follows redirects, logs payloads or retries."""
    if urlparse(url).scheme != "https":
        raise ValueError("OAuth TLS required")
    request = Request(
        url,
        data=urlencode(fields).encode() if fields is not None else None,
        headers={"Accept": "application/json"},
        method="POST" if fields is not None else "GET",
    )
    try:
        with build_opener(NoRedirects()).open(request, timeout=15) as response:
            raw = response.read(128_001)
        if len(raw) > 128_000:
            raise ValueError("OAuth response bound")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("OAuth response must be an object")
        return value
    except (HTTPError, URLError, OSError, ValueError):
        raise RuntimeError("OAuth provider unavailable or rejected") from None


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class AuthBroker:
    def __init__(
        self,
        accounts: AccountRegistry,
        vault: Vault,
        providers: list[OAuthProvider],
        *,
        request: Callable[[str, dict[str, str] | None], dict[str, Any]] = oauth_request,
        clock: Callable[[], float] = time,
    ):
        self.accounts, self.store, self.vault = accounts, accounts.store, vault
        self.providers = {provider.id: provider for provider in providers}
        if len(self.providers) != len(providers):
            raise ValueError("unique OAuth configuration IDs required")
        self.request, self.clock = request, clock
        self.material = SecretMaterial()
        self.recover()

    @staticmethod
    def _fingerprint(provider: OAuthProvider) -> str:
        return hashlib.sha256(json.dumps(asdict(provider), sort_keys=True).encode()).hexdigest()

    def recover(self) -> None:
        # A consumed authorization code/rotating refresh token is never replayed after interruption.
        for pending in self.store.all("auth_code_pending"):
            if pending["state"] == "exchanging" or (
                pending["state"] == "pending" and pending["expires_at"] <= self.clock()
            ):
                pending["state"] = "blocked_reauthorization_required"
                self.store.put("auth_code_pending", pending["id"], pending)
            if pending["state"] != "pending":
                self.vault.delete(pending["verifier_ref"])
        for connection in self.store.all("auth_broker_connection"):
            if connection["state"] in {"exchanging", "refreshing", "deleting"}:
                if connection.get("account_id"):
                    self.accounts.disconnect(connection["account_id"])
                for key in ("credential_ref", "refresh_ref"):
                    if connection.get(key):
                        self.vault.delete(connection[key])
                connection["state"] = "blocked_reauthorization_required"
                self.store.put("auth_broker_connection", connection["id"], connection)
        for account in self.accounts.list_accounts():
            if account.status == "disconnected" and account.local_credentials == "deletion_pending":
                try:
                    self.finish_disconnect(account)
                except (OSError, PermissionError):
                    # Credential cleanup cannot restore authority or prevent Core recovery.
                    pass

    def begin(
        self,
        provider_id: str,
        scopes: frozenset[str],
        *,
        owner_authorized: bool,
        alias: str,
        identity_class: str = "owner-delegated",
        account_id: str | None = None,
    ) -> dict[str, Any]:
        if not owner_authorized:
            raise PermissionError("owner enrollment authority required")
        provider = self.providers[provider_id]
        self.accounts._text(alias)
        if len(scopes) > 100 or any(
            not s or len(s) > 500 or any(c.isspace() for c in s) for s in scopes
        ):
            raise ValueError("bounded OAuth scopes required")
        if account_id:
            account = self.accounts.get(account_id)
            if account.provider != provider.provider or account.identity_class != identity_class:
                raise PermissionError("account upgrade identity mismatch")
            existing = account.services.get(provider.service)
            if existing:
                scopes = scopes | frozenset(existing.scopes)
        verifier, challenge = pkce_pair()
        nonce, state, identifier = (
            secrets.token_urlsafe(32),
            secrets.token_urlsafe(32),
            secrets.token_hex(16),
        )
        reference = secrets.token_hex(16)
        pending: dict[str, Any] = {
            "id": identifier,
            "provider_id": provider_id,
            "configuration": self._fingerprint(provider),
            "account_id": account_id,
            "generation": self.accounts.get(account_id).generation if account_id else None,
            "account_epochs": {a.id: a.generation for a in self.accounts.list_accounts()},
            "alias": alias,
            "identity_class": identity_class,
            "state_digest": hashlib.sha256(state.encode()).hexdigest(),
            "nonce_digest": hashlib.sha256(nonce.encode()).hexdigest(),
            "verifier_ref": reference,
            "scopes": sorted(scopes | {"openid"}),
            "expires_at": self.clock() + 300,
            "state": "pending",
        }
        self.store.put("auth_code_pending", identifier, pending)
        self.vault.put(verifier, expires_at=pending["expires_at"], reference=reference)
        fields = {
            "client_id": provider.client_id,
            "redirect_uri": provider.redirect_uri,
            "response_type": "code",
            "scope": " ".join(pending["scopes"]),
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        if provider.provider == "google":
            fields["access_type"] = "offline"
        return {
            "id": identifier,
            "url": provider.authorization_endpoint + "?" + urlencode(fields),
            "expires_at": pending["expires_at"],
        }

    def _identity(
        self, token: str, provider: OAuthProvider, nonce_digest: str | None, access_token: str
    ) -> tuple[str, str]:
        # OIDC ID tokens establish identity; decoding an unsigned JWT never establishes an account.
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        try:
            if not isinstance(token, str) or len(token) > 32_000:
                raise ValueError
            header64, claims64, signature64 = token.split(".")
            header, claims = json.loads(_decode(header64)), json.loads(_decode(claims64))
            if header["alg"] != "RS256" or not isinstance(header["kid"], str):
                raise ValueError
            keys = self.request(provider.jwks_uri, None)["keys"]
            matches = [
                k
                for k in keys
                if k.get("kid") == header["kid"]
                and k.get("kty") == "RSA"
                and k.get("use", "sig") == "sig"
                and k.get("alg", "RS256") == "RS256"
            ]
            if len(matches) != 1:
                raise ValueError
            key = matches[0]
            public = rsa.RSAPublicNumbers(
                int.from_bytes(_decode(key["e"])), int.from_bytes(_decode(key["n"]))
            ).public_key()
            if public.key_size < 2048:
                raise ValueError
            public.verify(
                _decode(signature64),
                (header64 + "." + claims64).encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            issuers = {provider.issuer}
            if provider.provider == "google":
                issuers.add("accounts.google.com")
            if claims["iss"] not in issuers or claims["aud"] != provider.client_id:
                raise ValueError
            if claims.get("azp", provider.client_id) != provider.client_id:
                raise ValueError
            for name in ("exp", "iat"):
                if type(claims[name]) not in {int, float} or not math.isfinite(claims[name]):
                    raise ValueError
            if claims["exp"] <= self.clock() or claims["iat"] > self.clock() + 60:
                raise ValueError
            if "at_hash" in claims:
                expected_hash = (
                    base64.urlsafe_b64encode(hashlib.sha256(access_token.encode()).digest()[:16])
                    .rstrip(b"=")
                    .decode()
                )
                if not hmac.compare_digest(expected_hash, claims["at_hash"]):
                    raise ValueError
            if nonce_digest is not None and not hmac.compare_digest(
                hashlib.sha256(claims["nonce"].encode()).hexdigest(), nonce_digest
            ):
                raise ValueError
            subject = self.accounts._text(claims["sub"])
            tenant = "google"
            if provider.provider == "microsoft":
                if claims["tid"] != provider.tenant:
                    raise ValueError
                tenant, subject = provider.tenant, self.accounts._text(claims["oid"])
            return tenant, subject
        except (KeyError, TypeError, ValueError, InvalidSignature, AttributeError):
            raise PermissionError("OIDC signature, account or nonce validation failed") from None

    def _token_fields(self, provider: OAuthProvider) -> dict[str, str]:
        fields = {"client_id": provider.client_id}
        if provider.client_secret_ref:
            fields["client_secret"] = self.vault.read(provider.client_secret_ref).value
            self.material.remember(fields["client_secret"])
        return fields

    def complete(
        self,
        identifier: str,
        state: str,
        code: str,
        *,
        owner_authorized: bool,
    ) -> Account:
        if not owner_authorized:
            raise PermissionError("owner callback authority required")
        if not isinstance(code, str) or not code or len(code) > 8000:
            raise ValueError("bounded authorization code required")
        with self.store.transaction():
            pending = self.store.get("auth_code_pending", identifier)
            provider = self.providers[pending["provider_id"]]
            if (
                pending["state"] != "pending"
                or pending["expires_at"] <= self.clock()
                or not hmac.compare_digest(
                    hashlib.sha256(state.encode()).hexdigest(), pending["state_digest"]
                )
                or pending["configuration"] != self._fingerprint(provider)
            ):
                raise PermissionError("OAuth callback state, configuration or expiry mismatch")
            if pending["account_id"]:
                self.accounts.check(pending["account_id"], pending["generation"])
            pending["state"] = "exchanging"
            self.store.put("auth_code_pending", identifier, pending)
        try:
            fields = {
                **self._token_fields(provider),
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": provider.redirect_uri,
                "code_verifier": self.vault.read(pending["verifier_ref"]).value,
            }
            data = self.request(provider.token_endpoint, fields)
            return self._accept(identifier, pending, provider, data, pending["nonce_digest"])
        except Exception:
            pending["state"] = "blocked_reauthorization_required"
            self.store.put("auth_code_pending", identifier, pending)
            self._fail_connection(identifier)
            raise RuntimeError(
                "OAuth enrollment rejected or interrupted; reauthorization required"
            ) from None
        finally:
            self.vault.delete(pending["verifier_ref"])

    def _accept(
        self,
        identifier: str,
        pending: dict[str, Any],
        provider: OAuthProvider,
        data: dict[str, Any],
        nonce_digest: str | None,
    ) -> Account:
        self.material.clear()
        for key in ("access_token", "refresh_token", "id_token"):
            if isinstance(data.get(key), str):
                self.material.remember(data[key])
        if "scope" not in data:
            data["scope"] = " ".join(pending["scopes"])
        if (
            data.get("error")
            or not isinstance(data.get("access_token"), str)
            or not data["access_token"]
        ):
            raise PermissionError("provider rejected enrollment")
        expiry = data.get("expires_in")
        if (
            data.get("token_type", "").lower() != "bearer"
            or type(expiry) is not int
            or not 0 < expiry <= 86400
            or not isinstance(data.get("scope"), str)
        ):
            raise PermissionError("invalid token contract")
        scopes = frozenset(data["scope"].split())
        if not scopes <= set(pending["scopes"]):
            raise PermissionError("unexpected provider scope expansion")
        account_id = pending.get("account_id")
        id_token = data.get("id_token")
        if nonce_digest is None and account_id and not id_token:
            # A bound refresh grant preserves the originally verified identity, never a new claim.
            prior_account = self.accounts.check(account_id, pending["generation"])
            tenant, subject = prior_account.tenant, prior_account.subject
        else:
            if not isinstance(id_token, str):
                raise PermissionError("verified OIDC identity token required")
            tenant, subject = self._identity(id_token, provider, nonce_digest, data["access_token"])
        if account_id:
            account = self.accounts.check(account_id, pending["generation"])
            if (account.provider, account.tenant, account.subject) != (
                provider.provider,
                tenant,
                subject,
            ):
                raise PermissionError("account switching during authorization denied")
        else:
            account = self.accounts.add(
                provider.provider,
                tenant,
                subject,
                pending["alias"],
                identity_class=pending["identity_class"],
                verified=True,
            )
            expected = pending.get("account_epochs", {}).get(account.id)
            if expected is not None and expected != account.generation:
                raise PermissionError("account changed during enrollment")
        credential_ref, refresh_ref = secrets.token_hex(16), secrets.token_hex(16)
        previous = account.services.get(provider.service)
        previous_connection = next(
            (
                c
                for c in self.store.all("auth_broker_connection")
                if previous
                and c["credential_ref"] == previous.credential_ref
                and c["state"] in {"ready", "refreshing"}
            ),
            None,
        )
        if (
            not data.get("refresh_token")
            and previous_connection
            and previous_connection["refresh_ref"]
        ):
            data["refresh_token"] = self.vault.read(previous_connection["refresh_ref"]).value
        connection: dict[str, Any] = {
            "id": identifier,
            "provider_id": provider.id,
            "account_id": account.id,
            "credential_ref": credential_ref,
            "refresh_ref": refresh_ref,
            "state": "exchanging",
            "configuration": self._fingerprint(provider),
        }
        self.store.put("auth_broker_connection", identifier, connection)
        self.vault.put(
            data["access_token"], expires_at=self.clock() + expiry, reference=credential_ref
        )
        refresh = data.get("refresh_token")
        if refresh:
            if not isinstance(refresh, str):
                raise ValueError("invalid refresh contract")
            self.vault.put(refresh, reference=refresh_ref)
        else:
            connection["refresh_ref"] = ""
        account = self.accounts.bind(
            account.id,
            provider.service,
            CredentialRef(credential_ref),
            scopes,
            provider.audience,
            expires_at=self.clock() + expiry,
            expected_generation=account.generation,
        )
        connection.update(state="ready", generation=account.generation, scopes=sorted(scopes))
        pending["state"] = "authorized"
        with self.store.transaction():
            self.store.put("auth_broker_connection", identifier, connection)
            if nonce_digest is not None:
                self.store.put("auth_code_pending", identifier, pending)
        if previous:
            self.vault.delete(previous.credential_ref)
        if previous_connection and previous_connection["refresh_ref"]:
            self.vault.delete(previous_connection["refresh_ref"])
        return account

    def _fail_connection(self, identifier: str) -> None:
        try:
            connection = self.store.get("auth_broker_connection", identifier)
        except KeyError:
            return
        account = self.accounts.get(connection["account_id"])
        if any(b.credential_ref == connection["credential_ref"] for b in account.services.values()):
            self.accounts.disconnect(account.id)
        for key in ("credential_ref", "refresh_ref"):
            if connection.get(key):
                self.vault.delete(connection[key])
        connection["state"] = "blocked_reauthorization_required"
        self.store.put("auth_broker_connection", identifier, connection)

    def refresh(self, identifier: str, *, owner_authorized: bool) -> Account:
        if not owner_authorized:
            raise PermissionError("owner refresh authority required")
        with self.store.transaction():
            connection = self.store.get("auth_broker_connection", identifier)
            provider = self.providers[connection["provider_id"]]
            account = self.accounts.check(connection["account_id"], connection["generation"])
            if (
                connection["state"] != "ready"
                or not connection["refresh_ref"]
                or connection["configuration"] != self._fingerprint(provider)
            ):
                raise PermissionError("refresh unavailable")
            connection["state"] = "refreshing"
            self.store.put("auth_broker_connection", identifier, connection)
        pending = {
            "account_id": account.id,
            "generation": account.generation,
            "alias": account.alias,
            "identity_class": account.identity_class,
            "scopes": connection["scopes"],
            "id": identifier,
        }
        try:
            data = self.request(
                provider.token_endpoint,
                {
                    **self._token_fields(provider),
                    "grant_type": "refresh_token",
                    "refresh_token": self.vault.read(connection["refresh_ref"]).value,
                },
            )
            # Providers may omit a rotated refresh token; preserve it privately when omitted.
            if "refresh_token" not in data:
                data["refresh_token"] = self.vault.read(connection["refresh_ref"]).value
            account = self._accept(identifier, pending, provider, data, None)
            self.vault.delete(connection["refresh_ref"])
            return account
        except Exception:
            self.accounts.disconnect(account.id)
            self._fail_connection(identifier)
            self.vault.delete(connection["credential_ref"])
            self.vault.delete(connection["refresh_ref"])
            raise RuntimeError(
                "refresh rejected or interrupted; reauthorization required"
            ) from None

    def disconnect(self, account_id: str, *, owner_authorized: bool) -> Account:
        if not owner_authorized:
            raise PermissionError("owner disconnect authority required")
        account = self.accounts.disconnect(account_id)
        return self.finish_disconnect(account)

    def finish_disconnect(self, account: Account) -> Account:
        """Delete only references owned by the committed revocation snapshot, outside DB locks."""
        if account.status != "disconnected":
            raise PermissionError(
                "committed account revocation required before credential deletion"
            )
        current = self.accounts.get(account.id)
        if current.generation != account.generation or current.status != "disconnected":
            raise PermissionError("account changed after disconnect")
        connections = [
            c
            for c in self.store.all("auth_broker_connection")
            if c["account_id"] == account.id
            and c.get("generation", account.generation) < account.generation
        ]
        references = {binding.credential_ref for binding in account.services.values()}
        for connection in connections:
            references.update(
                ref for ref in (connection["credential_ref"], connection["refresh_ref"]) if ref
            )
        try:
            for connection in connections:
                connection["state"] = "deleting"
                self.store.put("auth_broker_connection", connection["id"], connection)
            for reference in references:
                self.vault.delete(reference)
                try:
                    self.vault.read(reference, allow_expired=True)
                except KeyError:
                    pass
                else:
                    raise OSError("local credential deletion could not be verified")
            for connection in connections:
                connection["state"] = "locally_deleted_remote_revocation_unknown"
                self.store.put("auth_broker_connection", connection["id"], connection)
        except (OSError, PermissionError, ValueError):
            self.accounts.credential_deletion(account.id, account.generation, "deletion_failed")
            raise OSError("local credential deletion failed; account remains disabled") from None
        self.accounts.credential_deletion(account.id, account.generation, "deleted")
        return self.accounts.get(account.id)
