"""Desktop surface admission atop Mobile's signed Core authority and existing Runtime.

Presentation never executes apps. Private payloads expire on restart, not into memory.
"""

import sqlite3
from typing import Any

from .contracts import Epistemic, Task, TaskState, new_id
from .desktop_actions import (
    OPERATIONS,
    conversation_form,
    editing_request,
    form_intent,
    public_capability,
)
from .desktop_context import ContextSource, DesktopContext, WindowsContext
from .event_archive import MemoryWriter, SourceEvent
from .grid import NodeRole, SessionHandle
from .jev import ExecutionClass, Intent, decide
from .mobile import Mobile
from .storage import StateConflict
from .voice_contracts import StopToken, Transcript
from .voice_core import addition_intent


def orb_state(state: str | None, *, online: bool = True, voice: str = "idle") -> str:
    if not online or state in {"failed", "blocked", "unknown"}:
        return "error"
    if voice in {"listening", "speaking"}:
        return voice
    if state == "planned":
        return "waiting"
    if state in {"executing", "awaiting_result", "result_received", "verifying"}:
        return "thinking"
    return "attentive" if state else "idle"


class Desktop(Mobile):
    source = "desktop"

    def __init__(
        self,
        *args: Any,
        context: WindowsContext | None = None,
        native_catalogs: dict[str, dict[str, Any]] | None = None,
        worker_outputs: dict[str, dict[str, str]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.context_adapter = context
        self.native_catalogs = native_catalogs or {}
        self.worker_outputs = worker_outputs or {}
        self.contexts: dict[str, tuple[str, DesktopContext]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.voice: Any = (
            None  # Explicitly installed prepared Voice Core adapter, never auto-capture.
        )
        self.store.task_resources.add(self)

    def task_transitioned(self, task: Task) -> None:
        if task.state not in {
            TaskState.PLANNED,
            TaskState.EXECUTING,
            TaskState.AWAITING_RESULT,
            TaskState.RESULT_RECEIVED,
            TaskState.VERIFYING,
        }:
            private = self.store.transient.get(task.id, {})
            if private.get("discarded"):
                self.store.transient.pop(task.id, None)

    def authenticate(self, session: SessionHandle, scope: str) -> None:
        scope = scope.replace("mobile:", "desktop:", 1)
        self.grid.authenticate(session, scope)
        if self.store.get("node", session.node_id)["role"] != NodeRole.DESKTOP:
            raise PermissionError("Desktop role required")

    def approvable(self, task_id: str) -> bool:
        return any(row["id"] == task_id for row in self.store.all("desktop_task"))

    def complete(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        import base64
        import json

        challenge = self.store.get("sunday_challenge", str(payload.get("challenge_id")))
        claim = json.loads(base64.b64decode(challenge["payload"]))
        if claim["operation"] == "approve":
            task_id = claim["material"]["task_id"]
            private = self.private_for(session, task_id)
            if not private:
                raise PermissionError("private request expired; recreate it")
            ownership = self.store.get("plan", task_id).get("interaction")
            if ownership:
                lease = self.store.get("interaction_lease", ownership["resource"])
                if (
                    lease["session"] != session.id
                    or lease["expires"] <= self.grid.clock()
                    or lease["generation"] != ownership["generation"]
                ):
                    raise PermissionError("interaction ownership expired or changed")
            captured = private.get("context_id")
            if captured:
                self.attached(session, captured)
            request = private["parameters"].get("request", {})
            if any(
                c.risk == "critical"
                for c in self.grid.search(self.store.get("plan", task_id)["kind"])
                if c.node_id == claim["material"]["target"]
            ):
                raise PermissionError("critical capability requires strong owner approval")
            if request.get("operation") == "clipboard_write":
                self.permission(session, "desktop.clipboard", ("desktop:clipboard",))
        view = super().complete(session, payload)
        if claim["operation"] == "approve":
            self.retain_turn(session, view["task_id"], "oscar", view)
        return view

    def conversation(self, session: SessionHandle, before: int = 0) -> dict[str, Any]:
        self.permission(session, "desktop.conversation", ("desktop:text",))
        archive = self.runtime.memory.archive if self.runtime.memory else None
        granted = self.grants(session)
        retained = bool(
            archive
            and "desktop:conversation:read" in granted
            and self.policy.evaluate(
                "desktop.conversation.read",
                ("desktop:conversation:read",),
                granted,
                {"node": session.node_id, "source": self.source},
            ).allowed
        )
        turns = []
        cursor = None
        if retained and archive is not None:
            page = archive.conversation(self.runtime.relationship_id, before=before)
            cursor = page["before"]
            turns = [
                {
                    "id": e.id,
                    "task_id": e.task_id or "",
                    "role": "owner" if e.kind == "conversation_owner" else "oscar",
                    "text": e.content,
                    "status": e.status,
                    "occurred_at": e.occurred_at,
                    "retained": True,
                }
                for e in page["events"]
            ]
        elif before:
            raise PermissionError("retained conversation read unavailable")
        if not before:
            seen = {(t["task_id"], t["role"]) for t in turns}
            for row in self.store.all("desktop_task"):
                if row["mode"] != "Ask" or row.get("session_id") != session.id:
                    continue
                private = self.private_for(session, row["id"])
                if not private or private.get("context_id"):
                    continue
                view = self.inspect(session, row["id"])
                for role, text in (
                    ("owner", private["objective"].description),
                    ("oscar", view.get("value") or view.get("response")),
                ):
                    if not text or (row["id"], role) in seen:
                        continue
                    if (
                        retained
                        and archive is not None
                        and archive.db.execute(
                            "SELECT 1 FROM archive_events WHERE id=? AND relationship=?",
                            (row["id"] + ":" + role, self.runtime.relationship_id),
                        ).fetchone()
                    ):
                        continue  # Do not resurrect older/forgotten saved events as private turns.
                    turns.append(
                        {
                            "id": row["id"] + ":" + role,
                            "task_id": row["id"],
                            "role": role,
                            "text": text,
                            "status": Epistemic.REPORTED
                            if role == "owner"
                            else view.get("epistemic")
                            or view.get("response_status")
                            or Epistemic.UNKNOWN,
                            "occurred_at": private["objective"].created_at,
                            "retained": False,
                        }
                    )
        return {
            "turns": turns,
            "before": cursor,
            "persistence": "authorized" if retained else "session_only",
            "retention": bool(
                archive
                and self.policy.evaluate(
                    "desktop.conversation.retain",
                    ("desktop:conversation:retain",),
                    granted,
                    {"node": session.node_id, "source": self.source},
                ).allowed
            ),
            "revision": archive.generation(self.runtime.relationship_id)
            if retained and archive is not None
            else 0,
        }

    def retain_turn(
        self, session: SessionHandle, task_id: str, role: str, view: dict[str, Any]
    ) -> None:
        archive = self.runtime.memory.archive if self.runtime.memory else None
        private = self.private_for(session, task_id)
        if not archive or not private or private.get("context_id") or view.get("mode") != "Ask":
            return
        try:
            self.permission(
                session, "desktop.conversation.retain", ("desktop:conversation:retain",)
            )
        except PermissionError:
            return
        text = (
            private["objective"].description
            if role == "owner"
            else view.get("value") or view.get("response")
        )
        if role == "oscar" and private.get("result") and private["result"].success:
            text = private["result"].value or text
        if not text:
            return
        event = SourceEvent(
            self.runtime.relationship_id,
            text,
            "desktop/conversation",
            self.grid.clock(),
            kind="conversation_" + role,
            sensitivity="personal",
            task_id=task_id,
            id=task_id + ":" + role,
            status=Epistemic.REPORTED
            if role == "owner"
            else Epistemic(
                view.get("epistemic") or view.get("response_status") or Epistemic.UNKNOWN
            ),
        )
        try:
            archive.append(event, retain_authorized=True)
            MemoryWriter(archive).retain(
                (event.id,), event.content, "episodic", retain_authorized=True, inferred=False
            )
        except (ValueError, sqlite3.Error, OSError):
            # Retention failure must not make an already executed action appear unexecuted.
            self.store.audit(task_id, "conversation_retention_failed", {"role": role})

    def permission(self, session: SessionHandle, operation: str, scopes: tuple[str, ...]) -> None:
        for scope in scopes:
            self.authenticate(session, scope)
        decision = self.policy.evaluate(
            operation,
            scopes,
            self.grants(session),
            {"node": session.node_id, "source": self.source},
        )
        if not decision.allowed:
            raise PermissionError("desktop permission/Personal Policy denied")

    def attached(self, session: SessionHandle, identifier: str) -> DesktopContext:
        owner, context = self.contexts[identifier]
        if owner != session.id or not context.fresh(self.grid.clock()):
            raise PermissionError("context unavailable, stale or from another session")
        self.permission(session, "desktop.capture", ("desktop:perceive:" + context.source,))
        return context

    def propose(
        self,
        session: SessionHandle,
        intent: Intent,
        mode: str,
        *,
        private_model: bool = False,
        capability_id: str | None = None,
        target_id: str | None = None,
        context_text: str | None = None,
    ) -> dict[str, Any]:
        route = decide(intent)
        kind = (
            "model_reasoning"
            if route.execution_class == ExecutionClass.MODEL
            else (route.capability_kind)
        )
        eligible = []
        permission_denied = False
        if private_model and kind != "model_reasoning":
            return {
                "state": "blocked",
                "epistemic": "UNKNOWN",
                "message": "Private context cannot become a live/public retrieval query",
            }
        for cap in self.grid.search(kind or ""):
            if capability_id is not None and cap.id != capability_id:
                continue
            if target_id is not None and cap.node_id != target_id:
                continue
            if cap.node_id not in self.targets:
                continue
            if cap.risk == "critical":
                continue  # Native strong owner verification is a manual acceptance boundary.
            check = self.policy.evaluate(
                cap.id,
                cap.permissions,
                self.grants(session),
                {"source": "desktop", "node": session.node_id, "target": cap.node_id},
            )
            if check.allowed or check.reason == "personal policy requires confirmation":
                eligible.append(cap)
            else:
                permission_denied = True
        if len(eligible) != 1:
            return {
                "state": "blocked",
                "epistemic": "UNKNOWN",
                "reason": "permission_denied"
                if not eligible and permission_denied
                else "capability_unavailable",
                "message": (
                    "Permission or Personal Policy denied this request; nothing executed"
                    if not eligible and permission_denied
                    else "Core/Worker capability unavailable or ambiguous; nothing executed"
                ),
            }
        target = eligible[0].node_id
        self.authenticate(session, "control:inspect:" + target)
        task = self.runtime.create(
            intent,
            initiator="owner-desktop",
            retry_budget=0,
            transient=True,
            mode="private" if private_model else "auto",
            context_text=context_text,
        )
        self.store.put(
            "sunday_task", task.id, {"id": task.id, "node_id": session.node_id, "target": target}
        )
        self.store.put(
            "desktop_task", task.id, {"id": task.id, "mode": mode, "session_id": session.id}
        )
        view = self.inspect(session, task.id)
        view["approval_required"] = task.state == TaskState.PLANNED
        return view

    def inspect(self, session: SessionHandle, task_id: str) -> dict[str, Any]:
        view = super().inspect(session, task_id)
        private = self.private_for(session, task_id)
        response_length = 0
        try:
            association = self.store.get("sunday_task", task_id)
        except KeyError:
            association = {}
        try:
            desktop_record = self.store.get("desktop_task", task_id)
        except KeyError:
            desktop_record = {}
        # Private response is only visible to the originating owner surface session/node.
        if (
            association.get("node_id") == session.node_id
            and desktop_record.get("session_id") == session.id
            and "result" in private
            and view["state"] != TaskState.CANCELLED
        ):
            result = private["result"]
            if result.success and result.value is not None:
                view["response"] = result.value[:8192]
                response_length = len(result.value)
                view["response_status"] = Epistemic.REPORTED
                if view["state"] == TaskState.VERIFIED and (
                    self.store.get("plan", task_id)["kind"] == "addition"
                ):
                    view["value"] = result.value
                    view["epistemic"] = Epistemic.VERIFIED
            output = self.worker_outputs.get(str(view["target"]), {}).get(result.action_id)
            if result.success and output is not None:
                view["response"] = output[:8192]
                response_length = len(output)
                view["response_status"] = Epistemic.REPORTED
        if "retry" in view["actions"]:
            view["actions"].remove("retry")  # private input cannot be blindly replayed
        if "approve" in view["actions"] and not private:
            view["actions"].remove("approve")
        view["evidence"] = [
            {
                key: row[key]
                for key in ("id", "source", "method", "observed_at", "matches", "status")
            }
            for row in self.store.all("evidence")
            if row["task_id"] == task_id
        ]
        view["artifacts"] = []
        if (
            desktop_record.get("session_id") == session.id
            and association.get("node_id") == session.node_id
        ):
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
        view["mode"] = desktop_record.get("mode", "")
        view["response_truncated"] = bool(view.get("response")) and response_length > 8192
        if self.store.get("plan", task_id)["kind"] == "memory" and view.get("response"):
            from .memory_executor import recall_text

            memory = self.runtime.memory
            objective = private.get("objective")
            context = (
                memory.context(
                    memory.retrieve(self.runtime.relationship_id, objective.description),
                    objective=objective.description,
                    project=None,
                    live={},
                    policy_ids=(),
                    max_chars=8192,
                )
                if memory and objective
                else {"memories": []}
            )
            if recall_text(context) == view["response"] and context["memories"]:
                view["response_status"] = (
                    Epistemic.INFERRED
                    if any(item["status"] == Epistemic.INFERRED for item in context["memories"])
                    else Epistemic.RECALLED
                )
                view["source_event_ids"] = sorted(
                    {event for item in context["memories"] for event in item["event_ids"]}
                )
            else:
                view["response"] = (
                    "Historical evidence is unavailable or changed. "
                    "Retrieve again before relying on it."
                )
                view["response_status"] = Epistemic.UNKNOWN
                view["response_truncated"] = False
        view["orb"] = orb_state(view["state"])
        try:
            checkpoint = self.store.get("worker_checkpoint", task_id)
            view["progress"] = {
                "fraction": checkpoint["fraction"],
                "step": checkpoint["step"],
                "status": Epistemic.REPORTED,
            }
        except KeyError:
            view["progress"] = None
        return view

    def private_for(self, session: SessionHandle, task_id: str) -> dict[str, Any]:
        try:
            record = self.store.get("desktop_task", task_id)
            association = self.store.get("sunday_task", task_id)
        except KeyError:
            return {}
        private = self.store.transient.get(task_id, {})
        if (
            record.get("session_id") != session.id
            or association.get("node_id") != session.node_id
            or private.get("discarded")
        ):
            return {}
        return private

    def challenge(self, session: SessionHandle, payload: dict[str, Any]) -> dict[str, Any]:
        import json

        if payload.get("operation") != "reply":
            state = self.inspect(session, str(payload.get("task_id")))["state"]
            private = self.private_for(session, str(payload.get("task_id")))
            review = json.dumps(private.get("parameters", {}), ensure_ascii=False)
            if len(review.encode("utf-8")) > 24_000:
                raise ValueError(
                    "Exact review exceeds its safe display bound; shorten the request or context. "
                    "Nothing was approved."
                )
        view = super().challenge(session, payload)
        if payload.get("operation") != "reply":
            view["confirmation"] = "explicit_desktop_owner_review"
            view["evidence_state"] = state
            view["review"] = review
        return view

    def request(self, session: SessionHandle, data: dict[str, Any]) -> dict[str, Any]:
        context: DesktopContext | None
        # Reuse strict Mobile admission/security for common inspection and signed controls.
        op, payload = data.get("operation"), data.get("payload")
        import re

        if (
            set(data) != {"version", "operation", "request_id", "payload"}
            or type(data["version"]) is not int
            or data["version"] != 1
            or not isinstance(data["request_id"], str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,80}", data["request_id"]) is None
            or not isinstance(payload, dict)
        ):
            raise ValueError("invalid bounded desktop envelope")
        if op == "conversation" and set(payload) == {"before"}:
            self.authenticate(session, "desktop:connect")
            if type(payload["before"]) is not int or payload["before"] < 0:
                raise ValueError("bounded conversation cursor required")
            return self.conversation(session, payload["before"])
        if op == "snapshot" and payload == {}:
            view = super().request(session, data)
            view["conversation"] = self.conversation(session)
            view["voice_available"] = (
                self.voice is not None
                and self.policy.evaluate(
                    "desktop.voice",
                    ("desktop:microphone",),
                    self.grants(session),
                    {"node": session.node_id, "source": self.source},
                ).allowed
            )
            view["operating"] = {
                "access": "Ask",
                "secure": "unavailable",
                "full_access": "unavailable",
                "awareness": self.runtime.world.sentry.settings().mode.value
                if self.runtime.world
                else "unavailable",
                "sentry": "configured_sources_only"
                if self.runtime.world and self.runtime.world.sentry.settings().source_ids
                else "unavailable",
                "worker_autonomy": "Manual",
                "automations": "task_foundation",
            }
            return view
        if op in {"catalog", "act"}:
            self.authenticate(session, "desktop:connect")
            self.permission(session, "desktop.catalog", ("desktop:inspect",))
            available = []
            for node in self.grid.nodes():
                if node["id"] not in self.targets or node["status"] not in {"online", "degraded"}:
                    continue
                if "control:inspect:" + node["id"] not in self.grants(session):
                    continue
                from .contracts import Capability

                for row in node["capabilities"]:
                    cap = Capability.from_dict(row)
                    decision = self.policy.evaluate(
                        cap.id,
                        cap.permissions,
                        self.grants(session),
                        {"node": session.node_id, "source": "desktop", "target": cap.node_id},
                    )
                    if cap.risk != "critical" and (
                        decision.allowed
                        or decision.reason == "personal policy requires confirmation"
                    ):
                        available.append(cap)
            if op == "catalog" and payload == {}:
                return {
                    "capabilities": [
                        public_capability(c, self.native_catalogs.get(c.node_id, {}))
                        for c in available
                    ],
                    "observed_at_ms": round(self.grid.clock() * 1000),
                }
            if op == "act" and isinstance(payload, dict):
                if not self.admit(session, data):
                    return {"replayed": True, "inspect_required": True}
                selected_cap = next(
                    (
                        c
                        for c in available
                        if c.node_id + "::" + c.id == payload.get("capability_id")
                    ),
                    None,
                )
                if selected_cap is None:
                    raise PermissionError("current capability unavailable; refresh catalog")
                intent = form_intent(
                    selected_cap, payload, self.native_catalogs.get(selected_cap.node_id, {})
                )
                return self.propose(
                    session,
                    intent,
                    "Act",
                    capability_id=selected_cap.id,
                    target_id=selected_cap.node_id,
                )
            raise ValueError("invalid catalog/Act request")
        if op not in {"capture", "discard", "interact", "preview", "apply", "claim", "voice"}:
            if op == "text":
                raise ValueError("desktop uses typed interaction modes")
            return super().request(session, data)
        if (
            set(data) != {"version", "operation", "request_id", "payload"}
            or type(data["version"]) is not int
            or data["version"] != 1
            or not isinstance(payload, dict)
            or not isinstance(data["request_id"], str)
            or not 0 < len(data["request_id"]) <= 80
        ):
            raise ValueError("invalid desktop request")
        self.authenticate(session, "desktop:connect")
        if op == "voice":
            if self.voice is None:
                return {
                    "state": "blocked",
                    "epistemic": "UNKNOWN",
                    "message": "Voice adapter unavailable; microphone not opened",
                }
            if payload == {"operation": "stop"}:
                return dict(self.voice.finish(session))
            if payload == {"operation": "cancel"}:
                return dict(self.voice.cancel(session))
            if payload == {"operation": "inspect"}:
                return dict(self.voice.inspect(session))
            if set(payload) == {"operation", "context_id"} and payload["operation"] == "start":
                return dict(self.voice.start(session, payload["context_id"]))
            raise ValueError("unsupported voice operation")
        if op in {"interact", "apply"} and not self.admit(session, data):
            return {"replayed": True, "inspect_required": True}
        with self.lock:
            if op == "claim" and set(payload) == {"resource"}:
                resource = payload["resource"]
                if resource not in {"input", "voice"}:
                    raise ValueError("bounded interaction resource required")
                lease = self.grid.claim_interaction(session, resource)
                return {"owner": session.node_id, "expires": lease["expires"]}
            if op == "discard" and not payload:
                if self.voice is not None and self.voice.owner == session.id:
                    self.voice.cancel(session)
                self.contexts = {k: v for k, v in self.contexts.items() if v[0] != session.id}
                for task_id in list(self.store.transient):
                    try:
                        association = self.store.get("sunday_task", task_id)
                        record = self.store.get("desktop_task", task_id)
                        if (
                            association.get("node_id") != session.node_id
                            or record.get("session_id") != session.id
                        ):
                            continue
                        state = self.store.task(task_id).state
                        if state not in {
                            TaskState.EXECUTING,
                            TaskState.AWAITING_RESULT,
                            TaskState.RESULT_RECEIVED,
                            TaskState.VERIFYING,
                        }:
                            self.store.transient.pop(task_id, None)
                        else:
                            self.store.transient[task_id]["discarded"] = True
                    except KeyError:
                        continue
                self.previews = {
                    k: v for k, v in self.previews.items() if v["session"] != session.id
                }
                return {"discarded": True, "retained": False}
            if op == "capture" and set(payload) in ({"source"}, {"source", "target"}):
                source = ContextSource(payload["source"])
                self.permission(session, "desktop.capture", ("desktop:perceive:" + source,))
                if self.context_adapter is None:
                    return {"permission": "unavailable", "epistemic": "UNKNOWN"}
                if len(self.contexts) >= 32:
                    raise StateConflict("discard stale context before recapture")
                target_identity = None
                if "target" in payload:
                    target = payload["target"]
                    if (
                        source not in {ContextSource.FOCUSED, ContextSource.SELECTION}
                        or not isinstance(target, dict)
                        or set(target) != {"handle", "pid", "runtime_id"}
                        or any(
                            type(target[k]) is not int or target[k] <= 0 for k in ("handle", "pid")
                        )
                        or not isinstance(target["runtime_id"], str)
                    ):
                        raise ValueError("explicit registered UIA target required")
                    target_identity = (target["handle"], target["pid"], target["runtime_id"])
                captured_context = self.context_adapter.capture(source, new_id(), target_identity)
                self.contexts[captured_context.id] = (session.id, captured_context)
                return captured_context.view(self.grid.clock())
            if op == "interact" and set(payload) == {"mode", "text", "context_id"}:
                mode, text = payload["mode"], payload["text"]
                self.permission(session, "desktop.interact", ("desktop:text",))
                if mode not in {"Ask", "Dictate", "Edit", "Act"} or (
                    not isinstance(text, str) or not 0 < len(text) <= 4096
                ):
                    raise ValueError("bounded mode/input required")
                context = (
                    self.attached(session, payload["context_id"])
                    if (payload["context_id"])
                    else None
                )
                if mode == "Ask":
                    if context is not None and editing_request(text):
                        mode = "Edit"
                    form = conversation_form(text)
                    if form:
                        operation, fields = form
                        from .contracts import Capability

                        candidates = [
                            Capability.from_dict(c)
                            for node in self.grid.nodes()
                            if node["id"] in self.targets
                            and node["status"] in {"online", "degraded"}
                            for c in node["capabilities"]
                            if operation in OPERATIONS.get(c["input_kind"], ())
                            and c["risk"] != "critical"
                        ]
                        if len(candidates) != 1:
                            return {
                                "state": "blocked",
                                "epistemic": "UNKNOWN",
                                "message": "That action is not available here. Nothing changed.",
                            }
                        cap = candidates[0]
                        typed = form_intent(
                            cap,
                            {
                                "capability_id": cap.node_id + "::" + cap.id,
                                "operation": operation,
                                "fields": fields,
                            },
                            self.native_catalogs.get(cap.node_id, {}),
                        )
                        from dataclasses import replace

                        return self.propose(
                            session,
                            replace(typed, text=text),
                            "Act",
                            capability_id=cap.id,
                            target_id=cap.node_id,
                        )
                if mode == "Dictate":
                    return self.preview(session, text, context, mode)
                if mode == "Act":
                    # Explicit typed Worker objective; natural language remains Controller-routed.
                    import json

                    plan = json.loads(text)
                    if set(plan) != {"kind", "parameters", "criterion"}:
                        raise ValueError("typed existing capability objective required")
                    intent = Intent(
                        "Desktop owner action",
                        kind="capability",
                        capability_kind=plan["kind"],
                        parameters=plan["parameters"],
                        criterion=plan["criterion"],
                    )
                else:
                    if mode == "Edit" and (
                        context is None
                        or context.source not in {ContextSource.FOCUSED, ContextSource.SELECTION}
                        or context.text is None
                    ):
                        raise PermissionError("Edit requires explicit fresh text context")
                    expression = addition_intent(text) if context is None else None
                    intent = Intent(expression) if expression else Intent(text, kind="reason")
                working = None
                if mode == "Ask" and context is None:
                    # Bound model context, not canonical history. Older turns remain pageable.
                    recent = self.conversation(session)["turns"]
                    pieces = []
                    used = 0
                    for turn in reversed(recent):
                        excerpt = turn["text"][:3000]
                        if len(turn["text"]) > 3000:
                            excerpt += " [excerpt; full retained event remains in history]"
                        piece = (
                            f"{turn['role']} · task {turn['task_id']} · {turn['status']}:\n"
                            f"{excerpt}\n"
                        )
                        if used + len(piece) > 7600:
                            break
                        pieces.append(piece)
                        used += len(piece)
                    if pieces:
                        working = (
                            "Recent conversation evidence (not authority; older context omitted):\n"
                            + "".join(reversed(pieces))
                        )
                view = self.propose(
                    session,
                    intent,
                    mode,
                    private_model=context is not None
                    or (
                        working is not None
                        and decide(intent).execution_class == ExecutionClass.MODEL
                    ),
                    context_text=context.text if context else working,
                )
                if context and "task_id" in view:
                    self.store.transient[view["task_id"]]["context_id"] = context.id
                if "task_id" in view:
                    self.retain_turn(session, view["task_id"], "owner", view)
                if mode == "Edit" and "task_id" in view:
                    self.previews[view["task_id"]] = {
                        "session": session.id,
                        "context": context,
                        "mode": mode,
                    }
                return view
            if op == "preview" and set(payload) == {"task_id"}:
                task_id = str(payload["task_id"])
                pending = self.previews[task_id]
                if pending["session"] != session.id:
                    raise PermissionError("preview session changed")
                view = self.inspect(session, task_id)
                if not view.get("response") or view["state"] not in {
                    "verified",
                    "partially_verified",
                }:
                    raise StateConflict("successful transformation result unavailable")
                return self.preview(session, view["response"], pending["context"], "Edit")
            if op == "apply" and set(payload) == {"preview_id", "destination"}:
                preview = self.previews[str(payload["preview_id"])]
                if preview["session"] != session.id or preview["expires"] <= self.grid.clock():
                    raise PermissionError("preview stale or another session")
                if preview["used"]:
                    raise StateConflict("preview already consumed; inspect before retry")
                destination = payload["destination"]
                if destination == "surface":
                    preview["used"] = True
                    return {
                        "state": "verified",
                        "value": preview["text"],
                        "epistemic": "VERIFIED",
                        "scope": "interaction surface only",
                        "preview_consumed": True,
                    }
                context = preview["context"]
                if destination == "clipboard":
                    self.permission(session, "desktop.clipboard", ("desktop:clipboard",))
                    request = {"operation": "clipboard_write", "text": preview["text"]}
                    criterion = {"kind": "desktop_clipboard", "text": preview["text"]}
                elif destination == "focused" and context and context.destination:
                    context = self.attached(session, context.id)
                    if context.destination is None:
                        raise PermissionError("destination unavailable")
                    handle, pid, identity = context.destination
                    request = {
                        "operation": "set_text_checked",
                        "handle": handle,
                        "pid": pid,
                        "runtime_id": identity,
                        "text": preview["replacement"],
                        "expected_text": context.original,
                    }
                    criterion = {
                        "kind": "desktop_text",
                        "request": {
                            "operation": "read",
                            "handle": handle,
                            "pid": pid,
                            "runtime_id": identity,
                        },
                        "text": preview["replacement"],
                    }
                else:
                    return {
                        "state": "blocked",
                        "epistemic": "UNKNOWN",
                        "message": "Reliable insertion unsupported; choose surface or clipboard",
                    }
                preview["used"] = True
                lease = self.grid.claim_interaction(session, "input")
                view = self.propose(
                    session,
                    Intent(
                        "Apply reviewed desktop text",
                        kind="capability",
                        capability_kind="desktop_clipboard"
                        if destination == "clipboard"
                        else "desktop_control",
                        parameters={"request": request},
                        criterion=criterion,
                    ),
                    preview["mode"],
                )
                view["preview_consumed"] = True
                if context and "task_id" in view and destination == "focused":
                    self.store.transient[view["task_id"]]["context_id"] = context.id
                if "task_id" in view:
                    plan = self.store.get("plan", view["task_id"])
                    plan["interaction"] = {"resource": "input", "generation": lease["generation"]}
                    self.store.put("plan", view["task_id"], plan)
                    lease["task_id"] = view["task_id"]
                    self.store.put("interaction_lease", "input", lease)
                return view
        raise ValueError("unsupported desktop request")

    def preview(
        self, session: SessionHandle, text: str, context: DesktopContext | None, mode: str
    ) -> dict[str, Any]:
        if not text or len(text) > 8192 or len(self.previews) >= 64:
            raise ValueError("preview bound exceeded; discard finished interactions")
        if context:
            self.attached(session, context.id)
        replacement = text
        if context and context.original is not None:
            if mode == "Dictate":
                replacement = context.original + text
            elif context.selection_start is not None:
                start = context.selection_start
                if context.original[start : start + len(context.text or "")] != context.text:
                    raise StateConflict("structured selection offsets unavailable")
                replacement = (
                    context.original[:start]
                    + text
                    + context.original[start + len(context.text or "") :]
                )
        if len(replacement) > 8192:
            raise ValueError("destination exceeds bounded text size")
        identifier = new_id()
        expires = self.grid.clock() + 15
        self.previews[identifier] = {
            "session": session.id,
            "text": text,
            "context": context,
            "replacement": replacement,
            "mode": mode,
            "used": False,
            "expires": expires,
        }
        return {
            "preview_id": identifier,
            "before": context.text if context else None,
            "after": text,
            "epistemic": "REPORTED",
            "expires": expires,
            "focused_before": context.original if context and context.destination else None,
            "focused_after": replacement if context and context.destination else None,
            "mode": mode,
            "destinations": ["surface", "clipboard"]
            + (["focused"] if context and context.destination else []),
        }

    def transcript(
        self, session: SessionHandle, transcript: Transcript, stop: StopToken, context_id: str = ""
    ) -> dict[str, Any]:
        self.permission(session, "desktop.voice", ("desktop:microphone",))
        stop.check()
        if not transcript.final:
            raise ValueError("provisional dictation cannot be applied")
        context = self.attached(session, context_id) if context_id else None
        return self.preview(session, transcript.text, context, "Dictate")
