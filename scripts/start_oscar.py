"""Start the everyday Desktop with OSCAR's persistent, authenticated local Core.

Never reads project credential files. Provider setup uses the existing OS Vault.
"""

import argparse
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path
from queue import Queue
from threading import Thread

from oscar.cloud_state import DataDirectoryLock
from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.mobile import MobileServer
from oscar.models import ModelRequest, RoutingPolicy
from oscar.policy import PersonalPolicy
from oscar.storage import Store

ROOT = Path(__file__).resolve().parents[1]


def renew_local_execution(state: Path) -> bool:
    """A trusted local restart may renew expiry, but never undo revocation."""
    if not state.is_file():
        return False
    store = Store(state)
    try:
        try:
            node = store.get("node", "oscar-local-core")
            binding = store.get("core_execution", "oscar-local-core")
            session = store.get("session", binding["session_id"])
        except KeyError:
            return False
        return bool(
            not node["revoked"]
            and not session["revoked"]
            and session.get("internal")
            and session["node_id"] == "oscar-local-core"
        )
    finally:
        store.close()


def desktop_session(h: Harness):
    """Local trusted enrollment; each launch replaces the old surface session."""
    scopes = (
        "heartbeat",
        "desktop:connect",
        "desktop:inspect",
        "desktop:text",
        "desktop:conversation:read",
        "desktop:conversation:retain",
        "models",
        "math",
        "memory:read",
        "files:write",
        *(f"control:{op}:{h.node_id}" for op in ("inspect", "approve", "cancel")),
    )
    node = "oscar-local-desktop"
    try:
        existing = h.store.get("node", node)
    except KeyError:
        h.grid.register(Node(node, NodeRole.DESKTOP, scopes))
    else:
        if existing["revoked"] or set(existing["scopes"]) != set(scopes):
            raise PermissionError("Desktop enrollment changed; inspect before restarting")
    with h.store.transaction():
        for previous in h.store.all("session"):
            if previous["node_id"] == node and not previous["revoked"]:
                h.store.put("session", previous["id"], {**previous, "revoked": True})
        return h.grid.pair(node, scopes, ttl=86400)


def run_desktop(core: Desktop, session, executable: Path) -> None:
    # Credentials travel only over the anonymous stdin pipe, never arguments/files.
    with MobileServer(core) as server:
        process = subprocess.Popen(
            [str(executable), "--bootstrap-stdin", "--interaction"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines: Queue[str] = Queue()
        assert process.stdout is not None and process.stdin is not None

        def collect() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                lines.put(line)
            lines.put("")

        reader = Thread(target=collect, daemon=True)
        reader.start()
        try:
            public = json.loads(lines.get(timeout=90))
            if set(public) != {"owner_public_key"}:
                raise RuntimeError("Desktop enrollment protocol rejected")
            core.register_owner_key(session, public["owner_public_key"], owner_authorized=True)
            process.stdin.write(
                json.dumps(
                    {
                        "url": server.url,
                        "node": session.node_id,
                        "session": session.id,
                        "token": session.token,
                        "reference": False,
                        "reference_target": None,
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            process.stdin.close()
            print(
                "OSCAR Core online. Conversation history is retained locally. "
                "Quit from the tray to stop."
            )
            process.wait()
            if process.returncode:
                raise RuntimeError("Desktop exited unsuccessfully")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--model", help="Override the saved local model for this launch")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check live local model routing without opening Desktop",
    )
    args = parser.parse_args()
    data = args.data_dir or Path(os.environ["LOCALAPPDATA"]) / "DawnlightLabs/OSCAR"
    executable = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    if not args.check and not executable.is_file():
        parser.error("Build Desktop first: python -m scripts.build_desktop")
    data.mkdir(parents=True, exist_ok=True)
    template = ModelRequest.from_config(
        {
            "mode": "local",
            "pinned_provider": "ollama-local",
            "pinned_model": args.model or "qwen3.5:9b",
            "max_output_tokens": 1024,
            "ollama_think": False,
        }
    )
    with (
        DataDirectoryLock(data),
        Harness(
            data / "core.sqlite",
            data / "workspace",
            ROOT / "config/development-models.json",
            template,
            node_id="oscar-local-core",
            model_timeout_seconds=120,
            credential_environ={},
            execution_enrollment_authorized=renew_local_execution(data / "core.sqlite"),
        ) as h,
    ):
        try:
            saved = h.store.get("desktop_model", "selection")
        except KeyError:
            pass
        else:
            if args.model:
                saved = {
                    "configuration": {
                        **saved["configuration"],
                        "pinned_model": args.model,
                    }
                }
            template = ModelRequest.from_config(saved["configuration"])
            h.dispatcher.executors["models.reason"].template = template
        h.router.refresh(template, RoutingPolicy(timeout_seconds=120))
        if not h.router.rank(template):
            raise RuntimeError("Selected local model unavailable. Start Ollama or choose --model.")
        if args.check:
            result = h.router.execute(
                replace(template, prompt="Reply with a short greeting.", max_output_tokens=64),
                RoutingPolicy(timeout_seconds=120),
            )
            if not result.response.text.strip():
                raise RuntimeError("Local model returned no answer")
            print("Real local inference completed through OSCAR Model Router.")
            return 0
        session = desktop_session(h)
        core = Desktop(h.runtime, PersonalPolicy(h.store), {h.node_id: (h.dispatcher, h.session)})
        run_desktop(core, session, executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
