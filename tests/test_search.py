"""Real loopback search contracts; these tests do not claim hosted Tavily access."""

import json
import unittest
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch

from oscar.capabilities import Cancelled
from oscar.credentials import CredentialPool
from oscar.freshness import Authority
from oscar.models import Failure, ProviderError, ProviderSpec
from oscar.retrieval import RetrievalRequest
from oscar.search import OFFICIAL_DOMAINS, TavilySource
from oscar.storage import Store

from .support import Clock


class SearchContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "search.sqlite")
        self.clock = Clock()
        self.environ = {
            "TAVILY_API_KEY_1": "synthetic-search-secret-one",
            "TAVILY_API_KEY_2": "synthetic-search-secret-two",
            "TAVILY_API_KEY_3": "synthetic-search-secret-three",
        }
        self.status = 200
        self.body = {
            "results": [
                {
                    "url": "https://console.groq.com/docs/models",
                    "content": "Current provider catalog excerpt.",
                }
            ],
            "usage": {"credits": 1},
        }
        self.headers = {}
        self.scheduled = []
        self.requests = []
        self.page_reads = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                outer.requests.append(
                    {
                        "path": self.path,
                        "body": json.loads(self.rfile.read(length)),
                        # Credential content is never retained, even in the fixture.
                        "bearer": self.headers.get("Authorization", "").startswith("Bearer "),
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

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(
            target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True
        )
        self.thread.start()
        self.addCleanup(self.close)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.source = self.make_source()
        self.request = RetrievalRequest("synthetic private current model question", result_limit=2)

    def make_source(self, environ=None):
        source = TavilySource(
            self.store,
            self.environ if environ is None else environ,
            self.clock,
            lambda value: value.replace("synthetic-other-provider-secret", "<redacted>"),
        )
        source.provider = replace(source.provider, base_url=self.url)
        source.page_reader = self.read_page
        return source

    def read_page(self, url, timeout, *, redact):
        self.page_reads.append({"url": url, "timeout": timeout})
        content = next(
            (
                item["content"]
                for item in self.body["results"]
                if item.get("url") == url and isinstance(item.get("content"), str)
            ),
            "Current official documentation retrieved independently.",
        )
        return redact(content)[:1500]

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.store.close()
        self.temp.cleanup()

    def search(self, request=None, slot="tavily-1", check_cancel=lambda: None):
        return self.source.search(request or self.request, slot, check_cancel)

    def persisted(self):
        return json.dumps(self.store.db.execute("SELECT data FROM records").fetchall())

    def test_basic_bearer_wire_is_bounded_and_cost_explicit(self):
        result = self.search(
            replace(self.request, domains=("console.groq.com",), time_range="month")
        )
        wire = self.requests[0]
        self.assertTrue(wire["bearer"])
        self.assertEqual(wire["path"], "/search")
        self.assertEqual(
            wire["body"],
            {
                "query": self.request.query,
                "search_depth": "basic",
                "auto_parameters": False,
                "max_results": 2,
                "include_answer": False,
                "include_raw_content": False,
                "include_usage": True,
                "include_published_date": True,
                "include_domains": ["console.groq.com"],
                "include_domains_mode": "restrict",
                "time_range": "month",
            },
        )
        self.assertEqual(len(result.facts), 1)
        self.assertEqual(self.store.all("search_observation")[0]["credits"], 1)
        self.assertNotIn(self.request.query, self.persisted())
        self.assertNotIn(self.request.query, repr(self.request))

    def test_domain_restriction_filters_spoof_hosts_before_retaining_facts(self):
        self.body["results"] = [
            {"url": "https://console.groq.com.evil.invalid/docs", "content": "Spoof"},
            {"url": "https://docs.console.groq.com/models", "content": "Allowed subdomain"},
        ]
        result = self.search(replace(self.request, domains=("console.groq.com",)))
        self.assertEqual(len(result.facts), 1)
        self.assertEqual(result.facts[0].source.identity, "https://docs.console.groq.com/models")
        self.assertEqual(self.store.all("search_observation")[0]["omitted_sources"], 1)

    def test_configured_provider_objective_has_bounded_official_coverage(self):
        self.scheduled = [
            (
                200,
                {
                    "results": [
                        {"url": "https://" + domains[0] + "/models", "content": "Reported access"}
                    ]
                },
            )
            for domains in OFFICIAL_DOMAINS.values()
        ]
        result = self.source.retrieve(
            RetrievalRequest(
                "What models do configured providers currently support?", result_limit=6
            ),
            lambda: None,
        )
        self.assertEqual(len(self.requests), 6)
        self.assertEqual(len(result.facts), 6)
        self.assertTrue(all(wire["body"]["max_results"] == 1 for wire in self.requests))
        self.assertTrue(all(wire["body"]["include_domains"] for wire in self.requests))
        self.assertTrue(
            all(fact.source.authority == Authority.OFFICIAL_DOCS for fact in result.facts)
        )
        self.assertEqual([slot.requests for slot in self.source.pool.slots.values()], [2, 2, 2])

    def test_configured_objective_filters_provider_domains_before_result_budget(self):
        self.body["results"] = [
            {"url": "https://docs.api.nvidia.com/nim", "content": "Reported API catalog"}
        ]
        result = self.source.retrieve(
            RetrievalRequest(
                "What models do configured providers currently support?",
                domains=("docs.api.nvidia.com",),
                result_limit=1,
            ),
            lambda: None,
        )
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(len(result.facts), 1)
        self.assertEqual(self.requests[0]["body"]["include_domains"], ["docs.api.nvidia.com"])

    def test_total_search_deadline_bounds_timeout_and_stops_additional_calls(self):
        elapsed = iter((100, 125))
        monotonic_now = {"value": 125}
        timeouts = []
        original_open = self.source.opener.open
        original_read_page = self.source.page_reader

        def bounded_open(request, timeout):
            timeouts.append(timeout)
            return original_open(request, timeout=timeout)

        def read_page_then_expire_budget(url, timeout, *, redact):
            text = original_read_page(url, timeout, redact=redact)
            monotonic_now["value"] = 131
            return text

        with (
            patch(
                "oscar.search.monotonic", side_effect=lambda: next(elapsed, monotonic_now["value"])
            ),
            patch.object(self.source.opener, "open", side_effect=bounded_open),
            patch.object(self.source, "page_reader", side_effect=read_page_then_expire_budget),
        ):
            result = self.source.retrieve(
                RetrievalRequest("What models do configured providers currently support?"),
                lambda: None,
            )
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(timeouts, [5])
        self.assertEqual(len(result.facts), 1)
        self.assertLessEqual(self.page_reads[0]["timeout"], 5)
        self.assertIn("Search time budget reached: UNKNOWN.", result.limitations)
        self.assertTrue(self.source.pool.eligible("tavily-2", model="*"))

    def test_current_official_page_content_supersedes_stale_search_index(self):
        self.body["results"][0]["content"] = "Retired model-old is the current supported model."
        self.source.page_reader = lambda url, timeout, redact: redact(
            "Model-old is retired. The current supported model is model-new."
        )
        result = self.search()
        self.assertEqual(result.facts[0].retrieval_method, "official_page")
        self.assertEqual(result.facts[0].source.authority, Authority.OFFICIAL_DOCS)
        self.assertIn("model-new", result.facts[0].text)
        self.assertNotIn("model-old is the current supported model", result.facts[0].text)
        self.assertNotIn("model-new", self.persisted())

    def test_unavailable_official_page_never_promotes_indexed_material_to_current_authority(self):
        def unavailable(url, timeout, *, redact):
            raise ProviderError(Failure.NETWORK)

        self.source.page_reader = unavailable
        result = self.search()
        self.assertEqual(len(result.facts), 1)
        self.assertEqual(result.facts[0].retrieval_method, "search_excerpt")
        self.assertEqual(result.facts[0].source.authority, Authority.SECONDARY)
        self.assertIn("UNKNOWN / potentially stale", result.facts[0].text)
        self.assertEqual(result.facts[0].source.identity, "https://console.groq.com/docs/models")

    def test_success_rate_headers_update_shared_capacity_without_sibling_rotation(self):
        self.headers = {
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-reset-requests": "60s",
        }
        result = self.search()
        self.assertEqual(len(result.facts), 1)
        capacity = self.source.pool.capacity("tavily-2", "*")
        self.assertEqual(capacity.request_limit, 1000)
        self.assertEqual(capacity.remaining_requests, 0)
        self.assertEqual(capacity.requests_reset_at, self.clock() + 60)
        blocked = self.source.retrieve(self.request, lambda: None)
        self.assertEqual(blocked.status, "UNKNOWN")
        self.assertEqual(len(self.requests), 1)
        self.assertFalse(self.source.pool.eligible("tavily-3", model="*"))
        self.clock.now += 61
        self.assertTrue(self.source.pool.eligible("tavily-3", model="*"))
        self.assertIsNone(self.source.pool.capacity("tavily-3", "*").remaining_requests)

    def test_distinct_search_observations_are_preserved_even_with_same_timestamp(self):
        self.search()
        self.search()
        observations = self.store.all("search_observation")
        self.assertEqual(len(observations), 2)
        self.assertTrue(all(item["observed_at"] == self.clock() for item in observations))

    def test_official_docs_and_community_secondary_evidence_stay_distinct(self):
        self.body["results"] = [
            {"url": "https://docs.ollama.com/cloud", "content": "Official documentation"},
            {"url": "https://ollama.com/community/current", "content": "Community report"},
            {"url": "https://console.groq.com.evil.invalid/models", "content": "Spoof host"},
        ]
        result = self.search(replace(self.request, result_limit=3))
        self.assertEqual(
            [fact.source.authority for fact in result.facts],
            [Authority.OFFICIAL_DOCS, Authority.SECONDARY, Authority.SECONDARY],
        )
        self.assertTrue(all(fact.source.scope == "provider" for fact in result.facts))
        self.assertIn("not account entitlement", result.facts[0].text)
        self.assertEqual(
            [fact.retrieval_method for fact in result.facts],
            ["official_page", "search_excerpt", "search_excerpt"],
        )
        self.assertTrue(
            all("UNKNOWN / potentially stale" in fact.text for fact in result.facts[1:])
        )

    def test_result_excerpt_and_publication_are_bounded_with_current_observation(self):
        self.body["results"] = [
            {
                "url": f"https://ai.google.dev/docs/{index}",
                "content": "x" * 4000,
                "published_date": "2026-09-01T00:00:00Z",
            }
            for index in range(5)
        ]
        result = self.search()
        self.assertEqual(len(result.facts), 2)
        self.assertLessEqual(len(result.facts[0].text), 1600)
        self.assertEqual(result.facts[0].source.observed_at, self.clock())
        self.assertEqual(result.facts[0].source.published_at, "2026-09-01T00:00:00Z")
        self.assertIn("Publication dates", " ".join(result.limitations))
        self.assertTrue(result.facts[0].source.current(self.clock()))
        self.clock.now += 301
        self.assertFalse(result.facts[0].source.current(self.clock()))

    def test_unsafe_url_references_are_omitted(self):
        urls = [
            "http://console.groq.com/docs",
            "https://user:password@console.groq.com/docs",
            "https://console.groq.com/docs?private=query",
            "https://console.groq.com/docs#private-fragment",
            "https://console.groq.com/" + self.environ["TAVILY_API_KEY_1"],
        ]
        self.body["results"] = [{"url": url, "content": "Untrusted"} for url in urls]
        result = self.search(replace(self.request, result_limit=5))
        self.assertFalse(result.facts)
        self.assertEqual(self.store.all("search_observation")[0]["omitted_sources"], 5)

    def test_all_secret_fields_are_redacted_before_result_or_evidence_can_escape(self):
        self.body["results"][0].update(
            content=self.environ["TAVILY_API_KEY_1"] + " synthetic-other-provider-secret",
            published_date=self.environ["TAVILY_API_KEY_2"],
        )
        result = self.search()
        exposed = (
            json.dumps(asdict(result)) + repr(result) + repr(self.source.pool) + self.persisted()
        )
        for secret in (*self.environ.values(), "synthetic-other-provider-secret"):
            self.assertNotIn(secret, exposed)
        self.assertIn("<redacted>", result.facts[0].text)

    def test_secret_crossing_excerpt_boundary_is_redacted_before_truncation(self):
        secret = self.environ["TAVILY_API_KEY_1"]
        self.body["results"][0]["content"] = "x" * 1490 + secret + " remaining material"
        result = self.search()
        self.assertNotIn(secret[:10], result.facts[0].text)
        self.assertLessEqual(len(result.facts[0].text), 1600)

    def test_invalid_key_fails_over_once_without_invalidating_siblings(self):
        self.scheduled = [(401, {"detail": "Credential error not retained"}), (200, self.body)]
        result = self.source.retrieve(self.request, lambda: None)
        self.assertEqual(len(result.facts), 1)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.source.pool.slots["tavily-1"].validity, "invalid")
        self.assertEqual(self.source.pool.slots["tavily-2"].validity, "valid")
        self.assertEqual(self.source.pool.slots["tavily-3"].validity, "unknown")
        self.assertNotIn("Credential error", self.persisted())

    def test_shared_rate_cooldown_stops_sibling_rotation_without_disabling_other_pool(self):
        self.status, self.body, self.headers = (
            429,
            {"detail": "Not retained"},
            {"Retry-After": "60"},
        )
        result = self.source.retrieve(self.request, lambda: None)
        self.assertEqual(result.status, "UNKNOWN")
        self.assertEqual(len(self.requests), 1)
        self.assertTrue(
            all(not self.source.pool.eligible(slot, model="*") for slot in self.source.pool.slots)
        )
        unrelated = CredentialPool(
            [
                ProviderSpec(
                    "unrelated", "fixture", "https://unrelated.invalid", {"other-1": "FIXTURE"}
                )
            ],
            {"FIXTURE": "synthetic-other-account"},
            self.store,
            self.clock,
        )
        self.assertTrue(unrelated.eligible("other-1"))
        self.clock.now += 61
        self.assertTrue(self.source.pool.eligible("tavily-2", model="*"))
        self.assertTrue(unrelated.eligible("other-1"))

    def test_documented_432_and_433_quota_do_not_invent_numeric_balance(self):
        for status in (432, 433):
            with self.subTest(status=status):
                self.status, self.body = (
                    status,
                    {"detail": "Quota or usage limit; no numeric balance"},
                )
                with self.assertRaises(ProviderError) as caught:
                    self.search()
                self.assertEqual(caught.exception.category, Failure.QUOTA)
                self.assertEqual(caught.exception.http_status, status)
                self.assertIsNone(self.source.pool.capacity("tavily-1", "*").remaining_requests)
                self.assertIsNone(self.source.pool.slots["tavily-1"].remaining_requests)
                self.assertFalse(self.source.pool.eligible("tavily-2", model="*"))
                self.assertNotIn("no numeric balance", self.persisted())
                self.clock.now += 301

    def test_explicit_retry_after_longer_than_hour_is_not_shortened_or_lost_on_restore(self):
        self.status, self.body, self.headers = 429, {}, {"Retry-After": "7200"}
        started = self.clock()
        with self.assertRaises(ProviderError) as caught:
            self.search()
        self.assertEqual(caught.exception.retry_after, 7200)
        self.assertEqual(self.source.pool.capacity("tavily-2", "*").cooldown_until, started + 7200)
        self.clock.now += 3601
        self.assertFalse(self.source.pool.eligible("tavily-2", model="*"))
        restored = self.make_source()
        self.assertFalse(restored.pool.eligible("tavily-3", model="*"))
        self.clock.now += 3600
        self.assertTrue(restored.pool.eligible("tavily-3", model="*"))

    def test_missing_credentials_yield_unknown_without_http(self):
        source = self.make_source({})
        result = source.retrieve(self.request, lambda: None)
        self.assertEqual(result.status, "UNKNOWN")
        self.assertFalse(result.facts)
        self.assertIn("potentially stale", " ".join(result.limitations))
        self.assertFalse(self.requests)

    def test_malformed_oversize_and_missing_results_never_report_success(self):
        for body in (b"not-json", b" " * 500_001, {}, {"results": "wrong"}, {"results": [{}]}):
            with self.subTest(body_type=type(body).__name__):
                self.body = body
                self.clock.now += 1
                with self.assertRaises(ProviderError) as caught:
                    self.search()
                self.assertEqual(caught.exception.category, Failure.CAPABILITY)
                self.assertEqual(
                    self.store.all("search_observation")[-1].get("status"), "UNAVAILABLE"
                )
                self.assertEqual(self.source.pool.slots["tavily-1"].concurrent, 0)

    def test_usage_is_numeric_observation_not_guessed_available_quota(self):
        for credits in (True, -1, float("nan"), "100"):
            with self.subTest(credit_type=type(credits).__name__):
                self.body["usage"] = {"credits": credits}
                self.clock.now += 1
                self.search()
                self.assertIsNone(self.store.all("search_observation")[-1]["credits"])
                self.assertIsNone(self.source.pool.capacity("tavily-1", "*"))
                self.assertIsNone(self.source.pool.slots["tavily-1"].remaining_requests)

    def test_redirect_does_not_send_credentials_to_redirect_destination(self):
        self.status, self.body = 307, {}
        self.headers = {"Location": self.url + "/credential-target"}
        with self.assertRaises(ProviderError):
            self.search()
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.requests[0]["path"], "/search")
        self.assertEqual(self.source.pool.slots["tavily-1"].concurrent, 0)

    def test_cancellation_after_network_read_releases_slot_and_propagates(self):
        calls = 0

        def cancel_after_read():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise Cancelled("synthetic cancellation")

        with self.assertRaises(Cancelled):
            self.search(check_cancel=cancel_after_read)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.source.pool.slots["tavily-1"].concurrent, 0)
        self.assertTrue(self.source.pool.eligible("tavily-2", model="*"))
        self.assertNotEqual(self.store.all("search_observation")[0].get("status"), "REPORTED")

    def test_cancellation_before_search_does_not_open_network_or_reserve(self):
        def cancel():
            raise Cancelled("synthetic cancellation")

        with self.assertRaises(Cancelled):
            self.source.retrieve(self.request, cancel)
        self.assertFalse(self.requests)
        self.assertEqual(self.source.pool.slots["tavily-1"].concurrent, 0)
        self.assertFalse(self.store.all("search_observation"))
