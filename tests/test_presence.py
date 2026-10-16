import copy
import unittest

from oscar.adaptive import task_view, validate_view
from oscar.contracts import TaskState, new_id
from oscar.credentials import CredentialPool
from oscar.grid import Node, NodeRole
from oscar.mobile import Mobile
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.presence import PresenceRuntime
from oscar.setup_runtime import SetupRuntime
from tests.support import Rig


class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.r.runtime.presence = PresenceRuntime(self.r.runtime)
        self.core = Mobile(self.r.runtime, PersonalPolicy(self.r.store), self.r.transports)
        scopes = ("heartbeat", "mobile:connect", "presence:read")
        self.r.grid.register(Node("projection", NodeRole.MOBILE, scopes))
        self.session = self.r.grid.pair("projection", scopes)

    def tearDown(self):
        self.r.close()

    def read(self):
        return self.core.request(
            self.session,
            {"version": 1, "request_id": new_id(), "operation": "presence", "payload": {}},
        )

    def test_canonical_shared_state_and_generation_survive_restart(self):
        task = self.r.file_task()
        first = self.read()["expression"]
        self.assertEqual("waiting", first["operation"])
        self.r.store.transition(task.id, TaskState.EXECUTING)
        self.r.grid.lease(task.id, "test-node")
        other = PresenceRuntime(self.r.runtime).snapshot()["expression"]
        self.assertEqual(first["source"], other["source"])
        self.assertGreater(other["generation"], first["generation"])
        self.assertEqual("executing", other["operation"])
        self.assertEqual(30_000, other["expiresAt"] - other["eventTime"])
        self.assertNotIn(task.id, str(other))
        self.assertNotIn("tasks", self.read())
        self.r.clock.now += 31
        self.assertEqual("unknown", self.read()["expression"]["operation"])

    def test_revocation_policy_and_relationship_filtering(self):
        self.r.file_task()
        self.r.runtime.relationship_id = "other"
        self.assertEqual("idle", self.read()["expression"]["operation"])
        now = self.r.clock()
        self.core.policy.save(
            PolicyRule("hide", "core.presence.read", PolicyEffect.DENY, "owner", now, now, {}),
            owner_authorized=True,
        )
        with self.assertRaises(PermissionError):
            self.read()

    def test_current_node_scope_removal_hides_presence(self):
        node = self.r.store.get("node", self.session.node_id)
        self.r.store.put(
            "node", self.session.node_id, {**node, "scopes": ["heartbeat", "mobile:connect"]}
        )
        with self.assertRaises(PermissionError):
            self.read()
        self.r.grid.revoke(self.session.node_id)
        with self.assertRaises(PermissionError):
            self.read()

    def test_preferences_change_presentation_without_operational_claim(self):
        self.r.runtime.setup = SetupRuntime(self.r.runtime, CredentialPool([], environ={}))
        self.r.runtime.setup.configure(
            "preferences", {"reduced_motion": True, "show_presence": False}, owner_authorized=True
        )
        view = self.read()
        self.assertFalse(view["visible"])
        self.assertTrue(view["expression"]["reducedMotion"])
        self.assertEqual("idle", view["expression"]["operation"])

    def test_adaptive_schema_negotiation_and_no_authority(self):
        task = {
            "task_id": new_id(),
            "state": "verified",
            "generation": 2,
            "evidence_ids": [new_id()],
        }
        view = task_view(task, 1000, ["result_evidence"])
        self.assertEqual("result_evidence", view["components"][0]["type"])
        self.assertEqual("prose", task_view(task, 1000, ["unsupported"])["components"][0]["type"])
        for change in (
            {"script": "execute()"},
            {"version": 2},
            {"expires_at_ms": 99_000},
            {"actions": [{"type": "approve", "task_id": task["task_id"]}]},
        ):
            with self.assertRaises(ValueError):
                validate_view({**view, **change})
        invalid = copy.deepcopy(view)
        invalid["components"][0]["type"] = "webview"
        with self.assertRaises(ValueError):
            validate_view(invalid)
        self.assertEqual([], self.r.store.all("task"))
