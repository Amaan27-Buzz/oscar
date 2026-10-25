"""Native authenticated transport. HTTP reference target is deliberately loopback-only."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, replace
from http.client import HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import time
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .memory_fabric import MemoryFabric
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from .capabilities import Cancellation, Cancelled, Executor
from .contracts import Action, ArtifactRef, Envelope, Epistemic, Result, TaskState, record
from .grid import Grid, SessionHandle
from .http_client import NoRedirects
from .storage import StateConflict, Store


def parse_result(data: dict[str, Any]) -> Result:
    if set(data) != set(Result.__dataclass_fields__) or type(data["success"]) is not bool:
        raise ValueError("invalid result contract")
    if data["status"] != Epistemic.REPORTED:
        raise ValueError("executors can only report")
    artifact = data["artifact"]
    if artifact is not None:
        if not isinstance(artifact, dict) or artifact["status"] != Epistemic.REPORTED:
            raise ValueError("invalid reported artifact")
        artifact = ArtifactRef(**artifact)
        if artifact.task_id != data["task_id"]:
            raise ValueError("reported artifact belongs to a different task")
    return Result(**{**data, "status": Epistemic.REPORTED, "artifact": artifact})


class Transport(Protocol):
    def invoke(self, envelope: Envelope, session: SessionHandle) -> Result: ...

    def control(self, envelope: Envelope, session: SessionHandle) -> dict[str, Any]: ...


class Dispatcher:
    """Target-side authorization/deduplication. Both local and HTTP paths use this boundary."""

    def __init__(
        self,
        store: Store,
        grid: Grid,
        node_id: str,
        executors: dict[str, Executor],
        *,
        pause_semantics: str = "executor-defined",
    ):
        self.store, self.grid, self.node_id, self.executors = store, grid, node_id, executors
        self.pause_semantics = pause_semantics
        self.memory: MemoryFabric | None = None

    def invoke(self, envelope: Envelope, session: SessionHandle) -> Result:
        envelope = Envelope.parse(record(envelope))
        if envelope.kind != "action" or envelope.node_id != self.node_id:
            raise ValueError("invalid action target")
        action = Action(**envelope.payload)
        if (
            action.task_id != envelope.task_id
            or action.correlation_id != envelope.correlation_id
            or record(action) != self.store.get("action", action.id)
        ):
            raise PermissionError("action does not match authorized durable plan")
        # The catalog exposes lightweight manifests; detailed target contract is checked here.
        node = self.store.get("node", self.node_id)
        candidates = [c for c in node["capabilities"] if c["id"] == action.capability_id]
        if len(candidates) != 1 or action.capability_id not in self.executors:
            raise PermissionError("target capability unavailable")
        # A successfully advertised node necessarily has heartbeat scope. Authenticated
        # target-side activity is fresh liveness evidence, so continuous real work must
        # not expire solely because a separate timer heartbeat was not scheduled.
        self.grid.heartbeat(session, lease_id=envelope.lease_id)
        self.grid.accept(envelope, session.token, "execute")
        for permission in candidates[0]["permissions"]:
            self.grid.authenticate(session, permission, lease_id=envelope.lease_id)

        def authorize_execution() -> None:
            from .authority import check_task_authority

            check_task_authority(self.store, self.grid, action.task_id, candidates[0], session)
            latest = self.store.get("node", self.node_id)
            if [c for c in latest["capabilities"] if c["id"] == action.capability_id] != candidates:
                raise PermissionError("target capability withdrawn or changed")
            self.grid.authenticate(session, "execute", lease_id=envelope.lease_id)
            for permission in candidates[0]["permissions"]:
                self.grid.authenticate(session, permission, lease_id=envelope.lease_id)
            current = self.store.task(action.task_id)
            lease = self.store.get("lease", envelope.lease_id)
            if (
                current.lease_id != envelope.lease_id
                or not lease["active"]
                or lease["expires_at"] <= self.grid.clock()
            ):
                raise PermissionError("execution lease expired or superseded")
            plan = self.store.get("plan", action.task_id)
            if plan.get("executive"):
                from .executive import authorize_step

                authorize_step(
                    self.store, self.grid, action.task_id, candidates[0], session, self.memory
                )

        cancellation = Cancellation(self.store, action.task_id, authorize_execution)
        cancellation.check()
        fingerprint = hashlib.sha256(
            json.dumps(record(action), sort_keys=True).encode()
        ).hexdigest()
        key = f"{action.initiator}:{action.idempotency_key}"
        previous = self.store.claim_action(key, fingerprint, action.id)
        if previous is not None:
            return parse_result(previous)
        self.store.audit(
            action.task_id,
            "action_authorized",
            {
                "action_id": action.id,
                "capability_id": action.capability_id,
                "initiator": action.initiator,
                "node_id": self.node_id,
                "permissions": candidates[0]["permissions"],
                "reversible": candidates[0]["reversible"],
                "correlation_id": action.correlation_id,
            },
        )
        private = self.store.transient.get(action.task_id)
        execution = action
        if "transient_digest" in action.parameters:
            if private is None:
                raise StateConflict("private payload unavailable; no replay")
            objective = private["objective"]
            material = json.dumps(
                {
                    "description": objective.description,
                    "parameters": private["parameters"],
                    "criterion": objective.criterion,
                },
                allow_nan=False,
            )
            if (
                hashlib.sha256(material.encode()).hexdigest()
                != action.parameters["transient_digest"]
            ):
                raise StateConflict("private payload changed after review")
            execution = replace(action, parameters=private["parameters"])
        ownership = self.store.get("plan", action.task_id).get("interaction")
        if ownership:
            with self.store.transaction():
                lease = self.store.get("interaction_lease", ownership["resource"])
                if (
                    lease.get("task_id") != action.task_id
                    or lease["expires"] <= self.grid.clock()
                    or lease["generation"] != ownership["generation"]
                ):
                    raise StateConflict("interaction fence expired")
                lease["expires"] = self.grid.clock() + 120
                self.store.put("interaction_lease", ownership["resource"], lease)
        try:
            result = self.executors[action.capability_id](execution, cancellation)
        except Cancelled:
            raise
        except Exception:
            raise OSError("executor failed; outcome requires independent inspection") from None
        if (
            result.action_id != action.id
            or result.task_id != action.task_id
            or result.correlation_id != action.correlation_id
        ):
            raise ValueError("executor returned unrelated result")
        result = parse_result(record(result))
        if private is not None:
            private["result"] = result
            # Content, artifacts and arbitrary errors never enter durable result/dedup rows.
            result = replace(
                result,
                value=None,
                artifact=None,
                error="private executor failed" if result.error else None,
            )
        self.store.complete_action(key, record(result))
        return result

    def control(self, envelope: Envelope, session: SessionHandle) -> dict[str, Any]:
        envelope = Envelope.parse(record(envelope))
        if envelope.node_id != self.node_id or envelope.kind not in {"cancel", "pause", "resume"}:
            raise ValueError("invalid control message")
        if envelope.kind in {"pause", "resume"}:
            self.grid.accept(envelope, session.token, "pause")
            self.store.put("worker_control", envelope.task_id, {"paused": envelope.kind == "pause"})
            self.store.audit(
                envelope.task_id,
                "worker_" + envelope.kind,
                {
                    "correlation_id": envelope.correlation_id,
                    "pause_semantics": self.pause_semantics,
                },
            )
            return {
                "kind": envelope.kind,
                "task_id": envelope.task_id,
                "correlation_id": envelope.correlation_id,
                "pause_semantics": self.pause_semantics,
            }
        self.grid.accept(envelope, session.token, "cancel")
        task = self.store.task(envelope.task_id)
        if not task.cancelled:
            self.store.transition(task.id, TaskState.CANCELLED)
        return {"kind": "cancelled", "task_id": task.id, "correlation_id": task.correlation_id}


class HTTPTransport:
    def __init__(self, url: str, timeout: float = 10):
        if not url.startswith("http://127.0.0.1:"):
            raise ValueError(
                "reference HTTP transport is loopback-only; remote deployment requires TLS"
            )
        self.url, self.timeout = url, timeout

    def invoke(self, envelope: Envelope, session: SessionHandle) -> Result:
        request = Request(
            self.url + "/action",
            data=json.dumps(asdict(envelope)).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + session.token,
            },
        )
        try:
            with build_opener(NoRedirects()).open(request, timeout=self.timeout) as response:
                data = json.loads(response.read(2_000_001))
        except (HTTPException, HTTPError, URLError, TimeoutError, OSError) as error:
            if isinstance(error, HTTPError):
                error.close()
            raise StateConflict(
                "reference transport failed; execution outcome may be unknown"
            ) from None
        if not isinstance(data, dict):
            raise ValueError("invalid transport result")
        return parse_result(data)

    def control(self, envelope: Envelope, session: SessionHandle) -> dict[str, Any]:
        request = Request(
            self.url + ("/cancel" if envelope.kind == "cancel" else "/control"),
            data=json.dumps(record(envelope)).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + session.token,
            },
        )
        try:
            with build_opener(NoRedirects()).open(request, timeout=self.timeout) as response:
                data = json.loads(response.read(4096))
            expected = {
                "kind": "cancelled" if envelope.kind == "cancel" else envelope.kind,
                "task_id": envelope.task_id,
                "correlation_id": envelope.correlation_id,
            }
            # Version-1 targets may omit the additive pause qualifier. Identity and
            # control state must still match exactly; unknown fields are rejected.
            if isinstance(data, dict) and envelope.kind in {"pause", "resume"}:
                semantics = data.get("pause_semantics")
                if semantics is not None:
                    if semantics not in {
                        "executor-defined",
                        "before-next-subprocess",
                        "POSIX-process-group",
                    }:
                        raise ValueError("invalid pause semantics")
                    expected["pause_semantics"] = semantics
            if data != expected:
                raise ValueError("invalid cancellation acknowledgement")
            return dict(data)
        except (HTTPException, HTTPError, URLError, TimeoutError, OSError) as error:
            if isinstance(error, HTTPError):
                error.close()
            raise StateConflict("remote cancellation delivery unverified") from None


class ReferenceServer:
    def __init__(self, dispatcher: Dispatcher):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if (
                        self.path not in {"/action", "/cancel", "/control"}
                        or not 0 < length <= 2_000_000
                    ):
                        raise ValueError("invalid request")
                    envelope = Envelope.parse(json.loads(self.rfile.read(length)))
                    authorization = self.headers.get("Authorization", "")
                    if not authorization.startswith("Bearer "):
                        raise PermissionError("authorization missing")
                    session = SessionHandle(
                        envelope.session_id, envelope.node_id, authorization[7:]
                    )
                    if self.path == "/action":
                        body = json.dumps(record(dispatcher.invoke(envelope, session))).encode()
                    else:
                        body = json.dumps(dispatcher.control(envelope, session)).encode()
                    self.send_response(200)
                except (ValueError, TypeError, KeyError, PermissionError, StateConflict):
                    body = b'{"error":"request rejected"}'
                    self.send_response(403)
                except Exception:
                    # Never include executor exceptions, tokens or payloads in an HTTP error/log.
                    body = b'{"error":"executor failure; inspect task state"}'
                    self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self) -> "ReferenceServer":
        self.thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def action_envelope(
    action: Action, session: SessionHandle, lease_id: str, clock: Callable[[], float] = time
) -> Envelope:
    return Envelope(
        "action",
        session.node_id,
        session.id,
        action.task_id,
        action.correlation_id,
        lease_id,
        record(action),
        clock(),
    )
