"""Reviewed conversation reaches the existing browser Worker; effects remain REPORTED."""

import base64
import importlib.util
import json
import ssl
import unittest
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import monotonic, sleep
from urllib.parse import parse_qs

from oscar.browser_worker import run
from oscar.cloud_http import CloudHTTPServer
from oscar.contracts import Capability
from oscar.credentials import CredentialPool
from oscar.desktop_actions import form_intent, public_capability
from oscar.harness import ModelExecutor
from oscar.jev import Intent
from oscar.models import Funding, ModelRequest, ModelSpec, RoutingPolicy
from oscar.planner_authoring import PlannerAuthoring
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.remote_client import GridClient
from oscar.router import Router
from tests import test_connected_acceptance as connected_fixture
from tests import test_providers as provider_fixture
from tests import test_remote_machine as machine_fixture
from tests.test_remote_grid import signature


class BrowserWorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.cap = Capability(
            "machine.browser",
            "Browser",
            "Scoped browser",
            "machine",
            "worker",
            ("machine:host", "browser:control"),
            "browser",
            "metadata",
            "high",
        )
        self.request = {
            "origins": ["https://example.com"],
            "steps": [
                {"operation": "navigate", "url": "https://example.com/form"},
                {"operation": "fill", "selector": "#name", "text": "Reviewed"},
                {"operation": "submit", "selector": "#submit"},
            ],
            "timeout": 30,
            "max_text": 4096,
        }

    def intent(self, parameters, **extra):
        return form_intent(
            self.cap,
            {
                "capability_id": self.cap.id,
                "operation": "browser_workflow",
                "fields": {"workflow": json.dumps(parameters), **extra},
            },
            {},
        )

    def test_existing_strict_plan_and_explicit_account_pair_are_preserved(self):
        parameters = {"request": self.request, "account_id": "synthetic", "account_generation": 2}
        intent = self.intent(parameters)
        self.assertEqual(parameters, intent.parameters)
        self.assertEqual({"kind": "unavailable"}, intent.criterion)
        self.assertNotIn("browser_workflow", public_capability(self.cap, {})["operations"])
        examples = PlannerAuthoring.descriptor(asdict(self.cap))["intent_examples"]
        self.assertTrue(any("verification" in e["parameters"] for e in examples))
        self.assertTrue(
            any(
                any(s["operation"] == "submit" for s in e["parameters"]["request"]["steps"])
                for e in examples
            )
        )

    def test_wrong_origin_profile_upload_and_hidden_fields_reject(self):
        for parameters in (
            {
                "request": {
                    **self.request,
                    "steps": [{"operation": "navigate", "url": "https://evil.example"}],
                }
            },
            {"request": self.request, "profile": "personal-browser"},
            {"request": self.request, "account_id": "synthetic"},
            {"request": self.request, "account_id": "synthetic", "account_generation": 0},
            {
                "request": {
                    **self.request,
                    "steps": [{"operation": "upload", "selector": "#file", "path": "../private"}],
                }
            },
            {
                "request": {
                    **self.request,
                    "steps": [{"operation": "submit", "selector": "#submit", "script": "hidden"}],
                }
            },
            {"request": {**self.request, "timeout": float("nan")}},
        ):
            with (
                self.subTest(parameters=parameters),
                self.assertRaises((ValueError, PermissionError)),
            ):
                self.intent(parameters)
        with self.assertRaises(ValueError):
            self.intent({"request": self.request}, hidden="unreviewed")


@unittest.skipUnless(importlib.util.find_spec("playwright"), "optional installed Playwright")
class BrowserWorkflowAcceptanceTests(unittest.TestCase):
    setUp = machine_fixture.RemoteMachineExecutionTests.setUp
    enroll = machine_fixture.RemoteMachineExecutionTests.enroll
    start_worker = machine_fixture.RemoteMachineExecutionTests.start_worker
    close = provider_fixture.ProviderContractTests.close

    def test_conversation_signed_reviews_outbound_submission_and_independent_readback(self):
        self.check_workflow()

    def test_reviewed_exact_browser_text_can_verify(self):
        self.check_workflow("match")

    def test_authenticated_profile_is_used_by_independent_readback(self):
        self.check_workflow("authenticated")

    def test_wrong_browser_text_fails_without_replaying_submission(self):
        self.check_workflow("mismatch")

    def test_readback_redirect_fails_even_when_text_matches(self):
        self.check_workflow("redirect")

    def check_workflow(self, verification=None):
        connected_fixture.ConnectedAcceptanceTests.certificate(self)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(self.ca, self.root / "tls-key.pem")
        grid_server = CloudHTTPServer(self.core)
        grid_server.socket = tls.wrap_socket(grid_server.socket, server_side=True)
        grid_server.start()
        self.addCleanup(grid_server.close)
        endpoint = f"https://127.0.0.1:{self.core.config.listen_port}"
        self.desktop, self.owner = (
            GridClient(
                endpoint,
                client.session,
                lambda value: base64.b64decode(signature(self.transport_key, value)),
                ssl_context=self.context,
            )
            for client in (self.desktop, self.owner)
        )
        provider_fixture.ProviderContractTests.setUp(self)
        h = self.core.harness
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
        pool = CredentialPool([provider], {"SYNTHETIC_PLANNER": "synthetic-only"}, h.store)
        h.dispatcher.executors["models.reason"] = ModelExecutor(
            Router(Registry([provider], [model]), pool, {"openai": HTTPAdapter("openai")}, h.store),
            ModelRequest("template", "template", "", max_output_tokens=2048),
            RoutingPolicy(),
        )
        path = self.root / "independent-server-effect.txt"
        submissions = []
        receipt_reads = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if verification == "authenticated" and self.path == "/receipt":
                    receipt_reads.append(self.headers.get("Cookie", ""))
                    if self.headers.get("Cookie", "") != "readback=synthetic":
                        self.send_response(403)
                        self.end_headers()
                        self.wfile.write(b"<html><body>Authorization required</body></html>")
                        return
                if verification == "redirect" and self.path == "/readback":
                    self.send_response(303)
                    self.send_header("Location", "/receipt")
                    self.end_headers()
                    return
                self.send_response(200)
                if verification == "authenticated" and self.path == "/":
                    self.send_header(
                        "Set-Cookie", "readback=synthetic; Max-Age=3600; HttpOnly; SameSite=Strict"
                    )
                self.end_headers()
                receipt = path.read_text() if path.exists() else "No submission"
                self.wfile.write(
                    (
                        '<html><body><output id="receipt">' + receipt + "</output>"
                        '<form method="post"><input id="message" name="message">'
                        '<select id="choice" name="choice"><option value="a">A</option>'
                        '<option value="b">B</option></select>'
                        '<button id="submit">Submit</button></form></body></html>'
                    ).encode()
                )

            def do_POST(self):
                fields = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
                submissions.append(fields)
                path.write_text(fields["message"][0] + ":" + fields["choice"][0])
                self.send_response(303)
                self.send_header("Location", "/receipt")
                self.end_headers()

            def log_message(self, *args):
                pass

        web = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(web.server_close)
        self.addCleanup(web.shutdown)
        Thread(target=web.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{web.server_port}"
        self.start_worker(
            ("machine.browser", "machine.files.write"),
            browser=True,
            profiles=verification == "authenticated",
        )
        request = {
            "origins": [origin],
            "timeout": 30,
            "max_text": 1000,
            "steps": [
                {"operation": "navigate", "url": origin},
                {"operation": "fill", "selector": "#message", "text": "Synthetic receipt"},
                {"operation": "select", "selector": "#choice", "value": "b"},
                {"operation": "submit", "selector": "#submit"},
                {"operation": "wait", "selector": "#receipt"},
                {"operation": "inspect"},
            ],
        }
        cap = next(c for c in self.worker.effects.capabilities() if c.id == "machine.browser")
        parameters = {"request": request}
        if verification == "authenticated":
            account = h.accounts.add("fixture", "synthetic", "browser-owner", "Work", verified=True)
            parameters.update(account_id=account.id, account_generation=account.generation)
        if verification:
            parameters["verification"] = {
                "url": origin + ("/readback" if verification == "redirect" else "/receipt"),
                "selector": "#receipt",
                "text": "Different receipt"
                if verification == "mismatch"
                else "Synthetic receipt:b",
            }
        intent = form_intent(
            cap,
            {
                "capability_id": cap.id,
                "operation": "browser_workflow",
                "fields": {"workflow": json.dumps(parameters)},
            },
            {},
        )
        steps = [
            {
                "id": "submit",
                "intent": asdict(intent),
                "node_id": "test-machine",
                "capability_id": "machine.browser",
                "depends_on": [],
            }
        ]
        if verification:
            steps.append(
                {
                    "id": "save-confirmation",
                    "intent": asdict(
                        Intent(
                            "Save confirmed registration",
                            "file_write",
                            "registration.txt",
                            "Synthetic receipt:b",
                        )
                    ),
                    "node_id": "test-machine",
                    "capability_id": "machine.files.write",
                    "depends_on": ["submit"],
                }
            )
        self.body["choices"][0]["message"]["content"] = json.dumps({"steps": steps})

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

        def approve(change):
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
            return review

        for verb in ("Fill", "Click", "Submit", "Select", "Navigate"):
            candidate = ask(f"On device test-machine: {verb} the local synthetic form")
            self.assertIn("assistance_proposal", candidate, candidate)
        first = ask(
            "On device test-machine: Fill the local synthetic form and submit it"
            + (
                "; save registration.txt only after the exact receipt matches"
                if verification
                else ""
            )
        )
        self.assertEqual([], self.requests)
        self.assertFalse(path.exists())
        self.assertIn("assistance_proposal", first, first)
        approve(first["assistance_proposal"])
        until = monotonic() + 8
        while monotonic() < until and not self.requests:
            h.executive.tick()
            sleep(0.02)
        self.assertEqual(1, len(self.requests))
        second = ask("Proceed with the plan")["assistance_proposal"]
        self.assertFalse(path.exists())
        review = approve(second)
        self.assertIn("Synthetic receipt", review["review"])
        goal = h.store.all("planner_request")[0]["accepted_goal"]
        until = monotonic() + 40
        while monotonic() < until:
            self.worker.step()
            tasks = h.executive._tasks(goal)
            if (
                verification in {"match", "authenticated"}
                and len(tasks) == 2
                and all(h.store.task(task).state == "verified" for task in tasks)
            ):
                break
            if tasks and h.store.task(tasks[0]).state in {
                "partially_verified",
                "failed",
                "blocked",
                "unknown",
            }:
                break
            sleep(2)  # Match the production outbound Worker polling cadence.
        expected = (
            "verified"
            if verification in {"match", "authenticated"}
            else "failed"
            if verification
            else "partially_verified"
        )
        self.assertEqual(
            expected, h.store.task(tasks[0]).state, (h.store.all("result"), h.store.all("evidence"))
        )
        if verification in {"match", "authenticated"}:
            self.assertEqual(2, len(tasks))
            self.assertTrue(all(h.store.task(task).state == "verified" for task in tasks))
            self.assertEqual(
                "Synthetic receipt:b", (self.workspace / "registration.txt").read_text()
            )
        else:
            self.assertFalse((self.workspace / "registration.txt").exists())
        self.assertEqual("Synthetic receipt:b", path.read_text())
        self.assertEqual([{"message": ["Synthetic receipt"], "choice": ["b"]}], submissions)
        observed = run(
            {
                **request,
                "steps": [
                    {"operation": "navigate", "url": origin + "/receipt"},
                    {"operation": "inspect"},
                ],
            },
            self.workspace,
        )
        if verification == "authenticated":
            self.assertNotIn("Synthetic receipt:b", observed["observations"][0]["text"])
            self.assertGreaterEqual(receipt_reads.count("readback=synthetic"), 2)
            self.assertEqual("", receipt_reads[-1])
        else:
            self.assertIn("Synthetic receipt:b", observed["observations"][0]["text"])
        self.assertEqual("blocked", ask("Proceed with the plan")["state"])
        for _ in range(3):
            self.worker.step()
        self.assertEqual(1, len(submissions))
