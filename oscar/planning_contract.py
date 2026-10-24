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
    }
    return {
        "oneOf": [
            {
                "type": "object",
                "properties": {
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
                    }
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
