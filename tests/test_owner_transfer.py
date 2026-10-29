"""Semantic comparison unit cases; no real accounts, provider network or model."""

import json
import unittest

from oscar.owner_transfer import source_task_digest, source_task_records, source_transfer_proof


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

    def test_uncompleted_status_semantics_are_preserved_across_providers(self):
        proof = source_transfer_proof(
            self.google_source([self.task()]),
            "source-account",
            [self.microsoft_effect()],
            required_fields=("title", "notes", "due", "status"),
        )
        self.assertEqual(1, proof["count"])

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
                required_fields=("recurrence",),
            )
        modified = {**self.task(), "status": "completed"}
        with self.assertRaisesRegex(PermissionError, "cannot be preserved"):
            source_task_records("google.tasks.list", {"items": [modified]})

    def test_nontrivial_source_fields_do_not_disappear_in_equivalence_proof(self):
        for changes in (
            {"parent": "task-parent"},
            {"links": [{"type": "email", "link": "https://example.invalid"}]},
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(PermissionError, "unsupported semantic fields"):
                    source_task_records(
                        "google.tasks.list", {"items": [{**self.task(), **changes}]}
                    )
        with self.assertRaisesRegex(PermissionError, "unsupported semantic fields"):
            source_task_records(
                "microsoft.todo.tasks.list",
                {
                    "value": [{
                        "title": "Source title",
                        "status": "notStarted",
                        "importance": "high",
                    }],
                },
            )

    def test_microsoft_utc_zero_fraction_due_date_has_equal_semantics(self):
        payload = {
            "value": [{
                "title": "Source title",
                "status": "notStarted",
                "body": {
                    "contentType": "text",
                    "content": "Private source notes",
                },
                "dueDateTime": {
                    "dateTime": "2026-10-28T00:00:00.0000000",
                    "timeZone": "UTC",
                },
            }]
        }
        records = source_task_records("microsoft.todo.tasks.list", payload)
        self.assertEqual("2026-10-28", records[0]["due"])
        payload["value"][0]["dueDateTime"]["dateTime"] = (
            "2026-10-28T00:00:00.0000001"
        )
        with self.assertRaisesRegex(PermissionError, "cannot be preserved"):
            source_task_records("microsoft.todo.tasks.list", payload)

    def test_microsoft_rich_notes_are_not_silently_downgraded(self):
        for notes in (
            {"contentType": "html", "content": "<b>Important</b>"},
            {"contentType": None, "content": "invalid"},
            "not a typed notes body",
        ):
            with self.subTest(notes=notes):
                with self.assertRaisesRegex(PermissionError, "without loss"):
                    source_task_records(
                        "microsoft.todo.tasks.list",
                        {"value": [{
                            "title": "Source title",
                            "status": "notStarted",
                            "body": notes,
                        }]},
                    )

    def test_missing_source_status_is_not_assumed_uncompleted(self):
        item = self.task()
        item.pop("status")
        with self.assertRaisesRegex(PermissionError, "status was not independently observed"):
            source_task_records("google.tasks.list", {"items": [item]})

    def test_unmatched_task_service_cannot_be_used_as_source(self):
        other = json.loads(self.google_source([self.task()]))
        other[0]["capability_id"] = "synthetic:google.calendar.events.list"
        with self.assertRaisesRegex(PermissionError, "unambiguous"):
            source_transfer_proof(
                json.dumps(other), "source-account", [self.microsoft_effect()]
            )

    def test_fresh_source_digest_detects_field_mutation_but_not_response_order(self):
        first = self.task()
        second = {**self.task(), "title": "Second task"}
        baseline = source_task_digest(
            "google.tasks.list", {"items": [first, second]}
        )
        self.assertEqual(
            baseline,
            source_task_digest("google.tasks.list", {"items": [second, first]}),
        )
        self.assertNotEqual(
            baseline,
            source_task_digest(
                "google.tasks.list",
                {"items": [first, {**second, "due": "2026-10-29T00:00:00Z"}]},
            ),
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
