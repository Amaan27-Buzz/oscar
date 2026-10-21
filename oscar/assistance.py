"""Signed native authoring over the existing Executive and source-specific Sentry."""

import base64
import json
import re
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from .contracts import Epistemic, new_id, record
from .credentials import redact_runtime_secrets
from .mobile import display_digest, fingerprint
from .policy import PersonalPolicy
from .sentry import AwarenessMode, SentrySettings, SentryState
from .storage import StateConflict

if TYPE_CHECKING:
    from .harness import Harness


class Assistance:
    def __init__(self, harness: "Harness"):
        self.h = harness

    @staticmethod
    def natural_change(text: str, name: str = "OSCAR responsibility") -> dict[str, Any]:
        """Explicit bounded schedules; missing run counts never imply standing authority."""
        if not isinstance(text, str) or not 1 <= len(text) <= 512:
            raise ValueError("bounded responsibility instruction required")
        interval, runs = None, 1
        scheduled = re.fullmatch(
            r"every (hour|day|week) for ([0-9]{1,3}) (?:runs|times)[:,] ?(.+)",
            text.strip(),
            re.IGNORECASE | re.DOTALL,
        )
        if scheduled:
            interval = {"hour": 3600, "day": 86400, "week": 604800}[scheduled[1].lower()]
            runs, text = int(scheduled[2]), scheduled[3]
        elif re.match(r"every\b", text, re.IGNORECASE):
            raise ValueError("specify every hour/day/week for 1..100 runs, followed by a colon")
        if not 1 <= runs <= 100:
            raise ValueError("responsibility requires 1..100 runs")
        return {
            "operation": "create_natural",
            "id": "new",
            "value": {
                "name": name,
                "instruction": text,
                "node_id": "",
                "start_at": None,
                "interval_seconds": interval,
                "max_runs": runs,
                "priority": 0,
                "conditions": [],
            },
        }

    def natural_value(self, value: dict[str, Any], grants: frozenset[str]) -> dict[str, Any]:
        from .desktop_actions import OPERATIONS, conversation_form, form_intent
        from .jev import Intent, decide

        if (
            set(value)
            != {
                "name",
                "instruction",
                "node_id",
                "start_at",
                "interval_seconds",
                "max_runs",
                "priority",
                "conditions",
            }
            or not isinstance(value["instruction"], str)
            or not 1 <= len(value["instruction"]) <= 512
        ):
            raise ValueError("exact bounded natural responsibility and schedule required")
        if not isinstance(value["node_id"], str):
            raise ValueError("explicit executor selection required")
        lines = [line.strip() for line in value["instruction"].splitlines() if line.strip()]
        if not 1 <= len(lines) <= 16:
            raise ValueError("one explicit action per line, at most sixteen actions")
        steps: list[dict[str, Any]] = []
        for line in lines:
            form = conversation_form(line)
            kind = (
                decide(Intent(line)).capability_kind
                if form is None
                else next(k for k, operations in OPERATIONS.items() if form[0] in operations)
            )
            if kind is None or form is None and kind != "addition":
                raise ValueError("instruction needs an explicit supported action and arguments")
            candidates = [
                cap
                for cap in self.h.grid.search(kind)
                if cap.node_id in self.h.executive.targets
                and (not value["node_id"] or cap.node_id == value["node_id"])
                and set(cap.permissions) <= grants
            ]
            if len(candidates) != 1:
                raise PermissionError("choose one available executor with the required owner scope")
            cap = candidates[0]
            intent = (
                Intent(line)
                if form is None
                else form_intent(
                    cap,
                    {
                        "capability_id": cap.id,
                        "operation": form[0],
                        "fields": form[1],
                    },
                    {},
                )
            )
            # Core file writes use their existing exact-file verifier, not machine metadata.
            if kind == "file_write" and form is not None:
                intent = Intent(line, "file_write", form[1]["path"], form[1]["text"])
            steps.append(
                {
                    "id": "step-" + str(len(steps) + 1),
                    "intent": asdict(intent),
                    "node_id": cap.node_id,
                    "capability_id": cap.id,
                    "depends_on": [steps[-1]["id"]] if steps else [],
                }
            )
        return {k: v for k, v in value.items() if k not in {"instruction", "node_id"}} | {
            "goal": value["instruction"],
            "steps": steps,
        }

    def snapshot(self) -> dict[str, Any]:
        from .authority import StandingAuthority

        h = self.h
        result: dict[str, Any] = {
            "version": 1,
            "relationship_id": h.runtime.relationship_id,
            "core_node_id": h.node_id,
            "authority": StandingAuthority(h.store, h.grid, h.runtime.relationship_id).snapshot(),
            "ask_rules": [
                r.id for r in PersonalPolicy(h.store).rules() if r.enabled and r.effect == "ask"
            ],
            "procedures": self.procedures(),
            "capabilities": [
                {k: c[k] for k in ("id", "node_id", "input_kind", "risk", "permissions")}
                | {"session_id": h.executive.targets[node["id"]][1].id}
                for node in h.grid.nodes()
                if node["id"] in h.executive.targets and node["status"] in {"online", "degraded"}
                for c in node["capabilities"]
            ],
            "sentry": {
                **record(h.world.sentry.settings()),
                "generation": h.world.sentry.configuration()[1],
                "sources": [
                    {k: row[k] for k in ("id", "perceive", "retain", "act", "simulated", "epoch")}
                    for row in h.store.all("perception_source")
                    if row["relationship"] == h.runtime.relationship_id
                ],
            },
            "observed_at_ms": round(h.grid.clock() * 1000),
        }
        authority = result["authority"]
        result["authority"] = {
            k: v for k, v in authority.items() if k not in {"capabilities", "accounts"}
        }
        result["capabilities_total"] = len(result["capabilities"])
        result["sources_total"] = len(result["sentry"]["sources"])
        result["truncated"] = False
        while (
            len(result["capabilities"]) > 256
            or len(result["sentry"]["sources"]) > 64
            or len(json.dumps(result).encode()) > 40000
        ):
            result["truncated"] = True
            if result["capabilities"]:
                result["capabilities"].pop()
            elif result["sentry"]["sources"]:
                result["sentry"]["sources"].pop()
            elif result["procedures"]:
                result["procedures"].pop()
            elif result["ask_rules"]:
                result["ask_rules"].pop()
            else:
                raise ValueError("assistance projection exceeds native response bound")
        return result

    def procedures(self) -> list[dict[str, Any]]:
        result = []
        for row in self.h.store.all("executive_workflow"):
            if row["relationship"] != self.h.runtime.relationship_id:
                continue
            try:
                _, data = self.h.executive._workflow(row["id"])
            except (KeyError, ValueError, PermissionError, StateConflict):
                continue
            state = "candidate"
            if row["evaluation_event_id"]:
                try:
                    assert self.h.runtime.memory is not None
                    event = self.h.runtime.memory.archive.event(row["evaluation_event_id"])
                    evaluation = json.loads(event.content)
                    if (
                        event.relationship_id == self.h.runtime.relationship_id
                        and evaluation["workflow_event_id"] == row["event_id"]
                        and event.kind == "workflow_evaluation"
                        and event.status == Epistemic.VERIFIED
                        and event.expires_at is not None
                        and event.expires_at > self.h.grid.clock()
                    ):
                        self.h.executive._proof(evaluation["verified_task_ids"])
                        state = "exact_replay_verified"
                except (KeyError, ValueError, PermissionError, StateConflict):
                    pass
            result.append(
                {
                    "id": row["id"],
                    "goal": data["goal"],
                    "source_goal_id": data["source_goal_id"],
                    "state": state,
                    "event_id": row["event_id"],
                }
            )
        return result[:64]

    def material(self, change: dict[str, Any], grants: frozenset[str]) -> dict[str, Any]:
        if set(change) != {"operation", "id", "value"}:
            raise ValueError("exact assistance change required")
        operation, identifier, value = change["operation"], change["id"], change["value"]
        if (
            not isinstance(operation, str)
            or not isinstance(identifier, str)
            or not 1 <= len(identifier) <= 80
            or not isinstance(value, dict)
            or len(json.dumps(change, allow_nan=False).encode()) > 16000
            or redact_runtime_secrets(json.dumps(change)) != json.dumps(change)
        ):
            raise ValueError("bounded non-secret assistance configuration required")
        h, state = self.h, {}
        proposal = None
        if operation == "create_natural":
            value = self.natural_value(value, grants)
            proposal = {"operation": "create", "id": identifier, "value": value}
            operation = "create"
        elif operation == "reuse":
            if set(value) != {"start_at", "interval_seconds", "max_runs", "priority"}:
                raise ValueError("exact replay schedule required")
            _, data = h.executive._workflow(identifier)
            goal = h.executive._row("executive_goal", data["source_goal_id"])
            worker = h.executive._row("executive_worker", goal["worker_id"])
            value = {
                "name": worker["name"],
                "goal": data["goal"],
                "steps": data["steps"],
                "conditions": data["conditions"],
                **value,
            }
            proposal = {"operation": "create", "id": identifier, "value": value}
            operation = "create"
        if operation == "create":
            if set(value) != {
                "name",
                "goal",
                "steps",
                "start_at",
                "interval_seconds",
                "max_runs",
                "priority",
                "conditions",
            }:
                raise ValueError("explicit Worker, steps and schedule required")
            if not isinstance(value["steps"], list) or not 1 <= len(value["steps"]) <= 16:
                raise ValueError("bounded task graph required")
            caps = []
            for step in value["steps"]:
                if (
                    not isinstance(step, dict)
                    or set(step)
                    != {
                        "id",
                        "intent",
                        "node_id",
                        "capability_id",
                        "depends_on",
                    }
                    or not isinstance(step["node_id"], str)
                    or not isinstance(step["capability_id"], str)
                ):
                    raise ValueError("exact typed responsibility step required")
                node = h.store.get("node", step["node_id"])
                found = [c for c in node["capabilities"] if c["id"] == step["capability_id"]]
                if len(found) != 1 or node["id"] not in h.executive.targets:
                    raise PermissionError("selected executor is unavailable")
                cap = found[0]
                if not set(cap["permissions"]) <= grants:
                    raise PermissionError("Worker cannot acquire capabilities outside owner scope")
                caps.append(cap)
            if value["conditions"] and "world:read" not in grants:
                raise PermissionError("context conditions require separate World read permission")
            state = {
                "capabilities": caps,
                "executors": [
                    {
                        "node_id": step["node_id"],
                        "session_id": h.executive.targets[step["node_id"]][1].id,
                    }
                    for step in value["steps"]
                ],
                "workers": len(h.store.all("executive_worker")),
                "goals": len(h.store.all("executive_goal")),
            }
        elif operation in {"pause", "resume", "cancel", "delete", "edit"}:
            goal = h.executive._row("executive_goal", identifier)
            state = {
                "goal": goal,
                "worker": h.executive._row("executive_worker", goal["worker_id"]),
            }
            if operation != "edit" and value:
                raise ValueError("unexpected control parameters")
            if operation == "edit" and (
                set(value) != {"start_at", "interval_seconds", "max_runs", "priority"}
            ):
                raise ValueError("exact replacement schedule required")
        elif operation in {"learn", "evaluate"}:
            if (
                set(value) != ({"retain"} if operation == "learn" else {"retain", "replay_goal_id"})
                or value["retain"] is not True
            ):
                raise ValueError("separate explicit canonical retention approval required")
            if "retain" not in grants:
                raise PermissionError("owner lacks canonical retention permission")
            if operation == "learn":
                goal = h.executive._row("executive_goal", identifier)
                if any(p["source_goal_id"] == identifier for p in self.procedures()):
                    raise StateConflict("a current candidate already references this verified goal")
            else:
                _, data = h.executive._workflow(identifier)
                goal = h.executive._row("executive_goal", value["replay_goal_id"])
                state["source"] = data
            if goal["state"] != "completed" or h.executive._review(goal) != goal["review_digest"]:
                raise PermissionError(
                    "only exact completed independently verified work may be retained"
                )
            tasks = [
                r["task_id"]
                for r in h.store.all("executive_task")
                if r["goal_id"] == goal["id"] and r["occurrence"] == goal["run_index"] - 1
            ]
            state |= {
                "goal": goal,
                "evidence_ids": h.executive._proof(tasks),
                "retention_seconds": 604800,
                "claim": "candidate_only_no_new_authority",
            }
        elif operation == "source_create":
            if identifier != value.get("id"):
                raise ValueError("source identity mismatch")
            state = h.world.review_source(value)
        elif operation == "sentry":
            if set(value) != {"mode", "state", "source_ids", "trigger_keys", "allow_interrupt"}:
                raise ValueError("explicit source-specific awareness configuration required")
            self.settings(value)
            state = {
                "settings": record(h.world.sentry.settings()),
                "generation": h.world.sentry.configuration()[1],
                "sources": [h.world.source_review(i) for i in value["source_ids"]],
            }
        elif operation == "source":
            if set(value) != {"perceive", "retain", "act"} or any(
                type(flag) is not bool for flag in value.values()
            ):
                raise ValueError("separate explicit source grants required")
            state = h.world.source_review(identifier)
        else:
            raise ValueError("unsupported assistance change")
        review = {"change": change, "current": state}
        if proposal is not None:
            review["proposal"] = proposal
        if len(json.dumps(review).encode()) > 24000:
            raise ValueError("responsibility review exceeds native display bound")
        return {
            "task_id": identifier,
            "target": "OSCAR " + operation,
            "change": change,
            "digest": fingerprint(state),
            "review": json.loads(json.dumps(review)),
        }

    @staticmethod
    def settings(value: dict[str, Any]) -> SentrySettings:
        if not isinstance(value["source_ids"], list) or not isinstance(value["trigger_keys"], list):
            raise ValueError("typed source and trigger selection required")
        return SentrySettings(
            mode=AwarenessMode(value["mode"]),
            state=SentryState(value["state"]),
            source_ids=tuple(value["source_ids"]),
            trigger_keys=tuple(value["trigger_keys"]),
            allow_interrupt=value["allow_interrupt"],
        )

    def authorize(
        self, node: str, session: str, scope: str, grants: frozenset[str]
    ) -> frozenset[str]:
        credential = self.h.store.get("session", session)
        grants &= frozenset(credential["scopes"]) & frozenset(
            self.h.store.get("node", node)["scopes"]
        )
        candidates = [
            s
            for s in self.h.store.all("session")
            if s["node_id"] == node
            and scope in s["scopes"]
            and not s["revoked"]
            and s["expires_at"] > self.h.grid.clock()
        ]
        if not candidates:
            raise PermissionError("current owner session required")
        if (
            not PersonalPolicy(self.h.store)
            .evaluate("assistance.manage", (scope,), grants, {"node": node}, confirmed=True)
            .allowed
        ):
            raise PermissionError("assistance management policy denied")
        return grants

    def challenge(
        self, node: str, session: str, scope: str, grants: frozenset[str], change: dict[str, Any]
    ) -> dict[str, Any]:
        grants = self.authorize(node, session, scope, grants)
        from .authority import StandingAuthority

        StandingAuthority(self.h.store, self.h.grid, self.h.runtime.relationship_id)._owner(
            node, session, scope, grants
        )
        material = self.material(change, grants)
        description = {
            "create_natural": "Review this responsibility",
            "create": "Review this responsibility",
            "reuse": "Review a one-time procedure replay",
            "learn": "Review saving this procedure",
            "evaluate": "Review retaining this exact replay evaluation",
            "source_create": "Review a new context source",
        }.get(change["operation"], "Review " + change["operation"] + " for OSCAR")
        review = json.dumps(material["review"], sort_keys=True)
        expires = round((self.h.grid.clock() + 30) * 1000)
        claim = {
            "version": 2,
            "node_id": node,
            "session_id": session,
            "operation": "approve",
            "scope": scope,
            "generation": 1,
            "material": material,
            "nonce": new_id(),
            "expires_at_ms": expires,
            "display_digest": display_digest(
                "approve", scope, material["target"], review, description
            ),
        }
        body = json.dumps(claim, sort_keys=True, separators=(",", ":")).encode()
        if len(body) > 32768:
            raise ValueError("signed responsibility exceeds native review bound")
        encoded = base64.b64encode(body).decode()
        identifier = new_id()
        self.h.store.put("assistance_review", identifier, {"payload": encoded, "used": False})
        return {
            "challenge_id": identifier,
            "signing_payload": encoded,
            "expires_at_ms": expires,
            "operation": "approve",
            "target": material["target"],
            "description": description,
            "scope": scope,
            "generation": 1,
            "review": review,
            "exact_request": description,
            "capability": "assistance.manage",
            "reason": "Create or change this continuing responsibility",
            "consequence": "Work runs only within the reviewed capabilities and current authority",
            "policy_reason": "Exact signed review; grants and executor contracts rechecked",
            "evidence_state": "PLANNED",
        }

    def complete(
        self,
        node: str,
        session: str,
        key: str,
        scope: str,
        grants: frozenset[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        from .remote_grid import verify_signature

        if set(payload) != {"challenge_id", "signature"}:
            raise ValueError("exact signed assistance review required")
        h = self.h
        cancellations: list[str] = []
        with h.store.transaction():
            row = h.store.get("assistance_review", payload["challenge_id"])
            body = base64.b64decode(row["payload"], validate=True)
            claim = json.loads(body)
            if (
                row["used"]
                or claim["node_id"] != node
                or claim["session_id"] != session
                or claim["scope"] != scope
                or claim["expires_at_ms"] <= h.grid.clock() * 1000
            ):
                raise PermissionError("assistance review expired, changed or consumed")
            verify_signature(key, payload["signature"], body)
            from .authority import StandingAuthority

            if (
                StandingAuthority(h.store, h.grid, h.runtime.relationship_id)._owner(
                    node, session, scope, grants
                )
                != key
            ):
                raise PermissionError("owner key changed")
            grants = self.authorize(node, session, scope, grants)
            material = self.material(claim["material"]["change"], grants)
            if material != claim["material"]:
                raise PermissionError("assistance changed since review")
            change = material["change"]
            if "proposal" in material["review"]:
                change = material["review"]["proposal"]
            operation, identifier, value = change["operation"], change["id"], change["value"]
            h.store.put("assistance_review", payload["challenge_id"], {**row, "used": True})
            if operation == "create":
                pairs = list(
                    dict.fromkeys((s["node_id"], s["capability_id"]) for s in value["steps"])
                )
                permissions = tuple(
                    sorted(
                        {
                            p
                            for n, c in pairs
                            for cap in h.store.get("node", n)["capabilities"]
                            if cap["id"] == c
                            for p in cap["permissions"]
                        }
                        | ({"world:read"} if value["conditions"] else set())
                    )
                )
                worker = h.executive.worker(
                    value["name"], pairs, permissions, owner_authorized=True
                )
                proposal = h.executive.propose(
                    worker,
                    value["goal"],
                    value["steps"],
                    **{
                        k: value[k]
                        for k in (
                            "start_at",
                            "interval_seconds",
                            "max_runs",
                            "priority",
                            "conditions",
                        )
                    },
                )
                h.executive.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
                h.store.put(
                    "executive_owner",
                    proposal["id"],
                    {
                        "node": node,
                        "session": session,
                        "scope": scope,
                        "public_key": key,
                        "review_digest": proposal["review_digest"],
                    },
                )
            elif operation == "source_create":
                h.world.configure_native_source(value, owner_authorized=True)
            elif operation == "learn":
                h.executive.learn(
                    identifier,
                    owner_authorized=True,
                    retain_authorized=True,
                    event_id=payload["challenge_id"],
                )
            elif operation == "evaluate":
                h.executive.evaluate_workflow(
                    identifier,
                    value["replay_goal_id"],
                    owner_authorized=True,
                    retain_authorized=True,
                    event_id=payload["challenge_id"],
                )
            elif operation == "sentry":
                h.world.sentry.configure(self.settings(value), owner_authorized=True)
                h.world.wake.set()
            elif operation == "source":
                h.world.set_source_grants(identifier, value, owner_authorized=True)
            elif operation == "edit":
                proposal = h.executive.replan(identifier, owner_authorized=True, **value)
                h.executive.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
                h.store.put(
                    "executive_owner",
                    proposal["id"],
                    {
                        "node": node,
                        "session": session,
                        "scope": scope,
                        "public_key": key,
                        "review_digest": proposal["review_digest"],
                    },
                )
            else:
                goal = h.executive._row("executive_goal", identifier)
                if operation == "delete":
                    # Retire instead of erasing execution history or uncertain side effects.
                    cancellations = h.executive.revoke_worker_state(
                        goal["worker_id"], owner_authorized=True
                    )
                else:
                    cancellations = h.executive.control_state(
                        identifier, operation, owner_authorized=True
                    )
                    if operation == "resume":
                        h.store.put(
                            "executive_owner",
                            identifier,
                            {
                                "node": node,
                                "session": session,
                                "scope": scope,
                                "public_key": key,
                                "review_digest": goal["review_digest"],
                            },
                        )
            h.store.audit(
                "",
                "owner_assistance_change",
                {"node_id": node, "operation": material["change"]["operation"], "id": identifier},
            )
        for task_id in cancellations:
            h.runtime.cancel(task_id, h.executive.targets)
        return {
            "assistance": self.snapshot(),
            "executive": h.executive.snapshot(),
            "status": "verified",
            "message": "OSCAR responsibility settings updated",
        }
