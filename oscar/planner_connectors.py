"""Private, expiring connector arguments behind reviewed Executive plan references."""

import json
import re
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from .capabilities import Cancellation, Cancelled
from .connectors import (
    AuthType,
    ConnectionState,
    ConnectorCapability,
    ConnectorError,
    ConnectorOutcome,
    endpoint,
)
from .contracts import Epistemic, Evidence, Objective, Result, Task, TaskState, Verification, new_id
from .executive import digest
from .jev import Intent

if TYPE_CHECKING:
    from .harness import Harness


class ConnectorPlanning:
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
        instance_id, name = cap["id"].split(":", 1)
        instance = self.h.connectors.instances[instance_id]
        spec = next(s for s in instance.manifest.capabilities if s.name == name)
        if (
            self.h.connectors.state(instance, spec) != ConnectionState.READY
            or instance.account_id is None
            or instance.account_generation is None
        ):
            raise PermissionError("current account-bound connector required")
        if instance.manifest.auth == AuthType.MCP:
            from .connector_providers import mcp_capability_name
            from .mcp_client import schema_digest

            client = self.h.plugins.sessions[instance_id]
            tool = next(t for t in client.tools if mcp_capability_name(t["name"]) == name)
            if self.h.store.get("mcp_installation", instance_id)["schemas"].get(
                tool["name"]
            ) != schema_digest(tool["inputSchema"]):
                raise PermissionError("MCP schema needs installation review")
            operation, schema = tool["name"], tool["inputSchema"]
        else:
            if instance_id not in self.h._account_instances:
                raise PermissionError("current native account projection required")
            operation, schema = spec.name, self.http_schema(spec)
        return {
            "capability": cap,
            "instance": {**asdict(instance), "granted_scopes": sorted(instance.granted_scopes)},
            "operation": operation,
            "schema": schema,
            "risk": spec.risk.value,
            "transport": "mcp" if instance.manifest.auth == AuthType.MCP else "https",
            "endpoint": {
                "method": spec.method,
                "origin": instance.manifest.base_url,
                "path": spec.path,
            },
        }

    @staticmethod
    def http_schema(spec: ConnectorCapability) -> dict[str, Any]:
        paths = re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", spec.path)
        properties: dict[str, Any] = {
            "path": {
                "type": "object",
                "properties": {
                    p: {"type": "string", "minLength": 1, "maxLength": 500} for p in paths
                },
                "required": paths,
                "additionalProperties": False,
            },
            "query": {
                "type": "object",
                "properties": {
                    q: {"type": ["string", "integer", "boolean"]} for q in spec.query_fields
                },
                "additionalProperties": False,
            },
        }
        conditional = spec.name in {
            "google.calendar.events.update",
            "google.calendar.events.delete",
        }
        if conditional:
            properties["if_match"] = {
                "type": "string",
                "minLength": 3,
                "maxLength": 256,
                "description": (
                    "Copy the exact strong etag from the current selected event observation; "
                    "never guess. A changed version requires a fresh reviewed action."
                ),
            }
        if spec.body_required:
            properties["body"] = {"type": "object"}
            if spec.name == "microsoft.todo.tasks.create":
                properties["body"]["description"] = (
                    "Task fields: title, body object with contentType and content for "
                    "literal notes, "
                    "dueDateTime object with dateTime at UTC midnight and timeZone UTC, "
                    "status notStarted. Omit dueDateTime when no date was requested; "
                    "do not use null."
                )
                properties["body"]["properties"] = {
                    "title": {"type": "string"},
                    "status": {"type": "string"},
                    "body": {
                        "type": "object",
                        "properties": {
                            "contentType": {"enum": ["text", "html"]},
                            "content": {"type": "string"},
                        },
                        "required": ["contentType", "content"],
                    },
                    "dueDateTime": {
                        "type": "object",
                        "properties": {
                            "dateTime": {"type": "string", "minLength": 1},
                            "timeZone": {"type": "string", "minLength": 1},
                        },
                        "required": ["dateTime", "timeZone"],
                    },
                }
            elif spec.name in {"google.tasks.update", "microsoft.todo.tasks.update"}:
                properties["body"]["description"] = (
                    "A status-only body has independent saved-resource verification. "
                    "Other updates retain generic partial verification."
                )
        return {
            "type": "object",
            "properties": properties,
            "required": (["path"] if paths else [])
            + (["body"] if spec.body_required else [])
            + (["if_match"] if conditional else []),
            "additionalProperties": False,
        }

    def descriptor(self, cap: dict[str, Any]) -> dict[str, Any] | None:
        if cap.get("output_kind") != "connector-reference":
            return None
        try:
            current = self.contract(cap)
        except (KeyError, StopIteration, ValueError, PermissionError):
            return None
        instance = current["instance"]
        account = self.h.accounts.get(instance["account_id"])
        return {
            "node_id": cap["node_id"],
            "capability_id": cap["id"],
            "kind": cap["input_kind"],
            "summary": "Current reviewed account-bound connector operation",
            "account_id": instance["account_id"],
            "account": {"alias": account.alias, "provider": account.provider},
            "account_generation": instance["account_generation"],
            "operation": current["operation"],
            "transport": current["transport"],
            "risk": current["risk"],
            "endpoint": current["endpoint"],
            "argument_schema": current["schema"],
            "intent_examples": [
                asdict(
                    Intent(
                        "Invoke selected connector operation",
                        "capability",
                        capability_kind=cap["input_kind"],
                        parameters={"arguments": {}},
                    )
                )
            ],
            "intent_rule": (
                "Return a compact connector step: id, capability_id, arguments matching "
                "argument_schema, and depends_on ([] when independent). No intent/node_id/inputs. "
                "For observe:true omit depends_on and use a single read-only GET. "
                "Use the exact selected account/tool; never invent arguments or references. "
                "No input substitutions or verification claims. Observation stages may use "
                "only native HTTPS GET operations marked read, without a body. "
                "For HTTPS, use exactly argument_schema fields, including if_match when required; "
                "origin, method, headers "
                "and credentials are fixed by Core. Body fields must come from the owner's "
                "explicit request; the endpoint shape is not a provider body-field schema. "
                "Arguments are privately staged for exact review and one immediate execution. "
                "A tool report does not independently verify the objective."
            ),
        }

    def goal_accounts(self, goal: str, caps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        from .planning_contract import resolved_owner_account_bindings

        bindings = resolved_owner_account_bindings(goal, self.h.accounts.list_accounts())
        if not bindings:
            return caps
        allowed = {binding["account_id"] for binding in bindings}
        selected = []
        for cap in caps:
            descriptor = self.descriptor(cap)
            if descriptor is not None:
                if descriptor["account_id"] not in allowed:
                    continue
                instance = self.h.connectors.instances[cap["id"].split(":", 1)[0]]
                account = self.h.accounts.get(descriptor["account_id"])
                current = self.h.accounts.select(
                    account.provider, instance.manifest.id, alias=account.alias
                )
                if current.id != account.id or current.generation != account.generation:
                    raise PermissionError("selected account changed")
            selected.append(cap)
        return selected

    def check_goal_accounts(
        self,
        goal: str,
        steps: list[dict[str, Any]],
        *,
        observe: bool = False,
        source_observations: dict[str, Any] | None = None,
    ) -> None:
        """Admit actual account effects against owner roles, not an account union.

        The model can choose its plan, but it cannot turn a named source into a
        destination, change an explicit resource ID, or supply its own objective.
        A role that owner text does not establish must remain unresolved.
        """
        from .planning_contract import resolved_owner_account_bindings

        caps = [
            next(
                c
                for c in self.h.store.get("node", step["node_id"])["capabilities"]
                if c["id"] == step["capability_id"]
            )
            for step in steps
        ]
        if len(self.goal_accounts(goal, caps)) != len(caps):
            raise PermissionError("plan does not preserve the owner's selected account")
        bindings = resolved_owner_account_bindings(goal, self.h.accounts.list_accounts())
        if not bindings:
            # Do not let an alias-free cross-service goal silently collapse to
            # whichever provider's mutation the model happened to select.
            mentioned = {
                account.provider
                for account in self.h.accounts.list_accounts()
                if re.search(r"\b" + re.escape(account.provider) + r"\b", goal, re.I)
            }
            routed = {
                descriptor["account"]["provider"]
                for cap in caps
                if (descriptor := self.descriptor(cap)) is not None
            }
            if (
                (len(mentioned) > 1 or mentioned - routed)
                and any(
                    not self.is_read(cap) for cap in caps if self.descriptor(cap) is not None
                )
            ):
                raise ValueError(
                    "Clarify exact source and destination account aliases before effects."
                )
            return
        roles = {(b["provider"], b["alias"]): b for b in bindings}
        if len(roles) != len(bindings):
            raise ValueError("Clarify repeated or conflicting account roles.")
        selected: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
        for step, cap in zip(steps, caps):
            descriptor = self.descriptor(cap)
            if descriptor is None:
                continue
            binding = roles.get(
                (descriptor["account"]["provider"], descriptor["account"]["alias"])
            )
            if (
                binding is None
                or descriptor["account_id"] != binding["account_id"]
                or descriptor["account_generation"] != binding["generation"]
            ):
                raise PermissionError("plan selects an account absent from the owner goal")
            selected.append((step, cap, binding))

        if len(roles) > 1 and any(b["role"] is None for b in bindings):
            if any(not self.is_read(cap) for _, cap, _ in selected):
                raise ValueError(
                    "Clarify each source and destination account before authorizing effects."
                )
        destination_effects: set[tuple[str, str]] = set()
        source_reads: set[str] = set()
        destination_steps: list[dict[str, Any]] = []
        for step, cap, binding in selected:
            current = self.contract(cap)
            method = current["endpoint"]["method"].upper()
            if current["transport"] != "https" and binding["role"] is not None:
                raise PermissionError("typed source/destination roles require a reviewed endpoint")
            if binding["role"] == "source" and method != "GET":
                raise PermissionError("owner source account cannot receive a proposed effect")
            if binding["role"] == "source" and method == "GET":
                source_reads.add(step["id"])
            if binding["role"] == "destination" and method != "GET":
                destination_steps.append(step)
                if re.search(
                    r"\b(copy|duplicate|replicate|transfer|migrate|sync)\b|"
                    r"\bcreate\s+equivalent\b",
                    goal,
                    re.I,
                ) and (method != "POST" or current["operation"].rsplit(".", 1)[-1] != "create"):
                    raise PermissionError(
                        "owner requested a copy; destination operation must create"
                    )
                destination_effects.add((binding["provider"], binding["alias"]))
            if binding["resources"]:
                parameters = step["intent"].get("parameters") or {}
                arguments = parameters.get("arguments")
                if arguments is None and "request_ref" in parameters:
                    ref = parameters["request_ref"]
                    if ref not in self.inputs:
                        raise PermissionError("private resource binding unavailable")
                    arguments = self.arguments(ref, self.check(ref))
                paths = arguments.get("path", {}) if isinstance(arguments, dict) else {}
                if not isinstance(paths, dict) or (
                    (method != "GET" or paths)
                    and not all(resource in paths.values() for resource in binding["resources"])
                ):
                    raise PermissionError("plan does not preserve the owner's resource ID")

        if not observe and destination_steps and source_reads:
            graph = {step["id"]: set(step["depends_on"]) for step in steps}

            def ancestors(step_id: str) -> set[str]:
                visited: set[str] = set()
                pending = list(graph[step_id])
                while pending:
                    key = pending.pop()
                    if key in visited:
                        continue
                    visited.add(key)
                    pending.extend(graph.get(key, ()))
                return visited

            for step in destination_steps:
                if not ancestors(step["id"]) & source_reads:
                    raise PermissionError(
                        "destination effect must depend on verified source read"
                    )
        elif not observe and destination_steps and any(
            binding["role"] == "source" for binding in bindings
        ):
            if source_observations is None:
                raise PermissionError("source observation required before transfer effects")
            from .planner_observations import context

            context(self.h.store, self.h.grid, source_observations)
            observed_goal = self.h.store.get(
                "executive_goal", source_observations["goal_id"]
            )
            expected_sources = {
                binding["account_id"]
                for binding in bindings
                if binding["role"] == "source"
            }
            read_accounts = {
                criterion["connector_account"]["id"]
                for step in observed_goal["steps"]
                if (criterion := (step["intent"].get("criterion") or {})).get("kind")
                == "connector_observation"
                and isinstance(criterion.get("connector_account"), dict)
                and "id" in criterion["connector_account"]
            }
            if not expected_sources <= read_accounts:
                raise PermissionError("no verified observation of owner's source account")

        if not observe:
            expected = {
                (b["provider"], b["alias"])
                for b in bindings
                if b["role"] == "destination"
            }
            if expected - destination_effects:
                raise PermissionError(
                    "plan does not perform the owner's destination operation"
                )

    def is_read(self, cap: dict[str, Any]) -> bool:
        if self.descriptor(cap) is None:
            return False
        current = self.contract(cap)
        return (
            current["transport"] == "https"
            and current["endpoint"]["method"] == "GET"
            and current["risk"] == "read"
            and list(cap["permissions"]) == ["connectors:read"]
            and "body" not in current["schema"]["properties"]
        )

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
            raise PermissionError("connector planning contract changed")
        return self.contract(cap)

    def reap(self) -> None:
        for ref, row in list(self.inputs.items()):
            if row["expires"] <= self.h.grid.clock() or (
                ref not in self.h.connectors.requests and not row.get("effect_task")
            ):
                self.h.connectors.release_request(ref)
                self.inputs.pop(ref, None)
        for ref, entry in list(self.h.store.transient.items()):
            if ref.startswith(("assistance-review:", "connector-observation:")) and (
                entry["expires"] <= self.h.grid.clock()
            ):
                self.h.store.transient.pop(ref, None)

    def task_transitioned(self, task: Task) -> None:
        if task.state not in {
            TaskState.PLANNED,
            TaskState.EXECUTING,
            TaskState.AWAITING_RESULT,
            TaskState.RESULT_RECEIVED,
            TaskState.VERIFYING,
            TaskState.VERIFIED,
        }:
            self.h.store.transient.pop("connector-observation:" + task.id, None)
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
            for index, step in enumerate(steps):
                if (
                    isinstance(step, dict)
                    and isinstance(document, dict)
                    and (
                        set(step) == {"id", "capability_id", "arguments", "depends_on"}
                        and (document.get("observe") is not True or step["depends_on"] == [])
                        or document.get("observe") is True
                        and set(step) == {"id", "capability_id", "arguments"}
                    )
                ):
                    selected = next(
                        (p for p in pins if p["capability_id"] == step["capability_id"]), None
                    )
                    if selected is None:
                        raise PermissionError("unselected compact connector")
                    current = self.current(selected)
                    if document.get("observe") is True and not self.is_read(current["capability"]):
                        raise PermissionError("compact observations require a native read-only GET")
                    step = {
                        "id": step["id"],
                        "node_id": selected["node_id"],
                        "capability_id": selected["capability_id"],
                        "intent": asdict(
                            Intent(
                                "Invoke selected connector operation",
                                "capability",
                                capability_kind=current["capability"]["input_kind"],
                                parameters={"arguments": step["arguments"]},
                            )
                        ),
                        "depends_on": step.get("depends_on", []),
                        "inputs": [],
                    }
                    steps[index] = step
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
                ):
                    raise ValueError("exact connector argument plan required")
                observe = isinstance(document, dict) and document.get("observe") is True
                read = self.is_read(current["capability"]) and "body" not in params["arguments"]
                if observe and not read:
                    raise PermissionError("connector observations require a native read-only GET")
                if current["transport"] == "mcp":
                    from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

                    if not Draft202012Validator(current["schema"]).is_valid(params["arguments"]):
                        raise ValueError("MCP arguments do not match the reviewed schema")
                    arguments = {
                        "path": {"name": current["operation"]},
                        "body": params["arguments"],
                    }
                else:
                    instance_id, name = step["capability_id"].split(":", 1)
                    spec = next(
                        s
                        for s in self.h.connectors.instances[instance_id].manifest.capabilities
                        if s.name == name
                    )
                    endpoint(spec, params["arguments"])
                    arguments = params["arguments"]
                    if name == "microsoft.todo.tasks.create":
                        fields = current["schema"]["properties"]["body"]["properties"]
                        for field in ("body", "dueDateTime"):
                            if field not in arguments["body"]:
                                continue
                            value, shape = arguments["body"][field], fields[field]
                            if not isinstance(value, dict) or any(
                                not isinstance(value.get(key), str)
                                or len(value[key]) < shape["properties"][key].get("minLength", 0)
                                for key in shape["required"]
                            ):
                                raise ValueError(
                                    "Microsoft task notes and dates require typed objects"
                                )
                            if field == "body" and value["contentType"] not in ("text", "html"):
                                raise ValueError("Microsoft task note type must be text or html")
                from .communication import task_expectation

                mutation = (
                    current["transport"] == "https"
                    and task_expectation(current["operation"], arguments) is not None
                )
                ref = self.h.connectors.stage(arguments)
                staged.append(ref)
                self.inputs[ref] = {
                    "planner_task": task_id,
                    "pin": selected,
                    "expires": self.h.grid.clock() + 120,
                    "input_digest": digest(self.h.connectors.requests[ref]),
                    **({"observation": arguments} if read else {}),
                    **({"verification_arguments": arguments} if mutation else {}),
                }

                def guard(reference: str = ref) -> None:
                    self.check(reference)

                self.h.connectors.request_guards[ref] = guard
                account = current["instance"]
                step["intent"] = asdict(
                    Intent(
                        "Invoke selected connector operation",
                        "capability",
                        capability_kind=step["capability_id"],
                        parameters={"request_ref": ref},
                        criterion={
                            "kind": "connector_observation"
                            if read
                            else "connector_planned_task"
                            if mutation
                            else "unavailable",
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

    def discard_draft(self, task_id: str) -> None:
        for ref, row in list(self.inputs.items()):
            if row["planner_task"] == task_id and not row.get("effect_task"):
                self.h.connectors.release_request(ref)
                self.inputs.pop(ref, None)

    def check(self, ref: str) -> dict[str, Any]:
        row = self.inputs.get(ref)
        if row is None or row["expires"] <= self.h.grid.clock():
            raise PermissionError("private connector plan expired; request a new draft")
        if ref in self.h.connectors.request_owners:
            row["effect_task"] = self.h.connectors.request_owners[ref]
        if (
            ref in self.h.connectors.requests
            and digest(self.h.connectors.requests[ref]) != row["input_digest"]
            or "observation" in row
            and digest(row["observation"]) != row["input_digest"]
            or "verification_arguments" in row
            and digest(row["verification_arguments"]) != row["input_digest"]
        ):
            raise PermissionError("private connector arguments changed")
        return self.current(row["pin"])

    def task_criterion(self, objective: Objective, result: Result) -> dict[str, Any]:
        from .communication import task_expectation
        from .executive import authorize_step

        ref, row = next(
            (ref, row)
            for ref, row in self.inputs.items()
            if row.get("effect_task") == result.task_id and "verification_arguments" in row
        )
        current = self.check(ref)
        cap, instance = current["capability"], current["instance"]
        account = {"id": instance["account_id"], "generation": instance["account_generation"]}
        if (
            objective.criterion.get("connector_account") != account
            or objective.correlation_id != result.correlation_id
            or result.executor != cap["id"]
            or current["transport"] != "https"
        ):
            raise PermissionError("exact private task verification required")
        authorize_step(
            self.h.store,
            self.h.grid,
            result.task_id,
            cap,
            self.h.executive.targets[cap["node_id"]][1],
            self.h.memory,
        )
        binding = self.h.store.get("plan", result.task_id)["executive"]
        owner = self.h.store.get("executive_owner", binding["goal_id"])
        target_session = self.h.executive.targets[cap["node_id"]][1]
        for node_id, session_id in (
            (owner["node"], owner["session"]),
            (cap["node_id"], target_session.id),
        ):
            session = self.h.store.get("session", session_id)
            node = self.h.store.get("node", node_id)
            if "connectors:read" not in set(session["scopes"]) & set(node["scopes"]):
                raise PermissionError("current owner and executor read scope required")
        expected = task_expectation(current["operation"], row["verification_arguments"])
        if expected is None:
            raise PermissionError("private task verification contract unavailable")
        return {
            "kind": "connector_communication",
            "connector_account": account,
            "instance_id": instance["id"],
            "operation": current["operation"],
            "expected": expected,
        }

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
                    "arguments": self.arguments(ref, current),
                }
            )
        return reviews

    def verify_observation(
        self, objective: Objective, result: Result, outcome: ConnectorOutcome | None
    ) -> Verification:
        matches = None
        content_hash = None
        detail = "independent account GET unavailable"
        try:
            from .executive import authorize_step

            ref, row = next(
                (ref, row)
                for ref, row in self.inputs.items()
                if row.get("effect_task") == result.task_id and "observation" in row
            )
            current = self.check(ref)
            cap = current["capability"]
            instance_id, name = cap["id"].split(":", 1)
            instance = self.h.connectors.instances[instance_id]
            spec = next(c for c in instance.manifest.capabilities if c.name == name)
            if (
                not self.is_read(cap)
                or outcome is None
                or not result.success
                or outcome.result != result
                or outcome.executed_instance != instance
                or outcome.instance_id != instance_id
                or outcome.capability_name != name
                or result.executor != cap["id"]
                or objective.correlation_id != result.correlation_id
                or objective.criterion["connector_account"]
                != {
                    "id": instance.account_id,
                    "generation": instance.account_generation,
                }
            ):
                raise PermissionError("exact native account observation required")

            def guard() -> None:
                self.check(ref)
                authorize_step(
                    self.h.store,
                    self.h.grid,
                    result.task_id,
                    cap,
                    self.h.executive.targets[cap["node_id"]][1],
                    self.h.memory,
                )
                for identifier in (name, "connectors:read"):
                    if not self.h.connectors.policy.evaluate(
                        identifier,
                        ("connectors:read",),
                        outcome.granted,
                        outcome.context,
                        confirmed=outcome.confirmed,
                    ).allowed:
                        raise PermissionError("observation readback denied")

            value = json.dumps(outcome.payload, sort_keys=True, allow_nan=False)
            if len(value.encode()) > 4096:
                raise ValueError("bounded provider observation required")
            cancellation = Cancellation(self.h.store, result.task_id, guard)
            cancellation.check()
            payload, _ = self.h.connectors._request(
                instance, spec, row["observation"], cancellation
            )
            cancellation.check()
            matches = digest(payload) == digest(outcome.payload)
            detail = "independent account GET matches" if matches else "provider response changed"
            if matches:
                if len(self.h.store.transient) >= 100:
                    raise ValueError("private observation capacity reached")
                content_hash = digest(payload)
                pin = dict(row["pin"])
                self.h.store.transient["connector-observation:" + result.task_id] = {
                    "value": value,
                    "result_id": result.id,
                    "expires": min(row["expires"], self.h.grid.clock() + spec.freshness_seconds),
                    "guard": lambda: self.current(pin),
                }
        except (KeyError, StopIteration, ValueError, PermissionError, Cancelled, ConnectorError):
            matches = None
        evidence = Evidence(
            new_id(),
            result.task_id,
            result.correlation_id,
            "connector-independent-readback",
            "native account GET response comparison",
            self.h.grid.clock(),
            matches,
            Epistemic.VERIFIED if matches else Epistemic.REPORTED,
            detail,
            content_hash=content_hash,
        )
        return Verification(
            TaskState.VERIFIED
            if matches
            else TaskState.FAILED
            if matches is False
            else TaskState.PARTIALLY_VERIFIED,
            evidence,
        )

    def arguments(self, ref: str, current: dict[str, Any]) -> dict[str, Any]:
        request = self.h.connectors.requests[ref]
        return dict(request["body"] if current["transport"] == "mcp" else request)

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
        if "observation" in self.inputs[ref]:
            from .policy import PersonalPolicy

            cap = current["capability"]
            worker = self.h.store.get("executive_worker", binding["worker_id"])
            decision = PersonalPolicy(self.h.store).evaluate(
                cap["id"],
                tuple(cap["permissions"]),
                frozenset(worker["grants"]),
                {"source": "executive", "node": cap["node_id"]},
                now=self.h.grid.clock(),
            )
            if decision.allowed:
                raise PermissionError("read-only action requires no additional confirmation")
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
                    "arguments": self.arguments(ref, current),
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
