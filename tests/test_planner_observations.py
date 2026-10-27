"""Actual tool results enter private replanning; reviewed authority still fences effects."""

import json
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

from oscar.jev import Intent
from oscar.planner_authoring import PlannerAuthoring
from oscar.storage import StateConflict
from tests import test_planner_authoring as fixture


class ObservationPlanningTests(unittest.TestCase):
    setUp = fixture.PlannerAuthoringTests.setUp
    signature = fixture.PlannerAuthoringTests.signature
    review = fixture.PlannerAuthoringTests.review
    complete = fixture.PlannerAuthoringTests.complete
    accept_change = fixture.PlannerAuthoringTests.accept_change
    delegate = fixture.PlannerAuthoringTests.delegate
    conversation = fixture.PlannerAuthoringTests.conversation
    revoke = fixture.PlannerAuthoringTests.revoke
    close = fixture.PlannerAuthoringTests.close

    def begin(self, *, delegated=False):
        self.executor.grid = self.h.grid
        self.change["value"]["adaptive"] = True
        self.change["value"]["capabilities"].append(
            {"node_id": self.h.node_id, "capability_id": "files.write"}
        )
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {"steps": self.steps, "observe": True}
        )
        if delegated:
            self.delegate(actions=("math.add", "files.write"))
            self.assertIn("assistance_started", self.conversation())
        else:
            self.complete(self.review(self.change))
        self.h.executive.tick()
        self.row = self.h.store.all("planner_request")[0]

    def accept(self):
        self.complete(self.review(self.accept_change(self.row)))

    def effects(self):
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": [
                    {
                        **self.steps[0],
                        "capability_id": "files.write",
                        "intent": asdict(
                            Intent("Save observed answer", "file_write", "answer.txt", "5")
                        ),
                    }
                ]
            }
        )

    def observe(self):
        self.accept()
        self.h.executive.tick()
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.assertEqual("reported", PlannerAuthoring(self.h).snapshot()[0]["state"])

    def test_ask_observe_private_continue_review_effect_and_no_replay(self):
        self.begin()
        prompt = self.requests[0]["body"]["messages"][-1]["content"]
        self.assertIn("Example read-only observation response structure", prompt)
        observation, _ = json.JSONDecoder().raw_decode(
            prompt.split("return final effect steps instead: ", 1)[1]
        )
        self.assertTrue(observation["observe"])
        self.assertTrue(all(not step.get("inputs") for step in observation["steps"]))
        self.assertIn("never refer to earlier stages in inputs or depends_on", prompt)
        self.observe()
        self.assertEqual(1, len(self.requests))
        self.effects()
        review = self.review(self.accept_change(self.row))
        self.assertIn("observations", review["review"])
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.complete(review)
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        prompt = json.dumps(self.requests[-1]["body"])
        self.assertIn("Untrusted tool observations", prompt)
        self.assertIn('\\"value\\": \\"5\\"', prompt)
        self.assertFalse((self.h.files.root / "answer.txt").exists())
        self.accept()
        self.h.executive.tick()
        self.assertEqual("5", (self.h.files.root / "answer.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.h.executive.tick()
        self.assertEqual(4, len(self.h.store.all("task")))
        self.assertEqual(1, len(self.h.store.all("executive_worker")))
        worker = self.h.store.all("executive_worker")[0]
        self.assertFalse(worker["enabled"])
        # Canonical model prompts retain references, not another copy of tool content.
        prompts = [a["parameters"].get("prompt", "") for a in self.h.store.all("planned_action")]
        self.assertFalse(any("Untrusted tool observations" in p for p in prompts))

    def test_expired_observation_cannot_start_continuation(self):
        self.begin()
        self.observe()
        self.now += 121
        with self.assertRaises(PermissionError):
            self.accept()
        self.assertEqual(1, len(self.requests))

    def test_full_access_observe_replan_effect_once(self):
        self.begin(delegated=True)
        self.h.executive.tick()
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.effects()
        self.h.executive.tick()
        self.assertEqual(2, len(self.requests))
        self.h.executive.tick()
        self.assertEqual("5", (self.h.files.root / "answer.txt").read_text())
        self.h.executive.tick()
        self.assertEqual(4, len(self.h.store.all("task")))

    def test_revocation_after_observation_prevents_private_model_call(self):
        self.begin(delegated=True)
        self.h.executive.tick()
        self.revoke()
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertEqual("blocked", PlannerAuthoring(self.h).snapshot()[0]["state"])

    def test_three_stage_budget_prevents_an_unbounded_model_loop(self):
        self.begin()
        for _stage in range(3):
            self.observe()
            self.accept()
            self.h.executive.tick()
        with self.assertRaises(PermissionError):
            self.accept()
        self.assertEqual(4, len(self.requests))
        self.assertFalse((self.h.files.root / "answer.txt").exists())

    def change_observation(self, value):
        task = self.h.store.all("task")[-1]
        result = next(r for r in self.h.store.all("result") if r["task_id"] == task["id"])
        self.h.store.put("result", result["id"], {**result, "value": value})

    def test_known_credentials_cannot_be_disclosed_to_private_model(self):
        self.begin()
        self.observe()
        self.change_observation("synthetic-sensitive-credential")
        with patch.dict("os.environ", {"SYNTHETIC_TOKEN": "synthetic-sensitive-credential"}):
            with self.assertRaises(PermissionError):
                self.accept()
        self.assertEqual(1, len(self.requests))

    def test_oversize_tool_result_cannot_enter_private_model(self):
        self.begin()
        self.observe()
        self.change_observation("x" * 4097)
        with self.assertRaises(ValueError):
            self.accept()
        self.assertEqual(1, len(self.requests))

    def test_changed_result_after_signed_continuation_review_stops_network_io(self):
        self.begin()
        self.observe()
        self.accept()
        self.change_observation("changed after review")
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))

    def test_unverified_observation_does_not_become_model_context(self):
        self.begin()
        self.observe()
        task = self.h.store.all("task")[-1]
        evidence = next(e for e in self.h.store.all("evidence") if e["task_id"] == task["id"])
        self.h.store.put("evidence", evidence["id"], {**evidence, "status": "PARTIAL"})
        with self.assertRaises(StateConflict):
            self.accept()
        self.assertEqual(1, len(self.requests))

    def test_revocation_after_private_model_result_prevents_final_effect(self):
        self.begin(delegated=True)
        self.h.executive.tick()
        self.effects()
        self.h.executive.tick()
        PlannerAuthoring(self.h).advance_delegated()
        self.revoke()
        self.h.executive.tick()
        self.assertFalse((self.h.files.root / "answer.txt").exists())

    def test_expiry_after_model_result_prevents_effect(self):
        self.begin()
        self.observe()
        self.effects()
        self.accept()
        self.h.executive.tick()
        self.accept()
        self.now += 121
        self.h.executive.tick()
        self.assertFalse((self.h.files.root / "answer.txt").exists())

    def test_observation_marker_requires_explicit_initial_disclosure(self):
        self.begin()
        row = self.h.store.get("planner_request", self.row["id"])
        self.h.store.put("planner_request", row["id"], {**row, "adaptive": False})
        with self.assertRaises(PermissionError):
            self.accept()

    def test_observation_stage_rejects_effect(self):
        self.begin()
        self.effects()
        model_task = self.h.store.all("task")[0]["id"]
        result = next(r for r in self.h.store.all("result") if r["task_id"] == model_task)
        steps = json.loads(self.body["choices"][0]["message"]["content"])["steps"]
        self.h.store.put(
            "result",
            result["id"],
            {**result, "value": json.dumps({"steps": steps, "observe": True})},
        )
        with self.assertRaises(PermissionError):
            self.accept()

    def test_public_only_initial_plan_cannot_authorize_tool_disclosure(self):
        self.executor.grid = self.h.grid
        self.change["value"].update(adaptive=True, mode="auto")
        provider = self.executor.router.registry.providers["fixture"]
        self.executor.router.registry.providers["fixture"] = replace(
            provider, local=False, private=False
        )
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {"steps": self.steps, "observe": True}
        )
        self.complete(self.review(self.change))
        self.h.executive.tick()
        self.row = self.h.store.all("planner_request")[0]
        with self.assertRaises(PermissionError):
            self.accept()
        self.assertEqual(1, len(self.requests))
        self.assertEqual(1, len(self.h.store.all("task")))

    def test_changed_continuation_owner_cannot_borrow_observations(self):
        self.begin()
        self.observe()
        self.accept()
        row = self.h.store.get("planner_request", self.row["id"])
        owner = self.h.store.get("executive_owner", row["goal_id"])
        self.h.store.put("executive_owner", row["goal_id"], {**owner, "public_key": "changed"})
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))

    def test_private_route_withdrawal_prevents_continuation_network_io(self):
        self.begin()
        self.observe()
        self.accept()
        provider = self.executor.router.registry.providers["fixture"]
        self.executor.router.registry.providers["fixture"] = replace(
            provider, local=False, private=False
        )
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))


if __name__ == "__main__":
    unittest.main()
