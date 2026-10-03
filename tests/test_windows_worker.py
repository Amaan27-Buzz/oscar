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
