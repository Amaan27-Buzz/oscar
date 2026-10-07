"""Harmless real WPF/UIA fixture through the existing Windows Worker and Core ledger.

No owner application, clipboard, microphone, screenshot or private file is accessed.
"""

import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path
from queue import Queue
from threading import Thread
from time import monotonic, sleep
from typing import Any

from oscar.desktop import Desktop
from oscar.desktop_context import WindowsContext
from oscar.desktop_verify import DesktopVerifier, compare_text
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.interactive_worker import InteractiveWorker
from oscar.machine import MachineScope
from oscar.policy import PersonalPolicy
from oscar.transport import Dispatcher
from oscar.windows_desktop import InstalledApp, WindowsDesktop

FIXTURE = r"""
param([string]$StopFile)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName PresentationFramework,UIAutomationClient,UIAutomationTypes
$w=[Windows.Window]::new();$w.Title='OSCAR disposable UIA reference';$w.Width=420;$w.Height=170
$field=[Windows.Controls.TextBox]::new();$field.Text='Desktop reference before'
$field.Margin=[Windows.Thickness]::new(20);$w.Content=$field
[Windows.Automation.AutomationProperties]::SetAutomationId($field,'oscar-fixture-text')
$w.Add_ContentRendered({
 $w.Activate()|Out-Null;$field.Focus()|Out-Null
 $handle=[Windows.Interop.WindowInteropHelper]::new($w).Handle
 [Console]::WriteLine((@{handle=$handle.ToInt64();pid=$PID}|ConvertTo-Json -Compress))
})
$timer=[Windows.Threading.DispatcherTimer]::new();$timer.Interval=[TimeSpan]::FromMilliseconds(100)
$timer.Add_Tick({if (Test-Path -LiteralPath $StopFile) {$w.Close()}});$timer.Start()
$w.ShowDialog()|Out-Null;$timer.Stop()
"""


def fixture_tree(desktop: WindowsDesktop, identity: dict[str, Any]) -> Any:
    """Wait for cold accessibility startup before any action. Only read operations retry."""
    deadline = monotonic() + 60
    while monotonic() < deadline:
        try:
            return desktop.observe(
                {"operation": "tree", **identity}, timeout=min(15, deadline - monotonic())
            )
        except (OSError, subprocess.SubprocessError):
            sleep(0.1)
    raise RuntimeError("reference accessibility unavailable before action; nothing applied")


def main() -> int:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    if os.name != "nt":
        raise OSError("Windows reference required")
    root = Path(__file__).resolve().parents[1]
    output = root / ".oscar/desktop"
    output.mkdir(parents=True, exist_ok=True)
    shell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    with tempfile.TemporaryDirectory(prefix="desktop-uia-reference-") as directory:
        temporary = Path(directory)
        script = temporary / "fixture.ps1"
        script.write_text(FIXTURE)
        stop = temporary / "stop"
        process = subprocess.Popen(
            [str(shell), "-NoProfile", "-STA", "-File", str(script), "-StopFile", str(stop)],
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
            assert process.stdout
            # The fixture has no secrets/content in its readiness line.
            readiness: Queue[str] = Queue(maxsize=1)
            stream = process.stdout
            reader = Thread(target=lambda: readiness.put(stream.readline()), daemon=True)
            reader.start()
            identity = json.loads(readiness.get(timeout=20))
            with Harness(
                temporary / "core.db",
                temporary / "workspace",
                root / "config/development-models.json",
            ) as harness:
                scopes = (
                    "heartbeat",
                    "advertise",
                    "execute",
                    "cancel",
                    "pause",
                    "files:read",
                    "files:write",
                    "machine:host",
                    "desktop:control",
                )
                harness.grid.register(Node("reference-uia-worker", NodeRole.DESKTOP, scopes))
                worker_session = harness.grid.pair("reference-uia-worker", scopes)
                policy = PersonalPolicy(harness.store)
                worker = InteractiveWorker(
                    harness.store,
                    harness.grid,
                    worker_session,
                    MachineScope(temporary / "workspace", True, (str(shell),)),
                    policy,
                    desktop=True,
                )
                app = InstalledApp(
                    "wpf-reference",
                    "WPF fixture",
                    "OSCAR",
                    str(shell),
                    "native_exe",
                    "explicit-disposable-reference",
                    harness.grid.clock(),
                    True,
                    ("observe_window",),
                )
                worker.desktop.apps[app.id] = app
                worker.desktop.bind(identity["handle"], identity["pid"], app.id)
                caps = worker.capabilities()
                harness.grid.advertise(worker_session, caps)
                dispatcher = Dispatcher(
                    harness.store,
                    harness.grid,
                    worker_session.node_id,
                    {c.id: worker.execute for c in caps},
                )
                target = worker_session.node_id
                owner_scopes = (
                    "heartbeat",
                    "desktop:connect",
                    "desktop:inspect",
                    "desktop:text",
                    "desktop:perceive:focused",
                    "machine:host",
                    "desktop:control",
                    "control:inspect:" + target,
                    "control:approve:" + target,
                    "control:cancel:" + target,
                )
                harness.grid.register(
                    Node("reference-desktop-owner", NodeRole.DESKTOP, owner_scopes)
                )
                owner = harness.grid.pair("reference-desktop-owner", owner_scopes)
                harness.runtime.verifier = DesktopVerifier(harness.runtime.verifier, worker.desktop)
                core = Desktop(
                    harness.runtime,
                    policy,
                    {target: (dispatcher, worker_session)},
                    context=WindowsContext(worker.desktop),
                )
                key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                public = key.public_key().public_bytes(
                    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
                )
                core.register_owner_key(
                    owner, base64.b64encode(public).decode(), owner_authorized=True
                )

                def call(op: str, payload: dict[str, Any]) -> dict[str, Any]:
                    from oscar.contracts import new_id

                    return core.request(
                        owner,
                        {"version": 1, "operation": op, "request_id": new_id(), "payload": payload},
                    )

                tree = fixture_tree(worker.desktop, identity)
                harness.grid.heartbeat(worker_session)
                field = next(row for row in tree if row["automation_id"] == "oscar-fixture-text")
                captured = call(
                    "capture",
                    {
                        "source": "focused",
                        "target": {**identity, "runtime_id": field["runtime_id"]},
                    },
                )
                if captured["text"] != "Desktop reference before":
                    raise RuntimeError("fixture context identity/readback mismatch")
                preview = call(
                    "interact",
                    {
                        "mode": "Dictate",
                        "text": " plus dictated text",
                        "context_id": captured["id"],
                    },
                )
                proposed = call(
                    "apply", {"preview_id": preview["preview_id"], "destination": "focused"}
                )
                challenge = call(
                    "challenge", {"operation": "approve", "task_id": proposed["task_id"]}
                )
                signature = key.sign(
                    base64.b64decode(challenge["signing_payload"]),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                    hashes.SHA256(),
                )
                completed = call(
                    "complete",
                    {
                        "challenge_id": challenge["challenge_id"],
                        "signature": base64.b64encode(signature).decode(),
                    },
                )
                expected = "Desktop reference before plus dictated text"
                if completed["state"] != "verified":
                    raise RuntimeError("real Worker/UIA text task failed independent verification")
                # Separate observer, no Worker result consulted.
                tree = worker.desktop.observe({"operation": "tree", **identity})
                field = next(row for row in tree if row["automation_id"] == "oscar-fixture-text")
                if field["text"] != expected:
                    raise RuntimeError("independent UIA field differs")
                # The fixed bridge/anonymous pipe must handle maximum Unicode text too.
                long_text = "\u03bb" * 8192
                field_request = {
                    "handle": identity["handle"],
                    "pid": identity["pid"],
                    "runtime_id": field["runtime_id"],
                }
                worker.desktop.observe(
                    {
                        "operation": "set_text_checked",
                        **field_request,
                        "expected_text": expected,
                        "text": long_text,
                    }
                )
                if (
                    compare_text(worker.desktop, {"operation": "read", **field_request}, long_text)
                    is not True
                ):
                    raise RuntimeError("maximum Unicode pipe/readback failed")
                try:
                    worker.desktop.observe(
                        {
                            "operation": "set_text_checked",
                            **field_request,
                            "expected_text": "stale",
                            "text": "must not apply",
                        }
                    )
                except OSError:
                    pass
                else:
                    raise RuntimeError("stale expected-value fence did not reject")
                if (
                    worker.desktop.observe({"operation": "read", **field_request})["text"]
                    != long_text
                ):
                    raise RuntimeError("stale write changed fixture text")
                dump = "\n".join(harness.store.db.iterdump())
                if expected in dump or "Desktop reference before" in dump:
                    raise RuntimeError("private fixture content entered durable state")
                report = {
                    "evidence": "REFERENCE_WINDOWS_WPF_UIA_WORKER",
                    "state": "VERIFIED",
                    "context": "fresh registered focused ValuePattern",
                    "application": "signed preview -> expected-value fence -> ValuePattern",
                    "verification": "independent UIA exact readback",
                    "pipe_boundary": "8192 Unicode characters roundtrip VERIFIED",
                    "stale_write": "rejected; destination unchanged VERIFIED",
                    "retention": "database content absence VERIFIED",
                    "owner_acceptance": "NOT_RUN",
                    "microphone": "NOT_RUN",
                    "evidence_ids": completed["evidence_ids"],
                }
                (output / "windows-reference.json").write_text(json.dumps(report, indent=2) + "\n")
                print(json.dumps(report))
        finally:
            stop.touch()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()  # This fixture process only.
                process.wait(timeout=5)
            if process.stdout:
                process.stdout.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
