"""Rendered memory controls and synthetic signed reviews through an actual TLS Core."""

import base64
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from time import monotonic, sleep, time

from oscar.cloud import CloudCore
from oscar.event_archive import MemoryWriter, SourceEvent
from scripts.software_android_reference import AVD, PACKAGE, ROOT, SERIAL, source_hashes
from scripts.verify_connected_grid import android_core_fixture
from tests.test_connected_acceptance import sign

ORIGINAL = "The synthetic project is named Copper"
CORRECTION = "The synthetic project is named Silver"


def main() -> int:
    adb = Path(os.environ["ANDROID_HOME"]) / "platform-tools/adb.exe"
    output = ROOT / ".oscar/software-android-memory"
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "native-memory.json"
    receipt_path.unlink(missing_ok=True)

    def pinned():
        return source_hashes() | {
            Path(__file__).relative_to(ROOT).as_posix(): hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest()
        }

    sources = pinned()

    def raw(*arguments: str, timeout: int = 30, contents: str | None = None) -> str:
        result = subprocess.run(
            [str(adb), "-s", SERIAL, *arguments],
            capture_output=True,
            text=True,
            input=contents,
            timeout=timeout,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Exact disposable emulator request failed")
        return result.stdout

    def guard():
        assert raw("emu", "avd", "name").splitlines()[0].strip() == AVD
        assert raw("shell", "getprop", "ro.kernel.qemu").strip() == "1"
        assert raw("shell", "getprop", "ro.build.version.sdk").strip() == "35"
        assert raw("shell", "getprop", "sys.boot_completed").strip() == "1"

    def device(*arguments: str, timeout: int = 30, contents: str | None = None):
        guard()
        return raw(*arguments, timeout=timeout, contents=contents)

    def read(name):
        return device("exec-out", "run-as", PACKAGE, "cat", "files/software-memory-" + name)

    def write(name, value):
        temporary = "files/software-memory-" + name + ".tmp"
        destination = "files/software-memory-" + name
        device("shell", "-T", "run-as", PACKAGE, "tee", temporary, contents=value)
        device("shell", "run-as", PACKAGE, "mv", temporary, destination)

    def accepted(process, log):
        text = log.read_text(encoding="utf-8")
        assert (
            process.returncode == 0
            and re.search(r"OK \(1 test\)", text)
            and not re.search(
                r"FAILURES|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -[34]", text
            )
        ), "Inspect private memory instrumentation log"

    def instrument(method, details=None):
        arguments = [
            "shell",
            "am",
            "instrument",
            "-w",
            "-r",
            "-e",
            "class",
            PACKAGE + "." + method,
            "-e",
            "memory_disposable",
            "true",
        ]
        for key in ("grid_ca", "grid_origin", "grid_invitation"):
            if details is not None:
                arguments += ["-e", key, str(details[key])]
        arguments += [PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner"]
        guard()
        path = output / (method.replace("#", "-") + ".log")
        with path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen([str(adb), "-s", SERIAL, *arguments], stdout=log, stderr=log)
        return process, path

    guard()
    for package in (PACKAGE, PACKAGE + ".test"):
        installed = device("shell", "pm", "list", "packages", package).splitlines()
        assert "package:" + package not in installed, "A fresh disposable package is required"
    installed = []
    process = None
    result = None
    try:
        device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        device("shell", "wm", "dismiss-keyguard")
        for apk, package in (
            ("app/build/outputs/apk/debug/app-debug.apk", PACKAGE),
            (
                "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
                PACKAGE + ".test",
            ),
        ):
            assert "Success" in device("install", "-t", str(ROOT / "mobile" / apk), timeout=120)
            installed.append(package)
        device("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
        process, log = instrument("GridKeystoreTest#exportGridIdentity")
        process.wait(timeout=90)
        accepted(process, log)
        identity = json.loads(
            device("exec-out", "run-as", PACKAGE, "cat", "files/d2-device-identity.json")
        )
        with android_core_fixture(identity, management=True, memory_control=True) as (
            fixture,
            core_process,
            details,
        ):
            fixture.stop(core_process)
            core = CloudCore(fixture.config, start_services=False)
            try:
                archive = core.harness.archive
                relationship = core.harness.runtime.relationship_id
                source = SourceEvent(
                    relationship,
                    ORIGINAL,
                    "remote-grid:synthetic-memory",
                    time(),
                    kind="conversation_owner",
                )
                archive.append(source, retain_authorized=True)
                memory = MemoryWriter(archive).retain(
                    (source.id,), ORIGINAL, "episodic", retain_authorized=True, inferred=False
                )
                baseline = archive.generation(relationship)
            finally:
                core.close()
            fixture.start_core()
            archive_path = fixture.config.data_dir / "core.archive.sqlite"

            def readback():
                with closing(
                    sqlite3.connect(archive_path.as_uri() + "?mode=ro", uri=True)
                ) as database:
                    memories = {
                        key: (forgotten, json.loads(payload))
                        for key, forgotten, payload in database.execute(
                            "SELECT id,forgotten,payload FROM archive_memories "
                            "WHERE relationship=?",
                            (relationship,),
                        )
                    }
                    events = {
                        key: (forgotten, json.loads(payload))
                        for key, forgotten, payload in database.execute(
                            "SELECT id,forgotten,payload FROM archive_events WHERE relationship=?",
                            (relationship,),
                        )
                    }
                    generation = database.execute(
                        "SELECT generation FROM archive_generations WHERE relationship=?",
                        (relationship,),
                    ).fetchone()[0]
                    fts = {row[0] for row in database.execute("SELECT memory_id FROM archive_fts")}
                return memories, events, generation, fts

            initial_memories, initial_events, _, _ = readback()
            port = "tcp:" + str(details["grid_port"])
            device("reverse", port, port)
            try:
                process, log = instrument(
                    "NativeMemoryAcceptanceTest#renderedCorrectionForgetRefreshAndConsumedReviewRejection",
                    details,
                )

                def phase(expected):
                    deadline = monotonic() + 45
                    while monotonic() < deadline:
                        if process.poll() is not None:
                            accepted(process, log)
                            raise RuntimeError("Native memory test ended before " + expected)
                        try:
                            if read("stage").strip() == expected:
                                return
                        except RuntimeError:
                            pass
                        sleep(0.2)
                    raise RuntimeError("Native memory phase timed out: " + expected)

                phase("declined")
                memories, events, generation, _ = readback()
                assert memories == initial_memories and events == initial_events
                assert memories[memory.id][1]["content"] == ORIGINAL
                assert events[source.id][1]["content"] == ORIGINAL and generation == baseline
                write("declined.ack", "verified")
                reviewed = []
                corrected_id = None
                for name, operation in (
                    ("correction", "memory_correct"),
                    ("forget", "memory_forget"),
                ):
                    phase(name + "_review")
                    review = json.loads(read(name + ".json"))
                    assert set(review) == {"challenge_id", "signing_payload", "completion"}
                    assert review["completion"] == "assistance_complete"
                    payload = base64.b64decode(review["signing_payload"], validate=True)
                    assert 0 < len(payload) <= 40_000
                    claim = json.loads(payload)
                    change = claim["material"]["change"]
                    assert change["operation"] == operation
                    assert claim["node_id"] == "synthetic-emulated-android"
                    assert claim["material"]["review"]["current"]["relationship_id"] == relationship
                    if name == "correction":
                        assert change["id"] == memory.id
                        assert change["value"]["content"] == CORRECTION
                        assert change["value"]["retain"] is True
                    else:
                        assert change["id"] == corrected_id
                        assert change["value"]["forget_sources"] is True
                    write(
                        name + ".signature",
                        base64.b64encode(sign(fixture.owner_key, payload)).decode(),
                    )
                    phase(name + "_completed")
                    memories, events, generation, fts = readback()
                    if name == "correction":
                        assert len(memories) == len(initial_memories) + 1
                        assert memories[memory.id][1]["valid_to"] is not None
                        (corrected_id,) = set(memories) - set(initial_memories)
                        assert all(
                            memories[key] == value
                            for key, value in initial_memories.items()
                            if key != memory.id
                        )
                        corrected = memories[corrected_id][1]
                        assert (
                            corrected["supersedes"] == memory.id
                            and corrected["content"] == CORRECTION
                        )
                        correction_source = corrected["event_ids"][0]
                        assert events[correction_source][1]["corrects"] == source.id
                        assert generation > baseline
                    else:
                        assert memories[corrected_id] == (1, {})
                        assert events[correction_source] == (1, {}) and corrected_id not in fts
                        assert (
                            memories[memory.id][0] == 0
                            and events[source.id][1]["content"] == ORIGINAL
                        )
                    reviewed.append(
                        {
                            "operation": operation,
                            "payload_sha256": hashlib.sha256(payload).hexdigest(),
                        }
                    )
                    write(name + ".ack", "verified")
                process.wait(timeout=45)
                accepted(process, log)
                result = json.loads(read("result.json"))
                assert all(
                    value is True
                    for key, value in result.items()
                    if key != "android_owner_biometrics"
                )
                memories, events, _, fts = readback()
                assert memories[corrected_id] == (1, {}) and events[correction_source] == (1, {})
                assert corrected_id not in fts
                result["independent_archive_readback"] = reviewed
            finally:
                device("reverse", "--remove", port)
        assert not fixture.root.exists(), "Synthetic Core credentials or process workspace remained"
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=20)
        for package in reversed(installed):
            assert "Success" in device("uninstall", package)
            assert (
                "package:" + package
                not in device("shell", "pm", "list", "packages", package).splitlines()
            )
    assert result is not None
    assert sources == pinned(), "Source or APK changed during acceptance; receipt rejected"
    receipt = {
        "classification": "EMULATED_SYNTHETIC_ACTUAL_TLS_MEMORY",
        "serial": SERIAL,
        "avd": AVD,
        "api": 35,
        "native_readback": result,
        "source_sha256": sources,
        "authority": (
            "Rendered review; exact host synthetic owner signature; native signed Grid proof"
        ),
        "scope": "Activity recreation; correction preserves the original historical statement",
        "physical_phone": "NOT_RUN",
        "real_owner_biometrics": "NOT_RUN",
        "personal_memory": "NOT_RUN",
        "cleanup": (
            "Fresh packages removed and read back; synthetic Core processes and data removed"
        ),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("Actual rendered Android memory correction and forgetting acceptance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
