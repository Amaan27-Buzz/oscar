"""Decoding shape only; Executive validation and native authority remain mandatory."""

from typing import Any


def executive_plan_schema() -> dict[str, Any]:
    intent = {
        "text": {"type": "string", "minLength": 1, "maxLength": 4096},
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
    return {
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
