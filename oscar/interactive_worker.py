"""Typed desktop/browser capabilities composed with the existing machine Worker."""

import hashlib
import json
import os
from pathlib import Path
from time import time
from typing import Any

from .capabilities import Cancellation
from .contracts import Action, Capability, Result, new_id
from .machine import MachineWorker


class InteractiveWorker(MachineWorker):
    def __init__(self, *args: Any, desktop: bool = False, browser: bool = False, **kwargs: Any):
        super().__init__(*args, **kwargs)
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
        if desktop and os.name == "nt" and self.scope.trusted_host_execution:
            from .windows_desktop import WindowsDesktop, discover_apps

            adapter = WindowsDesktop(
                permissions=frozenset({"machine:host", "desktop:control"}),
                allowed_apps=tuple(discover_apps()),
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

    def execute(self, action: Action, cancellation: Cancellation) -> Result:
        if action.capability_id not in {"machine.apps", "machine.desktop", "machine.browser"}:
            return super().execute(action, cancellation)
        cap = next(c for c in self.capabilities() if c.id == action.capability_id)
        if not self.policy.evaluate(cap.name, cap.permissions, frozenset(cap.permissions)).allowed:
            return Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                cap.id,
                False,
                error="machine_blocked:policy",
            )
        self.owners[action.id] = self.store.task(action.task_id).lease_id or ""
        self.check(action, cancellation)
        self.checkpoint(action, "interactive-started", 0)
        try:
            request = action.parameters["request"]
            if cap.id == "machine.apps":
                if request == {"operation": "catalog"}:
                    output = json.dumps(self.desktop.catalog())
                elif set(request) == {"operation", "app_id"} and request["operation"] == "launch":
                    process = self.desktop.launch(request["app_id"])
                    output = json.dumps(
                        {"pid": process.pid, "app_id": request["app_id"], "observed_at": time()}
                    )
                else:
                    raise ValueError("typed app operation required")
            elif cap.id == "machine.desktop":
                if set(request) == {"operation", "handle", "pid", "app_id"} and (
                    request["operation"] == "bind"
                ):
                    self.desktop.bind(request["handle"], request["pid"], request["app_id"])
                    output = json.dumps({"target_bound": True})
                else:
                    code, output = self.run_command(
                        action, cancellation, self.desktop.command(request), ".", 15
                    )
                    if code:
                        raise ValueError("UI Automation operation failed")
            else:
                from .browser_worker import validate

                validate(request)
                assert self.browser_python is not None
                code, output = self.run_command(
                    action,
                    cancellation,
                    [
                        self.browser_python,
                        str(Path(__file__).with_name("browser_worker.py")),
                        "--request",
                        json.dumps(request),
                    ],
                    ".",
                    request["timeout"],
                )
                if code:
                    raise ValueError("browser operation failed")
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
