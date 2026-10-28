"""Explicitly synthetic HTTP providers through the real bounded connector adapter."""

import json
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from oscar.connector_providers import load_google
from oscar.connectors import ConnectorError, HTTPSConnector
from oscar.http_client import NoRedirects


class SyntheticProvider:
    def __init__(self):
        self.calls = []
        self.redirect = False
        self.reject_version = False
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.respond()

            def do_POST(self):
                self.respond()

            def do_PATCH(self):
                self.respond()

            def do_PUT(self):
                self.respond()

            def do_DELETE(self):
                self.respond()

            def respond(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                owner.calls.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "body": json.loads(body) if body else None,
                        "authorization": self.headers.get("Authorization"),
                        "if_match": self.headers.get("If-Match"),
                    }
                )
                if owner.redirect:
                    self.send_response(302)
                    self.send_header("Location", "http://127.0.0.1:1/credential-sink")
                    self.end_headers()
                    return
                if owner.reject_version:
                    self.send_response(412)
                    self.end_headers()
                    return
                payload = b'{"id":"synthetic-resource","fixture":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def opener(self):
        owner = self

        class FixtureOpener:
            def open(self, request, timeout):
                # Test-only remapping. Production manifest validation still requires HTTPS.
                url = urlsplit(request.full_url)
                redirected = Request(
                    owner.url + url.path + ("?" + url.query if url.query else ""),
                    data=request.data,
                    headers=dict(request.header_items()),
                    method=request.get_method(),
                )
                return build_opener(NoRedirects()).open(redirected, timeout=timeout)

        return FixtureOpener()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class SyntheticHTTPTests(unittest.TestCase):
    def setUp(self):
        self.provider = SyntheticProvider()

    def tearDown(self):
        self.provider.close()

    def test_all_google_methods_over_actual_synthetic_http(self):
        import re

        root = Path(__file__).resolve().parents[1]
        with patch("oscar.connectors.build_opener", return_value=self.provider.opener()):
            for manifest in load_google(root / "config/google-connectors.json"):
                for spec in manifest.capabilities:
                    params = {"path": {k: "synthetic" for k in re.findall(r"\{(.*?)\}", spec.path)}}
                    if spec.body_required:
                        params["body"] = {"fixture": True}
                    if spec.name in {
                        "google.calendar.events.update",
                        "google.calendar.events.delete",
                    }:
                        params["if_match"] = '"source-version"'
                    if spec.name.endswith("export"):
                        params["query"] = {"mimeType": "text/plain"}
                    payload, _ = HTTPSConnector().request(manifest, spec, params, "synthetic-token")
                    self.assertTrue(payload)
                    self.assertEqual(spec.method, self.provider.calls[-1]["method"])
                    self.assertEqual(params.get("if_match"), self.provider.calls[-1]["if_match"])
                    self.assertEqual(
                        "Bearer synthetic-token", self.provider.calls[-1]["authorization"]
                    )
        self.assertEqual(44, len(self.provider.calls))
        media = next(c for c in self.provider.calls if "alt=media" in c["path"])
        self.assertEqual("GET", media["method"])

    def test_credential_redirect_is_not_followed(self):
        root = Path(__file__).resolve().parents[1]
        manifest = load_google(root / "config/google-connectors.json")[0]
        self.provider.redirect = True
        with patch("oscar.connectors.build_opener", return_value=self.provider.opener()):
            with self.assertRaisesRegex(ConnectorError, "http_failure"):
                HTTPSConnector().request(
                    manifest,
                    manifest.capabilities[0],
                    {"path": {"userId": "me"}},
                    "synthetic-token",
                )
        self.assertEqual(1, len(self.provider.calls))

    def test_calendar_delete_requires_exact_version_and_never_retries_conflict(self):
        from oscar.connectors import endpoint
        from oscar.planner_connectors import ConnectorPlanning

        root = Path(__file__).resolve().parents[1]
        manifest = next(
            m
            for m in load_google(root / "config/google-connectors.json")
            if any(c.name == "google.calendar.events.delete" for c in m.capabilities)
        )
        spec = next(c for c in manifest.capabilities if c.name.endswith("events.delete"))
        arguments = {"path": {"calendarId": "primary", "eventId": "event-1"}}
        self.assertIn("if_match", ConnectorPlanning.http_schema(spec)["required"])
        for tag in (None, "", "*", 'W/"version"', '"a", "b"', '"a\r\nb"', 42):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                endpoint(spec, {**arguments, "if_match": tag})
        with self.assertRaises(ValueError):
            endpoint(spec, arguments)
        self.assertEqual([], self.provider.calls)
        self.provider.reject_version = True
        with patch("oscar.connectors.build_opener", return_value=self.provider.opener()):
            with self.assertRaisesRegex(ConnectorError, "precondition_failed"):
                HTTPSConnector().request(
                    manifest,
                    spec,
                    {**arguments, "if_match": '"observed-version"'},
                    "synthetic-token",
                )
        self.assertEqual(1, len(self.provider.calls))
        self.assertEqual("DELETE", self.provider.calls[0]["method"])
        self.assertEqual('"observed-version"', self.provider.calls[0]["if_match"])
