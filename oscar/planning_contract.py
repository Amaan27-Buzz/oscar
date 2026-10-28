"""Decoding shape only; Executive validation and native authority remain mandatory."""

import json
import re
from copy import deepcopy
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
            (match.start(), match.end() + consumed, match.group("provider").casefold(), alias)
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
