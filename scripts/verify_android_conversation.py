"""Native conversation -> TLS Core -> outbound Desktop Worker; synthetic authority only."""

import base64
import hashlib
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import monotonic, sleep

from scripts.verify_connected_grid import android_core_fixture
from tests.test_connected_acceptance import sign
from tests.test_providers import ProviderContractTests

ROOT = Path(__file__).resolve().parents[1]
SERIAL = "emulator-5582"
AVD = "oscar_group05_capability_api35"
PACKAGE = "io.dawnlight.oscar.mobile"


def source_hashes():
    paths = [
        *ROOT.glob("oscar/*.py"),
        *ROOT.glob("tests/*.py"),
        Path(__file__),
        ROOT / "scripts/verify_connected_grid.py",
    ]
    paths += list((ROOT / "mobile/app/src").rglob("*.kt"))
    paths += list((ROOT / "mobile/app/src").rglob("*.java"))
    paths += list((ROOT / "mobile/app/build/outputs/apk").rglob("*.apk"))
    return {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def main():
    adb = Path(os.environ["ANDROID_HOME"]) / "platform-tools/adb.exe"
    output = ROOT / ".oscar/android-conversation"
    output.mkdir(parents=True, exist_ok=True)
    sources = source_hashes()

    def raw(*args, timeout=30):
        result = subprocess.run(
            [str(adb), "-s", SERIAL, *args], capture_output=True, text=True, timeout=timeout
        )
        assert result.returncode == 0, "Exact disposable emulator command failed"
        return result.stdout

    def device(*args, timeout=30):
        assert raw("emu", "avd", "name").splitlines()[0].strip() == AVD
        for name, expected in (
            ("ro.kernel.qemu", "1"),
            ("ro.build.version.sdk", "35"),
            ("sys.boot_completed", "1"),
        ):
            assert raw("shell", "getprop", name).strip() == expected
        return raw(*args, timeout=timeout)

    def instrument(method, details=None):
        args = ["shell", "am", "instrument", "-w", "-r", "-e", "class", PACKAGE + "." + method]
        for name in ("grid_origin", "grid_invitation", "grid_ca"):
            if details:
                args += ["-e", name, details[name]]
        log = device(*args, PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner", timeout=150)
        (output / (method.replace("#", "-") + ".log")).write_text(log, encoding="utf-8")
        assert re.search(r"OK \(1 test\)", log) and not re.search(
            r"FAILURES|INSTRUMENTATION_FAILED", log
        ), "Inspect native instrumentation log"

    device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    device("shell", "wm", "dismiss-keyguard")
    fixture_model = ProviderContractTests()
    fixture_model.setUp()
    try:
        for apk in ("debug/app-debug.apk", "androidTest/debug/app-debug-androidTest.apk"):
            assert "Success" in device(
                "install", "-r", str(ROOT / "mobile/app/build/outputs/apk" / apk), timeout=90
            )
        instrument("GridKeystoreTest#exportGridIdentity")
        identity = json.loads(
            device("exec-out", "run-as", PACKAGE, "cat", "files/d2-device-identity.json")
        )
        with android_core_fixture(identity, management=True) as (fixture, _, details):
            fixture.stop_all()
            manifest = {
                "version": 1,
                "providers": [
                    {
                        "id": "fixture",
                        "adapter": "openai",
                        "base_url": fixture_model.url,
                        "credential_envs": {},
                        "local": True,
                    }
                ],
                "models": [
                    {
                        "provider_id": "fixture",
                        "id": "fixture-model",
                        "capabilities": ["text", "structured"],
                        "quality": 2,
                        "affinities": {"reasoning": 1},
                        "context_limit": 32768,
                        "output_limit": 4096,
                        "funding": "free",
                    }
                ],
            }
            (fixture.root / "models.json").write_text(json.dumps(manifest), encoding="utf-8")
            fixture_model.body["choices"][0]["message"]["content"] = json.dumps(
                [
                    {
                        "id": "save",
                        "intent": {
                            "text": "Save native phone handoff 7481",
                            "kind": "file_write",
                            "path": "native-phone-handoff.txt",
                            "content": "NATIVE HANDOFF 7481",
                            "parameters": {},
                        },
                        "node_id": "synthetic-desktop",
                        "capability_id": "machine.files.write",
                        "depends_on": [],
                    }
                ]
            )
            fixture.start_core()
            fixture.start_worker()
            port = str(details["grid_port"])
            device("reverse", "tcp:" + port, "tcp:" + port)
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    native = executor.submit(
                        instrument,
                        "NativeGridExecutionTest#conversationDelegatesToDesktop",
                        details,
                    )
                    deadline = monotonic() + 60
                    while (
                        "software-handoff-review.json"
                        not in device("shell", "run-as", PACKAGE, "ls", "files").split()
                    ):
                        if native.done():
                            native.result()
                        assert monotonic() < deadline, "Native delegation review was not exported"
                        sleep(0.2)
                    review = json.loads(
                        device(
                            "exec-out",
                            "run-as",
                            PACKAGE,
                            "cat",
                            "files/software-handoff-review.json",
                        )
                    )
                    signature = base64.b64encode(
                        sign(fixture.owner_key, base64.b64decode(review["signing_payload"]))
                    ).decode()
                    device(
                        "shell",
                        "run-as",
                        PACKAGE,
                        "sh",
                        "-c",
                        "'echo " + signature + " > files/software-handoff-signature.txt'",
                    )
                    try:
                        native.result(timeout=120)
                    except Exception:
                        (output / "failed-snapshot.json").write_text(
                            json.dumps(
                                {
                                    "snapshot": fixture.mobile.request("snapshot", {}),
                                    "requests": fixture_model.requests,
                                    "marker_exists": (
                                        fixture.workspace / "native-phone-handoff.txt"
                                    ).exists(),
                                },
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                        raise
                assert (fixture.workspace / "native-phone-handoff.txt").read_text(
                    encoding="utf-8"
                ) == "NATIVE HANDOFF 7481"
                snapshot = fixture.mobile.request("snapshot", {})
                tasks = [
                    t
                    for t in snapshot["tasks"]
                    if t["description"] == "Save native phone handoff 7481"
                ]
                assert len(tasks) == 1 and tasks[0]["state"] == "verified"
                assert len(fixture_model.requests) == 1
                receipt = {
                    "classification": "NATIVE_EMULATED_CONVERSATION_DESKTOP_HANDOFF_VERIFIED",
                    "serial": SERIAL,
                    "avd": AVD,
                    "task": tasks[0],
                    "model_requests": len(fixture_model.requests),
                    "qualification": (
                        "Actual Android Keystore, CoreSession.send, separate TLS Core and outbound "
                        "Windows Worker. Synthetic fixed model response and host-signed Full "
                        "authority; no model accuracy, physical phone or owner biometric claim."
                    ),
                }
            finally:
                device("reverse", "--remove", "tcp:" + port)
    finally:
        fixture_model.doCleanups()
        device("uninstall", PACKAGE + ".test")
        device("uninstall", PACKAGE)
    assert sources == source_hashes(), "Sources/APKs changed during acceptance"
    receipt["source_sha256"] = sources
    receipt["cleanup"] = (
        "Both disposable apps uninstalled; reverse tunnel removed; "
        "fixture processes and synthetic data removed"
    )
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in ("classification", "model_requests", "qualification", "cleanup")
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
