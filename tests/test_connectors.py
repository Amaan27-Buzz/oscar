"""Synthetic provider contracts; never claims authenticated private-account acceptance."""

import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from unittest.mock import patch

from oscar.capabilities import Cancellation, ScopedFiles, Verifier
from oscar.connector_providers import (
    MCPBoundary,
    github_manifest,
    load_google,
    microsoft_manifest,
    notion_manifest,
    slack_manifest,
)
from oscar.connectors import (
    ConnectionState,
    ConnectorError,
    ConnectorEvent,
    ConnectorFabric,
    ConnectorInstance,
    ConnectorManifest,
    ConnectorVerifier,
    CredentialRef,
    EnvironmentSecrets,
    HTTPSConnector,
    RiskLevel,
    endpoint,
    pkce_pair,
)
from oscar.contracts import Action, Epistemic, Objective, Task, TaskState, new_id, record
from oscar.freshness import Authority, SourceRef
from oscar.grid import Grid, Node, NodeRole
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.storage import Store

ROOT = Path(__file__).resolve().parents[1]


class FixtureHTTP:
    def __init__(self):
        self.calls = []
        self.payload = {"id": "event-1", "summary": "fixture"}
        self.failure = None

    def request(self, manifest, spec, parameters, secret):
        path, _ = endpoint(spec, parameters)
        self.calls.append((spec.method, path, secret))
        if self.failure:
            raise ConnectorError(self.failure)
        return dict(self.payload), manifest.base_url + path.split("?")[0]


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state.sqlite")
        self.policy = PersonalPolicy(self.store)
        self.secret = "synthetic-oauth-token-only"
        self.secrets = EnvironmentSecrets(
            {"fixture": "FIXTURE_TOKEN"}, {"FIXTURE_TOKEN": self.secret}
        )
        self.http = FixtureHTTP()
        self.fabric = ConnectorFabric(self.store, self.secrets, self.policy, self.http)
        self.manifest = next(
            m
            for m in load_google(ROOT / "config/google-connectors.json")
            if m.id == "google.calendar"
        )
        scopes = frozenset(s for c in self.manifest.capabilities for s in c.scopes)
        self.instance = ConnectorInstance(
            "calendar", self.manifest, CredentialRef("fixture"), scopes
        )
        self.fabric.install(self.instance)
        self.objective = Objective(new_id(), "synthetic calendar write", "owner", {}, time())
        self.task = Task(new_id(), self.objective.id, self.objective.correlation_id)
        self.store.put("task", self.task.id, record(self.task))
        self.cancel = Cancellation(self.store, self.task.id)
        self.action = Action(
            new_id(),
            self.task.id,
            self.task.correlation_id,
            "calendar:google.calendar.events.create",
            {
                "path": {"calendarId": "primary"},
                "body": {"summary": "fixture"},
            },
            new_id(),
            "owner",
        )

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def execute(self, **kwargs):
        return self.fabric.execute(
            "calendar",
            "google.calendar.events.create",
            self.action,
            self.cancel,
            frozenset({"connectors:write", "connectors:read"}),
            **kwargs,
        )

    def test_mutation_confirmation_and_report_boundary(self):
        denied = self.execute()
        self.assertFalse(denied.result.success)
        self.assertEqual([], self.http.calls)
        outcome = self.execute(confirmed=True)
        self.assertTrue(outcome.result.success)
        self.assertEqual(Epistemic.REPORTED, outcome.result.status)
        self.assertIsNone(outcome.result.value)
        self.assertNotIn("fixture", json.dumps(self.store.ledger(self.task.id)))

    def test_readback_match_and_lie_rejection(self):
        outcome = self.execute(confirmed=True)
        objective = replace(
            self.objective,
            criterion={
                "kind": "connector_fields",
                "instance_id": "calendar",
                "read_capability": "google.calendar.events.get",
                "read_parameters": {"path": {"calendarId": "primary", "eventId": "event-1"}},
                "expected": {"summary": "fixture"},
            },
        )
        verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), self.fabric)
        self.assertEqual(TaskState.VERIFIED, verifier.verify(objective, outcome.result).state)
        self.http.payload["summary"] = "wrong"
        self.assertEqual(TaskState.FAILED, verifier.verify(objective, outcome.result).state)
        other = replace(
            objective,
            criterion={
                **objective.criterion,
                "read_parameters": {"path": {"calendarId": "primary", "eventId": "unrelated"}},
            },
        )
        self.assertEqual(TaskState.PARTIALLY_VERIFIED, verifier.verify(other, outcome.result).state)

    def test_missing_auth_scopes_unavailability(self):
        cap = self.manifest.capabilities[0]
        for instance, expected in [
            (replace(self.instance, credential=None), ConnectionState.AUTH_MISSING),
            (replace(self.instance, granted_scopes=frozenset()), ConnectionState.SCOPE_MISSING),
            (replace(self.instance, available=False), ConnectionState.UNAVAILABLE),
        ]:
            self.assertEqual(expected, self.fabric.state(instance, cap))
            self.fabric.instances["calendar"] = instance
            self.assertEqual([], self.fabric.capabilities("node"))
        outcome = self.execute(confirmed=True)
        self.assertFalse(outcome.result.success)
        self.assertEqual([], self.http.calls)

    def test_policy_cannot_grant_permission_and_deny_survives_confirmation(self):
        now = time()
        self.policy.save(
            PolicyRule(
                "never", "google.calendar.*", PolicyEffect.DENY, "explicit owner", now, now, {}
            ),
            owner_authorized=True,
        )
        self.assertFalse(self.execute(confirmed=True).result.success)
        self.assertEqual([], self.http.calls)
        decision = self.policy.evaluate(
            "google.calendar.events.create", ("connectors:write",), frozenset(), confirmed=True
        )
        self.assertFalse(decision.allowed)

    def test_google_and_non_google_catalog(self):
        google = load_google(ROOT / "config/google-connectors.json")
        self.assertEqual(35, sum(len(m.capabilities) for m in google))
        for manifest in (
            *google,
            microsoft_manifest(),
            github_manifest(public=True),
            slack_manifest(),
            notion_manifest(),
        ):
            scopes = frozenset(s for c in manifest.capabilities for s in c.scopes)
            self.fabric.install(
                ConnectorInstance(manifest.id, manifest, CredentialRef("fixture"), scopes)
            )
        caps = self.fabric.capabilities("connectors")
        permissions = tuple(sorted({p for c in caps for p in c.permissions}))
        grid = Grid(self.store)
        scopes = ("advertise", "heartbeat", "execute", *permissions)
        grid.register(Node("connectors", NodeRole.CLOUD, scopes))
        session = grid.pair("connectors", scopes)
        self.fabric.advertise(grid, session)
        self.assertTrue(grid.search("google.gmail.search"))
        self.assertTrue(grid.search("github.repositories.get"))
        self.assertTrue(grid.search("notion.data_sources.query"))

    def test_each_google_endpoint_contract(self):
        for manifest in load_google(ROOT / "config/google-connectors.json"):
            for spec in manifest.capabilities:
                import re

                path = {k: "fixture/id" for k in re.findall(r"\{(.*?)\}", spec.path)}
                params = {"path": path}
                if spec.body_required:
                    params["body"] = {"synthetic": True}
                uri, body = endpoint(spec, params)
                self.assertNotIn("fixture/id", uri)
                self.assertEqual(spec.body_required, body is not None)
                with self.assertRaises(ValueError):
                    endpoint(spec, {**params, "query": {"unknown": "value"}})

    def test_secret_and_private_payload_never_persist(self):
        self.http.payload["token"] = self.secret
        outcome = self.execute(confirmed=True)
        self.assertNotIn(self.secret, json.dumps(outcome.payload))
        self.assertNotIn(self.secret, json.dumps(self.store.all("connector_event_receipt")))
        self.assertNotIn(self.secret, json.dumps(self.store.ledger(self.task.id)))
        reference = self.fabric.stage(self.action.parameters)
        durable = replace(self.action, parameters={"request_ref": reference})
        executor = self.fabric.executor(
            "calendar",
            "google.calendar.events.create",
            frozenset({"connectors:write"}),
            confirmed=lambda _: True,
        )
        self.assertTrue(executor(durable, self.cancel).success)
        self.fabric.release_request(reference)
        self.assertEqual("connector_blocked:input_expired", executor(durable, self.cancel).error)
        with self.assertRaises(ValueError):
            self.fabric.stage({"body": {"token": self.secret}})

    def test_event_auth_dedup_and_no_content_retention(self):
        source = SourceRef(
            "https://www.googleapis.com/calendar/v3",
            Authority.LIVE_API,
            "account",
            time(),
            evidence_id=new_id(),
        )
        event = ConnectorEvent(
            "calendar", "event-1", source, cursor="private-cursor", mechanism="incremental-sync"
        )
        with self.assertRaises(PermissionError):
            self.fabric.ingest(event, authenticated=False)
        self.assertTrue(self.fabric.ingest(event, authenticated=True))
        self.assertFalse(self.fabric.ingest(event, authenticated=True))
        self.assertNotIn("private-cursor", json.dumps(self.store.all("connector_event_receipt")))

    def test_readback_cannot_borrow_ungranted_permission_or_another_account(self):
        outcome = self.fabric.execute(
            "calendar",
            "google.calendar.events.create",
            self.action,
            self.cancel,
            frozenset({"connectors:write"}),
            confirmed=True,
        )
        objective = replace(
            self.objective,
            criterion={
                "kind": "connector_fields",
                "instance_id": "calendar",
                "read_capability": "google.calendar.events.get",
                "read_parameters": {"path": {"calendarId": "primary", "eventId": "event-1"}},
                "expected": {"summary": "fixture"},
            },
        )
        verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), self.fabric)
        self.assertEqual(
            TaskState.PARTIALLY_VERIFIED, verifier.verify(objective, outcome.result).state
        )
        self.assertEqual(1, len(self.http.calls))
        self.fabric.outcomes[outcome.result.id] = replace(
            outcome, instance_id="another-account", granted=frozenset({"connectors:read"})
        )
        self.assertEqual(
            TaskState.PARTIALLY_VERIFIED, verifier.verify(objective, outcome.result).state
        )

    def test_provider_exception_cannot_leak_secret_into_ledger(self):
        self.http.failure = self.secret
        outcome = self.execute(confirmed=True)
        self.assertEqual("connector_failure", outcome.result.error)
        self.assertNotIn(self.secret, json.dumps(self.store.ledger(self.task.id)))

    def test_mcp_fabric_scope_confirmation_and_reported_result(self):
        from oscar.connector_providers import MCPConnectorHTTP

        class Session:
            def __init__(self):
                self.calls = 0

            def list_tools(self):
                return [
                    {
                        "name": "delete",
                        "inputSchema": {"type": "object"},
                        "annotations": {"readOnlyHint": True},
                    }
                ]

            def call_tool(self, name, arguments):
                self.calls += 1
                return {"content": [{"type": "text", "text": "synthetic success"}]}

        session = Session()
        boundary = MCPBoundary(session, {"delete": RiskLevel.DESTRUCTIVE})
        fabric = ConnectorFabric(self.store, self.secrets, self.policy, MCPConnectorHTTP(boundary))
        fabric.install(ConnectorInstance("mcp", boundary.manifest(), session_ready=True))
        action = replace(
            self.action,
            capability_id="mcp:mcp.delete",
            parameters={"path": {"name": "delete"}, "body": {}},
        )
        denied = fabric.execute(
            "mcp", "mcp.delete", action, self.cancel, frozenset({"connectors:destructive"})
        )
        self.assertFalse(denied.result.success)
        self.assertEqual(0, session.calls)
        allowed = fabric.execute(
            "mcp",
            "mcp.delete",
            action,
            self.cancel,
            frozenset({"connectors:destructive"}),
            confirmed=True,
        )
        self.assertEqual(Epistemic.REPORTED, allowed.result.status)
        self.assertEqual(1, session.calls)

    def test_pkce_s256(self):
        import base64

        verifier, challenge = pkce_pair()
        self.assertGreaterEqual(len(verifier), 43)
        self.assertEqual(
            challenge,
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("="),
        )

    def test_provider_failure_and_cancellation(self):
        self.http.failure = "rate_limited"
        self.assertFalse(self.execute(confirmed=True).result.success)
        self.store.transition(self.task.id, TaskState.CANCELLED)
        from oscar.capabilities import Cancelled

        with self.assertRaises(Cancelled):
            self.execute(confirmed=True)

    def test_endpoint_and_header_secret_boundaries(self):
        for url in (
            "http://example.com",
            "https://a:b@example.com",
            "https://example.com?q=secret",
        ):
            with self.assertRaises(ValueError):
                ConnectorManifest("unsafe", "unsafe", url, ())
        with self.assertRaises(ValueError):
            ConnectorManifest(
                "bad", "bad", "https://example.com", (), headers=(("Authorization", "secret"),)
            )
        spec = self.manifest.capabilities[0]
        with self.assertRaises(ValueError):
            endpoint(spec, {"path": {"calendarId": ".."}})

    def test_https_array_response_and_slack_http_200_error(self):
        class Response:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self, bound):
                return json.dumps(self.payload).encode()

        class Opener:
            def __init__(self, payload):
                self.payload = payload

            def open(self, request, timeout):
                self.request = request
                return Response(self.payload)

        manifest = github_manifest(public=True)
        opener = Opener([{"id": 1}])
        with patch("oscar.connectors.build_opener", return_value=opener):
            payload, _ = HTTPSConnector().request(
                manifest, manifest.capabilities[1], {"path": {"owner": "a", "repo": "b"}}, None
            )
        self.assertEqual({"items": [{"id": 1}]}, payload)
        opener = Opener({"ok": False, "error": "fixture error"})
        with patch("oscar.connectors.build_opener", return_value=opener):
            with self.assertRaisesRegex(ConnectorError, "provider_rejected"):
                HTTPSConnector().request(
                    manifest, manifest.capabilities[0], {"path": {"owner": "a", "repo": "b"}}, None
                )

    def test_mcp_annotations_are_not_authority(self):
        class Session:
            def list_tools(self):
                return [
                    {
                        "name": "search",
                        "inputSchema": {"type": "object"},
                        "annotations": {"readOnlyHint": True},
                    },
                    {
                        "name": "delete",
                        "inputSchema": {"type": "object"},
                        "annotations": {"readOnlyHint": True},
                    },
                ]

            def call_tool(self, name, arguments):
                return {"content": [{"type": "text", "text": "synthetic testimony"}]}

        boundary = MCPBoundary(Session(), {"search": RiskLevel.READ})
        self.assertEqual(["mcp.search"], [c.name for c in boundary.manifest().capabilities])
        with self.assertRaises(PermissionError):
            boundary.call("delete", {})
        self.assertIn("content", boundary.call("search", {}))
