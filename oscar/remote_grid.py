"""Authenticated outbound transport for the canonical Grid and execution Runtime."""

import argparse
import base64
import hashlib
import json
import re
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from threading import BoundedSemaphore, Event, RLock, Thread
from time import monotonic, time
from typing import TYPE_CHECKING, Any

from .android_worker import (
    ANDROID_CAPABILITIES,
    android_readback,
    conversation_android,
    platform_readback_matches,
    validate_android,
)
from .authority import StandingAuthority
from .capabilities import Verifier, addition_operands
from .contracts import (
    Action,
    Capability,
    Envelope,
    Epistemic,
    Evidence,
    Objective,
    Result,
    TaskState,
    Verification,
    new_id,
    record,
)
from .credentials import redact_runtime_secrets
from .event_archive import MemoryWriter, SourceEvent
from .grid import Node, NodeRole, SessionHandle
from .jev import Intent, decide
from .mobile import display_digest, fingerprint
from .mobile import public_key as load_public_key
from .policy import PersonalPolicy
from .remote_client import request_proof
from .remote_machine import REMOTE_MACHINE_CAPABILITIES, machine_readback, validate_remote_machine
from .storage import StateConflict
from .transport import parse_result

if TYPE_CHECKING:
    from .cloud import CloudCore

WORKER_CAPABILITIES = {
    "machine.files.read": ("file_read", "files:read", "low"),
    "machine.files.write": ("file_write", "files:write", "high"),
    **ANDROID_CAPABILITIES,
    **REMOTE_MACHINE_CAPABILITIES,
}


def verify_signature(encoded_key: str, signature: str, message: bytes) -> None:
    hashes = import_module("cryptography.hazmat.primitives.hashes")
    padding = import_module("cryptography.hazmat.primitives.asymmetric.padding")
    invalid = import_module("cryptography.exceptions").InvalidSignature
    try:
        if not isinstance(signature, str) or len(signature) > 1024:
            raise ValueError("signature exceeds bound")
        load_public_key(encoded_key).verify(
            base64.b64decode(signature, validate=True),
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    except (invalid, ValueError, TypeError):
        raise PermissionError("device signature rejected") from None


def identifier(value: Any, *, node: bool = False) -> str:
    pattern = r"[a-z0-9][a-z0-9-]{7,63}" if node else r"[A-Za-z0-9_-]{1,64}"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("bounded explicit identity required")
    return value


def create_invitation(
    core: "CloudCore",
    node_id: str,
    role: str,
    installation_id: str,
    public_key: str,
    workspace: str = "",
    retain: bool = False,
    owner_public_key: str | None = None,
    ttl: int = 300,
    recover: bool = False,
    android_control: bool = False,
    machine_control: bool = False,
    connector_control: bool = False,
    memory_control: bool = False,
    screen_capture: bool = False,
    screen_retain: bool = False,
) -> dict[str, Any]:
    """Trusted offline owner operation. Reachability alone cannot call this method."""
    identifier(node_id, node=True)
    identifier(installation_id)
    if role not in {"desktop", "mobile"} or not 30 <= ttl <= 300:
        raise ValueError("explicit supported role and bounded invitation lifetime required")
    if role == "desktop" or workspace:
        identifier(workspace)
    if node_id == core.config.core_id:
        raise ValueError("device cannot replace Core identity")
    load_public_key(public_key)
    if owner_public_key is not None:
        load_public_key(owner_public_key)
    h = core.harness
    scopes = [
        "grid:connect",
        "heartbeat",
        "grid:inspect",
        "presence:read",
        "grid:submit",
        "grid:cancel",
        "files:read",
        "files:write",
        "math",
        "models",
    ]
    if retain:
        scopes += ["archive:retain", "archive:read"]
    if role == "desktop" or workspace:
        scopes += ["advertise", "execute"]
    if type(android_control) is not bool:
        raise ValueError("explicit Android control scope required")
    if role == "mobile" and workspace or android_control:
        scopes += ["android:act", "android:perceive"]
    if type(machine_control) is not bool:
        raise ValueError("explicit machine control scope required")
    if machine_control:
        scopes += ["machine:host", "desktop:control", "desktop:clipboard", "browser:control"]
    if (
        type(screen_capture) is not bool
        or type(screen_retain) is not bool
        or screen_retain
        and not screen_capture
        or screen_capture
        and not machine_control
    ):
        raise ValueError("separate Desktop capture and retention consent required")
    if screen_capture:
        scopes.append("desktop:capture")
    if screen_retain:
        scopes.append("screen:retain")
    if type(connector_control) is not bool:
        raise ValueError("explicit connector control scope required")
    if connector_control:
        scopes += ["connectors:read", "connectors:write", "connectors:external-communication"]
    if type(memory_control) is not bool:
        raise ValueError("explicit canonical memory control scope required")
    if memory_control:
        scopes += ["memory:read", "memory:manage"]
    if owner_public_key:
        scopes += ["grid:approve", "world:read"]
    challenge = new_id()
    binding = {
        "core_id": core.config.core_id,
        "node_id": node_id,
        "role": role,
        "installation_id": installation_id,
        "owner_id": h.runtime.relationship_id,
        "workspace": workspace,
        "public_key": public_key,
        "scopes": scopes,
        "owner_public_key": owner_public_key,
        "version": 2,
    }
    claim = {
        **binding,
        "challenge_id": challenge,
        "nonce": new_id(),
        "expires_at_ms": int((time() + ttl) * 1000),
    }
    signing_payload = base64.b64encode(
        json.dumps(
            claim,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).decode()
    with h.store.transaction():
        try:
            previous = h.store.get("node", node_id)
        except KeyError:
            previous = None
        if previous and not recover:
            raise StateConflict("existing device requires explicit owner recovery")
        if len(h.store.all("remote_device")) >= 64 and previous is None:
            raise StateConflict("device enrollment capacity reached")
        # A fresh owner-authorized invitation supersedes every old one for this device.
        for row in h.store.all("remote_invitation"):
            if row["binding"]["node_id"] == node_id or row["expires_at_ms"] <= time() * 1000:
                h.store.delete("remote_invitation", row["id"])
        if len(h.store.all("remote_invitation")) >= 64:
            raise StateConflict("pending invitation capacity reached")
        h.store.put(
            "remote_invitation",
            challenge,
            {
                "id": challenge,
                "binding": binding,
                "signing_payload": signing_payload,
                "expires_at_ms": claim["expires_at_ms"],
                "recover": recover,
            },
        )
        h.store.audit("", "remote_enrollment_initiated", {"node_id": node_id, "role": role})
    return {
        k: claim[k]
        for k in (
            "version",
            "core_id",
            "node_id",
            "role",
            "installation_id",
            "workspace",
            "public_key",
            "challenge_id",
            "expires_at_ms",
        )
    } | {"signing_payload": signing_payload}


class OutboundTransport:
    """Runtime Transport adapter: durable delivery, never a second task scheduler."""

    def __init__(self, remote: "RemoteGrid"):
        self.remote = remote

    def invoke(self, envelope: Envelope, session: SessionHandle) -> Result:
        self.remote.prepare_executive(envelope, session)
        return parse_result(self.remote.exchange(envelope.task_id, "action"))

    def control(self, envelope: Envelope, session: SessionHandle) -> dict[str, Any]:
        return {"status": "UNKNOWN", "task_id": envelope.task_id}


class RemoteVerifier(Verifier):
    def __init__(self, remote: "RemoteGrid", original: Verifier):
        super().__init__(original.files, original.clock)
        self.remote, self.original = remote, original

    def bind_task(self, task_id: str, parameters: dict[str, Any]) -> None:
        self.original.bind_task(task_id, parameters)

    def release_task(self, task_id: str) -> None:
        self.original.release_task(task_id)

    def verify(self, objective: Objective, result: Result) -> Verification:
        if objective.criterion["kind"] == "remote_machine":
            if objective.criterion.get("match_report"):
                actual = self.remote.exchange(result.task_id, "readback")["content"]
                matches = actual == result.value
                return Verification(
                    TaskState.VERIFIED if matches else TaskState.FAILED,
                    Evidence(
                        new_id(),
                        result.task_id,
                        result.correlation_id,
                        "remote-read-only-observer",
                        "separate current read-only observation and Core exact comparison",
                        time(),
                        matches,
                        Epistemic.VERIFIED if matches else Epistemic.KNOWN,
                        "read-only observations compared",
                        content_hash=hashlib.sha256(actual.encode()).hexdigest(),
                    ),
                )
            if "text" in objective.criterion:
                actual = self.remote.exchange(result.task_id, "readback")["content"]
                observed = json.loads(actual)
                matches = (
                    isinstance(observed, dict)
                    and observed.get("text") == objective.criterion["text"]
                    and (
                        "url" not in objective.criterion
                        or observed.get("url") == objective.criterion["url"]
                    )
                )
                return Verification(
                    TaskState.VERIFIED if matches else TaskState.FAILED,
                    Evidence(
                        new_id(),
                        result.task_id,
                        result.correlation_id,
                        "remote-native-observer",
                        "separate native read and Core exact-text comparison",
                        time(),
                        matches,
                        Epistemic.VERIFIED if matches else Epistemic.KNOWN,
                        "destination compared",
                        content_hash=hashlib.sha256(actual.encode()).hexdigest(),
                    ),
                )
            return Verification(
                TaskState.PARTIALLY_VERIFIED,
                Evidence(
                    new_id(),
                    result.task_id,
                    result.correlation_id,
                    "remote-machine-report",
                    "authenticated native executor report",
                    time(),
                    None,
                    Epistemic.REPORTED,
                    "Native execution reported; objective-specific independent readback required",
                ),
            )
        if objective.criterion["kind"] == "remote_android":
            criterion = objective.criterion
            actual = self.remote.exchange(result.task_id, "readback")["content"]
            observed = json.loads(actual)
            if not isinstance(observed, dict) or observed.get("package") != criterion["package"]:
                raise ValueError("Android readback package mismatch")
            matches = platform_readback_matches(criterion["operation"], criterion, observed)
            if criterion["operation"] == "android_ui_set_text":
                candidates = [
                    n
                    for n in observed.get("observations", [])
                    if n.get("resource_id") == criterion["target"]
                ]
                matches = len(candidates) == 1 and candidates[0].get("text") == criterion["value"]
            elif criterion["operation"] in {
                "android_ui_inspect",
                "android_files_read",
                "android_clipboard_read",
            }:
                matches = actual == result.value
            return Verification(
                TaskState.PARTIALLY_VERIFIED
                if matches is None
                else TaskState.VERIFIED
                if matches
                else TaskState.FAILED,
                Evidence(
                    new_id(),
                    result.task_id,
                    result.correlation_id,
                    "remote-android-native",
                    "separate read-only native observation and Core comparison",
                    time(),
                    matches,
                    Epistemic.REPORTED
                    if matches is None
                    else Epistemic.VERIFIED
                    if matches
                    else Epistemic.KNOWN,
                    "Native effect requires app-specific observation"
                    if matches is None
                    else "Exact Android readback",
                    content_hash=hashlib.sha256(actual.encode()).hexdigest(),
                ),
            )
        if objective.criterion["kind"] != "remote_file":
            return self.original.verify(objective, result)
        actual = self.remote.exchange(result.task_id, "readback")["content"]
        expected = objective.criterion.get("content", result.value)
        matches = actual == expected
        return Verification(
            TaskState.VERIFIED if matches else TaskState.FAILED,
            Evidence(
                new_id(),
                result.task_id,
                result.correlation_id,
                "remote-scoped-filesystem",
                "separate readback request and Core exact-byte comparison",
                time(),
                matches,
                Epistemic.VERIFIED if matches else Epistemic.KNOWN,
                "readback matches" if matches else "readback differs",
                result.artifact.id if result.artifact else None,
                hashlib.sha256(actual.encode()).hexdigest(),
            ),
        )


class RemoteGrid:
    def __init__(self, core: "CloudCore"):
        self.core, self.h = core, core.harness
        self.store, self.grid = self.h.store, self.h.grid
        self.lock, self.stop = RLock(), Event()
        self.slots = BoundedSemaphore(4)
        self.threads: list[Thread] = []
        self.sessions: dict[str, SessionHandle] = {}
        self.transport = OutboundTransport(self)
        self.h.runtime.verifier = RemoteVerifier(self, self.h.runtime.verifier)
        # Process loss fences deliveries even when their node heartbeat is still fresh.
        for row in self.store.all("remote_delivery"):
            if row["state"] in {"pending", "claimed"}:
                self.store.put("remote_delivery", row["id"], {**row, "state": "uncertain"})
                task = self.store.task(row["task_id"])
                if task.state in {
                    TaskState.EXECUTING,
                    TaskState.AWAITING_RESULT,
                    TaskState.RESULT_RECEIVED,
                    TaskState.VERIFYING,
                }:
                    self.store.transition(
                        task.id,
                        TaskState.UNKNOWN
                        if task.state == TaskState.VERIFYING
                        else TaskState.BLOCKED,
                        blocker="Core restarted; inspect effect before retry",
                    )
                if task.lease_id:
                    self.grid.release(task.lease_id)
        for row in self.store.all("remote_device"):
            self.grid.disconnect(row["node_id"])
        for row in self.store.all("remote_task"):
            task = self.store.task(row["task_id"])
            if task.state in {
                TaskState.PLANNED,
                TaskState.EXECUTING,
                TaskState.AWAITING_RESULT,
                TaskState.RESULT_RECEIVED,
                TaskState.VERIFYING,
            }:
                self.store.transition(
                    task.id,
                    TaskState.UNKNOWN if task.state == TaskState.VERIFYING else TaskState.BLOCKED,
                    blocker="Core restarted; inspect effect and submit a fresh request",
                )
            if task.lease_id:
                self.grid.release(task.lease_id)

    def close(self) -> None:
        self.stop.set()
        for thread in self.threads:
            thread.join(timeout=5)
        if any(thread.is_alive() for thread in self.threads):
            raise StateConflict("remote execution did not stop")
        self.sessions.clear()

    def enroll(self, data: dict[str, Any]) -> dict[str, Any]:
        if (
            set(data) != {"version", "challenge_id", "signature"}
            or type(data["version"]) is not int
            or data["version"] != 2
        ):
            raise ValueError("explicit enrollment proof required")
        with self.lock:
            row = self.store.get("remote_invitation", identifier(data["challenge_id"]))
            if row["expires_at_ms"] <= time() * 1000:
                raise PermissionError("invitation expired")
            binding = row["binding"]
            verify_signature(
                binding["public_key"], data["signature"], base64.b64decode(row["signing_payload"])
            )
            with self.store.transaction():
                self.store.delete("remote_invitation", row["id"])

            # Burn a valid proof before attempting authority changes; failure needs owner recovery.
            def prepare() -> None:
                node_id = binding["node_id"]
                try:
                    node = self.store.get("node", node_id)
                except KeyError:
                    node = None
                if node is not None:
                    if not row["recover"]:
                        raise PermissionError("explicit device recovery required")
                    self._fence_sessions(node_id)
                    self.store.put(
                        "node",
                        node_id,
                        record(
                            Node(
                                node_id,
                                NodeRole.DESKTOP
                                if binding["role"] == "desktop"
                                else NodeRole.MOBILE,
                                tuple(binding["scopes"]),
                            )
                        ),
                    )
                else:
                    self.grid.register(
                        Node(
                            node_id,
                            NodeRole.DESKTOP if binding["role"] == "desktop" else NodeRole.MOBILE,
                            tuple(binding["scopes"]),
                        )
                    )

            def deliver(session: SessionHandle) -> None:
                self.store.put(
                    "remote_device", session.node_id, {**binding, "session_id": session.id}
                )

            session = self.grid.pair(
                binding["node_id"], tuple(binding["scopes"]), prepare=prepare, deliver=deliver
            )
            self.sessions[session.node_id] = session
            return self.session_view(session)

    def session_view(self, session: SessionHandle) -> dict[str, Any]:
        row = self.store.get("session", session.id)
        return {
            "version": 2,
            "core_id": self.core.config.core_id,
            "node_id": session.node_id,
            "session_id": session.id,
            "token": session.token,
            "expires_at_ms": int(row["expires_at"] * 1000),
            "scopes": row["scopes"],
        }

    def _fence_sessions(self, node_id: str) -> None:
        for row in self.store.all("session"):
            if row["node_id"] == node_id:
                self._revoke_session(row["id"])

    def authenticate(
        self, headers: Any, body: bytes, admit: Callable[[str], None] | None = None
    ) -> SessionHandle:
        keys = (
            "Authorization",
            "X-Oscar-Node",
            "X-Oscar-Session",
            "X-Oscar-Nonce",
            "X-Oscar-Time",
            "X-Oscar-Signature",
        )
        if any(len(headers.get_all(k, [])) != 1 for k in keys):
            raise PermissionError("explicit device proof required")
        auth = headers["Authorization"]
        if not re.fullmatch(r"Bearer [A-Za-z0-9_-]{32,128}", auth):
            raise PermissionError("invalid session")
        node, session_id = (
            identifier(headers["X-Oscar-Node"], node=True),
            headers["X-Oscar-Session"],
        )
        nonce, instant = headers["X-Oscar-Nonce"], headers["X-Oscar-Time"]
        if (
            not re.fullmatch(r"[a-f0-9]{32}", session_id)
            or not re.fullmatch(r"[a-f0-9]{32}", nonce)
            or not re.fullmatch(r"[0-9]{13}", instant)
            or abs(time() * 1000 - int(instant)) > 60000
        ):
            raise PermissionError("invalid or expired request")
        handle = SessionHandle(session_id, node, auth.removeprefix("Bearer "))
        with self.lock:
            self.require(handle, "grid:connect")
            binding = self.store.get("remote_device", node)
            verify_signature(
                binding["public_key"],
                headers["X-Oscar-Signature"],
                request_proof(node, session_id, nonce, instant, body),
            )
            if admit is not None:
                admit(node)
            self.store.consume_nonce(session_id, nonce)
            self.sessions[node] = handle
        return handle

    def require(self, session: SessionHandle, scope: str) -> dict[str, Any]:
        self.grid.authenticate(session, scope)
        binding = self.store.get("remote_device", session.node_id)
        if (
            binding["core_id"] != self.core.config.core_id
            or binding["session_id"] != session.id
            or binding["owner_id"] != self.h.runtime.relationship_id
        ):
            raise PermissionError("device binding denied")
        return binding

    def policy(self, session: SessionHandle, capability: Capability, *, confirmed: bool) -> None:
        for permission in capability.permissions:
            self.grid.authenticate(session, permission)
        scopes = frozenset(self.store.get("session", session.id)["scopes"])
        decision = PersonalPolicy(self.store).evaluate(
            capability.id,
            capability.permissions,
            scopes,
            {"node": session.node_id, "target": capability.node_id, "source": "remote-grid"},
            confirmed=confirmed,
            confirmation_required=capability.risk != "low",
        )
        if not decision.allowed:
            raise PermissionError("Personal Policy denied remote action")

    def artifact_permission(
        self,
        requester_id: str,
        executor: SessionHandle,
        capability: Capability,
        parameters: dict[str, Any],
        *,
        delegated: bool = False,
    ) -> None:
        if (
            capability.input_kind not in {"coding", "terminal_command"}
            or "verification" not in parameters
        ):
            return
        reads = [
            c
            for c in self.grid.search("file_read")
            if c.node_id == executor.node_id and c.id == "machine.files.read"
        ]
        if len(reads) != 1:
            raise PermissionError("artifact verification requires a current shared file reader")
        read = reads[0]
        self.policy(executor, read, confirmed=False)
        requester = self.store.get("session", requester_id)
        node = self.store.get("node", requester["node_id"])
        if requester["revoked"] or node["revoked"] or requester["expires_at"] <= time():
            raise PermissionError("artifact requester authority unavailable")
        granted = frozenset(requester["scopes"]) & frozenset(node["scopes"])
        policy = PersonalPolicy(self.store)
        for identifier in (read.id, *read.permissions):
            for source, scopes in (
                (node["id"], granted),
                (executor.node_id, frozenset(self.store.get("session", executor.id)["scopes"])),
            ):
                if not policy.evaluate(
                    identifier,
                    read.permissions,
                    scopes,
                    {"node": source, "target": executor.node_id, "source": "remote-grid"},
                ).allowed:
                    raise PermissionError("separate artifact-read permission required")
        if delegated and not StandingAuthority(
            self.store, self.grid, self.h.runtime.relationship_id
        ).permits(record(read), executor):
            raise PermissionError("standing delegation must also cover the artifact reader")

    def request(self, session: SessionHandle, data: dict[str, Any]) -> dict[str, Any]:
        if (
            set(data) != {"version", "operation", "request_id", "payload"}
            or type(data["version"]) is not int
            or data["version"] != 2
            or not isinstance(data["payload"], dict)
        ):
            raise ValueError("versioned Grid request required")
        identifier(data["request_id"])
        operation, payload = data["operation"], data["payload"]
        if operation in {
            "management_challenge",
            "management_complete",
            "oauth_callback",
            "assistance_challenge",
            "assistance_complete",
            "authority_challenge",
            "authority_complete",
            "authority_revoke",
        }:
            with self.lock:
                binding = self.require(session, "grid:approve")
                if not binding["owner_public_key"]:
                    raise PermissionError("enrolled owner review required")
                grants = frozenset(self.store.get("session", session.id)["scopes"])
            from .assistance import Assistance
            from .authority import StandingAuthority
            from .connections import Connections

            manager: Any = (
                StandingAuthority(self.store, self.grid, self.h.runtime.relationship_id)
                if operation.startswith("authority_")
                else Assistance(self.h)
                if operation.startswith("assistance_")
                else Connections(self.h)
            )
            if operation.endswith("_challenge"):
                return dict(
                    manager.challenge(session.node_id, session.id, "grid:approve", grants, payload)
                )
            if operation == "authority_revoke":
                if payload:
                    raise ValueError("downgrade takes no parameters")
                return dict(manager.revoke(session.node_id, session.id, "grid:approve", grants))
            if operation == "oauth_callback":
                return dict(
                    manager.oauth_callback(
                        session.node_id, session.id, "grid:approve", grants, payload
                    )
                )
            return dict(
                manager.complete(
                    session.node_id,
                    session.id,
                    binding["owner_public_key"],
                    "grid:approve",
                    grants,
                    payload,
                )
            )
        with self.lock:
            self.require(session, "grid:connect")
            self.grid.heartbeat(session)
            if operation in {"snapshot", "conversation"}:
                return self.snapshot(session, payload)
            if operation == "presence" and not payload:
                presence = self.presence(session)
                if presence is None:
                    raise PermissionError("Presence is not authorized or available")
                return {**presence, "observed_at_ms": int(time() * 1000)}
            if operation == "phone_context":
                from .phone_context import request

                def phone_authority() -> None:
                    self.require(session, "android:perceive")

                return request(self.h.world, session, payload, phone_authority)
            if operation == "day_brief" and not payload:
                self.require(session, "world:read")
                grants = frozenset(self.store.get("session", session.id)["scopes"])
                permission = PersonalPolicy(self.store).evaluate(
                    "core.world.read",
                    ("world:read",),
                    grants,
                    {"node": session.node_id, "source": "remote-grid"},
                )
                if not permission.allowed:
                    raise PermissionError(permission.reason)
                return {"day_brief": self.h.world.brief()}
            if operation == "inspect" and set(payload) == {"task_id"}:
                self.require(session, "grid:inspect")
                task_id = identifier(payload["task_id"])
                row = self.store.get("remote_task", task_id)
                if row.get("source") == "memory" and not row.get("retain", True):
                    from .memory_executor import authorize_recall

                    authorize_recall(self.h.runtime, task_id, session.id)
                return self.inspect(
                    task_id,
                    redacted=not self.can_read(session),
                    viewer_session=session.id,
                )
            if operation == "submit":
                return self.submit(session, data["request_id"], payload)
            if operation == "challenge":
                return self.challenge(session, payload)
            if operation == "complete":
                return self.complete(session, payload)
            if operation == "cancel" and set(payload) == {"task_id"}:
                self.require(session, "grid:cancel")
                task_id = identifier(payload["task_id"])
                self.inspect(task_id)
                self.h.runtime.cancel(task_id)
                for row in self.store.all("remote_delivery"):
                    if row["task_id"] == task_id and row["state"] in {"pending", "claimed"}:
                        self.store.put("remote_delivery", row["id"], {**row, "state": "uncertain"})
                return self.inspect(task_id, redacted=not self.can_read(session))
            if operation == "advertise":
                return self.advertise(session, payload)
            if operation == "poll" and not payload:
                self.require(session, "execute")
                node = self.store.get("node", session.node_id)
                target = self.h.executive.targets.get(session.node_id)
                if (
                    node.get("executor_session") != session.id
                    or target is None
                    or target[1].id != session.id
                    or target[1].node_id != session.node_id
                ):
                    # Restart discards remote capabilities/targets. No delivery is claimed
                    # until the authenticated Worker explicitly advertises them again.
                    return {"delivery": None, "advertise_required": True}
                self.grid.executor_heartbeat(session)
                for row in self.store.all("remote_delivery"):
                    if row["node_id"] == session.node_id and row["state"] == "pending":
                        try:
                            self.check(session, row["id"])
                        except (PermissionError, KeyError):
                            self.store.put(
                                "remote_delivery", row["id"], {**row, "state": "uncertain"}
                            )
                            continue
                        self.store.put("remote_delivery", row["id"], {**row, "state": "claimed"})
                        return {"delivery": self.delivery_view(row)}
                return {"delivery": None}
            if operation == "check" and set(payload) in (
                {"delivery_id"},
                {"delivery_id", "authority"},
            ):
                self.grid.executor_heartbeat(session)
                delivery = self.check(session, identifier(payload["delivery_id"]))
                authority = self.store.get("remote_task", delivery["task_id"]).get("authority")
                if payload.get("authority") != authority:
                    raise PermissionError("Worker authority pin differs from Core")
                return {"authorized": True, **({"authority": authority} if authority else {})}
            if operation == "deliver" and set(payload) == {"delivery_id", "result"}:
                self.grid.executor_heartbeat(session)
                return self.deliver(session, payload)
            if operation == "rotate" and not payload:
                binding = self.require(session, "grid:connect")

                def replace(new: SessionHandle) -> None:
                    self.store.put(
                        "remote_device", session.node_id, {**binding, "session_id": new.id}
                    )
                    self._revoke_session(session.id)

                new = self.grid.pair(session.node_id, tuple(binding["scopes"]), deliver=replace)
                self.grid.disconnect(session.node_id)
                self.sessions[session.node_id] = new
                return self.session_view(new)
            if operation in {"disconnect", "revoke"} and not payload:
                if operation == "revoke":
                    # Commit the denial before best-effort lease/task cleanup.
                    with self.store.transaction():
                        node = self.store.get("node", session.node_id)
                        self.store.put("node", session.node_id, {**node, "revoked": True})
                        self._fence_sessions(session.node_id)
                        for invitation in self.store.all("remote_invitation"):
                            if invitation["binding"]["node_id"] == session.node_id:
                                self.store.delete("remote_invitation", invitation["id"])
                    self.grid.revoke(session.node_id)
                else:
                    from .phone_context import withdraw

                    withdraw(self.h.world, session.id)
                    self.grid.disconnect(session.node_id)
                self.sessions.pop(session.node_id, None)
                return {"state": "revoked" if operation == "revoke" else "offline"}
        raise ValueError("unsupported Grid operation or payload")

    def _revoke_session(self, session_id: str) -> None:
        row = self.store.get("session", session_id)
        self.store.put("session", session_id, {**row, "revoked": True})
        from .phone_context import withdraw

        withdraw(self.h.world, session_id)

    def advertise(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        binding = self.require(session, "advertise")
        if (
            set(payload) != {"workspace", "capabilities"}
            or payload["workspace"] != binding["workspace"]
            or not isinstance(payload["capabilities"], list)
            or len(payload["capabilities"]) > 32
        ):
            raise PermissionError("advertisement outside enrolled workspace")
        capabilities = []
        for data in payload["capabilities"]:
            if not isinstance(data, dict) or set(data) != set(Capability.__dataclass_fields__):
                raise ValueError("explicit capability contract required")
            cap = Capability.from_dict(data)
            spec = WORKER_CAPABILITIES.get(cap.id)
            if (
                spec is None
                or (cap.id.startswith("android.") and binding["role"] != "mobile")
                or (not cap.id.startswith("android.") and binding["role"] != "desktop")
                or (cap.input_kind, cap.permissions, cap.risk)
                != (spec[0], (spec[1],) if isinstance(spec[1], str) else spec[1], spec[2])
                or cap.node_id != session.node_id
                or cap.execution_class != "machine"
                or cap.output_kind
                != (
                    "file"
                    if cap.input_kind == "file_write"
                    else "artifact"
                    if cap.input_kind in {"repository_task", "screen_capture"}
                    else "metadata"
                    if cap.id in REMOTE_MACHINE_CAPABILITIES
                    and cap.input_kind not in {"directory_list", "file_search"}
                    else "reference"
                )
                or type(cap.version) is not int
                or cap.version != 1
                or type(cap.reversible) is not bool
                or any(
                    not isinstance(v, str) or not 0 < len(v) <= 240
                    for v in (
                        cap.id,
                        cap.name,
                        cap.summary,
                        cap.execution_class,
                        cap.node_id,
                        cap.input_kind,
                        cap.output_kind,
                        cap.risk,
                    )
                )
            ):
                raise PermissionError("capability exceeds owner enrollment")
            capabilities.append(cap)
        self.grid.advertise(session, capabilities, executor=True)
        if isinstance(self.h.executive.targets, dict):
            self.h.executive.targets[session.node_id] = (self.transport, session)
        return {"state": "online", "capabilities": [record(c) for c in capabilities]}

    def submit(
        self, session: SessionHandle, request_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self.require(session, "grid:submit")
        required = {"text", "kind", "target", "parameters", "retain"}
        if (
            set(payload) != required
            or type(payload["retain"]) is not bool
            or not isinstance(payload["parameters"], dict)
            or not isinstance(payload["text"], str)
            or not 0 < len(payload["text"].encode()) <= 8192
        ):
            raise ValueError("explicit bounded request and retention choice required")
        ephemeral_recall = (
            not payload["retain"]
            and payload["kind"] == "text"
            and payload["target"] == self.h.node_id
            and not payload["parameters"]
            and decide(Intent(payload["text"])).capability_kind == "memory"
        )
        if not ephemeral_recall:
            self.require(session, "archive:retain")
            if not payload["retain"]:
                raise ValueError("this remote operation requires explicit retention")
        if redact_runtime_secrets(json.dumps(payload)) != json.dumps(payload):
            raise ValueError("secrets cannot enter canonical history")
        key, digest = session.node_id + ":" + request_id, fingerprint(payload)
        try:
            old = self.store.get("remote_admission", key)
        except KeyError:
            old = None
        if old:
            if old["digest"] != digest:
                raise StateConflict("request identity changed")
            self.retain(self.store.get("remote_task", old["task_id"]), result=False)
            return self.inspect(old["task_id"], viewer_session=session.id)
        if (
            len(
                [
                    r
                    for r in self.store.all("remote_task")
                    if self.store.task(r["task_id"]).state
                    in {TaskState.PLANNED, TaskState.EXECUTING, TaskState.AWAITING_RESULT}
                ]
            )
            >= 32
        ):
            raise StateConflict("remote task queue full")
        kind, parameters, target = payload["kind"], payload["parameters"], payload["target"]
        identifier(target, node=True)
        if kind == "text" and target == self.h.node_id and not ephemeral_recall:
            if parameters:
                raise ValueError("text parameters must be empty")
            from .assistance import Assistance
            from .communication import prepare

            try:
                proposal = Assistance.conversation_change(payload["text"])
            except ValueError:
                return {
                    "state": "blocked",
                    "epistemic": "UNKNOWN",
                    "message": (
                        "Specify every hour/day/week for 1..100 runs, followed by exact actions."
                    ),
                }
            if proposal is not None:
                return {"assistance_proposal": proposal}
            communication = prepare(self.h, payload["text"])
            if communication is not None:
                try:
                    return self.submit_communication(session, key, digest, payload, communication)
                finally:
                    assert communication.intent.parameters is not None
                    reference = communication.intent.parameters["request_ref"]
                    if reference not in self.h.connectors.request_owners:
                        self.h.connectors.release_request(reference)
            from .desktop_actions import OPERATIONS, conversation_form, form_intent

            form = conversation_form(payload["text"])
            native = conversation_android(payload["text"])
            if native is not None:
                requested_node, kind, parameters = native
                candidates = [
                    cap
                    for cap in self.grid.search(kind)
                    if cap.node_id in self.sessions
                    and cap.id in ANDROID_CAPABILITIES
                    and (requested_node is None or cap.node_id == requested_node)
                ]
                if len(candidates) != 1:
                    raise StateConflict(
                        "Android target is unavailable or ambiguous; select a device"
                    )
                target = candidates[0].node_id
            elif form is not None:
                operation, fields = form
                candidates = [
                    cap
                    for input_kind, operations in OPERATIONS.items()
                    if operation in operations
                    for cap in self.grid.search(input_kind)
                    if cap.node_id in self.sessions
                    and cap.node_id != self.h.node_id
                    and cap.id in WORKER_CAPABILITIES
                ]
                if len(candidates) != 1:
                    raise StateConflict(
                        "action target is unavailable or ambiguous; select a device"
                    )
                selected = candidates[0]
                typed = form_intent(
                    selected,
                    {"capability_id": selected.id, "operation": operation, "fields": fields},
                    {},
                )
                if typed.parameters is None or typed.capability_kind is None:
                    raise ValueError("typed capability action required")
                kind, parameters, target = (
                    typed.capability_kind,
                    typed.parameters,
                    selected.node_id,
                )
            else:
                from .planner_authoring import PlannerAuthoring

                planned = PlannerAuthoring(self.h).conversation(
                    payload["text"],
                    session.node_id,
                    session.id,
                    "grid:approve",
                    frozenset(self.store.get("session", session.id)["scopes"]),
                )
                if planned is not None:
                    return planned
        criterion: dict[str, Any] = {"kind": "unavailable"}
        if kind in {"file_read", "file_write"}:
            needed = {"path", "content"} if kind == "file_write" else {"path"}
            if set(parameters) != needed or not all(
                isinstance(v, str) for v in parameters.values()
            ):
                raise ValueError("typed file parameters required")
            path = parameters["path"]
            if (
                len(path) > 240
                or not path
                or "\\" in path
                or ":" in path
                or any(p in {"", ".", ".."} for p in path.split("/"))
                or "\x00" in path
            ):
                raise ValueError("relative workspace path required")
            if len(parameters.get("content", "").encode()) > 8192:
                raise ValueError("file content exceeds bound")
            candidates = [c for c in self.grid.search(kind) if c.node_id == target]
            if len(candidates) != 1:
                raise StateConflict("exact target capability unavailable")
            capability = candidates[0]
            criterion = {"kind": "remote_file", "path": path}
            if kind == "file_write":
                criterion["content"] = parameters["content"]
            self.policy(session, capability, confirmed=kind == "file_write")
            intent = Intent(
                payload["text"],
                kind="capability",
                capability_kind=kind,
                parameters=parameters,
                criterion=criterion,
            )
        elif kind in {spec[0] for spec in ANDROID_CAPABILITIES.values()}:
            parameters = validate_android(kind, parameters)
            candidates = [c for c in self.grid.search(kind) if c.node_id == target]
            if len(candidates) != 1:
                raise StateConflict("exact Android capability unavailable")
            capability = candidates[0]
            self.policy(session, capability, confirmed=capability.risk != "low")
            criterion = {"kind": "remote_android", "operation": kind, **parameters}
            intent = Intent(
                payload["text"],
                kind="capability",
                capability_kind=kind,
                parameters=parameters,
                criterion=criterion,
            )
        elif kind in {spec[0] for spec in REMOTE_MACHINE_CAPABILITIES.values()}:
            parameters = validate_remote_machine(kind, parameters)
            candidates = [c for c in self.grid.search(kind) if c.node_id == target]
            if len(candidates) != 1:
                raise StateConflict("exact machine capability unavailable")
            capability = candidates[0]
            self.policy(session, capability, confirmed=capability.risk != "low")
            criterion = {"kind": "remote_machine", "operation": kind}
            if kind in {"coding", "terminal_command"} and "verification" in parameters:
                executor = self.sessions.get(target)
                if executor is None:
                    raise PermissionError("artifact executor unavailable")
                self.artifact_permission(session.id, executor, capability, parameters)
                criterion = {"kind": "remote_file", **parameters["verification"]}
            elif (
                capability.id
                in {
                    "machine.apps",
                    "machine.files.list",
                    "machine.files.search",
                    "machine.controls",
                }
                or capability.id == "machine.browser"
                and parameters["request"].get("read_only")
            ) and machine_readback(capability.id, parameters):
                criterion["match_report"] = True
            elif machine_readback(capability.id, parameters) is not None:
                expected = parameters.get("verification", parameters["request"])
                criterion["text"] = expected["text"]
                if capability.id == "machine.browser":
                    criterion["url"] = expected["url"]
            intent = Intent(
                payload["text"],
                kind="capability",
                capability_kind=kind,
                parameters=parameters,
                criterion=criterion,
            )
        elif kind in {"addition", "text"} and target == self.h.node_id:
            if kind == "addition":
                if set(parameters) != {"expression"} or not isinstance(
                    parameters["expression"], str
                ):
                    raise ValueError("bounded arithmetic required")
                addition_operands(parameters["expression"])
                intent = Intent(parameters["expression"])
                capability = next(c for c in self.grid.search("addition") if c.node_id == target)
            else:
                if parameters:
                    raise ValueError("text parameters must be empty")
                intent = Intent(payload["text"], kind="reason")
                capability = next(
                    c
                    for c in self.grid.search(
                        "memory"
                        if decide(intent).capability_kind == "memory"
                        else "model_reasoning"
                    )
                    if c.node_id == target
                )
        else:
            raise ValueError("unsupported typed remote request")
        # Retention is a distinct policy decision, not a side effect of action permission.
        if payload["retain"] and (
            not PersonalPolicy(self.store)
            .evaluate(
                "core.archive.retain",
                ("archive:retain",),
                frozenset(self.store.get("session", session.id)["scopes"]),
                {"source": "remote-grid", "relationship": self.h.runtime.relationship_id},
            )
            .allowed
        ):
            raise PermissionError("retention policy denied")
        recalling = capability.input_kind == "memory"
        self.policy(session, capability, confirmed=capability.risk != "low")
        if recalling:
            if (
                not PersonalPolicy(self.store)
                .evaluate(
                    "memory.read",
                    ("memory:read",),
                    frozenset(self.store.get("session", session.id)["scopes"]),
                    {
                        "node": session.node_id,
                        "source": "remote-grid",
                        "relationship": self.h.runtime.relationship_id,
                    },
                )
                .allowed
            ):
                raise PermissionError("memory read policy denied")
        task = self.h.runtime.create(
            intent,
            initiator=session.node_id,
            retry_budget=0,
            transient=recalling,
            creation_key=None if recalling else "remote:" + key,
        )
        if ephemeral_recall:
            self.store.transient[task.id]["remote_query"] = payload["text"]
        plan = self.store.get("plan", task.id)
        if kind == "text":
            choices = [c for c in self.grid.search(plan["kind"]) if c.node_id == target]
            if choices:
                capability = choices[0]
        self.policy(session, capability, confirmed=capability.risk != "low")
        action = Action(
            new_id(),
            task.id,
            task.correlation_id,
            capability.id,
            plan["parameters"],
            task.id,
            session.node_id,
        )
        executor = self.h.session if target == self.h.node_id else self.sessions.get(target)
        if executor is None:
            raise PermissionError("executor session unavailable")
        authority = StandingAuthority(self.store, self.grid, self.h.runtime.relationship_id).bind(
            task.id, record(capability), executor
        )
        try:
            self.artifact_permission(
                session.id, executor, capability, parameters, delegated=authority is not None
            )
        except PermissionError:
            self.store.transition(
                task.id, TaskState.BLOCKED, blocker="Artifact read authority unavailable"
            )
            raise
        deadline = int((time() + 120) * 1000)
        workspace = (
            self.store.get("remote_device", target)["workspace"] if target != self.h.node_id else ""
        )
        review = fingerprint(
            {
                "action": record(action),
                "target": target,
                "workspace": workspace,
                "deadline_ms": deadline,
            }
        )
        row = {
            "task_id": task.id,
            "target": target,
            "requester": session.node_id,
            "requester_session": session.id,
            "capability": record(capability),
            "workspace": workspace,
            "deadline_ms": deadline,
            "review_digest": review,
            "approval_required": capability.risk != "low" and authority is None,
            "approved": capability.risk == "low" or authority is not None,
            "authority": authority,
            "event_id": new_id(),
            "occurred_at": time(),
            "text": "" if ephemeral_recall else payload["text"],
            "retain": payload["retain"],
            **({"source": "memory"} if recalling else {}),
        }
        with self.store.transaction():
            self.store.put("planned_action", task.id, record(action))
            self.store.put("action", action.id, record(action))
            self.store.put("remote_task", task.id, row)
            self.store.put("remote_admission", key, {"digest": digest, "task_id": task.id})
        self.retain(row, result=False)
        if not row["approval_required"]:
            self.start(task.id)
        return self.inspect(task.id, viewer_session=session.id)

    def submit_communication(
        self,
        session: SessionHandle,
        key: str,
        digest: str,
        payload: dict[str, Any],
        communication: Any,
    ) -> dict[str, Any]:
        capability = communication.capability
        self.policy(session, capability, confirmed=capability.risk != "low")
        if (
            not PersonalPolicy(self.store)
            .evaluate(
                "core.archive.retain",
                ("archive:retain",),
                frozenset(self.store.get("session", session.id)["scopes"]),
                {"source": "remote-grid", "relationship": self.h.runtime.relationship_id},
            )
            .allowed
        ):
            raise PermissionError("retention policy denied")
        with self.store.transaction():
            task = self.h.runtime.create(
                communication.intent,
                initiator=session.node_id,
                retry_budget=0,
                transient=True,
            )
            private = self.store.transient[task.id]
            private["review_parameters"] = communication.review
            private["connector_guard"] = lambda: self.authorize_communication(task.id)
            plan = self.store.get("plan", task.id)
            executor = self.h.executive.targets[capability.node_id][1]
            authority = StandingAuthority(
                self.store, self.grid, self.h.runtime.relationship_id
            ).bind(
                task.id,
                record(capability),
                executor,
            )
            action = Action(
                new_id(),
                task.id,
                task.correlation_id,
                capability.id,
                plan["parameters"],
                task.id,
                session.node_id,
            )
            deadline = int((time() + 120) * 1000)
            row = {
                "task_id": task.id,
                "target": capability.node_id,
                "requester": session.node_id,
                "requester_session": session.id,
                "capability": record(capability),
                "workspace": "",
                "deadline_ms": deadline,
                "review_digest": fingerprint(
                    {
                        "action": record(action),
                        "target": capability.node_id,
                        "workspace": "",
                        "deadline_ms": deadline,
                    }
                ),
                "private_review_digest": fingerprint(communication.review),
                "approval_required": capability.risk != "low" and authority is None,
                "approved": capability.risk == "low" or authority is not None,
                "authority": authority,
                "event_id": new_id(),
                "occurred_at": time(),
                "text": payload["text"],
                "source": "communication",
            }
            self.store.put("planned_action", task.id, record(action))
            self.store.put("action", action.id, record(action))
            self.store.put("remote_task", task.id, row)
            self.store.put("remote_admission", key, {"digest": digest, "task_id": task.id})
        self.retain(row, result=False)
        if not row["approval_required"]:
            self.start(task.id)
        return self.inspect(task.id)

    def authorize_communication(self, task_id: str) -> None:
        row = self.store.get("remote_task", task_id)
        self.h.archive.event(row["event_id"])
        if row["deadline_ms"] <= time() * 1000 or not self.review_matches(row):
            raise PermissionError("communication review expired or changed")
        requester = self.store.get("session", row["requester_session"])
        # The token is checked at admission; current persisted scopes and expiry fence execution.
        for identifier in (row["requester_session"], row.get("approval_session")):
            if identifier is None:
                continue
            session = self.store.get("session", identifier)
            node = self.store.get("node", session["node_id"])
            if session["revoked"] or node["revoked"] or session["expires_at"] <= time():
                raise PermissionError("communication owner session expired or revoked")
            if identifier == row.get("approval_session") and (
                "grid:approve" not in session["scopes"] or "grid:approve" not in node["scopes"]
            ):
                raise PermissionError("communication approver scope withdrawn")
        capability = Capability.from_dict(row["capability"])
        granted = frozenset(requester["scopes"]) & frozenset(
            self.store.get("node", row["requester"])["scopes"]
        )
        for operation in (capability.id, *capability.permissions):
            if (
                not PersonalPolicy(self.store)
                .evaluate(
                    operation,
                    capability.permissions,
                    granted,
                    {
                        "node": row["requester"],
                        "target": capability.node_id,
                        "source": "remote-grid",
                    },
                    confirmed=row["approved"],
                    confirmation_required=capability.risk != "low",
                )
                .allowed
            ):
                raise PermissionError("communication requester scope or policy withdrawn")
        if row["approval_required"] and (
            not row["approved"] or row.get("approval_expires_ms", 0) <= time() * 1000
        ):
            raise PermissionError("communication approval expired")

    def retain(self, row: dict[str, Any], *, result: bool) -> None:
        if not row.get("retain", True):
            return
        if result and row.get("source") == "memory":
            return  # Recalled answers remain derived from their original canonical sources.
        task = self.store.task(row["task_id"])
        content = row["text"]
        event_id = row["event_id"]
        if result:
            try:
                self.h.archive.event(event_id)
            except KeyError:
                return
            projection = self.inspect(task.id)
            content = json.dumps(
                {
                    "task_id": task.id,
                    "state": task.state,
                    "result": projection["result"],
                    "evidence": projection["evidence"],
                },
                sort_keys=True,
            )
            event_id = hashlib.sha256((row["event_id"] + ":result").encode()).hexdigest()[:32]
        self.h.archive.append(
            SourceEvent(
                self.h.runtime.relationship_id,
                content,
                "remote-grid:oscar" if result else "remote-grid:owner",
                row["occurred_at"],
                kind="remote_result" if result else "owner_turn",
                id=event_id,
                turn_id=row["event_id"],
                episode_id=row["event_id"],
                task_id=task.id,
                status=Epistemic.VERIFIED
                if result and task.state == TaskState.VERIFIED
                else Epistemic.REPORTED,
                sensitivity="personal",
            ),
            retain_authorized=True,
        )
        # Result episodes depend on their source turn so forget propagates to both.
        retained = self.h.archive.db.execute(
            "SELECT 1 FROM archive_memories WHERE relationship=? AND forgotten=0 "
            "AND json_extract(payload,'$.event_ids[0]')=? LIMIT 1",
            (self.h.runtime.relationship_id, event_id),
        ).fetchone()
        if retained is None:
            MemoryWriter(self.h.archive).retain(
                (event_id, row["event_id"]) if result else (event_id,),
                content,
                "episodic",
                retain_authorized=True,
                inferred=result,
            )

    def can_read(self, session: SessionHandle) -> bool:
        return all(
            "archive:read" in self.store.get(kind, identifier)["scopes"]
            for kind, identifier in (("session", session.id), ("node", session.node_id))
        )

    def inspect(
        self,
        task_id: str,
        *,
        redacted: bool = False,
        viewer_session: str | None = None,
    ) -> dict[str, Any]:
        row = self.store.get("remote_task", task_id)
        task = self.store.task(task_id)
        if task.state == TaskState.PLANNED and row["deadline_ms"] <= time() * 1000:
            task = self.store.transition(
                task.id,
                TaskState.BLOCKED,
                blocker="request or approval expired; review a fresh task",
            )
        action = self.store.get("planned_action", task_id)
        results = [r for r in self.store.all("result") if r["task_id"] == task_id]
        evidence = [r for r in self.store.all("evidence") if r["task_id"] == task_id]
        try:
            if row.get("source") == "executive":
                self.h.executive._row("executive_goal", row["goal_id"])
            else:
                self.h.archive.event(row["event_id"])
            forgotten = redacted and row.get("source") != "memory"
        except KeyError:
            forgotten = True
        if row.get("source") == "memory" and not row.get("retain", True):
            forgotten = not bool(self.store.transient.get(task_id))
        result = results[-1] if results and not forgotten else None
        if (
            row.get("source") == "communication"
            and not forgotten
            and viewer_session == row["requester_session"]
        ):
            private_result = self.store.transient.get(task_id, {}).get("result")
            if private_result is not None:
                try:
                    self.authorize_communication(task_id)
                except (PermissionError, KeyError):
                    pass
                else:
                    result = record(private_result)
        recalled: dict[str, Any] = {}
        transient_description = ""
        if row.get("source") == "memory":
            from .memory_executor import authorize_recall, recall_context, recall_text

            result = None
            recalled = {"response_status": Epistemic.UNKNOWN, "source_event_ids": []}
            if not forgotten and viewer_session is not None:
                try:
                    authorize_recall(self.h.runtime, task_id, viewer_session)
                    transient_description = self.store.transient.get(task_id, {}).get(
                        "remote_query", ""
                    )
                    private = self.store.transient.get(task_id, {}).get("result")
                    context = recall_context(
                        self.h.memory,
                        self.h.runtime.relationship_id,
                        self.store.transient.get(task_id, {}).get("remote_query", row["text"]),
                    )
                    if (
                        private
                        and private.success
                        and recall_text(context) == private.value
                        and context["memories"]
                    ):
                        result = record(private)
                        recalled = {
                            "response_status": Epistemic.INFERRED
                            if any(
                                item["status"] == Epistemic.INFERRED for item in context["memories"]
                            )
                            else Epistemic.RECALLED,
                            "source_event_ids": sorted(
                                {
                                    event
                                    for item in context["memories"]
                                    for event in item["event_ids"]
                                }
                            ),
                        }
                except (KeyError, PermissionError):
                    pass
        return {
            "task_id": task.id,
            "state": task.state,
            "retained_available": not forgotten and row.get("retain", True),
            "request_retained": row.get("retain", True),
            "description": (
                transient_description[:256] or "Historical request unavailable"
                if not row.get("retain", True)
                else "Retained interaction unavailable"
                if forgotten
                else row["text"][:256]
            ),
            "target": row["target"],
            "capability": action["capability_id"],
            "approval_required": task.state == TaskState.PLANNED
            and row["approval_required"]
            and not row["approved"]
            and not forgotten,
            "review_digest": row["review_digest"],
            "action_id": action["id"],
            "deadline_ms": row["deadline_ms"],
            "result": result,
            "evidence": evidence if not forgotten else [],
            "blocker": "Retained interaction unavailable" if forgotten else task.blocker,
            "generation": task.attempts,
            "correlation_id": task.correlation_id,
            **recalled,
        }

    def challenge(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        binding = self.require(session, "grid:approve")
        if (
            set(payload) != {"task_id", "operation"}
            or payload["operation"] != "approve"
            or not binding["owner_public_key"]
        ):
            raise PermissionError("enrolled native owner confirmation required")
        task_id = identifier(payload["task_id"])
        row, view = self.store.get("remote_task", task_id), self.inspect(task_id)
        if (
            view["state"] != TaskState.PLANNED
            or not view["approval_required"]
            or row["deadline_ms"] <= time() * 1000
        ):
            raise StateConflict("approval is stale or unavailable")
        review = json.dumps(
            self.store.transient.get(task_id, {}).get(
                "review_parameters", self.store.get("planned_action", task_id)["parameters"]
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        scope = "grid:approve"
        claim = {
            "version": 2,
            "node_id": session.node_id,
            "session_id": session.id,
            "operation": "approve",
            "scope": scope,
            "generation": view["generation"],
            "material": {
                "task_id": task_id,
                "target": row["target"],
                "digest": row["review_digest"],
            },
            "display_digest": display_digest("approve", scope, row["target"], review, row["text"]),
            "expires_at_ms": min(int((time() + 30) * 1000), row["deadline_ms"]),
            "nonce": new_id(),
        }
        encoded = base64.b64encode(
            json.dumps(claim, sort_keys=True, separators=(",", ":")).encode()
        ).decode()
        challenge_id = new_id()
        self.store.put("remote_approval", challenge_id, {"payload": encoded, "used": False})
        return {
            "challenge_id": challenge_id,
            "signing_payload": encoded,
            "expires_at_ms": claim["expires_at_ms"],
            "operation": "approve",
            "description": row["text"],
            "target": row["target"],
            "capability": view["capability"],
            "reason": "Exact scoped remote action",
            "consequence": "Execute only the reviewed operation on the enrolled device",
            "policy_reason": "Core and Worker recheck scoped Ask authority",
            "confirmation": "biometric_or_device_credential",
            "review": review,
            "exact_request": row["text"],
            "scope": scope,
            "generation": view["generation"],
        }

    def complete(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        binding = self.require(session, "grid:approve")
        if set(payload) != {"challenge_id", "signature"}:
            raise ValueError("exact approval signature required")
        approval_id = identifier(payload["challenge_id"])
        approval = self.store.get("remote_approval", approval_id)
        claim = json.loads(base64.b64decode(approval["payload"]))
        if (
            approval["used"]
            or claim["node_id"] != session.node_id
            or claim["session_id"] != session.id
            or claim["expires_at_ms"] <= time() * 1000
        ):
            raise PermissionError("stale or consumed approval")
        verify_signature(
            binding["owner_public_key"], payload["signature"], base64.b64decode(approval["payload"])
        )
        task_id = claim["material"]["task_id"]
        row = self.store.get("remote_task", task_id)
        view = self.inspect(task_id)
        if (
            view["state"] != TaskState.PLANNED
            or not view["approval_required"]
            or view["generation"] != claim["generation"]
            or row["review_digest"] != claim["material"]["digest"]
            or row["target"] != claim["material"]["target"]
            or not self.review_matches(row)
        ):
            raise StateConflict("reviewed plan changed")
        self.policy(session, Capability.from_dict(row["capability"]), confirmed=True)
        self.store.put("remote_approval", approval_id, {**approval, "used": True})
        self.store.put(
            "remote_task",
            task_id,
            {
                **row,
                "approved": True,
                "approval_session": session.id,
                "approval_node": session.node_id,
                "approval_expires_ms": claim["expires_at_ms"],
            },
        )
        if row.get("source") == "communication":
            from .executive import confirmation_digest

            self.store.put(
                "executive_confirmation",
                task_id,
                {
                    "digest": confirmation_digest(self.store, task_id),
                    "expires_at": claim["expires_at_ms"] / 1000,
                },
            )
        self.store.audit(
            task_id,
            "remote_owner_confirmed",
            {
                "node_id": session.node_id,
                "action_id": view["action_id"],
                "review_digest": row["review_digest"],
            },
        )
        self.start(task_id)
        return self.inspect(task_id)

    def review_matches(self, row: dict[str, Any]) -> bool:
        return bool(
            (
                row.get("source") != "communication"
                or row["private_review_digest"]
                == fingerprint(
                    self.store.transient.get(row["task_id"], {}).get("review_parameters")
                )
            )
            and row["review_digest"]
            == fingerprint(
                {
                    "action": self.store.get("planned_action", row["task_id"]),
                    "target": row["target"],
                    "workspace": row["workspace"],
                    "deadline_ms": row["deadline_ms"],
                }
            )
        )

    def start(self, task_id: str) -> None:
        if not self.slots.acquire(blocking=False):
            self.store.transition(
                task_id, TaskState.BLOCKED, blocker="remote execution capacity reached"
            )
            return
        row = self.store.get("remote_task", task_id)
        target = row["target"]
        mounted = (
            self.h.executive.targets.get(target) if row.get("source") == "communication" else None
        )
        session = (
            mounted[1]
            if mounted
            else self.h.session
            if target == self.h.node_id
            else self.sessions.get(target)
        )
        if session is None:
            self.slots.release()
            self.store.transition(
                task_id, TaskState.BLOCKED, blocker="Worker must reconnect before execution"
            )
            return

        def run() -> None:
            try:
                transport = (
                    mounted[0]
                    if mounted
                    else self.h.dispatcher
                    if target == self.h.node_id
                    else self.transport
                )
                self.h.runtime.run(task_id, {target: (transport, session)})
                # Snapshot repair and completion must retain one event and memory together.
                with self.lock:
                    self.retain(row, result=True)
            except Exception:
                from .cloud import diagnostic

                diagnostic("remote_task_failed", category="execution_or_retention_failed")
                task = self.store.task(task_id)
                if task.state in {
                    TaskState.EXECUTING,
                    TaskState.AWAITING_RESULT,
                    TaskState.RESULT_RECEIVED,
                    TaskState.VERIFYING,
                }:
                    self.store.transition(
                        task_id,
                        TaskState.UNKNOWN
                        if task.state == TaskState.VERIFYING
                        else TaskState.BLOCKED,
                        blocker="remote processing failed; inspect before retry",
                    )
                if task.lease_id:
                    self.grid.release(task.lease_id)
            finally:
                self.h.archive.close_thread()
                self.slots.release()

        self.threads = [t for t in self.threads if t.is_alive()]
        thread = Thread(target=run, name="oscar-remote-task", daemon=True)
        self.threads.append(thread)
        thread.start()

    def prepare_executive(self, envelope: Envelope, session: SessionHandle) -> None:
        """Bind a signed native responsibility to this exact live remote delivery."""
        from .executive import authorize_step

        with self.lock, self.store.transaction():
            try:
                self.store.get("remote_task", envelope.task_id)
                return
            except KeyError:
                pass
            task = self.store.task(envelope.task_id)
            plan = self.store.get("plan", task.id)
            try:
                execution = plan["executive"]
                owner = self.store.get("executive_owner", execution["goal_id"])
            except KeyError:
                raise PermissionError("signed native responsibility required") from None
            action = self.store.get("planned_action", task.id)
            if (
                record(envelope)["payload"] != action
                or envelope.node_id != session.node_id
                or envelope.session_id != session.id
                or task.lease_id != envelope.lease_id
            ):
                raise PermissionError("remote responsibility action or lease changed")
            capability = next(
                c
                for c in self.store.get("node", session.node_id)["capabilities"]
                if c["id"] == action["capability_id"]
            )
            authorize_step(self.store, self.grid, task.id, capability, session, self.h.memory)
            device = self.require(session, "execute")
            objective = self.store.get("objective", task.objective_id)
            parameters = action["parameters"]
            if capability["id"].startswith("android."):
                validate_android(capability["input_kind"], parameters)
                criterion = {
                    "kind": "remote_android",
                    "operation": capability["input_kind"],
                    **parameters,
                }
            elif capability["id"] in {"machine.files.read", "machine.files.write"}:
                criterion = {"kind": "remote_file", "path": parameters["path"]}
                if capability["id"] == "machine.files.write":
                    criterion["content"] = parameters["content"]
            elif capability["id"] in REMOTE_MACHINE_CAPABILITIES:
                validate_remote_machine(capability["input_kind"], parameters)
                criterion = {"kind": "remote_machine", "operation": capability["input_kind"]}
                if (
                    capability["input_kind"] in {"coding", "terminal_command"}
                    and "verification" in parameters
                ):
                    self.artifact_permission(
                        owner["session"],
                        session,
                        Capability.from_dict(capability),
                        parameters,
                        delegated=bool(owner.get("standing")),
                    )
                    criterion = {"kind": "remote_file", **parameters["verification"]}
                elif (
                    capability["id"]
                    in {
                        "machine.apps",
                        "machine.files.list",
                        "machine.files.search",
                        "machine.controls",
                    }
                    or capability["id"] == "machine.browser"
                    and parameters["request"].get("read_only")
                ) and machine_readback(capability["id"], parameters):
                    criterion["match_report"] = True
                elif machine_readback(capability["id"], parameters) is not None:
                    expected = parameters.get("verification", parameters["request"])
                    criterion["text"] = expected["text"]
                    if capability["id"] == "machine.browser":
                        criterion["url"] = expected["url"]
            else:
                raise PermissionError("remote responsibility verifier unavailable")
            self.store.put("objective", task.objective_id, {**objective, "criterion": criterion})
            authority = StandingAuthority(
                self.store, self.grid, self.h.runtime.relationship_id
            ).bind(task.id, capability, session)
            deadline = int((time() + 120) * 1000)
            review = fingerprint(
                {
                    "action": action,
                    "target": session.node_id,
                    "workspace": device["workspace"],
                    "deadline_ms": deadline,
                }
            )
            self.store.put(
                "remote_task",
                task.id,
                {
                    "task_id": task.id,
                    "source": "executive",
                    "goal_id": execution["goal_id"],
                    "target": session.node_id,
                    "requester": owner["node"],
                    "requester_session": owner["session"],
                    "capability": capability,
                    "workspace": device["workspace"],
                    "deadline_ms": deadline,
                    "review_digest": review,
                    "approval_required": False,
                    "approved": True,
                    "authority": authority,
                    "event_id": "",
                    "occurred_at": time(),
                    "text": objective["description"],
                },
            )

    def exchange(self, task_id: str, kind: str) -> dict[str, Any]:
        with self.lock:
            task = self.store.task(task_id)
            binding = self.store.get("remote_task", task_id)
            device = self.store.get("remote_device", binding["target"])
            identifier_ = new_id()
            row = {
                "id": identifier_,
                "kind": kind,
                "node_id": binding["target"],
                "session_id": device["session_id"],
                "task_id": task_id,
                "lease_id": task.lease_id,
                "state": "pending",
            }
            self.store.put("remote_delivery", identifier_, row)
        until = monotonic() + 35
        while not self.stop.wait(0.05):
            with self.lock:
                latest = self.store.get("remote_delivery", identifier_)
                if latest["state"] == "complete":
                    return dict(latest["result"])
                if latest["state"] == "uncertain" or self.store.task(task_id).state in {
                    TaskState.CANCELLED,
                    TaskState.BLOCKED,
                    TaskState.UNKNOWN,
                }:
                    raise StateConflict("remote delivery stopped; outcome requires inspection")
                if monotonic() > until or binding["deadline_ms"] <= time() * 1000:
                    self.store.put("remote_delivery", identifier_, {**latest, "state": "uncertain"})
                    raise StateConflict("remote response lost; inspect before retry")
        raise StateConflict("Core transport stopping; inspect before retry")

    def delivery_view(self, row: dict[str, Any]) -> dict[str, Any]:
        binding = self.store.get("remote_task", row["task_id"])
        action = self.store.get("planned_action", row["task_id"])
        return {
            k: row[k] for k in ("id", "kind", "node_id", "session_id", "task_id", "lease_id")
        } | {
            "action": action,
            "deadline_ms": binding["deadline_ms"],
            "workspace": binding["workspace"],
            "review_digest": binding["review_digest"],
            "approved": binding["approved"],
            "authority": binding.get("authority"),
            "parameters": (
                android_readback(action["parameters"])
                if binding["capability"]["id"].startswith("android.")
                else machine_readback(action["capability_id"], action["parameters"])
                if action["capability_id"] in REMOTE_MACHINE_CAPABILITIES
                else {"path": action["parameters"]["path"]}
            )
            if row["kind"] == "readback"
            else action["parameters"],
        }

    def check(self, session: SessionHandle, delivery_id: str) -> dict[str, Any]:
        self.require(session, "execute")
        row = self.store.get("remote_delivery", delivery_id)
        binding = self.store.get("remote_task", row["task_id"])
        # Forgotten source material cannot be resurfaced by a pending delivery.
        if binding.get("source") == "executive":
            from .executive import authorize_step

            authorize_step(
                self.store, self.grid, row["task_id"], binding["capability"], session, self.h.memory
            )
        else:
            self.h.archive.event(binding["event_id"])
        task = self.store.task(row["task_id"])
        lease = self.store.get("lease", row["lease_id"])
        if (
            row["node_id"] != session.node_id
            or row["session_id"] != session.id
            or row["state"] not in {"pending", "claimed"}
            or binding["deadline_ms"] <= time() * 1000
            or task.cancelled
            or task.lease_id != row["lease_id"]
            or not lease["active"]
            or lease["expires_at"] <= time()
            or lease["node_id"] != session.node_id
            or not self.review_matches(binding)
        ):
            raise PermissionError("remote lease, task or target denied")
        expected = TaskState.AWAITING_RESULT if row["kind"] == "action" else TaskState.VERIFYING
        if task.state != expected:
            raise PermissionError("task no longer accepts delivery")
        cap = Capability.from_dict(binding["capability"])
        parameters = self.store.get("planned_action", task.id)["parameters"]
        if cap.input_kind == "browser" and "account_id" in parameters:
            self.h.accounts.check(parameters["account_id"], parameters["account_generation"])
        authority = StandingAuthority(self.store, self.grid, self.h.runtime.relationship_id)
        authority.check_task(task.id, binding["capability"], session)
        if binding.get("authority") is not None and not authority.permits(
            binding["capability"], session, task_id=task.id
        ):
            raise PermissionError("delegated authority unavailable")
        if not any(
            node["id"] == session.node_id and binding["capability"] in node["capabilities"]
            for node in self.grid.nodes()
        ):
            raise PermissionError("capability withdrawn")
        self.policy(session, cap, confirmed=binding["approved"])
        requester = self.store.get("session", binding["requester_session"])
        requester_node = self.store.get("node", binding["requester"])
        self.artifact_permission(
            binding["requester_session"],
            session,
            cap,
            parameters,
            delegated=binding.get("authority") is not None,
        )
        if requester["revoked"] or requester["expires_at"] <= time() or requester_node["revoked"]:
            raise PermissionError("requester authority expired or revoked")
        granted = frozenset(requester["scopes"]) & frozenset(requester_node["scopes"])
        if (
            not PersonalPolicy(self.store)
            .evaluate(
                cap.id,
                cap.permissions,
                granted,
                {"node": binding["requester"], "target": session.node_id, "source": "remote-grid"},
                confirmed=binding["approved"],
                confirmation_required=cap.risk != "low",
            )
            .allowed
        ):
            raise PermissionError("requester permission or Personal Policy changed")
        if binding["approval_required"]:
            approver = self.store.get("session", binding.get("approval_session", ""))
            approver_node = self.store.get("node", binding.get("approval_node", ""))
            if (
                not binding["approved"]
                or approver["revoked"]
                or approver_node["revoked"]
                or approver["expires_at"] <= time()
                or "grid:approve" not in approver["scopes"]
                or "grid:approve" not in approver_node["scopes"]
                or (row["kind"] == "action" and binding["approval_expires_ms"] <= time() * 1000)
            ):
                raise PermissionError("approval expired or revoked")
        return row

    def deliver(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        delivery_id = identifier(payload["delivery_id"])
        row = self.store.get("remote_delivery", delivery_id)
        if row["node_id"] != session.node_id or row["session_id"] != session.id:
            raise PermissionError("receipt belongs to another target")
        self.require(session, "execute")
        if row["state"] == "complete":
            if row["result"] != payload["result"]:
                raise StateConflict("receipt identity reused")
            return {"accepted": True}
        self.check(session, delivery_id)
        value = payload["result"]
        if (
            not isinstance(value, dict)
            or len(json.dumps(value).encode()) > 20000
            or redact_runtime_secrets(json.dumps(value)) != json.dumps(value)
        ):
            raise ValueError("bounded private-safe receipt required")
        if row["kind"] == "action":
            parsed = parse_result(value)
            action = self.store.get("planned_action", row["task_id"])
            if (
                parsed.task_id != row["task_id"]
                or parsed.action_id != action["id"]
                or parsed.correlation_id != action["correlation_id"]
                or parsed.executor != action["capability_id"]
                or parsed.value is not None
                and (not isinstance(parsed.value, str) or len(parsed.value.encode()) > 8192)
            ):
                raise ValueError("receipt correlation rejected")
        elif (
            set(value) != {"content"}
            or not isinstance(value["content"], str)
            or len(value["content"].encode()) > 8192
        ):
            raise ValueError("bounded independent readback required")
        self.store.put(
            "remote_delivery", delivery_id, {**row, "state": "complete", "result": value}
        )
        return {"accepted": True}

    def presence(self, session: SessionHandle) -> dict[str, Any] | None:
        try:
            self.require(session, "presence:read")
        except PermissionError:
            return None
        permission = PersonalPolicy(self.store).evaluate(
            "core.presence.read",
            ("presence:read",),
            frozenset(self.store.get("session", session.id)["scopes"]),
            {"node": session.node_id, "source": "remote-grid"},
        )
        if not permission.allowed or self.h.runtime.presence is None:
            return None
        return self.h.runtime.presence.snapshot()

    def snapshot(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        self.require(session, "grid:inspect")
        can_read = self.can_read(session)
        if (
            set(payload) - {"cursor", "archive_generation"}
            or type(payload.get("cursor", 0)) is not int
            or payload.get("cursor", 0) < 0
        ):
            raise ValueError("bounded durable cursor required")
        archive = self.h.archive
        archive.purge_expired_events(self.h.runtime.relationship_id)
        with self.store.lock:
            recent = [
                json.loads(r[0])
                for r in self.store.db.execute(
                    "SELECT data FROM records WHERE kind='remote_task' ORDER BY rowid DESC LIMIT 12"
                )
            ][::-1]
        visible = []
        for row in recent:
            if not row.get("retain", True):
                from .memory_executor import authorize_recall

                try:
                    authorize_recall(self.h.runtime, row["task_id"], session.id)
                except (KeyError, PermissionError):
                    continue
                if not self.store.transient.get(row["task_id"]):
                    continue
            visible.append(row)
        recent = visible
        for row in recent:
            if row.get("source") == "executive":
                continue  # Responsibility storage does not grant conversation retention.
            task = self.store.task(row["task_id"])
            result_id = hashlib.sha256((row["event_id"] + ":result").encode()).hexdigest()[:32]
            if (
                task.state
                in {
                    TaskState.VERIFIED,
                    TaskState.FAILED,
                    TaskState.BLOCKED,
                    TaskState.UNKNOWN,
                    TaskState.CANCELLED,
                }
                and archive.db.execute(
                    "SELECT 1 FROM archive_events WHERE id=?", (result_id,)
                ).fetchone()
                is None
            ):
                self.retain(row, result=True)
        # Tombstones, events and retained task detail come from one committed archive view.
        with archive.db:
            archive.db.execute("BEGIN")
            return self._snapshot_projection(session, payload, recent, can_read)

    def _snapshot_projection(
        self,
        session: SessionHandle,
        payload: dict[str, Any],
        recent: list[dict[str, Any]],
        can_read: bool,
    ) -> dict[str, Any]:
        archive = self.h.archive
        epoch = fingerprint(
            {
                "archive_read": can_read,
                "tombstones": list(
                    archive.db.execute("SELECT id,forgotten_at FROM archive_tombstones ORDER BY id")
                ),
            }
        )
        reset = not can_read or payload.get("archive_generation", epoch) != epoch
        cursor = 0 if reset else payload.get("cursor", 0)
        candidates = (
            archive.db.execute(
                "SELECT rowid,payload FROM archive_events WHERE relationship=? AND forgotten=0 "
                "AND rowid>? ORDER BY rowid LIMIT 100",
                (self.h.runtime.relationship_id, cursor),
            ).fetchall()
            if can_read
            else []
        )
        rows: list[tuple[int, str]] = []
        size = 0
        for sequence, raw in candidates:
            if rows and size + len(raw.encode()) > 196608:
                break
            rows.append((sequence, raw))
            size += len(raw.encode())
        events = []
        for sequence, raw in rows:
            event = json.loads(raw)
            if event["kind"] not in {
                "owner_turn",
                "remote_result",
                "conversation_owner",
                "conversation_oscar",
            }:
                continue
            text = event["content"]
            if event["kind"] == "remote_result":
                try:
                    archive.event(event["turn_id"])
                except KeyError:
                    continue
                projection = json.loads(text)
                receipt = projection.get("result") or {}
                value = receipt.get("value")
                text = str(value) if value is not None else "Task " + projection["state"]
            events.append(
                {
                    "event_id": event["id"],
                    "sequence": sequence,
                    "turn_id": event["turn_id"],
                    "task_id": event["task_id"],
                    "speaker": "oscar"
                    if event["kind"] in {"remote_result", "conversation_oscar"}
                    else "owner",
                    "text": text,
                    "status": event["status"],
                    "occurred_at": event["occurred_at"],
                }
            )
        tasks = [
            self.inspect(row["task_id"], redacted=not can_read, viewer_session=session.id)
            for row in recent
        ]
        snapshot = {
            "version": 2,
            "core_id": self.core.config.core_id,
            "node_id": session.node_id,
            "relationship_id": self.h.runtime.relationship_id,
            "nodes": self.grid.nodes(),
            "tasks": tasks,
            "events": events,
            "cursor": rows[-1][0] if rows else cursor,
            "reset": reset,
            "archive_generation": epoch,
            "providers": self.core.status()["providers"],
            "observed_at_ms": int(time() * 1000),
        }
        presence = self.presence(session)
        if "grid:approve" in self.store.get("session", session.id)["scopes"]:
            from .assistance import Assistance
            from .connections import snapshot as connections_snapshot

            snapshot["connections"] = connections_snapshot(self.h)
            snapshot["executive"] = {
                **self.h.executive.snapshot(),
                "management": Assistance(self.h).snapshot(
                    frozenset(self.store.get("session", session.id)["scopes"])
                    & frozenset(self.store.get("node", session.node_id)["scopes"]),
                    session.node_id,
                ),
            }
        authority = StandingAuthority(
            self.store, self.grid, self.h.runtime.relationship_id
        ).snapshot()
        snapshot["operating"] = {
            "access": {"ask": "Ask", "secure": "Secure", "full": "Full Access"}[authority["mode"]],
            "secure": "signed_delegation_available",
            "full_access": "signed_delegation_available",
            "awareness": self.h.world.sentry.settings().mode.value,
            "sentry": self.h.world.sentry.settings().state.value,
            "worker_autonomy": "scoped",
            "automations": "signed_authoring",
        }
        if presence is not None:
            snapshot["presence"] = presence
        while len(json.dumps(snapshot).encode()) > 245760:
            if len(events) > 1:
                events.pop()
                snapshot["cursor"] = events[-1]["sequence"]
            elif len(tasks) > 1:
                tasks.pop(0)
            else:
                raise StateConflict("Grid projection exceeds response bound")
        return snapshot


def main() -> None:
    from .cloud import CloudConfig, CloudCore, credential_output

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["invite"])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--role", choices=["desktop", "mobile"], required=True)
    parser.add_argument("--installation", required=True)
    parser.add_argument("--public-key-file", type=Path, required=True)
    parser.add_argument("--owner-key-file", type=Path)
    parser.add_argument("--workspace", default="")
    parser.add_argument("--retain", action="store_true")
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--android-control", action="store_true")
    parser.add_argument("--machine-control", action="store_true")
    parser.add_argument("--screen-capture", action="store_true")
    parser.add_argument("--screen-retain", action="store_true")
    parser.add_argument("--connector-control", action="store_true")
    parser.add_argument("--memory-control", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    core = CloudCore(CloudConfig.load(args.config), start_services=False)
    try:
        with credential_output(args.output) as (output, _):
            invitation = create_invitation(
                core,
                args.node,
                args.role,
                args.installation,
                args.public_key_file.read_text(encoding="utf-8").strip(),
                args.workspace,
                args.retain,
                args.owner_key_file.read_text(encoding="utf-8").strip()
                if args.owner_key_file
                else None,
                recover=args.recover,
                android_control=args.android_control,
                machine_control=args.machine_control,
                connector_control=args.connector_control,
                memory_control=args.memory_control,
                screen_capture=args.screen_capture,
                screen_retain=args.screen_retain,
            )
            json.dump(invitation, output)
    finally:
        core.close()
    print(json.dumps({"event": "remote_invitation_written", "role": args.role}))


if __name__ == "__main__":
    main()
