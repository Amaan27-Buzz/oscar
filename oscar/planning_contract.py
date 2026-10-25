"""Decoding shape only; Executive validation and native authority remain mandatory."""

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


def executive_plan_schema(*, observation_only: tuple[str, ...] = ()) -> dict[str, Any]:
    intent = {
        # Ollama rejects the 4096-repeat grammar; Executive enforces that text bound.
        "text": {"type": "string", "minLength": 1},
        **{
            key: {"type": ["string", "null"]}
            for key in ("kind", "path", "content", "capability_kind")
        },
        **{key: {"type": ["object", "null"]} for key in ("parameters", "criterion")},
    }
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
                            "required": [key for key in step if key != "inputs"],
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
            variant = deepcopy(plan["properties"]["steps"]["items"])
            fields = variant["properties"]
            fields["capability_id"] = {"const": capability}
            fields["depends_on"] = {"type": "array", "maxItems": 0}
            fields["inputs"] = {"type": "array", "maxItems": 0}
            values = fields["intent"]["properties"]
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
            elif capability not in OBSERVATION_KINDS:
                properties = {"arguments": {"type": "object"}}
                required = ["arguments"]
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
    return schema
