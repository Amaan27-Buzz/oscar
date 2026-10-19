"""Host orchestration safety; mocks do not establish Android acceptance."""

import base64
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts import verify_android_grid as verifier


class AndroidGridVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for relative in (
            "app/build/outputs/apk/debug/app-debug.apk",
            "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
        ):
            apk = self.root / "mobile" / relative
            apk.parent.mkdir(parents=True, exist_ok=True)
            apk.write_bytes(b"synthetic-test-apk")
        self.commands: list[list[str]] = []
        self.qemu = "1"
        self.fail_install = False
        self.timeout_connected = False
        self.skip_identity = False
        self.revoked = True
        self.invitation = base64.b64encode(
            json.dumps({"node_id": "synthetic-android"}).encode()
        ).decode()

    def adb(self, command: list[str], **_options: object) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        if command[1:] == ["devices", "-l"]:
            output = "List of devices attached\nemulator-5590 device product:sdk_gphone64_x86_64\n"
        else:
            self.assertEqual(command[1:3], ["-s", "emulator-5590"])
            operation = command[3:]
            if operation == ["get-state"]:
                output = "device\n"
            elif operation == ["shell", "getprop", "ro.kernel.qemu"]:
                output = self.qemu + "\n"
            elif operation == ["emu", "avd", "name"]:
                output = "oscar_disposable_fixture\nOK\n"
            elif operation[0] == "install":
                if self.fail_install:
                    return subprocess.CompletedProcess(command, 1, "", "INSTALL_FAILED_TEST_ONLY")
                output = "Performing Streamed Install\nSuccess\n"
            elif operation[:3] == ["shell", "am", "instrument"]:
                if any("#connectedGrid" in value for value in operation) and self.timeout_connected:
                    raise subprocess.TimeoutExpired(
                        command,
                        180,
                        output=(self.invitation + "\nassertion stalled").encode(),
                        stderr=b"timeout",
                    )
                output = (
                    "INSTRUMENTATION_STATUS_CODE: -3\nOK (1 test)\n"
                    if self.skip_identity
                    else "OK (1 test)\n"
                )
            elif operation[:2] == ["exec-out", "run-as"]:
                output = json.dumps({"installation_id": "synthetic", "public_key": "public"})
            else:
                output = ""
        return subprocess.CompletedProcess(command, 0, output, "")

    def run_verifier(self, serial: str = "emulator-5590") -> int:
        fixture = Mock()
        fixture.mobile.request.return_value = {
            "nodes": [{"id": "synthetic-android", "revoked": self.revoked, "status": "offline"}]
        }
        details = {
            "grid_port": 7777,
            "grid_origin": "https://127.0.0.1:7777",
            "grid_invitation": self.invitation,
            "grid_ca": "public-ca",
        }
        with (
            patch.object(verifier, "ROOT", self.root),
            patch.object(subprocess, "run", side_effect=self.adb),
            patch.object(
                verifier,
                "android_core_fixture",
                return_value=contextlib.nullcontext((fixture, Mock(), details)),
            ),
            patch("sys.argv", ["verify_android_grid", "--serial", serial, "--adb", "adb"]),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            return verifier.main()

    def test_reinstalls_both_exact_apks_after_guard_before_instrumentation(self) -> None:
        self.assertEqual(self.run_verifier(), 0)
        operations = [command[3:] for command in self.commands[1:]]
        self.assertEqual(operations[1], ["shell", "getprop", "ro.kernel.qemu"])
        self.assertEqual(operations[2], ["emu", "avd", "name"])
        self.assertEqual(operations[3][:3], ["install", "-r", "-t"])
        self.assertTrue(operations[3][3].endswith("app-debug.apk"))
        self.assertEqual(operations[4][:3], ["install", "-r", "-t"])
        self.assertTrue(operations[4][3].endswith("app-debug-androidTest.apk"))
        self.assertEqual(operations[5][:3], ["shell", "am", "instrument"])
        self.assertEqual(sum(op[:3] == ["shell", "am", "instrument"] for op in operations), 5)
        self.assertEqual(operations[-1], ["reverse", "--remove", "tcp:7777"])

    def test_physical_serial_rejected_before_any_adb(self) -> None:
        with self.assertRaises(SystemExit):
            self.run_verifier("owner-phone")
        self.assertEqual(self.commands, [])

    def test_successful_native_report_requires_independent_revocation_readback(self) -> None:
        self.revoked = False
        with self.assertRaisesRegex(RuntimeError, "did not confirm Android revocation"):
            self.run_verifier()
        self.assertEqual(self.commands[-1][3:], ["reverse", "--remove", "tcp:7777"])

    def test_qemu_guard_prevents_install_even_with_emulator_like_serial(self) -> None:
        self.qemu = "0"
        with self.assertRaisesRegex(RuntimeError, "not an emulator"):
            self.run_verifier()
        self.assertFalse(any("install" in command for command in self.commands))

    def test_install_failure_keeps_diagnostic_stderr_and_stops(self) -> None:
        self.fail_install = True
        with self.assertRaisesRegex(RuntimeError, "install-app .*exit 1"):
            self.run_verifier()
        self.assertFalse(any("instrument" in command for command in self.commands))
        log = self.root / ".oscar/d2-android/install-app.log"
        self.assertIn("INSTALL_FAILED_TEST_ONLY", log.read_text())

    def test_timeout_sanitizes_invitation_and_cleans_reverse(self) -> None:
        self.timeout_connected = True
        with self.assertRaisesRegex(RuntimeError, "timed out: instrument-connectedGrid") as error:
            self.run_verifier()
        self.assertNotIn(self.invitation, str(error.exception))
        log = (self.root / ".oscar/d2-android/instrument-connectedGrid.log").read_text()
        self.assertNotIn(self.invitation, log)
        self.assertIn("assertion stalled", log)
        self.assertEqual(self.commands[-1][3:], ["reverse", "--remove", "tcp:7777"])

    def test_assumption_cannot_be_reported_as_pass(self) -> None:
        self.skip_identity = True
        with self.assertRaisesRegex(RuntimeError, "native emulator check failed"):
            self.run_verifier()


if __name__ == "__main__":
    unittest.main()
