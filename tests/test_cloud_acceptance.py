"""Actual service processes and sockets, synthetic credentials, real canonical storage."""

import json
import os
import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from http.client import RemoteDisconnected
from pathlib import Path
from time import monotonic, sleep

from oscar.cloud import CloudConfig
from oscar.cloud_state import backup_state, restore_state
from oscar.contracts import new_id
from oscar.grid import SessionHandle
from tests.test_cloud import auth_headers, configuration, request


class CloudAcceptanceTests(unittest.TestCase):
    def setUp(self):
        from tempfile import TemporaryDirectory

        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = configuration(self.root)
        self.config = CloudConfig.load(self.path)
        self.processes = []
        self.addCleanup(self.stop_all)
        self.command("--initialize")
        self.credential = self.root / "client.json"
        self.command(
            "--enroll-client",
            "--node-id",
            "synthetic-client",
            "--credential-output",
            str(self.credential),
        )
        data = json.loads(self.credential.read_text())
        self.session = SessionHandle(data["session_id"], data["node_id"], data["token"])

    def command(self, *args, expected=0):
        result = subprocess.run(
            [sys.executable, "-m", "oscar.cloud", "--config", str(self.path), *args],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def launch(self, *, crash_before_archive=False):
        command = [sys.executable, "-m", "oscar.cloud"]
        if crash_before_archive:
            command = [
                sys.executable,
                "-c",
                "import os; from oscar.cloud import main; "
                "from oscar.event_archive import EventArchive; "
                "EventArchive.append=lambda *a,**k: os._exit(79); "
                "raise SystemExit(main())",
            ]
        log = (self.root / "service.log").open("a", encoding="utf-8")
        self.addCleanup(log.close)
        process = subprocess.Popen([*command, "--config", str(self.path)], stdout=log, stderr=log)
        self.processes.append(process)
        deadline = monotonic() + 20
        while monotonic() < deadline:
            if process.poll() is not None:
                self.fail("Core exited before ready: " + (self.root / "service.log").read_text())
            try:
                if request(self.config, "/readyz")[0] == 200:
                    return process
            except OSError:
                pass
            sleep(0.05)
        self.fail("Core readiness timed out")

    def stop(self, process, *, crash=False):
        if process.poll() is None:
            process.kill() if crash else process.terminate()
            process.wait(timeout=20)

    def stop_all(self):
        for process in self.processes:
            self.stop(process)

    def test_fresh_real_request_crash_restart_replay_backup_and_independent_restore(self):
        process = self.launch()
        request_id = new_id()
        body = {"request_id": request_id, "expression": "123 + 456"}
        admission_headers = auth_headers(self.session)
        code, first = request(self.config, "/v1/probes", body=body, headers=admission_headers)
        self.assertEqual(200, code)
        self.assertEqual(579, first["value"])
        self.stop(process, crash=True)
        process = self.launch()
        self.assertEqual(
            409, request(self.config, "/v1/probes", body=body, headers=admission_headers)[0]
        )
        self.assertEqual(
            (200, first), request(self.config, "/v1/probes/" + request_id, session=self.session)
        )
        self.assertEqual(
            (200, first), request(self.config, "/v1/probes", body=body, session=self.session)
        )
        self.stop(process)
        with closing(sqlite3.connect(self.config.data_dir / "core.sqlite")) as db:
            self.assertEqual(
                1, db.execute("SELECT count(*) FROM records WHERE kind='task'").fetchone()[0]
            )
        backup = self.root / "snapshot"
        backup_state(self.config.data_dir, backup)
        restored = self.root / "restored"
        restore_state(backup, restored)
        data = json.loads(self.path.read_text())
        self.path.write_text(json.dumps({**data, "data_dir": str(restored)}))
        self.config = CloudConfig.load(self.path)
        process = self.launch()
        self.assertEqual(
            (200, first), request(self.config, "/v1/probes/" + request_id, session=self.session)
        )
        self.stop(process)
        if os.name != "nt":
            self.assertEqual(0, process.returncode)
            self.assertIn('"core_stopped"', (self.root / "service.log").read_text())
        logs = (self.root / "service.log").read_text()
        self.assertNotIn(self.session.token, logs)
        self.assertNotIn(body["expression"], logs)

    def test_process_death_in_cross_database_admission_gap_repairs_without_second_task(self):
        process = self.launch(crash_before_archive=True)
        body = {"request_id": new_id(), "expression": "4 + 5"}
        with self.assertRaises((OSError, RemoteDisconnected)):
            request(self.config, "/v1/probes", session=self.session, body=body)
        self.assertEqual(79, process.wait(timeout=10))
        process = self.launch()
        # Inspect reports pending persistence rather than claiming a successful request.
        self.assertEqual(
            409, request(self.config, "/v1/probes/" + body["request_id"], session=self.session)[0]
        )
        code, repaired = request(self.config, "/v1/probes", session=self.session, body=body)
        self.assertEqual(200, code)
        self.assertEqual("verified", repaired["state"])
        self.stop(process)
        with closing(sqlite3.connect(self.config.data_dir / "core.sqlite")) as db:
            self.assertEqual(
                1, db.execute("SELECT count(*) FROM records WHERE kind='task'").fetchone()[0]
            )
        with closing(sqlite3.connect(self.config.data_dir / "core.archive.sqlite")) as db:
            self.assertEqual(1, db.execute("SELECT count(*) FROM archive_events").fetchone()[0])

    def test_offline_revocation_and_security_configuration_fail_closed(self):
        self.command("--revoke-client", "--node-id", "synthetic-client")
        process = self.launch()
        self.assertEqual(401, request(self.config, "/v1/status", session=self.session)[0])
        self.stop(process)
        data = json.loads(self.path.read_text())
        del data["ingress"]
        self.path.write_text(json.dumps(data))
        result = self.command(expected=1)
        self.assertIn("core_failed", result.stdout)
        self.assertNotIn(self.session.token, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
