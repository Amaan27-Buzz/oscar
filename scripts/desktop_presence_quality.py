"""Disposable, authenticated native Presence QA. Scripted executors are reference evidence only."""

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from threading import Event, Thread
from time import time

from oscar.contracts import Capability, Result, new_id
from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.mobile import MobileServer
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exe", type=Path, default=ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    )
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if not args.exe.is_file():
        raise RuntimeError("Build the isolated debug Tauri candidate first")
    with tempfile.TemporaryDirectory(
        prefix="oscar-presence-quality-", ignore_cleanup_errors=True
    ) as temp:
        path = Path(temp)
        with Harness(
            path / "core.db", path / "workspace", ROOT / "config/development-models.json"
        ) as h:
            scopes = (
                "heartbeat",
                "desktop:connect",
                "desktop:inspect",
                "desktop:text",
                "math",
                "models",
                "files:write",
                "control:inspect:" + h.node_id,
                "control:approve:" + h.node_id,
                "control:deny:" + h.node_id,
                "control:cancel:" + h.node_id,
            )
            h.grid.register(Node("quality-reference", NodeRole.DESKTOP, scopes))
            owner = h.grid.pair("quality-reference", scopes)
            core = Desktop(
                h.runtime, PersonalPolicy(h.store), {h.node_id: (h.dispatcher, h.session)}
            )
            worker_online, stop, release = Event(), Event(), Event()
            worker_online.set()
            capabilities = [Capability(**c) for c in h.store.get("node", h.node_id)["capabilities"]]
            model_mode = ["reported"]

            def reference_model(action, cancellation):
                cancellation.check()
                return Result(
                    new_id(),
                    action.id,
                    action.task_id,
                    action.correlation_id,
                    action.capability_id,
                    model_mode[0] != "failure",
                    value=("A scripted reference answer; no real model inference. " * 140)
                    if model_mode[0] == "long"
                    else "A scripted reference answer; no real model inference.",
                    error="reference executor failure" if model_mode[0] == "failure" else None,
                )

            h.dispatcher.executors["models.reason"] = reference_model

            def upkeep():
                while not stop.wait(5):
                    if worker_online.is_set():
                        h.grid.heartbeat(h.session)

            Thread(target=upkeep, daemon=True).start()
            original_request = core.request

            def observed(session, data):
                result = original_request(session, data)
                if data.get("operation") == "interact":
                    print(
                        json.dumps(
                            {
                                "core_response": {
                                    k: result.get(k)
                                    for k in ("state", "reason", "message", "task_id")
                                }
                            }
                        ),
                        flush=True,
                    )
                return result

            core.request = observed
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                debug_port = probe.getsockname()[1]
            env = {
                k: os.environ[k]
                for k in (
                    "SystemRoot",
                    "windir",
                    "SystemDrive",
                    "TEMP",
                    "TMP",
                    "PATH",
                    "USERPROFILE",
                    "LOCALAPPDATA",
                    "APPDATA",
                    "ProgramData",
                    "ProgramFiles",
                    "ProgramFiles(x86)",
                    "CommonProgramFiles",
                )
                if k in os.environ
            }
            env["WEBVIEW2_USER_DATA_FOLDER"] = str(path / "webview")
            env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={debug_port}"
            with MobileServer(core) as server:
                process = subprocess.Popen(
                    [
                        str(args.exe),
                        "--living-presence",
                        *([] if args.offline else ["--bootstrap-stdin"]),
                    ],
                    stdin=subprocess.DEVNULL if args.offline else subprocess.PIPE,
                    stdout=subprocess.DEVNULL if args.offline else subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    env=env,
                )
                worker = None
                held_kind = None
                try:
                    if not args.offline:
                        public = json.loads(process.stdout.readline())
                        assert set(public) == {"owner_public_key"}
                        core.register_owner_key(
                            owner, public["owner_public_key"], owner_authorized=True
                        )
                        process.stdin.write(
                            json.dumps(
                                {
                                    "url": server.url,
                                    "node": owner.node_id,
                                    "session": owner.id,
                                    "token": owner.token,
                                    "reference": True,
                                }
                            )
                            + "\n"
                        )
                        process.stdin.flush()
                        process.stdin.close()
                    print(
                        json.dumps(
                            {
                                "evidence": "AUTHENTICATED_DISPOSABLE_CORE"
                                if not args.offline
                                else "UNCOMMISSIONED_NATIVE",
                                "pid": process.pid,
                                "native_debug_port": debug_port,
                                "commands": (
                                    "status block restore deny allow work execute finish reported "
                                    "failure disconnect reconnect cleanup"
                                ),
                            }
                        ),
                        flush=True,
                    )
                    for line in sys.stdin:
                        command = line.strip()
                        if command == "cleanup":
                            break
                        if command == "status":
                            print(
                                json.dumps(
                                    {
                                        "process_running": process.poll() is None,
                                        "tasks": [
                                            {"id": t["id"], "state": t["state"]}
                                            for t in h.store.all("task")
                                        ],
                                        "actions": len(h.store.all("action")),
                                    }
                                ),
                                flush=True,
                            )
                        elif command == "block":
                            worker_online.clear()
                            h.grid.disconnect(h.node_id)
                            print(
                                '"REFERENCE Worker disconnected; Core remains online"', flush=True
                            )
                        elif command == "restore":
                            h.grid.advertise(h.session, capabilities)
                            worker_online.set()
                            print(
                                '"REFERENCE Worker re-advertised original capabilities"', flush=True
                            )
                        elif command in {"deny", "allow"}:
                            core.policy.save(
                                PolicyRule(
                                    "quality-math",
                                    "math.add",
                                    PolicyEffect.DENY if command == "deny" else PolicyEffect.ALLOW,
                                    "owner",
                                    time(),
                                    time(),
                                    {},
                                ),
                                owner_authorized=True,
                            )
                            print(json.dumps({"disposable_policy": command}), flush=True)
                        elif command in {"reported", "failure", "long"}:
                            model_mode[0] = command
                            print(
                                json.dumps(
                                    {
                                        "scripted_reference_model": model_mode[0],
                                        "real_inference": False,
                                    }
                                ),
                                flush=True,
                            )
                        elif command in {"work", "execute"}:
                            if worker and worker.is_alive():
                                raise RuntimeError(
                                    "Finish the active reference task before starting another"
                                )
                            task = next(
                                h.store.task(t["id"])
                                for t in reversed(h.store.all("task"))
                                if t["state"] == "planned"
                            )
                            release.clear()
                            started = Event()
                            if command == "execute":
                                # Delay the lease; the frontend still receives real Core state.
                                original_lease = h.grid.lease

                                def held_lease(
                                    *a, _started=started, _original=original_lease, **kw
                                ):
                                    _started.set()
                                    if not release.wait(60):
                                        raise RuntimeError("reference lease barrier expired")
                                    return _original(*a, **kw)

                                h.grid.lease = held_lease
                                held_kind = "lease"
                            else:
                                original_math = h.dispatcher.executors["math.add"]

                                def held_math(
                                    action, cancellation, _started=started, _original=original_math
                                ):
                                    _started.set()
                                    if not release.wait(60):
                                        raise RuntimeError("reference executor barrier expired")
                                    return _original(action, cancellation)

                                h.dispatcher.executors["math.add"] = held_math
                                held_kind = "math"
                            worker = Thread(
                                target=h.runtime.run, args=(task.id, core.targets), daemon=True
                            )
                            worker.start()
                            assert started.wait(10)
                            print(
                                json.dumps(
                                    {
                                        "reference_programmatic_progression": task.id,
                                        "actual_core_state": h.store.task(task.id).state,
                                        "gui_owner_approval": False,
                                    }
                                ),
                                flush=True,
                            )
                        elif command == "finish":
                            release.set()
                            if worker:
                                worker.join(10)
                            if held_kind == "lease":
                                h.grid.lease = original_lease
                            elif held_kind == "math":
                                h.dispatcher.executors["math.add"] = original_math
                            held_kind = None
                            print(
                                json.dumps(
                                    {
                                        "actual_tasks": [
                                            {"state": t["state"]} for t in h.store.all("task")
                                        ]
                                    }
                                ),
                                flush=True,
                            )
                        elif command == "disconnect":
                            server.server.shutdown()
                            server.thread.join(3)
                            print('"Disposable Core server stopped"', flush=True)
                        elif command == "reconnect":
                            server.thread = Thread(target=server.server.serve_forever, daemon=True)
                            server.thread.start()
                            print('"Disposable Core server restored"', flush=True)
                        elif command:
                            raise ValueError("Unknown bounded fixture command")
                finally:
                    release.set()
                    stop.set()
                    if worker:
                        worker.join(10)
                    if process.poll() is None:
                        process.terminate()
                        process.wait(10)
                    print('"Owned fixture cleanup; not evidence of UI Quit"', flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
