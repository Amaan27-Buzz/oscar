"""Owned urllib errors release response streams without changing failure semantics."""

import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError

from oscar.auth_broker import google_revoke, oauth_request
from oscar.contracts import Envelope
from oscar.discovery import HTTPDiscovery
from oscar.grid import SessionHandle
from oscar.models import Failure, ModelRequest, ProviderError, ProviderSpec
from oscar.oauth_device import post
from oscar.providers import HTTPAdapter
from oscar.retrieval import RetrievalRequest
from oscar.search import TavilySource
from oscar.storage import StateConflict, Store
from oscar.transport import HTTPTransport


class HTTPResourceTests(unittest.TestCase):
    def test_oauth_errors_close_without_exposing_response(self):
        for module, operation, revocation in (
            ("auth_broker", lambda: oauth_request("https://example.invalid/token", {}), False),
            ("oauth_device", lambda: post("/login/device/code", {}), False),
            ("auth_broker", lambda: google_revoke("synthetic-only"), True),
        ):
            with self.subTest(module=module, operation=operation):
                body = io.BytesIO(b"synthetic-private-diagnostic")
                error = HTTPError("https://example.invalid", 401, "private", {}, body)
                with patch("oscar." + module + ".build_opener") as opener:
                    opener.return_value.open.side_effect = error
                    if revocation:
                        self.assertFalse(operation())
                    else:
                        with self.assertRaisesRegex(RuntimeError, "unavailable or rejected"):
                            operation()
                self.assertTrue(body.closed)
                opener.return_value.open.assert_called_once()

    def test_transport_errors_close_and_leave_execution_unverified(self):
        transport = HTTPTransport("http://127.0.0.1:1")
        session = SessionHandle("session", "node", "synthetic-only")
        for method, kind, message in (
            (transport.invoke, "action", "outcome may be unknown"),
            (transport.control, "cancel", "delivery unverified"),
        ):
            with self.subTest(kind=kind):
                body = io.BytesIO(b"synthetic-private-diagnostic")
                error = HTTPError(transport.url, 500, "private", {}, body)
                envelope = Envelope(kind, "node", "session", "task", "correlation", "lease", {}, 0)
                with patch("oscar.transport.build_opener") as opener:
                    opener.return_value.open.side_effect = error
                    with self.assertRaisesRegex(StateConflict, message):
                        method(envelope, session)
                self.assertTrue(body.closed)
                opener.return_value.open.assert_called_once()

    def test_provider_and_discovery_close_with_status_and_retry_after_intact(self):
        provider = ProviderSpec("fixture", "openai", "http://127.0.0.1:1", {}, local=True)
        adapter, discovery = HTTPAdapter("openai"), HTTPDiscovery()
        for client, operation in (
            (
                adapter,
                lambda: adapter.generate(
                    provider,
                    "model",
                    "synthetic-only",
                    ModelRequest("task", "correlation", "x"),
                    1,
                    lambda: None,
                ),
            ),
            (discovery, lambda: discovery.inventory(provider, "fixture", "synthetic-only", 1)),
        ):
            with self.subTest(client=type(client).__name__):
                body = io.BytesIO(b'{"error":{"message":"synthetic-private-diagnostic"}}')
                error = HTTPError(provider.base_url, 429, "private", {"Retry-After": "45"}, body)
                with patch.object(client.opener, "open", side_effect=error) as opened:
                    with self.assertRaises(ProviderError) as caught:
                        operation()
                self.assertTrue(body.closed)
                self.assertEqual(caught.exception.category, Failure.RATE_LIMIT)
                self.assertEqual(caught.exception.http_status, 429)
                self.assertNotIn("private", repr(caught.exception))
                if client is adapter:
                    self.assertEqual(caught.exception.retry_after, 45)
                opened.assert_called_once()

    def test_search_closes_before_failing_capacity_persistence(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        store = Store(Path(directory.name) / "search.sqlite")
        try:
            source = TavilySource(store, {"TAVILY_API_KEY_1": "synthetic-only"})
            body = io.BytesIO(b"synthetic-private-diagnostic")
            error = HTTPError("https://example.invalid", 429, "private", {}, body)
            with (
                patch.object(source.opener, "open", side_effect=error) as opened,
                patch.object(source.pool, "failed", side_effect=RuntimeError("storage failed")),
            ):
                with self.assertRaisesRegex(RuntimeError, "storage failed"):
                    source.search(
                        RetrievalRequest("synthetic current weather"), "tavily-1", lambda: None
                    )
            self.assertTrue(body.closed)
            opened.assert_called_once()
        finally:
            store.close()
