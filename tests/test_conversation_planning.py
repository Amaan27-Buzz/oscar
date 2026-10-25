"""Authenticated conversation, real synthetic HTTP model I/O and independently read files."""

import base64
import json
import sys
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
from oscar.machine import MachineScope, MachineWorker
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_authoring import PlannerAuthoring
from oscar.policy import PersonalPolicy
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.router import Router
from oscar.transport import Dispatcher
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

    def test_explicit_worker_or_device_routes_without_a_goal_verb_allowlist(self):
        for instruction in (
            "Create worker File preparation: First inspect the input file, then prepare an answer",
            "On device "
            + self.h.node_id
            + ": First inspect the input file, then prepare an answer",
            "Across devices "
            + self.h.node_id
            + ": First inspect the input file, then prepare an answer",
        ):
            with self.subTest(instruction=instruction):
                change = self.proposed(instruction)
                self.assertEqual("plan_draft", change["operation"])
                self.assertEqual(
                    "First inspect the input file, then prepare an answer", change["value"]["goal"]
                )
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual([], self.h.store.all("executive_worker"))

    def test_explicit_worker_keeps_memory_and_current_evidence_preflight(self):
        for goal in (
            "Remember what we decided",
            "Check whether the deployment succeeded",
            "What is the current weather?",
        ):
            with self.subTest(goal=goal):
                self.assertIsNone(self.conversation("Create worker Evidence: " + goal))
        self.assertEqual([], self.requests)
        self.assertEqual([], self.h.store.all("task"))

    def test_signed_result_handoff_is_visible_and_uses_actual_output(self):
        self.result_handoff()

    def test_autonomous_named_worker_uses_result_under_current_full_delegation(self):
        planner_fixture.PlannerAuthoringTests.delegate(self, actions=("math.add", "files.write"))
        self.result_handoff(full=True)

    def coding_worker(self):
        self.grants |= frozenset({"machine:host"})
        for kind, identifier in (("session", self.owner.id), ("node", self.owner.node_id)):
            row = self.h.store.get(kind, identifier)
            self.h.store.put(kind, identifier, {**row, "scopes": sorted(self.grants)})
        scopes = ("heartbeat", "advertise", "execute", "cancel", "machine:host")
        self.h.grid.register(Node("coding-device", NodeRole.DESKTOP, scopes))
        session = self.h.grid.pair("coding-device", scopes)
        worker = MachineWorker(
            self.h.store,
            self.h.grid,
            session,
            MachineScope(self.h.files.root, True, (sys.executable,)),
        )
        # Synthetic installed-agent fixture executes real Python, never an authenticated agent.
        worker.agents = {"codex": sys.executable}
        self.h.grid.advertise(
            session, [c for c in worker.capabilities() if c.input_kind == "coding"]
        )
        self.h.executive.targets[session.node_id] = (
            Dispatcher(self.h.store, self.h.grid, session.node_id, worker.executors()),
            session,
        )
        return worker

    def coding_plan(self, criterion):
        self.coding_worker()
        code = (
            "from pathlib import Path; p=Path('executions.txt'); "
            "p.write_text(p.read_text()+'1' if p.exists() else '1'); "
            "Path('coded.txt').write_text('42')"
        )
        self.body["choices"][0]["message"]["content"] = json.dumps(
            {
                "steps": [
                    {
                        "id": "code",
                        "intent": asdict(
                            Intent(
                                "Implement the exact requested file",
                                "capability",
                                capability_kind="coding",
                                parameters={"arguments": ["-c", code], "cwd": ".", "timeout": 20},
                                criterion=criterion,
                            )
                        ),
                        "node_id": "coding-device",
                        "capability_id": "machine.agent.codex",
                        "depends_on": [],
                    }
                ]
            }
        )
        return self.proposed(
            "Create worker Code result: On device coding-device: "
            'Implement coded.txt containing "42"'
        )

    def test_signed_coding_plan_runs_real_process_once_and_reads_exact_artifact(self):
        change = self.coding_plan({"kind": "file_exact", "path": "coded.txt", "content": "42"})
        self.complete(self.review(change))
        self.h.executive.tick()
        self.assertIn("machine.agent.codex", json.dumps(self.requests))
        self.assertFalse((self.h.files.root / "coded.txt").exists())
        review = self.review(self.proposed("Review the plan"))
        self.assertIn("arguments", review["review"])
        self.complete(review)
        self.h.executive.tick()
        self.h.executive.tick()
        self.assertEqual("42", (self.h.files.root / "coded.txt").read_text())
        self.assertEqual("1", (self.h.files.root / "executions.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.assertEqual("Code result", self.h.store.all("executive_worker")[-1]["name"])

    def test_coding_process_success_does_not_verify_an_unknown_objective(self):
        self.complete(self.review(self.coding_plan({"kind": "unavailable"})))
        self.h.executive.tick()
        self.complete(self.review(self.proposed("Review the plan")))
        self.h.executive.tick()
        self.assertEqual("partially_verified", self.h.store.all("task")[-1]["state"])
        self.assertNotEqual("completed", self.h.store.all("executive_goal")[-1]["state"])

    def delegate_coding(self):
        payload = planner_fixture.authority_fixture.StandingAuthorityTests.payload(
            self,
            "full",
            capabilities=[
                {"node_id": node, "session_id": session.id, "capability_id": capability}
                for node, capability in (
                    (self.h.node_id, "models.reason"),
                    ("coding-device", "machine.agent.codex"),
                )
                for session in (self.h.executive.targets[node][1],)
            ],
        )
        review = self.authority.challenge(
            self.owner.node_id, self.owner.id, self.owner_scope, self.grants, payload
        )
        self.authority.complete(
            self.owner.node_id,
            self.owner.id,
            self.public,
            self.owner_scope,
            self.grants,
            self.signature(review),
        )

    def test_coding_worker_runs_autonomously_under_exact_standing_delegation(self):
        self.coding_plan({"kind": "file_exact", "path": "coded.txt", "content": "42"})
        self.delegate_coding()
        response = self.conversation(
            "Create worker Code result: On device coding-device: "
            'Implement coded.txt containing "42"'
        )
        self.assertIn("assistance_started", response)
        for _ in range(4):
            self.h.executive.tick()
        self.assertEqual("42", (self.h.files.root / "coded.txt").read_text())
        self.assertEqual("1", (self.h.files.root / "executions.txt").read_text())
        self.assertEqual("verified", self.h.store.all("task")[-1]["state"])
        self.assertEqual(1, len(self.requests))

    def test_coding_delegation_revoked_after_planning_blocks_process(self):
        self.coding_plan({"kind": "file_exact", "path": "coded.txt", "content": "42"})
        self.delegate_coding()
        self.conversation("On device coding-device: Implement the requested file")
        self.h.executive.tick()
        self.authority.revoke(self.owner.node_id, self.owner.id, self.owner_scope, self.grants)
        for _ in range(3):
            self.h.executive.tick()
        self.assertFalse((self.h.files.root / "executions.txt").exists())
        self.assertEqual("blocked", PlannerAuthoring(self.h).snapshot()[0]["state"])

    def test_coding_parameters_are_validated_before_effect_review(self):
        change = self.coding_plan({"kind": "unavailable"})
        output = json.loads(self.body["choices"][0]["message"]["content"])
        for parameters in (
            {"arguments": "shell code"},
            {"arguments": [None]},
            {"arguments": [], "timeout": 121},
            {"arguments": [], "authority": "full"},
        ):
            with self.subTest(parameters=parameters):
                output["steps"][0]["intent"]["parameters"] = parameters
                self.body["choices"][0]["message"]["content"] = json.dumps(output)
                self.complete(self.review(change))
                self.h.executive.tick()
                row = self.h.store.all("planner_request")[-1]
                self.assertEqual("blocked", self.conversation("Review plan " + row["id"])["state"])
        self.assertFalse((self.h.files.root / "executions.txt").exists())

    def result_handoff(self, full=False):
        steps = [
            {**self.steps[0], "id": "sum", "intent": asdict(Intent("17 + 25"))},
            {
                "id": "save",
                "intent": asdict(Intent("Save verified result", "file_write", "answer.txt", "")),
                "node_id": self.h.node_id,
                "capability_id": "files.write",
                "depends_on": ["sum"],
                "inputs": [{"from_step": "sum", "select": [], "to": ["content"]}],
            },
        ]
        self.body["choices"][0]["message"]["content"] = json.dumps({"steps": steps})
        objective = "Create worker Verified calculation: Calculate 17 + 25, then save its result"
        if full:
            self.assertIn("assistance_started", self.conversation(objective))
        else:
            self.complete(self.review(self.proposed(objective)))
        self.h.executive.tick()
        if not full:
            review = self.review(self.proposed("Review the plan"))
            self.assertIn('"from_step": "sum"', review["review"])
            self.assertFalse((self.h.files.root / "answer.txt").exists())
            self.complete(review)
        self.h.executive.tick()
        self.assertEqual("42", (self.h.files.root / "answer.txt").read_text())
        self.assertEqual(1, len(self.requests))
        worker = self.h.store.all("executive_worker")[-1]
        self.assertEqual("Verified calculation", worker["name"])

    def test_explicit_multiple_devices_pin_all_targets_without_silent_selection(self):
        self.test_unavailable_route_and_ambiguous_device_never_send_input()
        change = self.proposed(
            "Across devices "
            + self.h.node_id
            + ", second-device: Prepare a welcome file on each device"
        )
        self.assertEqual(
            {self.h.node_id, "second-device"},
            {c["node_id"] for c in change["value"]["capabilities"]},
        )
        for devices in ("missing, second-device", "second-device, second-device", "second-device,"):
            self.assertEqual(
                "blocked",
                self.conversation("Across devices " + devices + ": Prepare a welcome file")[
                    "state"
                ],
            )
        self.assertEqual([], self.requests)

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
        self.body["choices"][0]["message"]["content"] = json.dumps({"steps": json.loads(content)})
        self.complete(self.review(self.proposed()))
        self.h.executive.tick()
        prompt = self.requests[-1]["body"]["messages"][-1]["content"]
        self.assertIn('"steps" and optional boolean "observe"', prompt)
        self.assertIn('return {"steps":[...],"observe":true}', prompt)
        self.assertIn("Preserve the chosen example's kind and capability_kind exactly", prompt)
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
        self.remote_workflow()

    def test_authenticated_cross_device_result_handoff(self):
        self.remote_workflow(handoff=True)

    def remote_workflow(self, handoff=False):
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
        if handoff:
            self.body["choices"][0]["message"]["content"] = json.dumps(
                {
                    "steps": [
                        {
                            "id": "sum",
                            "intent": asdict(Intent("17 + 25")),
                            "node_id": h.node_id,
                            "capability_id": "math.add",
                            "depends_on": [],
                        },
                        {
                            "id": "save",
                            "intent": asdict(
                                Intent("Copy actual result", "file_write", "welcome.txt", "")
                            ),
                            "node_id": "test-desktop",
                            "capability_id": "machine.files.write",
                            "depends_on": ["sum"],
                            "inputs": [{"from_step": "sum", "select": [], "to": ["content"]}],
                        },
                    ]
                }
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
        first = ask(
            "Across devices " + h.node_id + ", test-desktop: Calculate 17 + 25, then save result"
            if handoff
            else "On device test-desktop: Prepare a welcome note and save it as welcome.txt"
        )
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
        self.assertEqual("42" if handoff else "Synthetic remote welcome", path.read_text())
        tasks = h.executive._tasks(goal)
        self.assertEqual("verified", h.store.task(tasks[0]).state)
        self.assertTrue(h.store.all("evidence")[-1]["matches"])
        if handoff:
            self.assertEqual(2, len(tasks))
            bindings = [h.store.get("plan", t)["executive"] for t in tasks]
            self.assertEqual({h.node_id, "test-desktop"}, {b["node_id"] for b in bindings})
            copied = next(b for b in bindings if b["step_id"] == "save")
            self.assertIn(copied["inputs"][0]["task_id"], tasks)
        self.assertEqual("blocked", ask("Proceed with the plan")["state"])

    close = provider_fixture.ProviderContractTests.close
