"""Private, expiring MCP arguments behind reviewed Executive plan references."""

import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from .connectors import ConnectionState
from .contracts import Task, TaskState
from .executive import digest
from .jev import Intent

if TYPE_CHECKING:
    from .harness import Harness


class MCPPlanning:
    def __init__(self, harness: "Harness"):
        self.h = harness
        self.inputs: dict[str, dict[str, Any]] = {}
        harness.store.close_callbacks.append(self.close)
        harness.store.task_resources.add(self)

    def close(self) -> None:
        for ref in self.inputs:
            self.h.connectors.release_request(ref)
        self.inputs.clear()

    def contract(self, cap: dict[str, Any]) -> dict[str, Any]:
        from .connector_providers import mcp_capability_name
        from .mcp_client import schema_digest

        instance_id, name = cap["id"].split(":", 1)
        instance = self.h.connectors.instances[instance_id]
        client = self.h.plugins.sessions[instance_id]
        spec = next(s for s in instance.manifest.capabilities if s.name == name)
        tool = next(t for t in client.tools if mcp_capability_name(t["name"]) == name)
        if (
            self.h.connectors.state(instance, spec) != ConnectionState.READY
            or instance.account_id is None
            or instance.account_generation is None
            or self.h.store.get("mcp_installation", instance_id)["schemas"].get(tool["name"])
            != schema_digest(tool["inputSchema"])
        ):
            raise PermissionError("current account-bound MCP tool required")
        return {
            "capability": cap,
            "instance": {**asdict(instance), "granted_scopes": sorted(instance.granted_scopes)},
            "tool": tool["name"],
            "schema": tool["inputSchema"],
        }

    def descriptor(self, cap: dict[str, Any]) -> dict[str, Any] | None:
        if cap.get("output_kind") != "connector-reference":
            return None
        try:
            current = self.contract(cap)
        except (KeyError, StopIteration, ValueError, PermissionError):
            return None
        instance = current["instance"]
        return {
            "node_id": cap["node_id"],
            "capability_id": cap["id"],
            "kind": cap["input_kind"],
            "summary": "Explicitly installed, reviewed MCP tool",
            "account_id": instance["account_id"],
            "account_generation": instance["account_generation"],
            "operation": current["tool"],
            "argument_schema": current["schema"],
            "intent_examples": [
                asdict(
                    Intent(
                        "Invoke selected MCP tool",
                        "capability",
                        capability_kind=cap["input_kind"],
                        parameters={"arguments": {}},
                    )
                )
            ],
            "intent_rule": (
                "Supply parameters with exactly arguments, an object matching argument_schema. "
                "Use the exact selected account/tool; never invent arguments or references. "
                "No inputs substitutions, verification claims or observation stages for MCP. "
                "Arguments are privately staged for exact review and one immediate execution. "
                "A tool report does not independently verify the objective."
            ),
        }

    def pins(self, caps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "node_id": c["node_id"],
                "capability_id": c["id"],
                "contract": digest(self.contract(c)),
            }
            for c in caps
            if self.descriptor(c) is not None
        ]

    def current(self, pin: dict[str, Any]) -> dict[str, Any]:
        cap = next(
            c
            for c in self.h.store.get("node", pin["node_id"])["capabilities"]
            if c["id"] == pin["capability_id"]
        )
        if digest(self.contract(cap)) != pin["contract"] or not any(
            c.id == cap["id"] and c.node_id == cap["node_id"]
            for c in self.h.grid.search(cap["input_kind"])
        ):
            raise PermissionError("MCP planning contract changed")
        return self.contract(cap)

    def reap(self) -> None:
        for ref, row in list(self.inputs.items()):
            if row["expires"] <= self.h.grid.clock() or (
                ref not in self.h.connectors.requests and not row.get("effect_task")
            ):
                self.h.connectors.release_request(ref)
                self.inputs.pop(ref, None)
        for ref, entry in list(self.h.store.transient.items()):
            if ref.startswith("assistance-review:") and entry["expires"] <= self.h.grid.clock():
                self.h.store.transient.pop(ref, None)

    def task_transitioned(self, task: Task) -> None:
        if task.state in {
            TaskState.PLANNED,
            TaskState.EXECUTING,
            TaskState.AWAITING_RESULT,
            TaskState.RESULT_RECEIVED,
            TaskState.VERIFYING,
        }:
            return
        for ref, row in list(self.inputs.items()):
            if row.get("effect_task") == task.id:
                self.h.connectors.release_request(ref)
                self.inputs.pop(ref, None)

    def sanitize(self, text: str, task_id: str, pins: list[dict[str, Any]]) -> str:
        """Run before model Result persistence; no raw tool arguments enter the ledger."""
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

        self.reap()
        if len(text.encode()) > 32768:
            raise ValueError("bounded connector plan required")
        document = json.loads(text)
        if not isinstance(document, dict | list):
            raise ValueError("typed connector plan required")
        if isinstance(document, dict) and set(document) not in (
            {"steps"},
            {"steps", "observe"},
            {"clarification"},
        ):
            raise ValueError("exact connector plan envelope required")
        steps = document if isinstance(document, list) else document.get("steps", [])
        if not isinstance(steps, list) or len(steps) > 16:
            raise ValueError("bounded connector plan required")
        staged = []
        try:
            for step in steps:
                if not isinstance(step, dict) or not isinstance(step.get("intent"), dict):
                    raise ValueError("typed connector step required")
                if set(step) - {"inputs"} != {
                    "id",
                    "intent",
                    "node_id",
                    "capability_id",
                    "depends_on",
                }:
                    raise ValueError("exact connector step required")
                selected = next(
                    (p for p in pins if p["capability_id"] == step["capability_id"]), None
                )
                if selected is None:
                    if ":" in step["capability_id"] or "arguments" in (
                        step["intent"].get("parameters") or {}
                    ):
                        raise PermissionError("unselected connector plan")
                    continue
                if step["node_id"] != selected["node_id"] or step.get("inputs"):
                    raise PermissionError("exact connector executor and literal arguments required")
                current = self.current(selected)
                intent = step["intent"]
                params = intent["parameters"]
                if (
                    not isinstance(params, dict)
                    or set(params) != {"arguments"}
                    or not isinstance(params["arguments"], dict)
                    or intent.get("kind") != "capability"
                    or intent.get("capability_kind") != step["capability_id"]
                    or intent.get("path") is not None
                    or intent.get("content") is not None
                    or intent.get("criterion") not in (None, {"kind": "unavailable"})
                    or isinstance(document, dict)
                    and document.get("observe")
                ):
                    raise ValueError("exact MCP argument plan required")
                if not Draft202012Validator(current["schema"]).is_valid(params["arguments"]):
                    raise ValueError("MCP arguments do not match the reviewed schema")
                ref = self.h.connectors.stage(
                    {"path": {"name": current["tool"]}, "body": params["arguments"]}
                )
                staged.append(ref)
                self.inputs[ref] = {
                    "planner_task": task_id,
                    "pin": selected,
                    "expires": self.h.grid.clock() + 120,
                    "input_digest": digest(self.h.connectors.requests[ref]),
                }

                def guard(reference: str = ref) -> None:
                    self.check(reference)

                self.h.connectors.request_guards[ref] = guard
                account = current["instance"]
                step["intent"] = asdict(
                    Intent(
                        "Invoke selected MCP tool",
                        "capability",
                        capability_kind=step["capability_id"],
                        parameters={"request_ref": ref},
                        criterion={
                            "kind": "unavailable",
                            "connector_account": {
                                "id": account["account_id"],
                                "generation": account["account_generation"],
                            },
                        },
                    )
                )
            return json.dumps(document, allow_nan=False)
        except Exception:
            for ref in staged:
                self.h.connectors.release_request(ref)
                self.inputs.pop(ref, None)
            raise

    def check(self, ref: str) -> dict[str, Any]:
        row = self.inputs.get(ref)
        if row is None or row["expires"] <= self.h.grid.clock():
            raise PermissionError("private connector plan expired; request a new draft")
        if ref in self.h.connectors.request_owners:
            row["effect_task"] = self.h.connectors.request_owners[ref]
        if (
            ref in self.h.connectors.requests
            and digest(self.h.connectors.requests[ref]) != row["input_digest"]
        ):
            raise PermissionError("private connector arguments changed")
        return self.current(row["pin"])

    def review(self, steps: list[dict[str, Any]], planner_task: str) -> list[dict[str, Any]]:
        self.reap()
        reviews = []
        for step in steps:
            params = step["intent"].get("parameters") or {}
            ref = params.get("request_ref")
            if ref is None:
                continue
            current = self.check(ref)
            row = self.inputs[ref]
            if (
                row["planner_task"] != planner_task
                or row["pin"]["node_id"] != step["node_id"]
                or row["pin"]["capability_id"] != step["capability_id"]
                or ref in self.h.connectors.request_owners
            ):
                raise PermissionError("connector plan belongs to another task or executor")
            reviews.append(
                {
                    "node_id": step["node_id"],
                    "capability_id": step["capability_id"],
                    "account_id": current["instance"]["account_id"],
                    "arguments": self.h.connectors.requests[ref]["body"],
                }
            )
        return reviews

    def task_review(self, task_id: str, grants: frozenset[str]) -> dict[str, Any]:
        """Expose exact private inputs only through the signed native review channel."""
        self.reap()
        binding = self.h.store.get("plan", task_id)["executive"]
        goal = self.h.executive._row("executive_goal", binding["goal_id"])
        owner = self.h.store.get("executive_owner", goal["id"])
        if (
            self.h.store.task(task_id).state != TaskState.PLANNED
            or goal["state"] != "enabled"
            or owner.get("standing")
            or binding["review_digest"] != goal["review_digest"]
            or self.h.executive._review(goal) != goal["review_digest"]
        ):
            raise PermissionError("current Ask action required")
        step = next(s for s in goal["steps"] if s["id"] == binding["step_id"])
        ref = step["intent"]["parameters"]["request_ref"]
        current = self.check(ref)
        if (
            self.h.connectors.request_owners.get(ref) != task_id
            or current["capability"]["id"] != binding["capability_id"]
            or current["capability"]["node_id"] != binding["node_id"]
            or not set(current["capability"]["permissions"]) <= grants
        ):
            raise PermissionError("current private action and owner scope required")
        review = self.h.executive.review_task(task_id)
        try:
            confirmation = self.h.store.get("executive_confirmation", task_id)
        except KeyError:
            confirmation = None
        if (
            confirmation
            and confirmation["digest"] == review["digest"]
            and confirmation["expires_at"] > self.h.grid.clock()
        ):
            raise PermissionError("action already approved")
        return {
            "goal_id": goal["id"],
            "task_review": review,
            "connector_inputs": [
                {
                    "node_id": binding["node_id"],
                    "capability_id": binding["capability_id"],
                    "account_id": current["instance"]["account_id"],
                    "arguments": self.h.connectors.requests[ref]["body"],
                }
            ],
        }

    def pending(self, grants: frozenset[str]) -> list[dict[str, str]]:
        result = []
        for ref in list(self.inputs):
            task_id = self.h.connectors.request_owners.get(ref)
            if task_id is None:
                continue
            try:
                review = self.task_review(task_id, grants)
            except (KeyError, ValueError, StopIteration, PermissionError):
                continue
            result.append({"task_id": task_id, "goal_id": review["goal_id"]})
            if len(result) == 16:
                break
        return result
