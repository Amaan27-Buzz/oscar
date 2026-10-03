"""Real Win32 regression cases, never substituted by POSIX success."""

import ctypes
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from oscar.capabilities import Cancellation, ScopedFiles
from oscar.contracts import TaskState
from tests import test_machine


@unittest.skipUnless(sys.platform == "win32", "requires real Windows")
class WindowsWorkerTests(unittest.TestCase):
    setUp = test_machine.MachineTests.setUp
    tearDown = test_machine.MachineTests.tearDown
    task = test_machine.MachineTests.task
    run_task = test_machine.MachineTests.run_task
    result = test_machine.MachineTests.result

    def test_junction_root_parent_leaf_and_listing(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside")
        link = self.workspace / "junction"
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True
        )
        try:
            with self.assertRaises(PermissionError):
                ScopedFiles(link)
            with self.assertRaises(PermissionError):
                self.worker.files.read("junction/secret.txt")
            with self.assertRaises(PermissionError):
                self.worker.files.write(
                    "junction/secret.txt",
                    "overwrite",
                    Cancellation(self.store, self.task("file_read", {"path": "x"}).id),
                )
            self.assertNotIn("junction", self.worker.files.names(".", ""))
            self.assertEqual("outside", (outside / "secret.txt").read_text())
        finally:
            link.rmdir()  # Removes only the junction directory entry.

    def test_windows_namespace_aliases_rejected(self):
        for path in (
            "C:/outside",
            "//server/share",
            "a:stream",
            "CON",
            "nul.txt",
            "file.",
            "file ",
            "../escape",
            "a\\b",
            "a/../b",
            "LPT1",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.worker.files.read(path)

    def test_pinned_parent_cannot_be_replaced(self):
        from oscar.windows_files import WindowsScopedFiles

        parent = self.workspace / "parent"
        parent.mkdir()
        files = WindowsScopedFiles(self.workspace)
        with files.checked_directory("parent"):
            with self.assertRaises(OSError):
                parent.rename(self.workspace / "moved")

    def assert_dead(self, pid):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        for _ in range(100):
            handle = kernel.OpenProcess(0x1000, False, pid)
            if not handle:
                return
            status = ctypes.c_uint32()
            kernel.GetExitCodeProcess(handle, ctypes.byref(status))
            kernel.CloseHandle(handle)
            if status.value != 259:
                return
            sleep(0.02)
        self.fail("descendant remains alive")

    def tree_command(self, ending="import time; time.sleep(30)"):
        return [
            sys.executable,
            "-c",
            "import subprocess,sys; from pathlib import Path; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "Path('child.pid').write_text(str(p.pid)); " + ending,
        ]

    def test_cancel_kills_descendant(self):
        task = self.task("terminal_command", {"argv": self.tree_command()})
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.runtime.run, task.id, self.transports)
            for _ in range(200):
                if (self.workspace / "child.pid").exists():
                    break
                sleep(0.01)
            pid = int((self.workspace / "child.pid").read_text())
            self.runtime.cancel(task.id)
            self.assertEqual(TaskState.CANCELLED, running.result(timeout=5).state)
        self.assert_dead(pid)

    def test_timeout_kills_descendant(self):
        task = self.run_task("terminal_command", {"argv": self.tree_command(), "timeout": 1})
        self.assertEqual("command_timeout", self.result(task)["error"])
        self.assert_dead(int((self.workspace / "child.pid").read_text()))

    def test_parent_exit_kills_background_descendant(self):
        task = self.run_task("terminal_command", {"argv": self.tree_command("pass")})
        self.assertEqual(TaskState.PARTIALLY_VERIFIED, task.state)
        self.assert_dead(int((self.workspace / "child.pid").read_text()))

    def test_allowlist_rejects_shell_shim(self):
        task = self.run_task("terminal_command", {"argv": ["cmd.exe", "/c", "echo bad"]})
        self.assertEqual(TaskState.FAILED, task.state)

    def test_real_list_search_and_utf8_file(self):
        task = self.run_task(
            "file_write",
            {"path": "notes.txt", "content": "caf\u00e9 \u03bb\n"},
            {"kind": "file_exact", "path": "notes.txt", "content": "caf\u00e9 \u03bb\n"},
        )
        self.assertEqual(TaskState.VERIFIED, task.state)
        self.assertEqual("caf\u00e9 \u03bb\n".encode(), self.worker.files.read("notes.txt"))
        for kind, pattern in (("directory_list", ""), ("file_search", "notes")):
            task = self.run_task(kind, {"pattern": pattern})
            action = self.store.get("planned_action", task.id)
            self.assertEqual('["notes.txt"]', self.worker.outputs[action["id"]])

    def test_real_git_status_diff_log(self):
        from scripts.verify_worker_reference import initialize_repository

        initial = initialize_repository(self.workspace)
        task = self.run_task(
            "repository_task",
            {"path": "tracked.txt", "content": "before\n", "message": "tracked artifact"},
            {
                "kind": "git_file_exact",
                "path": "tracked.txt",
                "content": "before\n",
                "initial_head": initial,
            },
        )
        self.assertEqual(TaskState.VERIFIED, task.state)
        (self.workspace / "tracked.txt").write_bytes(b"after\n")
        for operation, expected in (
            ("status", " M tracked.txt"),
            ("diff", "+after"),
            ("log", initial),
        ):
            task = self.run_task("git_operation", {"operation": operation})
            self.assertEqual(TaskState.PARTIALLY_VERIFIED, task.state)
            action = self.store.get("planned_action", task.id)
            self.assertIn(expected, self.worker.outputs[action["id"]])

    def test_output_bound_kills_descendant(self):
        task = self.run_task("terminal_command", {"argv": self.tree_command("print('x'*100000)")})
        self.assertEqual(TaskState.FAILED, task.state)
        self.assert_dead(int((self.workspace / "child.pid").read_text()))

    def test_paused_before_launch_times_out_without_mutation(self):
        task = self.task("terminal_command", {"argv": self.tree_command(), "timeout": 0.2})
        self.worker.set_paused(task.id, True, owner_authorized=True)
        self.assertEqual(TaskState.FAILED, self.runtime.run(task.id, self.transports).state)
        self.assertEqual("command_timeout", self.result(task)["error"])
        self.assertFalse((self.workspace / "child.pid").exists())

    def test_job_assignment_failure_never_runs_child(self):
        from oscar.windows_process import WindowsJob

        job = WindowsJob()
        job.kernel.AssignProcessToJobObject = lambda *_: False
        marker = self.workspace / "should-not-exist"
        try:
            with self.assertRaises(OSError):
                job.start(
                    [
                        sys.executable,
                        "-c",
                        f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')",
                    ],
                    stdout=subprocess.PIPE,
                )
            self.assertFalse(marker.exists())
        finally:
            job.close()

    def test_running_pause_does_not_claim_process_suspension(self):
        task = self.task("terminal_command", {"argv": self.tree_command()})
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.runtime.run, task.id, self.transports)
            for _ in range(200):
                if (self.workspace / "child.pid").exists():
                    break
                sleep(0.01)
            self.worker.set_paused(task.id, True, owner_authorized=True)
            self.runtime.cancel(task.id)
            self.assertEqual(TaskState.CANCELLED, running.result(timeout=5).state)

    def test_abrupt_worker_death_after_mutation_blocks_replay(self):
        from scripts.verify_worker_reference import WorkerProcess

        worker = WorkerProcess(
            self.root / "state.sqlite", self.workspace, self.session, discover_agents=False
        )
        command = self.tree_command()
        command[-1] = command[-1].replace(
            "import subprocess,sys;",
            "import subprocess,sys; "
            "from pathlib import Path; Path('ambiguous.txt').write_text('one mutation');",
        )
        task = self.task("terminal_command", {"argv": command})
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                running = pool.submit(
                    self.runtime.run, task.id, {"machine": (worker.transport, self.session)}
                )
                for _ in range(300):
                    if (self.workspace / "child.pid").exists():
                        break
                    sleep(0.01)
                pid = int((self.workspace / "child.pid").read_text())
                worker.close()  # Abrupt OS-process exit closes the Job handle.
                self.assertEqual(TaskState.BLOCKED, running.result(timeout=8).state)
            self.assert_dead(pid)
            self.assertEqual("one mutation", (self.workspace / "ambiguous.txt").read_text())
            self.grid.disconnect("machine")
            session = self.grid.pair("machine", self.store.get("node", "machine")["scopes"])
            worker = WorkerProcess(
                self.root / "state.sqlite", self.workspace, session, discover_agents=False
            )
            self.runtime.reclaim(task.id)
            state = self.runtime.run(task.id, {"machine": (worker.transport, session)})
            self.assertEqual(TaskState.BLOCKED, state.state)
            self.assertEqual("one mutation", (self.workspace / "ambiguous.txt").read_text())
            action = self.store.get("planned_action", task.id)
            row = self.store.db.execute(
                "SELECT state FROM dedup WHERE action_id=?", (action["id"],)
            ).fetchone()
            self.assertEqual("started", row[0])
        finally:
            worker.close()
