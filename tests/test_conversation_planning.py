"""Authenticated conversation, real synthetic HTTP model I/O and independently read files."""

import base64
import json
import unittest
from dataclasses import asdict, replace
from time import monotonic, sleep

from oscar.contracts import Capability, new_id
from oscar.credentials import CredentialPool
from oscar.desktop import Desktop
from oscar.event_archive import SourceEvent
from oscar.grid import Node, NodeRole
from oscar.harness import ModelExecutor
from oscar.jev import Intent
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_authoring import PlannerAuthoring
from oscar.policy import PersonalPolicy
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.router import Router
from tests import test_planner_authoring as planner_fixture
from tests import test_providers as provider_fixture
from tests import test_remote_grid as remote_fixture


class ConversationPlanningTests(unittest.TestCase):
    setUp = planner_fixture.PlannerAuthoringTests.setUp
    close = planner_fixture.PlannerAuthoringTests.close
    signature = planner_fixture.PlannerAuthoringTests.signature
    review = planner_fixture.PlannerAuthoringTests.review
    complete = planner_fixture.PlannerAuthoringTests.complete

    def conversation(self, text):
        return PlannerAuthoring(self.h).conversation(
            text, self.owner.node_id, self.owner.id, self.owner_scope, self.grants
        )

    def proposed(self, text="Prepare a short welcome note and save it as welcome.txt"):
        return self.conversation(text)["assistance_proposal"]

    def file_result(self):
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    "id": "save",
                    "intent": asdict(
                        Intent(
                            "Save the synthetic welcome",
                            "file_write",
                            "welcome.txt",
                            "Welcome to OSCAR",
                        )
                    ),
                    "node_id": self.h.node_id,
                    "capability_id": "files.write",
                    "depends_on": [],
                }
            ]
        )

    def draft(self):
        self.file_result()
        change = self.proposed()
        self.complete(self.review(change))
        self.h.executive.tick()
        return self.h.store.all("planner_request")[-1]

    def test_unsigned_input_and_effect_reviews_make_no_calls_or_effects_until_signed(self):
        self.file_result()
        marker = "Unselected synthetic conversation and memory must remain private"
        self.h.archive.append(
            SourceEvent(self.h.runtime.relationship_id, marker, "synthetic-history", self.now),
            retain_authorized=True,
        )
        first = self.proposed()
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("task"))
        reviewed = self.review(first)
        self.assertIn("intent_examples", reviewed["review"])
        self.assertIn("Only this goal", reviewed["review"])
        self.assertEqual([], self.requests)  # Declining the privacy review sends nothing.
        self.complete(reviewed)
        self.h.executive.tick()
        self.assertEqual(1, len(self.requests))
        self.assertNotIn(marker, json.dumps(self.requests))
        path = self.h.files.root / "welcome.txt"
        second = self.proposed("Proceed with the plan")
        self.assertEqual("plan_accept", second["operation"])
        self.assertFalse(path.exists())
        reviewed_effects = self.review(second)
        self.h.executive.tick()
        self.assertFalse(path.exists())  # Declining effects leaves only the model proposal.
        self.complete(reviewed_effects)
        self.h.executive.tick()
        self.assertEqual("Welcome to OSCAR", path.read_text())
        task = self.h.store.all("task")[-1]
        self.assertEqual("verified", task["state"])
        self.assertEqual("blocked", self.conversation("Proceed with the plan")["state"])
        with self.assertRaises(PermissionError):
            self.complete(reviewed_effects)

    def test_compound_arithmetic_enters_review_but_simple_arithmetic_keeps_fast_path(self):
        self.assertIsNone(self.conversation("Calculate 17 + 25"))
        proposal = self.proposed('Calculate 17 + 25, then create welcome.txt containing "42"')
        self.assertEqual("plan_draft", proposal["operation"])
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("task"))
        self.assertFalse((self.h.files.root / "welcome.txt").exists())

    def test_followup_resolves_persisted_current_owner_session_and_declines_other_session(self):
        row = self.draft()
        # A new service object reconstructs the reference from canonical state.
        self.assertEqual(row["id"], self.proposed("Review the plan")["id"])
        self.h.store.put(
            "executive_owner",
            row["goal_id"],
            {**self.h.store.get("executive_owner", row["goal_id"]), "session": "another-session"},
        )
        self.assertEqual("blocked", self.conversation("Review the plan")["state"])
        self.assertEqual(1, len(self.requests))
        self.assertFalse((self.h.files.root / "welcome.txt").exists())

    def test_object_plan_envelope_matches_json_mode_and_still_requires_effect_review(self):
        self.file_result()
        content = self.body["choices"][0]["message"]["content"]
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {"steps": json.loads(content)}
        )
        self.complete(self.review(self.proposed()))
        self.h.executive.tick()
        prompt = self.requests[-1]["body"]["messages"][-1]["content"]
        self.assertIn('exactly one key, "steps"', prompt)
        self.assertIn('"steps": [{', prompt)
        change = self.proposed("Review the plan")
        path = self.h.files.root / "welcome.txt"
        self.assertFalse(path.exists())
        self.complete(self.review(change))
        self.h.executive.tick()
        self.assertEqual("Welcome to OSCAR", path.read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])

    def test_object_plan_envelope_rejects_extra_keys_and_untyped_steps(self):
        self.draft()
        task_id = self.h.store.all("task")[0]["id"]
        result = next(r for r in self.h.store.all("result") if r["task_id"] == task_id)
        for value in (
            {"steps": [], "authority": "full"},
            {"steps": [], "clarification": "also execute"},
            {"steps": {"id": "save"}},
            {"steps": ["save"]},
        ):
            with self.subTest(value=value):
                self.h.store.put("result", result["id"], {**result, "value": json.dumps(value)})
                with self.assertRaisesRegex(ValueError, "typed step array"):
                    self.h.executive.result_steps(task_id)
        self.assertFalse((self.h.files.root / "welcome.txt").exists())

    def test_failed_planning_explains_recovery_without_retries_and_new_review_can_succeed(self):
        self.body["choices"][0]["message"]["content"] = ""
        self.complete(self.review(self.proposed()))
        self.h.executive.tick()
        count = len(self.requests)
        for _ in range(2):
            response = self.conversation("Review the plan")
            self.assertEqual("blocked", response["state"])
            self.assertIn("request a new draft", response["message"])
            self.assertIn("No proposed action was accepted", response["message"])
        self.assertEqual(count, len(self.requests))
        self.assertFalse((self.h.files.root / "welcome.txt").exists())
        self.file_result()
        self.assertEqual("blocked", self.conversation("Prepare a welcome file")["state"])
        self.now = max(r["until"] for r in self.h.store.all("route_health")) + 1
        self.h.grid.heartbeat(self.h.session)
        self.h.grid.heartbeat(self.owner)
        change = self.proposed()
        self.assertEqual(count, len(self.requests))
        self.complete(self.review(change))
        self.h.executive.tick()
        row = self.h.store.all("planner_request")[-1]
        effects = self.proposed("Review plan " + row["id"])
        self.assertFalse((self.h.files.root / "welcome.txt").exists())
        self.complete(self.review(effects))
        self.h.executive.tick()
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "welcome.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])

    def test_malformed_plan_guidance_never_echoes_model_content_or_executes_it(self):
        self.body["choices"][0]["message"]["content"] = "Private malformed model marker"
        self.complete(self.review(self.proposed()))
        self.h.executive.tick()
        response = self.conversation("Review the plan")
        self.assertEqual("blocked", response["state"])
        self.assertIn("Request a new draft", response["message"])
        self.assertNotIn("Private malformed model marker", response["message"])
        self.assertFalse((self.h.files.root / "welcome.txt").exists())

    def test_multiple_plans_require_exact_reference_and_revocation_denies_it(self):
        first = self.draft()
        self.draft()
        self.assertEqual("blocked", self.conversation("Review the plan")["state"])
        self.assertEqual(first["id"], self.proposed("Review plan " + first["id"])["id"])
        session = self.h.store.get("session", self.owner.id)
        self.h.store.put("session", self.owner.id, {**session, "revoked": True})
        self.assertEqual("blocked", self.conversation("Review plan " + first["id"])["state"])

    def test_unavailable_route_and_ambiguous_device_never_send_input(self):
        self.executor.router.pool.slots["synthetic"].present = False
        self.assertEqual("blocked", self.conversation("Prepare a welcome file")["state"])
        self.assertEqual([], self.requests)
        self.executor.router.pool.slots["synthetic"].present = True
        self.h.grid.register(
            Node(
                "second-device",
                NodeRole.DESKTOP,
                ("heartbeat", "advertise", "execute", "files:write"),
            )
        )
        session = self.h.grid.pair(
            "second-device", ("heartbeat", "advertise", "execute", "files:write")
        )
        cap = Capability(
            "second.write",
            "Save file",
            "Exact file",
            "deterministic",
            session.node_id,
            ("files:write",),
            "file_write",
            "file",
        )
        self.h.grid.advertise(session, [cap])
        self.h.executive.targets[session.node_id] = (self.h.dispatcher, session)
        self.assertIn(
            "Choose an action device", self.conversation("Prepare a welcome file")["message"]
        )
        change = self.proposed("On device " + self.h.node_id + ": Prepare a welcome file")
        self.assertTrue(
            all(c["node_id"] == self.h.node_id for c in change["value"]["capabilities"])
        )
        self.assertEqual([], self.requests)

    def test_memory_and_freshness_stay_controller_routed_and_accounts_require_details(self):
        for text in (
            "2 + 3",
            "What did we decide?",
            "Prepare the same report as last time",
            "Prepare a report about the current weather",
            "Explain how a compiler works",
        ):
            with self.subTest(text=text):
                self.assertIsNone(self.conversation(text))
        result = self.conversation("Send a message to the university account")
        self.assertEqual("blocked", result["state"])
        self.assertIn("exact available account", result["message"])
        self.assertEqual([], self.requests)

    def test_untrusted_output_missing_information_and_escalation_never_execute(self):
        for output in (
            '{"clarification":"Which destination account?"}',
            '{"authority":"full"}',
            json.dumps([{**self.steps[0], "node_id": "unapproved-device"}]),
        ):
            with self.subTest(output=output):
                self.body["choices"][0]["message"]["content"] = output
                self.complete(self.review(self.proposed("Prepare a separate welcome file")))
                self.h.executive.tick()
                row = self.h.store.all("planner_request")[-1]
                result = self.conversation("Review plan " + row["id"])
                self.assertEqual("blocked", result["state"])
        self.assertFalse((self.h.files.root / "welcome.txt").exists())

    def test_model_step_field_types_are_rejected_before_lookups(self):
        bad_steps = [
            {**self.steps[0], "id": 1, "depends_on": None},
            {**self.steps[0], "depends_on": [{}]},
            {**self.steps[0], "intent": {"text": "save", "kind": []}},
            {**self.steps[0], "intent": {"text": "save", "unknown_authority": True}},
        ]
        for step in bad_steps:
            with self.subTest(step=step):
                self.body["choices"][0]["message"]["content"] = json.dumps([step])
                self.complete(self.review(self.proposed("Prepare a separate welcome file")))
                self.h.executive.tick()
                row = self.h.store.all("planner_request")[-1]
                self.assertEqual("blocked", self.conversation("Review plan " + row["id"])["state"])
        self.assertFalse((self.h.files.root / "welcome.txt").exists())

    def test_authenticated_desktop_conversation_opens_both_existing_reviews(self):
        self.file_result()
        scope = "control:approve:" + self.h.node_id
        self.owner_scope = scope
        self.grants |= frozenset({scope, "desktop:connect", "desktop:text"})
        for kind, identifier in (("node", self.owner.node_id), ("session", self.owner.id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(
                kind,
                identifier,
                {
                    **row,
                    "scopes": sorted(self.grants),
                    **({"role": NodeRole.DESKTOP} if kind == "node" else {}),
                },
            )
        desktop = Desktop(self.h.runtime, PersonalPolicy(self.h.store), self.h.executive.targets)

        def call(operation, payload):
            return desktop.request(
                self.owner,
                {"version": 1, "operation": operation, "request_id": new_id(), "payload": payload},
            )

        def ask(text):
            return call("interact", {"mode": "Ask", "text": text, "context_id": ""})

        first = ask("Prepare a short welcome note and save it as welcome.txt")[
            "assistance_proposal"
        ]
        self.assertEqual([], self.requests)
        review = call("assistance_challenge", first)
        call("assistance_complete", self.signature(review))
        self.h.executive.tick()
        second = ask("Review the plan")["assistance_proposal"]
        self.assertEqual("plan_accept", second["operation"])
        review = call("assistance_challenge", second)
        call("assistance_complete", self.signature(review))
        self.h.executive.tick()
        self.assertEqual("Welcome to OSCAR", (self.h.files.root / "welcome.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])


class RemoteConversationPlanningTests(unittest.TestCase):
    setUp = remote_fixture.RemoteGridTests.setUp
    tearDown = remote_fixture.RemoteGridTests.tearDown
    invitation = remote_fixture.RemoteGridTests.invitation
    enroll = remote_fixture.RemoteGridTests.enroll

    def test_authenticated_remote_conversation_model_and_signed_file_effect(self):
        h = self.core.harness
        provider_fixture.ProviderContractTests.setUp(self)
        provider = replace(self.provider, credential_envs={"synthetic": "SYNTHETIC_PLANNER"})
        model = ModelSpec(
            "fixture",
            "fixture-model",
            frozenset({"text"}),
            2,
            {"reasoning": 1},
            8192,
            4096,
            Funding.FREE,
            provenance="synthetic HTTP fixture",
        )
        pool = CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic-key"}, h.store)
        executor = ModelExecutor(
            Router(Registry([provider], [model]), pool, {"openai": HTTPAdapter("openai")}, h.store),
            ModelRequest("template", "template", "", max_output_tokens=2048),
            RoutingPolicy(),
        )
        h.dispatcher.executors["models.reason"] = executor
        self.body["choices"][0]["message"]["content"] = json.dumps(
            [
                {
                    "id": "save",
                    "intent": asdict(
                        Intent(
                            "Save welcome", "file_write", "welcome.txt", "Synthetic remote welcome"
                        )
                    ),
                    "node_id": "test-desktop",
                    "capability_id": "machine.files.write",
                    "depends_on": [],
                }
            ]
        )

        def ask(text):
            return self.mobile.request(
                "submit",
                {
                    "text": text,
                    "kind": "text",
                    "target": h.node_id,
                    "parameters": {},
                    "retain": True,
                },
            )

        def approve(change):
            review = self.mobile.request("assistance_challenge", change)
            return self.mobile.request(
                "assistance_complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": remote_fixture.signature(
                        self.owner_key, base64.b64decode(review["signing_payload"])
                    ),
                },
            )

        self.assertEqual("blocked", ask("Prepare a welcome note and save it")["state"])
        first = ask("On device test-desktop: Prepare a welcome note and save it as welcome.txt")
        self.assertEqual([], self.requests)
        approve(first["assistance_proposal"])
        until = monotonic() + 8
        while monotonic() < until and not self.requests:
            h.executive.tick()
            sleep(0.02)
        self.assertEqual(1, len(self.requests))
        second = ask("Proceed with the plan")["assistance_proposal"]
        path = self.workspace / "welcome.txt"
        self.assertFalse(path.exists())
        approve(second)
        goal = h.store.all("planner_request")[0]["accepted_goal"]
        until = monotonic() + 8
        while monotonic() < until:
            self.worker.step()
            if h.store.get("executive_goal", goal)["state"] == "completed":
                break
            sleep(0.02)
        self.assertEqual("Synthetic remote welcome", path.read_text())
        tasks = h.executive._tasks(goal)
        self.assertEqual("verified", h.store.task(tasks[0]).state)
        self.assertTrue(h.store.all("evidence")[-1]["matches"])
        self.assertEqual("blocked", ask("Proceed with the plan")["state"])

    close = provider_fixture.ProviderContractTests.close
