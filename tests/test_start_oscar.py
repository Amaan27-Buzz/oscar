"""Everyday enrollment preserves canonical history and respects revocation."""

from scripts.start_oscar import desktop_session, renew_local_execution
from tests.test_desktop_conversation import ConversationTests


class EverydayDesktopTests(ConversationTests):
    def test_expired_core_execution_can_renew_but_revoked_execution_cannot(self):
        binding = self.h.store.get("core_execution", self.h.node_id)
        current = self.h.store.get("session", binding["session_id"])
        current = {**current, "node_id": "oscar-local-core"}
        # The everyday Core uses its own stable identity.
        self.h.store.put("node", "oscar-local-core", {"revoked": False})
        self.h.store.put("core_execution", "oscar-local-core", binding)
        self.h.store.put("session", current["id"], {**current, "expires_at": 1})
        self.assertTrue(renew_local_execution(self.root / "core.db"))
        self.h.store.put("session", current["id"], {**current, "revoked": True})
        self.assertFalse(renew_local_execution(self.root / "core.db"))

    def test_everyday_session_retains_history_across_new_surface_session(self):
        self.session = desktop_session(self.h)
        self.core.register_owner_key(self.session, self.encoded, owner_authorized=True)
        task = self.ask("17 + 25")
        self.confirm(task["task_id"])
        previous = self.session
        self.session = desktop_session(self.h)
        self.assertNotEqual(previous.id, self.session.id)
        self.assertTrue(self.h.store.get("session", previous.id)["revoked"])
        history = self.call("conversation", {"before": 0})
        self.assertEqual([t["text"] for t in history["turns"]], ["17 + 25", "42"])

    def test_revoked_enrollment_is_not_silently_reactivated(self):
        self.session = desktop_session(self.h)
        node = self.h.store.get("node", self.session.node_id)
        self.h.store.put("node", self.session.node_id, {**node, "revoked": True})
        with self.assertRaises(PermissionError):
            desktop_session(self.h)
