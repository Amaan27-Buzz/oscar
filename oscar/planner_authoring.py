"""Two signed reviews over the existing Executive model-planning path."""

from dataclasses import replace
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

    def capabilities(self, pins: Any, grants: frozenset[str]) -> list[dict[str, Any]]:
        if not isinstance(pins, list) or not 2 <= len(pins) <= 16:
            raise ValueError("select a model and one to fifteen action capabilities")
        result = []
        for pin in pins:
            if not isinstance(pin, dict) or set(pin) != {"node_id", "capability_id"}:
                raise ValueError("exact capability selection required")
            node = self.h.store.get("node", pin["node_id"])
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
            import re

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
            request = replace(
                executor.template,
                prompt=value["goal"],
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
            pins = [
                {"node_id": c["node_id"], "capability_id": c["id"], "kind": c["input_kind"]}
                for c in caps
                if c != planner
            ]
            step = h.executive.planning_step(
                value["goal"],
                pins,
                {"node_id": planner["node_id"], "capability_id": planner["id"]},
                mode,
                sources,
                digest(executor.planning_configuration()),
            )
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
    ) -> None:
        h = self.h
        if operation == "plan_draft":
            caps = state["capabilities"]
            worker = h.executive.worker(
                value["name"],
                [(c["node_id"], c["id"]) for c in caps],
                tuple(sorted({p for c in caps for p in c["permissions"]})),
                owner_authorized=True,
            )
            proposal = h.executive.draft_plan(
                worker,
                value["goal"],
                mode=value["mode"],
                planning_sources=state["sources"],
                planning_configuration=digest(state["model_configuration"]),
            )
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
                },
            )
        else:
            row = state["request"]
            proposal = h.executive.propose_from_result(
                row["worker_id"], row["goal"], state["planner_task_id"], **value
            )
            h.store.put("planner_request", identifier, {**row, "accepted_goal": proposal["id"]})
        h.executive.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
        h.store.put(
            "executive_owner", proposal["id"], {**owner, "review_digest": proposal["review_digest"]}
        )

    def snapshot(self) -> list[dict[str, Any]]:
        rows = []
        for row in self.h.store.all("planner_request"):
            if row["relationship"] != self.h.runtime.relationship_id:
                continue
            tasks = self.h.executive._tasks(row["goal_id"])
            state = "accepted" if row.get("accepted_goal") else "waiting"
            if state == "waiting" and tasks:
                status = self.h.store.task(tasks[-1]).state
                state = (
                    "reported"
                    if status in {TaskState.PARTIALLY_VERIFIED, TaskState.VERIFIED}
                    else str(status)
                )
            rows.append({"id": row["id"], "goal": row["goal"], "state": state})
        return rows[:64]
