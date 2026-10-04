"""Opt-in real laptop desktop/browser acceptance; synthetic content only."""

import argparse
import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import TimeoutExpired
from threading import Thread
from time import monotonic, sleep, time
from traceback import extract_tb
from typing import Any
from urllib.parse import parse_qs
from urllib.request import urlopen

from oscar.contracts import Epistemic, Evidence, TaskState, new_id
from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import InteractiveWorker, browser_diagnostic
from oscar.jev import Intent
from oscar.machine import MachineScope, MachineVerifier
from oscar.powershell import discover
from oscar.runtime import Runtime
from oscar.storage import Store
from oscar.transport import Dispatcher
from oscar.windows_desktop import WindowsDesktop, discover_apps


def fixture_window(windows: list[dict[str, Any]], bound: dict[str, Any], fixture: str) -> bool:
    matches = [w for w in windows if w["handle"] == bound["handle"] and w["pid"] == bound["pid"]]
    return len(matches) == 1 and fixture in matches[0]["name"]


class AcceptanceFailure(RuntimeError):
    def __init__(self, check: str, expected: Any, observed: Any):
        self.check = check
        self.expected = expected
        self.observed = observed
        super().__init__(f"{check}: expected {expected!r}; observed {observed!r}")


def require(condition: bool, check: str, expected: Any, observed: Any) -> None:
    """Only pass non-secret summaries, identities or hashes to diagnostics."""
    if not condition:
        raise AcceptanceFailure(check, expected, observed)


def text_summary(value: str) -> dict[str, Any]:
    return {"length": len(value), "sha256": hashlib.sha256(value.encode()).hexdigest()}


def wait_for_focus(
    observer: Any,
    selector: dict[str, Any],
    fixture: str,
    *,
    prior_pid: int = 0,
    timeout: float = 3.0,
) -> dict[str, Any]:
    """Read-only independent polling; never refocus, click or accept foreign focus."""
    deadline = monotonic() + timeout
    observed: dict[str, Any] = {"pid": None}

    while monotonic() < deadline:
        try:
            snapshot = observer.observe(
                {"operation": "focus_snapshot", **selector},
                timeout=deadline - monotonic(),
            )
            require(monotonic() <= deadline, "desktop.focus_readback", selector, observed)
            windows = snapshot["windows"]
            require(
                len(windows) == 2
                and all(fixture_window([window], selector, fixture) for window in windows),
                "desktop.focus_identity",
                selector,
                {"fixture_window_matches": False},
            )
            editors = snapshot["editors"]
            require(
                len(editors) == 2
                and all(
                    editor.get("runtime_id") == selector["runtime_id"]
                    and editor.get("pid") == selector["pid"]
                    and editor.get("text") is not None
                    and editor["text"].strip() == ""
                    for editor in editors
                ),
                "desktop.focus_identity",
                {**selector, "empty_editor": True},
                [
                    {
                        "pid": editor.get("pid"),
                        "runtime_id": editor.get("runtime_id"),
                        "text": text_summary(editor.get("text") or ""),
                    }
                    for editor in editors
                ],
            )
            focused = snapshot["focused"]
            observed = {key: focused.get(key) for key in ("pid", "handle", "runtime_id")}
            require(
                focused.get("pid") in {0, None, prior_pid, selector["pid"]},
                "desktop.focus_readback",
                {"target_pid": selector["pid"], "unchanged_prior_pid": prior_pid},
                observed,
            )
            if focused.get("pid") == selector["pid"]:
                return observed
        except AcceptanceFailure:
            raise
        except (OSError, PermissionError, TimeoutError, TimeoutExpired) as error:
            raise AcceptanceFailure(
                "desktop.focus_readback",
                selector,
                {**observed, "observer_error_type": type(error).__name__},
            ) from error
        sleep(min(0.1, max(0, deadline - monotonic())))
    raise AcceptanceFailure("desktop.focus_readback", selector, observed)


def failure_evidence(root: Path, error: Exception, context: dict[str, Any]) -> dict[str, Any]:
    check = (
        error.check
        if isinstance(error, AcceptanceFailure)
        else context.get("check", "precondition")
    )
    message = (
        str(error)
        if isinstance(error, AcceptanceFailure)
        else (f"{check}: {type(error).__name__}; inspect traceback locations and action receipt")
    )
    if not context.get("fixture_id") and (root / "fixture.json").exists():
        context["fixture_id"] = json.loads((root / "fixture.json").read_text(encoding="utf-8"))[
            "fixture_id"
        ]
    report = {
        "status": "FAILED",
        "root": str(root),
        "phase": check.split(".")[0],
        "check": check,
        "error_type": type(error).__name__,
        "error": message,
        "expected": error.expected if isinstance(error, AcceptanceFailure) else "check succeeds",
        "observed": error.observed if isinstance(error, AcceptanceFailure) else "exception raised",
        "traceback": [
            {"file": frame.filename, "line": frame.lineno, "function": frame.name}
            for frame in extract_tb(error.__traceback__)
        ],
        "fixture_id": context.get("fixture_id"),
        "bound_target": context.get("bound_target"),
        "stale_fixture_windows": context.get("stale_fixture_windows", []),
        "last_successful_action": context.get("last_successful_action"),
        "actions_path": str(root / "actions.json"),
        "cleanup": context.get("cleanup", {"fixture_tab": "owner review; never blindly closed"}),
    }
    if root.exists():
        (root / "failure.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


class Fixture(BaseHTTPRequestHandler):
    state = ""

    def log_message(self, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/download":
            payload = b"bounded fixture download\n"
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
        elif self.path == "/state":
            payload = json.dumps({"value": type(self).state}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        else:
            payload = b"""<!doctype html><title>OSCAR form acceptance</title>
            <form method="post" action="/submit"><label>Proof<input id="proof" name="proof"></label>
            <button id="submit">Submit</button></form>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if self.path != "/submit" or not 0 < length <= 4096:
            self.send_error(400)
            return
        type(self).state = parse_qs(self.rfile.read(length).decode())["proof"][0]
        payload = (
            b'<!doctype html><title>OSCAR accepted</title><p id="accepted">Accepted fixture</p>'
            b'<a id="download" href="/download">Download synthetic fixture</a>'
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run(root: Path, *, desktop: bool) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    fixture_id = new_id()
    fixture_name = "OSCAR-acceptance-" + fixture_id + ".txt"
    deadline = time() + 600
    (root / "fixture.json").write_text(
        json.dumps({"fixture_id": fixture_id, "fixture_name": fixture_name, "root": str(root)}),
        encoding="utf-8",
    )
    workspace = root / "workspace"
    workspace.mkdir()
    manifest = discover()
    if manifest is None:
        raise AcceptanceFailure("precondition.powershell", "available PowerShell", "unavailable")
    apps = tuple(discover_apps())
    notepad = next(
        (app for app in apps if app.available and app.name.casefold() == "notepad.exe"), None
    )
    if desktop and notepad is None:
        raise AcceptanceFailure("precondition.notepad", "registered Notepad", "unavailable")
    store = Store(root / "runtime.sqlite")
    grid = Grid(store)
    scopes = (
        "heartbeat",
        "advertise",
        "execute",
        "pause",
        "cancel",
        "files:read",
        "files:write",
        "machine:host",
        "desktop:control",
        "browser:control",
    )
    grid.register(Node("laptop-interactive", NodeRole.DESKTOP, scopes))
    session = grid.pair("laptop-interactive", scopes)
    observer = WindowsDesktop(permissions=frozenset(scopes), allowed_apps=apps)
    worker = InteractiveWorker(
        store,
        grid,
        session,
        MachineScope(
            workspace, True, (sys.executable, manifest.executable, observer.shell), max_timeout=120
        ),
        desktop=desktop,
        desktop_app_ids=(notepad.id,) if notepad else (),
        browser=True,
    )
    if worker.browser_python is None:
        diagnostic = worker.browser_probe
        store.close()
        raise AcceptanceFailure(diagnostic["category"], "available browser worker", diagnostic)
    grid.advertise(session, worker.capabilities())
    runtime = Runtime(store, grid, MachineVerifier(worker.files))
    dispatcher = Dispatcher(store, grid, session.node_id, worker.executors())
    transports = {session.node_id: (dispatcher, session)}
    records = []
    context: dict[str, Any] = {
        "fixture_id": fixture_id,
        "check": "runtime.setup",
        "cleanup": {
            "store": "open",
            "server": "not started",
            "fixture_tab": "owner review; never blindly closed",
        },
    }
    owned_editor: dict[str, Any] | None = None
    owned_text = ""

    def execute(kind: str, request: dict[str, Any]) -> dict[str, Any]:
        nonlocal owned_text
        context["check"] = kind + "." + request.get("operation", "execute")
        if time() >= deadline:
            raise AcceptanceFailure(
                "runtime.deadline", "complete within 600 seconds", "deadline elapsed"
            )
        if (
            kind == "desktop_control"
            and request["operation"]
            in {
                "mouse_click",
                "set_text",
                "key",
                "invoke",
                "close_tab",
            }
            and not fixture_window(
                observer.observe({"operation": "windows"}), request, fixture_name
            )
        ):
            raise AcceptanceFailure(
                "desktop.mutation_identity", "active owned fixture", {"fixture_matches": False}
            )
        if (
            kind == "desktop_control"
            and request["operation"]
            in {
                "mouse_click",
                "set_text",
                "key",
                "invoke",
                "close_tab",
            }
            and owned_editor is not None
        ):
            observed = observer.observe({"operation": "read", **owned_editor})
            if observed["text"].strip() != owned_text:
                raise AcceptanceFailure(
                    "desktop.mutation_content",
                    text_summary(owned_text),
                    text_summary(observed["text"].strip()),
                )
        task = runtime.create(
            Intent(
                "Gate B synthetic interactive objective",
                "capability",
                capability_kind=kind,
                parameters={"request": request},
            )
        )
        completed = runtime.run(task.id, transports)
        result = next(r for r in store.all("result") if r["task_id"] == task.id)
        require(result["status"] == "REPORTED", "runtime.reported", "REPORTED", result["status"])
        if not result["success"]:
            if kind == "browser":
                action = store.get("planned_action", task.id)
                diagnostic = browser_diagnostic(worker.outputs.pop(action["id"], ""), 1)
                raise AcceptanceFailure(
                    diagnostic["category"],
                    "successful browser execution",
                    {"kind": kind, "task_id": task.id, **diagnostic},
                )
            raise AcceptanceFailure(
                "runtime.operation",
                "successful REPORTED receipt",
                {"kind": kind, "task_id": task.id, "success": False},
            )
        require(
            completed.state == TaskState.PARTIALLY_VERIFIED,
            "runtime.state",
            TaskState.PARTIALLY_VERIFIED.value,
            completed.state.value,
        )
        action = store.get("planned_action", task.id)
        output = json.loads(worker.outputs.pop(action["id"]))
        if kind == "desktop_control" and request["operation"] == "set_text":
            owned_text = request["text"]
        elif kind == "desktop_control" and request.get("key") == "backspace":
            owned_text = ""
        records.append(
            {
                "task_id": task.id,
                "correlation_id": task.correlation_id,
                "capability": action["capability_id"],
                "operation": request.get("operation", "execute"),
                "result_status": result["status"],
                "result_sha256": json.loads(result["value"])["sha256"],
                "observed_at": time(),
            }
        )
        context["last_successful_action"] = records[-1].copy()
        (root / "actions.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        return output

    def verified(method: str, observed: bytes) -> None:
        entry = records[-1]
        evidence = Evidence(
            new_id(),
            entry["task_id"],
            entry["correlation_id"],
            "acceptance-independent-observer",
            method,
            time(),
            True,
            Epistemic.VERIFIED,
            "independent resulting state matches synthetic objective",
            content_hash=hashlib.sha256(observed).hexdigest(),
        )
        store.transition(entry["task_id"], TaskState.VERIFYING)
        store.transition(entry["task_id"], TaskState.VERIFIED, evidence=evidence)
        entry.update(
            verification_status="VERIFIED", evidence_id=evidence.id, verification_method=method
        )

    report: dict[str, Any] = {
        "platform": sys.platform,
        "observed_at": time(),
        "desktop": "UNVERIFIED",
        "fixture_id": fixture_id,
    }
    try:
        if desktop:
            previous = observer.observe({"operation": "windows"})
            report["stale_fixture_windows"] = [
                {"handle": w["handle"], "pid": w["pid"]}
                for w in previous
                if "OSCAR-acceptance-" in w["name"]
            ]
            context["stale_fixture_windows"] = report["stale_fixture_windows"]
            (workspace / fixture_name).write_bytes(b"")
            app = next(
                app
                for app in observer.apps.values()
                if app.available and app.name.casefold() == "notepad.exe"
            )
            catalog = execute("installed_app", {"operation": "catalog"})
            require(
                any(record["id"] == app.id for record in catalog),
                "desktop.catalog",
                app.id,
                {"catalog_records": len(catalog)},
            )
            launch = execute(
                "installed_app", {"operation": "launch", "app_id": app.id, "artifact": fixture_name}
            )
            target = None
            for _ in range(20):
                windows = observer.observe({"operation": "windows"})
                for window in windows:
                    if window["handle"] and fixture_name in window["name"]:
                        try:
                            observer.bind(window["handle"], window["pid"], app.id)
                            target = window
                            break
                        except (OSError, PermissionError):
                            pass
                if target:
                    break
                sleep(0.2)
            if target is None:
                raise AcceptanceFailure(
                    "desktop.fixture_window", "new bound fixture window", "not found"
                )
            bound = {"handle": target["handle"], "pid": target["pid"]}
            context["bound_target"] = bound
            execute("desktop_control", {"operation": "bind", **bound, "app_id": app.id})
            tree = execute("desktop_control", {"operation": "tree", **bound})
            editors = [
                element
                for element in tree
                if element["type"] in {"ControlType.Edit", "ControlType.Document"}
                and element["text"] in {"", "\r\n"}
            ]
            if len(editors) != 1:
                raise AcceptanceFailure(
                    "desktop.fixture_editor", {"empty_editors": 1}, {"empty_editors": len(editors)}
                )
            editor = editors[0]
            selector = {**bound, "runtime_id": editor["runtime_id"]}
            owned_editor = selector
            context["bound_target"] = selector
            context["check"] = "desktop.focus_readback"
            prior_pid = observer.observe({"operation": "focused"}).get("pid", 0)
            execute(
                "desktop_control",
                {"operation": "mouse_click", **selector, "x_fraction": 0.5, "y_fraction": 0.5},
            )
            context["check"] = "desktop.focus_readback"
            focused = wait_for_focus(observer, selector, fixture_name, prior_pid=prior_pid)
            verified("separate UIA focused-process readback", str(focused["pid"]).encode())
            proof = "OSCAR-GATE-B-" + str(int(time()))
            execute("desktop_control", {"operation": "set_text", **selector, "text": proof})
            context["check"] = "desktop.text_readback"
            independently_read = observer.observe({"operation": "read", **selector})
            require(
                independently_read["text"].strip() == proof,
                "desktop.text_readback",
                text_summary(proof),
                text_summary(independently_read["text"].strip()),
            )
            verified("separate UIA text readback", independently_read["text"].strip().encode())
            execute("desktop_control", {"operation": "key", **selector, "key": "select_all"})
            execute("desktop_control", {"operation": "key", **selector, "key": "backspace"})
            context["check"] = "desktop.empty_after_clear"
            empty = observer.observe({"operation": "read", **selector})["text"].strip()
            require(empty == "", "desktop.empty_after_clear", text_summary(""), text_summary(empty))
            verified("separate UIA empty text readback", b"")
            current = observer.observe({"operation": "tree", **bound})
            indexed = {e["runtime_id"]: e for e in current}

            def fixture_descendant(element: dict[str, Any]) -> bool:
                for _ in range(8):
                    if element["type"] == "ControlType.TabItem":
                        return fixture_name in element["name"]
                    element = indexed.get(element.get("parent_runtime_id"), {})
                    if not element:
                        break
                return False

            close_buttons = [
                e for e in current if e["name"].casefold() == "close tab" and fixture_descendant(e)
            ]
            if len(close_buttons) == 1:
                execute(
                    "desktop_control",
                    {"operation": "invoke", **bound, "runtime_id": close_buttons[0]["runtime_id"]},
                )
            elif not close_buttons:
                observed = next(
                    w
                    for w in observer.observe({"operation": "windows"})
                    if w["handle"] == bound["handle"]
                )
                require(
                    fixture_name in observed["name"],
                    "desktop.close_identity",
                    {**bound, "fixture_match": True},
                    {"fixture_match": False},
                )
                execute(
                    "desktop_control",
                    {"operation": "close_tab", **selector, "expected_title": observed["name"]},
                )
            else:
                raise AcceptanceFailure(
                    "desktop.fixture_close",
                    {"close_buttons": 1},
                    {"close_buttons": len(close_buttons)},
                )
            sleep(0.5)
            remaining = observer.observe({"operation": "windows"})
            if any(fixture_name in window["name"] for window in remaining):
                current = observer.observe({"operation": "tree", **bound})
                discard = [
                    e
                    for e in current
                    if e["name"] in {"Don't save", "Don’t save"}
                    and "InvokePatternIdentifiers.Pattern" in e["patterns"]
                ]
                if len(discard) != 1 or not any(fixture_name in e["name"] for e in current):
                    raise AcceptanceFailure(
                        "desktop.fixture_discard",
                        "one owned discard action",
                        {"discard_actions": len(discard)},
                    )
                execute(
                    "desktop_control",
                    {"operation": "invoke", **bound, "runtime_id": discard[0]["runtime_id"]},
                )
                sleep(0.5)
            context["check"] = "desktop.fixture_tab_absent"
            still_open = any(
                fixture_name in w["name"] for w in observer.observe({"operation": "windows"})
            )
            require(not still_open, "desktop.fixture_tab_absent", False, still_open)
            verified("separate UIA test-tab absence", fixture_name.encode())
            context["check"] = "desktop.fixture_file_empty"
            fixture_bytes = (workspace / fixture_name).read_bytes()
            require(fixture_bytes == b"", "desktop.fixture_file_empty", 0, len(fixture_bytes))
            (workspace / fixture_name).unlink()
            require(
                not list(workspace.iterdir()),
                "desktop.workspace_cleanup",
                {"files": 0},
                {"files": len(list(workspace.iterdir()))},
            )
            context["cleanup"]["fixture_tab"] = "owned fixture closed; empty file removed"
            report["desktop"] = {
                "status": "VERIFIED",
                "app_id": app.id,
                "source": app.source,
                "activation": app.activation,
                "catalog_records": len(catalog),
                "launch_pid": launch["pid"],
                "observed_pid": target["pid"],
                "window_handle": target["handle"],
                "runtime_id": editor["runtime_id"],
                "proof_sha256": hashlib.sha256(proof.encode()).hexdigest(),
                "verification": "separate UIA observer process readback and test-tab absence",
                "cleanup": "empty document, closed test tab, no workspace files",
            }
        # Per-run handler state prevents successful prior proof from leaking into reruns.
        handler = type("RunFixture", (Fixture,), {"state": ""})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        context["cleanup"]["server"] = "running"
        local = "http://127.0.0.1:" + str(server.server_port)
        proof = "synthetic-browser-proof-" + fixture_id
        plan = {
            "origins": [local],
            "timeout": 60,
            "max_text": 3000,
            "steps": [
                {"operation": "navigate", "url": local + "/"},
                {"operation": "fill", "selector": "#proof", "text": proof},
                {"operation": "submit", "selector": "#submit"},
                {"operation": "wait", "selector": "#accepted"},
                {
                    "operation": "download",
                    "selector": "#download",
                    "path": "fixture.txt",
                    "max_bytes": 1024,
                },
                {"operation": "inspect"},
                {"operation": "screenshot", "path": "fixture.png"},
            ],
        }
        try:
            result = execute("browser", plan)
            context["check"] = "browser.fixture_server_readback"
            with urlopen(local + "/state", timeout=5) as response:
                actual = json.load(response)
            require(
                actual["value"] == proof,
                "browser.fixture_server_readback",
                text_summary(proof),
                text_summary(actual["value"]),
            )
            context["check"] = "browser.download_readback"
            download = (workspace / "fixture.txt").read_bytes()
            require(
                download == b"bounded fixture download\n",
                "browser.download_readback",
                {
                    "bytes": len(b"bounded fixture download\n"),
                    "sha256": hashlib.sha256(b"bounded fixture download\n").hexdigest(),
                },
                {"bytes": len(download), "sha256": hashlib.sha256(download).hexdigest()},
            )
            require(
                result["observations"][0]["title"] == "OSCAR accepted",
                "browser.result_title",
                text_summary("OSCAR accepted"),
                text_summary(result["observations"][0]["title"]),
            )
            verified("independent server GET after browser submission", actual["value"].encode())
            report["browser_fixture"] = {
                "status": "VERIFIED",
                "url": local,
                "verification": "independent HTTP server state GET after browser submit",
                "artifact_sha256": hashlib.sha256(
                    (workspace / "fixture.png").read_bytes()
                ).hexdigest(),
            }
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            context["cleanup"]["server"] = (
                "closed" if not thread.is_alive() else "thread still alive"
            )
        plan = {
            "origins": ["https://example.com"],
            "timeout": 60,
            "max_text": 3000,
            "steps": [
                {"operation": "navigate", "url": "https://example.com/"},
                {"operation": "inspect"},
            ],
        }
        public = execute("browser", plan)["observations"][0]
        context["check"] = "browser.public_source_readback"
        with urlopen("https://example.com/", timeout=15) as response:
            source = response.read(64_000).decode()
        require(
            public["url"] == "https://example.com/",
            "browser.public_url",
            text_summary("https://example.com/"),
            text_summary(public["url"]),
        )
        marker = "This domain is for use in documentation examples"
        require(
            public["title"] == "Example Domain",
            "browser.public_title",
            text_summary("Example Domain"),
            text_summary(public["title"]),
        )
        require(marker in public["text"], "browser.public_marker", True, False)
        require(
            "<title>Example Domain</title>" in source, "browser.public_source_title", True, False
        )
        require(marker in source, "browser.public_source_marker", True, False)
        verified("independent HTTPS title and content marker", source.encode())
        report["browser_public"] = {
            "status": "VERIFIED",
            "url": public["url"],
            "title": public["title"],
            "verification": "independent HTTPS title/marker read",
        }
        report["actions"] = records
        return report
    except Exception as error:
        context["cleanup"]["store"] = "closing"
        failure_evidence(root, error, context)
        raise
    finally:
        store.close()
        if (root / "failure.json").exists():
            saved = json.loads((root / "failure.json").read_text(encoding="utf-8"))
            saved["cleanup"]["store"] = "closed"
            (root / "failure.json").write_text(json.dumps(saved, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--desktop", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit(
            "precondition.platform: expected Windows; observed non-Windows; no actions started"
        )
    root = args.root.resolve()
    print("Artifact/evidence root: " + str(root), flush=True)
    if root.exists():
        raise SystemExit(
            f"precondition.root: expected fresh evidence root; observed existing {root}; "
            "no actions started; choose a fresh timestamp root"
        )
    try:
        report = run(root, desktop=args.desktop)
    except Exception as error:
        failure = root / "failure.json"
        report = (
            json.loads(failure.read_text(encoding="utf-8"))
            if failure.exists()
            else failure_evidence(root, error, {"check": "precondition.setup"})
        )
        print(json.dumps(report, indent=2))
        return 1
    (args.root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
