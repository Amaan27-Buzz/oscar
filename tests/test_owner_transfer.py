"""Semantic comparison unit cases; no real accounts, provider network or model."""

import json
import unittest

from oscar.owner_transfer import source_task_records, source_transfer_proof


class OwnerTransferEquivalenceTests(unittest.TestCase):
    def google_source(self, tasks, **extra):
        return json.dumps(
            [
                {
                    "account_id": "source-account",
                    "capability_id": "synthetic:google.tasks.list",
                    "task_id": "verified-read",
                    "evidence_id": "independent-evidence",
                    "value": json.dumps({"items": tasks, **extra}),
                }
            ]
        )

    def microsoft_effect(self, title="Source title", notes="Private source notes", due=True):
        body = {
            "title": title,
            "body": {"contentType": "text", "content": notes},
        }
        if due:
            body["dueDateTime"] = {
                "dateTime": "2026-10-28T00:00:00",
                "timeZone": "UTC",
            }
        return {
            "step_id": "create-dest",
            "operation": "microsoft.todo.tasks.create",
            "arguments": {"path": {"listId": "bound-destination"}, "body": body},
        }

    def task(self):
        return {
            "title": "Source title",
            "notes": "Private source notes",
            "due": "2026-10-28T00:00:00Z",
            "status": "needsAction",
        }

    def test_exact_cross_provider_task_fields_have_private_digest_proof(self):
        proof = source_transfer_proof(
            self.google_source([self.task()]),
            "source-account",
            [self.microsoft_effect()],
            required_fields=("title", "notes", "due"),
        )
        self.assertEqual("source_task_field_equivalence", proof["kind"])
        self.assertEqual(1, proof["count"])
        self.assertEqual(["create-dest"], proof["destination_step_ids"])
        self.assertNotIn("Source title", json.dumps(proof))
        self.assertNotIn("Private source notes", json.dumps(proof))

    def test_missing_due_date_is_not_an_equivalent_copy(self):
        with self.assertRaisesRegex(PermissionError, "fields differ"):
            source_transfer_proof(
                self.google_source([self.task()]),
                "source-account",
                [self.microsoft_effect(due=False)],
                required_fields=("due",),
            )

    def test_wrong_title_and_notes_are_rejected(self):
        for effect in (
            self.microsoft_effect(title="Fabricated title"),
            self.microsoft_effect(notes="Wrong notes"),
        ):
            with self.subTest(effect=effect["arguments"]["body"]):
                with self.assertRaisesRegex(PermissionError, "fields differ"):
                    source_transfer_proof(
                        self.google_source([self.task()]),
                        "source-account",
                        [effect],
                    )

    def test_incomplete_or_duplicate_destination_effects_are_rejected(self):
        for effects in ([], [self.microsoft_effect(), self.microsoft_effect()]):
            with self.subTest(count=len(effects)):
                with self.assertRaisesRegex(PermissionError, "fields differ"):
                    source_transfer_proof(
                        self.google_source([self.task()]), "source-account", effects
                    )

    def test_partial_page_and_unverified_source_cannot_prove_complete_copy(self):
        with self.assertRaisesRegex(PermissionError, "complete source task page"):
            source_task_records(
                "google.tasks.list",
                {"items": [self.task()], "nextPageToken": "next-page"},
            )
        with self.assertRaisesRegex(PermissionError, "unambiguous"):
            source_transfer_proof("[]", "source-account", [self.microsoft_effect()])

    def test_unknown_fields_and_unsupported_source_status_fail_closed(self):
        with self.assertRaisesRegex(PermissionError, "preserving adapter"):
            source_transfer_proof(
                self.google_source([self.task()]),
                "source-account",
                [self.microsoft_effect()],
                required_fields=("status",),
            )
        modified = {**self.task(), "status": "completed"}
        with self.assertRaisesRegex(PermissionError, "cannot be preserved"):
            source_task_records("google.tasks.list", {"items": [modified]})

    def test_unmatched_task_service_cannot_be_used_as_source(self):
        other = json.loads(self.google_source([self.task()]))
        other[0]["capability_id"] = "synthetic:google.calendar.events.list"
        with self.assertRaisesRegex(PermissionError, "unambiguous"):
            source_transfer_proof(
                json.dumps(other), "source-account", [self.microsoft_effect()]
            )

    def test_microsoft_to_google_task_transfer_uses_same_canonical_fields(self):
        source = json.dumps(
            [{
                "account_id": "source-account",
                "capability_id": "synthetic:microsoft.todo.tasks.list",
                "task_id": "verified-read",
                "evidence_id": "independent-evidence",
                "value": json.dumps({
                    "value": [{
                        "title": "Source title",
                        "body": {"contentType": "text", "content": "Private source notes"},
                        "dueDateTime": {
                            "dateTime": "2026-10-28T00:00:00",
                            "timeZone": "UTC",
                        },
                        "status": "notStarted",
                    }],
                }),
            }]
        )
        destination = {
            "step_id": "google-copy",
            "operation": "google.tasks.create",
            "arguments": {
                "path": {"tasklist": "bound-destination"},
                "body": self.task(),
            },
        }
        proof = source_transfer_proof(source, "source-account", [destination])
        self.assertEqual(["google-copy"], proof["destination_step_ids"])


if __name__ == "__main__":
    unittest.main()
