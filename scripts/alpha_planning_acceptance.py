"""Real verified-free cloud planning, signed Ask reviews and independent file proof.

All objectives, owner signing identities and state are disposable synthetic data.
No local models, paid calls, personal accounts or plaintext credential outputs.
"""

import argparse
import base64
import tempfile
from pathlib import Path
from time import monotonic, sleep

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.contracts import new_id
from oscar.credential_loading import existing_provider_environment
from oscar.desktop import Desktop
from oscar.harness import Harness
from oscar.models import ModelRequest, RoutingPolicy
from oscar.policy import PersonalPolicy
from oscar.registry import Registry
from scripts.start_oscar import ROOT, desktop_session


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    args = parser.parse_args()
    registry = Registry.load(ROOT / "config/development-models.json")
    credentials = existing_provider_environment(ROOT / ".env.local", registry.providers.values())
    template = ModelRequest.from_config(
        {
            "mode": "free_first",
            "pinned_provider": "openrouter",
            "pinned_model": args.model,
            "max_output_tokens": 4096,
        }
    )
    policy = RoutingPolicy(
        require_free=True,
        allowed_providers=frozenset({"openrouter"}),
        private_providers=frozenset({"openrouter"}),
        timeout_seconds=120,
        max_paid_cost=0,
    )
    with tempfile.TemporaryDirectory(prefix="oscar-cloud-plan-") as directory:
        root = Path(directory)
        with Harness(
            root / "core.sqlite",
            root / "workspace",
            ROOT / "config/development-models.json",
            template,
            node_id="oscar-local-core",
            credential_environ=credentials,
            model_timeout_seconds=120,
        ) as h:
            h.dispatcher.executors["models.reason"].policy = policy
            h.router.refresh(template, policy)
            assert h.router.rank(template, policy), "No verified-free cloud model available"
            session = desktop_session(h)
            core = Desktop(h.runtime, PersonalPolicy(h.store), h.executive.targets)
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            encoded = base64.b64encode(
                key.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            ).decode()
            core.register_owner_key(session, encoded, owner_authorized=True)

            def call(operation, payload):
                return core.request(
                    session,
                    {
                        "version": 1,
                        "request_id": new_id(),
                        "operation": operation,
                        "payload": payload,
                    },
                )

            def ask(text):
                return call("interact", {"mode": "Ask", "text": text, "context_id": ""})

            def approve(change):
                challenge = call("assistance_challenge", change)
                signature = key.sign(
                    base64.b64decode(challenge["signing_payload"]),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                    hashes.SHA256(),
                )
                return call(
                    "assistance_complete",
                    {
                        "challenge_id": challenge["challenge_id"],
                        "signature": base64.b64encode(signature).decode(),
                    },
                )

            path = root / "workspace/alpha-proof.txt"
            first = ask(
                "Delegate a worker Number note: calculate 37 + 58 using math.add, then save "
                "the actual result into alpha-proof.txt using files.write. Use two steps with "
                "an inputs handoff from arithmetic to file content."
            )
            assert "assistance_proposal" in first, first.get("state")
            assert not path.exists()
            approve(first["assistance_proposal"])
            deadline = monotonic() + 125
            while monotonic() < deadline:
                tasks = h.store.all("task")
                if tasks and tasks[-1]["state"] in {
                    "verified",
                    "partially_verified",
                    "failed",
                    "blocked",
                }:
                    break
                sleep(0.05)
            assert not path.exists(), "Draft inference must not execute the proposed effects"
            second = ask("Review the plan")
            assert second.get("assistance_proposal", {}).get("operation") == "plan_accept", (
                second.get("message")
            )
            approve(second["assistance_proposal"])
            deadline = monotonic() + 15
            while monotonic() < deadline:
                if path.is_file():
                    row = h.store.all("planner_request")[0]
                    steps = h.executive._tasks(row["accepted_goal"])
                    if steps and all(h.store.task(t).state == "verified" for t in steps):
                        break
                sleep(0.05)
            assert path.read_text(encoding="utf-8") == "95"
            row = h.store.all("planner_request")[0]
            steps = h.executive._tasks(row["accepted_goal"])
            assert len(steps) == 2 and all(h.store.task(t).state == "verified" for t in steps)
            assert h.store.all("executive_worker")
            print("PASS: real free cloud model planned a two-step Worker with a result handoff.")
            print("PASS: signed Ask reviews preceded effects; both steps and final file verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
