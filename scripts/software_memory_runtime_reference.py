"""Opted-in real offline indexes through the normal synthetic-owner Core surfaces.

Requires already cached models and an explicitly administered loopback Neo4j.
Creates only a new selected workspace. No downloads or non-loopback sockets.
"""

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import secrets
import socket
import subprocess
from datetime import UTC, datetime
from http.client import HTTPConnection
from pathlib import Path
from time import monotonic, sleep, time
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.cloud import CloudConfig, CloudCore
from oscar.cloud_http import CloudHTTPServer
from oscar.contracts import new_id
from oscar.desktop import Desktop
from oscar.event_archive import MemoryWriter, SourceEvent
from oscar.grid import Node, NodeRole
from oscar.local_memory import LocalMemory
from oscar.memory_fabric import MemoryFabric
from oscar.policy import PersonalPolicy
from oscar.remote_client import request_proof
from oscar.remote_grid import create_invitation

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "Travelling without internet requires locally hosted models"
QUERY = "Recall artificial intelligence while disconnected abroad"


def hashes_now():
    paths = [Path(__file__), *(ROOT / "oscar").glob("*.py")]
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(paths)
    }


def sign(key, data):
    return base64.b64encode(
        key.sign(
            data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256()
        )
    ).decode()


def public_key(key):
    return base64.b64encode(
        key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    ).decode()


class LoopbackClient:
    """Reference HTTP transport; production GridClient still requires trusted HTTPS."""

    def __init__(self, port, key):
        self.port, self.key, self.session = port, key, None

    def post(self, path, data, headers=None, expected=200):
        body = json.dumps(data, separators=(",", ":")).encode()
        connection = HTTPConnection("127.0.0.1", self.port, timeout=90)
        try:
            connection.request(
                "POST", path, body, {"Content-Type": "application/json", **(headers or {})}
            )
            response = connection.getresponse()
            result = json.loads(response.read())
            assert response.status == expected, (response.status, result)
            return result
        finally:
            connection.close()

    def request(self, operation, payload, expected=200):
        data = {"version": 2, "operation": operation, "request_id": new_id(), "payload": payload}
        body = json.dumps(data, separators=(",", ":")).encode()
        nonce, instant = secrets.token_hex(16), str(int(time() * 1000))
        node, session = self.session["node_id"], self.session["session_id"]
        return self.post(
            "/v2/grid/request",
            data,
            {
                "Authorization": "Bearer " + self.session["token"],
                "X-Oscar-Node": node,
                "X-Oscar-Session": session,
                "X-Oscar-Nonce": nonce,
                "X-Oscar-Time": instant,
                "X-Oscar-Signature": sign(
                    self.key, request_proof(node, session, nonce, instant, body)
                ),
            },
            expected,
        )

    def recall(self, core_id):
        view = self.request(
            "submit",
            {"text": QUERY, "kind": "text", "target": core_id, "parameters": {}, "retain": False},
        )
        deadline = monotonic() + 15
        while view["state"] in {"planned", "executing", "awaiting_result", "verifying"}:
            assert monotonic() < deadline, "bounded recall completion"
            sleep(0.05)
            view = self.request("inspect", {"task_id": view["task_id"]})
        return view


def retained(harness, content, relationship="owner"):
    event = SourceEvent(relationship, content, "synthetic-authorized-owner", time() - 10)
    harness.archive.append(event, retain_authorized=True)
    memory = MemoryWriter(harness.archive).retain(
        (event.id,), content, "episodic", retain_authorized=True, inferred=False
    )
    return event, memory


def desktop_recall(harness):
    scopes = (
        "heartbeat",
        "desktop:connect",
        "desktop:text",
        "desktop:inspect",
        "memory:read",
        "control:inspect:" + harness.node_id,
        "control:approve:" + harness.node_id,
    )
    harness.grid.register(Node("synthetic-local-reader", NodeRole.DESKTOP, scopes))
    session = harness.grid.pair("synthetic-local-reader", scopes)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    desktop = Desktop(harness.runtime, PersonalPolicy(harness.store), harness.executive.targets)
    desktop.register_owner_key(session, public_key(key), owner_authorized=True)

    def call(operation, payload):
        return desktop.request(
            session,
            {
                "version": 1,
                "operation": operation,
                "request_id": new_id(),
                "payload": payload,
            },
        )

    view = call("interact", {"mode": "Ask", "text": QUERY, "context_id": ""})
    assert view["approval_required"]
    challenge = call("challenge", {"operation": "approve", "task_id": view["task_id"]})
    result = call(
        "complete",
        {
            "challenge_id": challenge["challenge_id"],
            "signature": sign(key, base64.b64decode(challenge["signing_payload"])),
        },
    )
    assert result["response"] == SOURCE and result["response_status"] == "RECALLED", result
    return desktop, session, result


def run(arguments):
    root = arguments.workspace.resolve()
    root.mkdir(parents=True, exist_ok=False)
    before = hashes_now()
    report = {
        "state": "FAILED",
        "observed_at": datetime.now(UTC).isoformat(),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "qualification": (
            "Real cached FastEmbed/BM25/reranker, embedded Qdrant, local Neo4j Graphiti; "
            "synthetic owners; loopback HTTP signed Grid and Desktop Core API; "
            "no physical or hosted acceptance"
        ),
        "sources": before,
        "network": {"non_loopback_attempts": [], "loopback_connections": 0},
        "versions": {
            package: importlib.metadata.version(package)
            for package in ("fastembed", "qdrant-client", "graphiti-core", "onnxruntime", "neo4j")
        },
    }
    native_connect = socket.socket.connect

    def connect(sock, address):
        if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
            report["network"]["non_loopback_attempts"].append(str(address))
            raise PermissionError("offline acceptance forbids non-loopback sockets")
        report["network"]["loopback_connections"] += 1
        return native_connect(sock, address)

    secret_dir = root / "secrets"
    secret_dir.mkdir(mode=0o700)
    secret = secret_dir / "graph-password"
    secret.write_text(json.dumps({"secret": secrets.token_hex(24), "expires_at": None}))
    secret.chmod(0o600)
    manifest = root / "models.json"
    manifest.write_text(json.dumps({"version": 1, "providers": [], "models": []}))
    with socket.socket() as available:
        available.bind(("127.0.0.1", 0))
        port = available.getsockname()[1]
    config_path = root / "cloud.json"
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "environment": "production",
                "core_id": "synthetic-memory-core",
                "data_dir": str(root / "data"),
                "manifest": str(manifest),
                "secret_dir": str(secret_dir),
                "listen_host": "127.0.0.1",
                "listen_port": port,
                "ingress": "loopback",
                "allowed_hosts": ["127.0.0.1"],
                "provider_secrets": {"OSCAR_NEO4J_PASSWORD": "graph-password"},
                "local_memory": {
                    "version": 1,
                    "authorized_local_projection": True,
                    "relationship_id": "owner",
                    "model_cache": str(arguments.model_cache.resolve()),
                    "bm25_model_dir": str(arguments.bm25_model_dir.resolve()),
                    "qdrant_path": str(root / "derived"),
                    "neo4j": {
                        "uri": "bolt://127.0.0.1:17687",
                        "user": "neo4j",
                        "password_env": "OSCAR_NEO4J_PASSWORD",
                        "database": "neo4j",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    config = CloudConfig.load(config_path)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = LoopbackClient(port, key)
    started = monotonic()
    core = server = None
    try:
        with (
            patch.dict(os.environ, {"HF_HUB_OFFLINE": "1", "GRAPHITI_TELEMETRY_ENABLED": "false"}),
            patch.object(socket.socket, "connect", connect),
        ):
            core = CloudCore(config, initialize=True)
            server = CloudHTTPServer(core)
            server.start()
            h = core.harness
            assert core.ready() and isinstance(h.memory, LocalMemory), core.status()
            assert h.memory.vector and h.memory.graph and h.memory.reranker, h.memory.status()
            event, memory = retained(h, SOURCE)
            foreign, _ = retained(h, "Foreign relationship confidential evidence", "other-owner")
            baseline = MemoryFabric(h.archive).retrieve("owner", QUERY)
            assert not baseline.hits, "zero lexical-overlap baseline required"
            report["archive_only_paraphrase"] = {
                "hits": len(baseline.hits),
                "attempts": baseline.attempts,
            }
            evidence = h.memory.retrieve("owner", QUERY)
            assert [hit.memory.id for hit in evidence.hits] == [memory.id], evidence
            assert {"3-qdrant-hybrid", "4-graphiti-temporal"} <= set(evidence.hits[0].paths), (
                evidence
            )
            report["configured_paraphrase"] = {
                "memory_id": memory.id,
                "source_event_id": event.id,
                "paths": evidence.hits[0].paths,
                "rerank_score": evidence.hits[0].rerank_score,
                "health": core.status()["memory"],
                "foreign_source_excluded": foreign.id not in evidence.hits[0].memory.event_ids,
            }
            desktop, desktop_session, desktop_view = desktop_recall(h)
            assert desktop_view["source_event_ids"] == [event.id], desktop_view
            report["desktop"] = {
                "state": desktop_view["state"],
                "response_status": desktop_view["response_status"],
                "source_event_ids": desktop_view["source_event_ids"],
                "signed_ask_review": True,
            }
            invitation = create_invitation(
                core,
                "synthetic-mobile-reader",
                "mobile",
                "synthetic-installation",
                public_key(key),
                memory_control=True,
            )
            client.session = client.post(
                "/v2/grid/enroll",
                {
                    "version": 2,
                    "challenge_id": invitation["challenge_id"],
                    "signature": sign(key, base64.b64decode(invitation["signing_payload"])),
                },
            )
            for kind, identity in (
                ("session", client.session["session_id"]),
                ("node", client.session["node_id"]),
            ):
                row = h.store.get(kind, identity)
                h.store.put(
                    kind,
                    identity,
                    {
                        **row,
                        "scopes": [scope for scope in row["scopes"] if scope != "memory:manage"],
                    },
                )
            view = client.recall(config.core_id)
            assert view["result"]["value"] == SOURCE and view["response_status"] == "RECALLED", view
            assert (
                view["source_event_ids"] == [event.id] and view["result"]["status"] == "REPORTED"
            ), view
            assert any(
                row["event"] == "memory_preflight" and memory.id in row["memory_ids"]
                for row in h.store.ledger(view["task_id"])
            )
            assert SOURCE not in json.dumps(h.store.all("result") + h.store.all("action_receipt"))
            assert QUERY not in " ".join(
                row[0] for row in h.store.db.execute("SELECT data FROM records")
            )
            assert QUERY not in " ".join(
                row[0] for row in h.store.db.execute("SELECT data FROM audit")
            )
            report["remote"] = {
                "state": view["state"],
                "response_status": view["response_status"],
                "source_event_ids": view["source_event_ids"],
                "raw_result_status": view["result"]["status"],
                "answer_copy_in_durable_results": False,
                "read_without_retention": True,
                "read_without_management": True,
            }
            server.close()
            server = None
            core.close()
            core = CloudCore(config)
            server = CloudHTTPServer(core)
            server.start()
            h = core.harness
            assert core.ready()
            old = client.request("inspect", {"task_id": view["task_id"]})
            assert old["result"] is None and old["response_status"] == "UNKNOWN", old
            restarted = client.recall(config.core_id)
            assert restarted["result"]["value"] == SOURCE and restarted["source_event_ids"] == [
                event.id
            ], restarted
            report["restart"] = {
                "canonical_source_survived": True,
                "fresh_recall": restarted["response_status"],
                "old_ephemeral_answer": old["response_status"],
                "health": core.status()["memory"],
            }
            # Withdraw only read, leaving device authentication and every other grant intact.
            row = h.store.get("session", client.session["session_id"])
            h.store.put(
                "session",
                row["id"],
                {
                    **row,
                    "scopes": [scope for scope in row["scopes"] if scope != "memory:read"],
                },
            )
            denied = client.request("inspect", {"task_id": restarted["task_id"]}, expected=403)
            snapshot = client.request("snapshot", {})
            assert restarted["task_id"] not in [item["task_id"] for item in snapshot["tasks"]]
            assert denied["error"] == "permission_denied"
            report["withdrawal"] = {
                "exact_session_read_denied": True,
                "ephemeral_task_omitted": True,
            }
            h.store.put("session", row["id"], row)  # Explicit synthetic owner fixture regrant.
            # Actual derived-state drift: remove only markers in these new owned projections.
            h.memory.vector.client.delete_collection(h.memory.vector.collection)
            graph = h.memory.graph
            graph.loop.run_until_complete(
                graph.graph.driver.execute_query(
                    "MATCH (n:OSCARProjectionState {group_id:$group}) DELETE n", group=graph.group
                )
            )
            degraded = h.memory.retrieve("owner", "Recall travelling without internet")
            assert [hit.memory.id for hit in degraded.hits] == [memory.id]
            assert not any(
                "qdrant" in path or "graphiti" in path for path in degraded.hits[0].paths
            )
            report["derived_drift"] = {
                "health": core.status()["memory"],
                "canonical_fallback_paths": degraded.hits[0].paths,
                "unavailable": degraded.unavailable,
            }
            h.memory.forget(memory.id, owner_authorized=True, forget_sources=True)
            after = client.request("inspect", {"task_id": restarted["task_id"]})
            assert (
                after["result"] is None
                and after["response_status"] == "UNKNOWN"
                and not after["source_event_ids"]
            ), after
            assert not h.memory.retrieve("owner", QUERY).hits
            assert not h.memory.vector.query(QUERY, "owner") and not h.memory.graph.query(
                QUERY, "owner"
            )
            assert not h.archive.memories("owner")
            graph_rows, _, _ = h.memory.graph.loop.run_until_complete(
                h.memory.graph.graph.driver.execute_query(
                    "MATCH (n:OSCARMemoryProjection {group_id:$group}) RETURN count(n) AS count",
                    group=h.memory.graph.group,
                )
            )
            assert graph_rows[0]["count"] == 0
            assert h.memory.vector.client.count(h.memory.vector.collection, exact=True).count == 1
            report["forget"] = {
                "old_answer_withdrawn": True,
                "canonical_admission_empty": True,
                "physical_semantic_empty": True,
                "physical_temporal_empty": True,
                "temporal_projection_nodes": 0,
                "semantic_points_only_generation_marker": 1,
                "health": core.status()["memory"],
            }
            report["state"] = "PASS"
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        if server:
            server.close()
        if core:
            core.close()
        report["elapsed_seconds"] = round(monotonic() - started, 3)
        report["source_stable"] = hashes_now() == before
        output = root / "receipt.json"
        output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    key: report.get(key)
                    for key in ("state", "elapsed_seconds", "source_stable", "error")
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--model-cache", type=Path, required=True)
    parser.add_argument("--bm25-model-dir", type=Path, required=True)
    run(parser.parse_args())
