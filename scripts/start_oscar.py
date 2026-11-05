"""Start the everyday Desktop with OSCAR's persistent, authenticated local Core.

Cloud inference is restricted to verified-free routes; local fallback is disabled.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from queue import Queue
from threading import Event, Thread

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import CloudHTTPServer
from oscar.connectors import ConnectorVerifier
from oscar.credential_loading import existing_provider_environment, import_missing_vault_bindings
from oscar.desktop import Desktop
from oscar.desktop_verify import DesktopVerifier
from oscar.grid import InternalSessionRuntime, Node, NodeRole, SessionHandle
from oscar.harness import Harness, ModelExecutor
from oscar.interactive_worker import InteractiveWorker
from oscar.machine import MachineScope, MachineVerifier
from oscar.mobile import MobileServer
from oscar.models import ModelRequest, RoutingPolicy
from oscar.policy import PersonalPolicy
from oscar.registry import Registry
from oscar.remote_grid import RemoteVerifier
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store
from oscar.transport import Dispatcher

ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[1]
)


def renew_local_execution(state: Path, node_id: str = "oscar-local-core") -> bool:
    """A trusted local restart may renew expiry, but never undo revocation."""
    if not state.is_file():
        return False
    store = Store(state)
    try:
        try:
            node = store.get("node", node_id)
            binding = store.get("core_execution", node_id)
            session = store.get("session", binding["session_id"])
        except KeyError:
            return False
        return bool(
            not node["revoked"]
            and not session["revoked"]
            and session.get("internal")
            and session["node_id"] == node_id
        )
    finally:
        store.close()


def desktop_session(h: Harness, worker_node: str | None = None) -> SessionHandle:
    """Local trusted enrollment; each launch replaces the old surface session."""
    scopes = (
        "heartbeat",
        "desktop:connect",
        "desktop:inspect",
        "desktop:text",
        "desktop:conversation:read",
        "desktop:conversation:retain",
        "models",
        "math",
        "memory:read",
        "files:write",
        *(f"control:{op}:{h.node_id}" for op in ("inspect", "approve", "cancel")),
    )
    node = "oscar-local-desktop"
    base_scopes = scopes
    if worker_node:
        scopes += (
            "files:read",
            "machine:host",
            "desktop:control",
            *(f"control:{op}:{worker_node}" for op in ("inspect", "approve", "cancel")),
        )
    try:
        existing = h.store.get("node", node)
    except KeyError:
        h.grid.register(Node(node, NodeRole.DESKTOP, scopes))
    else:
        # Migrate only the exact first everyday-launcher enrollment, never an
        # enrollment whose owner has narrowed or revoked its grants.
        if not existing["revoked"] and set(existing["scopes"]) == set(base_scopes) and worker_node:
            h.store.put("node", node, {**existing, "scopes": list(scopes)})
            existing = h.store.get("node", node)
        if existing["revoked"] or set(existing["scopes"]) != set(scopes):
            raise PermissionError("Desktop enrollment changed; inspect before restarting")
    with h.store.transaction():
        for previous in h.store.all("session"):
            if previous["node_id"] == node and not previous["revoked"]:
                h.store.put("session", previous["id"], {**previous, "revoked": True})
        return h.grid.pair(node, scopes, ttl=86400)


def mount_windows_worker(h: Harness, state: Path) -> InteractiveWorker:
    """Mount installed executors under Ask; no capture, clipboard or microphone grant."""
    node_id = "oscar-local-windows"
    scopes = (
        "heartbeat",
        "advertise",
        "execute",
        "cancel",
        "pause",
        "files:read",
        "files:write",
        "machine:host",
        "desktop:control",
    )
    try:
        existing = h.store.get("node", node_id)
    except KeyError:
        h.grid.register(Node(node_id, NodeRole.DESKTOP, scopes))
    else:
        if existing["revoked"] or set(existing["scopes"]) != set(scopes):
            raise PermissionError("Windows Worker enrollment changed; inspect before restarting")
    session = h.grid.pair(
        node_id,
        scopes,
        internal=True,
        reenroll=renew_local_execution(state, node_id),
    )
    python = shutil.which("python.exe") if getattr(sys, "frozen", False) else sys.executable
    executables = [python] if python else []
    for command in ("git.exe", "pwsh.exe", "powershell.exe"):
        executable = shutil.which(command)
        if executable:
            executables.append(executable)
    worker = InteractiveWorker(
        h.store,
        h.grid,
        session,
        MachineScope(h.files.root, True, tuple(dict.fromkeys(executables))),
        PersonalPolicy(h.store),
        desktop=True,
    )
    capabilities = worker.capabilities()
    h.grid.advertise(session, capabilities)
    dispatcher = Dispatcher(h.store, h.grid, node_id, worker.executors())
    h.executive.targets = {**h.executive.targets, node_id: (dispatcher, session)}
    verifier = h.runtime.verifier
    if isinstance(verifier, RemoteVerifier):
        verifier = verifier.original
    if not isinstance(verifier, ConnectorVerifier):
        raise RuntimeError("Canonical connector verifier composition changed")
    verifier.base = MachineVerifier(worker.files)
    if worker.desktop:
        verifier.base = DesktopVerifier(verifier.base, worker.desktop)
    maintenance = InternalSessionRuntime(h.grid, session)
    maintenance.thread.start()
    h.store.close_callbacks.insert(0, maintenance.close)
    return worker


def run_desktop(core: Desktop, session: SessionHandle, executable: Path) -> None:
    # Credentials travel only over the anonymous stdin pipe, never arguments/files.
    with MobileServer(core) as server:
        process = subprocess.Popen(
            [str(executable), "--bootstrap-stdin", "--interaction"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines: Queue[str] = Queue()
        assert process.stdout is not None and process.stdin is not None

        def collect() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                lines.put(line)
            lines.put("")

        reader = Thread(target=collect, daemon=True)
        reader.start()
        try:
            public = json.loads(lines.get(timeout=90))
            if set(public) != {"owner_public_key"}:
                raise RuntimeError("Desktop enrollment protocol rejected")
            core.register_owner_key(session, public["owner_public_key"], owner_authorized=True)
            process.stdin.write(
                json.dumps(
                    {
                        "url": server.url,
                        "node": session.node_id,
                        "session": session.id,
                        "token": session.token,
                        "reference": False,
                        "reference_target": None,
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            process.stdin.close()
            print(
                "OSCAR Core online. Conversation history is retained locally. "
                "Quit from the tray to stop."
            )
            process.wait()
            if process.returncode:
                raise RuntimeError("Desktop exited unsuccessfully")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument(
        "--grid-port", type=int, default=8765, help="Authenticated loopback Grid port"
    )
    parser.add_argument("--provider", help="Optional cloud provider pin")
    parser.add_argument(
        "--headless", action="store_true", help="Run Core and authenticated Grid without Desktop"
    )
    parser.add_argument(
        "--stop-on-stdin-close",
        action="store_true",
        help="With --headless, stop cleanly when the parent closes its stdin pipe",
    )
    parser.add_argument(
        "--confirm-free-plan",
        action="append",
        choices=("google", "groq"),
        default=[],
        help="Confirm this account has billing disabled and uses its Free plan (24 hours)",
    )
    parser.add_argument("--model", help="Cloud model ID; use with --provider")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check verified-free cloud inference without opening Desktop",
    )
    args = parser.parse_args()
    if args.stop_on_stdin_close and not args.headless:
        parser.error("--stop-on-stdin-close requires --headless")
    if not 1 <= args.grid_port <= 65535:
        parser.error("Grid port must be between 1 and 65535")
    data = args.data_dir or Path(os.environ["LOCALAPPDATA"]) / "DawnlightLabs/OSCAR"
    executable = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    if not args.check and not args.headless and not executable.is_file():
        parser.error("Build Desktop first: python -m scripts.build_desktop")
    data.mkdir(parents=True, exist_ok=True)
    registry = Registry.load(ROOT / "config/development-models.json")
    credentials = existing_provider_environment(ROOT / ".env.local", registry.providers.values())
    cloud_providers = frozenset(
        p.id for p in registry.providers.values() if not p.local and p.enabled
    )
    if args.provider and args.provider not in cloud_providers:
        parser.error("Choose a configured cloud provider; local inference is disabled")
    template = ModelRequest.from_config(
        {
            "mode": "free_first",
            "pinned_provider": args.provider,
            "pinned_model": args.model,
            "max_output_tokens": 2048,
        }
    )
    policy = RoutingPolicy(
        require_free=True,
        allowed_providers=cloud_providers,
        private_providers=cloud_providers,
        timeout_seconds=120,
        max_paid_cost=0,
    )
    configuration = CloudConfig(
        core_id="oscar-local-core",
        data_dir=data,
        manifest=ROOT / "config/development-models.json",
        secret_dir=data.parent / "OSCAR-vault",
        listen_host="127.0.0.1",
        listen_port=args.grid_port,
        ingress="loopback",
        allowed_hosts=("127.0.0.1",),
        model_request=template,
        model_timeout_seconds=120,
    )
    with closing(
        CloudCore(
            configuration,
            initialize=True,
            adopt_existing=True,
            renew_execution=renew_local_execution(data / "core.sqlite"),
            start_services=False,
            vault=WindowsCredentialStore(),
            credential_environ=credentials,
        )
    ) as coordinator:
        h = coordinator.harness
        assert h.runtime.setup is not None
        import_missing_vault_bindings(h.runtime.setup, h.registry.providers.values(), credentials)
        for slot in h.pool.slots.values():
            if slot.provider in args.confirm_free_plan and slot.present:
                h.runtime.setup.confirm_free_plan(slot.id, owner_authorized=True)
        executor = h.dispatcher.executors["models.reason"]
        assert isinstance(executor, ModelExecutor)
        executor.policy = policy
        try:
            saved = h.store.get("desktop_model", "selection")["configuration"]
        except KeyError:
            saved = None
        if saved and not args.provider and not args.model:
            if saved.get("mode") != "local" and saved.get("pinned_provider") in cloud_providers | {
                None
            }:
                template = ModelRequest.from_config(saved)
        executor.template = template
        h.router.refresh(template, policy)
        routes = h.router.rank(template, policy)
        if args.check:
            h.start()
            if not routes:
                raise RuntimeError(
                    "No verified-free cloud model available; no paid/local fallback used"
                )
            result = h.router.execute(
                replace(template, prompt="Reply with a short greeting.", max_output_tokens=64),
                policy,
            )
            if not result.response.text.strip():
                raise RuntimeError("Cloud model returned no answer")
            print("Verified-free cloud inference completed through OSCAR Model Router.")
            print("Provider:", result.route.provider, "Model:", result.route.model)
            return 0
        if not routes:
            print("Core ready; no verified-free model is currently available. Check model setup.")
        worker = mount_windows_worker(h, data / "core.sqlite")
        h.start()
        if args.headless:
            grid_server = CloudHTTPServer(coordinator)
            grid_server.start()
            try:
                print("OSCAR Core and authenticated loopback Grid ready.", flush=True)
                if args.stop_on_stdin_close:
                    while sys.stdin.buffer.read(1):
                        pass
                else:
                    Event().wait()
            except KeyboardInterrupt:
                pass
            finally:
                grid_server.close()
            return 0
        session = desktop_session(h, worker.session.node_id)
        core = Desktop(
            h.runtime,
            PersonalPolicy(h.store),
            h.executive.targets,
            native_catalogs={
                worker.session.node_id: {
                    "executables": worker.scope.allowed_executables,
                    "applications": worker.desktop.catalog() if worker.desktop else [],
                }
            },
            worker_outputs={worker.session.node_id: worker.outputs},
        )
        grid_server = CloudHTTPServer(coordinator)
        grid_server.start()
        try:
            run_desktop(core, session, executable)
        finally:
            grid_server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
