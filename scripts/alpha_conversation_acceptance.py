"""Real local inference through signed Desktop admission and restart history.

Disposable synthetic conversation only; no UI, personal data or credential files.
"""

import argparse
import base64
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.contracts import new_id
from oscar.desktop import Desktop
from oscar.harness import Harness
from oscar.models import ModelRequest
from oscar.policy import PersonalPolicy
from scripts.start_oscar import ROOT, desktop_session


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3.5:0.8b")
    args = parser.parse_args()
    template = ModelRequest.from_config(
        {
            "mode": "local",
            "pinned_provider": "ollama-local",
            "pinned_model": args.model,
            "max_output_tokens": 256,
            "ollama_think": False,
        }
    )
    with tempfile.TemporaryDirectory(prefix="oscar-conversation-") as directory:
        root = Path(directory)
        for restarted in (False, True):
            with Harness(
                root / "core.sqlite",
                root / "workspace",
                ROOT / "config/development-models.json",
                template,
                node_id="oscar-local-core",
                model_timeout_seconds=120,
                credential_environ={},
            ) as h:
                core = Desktop(
                    h.runtime,
                    PersonalPolicy(h.store),
                    {
                        h.node_id: (h.dispatcher, h.session),
                    },
                )
                session = desktop_session(h)
                key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                encoded = base64.b64encode(
                    key.public_key().public_bytes(
                        serialization.Encoding.DER,
                        serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                ).decode()
                core.register_owner_key(session, encoded, owner_authorized=True)

                def call(operation, payload, core=core, session=session):
                    return core.request(
                        session,
                        {
                            "version": 1,
                            "request_id": new_id(),
                            "operation": operation,
                            "payload": payload,
                        },
                    )

                if restarted:
                    assert (
                        h.store.get("desktop_model", "selection")["configuration"]["pinned_model"]
                        == args.model
                    )
                    turns = call("conversation", {"before": 0})["turns"]
                    assert len(turns) == 2 and all(t["retained"] for t in turns)
                    assert turns[0]["text"] == "Explain briefly how a rainbow forms."
                    assert turns[1]["text"].strip()
                    print(
                        "PASS: real model response and canonical conversation "
                        "survived Core restart."
                    )
                    continue
                selected = call("select_model", {"model": args.model})
                assert selected["selected"] == args.model
                assert args.model in call("snapshot", {})["models"]["available"]
                task = call(
                    "interact",
                    {
                        "mode": "Ask",
                        "text": "Explain briefly how a rainbow forms.",
                        "context_id": "",
                    },
                )
                if task["state"] == "planned":
                    challenge = call(
                        "challenge", {"operation": "approve", "task_id": task["task_id"]}
                    )
                    signature = key.sign(
                        base64.b64decode(challenge["signing_payload"]),
                        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                        hashes.SHA256(),
                    )
                    task = call(
                        "complete",
                        {
                            "challenge_id": challenge["challenge_id"],
                            "signature": base64.b64encode(signature).decode(),
                        },
                    )
                assert task.get("value") or task.get("response"), task["state"]
                history = h.store.all("route_history")
                assert any(r.get("provider") == "ollama-local" for r in history)
                print("PASS: signed Desktop request reached the real local Model Router.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
