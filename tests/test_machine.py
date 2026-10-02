"""Real POSIX filesystem/Git/process tests; unavailable physical machines stay unverified."""

import json
import os
import shutil
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from unittest.mock import patch

from oscar.contracts import TaskState
from oscar.grid import Grid, Node, NodeRole
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier, MachineWorker
from oscar.runtime import Runtime
from oscar.storage import StateConflict, Store
from oscar.transport import Dispatcher


class MachineTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "repo"
        self.workspace.mkdir()
        self.store = Store(self.root / "state.sqlite")
        self.grid = Grid(self.store)
        scopes = (
            "heartbeat",
            "advertise",
            "execute",
            "cancel",
            "files:read",
            "files:write",
            "machine:host",
        )
        self.grid.register(Node("machine", NodeRole.DESKTOP, scopes))
        self.session = self.grid.pair("machine", scopes)
        self.git = shutil.which("git")
        self.worker = MachineWorker(
            self.store,
            self.grid,
            self.session,
            MachineScope(self.workspace, True, (self.git, sys.executable)),
        )
        self.grid.advertise(self.session, self.worker.capabilities())
        self.runtime = Runtime(self.store, self.grid, MachineVerifier(self.worker.files))
        self.dispatcher = Dispatcher(self.store, self.grid, "machine", self.worker.executors())
        self.transports = {"machine": (self.dispatcher, self.session)}

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def task(self, kind, parameters, criterion=None):
        return self.runtime.create(
            Intent(
                "structured machine objective",
                "capability",
                capability_kind=kind,
                parameters=parameters,
                criterion=criterion,
            )
        )

    def run_task(self, kind, parameters, criterion=None):
        task = self.task(kind, parameters, criterion)
        return self.runtime.run(task.id, self.transports)

    def result(self, task):
        return next(r for r in self.store.all("result") if r["task_id"] == task.id)

    def test_real_exact_file_and_scoped_read(self):
        task = self.runtime.create(Intent("write", "file_write", "proof.txt", "exact\n"))
        self.assertEqual(TaskState.VERIFIED, self.runtime.run(task.id, self.transports).state)
        read = self.run_task("file_read", {"path": "proof.txt"})
        self.assertEqual(TaskState.PARTIALLY_VERIFIED, read.state)
        self.assertEqual(6, json.loads(self.result(read)["value"])["bytes"])

    def test_real_repository_commit_and_verification(self):
        subprocess.run([self.git, "init", "-q"], cwd=self.workspace, check=True)
        subprocess.run(
            [
                self.git,
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=f@example.invalid",
                "commit",
                "--allow-empty",
                "-qm",
                "initial",
            ],
            cwd=self.workspace,
            check=True,
        )
        initial = subprocess.check_output(
            [self.git, "rev-parse", "HEAD"], cwd=self.workspace, text=True
        ).strip()
        task = self.run_task(
            "repository_task",
            {"path": "result.txt", "content": "verified\n", "message": "reference work"},
            {
                "kind": "git_file_exact",
                "path": "result.txt",
                "content": "verified\n",
                "initial_head": initial,
            },
        )
        self.assertEqual(TaskState.VERIFIED, task.state)
        self.assertEqual("verified\n", (self.workspace / "result.txt").read_text())
        self.assertTrue(self.store.get("worker_checkpoint", task.id))
        self.assertTrue(any(e["event"] == "progress_observed" for e in self.store.ledger(task.id)))

    def test_terminal_environment_is_filtered(self):
        with patch.dict(os.environ, {"OSCAR_TEST_SECRET_KEY": "synthetic-private-secret"}):
            task = self.run_task(
                "terminal_command",
                {
                    "argv": [
                        sys.executable,
                        "-c",
                        "import os; assert 'OSCAR_TEST_SECRET_KEY' not in os.environ; "
                        "print('filtered')",
                    ]
                },
            )
        self.assertTrue(self.result(task)["success"])
        self.assertNotIn("filtered", self.result(task)["value"])

    def test_path_traversal_symlink_and_cwd_rejection(self):
        (self.workspace / "link").symlink_to(self.root, target_is_directory=True)
        for path in ("../escape", "link/escape", "/tmp/escape", "a\\b"):
            task = self.run_task("file_read", {"path": path})
            self.assertEqual(TaskState.FAILED, task.state)
        task = self.run_task(
            "terminal_command", {"argv": [sys.executable, "-c", "pass"], "cwd": "link"}
        )
        self.assertEqual(TaskState.FAILED, task.state)

    def test_timeout_and_output_bounds(self):
        task = self.run_task(
            "terminal_command",
            {"argv": [sys.executable, "-c", "import time; time.sleep(5)"], "timeout": 0.1},
        )
        self.assertEqual("command_timeout", self.result(task)["error"])
        task = self.run_task(
            "terminal_command", {"argv": [sys.executable, "-c", "print('x' * 100000)"]}
        )
        self.assertEqual(TaskState.FAILED, task.state)

    def test_no_host_or_unavailable_agent_advertisement(self):
        worker = MachineWorker(self.store, self.grid, self.session, MachineScope(self.workspace))
        names = [c.id for c in worker.capabilities()]
        self.assertNotIn("machine.command", names)
        self.assertNotIn("machine.git", names)
        self.assertFalse(any(c.startswith("machine.agent.") for c in names))
        self.assertFalse(any(c.startswith("machine.wake") for c in names))
        with patch("oscar.machine.shutil.which", return_value=None):
            worker = MachineWorker(
                self.store,
                self.grid,
                self.session,
                MachineScope(self.workspace, True, (sys.executable,)),
            )
        self.assertEqual({}, worker.agents)

    def test_cancellation_terminates_process(self):
        task = self.task(
            "terminal_command", {"argv": [sys.executable, "-c", "import time; time.sleep(30)"]}
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.runtime.run, task.id, self.transports)
            for _ in range(100):
                if self.store.all("worker_checkpoint"):
                    break
                sleep(0.01)
            self.runtime.cancel(task.id)
            self.assertEqual(TaskState.CANCELLED, running.result(timeout=3).state)

    def test_pause_and_resume(self):
        task = self.task(
            "terminal_command", {"argv": [sys.executable, "-c", "import time; time.sleep(0.4)"]}
        )
        self.worker.set_paused(task.id, True, owner_authorized=True)
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.runtime.run, task.id, self.transports)
            sleep(0.15)
            self.assertFalse(running.done())
            self.worker.set_paused(task.id, False, owner_authorized=True)
            self.assertEqual(TaskState.PARTIALLY_VERIFIED, running.result(timeout=3).state)
        with self.assertRaises(PermissionError):
            self.worker.set_paused(task.id, True, owner_authorized=False)

    def test_lease_expiry_and_stale_renewal(self):
        task = self.task("terminal_command", {"argv": [sys.executable, "-c", "pass"]})
        self.store.transition(task.id, TaskState.EXECUTING)
        lease = self.grid.lease(task.id, "machine", ttl=0.01)
        sleep(0.03)
        self.assertIn(task.id, self.grid.reap())
        self.assertEqual(TaskState.BLOCKED, self.store.task(task.id).state)
        with self.assertRaises(StateConflict):
            self.grid.renew(lease, self.session)
        self.assertEqual(TaskState.PLANNED, self.runtime.reclaim(task.id).state)

    def test_wrong_executable_and_timeout_contract(self):
        task = self.run_task("terminal_command", {"argv": ["/usr/bin/unknown", "--help"]})
        self.assertEqual(TaskState.FAILED, task.state)
        for timeout in (float("nan"), float("inf"), -1):
            with self.assertRaises(ValueError):
                MachineScope(self.workspace, max_timeout=timeout)

    def test_runtime_rejects_secret_before_durable_plan(self):
        with patch.dict(os.environ, {"OSCAR_FIXTURE_API_KEY": "synthetic-runtime-secret"}):
            with self.assertRaises(ValueError):
                self.runtime.create(
                    Intent("write", "file_write", "key.txt", "synthetic-runtime-secret")
                )
        self.assertEqual([], self.store.all("objective"))

    def test_machine_lie_does_not_verify_file(self):
        from oscar.contracts import Result, new_id

        task = self.runtime.create(Intent("write", "file_write", "lie.txt", "expected"))

        def lie(action, cancellation):
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                action.capability_id,
                True,
            )

        dispatcher = Dispatcher(self.store, self.grid, "machine", {"machine.files.write": lie})
        state = self.runtime.run(task.id, {"machine": (dispatcher, self.session)})
        self.assertEqual(TaskState.FAILED, state.state)
        self.assertFalse((self.workspace / "lie.txt").exists())
