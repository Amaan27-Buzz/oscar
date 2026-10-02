"""POSIX reference machine executors, under native Dispatcher/Grid authorization.

Filesystem operations are FD-scoped. Terminal/agent execution is explicit trusted
host authority, not an OS sandbox: cwd alone does not confine a subprocess.
"""

import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep, time
from typing import Any

from .capabilities import Cancellation, FileExecutor, ScopedFiles, Verifier
from .contracts import (
    Action,
    ArtifactRef,
    Capability,
    Envelope,
    Epistemic,
    Evidence,
    Objective,
    Result,
    TaskState,
    Verification,
    new_id,
)
from .grid import Grid, SessionHandle
from .policy import PersonalPolicy
from .storage import StateConflict, Store

AGENT_EXECUTABLES = {
    "codex": "codex",
    "claude-code": "claude",
    "opencode": "opencode",
    "gemini-cli": "gemini",
}


@dataclass(frozen=True)
class MachineScope:
    root: Path
    trusted_host_execution: bool = False
    allowed_executables: tuple[str, ...] = ()
    max_timeout: float = 120
    max_output: int = 64_000

    def __post_init__(self) -> None:
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("workspace must be an existing real directory")
        if not math.isfinite(self.max_timeout) or not 0 < self.max_timeout <= 3600:
            raise ValueError("invalid machine timeout")
        if not 1024 <= self.max_output <= 1_000_000:
            raise ValueError("invalid output bound")
        if any(
            not Path(p).is_absolute() or not os.access(p, os.X_OK) for p in self.allowed_executables
        ):
            raise ValueError("allowed executables must be installed absolute executable paths")

    def directory(self, relative: str) -> Path:
        if relative == ".":
            return self.root.resolve()
        # Directory-FD traversal rejects symlinks. Returned paths are for trusted host commands.
        files = ScopedFiles(self.root)
        with files.parent(relative) as (parent, name):
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(fd)
        return self.root.resolve() / relative


class MachineWorker:
    def __init__(
        self,
        store: Store,
        grid: Grid,
        session: SessionHandle,
        scope: MachineScope,
        policy: PersonalPolicy | None = None,
    ):
        self.store, self.grid, self.session, self.scope = store, grid, session, scope
        self.files = ScopedFiles(scope.root)
        self.policy = policy or PersonalPolicy(store)
        self.git = shutil.which("git") if scope.trusted_host_execution else None
        if self.git not in scope.allowed_executables:
            self.git = None
        self.agents = {
            name: path
            for name, command in AGENT_EXECUTABLES.items()
            if (path := shutil.which(command)) is not None
            and path in scope.allowed_executables
            and scope.trusted_host_execution
        }
        self.owners: dict[str, str] = {}
        self.outputs: dict[str, str] = {}  # Bounded active context; never task/ledger persistence.

    def capabilities(self) -> list[Capability]:
        specs = [
            ("machine.files.write", "file_write", "files:write", "file", "high"),
            ("machine.files.read", "file_read", "files:read", "reference", "low"),
            ("machine.files.list", "directory_list", "files:read", "reference", "low"),
            ("machine.files.search", "file_search", "files:read", "reference", "low"),
            ("machine.executables", "executable_discovery", "files:read", "metadata", "low"),
        ]
        if self.git:
            specs += [
                ("machine.git", "git_operation", "machine:host", "metadata", "high"),
                ("machine.repository", "repository_task", "machine:host", "artifact", "high"),
            ]
        if self.scope.trusted_host_execution and self.scope.allowed_executables:
            specs.append(
                ("machine.command", "terminal_command", "machine:host", "metadata", "high")
            )
        specs += [
            ("machine.agent." + name, "coding", "machine:host", "metadata", "high")
            for name in self.agents
        ]
        return [
            Capability(
                identifier,
                identifier,
                "Scoped reference machine " + kind,
                "machine",
                self.session.node_id,
                (permission,),
                kind,
                output,
                risk,
            )
            for identifier, kind, permission, output, risk in specs
        ]

    def executors(self) -> dict[str, Any]:
        return {cap.id: self.execute for cap in self.capabilities()}

    def checkpoint(self, action: Action, step: str, fraction: float) -> None:
        task = self.store.task(action.task_id)
        if not task.lease_id:
            raise StateConflict("machine execution requires native task lease")
        self.grid.heartbeat(self.session)
        envelope = Envelope(
            "progress",
            self.session.node_id,
            self.session.id,
            task.id,
            task.correlation_id,
            task.lease_id,
            {},
            self.grid.clock(),
        )
        self.grid.progress(envelope, self.session.token, fraction)
        self.grid.renew(task.lease_id, self.session, ttl=30)
        self.store.put(
            "worker_checkpoint",
            task.id,
            {
                "task_id": task.id,
                "action_id": action.id,
                "lease_id": task.lease_id,
                "step": step,
                "fraction": fraction,
                "observed_at": time(),
                "correlation_id": task.correlation_id,
            },
        )

    def controls(self, task_id: str) -> dict[str, Any]:
        try:
            return self.store.get("worker_control", task_id)
        except KeyError:
            return {"paused": False}

    def set_paused(self, task_id: str, paused: bool, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("pause requires owner authority")
        self.store.put("worker_control", task_id, {"paused": paused})
        self.store.audit(task_id, "worker_pause" if paused else "worker_resume", {})

    def check(self, action: Action, cancellation: Cancellation) -> None:
        cancellation.check()
        task = self.store.task(action.task_id)
        lease = self.store.get("lease", task.lease_id or "")
        if (
            self.owners.get(action.id) != task.lease_id
            or not lease["active"]
            or lease["expires_at"] <= self.grid.clock()
            or lease["node_id"] != self.session.node_id
        ):
            raise StateConflict("worker ownership expired")
        self.grid.authenticate(self.session, "execute")
        if not any(
            n["id"] == self.session.node_id and n["status"] in {"online", "degraded"}
            for n in self.grid.nodes()
        ):
            raise StateConflict("worker disconnected")

    def run_command(
        self, action: Action, cancellation: Cancellation, argv: list[str], cwd: str, timeout: float
    ) -> tuple[int, str]:
        if not self.scope.trusted_host_execution:
            raise PermissionError("host subprocess execution is not enabled")
        if (
            not argv
            or not all(isinstance(a, str) and "\x00" not in a for a in argv)
            or argv[0] not in self.scope.allowed_executables
            or not math.isfinite(timeout)
            or not 0 < timeout <= self.scope.max_timeout
            or sum(len(a) for a in argv) > 64_000
        ):
            raise ValueError("invalid or unauthorized command")
        directory = self.scope.directory(cwd)
        env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL") if k in os.environ}
        env.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        self.check(action, cancellation)
        process = subprocess.Popen(
            argv,
            cwd=directory,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        assert process.stdout is not None
        os.set_blocking(process.stdout.fileno(), False)
        started, last_progress = monotonic(), 0.0
        output = bytearray()
        paused = False
        try:
            while True:
                self.check(action, cancellation)
                want_pause = self.controls(action.task_id)["paused"] is True
                if want_pause != paused:
                    os.killpg(process.pid, signal.SIGSTOP if want_pause else signal.SIGCONT)
                    paused = want_pause
                chunk = process.stdout.read(8192) or b""
                output.extend(chunk)
                if len(output) > self.scope.max_output:
                    raise ValueError("command output bound exceeded")
                if monotonic() - started >= timeout:
                    raise TimeoutError("machine command timeout")
                if monotonic() - last_progress >= 1:
                    self.checkpoint(action, "process-running", 0.5)
                    last_progress = monotonic()
                if process.poll() is not None:
                    tail = process.stdout.read(self.scope.max_output + 1) or b""
                    output.extend(tail)
                    if len(output) > self.scope.max_output:
                        raise ValueError("command output bound exceeded")
                    break
                sleep(0.02)
            # Kill remaining members even when the parent exited; do not orphan background jobs.
            text = output.decode(errors="replace")
            for key, value in os.environ.items():
                if value and any(
                    term in key.upper() for term in ("TOKEN", "KEY", "SECRET", "PASSWORD")
                ):
                    text = text.replace(value, "<redacted>")
            return process.returncode, text
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
            process.stdout.close()

    def git_command(self, operation: str, parameters: dict[str, Any]) -> list[str]:
        if not self.git or self.git not in self.scope.allowed_executables:
            raise PermissionError("Git executor unavailable")
        prefix = [
            self.git,
            "-c",
            "core.hooksPath=" + os.devnull,
            "-c",
            "core.fsmonitor=false",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.name=OSCAR reference",
            "-c",
            "user.email=oscar-reference@example.invalid",
        ]
        operations = {
            "status": ["status", "--porcelain"],
            "diff": ["diff", "--no-ext-diff", "--no-textconv"],
            "log": ["log", "-10", "--format=%H"],
            "branches": ["branch", "--list"],
            "head": ["rev-parse", "HEAD"],
            "init": ["init", "--quiet"],
        }
        if operation in operations:
            return prefix + operations[operation]
        if operation == "branch":
            name = parameters.get("name")
            if not isinstance(name, str) or not name or name.startswith("-"):
                raise ValueError("invalid branch name")
            return prefix + ["branch", name]
        if operation == "commit":
            message = parameters.get("message")
            if not isinstance(message, str) or not 0 < len(message) <= 500:
                raise ValueError("bounded commit message required")
            return prefix + ["commit", "-m", message]
        raise ValueError("unsupported Git operation")

    def execute(self, action: Action, cancellation: Cancellation) -> Result:
        caps = {c.id: c for c in self.capabilities()}
        cap = caps[action.capability_id]
        # Existing Dispatcher already checks grants; policies are rechecked at the target.
        decision = self.policy.evaluate(cap.name, cap.permissions, frozenset(cap.permissions))
        if not decision.allowed:
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                cap.id,
                False,
                error="machine_blocked:policy",
            )
        self.owners[action.id] = self.store.task(action.task_id).lease_id or ""
        self.check(action, cancellation)
        self.checkpoint(action, "started", 0)
        p = action.parameters
        artifact: ArtifactRef | None = None
        metadata: dict[str, Any] = {}
        try:
            if cap.id == "machine.files.write":
                return FileExecutor(self.files)(action, cancellation)
            if cap.id == "machine.files.read":
                data = self.files.read(p["path"])
                if len(data) > 1_000_000:
                    raise ValueError("read bound exceeded")
                self.outputs[action.id] = data.decode(errors="replace")
                metadata = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            elif cap.id in {"machine.files.list", "machine.files.search"}:
                directory = self.scope.directory(p.get("cwd", "."))
                pattern = p.get("pattern", "")
                if not isinstance(pattern, str) or len(pattern) > 200:
                    raise ValueError("invalid filename search")
                with os.scandir(directory) as entries:
                    names: list[str] = []
                    for entry in entries:
                        if len(names) >= 500:
                            raise ValueError("directory result bound exceeded")
                        if not entry.is_symlink() and pattern in entry.name:
                            names.append(entry.name)
                self.outputs[action.id] = json.dumps(sorted(names))
                metadata = {"entries": len(names)}
            elif cap.id == "machine.executables":
                metadata = {
                    "agents": sorted(self.agents),
                    "executables": [Path(p).name for p in self.scope.allowed_executables],
                }
            elif cap.id == "machine.repository":
                if set(p) != {"path", "content", "message"}:
                    raise ValueError("invalid repository objective")
                # A single new file plus commit: exact bounded reference objective, no LLM.
                if (self.scope.root / ".git").is_symlink():
                    raise PermissionError("symlink Git directory denied")
                with self.files.parent(p["path"]) as (parent, name):
                    try:
                        os.stat(name, dir_fd=parent, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        raise ValueError("repository reference task only creates a new file")
                status, out = self.run_command(
                    action, cancellation, self.git_command("status", {}), ".", 10
                )
                if status or out.strip():
                    raise ValueError("repository must start clean")
                self.files.write(p["path"], p["content"], cancellation)
                self.checkpoint(action, "file-written", 0.3)
                assert self.git is not None
                code, _ = self.run_command(
                    action,
                    cancellation,
                    [self.git, "-c", "core.hooksPath=" + os.devnull, "add", "--", p["path"]],
                    ".",
                    10,
                )
                if code:
                    raise ValueError("Git add failed")
                code, _ = self.run_command(
                    action, cancellation, self.git_command("commit", p), ".", 10
                )
                if code:
                    raise ValueError("Git commit failed")
                code, commit = self.run_command(
                    action, cancellation, self.git_command("head", {}), ".", 10
                )
                if code:
                    raise ValueError("Git commit inspection failed")
                metadata = {"commit": commit.strip()}
                artifact = ArtifactRef(
                    new_id(),
                    action.task_id,
                    cap.id,
                    "git-file",
                    str(self.scope.root.resolve() / p["path"]),
                    time(),
                )
            else:
                if cap.id == "machine.git":
                    argv = self.git_command(p["operation"], p)
                elif cap.id.startswith("machine.agent."):
                    name = cap.id.removeprefix("machine.agent.")
                    argv = [self.agents[name], *p["arguments"]]
                else:
                    argv = p["argv"]
                code, output = self.run_command(
                    action, cancellation, argv, p.get("cwd", "."), p.get("timeout", 30)
                )
                self.outputs[action.id] = output
                metadata = {"exit_code": code, "output_bytes": len(output.encode())}
                if code:
                    return Result(
                        new_id(),
                        action.id,
                        action.task_id,
                        action.correlation_id,
                        cap.id,
                        False,
                        value=json.dumps(metadata),
                        error="process_failed",
                    )
            self.checkpoint(action, "execution-finished", 1)
            # All log/progress is metadata-only. Arbitrary command output never enters persistence.
            self.store.audit(
                action.task_id,
                "machine_execution",
                {
                    "action_id": action.id,
                    "capability": cap.id,
                    **metadata,
                    "status": Epistemic.REPORTED,
                    "correlation_id": action.correlation_id,
                },
            )
            if len(self.outputs) > 100:
                self.outputs.pop(next(iter(self.outputs)))
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                cap.id,
                True,
                value=json.dumps(metadata),
                artifact=artifact,
            )
        except TimeoutError:
            error = "command_timeout"
        except (OSError, ValueError, PermissionError):
            error = "machine_scope_or_operation_rejected"
        return Result(
            new_id(), action.id, action.task_id, action.correlation_id, cap.id, False, error=error
        )


class MachineVerifier(Verifier):
    """Core inspection of bytes, HEAD tree and clean Git state, independent of Worker report."""

    def verify(self, objective: Objective, result: Result) -> Verification:
        if objective.criterion.get("kind") != "git_file_exact":
            return super().verify(objective, result)
        c = objective.criterion
        matches: bool | None = None
        digest: str | None = None
        detail = "repository verification unavailable"
        try:
            actual = self.files.read(c["path"])
            digest = hashlib.sha256(actual).hexdigest()
            prefix = ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false"]
            env = {"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}

            def read(args: list[str]) -> bytes:
                return subprocess.check_output(
                    prefix + args,
                    cwd=self.files.root,
                    env=env,
                    timeout=5,
                    stderr=subprocess.DEVNULL,
                )

            committed = read(["show", "HEAD:" + c["path"]])
            head = read(["rev-parse", "HEAD"]).decode().strip()
            reported = json.loads(result.value or "{}")
            matches = (
                actual == c["content"].encode() == committed
                and reported.get("commit") == head
                and head != c["initial_head"]
                and not read(["status", "--porcelain"]).strip()
            )
            detail = "exact bytes, HEAD tree, new commit and clean status compared"
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
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
            "core-repository-inspector",
            "independent file/Git tree inspection",
            self.clock(),
            matches,
            Epistemic.VERIFIED if matches else Epistemic.KNOWN,
            detail,
            result.artifact.id if result.artifact else None,
            digest,
        )
        return Verification(state, evidence)
