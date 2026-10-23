"""Typed desktop/browser capabilities composed with the existing machine Worker."""

import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path
from threading import Thread
from time import time
from typing import Any

from .browser_profiles import BrowserProfiles
from .capabilities import Cancellation
from .contracts import Action, Capability, Result, new_id
from .machine import MachineWorker

# A fixed OSCAR package entrypoint: source anchoring is separate from artifact cwd.
# -I excludes cwd/user-site/PYTHONPATH; dependencies still come from this interpreter.
# Importlib loads our package with its normal __path__, without changing sys.path.
BROWSER_BOOTSTRAP = """
import importlib, importlib.util, json, sys
from pathlib import Path
try:
    package = Path(sys.argv.pop(1))
    spec = importlib.util.spec_from_file_location(
        "oscar", package / "__init__.py", submodule_search_locations=[str(package)])
    if spec is None or spec.loader is None:
        raise ImportError("package unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules["oscar"] = module
    spec.loader.exec_module(module)
    worker = importlib.import_module("oscar.browser_worker")
except Exception:
    print(json.dumps({"category": "browser.import", "error_type": "ImportError"}))
    raise SystemExit(1)
sys.argv[0] = "oscar.browser_worker"
raise SystemExit(worker.main())
"""

BROWSER_CATEGORIES = frozenset(
    {
        "browser.ready",
        "browser.import",
        "browser.worker_launch",
        "browser.playwright_unavailable",
        "browser.chromium_unavailable",
        "browser.playwright_launch",
        "browser.plan_execution",
    }
)
BROWSER_PREFLIGHT_TIMEOUT = 30


def browser_command(executable: str, arguments: list[str]) -> list[str]:
    """Invoke only our fixed browser module; cwd stays the authorized artifact root."""
    return [
        executable,
        "-I",
        "-c",
        BROWSER_BOOTSTRAP,
        str(Path(__file__).resolve().parent),
        *arguments,
    ]


def browser_diagnostic(output: str, code: int) -> dict[str, Any]:
    """Retain categories/metadata only, never arbitrary subprocess/page/exception text."""
    category, error_type = "browser.worker_launch", "Exception"
    try:
        record = json.loads(output) if len(output.encode()) <= 4096 else {}
        if isinstance(record, dict):
            if record.get("category") in BROWSER_CATEGORIES:
                category = record["category"]
            if record.get("error_type") in {
                "ImportError",
                "ModuleNotFoundError",
                "OSError",
                "FileNotFoundError",
                "ValueError",
                "PermissionError",
                "RuntimeError",
                "TimeoutError",
                "Error",
            }:
                error_type = record["error_type"]
    except (ValueError, TypeError):
        pass
    if code and category == "browser.ready":
        category = "browser.worker_launch"
    return {
        "category": category,
        "error_type": error_type,
        "exit_code": code,
        "output_bytes": len(output.encode()),
    }


def browser_preflight(executable: str, workspace: Path) -> dict[str, Any]:
    """Probe the same source-anchored module/interpreter/cwd as real execution."""
    env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "TEMP", "TMP") if k in os.environ}
    job: Any = None
    process = None
    reader: Thread | None = None
    captured = bytearray()
    try:
        argv = browser_command(executable, ["--probe"])
        if os.name == "nt":
            from .windows_process import WindowsJob

            job = WindowsJob()
            process = job.start(
                argv, cwd=workspace, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
        else:
            process = subprocess.Popen(
                argv,
                cwd=workspace,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        stream = process.stdout
        if stream is None:
            raise OSError("probe output unavailable")
        reader = Thread(target=lambda: captured.extend(stream.read(4097)), daemon=True)
        reader.start()
        process.wait(timeout=BROWSER_PREFLIGHT_TIMEOUT)
        reader.join(timeout=1)
        if reader.is_alive() or len(captured) > 4096:
            return browser_diagnostic("", 1)
        diagnostic = browser_diagnostic(captured.decode(errors="replace"), process.returncode)
        return diagnostic
    except subprocess.TimeoutExpired:
        return {**browser_diagnostic("", 1), "error_type": "TimeoutError"}
    except (OSError, subprocess.SubprocessError):
        return browser_diagnostic("", 1)
    finally:
        if job:
            job.close()
        elif process and process.poll() is None:
            posix: Any = os
            signals: Any = signal
            posix.killpg(process.pid, signals.SIGKILL)
        if process:
            process.wait(timeout=3)
            if reader:
                reader.join(timeout=1)
            if process.stdout:
                process.stdout.close()


def browser_available(executable: str, workspace: Path) -> bool:
    return bool(browser_preflight(executable, workspace)["category"] == "browser.ready")


class InteractiveWorker(MachineWorker):
    def clipboard_granted(self) -> bool:
        try:
            self.check_permission("desktop:clipboard")
            return True
        except (PermissionError, KeyError):
            return False

    def __init__(
        self,
        *args: Any,
        desktop: bool = False,
        browser: bool = False,
        desktop_app_ids: tuple[str, ...] = (),
        browser_profiles: BrowserProfiles | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.browser_profiles = browser_profiles
        self.desktop: Any = None
        self.browser_python = (
            next(
                (
                    path
                    for path in self.scope.allowed_executables
                    if Path(path).name.lower() in {"python.exe", "python3", "python"}
                ),
                None,
            )
            if browser and self.scope.trusted_host_execution
            else None
        )
        self.browser_probe = browser_diagnostic("", 1)
        if self.browser_python:
            self.browser_probe = browser_preflight(self.browser_python, self.scope.root)
            if self.browser_probe["category"] != "browser.ready":
                self.browser_python = None
        if desktop and os.name == "nt" and self.scope.trusted_host_execution:
            from .windows_desktop import WindowsDesktop, discover_apps

            catalog = tuple(discover_apps())
            desktop_permissions = {"machine:host", "desktop:control"}
            if self.clipboard_granted():
                desktop_permissions.add("desktop:clipboard")
            adapter = WindowsDesktop(
                permissions=frozenset(desktop_permissions),
                allowed_apps=tuple(app for app in catalog if app.id in desktop_app_ids),
                catalog_apps=catalog,
                workspace=self.scope.root,
            )
            if adapter.shell in self.scope.allowed_executables:
                self.desktop = adapter

    def capabilities(self) -> list[Capability]:
        caps = super().capabilities()
        if getattr(self, "desktop", None):
            caps += [
                Capability(
                    "machine.desktop",
                    "machine.desktop",
                    "Bounded Windows UIA",
                    "machine",
                    self.session.node_id,
                    ("machine:host", "desktop:control"),
                    "desktop_control",
                    "metadata",
                    "high",
                ),
                Capability(
                    "machine.apps",
                    "machine.apps",
                    "Registered installed apps",
                    "machine",
                    self.session.node_id,
                    ("machine:host", "desktop:control"),
                    "installed_app",
                    "metadata",
                    "high",
                ),
            ]
            if "desktop:clipboard" in self.desktop.permissions and self.clipboard_granted():
                caps.append(
                    Capability(
                        "machine.clipboard",
                        "machine.clipboard",
                        "Explicit clipboard write/readback",
                        "machine",
                        self.session.node_id,
                        ("machine:host", "desktop:control", "desktop:clipboard"),
                        "desktop_clipboard",
                        "metadata",
                        "high",
                    )
                )
        if getattr(self, "browser_python", None):
            caps.append(
                Capability(
                    "machine.browser",
                    "machine.browser",
                    "Isolated typed browser",
                    "machine",
                    self.session.node_id,
                    ("machine:host", "browser:control"),
                    "browser",
                    "metadata",
                    "high",
                )
            )
        return caps

    def check(self, action: Action, cancellation: Cancellation) -> None:
        super().check(action, cancellation)
        if action.capability_id == "machine.browser" and "account_id" in action.parameters:
            if self.browser_profiles is None:
                raise PermissionError("account browser storage unavailable")
            self.browser_profiles.check(action.parameters)

    def execute(self, action: Action, cancellation: Cancellation) -> Result:
        if action.capability_id not in {
            "machine.apps",
            "machine.desktop",
            "machine.clipboard",
            "machine.browser",
        }:
            return super().execute(action, cancellation)
        cap = next((c for c in self.capabilities() if c.id == action.capability_id), None)
        if cap is None:
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                action.capability_id,
                False,
                error="machine_blocked:capability_unavailable",
            )
        if not self.authorize_execution(action, cap):
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                cap.id,
                False,
                error="machine_blocked:policy",
            )
        self.check(action, cancellation)
        self.checkpoint(action, "interactive-started", 0)
        try:
            request = action.parameters["request"]
            if cap.id == "machine.apps":
                if request == {"operation": "catalog"}:
                    output = json.dumps(self.desktop.catalog())
                elif (
                    set(request) in ({"operation", "app_id"}, {"operation", "app_id", "artifact"})
                    and request["operation"] == "launch"
                ):
                    process = self.desktop.launch(
                        request["app_id"], artifact=request.get("artifact")
                    )
                    output = json.dumps(
                        {"pid": process.pid, "app_id": request["app_id"], "observed_at": time()}
                    )
                else:
                    raise ValueError("typed app operation required")
            elif cap.id in {"machine.desktop", "machine.clipboard"}:
                if request.get("operation") in {"clipboard_write", "clipboard_read"}:
                    if cap.id != "machine.clipboard":
                        raise PermissionError("clipboard requires its separately scoped capability")
                    self.check_permission("desktop:clipboard")
                elif cap.id == "machine.clipboard":
                    raise PermissionError("clipboard capability cannot execute UIA operations")
                if set(request) == {"operation", "handle", "pid", "app_id"} and (
                    request["operation"] == "bind"
                ):
                    self.desktop.bind(request["handle"], request["pid"], request["app_id"])
                    output = json.dumps({"target_bound": True})
                else:
                    code, output = self.run_command(
                        action,
                        cancellation,
                        self.desktop.command(request),
                        ".",
                        15,
                        input_data=self.desktop.input(request),
                    )
                    self.outputs[action.id] = output
                    if code:
                        raise ValueError("UI Automation operation failed")
            else:
                from .browser_worker import validate

                validate(request)
                assert self.browser_python is not None
                arguments = ["--request", json.dumps(request)]
                if "account_id" in action.parameters:
                    if self.browser_profiles is None:
                        raise PermissionError("account browser storage unavailable")
                    with self.browser_profiles.open(action.parameters, self.scope.root) as profile:
                        code, output = self.run_command(
                            action,
                            cancellation,
                            browser_command(
                                self.browser_python, [*arguments, "--profile", str(profile)]
                            ),
                            ".",
                            request["timeout"],
                        )
                else:
                    if set(action.parameters) - {"request", "timeout"}:
                        raise ValueError("unsupported browser parameters")
                    code, output = self.run_command(
                        action,
                        cancellation,
                        browser_command(self.browser_python, arguments),
                        ".",
                        request["timeout"],
                    )
                if code:
                    diagnostic = browser_diagnostic(output, code)
                    self.outputs[action.id] = json.dumps(diagnostic)
                    return Result(
                        new_id(),
                        action.id,
                        action.task_id,
                        action.correlation_id,
                        cap.id,
                        False,
                        error=diagnostic["category"],
                    )
            if len(output.encode()) > self.scope.max_output:
                raise ValueError("interactive output bound exceeded")
            self.outputs[action.id] = output
            self.checkpoint(action, "interactive-reported", 1)
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                cap.id,
                True,
                value=json.dumps(
                    {
                        "sha256": hashlib.sha256(output.encode()).hexdigest(),
                        "bytes": len(output.encode()),
                    }
                ),
            )
        except TimeoutError:
            error = "command_timeout"
        except (KeyError, OSError, ValueError, PermissionError):
            error = "machine_scope_or_operation_rejected"
        return Result(
            new_id(), action.id, action.task_id, action.correlation_id, cap.id, False, error=error
        )
