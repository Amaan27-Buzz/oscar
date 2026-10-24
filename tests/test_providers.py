import json
import unittest
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch
from urllib.error import URLError

from oscar.discovery import HTTPDiscovery
from oscar.models import Failure, Funding, ModelRequest, ProviderError, ProviderSpec
from oscar.providers import HTTPAdapter, rate_limits


class ProviderContractTests(unittest.TestCase):
    """Real loopback HTTP; fixtures prove adapter wire behavior, not hosted integration."""

    def setUp(self):
        self.status = 200
        self.body = {
            "choices": [{"message": {"content": "OSCAR_PROVIDER_OK"}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4},
        }
        self.headers = {}
        self.requests = []
        self.scheduled = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def respond(self):
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length)) if length else None
                # Only the presence of authorization is inspected/retained, never its material.
                outer.requests.append(
                    {
                        "path": self.path,
                        "body": data,
                        "bearer": bool(self.headers.get("Authorization")),
                        "google_key": bool(self.headers.get("x-goog-api-key")),
                    }
                )
                status, body = (
                    outer.scheduled.pop(0) if outer.scheduled else (outer.status, outer.body)
                )
                encoded = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                for key, value in outer.headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            do_POST = respond
            do_GET = respond

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.provider = ProviderSpec("fixture", "openai", self.url, {}, local=True)
        self.request = ModelRequest(
            "fixture-task", "fixture-correlation", "Reply exactly OSCAR_PROVIDER_OK"
        )

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def generate(self, kind="openai", sink=None, request=None):
        return HTTPAdapter(kind).generate(
            self.provider,
            "fixture-model",
            "synthetic-only",
            request or self.request,
            2,
            lambda: None,
            sink,
        )

    def test_openai_wire_contract_usage_and_quota(self):
        self.headers = {
            "x-ratelimit-remaining-requests": "15",
            "x-ratelimit-remaining-tokens": "400",
        }
        response = self.generate()
        self.assertEqual(response.text, "OSCAR_PROVIDER_OK")
        self.assertEqual(response.input_tokens, 8)
        self.assertEqual(response.remaining_requests, 15)
        self.assertEqual(self.requests[0]["path"], "/chat/completions")
        self.assertTrue(self.requests[0]["bearer"])
        self.assertEqual(self.requests[0]["body"]["model"], "fixture-model")

    def test_generic_request_limit_headers_keep_window_unknown(self):
        limits = rate_limits(
            {
                "x-ratelimit-limit": "20",
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "2000",
                "Retry-After": "2",
            },
            "openrouter",
            1000,
        )
        self.assertEqual(limits.request_limit, 20)
        self.assertEqual(limits.remaining_requests, 0)
        self.assertIsNone(limits.requests_reset_at)
        self.assertEqual(limits.request_reset_hint, "2000")
        self.assertEqual(limits.request_window, "UNKNOWN")
        self.assertEqual(limits.retry_after, 2)

    def test_stream_keeps_backing_model_provider_from_earlier_chunk(self):
        self.body = (
            b'data: {"model":"backing/current","provider":"Fixture Provider",'
            b'"choices":[{"delta":{"content":"OSCAR_PROVIDER_OK"}}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        response = self.generate(sink=lambda event: None)
        self.assertEqual(response.actual_model, "backing/current")
        self.assertEqual(response.actual_provider, "Fixture Provider")

    def test_google_native_wire_contract(self):
        self.body = {
            "candidates": [{"content": {"parts": [{"text": "OSCAR_PROVIDER_OK"}]}}],
            "usageMetadata": {"promptTokenCount": 8, "candidatesTokenCount": 4},
        }
        response = self.generate("google")
        self.assertEqual(response.text, "OSCAR_PROVIDER_OK")
        self.assertEqual(response.output_tokens, 4)
        self.assertTrue(self.requests[0]["google_key"])
        self.assertFalse(self.requests[0]["bearer"])
        self.assertEqual(self.requests[0]["path"], "/models/fixture-model:generateContent")

    def test_ollama_native_wire_contract(self):
        self.body = {
            "message": {"content": "OSCAR_PROVIDER_OK"},
            "done": True,
            "prompt_eval_count": 8,
            "eval_count": 4,
        }
        response = self.generate("ollama")
        self.assertEqual(response.text, "OSCAR_PROVIDER_OK")
        self.assertEqual(response.output_tokens, 4)
        self.assertEqual(self.requests[0]["path"], "/chat")
        self.assertEqual(self.requests[0]["body"]["options"]["num_predict"], 128)

    def test_structured_output_validates_actual_json(self):
        self.body["choices"][0]["message"]["content"] = '{"ok":true}'
        response = self.generate(
            request=replace(self.request, required=frozenset({"text", "structured"}))
        )
        self.assertTrue(response.structured_ok)
        self.assertEqual(self.requests[0]["body"]["response_format"], {"type": "json_object"})

    def test_explicit_ollama_thinking_is_typed_and_never_ignored_by_other_adapters(self):
        self.body = {"message": {"content": "OSCAR_PROVIDER_OK"}, "done": True}
        for preference in (None, False, True):
            with self.subTest(preference=preference):
                request = replace(self.request, ollama_think=preference)
                self.generate("ollama", request=request)
                body = self.requests[-1]["body"]
                self.assertEqual(preference is not None, "think" in body)
                if preference is not None:
                    self.assertIs(body["think"], preference)
        before = len(self.requests)
        for adapter in ("openai", "google"):
            with self.assertRaises(ProviderError) as caught:
                self.generate(adapter, request=replace(self.request, ollama_think=False))
            self.assertEqual(Failure.CAPABILITY, caught.exception.category)
        self.assertEqual(before, len(self.requests))
        for invalid in (0, 1, "false", [], {}):
            with self.assertRaises(ValueError):
                replace(self.request, ollama_think=invalid)

    def test_invalid_structured_output_is_failure(self):
        with self.assertRaises(ProviderError) as caught:
            self.generate(request=replace(self.request, required=frozenset({"text", "structured"})))
        self.assertEqual(caught.exception.category, Failure.STRUCTURED)

    def test_empty_or_malformed_200_is_not_provider_success(self):
        for body in ({}, b"not-json", {"choices": []}):
            self.body = body
            with self.assertRaises(ProviderError):
                self.generate()

    def test_inline_200_backing_errors_retain_http_status_and_categorical_cause(self):
        for code, cause in [
            (502, Failure.PROVIDER),
            (401, Failure.ACCESS),
            ("1113", Failure.QUOTA),
            ("model_decommissioned", Failure.MODEL),
        ]:
            self.body = {"error": {"code": code, "message": "not retained"}}
            with self.assertRaises(ProviderError) as caught:
                self.generate()
            self.assertEqual(caught.exception.http_status, 200)
            self.assertEqual(caught.exception.category, cause)
            self.assertNotIn("not retained", str(caught.exception))

    def test_credential_rate_quota_model_and_provider_are_distinct(self):
        examples = [
            (401, {}, Failure.CREDENTIAL),
            (403, {}, Failure.ACCESS),
            (429, {}, Failure.UNKNOWN_LIMIT),
            (429, {"error": {"code": "rate_limit_exceeded"}}, Failure.RATE_LIMIT),
            (429, {"error": {"code": "insufficient_quota"}}, Failure.QUOTA),
            (404, {}, Failure.MODEL),
            (503, {}, Failure.PROVIDER),
            (422, {}, Failure.CAPABILITY),
        ]
        for status, body, category in examples:
            self.status, self.body = status, body
            with self.assertRaises(ProviderError) as caught:
                self.generate()
            self.assertEqual(caught.exception.category, category)

    def test_zai_documented_business_errors_distinguish_capacity_and_products(self):
        for code, category in [
            ("1113", Failure.QUOTA),
            ("1302", Failure.RATE_LIMIT),
            ("1305", Failure.CAPACITY),
            ("1315", Failure.PRODUCT),
            ("1311", Failure.PRODUCT),
        ]:
            self.status, self.body = 429, {"error": {"code": code}}
            with self.assertRaises(ProviderError) as error:
                self.generate()
            self.assertEqual(error.exception.category, category)
            self.assertEqual(error.exception.business_code, code)
            self.assertEqual(error.exception.http_status, 429)

    def test_retired_model_error_does_not_become_bad_credential(self):
        self.status = 403
        self.body = {"error": {"code": "model_decommissioned"}}
        with self.assertRaises(ProviderError) as error:
            self.generate()
        self.assertEqual(error.exception.category, Failure.MODEL)

    def test_402_does_not_invent_account_balance(self):
        self.status, self.body = 402, {"error": "generic rejection"}
        with self.assertRaises(ProviderError) as error:
            self.generate()
        self.assertEqual(error.exception.category, Failure.FUNDING)

    def test_groq_headers_preserve_limits_and_independent_reset_windows(self):
        headers = {
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-limit-tokens": "8000",
            "x-ratelimit-remaining-requests": "999",
            "x-ratelimit-remaining-tokens": "7900",
            "x-ratelimit-reset-requests": "1m30.5s",
            "x-ratelimit-reset-tokens": "7.66s",
            "Retry-After": "1.5",
        }
        limits = rate_limits(headers, "groq", 1000)
        self.assertEqual(limits.request_limit, 1000)
        self.assertEqual(limits.token_limit, 8000)
        self.assertEqual(limits.requests_reset_at, 1090.5)
        self.assertEqual(limits.tokens_reset_at, 1007.66)
        self.assertEqual(limits.retry_after, 1.5)
        self.assertEqual((limits.request_window, limits.token_window), ("day", "minute"))

    def test_dynamic_backing_model_and_provider_are_preserved(self):
        self.body.update(model="current/backing:free", provider="FixtureProvider")
        response = self.generate()
        self.assertEqual(response.actual_model, "current/backing:free")
        self.assertEqual(response.actual_provider, "FixtureProvider")

    def test_google_model_version_is_preserved(self):
        self.body = {
            "modelVersion": "current-gemini-version",
            "candidates": [{"content": {"parts": [{"text": "answer"}]}}],
        }
        self.assertEqual(self.generate("google").actual_model, "current-gemini-version")

    def test_discovery_paginates_google_before_marking_absence(self):
        self.scheduled = [
            (
                200,
                {
                    "models": [
                        {
                            "name": "models/one",
                            "inputTokenLimit": 1024,
                            "outputTokenLimit": 128,
                            "supportedGenerationMethods": ["generateContent"],
                        }
                    ],
                    "nextPageToken": "next-page",
                },
            ),
            (
                200,
                {
                    "models": [
                        {"name": "models/two", "supportedGenerationMethods": ["generateContent"]}
                    ]
                },
            ),
        ]
        provider = replace(self.provider, adapter="google")
        inventory = HTTPDiscovery().inventory(provider, "fixture", "synthetic-only", 2)
        self.assertEqual({m.id for m in inventory.models}, {"one", "two"})
        self.assertTrue(inventory.complete)
        self.assertEqual(inventory.pages, 2)
        self.assertIn("pageToken=next-page", self.requests[1]["path"])
        self.assertTrue(all(r["google_key"] for r in self.requests))

    def test_openrouter_aliases_and_live_zero_pricing_are_valid_inventory(self):
        self.body = {
            "data": [
                {"id": "~vendor/model-latest", "pricing": {"prompt": "0", "completion": "0"}},
                {
                    "id": "vendor/request-fee",
                    "pricing": {"prompt": "0", "completion": "0", "request": "0.1"},
                },
            ],
            "links": {"next": None},
        }
        provider = replace(self.provider, id="openrouter")
        inventory = HTTPDiscovery().inventory(provider, "fixture", "synthetic-only", 2)
        self.assertEqual(inventory.models[0].id, "~vendor/model-latest")
        self.assertEqual(inventory.models[0].funding, Funding.FREE)
        self.assertEqual(inventory.models[1].funding, Funding.UNKNOWN)
        self.assertEqual(self.requests[0]["path"], "/models/user")

    def test_incomplete_or_malformed_discovery_does_not_claim_complete_inventory(self):
        self.body = {"data": [{"id": "model"}], "links": {"next": "/unhandled-page"}}
        self.assertFalse(
            HTTPDiscovery().inventory(self.provider, "fixture", "synthetic", 2).complete
        )
        self.body = {"data": [{"id": "illegal model id"}]}
        with self.assertRaises(ProviderError):
            HTTPDiscovery().inventory(self.provider, "fixture", "synthetic", 2)

    def test_discovery_rejects_credential_echo_without_persisting_or_logging_it(self):
        self.body = {"data": [{"id": "synthetic-only"}]}
        with self.assertRaises(ProviderError) as error:
            HTTPDiscovery().inventory(self.provider, "fixture", "synthetic-only", 2)
        self.assertNotIn("synthetic-only", str(error.exception))

    def test_account_daily_limit_is_distinct_from_unknown_unlimited_credit_cap(self):
        self.body = {
            "data": {
                "label": "do-not-retain-label",
                "is_free_tier": True,
                "limit_remaining": None,
                "free_model_daily_requests": {"limit": 50, "remaining": 47},
            }
        }
        provider = replace(self.provider, id="openrouter")
        account = HTTPDiscovery().account(provider, "synthetic", 2)
        self.assertTrue(account.free_tier)
        self.assertEqual(account.limits.remaining_requests, 47)
        self.assertIsNone(account.credit_cap_remaining)
        self.assertNotIn("do-not-retain-label", repr(account))

    def test_cloud_ollama_structured_feature_is_not_assumed_from_local_api(self):
        provider = replace(self.provider, id="ollama-cloud", adapter="ollama")
        with self.assertRaises(ProviderError):
            HTTPAdapter("ollama").generate(
                provider,
                "model",
                "synthetic",
                replace(self.request, required=frozenset({"text", "structured"})),
                2,
                lambda: None,
            )
        self.assertEqual(self.requests, [])

    def test_error_body_and_material_are_never_exposed(self):
        self.status = 401
        self.body = {"error": "synthetic-only prompt and server diagnostic"}
        with self.assertRaises(ProviderError) as caught:
            self.generate()
        self.assertEqual(str(caught.exception), "credential_failure")
        self.assertNotIn("synthetic-only", repr(caught.exception))
        self.assertIsNone(caught.exception.__cause__)

    def test_incomplete_http_read_never_exposes_partial_diagnostics(self):
        from http.client import IncompleteRead

        adapter = HTTPAdapter("openai")
        with patch.object(
            adapter.opener, "open", side_effect=IncompleteRead(b"synthetic-only", 100)
        ):
            calls = [
                lambda: adapter.generate(
                    self.provider, "fixture", "synthetic-only", self.request, 2, lambda: None
                ),
                lambda: adapter.discover(self.provider, "synthetic-only"),
            ]
            for call in calls:
                with self.assertRaises(ProviderError) as caught:
                    call()
                self.assertEqual(caught.exception.category, Failure.NETWORK)
                self.assertNotIn("synthetic-only", repr(caught.exception))

    def test_incomplete_error_body_preserves_safe_error_category(self):
        from http.client import IncompleteRead
        from unittest.mock import Mock
        from urllib.error import HTTPError

        adapter = HTTPAdapter("openai")
        body = Mock()
        body.read.side_effect = IncompleteRead(b"synthetic-only", 100)
        error = HTTPError(self.url, 401, "synthetic-only", {}, body)
        with patch.object(adapter.opener, "open", side_effect=error):
            with self.assertRaises(ProviderError) as caught:
                adapter.generate(
                    self.provider, "fixture", "synthetic-only", self.request, 2, lambda: None
                )
        self.assertEqual(caught.exception.category, Failure.CREDENTIAL)
        self.assertNotIn("synthetic-only", repr(caught.exception))
        body.close.assert_called_once()

    def test_network_policy_denial_is_separate(self):
        self.status = 403
        self.headers = {"x-mitmproxy-blocked-reason": "POLICY"}
        with self.assertRaises(ProviderError) as caught:
            self.generate()
        self.assertEqual(caught.exception.category, Failure.NETWORK_POLICY)

    def test_connect_policy_denial_is_classified_for_generate_and_discovery(self):
        adapter = HTTPAdapter("openai")
        with patch.object(
            adapter.opener, "open", side_effect=URLError("Tunnel connection failed: 403 Forbidden")
        ):
            for call in (
                lambda: adapter.generate(
                    self.provider, "fixture", "synthetic", self.request, 2, lambda: None
                ),
                lambda: adapter.discover(self.provider, "synthetic"),
            ):
                with self.assertRaises(ProviderError) as caught:
                    call()
                self.assertEqual(caught.exception.category, Failure.NETWORK_POLICY)

    def test_redirects_do_not_forward_credentials(self):
        self.status = 302
        self.headers = {"Location": self.url + "/credential-stealer"}
        with self.assertRaises(ProviderError):
            self.generate()
        self.assertEqual(len(self.requests), 1)

    def test_openai_stream_contract(self):
        self.body = (
            b'data: {"choices":[{"delta":{"content":"OSCAR_"}}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"PROVIDER_OK"},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        chunks = []
        response = self.generate(sink=chunks.append)
        self.assertEqual(response.text, "OSCAR_PROVIDER_OK")
        self.assertEqual(chunks, ["OSCAR_", "PROVIDER_OK"])

    def test_google_stream_contract(self):
        self.body = (
            b'data: {"candidates":[{"content":{"parts":[{"text":"OK"}]},'
            b'"finishReason":"STOP"}]}\n\n'
        )
        chunks = []
        self.assertEqual(self.generate("google", chunks.append).text, "OK")
        self.assertEqual(chunks, ["OK"])

    def test_ollama_ndjson_stream_contract(self):
        self.body = (
            b'{"message":{"content":"OSCAR_"},"done":false}\n'
            b'{"message":{"content":"PROVIDER_OK"},"done":true,"eval_count":4}\n'
        )
        chunks = []
        self.assertEqual(self.generate("ollama", chunks.append).text, "OSCAR_PROVIDER_OK")

    def test_stream_disconnect_preserves_emission_provenance(self):
        self.body = b'data: {"choices":[{"delta":{"content":"partial output"}}]}\n\n'
        chunks = []
        with self.assertRaises(ProviderError) as caught:
            self.generate(sink=chunks.append)
        self.assertTrue(caught.exception.emitted)
        self.assertEqual(chunks, ["partial output"])

    def test_discovery_is_real_read_only_replaceable_inventory(self):
        self.body = {"data": [{"id": "new-model-1"}, {"id": "new-model-2"}]}
        self.assertEqual(
            HTTPAdapter("openai").discover(self.provider, "synthetic-only"),
            ["new-model-1", "new-model-2"],
        )
        self.assertEqual(self.requests[0]["path"], "/models")

    def test_unknown_usage_and_quota_stay_unknown(self):
        del self.body["usage"]
        response = self.generate()
        self.assertIsNone(response.input_tokens)
        self.assertIsNone(response.remaining_requests)

    def http_router(self):
        from .support import RouterRig

        r = RouterRig()
        self.addCleanup(r.close)
        r.registry.providers = {
            name: replace(provider, local=True, base_url=self.url + "/" + name)
            for name, provider in r.registry.providers.items()
        }
        r.router.adapters = {"test": HTTPAdapter("openai")}
        return r

    def test_router_credential_failover_over_real_http(self):
        r = self.http_router()
        self.scheduled = [(401, {"error": "synthetic credential rejected"}), (200, self.body)]
        routed = r.router.execute(r.request)
        self.assertEqual(routed.route.slot, "plentiful-2")
        self.assertEqual(routed.response.text, "OSCAR_PROVIDER_OK")
        self.assertEqual(routed.status, "REPORTED")
        self.assertEqual(len(self.requests), 2)
        self.assertTrue(all(request["bearer"] for request in self.requests))

    def test_router_cross_provider_fallback_over_real_http(self):
        r = self.http_router()
        self.scheduled = [(503, {"error": "synthetic provider failure"}), (200, self.body)]
        routed = r.router.execute(r.request)
        self.assertEqual(routed.route.provider, "scarce")
        self.assertEqual(
            [request["path"] for request in self.requests],
            ["/plentiful/chat/completions", "/scarce/chat/completions"],
        )
        self.assertTrue(r.store.all("route_history")[1]["fallback"])
