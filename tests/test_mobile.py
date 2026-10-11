"""Real loopback/Core and synthetic owner keys, never Android device acceptance."""

import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from time import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from oscar.contracts import TaskState
from oscar.grid import Node, NodeRole, SessionHandle
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.mobile import Mobile, MobileServer, display_digest
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.storage import StateConflict

from .support import RouterRig


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "optional Mobile security executor")
class MobileTests(unittest.TestCase):
    def test_full_native_review_digest_and_private_progress_metadata(self) -> None:
        task = self.call("text", {"text": "what is two plus three"}, "native-review")
        challenge = self.call("challenge", {"operation": "approve", "task_id": task["task_id"]})
        claim = json.loads(base64.b64decode(challenge["signing_payload"]))
        self.assertEqual(challenge["exact_request"], "what is two plus three")
        self.assertEqual(
            claim["display_digest"],
            display_digest(
                challenge["operation"],
                challenge["scope"],
                challenge["target"],
                challenge["review"],
                challenge["exact_request"],
            ),
        )
        self.assertNotEqual(
            claim["display_digest"],
            display_digest(
                "approve", challenge["scope"], challenge["target"], "{}", challenge["exact_request"]
            ),
        )
        self.h.store.put(
            "worker_checkpoint",
            task["task_id"],
            {"fraction": 0.5, "step": "synthetic-private-step"},
        )
        view = self.core.inspect(self.session, task["task_id"])
        self.assertEqual(view["progress"]["status"], "REPORTED")
        self.assertEqual(view["progress"]["step"], "synthetic-private-step")
        self.assertFalse(view["progress"]["current"])
        replacement = self.h.grid.pair(self.session.node_id, self.scopes)
        public = self.core.inspect(replacement, task["task_id"])
        self.assertEqual(public["progress"]["step"], "Worker checkpoint available")
        self.assertEqual(public["artifacts"], [])
        self.assertNotIn("approve", public["actions"])

    def test_core_origin_task_without_surface_association_is_inspectable(self) -> None:
        task = self.h.runtime.create(Intent("3+4"))
        self.h.runtime.run(task.id, {self.h.node_id: (self.h.dispatcher, self.h.session)})
        view = self.core.inspect(self.session, task.id)
        self.assertEqual(view["origin_surface"], "Core")
        self.assertIsNone(view["origin_node"])

    def setUp(self) -> None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.h = Harness(
            root / "core.db", root / "workspace", Path("config/development-models.json")
        )
        self.now = [time()]
        self.h.grid.clock = lambda: self.now[0]
        self.scopes = (
            "mobile:connect",
            "mobile:inspect",
            "mobile:text",
            "heartbeat",
            "math",
            "control:inspect:" + self.h.node_id,
            "control:approve:" + self.h.node_id,
            "control:cancel:" + self.h.node_id,
            "notifications:reply",
            "communications:send",
        )
        self.h.grid.register(Node("reference-mobile", NodeRole.MOBILE, self.scopes))
        self.session = self.h.grid.pair("reference-mobile", self.scopes)
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        encoded = base64.b64encode(
            self.key.public_key().public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).decode()
        self.policy = PersonalPolicy(self.h.store)
        self.core = Mobile(
            self.h.runtime, self.policy, {self.h.node_id: (self.h.dispatcher, self.h.session)}
        )
        with self.assertRaises(PermissionError):
            self.core.register_owner_key(self.session, encoded, owner_authorized=False)
        self.core.register_owner_key(self.session, encoded, owner_authorized=True)

    def tearDown(self) -> None:
        self.h.store.close()
        self.temp.cleanup()

    def envelope(self, operation: str, payload: dict, identifier: str = "request") -> dict:
        return {"version": 1, "operation": operation, "request_id": identifier, "payload": payload}

    def call(self, operation: str, payload: dict, identifier: str = "request") -> dict:
        return self.core.request(self.session, self.envelope(operation, payload, identifier))

    def signed(self, challenge: dict) -> dict:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        signature = self.key.sign(
            base64.b64decode(challenge["signing_payload"]),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        return {
            "challenge_id": challenge["challenge_id"],
            "signature": base64.b64encode(signature).decode(),
        }

    def test_real_loopback_signed_core_task_and_wrong_token(self) -> None:
        with MobileServer(self.core) as server:
            headers = {
                "Authorization": "Bearer " + self.session.token,
                "X-Oscar-Node": self.session.node_id,
                "X-Oscar-Session": self.session.id,
            }

            def post(operation: str, payload: dict, identifier: str) -> dict:
                request = Request(
                    server.url + "/v1/mobile",
                    data=json.dumps(self.envelope(operation, payload, identifier)).encode(),
                    headers=headers,
                )
                with urlopen(request, timeout=5) as response:
                    return json.loads(response.read())

            proposed = post("text", {"text": "what is two plus three"}, "text")
            self.assertEqual(proposed["state"], TaskState.PLANNED)
            challenge = post(
                "challenge", {"operation": "approve", "task_id": proposed["task_id"]}, "challenge"
            )
            self.assertEqual("what is two plus three", challenge["exact_request"])
            self.assertEqual("2 + 3", json.loads(challenge["review"])["expression"])
            result = post("complete", self.signed(challenge), "approve")
            self.assertEqual(result["state"], TaskState.VERIFIED)
            self.assertTrue(result["evidence_ids"])
            self.assertEqual(result["value"], "5")
            self.assertIsNone(self.h.store.all("result")[-1]["value"])
            self.assertEqual(self.h.store.transient[proposed["task_id"]]["result"].value, "5")
            headers["Authorization"] = "Bearer invalid-reference-token"
            with self.assertRaises(HTTPError) as rejected:
                post("snapshot", {}, "snapshot")
            self.assertEqual(rejected.exception.code, 403)
            self.assertNotIn(self.session.token, str(rejected.exception))
            rejected.exception.close()

    def test_idempotency_replay_and_unsupported_text(self) -> None:
        proposed = self.call("text", {"text": "2 + 3"}, "same")
        self.assertTrue(self.call("text", {"text": "2 + 3"}, "same")["replayed"])
        self.assertEqual(len(self.h.store.all("task")), 1)
        with self.assertRaises(StateConflict):
            self.call("text", {"text": "3 + 4"}, "same")
        blocked = self.call("text", {"text": "send an email"}, "unsupported")
        self.assertEqual(blocked["state"], TaskState.BLOCKED)
        self.assertEqual(len(self.h.store.all("task")), 1)
        challenge = self.call("challenge", {"operation": "cancel", "task_id": proposed["task_id"]})
        signed = self.signed(challenge)
        result = self.call("complete", signed, "cancel")
        self.assertEqual(result["state"], TaskState.CANCELLED)
        with self.assertRaises(PermissionError):
            self.call("complete", signed, "replay")

    def test_changed_plan_expiry_wrong_signature_and_revocation(self) -> None:
        proposed = self.call("text", {"text": "2 + 3"}, "text")
        task_id = proposed["task_id"]
        challenge = self.call("challenge", {"operation": "approve", "task_id": task_id})
        self.h.store.put(
            "plan", task_id, {"kind": "addition", "parameters": {"expression": "8 + 9"}}
        )
        with self.assertRaises(StateConflict):
            self.call("complete", self.signed(challenge), "changed")
        challenge = self.call("challenge", {"operation": "approve", "task_id": task_id}, "new")
        with self.assertRaises(PermissionError):
            self.call(
                "complete",
                {
                    "challenge_id": challenge["challenge_id"],
                    "signature": base64.b64encode(b"not-a-signature").decode(),
                },
                "wrong",
            )
        self.now[0] += 31
        with self.assertRaises(PermissionError):
            self.call("complete", self.signed(challenge), "expired")
        self.h.grid.revoke(self.session.node_id)
        with self.assertRaises(PermissionError):
            self.call("snapshot", {}, "revoked")
        self.assertEqual(self.h.store.task(task_id).state, TaskState.PLANNED)

    def test_policy_and_scope_rechecked_after_confirmation(self) -> None:
        proposed = self.call("text", {"text": "2 + 3"}, "text")
        challenge = self.call("challenge", {"operation": "approve", "task_id": proposed["task_id"]})
        self.policy.save(
            PolicyRule("deny-math", "math.add", PolicyEffect.DENY, "owner", 1, 1, {}),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.call("complete", self.signed(challenge), "denied")
        self.assertFalse(self.h.store.all("result"))
        invalid = SessionHandle(self.session.id, "another-node", self.session.token)
        with self.assertRaises((PermissionError, KeyError)):
            self.core.request(invalid, self.envelope("snapshot", {}))

    def test_reply_source_policy_and_missing_communication_grant(self) -> None:
        payload = {
            "operation": "reply",
            "package": "example.messaging",
            "key_hash": hashlib.sha256(b"reference").hexdigest(),
            "text_hash": hashlib.sha256(b"neutral reply").hexdigest(),
        }
        challenge = self.call("challenge", payload)
        self.policy.save(
            PolicyRule(
                "source-deny",
                "notification.reply",
                PolicyEffect.DENY,
                "owner",
                1,
                1,
                {"app": "example.messaging"},
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.call("complete", self.signed(challenge), "source-denied")
        row = self.h.store.get("session", self.session.id)
        row["scopes"].remove("communications:send")
        self.h.store.put("session", self.session.id, row)
        with self.assertRaises(PermissionError):
            self.call("complete", self.signed(challenge), "send-denied")
        first = self.call("text", {"text": "2 + 3"}, "first-text")
        second = self.call("text", {"text": "4 + 5"}, "second-text")
        self.assertNotEqual(first["task_id"], second["task_id"])

    def test_reply_permit_is_not_delivery_and_retains_no_text(self) -> None:
        payload = {
            "operation": "reply",
            "package": "example.messaging",
            "key_hash": hashlib.sha256(b"reference-notification").hexdigest(),
            "text_hash": hashlib.sha256(b"Original neutral reference reply").hexdigest(),
        }
        challenge = self.call("challenge", payload)
        result = self.call("complete", self.signed(challenge), "reply")
        self.assertEqual(result["permit"]["text_hash"], payload["text_hash"])
        self.assertEqual(result["status"], "REPORTED")
        self.assertIn("NOT_VERIFIED", result["verification"])
        rows = json.dumps(self.h.store.all("sunday_challenge"))
        self.assertNotIn("Original neutral reference reply", rows)
        self.assertFalse(self.h.store.all("task"))

    def test_deny_retry_and_task_generation_are_core_owned(self) -> None:
        proposed = self.call("text", {"text": "2 + 3"}, "deny-text")
        self.assertIn("deny", proposed["actions"])
        challenge = self.call("challenge", {"operation": "deny", "task_id": proposed["task_id"]})
        result = self.call("complete", self.signed(challenge), "deny")
        self.assertEqual(result["state"], TaskState.CANCELLED)
        self.assertEqual(result["actions"], [])
        self.assertFalse(self.h.store.all("result"))
        proposed = self.call("text", {"text": "4 + 5"}, "retry-text")
        self.h.store.transition(proposed["task_id"], TaskState.BLOCKED, blocker="reference loss")
        challenge = self.call("challenge", {"operation": "retry", "task_id": proposed["task_id"]})
        result = self.call("complete", self.signed(challenge), "retry")
        self.assertEqual(result["state"], TaskState.PLANNED)
        self.assertFalse(self.h.store.all("result"))
        with self.assertRaises(StateConflict):
            self.call("challenge", {"operation": "retry", "task_id": proposed["task_id"]}, "again")

    def test_old_enrollment_compatibility_and_offline_reconnect(self) -> None:
        row = self.h.store.get("node", self.session.node_id)
        row["role"] = NodeRole.SUNDAY
        row["scopes"] = [scope.replace("mobile:", "sunday:") for scope in row["scopes"]]
        self.h.store.put("node", self.session.node_id, row)
        scopes = self.h.store.get("session", self.session.id)
        scopes["scopes"] = [scope.replace("mobile:", "sunday:") for scope in scopes["scopes"]]
        self.h.store.put("session", self.session.id, scopes)
        self.assertIn("nodes", self.call("snapshot", {}))
        self.now[0] += 31
        snapshot = self.call("snapshot", {}, "offline")
        target = next(node for node in snapshot["nodes"] if node["id"] == self.h.node_id)
        self.assertEqual(target["status"], "offline")
        self.assertFalse(target["capabilities"])
        self.h.grid.heartbeat(self.h.session)
        self.h.grid.advertise(self.h.session, [])
        self.assertEqual(self.call("snapshot", {}, "reconnect")["nodes"][0]["status"], "online")

    def test_invalid_envelope_and_session_expiry_are_rejected(self) -> None:
        for value in (
            {},
            {"version": True, "operation": "snapshot", "request_id": "bad", "payload": {}},
        ):
            with self.assertRaises((ValueError, KeyError)):
                self.core.request(self.session, value)
        self.now[0] += 3601
        with self.assertRaises(PermissionError):
            self.call("snapshot", {}, "expired")

    def test_rename_does_not_bypass_legacy_source_policy(self) -> None:
        task = self.call("text", {"text": "2 + 3"}, "policy-text")
        challenge = self.call("challenge", {"operation": "approve", "task_id": task["task_id"]})
        self.policy.save(
            PolicyRule(
                "legacy-source-deny",
                "math.add",
                PolicyEffect.DENY,
                "owner",
                1,
                1,
                {"source": "sunday"},
            ),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.call("complete", self.signed(challenge), "legacy-denied")
        self.assertFalse(self.h.store.all("result"))

    def reasoning_fixture(self) -> RouterRig:
        from oscar.harness import ModelExecutor
        from oscar.models import RoutingPolicy

        router = RouterRig()
        router.registry.providers = {
            key: replace(provider, local=True, private=True)
            for key, provider in router.registry.providers.items()
        }
        self.addCleanup(router.close)
        for table, identifier in (("node", self.session.node_id), ("session", self.session.id)):
            row = self.h.store.get(table, identifier)
            row["scopes"].append("models")
            self.h.store.put(table, identifier, row)
        self.h.dispatcher.executors["models.reason"] = ModelExecutor(
            router.router, router.request, RoutingPolicy()
        )
        return router

    def test_core_reasoning_route_stays_reported_and_memory_misses_block(self) -> None:
        router = self.reasoning_fixture()
        task = self.call("text", {"text": "Explain a neutral sorting algorithm"}, "reason-text")
        self.assertEqual(self.h.store.get("plan", task["task_id"])["kind"], "model_reasoning")
        self.assertFalse(router.adapter.calls)
        challenge = self.call("challenge", {"operation": "approve", "task_id": task["task_id"]})
        result = self.call("complete", self.signed(challenge), "reason-approve")
        self.assertTrue(router.adapter.calls)
        self.assertEqual(result["response"], "reported synthetic answer")
        self.assertEqual(result["response_status"], "REPORTED")
        self.assertNotEqual(result["state"], TaskState.VERIFIED)
        self.assertNotIn("value", result)
        recalled = self.call("text", {"text": "remember what I chose last time"}, "recall")
        self.assertEqual(recalled["state"], TaskState.BLOCKED)
        self.assertEqual(len(self.h.store.all("task")), 1)

    def test_inspection_and_signed_cancel_remain_available_during_reasoning(self) -> None:
        from threading import Event, Thread

        from oscar.models import ProviderResponse

        router = self.reasoning_fixture()
        entered, release = Event(), Event()

        def blocked(check_cancel, sink):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("reference executor timed out")
            check_cancel()
            return ProviderResponse("late synthetic answer")

        router.adapter.steps.append(blocked)
        task = self.call("text", {"text": "Explain a neutral algorithm"}, "concurrent-text")
        challenge = self.call("challenge", {"operation": "approve", "task_id": task["task_id"]})
        signature = self.signed(challenge)
        thread = Thread(target=lambda: self.call("complete", signature, "concurrent-approve"))
        thread.start()
        try:
            self.assertTrue(entered.wait(5))
            inspected = self.call("inspect", {"task_id": task["task_id"]}, "inspect-running")
            self.assertEqual(inspected["state"], TaskState.AWAITING_RESULT)
            cancel = self.call(
                "challenge", {"operation": "cancel", "task_id": task["task_id"]}, "cancel-challenge"
            )
            cancelled = self.call("complete", self.signed(cancel), "cancel-running")
            self.assertEqual(cancelled["state"], TaskState.CANCELLED)
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.h.store.task(task["task_id"]).state, TaskState.CANCELLED)

    def test_crash_after_admission_never_replays_a_mutation(self) -> None:
        from unittest.mock import patch

        with patch.object(self.h.runtime, "create", side_effect=OSError("synthetic interruption")):
            with self.assertRaises(OSError):
                self.call("text", {"text": "2 + 3"}, "crash-admitted")
        restarted = Mobile(self.h.runtime, self.policy, self.core.targets)
        result = restarted.request(
            self.session, self.envelope("text", {"text": "2 + 3"}, "crash-admitted")
        )
        self.assertTrue(result["inspect_required"])
        self.assertTrue(result["replayed"])
        self.assertFalse(self.h.store.all("task"))

    def test_private_session_replacement_discard_and_exact_review(self) -> None:
        self.reasoning_fixture()
        text = "Explain a private-session-sentinel sorting algorithm"
        task = self.call("text", {"text": text}, "private-text")
        task_id = task["task_id"]
        challenge = self.call("challenge", {"operation": "approve", "task_id": task_id})
        self.assertEqual(text, challenge["exact_request"])
        self.assertEqual(text, json.loads(challenge["review"])["prompt"])
        self.assertEqual("control:approve:" + self.h.node_id, challenge["scope"])
        result = self.call("complete", self.signed(challenge), "private-approve")
        self.assertEqual("reported synthetic answer", result["response"])
        durable = str(
            [
                self.h.store.all(table)
                for table in ("objective", "plan", "action", "result", "audit")
            ]
        )
        self.assertNotIn("private-session-sentinel", durable)
        self.assertNotIn("reported synthetic answer", durable)
        planned = self.call("text", {"text": text}, "private-planned")
        origin = self.session
        self.session = self.h.grid.pair(origin.node_id, self.scopes)
        self.core.register_owner_key(
            self.session,
            self.h.store.get("sunday_key", origin.node_id)["public_key"],
            owner_authorized=True,
        )
        shared = self.call("inspect", {"task_id": task_id})
        self.assertNotIn("private-session-sentinel", str(shared))
        self.assertNotIn("response", shared)
        self.assertNotIn(
            "approve", self.call("inspect", {"task_id": planned["task_id"]})["actions"]
        )
        with self.assertRaises(StateConflict):
            self.call("challenge", {"operation": "approve", "task_id": planned["task_id"]})
        denial = self.call("challenge", {"operation": "deny", "task_id": planned["task_id"]})
        self.assertEqual("{}", denial["review"])
        self.assertEqual("", denial["exact_request"])
        self.call("discard", {})
        self.assertIn(task_id, self.h.store.transient)
        self.session = origin
        self.call("discard", {})
        self.assertNotIn(task_id, self.h.store.transient)
        self.assertNotIn(planned["task_id"], self.h.store.transient)
        self.assertEqual(TaskState.PARTIALLY_VERIFIED, self.h.store.task(task_id).state)

    def test_exact_review_bounds_changed_private_payload_and_critical_capability(self) -> None:
        task = self.call("text", {"text": "2 + 3"}, "bounded-text")
        task_id = task["task_id"]
        private = self.h.store.transient[task_id]
        challenge = self.call("challenge", {"operation": "approve", "task_id": task_id})
        private["parameters"] = {"expression": "4 + 5"}
        with self.assertRaises(StateConflict):
            self.call("complete", self.signed(challenge), "private-changed")
        private["parameters"] = {"expression": "漢" * 8192}
        count = len(self.h.store.all("sunday_challenge"))
        with self.assertRaisesRegex(ValueError, "Exact review exceeds"):
            self.call("challenge", {"operation": "approve", "task_id": task_id})
        self.assertEqual(count, len(self.h.store.all("sunday_challenge")))
        private["parameters"] = {"expression": "2 + 3"}
        challenge = self.call("challenge", {"operation": "approve", "task_id": task_id})
        node = self.h.store.get("node", self.h.node_id)
        for capability in node["capabilities"]:
            if capability["id"] == "math.add":
                capability["risk"] = "critical"
        self.h.store.put("node", self.h.node_id, node)
        with self.assertRaisesRegex(PermissionError, "strong approval"):
            self.call("complete", self.signed(challenge), "critical-rejected")
        self.assertEqual([], self.h.store.all("action"))

    def test_follow_up_context_is_core_owned_same_session_and_discardable(self) -> None:
        self.reasoning_fixture()
        task = self.call("text", {"text": "2 + 3"}, "context-first")
        challenge = self.call("challenge", {"operation": "approve", "task_id": task["task_id"]})
        self.call("complete", self.signed(challenge), "context-complete")
        follow_up = self.call("text", {"text": "Explain this arithmetic result"}, "context-follow")
        parameters = self.h.store.transient[follow_up["task_id"]]["parameters"]
        self.assertIn("Previous Core task " + task["task_id"], parameters["prompt"])
        self.assertIn("Result: 5", parameters["prompt"])
        self.assertEqual("private", parameters["mode"])
        original = self.session
        self.session = self.h.grid.pair(original.node_id, tuple(self.core.grants(original)))
        foreign = self.call("text", {"text": "Explain arithmetic"}, "context-foreign")
        self.assertNotIn(
            "Previous Core task", self.h.store.transient[foreign["task_id"]]["parameters"]["prompt"]
        )
        self.session = original
        self.call("discard", {})
        next_task = self.call("text", {"text": "Explain arithmetic"}, "context-after-discard")
        self.assertNotIn(
            "Previous Core task",
            self.h.store.transient[next_task["task_id"]]["parameters"]["prompt"],
        )
        self.assertIn(foreign["task_id"], self.h.store.transient)

    def test_discard_during_mobile_execution_preserves_verification_without_private_result(
        self,
    ) -> None:
        from threading import Event, Thread

        entered, release = Event(), Event()
        executor = self.h.dispatcher.executors["math.add"]

        def held(action, cancellation):
            entered.set()
            self.assertTrue(release.wait(3))
            return executor(action, cancellation)

        self.h.dispatcher.executors["math.add"] = held
        task = self.call("text", {"text": "2 + 3"}, "active-private")
        thread = Thread(target=self.h.runtime.run, args=(task["task_id"], self.core.targets))
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            self.call("discard", {})
            self.assertTrue(self.h.store.transient[task["task_id"]]["discarded"])
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(TaskState.VERIFIED, self.h.store.task(task["task_id"]).state)
        self.assertNotIn(task["task_id"], self.h.store.transient)
        self.assertNotIn("value", self.call("inspect", {"task_id": task["task_id"]}))
