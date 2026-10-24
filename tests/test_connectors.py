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
        outcome = self.execute(confirmed=True)
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
        self.assertEqual(41, sum(len(m.capabilities) for m in google))
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
        self.fabric.bind_task(self.task.id, durable.parameters)
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

    def criterion(self):
        return {
            "kind": "connector_fields",
            "instance_id": "calendar",
            "read_parameters": {"path": {"calendarId": "primary", "eventId": "event-1"}},
            "expected": {"summary": "fixture"},
        }

    def runtime_fixture(self, *, confirmed=True):
        from oscar.runtime import Runtime
        from oscar.transport import Dispatcher

        grid = Grid(self.store)
        scopes = (
            "execute",
            "advertise",
            "heartbeat",
            "cancel",
            "connectors:write",
            "connectors:read",
            "connectors:external-communication",
            "connectors:destructive",
        )
        grid.register(Node("connector-node", NodeRole.CLOUD, scopes))
        session = grid.pair("connector-node", scopes)
        self.fabric.advertise(grid, session)
        verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), self.fabric)
        runtime = Runtime(self.store, grid, verifier)
        executor = self.fabric.executor(
            "calendar",
            "google.calendar.events.create",
            frozenset(scopes),
            confirmed=lambda _: confirmed,
        )
        dispatcher = Dispatcher(
            self.store, grid, "connector-node", {self.action.capability_id: executor}
        )
        return runtime, {"connector-node": (dispatcher, session)}

    def staged_task(self, runtime, *, verify=True):
        from oscar.jev import Intent

        reference = self.fabric.stage(
            {**self.action.parameters, "body": {"summary": "private-staged-marker"}}
        )
        task = runtime.create(
            Intent(
                "synthetic action",
                "capability",
                capability_kind="google.calendar.events.create",
                parameters={"request_ref": reference},
                criterion=self.criterion() if verify else None,
            )
        )
        return task, reference

    def test_120_sequential_runtime_actions_release_inputs_and_outcomes(self):
        runtime, transports = self.runtime_fixture()
        self.http.payload["private"] = "private-outcome-marker"
        original = self.http.request

        def inspect(manifest, spec, parameters, secret):
            self.assertEqual({}, self.fabric.requests)
            if spec.method == "GET":
                self.assertEqual(1, len(self.fabric.outcomes))
            return original(manifest, spec, parameters, secret)

        self.http.request = inspect
        for index in range(120):
            task, reference = self.staged_task(runtime, verify=index % 2 == 0)
            completed = runtime.run(task.id, transports)
            self.assertEqual(
                TaskState.VERIFIED if index % 2 == 0 else TaskState.PARTIALLY_VERIFIED,
                completed.state,
            )
            self.assertNotIn(reference, self.fabric.requests)
            self.assertEqual({}, self.fabric.outcomes)
            self.assertEqual({}, self.fabric.request_owners)
        durable = json.dumps(
            {
                kind: self.store.all(kind)
                for kind in ["task", "objective", "plan", "action", "result", "evidence"]
            }
        )
        durable += json.dumps(self.store.db.execute("SELECT data FROM audit").fetchall())
        self.assertNotIn("private-staged-marker", durable)
        self.assertNotIn("private-outcome-marker", durable)

    def test_runtime_cancel_before_dispatch_releases_staged_input(self):
        runtime, transports = self.runtime_fixture()
        task, reference = self.staged_task(runtime)
        self.assertEqual(TaskState.CANCELLED, runtime.cancel(task.id, transports).state)
        self.assertNotIn(reference, self.fabric.requests)
        self.assertEqual({}, self.fabric.request_owners)
        self.assertEqual([], self.http.calls)

    def test_runtime_failure_and_unreachable_executor_release_private_context(self):
        for scenario in ["provider", "permission", "endpoint", "unreachable"]:
            with self.subTest(scenario=scenario):
                runtime, transports = self.runtime_fixture(confirmed=scenario != "permission")
                task, reference = self.staged_task(runtime)
                self.http.failure = "provider_rejected" if scenario == "provider" else None
                if scenario == "endpoint":
                    self.fabric.requests[reference] = {"unexpected": "private-staged-marker"}
                completed = runtime.run(task.id, {} if scenario == "unreachable" else transports)
                self.assertIn(completed.state, {TaskState.FAILED, TaskState.BLOCKED})
                self.assertEqual({}, self.fabric.requests)
                self.assertEqual({}, self.fabric.outcomes)
                self.assertEqual({}, self.fabric.request_owners)
                # Reuse the same advertised session for each scenario.
                self.store.close()
                self.store = Store(self.root / (scenario + ".sqlite"))
                self.policy = PersonalPolicy(self.store)
                self.fabric = ConnectorFabric(self.store, self.secrets, self.policy, self.http)
                self.fabric.install(self.instance)

    def test_verifier_exception_releases_outcome_at_runtime_completion(self):
        runtime, transports = self.runtime_fixture()
        task, _ = self.staged_task(runtime)
        with patch.object(runtime.verifier, "verify", side_effect=ValueError("synthetic")):
            self.assertEqual(TaskState.UNKNOWN, runtime.run(task.id, transports).state)
        self.assertEqual({}, self.fabric.outcomes)
        self.assertEqual({}, self.fabric.requests)

    def test_cancellation_during_provider_call_does_not_retain_outcome(self):
        runtime, transports = self.runtime_fixture()
        task, _ = self.staged_task(runtime)
        original = self.http.request

        def cancel(manifest, spec, parameters, secret):
            runtime.cancel(task.id)
            return original(manifest, spec, parameters, secret)

        self.http.request = cancel
        self.assertEqual(TaskState.CANCELLED, runtime.run(task.id, transports).state)
        self.assertEqual({}, self.fabric.outcomes)
        self.assertEqual({}, self.fabric.requests)

    def test_restart_blocks_expired_inputs_and_unavailable_readback(self):
        runtime, transports = self.runtime_fixture()
        task, _ = self.staged_task(runtime)
        outcome = self.execute(confirmed=True)
        restarted = ConnectorFabric(self.store, self.secrets, self.policy, self.http)
        restarted.install(self.instance)
        runtime.verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), restarted)
        transports["connector-node"][0].executors[self.action.capability_id] = restarted.executor(
            "calendar",
            "google.calendar.events.create",
            frozenset({"connectors:write"}),
            confirmed=lambda _: True,
        )
        self.assertEqual(TaskState.BLOCKED, runtime.run(task.id, transports).state)
        self.assertEqual(
            TaskState.PARTIALLY_VERIFIED,
            runtime.verifier.verify(
                replace(self.objective, criterion=self.criterion()), outcome.result
            ).state,
        )
        self.assertEqual(1, len(self.http.calls))

    def test_readback_manifest_resource_and_executor_adversaries(self):
        verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), self.fabric)
        for attack in [
            "another_get",
            "another_event",
            "another_calendar",
            "another_account",
            "undeclared",
            "executor",
            "action",
            "task",
            "correlation",
            "instance_replaced",
        ]:
            with self.subTest(attack=attack):
                self.fabric.instances["calendar"] = self.instance
                criterion = self.criterion()
                action = self.action
                name = "google.calendar.events.create"
                if attack == "undeclared":
                    name = "google.calendar.events.delete"
                    action = replace(
                        action,
                        capability_id="calendar:" + name,
                        parameters={"path": {"calendarId": "primary", "eventId": "event-1"}},
                    )
                    criterion["read_capability"] = "google.calendar.events.get"
                outcome = self.fabric.execute(
                    "calendar",
                    name,
                    action,
                    self.cancel,
                    frozenset(
                        {
                            "connectors:write",
                            "connectors:read",
                            "connectors:destructive",
                            "connectors:external-communication",
                        }
                    ),
                    confirmed=True,
                )
                result = outcome.result
                if attack == "another_get":
                    criterion["read_capability"] = "google.calendar.events.list"
                    criterion["read_parameters"] = {"path": {"calendarId": "event-1"}}
                if attack == "another_event":
                    criterion["read_parameters"]["path"]["eventId"] = "other"
                if attack == "another_calendar":
                    criterion["read_parameters"]["path"]["calendarId"] = "other"
                if attack == "another_account":
                    criterion["instance_id"] = "other"
                if attack == "executor":
                    result = replace(result, executor="calendar:google.calendar.events.update")
                if attack == "action":
                    result = replace(result, action_id=new_id())
                if attack == "task":
                    result = replace(result, task_id=new_id())
                if attack == "correlation":
                    result = replace(result, correlation_id=new_id())
                if attack == "instance_replaced":
                    self.fabric.instances["calendar"] = replace(
                        self.instance, credential=CredentialRef("other")
                    )
                calls = len(self.http.calls)
                self.assertNotEqual(
                    TaskState.VERIFIED,
                    verifier.verify(replace(self.objective, criterion=criterion), result).state,
                )
                self.assertEqual(calls, len(self.http.calls))
                self.assertNotIn(outcome.result.id, self.fabric.outcomes)

    def test_executor_cannot_claim_another_executed_capability(self):
        with self.assertRaises(ValueError):
            self.fabric.execute(
                "calendar",
                "google.calendar.events.create",
                replace(self.action, capability_id="calendar:google.calendar.events.update"),
                self.cancel,
                frozenset({"connectors:write"}),
                confirmed=True,
            )
        self.assertEqual([], self.http.calls)

    def test_composite_consequences_block_missing_permission_and_policy_denial(self):
        import re

        manifests = [
            self.manifest,
            *[
                m
                for m in load_google(ROOT / "config/google-connectors.json")
                if m.id == "google.gmail"
            ],
            microsoft_manifest(),
            slack_manifest(),
            github_manifest(),
        ]
        names = {
            "google.calendar.events.create",
            "google.calendar.events.update",
            "google.calendar.events.delete",
            "google.gmail.send",
            "microsoft.calendar.events.create",
            "microsoft.mail.send",
            "slack.messages.post",
            "github.issues.create",
        }
        for manifest in manifests:
            for spec in manifest.capabilities:
                if spec.name not in names:
                    continue
                for notifications in (
                    ["all", "externalOnly", "none"] if manifest.id == "google.calendar" else [None]
                ):
                    with self.subTest(capability=spec.name, notifications=notifications):
                        instance = ConnectorInstance(
                            spec.name,
                            manifest,
                            CredentialRef("fixture"),
                            frozenset(s for c in manifest.capabilities for s in c.scopes),
                        )
                        self.fabric.install(instance)
                        parameters = {
                            "path": {key: "fixture" for key in re.findall(r"\{(.*?)\}", spec.path)}
                        }
                        if spec.body_required:
                            parameters["body"] = {
                                "attendees": [{"email": "synthetic@example.invalid"}]
                            }
                        if notifications is not None:
                            parameters["query"] = {"sendUpdates": notifications}
                        action = replace(
                            self.action,
                            capability_id=instance.id + ":" + spec.name,
                            parameters=parameters,
                        )
                        granted = frozenset(
                            {"connectors:write", "connectors:destructive", "connectors:read"}
                        )
                        denied = self.fabric.execute(
                            instance.id, spec.name, action, self.cancel, granted, confirmed=True
                        )
                        self.assertFalse(denied.result.success)
                        granted |= {"connectors:external-communication"}
                        self.assertFalse(
                            self.fabric.execute(
                                instance.id, spec.name, action, self.cancel, granted
                            ).result.success
                        )
                        now = time()
                        self.policy.save(
                            PolicyRule(
                                "communication-deny",
                                "connectors:external-communication",
                                PolicyEffect.DENY,
                                "explicit owner",
                                now,
                                now,
                                {},
                            ),
                            owner_authorized=True,
                        )
                        self.assertFalse(
                            self.fabric.execute(
                                instance.id, spec.name, action, self.cancel, granted, confirmed=True
                            ).result.success
                        )
                        self.assertEqual([], self.http.calls)
                        self.policy.save(
                            PolicyRule(
                                "communication-deny",
                                "connectors:external-communication",
                                PolicyEffect.DENY,
                                "explicit owner",
                                now,
                                now,
                                {},
                                enabled=False,
                            ),
                            owner_authorized=True,
                        )
                        self.assertTrue(
                            self.fabric.execute(
                                instance.id, spec.name, action, self.cancel, granted, confirmed=True
                            ).result.success
                        )
                        self.http.calls.clear()
                        self.fabric.release_task(self.task.id)
                        del self.fabric.instances[instance.id]

    def test_creation_without_attendees_keeps_write_permission(self):
        self.assertTrue(self.execute(confirmed=True).result.success)
        spec = next(
            c
            for c in microsoft_manifest().capabilities
            if c.name == "microsoft.calendar.events.create"
        )
        self.assertEqual(
            ("connectors:write",), spec.action_permissions({"body": {"subject": "synthetic"}})
        )

    def test_active_context_bound_remains_100_and_completed_tasks_are_reaped(self):
        references = [self.fabric.stage(self.action.parameters) for _ in range(100)]
        with self.assertRaises(ValueError):
            self.fabric.stage(self.action.parameters)
        for reference in references:
            self.fabric.release_request(reference)
        outcomes = [self.execute(confirmed=True) for _ in range(100)]
        with self.assertRaises(ValueError):
            self.execute(confirmed=True)
        self.store.transition(self.task.id, TaskState.CANCELLED)
        self.assertEqual({}, self.fabric.outcomes)
        self.fabric.stage(self.action.parameters)
        self.assertTrue(all(outcome.result.id not in self.fabric.outcomes for outcome in outcomes))

    def test_shared_staged_input_cannot_be_consumed_by_another_task(self):
        reference = self.fabric.stage(self.action.parameters)
        self.fabric.bind_task("other-task", {"request_ref": reference})
        executor = self.fabric.executor(
            "calendar",
            "google.calendar.events.create",
            frozenset({"connectors:write"}),
            confirmed=lambda _: True,
        )
        with self.assertRaises(ValueError):
            executor(replace(self.action, parameters={"request_ref": reference}), self.cancel)
        self.assertIn(reference, self.fabric.requests)
        self.assertEqual([], self.http.calls)

    def test_grid_session_cannot_borrow_executor_communication_grant(self):
        runtime, transports = self.runtime_fixture()
        task, _ = self.staged_task(runtime)
        dispatcher, session = transports["connector-node"]
        narrow = runtime.grid.pair(
            "connector-node",
            tuple(
                s
                for s in self.store.get("session", session.id)["scopes"]
                if s != "connectors:external-communication"
            ),
        )
        self.assertEqual(
            TaskState.BLOCKED, runtime.run(task.id, {"connector-node": (dispatcher, narrow)}).state
        )
        self.assertEqual([], self.http.calls)
        self.assertEqual({}, self.fabric.requests)

    def test_cancelled_direct_executor_consumes_input_before_cancellation_check(self):
        from oscar.capabilities import Cancelled

        reference = self.fabric.stage(self.action.parameters)
        self.fabric.bind_task(self.task.id, {"request_ref": reference})
        other_store = Store(self.root / "state.sqlite")
        try:
            other_store.transition(self.task.id, TaskState.CANCELLED)
        finally:
            other_store.close()
        executor = self.fabric.executor(
            "calendar",
            "google.calendar.events.create",
            frozenset({"connectors:write"}),
            confirmed=lambda _: True,
        )
        with self.assertRaises(Cancelled):
            executor(replace(self.action, parameters={"request_ref": reference}), self.cancel)
        self.assertEqual({}, self.fabric.requests)
        self.assertEqual({}, self.fabric.outcomes)

    def test_communication_permission_cannot_replace_write_permission(self):
        manifest = slack_manifest()
        instance = ConnectorInstance(
            "slack", manifest, CredentialRef("fixture"), frozenset({"chat:write"})
        )
        self.fabric.install(instance)
        action = replace(
            self.action,
            capability_id="slack:slack.messages.post",
            parameters={"body": {"channel": "synthetic", "text": "synthetic"}},
        )
        outcome = self.fabric.execute(
            "slack",
            "slack.messages.post",
            action,
            self.cancel,
            frozenset({"connectors:external-communication"}),
            confirmed=True,
        )
        self.assertFalse(outcome.result.success)
        self.assertEqual([], self.http.calls)

    def test_failed_readback_releases_payload_and_requires_read_policy(self):
        verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), self.fabric)
        outcome = self.execute(confirmed=True)
        self.http.failure = "network_failure"
        self.assertEqual(
            TaskState.PARTIALLY_VERIFIED,
            verifier.verify(
                replace(self.objective, criterion=self.criterion()), outcome.result
            ).state,
        )
        self.assertEqual({}, self.fabric.outcomes)
        self.http.failure = None
        outcome = self.execute(confirmed=True)
        now = time()
        self.policy.save(
            PolicyRule("no-read", "connectors:read", PolicyEffect.DENY, "owner", now, now, {}),
            owner_authorized=True,
        )
        calls = len(self.http.calls)
        self.assertEqual(
            TaskState.PARTIALLY_VERIFIED,
            verifier.verify(
                replace(self.objective, criterion=self.criterion()), outcome.result
            ).state,
        )
        self.assertEqual(calls, len(self.http.calls))
        self.assertEqual({}, self.fabric.outcomes)

    def test_mcp_owner_review_can_require_composite_consequences(self):
        from oscar.connector_providers import MCPConnectorHTTP

        class Session:
            def __init__(self):
                self.calls = 0

            def list_tools(self):
                return [
                    {
                        "name": "remove_and_notify",
                        "inputSchema": {},
                        "annotations": {"readOnlyHint": True},
                    }
                ]

            def call_tool(self, name, arguments):
                self.calls += 1
                return {"content": []}

        session = Session()
        boundary = MCPBoundary(
            session, {"remove_and_notify": (RiskLevel.DESTRUCTIVE, RiskLevel.COMMUNICATION)}
        )
        fabric = ConnectorFabric(self.store, self.secrets, self.policy, MCPConnectorHTTP(boundary))
        fabric.install(ConnectorInstance("mcp", boundary.manifest(), session_ready=True))
        action = replace(
            self.action,
            capability_id="mcp:mcp.remove_and_notify",
            parameters={"path": {"name": "remove_and_notify"}, "body": {}},
        )
        self.assertFalse(
            fabric.execute(
                "mcp",
                "mcp.remove_and_notify",
                action,
                self.cancel,
                frozenset({"connectors:destructive"}),
                confirmed=True,
            ).result.success
        )
        self.assertEqual(0, session.calls)
        self.assertTrue(
            fabric.execute(
                "mcp",
                "mcp.remove_and_notify",
                action,
                self.cancel,
                frozenset({"connectors:destructive", "connectors:external-communication"}),
                confirmed=True,
            ).result.success
        )
        self.assertEqual(1, session.calls)
        with self.assertRaises(ValueError):
            MCPBoundary(
                session, {"remove_and_notify": (RiskLevel.READ, RiskLevel.COMMUNICATION)}
            ).manifest()

    def test_cross_store_completion_is_reaped_at_admission(self):
        reference = self.fabric.stage(self.action.parameters)
        self.fabric.bind_task(self.task.id, {"request_ref": reference})
        outcome = self.execute(confirmed=True)
        other_store = Store(self.root / "state.sqlite")
        try:
            other_store.transition(self.task.id, TaskState.CANCELLED)
        finally:
            other_store.close()
        self.fabric.stage(self.action.parameters)
        self.assertNotIn(reference, self.fabric.requests)
        self.assertNotIn(outcome.result.id, self.fabric.outcomes)

    def test_store_does_not_keep_abandoned_fabric_private_context_alive(self):
        import gc
        import weakref

        fabric = ConnectorFabric(self.store, self.secrets, self.policy, self.http)
        fabric.stage({"body": {"private": "synthetic-private-marker"}})
        reference = weakref.ref(fabric)
        del fabric
        gc.collect()
        self.assertIsNone(reference())

    def test_task_blocked_during_provider_call_does_not_cache_late_payload(self):
        runtime, transports = self.runtime_fixture()
        task, _ = self.staged_task(runtime)
        original = self.http.request

        def lose_task(manifest, spec, parameters, secret):
            self.store.transition(task.id, TaskState.BLOCKED, blocker="synthetic lease loss")
            return original(manifest, spec, parameters, secret)

        self.http.request = lose_task
        self.assertEqual(TaskState.BLOCKED, runtime.run(task.id, transports).state)
        self.assertEqual({}, self.fabric.outcomes)
        self.assertEqual({}, self.fabric.requests)

    def test_cross_store_cancel_after_outcome_creation_is_cleaned_by_runner(self):
        runtime, transports = self.runtime_fixture()
        task, _ = self.staged_task(runtime)
        original = self.store.audit

        def remote_cancel(task_id, event, data):
            if event == "connector_result":
                self.assertEqual(1, len(self.fabric.outcomes))
                other = Store(self.root / "state.sqlite")
                try:
                    other.transition(task_id, TaskState.CANCELLED)
                finally:
                    other.close()
            original(task_id, event, data)

        with patch.object(self.store, "audit", side_effect=remote_cancel):
            self.assertEqual(TaskState.CANCELLED, runtime.run(task.id, transports).state)
        self.assertEqual({}, self.fabric.outcomes)
        self.assertEqual({}, self.fabric.requests)

    def ownership_fixture(self):
        reference = self.fabric.stage(
            {"path": {"calendarId": "primary"}, "body": {"summary": "ownership-private-input"}}
        )
        self.http.payload["private"] = "ownership-private-outcome"
        action = replace(self.action, parameters={"request_ref": reference})
        self.store.put("action", action.id, record(action))
        executor = self.fabric.executor(
            "calendar",
            "google.calendar.events.create",
            frozenset({"connectors:write", "connectors:read"}),
            confirmed=lambda _: True,
        )
        return reference, action, executor

    def assert_ownership_payloads_not_persisted(self):
        durable = json.dumps(self.store.db.execute("SELECT data FROM records").fetchall())
        durable += json.dumps(self.store.db.execute("SELECT data FROM audit").fetchall())
        self.assertNotIn("ownership-private-input", durable)
        self.assertNotIn("ownership-private-outcome", durable)

    def test_executor_rejects_unbound_staged_reference(self):
        reference, action, executor = self.ownership_fixture()
        with self.assertRaisesRegex(ValueError, "not bound to this task"):
            executor(action, self.cancel)
        self.assertIn(reference, self.fabric.requests)
        self.assertNotIn(reference, self.fabric.request_owners)
        self.assertEqual([], self.http.calls)
        self.assertEqual({}, self.fabric.outcomes)
        self.assert_ownership_payloads_not_persisted()
        self.fabric.release_request(reference)
        self.assertEqual({}, self.fabric.requests)

    def test_executor_accepts_reference_explicitly_bound_to_current_task(self):
        reference, action, executor = self.ownership_fixture()
        self.fabric.bind_task(self.task.id, action.parameters)
        result = executor(action, self.cancel)
        self.assertTrue(result.success)
        self.assertEqual(1, len(self.http.calls))
        self.assertNotIn(reference, self.fabric.requests)
        self.assertNotIn(reference, self.fabric.request_owners)
        self.assertIn(result.id, self.fabric.outcomes)
        verifier = ConnectorVerifier(Verifier(ScopedFiles(self.root / "files")), self.fabric)
        self.assertEqual(
            TaskState.VERIFIED,
            verifier.verify(replace(self.objective, criterion=self.criterion()), result).state,
        )
        self.assertEqual({}, self.fabric.outcomes)
        self.assert_ownership_payloads_not_persisted()

    def test_executor_rejects_reference_explicitly_bound_to_another_task(self):
        reference, action, executor = self.ownership_fixture()
        other = replace(self.task, id=new_id())
        self.store.put("task", other.id, record(other))
        self.fabric.bind_task(other.id, action.parameters)
        with self.assertRaisesRegex(ValueError, "not bound to this task"):
            executor(action, self.cancel)
        self.assertIn(reference, self.fabric.requests)
        self.assertEqual(other.id, self.fabric.request_owners[reference])
        self.assertEqual([], self.http.calls)
        self.assertEqual({}, self.fabric.outcomes)
        self.assert_ownership_payloads_not_persisted()
        self.store.transition(other.id, TaskState.CANCELLED)
        self.assertEqual({}, self.fabric.requests)
        self.assertEqual({}, self.fabric.request_owners)
