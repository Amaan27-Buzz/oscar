"""Private installed Ollama inference through authenticated Desktop and both real reviews.

Only the exact local model below is eligible. No downloads, cloud aliases or owner data.
"""

import argparse
import base64
import hashlib
import json
import subprocess
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from urllib.request import urlopen

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.cloud import CloudConfig, CloudCore
from oscar.contracts import new_id
from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.policy import PersonalPolicy

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


def run(full=False, multistep=False, handoff=False, model=MODEL):
    multistep = multistep or handoff
    output = ROOT / ".oscar/conversation-local-full-inference.json" if full else OUTPUT
    if multistep:
        output = ROOT / (
            ".oscar/conversation-local-multistep-full.json"
            if full
            else ".oscar/conversation-local-multistep-ask.json"
        )
    if handoff:
        output = ROOT / (
            ".oscar/conversation-local-handoff-full.json"
            if full
            else ".oscar/conversation-local-handoff-ask.json"
        )
    if model != MODEL:
        output = output.with_stem(output.stem + "-" + model.replace(":", "-"))
    output = output.with_stem(output.stem + "-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    before = source_hashes()
    with urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
        models = json.load(response)["models"]
    installed = [entry for entry in models if entry["name"] == model]
    assert len(installed) == 1, "exact already-installed local model required"
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "state": "FAILED",
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "provider": "http://127.0.0.1:11434/api",
        "model": model,
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
            manifest = root / "models.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "providers": [
                            {
                                "id": "local-acceptance",
                                "adapter": "ollama",
                                "base_url": "http://127.0.0.1:11434/api",
                                "credential_envs": {},
                                "local": True,
                                "private": True,
                                "provenance": "exact installed local model; no cloud fallback",
                            }
                        ],
                        "models": [
                            {
                                "provider_id": "local-acceptance",
                                "id": model,
                                "capabilities": ["text", "structured"],
                                "quality": 2,
                                "affinities": {"reasoning": 1},
                                "context_limit": 32768,
                                "output_limit": 8192,
                                "funding": "local",
                                "provenance": "installed local acceptance; unbenchmarked tier",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            configuration = {
                "max_output_tokens": 8192,
                "mode": "private",
                "pinned_provider": "local-acceptance",
                "pinned_model": model,
                "ollama_think": False,
                "required": ["text", "structured"],
            }
            report["model_configuration"] = configuration
            report["normal_cloud_configuration"] = True
            secrets = root / "secrets"
            secrets.mkdir()
            cloud = root / "cloud.json"
            cloud.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "environment": "production",
                        "core_id": "synthetic-model-core",
                        "data_dir": str(root / "data"),
                        "manifest": str(manifest),
                        "secret_dir": str(secrets),
                        "listen_host": "127.0.0.1",
                        "listen_port": 8080,
                        "ingress": "loopback",
                        "allowed_hosts": ["127.0.0.1"],
                        "provider_secrets": {},
                        "model_request": configuration,
                    }
                ),
                encoding="utf-8",
            )
            with closing(CloudCore(CloudConfig.load(cloud), initialize=True)) as core:
                h = core.harness
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

                adapter = h.adapters["ollama"]
                parse_text = adapter._text
                build_request = adapter._request

                def observe_request(*args):
                    request = build_request(*args)
                    body = json.loads(request.data)
                    report["provider_decoding"] = {k: body.get(k) for k in ("format", "options")}
                    return request

                def observe_text(data, streaming=False, *, images=False):
                    value = parse_text(data, streaming, images=images)
                    report["synthetic_provider_text"] = value
                    return value

                adapter._text = observe_text
                adapter._request = observe_request
                path = h.files.root / "welcome.txt"
                objective = 'Create welcome.txt as a note with exact text "Hello from local OSCAR."'
                expected = "Hello from local OSCAR."
                if multistep:
                    objective = (
                        "Calculate 17 + 25 using math.add, then create welcome.txt with exact "
                        'text "42" using files.write. Use two separate steps; the file step '
                        "must depend on the arithmetic step."
                    )
                    expected = "42"
                if handoff:
                    objective = (
                        "Calculate 17 + 25 using math.add, then save the actual result value "
                        "into welcome.txt using files.write. Use two steps and an inputs handoff "
                        "from the arithmetic step to file content; do not calculate or hardcode "
                        "the file content yourself."
                    )
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
                                for cap in ("models.reason", "files.write", "math.add")
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
                    if len(tasks) == (2 if multistep else 1) and all(
                        h.store.task(task).state == "verified" for task in tasks
                    ):
                        break
                    sleep(0.05)
                assert len(tasks) == (2 if multistep else 1) and all(
                    h.store.task(task).state == "verified" for task in tasks
                )
                assert path.read_text(encoding="utf-8") == expected
                if multistep:
                    from oscar.capabilities import addition_operands

                    steps = h.store.get("executive_goal", row["accepted_goal"])["steps"]
                    assert len(steps) == len(tasks) == 2, "two real dependent steps required"
                    arithmetic = next(s for s in steps if s["capability_id"] == "math.add")
                    written = next(s for s in steps if s["capability_id"] == "files.write")
                    assert arithmetic["id"] in written["depends_on"]
                    assert addition_operands(arithmetic["intent"]["text"]) == (17, 25)
                    if handoff:
                        assert written["inputs"] == [
                            {"from_step": arithmetic["id"], "select": [], "to": ["content"]}
                        ]
                        copies = [h.store.get("plan", task)["executive"] for task in tasks]
                        report["result_handoff_provenance"] = [
                            p["inputs"] for p in copies if p.get("inputs")
                        ]
                        assert len(report["result_handoff_provenance"]) == 1
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
        with output.open("x", encoding="utf-8") as receipt:
            receipt.write(json.dumps(report, indent=2, default=str) + "\n")
        print(
            json.dumps(
                {
                    key: report.get(key)
                    for key in ("state", "model", "elapsed_seconds", "source_stable", "error")
                }
                | {"receipt": str(output.relative_to(ROOT))}
            ),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Use signed synthetic Full Access")
    parser.add_argument("--multistep", action="store_true", help="Require arithmetic then file")
    parser.add_argument("--handoff", action="store_true", help="Copy actual verified result")
    parser.add_argument(
        "--model",
        default=MODEL,
        choices=(MODEL, "qwen3.5:9b"),
        help="Select an already-installed local model; never download",
    )
    args = parser.parse_args()
    run(args.full, args.multistep, args.handoff, args.model)
