"""Crash boundaries, stale projections and unsupported recall remain explicit."""

import json
import os
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.contracts import Epistemic
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.memory_fabric import HistoricalClaim, MemoryFabric
from oscar.memory_indexes import digest
from oscar.oauth_device import GitHubDeviceFlow
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store
from scripts.verify_gate_b_interactive import fixture_window
from tests.test_oauth_device import TestVault


class Projection:
    identity = "test-projection"

    def __init__(self):
        self.marker = None
        self.records = []
        self.calls = 0
        self.fail = False

    def rebuild(self, records, *, relationship=None):
        self.marker = None
        if self.fail:
            raise OSError("fixture outage")
        self.records = records
        self.marker = digest(records)

    def current_digest(self):
        if self.fail:
            raise OSError("fixture outage")
        return self.marker

    def query(self, query, relationship, *, limit=20):
        self.calls += 1
        if self.fail:
            raise OSError("fixture outage")
        return [r.id for r in self.records if r.relationship_id == relationship][:limit]

    def forget(self, ids):
        self.marker = None

    def close(self):
        pass


class ArchiveIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "archive.sqlite"
        self.archive = EventArchive(self.path)
        self.vector, self.graph = Projection(), Projection()
        self.graph.identity = "test-graph"
        self.fabric = MemoryFabric(self.archive, vector=self.vector, graph=self.graph)

    def tearDown(self):
        self.archive.close()
        self.temp.cleanup()

    def retain(self, text):
        event = SourceEvent("owner", text, "synthetic", time() - 10)
        self.archive.append(event, retain_authorized=True)
        return MemoryWriter(self.archive).retain(
            (event.id,), text, "semantic", retain_authorized=True, inferred=False
        )

    def test_canonical_update_fences_queries_and_rebuild_is_idempotent(self):
        self.retain("Chosen editor is Zed")
        self.assertEqual((), self.fabric.rebuild("owner"))
        generation = self.archive.generation("owner")
        self.retain("Project identifier ABC-921")
        recalled = self.fabric.retrieve("owner", "ABC-921")
        self.assertTrue(recalled.hits)
        self.assertEqual(0, self.vector.calls)
        self.assertIn("3-qdrant-hybrid:OUTDATED", recalled.unavailable)
        self.assertGreater(self.archive.generation("owner"), generation)
        self.assertEqual((), self.fabric.rebuild("owner"))
        marker = self.vector.marker
        self.assertEqual((), self.fabric.rebuild("owner"))
        self.assertEqual(marker, self.vector.marker)
        self.assertEqual("CURRENT", self.archive.index_state("owner", self.vector.identity))

    def test_rebuild_failure_preserves_archive_and_other_service(self):
        memory = self.retain("Canonical surviving history")
        self.vector.fail = True
        self.assertEqual((self.vector.identity,), self.fabric.rebuild("owner"))
        recalled = self.fabric.retrieve("owner", memory.content)
        self.assertEqual(memory.id, recalled.hits[0].memory.id)
        self.assertIn("4-graphiti-temporal", recalled.hits[0].paths)
        self.assertEqual("FAILED", self.archive.index_state("owner", self.vector.identity))

    def test_physical_projection_loss_and_restart_fail_closed(self):
        memory = self.retain("Restart evidence")
        self.fabric.rebuild("owner")
        self.vector.marker = None
        self.archive.close()
        self.archive = EventArchive(self.path)
        fabric = MemoryFabric(self.archive, vector=self.vector)
        self.assertTrue(fabric.retrieve("owner", memory.content).hits)
        self.assertEqual(0, self.vector.calls)

    def test_empty_other_relationship_cannot_clear_existing_projection(self):
        self.retain("Owner history stays intact")
        self.fabric.rebuild("owner")
        marker = self.vector.marker
        self.assertEqual((self.vector.identity, self.graph.identity), self.fabric.rebuild("other"))
        self.assertEqual(marker, self.vector.marker)
        self.assertEqual("CURRENT", self.archive.index_state("owner", self.vector.identity))

    def test_archive_write_during_index_query_fences_entire_recall(self):
        self.retain("Original fact")
        self.fabric.rebuild("owner")
        original = self.vector.query

        def concurrent(query, relationship, *, limit=20):
            self.retain("Concurrent canonical change")
            return original(query, relationship, limit=limit)

        self.vector.query = concurrent
        recalled = self.fabric.retrieve("owner", "Original fact")
        self.assertEqual((), recalled.hits)
        self.assertFalse(recalled.retrieval_succeeded)
        self.assertIn("concurrent-archive-update", recalled.unavailable)
        self.assertTrue(self.archive.fts("owner", "Concurrent canonical change"))

    def test_process_exit_after_canonical_commit_before_projection_update(self):
        self.retain("Before crash")
        self.fabric.rebuild("owner")
        code = """
import os,sys,time
from pathlib import Path
from oscar.event_archive import EventArchive,MemoryWriter,SourceEvent
a=EventArchive(Path(sys.argv[1]))
e=SourceEvent('owner','Committed crash evidence','synthetic',time.time()-1)
a.append(e,retain_authorized=True)
MemoryWriter(a).retain((e.id,),e.content,'semantic',retain_authorized=True)
os._exit(73)
"""
        completed = subprocess.run([sys.executable, "-c", code, str(self.path)], timeout=15)
        self.assertEqual(73, completed.returncode)
        recalled = self.fabric.retrieve("owner", "Committed crash evidence")
        self.assertTrue(recalled.hits)
        self.assertEqual(0, self.vector.calls)

    def test_independent_outages_and_eventual_unknown(self):
        memory = self.retain("Evidence fallback survives outage")
        self.fabric.rebuild("owner")
        for provider in (self.vector, self.graph):
            with self.subTest(provider=provider.identity):
                provider.fail = True
                recall = self.fabric.retrieve("owner", memory.content)
                self.assertTrue(recall.hits)
                provider.fail = False

        class FailedRanking:
            identity = "unavailable-reranker"

            def rank(self, query, texts):
                raise OSError("fixture failure")

        self.fabric.reranker = FailedRanking()
        recalled = self.fabric.retrieve("owner", memory.content)
        self.assertIn("reranker", recalled.unavailable)
        self.assertTrue(recalled.hits)
        self.vector.fail = self.graph.fail = True
        self.assertEqual((), self.fabric.retrieve("owner", "Unseen Martian password").hits)

    def test_lucky_guess_ambiguous_entity_and_superseded_cache_are_unknown(self):
        memory = self.retain("The chosen editor is Zed")
        recalled = self.fabric.retrieve("owner", memory.content)
        claim = HistoricalClaim(
            memory.content, memory.event_ids, (memory.id,), Epistemic.RECALLED, 1
        )
        self.assertEqual(Epistemic.RECALLED, self.fabric.check_claim(claim, recalled))
        self.assertEqual(
            Epistemic.UNKNOWN,
            self.fabric.check_claim(claim, replace(recalled, retrieval_succeeded=False)),
        )
        self.assertEqual(
            Epistemic.UNKNOWN, self.fabric.check_claim(replace(claim, event_ids=()), recalled)
        )
        self.assertEqual(
            Epistemic.UNKNOWN, self.fabric.check_claim(claim, replace(recalled, hits=()))
        )
        self.assertEqual(
            Epistemic.UNKNOWN,
            self.fabric.check_claim(
                claim, replace(recalled, ambiguous_entities=("alex1", "alex2"))
            ),
        )
        with self.archive.db:
            self.archive.db.execute(
                "UPDATE archive_memories SET payload=json_set(payload,'$.valid_to',?) WHERE id=?",
                (time() - 1, memory.id),
            )
        self.assertEqual(Epistemic.UNKNOWN, self.fabric.check_claim(claim, recalled))


class SimulatedCrash(BaseException):
    pass


class EnrollmentRecoveryTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "native Windows credential store")
    def test_native_token_write_process_crash_reconciles_without_exchange(self):
        from uuid import uuid4

        device_ref, token_ref = uuid4().hex, uuid4().hex
        vault = WindowsCredentialStore()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "native.sqlite"
            store = Store(path)
            try:
                vault.put("synthetic-crash-device", reference=device_ref)
                store.put(
                    "oauth_pending",
                    "native-crash",
                    {
                        "id": "native-crash",
                        "device_ref": device_ref,
                        "state": "polling",
                    },
                )
                store.put(
                    "oauth_connection",
                    "native-crash",
                    {
                        "id": "native-crash",
                        "credential_ref": token_ref,
                        "state": "enrolling_token",
                    },
                )
                code = """
import os,sys
from oscar.secure_credentials import WindowsCredentialStore
WindowsCredentialStore().put('synthetic-crash-token',reference=sys.argv[1])
os._exit(73)
"""
                child = subprocess.run([sys.executable, "-c", code, token_ref], timeout=15)
                self.assertEqual(73, child.returncode)
                store.close()
                store = Store(path)
                GitHubDeviceFlow(
                    store, vault, request=lambda *args: self.fail("no exchange replay")
                )
                self.assertEqual("ready", store.get("oauth_connection", "native-crash")["state"])
                self.assertEqual("synthetic-crash-token", vault.read(token_ref).value)
                with self.assertRaises(KeyError):
                    vault.read(device_ref)
                self.assertNotIn("synthetic-crash-token", path.read_bytes().decode(errors="ignore"))
            finally:
                vault.delete(device_ref)
                vault.delete(token_ref)
                store.close()

    def test_faults_at_every_durable_and_native_boundary(self):
        stages = (
            "device_intent",
            "device_written",
            "device_active",
            "exchange_intent",
            "exchange_returned",
            "token_intent",
            "token_written",
            "token_active",
            "device_deleted",
            "disconnect_intent",
            "credential_deleted",
            "disconnect_recorded",
        )
        for stage in stages:
            with self.subTest(stage=stage), TemporaryDirectory() as directory:
                path = Path(directory) / "state.sqlite"
                store, vault = Store(path), TestVault()
                now = [1000]

                def request(endpoint, fields):
                    if endpoint.endswith("/code"):
                        return {
                            "verification_uri": "https://github.com/login/device",
                            "device_code": "synthetic-device",
                            "user_code": "TEST",
                            "expires_in": 900,
                            "interval": 5,
                        }
                    return {
                        "access_token": "synthetic-token",
                        "token_type": "bearer",
                        "scope": "user:email",
                    }

                def fault(observed, stage=stage):
                    if observed == stage:
                        raise SimulatedCrash()

                flow = GitHubDeviceFlow(store, vault, request, lambda now=now: now[0], fault)
                with self.assertRaises(SimulatedCrash):
                    challenge = flow.begin("synthetic_client", owner_authorized=True)
                    now[0] += 5
                    connection = flow.poll_once(
                        challenge["id"], challenge["nonce"], owner_authorized=True
                    )
                    flow.disconnect(connection["id"], owner_authorized=True)
                store.close()
                store = Store(path)
                GitHubDeviceFlow(store, vault, request, lambda now=now: now[0])
                for record in store.all("oauth_connection"):
                    if stage in {"token_written", "token_active", "device_deleted"}:
                        self.assertEqual("ready", record["state"])
                        self.assertEqual(
                            "synthetic-token", vault.read(record["credential_ref"]).value
                        )
                    elif stage.startswith("disconnect") or stage == "credential_deleted":
                        self.assertIn("provider_revocation_pending", record["state"])
                        self.assertEqual(
                            "UNKNOWN_OWNER_ACTION_REQUIRED", record["remote_revocation"]
                        )
                        self.assertNotIn(record["credential_ref"], vault.values)
                    else:
                        self.assertIn("failed_recovery", record["state"])
                durable = json.dumps(store.all("oauth_connection") + store.all("oauth_pending"))
                self.assertNotIn("synthetic-token", durable)
                self.assertNotIn("synthetic-device", durable)
                store.close()

    def test_active_missing_vault_entry_requires_reauthorization(self):
        with TemporaryDirectory() as directory:
            store = Store(Path(directory) / "state.sqlite")
            store.put(
                "oauth_connection",
                "lost",
                {
                    "id": "lost",
                    "credential_ref": "missing",
                    "state": "ready",
                },
            )
            GitHubDeviceFlow(store, TestVault())
            self.assertEqual(
                "failed_recovery_reauthorization_required",
                store.get("oauth_connection", "lost")["state"],
            )
            store.close()


class HarnessOwnershipTests(unittest.TestCase):
    def test_owner_window_stale_fixture_and_changed_process_rejected(self):
        bound = {"handle": 12, "pid": 8}
        fixture = "OSCAR-acceptance-unique.txt"
        self.assertTrue(fixture_window([{**bound, "name": fixture + " - Notepad"}], bound, fixture))
        for window in (
            {**bound, "name": "Owner notes - Notepad"},
            {**bound, "name": "OSCAR-acceptance-prior.txt - Notepad"},
            {"handle": 12, "pid": 99, "name": fixture},
        ):
            self.assertFalse(fixture_window([window], bound, fixture))
