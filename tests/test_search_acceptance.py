"""Source-fetch acceptance cannot be inferred from preflight or unrelated evidence.

These use synthetic evidence through real loopback transport, never hosted search.
"""

import unittest
from dataclasses import asdict
from types import SimpleNamespace

from oscar.contracts import Capability, Result, TaskState, new_id
from oscar.freshness import Authority, SourceRef
from oscar.models import ProviderSpec
from oscar.retrieval import RetrievalRequest, RetrievalResult, RetrievedFact
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
        self.hide_provenance = False
        self.preflight_age = 0
        self.access_status = "REPORTED"
        self.access_relevant = True
        self.access_age = 0
        self.native_scope = "account"
        self.native_complete = True
        self.preserve_title = True
        self.title_returned = True
        self.constraint_provenance = True
        self.synthesis_scopes = True
        for slot in self.source.pool.slots.values():
            slot.present = True
        self.source.search = self.preflight

    def observe(self, **extra):
        identifier = new_id()
        self.rig.store.put(
            "search_observation",
            identifier,
            {
                "id": identifier,
                "status": "REPORTED",
                "http_status": 200,
                "retained_sources": 1,
                "observed_at": self.rig.clock() - self.preflight_age
                if "slot" in extra
                else self.rig.clock(),
                **extra,
            },
        )
        return identifier

    def preflight(self, request, slot, check_cancel):
        source = SourceRef(
            "https://console.groq.com/docs/models",
            Authority.OFFICIAL_DOCS,
            "provider",
            self.rig.clock(),
            title="Official models",
            source_provider="tavily",
            provider_id="groq",
            evidence_id=new_id(),
        )
        self.observe(
            slot=slot,
            source_metadata=[
                {
                    "evidence_id": source.evidence_id,
                    "identity": source.identity,
                    "title_returned": True,
                    "title": source.title,
                    "published_at": None,
                }
            ],
        )
        return RetrievalResult((RetrievedFact("Fixture official page", source),))

    def execute(self, action, cancellation):
        cancellation.check()
        evidence_ids = []
        claims = []
        for provider, url in API_URLS.items():
            native_url = API_URLS["groq"] if self.duplicate_native else url
            web_url = "https://" + OFFICIAL_DOMAINS[provider][0] + "/docs/pricing"
            native = SourceRef(
                native_url,
                Authority.LIVE_API,
                self.native_scope,
                self.rig.clock() - self.evidence_age,
                provider_id=provider,
                source_provider=provider,
                evidence_id=new_id(),
            )
            web = SourceRef(
                web_url,
                Authority.OFFICIAL_DOCS,
                "provider",
                self.rig.clock() - self.evidence_age - self.access_age,
                title="API free tier limits"
                if self.preserve_title and self.title_returned
                else None,
                source_provider="tavily",
                provider_id=provider,
                evidence_id=new_id(),
            )
            self.rig.store.put(
                "model_inventory",
                provider,
                {
                    "provider": provider,
                    "complete": self.native_complete,
                    "source": asdict(native),
                    "models": [],
                },
            )
            methods = [(native, "direct")]
            if self.access_status == "REPORTED":
                methods.append((web, self.web_method))
            for source, method in methods:
                evidence_ids.append(source.evidence_id)
                self.rig.store.put(
                    "retrieval_evidence",
                    source.evidence_id,
                    {
                        "task_id": self.evidence_task_id or action.task_id,
                        "correlation_id": self.evidence_correlation or action.correlation_id,
                        "source": asdict(source),
                        "retrieval_method": method,
                        "status": "REPORTED",
                        "conflicts": ["preserved fixture cache conflict"],
                        "access_topics": ["api_limits"]
                        if source is web and self.access_relevant
                        else [],
                    },
                )
            attempts = []
            if self.objective_search:
                for stage in range(2 if self.access_status == "UNKNOWN" else 1):
                    attempts.append(
                        self.observe(
                            task_id=action.task_id,
                            correlation_id=action.correlation_id,
                            provider_id=provider,
                            purpose="official_access_constraints",
                            query_stage=stage,
                            domains=list(OFFICIAL_DOMAINS[provider]),
                            source_metadata=[
                                {
                                    "evidence_id": web.evidence_id,
                                    "identity": web.identity,
                                    "title_returned": self.title_returned,
                                    "title": "API free tier limits"
                                    if self.title_returned
                                    else None,
                                    "published_at": None,
                                }
                            ]
                            if self.access_status == "REPORTED"
                            else [],
                        )
                    )
            self.rig.store.put(
                "constraint_assessment",
                new_id(),
                {
                    "task_id": action.task_id,
                    "correlation_id": action.correlation_id,
                    "provider": provider,
                    "status": self.access_status,
                    "observed_at": self.rig.clock() - self.access_age,
                    "attempt_ids": attempts if self.constraint_provenance else [],
                    "evidence_ids": [web.evidence_id] if self.access_status == "REPORTED" else [],
                    "reason": "Explicit bounded official-source result or UNKNOWN",
                },
            )
            claims.append(
                {
                    "provider": provider,
                    "provider_global_support": "REPORTED source excerpts"
                    if self.access_status == "REPORTED"
                    else "UNKNOWN no official current support",
                    "account_visible_availability": "REPORTED live API listing"
                    if self.synthesis_scopes
                    else "VERIFIED provider docs prove account access",
                    "generation_probed_state": "UNKNOWN not probed",
                    "account_funding": "UNKNOWN no entitlement evidence",
                    "account_quota": "UNKNOWN no account quota endpoint read",
                    "public_access_constraints": self.access_status,
                }
            )
        self.rig.store.put(
            "retrieval_synthesis",
            new_id(),
            {
                "task_id": action.task_id,
                "correlation_id": action.correlation_id,
                "status": "REPORTED",
                "claims": claims,
                "evidence_ids": evidence_ids,
                "conflicts_preserved": True,
            },
        )
        if self.expire_lease:
            self.rig.clock.now += 121
        value = self.result_value
        if isinstance(value, str) and not self.hide_provenance:
            value += "\n" + "\n".join(
                e["source"]["identity"]
                + " "
                + e["source"]["evidence_id"]
                + " "
                + "; ".join(e["conflicts"])
                for e in self.rig.store.all("retrieval_evidence")
            )
        return Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            self.result_success,
            value,
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
        self.assertEqual(len(report["slot_preflight_observations"]), 3)
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

    def test_six_official_hosts_with_irrelevant_content_are_rejected(self):
        self.access_relevant = False
        report = search_acceptance(self.harness)
        self.assertEqual(len(report["official_web_coverage"]), 6)
        self.assertEqual(report["acceptance"], "PARTIAL")

    def test_evidenced_unknown_after_two_official_query_stages_is_accepted(self):
        self.access_status = "UNKNOWN"
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PASS")
        self.assertEqual(set(report["constraint_coverage"].values()), {"UNKNOWN"})
        self.assertEqual(report["official_web_coverage"], [])
        self.assertEqual(report["task_state"], TaskState.PARTIALLY_VERIFIED)

    def test_unknown_without_official_attempt_provenance_is_rejected(self):
        self.access_status = "UNKNOWN"
        self.constraint_provenance = False
        self.assertEqual(search_acceptance(self.harness)["acceptance"], "PARTIAL")

    def test_missing_current_run_preflight_cannot_use_previous_success(self):
        self.preflight(RetrievalRequest("fixture"), "tavily-3", lambda: None)
        self.source.pool.slots["tavily-3"].present = False
        report = search_acceptance(self.harness)
        self.assertFalse(report["acceptance_checks"]["current_run_three_authenticated_preflights"])
        self.assertEqual(report["acceptance"], "PARTIAL")

    def test_web_claims_cannot_replace_account_native_inventory(self):
        self.native_scope = "provider"
        report = search_acceptance(self.harness)
        self.assertEqual(report["native_provider_coverage"], [])
        self.assertEqual(report["acceptance"], "PARTIAL")

    def test_incomplete_native_inventories_cannot_pass(self):
        self.native_complete = False
        self.assertEqual(search_acceptance(self.harness)["acceptance"], "PARTIAL")

    def test_stale_official_access_evidence_cannot_pass(self):
        self.access_age = 301
        self.assertEqual(search_acceptance(self.harness)["acceptance"], "PARTIAL")

    def test_returned_title_must_match_persisted_metadata(self):
        self.preserve_title = False
        report = search_acceptance(self.harness)
        self.assertFalse(report["acceptance_checks"]["source_metadata_retained"])
        self.assertEqual(report["acceptance"], "PARTIAL")

    def test_synthesis_cannot_upgrade_public_docs_to_verified_account_access(self):
        self.synthesis_scopes = False
        self.assertEqual(search_acceptance(self.harness)["acceptance"], "PARTIAL")

    def test_genuinely_absent_provider_title_is_optional(self):
        self.title_returned = False
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PASS")
        self.assertTrue(
            all(
                e["source"]["title"] is None
                for e in report["sources"]
                if e["source"]["scope"] == "provider"
            )
        )

    def test_synthesis_hiding_conflicts_or_source_refs_is_rejected(self):
        self.hide_provenance = True
        report = search_acceptance(self.harness)
        self.assertEqual(report["acceptance"], "PARTIAL")
        self.assertFalse(report["acceptance_checks"]["visible_provenance_and_conflicts"])

    def test_appended_stale_preflight_timestamp_is_not_current_run_proof(self):
        self.preflight_age = 301
        self.assertEqual(search_acceptance(self.harness)["acceptance"], "PARTIAL")
