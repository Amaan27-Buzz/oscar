"""Read-only/manual harness contracts; never drive the owner's desktop."""

import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from oscar.powershell import discover
from oscar.windows_desktop import BRIDGE, BRIDGE_PATH, WindowsDesktop
from scripts.verify_gate_b_interactive import (
    AcceptanceFailure,
    failure_evidence,
    fixture_window,
    main,
    require,
    text_summary,
    wait_for_focus,
)


class Observer:
    def __init__(self, pids, *, change=None):
        self.pids = iter(pids)
        self.change = change
        self.calls = []
        self.last = 0

    def observe(self, request, *, timeout):
        self.calls.append((request, timeout))
        self.last = next(self.pids, self.last)
        window = {"handle": 12, "pid": 8, "name": "OSCAR-acceptance-new.txt - Notepad"}
        editor = {"pid": 8, "runtime_id": "1.2", "text": ""}
        snapshot = {
            "windows": [window.copy(), window.copy()],
            "editors": [editor.copy(), editor.copy()],
            "focused": {"pid": self.last, "runtime_id": "focus"},
        }
        if self.change:
            self.change(snapshot)
        return snapshot


class InteractiveHarnessTests(unittest.TestCase):
    selector = {"handle": 12, "pid": 8, "runtime_id": "1.2"}
    fixture = "OSCAR-acceptance-new.txt"

    def test_documented_module_entrypoint_from_root(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "scripts.verify_gate_b_interactive", "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--desktop", result.stdout)
        self.assertIn("--root", result.stdout)

    def test_delayed_focus_requires_independent_target_pid(self):
        observer = Observer([0, 99, 8])
        focused = wait_for_focus(observer, self.selector, self.fixture, prior_pid=99)
        self.assertEqual(focused["pid"], 8)
        self.assertEqual(len(observer.calls), 3)
        self.assertTrue(
            all(request["operation"] == "focus_snapshot" for request, _ in observer.calls)
        )
        self.assertTrue(all(0 < bound <= 3 for _, bound in observer.calls))

    def test_never_focused_fails_with_observation(self):
        with self.assertRaises(AcceptanceFailure) as caught:
            wait_for_focus(Observer([0]), self.selector, self.fixture, timeout=0.02)
        self.assertEqual(caught.exception.check, "desktop.focus_readback")
        self.assertEqual(caught.exception.observed["pid"], 0)
        self.assertIn("expected", str(caught.exception))

    def test_unrelated_focus_change_fails_immediately(self):
        observer = Observer([99, 77, 8])
        with self.assertRaises(AcceptanceFailure) as caught:
            wait_for_focus(observer, self.selector, self.fixture, prior_pid=99)
        self.assertEqual(caught.exception.observed["pid"], 77)
        self.assertEqual(len(observer.calls), 2)

    def test_foreign_pid_without_prior_observation_rejected(self):
        with self.assertRaises(AcceptanceFailure):
            wait_for_focus(Observer([99]), self.selector, self.fixture)

    def test_identity_changes_before_or_after_focus_rejected(self):
        for section, key, value in (
            ("windows", "pid", 99),
            ("windows", "handle", 99),
            ("windows", "name", "OSCAR-acceptance-prior.txt - Notepad"),
            ("editors", "runtime_id", "changed"),
            ("editors", "text", "owner private note"),
        ):
            for index in (0, 1):
                with self.subTest(section=section, key=key, index=index):

                    def change(snapshot, section=section, index=index, key=key, value=value):
                        snapshot[section][index][key] = value

                    observer = Observer([8], change=change)
                    with self.assertRaises(AcceptanceFailure) as caught:
                        wait_for_focus(observer, self.selector, self.fixture)
                    self.assertEqual(caught.exception.check, "desktop.focus_identity")
                    self.assertEqual(len(observer.calls), 1)
                    self.assertNotIn("owner private note", str(caught.exception))

    def test_stale_and_owner_windows_are_never_admitted(self):
        for title in ("Owner notes - Notepad", "OSCAR-acceptance-prior.txt - Notepad"):
            self.assertFalse(
                fixture_window(
                    [{"handle": 12, "pid": 8, "name": title}], self.selector, self.fixture
                )
            )

    def test_failure_evidence_has_named_check_and_safe_details(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                require(
                    False,
                    "desktop.text_readback",
                    text_summary("synthetic"),
                    text_summary("owner private note"),
                )
            except AcceptanceFailure as error:
                report = failure_evidence(
                    root,
                    error,
                    {
                        "fixture_id": "unique",
                        "bound_target": self.selector,
                        "last_successful_action": {
                            "capability": "machine.desktop",
                            "operation": "mouse_click",
                        },
                        "cleanup": {"fixture_tab": "owner review"},
                    },
                )
            saved = json.loads((root / "failure.json").read_text())
            self.assertEqual(saved, report)
            self.assertEqual(saved["phase"], "desktop")
            self.assertEqual(saved["check"], "desktop.text_readback")
            self.assertTrue(saved["error"])
            self.assertTrue(saved["traceback"][0]["line"])
            self.assertEqual(saved["bound_target"], self.selector)
            self.assertEqual(saved["last_successful_action"]["operation"], "mouse_click")
            self.assertNotIn("owner private note", json.dumps(saved))

    def test_main_preserves_named_failure_and_failed_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"

            def fail(path, *, desktop):
                path.mkdir()
                error = AcceptanceFailure("desktop.focus_readback", {"pid": 8}, {"pid": 0})
                failure_evidence(path, error, {"fixture_id": "new"})
                raise error

            with (
                patch("scripts.verify_gate_b_interactive.run", side_effect=fail),
                patch("scripts.verify_gate_b_interactive.os", SimpleNamespace(name="nt")),
                patch.object(sys, "argv", ["harness", "--root", str(root), "--desktop"]),
                patch("builtins.print"),
            ):
                self.assertEqual(main(), 1)
                with self.assertRaises(SystemExit):
                    main()
            self.assertEqual(
                json.loads((root / "failure.json").read_text())["check"], "desktop.focus_readback"
            )

    def test_snapshot_is_read_only_and_brackets_focus(self):
        snapshot = BRIDGE.split(" 'focus_snapshot' {", 1)[1].split(" 'focus' {", 1)[0]
        self.assertNotIn("SetFocus", snapshot)
        self.assertNotIn("SendKeys", snapshot)
        self.assertLess(snapshot.index("$beforeWindow"), snapshot.index("::FocusedElement"))
        self.assertGreater(snapshot.index("(Describe $window)"), snapshot.index("::FocusedElement"))

    def test_observer_subprocess_uses_remaining_timeout(self):
        observer = object.__new__(WindowsDesktop)
        with (
            patch.object(WindowsDesktop, "command", return_value=["owned-observer"]),
            patch(
                "oscar.windows_desktop.subprocess.run",
                return_value=SimpleNamespace(returncode=0, stdout=b"{}"),
            ) as execute,
        ):
            observer.observe({"operation": "focus_snapshot"}, timeout=0.25)
            self.assertEqual(execute.call_args.kwargs["timeout"], 0.25)
            with self.assertRaises(ValueError):
                observer.observe({}, timeout=0)

    def test_timed_out_observer_has_named_diagnostic(self):
        observer = Observer([8])
        with patch.object(
            observer, "observe", side_effect=subprocess.TimeoutExpired("observer", 0.1)
        ):
            with self.assertRaises(AcceptanceFailure) as caught:
                wait_for_focus(observer, self.selector, self.fixture)
        self.assertEqual(caught.exception.check, "desktop.focus_readback")
        self.assertEqual(caught.exception.observed["observer_error_type"], "TimeoutExpired")

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell syntax contract")
    def test_native_bridge_parses_without_running_desktop_actions(self):
        manifest = discover()
        self.assertIsNotNone(manifest)
        encoded = base64.b64encode(str(BRIDGE_PATH).encode()).decode()
        script = (
            "$path=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + encoded + "'));"
            "$tokens=$null;$errors=$null;"
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            "$path,[ref]$tokens,[ref]$errors);"
            "if ($errors.Count) {$errors|ForEach-Object {$_.Message};exit 1}"
        )
        result = subprocess.run(
            [
                manifest.executable,
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(script.encode("utf-16-le")).decode(),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
