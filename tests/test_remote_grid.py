import base64
import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from email.message import Message
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import sleep, time
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import CloudHTTPServer
from oscar.cloud_state import backup_state, restore_state
from oscar.contracts import new_id
from oscar.event_archive import SourceEvent
from oscar.grid import SessionHandle
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.remote_client import request_proof
from oscar.remote_grid import create_invitation
from oscar.remote_worker import RemoteWorker
from oscar.storage import StateConflict
from tests.test_cloud import configuration, request


def keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = base64.b64encode(
        key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    ).decode()
    return key, public


def signature(key, body):
    return base64.b64encode(
        key.sign(
            body,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    ).decode()


class DirectClient:
    def __init__(self, core, session):
        self.core, self.session = core, session
        self.handle = SessionHandle(session["session_id"], session["node_id"], session["token"])

    def request(self, operation, payload, request_id=None):
        return self.core.remote.request(
            self.handle,
            {
                "version": 2,
                "operation": operation,
                "request_id": request_id or new_id(),
                "payload": payload,
            },
        )


class RemoteGridTests(unittest.TestCase):
    def test_memory_control_invitation_is_explicit_and_separate_from_retention(self):
        ordinary = self.invitation("ordinary-memory", retain=False)
        granted = self.invitation("granted-memory", retain=False, memory_control=True)
        normal_scopes = json.loads(base64.b64decode(ordinary["signing_payload"]))["scopes"]
        memory_scopes = json.loads(base64.b64decode(granted["signing_payload"]))["scopes"]
        self.assertNotIn("memory:read", normal_scopes)
        self.assertTrue({"memory:read", "memory:manage"} <= set(memory_scopes))
        self.assertNotIn("archive:retain", memory_scopes)
        self.assertNotIn("retain", memory_scopes)

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = CloudConfig.load(configuration(self.root))
        self.core = CloudCore(self.config, initialize=True)
        self.key, self.public = keypair()
        self.owner_key, self.owner_public = keypair()
        self.desktop = self.enroll("test-desktop", "desktop", owner=True)
        self.mobile = self.enroll("test-mobile", "mobile", owner=True)
        self.workspace = self.root / "worker-workspace"
        self.workspace.mkdir()
        (self.workspace / "known.txt").write_text("known test bytes", encoding="utf-8")
        self.worker = RemoteWorker(
            self.desktop, self.workspace, "test-workspace", self.root / "journal.sqlite"
        )
        self.worker.advertise()

    def tearDown(self):
        self.worker.close()
        self.core.close()
        self.tmp.cleanup()

    def invitation(self, node="test-another", role="mobile", **changes):
        return create_invitation(
            self.core,
            node,
            role,
            "installation-" + node,
            self.public,
            workspace="test-workspace" if role == "desktop" else "",
            retain=changes.pop("retain", True),
            **changes,
        )

    def enroll(self, node, role, owner=False):
        invite = self.invitation(node, role, owner_public_key=self.owner_public if owner else None)
        session = self.core.remote.enroll(
            {
                "version": 2,
                "challenge_id": invite["challenge_id"],
                "signature": signature(self.key, base64.b64decode(invite["signing_payload"])),
            }
        )
        return DirectClient(self.core, session)

    def submit(self, kind="file_read", **changes):
        payload = {
            "text": "Read the synthetic file",
            "kind": kind,
            "target": "test-desktop",
            "parameters": {"path": "known.txt"},
            "retain": True,
            **changes,
        }
        return self.mobile.request("submit", payload)

    def test_day_brief_requires_current_world_scope_and_personal_policy(self):
        brief = self.mobile.request("day_brief", {})["day_brief"]
        self.assertEqual(1, brief["version"])
        self.assertEqual(self.core.harness.runtime.relationship_id, brief["relationship_id"])
        self.assertNotIn("day_brief", self.mobile.request("snapshot", {}))
        store = self.core.harness.store
        PersonalPolicy(store).save(
            PolicyRule(
                "deny-world",
                "core.world.read",
                PolicyEffect.DENY,
                "synthetic-owner",
                time(),
                time(),
                {},
                user_authoritative=True,
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.mobile.request("day_brief", {})
        row = store.get("session", self.mobile.handle.id)
        store.put(
            "session",
            self.mobile.handle.id,
            {**row, "scopes": [s for s in row["scopes"] if s != "world:read"]},
        )
        with self.assertRaises(PermissionError):
            self.mobile.request("day_brief", {})

    def test_snapshot_cannot_keep_worker_capabilities_alive(self):
        grid = self.core.harness.grid
        observed = time()
        with patch.object(grid, "clock", return_value=observed + 31):
            snapshot = self.desktop.request("snapshot", {})
            node = next(n for n in snapshot["nodes"] if n["id"] == "test-desktop")
            self.assertEqual("online", node["status"])
            self.assertEqual([], node["capabilities"])
            self.assertEqual([], grid.search("file_read"))
            self.assertIsNone(self.desktop.request("poll", {})["delivery"])
            self.assertTrue(grid.search("file_read"))

    def approve(self, task):
        challenge = self.mobile.request(
            "challenge", {"task_id": task["task_id"], "operation": "approve"}
        )
        return self.mobile.request(
            "complete",
            {
                "challenge_id": challenge["challenge_id"],
                "signature": signature(
                    self.owner_key, base64.b64decode(challenge["signing_payload"])
                ),
            },
        )

    def finish(self, task):
        until = time() + 6
        while time() < until:
            self.worker.step()
            view = self.mobile.request("inspect", {"task_id": task["task_id"]})
            if view["state"] in {"verified", "failed", "blocked", "unknown", "cancelled"}:
                return view
            sleep(0.02)
        self.fail("real scoped Worker did not complete within test deadline")

    def responsibility(self, path, *, start_at=None):
        change = {
            "operation": "create",
            "id": "new",
            "value": {
                "name": "Synthetic remote routine",
                "goal": "Write reviewed remote notes",
                "steps": [
                    {
                        "id": "save",
                        "node_id": "test-desktop",
                        "capability_id": "machine.files.write",
                        "intent": {
                            "text": "Write reviewed remote notes",
                            "kind": "file_write",
                            "path": path,
                            "content": "synthetic routine",
                        },
                        "depends_on": [],
                    }
                ],
                "start_at": start_at,
                "interval_seconds": None,
                "max_runs": 1,
                "priority": 0,
                "conditions": [],
            },
        }
        review = self.mobile.request("assistance_challenge", change)
        result = self.mobile.request(
            "assistance_complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": signature(self.owner_key, base64.b64decode(review["signing_payload"])),
            },
        )
        return result["executive"]["goals"][-1]["id"]

    def test_signed_responsibility_runs_existing_remote_worker_with_independent_readback(self):
        goal_id = self.responsibility("routine.txt")
        h = self.core.harness
        until = time() + 8
        while time() < until:
            self.worker.step()
            goal = h.store.get("executive_goal", goal_id)
            if goal["state"] == "completed":
                break
            sleep(0.02)
        self.assertEqual("completed", goal["state"])
        task_id = next(
            r["task_id"] for r in h.store.all("executive_task") if r["goal_id"] == goal_id
        )
        self.assertEqual("verified", h.store.task(task_id).state)
        self.assertEqual("synthetic routine", (self.workspace / "routine.txt").read_text())
        view = self.mobile.request("inspect", {"task_id": task_id})
        self.assertTrue(view["evidence"][0]["matches"])
        self.assertFalse(view["approval_required"])
        self.assertEqual("executive", h.store.get("remote_task", task_id)["source"])
        self.assertEqual([], self.mobile.request("snapshot", {})["events"])

    def test_owner_revocation_fences_scheduled_responsibility_before_remote_effect(self):
        goal_id = self.responsibility("revoked-routine.txt", start_at=time() + 0.2)
        self.mobile.request("revoke", {})
        h = self.core.harness
        until = time() + 3
        while time() < until:
            self.worker.step()
            if any(r["goal_id"] == goal_id for r in h.store.all("executive_task")):
                break
            sleep(0.02)
        self.assertTrue(any(r["goal_id"] == goal_id for r in h.store.all("executive_task")))
        self.assertFalse((self.workspace / "revoked-routine.txt").exists())
        self.assertFalse(h.store.all("remote_delivery"))

    def delivery(self):
        for _ in range(100):
            value = self.desktop.request("poll", {})["delivery"]
            if value:
                return value
            sleep(0.01)
        self.fail("no outbound delivery")

    def test_enrollment_proof_single_use_and_role_binding(self):
        invite = self.invitation()
        body = base64.b64decode(invite["signing_payload"])
        wrong, _ = keypair()
        with self.assertRaises(PermissionError):
            self.core.remote.enroll(
                {
                    "version": 2,
                    "challenge_id": invite["challenge_id"],
                    "signature": signature(wrong, body),
                }
            )
        self.core.remote.enroll(
            {
                "version": 2,
                "challenge_id": invite["challenge_id"],
                "signature": signature(self.key, body),
            }
        )
        with self.assertRaises(KeyError):
            self.core.remote.enroll(
                {
                    "version": 2,
                    "challenge_id": invite["challenge_id"],
                    "signature": signature(self.key, body),
                }
            )
        with self.assertRaises(PermissionError):
            self.mobile.request("advertise", {"workspace": "test-workspace", "capabilities": []})

    def test_request_proof_replay_and_changed_body(self):
        body = b'{"version":2,"operation":"snapshot","request_id":"unit-test","payload":{}}'
        nonce, instant = new_id(), str(int(time() * 1000))
        s = self.mobile.session
        headers = Message()
        for name, value in {
            "Authorization": "Bearer " + s["token"],
            "X-Oscar-Node": s["node_id"],
            "X-Oscar-Session": s["session_id"],
            "X-Oscar-Nonce": nonce,
            "X-Oscar-Time": instant,
            "X-Oscar-Signature": signature(
                self.key, request_proof(s["node_id"], s["session_id"], nonce, instant, body)
            ),
        }.items():
            headers[name] = value
        with self.assertRaises(PermissionError):
            self.core.remote.authenticate(headers, body + b" ")
        self.core.remote.authenticate(headers, body)
        with self.assertRaises(StateConflict):
            self.core.remote.authenticate(headers, body)

    def test_android_conversation_requires_exact_live_device_and_current_owner_scope(self):
        from oscar.contracts import Capability, record

        def enroll_native(node, workspace="", control=False):
            invitation = create_invitation(
                self.core,
                node,
                "mobile",
                "installation-" + node,
                self.public,
                workspace=workspace,
                android_control=control,
                retain=True,
                owner_public_key=self.owner_public if control else None,
            )
            return DirectClient(
                self.core,
                self.core.remote.enroll(
                    {
                        "version": 2,
                        "challenge_id": invitation["challenge_id"],
                        "signature": signature(
                            self.key, base64.b64decode(invitation["signing_payload"])
                        ),
                    }
                ),
            )

        self.mobile = enroll_native("native-owner", control=True)
        phone = enroll_native("native-phone", "selected-apps")

        def advertise(client, active=True):
            cap = Capability(
                id="android.clipboard.write",
                name="Selected clipboard",
                summary="Scoped clipboard",
                execution_class="machine",
                node_id=client.handle.node_id,
                permissions=("android:act",),
                input_kind="android_clipboard_write",
                output_kind="reference",
                risk="high",
                version=1,
                reversible=False,
            )
            client.request(
                "advertise",
                {"workspace": "selected-apps", "capabilities": [record(cap)] if active else []},
            )

        def submit(text):
            return self.submit("text", text=text, target=self.core.config.core_id, parameters={})

        advertise(phone)
        task = submit("Copy Exact  Text to clipboard in example.editor")
        self.assertEqual("planned", task["state"])
        self.assertTrue(task["approval_required"])
        self.assertEqual("native-phone", task["target"])
        action = self.core.harness.store.get("planned_action", task["task_id"])
        self.assertEqual("android.clipboard.write", action["capability_id"])
        self.assertEqual(
            {"package": "example.editor", "target": "", "value": "Exact  Text"},
            action["parameters"],
        )
        self.assertIsNone(phone.request("poll", {})["delivery"])
        other = enroll_native("other-phone", "selected-apps")
        advertise(other)
        with self.assertRaises(StateConflict):
            submit("Copy Text to clipboard in example.editor")
        exact = submit("On device native-phone: Copy Text to clipboard in example.editor")
        self.assertEqual("native-phone", exact["target"])
        advertise(phone, active=False)
        with self.assertRaises(StateConflict):
            submit("On device native-phone: Copy Text to clipboard in example.editor")
        store = self.core.harness.store
        owner = store.get("session", self.mobile.handle.id)
        store.put(
            "session",
            self.mobile.handle.id,
            {**owner, "scopes": [s for s in owner["scopes"] if s != "android:act"]},
        )
        with self.assertRaises(PermissionError):
            submit("On device other-phone: Copy Text to clipboard in example.editor")

    def test_native_conversation_routes_explicit_file_request_through_real_worker(self):
        task = self.submit(
            "text",
            text="Please write notes.txt with text Synthetic conversation routine",
            target=self.core.config.core_id,
            parameters={},
        )
        self.assertEqual("planned", task["state"])
        self.assertFalse((self.workspace / "notes.txt").exists())
        self.approve(task)
        self.assertEqual("verified", self.finish(task)["state"])
        self.assertEqual(
            "Synthetic conversation routine", (self.workspace / "notes.txt").read_text()
        )

    def test_real_file_read_and_signed_write_independently_verified(self):
        read = self.finish(self.submit())
        self.assertEqual(read["state"], "verified")
        self.assertEqual(read["result"]["value"], "known test bytes")
        write = self.submit(
            "file_write",
            text="Write a disposable artifact",
            parameters={"path": "created.txt", "content": "approved actual bytes"},
        )
        self.assertTrue(write["approval_required"])
        self.assertFalse((self.workspace / "created.txt").exists())
        self.assertIsNone(self.desktop.request("poll", {})["delivery"])
        self.approve(write)
        final = self.finish(write)
        self.assertEqual(final["state"], "verified")
        self.assertEqual((self.workspace / "created.txt").read_text(), "approved actual bytes")
        self.assertEqual(
            final["evidence"][0]["method"],
            "separate readback request and Core exact-byte comparison",
        )

    def test_independent_readback_detects_changed_result(self):
        task = self.submit()
        delivery = self.delivery()
        result = self.worker.execute(delivery)
        self.desktop.request("deliver", {"delivery_id": delivery["id"], "result": result})
        (self.workspace / "known.txt").write_text("changed after execution")
        final = self.finish(task)
        self.assertEqual(final["state"], "failed")

    def test_duplicate_submission_and_receipt_do_not_repeat_effect(self):
        payload = {
            "text": "Read the synthetic file",
            "kind": "file_read",
            "target": "test-desktop",
            "parameters": {"path": "known.txt"},
            "retain": True,
        }
        task = self.mobile.request("submit", payload, "fixed-idempotent-id")
        duplicate = self.mobile.request("submit", payload, "fixed-idempotent-id")
        self.assertEqual(task["task_id"], duplicate["task_id"])
        with self.assertRaises(StateConflict):
            self.mobile.request("submit", {**payload, "text": "changed"}, "fixed-idempotent-id")
        delivery = self.delivery()
        receipt = {"delivery_id": delivery["id"], "result": self.worker.execute(delivery)}
        self.desktop.request("deliver", receipt)
        self.desktop.request("deliver", receipt)
        with self.assertRaises(StateConflict):
            self.desktop.request(
                "deliver", {**receipt, "result": {**receipt["result"], "value": "changed"}}
            )
        self.assertEqual(self.finish(task)["state"], "verified")

    def test_cancelled_and_wrong_node_delivery_cannot_execute(self):
        task = self.submit()
        delivery = self.delivery()
        with self.assertRaises(PermissionError):
            self.mobile.request("check", {"delivery_id": delivery["id"]})
        self.mobile.request("cancel", {"task_id": task["task_id"]})
        with self.assertRaises(PermissionError):
            self.worker.execute(delivery)
        self.assertEqual(
            self.mobile.request("inspect", {"task_id": task["task_id"]})["state"], "cancelled"
        )

    def test_rotation_revocation_and_owner_recovery_fence_old_session(self):
        new = self.mobile.request("rotate", {})
        with self.assertRaises(PermissionError):
            self.mobile.request("snapshot", {})
        rotated = DirectClient(self.core, new)
        rotated.request("revoke", {})
        with self.assertRaises(PermissionError):
            rotated.request("snapshot", {})
        with self.assertRaises(StateConflict):
            self.invitation("test-mobile")
        invite = self.invitation("test-mobile", recover=True)
        fresh = self.core.remote.enroll(
            {
                "version": 2,
                "challenge_id": invite["challenge_id"],
                "signature": signature(self.key, base64.b64decode(invite["signing_payload"])),
            }
        )
        self.assertNotEqual(fresh["session_id"], new["session_id"])
        self.assertEqual(
            DirectClient(self.core, fresh).request("snapshot", {})["node_id"], "test-mobile"
        )

    def test_policy_and_capability_withdrawal_rechecked_at_worker(self):
        task = self.submit()
        delivery = self.delivery()
        PersonalPolicy(self.core.harness.store).save(
            PolicyRule(
                "deny-remote",
                "machine.files.read",
                PolicyEffect.DENY,
                "synthetic-owner",
                time(),
                time(),
                {},
                user_authoritative=True,
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.worker.execute(delivery)
        self.desktop.request("advertise", {"workspace": "test-workspace", "capabilities": []})
        self.assertFalse(
            any(
                c
                for n in self.core.harness.grid.nodes()
                if n["id"] == "test-desktop"
                for c in n["capabilities"]
            )
        )
        self.mobile.request("cancel", {"task_id": task["task_id"]})

    def test_protocol_and_bounds_rejected(self):
        with self.assertRaises(ValueError):
            self.core.remote.request(
                self.mobile.handle,
                {"version": True, "operation": "snapshot", "request_id": new_id(), "payload": {}},
            )
        for path in ("../outside", "/absolute", "C:/escape", "bad\\path", ""):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.submit(parameters={"path": path})
        with self.assertRaises(ValueError):
            self.mobile.request("snapshot", {"cursor": True})

    def test_snapshot_order_resume_and_cross_client_continuity(self):
        task = self.finish(self.submit())
        for _ in range(100):
            first = self.mobile.request("snapshot", {"cursor": 0})
            if len(first["events"]) >= 2:
                break
            sleep(0.01)
        desktop = self.desktop.request("snapshot", {"cursor": 0})
        self.assertEqual(first["events"], desktop["events"])
        self.assertIn(task["task_id"], [t["task_id"] for t in desktop["tasks"]])
        self.assertEqual(first["events"][0]["turn_id"], first["events"][1]["turn_id"])
        resumed = self.mobile.request(
            "snapshot",
            {"cursor": first["cursor"], "archive_generation": first["archive_generation"]},
        )
        self.assertEqual(resumed["events"], [])
        self.assertEqual(first["events"], sorted(first["events"], key=lambda e: e["sequence"]))

    def test_completion_and_snapshot_repair_retain_one_result_memory(self):
        archive = self.core.harness.archive
        append = archive.append

        def slow_result(event, **kwargs):
            if event.kind == "remote_result":
                sleep(0.05)
            return append(event, **kwargs)

        def snapshot(_):
            try:
                return self.mobile.request("snapshot", {})
            finally:
                archive.close_thread()

        with patch.object(archive, "append", side_effect=slow_result):
            task = self.finish(self.submit())
            with ThreadPoolExecutor(max_workers=8) as readers:
                views = list(readers.map(snapshot, range(8)))
        self.assertTrue(all(len(view["events"]) == 2 for view in views))
        self.assertEqual(
            archive.db.execute(
                "SELECT count(*) FROM archive_memories WHERE forgotten=0 "
                "AND json_extract(payload,'$.event_ids[1]') IS NOT NULL"
            ).fetchone()[0],
            1,
        )
        self.assertEqual(views[0]["tasks"][0]["task_id"], task["task_id"])

    def test_canonical_presence_progress_cancel_and_withdrawn_permission(self):
        before = self.mobile.request("snapshot", {})["presence"]["expression"]
        self.assertEqual(before["operation"], "idle")
        self.assertEqual(before["source"]["kind"], "core")
        self.assertTrue(before["source"]["id"].startswith("presence:"))
        task = self.submit("file_write", parameters={"path": "pending.txt", "content": "no"})
        requested_at = int(time() * 1000)
        response = self.desktop.request("presence", {})
        self.assertGreaterEqual(response["observed_at_ms"], requested_at)
        self.assertLessEqual(response["observed_at_ms"], int(time() * 1000))
        pending = response["expression"]
        self.assertEqual(pending["operation"], "waiting")
        self.assertEqual(pending["source"], before["source"])
        self.assertGreater(pending["generation"], before["generation"])
        self.assertGreater(pending["expiresAt"], int(time() * 1000))
        self.mobile.request("cancel", {"task_id": task["task_id"]})
        self.assertEqual(self.mobile.request("presence", {})["expression"]["operation"], "idle")
        store = self.core.harness.store
        node = store.get("node", self.mobile.handle.node_id)
        store.put(
            "node",
            node["id"],
            {**node, "scopes": [s for s in node["scopes"] if s != "presence:read"]},
        )
        self.assertNotIn("presence", self.mobile.request("snapshot", {}))
        with self.assertRaises(PermissionError):
            self.mobile.request("presence", {})

    def test_core_restart_after_effect_does_not_replay(self):
        task = self.submit("file_write", parameters={"path": "once.txt", "content": "write once"})
        self.approve(task)
        delivery = self.delivery()
        self.worker.execute(delivery)
        self.assertEqual((self.workspace / "once.txt").read_text(), "write once")

        self.core.close()
        self.core = CloudCore(self.config)
        self.desktop.core, self.mobile.core = self.core, self.core
        self.worker.advertise()
        self.assertIsNone(self.desktop.request("poll", {})["delivery"])
        view = self.mobile.request("inspect", {"task_id": task["task_id"]})
        self.assertIn(view["state"], {"blocked", "unknown"})
        self.assertEqual((self.workspace / "once.txt").read_text(), "write once")

    def test_restart_requests_fresh_advertisement_without_claiming_or_replaying_delivery(self):
        task = self.submit("file_write", parameters={"path": "never.txt", "content": "never"})
        self.approve(task)
        delivery = self.delivery()
        self.core.close()
        self.core = CloudCore(self.config)
        self.desktop.core, self.mobile.core = self.core, self.core
        self.assertEqual(
            {"delivery": None, "advertise_required": True}, self.desktop.request("poll", {})
        )
        self.assertEqual(
            "uncertain", self.core.harness.store.get("remote_delivery", delivery["id"])["state"]
        )
        self.assertNotIn(self.desktop.handle.node_id, self.core.harness.executive.targets)
        self.worker.advertise()
        self.assertIn(self.desktop.handle.node_id, self.core.harness.executive.targets)
        self.assertEqual({"delivery": None}, self.desktop.request("poll", {}))
        self.assertFalse((self.workspace / "never.txt").exists())
        self.assertIn(
            self.mobile.request("inspect", {"task_id": task["task_id"]})["state"],
            {"blocked", "unknown"},
        )

    def test_expired_approval_and_revoked_requester(self):
        task = self.submit("file_write", parameters={"path": "never.txt", "content": "no"})
        challenge = self.mobile.request(
            "challenge", {"task_id": task["task_id"], "operation": "approve"}
        )
        row = self.core.harness.store.get("remote_approval", challenge["challenge_id"])
        claim = json.loads(base64.b64decode(row["payload"]))
        claim["expires_at_ms"] = 0
        row["payload"] = base64.b64encode(json.dumps(claim).encode()).decode()
        self.core.harness.store.put("remote_approval", challenge["challenge_id"], row)
        with self.assertRaises(PermissionError):
            self.mobile.request(
                "complete",
                {
                    "challenge_id": challenge["challenge_id"],
                    "signature": signature(self.owner_key, base64.b64decode(row["payload"])),
                },
            )
        self.approve(task)
        delivery = self.delivery()
        self.mobile.request("revoke", {})
        with self.assertRaises(PermissionError):
            self.worker.execute(delivery)
        self.assertFalse((self.workspace / "never.txt").exists())

    def test_restore_invalidates_remote_sessions(self):
        self.core.close()
        backup = self.root / "backup"
        restored = self.root / "restored"
        backup_state(self.config.data_dir, backup)
        restore_state(backup, restored)
        from oscar.storage import Store

        store = Store(restored / "core.sqlite")
        try:
            self.assertTrue(store.get("session", self.mobile.session["session_id"])["revoked"])
        finally:
            store.close()

    def test_forgotten_source_resets_caches_and_hides_related_result(self):
        task = self.finish(self.submit())
        before = self.mobile.request("snapshot", {})
        archive = self.core.harness.archive
        source = self.core.harness.store.get("remote_task", task["task_id"])["event_id"]
        memory = archive.db.execute(
            "SELECT id FROM archive_memories WHERE forgotten=0 "
            "AND json_extract(payload,'$.event_ids[0]')=?",
            (source,),
        ).fetchone()[0]
        archive.forget(memory, owner_authorized=True, forget_sources=True)
        after = self.mobile.request(
            "snapshot",
            {"cursor": before["cursor"], "archive_generation": before["archive_generation"]},
        )
        self.assertTrue(after["reset"])
        self.assertFalse(after["events"])
        self.assertIsNone(after["tasks"][0]["result"])
        self.assertEqual(
            archive.db.execute(
                "SELECT count(*) FROM archive_memories WHERE forgotten=0"
            ).fetchone()[0],
            0,
        )

    def test_snapshot_and_concurrent_forget_use_one_committed_archive_generation(self):
        task = self.finish(self.submit())
        before = self.mobile.request("snapshot", {})
        archive = self.core.harness.archive
        source = self.core.harness.store.get("remote_task", task["task_id"])["event_id"]
        memory = archive.db.execute(
            "SELECT id FROM archive_memories WHERE forgotten=0 "
            "AND json_extract(payload,'$.event_ids[0]')=?",
            (source,),
        ).fetchone()[0]
        start, finished = Event(), Event()
        armed = False

        def forget():
            try:
                self.assertTrue(start.wait(5))
                archive.forget(memory, owner_authorized=True, forget_sources=True)
            finally:
                archive.close_thread()
                finished.set()

        def interleave(operation, table, *_):
            nonlocal armed
            if operation == sqlite3.SQLITE_READ and table == "archive_tombstones":
                armed = True
            if armed and operation == sqlite3.SQLITE_READ and table == "archive_events":
                start.set()
                if not finished.wait(5):
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        with ThreadPoolExecutor(1) as executor:
            writer = executor.submit(forget)
            archive.db.set_authorizer(interleave)
            try:
                during = self.mobile.request("snapshot", {})
            finally:
                archive.db.set_authorizer(None)
                start.set()
            writer.result()
        self.assertEqual(during["archive_generation"], before["archive_generation"])
        self.assertEqual(during["events"], before["events"])
        after = self.mobile.request(
            "snapshot", {"archive_generation": before["archive_generation"]}
        )
        self.assertTrue(after["reset"])
        self.assertEqual(after["events"], [])

    def test_large_archive_event_does_not_stall_cursor(self):
        archive = self.core.harness.archive
        archive.append(
            SourceEvent(
                self.core.harness.runtime.relationship_id,
                "é" * 16_500,
                "synthetic",
                time(),
                sensitivity="synthetic",
            ),
            retain_authorized=True,
        )
        archive.append(
            SourceEvent(
                self.core.harness.runtime.relationship_id,
                "later event",
                "synthetic",
                time(),
                sensitivity="synthetic",
            ),
            retain_authorized=True,
        )
        view = self.mobile.request("snapshot", {})
        self.assertEqual(view["events"][-1]["text"], "later event")
        self.assertLessEqual(len(json.dumps(view).encode()), 245760)

    def test_rotation_failure_rolls_back_new_session_and_preserves_current(self):
        store = self.core.harness.store
        previous = store.all("session")
        original = store.put

        def fail_binding(kind, identifier, value):
            if kind == "remote_device":
                raise OSError("synthetic persistence failure")
            return original(kind, identifier, value)

        with patch.object(store, "put", side_effect=fail_binding), self.assertRaises(OSError):
            self.mobile.request("rotate", {})
        self.assertEqual(store.all("session"), previous)
        self.assertEqual(self.mobile.request("snapshot", {})["node_id"], "test-mobile")

    def test_expired_invitation_and_session_cannot_resume(self):
        invite = self.invitation()
        store = self.core.harness.store
        row = store.get("remote_invitation", invite["challenge_id"])
        store.put("remote_invitation", row["id"], {**row, "expires_at_ms": 0})
        with self.assertRaises(PermissionError):
            self.core.remote.enroll(
                {
                    "version": 2,
                    "challenge_id": row["id"],
                    "signature": signature(self.key, base64.b64decode(invite["signing_payload"])),
                }
            )
        session = store.get("session", self.mobile.handle.id)
        store.put("session", session["id"], {**session, "expires_at": 0})
        with self.assertRaises(PermissionError):
            self.mobile.request("snapshot", {})

    def test_invalid_http_proofs_do_not_consume_valid_device_allowance(self):
        server = CloudHTTPServer(self.core)
        server.start()
        try:
            body = {"version": 2, "operation": "snapshot", "request_id": new_id(), "payload": {}}
            for _ in range(125):
                status, _ = request(
                    self.config,
                    "/v2/grid/request",
                    body=body,
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(status, 401)
            self.assertFalse(server.grid_arrivals)
            nonce, instant = new_id(), str(int(time() * 1000))
            session = self.mobile.session
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + session["token"],
                "X-Oscar-Node": session["node_id"],
                "X-Oscar-Session": session["session_id"],
                "X-Oscar-Nonce": nonce,
                "X-Oscar-Time": instant,
                "X-Oscar-Signature": signature(
                    self.key,
                    request_proof(
                        session["node_id"],
                        session["session_id"],
                        nonce,
                        instant,
                        json.dumps(body).encode(),
                    ),
                ),
            }
            status, _ = request(self.config, "/v2/grid/request", body=body, headers=headers)
            self.assertEqual(status, 200)
            missing = {**body, "operation": "inspect", "payload": {"task_id": new_id()}}
            nonce = new_id()
            headers["X-Oscar-Nonce"] = nonce
            headers["X-Oscar-Signature"] = signature(
                self.key,
                request_proof(
                    session["node_id"],
                    session["session_id"],
                    nonce,
                    instant,
                    json.dumps(missing).encode(),
                ),
            )
            self.assertEqual(
                request(self.config, "/v2/grid/request", body=missing, headers=headers)[0], 403
            )
            self.assertTrue(self.mobile.request("snapshot", {})["nodes"])
            for invalid in ({**body, "version": 7}, {**body, "payload": []}):
                self.assertEqual(
                    request(
                        self.config,
                        "/v2/grid/request",
                        body=invalid,
                        headers={"Content-Type": "application/json"},
                    )[0],
                    401,
                )
            self.assertEqual(
                request(
                    self.config,
                    "/v2/grid/request",
                    body={"oversized": "x" * 33000},
                    headers={"Content-Type": "application/json"},
                )[0],
                413,
            )
        finally:
            server.close()

    def test_real_bounded_core_response_and_unavailable_model(self):
        addition = self.mobile.request(
            "submit",
            {
                "text": "Calculate 19 + 23",
                "kind": "addition",
                "target": self.config.core_id,
                "parameters": {"expression": "19 + 23"},
                "retain": True,
            },
        )
        self.assertEqual(self.finish(addition)["result"]["value"], "42")
        text = self.mobile.request(
            "submit",
            {
                "text": "Explain an ocean tide",
                "kind": "text",
                "target": self.config.core_id,
                "parameters": {},
                "retain": True,
            },
        )
        final = self.finish(text)
        self.assertIn(final["state"], {"blocked", "failed"})
        self.assertFalse(final["evidence"])

    def test_no_archive_grant_allows_status_but_redacts_history_and_results(self):
        task = self.finish(self.submit())
        previous = self.mobile.request("snapshot", {})
        store = self.core.harness.store
        for kind, identity in (
            ("session", self.mobile.handle.id),
            ("node", self.mobile.handle.node_id),
        ):
            row = store.get(kind, identity)
            row["scopes"] = [s for s in row["scopes"] if not s.startswith("archive:")]
            store.put(kind, identity, row)
        view = self.mobile.request(
            "snapshot",
            {"cursor": previous["cursor"], "archive_generation": previous["archive_generation"]},
        )
        self.assertTrue(view["reset"])
        self.assertEqual(view["cursor"], 0)
        self.assertTrue(view["nodes"])
        self.assertFalse(view["events"])
        self.assertIsNone(view["tasks"][0]["result"])
        inspected = self.mobile.request("inspect", {"task_id": task["task_id"]})
        self.assertNotIn("synthetic file", inspected["description"])
        self.assertIsNone(inspected["result"])
        with self.assertRaises(PermissionError):
            self.submit()

    def test_signed_approval_rejects_changed_action_and_generation(self):
        for tamper in ("action", "generation"):
            with self.subTest(tamper=tamper):
                task = self.submit(
                    "file_write", parameters={"path": tamper + ".txt", "content": "reviewed"}
                )
                challenge = self.mobile.request(
                    "challenge", {"task_id": task["task_id"], "operation": "approve"}
                )
                store = self.core.harness.store
                if tamper == "action":
                    action = store.get("planned_action", task["task_id"])
                    store.put(
                        "planned_action",
                        task["task_id"],
                        {**action, "parameters": {"path": "changed.txt", "content": "different"}},
                    )
                else:
                    record = store.get("task", task["task_id"])
                    store.put(
                        "task", task["task_id"], {**record, "attempts": record["attempts"] + 1}
                    )
                with self.assertRaises(StateConflict):
                    self.mobile.request(
                        "complete",
                        {
                            "challenge_id": challenge["challenge_id"],
                            "signature": signature(
                                self.owner_key, base64.b64decode(challenge["signing_payload"])
                            ),
                        },
                    )
                self.assertFalse((self.workspace / "changed.txt").exists())

    def test_synced_result_is_readable_and_has_canonical_provenance(self):
        task = self.finish(self.submit())
        view = self.mobile.request("snapshot", {})
        result = next(e for e in view["events"] if e["speaker"] == "oscar")
        self.assertEqual(result["text"], "known test bytes")
        self.assertEqual(result["task_id"], task["task_id"])
        self.assertEqual(result["status"], "VERIFIED")
        archive = self.core.harness.archive
        self.assertIn('"evidence"', archive.event(result["event_id"]).content)

    def test_withdrawn_approval_scope_blocks_already_reviewed_write(self):
        task = self.submit("file_write", parameters={"path": "withdrawn.txt", "content": "never"})
        self.approve(task)
        delivery = self.delivery()
        store = self.core.harness.store
        row = store.get("node", self.mobile.handle.node_id)
        store.put(
            "node", row["id"], {**row, "scopes": [s for s in row["scopes"] if s != "grid:approve"]}
        )
        with self.assertRaises(PermissionError):
            self.worker.execute(delivery)
        self.assertFalse((self.workspace / "withdrawn.txt").exists())


if __name__ == "__main__":
    unittest.main()
