"""Signed reviews or current standing delegation over Executive model planning."""

import json
import re
from dataclasses import asdict, replace
from typing import TYPE_CHECKING, Any

from .contracts import TaskState, new_id, record
from .executive import digest
from .harness import ModelExecutor
from .models import Mode
from .storage import StateConflict

if TYPE_CHECKING:
    from .harness import Harness


class PlannerAuthoring:
    def __init__(self, harness: "Harness"):
        self.h = harness

    @staticmethod
    def descriptor(cap: dict[str, Any]) -> dict[str, Any]:
        """Examples pass through the same typed forms used by native action admission."""
        from .contracts import Capability
        from .desktop_actions import OPERATIONS, form_intent
        from .jev import Intent

        kind = cap["input_kind"]
        examples = []
        if kind == "addition":
            examples.append(asdict(Intent("2 + 3")))
        elif kind == "file_write":
            examples.append(asdict(Intent("Save reviewed text", "file_write", "notes.txt", "Text")))
        elif kind == "coding" and cap["id"] == "machine.agent.codex":
            examples.append(
                asdict(
                    Intent(
                        "Implement the requested repository change",
                        "capability",
                        capability_kind="coding",
                        parameters={
                            "arguments": [
                                "exec",
                                "Implement the requested change and run relevant checks.",
                            ],
                            "cwd": ".",
                            "timeout": 120,
                        },
                        criterion={"kind": "unavailable"},
                    )
                )
            )
        else:
            values = {
                "path": "notes.txt",
                "pattern": "*.txt",
                "name": "reviewed-branch",
                "text": "Text",
                "url": "https://example.com",
                "workflow": json.dumps(
                    {
                        "request": {
                            "origins": ["https://example.com"],
                            "steps": [
                                {"operation": "navigate", "url": "https://example.com/form"},
                                {
                                    "operation": "fill",
                                    "selector": "#message",
                                    "text": "Reviewed text",
                                },
                                {"operation": "submit", "selector": "#submit"},
                                {"operation": "wait", "selector": "#receipt"},
                                {"operation": "inspect"},
                            ],
                            "timeout": 30,
                            "max_text": 4096,
                        },
                        "verification": {
                            "url": "https://example.com/receipt",
                            "selector": "#receipt",
                            "text": "Reviewed text",
                        },
                    }
                ),
            }
            fields = {
                "read_file": ("path",),
                "find_files": ("pattern",),
                "git_branch": ("name",),
                "ps_file_hash": ("path",),
                "ps_write_utf8": ("path", "text"),
                "inspect_page": ("url",),
                "browser_workflow": ("workflow",),
            }
            for operation in OPERATIONS.get(kind, ()):
                # Native app/program identity requires a separate registered-target selection.
                if operation in {"launch_app", "program_version"}:
                    continue
                intent = form_intent(
                    Capability.from_dict(cap),
                    {
                        "capability_id": cap["id"],
                        "operation": operation,
                        "fields": {key: values[key] for key in fields.get(operation, ())},
                    },
                    {},
                )
                examples.append(asdict(intent))
        return {
            "node_id": cap["node_id"],
            "capability_id": cap["id"],
            "kind": kind,
            "summary": cap["summary"],
            "intent_examples": examples,
            **(
                {
                    "intent_rule": (
                        "Use only this advertised installed Codex executor. arguments is an exact "
                        "argv array. Host execution is trusted host authority, not a filesystem "
                        "sandbox. Do not request credential enrollment, permission bypasses or "
                        "unrequested publication. Process exit/output is only REPORTED. "
                        "Use file_exact with literal path/content only when the objective supplies "
                        "those exact expected bytes; never invent successful test evidence."
                    )
                }
                if kind == "coding" and examples
                else {}
            ),
            **(
                {
                    "intent_rule": "Addition intent text must be only A + B, "
                    "with integer operands; "
                    "no Calculate prefix or prose. Copy the example's other null fields."
                }
                if kind == "addition"
                else {}
            ),
            **(
                {
                    "verification_rule": (
                        "Optional browser verification requires an exact URL, selector and "
                        "expected text supplied by the owner or current source evidence. "
                        "Omit it when unknown; never invent a receipt."
                    )
                }
                if kind == "browser"
                else {}
            ),
        }

    def conversation(
        self, text: str, node: str, session: str, scope: str, grants: frozenset[str]
    ) -> dict[str, Any] | None:
        """Conversation uses signed reviews unless an exact Full Access grant covers it."""
        from .assistance import Assistance
        from .jev import DecisionRoute, Intent, decide

        instruction = re.sub(
            r"^(?:please |(?:can|could|would) you )", "", text.strip(), count=1, flags=re.IGNORECASE
        )
        delegated = re.fullmatch(
            r"(?:delegate|create) (?:a )?worker ([A-Za-z0-9 _-]{1,64}):\s*(.+)",
            instruction,
            re.IGNORECASE | re.DOTALL,
        )
        if delegated:
            instruction = delegated[2]
        followup = re.fullmatch(
            r"(?:review|proceed with|accept)(?: the)? (?:suggested )?plan"
            r"(?: ([a-f0-9-]{16,80}))?[.!]?",
            instruction,
            re.IGNORECASE,
        )
        explicit = re.fullmatch(
            r"on device ([A-Za-z0-9_.-]{1,80}):\s*(.+)", instruction, re.IGNORECASE | re.DOTALL
        )
        distributed = re.fullmatch(
            r"across devices ([A-Za-z0-9_., -]+):\s*(.+)", instruction, re.IGNORECASE | re.DOTALL
        )
        targets = (
            [explicit[1]]
            if explicit
            else [part.strip() for part in distributed[1].split(",")]
            if distributed
            else None
        )
        goal = explicit[2] if explicit else distributed[2] if distributed else instruction
        if not followup:
            names = tuple(
                row[0]
                for row in self.h.archive.db.execute(
                    "SELECT alias FROM archive_aliases WHERE relationship=? LIMIT 1000",
                    (self.h.runtime.relationship_id,),
                )
            )
            decision = decide(Intent(goal), names)
            if (
                decision.memory_required
                or decision.route
                in {DecisionRoute.WORLD, DecisionRoute.RECALL, DecisionRoute.VERIFY}
                or not (
                    re.match(
                        r"(?:plan|create|write|save|make|prepare|build|organize|open|launch|"
                        r"send|schedule|update|edit|fix|debug|implement|download|upload|"
                        r"move|copy|rename|delete|run|install|publish|deploy|"
                        r"fill|click|submit|select|navigate)\b",
                        goal,
                        re.IGNORECASE,
                    )
                    or re.match(r"calculate\b.+\bthen\b", goal, re.IGNORECASE | re.DOTALL)
                )
            ):
                return None
        try:
            grants = Assistance(self.h).authorize(node, session, scope, grants)
            from .authority import StandingAuthority

            key = StandingAuthority(
                self.h.store, self.h.grid, self.h.runtime.relationship_id
            )._owner(node, session, scope, grants)
            owner = {"node": node, "session": session, "scope": scope, "public_key": key}
            if followup:
                rows = []
                for row in self.h.store.all("planner_request"):
                    if (
                        row["relationship"] != self.h.runtime.relationship_id
                        or row.get("accepted_goal")
                        or followup[1]
                        and row["id"] != followup[1]
                    ):
                        continue
                    owner = self.h.store.get("executive_owner", row["goal_id"])
                    if (owner["node"], owner["session"], owner["scope"]) == (node, session, scope):
                        rows.append(row)
                if len(rows) != 1:
                    raise ValueError(
                        "Choose one current plan by its ID; no unique plan belongs to this session."
                    )
                change = {
                    "operation": "plan_accept",
                    "id": rows[0]["id"],
                    "value": {
                        "start_at": None,
                        "interval_seconds": None,
                        "max_runs": 1,
                        "priority": 0,
                    },
                }
            else:
                if targets is not None and (
                    not 1 <= len(targets) <= 8
                    or len(set(targets)) != len(targets)
                    or any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", t) for t in targets)
                ):
                    raise ValueError("Choose one to eight exact, comma-separated device IDs.")
                if not 1 <= len(goal) <= 480:
                    raise ValueError("Describe the objective in at most 480 characters.")
                if re.match(r"(?:send|schedule|publish|deploy|install)\b", goal, re.IGNORECASE):
                    raise ValueError(
                        "Specify the exact available account, destination and supported action. "
                        "Account or privileged operations cannot be inferred from a plan."
                    )
                available = [
                    cap
                    for n in self.h.grid.nodes()
                    if n["id"] in self.h.executive.targets
                    for cap in n["capabilities"]
                    if set(cap["permissions"]) <= grants
                    and any(
                        c.id == cap["id"] and c.node_id == cap["node_id"]
                        for c in self.h.grid.search(cap["input_kind"])
                    )
                ]
                try:
                    self.delegation(owner, [])
                except PermissionError:
                    pass
                else:
                    authority = StandingAuthority(
                        self.h.store, self.h.grid, self.h.runtime.relationship_id
                    )
                    available = [
                        c
                        for c in available
                        if authority.permits(c, self.h.executive.targets[c["node_id"]][1])
                    ]
                planners = [
                    c
                    for c in available
                    if c["input_kind"] == "model_reasoning" and c["node_id"] == self.h.node_id
                ]
                actions = [
                    c
                    for c in available
                    if (targets is None or c["node_id"] in targets)
                    and self.descriptor(c)["intent_examples"]
                ]
                duplicates = {
                    c["input_kind"]
                    for c in actions
                    if sum(a["input_kind"] == c["input_kind"] for a in actions) > 1
                }
                if targets is not None and set(targets) - {c["node_id"] for c in actions}:
                    raise PermissionError(
                        "Every selected device needs a current scoped action capability."
                    )
                if duplicates and distributed is None:
                    devices = ", ".join(
                        sorted({c["node_id"] for c in actions if c["input_kind"] in duplicates})
                    )
                    raise ValueError(
                        "Choose an action device: "
                        + devices
                        + ". Use â€˜On device DEVICE-ID: objectiveâ€™."
                    )
                if len(planners) != 1 or not actions:
                    raise PermissionError(
                        "A configured model and available scoped action device are required."
                    )
                if len(actions) > 15:
                    raise ValueError(
                        "Choose a device with at most fifteen supported action capabilities."
                    )
                change = {
                    "operation": "plan_draft",
                    "id": "new",
                    "value": {
                        "name": delegated[1].strip() if delegated else "Conversation objective",
                        "goal": goal,
                        "mode": "auto",
                        "capabilities": [
                            {"node_id": c["node_id"], "capability_id": c["id"]}
                            for c in [planners[0], *actions]
                        ],
                    },
                }
            state = self.material(change["operation"], change["id"], change["value"], grants)
            try:
                pin = self.delegation(owner, state["capabilities"])
            except PermissionError:
                pin = None
            if pin is not None and change["operation"] == "plan_draft":
                with self.h.store.transaction():
                    if self.delegation(owner, state["capabilities"]) != pin:
                        raise PermissionError("planning delegation changed")
                    goal_id = self.complete(
                        change["operation"],
                        change["id"],
                        change["value"],
                        state,
                        {**owner, "standing": pin},
                    )
                return {"assistance_started": {"id": goal_id, "mode": "full", "state": "enabled"}}
            return {"assistance_proposal": change}
        except (ValueError, PermissionError, StateConflict) as error:
            return {"state": "blocked", "epistemic": "UNKNOWN", "message": str(error)}

    def delegation(self, owner: dict[str, Any], caps: list[dict[str, Any]]) -> dict[str, Any]:
        from .authority import StandingAuthority

        authority = StandingAuthority(self.h.store, self.h.grid, self.h.runtime.relationship_id)
        state = authority._active()
        if (
            state["mode"] != "full"
            or (state["owner_node"], state["owner_session"], state["scope"])
            != (owner["node"], owner["session"], owner["scope"])
            or any(
                c["node_id"] not in self.h.executive.targets
                or not authority.permits(c, self.h.executive.targets[c["node_id"]][1])
                for c in caps
            )
        ):
            raise PermissionError(
                "current Full Access must cover this owner and every planned capability"
            )
        return {k: state[k] for k in ("grant_id", "epoch")}

    def advance_delegated(self) -> None:
        """Resume durable planning once; each effect still passes current runtime authority."""
        h = self.h
        rows = [
            r
            for r in h.store.all("planner_request")
            if r.get("delegation")
            and not r.get("accepted_goal")
            and not r.get("autonomy_blocked")
            and r["relationship"] == h.runtime.relationship_id
        ]
        for candidate in rows[:64]:
            tasks = h.executive._tasks(candidate["goal_id"])
            if not tasks or any(
                h.store.task(t).state
                in {
                    TaskState.PLANNED,
                    TaskState.EXECUTING,
                    TaskState.AWAITING_RESULT,
                }
                for t in tasks
            ):
                continue
            try:
                with h.store.transaction():
                    row = h.store.get("planner_request", candidate["id"])
                    if row.get("accepted_goal") or row.get("autonomy_blocked"):
                        continue
                    owner = h.store.get("executive_owner", row["goal_id"])
                    grants = frozenset(h.store.get("session", owner["session"])["scopes"])
                    from .assistance import Assistance

                    grants = Assistance(h).authorize(
                        owner["node"], owner["session"], owner["scope"], grants
                    )
                    value = {
                        "start_at": None,
                        "interval_seconds": None,
                        "max_runs": 1,
                        "priority": 0,
                    }
                    material = self.material("plan_accept", row["id"], value, grants)
                    if self.delegation(owner, material["capabilities"]) != row["delegation"]:
                        raise PermissionError("planning delegation changed")
                    self.complete("plan_accept", row["id"], value, material, owner)
            except (KeyError, ValueError, PermissionError, StateConflict):
                with h.store.transaction():
                    row = h.store.get("planner_request", candidate["id"])
                    if not row.get("accepted_goal"):
                        h.store.put("planner_request", row["id"], {**row, "autonomy_blocked": True})
                        h.store.audit("", "delegated_planning_blocked", {"request_id": row["id"]})

    def capabilities(self, pins: Any, grants: frozenset[str]) -> list[dict[str, Any]]:
        if not isinstance(pins, list) or not 2 <= len(pins) <= 16:
            raise ValueError("select a model and one to fifteen action capabilities")
        result = []
        for pin in pins:
            if (
                not isinstance(pin, dict)
                or set(pin) != {"node_id", "capability_id"}
                or any(not isinstance(v, str) or not 1 <= len(v) <= 240 for v in pin.values())
            ):
                raise ValueError("exact capability selection required")
            try:
                node = self.h.store.get("node", pin["node_id"])
            except KeyError:
                raise PermissionError("selected planning executor unavailable") from None
            matches = [c for c in node["capabilities"] if c["id"] == pin["capability_id"]]
            if len(matches) != 1 or pin["node_id"] not in self.h.executive.targets:
                raise PermissionError("selected planning executor unavailable")
            cap = matches[0]
            if not set(cap["permissions"]) <= grants or not any(
                c.id == cap["id"] and c.node_id == cap["node_id"]
                for c in self.h.grid.search(cap["input_kind"])
            ):
                raise PermissionError("current scoped capability required")
            result.append(cap)
        if len({(c["node_id"], c["id"]) for c in result}) != len(result):
            raise ValueError("duplicate planning capability")
        return result

    def material(
        self, operation: str, identifier: str, value: dict[str, Any], grants: frozenset[str]
    ) -> dict[str, Any]:
        h = self.h
        state: dict[str, Any]
        if operation == "plan_draft":
            if identifier != "new" or set(value) != {"name", "goal", "capabilities", "mode"}:
                raise ValueError("explicit goal, capabilities and model privacy required")
            if not isinstance(value["goal"], str) or not 1 <= len(value["goal"]) <= 480:
                raise ValueError("bounded planning goal required")
            if not isinstance(value["name"], str) or not re.fullmatch(
                r"[A-Za-z0-9 _-]{1,64}", value["name"]
            ):
                raise ValueError("bounded responsibility name required")
            caps = self.capabilities(value["capabilities"], grants)
            planners = [c for c in caps if c["input_kind"] == "model_reasoning"]
            if len(planners) != 1 or planners[0]["node_id"] != h.node_id:
                raise PermissionError("one configured Core model route required")
            planner = planners[0]
            executor = h.dispatcher.executors.get(planner["id"])
            if not isinstance(executor, ModelExecutor):
                raise PermissionError("configured model executor unavailable")
            mode = value["mode"]
            if mode not in {"auto", "private"}:
                raise ValueError("choose private or configured routing explicitly")
            pins = [self.descriptor(c) for c in caps if c != planner]
            step = h.executive.planning_step(
                value["goal"],
                pins,
                {"node_id": planner["node_id"], "capability_id": planner["id"]},
                mode,
                [],
                digest(executor.planning_configuration()),
            )
            parameters = step["intent"]["parameters"]
            if "structured" in executor.template.required:
                from .planning_contract import executive_plan_schema

                parameters["prompt"] += "\nResponse JSON schema: " + json.dumps(
                    executive_plan_schema()
                )
            request = replace(
                executor.template,
                prompt=parameters["prompt"],
                mode=Mode.PRIVATE if mode == "private" else executor.template.mode,
            )
            routes = executor.router.rank(request, executor.policy)
            providers = sorted({r.provider for r in routes})
            if not providers or len(providers) > 32:
                raise PermissionError("no currently eligible configured model source")
            sources = [
                {"id": p, "contract": digest(record(executor.router.registry.providers[p]))}
                for p in providers
            ]
            parameters["planning_sources"] = sources
            state = {
                "capabilities": caps,
                "step": step,
                "sources": sources,
                "model_configuration": executor.planning_configuration(),
                "privacy": (
                    "Only this goal and selected capability descriptors are model input. "
                    "No files, memories or ambient context are attached."
                ),
                "providers": [
                    {
                        "id": p,
                        "endpoint": executor.router.registry.providers[p].base_url,
                        "private": executor.router.registry.providers[p].private,
                        "local": executor.router.registry.providers[p].local,
                    }
                    for p in providers
                ],
            }
        else:
            if operation != "plan_accept" or set(value) != {
                "start_at",
                "interval_seconds",
                "max_runs",
                "priority",
            }:
                raise ValueError("exact suggested-plan schedule required")
            row = h.store.get("planner_request", identifier)
            if row["relationship"] != h.runtime.relationship_id or row.get("accepted_goal"):
                raise PermissionError("planning request unavailable or already accepted")
            owner = h.store.get("executive_owner", row["goal_id"])
            from .authority import StandingAuthority

            if (
                StandingAuthority(h.store, h.grid, h.runtime.relationship_id)._owner(
                    owner["node"], owner["session"], owner["scope"], frozenset({owner["scope"]})
                )
                != owner["public_key"]
            ):
                raise PermissionError("planning owner session changed")
            executor = h.dispatcher.executors.get(row["planner_id"])
            if (
                not isinstance(executor, ModelExecutor)
                or digest(executor.planning_configuration()) != row["configuration"]
            ):
                raise PermissionError("planning model configuration changed")
            for source in row["sources"]:
                provider = executor.router.registry.providers.get(source["id"])
                if provider is None or digest(record(provider)) != source["contract"]:
                    raise PermissionError("planning model source changed")
            worker = h.executive._row("executive_worker", row["worker_id"])
            if not worker["enabled"]:
                raise PermissionError("planning Worker retired")
            original_grants = frozenset(
                h.store.get("session", owner["session"])["scopes"]
            ) & frozenset(h.store.get("node", owner["node"])["scopes"])
            caps = self.capabilities(row["capabilities"], grants & original_grants)
            if row["contracts"] != [digest(c) for c in caps]:
                raise PermissionError("planning capability contracts changed")
            tasks = h.executive._tasks(row["goal_id"])
            if len(tasks) != 1:
                raise StateConflict("one completed model result required")
            steps = h.executive.validate_steps(worker, h.executive.result_steps(tasks[0]))
            if any(
                s["capability_id"] == row["planner_id"] and s["node_id"] == h.node_id for s in steps
            ):
                raise PermissionError("suggested effects cannot initiate another model call")
            state = {
                "request": row,
                "owner": owner,
                "worker": worker,
                "capabilities": caps,
                "steps": steps,
                "planner_task_id": tasks[0],
                "routing_evidence": [
                    {
                        k: r.get(k)
                        for k in (
                            "id",
                            "provider",
                            "model",
                            "actual_provider",
                            "actual_model",
                            "mode",
                            "provider_response_success",
                            "verification_evidence_id",
                        )
                    }
                    for r in h.store.all("route_history")
                    if r["task_id"] == tasks[0]
                ],
                "result_digest": digest(
                    [r for r in h.store.all("result") if r["task_id"] == tasks[0]]
                ),
            }
        state["executors"] = [
            {"node_id": c["node_id"], "session_id": h.executive.targets[c["node_id"]][1].id}
            for c in state["capabilities"]
        ]
        state["accounts"] = [
            {k: a[k] for k in ("id", "generation", "status")}
            for a in h.store.all("connected_account")
        ]
        state["policy"] = h.store.all("personal_policy")
        return state

    def complete(
        self,
        operation: str,
        identifier: str,
        value: dict[str, Any],
        state: dict[str, Any],
        owner: dict[str, Any],
    ) -> str:
        h = self.h
        if operation == "plan_draft":
            caps = state["capabilities"]
            worker = h.executive.worker(
                value["name"],
                [(c["node_id"], c["id"]) for c in caps],
                tuple(sorted({p for c in caps for p in c["permissions"]})),
                owner_authorized=True,
                temporary=True,
            )
            proposal = h.executive.propose(worker, "Draft plan: " + value["goal"], [state["step"]])
            request_id = new_id()
            h.store.put(
                "planner_request",
                request_id,
                {
                    "id": request_id,
                    "relationship": h.runtime.relationship_id,
                    "goal": value["goal"],
                    "goal_id": proposal["id"],
                    "worker_id": worker,
                    "capabilities": value["capabilities"],
                    "contracts": [digest(c) for c in caps],
                    "planner_id": state["step"]["capability_id"],
                    "sources": state["sources"],
                    "configuration": digest(state["model_configuration"]),
                    **({"delegation": owner["standing"]} if owner.get("standing") else {}),
                },
            )
        else:
            row = state["request"]
            proposal = h.executive.propose_from_result(
                row["worker_id"], row["goal"], state["planner_task_id"], **value
            )
            h.store.put("planner_request", identifier, {**row, "accepted_goal": proposal["id"]})
            draft = h.store.get("executive_goal", row["goal_id"])
            h.store.put("executive_goal", draft["id"], {**draft, "state": "reported"})
        h.executive.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
        h.store.put(
            "executive_owner", proposal["id"], {**owner, "review_digest": proposal["review_digest"]}
        )
        return str(proposal["id"])

    def snapshot(self) -> list[dict[str, Any]]:
        rows = []
        for row in self.h.store.all("planner_request"):
            if row["relationship"] != self.h.runtime.relationship_id:
                continue
            tasks = self.h.executive._tasks(row["goal_id"])
            state = (
                "accepted"
                if row.get("accepted_goal")
                else "blocked"
                if row.get("autonomy_blocked")
                else "waiting"
            )
            if state == "waiting" and tasks:
                status = self.h.store.task(tasks[-1]).state
                state = (
                    "reported"
                    if status in {TaskState.PARTIALLY_VERIFIED, TaskState.VERIFIED}
                    else str(status)
                )
            rows.append({"id": row["id"], "goal": row["goal"], "state": state})
        return rows[:64]
