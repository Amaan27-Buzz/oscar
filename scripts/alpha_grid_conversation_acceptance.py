"""Real installed-model follow-up through signed Grid admission and canonical history."""

import base64
import tempfile
from contextlib import closing
from pathlib import Path
from time import monotonic, sleep, time

from oscar.cloud import CloudConfig, CloudCore
from oscar.event_archive import SourceEvent
from oscar.models import ModelRequest, RoutingPolicy
from oscar.remote_grid import create_invitation
from tests.test_oauth_device import TestVault
from tests.test_remote_grid import DirectClient, keypair, signature

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="oscar-grid-conversation-") as temporary:
        root = Path(temporary)
        template = ModelRequest.from_config(
            {
                "mode": "local",
                "pinned_provider": "ollama-local",
                "pinned_model": "qwen3.5:4b",
                "max_output_tokens": 256,
                "ollama_think": False,
            }
        )
        config = CloudConfig(
            core_id="synthetic-alpha-core",
            data_dir=root / "data",
            manifest=ROOT / "config/development-models.json",
            secret_dir=root / "unused-vault",
            listen_host="127.0.0.1",
            listen_port=18766,
            ingress="loopback",
            allowed_hosts=("127.0.0.1",),
            model_request=template,
            model_timeout_seconds=120,
        )
        with closing(
            CloudCore(config, initialize=True, vault=TestVault(), credential_environ={})
        ) as core:
            h = core.harness
            executor = h.dispatcher.executors["models.reason"]
            executor.policy = RoutingPolicy(
                require_free=True,
                allow_local=True,
                allowed_providers=frozenset({"ollama-local"}),
                timeout_seconds=120,
                max_paid_cost=0,
            )
            h.router.refresh(template, executor.policy)
            assert h.router.rank(template, executor.policy), "Installed local model unavailable"
            device_key, device_public = keypair()
            owner_key, owner_public = keypair()
            invitation = create_invitation(
                core,
                "synthetic-alpha-phone",
                "mobile",
                "synthetic-install",
                device_public,
                retain=True,
                owner_public_key=owner_public,
            )
            enrolled = core.remote.enroll(
                {
                    "version": 2,
                    "challenge_id": invitation["challenge_id"],
                    "signature": signature(
                        device_key, base64.b64decode(invitation["signing_payload"])
                    ),
                }
            )
            phone = DirectClient(core, enrolled)
            source = SourceEvent(
                "owner",
                "The project codename is Cedar Otter, "
                "chosen for a calm and resourceful personality.",
                "desktop/conversation",
                time(),
                kind="conversation_owner",
            )
            h.archive.append(source, retain_authorized=True)
            task = phone.request(
                "submit",
                {
                    "text": "Explain how that observation could help.",
                    "kind": "text",
                    "target": h.node_id,
                    "parameters": {},
                    "retain": True,
                },
            )
            if task["approval_required"]:
                review = phone.request(
                    "challenge", {"operation": "approve", "task_id": task["task_id"]}
                )
                phone.request(
                    "complete",
                    {
                        "challenge_id": review["challenge_id"],
                        "signature": signature(
                            owner_key, base64.b64decode(review["signing_payload"])
                        ),
                    },
                )
            deadline = monotonic() + 125
            while monotonic() < deadline:
                result = phone.request("inspect", {"task_id": task["task_id"]})
                if result["state"] in {
                    "partially_verified",
                    "verified",
                    "blocked",
                    "failed",
                    "cancelled",
                    "unknown",
                }:
                    break
                sleep(0.1)
            answer = (result.get("result") or {}).get("value", "")
            assert "cedar" in answer.lower() and "otter" in answer.lower(), (
                "Real follow-up did not recover cross-device context"
            )
            assert source.content not in "\n".join(h.store.db.iterdump()), (
                "Prior conversation was duplicated in durable task state"
            )
            snapshot = phone.request("snapshot", {})
            assert any(
                e["speaker"] == "oscar" and "cedar" in e["text"].lower() for e in snapshot["events"]
            ), "Answer missing from shared canonical history"
            print("Real local Grid follow-up recovered Desktop context and retained its response.")
            print("Synthetic owner/device; no credentials, physical phone or personal data used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
