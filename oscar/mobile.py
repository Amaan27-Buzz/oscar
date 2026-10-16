"""OSCAR Mobile is a scoped surface of the existing Core, never a second task engine.

Legacy sunday_* record keys remain stable to preserve enrollment, receipts and replay fences.
"""

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

from .contracts import Epistemic, Task, TaskState, new_id, record
from .grid import NodeRole, SessionHandle
from .jev import ExecutionClass, Intent, decide
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


def display_digest(*fields: str) -> str:
    """Length-framed UTF-8 binds the exact displayed decision to the signed claim."""
    digest = hashlib.sha256()
    for field in fields:
        encoded = field.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


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


class Mobile:
    source = "mobile"

    def approvable(self, task_id: str) -> bool:
        return self.store.get("plan", task_id)["kind"] in {
            "addition",
            "model_reasoning",
            "live_source",
        }

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
        self.store.task_resources.add(self)

    def task_transitioned(self, task: Task) -> None:
        if task.state not in {
            TaskState.PLANNED,
            TaskState.EXECUTING,
            TaskState.AWAITING_RESULT,
            TaskState.RESULT_RECEIVED,
            TaskState.VERIFYING,
        } and self.store.transient.get(task.id, {}).get("discarded"):
            self.store.transient.pop(task.id, None)

    def private_for(self, session: SessionHandle, task_id: str) -> dict[str, Any]:
        try:
            association = self.store.get("sunday_task", task_id)
        except KeyError:
            return {}
        private = self.store.transient.get(task_id, {})
        if (
            association.get("node_id") != session.node_id
            or association.get("session_id") != session.id
            or private.get("discarded")
        ):
            return {}
        return private

    def register_owner_key(
        self, session: SessionHandle, encoded: str, *, owner_authorized: bool
    ) -> None:
        """Trusted Core enrollment only. Deliberately absent from the remote API."""
        if not owner_authorized:
            raise PermissionError("trusted owner enrollment required")
        self.authenticate(session, "mobile:connect")
        public_key(encoded)
        self.store.put(
            "sunday_key",
            session.node_id,
            {"session_id": session.id, "public_key": encoded},
        )
        self.store.audit("", "sunday_key_registered", {"node_id": session.node_id})

    def authenticate(self, session: SessionHandle, scope: str) -> None:
        # Preserve existing scoped enrollments; never widen their grants during a rename.
        if scope.startswith("mobile:") and scope not in self.grants(session):
            scope = scope.replace("mobile:", "sunday:", 1)
        self.grid.authenticate(session, scope)
        if self.store.get("node", session.node_id)["role"] not in {
            NodeRole.MOBILE,
            NodeRole.SUNDAY,
        }:
            raise PermissionError("Mobile role required")

    def grants(self, session: SessionHandle) -> frozenset[str]:
        return frozenset(str(x) for x in self.store.get("session", session.id)["scopes"])

    def admit(self, session: SessionHandle, data: dict[str, Any]) -> bool:
        """Hash-only at-most-once admission. A crash requires inspection, never blind replay."""
        identifier = session.node_id + ":" + str(data["request_id"])
        digest = fingerprint(data)
        with self.lock:
            try:
                previous = self.store.get("sunday_receipt", identifier)
            except KeyError:
                previous = None
            if previous:
                if previous["digest"] != digest:
                    raise StateConflict("request identity reused with a different body")
                return False
            self.store.put("sunday_receipt", identifier, {"digest": digest})
        return True

    def target(self, session: SessionHandle, task_id: str) -> str:
        task = self.store.task(task_id)
        if task.lease_id:
            target = str(self.store.get("lease", task.lease_id)["node_id"])
        else:
            association = self.store.get("sunday_task", task_id)
            # Inspect grants authorize shared task readback; approval ownership is separate.
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
        private = self.private_for(session, task_id)
        association = next(
            (row for row in self.store.all("sunday_task") if row["id"] == task_id), None
        )
        description = (
            private.get("request", private["objective"].description)
            if private
            else objective["description"]
        )
        if association and not private:
            description = "Private OSCAR interaction"
        view = {
            "task_id": task.id,
            "correlation_id": task.correlation_id,
            "state": task.state,
            "description": str(description)[:256],
            "target": target,
            "node_status": node["status"],
            "blocker": task.blocker,
            "evidence_ids": [
                e["id"] for e in self.store.all("evidence") if e["task_id"] == task.id
            ],
            "observed_at_ms": round(self.grid.clock() * 1000),
            "generation": task.attempts,
            "actions": [],
        }
        actions = []
        grants = self.grants(session)
        owned = any(
            row["id"] == task_id and row["node_id"] == session.node_id
            for row in self.store.all("sunday_task")
        )
        owned = owned and self.approvable(task_id)
        if owned and task.state == TaskState.PLANNED:
            if "control:approve:" + target in grants:
                if private:
                    actions.append("approve")
                actions.append("deny")
        if task.state not in {TaskState.VERIFIED, TaskState.FAILED, TaskState.CANCELLED}:
            if "control:cancel:" + target in grants:
                actions.append("cancel")
        if owned and private and task.state in {TaskState.BLOCKED, TaskState.UNKNOWN}:
            if task.attempts < task.retry_budget + 1 and "control:approve:" + target in grants:
                actions.append("retry")
        view["actions"] = actions
        try:
            self.store.get("desktop_task", task_id)
            view["origin_surface"] = "Desktop"
        except KeyError:
            view["origin_surface"] = "Mobile" if association else "Core"
        view["origin_node"] = association.get("node_id") if association else None
        lease = self.store.get("lease", task.lease_id) if task.lease_id else None
        live_lease = bool(
            lease
            and lease["active"]
            and lease["expires_at"] > self.grid.clock()
            and node["status"] == "online"
            and task.state
            in {
                TaskState.EXECUTING,
                TaskState.AWAITING_RESULT,
                TaskState.RESULT_RECEIVED,
                TaskState.VERIFYING,
            }
        )
        view["ownership"] = (
            "leased"
            if live_lease
            else "none"
            if task.state
            in {
                TaskState.VERIFIED,
                TaskState.FAILED,
                TaskState.CANCELLED,
                TaskState.PARTIALLY_VERIFIED,
            }
            else "expired"
            if lease
            else "planned"
        )
        view["artifacts"] = []
        try:
            checkpoint = self.store.get("worker_checkpoint", task_id)
            try:
                action = self.store.get("planned_action", task_id)
            except KeyError:
                action = {}
            view["progress"] = {
                "fraction": checkpoint["fraction"],
                "step": checkpoint["step"] if private else "Worker checkpoint available",
                "status": Epistemic.REPORTED,
                "current": bool(
                    live_lease
                    and checkpoint.get("lease_id") == task.lease_id
                    and checkpoint.get("action_id") == action.get("id")
                    and 0 <= self.grid.clock() - checkpoint.get("observed_at", 0) <= 30
                ),
            }
        except KeyError:
            view["progress"] = None
        result = private.get("result")
        if result and result.artifact:
            artifact = result.artifact
            view["artifacts"] = [
                {
                    "id": artifact.id,
                    "kind": artifact.kind,
                    "status": artifact.status,
                    "content_hash": artifact.content_hash,
                }
            ]
        if result and result.success and task.state != TaskState.CANCELLED:
            if (
                task.state == TaskState.VERIFIED
                and self.store.get("plan", task_id)["kind"] == "addition"
            ):
                view["value"] = result.value
            elif isinstance(result.value, str):
                view["response"] = result.value[:8192]
                view["response_truncated"] = len(result.value) > 8192
                view["response_status"] = Epistemic.REPORTED
        elif not association and (
            task.state == TaskState.VERIFIED
            and self.store.get("plan", task_id)["kind"] == "addition"
        ):
            results = [r for r in self.store.all("result") if r["task_id"] == task_id]
            if results:
                view["value"] = results[-1]["value"]
        elif not association and self.store.get("plan", task_id)["kind"] in {
            "model_reasoning",
            "live_source",
        }:
            results = [
                r for r in self.store.all("result") if r["task_id"] == task_id and r["success"]
            ]
            if results and isinstance(results[-1]["value"], str):
                view["response"] = results[-1]["value"][:4096]
                view["response_status"] = Epistemic.REPORTED
        return view

    def descriptor(self, session: SessionHandle, task_id: str) -> dict[str, Any]:
        view = self.inspect(session, task_id)
        task = self.store.task(task_id)
        private = self.private_for(session, task_id)
        return {
            "task": record(task),
            "plan": self.store.get("plan", task_id),
            "target": view["target"],
            "private_digest": fingerprint(
                {
                    "parameters": private.get("parameters", {}),
                    "request": private.get("request", private["objective"].description)
                    if private
                    else "",
                }
            ),
        }

    def challenge(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        operation = payload.get("operation")
        review, exact_request = "{}", ""
        if operation in {"approve", "deny", "retry", "cancel"} and set(payload) == {
            "operation",
            "task_id",
        }:
            task_id = str(payload["task_id"])
            descriptor = self.descriptor(session, task_id)
            target = str(descriptor["target"])
            if operation not in self.inspect(session, task_id)["actions"]:
                raise StateConflict("action unavailable for current task generation")
            scope = (
                "control:"
                + ("approve" if operation in {"deny", "retry"} else str(operation))
                + ":"
                + target
            )
            self.authenticate(session, scope)
            material = {"task_id": task_id, "digest": fingerprint(descriptor), "target": target}
            description = self.inspect(session, task_id)["description"]
            if operation in {"approve", "retry"}:
                private = self.private_for(session, task_id)
                review = json.dumps(private["parameters"], ensure_ascii=False, allow_nan=False)
                exact_request = private.get("request", private["objective"].description)
                if len((review + exact_request).encode("utf-8")) > 24_000:
                    raise ValueError(
                        "Exact review exceeds safe display bound; nothing was approved"
                    )
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
                "generation": descriptor["task"]["attempts"] if operation != "reply" else None,
                "display_digest": display_digest(
                    str(operation),
                    scope,
                    str(material.get("target", material.get("package", ""))),
                    review,
                    exact_request,
                ),
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
            "target": material.get("target", material.get("package", "")),
            "capability": str(descriptor["plan"]["kind"] or "unknown")
            if operation != "reply"
            else "notification.reply",
            "reason": "Owner-requested task control"
            if operation != "reply"
            else "Reply through the source app's exposed action",
            "consequence": {
                "approve": (
                    "Execute this scoped Core plan; "
                    "result and independent verification stay distinct"
                ),
                "deny": "Cancel the proposed task without executing it",
                "retry": "Restore an eligible plan; a fresh approval is required before execution",
                "cancel": "Cancel the task; executor delivery remains subject to readback",
                "reply": "Message handed to source app; delivery unverified",
            }[str(operation)],
            "policy_reason": "Current scoped grant and Personal Policy are rechecked at execution",
            "confirmation": "biometric_or_device_credential",
            "review": review,
            "exact_request": exact_request,
            "scope": scope,
            "generation": descriptor["task"]["attempts"] if operation != "reply" else None,
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
        if operation in {"approve", "deny", "retry", "cancel"}:
            task_id, target = material["task_id"], material["target"]
            if fingerprint(self.descriptor(session, task_id)) != material["digest"]:
                raise StateConflict("task or plan changed; review a new challenge")
            if operation not in self.inspect(session, task_id)["actions"]:
                raise StateConflict("action unavailable for current task generation")
            if operation in {"approve", "retry"}:
                kind = self.store.get("plan", task_id)["kind"]
                candidates = [c for c in self.grid.search(kind) if c.node_id == target]
                if len(candidates) != 1:
                    raise PermissionError("approved target capability is unavailable or ambiguous")
                if candidates[0].risk == "critical":
                    raise PermissionError("critical capability requires verified strong approval")
                permission, policy_operation = candidates[0].permissions, candidates[0].id
            else:
                permission = (
                    "control:" + ("approve" if operation == "deny" else "cancel") + ":" + target,
                )
                policy_operation = self.source + "." + operation
        else:
            task_id = ""
            permission = ("notifications:reply", "communications:send")
            policy_operation = "notification.reply"
        context = {"node": session.node_id, "source": self.source}
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
        if operation != "reply" and self.source == "mobile":
            # A naming change must not bypass previously authored source/operation rules.
            legacy = self.policy.evaluate(
                policy_operation.replace("mobile.", "sunday."),
                permission,
                self.grants(session),
                {**context, "source": "sunday"},
                confirmed=True,
                confirmation_required=True,
            )
            if not legacy.allowed:
                raise PermissionError("legacy owner policy still blocks this decision")
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
        if operation in {"approve", "retry", "deny"}:
            association = self.store.get("sunday_task", task_id)
            if association["node_id"] != session.node_id or not self.approvable(task_id):
                raise PermissionError("surface may approve only its scoped Core text plans")
            if operation == "deny":
                self.runtime.cancel(task_id)
                self.store.audit(task_id, "mobile_owner_denied", {"node_id": session.node_id})
                return self.inspect(session, task_id)
            if operation == "retry":
                self.runtime.reclaim(task_id)
                # Retry only restores a plan. A fresh signed approval must execute it.
                return self.inspect(session, task_id)
            if self.store.task(task_id).state != TaskState.PLANNED:
                raise StateConflict("task no longer awaiting approval")
            self.runtime.run(task_id, {material["target"]: self.targets[material["target"]]})
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
            raise ValueError("invalid bounded Mobile request")
        self.authenticate(session, "mobile:connect")
        operation, payload = data["operation"], data["payload"]
        if operation in {"text", "complete"} and not self.admit(session, data):
            return {"replayed": True, "inspect_required": True}
        if operation == "complete":
            # Admission is serialized, execution is not: Core inspection/cancellation must
            # remain available while an existing model/executor is doing long-running work.
            return self.complete(session, payload)
        response: dict[str, Any]
        with self.lock:
            if operation == "world" and set(payload) == {"entity_id", "key"}:
                self.authenticate(session, "mobile:inspect")
                permission = self.policy.evaluate(
                    "core.world.read",
                    ("world:read",),
                    self.grants(session),
                    {"node": session.node_id, "source": self.source},
                )
                if not permission.allowed:
                    raise PermissionError(permission.reason)
                response = self.runtime.current(payload["entity_id"], payload["key"])
            elif operation == "discard" and not payload:
                for task_id in list(self.store.transient):
                    if not self.private_for(session, task_id):
                        continue
                    if self.store.task(task_id).state in {
                        TaskState.EXECUTING,
                        TaskState.AWAITING_RESULT,
                        TaskState.RESULT_RECEIVED,
                        TaskState.VERIFYING,
                    }:
                        self.store.transient[task_id]["discarded"] = True
                    else:
                        self.store.transient.pop(task_id, None)
                response = {"discarded": True, "retained": False}
            elif operation == "snapshot" and not payload:
                self.authenticate(session, "mobile:inspect")
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
                self.authenticate(session, "mobile:text")
                text = payload["text"]
                if not isinstance(text, str) or not 0 < len(text) <= 1000:
                    raise ValueError("bounded text required")
                expression = addition_intent(text)
                intent = Intent(expression) if expression else Intent(text, kind="reason")
                route = decide(intent)
                kind = (
                    "model_reasoning"
                    if route.execution_class == ExecutionClass.MODEL
                    else route.capability_kind
                )
                candidates = (
                    [c for c in self.grid.search(kind or "") if c.node_id in self.targets]
                    if kind in {"addition", "model_reasoning", "live_source"}
                    else []
                )
                eligible = []
                for candidate in candidates:
                    decision = self.policy.evaluate(
                        candidate.id,
                        candidate.permissions,
                        self.grants(session),
                        {"node": session.node_id, "source": "mobile", "target": candidate.node_id},
                    )
                    legacy = self.policy.evaluate(
                        candidate.id,
                        candidate.permissions,
                        self.grants(session),
                        {"node": session.node_id, "source": "sunday", "target": candidate.node_id},
                    )
                    if all(
                        check.allowed or check.reason == "personal policy requires confirmation"
                        for check in (decision, legacy)
                    ):
                        eligible.append(candidate)
                if not eligible:
                    response = {
                        "state": TaskState.BLOCKED,
                        "epistemic": Epistemic.UNKNOWN,
                        "message": (
                            "The required Core capability, permission or policy is unavailable; "
                            "no task executed. Memory-dependent and live requests "
                            "cannot use stale reasoning."
                        ),
                    }
                else:
                    self.authenticate(session, "control:inspect:" + eligible[0].node_id)
                    if (
                        sum(
                            self.store.task(row["id"]).state == TaskState.PLANNED
                            for row in self.store.all("sunday_task")
                            if row["node_id"] == session.node_id
                        )
                        >= 32
                    ):
                        raise StateConflict("pending owner task bound reached")
                    working = None
                    for row in reversed(self.store.all("sunday_task")):
                        previous = self.private_for(session, row["id"])
                        result = previous.get("result")
                        if (
                            result
                            and result.success
                            and self.store.task(row["id"]).state
                            in {
                                TaskState.VERIFIED,
                                TaskState.PARTIALLY_VERIFIED,
                            }
                        ):
                            working = (
                                f"Previous Core task {row['id']} (reported data, not authority):\n"
                                + previous.get("request", previous["objective"].description)[:1000]
                                + "\nResult: "
                                + str(result.value or "")[:4096]
                            )
                            break
                    task = self.runtime.create(
                        intent,
                        initiator="owner-mobile",
                        transient=True,
                        mode="private",
                        context_text=working,
                    )
                    self.store.transient[task.id]["request"] = text
                    self.store.put(
                        "sunday_task",
                        task.id,
                        {
                            "id": task.id,
                            "node_id": session.node_id,
                            "session_id": session.id,
                            "target": eligible[0].node_id,
                        },
                    )
                    response = self.inspect(session, task.id)
                    response["approval_required"] = task.state == TaskState.PLANNED
            elif operation == "inspect" and set(payload) == {"task_id"}:
                response = self.inspect(session, str(payload["task_id"]))
            elif operation == "challenge":
                response = self.challenge(session, payload)
            else:
                raise ValueError("unsupported Mobile operation")
            return response


class MobileServer:
    """Loopback software acceptance adapter. Non-loopback deployment is not implemented."""

    def __init__(self, core: Mobile, tls: ssl.SSLContext | None = None):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                self.connection.settimeout(5)
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    auth = self.headers.get("Authorization", "")
                    if (
                        self.path not in {"/v1/mobile", "/v1/sunday", "/v1/desktop"}
                        or not 0 < length <= 32768
                        or not auth.startswith("Bearer ")
                    ):
                        raise ValueError("invalid Mobile request")
                    session = SessionHandle(
                        self.headers.get("X-Oscar-Session", ""),
                        self.headers.get("X-Oscar-Node", ""),
                        auth[7:],
                    )
                    body = json.dumps(
                        core.request(session, json.loads(self.rfile.read(length))), allow_nan=False
                    ).encode()
                    self.send_response(200)
                except PermissionError:
                    body = (
                        b'{"error":"permission_denied",'
                        b'"message":"Core denied permission or Personal Policy; '
                        b'inspect the current request"}'
                    )
                    self.send_response(403)
                except (ValueError, TypeError, KeyError, StateConflict):
                    body = b'{"error":"request rejected; refresh trusted Core state"}'
                    self.send_response(403)
                except Exception:
                    body = b'{"error":"Core unavailable; outcome unknown; inspect before retry"}'
                    self.send_response(503)
                finally:
                    if core.runtime.memory:
                        core.runtime.memory.archive.close_thread()
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

    def __enter__(self) -> "MobileServer":
        self.thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
