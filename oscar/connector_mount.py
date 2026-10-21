"""Explicit Connector Fabric executor enrollment in the existing Core Grid/runtime."""

import hashlib
import sqlite3
from collections.abc import Callable
from dataclasses import replace
from functools import cache
from pathlib import Path
from threading import Event, RLock, Thread
from typing import TYPE_CHECKING

from .capabilities import Executor
from .contracts import Action, Capability
from .executive import confirmation_digest
from .grid import Node, NodeRole
from .storage import StateConflict
from .transport import Dispatcher

if TYPE_CHECKING:
    from .connectors import ConnectorManifest
    from .harness import Harness


@cache
def account_manifests() -> tuple["ConnectorManifest", ...]:
    from .connector_providers import load_google, microsoft_manifest

    return (
        *load_google(Path(__file__).resolve().parents[1] / "config/google-connectors.json"),
        microsoft_manifest(),
    )


def project_accounts(harness: "Harness") -> None:
    """Rebuild executor bindings from current verified account metadata, never cached grants."""
    from .connectors import ConnectorInstance, CredentialRef

    manifests = account_manifests()
    projected = {}
    with harness.store.lock:
        for account in harness.accounts.list_accounts():
            if account.status != "connected":
                continue
            for manifest in manifests:
                binding = account.services.get(manifest.id)
                if account.provider != manifest.provider or binding is None:
                    continue
                if binding.expires_at is not None and binding.expires_at <= harness.grid.clock():
                    continue
                identifier = (
                    "native-account-"
                    + hashlib.sha256((account.id + ":" + manifest.id).encode()).hexdigest()[:24]
                )
                projected[identifier] = ConnectorInstance(
                    identifier,
                    manifest,
                    CredentialRef(binding.credential_ref),
                    frozenset(binding.scopes),
                    account_id=account.id,
                    account_generation=account.generation,
                    account_audience=binding.audience,
                )
        for identifier in harness._account_instances:
            harness.connectors.instances.pop(identifier, None)
        harness.connectors.instances.update(projected)
        harness._account_instances = set(projected)


class ConnectorMount:
    def __init__(
        self,
        harness: "Harness",
        node_id: str,
        grants: tuple[str, ...],
        *,
        owner_authorized: bool,
        confirmed: Callable[[Action], bool] | None = None,
    ):
        from .connectors import RiskLevel

        if owner_authorized is not True:
            raise PermissionError("explicit owner connector enrollment required")
        if node_id == harness.node_id or not node_id or len(node_id) > 100:
            raise ValueError("a distinct bounded connector executor node is required")
        allowed = {"connectors:" + risk.value for risk in RiskLevel}
        if not grants or not set(grants) <= allowed or len(grants) != len(set(grants)):
            raise ValueError("explicit connector permission ceiling required")
        self.harness, self.node_id = harness, node_id
        self.grants = frozenset(grants)
        self.confirmed = confirmed or self._confirmed
        self.lock, self.stop = RLock(), Event()
        scopes = ("heartbeat", "advertise", "execute", "cancel", *grants)
        try:
            previous = harness.store.get("node", node_id)
        except KeyError:
            harness.grid.register(Node(node_id, NodeRole.CLOUD, scopes))
        else:
            if not set(scopes) <= set(previous["scopes"]):
                raise PermissionError("persisted connector scope cannot silently expand")
        self.session = harness.grid.pair(node_id, scopes, internal=True, reenroll=True)
        self.dispatcher = Dispatcher(harness.store, harness.grid, node_id, {})
        self._advertised: list[Capability] | None = None
        self.refresh()
        harness.executive.targets = {
            **harness.executive.targets,
            node_id: (self.dispatcher, self.session),
        }
        self.thread = Thread(target=self._run, name="oscar-connector-catalog", daemon=True)
        harness.store.close_callbacks.insert(0, self.close)
        self.thread.start()

    def _confirmed(self, action: Action) -> bool:
        from .authority import delegated_confirmation
        from .contracts import record

        capability = next(
            (cap for cap in self._advertised or [] if cap.id == action.capability_id), None
        )
        if capability is not None and delegated_confirmation(
            self.harness.store, self.harness.grid, action.task_id, record(capability), self.session
        ):
            return True
        try:
            receipt = self.harness.store.get("executive_confirmation", action.task_id)
            return bool(
                self.harness.store.get("action", action.id)["task_id"] == action.task_id
                and receipt["digest"] == confirmation_digest(self.harness.store, action.task_id)
                and receipt["expires_at"] > self.harness.grid.clock()
            )
        except (KeyError, StateConflict):
            return False

    def refresh(self) -> list[Capability]:
        with self.lock:
            if self.stop.is_set():
                return []
            project_accounts(self.harness)
            caps = [
                replace(cap, input_kind=cap.id)
                for cap in self.harness.connectors.capabilities(self.node_id)
                if set(cap.permissions) <= self.grants
            ]
            executors: dict[str, Executor] = {}
            for cap in caps:
                instance_id, name = cap.id.split(":", 1)
                executors[cap.id] = self.harness.connectors.executor(
                    instance_id,
                    name,
                    self.grants,
                    confirmed=self.confirmed,
                )
            self.dispatcher.executors = executors
            if caps != self._advertised:
                self.harness.grid.advertise(self.session, caps)
                self._advertised = caps
            return caps

    def capability(self, name: str, *, account_id: str | None = None) -> Capability:
        candidates = []
        for cap in self.refresh():
            if cap.name != name and cap.id != name:
                continue
            instance_id = cap.id.split(":", 1)[0]
            instance = self.harness.connectors.instances[instance_id]
            session = self.harness.plugins.sessions.get(instance_id)
            bound_account = session.config.account_id if session else instance.account_id
            if account_id is None or account_id == bound_account:
                candidates.append(cap)
        if len(candidates) != 1:
            raise ValueError("connector/account selection is ambiguous or unavailable")
        return candidates[0]

    def _run(self) -> None:
        while not self.stop.wait(0.5):
            try:
                self.harness.grid.maintain_internal(self.session)
                self.refresh()
            except (PermissionError, KeyError):
                return
            except (sqlite3.Error, OSError, StateConflict):
                continue

    def close(self) -> None:
        if self.stop.is_set():
            return
        self.stop.set()
        if self.thread.ident is not None:
            self.thread.join(timeout=6)
        if self.thread.is_alive():
            raise StateConflict("connector catalog maintenance did not stop")
        with self.lock:
            self.dispatcher.executors.clear()
            try:
                self.harness.grid.advertise(self.session, [])
            except (KeyError, PermissionError):
                pass
            self.harness.executive.targets = {
                node: target
                for node, target in self.harness.executive.targets.items()
                if target[0] is not self.dispatcher
            }
