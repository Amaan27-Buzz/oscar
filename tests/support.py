from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.capabilities import FileExecutor, ScopedFiles, Verifier, addition_executor
from oscar.contracts import Action, Capability, TaskState, new_id, record
from oscar.credentials import CredentialPool
from oscar.grid import Grid, Node, NodeRole
from oscar.models import Funding, ModelRequest, ModelSpec, ProviderResponse, ProviderSpec
from oscar.registry import Registry
from oscar.router import Router
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import Dispatcher, action_envelope


class Clock:
    def __init__(self):
        self.now = time()

    def __call__(self):
        return self.now


class Rig:
    def __init__(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state.sqlite")
        self.clock = Clock()
        self.grid = Grid(self.store, self.clock)
        self.files = ScopedFiles(self.root / "workspace")
        self.runtime = Runtime(self.store, self.grid, Verifier(self.files))
        self.scopes = (
            "execute",
            "heartbeat",
            "advertise",
            "files:write",
            "math",
            "models",
            "cancel",
        )
        self.grid.register(Node("test-node", NodeRole.DESKTOP, self.scopes))
        self.session = self.grid.pair("test-node", self.scopes)
        self.caps = [
            Capability(
                "file",
                "File",
                "Exact file",
                "deterministic",
                "test-node",
                ("files:write",),
                "file_write",
                "file",
            ),
            Capability(
                "math",
                "Add",
                "Integer addition",
                "deterministic",
                "test-node",
                ("math",),
                "addition",
                "integer",
            ),
            Capability(
                "model",
                "Reason",
                "Test model contract",
                "model",
                "test-node",
                ("models",),
                "model_reasoning",
                "text",
            ),
        ]
        self.grid.advertise(self.session, self.caps)
        self.dispatcher = Dispatcher(
            self.store,
            self.grid,
            "test-node",
            {"file": FileExecutor(self.files), "math": addition_executor},
        )
        self.transports = {"test-node": (self.dispatcher, self.session)}

    def file_task(self, path="proof.txt", content="exact bytes\n"):
        from oscar.jev import Intent

        return self.runtime.create(Intent("Write file", "file_write", path, content))

    def leased_action(self):
        task = self.file_task()
        self.store.transition(task.id, TaskState.EXECUTING)
        lease = self.grid.lease(task.id, "test-node")
        self.store.transition(task.id, TaskState.AWAITING_RESULT)
        action = Action(
            new_id(),
            task.id,
            task.correlation_id,
            "file",
            {"path": "proof.txt", "content": "exact bytes\n"},
            task.id,
            "owner",
        )
        self.store.put("action", action.id, record(action))
        return task, action, action_envelope(action, self.session, lease, self.clock)

    def close(self):
        self.store.close()
        self.temp.cleanup()


class ScriptedAdapter:
    def __init__(self, steps=None):
        self.steps = list(steps or [])
        self.calls = []

    def generate(self, provider, model, secret, request, timeout, check_cancel, sink=None):
        self.calls.append((provider.id, model))
        check_cancel()
        step = (
            self.steps.pop(0) if self.steps else ProviderResponse("reported synthetic answer", 2, 3)
        )
        if callable(step):
            return step(check_cancel, sink)
        if isinstance(step, Exception):
            raise step
        return step


class RouterRig:
    def __init__(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "router.sqlite")
        self.clock = Clock()
        providers = [
            ProviderSpec(
                "plentiful",
                "test",
                "https://plentiful.invalid",
                {"plentiful-1": "FIXTURE_A", "plentiful-2": "FIXTURE_B"},
            ),
            ProviderSpec("scarce", "test", "https://scarce.invalid", {"scarce-1": "FIXTURE_C"}),
        ]
        models = [
            ModelSpec(
                "plentiful",
                "small",
                frozenset({"text", "structured"}),
                2,
                {"extraction": 1, "reasoning": 0.4},
                8192,
                1024,
                Funding.FREE,
                latency_ms=50,
                reliability=0.9,
                provenance="synthetic contract fixture",
            ),
            ModelSpec(
                "scarce",
                "strong",
                frozenset({"text", "structured", "rare"}),
                5,
                {"extraction": 0.5, "reasoning": 1},
                8192,
                1024,
                Funding.FREE,
                latency_ms=1000,
                reliability=0.95,
                provenance="synthetic contract fixture",
            ),
        ]
        self.registry = Registry(providers, models)
        self.pool = CredentialPool(
            providers,
            {
                "FIXTURE_A": "synthetic-value-alpha",
                "FIXTURE_B": "synthetic-value-beta",
                "FIXTURE_C": "synthetic-value-gamma",
            },
            self.store,
            self.clock,
        )
        for slot in self.pool.slots.values():
            slot.remaining_requests = 1000 if slot.provider == "plentiful" else 2
            slot.quota_observed_at = self.clock()
        self.adapter = ScriptedAdapter()
        self.router = Router(
            self.registry, self.pool, {"test": self.adapter}, self.store, self.clock
        )
        self.request = ModelRequest(
            new_id(), new_id(), "private prompt fixture", task_class="extraction", min_quality=2
        )

    def close(self):
        self.store.close()
        self.temp.cleanup()
