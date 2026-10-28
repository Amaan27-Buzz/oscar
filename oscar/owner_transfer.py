"""Bounded, private field-equivalence checks for independently observed task transfers.

This is a semantic adapter for task capabilities, not a replacement for provider
authority, signed reviews or final independent destination readback.
"""

import json
from collections import Counter
from typing import Any

from .communication import task_expectation
from .executive import digest


def _canonical(name: str, item: dict[str, Any]) -> dict[str, Any]:
    if "status" not in item:
        raise PermissionError("source task status was not independently observed")
    if item.get("deleted") is True or item.get("hidden") is True:
        raise PermissionError("deleted or hidden source task cannot be copied")
    if name == "google.tasks.list":
        keys = ("title", "notes", "due", "status")
        operation = "google.tasks.create"
    elif name == "microsoft.todo.tasks.list":
        keys = ("title", "body", "dueDateTime", "status")
        operation = "microsoft.todo.tasks.create"
    else:
        raise PermissionError("no reviewed source-to-destination task adapter")
    body = {key: item[key] for key in keys if key in item}
    expected = task_expectation(operation, {"path": {}, "body": body})
    if expected is None:
        raise PermissionError("source fields cannot be preserved by task adapter")
    return expected


def source_task_records(operation: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Reject pagination/truncation and unknown task shapes rather than guess coverage."""
    if not isinstance(payload, dict) or payload.get("nextPageToken") or payload.get(
        "@odata.nextLink"
    ):
        raise PermissionError("complete source task page required")
    key = {
        "google.tasks.list": "items",
        "microsoft.todo.tasks.list": "value",
    }.get(operation)
    if key is None:
        raise PermissionError("unsupported task source operation")
    items = payload.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= 16 or any(
        not isinstance(item, dict) for item in items
    ):
        raise PermissionError("one to sixteen complete typed source tasks required")
    return [_canonical(operation, item) for item in items]


def source_task_digest(operation: str, payload: dict[str, Any]) -> str:
    """Canonical bounded source snapshot, excluding provider metadata."""
    records = source_task_records(operation, payload)
    serialized = [
        json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records
    ]
    return digest(sorted(serialized))


def source_transfer_proof(
    observations_text: str,
    source_account_id: str,
    destination_effects: list[dict[str, Any]],
    *,
    required_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Match every model-selected destination mutation to verified source fields.

    Observation text is returned by planner_observations.context, which already
    revalidates evidence pins, account permissions, session and provenance.
    No private titles, notes or due dates are persisted in the returned proof.
    """
    if set(required_fields) - {"title", "notes", "due"}:
        raise PermissionError("requested task fields need an explicit preserving adapter")
    try:
        observations = json.loads(observations_text)
        source = [
            row
            for row in observations
            if row.get("account_id") == source_account_id
            and row.get("capability_id", "").split(":", 1)[-1]
            in {"google.tasks.list", "microsoft.todo.tasks.list"}
        ]
        if len(source) != 1:
            raise PermissionError("one unambiguous verified task source required")
        observed = source[0]
        operation = observed["capability_id"].split(":", 1)[-1]
        source_records = source_task_records(operation, json.loads(observed["value"]))
        normalized_effects = []
        for effect in destination_effects:
            expected = task_expectation(effect["operation"], effect["arguments"])
            if expected is None or not effect["operation"].endswith(".create"):
                raise PermissionError("destination task effect cannot preserve source fields")
            normalized_effects.append(expected)

        def serialize(value: dict[str, Any]) -> str:
            return json.dumps(value, sort_keys=True, separators=(",", ":"))

        if Counter(map(serialize, source_records)) != Counter(
            map(serialize, normalized_effects)
        ):
            raise PermissionError("destination task fields differ from source observations")
        return {
            "kind": "source_task_field_equivalence",
            "source_account_id": source_account_id,
            "source_task_id": observed["task_id"],
            "source_evidence_id": observed["evidence_id"],
            "source_operation": operation,
            "source_digest": digest(sorted(map(serialize, source_records))),
            "destination_step_ids": [effect["step_id"] for effect in destination_effects],
            "expected_field_digests": [digest(row) for row in normalized_effects],
            "count": len(source_records),
        }
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise PermissionError("typed source observation or task field missing") from exc
