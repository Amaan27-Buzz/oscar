"""Sunday is a scoped client of the existing Core, never a second task engine."""

import base64
import hashlib
import json
import re
import secrets
import ssl
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
from threading import RLock, Thread
from typing import Any

from .contracts import Epistemic, TaskState, new_id, record
from .grid import NodeRole, SessionHandle
from .jev import Intent
from .owner_control import OwnerControl
from .policy import PersonalPolicy
from .runtime import Runtime
from .storage import StateConflict
from .transport import Transport
from .voice_core import addition_intent


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def public_key(encoded: str) -> Any:
    # Optional platform security executor; importing OSCAR never requires it.
    serialization = import_module("cryptography.hazmat.primitives.serialization")
    rsa = import_module("cryptography.hazmat.primitives.asymmetric.rsa")

    if len(encoded) > 2000:
        raise ValueError("owner key exceeds bound")
    key = serialization.load_der_public_key(base64.b64decode(encoded, validate=True))
    if not isinstance(key, rsa.RSAPublicKey) or not 2048 <= key.key_size <= 4096:
        raise ValueError("supported owner RSA key required")
    return key


class Sunday:
    def __init__(
        self,
        runtime: Runtime,
        policy: PersonalPolicy,
        targets: Mapping[str, tuple[Transport, SessionHandle]],
    ):
        self.runtime, self.policy, self.targets = runtime, policy, targets
        self.store, self.grid = runtime.store, runtime.grid
        # ponytail: serialized admission, per-node locks if owner-control throughput requires it.
        self.lock = RLock()

    def register_owner_key(
        self, session: SessionHandle, encoded: str, *, owner_authorized: bool
    ) -> None:
        """Trusted Core enrollment only. Deliberately absent from the remote API."""
        if not owner_authorized:
            raise PermissionError("trusted owner enrollment required")
        self.authenticate(session, "sunday:connect")
        public_key(encoded)
        self.store.put(
            "sunday_key",
            session.node_id,
            {"session_id": session.id, "public_key": encoded},
        )
        self.store.audit("", "sunday_key_registered", {"node_id": session.node_id})

    def authenticate(self, session: SessionHandle, scope: str) -> None:
        self.grid.authenticate(session, scope)
        if self.store.get("node", session.node_id)["role"] != NodeRole.SUNDAY:
            raise PermissionError("Sunday role required")

    def grants(self, session: SessionHandle) -> frozenset[str]:
        return frozenset(str(x) for x in self.store.get("session", session.id)["scopes"])

    def target(self, session: SessionHandle, task_id: str) -> str:
        task = self.store.task(task_id)
        if task.lease_id:
            target = str(self.store.get("lease", task.lease_id)["node_id"])
        else:
            association = self.store.get("sunday_task", task_id)
            if association["node_id"] != session.node_id:
                raise PermissionError("task belongs to another surface")
            target = str(association["target"])
        if target not in self.targets:
            raise PermissionError("target unavailable to this Core adapter")
        return target

    def inspect(self, session: SessionHandle, task_id: str) -> dict[str, Any]:
        target = self.target(session, task_id)
        self.authenticate(session, "control:inspect:" + target)
        task = self.store.task(task_id)
        node = next(n for n in self.grid.nodes() if n["id"] == target)
        objective = self.store.get("objective", task.objective_id)
        view = {
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "state": task.state,
            "description": str(objective["description"])[:256],
            "target": target,
            "node_status": node["status"],
            "blocker": task.blocker,
            "evidence_ids": [
                e["id"] for e in self.store.all("evidence") if e["task_id"] == task.id
            ],
            "observed_at_ms": round(self.grid.clock() * 1000),
        }
        if (
            task.state == TaskState.VERIFIED
            and self.store.get("plan", task_id)["kind"] == "addition"
        ):
            results = [r for r in self.store.all("result") if r["task_id"] == task_id]
            if results:
                view["value"] = results[-1]["value"]
        return view

    def descriptor(self, session: SessionHandle, task_id: str) -> dict[str, Any]:
        view = self.inspect(session, task_id)
        task = self.store.task(task_id)
        return {
            "task": record(task),
            "plan": self.store.get("plan", task_id),
            "target": view["target"],
        }

    def challenge(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        operation = payload.get("operation")
        if operation in {"approve", "cancel"} and set(payload) == {"operation", "task_id"}:
            task_id = str(payload["task_id"])
            descriptor = self.descriptor(session, task_id)
            target = str(descriptor["target"])
            scope = "control:" + str(operation) + ":" + target
            self.authenticate(session, scope)
            material = {"task_id": task_id, "digest": fingerprint(descriptor), "target": target}
            description = self.inspect(session, task_id)["description"]
        elif operation == "reply" and set(payload) == {
            "operation",
            "package",
            "key_hash",
            "text_hash",
        }:
            self.authenticate(session, "notifications:reply")
            if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", str(payload["package"])):
                raise ValueError("invalid notification source")
            if any(
                not re.fullmatch(r"[a-f0-9]{64}", str(payload[k]))
                for k in ("key_hash", "text_hash")
            ):
                raise ValueError("notification hashes required")
            material = {k: payload[k] for k in ("package", "key_hash", "text_hash")}
            scope = "notifications:reply"
            description = "Reply to the exposed notification from " + str(payload["package"])
        else:
            raise ValueError("unsupported owner decision")
        key = self.store.get("sunday_key", session.node_id)
        if key["session_id"] != session.id:
            raise PermissionError("current session key enrollment required")
        identifier = new_id()
        expires = round((self.grid.clock() + 30) * 1000)
        body = json.dumps(
            {
                "version": 1,
                "node_id": session.node_id,
                "session_id": session.id,
                "nonce": secrets.token_hex(32),
                "operation": operation,
                "scope": scope,
                "material": material,
                "expires_at_ms": expires,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        encoded = base64.b64encode(body).decode()
        self.store.put(
            "sunday_challenge",
            identifier,
            {
                "node_id": session.node_id,
                "session_id": session.id,
                "payload": encoded,
                "used": False,
            },
        )
        return {
            "challenge_id": identifier,
            "signing_payload": encoded,
            "expires_at_ms": expires,
            "operation": operation,
            "description": description,
        }

    def complete(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        InvalidSignature = import_module("cryptography.exceptions").InvalidSignature
        hashes = import_module("cryptography.hazmat.primitives.hashes")
        padding = import_module("cryptography.hazmat.primitives.asymmetric.padding")

        if set(payload) != {"challenge_id", "signature"}:
            raise ValueError("invalid owner signature envelope")
        identifier = str(payload["challenge_id"])
        challenge = self.store.get("sunday_challenge", identifier)
        body = base64.b64decode(challenge["payload"], validate=True)
        claim = json.loads(body)
        self.authenticate(session, str(claim["scope"]))
        if (
            challenge["used"]
            or challenge["node_id"] != session.node_id
            or challenge["session_id"] != session.id
            or claim["expires_at_ms"] <= self.grid.clock() * 1000
        ):
            raise PermissionError("owner challenge stale or already consumed")
        key = self.store.get("sunday_key", session.node_id)
        if key["session_id"] != session.id:
            raise PermissionError("owner key session changed")
        try:
            public_key(key["public_key"]).verify(
                base64.b64decode(str(payload["signature"]), validate=True),
                body,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
        except (InvalidSignature, ValueError):
            raise PermissionError("owner signature rejected") from None
        operation, material = claim["operation"], claim["material"]
        permission: tuple[str, ...]
        if operation in {"approve", "cancel"}:
            task_id, target = material["task_id"], material["target"]
            if fingerprint(self.descriptor(session, task_id)) != material["digest"]:
                raise StateConflict("task or plan changed; review a new challenge")
            permission = ("math",) if operation == "approve" else ("control:cancel:" + target,)
            policy_operation = "math.add" if operation == "approve" else "sunday.cancel"
        else:
            task_id = ""
            permission = ("notifications:reply", "communications:send")
            policy_operation = "notification.reply"
        context = {"node": session.node_id, "source": "sunday"}
        if operation == "reply":
            context.update(app=str(material["package"]), source=str(material["package"]))
        else:
            context["target"] = str(material["target"])
        decision = self.policy.evaluate(
            policy_operation,
            permission,
            self.grants(session),
            context,
            confirmed=True,
            confirmation_required=True,
        )
        if not decision.allowed:
            raise PermissionError("owner decision blocked by permission or Personal Policy")
        with self.store.transaction():
            current = self.store.get("sunday_challenge", identifier)
            if current["used"]:
                raise StateConflict("owner challenge replay")
            current["used"] = True
            self.store.put("sunday_challenge", identifier, current)
        self.store.audit(
            task_id,
            "sunday_owner_confirmed",
            {"node_id": session.node_id, "operation": operation, "challenge_id": identifier},
        )
        if operation == "approve":
            association = self.store.get("sunday_task", task_id)
            if (
                association["node_id"] != session.node_id
                or self.store.get("plan", task_id)["kind"] != "addition"
                or self.store.task(task_id).state != TaskState.PLANNED
            ):
                raise PermissionError("foundation approves only its bounded Core addition plans")
            self.runtime.run(task_id, self.targets)
            return self.inspect(session, task_id)
        if operation == "cancel":
            task = self.store.task(task_id)
            if task.lease_id:
                transport, target_session = self.targets[material["target"]]
                OwnerControl(
                    self.store, self.grid, session, target_session, transport, self.runtime
                ).control(task_id, "cancel")
            else:
                self.runtime.cancel(task_id)
            return self.inspect(session, task_id)
        # A scoped target permit is authority, not proof a notification was sent or delivered.
        return {
            "permit": {
                **material,
                "id": identifier,
                "issued_at_ms": round(self.grid.clock() * 1000),
                "expires_at_ms": round((self.grid.clock() + 10) * 1000),
            },
            "status": Epistemic.REPORTED,
            "verification": "native delivery NOT_VERIFIED",
        }

    def request(self, session: SessionHandle, data: dict[str, Any]) -> dict[str, Any]:
        if (
            set(data) != {"version", "operation", "request_id", "payload"}
            or type(data["version"]) is not int
            or data["version"] != 1
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", str(data["request_id"]))
            or not isinstance(data["payload"], dict)
        ):
            raise ValueError("invalid bounded Sunday request")
        self.authenticate(session, "sunday:connect")
        operation, payload = data["operation"], data["payload"]
        with self.lock:
            # Hash-only admission identity; private request bodies and tokens are never retained.
            receipt_id = session.node_id + ":" + str(data["request_id"])
            digest = fingerprint(data)
            if operation in {"text", "complete"}:
                try:
                    previous = self.store.get("sunday_receipt", receipt_id)
                except KeyError:
                    previous = None
                if previous:
                    if previous["digest"] != digest:
                        raise StateConflict("request identity reused with a different body")
                    return {"replayed": True, "inspect_required": True}
            if operation == "snapshot" and not payload:
                self.authenticate(session, "sunday:inspect")
                self.grid.heartbeat(session)
                tasks = []
                for task_row in self.store.all("task")[-100:]:
                    try:
                        tasks.append(self.inspect(session, task_row["id"]))
                    except (PermissionError, KeyError):
                        continue
                response = {
                    "nodes": self.grid.nodes(),
                    "tasks": tasks,
                    "observed_at_ms": round(self.grid.clock() * 1000),
                }
            elif operation == "text" and set(payload) == {"text"}:
                self.authenticate(session, "sunday:text")
                text = payload["text"]
                if not isinstance(text, str) or not 0 < len(text) <= 1000:
                    raise ValueError("bounded text required")
                expression = addition_intent(text)
                decision = self.policy.evaluate("math.add", ("math",), self.grants(session))
                candidates = [c for c in self.grid.search("addition") if c.node_id in self.targets]
                if not expression or not decision.allowed or not candidates:
                    response = {
                        "state": TaskState.BLOCKED,
                        "epistemic": Epistemic.UNKNOWN,
                        "message": (
                            "This foundation supports permitted integer addition only; "
                            "no task executed."
                        ),
                    }
                else:
                    self.authenticate(session, "control:inspect:" + candidates[0].node_id)
                    if (
                        sum(
                            self.store.task(row["id"]).state == TaskState.PLANNED
                            for row in self.store.all("sunday_task")
                            if row["node_id"] == session.node_id
                        )
                        >= 32
                    ):
                        raise StateConflict("pending owner task bound reached")
                    task = self.runtime.create(Intent(expression), initiator="owner-sunday")
                    self.store.put(
                        "sunday_task",
                        task.id,
                        {
                            "id": task.id,
                            "node_id": session.node_id,
                            "target": candidates[0].node_id,
                        },
                    )
                    response = self.inspect(session, task.id)
                    response["approval_required"] = True
            elif operation == "inspect" and set(payload) == {"task_id"}:
                response = self.inspect(session, str(payload["task_id"]))
            elif operation == "challenge":
                response = self.challenge(session, payload)
            elif operation == "complete":
                response = self.complete(session, payload)
            else:
                raise ValueError("unsupported Sunday operation")
            if operation in {"text", "complete"}:
                self.store.put("sunday_receipt", receipt_id, {"digest": digest})
            return response


class SundayServer:
    """Loopback software acceptance adapter. Non-loopback deployment is not implemented."""

    def __init__(self, core: Sunday, tls: ssl.SSLContext | None = None):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                self.connection.settimeout(5)
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    auth = self.headers.get("Authorization", "")
                    if (
                        self.path != "/v1/sunday"
                        or not 0 < length <= 32768
                        or not auth.startswith("Bearer ")
                    ):
                        raise ValueError("invalid Sunday request")
                    session = SessionHandle(
                        self.headers.get("X-Oscar-Session", ""),
                        self.headers.get("X-Oscar-Node", ""),
                        auth[7:],
                    )
                    body = json.dumps(
                        core.request(session, json.loads(self.rfile.read(length))), allow_nan=False
                    ).encode()
                    self.send_response(200)
                except (ValueError, TypeError, KeyError, PermissionError, StateConflict):
                    body = b'{"error":"request rejected; refresh trusted Core state"}'
                    self.send_response(403)
                except Exception:
                    body = b'{"error":"Core unavailable; outcome unknown; inspect before retry"}'
                    self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        if tls:
            self.server.socket = tls.wrap_socket(self.server.socket, server_side=True)
        self.url = ("https" if tls else "http") + f"://127.0.0.1:{self.server.server_port}"
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "SundayServer":
        self.thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
