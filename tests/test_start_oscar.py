"""Everyday enrollment preserves canonical history and respects revocation."""

from oscar.desktop import Desktop
from oscar.policy import PersonalPolicy
from scripts.start_oscar import desktop_session, mount_windows_worker, renew_local_execution
from tests.test_desktop_conversation import ConversationTests


class EverydayDesktopTests(ConversationTests):
    def test_windows_worker_executes_signed_scoped_file_write_with_readback(self):
        worker = mount_windows_worker(self.h, self.root / "core.db")
        self.session = desktop_session(self.h, worker.session.node_id)
        self.core = Desktop(
            self.h.runtime,
            PersonalPolicy(self.h.store),
            self.h.executive.targets,
            native_catalogs={
                worker.session.node_id: {
                    "executables": worker.scope.allowed_executables,
                }
            },
        )
        self.core.register_owner_key(self.session, self.encoded, owner_authorized=True)
        catalog = self.call("catalog", {})["capabilities"]
        cap = next(
            c for c in catalog if c["id"] == worker.session.node_id + "::machine.files.write"
        )
        task = self.call(
            "act",
            {
                "capability_id": cap["id"],
                "operation": "write_file",
                "fields": {"path": "alpha-test.txt", "text": "Disposable alpha acceptance"},
            },
        )
        self.assertFalse((self.root / "workspace/alpha-test.txt").exists())
        self.assertEqual(self.confirm(task["task_id"])["state"], "verified")
        self.assertEqual(
            (self.root / "workspace/alpha-test.txt").read_text(),
            "Disposable alpha acceptance",
        )
        self.assertFalse(any(c["kind"] in {"screen_capture", "desktop_clipboard"} for c in catalog))
        if worker.powershell:
            shell_cap = next(c for c in catalog if c["kind"] == "powershell")
            shell_task = self.call(
                "act",
                {
                    "capability_id": shell_cap["id"],
                    "operation": "ps_write_utf8",
                    "fields": {"path": "alpha-shell-test.txt", "text": "Verified PowerShell write"},
                },
            )
            self.assertEqual(self.confirm(shell_task["task_id"])["state"], "verified")
            self.assertEqual(
                (self.root / "workspace/alpha-shell-test.txt").read_text(),
                "Verified PowerShell write",
            )

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
