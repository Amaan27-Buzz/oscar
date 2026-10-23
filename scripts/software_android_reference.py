"""Actual native Android execution through a separate TLS Core on one disposable AVD."""

import base64
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from time import monotonic, sleep

from scripts.verify_connected_grid import android_core_fixture
from tests.test_connected_acceptance import sign

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "io.dawnlight.oscar.mobile"
SERIAL = "emulator-5582"
AVD = "oscar_group05_capability_api35"


def source_hashes() -> dict[str, str]:
    paths = [*ROOT.glob("oscar/*.py"), Path(__file__), ROOT / "scripts/verify_connected_grid.py"]
    paths += [p for p in (ROOT / "mobile/app/src").rglob("*") if p.suffix in {".kt", ".java"}]
    paths += list((ROOT / "mobile/app/build/outputs/apk").rglob("*.apk"))
    return {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def main() -> int:
    adb = Path(os.environ["ANDROID_HOME"]) / "platform-tools/adb.exe"
    output = ROOT / ".oscar/software-android"
    output.mkdir(parents=True, exist_ok=True)
    receipt: dict | None = None
    (output / "native-grid.json").unlink(missing_ok=True)
    sources = source_hashes()

    def raw(*arguments: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                [str(adb), "-s", SERIAL, *arguments],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Exact disposable emulator request timed out") from None
        if result.returncode:
            raise RuntimeError("Exact disposable emulator request failed")
        return result.stdout

    def guard() -> None:
        assert raw("emu", "avd", "name").splitlines()[0].strip() == AVD
        assert raw("shell", "getprop", "ro.kernel.qemu").strip() == "1"
        assert raw("shell", "getprop", "ro.build.version.sdk").strip() == "35"
        assert raw("shell", "getprop", "sys.boot_completed").strip() == "1"

    def device(*arguments: str, timeout: int = 30) -> str:
        guard()
        return raw(*arguments, timeout=timeout)

    def instrument(method: str, *, details: dict | None = None, background: bool = False):
        guard()
        args = [
            str(adb),
            "-s",
            SERIAL,
            "shell",
            "am",
            "instrument",
            "-w",
            "-r",
            "-e",
            "class",
            PACKAGE + "." + method,
        ]
        for name, value in (details or {}).items():
            if name.startswith("grid_") and name not in {
                "grid_port",
                "grid_target",
                "grid_path",
                "grid_task",
            }:
                args += ["-e", name, str(value)]
        args += [PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner"]
        log_path = output / (method.replace("#", "-") + ".log")
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
        if background:
            return process, log_path
        try:
            process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError("Disposable instrumentation deadline exceeded") from None
        accepted(process, log_path)
        return None

    def accepted(process, path):
        log = path.read_text(encoding="utf-8")
        assert (
            process.returncode == 0
            and re.search(r"OK \(1 test\)", log)
            and not re.search(
                r"FAILURES|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -[34]", log
            )
        ), "Inspect private Android instrumentation log"

    def wait(check, message: str, seconds: int = 40):
        deadline = monotonic() + seconds
        while monotonic() < deadline:
            if check():
                return
            sleep(0.2)
        raise RuntimeError(message)

    guard()
    device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    device("shell", "wm", "dismiss-keyguard")
    previous_services = device(
        "shell", "settings", "get", "secure", "enabled_accessibility_services"
    ).strip()
    previous_access = device("shell", "settings", "get", "secure", "accessibility_enabled").strip()
    previous_listeners = device(
        "shell", "settings", "get", "secure", "enabled_notification_listeners"
    ).strip()
    listener = PACKAGE + "/.NotificationBoundary"
    listener_was_enabled = any(
        item in {listener, PACKAGE + "/" + PACKAGE + ".NotificationBoundary"}
        for item in previous_listeners.split(":")
    )
    process = None
    try:
        for apk in (
            "app/build/outputs/apk/debug/app-debug.apk",
            "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
        ):
            assert "Success" in device(
                "install", "-r", "-t", str(ROOT / "mobile" / apk), timeout=120
            )
        device("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
        device("shell", "pm", "grant", PACKAGE + ".test", "android.permission.POST_NOTIFICATIONS")
        device("shell", "cmd", "notification", "allow_listener", listener)
        device(
            "shell",
            "settings",
            "put",
            "secure",
            "enabled_accessibility_services",
            PACKAGE + "/.AppControlService",
        )
        device("shell", "settings", "put", "secure", "accessibility_enabled", "1")
        instrument("GridKeystoreTest#exportGridIdentity")
        identity = json.loads(
            device("exec-out", "run-as", PACKAGE, "cat", "files/d2-device-identity.json")
        )
        with android_core_fixture(identity, android_workspace="selected-apps", management=True) as (
            fixture,
            _,
            details,
        ):
            port = str(details["grid_port"])
            device("reverse", "tcp:" + port, "tcp:" + port)
            try:
                process, log_path = instrument(
                    "NativeGridExecutionTest#actualGridExecutesThenWithdrawsAndRevokes",
                    details=details,
                    background=True,
                )
                rebound = False
                phone_configured = False
                phone_context: dict = {}
                phone_ids = ["synthetic-phone-context"] + [
                    "synthetic-phone-context-" + str(index) for index in range(2, 9)
                ]
                phone_started = None
                phone_samples = 0
                next_phone_check = 0.0

                def review_phone(change: dict) -> None:
                    challenge = fixture.mobile.request("assistance_challenge", change)
                    fixture.mobile.request(
                        "assistance_complete",
                        {
                            "challenge_id": challenge["challenge_id"],
                            "signature": base64.b64encode(
                                sign(
                                    fixture.owner_key,
                                    base64.b64decode(challenge["signing_payload"]),
                                )
                            ).decode(),
                        },
                    )

                def ready():
                    nonlocal \
                        rebound, \
                        phone_configured, \
                        phone_started, \
                        phone_samples, \
                        next_phone_check
                    if not rebound:
                        stage = device(
                            "exec-out", "run-as", PACKAGE, "cat", "files/software-native-stage.txt"
                        ).strip()
                        if stage == "Worker start requested":
                            # Instrumentation force-stops leave an old Android service binding dead.
                            device(
                                "shell",
                                "settings",
                                "delete",
                                "secure",
                                "enabled_accessibility_services",
                            )
                            device(
                                "shell",
                                "settings",
                                "put",
                                "secure",
                                "enabled_accessibility_services",
                                PACKAGE + "/.AppControlService",
                            )
                            device(
                                "shell", "settings", "put", "secure", "accessibility_enabled", "1"
                            )
                            rebound = True
                    if not phone_configured:
                        try:
                            phone = json.loads(
                                device(
                                    "exec-out",
                                    "run-as",
                                    PACKAGE,
                                    "cat",
                                    "files/software-phone-binding.json",
                                )
                            )
                        except (RuntimeError, ValueError):
                            phone = None
                        if phone is not None:
                            assert phone["node_id"] == "synthetic-emulated-android"
                            device("shell", "cmd", "notification", "disallow_listener", listener)
                            device("shell", "cmd", "notification", "allow_listener", listener)
                            device(
                                "shell",
                                "am",
                                "start",
                                "-W",
                                "-n",
                                PACKAGE + ".test/" + PACKAGE + ".PhoneNotificationFixtureActivity",
                            )
                            for source_id in phone_ids:
                                review_phone(
                                    {
                                        "operation": "source_create",
                                        "id": source_id,
                                        "value": {
                                            "id": source_id,
                                            "adapter": "android",
                                            "entity_id": "phone:" + phone["node_id"],
                                            "interval_seconds": 5,
                                            "retain": False,
                                            "retention_seconds": 3600,
                                            **phone,
                                            "packages": [PACKAGE + ".test", PACKAGE],
                                        },
                                    }
                                )
                            review_phone(
                                {
                                    "operation": "sentry",
                                    "id": "awareness",
                                    "value": {
                                        "mode": "sentry",
                                        "state": "aware",
                                        "source_ids": phone_ids,
                                        "trigger_keys": [],
                                        "allow_interrupt": False,
                                    },
                                }
                            )
                            device(
                                "shell",
                                "run-as",
                                PACKAGE,
                                "touch",
                                "files/software-phone-configured",
                            )
                            phone_configured = True
                    if phone_configured and not phone_context and monotonic() >= next_phone_check:
                        next_phone_check = monotonic() + 2
                        brief = fixture.mobile.request("day_brief", {})["day_brief"]
                        current_phone = [s for s in brief["sources"] if s["id"] in phone_ids]
                        all_current = len(current_phone) == 8 and all(
                            s["state"] == "current" for s in current_phone
                        )
                        if phone_started is not None:
                            assert all_current, "A phone source expired during sustained acceptance"
                        selected = next(
                            (
                                source
                                for source in brief["sources"]
                                if source["id"] == "synthetic-phone-context"
                            ),
                            None,
                        )
                        if all_current and selected:
                            value = json.loads(selected["value"])
                            if value["notifications_available"] and value["media_available"]:
                                assert all(json.loads(s["value"]) == value for s in current_phone)
                                assert any(
                                    item["package"] == PACKAGE + ".test" and item["count"] >= 1
                                    for item in value["notifications"]
                                )
                                assert any(
                                    item["package"] == PACKAGE and item["state"] == 3
                                    for item in value["media"]
                                )
                                assert "synthetic-sensitive-body-marker" not in selected["value"]
                                archive = fixture.config.data_dir / "core.archive.sqlite"
                                with closing(
                                    sqlite3.connect(archive.as_uri() + "?mode=ro", uri=True)
                                ) as database:
                                    retained = database.execute(
                                        "SELECT count(*) FROM archive_events "
                                        "WHERE json_extract(payload,'$.source_id') "
                                        "LIKE 'synthetic-phone-context%'",
                                    ).fetchone()[0]
                                assert retained == 0
                                phone_samples += 1
                                if phone_started is None:
                                    phone_started = monotonic()
                                elapsed = monotonic() - phone_started
                                if elapsed >= 65:
                                    phone_context.update(
                                        {
                                            "source": selected["id"],
                                            "epoch": selected["epoch"],
                                            "value": value,
                                            "evidence": selected["evidence"],
                                            "retained_observations": retained,
                                            "retention": False,
                                            "sentry": "quiet authorized context",
                                            "source_ids": phone_ids,
                                            "sustained_seconds": round(elapsed, 3),
                                            "fresh_readback_samples": phone_samples,
                                        }
                                    )
                                    device(
                                        "shell",
                                        "run-as",
                                        PACKAGE,
                                        "touch",
                                        "files/software-phone-verified",
                                    )
                    if process.poll() is not None:
                        accepted(process, log_path)
                        raise RuntimeError("Native fixture ended before readiness")
                    try:
                        return (
                            json.loads(
                                device(
                                    "exec-out",
                                    "run-as",
                                    PACKAGE,
                                    "cat",
                                    "files/software-native-ready.json",
                                )
                            )
                            == {}
                        )
                    except (RuntimeError, ValueError):
                        return False

                wait(
                    ready,
                    "Native fixture did not become ready; inspect native stage receipt",
                    seconds=180,
                )
                node = "synthetic-emulated-android"

                def capabilities():
                    return {
                        c["id"]
                        for c in next(
                            (
                                item["capabilities"]
                                for item in fixture.mobile.request("snapshot", {})["nodes"]
                                if item["id"] == node
                            ),
                            [],
                        )
                    }

                timings = []
                tasks = []

                def execute(kind, target, value):
                    started = monotonic()
                    task = fixture.mobile.request(
                        "submit",
                        {
                            "text": "Synthetic selected-app acceptance",
                            "kind": kind,
                            "target": node,
                            "parameters": {"package": PACKAGE, "target": target, "value": value},
                            "retain": True,
                        },
                    )
                    if task["approval_required"]:
                        fixture.approve(task)
                    try:
                        final = fixture.wait_task(
                            task["task_id"], states=("verified", "partially_verified")
                        )
                    except AssertionError:
                        diagnostics = []
                        for line in (fixture.root / "process.log").read_text().splitlines():
                            try:
                                item = json.loads(line)
                            except ValueError:
                                continue
                            if item.get("event") == "http_request_failed":
                                diagnostics.append(
                                    {key: item[key] for key in ("category", "count")}
                                )
                        print(json.dumps({"core_request_diagnostics": diagnostics}), flush=True)
                        raise
                    assert final["evidence"] and final["result"]["success"]
                    if kind == "android_ui_set_text":
                        assert final["state"] == "verified"
                    tasks.append(
                        {
                            "task_id": task["task_id"],
                            "kind": kind,
                            "state": final["state"],
                            "evidence": final["evidence"],
                        }
                    )
                    timings.append(
                        {"kind": kind, "elapsed_ms": round((monotonic() - started) * 1000, 1)}
                    )

                wait(
                    lambda: "android.clipboard.write" in capabilities(),
                    "Foreground native clipboard capability was not advertised",
                )
                execute("android_clipboard_write", "", "Grid synthetic clipboard")
                assert tasks[-1]["state"] == "verified"
                device(
                    "shell", "run-as", PACKAGE, "touch", "files/software-native-clipboard-verified"
                )

                wait(
                    lambda: "android.media.control" in capabilities(),
                    "Native media capability not advertised",
                )
                execute("android_media_control", "", "pause")
                assert tasks[-1]["state"] == "verified"
                device("shell", "run-as", PACKAGE, "touch", "files/software-native-media-verified")

                def target_ready():
                    try:
                        device(
                            "exec-out",
                            "run-as",
                            PACKAGE,
                            "cat",
                            "files/software-native-target-ready",
                        )
                        return True
                    except RuntimeError:
                        return False

                wait(target_ready, "Synthetic target did not become ready")
                wait(
                    lambda: "android.ui.set_text" in capabilities(),
                    "Native capability was not advertised",
                )
                for kind, target, value in (
                    (
                        "android_ui_set_text",
                        PACKAGE + ":id/capability_fixture_input",
                        "Grid synthetic agenda",
                    ),
                    ("android_ui_click", PACKAGE + ":id/capability_fixture_submit", ""),
                ):
                    execute(kind, target, value)
                device("shell", "run-as", PACKAGE, "touch", "files/software-native-verified")
                wait(
                    lambda: "android.ui.set_text" not in capabilities(),
                    "Permission withdrawal did not withdraw remote capability",
                )
                device(
                    "shell", "run-as", PACKAGE, "touch", "files/software-native-withdrawal-verified"
                )
                process.wait(timeout=90)
                accepted(process, log_path)
                result = json.loads(
                    device(
                        "exec-out", "run-as", PACKAGE, "cat", "files/software-native-result.json"
                    )
                )
                nodes = fixture.mobile.request("snapshot", {})["nodes"]
                assert any(
                    n["id"] == node and n["revoked"] and n["status"] == "offline" for n in nodes
                )
                device("shell", "am", "force-stop", PACKAGE)
                instrument("NativeGridExecutionTest#processRestorationDoesNotReplayOrStartWorker")
                instrument("MobileVisualTest#productionNavigationAndUnavailableControls")
                captures = (
                    "01-oscar-home",
                    "05-automations-overview",
                    "06-worker-detail",
                    "07-create-automation",
                    "13-today-chief-of-staff",
                    "11-devices",
                    "15-preferences",
                    "14-access-modes",
                    "12-sentry-awareness",
                    "08-activity-feed",
                    "04-voice-interaction",
                )
                for name in captures:
                    guard()
                    with (output / (name + ".png")).open("wb") as capture:
                        subprocess.run(
                            [
                                str(adb),
                                "-s",
                                SERIAL,
                                "exec-out",
                                "run-as",
                                PACKAGE,
                                "cat",
                                "files/group25b/" + name + ".png",
                            ],
                            stdout=capture,
                            stderr=subprocess.DEVNULL,
                            timeout=30,
                            check=True,
                        )
                    assert (output / (name + ".png")).read_bytes().startswith(b"\x89PNG")
                receipt = {
                    "classification": "EMULATED_SYNTHETIC_ACTUAL_GRID",
                    "serial": SERIAL,
                    "avd": AVD,
                    "transport": "separate actual TLS Core and native Android Keystore proof",
                    "native_readback": result,
                    "phone_context": phone_context,
                    "tasks": tasks,
                    "timings": timings,
                    "physical_phone": "NOT_RUN",
                    "owner_biometrics": "NOT_RUN",
                    "real_accounts": "NOT_RUN",
                    "accessibility_service_enabled": True,
                    "native_navigation_captures": list(captures),
                }
            finally:
                device("reverse", "--remove", "tcp:" + port)
    finally:
        if process is not None and process.poll() is None:
            stage = device(
                "exec-out", "run-as", PACKAGE, "cat", "files/software-native-stage.txt"
            ).strip()
            if stage:
                print(json.dumps({"native_stage": stage}), flush=True)
            print(device("logcat", "-d", "-t", "300", "OscarNativeWorker:W", "*:S"), flush=True)
            process.terminate()
            process.wait(timeout=20)
        device(
            "shell",
            "settings",
            "put",
            "secure",
            "enabled_accessibility_services",
            previous_services,
        )
        device("shell", "settings", "put", "secure", "accessibility_enabled", previous_access)
        assert (
            device("shell", "settings", "get", "secure", "enabled_accessibility_services").strip()
            == previous_services
        )
        assert (
            device("shell", "settings", "get", "secure", "accessibility_enabled").strip()
            == previous_access
        )
        if not listener_was_enabled:
            device("shell", "cmd", "notification", "disallow_listener", listener)
        device(
            "shell",
            "settings",
            "put",
            "secure",
            "enabled_notification_listeners",
            previous_listeners,
        )
        assert (
            device("shell", "settings", "get", "secure", "enabled_notification_listeners").strip()
            == previous_listeners
        )
        device("uninstall", PACKAGE + ".test")
        device("uninstall", PACKAGE)
    assert receipt is not None
    assert sources == source_hashes(), "Source or APK changed during acceptance; receipt rejected"
    receipt["source_sha256"] = sources
    receipt["cleanup"] = (
        "previous Accessibility/notification settings read back; "
        "synthetic clipboard cleared; both disposable apps uninstalled"
    )
    (output / "native-grid.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
