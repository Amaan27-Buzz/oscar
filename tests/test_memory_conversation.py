import base64
import json
import unittest
from time import monotonic, sleep, time
from unittest.mock import patch

from oscar.event_archive import MemoryWriter, SourceEvent
from oscar.memory_executor import MemoryExecutor
from tests import test_desktop as desktop_fixture
from tests import test_remote_grid as remote_fixture


def grant(store, session, scope):
    for kind, identity in (("session", session.id), ("node", session.node_id)):
        row = store.get(kind, identity)
        store.put(kind, identity, {**row, "scopes": [*row["scopes"], scope]})


def retain(h):
    event = SourceEvent("owner", "My preferred editor is Copperfin", "synthetic-owner", time() - 10)
    h.archive.append(event, retain_authorized=True)
    memory = MemoryWriter(h.archive).retain(
        (event.id,),
        event.content,
        "preference",
        retain_authorized=True,
        inferred=False,
    )
    return event, memory


class RemoteRecallTests(unittest.TestCase):
    setUp = remote_fixture.RemoteGridTests.setUp
    tearDown = remote_fixture.RemoteGridTests.tearDown
    invitation = remote_fixture.RemoteGridTests.invitation
    enroll = remote_fixture.RemoteGridTests.enroll

    def ask(self):
        return self.mobile.request(
            "submit",
            {
                "text": "Recall my preferred editor",
                "kind": "text",
                "target": self.config.core_id,
                "parameters": {},
                "retain": True,
            },
        )

    def finish(self, view):
        deadline = monotonic() + 5
        while monotonic() < deadline:
            view = self.mobile.request("inspect", {"task_id": view["task_id"]})
            if view["state"] not in {"planned", "executing", "awaiting_result", "verifying"}:
                return view
            sleep(0.02)
        self.fail("bounded recall did not complete")

    def test_plain_conversation_recall_requires_read_grant_and_preserves_source_ids(self):
        h = self.core.harness
        event, memory = retain(h)
        with self.assertRaises(PermissionError):
            self.ask()
        self.assertEqual([], h.store.all("remote_task"))
        grant(h.store, self.mobile.handle, "memory:read")
        view = self.finish(self.ask())
        self.assertEqual(event.content, view["result"]["value"])
        self.assertEqual("RECALLED", view["response_status"])
        self.assertIn(event.id, view["source_event_ids"])
        self.assertEqual("REPORTED", view["result"]["status"])
        self.assertIn(
            memory.id,
            next(r for r in h.store.ledger(view["task_id"]) if r["event"] == "memory_preflight")[
                "memory_ids"
            ],
        )
        self.assertNotIn("Copperfin", json.dumps(h.store.all("result")))
        self.assertNotIn("Copperfin", json.dumps(h.store.all("action_receipt")))
        self.assertEqual(
            0,
            h.archive.db.execute(
                "SELECT count(*) FROM archive_events WHERE json_extract(payload,'$.task_id')=? "
                "AND json_extract(payload,'$.kind')='remote_result'",
                (view["task_id"],),
            ).fetchone()[0],
        )
        h.memory.forget(memory.id, owner_authorized=True, forget_sources=True)
        after = self.mobile.request("inspect", {"task_id": view["task_id"]})
        self.assertIsNone(after["result"])
        self.assertEqual("UNKNOWN", after["response_status"])
        self.assertEqual([], after["source_event_ids"])

    def test_read_scope_withdrawal_at_executor_boundary_blocks_recall(self):
        h = self.core.harness
        retain(h)
        grant(h.store, self.mobile.handle, "memory:read")
        execute = MemoryExecutor.__call__

        def withdraw(executor, action, cancellation):
            row = h.store.get("session", self.mobile.handle.id)
            h.store.put(
                "session",
                row["id"],
                {
                    **row,
                    "scopes": [s for s in row["scopes"] if s != "memory:read"],
                },
            )
            return execute(executor, action, cancellation)

        with patch.object(MemoryExecutor, "__call__", withdraw):
            view = self.finish(self.ask())
        self.assertIsNone(view["result"])
        self.assertEqual("UNKNOWN", view["response_status"])
        self.assertNotIn("Copperfin", json.dumps(h.store.all("result")))

    def test_read_only_nonretained_request_is_ephemeral_and_session_bound(self):
        h = self.core.harness
        event, _ = retain(h)
        invitation = self.invitation("read-only-mobile", retain=False, memory_control=True)
        session = self.core.remote.enroll(
            {
                "version": 2,
                "challenge_id": invitation["challenge_id"],
                "signature": remote_fixture.signature(
                    self.key, base64.b64decode(invitation["signing_payload"])
                ),
            }
        )
        self.mobile = remote_fixture.DirectClient(self.core, session)
        for kind, identity in (("session", session["session_id"]), ("node", session["node_id"])):
            row = h.store.get(kind, identity)
            h.store.put(
                kind,
                identity,
                {**row, "scopes": [s for s in row["scopes"] if s != "memory:manage"]},
            )
        query = "Recall my preferred editor"
        view = self.finish(
            self.mobile.request(
                "submit",
                {
                    "text": query,
                    "kind": "text",
                    "target": self.config.core_id,
                    "parameters": {},
                    "retain": False,
                },
            )
        )
        self.assertEqual("RECALLED", view["response_status"])
        self.assertEqual([event.id], view["source_event_ids"])
        self.assertFalse(view["request_retained"])
        self.assertFalse(view["retained_available"])
        self.assertEqual(query, view["description"])
        self.assertEqual("", h.store.get("remote_task", view["task_id"])["text"])
        self.assertNotIn(query, json.dumps(h.store.all("objective") + h.store.all("action")))
        self.assertNotIn(
            query,
            " ".join(row[0] for row in h.store.db.execute("SELECT data FROM records")),
        )
        self.assertNotIn(
            query,
            " ".join(row[0] for row in h.store.db.execute("SELECT data FROM audit")),
        )
        self.assertEqual(
            1, h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        hidden = self.core.remote.inspect(view["task_id"], viewer_session="other-session")
        self.assertIsNone(hidden["result"])
        self.assertEqual("Historical request unavailable", hidden["description"])
        owner_snapshot = self.mobile.request("snapshot", {})
        self.assertIn(view["task_id"], [item["task_id"] for item in owner_snapshot["tasks"]])
        other_snapshot = self.desktop.request("snapshot", {})
        self.assertNotIn(view["task_id"], [item["task_id"] for item in other_snapshot["tasks"]])
        h.store.transient.pop(view["task_id"])
        expired = self.mobile.request("inspect", {"task_id": view["task_id"]})
        self.assertIsNone(expired["result"])
        self.assertEqual("UNKNOWN", expired["response_status"])
        self.assertEqual("Historical request unavailable", expired["description"])


class DesktopRecallTests(unittest.TestCase):
    setUp = desktop_fixture.DesktopTests.setUp
    tearDown = desktop_fixture.DesktopTests.tearDown
    call = desktop_fixture.DesktopTests.call
    ask = desktop_fixture.DesktopTests.ask
    confirm = desktop_fixture.DesktopTests.confirm

    def test_main_conversation_signed_read_and_current_source_projection(self):
        event, memory = retain(self.h)
        with self.assertRaises(PermissionError):
            self.ask("Recall my preferred editor")
        grant(self.h.store, self.session, "memory:read")
        view = self.ask("Recall my preferred editor")
        self.assertTrue(view["approval_required"])
        result = self.confirm(view["task_id"])
        self.assertEqual(event.content, result["response"])
        self.assertEqual("RECALLED", result["response_status"])
        self.assertIn(event.id, result["source_event_ids"])
        self.h.memory.forget(memory.id, owner_authorized=True, forget_sources=True)
        after = self.core.inspect(self.session, view["task_id"])
        self.assertEqual("UNKNOWN", after["response_status"])
        self.assertNotIn("Copperfin", after["response"])


if __name__ == "__main__":
    unittest.main()
