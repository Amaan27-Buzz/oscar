"""Decoding shape only; Executive validation and native authority remain mandatory."""

import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

OBSERVATION_KINDS = {
    "machine.files.read": "file_read",
    "machine.files.list": "directory_list",
    "machine.files.search": "file_search",
    "machine.apps": "installed_app",
    "machine.controls": "desktop_inspection",
    "machine.browser": "browser",
    "machine.screen": "screen_capture",
}


def exact_account_aliases(goal: str) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    # shortcut: explicit provider/account-alias clauses only, extend with typed objectives.
    pattern = r'"(?:\\.|[^"\\])*"|\b(?P<provider>google|microsoft)\s+account\s+alias\s*'
    for match in re.finditer(pattern, goal, re.I):
        provider = match.group("provider")
        if provider is None:
            continue
        try:
            alias, _ = json.JSONDecoder().raw_decode(goal[match.end() :])
        except ValueError as exc:
            raise ValueError("account alias requires a JSON-quoted literal") from exc
        if not isinstance(alias, str) or not alias.strip() or len(alias) > 500:
            raise ValueError("bounded account alias required")
        aliases.setdefault(provider.casefold(), set()).add(alias)
    return aliases


def owner_account_bindings(goal: str) -> list[dict[str, Any]]:
    """Ground explicitly named account roles in owner text, never in a model draft.

    Directional clauses are unambiguous only when attached to an exact quoted
    account alias. Other natural-language roles need owner clarification, not a
    guess from whichever capability the model selected.
    """
    pattern = r'"(?:\\.|[^"\\])*"|\b(?P<provider>google|microsoft)\s+account\s+alias\s*'
    mentions = []
    for match in re.finditer(pattern, goal, re.I):
        if match.group("provider") is None:
            continue
        try:
            alias, consumed = json.JSONDecoder().raw_decode(goal[match.end() :])
        except ValueError as exc:
            raise ValueError("account alias requires a JSON-quoted literal") from exc
        if not isinstance(alias, str) or not alias.strip() or len(alias) > 500:
            raise ValueError("bounded account alias required")
        mentions.append(
            (
                match.start(),
                match.end() + consumed,
                match.group("provider").casefold(),
                alias,
            )
        )
    bindings: list[dict[str, Any]] = []
    for index, (start, end, provider, alias) in enumerate(mentions):
        previous = mentions[index - 1][1] if index else 0
        following = mentions[index + 1][0] if index + 1 < len(mentions) else len(goal)
        # A cue must occur after the preceding account reference. Do not
        # classify a second account from a verb attached to the first one.
        cues = list(
            re.finditer(
                r"\b(from|source|origin|to|into|destination|target)\b",
                goal[previous:start],
                re.I,
            )
        )
        role = None
        if cues and len(goal[previous:start]) - cues[-1].end() <= 100:
            role = (
                "source"
                if cues[-1].group(1).casefold() in {"from", "source", "origin"}
                else "destination"
            )
        # Only explicit identifiers are constraints; free prose cannot be
        # silently turned into a provider-specific list or folder identifier.
        resources = re.findall(
            r"\b(?:list|folder|calendar|board|resource|project|tasklist)\s+"
            r"(?:id|identifier)\s*(?::|=)?\s*(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9_-]+))",
            goal[end:following],
            re.I,
        )
        bindings.append(
            {
                "provider": provider,
                "alias": alias,
                "role": role,
                "resources": tuple(next(v for v in match if v) for match in resources),
            }
        )
    return bindings


def resolved_owner_account_bindings(goal: str, accounts: list[Any]) -> list[dict[str, Any]]:
    """Resolve owner-named service roles against verified registry identities.

    Service names identify a provider, never a credential. An alias-free service
    reference is admissible only when exactly one connected owner account has
    that provider. Multiple accounts require clarification; the model's selected
    capability cannot break the tie. Explicit quoted roles keep their existing
    strict syntax and resource-ID constraints.
    """
    explicit = owner_account_bindings(goal)
    if explicit:
        for binding in explicit:
            candidates = [
                a
                for a in accounts
                if a.status == "connected"
                and a.services
                and a.provider == binding["provider"]
                and a.alias == binding["alias"]
            ]
            if len(candidates) != 1:
                raise ValueError("Clarify an unavailable or ambiguous account alias.")
            binding["account_id"] = candidates[0].id
            binding["generation"] = candidates[0].generation
        return explicit

    connected = [
        a
        for a in accounts
        if a.status == "connected"
        and a.services
        and a.identity_class == "owner-delegated"
    ]
    references: list[tuple[int, int, str]] = []
    for provider in sorted({a.provider for a in connected}, key=len, reverse=True):
        if provider == "mcp-resource":
            continue
        for mention in re.finditer(
            r"(?<!\w)" + re.escape(provider) + r"(?!\w)", goal, re.I
        ):
            if any(mention.start() < end and mention.end() > start for start, end, _ in references):
                continue
            references.append((mention.start(), mention.end(), provider))
    references.sort()
    bindings: list[dict[str, Any]] = []
    for index, (start, end, provider) in enumerate(references):
        previous = references[index - 1][1] if index else 0
        cues = list(
            re.finditer(
                r"\b(from|source|origin|to|into|destination|target)\b",
                goal[previous:start],
                re.I,
            )
        )
        role = None
        if cues and start - previous - cues[-1].end() <= 100:
            role = (
                "source"
                if cues[-1].group(1).casefold() in {"from", "source", "origin"}
                else "destination"
            )
        matches = [a for a in connected if a.provider == provider]
        if len(matches) != 1:
            raise ValueError(
                "Clarify the exact account alias for each named service; "
                "multiple verified accounts match."
            )
        account = matches[0]
        bindings.append(
            {
                "provider": provider,
                "alias": account.alias,
                "account_id": account.id,
                "generation": account.generation,
                "role": role,
                "resources": (),
            }
        )
    if len(bindings) > 1 and (
        any(b["role"] is None for b in bindings)
        or len({b["role"] for b in bindings}) == 1
    ):
        raise ValueError("Clarify source and destination account roles.")
    if len({b["account_id"] for b in bindings}) != len(bindings):
        raise ValueError("Clarify repeated account references.")
    return bindings


@dataclass(frozen=True)
class OwnerAccountRole:
    account_id: str
    generation: int
    provider: str
    alias: str
    role: str
    resource_ids: tuple[str, ...]


@dataclass(frozen=True)
class OwnerObjectiveContract:
    """Owner-sourced objective; never replaced by model-generated plan text."""

    objective: str
    accounts: tuple[OwnerAccountRole, ...]
    operation: str
    required_fields: tuple[str, ...]
    completion_rule: str = "independent_source_and_destination_evidence"


def owner_objective_contract(goal: str, accounts: list[Any]) -> dict[str, Any] | None:
    """Capture actionable cross-account invariants before the model drafts effects.

    This is a conservative contract, not a claim of natural-language completeness.
    Unknown field/resource semantics must not be reported as verified.
    """
    roles = resolved_owner_account_bindings(goal, accounts)
    if not roles:
        return None
    transfer = re.search(
        r"\b(copy|duplicate|replicate|transfer|migrate|sync)\b|"
        r"\bcreate\s+equivalent\b",
        goal,
        re.I,
    )
    if not transfer:
        return None
    sources = [r for r in roles if r["role"] == "source"]
    destinations = [r for r in roles if r["role"] == "destination"]
    if len(sources) != 1 or len(destinations) != 1:
        raise ValueError("Clarify one source and one destination account for transfer.")
    if sources[0]["account_id"] == destinations[0]["account_id"]:
        raise ValueError("Clarify distinct source and destination accounts.")
    fields = tuple(
        field
        for field, pattern in (
            ("due", r"\b(due\s+dates?|deadlines?)\b"),
            ("title", r"\b(titles?|names?)\b"),
            ("notes", r"\b(notes?|descriptions?)\b"),
            ("status", r"\b(status|completion\s+state)\b"),
        )
        if re.search(pattern, goal, re.I)
    )
    return asdict(
        OwnerObjectiveContract(
            objective=goal,
            accounts=tuple(
                OwnerAccountRole(
                    account_id=role["account_id"],
                    generation=role["generation"],
                    provider=role["provider"],
                    alias=role["alias"],
                    role=role["role"],
                    resource_ids=tuple(role["resources"]),
                )
                for role in (sources[0], destinations[0])
            ),
            operation="copy",
            required_fields=fields,
        )
    )


def exact_file_literal(goal: str) -> str | None:
    pattern = r"\bexact\s+(?:text|content)\s*(?::|=)?\s*"
    marker = re.search(pattern, goal, re.I)
    if marker is None:
        return None
    # shortcut: explicit JSON-quoted literals only, extend with typed owner objectives.
    try:
        literal, consumed = json.JSONDecoder().raw_decode(goal[marker.end() :])
    except ValueError as exc:
        raise ValueError("exact file text requires a JSON-quoted literal") from exc
    if not isinstance(literal, str):
        raise ValueError("exact file text requires a JSON-quoted literal")
    if re.search(pattern, goal[marker.end() + consumed :], re.I):
        raise ValueError("one unambiguous exact file literal required")
    return literal


def executive_plan_schema(
    *,
    observation_only: tuple[str, ...] = (),
    goal: str = "",
    connector_schemas: dict[str, dict[str, Any]] | None = None,
    native_capabilities: tuple[str, ...] | None = None,
    native_kinds: dict[str, str] | None = None,
) -> dict[str, Any]:
    intent: dict[str, Any] = {
        # Ollama rejects the 4096-repeat grammar; Executive enforces that text bound.
        "text": {"type": "string", "minLength": 1},
        **{
            key: {"type": ["string", "null"]}
            for key in ("kind", "path", "content", "capability_kind")
        },
        **{key: {"type": ["object", "null"]} for key in ("parameters", "criterion")},
    }
    try:
        literal = exact_file_literal(goal)
    except ValueError:
        literal = None
    if literal is not None:
        intent["content"] = {"enum": [None, literal]}
    step = {
        "id": {"type": "string", "pattern": "^[a-z0-9_-]{1,40}$"},
        "intent": {
            "type": "object",
            "properties": intent,
            "required": list(intent),
            "additionalProperties": False,
        },
        "depends_on": {
            "type": "array",
            "items": {"type": "string", "pattern": "^[a-z0-9_-]{1,40}$"},
            "maxItems": 15,
        },
        "node_id": {"type": "string", "minLength": 1},
        "capability_id": {"type": "string", "minLength": 1},
        "inputs": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "from_step": {"type": "string", "pattern": "^[a-z0-9_-]{1,40}$"},
                    **{
                        key: {
                            "type": "array",
                            "maxItems": 8,
                            "items": {
                                "anyOf": [
                                    {"type": "string", "minLength": 1, "maxLength": 80},
                                    {"type": "integer", "minimum": 0, "maximum": 99},
                                ]
                            },
                        }
                        for key in ("select", "to")
                    },
                },
                "required": ["from_step", "select", "to"],
                "additionalProperties": False,
            },
        },
    }
    # Select the executor before decoding its intent, as with a tool name before arguments.
    step = {
        k: step[k] for k in ("id", "capability_id", "node_id", "intent", "depends_on", "inputs")
    }
    schema: dict[str, Any] = {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "observe": {"type": "boolean"},
                    "steps": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 16,
                        "items": {
                            "type": "object",
                            "properties": step,
                            "required": list(step),
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["steps"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "clarification": {"type": "string", "minLength": 1, "maxLength": 480}
                },
                "required": ["clarification"],
                "additionalProperties": False,
            },
        ]
    }
    if observation_only:
        plan = schema["oneOf"][0]
        plan["required"] = ["steps", "observe"]
        plan["properties"]["observe"] = {"const": True}
        plan["properties"]["steps"]["maxItems"] = 1
        variants = []
        for capability in observation_only:
            if capability not in OBSERVATION_KINDS:
                continue
            variant = deepcopy(plan["properties"]["steps"]["items"])
            fields = variant["properties"]
            fields["capability_id"] = {"const": capability}
            fields["depends_on"] = {"type": "array", "maxItems": 0}
            fields["inputs"] = {"type": "array", "maxItems": 0}
            values: dict[str, Any] = fields["intent"]["properties"]
            values["kind"] = {"const": "capability"}
            values["capability_kind"] = {"const": OBSERVATION_KINDS.get(capability, capability)}
            values["path"] = values["content"] = {"type": "null"}
            properties: dict[str, Any]
            if capability in {
                "machine.apps",
                "machine.controls",
                "machine.browser",
                "machine.screen",
            }:
                request: dict[str, Any] = {
                    "operation": {
                        "const": "targets" if capability == "machine.apps" else "inspect_controls"
                    },
                    "query": {"type": "string", "maxLength": 80},
                }
                if capability in {"machine.controls", "machine.screen"}:
                    request.update(
                        handle={"type": "integer", "minimum": 1},
                        pid={"type": "integer", "minimum": 1},
                    )
                if capability == "machine.screen":
                    request.pop("query")
                    request.update(operation={"const": "screenshot"}, path={"type": "string"})
                properties = {
                    "request": {
                        "type": "object",
                        "properties": request,
                        "required": list(request),
                        "additionalProperties": False,
                    }
                }
                if capability == "machine.browser":
                    # Native static-observation validation owns browser URL/step semantics.
                    properties = {
                        "request": {
                            "type": "object",
                            "properties": {"read_only": {"const": True}},
                            "required": ["read_only"],
                        }
                    }
                required = ["request"]
            else:
                properties = {
                    key: {"type": "string"}
                    for key in (
                        ("path",) if capability == "machine.files.read" else ("cwd", "pattern")
                    )
                }
                required = (
                    ["path"]
                    if capability == "machine.files.read"
                    else (["pattern"] if capability == "machine.files.search" else [])
                )
            values["parameters"] = {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            }
            variants.append(variant)
        plan["properties"]["steps"]["items"] = {"oneOf": variants}
    if not observation_only and native_kinds:
        variants = []
        for capability in native_capabilities or ():
            variant = deepcopy(schema["oneOf"][0]["properties"]["steps"]["items"])
            fields = variant["properties"]
            fields["capability_id"] = {"const": capability}
            values = fields["intent"]["properties"]
            kind = native_kinds.get(capability)
            if kind == "file_write":
                values["kind"] = {"const": "file_write"}
                values["path"] = {"type": "string", "minLength": 1}
                values["content"] = (
                    {"enum": ["", literal]} if literal is not None else {"type": "string"}
                )
                for key in ("capability_kind", "parameters", "criterion"):
                    values[key] = {"type": "null"}
            elif kind == "addition":
                values["text"] = {"type": "string", "pattern": r"^[0-9]{1,12} *\+ *[0-9]{1,12}$"}
                for key in values.keys() - {"text"}:
                    values[key] = {"type": "null"}
            variants.append(variant)
        schema["oneOf"][0]["properties"]["steps"]["items"] = {"oneOf": variants}
    connectors = (
        [c for c in observation_only if c not in OBSERVATION_KINDS]
        if observation_only
        else list(connector_schemas or {})
    )
    if connectors:
        plan = schema["oneOf"][0]
        schemas = list((connector_schemas or {}).values())
        unique = [s for i, s in enumerate(schemas) if s not in schemas[:i]]
        if unique:
            # Nested schema resources vary by decoder; native MCP validation stays exact.
            schema["$defs"] = {
                "a" + str(i): (
                    {"type": "object"}
                    if any(
                        key in json.dumps(s)
                        for key in ('"$ref"', '"$dynamicRef"', '"$recursiveRef"')
                    )
                    else s
                )
                for i, s in enumerate(unique)
            }
        if observation_only:
            variants = plan["properties"]["steps"]["items"]["oneOf"]
        else:
            native = plan["properties"]["steps"]["items"]
            if native_capabilities is not None and not native_kinds:
                native["properties"]["capability_id"] = {"enum": list(native_capabilities)}
            variants = []
        for capability in connectors:
            fields = {
                "id": step["id"],
                "capability_id": {"const": capability},
                "arguments": (
                    {"$ref": "#/$defs/a" + str(unique.index(connector_schemas[capability]))}
                    if connector_schemas and capability in connector_schemas
                    else {"type": "object"}
                ),
            }
            if not observation_only:
                fields["depends_on"] = step["depends_on"]
            variants.append(
                {
                    "type": "object",
                    "properties": fields,
                    "required": list(fields),
                    "additionalProperties": False,
                }
            )
        if not observation_only and native_capabilities != ():
            variants.extend(native.get("oneOf", [native]))
        plan["properties"]["steps"]["items"] = {"oneOf": variants}
    return schema
