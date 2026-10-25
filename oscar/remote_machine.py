"""Outbound machine effects under canonical Core delivery authority, never a second Core."""

import json
import math
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import Event, Thread
from time import monotonic
from typing import Any, TextIO

from .browser_profiles import BrowserProfiles
from .browser_worker import validate as validate_browser
from .capabilities import Cancellation
from .contracts import Action, Capability, Result, record
from .grid import SessionHandle
from .interactive_worker import InteractiveWorker
from .machine import MachineScope
from .remote_worker import Client, RemoteCancellation, RemoteWorker

# Core admits the contract; the native Worker additionally checks installed executors/local grants.
REMOTE_MACHINE_CAPABILITIES = {
    "machine.files.list": ("directory_list", ("files:read",), "low"),
    "machine.files.search": ("file_search", ("files:read",), "low"),
    "machine.executables": ("executable_discovery", ("files:read",), "low"),
    "machine.command": ("terminal_command", ("machine:host",), "high"),
    "machine.git": ("git_operation", ("machine:host",), "high"),
    "machine.repository": ("repository_task", ("machine:host",), "high"),
    "machine.powershell": ("powershell", ("machine:host",), "high"),
    "machine.desktop": ("desktop_control", ("machine:host", "desktop:control"), "high"),
    "machine.apps": ("installed_app", ("machine:host", "desktop:control"), "high"),
    "machine.visual": (
        "visual_control",
        ("machine:host", "desktop:control", "desktop:capture"),
        "high",
    ),
    "machine.screen": (
        "screen_capture",
        ("machine:host", "desktop:control", "desktop:capture", "screen:retain", "files:write"),
        "high",
    ),
    "machine.clipboard": (
        "desktop_clipboard",
        ("machine:host", "desktop:control", "desktop:clipboard"),
        "high",
    ),
    "machine.browser": ("browser", ("machine:host", "browser:control"), "high"),
    **{
        "machine.agent." + name: ("coding", ("machine:host",), "high")
        for name in ("codex", "claude-code", "opencode", "gemini-cli")
    },
}


def machine_readback(capability: str, parameters: dict[str, Any]) -> dict[str, Any] | None:
    """Derive only a read of the exact reviewed destination, never another effect."""
    spec = REMOTE_MACHINE_CAPABILITIES.get(capability)
    verification = parameters.get("verification")
    if spec and spec[0] in {"coding", "terminal_command"} and isinstance(verification, dict):
        if set(verification) == {"path", "content"}:
            return {"path": verification["path"]}
    request = parameters.get("request")
    if not isinstance(request, dict):
        return None
    if capability == "machine.apps" and set(request) == {"operation", "query"}:
        if request["operation"] == "targets":
            return {"request": request}
    if capability == "machine.desktop" and request.get("operation") == "set_text_checked":
        if set(request) == {"operation", "handle", "pid", "runtime_id", "text", "expected_text"}:
            return {"operation": "read", **{k: request[k] for k in ("handle", "pid", "runtime_id")}}
    if capability == "machine.clipboard" and set(request) == {"operation", "text"}:
        if request["operation"] == "clipboard_write":
            return {"operation": "clipboard_read"}
    if capability == "machine.browser" and "verification" in parameters:
        expected = parameters["verification"]
        return {
            **{k: parameters[k] for k in ("account_id", "account_generation") if k in parameters},
            "request": {
                "origins": request["origins"],
                "steps": [
                    {"operation": "navigate", "url": expected["url"]},
                    {"operation": "read_text", "selector": expected["selector"]},
                ],
                "timeout": min(request["timeout"], 15),
                "max_text": min(request["max_text"], 8192),
            },
        }
    return None


def validate_remote_machine(kind: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Bound transport input; existing native executors own final operation/path validation."""
    if kind not in {item[0] for item in REMOTE_MACHINE_CAPABILITIES.values()}:
        raise ValueError("unknown remote machine capability")
    if (
        not isinstance(parameters, dict)
        or len(json.dumps(parameters, allow_nan=False).encode()) > 16_000
    ):
        raise ValueError("bounded typed machine parameters required")
    fields = {
        "directory_list": ({"cwd"}, set()),
        "file_search": ({"cwd", "pattern"}, {"pattern"}),
        "executable_discovery": (set(), set()),
        "terminal_command": ({"argv", "cwd", "timeout", "verification"}, {"argv"}),
        "git_operation": ({"operation", "name", "message", "cwd", "timeout"}, {"operation"}),
        "repository_task": ({"path", "content", "message"}, {"path", "content", "message"}),
        "coding": ({"arguments", "cwd", "timeout", "verification"}, {"arguments"}),
        "powershell": ({"request", "cwd", "timeout"}, {"request"}),
        "desktop_control": ({"request"}, {"request"}),
        "installed_app": ({"request"}, {"request"}),
        "desktop_clipboard": ({"request"}, {"request"}),
        "visual_control": ({"request"}, {"request"}),
        "screen_capture": ({"request"}, {"request"}),
        "browser": ({"request", "account_id", "account_generation", "verification"}, {"request"}),
    }
    allowed, required = fields[kind]
    if not required <= set(parameters) <= allowed:
        raise ValueError("exact typed machine operation required")
    if "timeout" in parameters and (
        type(parameters["timeout"]) not in {int, float}
        or not math.isfinite(parameters["timeout"])
        or not 0 < parameters["timeout"] <= 120
    ):
        raise ValueError("bounded remote timeout required")
    for field in (
        "cwd",
        "pattern",
        "path",
        "content",
        "message",
        "operation",
        "name",
        "account_id",
    ):
        if field in parameters and (
            not isinstance(parameters[field], str) or "\x00" in parameters[field]
        ):
            raise ValueError("text machine parameters required")
    for field in ("argv", "arguments"):
        if field in parameters and (
            not isinstance(parameters[field], list)
            or len(parameters[field]) > 64
            or any(not isinstance(arg, str) or "\x00" in arg for arg in parameters[field])
            or field == "argv"
            and not parameters[field]
        ):
            raise ValueError("bounded native argument vector required")
    if "request" in parameters and not isinstance(parameters["request"], dict):
        raise ValueError("structured native request required")
    if kind == "installed_app":
        request = parameters["request"]
        if request.get("operation") == "targets":
            if (
                set(request) != {"operation", "query"}
                or not isinstance(request["query"], str)
                or len(request["query"]) > 80
                or "\x00" in request["query"]
            ):
                raise ValueError("bounded registered-app query required")
    if kind in {"coding", "terminal_command"} and "verification" in parameters:
        from .windows_files import WindowsScopedFiles

        expected = parameters["verification"]
        if (
            not isinstance(expected, dict)
            or set(expected) != {"path", "content"}
            or not isinstance(expected["path"], str)
            or not 1 <= len(expected["path"]) <= 240
            or not isinstance(expected["content"], str)
            or len(expected["content"].encode()) > 8192
        ):
            raise ValueError("bounded exact artifact verification required")
        WindowsScopedFiles.parts(expected["path"])
    if kind == "browser":
        if ("account_id" in parameters) != ("account_generation" in parameters):
            raise ValueError("exact browser account identity required")
        if "account_id" in parameters and (
            not parameters["account_id"]
            or type(parameters["account_generation"]) is not int
            or parameters["account_generation"] < 1
        ):
            raise ValueError("current browser account generation required")
        validate_browser(parameters["request"])
        if "verification" in parameters:
            expected = parameters["verification"]
            if (
                not isinstance(expected, dict)
                or set(expected) != {"url", "selector", "text"}
                or not isinstance(expected["text"], str)
                or len(expected["text"]) > 8192
                or len(expected["text"]) > parameters["request"]["max_text"]
            ):
                raise ValueError("exact bounded browser text verification required")
            readback = machine_readback("machine.browser", parameters)
            assert readback is not None
            validate_browser(readback["request"])
    return parameters


class RemoteEffects(InteractiveWorker):
    """Reuse native effects while every execution fence is checked by the real remote Core."""

    def __init__(
        self,
        client: Client,
        scope: MachineScope,
        guard: Callable[[], None],
        *,
        desktop: bool = False,
        browser: bool = False,
        desktop_app_ids: tuple[str, ...] = (),
    ):
        self.remote_grants = frozenset(client.session["scopes"])
        self.guard, self.active = guard, False
        self._last_running_check = 0.0
        # This is the existing remote credential, never a generated local execution session.
        session = SessionHandle(
            client.session["session_id"],
            client.session["node_id"],
            client.session["token"],
        )
        super().__init__(
            None,
            None,
            session,
            scope,
            desktop=desktop,
            browser=browser,
            desktop_app_ids=desktop_app_ids,
        )

    def authorize_execution(self, action: Action, cap: Capability) -> bool:
        if not set(cap.permissions) <= self.remote_grants:
            return False
        self.guard()
        return True

    def check(self, action: Action, cancellation: Cancellation) -> None:
        if not isinstance(cancellation, RemoteCancellation):
            raise PermissionError("remote Core cancellation required")
        cancellation.check()

    def check_running(self, action: Action, cancellation: Cancellation) -> None:
        # Bound running-child revocation polling without consuming Core admission at 50 Hz.
        if monotonic() - self._last_running_check >= 1:
            self.check(action, cancellation)
            self._last_running_check = monotonic()

    def check_permission(self, permission: str) -> None:
        if permission not in self.remote_grants:
            raise PermissionError("native execution scope unavailable")
        if self.active:
            self.guard()

    def checkpoint(self, action: Action, step: str, fraction: float) -> None:
        if step != "process-running":  # Running checks already refresh Core authority each second.
            self.guard()

    def controls(self, task_id: str) -> dict[str, Any]:
        return {"paused": False}

    def execution_cancellation(self, action: Action, cancellation: Cancellation) -> Cancellation:
        return RemoteCancellation(self.guard)

    def audit_execution(self, action: Action, metadata: dict[str, Any]) -> None:
        # The Core records the authenticated result. No private output or shadow task ledger.
        self.guard()


class RemoteMachine(RemoteWorker):
    """Existing outbound poll/journal protocol with actual installed native executors."""

    capability_ids = RemoteWorker.capability_ids | frozenset(REMOTE_MACHINE_CAPABILITIES)

    def __init__(
        self,
        client: Client,
        scope: MachineScope,
        workspace_id: str,
        journal: Path,
        *,
        capabilities: tuple[str, ...],
        desktop: bool = False,
        browser: bool = False,
        desktop_app_ids: tuple[str, ...] = (),
        profile_root: Path | None = None,
        local_authorize: Callable[[Action], bool] | None = None,
    ):
        # Base initialization owns only the established execution journal and scoped files.
        super().__init__(client, scope.root, workspace_id, journal, local_authorize=local_authorize)
        try:
            self._active_delivery: dict[str, Any] | None = None
            self.effects = RemoteEffects(
                client,
                scope,
                self._guard,
                desktop=desktop,
                browser=browser,
                desktop_app_ids=desktop_app_ids,
            )
            if profile_root is not None:
                self.effects.browser_profiles = BrowserProfiles(
                    None, profile_root, authorize=self._account_guard
                )
            actual = {cap.id: cap for cap in self.effects.capabilities()}
            if (
                not capabilities
                or len(set(capabilities)) != len(capabilities)
                or any(identifier not in actual for identifier in capabilities)
            ):
                raise PermissionError(
                    "only explicitly enabled installed capabilities may be shared"
                )
            if any(
                not set(actual[identifier].permissions) <= self.effects.remote_grants
                for identifier in capabilities
            ):
                raise PermissionError("capability exceeds current enrolled native scope")
            self.allowed = frozenset(capabilities)
        except BaseException:
            super().close()
            raise

    def advertise(self) -> None:
        caps = [record(cap) for cap in self.effects.capabilities() if cap.id in self.allowed]
        self.client.request("advertise", {"workspace": self.workspace_id, "capabilities": caps})
        self.status = "online"

    def validate_effect(self, action: Action, delivery: dict[str, Any]) -> None:
        if action.capability_id in {"machine.files.read", "machine.files.write"}:
            return super().validate_effect(action, delivery)
        spec = REMOTE_MACHINE_CAPABILITIES.get(action.capability_id)
        if spec is None:
            raise PermissionError("native capability is not shared")
        validate_remote_machine(spec[0], action.parameters)
        if spec[0] in {"coding", "terminal_command"} and "verification" in action.parameters:
            if (
                "machine.files.read" not in self.allowed
                or "files:read" not in self.effects.remote_grants
            ):
                raise PermissionError("artifact verification requires separately shared file read")
        expected = (
            machine_readback(action.capability_id, action.parameters)
            if delivery["kind"] == "readback"
            else action.parameters
        )
        if expected is None or delivery["parameters"] != expected:
            raise PermissionError("only the exact reviewed destination can be read back")
        full = (delivery.get("authority") or {}).get("mode") == "full"
        if spec[2] != "low" and not delivery["approved"] and not full:
            raise PermissionError("exact owner approval or current Full Access is required")

    def _guard(self) -> None:
        delivery = self._active_delivery
        if delivery is None:
            raise PermissionError("native effect has no active Core delivery")
        self.validate(delivery)
        check = {"delivery_id": delivery["id"]}
        expected: dict[str, Any] = {"authorized": True}
        if delivery.get("authority") is not None:
            check["authority"] = delivery["authority"]
            expected["authority"] = delivery["authority"]
        if self.client.request("check", check) != expected:
            raise PermissionError("current Core lease and authority required")

    def _account_guard(self, identifier: str, generation: int) -> None:
        delivery = self._active_delivery
        if delivery is None:
            raise PermissionError("account profile has no active Core delivery")
        parameters = delivery["action"]["parameters"]
        if (
            parameters.get("account_id") != identifier
            or parameters.get("account_generation") != generation
        ):
            raise PermissionError("profile differs from exact authorized account")
        self._guard()

    def execute(self, delivery: dict[str, Any]) -> dict[str, Any]:
        if self._active_delivery is not None:
            raise PermissionError("native Worker executes one delivery at a time")
        self._active_delivery = delivery
        self.effects.active = True
        try:
            return super().execute(delivery)
        finally:
            self._active_delivery = None
            self.effects.active = False
            self.effects.outputs.clear()

    def execute_effect(self, action: Action, cancellation: Cancellation) -> Result:
        if action.capability_id in {"machine.files.read", "machine.files.write"}:
            return super().execute_effect(action, cancellation)
        result = self.effects.execute(action, cancellation)
        if (
            result.success
            and action.capability_id == "machine.apps"
            and action.parameters["request"].get("operation") == "targets"
        ):
            result = replace(result, value=self.effects.outputs[action.id])
        if result.artifact:
            result = replace(
                result,
                artifact=replace(
                    result.artifact,
                    location="workspace:" + self.workspace_id,
                ),
            )
        return result

    def readback_effect(self, action: Action, delivery: dict[str, Any]) -> dict[str, Any]:
        if action.capability_id in {"machine.files.read", "machine.files.write"}:
            return super().readback_effect(action, delivery)
        self._guard()
        if action.capability_id == "machine.apps":
            observed = self.effects.desktop.app_targets(delivery["parameters"]["request"]["query"])
            self._guard()
            return {"content": json.dumps(observed)}
        if action.capability_id in REMOTE_MACHINE_CAPABILITIES and (
            REMOTE_MACHINE_CAPABILITIES[action.capability_id][0] in {"coding", "terminal_command"}
            and "verification" in action.parameters
        ):
            data = self.files.read(delivery["parameters"]["path"])
            if len(data) > 8192:
                raise ValueError("artifact readback exceeds permitted content boundary")
            self._guard()
            return {"content": data.decode("utf-8", errors="strict")}
        if action.capability_id == "machine.browser":
            observed = self.effects.execute(
                replace(action, parameters=delivery["parameters"]), RemoteCancellation(self._guard)
            )
            if not observed.success:
                raise ValueError("independent browser readback unavailable")
            report = json.loads(self.effects.outputs.pop(action.id))
            observations = report.get("observations")
            if not isinstance(observations, list) or len(observations) != 1:
                raise ValueError("one browser text observation required")
            return {"content": json.dumps(observations[0], allow_nan=False)}
        observed = self.effects.desktop.observe(delivery["parameters"], timeout=8)
        return {"content": json.dumps({"text": observed["text"]}, allow_nan=False)}


def supervised_scope(stream: TextIO) -> dict[str, Any]:
    line = stream.readline(16002)
    if not line.endswith("\n") or len(line.encode("utf-8")) > 16001:
        raise ValueError("bounded native scope line required")
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("native scope object required")
    return value


def supervise_stop(stream: TextIO, stop: Event) -> None:
    # Closing the native parent pipe also withdraws the local execution grant.
    try:
        line = stream.readline(65)
        if line != "stop\n":
            return
    finally:
        stop.set()


def main() -> int:
    """Native enrollment is separate; this command never creates an identity or grants."""
    import argparse
    import sys

    from .remote_client import GridClient
    from .remote_worker import WindowsNativeSigner, native_connection

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--scope", type=Path)
    source.add_argument("--scope-stdin", action="store_true")
    args = parser.parse_args()
    if args.scope_stdin:
        config = supervised_scope(sys.stdin)
    else:
        if args.scope.stat().st_size > 16_000:
            raise ValueError("bounded local native-sharing configuration required")
        config = json.loads(args.scope.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or set(config) - {
        "workspace",
        "workspace_id",
        "journal",
        "capabilities",
        "trusted_host_execution",
        "allowed_executables",
        "desktop",
        "browser",
        "desktop_app_ids",
        "profile_root",
    }:
        raise ValueError("exact local native-sharing configuration required")
    for key in ("trusted_host_execution", "desktop", "browser"):
        if key in config and type(config[key]) is not bool:
            raise ValueError("explicit native enablement required")
    for key in ("capabilities", "allowed_executables", "desktop_app_ids"):
        if key in config and (
            not isinstance(config[key], list)
            or any(not isinstance(value, str) or not value for value in config[key])
        ):
            raise ValueError("explicit native sharing list required")
    connection = native_connection(args.connection)
    if args.scope_stdin and config.get("workspace_id") != connection.get("workspace"):
        raise PermissionError("native scope differs from enrolled workspace")
    signer = WindowsNativeSigner(connection["installation_id"])
    stop = Event()
    try:
        client = GridClient(connection["url"], connection["session"], signer)
        scope = MachineScope(
            Path(config["workspace"]),
            trusted_host_execution=config.get("trusted_host_execution", False),
            allowed_executables=tuple(config.get("allowed_executables", ())),
            max_timeout=120,
        )
        worker = RemoteMachine(
            client,
            scope,
            config["workspace_id"],
            Path(config["journal"]),
            capabilities=tuple(config["capabilities"]),
            desktop=config.get("desktop", False),
            browser=config.get("browser", False),
            desktop_app_ids=tuple(config.get("desktop_app_ids", ())),
            profile_root=Path(config["profile_root"]) if config.get("profile_root") else None,
            local_authorize=lambda action: not stop.is_set(),
        )
        monitor_done = Event()
        if args.scope_stdin:
            Thread(target=supervise_stop, args=(sys.stdin, stop), daemon=True).start()

            def report() -> None:
                previous = None
                while not monitor_done.wait(0.1):
                    status = worker.status
                    if status != previous:
                        print(json.dumps({"status": status}), flush=True)
                        previous = status

            Thread(target=report, daemon=True).start()
        try:
            worker.run(stop)
        except KeyboardInterrupt:
            pass
        finally:
            monitor_done.set()
            worker.close()
            if args.scope_stdin:
                print(
                    json.dumps({"status": "stopped" if stop.is_set() else "unavailable"}),
                    flush=True,
                )
    finally:
        signer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
