"""Generated Windows speech -> free Groq transcription -> canonical Ask; no microphone/playback."""

import base64
import hashlib
import os
import struct
import tempfile
from dataclasses import replace
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from oscar.cloud_speech import GroqRecognizer
from oscar.credential_loading import existing_provider_environment, import_missing_vault_bindings
from oscar.desktop import Desktop
from oscar.desktop_voice import DesktopVoice
from oscar.harness import Harness, ModelExecutor
from oscar.models import RoutingPolicy
from oscar.policy import PersonalPolicy
from oscar.registry import Registry
from oscar.voice_adapters import WindowsSpeech
from oscar.voice_contracts import AudioFrame, Origin, StopToken
from oscar.voice_identity import oscar_voice_profile
from scripts.start_oscar import desktop_session
from tests.test_oauth_device import TestVault

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if os.name != "nt":
        raise OSError("Generated installed Windows speech required")
    config = ROOT / ".env.local"
    digest = hashlib.sha256(config.read_bytes()).digest()
    registry = Registry.load(ROOT / "config/development-models.json")
    credentials = existing_provider_environment(config, [registry.providers["groq"]])
    profile = replace(
        oscar_voice_profile(), provider="windows-system-speech", preferred_voice="local-system"
    )
    pcm = b"".join(
        chunk.pcm
        for chunk in WindowsSpeech().synthesize(
            "OSCAR, what is seven plus eight?", profile, "synthetic-alpha", StopToken()
        )
    )
    values = tuple(value / 32768 for (value,) in struct.iter_unpack("<h", pcm))
    frames = tuple(
        AudioFrame(values[i : i + 512], i / 16000, "synthetic-voice", origin=Origin.SIMULATED)
        for i in range(0, len(values), 512)
    )

    class Capture:
        def frames(self, stop):
            for frame in frames:
                stop.check()
                yield frame

        def close(self):
            pass

    with tempfile.TemporaryDirectory(prefix="oscar-cloud-voice-") as temporary:
        root = Path(temporary)
        with Harness(
            root / "core.sqlite",
            root / "workspace",
            ROOT / "config/development-models.json",
            node_id="oscar-local-core",
            credential_environ=credentials,
            vault=TestVault(),
        ) as h:
            assert h.runtime.setup is not None
            import_missing_vault_bindings(
                h.runtime.setup, [registry.providers["groq"]], credentials
            )
            for slot in h.pool.slots.values():
                if slot.provider == "groq" and slot.present:
                    h.runtime.setup.confirm_free_plan(slot.id, owner_authorized=True)
            executor = h.dispatcher.executors["models.reason"]
            assert isinstance(executor, ModelExecutor)
            executor.policy = RoutingPolicy(
                require_free=True, allowed_providers=frozenset({"groq"}), max_paid_cost=0
            )
            owner = desktop_session(h)
            core = Desktop(h.runtime, PersonalPolicy(h.store), h.executive.targets)
            core.voice = DesktopVoice(core, Capture(), GroqRecognizer(h), mode="Ask", muted=False)
            core.request(
                owner,
                {
                    "version": 1,
                    "request_id": "synthetic-voice-consent",
                    "operation": "enable_voice",
                    "payload": {"enabled": True},
                },
            )
            core.voice.start(owner)
            core.voice.thread.join(45)
            assert not core.voice.thread.is_alive(), "Voice acceptance timed out"
            result = core.voice.inspect(owner)
            assert result.get("state") == "planned", "Voice must preserve Ask review"
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public = base64.b64encode(
                key.public_key().public_bytes(
                    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
                )
            ).decode()
            core.register_owner_key(owner, public, owner_authorized=True)

            def call(operation, payload):
                return core.request(
                    owner,
                    {
                        "version": 1,
                        "request_id": "synthetic-" + operation,
                        "operation": operation,
                        "payload": payload,
                    },
                )

            review = call("challenge", {"operation": "approve", "task_id": result["task_id"]})
            signature = key.sign(
                base64.b64decode(review["signing_payload"]),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
            result = call(
                "complete",
                {
                    "challenge_id": review["challenge_id"],
                    "signature": base64.b64encode(signature).decode(),
                },
            )
            assert result.get("state") == "verified" and str(result.get("value")) == "15", (
                "Synthetic voice objective not verified"
            )
            history = core.conversation(owner)
            assert len(history["turns"]) == 2 and history["turns"][-1]["text"] == "15", (
                "Voice/text archive continuity missing"
            )
    assert digest == hashlib.sha256(config.read_bytes()).digest(), "Existing configuration changed"
    print("Generated speech, free Groq transcription, signed Ask and retained history passed.")
    print("No microphone, speaker playback, local reasoning model or real owner enrollment used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
