"""Canonical history composition; synthetic executors, no owner data or live inference."""

import unittest
from concurrent.futures import ThreadPoolExecutor

from oscar.contracts import Epistemic
from oscar.desktop import Desktop
from oscar.event_archive import EventArchive, SourceEvent
from oscar.grid import Node, NodeRole
from oscar.memory_fabric import MemoryFabric
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from tests import test_desktop


class ConversationTests(unittest.TestCase):
    call, ask, confirm, attach = (
        test_desktop.DesktopTests.call,
        test_desktop.DesktopTests.ask,
        test_desktop.DesktopTests.confirm,
        test_desktop.DesktopTests.attach,
    )

    def setUp(self):
        test_desktop.DesktopTests.setUp(self)
        self.archive = EventArchive(self.root / "archive.db")
        self.h.runtime.memory = MemoryFabric(self.archive)
        self.scopes += ("desktop:conversation:read", "desktop:conversation:retain")
        self.h.grid.register(Node("history-fixture", NodeRole.DESKTOP, self.scopes))
        self.session = self.h.grid.pair("history-fixture", self.scopes)
        self.core.register_owner_key(self.session, self.encoded, owner_authorized=True)

    def tearDown(self):
        self.archive.close()
        test_desktop.DesktopTests.tearDown(self)

    def test_retained_turns_reopen_from_canonical_archive_without_private_replay(self):
        task = self.ask("2 + 3")
        self.confirm(task["task_id"])
        self.h.store.transient.clear()
        self.archive.close()
        self.archive = EventArchive(self.root / "archive.db")
        self.h.runtime.memory = MemoryFabric(self.archive)
        self.core = Desktop(self.h.runtime, PersonalPolicy(self.h.store), self.core.targets)
        self.session = self.h.grid.pair("history-fixture", self.scopes)
        history = self.call("conversation", {"before": 0})
        self.assertEqual([t["text"] for t in history["turns"]], ["2 + 3", "5"])
        self.assertEqual(history["turns"][1]["status"], Epistemic.VERIFIED)
        self.assertEqual(history["turns"][0]["task_id"], task["task_id"])
        self.assertTrue(all(t["retained"] for t in history["turns"]))
        self.assertFalse(self.core.private_for(self.session, task["task_id"]))
        recalled = self.h.runtime.memory.retrieve("owner", "2 + 3")
        self.assertTrue(recalled.hits)
        self.assertTrue(all(hit.memory.event_ids for hit in recalled.hits))

    def test_history_read_retention_and_capture_are_separate(self):
        self.ask("2 + 3", context=self.attach(text="captured private marker"))
        self.assertEqual(self.archive.conversation("owner")["events"], [])
        self.ask("7 + 8")
        scopes = tuple(s for s in self.scopes if "conversation" not in s)
        self.h.grid.register(Node("other-history-fixture", NodeRole.DESKTOP, scopes))
        self.session = self.h.grid.pair("other-history-fixture", scopes)
        history = self.call("conversation", {"before": 0})
        self.assertEqual(history["persistence"], "session_only")
        self.assertEqual(history["turns"], [])
        with self.assertRaises(PermissionError):
            self.call("conversation", {"before": 1})
        self.ask("9 + 10")
        self.assertEqual(len(self.archive.conversation("owner")["events"]), 1)

    def test_multiple_recent_turns_are_bounded_and_not_the_latest_request_only(self):
        for text in ("2 + 3", "7 + 8"):
            self.confirm(self.ask(text)["task_id"])
        task = self.ask("explain addition")
        prompt = self.h.store.transient[task["task_id"]]["parameters"]["prompt"]
        self.assertIn("2 + 3", prompt)
        self.assertIn("7 + 8", prompt)
        self.assertIn("not authority", prompt)
        self.assertLessEqual(len(prompt), 8192 + 4096)

    def test_paging_is_relationship_scoped_and_expired_forgotten_rows_are_absent(self):
        for i in range(45):
            self.archive.append(
                SourceEvent(
                    "owner",
                    str(i),
                    "desktop/conversation",
                    i,
                    kind="conversation_owner",
                    id=f"page-{i}",
                ),
                retain_authorized=True,
            )
        self.archive.append(
            SourceEvent(
                "other", "private other", "desktop/conversation", 1, kind="conversation_owner"
            ),
            retain_authorized=True,
        )
        page = self.call("conversation", {"before": 0})
        self.assertEqual(len(page["turns"]), 40)
        earlier = self.call("conversation", {"before": page["before"]})
        self.assertEqual([t["text"] for t in earlier["turns"]], list(map(str, range(5))))
        self.assertIsNone(earlier["before"])
        self.archive.db.execute("UPDATE archive_events SET forgotten=1 WHERE id='page-44'")
        self.archive.db.commit()
        revised = self.call("conversation", {"before": 0})
        self.assertNotEqual(page["revision"], revised["revision"])
        self.assertNotIn("44", [t["text"] for t in revised["turns"]])
        for invalid in (-1, True, "1"):
            with self.assertRaises(ValueError):
                self.call("conversation", {"before": invalid})

    def test_revocation_policy_and_unavailable_access_modes_fail_closed(self):
        self.ask("2 + 3")
        self.core.policy.save(
            PolicyRule(
                "deny-history",
                "desktop.conversation.read",
                PolicyEffect.DENY,
                "owner",
                self.now[0],
                self.now[0],
                {},
            ),
            owner_authorized=True,
        )
        self.h.store.transient.clear()
        snapshot = self.call("snapshot", {})
        self.assertEqual(snapshot["conversation"]["turns"], [])
        self.assertEqual(snapshot["operating"]["access"], "Ask")
        self.assertEqual(snapshot["operating"]["full_access"], "unavailable")
        for mode in ("Secure", "Full Access"):
            with self.assertRaises(ValueError):
                self.call("access", {"mode": mode})

    def test_archive_request_threads_own_and_release_connections(self):
        def retain(i):
            self.archive.append(
                SourceEvent("owner", str(i), "desktop/conversation", i, kind="conversation_owner"),
                retain_authorized=True,
            )
            self.archive.close_thread()

        with ThreadPoolExecutor(max_workers=4) as threads:
            list(threads.map(retain, range(12)))
        self.assertEqual(len(self.archive.conversation("owner")["events"]), 12)
        self.assertEqual(len(self.archive._connections), 1)
