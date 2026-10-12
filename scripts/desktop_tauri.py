"""Actual Tauri desktop connected to a disposable Core. Native CNG owns its signing key.

No owner application, clipboard, microphone or provider credential is used.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from queue import Queue
from threading import Event, Thread
from typing import Any

from oscar.contracts import Result, new_id
from oscar.desktop import Desktop
from oscar.desktop_context import WindowsContext
from oscar.desktop_verify import DesktopVerifier
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.interactive_worker import InteractiveWorker
from oscar.machine import MachineScope, MachineVerifier
from oscar.mobile import MobileServer
from oscar.policy import PersonalPolicy
from oscar.transport import Dispatcher
from oscar.windows_desktop import InstalledApp
from scripts.desktop_windows_reference import FIXTURE, fixture_tree

ROOT = Path(__file__).resolve().parents[1]


def run_surface(
    core: Desktop, session: Any, *, check: bool, reference_target: dict[str, Any] | None = None
) -> dict[str, Any]:
    executable = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    if not executable.is_file():
        raise RuntimeError("build the Windows Tauri debug executable first")
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
    with MobileServer(core) as server:
        process = subprocess.Popen(
            [
                str(executable),
                "--isolated-preferences",
                "--bootstrap-stdin",
                *(["--reference-check"] if check else ["--interaction"]),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        lines: Queue[str] = Queue()
        assert process.stdout and process.stdin
        stream = process.stdout

        def collect() -> None:
            for line in iter(stream.readline, ""):
                lines.put(line)
            lines.put('{"native_process_ended":true}')

        reader = Thread(target=collect, daemon=True)
        reader.start()
        try:
            public = json.loads(lines.get(timeout=90))
            if set(public) != {"owner_public_key"}:
                raise RuntimeError("native public-key enrollment protocol rejected")
            core.register_owner_key(session, public["owner_public_key"], owner_authorized=True)
            bootstrap = {
                "url": server.url,
                "node": session.node_id,
                "session": session.id,
                "token": session.token,
                "reference": True,
                "reference_target": reference_target,
            }
            process.stdin.write(json.dumps(bootstrap) + "\n")
            process.stdin.flush()
            process.stdin.close()
            report = json.loads(lines.get(timeout=180)) if check else {}
            if report.get("native_process_ended"):
                raise RuntimeError("native process ended before reference verification")
            process.wait(timeout=30 if check else None)
            if process.returncode:
                raise RuntimeError("native reference failed; no owner acceptance claimed")
            if check and report.get("evidence") != "REFERENCE_TAURI_WINDOWS_CORE":
                raise RuntimeError("native reference receipt missing")
            return report
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            if core.voice is not None:
                core.voice.stop.cancel()
                core.voice.capture.close()
            stream.close()
            if process.stderr:
                # Only fixture diagnostics, never credential/bootstrap values.
                diagnostic = process.stderr.read()
                if process.returncode:
                    known = [
                        line
                        for line in diagnostic.splitlines()
                        if line.startswith("reference failed:")
                    ]
                    if known:
                        print(known[-1][:300])
                process.stderr.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise OSError("Windows product/reference required")
    output = ROOT / ".oscar/desktop"
    output.mkdir(parents=True, exist_ok=True)
    shell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    with tempfile.TemporaryDirectory(prefix="oscar-tauri-reference-") as directory:
        temporary = Path(directory)
        fixture = temporary / "field.ps1"
        fixture.write_text(FIXTURE, encoding="utf-8")
        stop_file = temporary / "stop"
        field_process = subprocess.Popen(
            [str(shell), "-NoProfile", "-STA", "-File", str(fixture), "-StopFile", str(stop_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env={
                k: os.environ[k]
                for k in ("SystemRoot", "windir", "TEMP", "TMP", "PATH")
                if k in os.environ
            },
        )
        try:
            assert field_process.stdout
            readiness: Queue[str] = Queue(maxsize=1)
            stream = field_process.stdout
            Thread(target=lambda: readiness.put(stream.readline()), daemon=True).start()
            identity = json.loads(readiness.get(timeout=60))
            with Harness(
                temporary / "core.db",
                temporary / "workspace",
                ROOT / "config/development-models.json",
            ) as h:
                worker_scopes = (
                    "heartbeat",
                    "advertise",
                    "execute",
                    "cancel",
                    "pause",
                    "files:read",
                    "files:write",
                    "machine:host",
                    "desktop:control",
                    "browser:control",
                )
                h.grid.register(Node("tauri-reference-worker", NodeRole.DESKTOP, worker_scopes))
                worker_session = h.grid.pair("tauri-reference-worker", worker_scopes)
                executables_list = [str(shell), sys.executable]
                git = shutil.which("git")
                if git is not None:
                    executables_list.append(git)
                executables = tuple(dict.fromkeys(executables_list))
                policy = PersonalPolicy(h.store)
                worker = InteractiveWorker(
                    h.store,
                    h.grid,
                    worker_session,
                    MachineScope(temporary / "workspace", True, executables),
                    policy,
                    desktop=True,
                    browser=True,
                )
                app = InstalledApp(
                    "tauri-field-fixture",
                    "Registered reference field",
                    "OSCAR",
                    str(shell),
                    "native_exe",
                    "disposable-reference",
                    h.grid.clock(),
                    True,
                    ("observe_window",),
                )
                worker.desktop.apps[app.id] = app
                worker.desktop.bind(identity["handle"], identity["pid"], app.id)
                tree = fixture_tree(worker.desktop, identity)
                field = next(e for e in tree if e["automation_id"] == "oscar-fixture-text")
                target = {**identity, "runtime_id": field["runtime_id"]}
                caps = worker.capabilities()
                h.grid.advertise(worker_session, caps)
                dispatcher = Dispatcher(
                    h.store, h.grid, worker_session.node_id, {c.id: worker.execute for c in caps}
                )
                h.runtime.verifier = DesktopVerifier(MachineVerifier(worker.files), worker.desktop)

                def transform(action: Any, cancellation: Any) -> Result:
                    cancellation.check()
                    return Result(
                        new_id(),
                        action.id,
                        action.task_id,
                        action.correlation_id,
                        action.capability_id,
                        True,
                        value="Reference transformed text",
                    )

                h.dispatcher.executors["models.reason"] = (
                    transform  # SIMULATED transformation, no inference claim.
                )
                targets = {
                    h.node_id: (h.dispatcher, h.session),
                    worker_session.node_id: (dispatcher, worker_session),
                }
                scopes = tuple(
                    dict.fromkeys(
                        [
                            "heartbeat",
                            "desktop:connect",
                            "desktop:inspect",
                            "desktop:text",
                            "desktop:perceive:foreground",
                            "desktop:perceive:focused",
                            "desktop:perceive:selection",
                            "math",
                            "models",
                            "files:read",
                            "files:write",
                            "machine:host",
                            "desktop:control",
                            "browser:control",
                            *[
                                f"control:{op}:{t}"
                                for t in targets
                                for op in ("inspect", "approve", "cancel")
                            ],
                        ]
                    )
                )
                h.grid.register(Node("tauri-reference-owner", NodeRole.DESKTOP, scopes))
                owner = h.grid.pair("tauri-reference-owner", scopes)
                core = Desktop(
                    h.runtime,
                    policy,
                    targets,
                    context=WindowsContext(worker.desktop),
                    native_catalogs={
                        worker_session.node_id: {
                            "executables": executables,
                            "applications": worker.desktop.catalog(),
                        }
                    },
                    worker_outputs={worker_session.node_id: worker.outputs},
                )
                stopped = Event()

                def heartbeat() -> None:
                    while not stopped.wait(5):
                        h.grid.heartbeat(h.session)
                        h.grid.heartbeat(worker_session)

                thread = Thread(target=heartbeat, daemon=True)
                thread.start()
                try:
                    report = run_surface(
                        core, owner, check=args.self_check, reference_target=target
                    )
                    if args.self_check:
                        resumed = run_surface(core, owner, check=True, reference_target=target)
                        if resumed.get("continued_tasks_seen", 0) < 1:
                            raise RuntimeError("native restart lost shared task continuity")
                        report["native_restart"] = "VERIFIED / shared Core tasks preserved"
                        report["continued_tasks_seen"] = resumed["continued_tasks_seen"]
                        (output / "tauri-reference.json").write_text(
                            json.dumps(report, indent=2) + "\n"
                        )
                        dump = "\n".join(h.store.db.iterdump())
                        if (
                            "Reference transformed text" in dump
                            or "Desktop reference before" in dump
                        ):
                            raise RuntimeError("private reference content entered durable state")
                        print(json.dumps(report))
                finally:
                    stopped.set()
                    thread.join(timeout=3)
        finally:
            stop_file.touch()
            try:
                field_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                field_process.terminate()
                field_process.wait(timeout=5)
            if field_process.stdout:
                field_process.stdout.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
