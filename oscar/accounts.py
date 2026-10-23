"""Identity and account metadata in the canonical Store; credentials stay in the vault.

Only trusted enrollment adapters may add verified provider identities or bind secrets.
Aliases and defaults express preferences, never provider authority or security roles.
"""

import math
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from time import time

from .connectors import CredentialRef
from .contracts import new_id
from .storage import Store


@dataclass(frozen=True)
class OperationalIdentity:
    id: str
    owner_id: str
    display_name: str = "OSCAR"
    operational_email: str | None = None
    audit_identity: str = ""
    status: str = "active"
    recovery_state: str = "owner_recovery_required"
    owned_resources: tuple[str, ...] = ()


@dataclass(frozen=True)
class ServiceBinding:
    credential_ref: str
    audience: str
    scopes: tuple[str, ...]
    expires_at: float | None = None
    denied_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class Account:
    id: str
    provider: str
    tenant: str
    subject: str
    alias: str
    identity_class: str
    owner_id: str
    generation: int = 1
    status: str = "connected"
    services: dict[str, ServiceBinding] = field(default_factory=dict)
    group: str = ""
    browser_profile_id: str = ""
    remote_revocation: str = "UNKNOWN"
    local_credentials: str = "not_configured"


class AccountRegistry:
    """A Connector/Auth Fabric metadata store, not a second capability registry."""

    def __init__(self, store: Store, clock: Callable[[], float] = time):
        self.store, self.clock = store, clock

    @contextmanager
    def _mutation(self) -> Iterator[None]:
        # Signed native changes compose atomically with review consumption in the same Store.
        with self.store.lock:
            if self.store.db.in_transaction:
                yield
            else:
                with self.store.transaction():
                    yield

    def operational_identity(self, owner_id: str | None = None) -> OperationalIdentity:
        if owner_id is not None:
            self._text(owner_id)
        with self._mutation():
            try:
                data = self.store.get("operational_identity", "oscar")
            except KeyError:
                identity = OperationalIdentity(
                    new_id(), owner_id or "owner", audit_identity=new_id()
                )
                self.store.put("operational_identity", "oscar", asdict(identity))
                return identity
        data["owned_resources"] = tuple(data["owned_resources"])
        identity = OperationalIdentity(**data)
        if owner_id is not None and identity.owner_id != owner_id:
            raise PermissionError("operational identity owner mismatch")
        return identity

    @staticmethod
    def _text(value: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > 500:
            raise ValueError("bounded nonempty account metadata required")
        if any(ord(c) < 32 for c in value):
            raise ValueError("account metadata cannot contain control characters")
        return value

    def _save(self, account: Account) -> Account:
        self.store.put("connected_account", account.id, asdict(account))
        return account

    def get(self, account_id: str) -> Account:
        data = self.store.get("connected_account", account_id)
        data["services"] = {
            key: ServiceBinding(
                **{
                    **value,
                    "scopes": tuple(value["scopes"]),
                    "denied_capabilities": tuple(value["denied_capabilities"]),
                }
            )
            for key, value in data["services"].items()
        }
        return Account(**data)

    def list_accounts(self) -> list[Account]:
        return [self.get(data["id"]) for data in self.store.all("connected_account")]

    def add(
        self,
        provider: str,
        tenant: str,
        subject: str,
        alias: str,
        *,
        verified: bool,
        identity_class: str = "owner-delegated",
        owner_id: str | None = None,
        group: str = "",
    ) -> Account:
        if not verified:
            raise PermissionError("verified provider identity required")
        owner_id = owner_id or self.operational_identity().owner_id
        provider = self._text(provider).casefold()
        for value in (tenant, subject, alias, owner_id):
            self._text(value)
        if identity_class not in {"owner-delegated", "oscar-owned", "service", "workload"}:
            raise ValueError("unsupported account identity class")
        if identity_class != "owner-delegated":
            self.operational_identity(owner_id)
        with self._mutation():
            for existing in self.list_accounts():
                if (existing.provider, existing.tenant, existing.subject) == (
                    provider,
                    tenant,
                    subject,
                ):
                    if existing.owner_id != owner_id or existing.identity_class != identity_class:
                        raise PermissionError("provider identity already bound to another identity")
                    return existing
            return self._save(
                Account(
                    new_id(),
                    provider,
                    tenant,
                    subject,
                    alias,
                    identity_class,
                    owner_id,
                    group=group,
                    browser_profile_id=new_id(),
                )
            )

    def add_resource_grant(self, issuer: str, resource: str, alias: str) -> Account:
        """Trusted OAuth adapter only: resource authority asserts no provider person identity."""
        for value in (issuer, resource, alias):
            self._text(value)
        with self._mutation():
            return self._save(
                Account(
                    new_id(),
                    "mcp-resource",
                    issuer,
                    new_id(),
                    alias,
                    "resource-grant",
                    self.operational_identity().owner_id,
                )
            )

    def bind(
        self,
        account_id: str,
        service: str,
        credential: CredentialRef,
        scopes: Iterable[str],
        audience: str,
        *,
        expires_at: float | None = None,
        denied_capabilities: Iterable[str] = (),
        expected_generation: int | None = None,
    ) -> Account:
        self._text(service)
        self._text(audience)
        scopes = tuple(sorted({self._text(s) for s in scopes}))
        denied = tuple(sorted({self._text(s) for s in denied_capabilities}))
        if expires_at is not None and (not math.isfinite(expires_at) or expires_at <= self.clock()):
            raise ValueError("credential expiry must be in the future")
        with self._mutation():
            account = self.get(account_id)
            if expected_generation is not None and account.generation != expected_generation:
                raise PermissionError("account changed during enrollment")
            # A reference is bound once to an account/service, even after local removal.
            try:
                owner = self.store.get("account_credential_owner", credential.id)
                if owner != {"account_id": account_id, "service": service}:
                    raise PermissionError("cross-account credential binding denied")
            except KeyError:
                self.store.put(
                    "account_credential_owner",
                    credential.id,
                    {"account_id": account_id, "service": service},
                )
            services = {
                **account.services,
                service: ServiceBinding(credential.id, audience, scopes, expires_at, denied),
            }
            return self._save(
                replace(
                    account,
                    services=services,
                    status="connected",
                    local_credentials="present",
                    generation=account.generation + 1,
                )
            )

    def rename(self, account_id: str, alias: str) -> Account:
        self._text(alias)
        with self._mutation():
            return self._save(replace(self.get(account_id), alias=alias))

    def set_default(self, account_id: str, service: str) -> None:
        with self._mutation():
            account = self.get(account_id)
            self.check(account.id, account.generation, service=service)
            self.store.put("account_default", account.provider + ":" + service, {"id": account.id})

    def check(
        self,
        account_id: str,
        generation: int,
        *,
        service: str | None = None,
        provider: str | None = None,
        audience: str | None = None,
        scopes: Iterable[str] = (),
        capability: str | None = None,
        credential: CredentialRef | None = None,
    ) -> Account:
        account = self.get(account_id)
        if account.status != "connected" or account.generation != generation:
            raise PermissionError("account unavailable or generation revoked")
        if provider is not None and account.provider != provider.casefold():
            raise PermissionError("provider identity mismatch")
        if service is not None:
            binding = account.services.get(service)
            if (
                binding is None
                or binding.expires_at is not None
                and binding.expires_at <= self.clock()
            ):
                raise PermissionError("service credential missing or expired")
            if audience is not None and audience != binding.audience:
                raise PermissionError("credential audience mismatch")
            if credential is not None and credential.id != binding.credential_ref:
                raise PermissionError("cross-account credential denied")
            if not set(scopes) <= set(binding.scopes):
                raise PermissionError("account scope missing")
            if capability in binding.denied_capabilities:
                raise PermissionError("organization prohibits capability")
        return account

    def select(
        self,
        provider: str,
        service: str,
        *,
        scopes: Iterable[str] = (),
        account_id: str | None = None,
        alias: str | None = None,
        tenant: str | None = None,
        identity_class: str | None = None,
    ) -> Account:
        candidates = []
        for account in self.list_accounts():
            if (
                account.provider != provider.casefold()
                or account_id is not None
                and account.id != account_id
                or alias is not None
                and account.alias != alias
                or tenant is not None
                and account.tenant != tenant
                or identity_class is not None
                and account.identity_class != identity_class
            ):
                continue
            try:
                self.check(account.id, account.generation, service=service, scopes=scopes)
            except PermissionError:
                continue
            candidates.append(account)
        if not account_id and not alias and len(candidates) > 1:
            try:
                default = self.store.get("account_default", provider.casefold() + ":" + service)
                candidates = [a for a in candidates if a.id == default["id"]]
            except KeyError:
                pass
        if len(candidates) != 1:
            raise PermissionError(
                "account selection ambiguous" if candidates else "account unavailable"
            )
        return candidates[0]

    def withdraw_scopes(self, account_id: str, service: str, scopes: Iterable[str]) -> Account:
        with self._mutation():
            account = self.get(account_id)
            binding = account.services[service]
            services = {
                **account.services,
                service: replace(binding, scopes=tuple(sorted(set(binding.scopes) - set(scopes)))),
            }
            return self._save(
                replace(account, services=services, generation=account.generation + 1)
            )

    def disconnect(self, account_id: str) -> Account:
        # Keep the tombstone and bindings so old sessions/references can never be reassigned.
        with self._mutation():
            account = self.get(account_id)
            return self._save(
                replace(
                    account,
                    status="disconnected",
                    generation=account.generation + 1,
                    remote_revocation="UNKNOWN_OWNER_ACTION_REQUIRED",
                    local_credentials="deletion_pending",
                )
            )

    def credential_deletion(self, account_id: str, generation: int, state: str) -> None:
        if state not in {"deleted", "deletion_failed", "deletion_unavailable"}:
            raise ValueError("explicit local credential deletion state required")
        with self._mutation():
            account = self.get(account_id)
            if account.generation == generation and account.status == "disconnected":
                self._save(replace(account, local_credentials=state))

    def remote_revocation(self, account_id: str, generation: int, state: str) -> None:
        if state not in {
            "PROVIDER_ACCEPTED_NOT_INDEPENDENTLY_VERIFIED",
            "UNKNOWN_OWNER_ACTION_REQUIRED",
        }:
            raise ValueError("explicit provider revocation evidence required")
        with self._mutation():
            account = self.get(account_id)
            if account.generation == generation and account.status == "disconnected":
                self._save(replace(account, remote_revocation=state))
