"""Disposable Windows software composition. Never auto-enroll an owner's real Core.

run_surface is also usable by a trusted, already enrolled Core composition.
"""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from threading import Event, Thread

from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole, SessionHandle
from oscar.harness import Harness
from oscar.mobile import MobileServer
from oscar.policy import PersonalPolicy

ROOT = Path(__file__).resolve().parents[1]


def reference_stage(stderr: str) -> str:
    """Only known acceptance markers can escape native diagnostics, never bootstrap material."""
    stages = {
        "bootstrap",
        "cng",
        "xaml",
        "tray",
        "ready",
        "propose",
        "challenge",
        "complete",
        "show",
        "render",
        "closed",
    }
    observed = [
        line.removeprefix("desktop.reference.stage=")
        for line in stderr.splitlines()
        if line.removeprefix("desktop.reference.stage=") in stages
    ]
    return observed[-1] if observed else "unknown"


def run_surface(
    core: Desktop,
    session: SessionHandle,
    *,
    self_check: bool = False,
    modifiers: int = 3,
    key: int = 79,
    boundary: str = "Enrolled OSCAR Core",
) -> int:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if not 1 <= key <= 255 or modifiers & ~15 or modifiers < 0:
        raise ValueError("Windows virtual key and supported modifier bits required")

    receipt = json.loads((ROOT / "mobile/orb-render.json").read_text())
    orb = ROOT / "mobile/app/src/main/res/drawable-nodpi/oscar_orb.png"
    if (
        receipt["source_sha256"]
        != hashlib.sha256((ROOT / "assets/brand/oscar-orb.svg").read_bytes()).hexdigest()
        or receipt["render_sha256"] != hashlib.sha256(orb.read_bytes()).hexdigest()
    ):
        raise ValueError("canonical Orb render/source mismatch")
    owner_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    encoded = base64.b64encode(
        owner_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    ).decode()
    # Trusted composition API, never exposed to the surface's HTTP listener.
    core.register_owner_key(session, encoded, owner_authorized=True)
    output = ROOT / ".oscar/desktop"
    output.mkdir(parents=True, exist_ok=True)
    shell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    arguments = [
        str(shell),
        "-NoProfile",
        "-STA",
        "-File",
        str(ROOT / "desktop/Presence.ps1"),
        "-HotkeyModifiers",
        str(modifiers),
        "-HotkeyKey",
        str(key),
    ]
    if self_check:
        arguments += ["-SelfCheck", "-OutputDirectory", str(output)]
    with MobileServer(core) as server:
        bootstrap = {
            "url": server.url,
            "node": session.node_id,
            "session": session.id,
            "token": session.token,
            "orb": str(orb),
            "boundary": boundary,
            "pkcs8": base64.b64encode(
                owner_key.private_bytes(
                    serialization.Encoding.DER,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            ).decode(),
        }
        process = subprocess.Popen(
            arguments,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env={
                k: os.environ[k]
                for k in ("SystemRoot", "windir", "TEMP", "TMP", "PATH")
                if k in os.environ
            },
        )
        try:
            stdout, stderr = process.communicate(
                # Hosted cold WPF/CNG startup measured 28s; keep reference startup bounded.
                json.dumps(bootstrap) + "\n",
                timeout=60 if self_check else None,
            )
        except subprocess.TimeoutExpired:
            process.terminate()
            _, diagnostic = process.communicate(timeout=5)
            raise RuntimeError(
                "native surface timeout at reference stage: " + reference_stage(diagnostic)
            ) from None
        finally:
            if core.voice is not None:
                core.voice.stop.cancel()
                core.voice.capture.close()
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        if process.returncode:
            # PowerShell diagnostic can contain bootstrap material: suppress it entirely.
            raise RuntimeError(
                "native surface failed at reference stage: " + reference_stage(stderr)
            )
        if self_check:
            report = json.loads(stdout.strip())
            report["orb_source_sha256"] = receipt["source_sha256"]
            (output / "reference.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report))
        del stderr
    return int(process.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--hotkey-modifiers", type=int, default=3)
    parser.add_argument("--hotkey-key", type=int, default=79)
    args = parser.parse_args()
    if os.name != "nt":
        raise OSError("Windows reference required")
    with tempfile.TemporaryDirectory(prefix="oscar-desktop-reference-") as temporary:
        path = Path(temporary)
        with Harness(
            path / "core.db", path / "workspace", ROOT / "config/development-models.json"
        ) as harness:
            scopes = (
                "heartbeat",
                "desktop:connect",
                "desktop:inspect",
                "desktop:text",
                "math",
                "files:write",
                "control:inspect:" + harness.node_id,
                "control:approve:" + harness.node_id,
                "control:cancel:" + harness.node_id,
            )
            harness.grid.register(Node("desktop-reference", NodeRole.DESKTOP, scopes))
            session = harness.grid.pair("desktop-reference", scopes)
            core = Desktop(
                harness.runtime,
                PersonalPolicy(harness.store),
                {harness.node_id: (harness.dispatcher, harness.session)},
            )
            stopped = Event()

            def heartbeat() -> None:
                while not stopped.wait(5):
                    harness.grid.heartbeat(harness.session)

            thread = Thread(target=heartbeat, daemon=True)
            thread.start()
            try:
                return run_surface(
                    core,
                    session,
                    self_check=args.self_check,
                    modifiers=args.hotkey_modifiers,
                    key=args.hotkey_key,
                    boundary="REFERENCE Core · temporary state · owner acceptance NOT RUN",
                )
            finally:
                stopped.set()
                thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())
