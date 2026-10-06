"""Explicit temporary software fixture and JVM interoperability; never owner/device enrollment."""

import argparse
import base64
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from threading import Event

from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.policy import PersonalPolicy
from oscar.sunday import Sunday, SundayServer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve-emulator-fixture", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    output = root / ".oscar/sunday"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sunday-reference-") as directory:
        temporary = Path(directory)
        with Harness(
            temporary / "core.db", temporary / "workspace", Path("config/development-models.json")
        ) as h:
            scopes = (
                "heartbeat",
                "sunday:connect",
                "sunday:inspect",
                "sunday:text",
                "math",
                "control:inspect:" + h.node_id,
                "control:approve:" + h.node_id,
                "control:cancel:" + h.node_id,
            )
            h.grid.register(Node("reference-sunday-software", NodeRole.SUNDAY, scopes))
            session = h.grid.pair("reference-sunday-software", scopes)
            core = Sunday(
                h.runtime, PersonalPolicy(h.store), {h.node_id: (h.dispatcher, h.session)}
            )
            compiler = Path(shutil.which("javac") or "")
            java = compiler.parent / ("java.exe" if compiler.suffix == ".exe" else "java")
            source = root / "sunday/app/src/main/java/io/dawnlight/oscar/sunday/OwnerWire.java"
            subprocess.run(
                [str(compiler), "--release", "17", "-d", str(temporary), str(source)], check=True
            )
            process = subprocess.Popen(
                [str(java), "-cp", str(temporary), "io.dawnlight.oscar.sunday.OwnerWire"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                assert process.stdout and process.stdin
                encoded = process.stdout.readline().strip()
                core.register_owner_key(session, encoded, owner_authorized=True)
                proposed = core.request(
                    session,
                    {
                        "version": 1,
                        "operation": "text",
                        "request_id": "jvm-text",
                        "payload": {"text": "2 + 3"},
                    },
                )
                challenge = core.request(
                    session,
                    {
                        "version": 1,
                        "operation": "challenge",
                        "request_id": "jvm-challenge",
                        "payload": {"operation": "approve", "task_id": proposed["task_id"]},
                    },
                )
                process.stdin.write(challenge["signing_payload"] + "\n")
                process.stdin.flush()
                signature = process.stdout.readline().strip()
                process.wait(timeout=10)
                if process.returncode != 0 or not signature:
                    raise RuntimeError("JVM signature executor failed")
                # Public reference key/signature only; no private key retained.
                base64.b64decode(signature, validate=True)
                result = core.request(
                    session,
                    {
                        "version": 1,
                        "operation": "complete",
                        "request_id": "jvm-approve",
                        "payload": {
                            "challenge_id": challenge["challenge_id"],
                            "signature": signature,
                        },
                    },
                )
                if result["state"] != "verified" or result.get("value") != "5":
                    raise RuntimeError("JVM/Core objective verification failed")
                report = {
                    "evidence_class": "REFERENCE_JVM_CORE_LOOPBACK",
                    "signature": "VERIFIED_PSS_INTEROPERABILITY",
                    "task_state": result["state"],
                    "value": result["value"],
                    "evidence_ids": result["evidence_ids"],
                    "android_keystore": "NOT_RUN",
                    "owner_biometric_pin": "NOT_RUN",
                    "physical_android": "NOT_RUN",
                }
                (output / "jvm-reference.json").write_text(
                    json.dumps(report, indent=2), encoding="utf-8"
                )
                print(json.dumps(report, indent=2))
                if args.serve_emulator_fixture:
                    with SundayServer(core) as server:
                        # Synthetic ephemeral session; never a real owner Core/database.
                        fixture = {
                            "url": server.url,
                            "node_id": session.node_id,
                            "session_id": session.id,
                            "token": session.token,
                        }
                        (output / "emulator-session.json").write_text(
                            json.dumps(fixture), encoding="utf-8"
                        )
                        print(
                            "REFERENCE_LOOPBACK_ONLY; no microphone, replies or real owner grants; "
                            + server.url,
                            flush=True,
                        )
                        for _ in range(90):
                            h.grid.heartbeat(h.session)
                            Event().wait(10)  # Bounded software-only inspection fixture.
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
