"""Synthetic provider state over real HTTP through native Ask/signature/Fabric/verification."""

import base64
import json
import unittest
from copy import deepcopy
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic, sleep, time
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, build_opener

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import CloudHTTPServer
from oscar.communication import matches, prepare
from oscar.connector_mount import account_manifests
from oscar.connectors import CredentialRef, RiskLevel
from oscar.contracts import new_id
from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.http_client import NoRedirects
from oscar.mobile import display_digest
from oscar.oauth_device import VaultResolver
from oscar.policy import PersonalPolicy
from oscar.remote_client import request_proof
from oscar.remote_grid import create_invitation
from oscar.sentry import AwarenessMode, SentrySettings, SentryState
from oscar.storage import StateConflict
from tests.test_cloud import configuration, request
from tests.test_connections import PrivateVault


class Provider:
    def __init__(self):
        self.calls, self.resources = [], {}
        self.requests = []
        self.after_get, self.tamper, self.fail = None, False, False
        self.transform = None
        self.response_headers = {}
        self.fail_after_post = False
        self.require_etag = False
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.respond()

            def do_PATCH(self):
                self.respond()

            def do_GET(self):
                self.respond()

            def respond(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                body = json.loads(body) if body else None
                path = urlsplit(self.path).path
                owner.requests.append((self.path, self.headers.get("Authorization")))
                owner.calls.append((self.command, path, body))
                if owner.fail and self.command in {"POST", "PATCH"}:
                    self.send_response(503)
                    self.end_headers()
                    return
                if self.command == "POST":
                    if path.endswith("sendMail"):
                        self.send_response(202)
                        self.end_headers()
                        return
                    result = {"id": "synthetic-resource", **body}
                    if path.startswith("/tasks/v1/lists/") and path.endswith("/tasks"):
                        result.setdefault("status", "needsAction")
                    if path.startswith("/v1.0/me/todo/lists/") and path.endswith("/tasks"):
                        result.setdefault("status", "notStarted")
                    if path == "/v2/spaces":
                        result = {
                            "name": "spaces/SyntheticSpace",
                            "meetingCode": "abc-defg-hij",
                            "meetingUri": "https://meet.google.com/abc-defg-hij",
                            **body,
                        }
                    if path.endswith("messages/send"):
                        result["labelIds"] = ["SENT"]
                        read_path = path.removesuffix("/send") + "/synthetic-resource"
                    else:
                        read_path = path + "/synthetic-resource"
                    if path == "/v2/spaces":
                        read_path = "/v2/spaces/SyntheticSpace"
                    if path.startswith("/api/v4/projects/") and path.endswith("/issues"):
                        result = {
                            "id": 9001,
                            "iid": 7,
                            "project_id": int(path.split("/")[4]),
                            "state": "opened",
                            **body,
                        }
                        read_path = path + "/7"
                    if path == "/v1.0/me/messages":
                        result["isDraft"] = True
                    owner.resources[read_path] = result
                elif self.command == "PATCH":
                    if path not in owner.resources:
                        self.send_response(404)
                        self.end_headers()
                        return
                    if owner.require_etag and self.headers.get("If-Match") != owner.resources[
                        path
                    ].get("etag"):
                        self.send_response(412)
                        self.end_headers()
                        return
                    owner.resources[path].update(body)
                    if owner.require_etag:
                        owner.resources[path]["etag"] = '"saved-version"'
                    result = deepcopy(owner.resources[path])
                elif path in owner.resources:
                    result = deepcopy(owner.resources[path])
                    if owner.tamper:
                        result["subject"] = result["summary"] = result["title"] = "wrong"
                        result["raw"] = "bm90IGFuIGVtYWls"
                        if "message" in result:
                            result["message"]["raw"] = result["raw"]
                    if owner.after_get:
                        owner.after_get()
                else:
                    result = (
                        {"messages": [{"id": "synthetic-resource"}]}
                        if "gmail" in path
                        else {
                            "value": [{"id": "synthetic-resource", "subject": "Synthetic mail"}],
                            "@odata.nextLink": "provider-pagination-is-explicit",
                        }
                    )
                if self.command in {"POST", "PATCH"} and owner.fail_after_post:
                    self.send_response(503)
                    self.end_headers()
                    return
                if owner.transform:
                    result = owner.transform(self.command, deepcopy(result))
                raw = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                for key, value in owner.response_headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def opener(self):
        owner = self

        class Opener:
            def open(self, request, timeout):
                url = urlsplit(request.full_url)
                remapped = Request(
                    owner.url + url.path + ("?" + url.query if url.query else ""),
                    data=request.data,
                    headers=dict(request.header_items()),
                    method=request.get_method(),
                )
                return build_opener(NoRedirects()).open(remapped, timeout=timeout)

        return Opener()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class CommunicationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root, self.vault = Path(temporary.name), PrivateVault()
        self.h = Harness(
            self.root / "core.sqlite",
            self.root / "files",
            Path("config/development-models.json"),
            start_services=False,
            vault=self.vault,
        )
        self.addCleanup(self.h.close)
        self.provider = Provider()
        self.addCleanup(self.provider.close)
        patched = patch("oscar.connectors.build_opener", return_value=self.provider.opener())
        patched.start()
        self.addCleanup(patched.stop)
        self.accounts = {}
        for provider, alias in (("google", "Google"), ("microsoft", "Work"), ("gitlab", "Code")):
            account = self.h.accounts.add(provider, "fixture", alias, alias, verified=True)
            for manifest in account_manifests():
                if manifest.provider != provider or manifest.id not in {
                    "google.gmail",
                    "google.calendar",
                    "google.tasks",
                    "google.contacts",
                    "google.meet",
                    "microsoft.graph",
                    "gitlab.api",
                }:
                    continue
                reference = (alias + manifest.id).lower()
                self.vault.put("synthetic-secret-" + reference, reference=reference)
                account = self.h.accounts.bind(
                    account.id,
                    manifest.id,
                    CredentialRef(reference),
                    {s for c in manifest.capabilities for s in c.scopes},
                    manifest.base_url,
                )
            self.accounts[alias] = account
        self.mount = self.h.ensure_connections()
        self.scopes = (
            "heartbeat",
            "desktop:connect",
            "desktop:inspect",
            "desktop:text",
            *("connectors:" + risk.value for risk in RiskLevel),
            "control:inspect:" + self.mount.node_id,
            "control:approve:" + self.mount.node_id,
            "control:cancel:" + self.mount.node_id,
        )
        self.h.grid.register(Node("communication-desktop", NodeRole.DESKTOP, self.scopes))
        self.session = self.h.grid.pair("communication-desktop", self.scopes)
        self.desktop = Desktop(
            self.h.runtime, PersonalPolicy(self.h.store), self.h.executive.targets
        )
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        encoded = base64.b64encode(
            self.key.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode()
        self.desktop.register_owner_key(self.session, encoded, owner_authorized=True)

    def call(self, operation, payload):
        return self.desktop.request(
            self.session,
            {
                "version": 1,
                "request_id": new_id(),
                "operation": operation,
                "payload": payload,
            },
        )

    def ask(self, text):
        return self.call("interact", {"mode": "Ask", "text": text, "context_id": ""})

    def approval(self, task_id):
        review = self.call("challenge", {"operation": "approve", "task_id": task_id})
        claim = json.loads(base64.b64decode(review["signing_payload"]))
        self.assertEqual(
            claim["display_digest"],
            display_digest(
                "approve",
                review["scope"],
                review["target"],
                review["review"],
                review["exact_request"],
            ),
        )
        signature = self.key.sign(
            base64.b64decode(review["signing_payload"]),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        return review, {
            "challenge_id": review["challenge_id"],
            "signature": base64.b64encode(signature).decode(),
        }

    def execute(self, text):
        before = len(self.provider.calls)
        view = self.ask(text)
        self.assertEqual("planned", view["state"], view)
        self.assertEqual("Ask", view["mode"])
        self.assertEqual(before, len(self.provider.calls))
        review, signed = self.approval(view["task_id"])
        self.assertIn("account_generation", review["review"])
        result = self.call("complete", signed)
        self.assertNotIn("retry", result["actions"])
        return result

    def test_gitlab_issue_signed_exact_review_and_project_local_readback(self):
        instruction = (
            'create gitlab issue using Code in project 51 titled "Issue" '
            'body "Private marker" visibility confidential'
        )
        view = self.ask(instruction)
        self.assertEqual("planned", view["state"], view)
        self.assertEqual([], self.provider.calls)
        review, signed = self.approval(view["task_id"])
        parameters = json.loads(review["review"])["parameters"]
        self.assertEqual({"project": "51"}, parameters["path"])
        self.assertIs(True, parameters["body"]["confidential"])
        result = self.call("complete", signed)
        self.assertEqual("verified", result["state"], result)
        self.assertEqual(
            [("POST", "/api/v4/projects/51/issues"), ("GET", "/api/v4/projects/51/issues/7")],
            [(method, path) for method, path, _ in self.provider.calls],
        )
        resource = self.provider.resources["/api/v4/projects/51/issues/7"]
        self.assertNotEqual(resource["id"], resource["iid"])
        read = self.execute("read gitlab issue 7 using Code in project 51")
        self.assertEqual("partially_verified", read["state"])
        self.assertIn("Private marker", read["response"])
        self.assertEqual("REPORTED", read["response_status"])

    def test_gitlab_reads_accept_read_api_without_api_or_mutation_authority(self):
        account = self.accounts["Code"]
        binding = account.services["gitlab.api"]
        self.h.accounts.bind(
            account.id,
            "gitlab.api",
            CredentialRef(binding.credential_ref),
            {"openid", "read_api"},
            "https://gitlab.com",
        )
        self.mount.refresh()
        for instruction in (
            "list gitlab projects using Code",
            "list gitlab issues using Code in project 51",
            "read gitlab issue 7 using Code in project 51",
        ):
            result = self.execute(instruction)
            self.assertEqual("partially_verified", result["state"], result)
            self.assertEqual("GET", self.provider.calls[-1][0])
        prepared = prepare(self.h, "list gitlab issues using Code in project 51")
        self.assertEqual(
            {"state": "opened", "per_page": 10, "page": 1}, prepared.review["parameters"]["query"]
        )
        with self.assertRaises((ValueError, PermissionError)):
            prepare(
                self.h,
                'create gitlab issue using Code in project 51 titled "Issue" '
                'body "Text" visibility project',
            )
        self.assertTrue(all(method == "GET" for method, _, _ in self.provider.calls))

    def test_gitlab_pagination_is_explicit_unknown_or_bounded_without_following_links(self):
        self.provider.resources["/api/v4/projects/51/issues"] = [{"id": 9001, "iid": 7}]
        for header, expected in (
            ("2", {"next_page": 2, "complete": False}),
            ("", {"next_page": None, "complete": True}),
            (None, {"next_page": None, "complete": None}),
            ("https://other.example/", {"next_page": None, "complete": None}),
            ("0", {"next_page": None, "complete": None}),
        ):
            with self.subTest(header=header):
                self.provider.response_headers = {} if header is None else {"X-Next-Page": header}
                before = len(self.provider.calls)
                result = self.execute("list gitlab issues using Code in project 51 page 2")
                self.assertEqual("partially_verified", result["state"])
                self.assertEqual(expected, json.loads(result["response"])["pagination"])
                self.assertEqual(1, len(self.provider.calls) - before)
                query = parse_qs(urlsplit(self.provider.requests[-1][0]).query)
                self.assertEqual(["2"], query["page"])
                self.assertEqual(["10"], query["per_page"])

    def test_gitlab_readback_requires_typed_iid_project_fields_and_visibility(self):
        for change in (
            {"iid": 8},
            {"iid": True},
            {"iid": "7"},
            {"project_id": 52},
            {"project_id": True},
            {"title": "Other"},
            {"description": "Other"},
            {"confidential": False},
            {"state": "closed"},
        ):
            with self.subTest(change=change):
                self.provider.transform = lambda method, value, change=change: (
                    {**value, **change} if method == "GET" else value
                )
                result = self.execute(
                    'create gitlab issue using Code in project 51 titled "Issue" '
                    'body "Text" visibility confidential'
                )
                self.assertEqual("failed", result["state"], result)

    def test_gitlab_malformed_mutation_iid_never_selects_another_resource(self):
        for iid in (None, True, 0, -1, "7", "../7", 2**63):
            with self.subTest(iid=iid):
                self.provider.transform = lambda method, value, iid=iid: {**value, "iid": iid}
                before = len(self.provider.calls)
                result = self.execute(
                    'create gitlab issue using Code in project 51 titled "Issue" '
                    'body "Text" visibility project'
                )
                self.assertNotEqual("verified", result["state"])
                self.assertEqual(1, len(self.provider.calls) - before)

    def test_gitlab_uncertain_saved_issue_is_not_replayed(self):
        self.provider.fail_after_post = True
        view = self.ask(
            'create gitlab issue using Code in project 51 titled "Issue" '
            'body "Text" visibility project'
        )
        _, signed = self.approval(view["task_id"])
        self.assertNotEqual("verified", self.call("complete", signed)["state"])
        self.assertIn("/api/v4/projects/51/issues/7", self.provider.resources)
        self.h.runtime.run(view["task_id"], self.h.executive.targets)
        with self.assertRaises((PermissionError, StateConflict)):
            self.call("complete", signed)
        self.assertEqual(1, len(self.provider.calls))

    def test_gitlab_bad_account_or_resource_fields_have_no_effect(self):
        for instruction in (
            'create gitlab issue using Google in project 51 titled "Issue" '
            'body "Text" visibility project',
            'create gitlab issue using Code in project ../51 titled "Issue" '
            'body "Text" visibility project',
            'create gitlab issue using Code in project 0 titled "Issue" '
            'body "Text" visibility project',
            'create gitlab issue using Code in project 51 titled "Bad\\nTitle" '
            'body "Text" visibility project',
            'create gitlab issue using Code in project 51 titled "Issue" body "Text"',
            "read gitlab issue ../7 using Code in project 51",
        ):
            with (
                self.subTest(instruction=instruction),
                self.assertRaises((ValueError, PermissionError)),
            ):
                prepare(self.h, instruction)
        self.assertEqual([], self.provider.calls)
        self.assertEqual({}, self.h.connectors.requests)

    def test_meet_signed_creation_and_read_use_correlated_resource_name(self):
        view = self.ask("create meet space using Google access restricted")
        self.assertEqual("planned", view["state"], view)
        self.assertEqual([], self.provider.calls)
        review, signed = self.approval(view["task_id"])
        self.assertEqual(
            {"path": {}, "body": {"config": {"accessType": "RESTRICTED"}}},
            json.loads(review["review"])["parameters"],
        )
        result = self.call("complete", signed)
        self.assertEqual("verified", result["state"], result)
        self.assertEqual(
            [("POST", "/v2/spaces"), ("GET", "/v2/spaces/SyntheticSpace")],
            [(method, path) for method, path, _ in self.provider.calls],
        )
        self.assertNotIn("id", self.provider.resources["/v2/spaces/SyntheticSpace"])
        read = self.execute("read meet space SyntheticSpace using Google")
        self.assertEqual("partially_verified", read["state"])
        self.assertEqual("REPORTED", read["response_status"])
        self.assertIn("https://meet.google.com/abc-defg-hij", read["response"])

    def test_meet_invalid_mutation_identity_blocks_readback_without_retry(self):
        for name in (None, "other/Foreign", "spaces/../foreign", "spaces/a/b", "spaces/"):
            with self.subTest(name=name):
                self.provider.transform = lambda method, value, name=name: {**value, "name": name}
                before = len(self.provider.calls)
                result = self.execute("create meet space using Google access restricted")
                self.assertNotEqual("verified", result["state"])
                self.assertEqual(1, len(self.provider.calls) - before)
                self.assertNotIn("retry", result["actions"])

    def test_meet_readback_identity_access_and_join_uri_must_match(self):
        for change in (
            {"name": "spaces/OtherSpace"},
            {"config": {"accessType": "OPEN"}},
            {"config": None},
            {"config": []},
            {"meetingUri": "https://other.example/abc-defg-hij"},
            {"meetingCode": "invalid"},
        ):
            with self.subTest(change=change):
                self.provider.transform = lambda method, value, change=change: (
                    {**value, **change} if method == "GET" else value
                )
                result = self.execute("create meet space using Google access restricted")
                self.assertEqual("failed", result["state"], result)
                self.assertEqual(["POST", "GET"], [c[0] for c in self.provider.calls[-2:]])

    def test_meet_requires_exact_account_scope_and_syntax(self):
        for text in (
            "create meet space using Work access restricted",
            "create meet space using Google access open",
            "create meet space using unknown access restricted",
            "read meet space ../Foreign using Google",
        ):
            with self.subTest(text=text), self.assertRaises((ValueError, PermissionError)):
                prepare(self.h, text)
        account = self.accounts["Google"]
        service = account.services["google.meet"]
        self.h.accounts.bind(
            account.id,
            "google.meet",
            CredentialRef(service.credential_ref),
            {"openid"},
            "https://meet.googleapis.com",
        )
        self.mount.refresh()
        with self.assertRaises((ValueError, PermissionError)):
            prepare(self.h, "create meet space using Google access restricted")
        self.assertEqual([], self.provider.calls)
        self.assertEqual({}, self.h.connectors.requests)

    def test_meet_uncertain_after_effect_is_not_replayed(self):
        self.provider.fail_after_post = True
        view = self.ask("create meet space using Google access restricted")
        _, signed = self.approval(view["task_id"])
        result = self.call("complete", signed)
        self.assertNotEqual("verified", result["state"])
        self.assertIn("/v2/spaces/SyntheticSpace", self.provider.resources)
        self.assertNotIn("retry", result["actions"])
        self.h.runtime.run(view["task_id"], self.h.executive.targets)
        with self.assertRaises((PermissionError, StateConflict)):
            self.call("complete", signed)
        self.assertEqual(1, len(self.provider.calls))

    def test_meet_generation_rotation_denies_reviewed_creation(self):
        view = self.ask("create meet space using Google access restricted")
        account = self.accounts["Google"]
        service = account.services["google.meet"]
        self.h.accounts.bind(
            account.id,
            "google.meet",
            CredentialRef(service.credential_ref),
            service.scopes,
            "https://meet.googleapis.com",
        )
        self.mount.refresh()
        _, signed = self.approval(view["task_id"])
        self.assertNotEqual("verified", self.call("complete", signed)["state"])
        self.assertEqual([], self.provider.calls)

    def test_google_draft_send_and_calendar_independent_saved_resource_readback(self):
        for text in (
            "draft email using Google to friend@example.com "
            'subject "Subject" body "Private marker"',
            'send email using Google to friend@example.com subject "Subject" body "Private marker"',
            'create calendar event using Google titled "Private marker" '
            "from 2026-10-22T09:00:00+05:30 to 2026-10-22T10:00:00+05:30 with friend@example.com",
        ):
            with self.subTest(text=text):
                result = self.execute(text)
                self.assertEqual("verified", result["state"], result)
                self.assertEqual(["POST", "GET"], [c[0] for c in self.provider.calls[-2:]])
                self.assertEqual({}, self.h.connectors.requests)
                self.assertEqual({}, self.h.connectors.outcomes)
        durable = json.dumps(self.h.store.db.execute("SELECT data FROM records").fetchall())
        durable += json.dumps(self.h.store.db.execute("SELECT data FROM audit").fetchall())
        self.assertNotIn("Private marker", durable)
        self.assertNotIn("friend@example.com", durable)
        self.assertEqual(
            0, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )

    def test_graph_draft_and_calendar_independent_readback_send_stays_partial(self):
        for text in (
            'draft email using Work to friend@example.com subject "Subject" body "Private marker"',
            'create calendar event using Work titled "Appointment" '
            "from 2026-10-22T09:00:00Z to 2026-10-22T10:00:00Z with friend@example.com",
        ):
            self.assertEqual("verified", self.execute(text)["state"])
        result = self.execute(
            'send email using Work to friend@example.com subject "Subject" body "Private marker"'
        )
        self.assertEqual("partially_verified", result["state"])
        self.assertTrue(self.provider.calls[-1][1].endswith("sendMail"))

    def test_graph_day_brief_reads_expanded_occurrences_over_real_http(self):
        stamp = datetime.fromtimestamp(time() + 600, UTC).isoformat()
        end = datetime.fromtimestamp(time() + 1200, UTC).isoformat()
        self.provider.resources["/v1.0/me/calendar/calendarView"] = {
            "value": [
                {
                    "id": identifier,
                    "subject": "Recurring appointment",
                    "start": {"dateTime": stamp},
                    "end": {"dateTime": end},
                    "isCancelled": False,
                    "body": "unselected occurrence detail",
                }
                for identifier in ("occurrence-one", "exception-two")
            ],
            "@odata.nextLink": "synthetic-next-page",
        }
        account = self.accounts["Work"]
        world = self.h.world
        world.configure_native_source(
            {
                "id": "work-day",
                "adapter": "calendar",
                "entity_id": "work-calendar",
                "interval_seconds": 30,
                "retain": False,
                "retention_seconds": 3600,
                "calendar_id": "primary",
                "horizon_seconds": 86400,
                "account_id": account.id,
                "account_generation": account.generation,
            },
            owner_authorized=True,
        )
        world.sentry.configure(
            SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, ("work-day",)),
            owner_authorized=True,
        )
        self.assertEqual(1, world.tick()["polled"])
        self.assertEqual([("GET", "/v1.0/me/calendar/calendarView", None)], self.provider.calls)
        brief = world.brief()
        self.assertEqual(1, len(brief["schedule"]["overlaps"]))
        self.assertTrue(brief["schedule"]["incomplete"])
        self.assertNotIn("unselected occurrence detail", brief["sources"][0]["value"])
        self.assertEqual(
            0, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )
        self.h.accounts.disconnect(account.id)
        self.assertEqual("unavailable", world.brief()["sources"][0]["state"])
        self.assertEqual(1, len(self.provider.calls))

    def test_lists_and_reads_remain_reported_transient_results(self):
        for alias in ("Google", "Work"):
            result = self.execute("list email using " + alias)
            self.assertEqual("partially_verified", result["state"])
            self.assertIn("synthetic-resource", result["response"])
            self.assertEqual("REPORTED", result["response_status"])

    def test_contacts_use_selected_account_bounded_fields_and_explicit_pagination(self):
        for alias, path, collection, token in (
            ("Google", "/v1/people/me/connections", "connections", "nextPageToken"),
            ("Work", "/v1.0/me/contacts", "value", "@odata.nextLink"),
        ):
            with self.subTest(alias=alias):
                self.provider.resources[path] = {
                    collection: [{"id": "synthetic-contact", "displayName": "Private contact"}],
                    token: "more-contacts-exist",
                }
                result = self.execute("list contacts using " + alias)
                self.assertEqual("partially_verified", result["state"])
                self.assertEqual("REPORTED", result["response_status"])
                self.assertIn("Private contact", result["response"])
                self.assertIn("more-contacts-exist", result["response"])
                uri, authorization = self.provider.requests[-1]
                query = parse_qs(urlsplit(uri).query)
                self.assertEqual(path, urlsplit(uri).path)
                if alias == "Google":
                    self.assertEqual(
                        {"pageSize": ["10"], "personFields": ["names,emailAddresses,phoneNumbers"]},
                        query,
                    )
                    self.assertEqual("Bearer synthetic-secret-googlegoogle.contacts", authorization)
                else:
                    self.assertEqual(["10"], query["$top"])
                    self.assertEqual(
                        ["id,displayName,emailAddresses,businessPhones,homePhones,mobilePhone"],
                        query["$select"],
                    )
                    self.assertEqual("Bearer synthetic-secret-workmicrosoft.graph", authorization)
        self.assertEqual(["GET", "GET"], [c[0] for c in self.provider.calls])
        for family in ("plan", "objective", "result", "evidence"):
            self.assertNotIn("Private contact", json.dumps(self.h.store.all(family)))
        self.assertEqual(
            0, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )

    def test_exact_contact_read_uses_provider_resource_id(self):
        for alias, identifier, path in (
            ("Google", "people/c123", "/v1/people/c123"),
            ("Work", "AAMk-contact=", "/v1.0/me/contacts/AAMk-contact%3D"),
        ):
            with self.subTest(alias=alias):
                self.provider.resources[path] = {"displayName": "Private contact"}
                result = self.execute(f"read contact {identifier} using {alias}")
                self.assertEqual("partially_verified", result["state"])
                self.assertIn("Private contact", result["response"])
                self.assertEqual(("GET", path, None), self.provider.calls[-1])

    def test_contact_revocation_before_signed_read_prevents_provider_io(self):
        view = self.ask("list contacts using Google")
        _, signed = self.approval(view["task_id"])
        self.h.accounts.disconnect(self.accounts["Google"].id)
        self.mount.refresh()
        with self.assertRaises(PermissionError):
            self.call("complete", signed)
        self.assertEqual([], self.provider.calls)

    def test_contact_read_requires_its_own_service_scope(self):
        account = self.accounts["Work"]
        self.h.accounts.bind(
            account.id,
            "microsoft.graph",
            CredentialRef("workmicrosoft.graph"),
            ("Mail.Read",),
            "https://graph.microsoft.com",
        )
        self.mount.refresh()
        self.assertEqual("blocked", self.ask("list contacts using Work")["state"])
        self.assertEqual([], self.provider.calls)

    def test_contact_alias_ambiguity_never_selects_an_account(self):
        self.h.accounts.add("google", "fixture", "another-owner", "Google", verified=True)
        self.assertEqual("blocked", self.ask("list contacts using Google")["state"])
        self.assertEqual([], self.provider.calls)
        self.assertEqual({}, self.h.connectors.requests)

    def test_invalid_contact_request_never_stages_or_executes(self):
        for instruction in (
            "list contacts using unknown",
            "read contact ../private using Google",
            "read contact people/c123 using Work",
            "read contact c123 using Google and send email",
            "list contacts using Google page https://foreign.example",
        ):
            with self.subTest(instruction=instruction):
                self.assertEqual("blocked", self.ask(instruction)["state"])
        self.assertEqual([], self.provider.calls)
        self.assertEqual({}, self.h.connectors.requests)
        self.assertEqual([], self.h.store.all("task"))

    def test_task_creation_uses_exact_list_account_and_independent_get(self):
        for alias in ("Google", "Work"):
            with self.subTest(alias=alias):
                result = self.execute(
                    f'create task using {alias} in list selected-list titled "Prepare meeting" '
                    'due 2026-10-25 notes "Private marker"'
                )
                self.assertEqual("verified", result["state"], result)
                post, get = self.provider.calls[-2:]
                self.assertEqual("POST", post[0])
                self.assertEqual("GET", get[0])
                self.assertIn("/selected-list/tasks", post[1])
                self.assertEqual(post[1] + "/synthetic-resource", get[1])
                self.assertEqual({}, self.h.connectors.requests)
                self.assertEqual({}, self.h.connectors.outcomes)
        for family in ("objective", "plan", "result"):
            self.assertNotIn("Private marker", json.dumps(self.h.store.all(family)))
        self.assertEqual(
            0, self.h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0]
        )

    def test_task_list_discovery_is_bounded_read_only_and_transient(self):
        for alias in ("Google", "Work"):
            for instruction in (
                f"list task lists using {alias}",
                f"list tasks using {alias} in list selected-list",
            ):
                result = self.execute(instruction)
                self.assertEqual("partially_verified", result["state"], result)
                self.assertEqual("GET", self.provider.calls[-1][0])
                self.assertEqual("REPORTED", result["response_status"])

    def test_task_readback_mismatch_never_verifies(self):
        self.provider.tamper = True
        for alias in ("Google", "Work"):
            result = self.execute(
                f'create task using {alias} in list selected-list titled "Prepare meeting" '
                'due 2026-10-25 notes "Private marker"'
            )
            self.assertNotEqual("verified", result["state"])

    def test_task_account_rotation_blocks_before_provider_io(self):
        view = self.ask(
            'create task using Work in list selected-list titled "Prepare meeting" '
            'due 2026-10-25 notes "Private marker"'
        )
        account = self.accounts["Work"]
        self.h.accounts.bind(
            account.id,
            "microsoft.graph",
            CredentialRef("workmicrosoft.graph"),
            account.services["microsoft.graph"].scopes,
            "https://graph.microsoft.com",
        )
        self.mount.refresh()
        _, signature = self.approval(view["task_id"])
        self.assertNotEqual("verified", self.call("complete", signature)["state"])
        self.assertEqual([], self.provider.calls)

    def test_uncertain_task_creation_is_not_retried_or_replayed(self):
        self.provider.fail = True
        view = self.ask(
            'create task using Google in list selected-list titled "Prepare meeting" '
            'due 2026-10-25 notes "Private marker"'
        )
        _, signed = self.approval(view["task_id"])
        result = self.call("complete", signed)
        self.assertNotEqual("verified", result["state"])
        self.assertNotIn("retry", result["actions"])
        self.h.runtime.run(view["task_id"], self.h.executive.targets)
        with self.assertRaises((PermissionError, StateConflict)):
            self.call("complete", signed)
        self.assertEqual(1, len(self.provider.calls))

    def test_invalid_task_fields_have_no_staged_input_or_provider_effect(self):
        for instruction in (
            'create task using Work in list selected-list titled "Title" '
            'due 2026-02-30 notes "Text"',
            'create task using Work in list ../foreign titled "Title" due 2026-10-25 notes "Text"',
            'create task using Work in list selected-list titled "Bad\\nTitle" '
            'due 2026-10-25 notes "Text"',
            'create task using unknown in list selected-list titled "Title" '
            'due 2026-10-25 notes "Text"',
            'create task using Work in list selected-list titled "Title" '
            'due 2026-10-25T09:00:00Z notes "Text"',
            'create task using Work in list selected-list titled "Title" '
            'due 2026-10-25 notes "Text" and send mail',
        ):
            with self.subTest(instruction=instruction):
                self.assertEqual("blocked", self.ask(instruction)["state"])
        self.assertEqual([], self.provider.calls)
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual({}, self.h.connectors.requests)

    def test_task_due_readback_preserves_date_and_rejects_false_utc_and_completion(self):
        expected = {"title": "Title", "notes": "Text", "due": "2026-10-25"}
        graph = {
            "title": "Title",
            "body": {"contentType": "text", "content": "Text"},
            "dueDateTime": {"dateTime": "2026-10-25T00:00:00", "timeZone": "UTC"},
            "status": "notStarted",
        }
        self.assertTrue(matches("microsoft.todo.tasks.create", graph, expected))
        graph["dueDateTime"]["dateTime"] += "+05:30"
        self.assertFalse(matches("microsoft.todo.tasks.create", graph, expected))
        google = {
            "title": "Title",
            "notes": "Text",
            "due": "2026-10-25T00:00:00.000Z",
            "status": "needsAction",
        }
        self.assertTrue(matches("google.tasks.create", google, expected))
        google["deleted"] = True
        self.assertFalse(matches("google.tasks.create", google, expected))
        google["deleted"], google["status"] = False, "completed"
        self.assertFalse(matches("google.tasks.create", google, expected))

    def test_readback_lie_never_verifies(self):
        self.provider.tamper = True
        for alias in ("Google", "Work"):
            result = self.execute(
                f'draft email using {alias} to friend@example.com subject "Subject" body "Text"'
            )
            self.assertNotEqual("verified", result["state"])

    def test_account_generation_change_before_approval_cannot_use_new_credential(self):
        view = self.ask(
            'draft email using Work to friend@example.com subject "Subject" body "Text"'
        )
        account = self.accounts["Work"]
        self.h.accounts.bind(
            account.id,
            "microsoft.graph",
            CredentialRef("workmicrosoft.graph"),
            account.services["microsoft.graph"].scopes,
            "https://graph.microsoft.com",
        )
        self.mount.refresh()
        _, signature = self.approval(view["task_id"])
        self.assertNotEqual("verified", self.call("complete", signature)["state"])
        self.assertEqual([], self.provider.calls)

    def test_account_revocation_and_policy_change_during_get_withdraw_proof(self):
        for change in ("account", "policy"):
            with self.subTest(change=change):

                def revoke(change=change):
                    if change == "account":
                        self.h.accounts.disconnect(self.accounts["Google"].id)
                    else:
                        now = self.h.grid.clock()
                        self.h.store.put(
                            "personal_policy",
                            "deny-read",
                            {
                                "id": "deny-read",
                                "capability": "connectors:read",
                                "effect": "deny",
                                "source": "owner",
                                "created_at": now,
                                "updated_at": now,
                                "conditions": {},
                            },
                        )

                self.provider.after_get = revoke
                alias = "Google" if change == "account" else "Work"
                result = self.execute(
                    f'draft email using {alias} to friend@example.com subject "Subject" body "Text"'
                )
                self.assertNotEqual("verified", result["state"])

    def test_desktop_readback_rechecks_current_owner_and_executor_scopes(self):
        for principal, identifier in (
            ("session", self.session.id),
            ("node", self.session.node_id),
            ("session", self.mount.session.id),
            ("node", self.mount.node_id),
        ):
            for phase in ("before", "during"):
                with self.subTest(principal=principal, identifier=identifier, phase=phase):
                    original = self.h.store.get(principal, identifier)

                    def revoke(principal=principal, identifier=identifier):
                        row = self.h.store.get(principal, identifier)
                        self.h.store.put(
                            principal,
                            identifier,
                            {**row, "scopes": [s for s in row["scopes"] if s != "connectors:read"]},
                        )

                    before = len(self.provider.calls)
                    try:
                        self.provider.after_get = revoke if phase == "during" else None
                        if phase == "before":
                            revoke()
                        result = self.execute(
                            "draft email using Work to friend@example.com "
                            'subject "Subject" body "Text"'
                        )
                        self.assertEqual("partially_verified", result["state"], result)
                        self.assertEqual(
                            ["POST", "GET"] if phase == "during" else ["POST"],
                            [c[0] for c in self.provider.calls[before:]],
                        )
                    finally:
                        self.provider.after_get = None
                        self.h.store.put(principal, identifier, original)

    def test_desktop_target_scoped_read_policy_withdraws_proof_during_get(self):
        def revoke():
            now = self.h.grid.clock()
            self.h.store.put(
                "personal_policy",
                "target-read-denial",
                {
                    "id": "target-read-denial",
                    "capability": "connectors:read",
                    "effect": "deny",
                    "source": "owner",
                    "created_at": now,
                    "updated_at": now,
                    "conditions": {"target": self.mount.node_id},
                },
            )

        self.provider.after_get = revoke
        result = self.execute(
            'draft email using Work to friend@example.com subject "Subject" body "Text"'
        )
        self.assertEqual("partially_verified", result["state"], result)
        self.assertEqual(["POST", "GET"], [c[0] for c in self.provider.calls])

    def test_uncertain_mutation_has_no_retry_or_replay(self):
        self.provider.fail = True
        view = self.ask(
            'send email using Google to friend@example.com subject "Subject" body "Text"'
        )
        _, signed = self.approval(view["task_id"])
        result = self.call("complete", signed)
        self.assertNotEqual("verified", result["state"])
        self.assertNotIn("retry", result["actions"])
        self.h.runtime.run(view["task_id"], self.h.executive.targets)
        with self.assertRaises((PermissionError, StateConflict)):
            self.call("complete", signed)
        self.assertEqual(1, len(self.provider.calls))

    def test_reject_ambiguous_headers_and_times_before_task_or_effect(self):
        for text in (
            "send email using Work to friend@example.com "
            'subject "Bad\\nBcc: hidden@example.com" body "Text"',
            'send email using unknown to friend@example.com subject "Subject" body "Text"',
            'send email using Work to Friend<friend@example.com> subject "Subject" body "Text"',
            'create calendar event using Work titled "Event" '
            "from 2026-10-22T09:00 to 2026-10-22T10:00",
            'create calendar event using Work titled "Event" '
            "from 2026-10-22T10:00Z to 2026-10-22T09:00Z",
            "send email using Work to friend@example.com "
            'subject "Subject" body "Text" and delete mail',
        ):
            with self.subTest(text=text):
                self.assertEqual("blocked", self.ask(text)["state"])
        self.assertEqual([], self.provider.calls)
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual({}, self.h.connectors.requests)
        self.assertIsNone(prepare(self.h, "What did we decide?"))

    def test_review_tamper_requires_new_signed_review(self):
        view = self.ask(
            'draft email using Work to friend@example.com subject "Subject" body "Text"'
        )
        _, signed = self.approval(view["task_id"])
        self.h.store.transient[view["task_id"]]["review_parameters"]["account_generation"] += 1
        with self.assertRaises(StateConflict):
            self.call("complete", signed)
        self.assertEqual([], self.provider.calls)

    def test_dispatch_input_cannot_differ_from_the_signed_review(self):
        view = self.ask(
            'draft email using Work to friend@example.com subject "Subject" body "Text"'
        )
        _, signed = self.approval(view["task_id"])
        reference = self.h.store.transient[view["task_id"]]["parameters"]["request_ref"]
        self.h.connectors.requests[reference]["body"]["toRecipients"][0]["emailAddress"][
            "address"
        ] = "changed@example.com"
        self.assertNotEqual("verified", self.call("complete", signed)["state"])
        self.assertEqual([], self.provider.calls)

    def test_known_credential_is_rejected_before_mime_encoding(self):
        result = self.ask(
            'draft email using Google to friend@example.com subject "Subject" '
            'body "synthetic-secret-googlegoogle.gmail"'
        )
        self.assertEqual("blocked", result["state"])
        self.assertEqual([], self.provider.calls)
        self.assertEqual({}, self.h.connectors.requests)

    def test_event_readback_normalizes_offset_without_claiming_delivery(self):
        self.assertTrue(
            matches(
                "google.calendar.events.create",
                {
                    "summary": "Event",
                    "start": {"dateTime": "2026-10-22T03:30:00Z"},
                    "end": {"dateTime": "2026-10-22T04:30:00Z"},
                },
                {
                    "title": "Event",
                    "start": "2026-10-22T09:00:00+05:30",
                    "end": "2026-10-22T10:00:00+05:30",
                    "attendees": [],
                },
            )
        )

    def cloud_client(self, core, server, node, *, connector=True):
        public = base64.b64encode(
            self.key.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode()

        def sign(body):
            return base64.b64encode(
                self.key.sign(
                    body,
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                    hashes.SHA256(),
                )
            ).decode()

        invitation = create_invitation(
            core,
            node,
            "mobile",
            "installation-" + node,
            public,
            retain=True,
            owner_public_key=public,
            connector_control=connector,
        )
        status, session = request(
            core.config,
            "/v2/grid/enroll",
            headers={"Content-Type": "application/json"},
            body={
                "version": 2,
                "challenge_id": invitation["challenge_id"],
                "signature": sign(base64.b64decode(invitation["signing_payload"])),
            },
        )
        self.assertEqual(200, status, session)

        def call(operation, payload, request_id=None, expected=200):
            body = {
                "version": 2,
                "operation": operation,
                "payload": payload,
                "request_id": request_id or new_id(),
            }
            nonce, instant = new_id(), str(int(time() * 1000))
            status, response = request(
                core.config,
                "/v2/grid/request",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + session["token"],
                    "X-Oscar-Node": node,
                    "X-Oscar-Session": session["session_id"],
                    "X-Oscar-Nonce": nonce,
                    "X-Oscar-Time": instant,
                    "X-Oscar-Signature": sign(
                        request_proof(
                            node,
                            session["session_id"],
                            nonce,
                            instant,
                            json.dumps(body).encode(),
                        )
                    ),
                },
            )
            self.assertEqual(expected, status, response)
            return response

        return session, call, sign

    def cloud(self, service="microsoft.graph"):
        root = self.root / "cloud"
        root.mkdir()
        core = CloudCore(
            CloudConfig.load(configuration(root)), initialize=True, start_services=False
        )
        self.addCleanup(core.close)
        core.harness.connectors.secrets = VaultResolver(self.vault)
        provider, alias = {
            "google.meet": ("google", "Google"),
            "gitlab.api": ("gitlab", "Code"),
        }.get(service, ("microsoft", "Work"))
        account = core.harness.accounts.add(provider, "fixture", alias, alias, verified=True)
        manifest = next(m for m in account_manifests() if m.id == service)
        self.cloud_account = core.harness.accounts.bind(
            account.id,
            manifest.id,
            CredentialRef((alias + service).lower()),
            {s for c in manifest.capabilities for s in c.scopes},
            manifest.base_url,
        )
        server = CloudHTTPServer(core)
        server.start()
        self.addCleanup(server.close)
        return core, server

    def test_cloud_native_request_actual_http_signature_readback_and_private_output(self):
        self.check_cloud_native_request(
            'draft email using Work to friend@example.com subject "Subject" body "Private marker"'
        )

    def test_cloud_task_creation_actual_http_signature_readback_and_private_output(self):
        self.check_cloud_native_request(
            'create task using Work in list selected-list titled "Prepare meeting" '
            'due 2026-10-25 notes "Private marker"'
        )

    def test_cloud_meet_creation_actual_http_signature_resource_name_and_private_output(self):
        self.check_cloud_native_request(
            "create meet space using Google access restricted", service="google.meet"
        )

    def test_cloud_gitlab_issue_actual_http_signature_iid_and_private_output(self):
        self.check_cloud_native_request(
            'create gitlab issue using Code in project 51 titled "Issue" '
            'body "Private marker" visibility confidential',
            service="gitlab.api",
        )

    def check_cloud_native_request(self, instruction, service="microsoft.graph"):
        core, server = self.cloud(service)
        marker = "SyntheticSpace" if service == "google.meet" else "Private marker"
        session, call, sign = self.cloud_client(core, server, "communication-phone")
        _, other, _ = self.cloud_client(core, server, "communication-other", connector=False)
        payload = {
            "kind": "text",
            "text": instruction,
            "target": core.config.core_id,
            "parameters": {},
            "retain": True,
        }
        other("submit", payload, expected=403)
        self.assertEqual([], self.provider.calls)
        request_id = new_id()
        view = call("submit", payload, request_id=request_id)
        self.assertTrue(view["approval_required"])
        task_id = view["task_id"]
        self.assertEqual(task_id, call("submit", payload, request_id=request_id)["task_id"])
        self.assertEqual(1, len(core.harness.store.all("remote_task")))
        review = call("challenge", {"operation": "approve", "task_id": task_id})
        self.assertIn("RESTRICTED" if service == "google.meet" else marker, review["review"])
        claim = json.loads(base64.b64decode(review["signing_payload"]))
        self.assertEqual(
            claim["display_digest"],
            display_digest(
                "approve",
                review["scope"],
                review["target"],
                review["review"],
                instruction,
            ),
        )
        signed = {
            "challenge_id": review["challenge_id"],
            "signature": sign(base64.b64decode(review["signing_payload"])),
        }
        call("complete", signed)
        deadline = monotonic() + 10
        while monotonic() < deadline:
            view = call("inspect", {"task_id": task_id})
            if view["state"] in {"verified", "failed", "blocked", "unknown", "cancelled"}:
                break
            sleep(0.05)
        self.assertEqual("verified", view["state"], view)
        self.assertIn(marker, view["result"]["value"])
        self.assertIsNone(other("inspect", {"task_id": task_id})["result"]["value"])
        self.assertEqual(["POST", "GET"], [c[0] for c in self.provider.calls])
        call("complete", signed, expected=403)
        self.assertEqual(task_id, call("submit", payload, request_id=request_id)["task_id"])
        self.assertEqual(2, len(self.provider.calls))
        store = core.harness.store
        self.assertNotIn(marker, json.dumps(store.all("plan")))
        self.assertNotIn(marker, json.dumps(store.all("objective")))
        self.assertNotIn(marker, json.dumps(store.all("result")))
        self.assertEqual(
            session["session_id"], store.get("remote_task", task_id)["requester_session"]
        )

    def test_cloud_readback_rechecks_current_owner_and_executor_scopes(self):
        core, server = self.cloud()
        session, call, sign = self.cloud_client(core, server, "readback-phone")
        mount = core.harness.ensure_connections()
        store = core.harness.store
        for principal, identifier in (
            ("session", session["session_id"]),
            ("node", session["node_id"]),
            ("session", mount.session.id),
            ("node", mount.node_id),
        ):
            with self.subTest(principal=principal, identifier=identifier):
                original = store.get(principal, identifier)

                def revoke(principal=principal, identifier=identifier):
                    row = store.get(principal, identifier)
                    store.put(
                        principal,
                        identifier,
                        {**row, "scopes": [s for s in row["scopes"] if s != "connectors:read"]},
                    )

                before = len(self.provider.calls)
                try:
                    self.provider.after_get = revoke
                    view = call(
                        "submit",
                        {
                            "kind": "text",
                            "target": core.config.core_id,
                            "parameters": {},
                            "retain": True,
                            "text": "draft email using Work to friend@example.com "
                            'subject "Subject" body "Text"',
                        },
                    )
                    task_id = view["task_id"]
                    review = call("challenge", {"operation": "approve", "task_id": task_id})
                    call(
                        "complete",
                        {
                            "challenge_id": review["challenge_id"],
                            "signature": sign(base64.b64decode(review["signing_payload"])),
                        },
                    )
                    for thread in core.remote.threads:
                        thread.join(timeout=10)
                    self.assertEqual("partially_verified", store.task(task_id).state)
                    self.assertEqual(["POST", "GET"], [c[0] for c in self.provider.calls[before:]])
                finally:
                    self.provider.after_get = None
                    store.put(principal, identifier, original)

    def test_cloud_requester_revoked_after_approval_blocks_actual_provider_io(self):
        core, server = self.cloud()
        session, call, sign = self.cloud_client(core, server, "communication-phone")
        payload = {
            "kind": "text",
            "target": core.config.core_id,
            "parameters": {},
            "retain": True,
            "text": 'send email using Work to friend@example.com subject "Subject" body "Text"',
        }
        view = call("submit", payload)
        review = call("challenge", {"operation": "approve", "task_id": view["task_id"]})
        with patch.object(core.remote, "start"):
            call(
                "complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": sign(base64.b64decode(review["signing_payload"])),
                },
            )
        row = core.harness.store.get("session", session["session_id"])
        core.harness.store.put("session", row["id"], {**row, "revoked": True})
        core.remote.start(view["task_id"])
        for thread in core.remote.threads:
            thread.join(timeout=10)
        self.assertNotEqual("verified", core.harness.store.task(view["task_id"]).state)
        self.assertEqual([], self.provider.calls)

    def test_cloud_restart_cannot_recreate_private_connector_input_or_replay(self):
        core, server = self.cloud()
        _, call, _ = self.cloud_client(core, server, "communication-phone")
        view = call(
            "submit",
            {
                "kind": "text",
                "target": core.config.core_id,
                "parameters": {},
                "retain": True,
                "text": (
                    'draft email using Work to friend@example.com subject "Subject" body "Text"'
                ),
            },
        )
        server.close()
        config = core.config
        core.close()
        restarted = CloudCore(config, start_services=False)
        self.addCleanup(restarted.close)
        self.assertEqual({}, restarted.harness.store.transient)
        self.assertEqual("blocked", restarted.harness.store.task(view["task_id"]).state)
        restarted.harness.runtime.run(view["task_id"], restarted.harness.executive.targets)
        self.assertEqual([], self.provider.calls)
