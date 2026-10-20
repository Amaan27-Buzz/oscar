"""Real UIA against an exclusively owned synthetic window, never owner applications."""

import os
import subprocess
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep, time

from oscar.contracts import TaskState
from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import InteractiveWorker
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier
from oscar.storage import Store
from oscar.transport import Dispatcher
from oscar.windows_desktop import InstalledApp, WindowsDesktop


@unittest.skipUnless(os.name == "nt", "actual Windows synthetic app acceptance")
class WindowsAppWorkflowTests(unittest.TestCase):
    def test_real_form_task_and_independent_readback(self):
        from oscar.runtime import Runtime

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            shell = str(
                Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            )
            fixture = Path(__file__).with_name("fixtures") / "windows_form.ps1"
            process = subprocess.Popen(
                [shell, "-NoProfile", "-STA", "-File", str(fixture), "-Root", str(root)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            try:
                deadline = monotonic() + 20
                while not (root / "window.txt").exists() and monotonic() < deadline:
                    if process.poll() is not None:
                        self.fail(f"synthetic app exited: {process.communicate()[1]!r}")
                    sleep(0.1)
                handle = int((root / "window.txt").read_text())
                self.assertEqual("False", (root / "keyboard-focus.txt").read_text())
                with closing(Store(root / "runtime.sqlite")) as store:
                    grid = Grid(store)
                    grants = (
                        "heartbeat",
                        "advertise",
                        "execute",
                        "cancel",
                        "machine:host",
                        "desktop:control",
                        "files:read",
                        "files:write",
                    )
                    grid.register(Node("synthetic-windows", NodeRole.DESKTOP, grants))
                    session = grid.pair("synthetic-windows", grants)
                    worker = InteractiveWorker(
                        store, grid, session, MachineScope(root, True, (shell,))
                    )
                    app = InstalledApp(
                        "synthetic-form",
                        "Synthetic form",
                        None,
                        shell,
                        "native_exe",
                        "run-owned-fixture",
                        time(),
                        True,
                        ("observe_window",),
                    )
                    worker.desktop = WindowsDesktop(
                        permissions=frozenset(grants), allowed_apps=(app,), workspace=root
                    )
                    worker.desktop.bind(handle, process.pid, app.id)
                    grid.advertise(session, worker.capabilities())
                    runtime = Runtime(store, grid, MachineVerifier(worker.files))
                    transports = {
                        session.node_id: (
                            Dispatcher(store, grid, session.node_id, worker.executors()),
                            session,
                        )
                    }
                    target = {"handle": handle, "pid": process.pid}
                    tree = worker.desktop.observe({"operation": "tree", **target})
                    self.assertTrue(any(e["name"] == "Synthetic input" for e in tree), tree)
                    editor = next(e for e in tree if e["name"] == "Synthetic input")
                    button = next(e for e in tree if e["name"] == "Submit synthetic form")
                    text = "OSCAR synthetic cross-app proof"

                    def execute(operation, element, **extra):
                        task = runtime.create(
                            Intent(
                                "Submit the synthetic form",
                                "capability",
                                capability_kind="desktop_control",
                                parameters={
                                    "request": {
                                        "operation": operation,
                                        **target,
                                        "runtime_id": element["runtime_id"],
                                        **extra,
                                    }
                                },
                            )
                        )
                        return runtime.run(task.id, transports)

                    self.assertEqual("", editor["text"])
                    entered = execute("set_text_checked", editor, text=text, expected_text="")
                    self.assertEqual(TaskState.PARTIALLY_VERIFIED, entered.state)
                    observed = worker.desktop.observe(
                        {"operation": "read", **target, "runtime_id": editor["runtime_id"]}
                    )
                    self.assertEqual(text, observed["text"])
                    completed = execute("invoke", button)
                    self.assertEqual(TaskState.PARTIALLY_VERIFIED, completed.state)
                    deadline = monotonic() + 5
                    while monotonic() < deadline:
                        if (root / "submitted.txt").exists() and (
                            root / "submitted.txt"
                        ).read_text() == text:
                            break
                        sleep(0.05)
                    self.assertEqual(text, (root / "submitted.txt").read_text())
                    after = worker.desktop.observe({"operation": "tree", **target})
                    self.assertTrue(any(e["name"] == "Submitted: " + text for e in after))
                    with self.assertRaises(PermissionError):
                        worker.desktop.command(
                            {"operation": "tree", **target, "pid": process.pid + 1}
                        )
                    worker.desktop.observe({"operation": "close", **target})
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
                if process.stderr:
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()
