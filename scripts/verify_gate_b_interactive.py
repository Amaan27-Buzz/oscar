"""Opt-in real laptop desktop/browser acceptance; synthetic content only."""

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import sleep, time
from typing import Any
from urllib.parse import parse_qs
from urllib.request import urlopen

from oscar.contracts import Epistemic, Evidence, TaskState, new_id
from oscar.grid import Grid, Node, NodeRole
from oscar.interactive_worker import InteractiveWorker
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
        raise RuntimeError("PowerShell precondition failed; no tasks started")
    apps = tuple(discover_apps())
    notepad = next(
        (app for app in apps if app.available and app.name.casefold() == "notepad.exe"), None
    )
    if desktop and notepad is None:
        raise RuntimeError("registered Notepad precondition failed; no desktop mutation")
    if importlib.util.find_spec("playwright") is None:
        raise RuntimeError("Playwright precondition failed; install the pinned browser extra")
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
    grid.advertise(session, worker.capabilities())
    runtime = Runtime(store, grid, MachineVerifier(worker.files))
    dispatcher = Dispatcher(store, grid, session.node_id, worker.executors())
    transports = {session.node_id: (dispatcher, session)}
    records = []
    owned_editor: dict[str, Any] | None = None
    owned_text = ""

    def execute(kind: str, request: dict[str, Any]) -> dict[str, Any]:
        nonlocal owned_text
        if time() >= deadline:
            raise TimeoutError("interactive acceptance deadline exceeded")
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
            raise PermissionError("fixture is no longer active; no owner-window mutation")
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
                raise PermissionError("fixture content changed outside this run; no mutation")
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
        assert result["status"] == "REPORTED", result
        if not result["success"]:
            action = store.get("planned_action", task.id)
            raise RuntimeError(
                f"interactive operation failed: {kind}: {result['error']}: "
                + worker.outputs.get(action["id"], "")
            )
        assert completed.state == TaskState.PARTIALLY_VERIFIED
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
                "result_status": result["status"],
                "result_sha256": json.loads(result["value"])["sha256"],
                "observed_at": time(),
            }
        )
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
            (workspace / fixture_name).write_bytes(b"")
            app = next(
                app
                for app in observer.apps.values()
                if app.available and app.name.casefold() == "notepad.exe"
            )
            catalog = execute("installed_app", {"operation": "catalog"})
            assert any(record["id"] == app.id for record in catalog)
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
                raise RuntimeError("no independently identified new Notepad window; no mutation")
            bound = {"handle": target["handle"], "pid": target["pid"]}
            execute("desktop_control", {"operation": "bind", **bound, "app_id": app.id})
            tree = execute("desktop_control", {"operation": "tree", **bound})
            editors = [
                element
                for element in tree
                if element["type"] in {"ControlType.Edit", "ControlType.Document"}
                and element["text"] in {"", "\r\n"}
            ]
            if len(editors) != 1:
                raise RuntimeError("new empty Notepad editor is ambiguous; no mutation")
            editor = editors[0]
            selector = {**bound, "runtime_id": editor["runtime_id"]}
            owned_editor = selector
            execute(
                "desktop_control",
                {"operation": "mouse_click", **selector, "x_fraction": 0.5, "y_fraction": 0.5},
            )
            focused = observer.observe({"operation": "focused"})
            assert focused["pid"] == target["pid"]
            verified("separate UIA focused-process readback", str(focused["pid"]).encode())
            proof = "OSCAR-GATE-B-" + str(int(time()))
            execute("desktop_control", {"operation": "set_text", **selector, "text": proof})
            independently_read = observer.observe({"operation": "read", **selector})
            assert independently_read["text"].strip() == proof
            verified("separate UIA text readback", independently_read["text"].strip().encode())
            execute("desktop_control", {"operation": "key", **selector, "key": "select_all"})
            execute("desktop_control", {"operation": "key", **selector, "key": "backspace"})
            assert observer.observe({"operation": "read", **selector})["text"].strip() == ""
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
                assert fixture_name in observed["name"]
                execute(
                    "desktop_control",
                    {"operation": "close_tab", **selector, "expected_title": observed["name"]},
                )
            else:
                raise RuntimeError("test-tab close is ambiguous; manual cleanup required")
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
                    raise RuntimeError("close/discard requires manual review")
                execute(
                    "desktop_control",
                    {"operation": "invoke", **bound, "runtime_id": discard[0]["runtime_id"]},
                )
                sleep(0.5)
            assert not any(
                fixture_name in w["name"] for w in observer.observe({"operation": "windows"})
            )
            verified("separate UIA test-tab absence", fixture_name.encode())
            assert (workspace / fixture_name).read_bytes() == b""
            (workspace / fixture_name).unlink()
            assert not list(workspace.iterdir())
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
            with urlopen(local + "/state", timeout=5) as response:
                actual = json.load(response)
            assert actual["value"] == proof
            assert (workspace / "fixture.txt").read_bytes() == b"bounded fixture download\n"
            assert result["observations"][0]["title"] == "OSCAR accepted"
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
        with urlopen("https://example.com/", timeout=15) as response:
            source = response.read(64_000).decode()
        assert public["url"] == "https://example.com/"
        marker = "This domain is for use in documentation examples"
        assert public["title"] == "Example Domain" and marker in public["text"]
        assert "<title>Example Domain</title>" in source
        assert marker in source
        verified("independent HTTPS title and content marker", source.encode())
        report["browser_public"] = {
            "status": "VERIFIED",
            "url": public["url"],
            "title": public["title"],
            "verification": "independent HTTPS title/marker read",
        }
        report["actions"] = records
        return report
    finally:
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--desktop", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("real Windows desktop acceptance requires Windows")
    root = args.root.resolve()
    print("Artifact/evidence root: " + str(root), flush=True)
    if root.exists():
        raise SystemExit("acceptance root already exists; choose a fresh timestamp root")
    try:
        report = run(root, desktop=args.desktop)
    except Exception as error:
        report = {
            "status": "FAILED",
            "error_type": type(error).__name__,
            "error": str(error),
            "root": str(root),
            "cleanup": "only owned browser/server resources; fixture tab may require owner review",
        }
        if root.exists():
            (root / "failure.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1
    (args.root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
