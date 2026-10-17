"""Developer composition root; reference roles are not physical-device availability claims."""

from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from time import time
from typing import Any

from .capabilities import Cancellation, FileExecutor, ScopedFiles, Verifier, addition_executor
from .contracts import Action, Capability, Result, new_id
from .credentials import CredentialPool
from .discovery import HTTPDiscovery
from .event_archive import EventArchive
from .executive import Executive
from .grid import Grid, InternalSessionRuntime, Node, NodeRole
from .memory_fabric import MemoryFabric
from .models import Mode, ModelRequest, ProviderError, RoutingPolicy
from .oauth_device import Vault
from .presence import PresenceRuntime
from .providers import HTTPAdapter
from .registry import Registry
from .retrieval import ProviderInventorySource, RetrievalExecutor
from .router import Router, RouteUnavailable
from .runtime import Runtime
from .search import TavilySource
from .setup_runtime import SetupRuntime
from .storage import StateConflict, Store
from .transport import Dispatcher
from .world_runtime import WorldRuntime


class ModelExecutor:
    def __init__(self, router: Router, template: ModelRequest, policy: RoutingPolicy):
        self.router, self.template, self.policy = router, template, policy

    def __call__(self, action: Action, cancellation: Cancellation) -> Result:
        request = replace(
            self.template,
            task_id=action.task_id,
            correlation_id=action.correlation_id,
            prompt=action.parameters["prompt"],
            mode=Mode.PRIVATE if action.parameters.get("mode") == "private" else self.template.mode,
        )
        try:
            routed = self.router.execute(request, self.policy, cancellation.check)
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                action.capability_id,
                True,
                value=routed.response.text,
            )
        except RouteUnavailable:
            error = "route_unavailable"
        except ProviderError as failure:
            error = failure.category.value
        return Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            False,
            error=error,
        )


class Harness:
    def __init__(
        self,
        state: Path,
        workspace: Path,
        manifest: Path,
        model_request: ModelRequest | None = None,
        *,
        clock: Callable[[], float] = time,
        execution_enrollment_authorized: bool = False,
        node_id: str = "reference-cloud",
        credential_environ: Mapping[str, str] | None = None,
        vault: Vault | None = None,
        start_services: bool = True,
    ):
        self.store = Store(state)
        self.grid = Grid(self.store, clock)
        self.files = ScopedFiles(workspace)
        self.archive = EventArchive(state.with_suffix(".archive.sqlite"))
        self.runtime = Runtime(
            self.store, self.grid, Verifier(self.files), memory=MemoryFabric(self.archive)
        )
        self.registry = Registry.load(manifest, self.store)
        self.pool = CredentialPool(
            list(self.registry.providers.values()), credential_environ, store=self.store
        )
        self.adapters = {kind: HTTPAdapter(kind) for kind in {"openai", "google", "ollama"}}
        self.router = Router(
            self.registry, self.pool, self.adapters, self.store, discovery=HTTPDiscovery()
        )
        self.search = TavilySource(self.store, credential_environ, redact=self.pool.redact)
        self.runtime.on_verification = self.router.observe_verification
        self.node_id = node_id
        scopes = ("heartbeat", "advertise", "execute", "files:write", "math", "models", "cancel")
        try:
            self.store.get("node", self.node_id)
        except KeyError:
            self.grid.register(Node(self.node_id, NodeRole.CLOUD, scopes))
        try:
            self.session = self.grid.pair(
                self.node_id, scopes, internal=True, reenroll=execution_enrollment_authorized
            )
        except BaseException:
            self.archive.close()
            self.store.close()
            raise
        self.execution_session = InternalSessionRuntime(self.grid, self.session)
        capabilities = [
            Capability(
                "sources.retrieve",
                "Live retrieval",
                "Provider-native inventories and replaceable public-web retrieval",
                "retrieval",
                self.node_id,
                ("models",),
                "live_source",
                "evidence",
            ),
            Capability(
                "files.write",
                "Write exact file",
                "Scoped exact-byte file creation",
                "deterministic",
                self.node_id,
                ("files:write",),
                "file_write",
                "file",
            ),
            Capability(
                "math.add",
                "Integer addition",
                "Bounded positive integer addition",
                "deterministic",
                self.node_id,
                ("math",),
                "addition",
                "integer",
            ),
            Capability(
                "models.reason",
                "Reason",
                "Native adaptive model route",
                "model",
                self.node_id,
                ("models",),
                "model_reasoning",
                "text",
            ),
        ]
        self.grid.advertise(self.session, capabilities)
        template = model_request or ModelRequest(new_id(), new_id(), "")
        self.dispatcher = Dispatcher(
            self.store,
            self.grid,
            self.node_id,
            {
                "files.write": FileExecutor(self.files),
                "math.add": addition_executor,
                "models.reason": ModelExecutor(self.router, template, RoutingPolicy()),
                "sources.retrieve": RetrievalExecutor(
                    self.router, (ProviderInventorySource(self.router), self.search)
                ),
            },
        )
        self.world = WorldRuntime(self.runtime, self.files)
        self.runtime.world = self.world
        self.runtime.setup = SetupRuntime(self.runtime, self.pool, vault)
        self.runtime.presence = PresenceRuntime(self.runtime)
        self.executive = Executive(self.runtime, {self.node_id: (self.dispatcher, self.session)})
        self.runtime.executive = self.executive
        self.store.close_callbacks.append(self.close_services)
        if start_services:
            self.start()

    def start(self) -> None:
        if self.execution_session.thread.ident is not None:
            raise StateConflict("Core services already started")
        try:
            self.execution_session.thread.start()
            self.world.start()
            self.executive.start()
        except BaseException:
            self.close()
            raise

    def close_services(self) -> None:
        self.executive.close()
        if self.execution_session.thread.ident is not None:
            self.execution_session.close()
        self.world.close()
        self.archive.close()

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "Harness":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
