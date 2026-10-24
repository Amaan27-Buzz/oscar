"""Private installed Ollama inference through authenticated Desktop and both real reviews.

Only the exact local model below is eligible. No downloads, cloud aliases or owner data.
"""

import argparse
import base64
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from urllib.request import urlopen

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.contracts import new_id
from oscar.credentials import CredentialPool
from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness, ModelExecutor
from oscar.models import Funding, Mode, ModelRequest, ModelSpec, ProviderSpec, RoutingPolicy
from oscar.policy import PersonalPolicy
from oscar.providers import HTTPAdapter
from oscar.registry import Registry
from oscar.router import Router

ROOT = Path(__file__).resolve().parents[1]
MODEL = "qwen3.5:4b"
OUTPUT = ROOT / ".oscar" / "conversation-local-inference.json"


def source_hashes():
    paths = {Path(__file__).resolve()}
    paths.update(path.resolve() for path in (ROOT / "oscar").glob("*.py"))
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(paths)
    }


def run(full=False):
    output = ROOT / ".oscar/conversation-local-full-inference.json" if full else OUTPUT
    before = source_hashes()
    with urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
        models = json.load(response)["models"]
    installed = [model for model in models if model["name"] == MODEL]
    assert len(installed) == 1, "exact already-installed local model required"
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "state": "FAILED",
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "provider": "http://127.0.0.1:11434/api",
        "model": MODEL,
        "authority_mode": "full" if full else "ask",
        "installed_model_digest": installed[0]["digest"],
        "qualification": (
            "Real local model inference; synthetic owner and workspace; Desktop Core API"
        ),
        "sources": before,
    }
    started = monotonic()
    try:
        with TemporaryDirectory(prefix="oscar-conversation-local-") as temporary:
            root = Path(temporary)
            with Harness(
                root / "core.sqlite",
                root / "files",
                ROOT / "config/development-models.json",
                credential_environ={},
                start_services=True,
            ) as h:
                provider = ProviderSpec(
                    "local-acceptance",
                    "ollama",
                    "http://127.0.0.1:11434/api",
                    {},
                    local=True,
                    private=True,
                    provenance="exact installed local model; no cloud fallback",
                )
                model = ModelSpec(
                    provider.id,
                    MODEL,
                    frozenset({"text"}),
                    2,
                    {"reasoning": 1},
                    32768,
                    8192,
                    Funding.LOCAL,
                    provenance="installed local acceptance; quality tier is test configuration",
                )
                router = Router(
                    Registry([provider], [model]),
                    CredentialPool([provider], {}, h.store),
                    {"ollama": HTTPAdapter("ollama")},
                    h.store,
                )
                h.dispatcher.executors["models.reason"] = ModelExecutor(
                    router,
                    ModelRequest(
                        "template",
                        "template",
                        "",
                        input_tokens=4096,
                        max_output_tokens=8192,
                        mode=Mode.PRIVATE,
                        pinned_provider=provider.id,
                        pinned_model=MODEL,
                    ),
                    RoutingPolicy(
                        allowed_providers=frozenset({provider.id}),
                        max_attempts=1,
                        timeout_seconds=120,
                    ),
                )
                scopes = (
                    "heartbeat",
                    "desktop:connect",
                    "desktop:text",
                    "files:write",
                    "math",
                    "models",
                    "control:approve:" + h.node_id,
                )
                h.grid.register(Node("synthetic-desktop", NodeRole.DESKTOP, scopes))
                session = h.grid.pair("synthetic-desktop", scopes)
                key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                public = base64.b64encode(
                    key.public_key().public_bytes(
                        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                ).decode()
                desktop = Desktop(h.runtime, PersonalPolicy(h.store), h.executive.targets)
                desktop.register_owner_key(session, public, owner_authorized=True)

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

                def ask(text):
                    return call("interact", {"mode": "Ask", "text": text, "context_id": ""})

                def approve(change, family="assistance"):
                    challenge = call(family + "_challenge", change)
                    signature = key.sign(
                        base64.b64decode(challenge["signing_payload"]),
                        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                        hashes.SHA256(),
                    )
                    return call(
                        family + "_complete",
                        {
                            "challenge_id": challenge["challenge_id"],
                            "signature": base64.b64encode(signature).decode(),
                        },
                    )

                path = h.files.root / "welcome.txt"
                objective = 'Create welcome.txt as a note with exact text "Hello from local OSCAR."'
                if full:
                    activation = approve(
                        {
                            "mode": "full",
                            "lifetime_seconds": 600,
                            "capabilities": [
                                {
                                    "node_id": h.node_id,
                                    "session_id": h.session.id,
                                    "capability_id": cap,
                                }
                                for cap in ("models.reason", "files.write")
                            ],
                            "account_ids": [],
                            "resolve_ask_rules": sorted(
                                rule.id
                                for rule in desktop.policy.rules()
                                if rule.enabled and rule.effect == "ask"
                            ),
                        },
                        "authority",
                    )
                    assert activation["authority"]["mode"] == "full", activation
                    report["signed_standing_activation"] = True
                first = ask(objective)
                if full:
                    assert first.get("assistance_started", {}).get("mode") == "full", first
                else:
                    assert first.get("assistance_proposal", {}).get("operation") == "plan_draft", (
                        first
                    )
                    assert not h.store.all("task") and not path.exists()
                    approve(first["assistance_proposal"])
                deadline = monotonic() + 125
                while monotonic() < deadline:
                    tasks = h.store.all("task")
                    if tasks and tasks[-1]["state"] in {
                        "partially_verified",
                        "verified",
                        "failed",
                        "blocked",
                    }:
                        break
                    sleep(0.05)
                report["model_tasks"] = h.store.all("task")
                report["routing_evidence"] = h.store.all("route_history")
                report["model_result"] = [row.get("value") for row in h.store.all("result")]
                if not full:
                    assert not path.exists(), "model output must not execute"
                    second = ask("Review the plan")
                    assert (
                        second.get("assistance_proposal", {}).get("operation") == "plan_accept"
                    ), second
                    approve(second["assistance_proposal"])
                report["second_review_required"] = not full
                deadline = monotonic() + 5
                tasks = []
                while monotonic() < deadline:
                    row = h.store.all("planner_request")[0]
                    tasks = (
                        h.executive._tasks(row["accepted_goal"]) if row.get("accepted_goal") else []
                    )
                    if tasks and all(h.store.task(task).state == "verified" for task in tasks):
                        break
                    sleep(0.05)
                assert tasks and all(h.store.task(task).state == "verified" for task in tasks)
                assert path.read_text(encoding="utf-8") == "Hello from local OSCAR."
                assert ask("Proceed with the plan")["state"] == "blocked"
                report.update(
                    state="PASS",
                    objective=objective,
                    artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    verified_tasks=[asdict(h.store.task(task)) for task in tasks],
                    evidence=h.store.all("evidence"),
                    no_effect_before_second_signature=not full,
                    accepted_plan=h.store.get("executive_goal", row["accepted_goal"])["steps"],
                )
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["elapsed_seconds"] = round(monotonic() - started, 3)
        report["source_stable"] = source_hashes() == before
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    key: report.get(key)
                    for key in ("state", "model", "elapsed_seconds", "source_stable", "error")
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Use signed synthetic Full Access")
    run(parser.parse_args().full)
