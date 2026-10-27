"""Persistent deployment composition of OSCAR's existing authoritative Core."""

import argparse
import json
import os
import re
import signal
import sqlite3
import stat
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, RLock
from time import time
from typing import Any, TextIO

from .cloud_state import DataDirectoryLock, initialize_identity
from .contracts import TaskState, new_id
from .event_archive import MemoryWriter, SourceEvent
from .grid import Node, NodeRole, SessionHandle
from .harness import Harness
from .jev import Intent
from .local_memory import LocalMemory, LocalMemoryConfig
from .models import ModelRequest, RoutingPolicy
from .policy import PersonalPolicy
from .registry import Registry
from .secure_credentials import InjectedCredentialStore
from .storage import StateConflict


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def diagnostic(event: str, **fields: str | int | bool) -> None:
    # Callers supply categories and counters only, never exceptions or request content.
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


@dataclass(frozen=True)
class CloudConfig:
    core_id: str
    data_dir: Path
    manifest: Path
    secret_dir: Path
    listen_host: str
    listen_port: int
    ingress: str
    allowed_hosts: tuple[str, ...]
    provider_secrets: dict[str, str] = field(default_factory=dict)
    auth_config: Path | None = None
    credential_key_ref: str | None = None
    local_memory: LocalMemoryConfig | None = None
    model_request: ModelRequest | None = None
    model_timeout_seconds: float = 15

    @classmethod
    def load(cls, path: Path) -> "CloudConfig":
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
            raise ValueError("bounded regular production configuration required")
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)
        required = {
            "version",
            "environment",
            "core_id",
            "data_dir",
            "manifest",
            "secret_dir",
            "listen_host",
            "listen_port",
            "ingress",
            "allowed_hosts",
            "provider_secrets",
        }
        if (
            not isinstance(data, dict)
            or not required <= set(data)
            or set(data)
            - required
            - {
                "auth_config",
                "credential_key_ref",
                "local_memory",
                "model_request",
                "model_timeout_seconds",
            }
        ):
            raise ValueError("explicit versioned production configuration required")
        if type(data["version"]) is not int or data["version"] != 1:
            raise ValueError("unsupported cloud configuration version")
        if data["environment"] != "production":
            raise ValueError("production environment required")
        if (
            not isinstance(data["core_id"], str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,63}", data["core_id"])
            or "replace" in data["core_id"]
            or "example" in data["core_id"]
        ):
            raise ValueError("explicit stable deployment identity required")
        paths = []
        for key in ("data_dir", "manifest", "secret_dir"):
            if not isinstance(data[key], str) or not Path(data[key]).is_absolute():
                raise ValueError("absolute deployment paths required")
            target = Path(data[key])
            if any(p.is_symlink() for p in (target, *target.parents)):
                raise ValueError("deployment paths cannot traverse symlinks")
            paths.append(target)
        root, manifest, secret_dir = paths
        if root == secret_dir or root in secret_dir.parents or secret_dir in root.parents:
            raise ValueError("secrets must be separate from persistent state/backups")
        if root == manifest or root in manifest.parents:
            raise ValueError("configuration must be outside persistent state")
        if not isinstance(data["listen_host"], str) or data["listen_host"] not in {
            "127.0.0.1",
            "0.0.0.0",
        }:
            raise ValueError("explicit supported bind address required")
        if type(data["listen_port"]) is not int or not 1024 <= data["listen_port"] <= 65535:
            raise ValueError("unprivileged service port required")
        if (
            not isinstance(data["ingress"], str)
            or data["ingress"] not in {"loopback", "tls-proxy"}
            or (data["listen_host"] != "127.0.0.1" and data["ingress"] != "tls-proxy")
        ):
            raise ValueError("non-loopback Core requires isolated TLS proxy ingress")
        if data["ingress"] == "tls-proxy" and data["listen_port"] != 8080:
            raise ValueError(
                "TLS proxy deployment requires Core listen_port 8080 for ingress/health checks; "
                "alternative ports require isolated loopback ingress"
            )
        hosts = data["allowed_hosts"]
        if (
            not isinstance(hosts, list)
            or not 1 <= len(hosts) <= 8
            or any(
                not isinstance(h, str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,252}", h)
                or "example" in h
                or "replace" in h
                for h in hosts
            )
        ):
            raise ValueError("explicit allowed host names required")
        if "127.0.0.1" not in hosts:
            raise ValueError("loopback health-check host must be allowed")
        refs = data["provider_secrets"]
        if (
            not isinstance(refs, dict)
            or len(refs) > 32
            or any(
                not re.fullmatch(r"[A-Z][A-Z0-9_]{0,100}", k)
                or not isinstance(v, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", v)
                for k, v in refs.items()
            )
        ):
            raise ValueError("bounded opaque provider-secret references required")
        # Parse before touching authority or launching any lifecycle threads.
        if not manifest.is_file() or manifest.stat().st_size > 1_000_000:
            raise ValueError("provider manifest exceeds bound")
        Registry.load(manifest)
        auth_config = data.get("auth_config")
        key_ref = data.get("credential_key_ref")
        if (auth_config is None) != (key_ref is None):
            raise ValueError("OAuth configuration requires a separately mounted credential key")
        if auth_config is not None:
            from .auth_broker import load_providers

            if (
                not isinstance(auth_config, str)
                or not Path(auth_config).is_absolute()
                or root in Path(auth_config).parents
            ):
                raise ValueError("absolute OAuth configuration outside persistent state required")
            if not isinstance(key_ref, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", key_ref):
                raise ValueError("opaque credential key mount required")
            load_providers(Path(auth_config))
        model_policy = RoutingPolicy(timeout_seconds=data.get("model_timeout_seconds", 15))
        return cls(
            data["core_id"],
            root,
            manifest,
            secret_dir,
            data["listen_host"],
            data["listen_port"],
            data["ingress"],
            tuple(hosts),
            refs,
            Path(auth_config) if auth_config else None,
            key_ref,
            LocalMemoryConfig.parse(data["local_memory"]) if "local_memory" in data else None,
            ModelRequest.from_config(data["model_request"]) if "model_request" in data else None,
            model_policy.timeout_seconds,
        )


class CloudCore:
    def __init__(
        self,
        config: CloudConfig,
        *,
        initialize: bool = False,
        renew_execution: bool = False,
        start_services: bool = True,
    ):
        self.config, self.lock = config, RLock()
        self.directory_lock = DataDirectoryLock(config.data_dir)
        self.directory_lock.__enter__()
        self.core: Harness | None = None
        self.remote: Any = None
        self.closed = False
        try:
            initialize_identity(config.data_dir, config.core_id, initialize=initialize)
            vault = InjectedCredentialStore(config.secret_dir)
            account_vault: Any = vault
            if config.auth_config is not None:
                import base64

                from .encrypted_credentials import EncryptedCredentialStore

                if not config.credential_key_ref:
                    raise ValueError("separately mounted account credential key required")
                key = base64.b64decode(vault.read(config.credential_key_ref).value, validate=True)
                account_vault = EncryptedCredentialStore(
                    config.data_dir / "account-credentials", key, vault
                )
            credentials: dict[str, str] = {}
            for name, reference in config.provider_secrets.items():
                try:
                    credentials[name] = vault.read(reference).value
                except (KeyError, FileNotFoundError, PermissionError):
                    # Optional provider unavailability never takes canonical memory down.
                    pass
            self.core = Harness(
                config.data_dir / "core.sqlite",
                config.data_dir / "workspace",
                config.manifest,
                node_id=config.core_id,
                credential_environ=credentials,
                vault=account_vault,
                auth_config=config.auth_config,
                execution_enrollment_authorized=renew_execution,
                start_services=False,
                memory_config=config.local_memory,
                model_request=config.model_request,
                model_timeout_seconds=config.model_timeout_seconds,
            )
            pools = (
                (self.core.pool, list(self.core.registry.providers.values())),
                (self.core.search.pool, [self.core.search.provider]),
            )
            for pool, providers in pools:
                for provider in providers:
                    for slot, name in provider.credential_envs.items():
                        if name in config.provider_secrets and slot in pool.slots:
                            ref = config.provider_secrets[name]

                            def resolve(reference: str = ref) -> str:
                                return vault.read(reference).value

                            pool.bind_resolver(slot, resolve)
            # A restarted process cannot own its predecessor's in-flight local lease.
            self._recover()
            from .remote_grid import RemoteGrid

            self.remote = RemoteGrid(self)
            if start_services:
                self.core.start()
                if not self.ready():
                    raise StateConflict("Core lifecycle did not become ready")
        except BaseException:
            self.close()
            raise

    @property
    def harness(self) -> Harness:
        if self.core is None or self.closed:
            raise StateConflict("Core lifecycle is unavailable")
        return self.core

    def _recover(self) -> None:
        h = self.harness
        for row in h.store.all("task"):
            if (
                row["state"] in {TaskState.EXECUTING, TaskState.AWAITING_RESULT}
                and not row["lease_id"]
            ):
                h.store.transition(
                    row["id"],
                    TaskState.BLOCKED,
                    blocker="Core restarted before execution lease; inspect before retry",
                )
        for row in h.store.all("lease"):
            if row["active"] and row["node_id"] == h.node_id:
                h.grid.release(row["id"])
            if row["node_id"] != h.node_id:
                continue
            task = h.store.task(row["task_id"])
            if task.lease_id == row["id"] and task.state in {
                TaskState.EXECUTING,
                TaskState.AWAITING_RESULT,
                TaskState.RESULT_RECEIVED,
                TaskState.VERIFYING,
            }:
                h.store.transition(
                    task.id,
                    TaskState.UNKNOWN if task.state == TaskState.VERIFYING else TaskState.BLOCKED,
                    blocker="Core restarted; inspect before retry",
                )
        h.grid.reap()

    def ready(self) -> bool:
        h = self.harness
        try:
            with h.store.lock:
                h.store.db.execute("SELECT 1").fetchone()
            h.archive.db.execute("SELECT 1 FROM archive_fts LIMIT 1").fetchone()
            h.grid.authenticate(h.session, "execute")
        except (KeyError, PermissionError, sqlite3.Error):
            return False
        return bool(
            h.executive.thread
            and h.executive.thread.is_alive()
            and h.execution_session.thread.is_alive()
            and h.world.thread
            and h.world.thread.is_alive()
            and h.executive.health != "unavailable"
            and h.world.health != "unavailable"
        )

    def status(self) -> dict[str, Any]:
        h = self.harness
        ready = self.ready()
        return {
            "version": 1,
            "core_id": self.config.core_id,
            "ready": ready,
            "memory": h.memory.status()
            if isinstance(h.memory, LocalMemory)
            else {
                "canonical": "sqlite-wal-fts5",
                "semantic": "unavailable",
                "temporal": "unavailable",
                "reranker": "unavailable",
            },
            "capabilities": {
                "integer_addition": "available" if ready else "unavailable",
                "windows_uia": "unavailable",
                "powershell": "unavailable",
                "desktop_capture": "unavailable",
                "remote_workers": "available"
                if any(
                    n["role"] == NodeRole.DESKTOP and n["status"] == "online"
                    for n in h.grid.nodes()
                )
                else "unavailable",
            },
            "providers": "configured"
            if any(s.present for s in h.pool.slots.values())
            else "unavailable",
            "executive": h.executive.health,
        }

    def inspect_probe(self, session: SessionHandle, request_id: str) -> dict[str, Any]:
        h = self.harness
        row = h.store.get("cloud_probe", session.node_id + ":" + request_id)
        task = h.store.task(row["task_id"])
        try:
            event = h.archive.event(row["event_id"])
        except KeyError:
            raise StateConflict(
                "probe archive admission incomplete; retry the exact request"
            ) from None
        value = None
        if task.state == TaskState.VERIFIED:
            with h.store.lock:
                result = h.store.db.execute(
                    "SELECT data FROM records WHERE kind='result' "
                    "AND json_extract(data,'$.task_id')=? ORDER BY rowid DESC LIMIT 1",
                    (task.id,),
                ).fetchone()
            if result is None:
                raise StateConflict("verified probe result is unavailable")
            value = int(json.loads(result[0])["value"])
        return {
            "request_id": request_id,
            "task_id": task.id,
            "state": task.state,
            "event_id": event.id,
            "expression": event.content,
            "value": value,
        }

    def probe(self, session: SessionHandle, data: dict[str, Any]) -> dict[str, Any]:
        if set(data) != {"request_id", "expression"} or not isinstance(data["expression"], str):
            raise ValueError("explicit diagnostic arithmetic request required")
        if not re.fullmatch(r"[0-9]{1,12} \+ [0-9]{1,12}", data["expression"]):
            raise ValueError("diagnostic supports bounded positive integer addition")
        request_id, expression = data["request_id"], data["expression"]
        if not isinstance(request_id, str) or not re.fullmatch(r"[a-f0-9]{32}", request_id):
            raise ValueError("opaque request identity required")
        h = self.harness
        with self.lock:
            # Recheck after admission and before mutation, including revocation races.
            h.grid.authenticate(session, "cloud:probe")
            h.grid.authenticate(session, "math")
            h.grid.authenticate(session, "archive:retain")
            decision = PersonalPolicy(h.store).evaluate("math.add", ("math",), frozenset({"math"}))
            if not decision.allowed:
                raise PermissionError("Personal Policy denies probe")
            retention = PersonalPolicy(h.store).evaluate(
                "core.archive.retain",
                ("archive:retain",),
                frozenset({"archive:retain"}),
                {"relationship": h.runtime.relationship_id, "source": "cloud:commissioning"},
            )
            if not retention.allowed:
                raise PermissionError("Personal Policy denies diagnostic retention")
            key = session.node_id + ":" + request_id
            try:
                previous = h.store.get("cloud_probe", key)
            except KeyError:
                previous = None
            if previous and previous["expression"] != expression:
                raise StateConflict("request identity reused")
            task = h.runtime.create(
                Intent(expression), initiator=session.node_id, creation_key="cloud-probe:" + key
            )
            # Cross-database admission deliberately uses a durable event identity, then
            # an immutable archive write; an exact request retry repairs the gap without replay.
            if previous is None:
                previous = {
                    "task_id": task.id,
                    "event_id": new_id(),
                    "expression": expression,
                    "occurred_at": time(),
                }
                h.store.put("cloud_probe", key, previous)
            event = SourceEvent(
                h.runtime.relationship_id,
                expression,
                "cloud:commissioning",
                previous["occurred_at"],
                kind="cloud_probe",
                id=previous["event_id"],
                turn_id=previous["event_id"],
                episode_id=previous["event_id"],
                task_id=task.id,
            )
            h.archive.append(event, retain_authorized=True)
            retained = h.archive.db.execute(
                "SELECT 1 FROM archive_memories WHERE relationship=? AND forgotten=0 "
                "AND json_extract(payload,'$.event_ids[0]')=? LIMIT 1",
                (event.relationship_id, event.id),
            ).fetchone()
            if retained is None:
                MemoryWriter(h.archive).retain(
                    (event.id,),
                    expression,
                    "episodic",
                    retain_authorized=True,
                    inferred=False,
                )
            h.runtime.run(task.id, {h.node_id: (h.dispatcher, h.session)})
            return self.inspect_probe(session, request_id)

    def close(self) -> None:
        if not self.closed:
            if self.remote is not None:
                self.remote.close()
            if self.core is not None:
                self.core.close()
            self.closed = True
            self.directory_lock.__exit__(None, None, None)


@contextmanager
def credential_output(path: Path) -> Iterator[tuple[TextIO, int | None]]:
    """Reserve a private output before authority changes; failed files are never reused."""
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("absolute nonsymlink credential destination required")
    parent_fd = None
    try:
        if os.name == "posix":
            posix: Any = os
            directory_flag, nofollow = posix.O_DIRECTORY, posix.O_NOFOLLOW
            parent_fd = os.open(path.anchor, os.O_RDONLY | directory_flag)
            for part in path.parent.parts[1:]:
                next_fd = os.open(part, os.O_RDONLY | directory_flag | nofollow, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
            parent = os.fstat(parent_fd)
            if parent.st_uid != posix.geteuid() or stat.S_IMODE(parent.st_mode) != 0o700:
                raise PermissionError("credential parent must be owned and private (0700)")
            descriptor = os.open(
                path.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
                0o600,
                dir_fd=parent_fd,
            )
        else:
            # Windows reference verification trusts the operator's private directory ACL.
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            yield output, parent_fd
    finally:
        if parent_fd is not None:
            os.close(parent_fd)


def enroll_client(core: CloudCore, node_id: str, path: Path, ttl: int) -> None:
    if (
        not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,63}", node_id)
        or node_id == core.config.core_id
        or not 60 <= ttl <= 86400
    ):
        raise ValueError("explicit diagnostic client identity and bounded TTL required")
    h = core.harness
    scopes = ("cloud:inspect", "cloud:probe", "math", "archive:retain")
    with credential_output(path) as (output, parent_fd):
        try:
            node = h.store.get("node", node_id)
        except KeyError:
            h.grid.register(Node(node_id, NodeRole.CLOUD, scopes))
        else:
            try:
                bound = h.store.get("cloud_client", node_id) == {"core_id": core.config.core_id}
            except KeyError:
                bound = False
            if node["revoked"] or not (
                bound
                or (
                    not node["paired"]
                    and node["role"] == NodeRole.CLOUD
                    and set(node["scopes"]) == set(scopes)
                )
            ):
                raise StateConflict("client identity unavailable; choose an explicit new identity")
        h.store.audit("", "cloud_enrollment_attempt", {"node_id": node_id})

        def deliver(handle: SessionHandle) -> None:
            json.dump(
                {"node_id": handle.node_id, "session_id": handle.id, "token": handle.token},
                output,
            )
            output.flush()
            os.fsync(output.fileno())
            if parent_fd is not None:
                os.fsync(parent_fd)
            if any(p.is_symlink() for p in (path, *path.parents)):
                raise PermissionError("credential destination changed during delivery")
            current, opened = path.lstat(), os.fstat(output.fileno())
            if (
                current.st_dev,
                current.st_ino,
            ) != (opened.st_dev, opened.st_ino):
                raise PermissionError("credential destination changed during delivery")
            h.store.put("cloud_client", node_id, {"core_id": core.config.core_id})
            h.store.audit("", "cloud_enrollment_delivered", {"node_id": node_id})

        try:
            h.grid.pair(node_id, scopes, ttl=ttl, deliver=deliver)
        except BaseException:
            h.store.audit("", "cloud_enrollment_failed", {"node_id": node_id})
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--initialize", action="store_true", help="initialize offline and exit")
    operation.add_argument("--enroll-client", action="store_true", help="offline diagnostic grant")
    operation.add_argument("--revoke-client", action="store_true")
    operation.add_argument(
        "--renew-execution",
        action="store_true",
        help="offline local execution reenrollment",
    )
    parser.add_argument("--node-id")
    parser.add_argument("--credential-output", type=Path)
    parser.add_argument("--ttl", type=int, default=3600)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        config = CloudConfig.load(args.config)
        if args.enroll_client and (
            not args.node_id
            or not args.credential_output
            or not args.credential_output.is_absolute()
            or not 60 <= args.ttl <= 86400
        ):
            raise ValueError("explicit client, private output and bounded TTL required")
        core = CloudCore(
            config,
            initialize=args.initialize,
            renew_execution=args.renew_execution,
            start_services=not any(
                (
                    args.initialize,
                    args.enroll_client,
                    args.revoke_client,
                    args.renew_execution,
                )
            ),
        )
        try:
            if args.enroll_client:
                enroll_client(core, args.node_id, args.credential_output, args.ttl)
                diagnostic("client_enrolled")
            elif args.revoke_client:
                if not args.node_id or args.node_id == config.core_id:
                    raise ValueError("explicit diagnostic client identity required")
                binding = core.harness.store.get("cloud_client", args.node_id)
                if binding != {"core_id": config.core_id}:
                    raise PermissionError("diagnostic client belongs to another deployment")
                core.harness.grid.revoke(args.node_id)
                diagnostic("client_revoked")
            elif args.initialize:
                diagnostic("core_initialized")
            elif args.renew_execution:
                diagnostic("execution_renewed")
            else:
                from .cloud_http import CloudHTTPServer

                stop = Event()
                for signum in (signal.SIGINT, signal.SIGTERM):
                    signal.signal(signum, lambda *_: stop.set())
                server = CloudHTTPServer(core)
                server.start()
                diagnostic("core_started", port=config.listen_port)
                try:
                    while not stop.wait(1):
                        core.harness.grid.reap()
                finally:
                    server.close()
        finally:
            core.close()
        if not any((args.initialize, args.enroll_client, args.revoke_client, args.renew_execution)):
            diagnostic("core_stopped")
    except (ValueError, TypeError, KeyError, OSError, sqlite3.Error, StateConflict, RecursionError):
        diagnostic("core_failed", category="configuration_or_state_unavailable")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
