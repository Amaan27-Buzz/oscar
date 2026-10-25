"""Anonymous static reads inform private plans without browser effect authority."""

import base64
import importlib.util
import json
import unittest
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import monotonic, sleep

from oscar.browser_worker import run, static_observation
from oscar.credentials import CredentialPool
from oscar.harness import ModelExecutor
from oscar.jev import Intent
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_observations import validate_stage
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.remote_machine import machine_readback, validate_remote_machine
from oscar.router import Router
from tests import test_providers as provider_fixture
from tests import test_remote_machine as machine_fixture
from tests.test_remote_grid import signature


def parameters(origin):
    return {
        "request": {
            "read_only": True,
            "origins": [origin],
            "timeout": 15,
            "max_text": 2048,
            "steps": [
                {"operation": "navigate", "url": origin + "/article"},
                {"operation": "inspect"},
            ],
        }
    }


def observation(value):
    return {
        "id": "read",
        "node_id": "test-machine",
        "capability_id": "machine.browser",
        "depends_on": [],
        "intent": asdict(
            Intent(
                "Read the scoped public article",
                "capability",
                capability_kind="browser",
                parameters=value,
                criterion={"kind": "unavailable"},
            )
        ),
    }


class BrowserObservationContractTests(unittest.TestCase):
    def test_only_bounded_anonymous_static_read_can_feed_an_observation(self):
        value = parameters("https://example.com")
        self.assertTrue(static_observation(value))
        validate_stage([observation(value)])
        self.assertEqual(value, machine_readback("machine.browser", value))
        for change in (
            {"read_only": False},
            {"timeout": 16},
            {"max_text": 2049},
            {"origins": ["https://example.com", "https://other.example"]},
            {
                "steps": [
                    {"operation": "navigate", "url": "https://example.com"},
                    {"operation": "click", "selector": "button"},
                ]
            },
        ):
            with self.subTest(change=change), self.assertRaises((ValueError, PermissionError)):
                validate_stage([observation({"request": {**value["request"], **change}})])
        for extra in (
            {"account_id": "private", "account_generation": 1},
            {
                "verification": {
                    "url": "https://example.com",
                    "selector": "body",
                    "text": "unrequested",
                }
            },
        ):
            invalid = {**value, **extra}
            self.assertFalse(static_observation(invalid))
            with self.assertRaises(ValueError):
                validate_remote_machine("browser", invalid)


@unittest.skipUnless(importlib.util.find_spec("playwright"), "optional installed Chromium")
class BrowserObservationTests(unittest.TestCase):
    setUp = machine_fixture.RemoteMachineExecutionTests.setUp
    enroll = machine_fixture.RemoteMachineExecutionTests.enroll
    start_worker = machine_fixture.RemoteMachineExecutionTests.start_worker
    submit = machine_fixture.RemoteMachineExecutionTests.submit
    approve = machine_fixture.RemoteMachineExecutionTests.approve
    finish = machine_fixture.RemoteMachineExecutionTests.finish

    def web(self, *, changing=False):
        self.reads, self.posts = [], []
        case = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/article":
                    self.send_response(404)
                    self.end_headers()
                    return
                case.reads.append(self.path)
                text = (
                    "Changed article" if changing and len(case.reads) > 1 else "Source token 4827"
                )
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    (
                        "<html><title>Public fixture</title><body>"
                        + text
                        + "<script>fetch('/effect',{method:'POST'})</script>"
                        "</body></html>"
                    ).encode()
                )

            def do_POST(self):
                case.posts.append(self.path)
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        Thread(target=server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{server.server_port}"

    def test_static_context_disables_page_script_and_marks_incomplete_text(self):
        origin = self.web()
        request = parameters(origin)["request"]
        report = run(request, self.workspace)["observations"][0]
        self.assertEqual("Source token 4827 ", report["text"])
        self.assertFalse(report["truncated"])
        self.assertEqual([], self.posts)
        short = {**request, "max_text": 8}
        self.assertTrue(run(short, self.workspace)["observations"][0]["truncated"])
        with self.assertRaises(PermissionError):
            run(request, self.workspace, profile=self.root / "private-profile")
        self.assertFalse((self.root / "private-profile").exists())

    def test_separate_browser_readback_rejects_changed_page_without_disclosure(self):
        origin = self.web(changing=True)
        self.start_worker(("machine.browser",), browser=True)
        task = self.submit("browser", parameters(origin))
        self.approve(task)
        self.assertEqual("failed", self.finish(task)["state"])
        self.assertEqual(2, len(self.reads))
        self.assertEqual([], self.posts)

    def test_signed_browser_observation_private_continue_and_verified_output(self):
        self.workflow()

    def test_full_delegation_observes_replans_and_writes_without_action_reviews(self):
        self.workflow(full=True)

    def workflow(self, full=False):
        origin = self.web()
        self.start_worker(("machine.browser", "machine.files.write"), browser=True)
        fixture = provider_fixture.ProviderContractTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        h = self.core.harness
        provider = replace(fixture.provider, credential_envs={"synthetic": "SYNTHETIC_PLANNER"})
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
        h.dispatcher.executors["models.reason"] = ModelExecutor(
            Router(
                Registry([provider], [model]),
                CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic-key"}, h.store),
                {"openai": HTTPAdapter("openai")},
                h.store,
            ),
            ModelRequest("template", "template", ""),
            RoutingPolicy(),
            grid=h.grid,
        )
        if full:
            from oscar.policy import PersonalPolicy

            review = self.owner.request(
                "authority_challenge",
                {
                    "mode": "full",
                    "lifetime_seconds": 600,
                    "account_ids": [],
                    "capabilities": [
                        {"node_id": session.node_id, "session_id": session.id, "capability_id": cap}
                        for session, cap in (
                            (self.desktop.handle, "machine.browser"),
                            (self.desktop.handle, "machine.files.write"),
                            (h.session, "models.reason"),
                        )
                    ],
                    "resolve_ask_rules": sorted(
                        r.id
                        for r in PersonalPolicy(h.store).rules()
                        if r.enabled and r.effect == "ask"
                    ),
                },
            )
            self.owner.request(
                "authority_complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": signature(
                        self.owner_key, base64.b64decode(review["signing_payload"])
                    ),
                },
            )
        final = {
            **observation(parameters(origin)),
            "id": "save",
            "capability_id": "machine.files.write",
            "intent": asdict(Intent("Save observed token", "file_write", "article.txt", "4827")),
        }
        fixture.scheduled = [
            (
                200,
                {
                    **fixture.body,
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {"steps": [observation(parameters(origin))], "observe": True}
                                )
                            }
                        }
                    ],
                },
            ),
            (
                200,
                {
                    **fixture.body,
                    "choices": [{"message": {"content": json.dumps({"steps": [final]})}}],
                },
            ),
        ]

        def ask(text):
            return self.owner.request(
                "submit",
                {
                    "text": text,
                    "kind": "text",
                    "target": h.node_id,
                    "parameters": {},
                    "retain": True,
                },
            )

        def accept(change):
            review = self.owner.request("assistance_challenge", change)
            self.owner.request(
                "assistance_complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": signature(
                        self.owner_key, base64.b64decode(review["signing_payload"])
                    ),
                },
            )

        def wait(predicate):
            deadline = monotonic() + 15
            while monotonic() < deadline:
                self.worker.step()
                if predicate():
                    return
                sleep(0.02)
            self.fail("canonical browser stage did not reach expected state")

        def model_ready():
            rows = h.store.all("planner_request")
            tasks = h.executive._tasks(rows[0]["goal_id"]) if rows else []
            return tasks and h.store.task(tasks[0]).state == "partially_verified"

        first = ask(
            "Create worker Article: On device test-machine: "
            "First read " + origin + "/article, then save its source token as article.txt"
        )
        self.assertEqual([], fixture.requests)
        if full:
            self.assertEqual("full", first["assistance_started"]["mode"])
            wait(
                lambda: h.store.all("planner_request")
                and h.store.all("planner_request")[0].get("accepted_goal")
            )
        else:
            accept(first["assistance_proposal"])
            wait(model_ready)
            accept(ask("Proceed with the plan")["assistance_proposal"])
            wait(
                lambda: h.store.get(
                    "executive_goal", h.store.all("planner_request")[0]["observation_goal"]
                )["state"]
                == "completed"
            )
            self.assertEqual(1, len(fixture.requests))
            accept(ask("Proceed with the plan")["assistance_proposal"])
            wait(lambda: len(fixture.requests) == 2 and model_ready())
        self.assertIn("Source token 4827", json.dumps(fixture.requests[-1]["body"]))
        self.assertEqual("private", h.store.all("route_history")[1]["mode"])
        if not full:
            self.assertFalse((self.workspace / "article.txt").exists())
            accept(ask("Proceed with the plan")["assistance_proposal"])
        row = h.store.all("planner_request")[0]
        wait(lambda: h.store.get("executive_goal", row["accepted_goal"])["state"] == "completed")
        self.assertEqual("4827", (self.workspace / "article.txt").read_text())
        self.assertEqual(2, len(self.reads))
        self.assertEqual([], self.posts)
        self.assertEqual(
            "verified", h.store.task(h.executive._tasks(row["accepted_goal"])[0]).state
        )
