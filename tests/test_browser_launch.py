import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from oscar.browser_worker import BrowserFailure, main, probe
from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import (
    InteractiveWorker,
    browser_command,
    browser_diagnostic,
    browser_preflight,
)
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import Dispatcher


class SourceBrowserLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", str(cls.root / "python")],
            check=True,
            capture_output=True,
            timeout=30,
        )
        cls.python = str(
            cls.root / "python" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        )
        cls.workspace = cls.root / "artifacts"
        cls.workspace.mkdir()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_uninstalled_checkout_launch_ignores_cwd_and_pythonpath(self):
        shadow = self.workspace / "oscar"
        shadow.mkdir(exist_ok=True)
        (shadow / "__init__.py").write_text("raise RuntimeError('foreign package')")
        process = subprocess.run(
            browser_command(self.python, ["--help"]),
            cwd=self.workspace,
            env={**os.environ, "PYTHONPATH": str(self.workspace)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertIn("--probe", process.stdout)
        self.assertFalse((self.root / "python" / "Lib/site-packages/oscar").exists())

    def test_missing_playwright_detected_through_real_launch(self):
        diagnostic = browser_preflight(self.python, self.workspace)
        self.assertEqual("browser.playwright_unavailable", diagnostic["category"])
        self.assertEqual(1, diagnostic["exit_code"])

    def test_real_import_failure_is_categorized(self):
        with patch("oscar.interactive_worker.__file__", str(self.workspace / "worker.py")):
            diagnostic = browser_preflight(self.python, self.workspace)
        self.assertEqual("browser.import", diagnostic["category"])

    def test_probe_output_is_bounded(self):
        with patch(
            "oscar.interactive_worker.browser_command",
            return_value=[self.python, "-I", "-c", "print('x' * 10000)"],
        ):
            diagnostic = browser_preflight(self.python, self.workspace)
        self.assertEqual("browser.worker_launch", diagnostic["category"])
        self.assertLess(len(json.dumps(diagnostic)), 200)


class BrowserDiagnosticTests(unittest.TestCase):
    def test_missing_chromium_is_distinct_and_does_not_launch(self):
        with TemporaryDirectory() as temporary:
            runtime = MagicMock()
            chromium = runtime.return_value.__enter__.return_value.chromium
            chromium.executable_path = str(Path(temporary) / "missing-chromium")
            with patch("oscar.browser_worker.playwright_runtime", return_value=runtime):
                with self.assertRaises(BrowserFailure) as failure:
                    probe()
            self.assertEqual("browser.chromium_unavailable", failure.exception.category)
            chromium.launch.assert_not_called()

    def test_playwright_launch_error_has_no_private_message(self):
        with patch("sys.argv", ["oscar.browser_worker", "--probe"]):
            with patch("oscar.browser_worker.probe", side_effect=RuntimeError("private-token")):
                with patch("builtins.print") as output:
                    self.assertEqual(1, main())
        diagnostic = json.loads(output.call_args.args[0])
        self.assertEqual("browser.playwright_launch", diagnostic["category"])
        self.assertNotIn("private-token", json.dumps(diagnostic))

    def test_nonzero_diagnostics_discard_private_fields_and_arbitrary_text(self):
        diagnostic = browser_diagnostic(
            json.dumps(
                {
                    "category": "browser.plan_execution",
                    "error_type": "ValueError",
                    "message": "private cookies, token and page text",
                }
            ),
            7,
        )
        self.assertEqual("browser.plan_execution", diagnostic["category"])
        self.assertEqual(7, diagnostic["exit_code"])
        self.assertNotIn("private", json.dumps(diagnostic))
        for output in ("private stderr", "x" * 5000, '{"category": ["private"]}'):
            self.assertEqual("browser.worker_launch", browser_diagnostic(output, 1)["category"])

    def test_success_category_cannot_hide_nonzero_exit(self):
        self.assertEqual(
            "browser.worker_launch",
            browser_diagnostic('{"category":"browser.ready"}', 1)["category"],
        )


class BrowserWorkerDiagnosticBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Store(self.root / "state.sqlite")
        self.addCleanup(self.store.close)
        self.grid = Grid(self.store)
        grants = (
            "advertise",
            "heartbeat",
            "execute",
            "cancel",
            "machine:host",
            "files:read",
            "files:write",
            "browser:control",
        )
        self.grid.register(Node("browser-test", NodeRole.DESKTOP, grants))
        self.session = self.grid.pair("browser-test", grants)

    def worker(self):
        return InteractiveWorker(
            self.store,
            self.grid,
            self.session,
            MachineScope(self.root, True, (sys.executable,)),
            browser=True,
        )

    def test_unavailable_launch_does_not_advertise_browser(self):
        with patch("oscar.interactive_worker.__file__", str(self.root / "missing.py")):
            worker = self.worker()
        self.assertEqual("browser.import", worker.browser_probe["category"])
        self.assertNotIn("machine.browser", {cap.id for cap in worker.capabilities()})

    def test_failed_operation_retains_only_safe_diagnostics_and_scoped_cwd(self):
        with patch(
            "oscar.interactive_worker.browser_preflight", return_value={"category": "browser.ready"}
        ):
            worker = self.worker()
        self.grid.advertise(self.session, worker.capabilities())
        runtime = Runtime(self.store, self.grid, MachineVerifier(worker.files))
        plan = {
            "origins": ["https://example.com"],
            "steps": [{"operation": "navigate", "url": "https://example.com"}],
            "timeout": 5,
            "max_text": 100,
        }
        task = runtime.create(
            Intent(
                "browser fixture",
                "capability",
                capability_kind="browser",
                parameters={"request": plan},
            )
        )
        with patch.object(
            worker,
            "run_command",
            return_value=(1, '{"category":"browser.import","message":"private-secret"}'),
        ) as execution:
            result = runtime.run(
                task.id,
                {
                    self.session.node_id: (
                        Dispatcher(self.store, self.grid, self.session.node_id, worker.executors()),
                        self.session,
                    )
                },
            )
        self.assertEqual("browser.import", result.blocker)
        self.assertEqual(".", execution.call_args.args[3])
        self.assertEqual(
            browser_command(sys.executable, ["--request", json.dumps(plan)]),
            execution.call_args.args[2],
        )
        self.assertEqual(
            "browser.import", json.loads(next(iter(worker.outputs.values())))["category"]
        )
        self.assertNotIn("private-secret", json.dumps(worker.outputs))
        self.assertNotIn(b"private-secret", (self.root / "state.sqlite").read_bytes())


if __name__ == "__main__":
    unittest.main()
