"""Source-fetch acceptance cannot be inferred from preflight or unrelated evidence.

These use synthetic evidence through real loopback transport, never hosted search.
"""

import unittest
from dataclasses import asdict
from types import SimpleNamespace

from oscar.contracts import Capability, Result, TaskState, new_id
from oscar.freshness import Authority, SourceRef
from oscar.models import ProviderSpec
from oscar.retrieval import RetrievalResult
from oscar.search import OFFICIAL_DOMAINS, TavilySource
from scripts.verify_gate_a_search import search_acceptance

from .support import Rig

API_URLS = {
    "groq": "https://api.groq.com/openai/v1/models",
    "openrouter": "https://openrouter.ai/api/v1/models/user",
    "google": "https://generativelanguage.googleapis.com/v1beta/models",
    "nvidia": "https://integrate.api.nvidia.com/v1/models",
    "zai": "https://api.z.ai/api/paas/v4/models",
    "ollama-cloud": "https://ollama.com/api/tags",
}


class SearchAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.rig = Rig()
        self.addCleanup(self.rig.close)
        self.source = TavilySource(self.rig.store, {}, self.rig.clock)
        self.harness = SimpleNamespace(
            search=self.source,
            store=self.rig.store,
            grid=self.rig.grid,
            session=self.rig.session,
            node_id="test-node",
            dispatcher=self.rig.dispatcher,
            runtime=self.rig.runtime,
            router=SimpleNamespace(clock=self.rig.clock),
            registry=SimpleNamespace(
                providers={
                    provider: ProviderSpec(provider, "fixture", url, {}, discovery_required=True)
                    for provider, url in API_URLS.items()
                }
            ),
        )
        self.rig.grid.advertise(
            self.rig.session,
            [
                Capability(
                    "sources.retrieve",
                    "Synthetic source fixture",
                    "Loopback acceptance evidence fixture",
                    "retrieval",
                    "test-node",
                    ("models",),
                    "live_source",
                    "evidence",
                )
            ],
        )
        self.rig.dispatcher.executors["sources.retrieve"] = self.execute
        self.objective_search = True
        self.result_success = True
        self.result_value = "Synthetic evidence-qualified answer; source content remains REPORTED."
        self.evidence_task_id = None
        self.evidence_correlation = None
        self.evidence_age = 0
        self.duplicate_native = False
        self.web_method = "official_page"
        self.expire_lease = False

    def observe(self):
        self.rig.store.put(
            "search_observation",
            new_id(),
            {
                "status": "REPORTED",
                "http_status": 200,
                "retained_sources": 1,
                "observed_at": self.rig.clock(),
            },
        )

    def execute(self, action, cancellation):
        cancellation.check()
        if self.objective_search:
            self.observe()
        for provider, url in API_URLS.items():
            native_url = API_URLS["groq"] if self.duplicate_native else url
            web_url = "https://" + OFFICIAL_DOMAINS[provider][0] + "/docs/models"
            for identity, authority, scope, method in (
                (native_url, Authority.LIVE_API, "account", "direct"),
                (web_url, Authority.OFFICIAL_DOCS, "provider", self.web_method),
            ):
                self.rig.store.put(
                    "retrieval_evidence",
                    new_id(),
                    {
                        "task_id": self.evidence_task_id or action.task_id,
                        "correlation_id": self.evidence_correlation or action.correlation_id,
                        "source": asdict(
                            SourceRef(
                                identity, authority, scope, self.rig.clock() - self.evidence_age
                            )
                        ),
                        "retrieval_method": method,
                        "status": "REPORTED",
                        "conflicts": [],
                    },
                )
        if self.expire_lease:
            self.rig.clock.now += 121
        return Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            self.result_success,
            self.result_value,
            error=None if self.result_success else "freshness_unavailable: UNKNOWN",
        )

    def test_real_correlated_loopback_flow_accepts_source_fetch_without_factual_verification(self):
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PASS")
        self.assertEqual(report["task_state"], TaskState.PARTIALLY_VERIFIED)
        self.assertEqual(report["native_provider_coverage"], sorted(API_URLS))
        self.assertEqual(report["official_web_coverage"], sorted(OFFICIAL_DOMAINS))
        self.assertTrue(report["objective_result_reported_success"])
        self.assertTrue(report["actual_live_tavily"])
        self.assertEqual(report["generation_calls"], 0)
        self.assertTrue(all(source["status"] == "REPORTED" for source in report["sources"]))

    def test_successful_slot_preflight_does_not_replace_objective_live_search(self):
        self.source.pool.slots["tavily-1"].present = True

        def preflight(*args, **kwargs):
            self.observe()
            return RetrievalResult(())

        self.source.search = preflight
        self.objective_search = False
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertFalse(report["actual_live_tavily"])
        self.assertEqual(len(report["slot_preflight_observations"]), 1)
        self.assertEqual(report["objective_search_observations"], [])

    def test_source_references_from_other_task_cannot_satisfy_current_objective(self):
        self.evidence_task_id = "unrelated-task"
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertEqual(report["sources"], [])
        self.assertEqual(report["native_provider_coverage"], [])

    def test_source_references_with_other_correlation_cannot_satisfy_objective(self):
        self.evidence_correlation = "unrelated-correlation"
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertEqual(report["sources"], [])

    def test_failed_result_with_complete_sources_is_not_acceptance_success(self):
        self.result_success = False
        report = search_acceptance(self.harness)
        self.assertEqual(report["task_state"], TaskState.BLOCKED)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertFalse(report["objective_result_reported_success"])
        self.assertEqual(len(report["official_web_coverage"]), 6)

    def test_transport_lease_failure_after_source_persistence_is_not_false_success(self):
        self.expire_lease = True
        report = search_acceptance(self.harness)
        self.assertEqual(report["task_state"], TaskState.BLOCKED)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertEqual(len(report["official_web_coverage"]), 6)
        self.assertTrue(report["objective_result_reported_success"])

    def test_six_duplicate_api_records_do_not_prove_six_provider_inventories(self):
        self.duplicate_native = True
        report = search_acceptance(self.harness)
        self.assertEqual(report["native_inventory_sources"], 6)
        self.assertEqual(report["native_provider_coverage"], ["groq"])
        self.assertEqual(report["acceptance"], "PARTIAL")

    def test_index_excerpts_on_official_hosts_do_not_replace_official_page_reads(self):
        self.web_method = "search_excerpt"
        report = search_acceptance(self.harness)
        self.assertEqual(report["official_web_coverage"], [])
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertTrue(report["actual_live_tavily"])

    def test_stale_and_future_sources_do_not_prove_current_objective(self):
        for age in (301, -1):
            with self.subTest(age=age):
                self.evidence_age = age
                report = search_acceptance(self.harness)
                self.assertEqual(report["sources"], [])
                self.assertEqual(report["acceptance"], "PARTIAL")

    def test_no_answer_is_not_successful_synthesis(self):
        self.result_value = None
        report = search_acceptance(self.harness)
        self.assertEqual(report["task_state"], TaskState.PARTIALLY_VERIFIED)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertFalse(report["objective_result_reported_success"])
