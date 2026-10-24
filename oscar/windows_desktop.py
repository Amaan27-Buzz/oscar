"""Opt-in Windows app discovery and bounded UIA. Observation is transient."""

import base64
import hashlib
import importlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time
from typing import Any

BRIDGE_PATH = Path(__file__).with_name("windows_uia.ps1")
BRIDGE = BRIDGE_PATH.read_text(encoding="utf-8")


@dataclass(frozen=True)
class InstalledApp:
    id: str
    name: str
    publisher: str | None
    activation: str
    launch_type: str
    source: str
    observed_at: float
    available: bool
    supported_operations: tuple[str, ...]
    unknown_capabilities: tuple[str, ...] = ("application-specific automation",)
    permissions: tuple[str, ...] = ("machine:host", "desktop:control")
    risk: str = "high"


def discover_apps() -> list[InstalledApp]:
    if os.name != "nt":
        return []
    winreg = importlib.import_module("winreg")

    records: dict[str, InstalledApp] = {}
    for hive, label in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
            try:
                with winreg.OpenKey(hive, base, 0, winreg.KEY_READ | view) as key:
                    for index in range(min(winreg.QueryInfoKey(key)[0], 512)):
                        name = winreg.EnumKey(key, index)
                        try:
                            with winreg.OpenKey(key, name) as entry:
                                executable = str(winreg.QueryValueEx(entry, "")[0]).strip('"')
                            path = Path(executable)
                            if not path.is_absolute() or path.suffix.lower() != ".exe":
                                continue
                            source = f"registry:{label}:{view}:{base}\\{name}"
                            identifier = hashlib.sha256(source.encode()).hexdigest()[:32]
                            records[identifier] = InstalledApp(
                                identifier,
                                name,
                                None,
                                str(path),
                                "native_exe",
                                source,
                                time(),
                                path.is_file(),
                                ("launch", "observe_window"),
                            )
                        except OSError:
                            continue
            except OSError:
                continue
    # Built-in executable identity is explicit; it is not merged with packaged aliases.
    path = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "notepad.exe"
    if path.is_file():
        source = "windows-system-directory:notepad.exe"
        identifier = hashlib.sha256(source.encode()).hexdigest()[:32]
        records[identifier] = InstalledApp(
            identifier,
            "Windows Notepad",
            "Microsoft",
            str(path),
            "native_exe",
            source,
            time(),
            True,
            ("launch", "observe_window"),
        )
    return list(records.values())


class WindowsDesktop:
    def __init__(
        self,
        *,
        permissions: frozenset[str],
        allowed_apps: tuple[InstalledApp, ...],
        workspace: Path | None = None,
        catalog_apps: tuple[InstalledApp, ...] | None = None,
    ):
        if os.name != "nt":
            raise OSError("Windows desktop unavailable")
        self.permissions, self.apps = permissions, {app.id: app for app in allowed_apps}
        self.catalog_apps = catalog_apps if catalog_apps is not None else allowed_apps
        self.workspace = workspace
        self.targets: dict[int, int] = {}
        self.target_apps: dict[int, str] = {}
        self.shell = str(
            Path(os.environ["SystemRoot"])
            / "System32"
            / "WindowsPowerShell"
            / "v1.0"
            / "powershell.exe"
        )

    def _authorize(self) -> None:
        if not {"machine:host", "desktop:control"} <= self.permissions:
            raise PermissionError("explicit host and desktop control grants required")

    def launch(self, app_id: str, *, artifact: str | None = None) -> subprocess.Popen[bytes]:
        self._authorize()
        app = self.apps[app_id]
        if not app.available or app.launch_type != "native_exe":
            raise ValueError("discovered native app required")
        arguments = []
        if artifact is not None:
            from .windows_files import WindowsScopedFiles

            if self.workspace is None or not isinstance(artifact, str):
                raise ValueError("scoped app artifact required")
            files = WindowsScopedFiles(self.workspace)
            if len(files.read(artifact)) > 64_000:
                raise ValueError("bounded app artifact required")
            arguments.append(str(self.workspace.resolve().joinpath(*files.parts(artifact))))
        env = {
            key: os.environ[key]
            for key in ("SystemRoot", "TEMP", "TMP", "PATH")
            if key in os.environ
        }
        return subprocess.Popen(
            [app.activation, *arguments],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def bind(self, handle: int, pid: int, app_id: str) -> None:
        """Target must match a discovered app's actual process executable."""
        self._authorize()
        if type(handle) is not int or type(pid) is not int or handle <= 0 or pid <= 0:
            raise ValueError("real numeric window/process identity required")
        app = self.apps[app_id]
        import ctypes
        from ctypes import wintypes

        win32: Any = ctypes
        kernel = win32.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        process = kernel.OpenProcess(0x1000, False, pid)
        if not process:
            raise OSError("cannot inspect target process")
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(buffer))
            if not kernel.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(length)):
                raise OSError("cannot establish app identity")
            if Path(buffer.value).resolve() != Path(app.activation).resolve():
                raise PermissionError("process differs from discovered app executable")
        finally:
            kernel.CloseHandle(process)
        self.targets[handle] = pid
        self.target_apps[handle] = app_id

    def command(self, request: dict[str, Any]) -> list[str]:
        self._authorize()
        fields = {
            "windows": set(),
            "focused": set(),
            "focused_identity": set(),
            "tree": {"handle", "pid"},
            "close": {"handle", "pid"},
            "read": {"handle", "pid", "runtime_id"},
            "focus_snapshot": {"handle", "pid", "runtime_id"},
            "focus": {"handle", "pid", "runtime_id"},
            "invoke": {"handle", "pid", "runtime_id"},
            "select": {"handle", "pid", "runtime_id"},
            "key": {"handle", "pid", "runtime_id", "key"},
            "close_tab": {"handle", "pid", "runtime_id", "expected_title"},
            "mouse_click": {"handle", "pid", "runtime_id", "x_fraction", "y_fraction"},
            "set_text": {"handle", "pid", "runtime_id", "text"},
            "set_text_checked": {"handle", "pid", "runtime_id", "text", "expected_text"},
            "context": {"handle", "pid", "runtime_id", "include_current"},
            "clipboard_write": {"text"},
            "clipboard_read": set(),
            "screenshot": {"handle", "pid"},
            "visual_click": {"handle", "pid", "sha256", "width", "height", "x", "y"},
        }
        operation = request.get("operation")
        if operation not in fields or set(request) != fields[operation] | {"operation"}:
            raise ValueError("invalid desktop operation")
        if operation in {"screenshot", "visual_click"}:
            if "desktop:capture" not in self.permissions:
                raise PermissionError("separate selected-window capture grant required")
            if type(request["handle"]) is not int or type(request["pid"]) is not int:
                raise ValueError("numeric window/process identity required")
        if operation == "visual_click":
            if (
                not isinstance(request["sha256"], str)
                or len(request["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in request["sha256"])
                or any(type(request[k]) is not int for k in ("width", "height", "x", "y"))
                or not 1 <= request["width"] <= 4096
                or not 1 <= request["height"] <= 2160
                or not 0 <= request["x"] < request["width"]
                or not 0 <= request["y"] < request["height"]
            ):
                raise ValueError("exact bounded screenshot and client coordinates required")
        if operation in {"clipboard_write", "clipboard_read"} and (
            "desktop:clipboard" not in self.permissions
        ):
            raise PermissionError("explicit clipboard grant required")
        if operation not in {
            "windows",
            "focused",
            "focused_identity",
            "clipboard_write",
            "clipboard_read",
        }:
            if self.targets.get(request["handle"]) != request["pid"]:
                raise PermissionError("unbound desktop target")
            self.bind(request["handle"], request["pid"], self.target_apps[request["handle"]])
        if "runtime_id" in request and (
            not isinstance(request["runtime_id"], str) or len(request["runtime_id"]) > 200
        ):
            raise ValueError("bounded UIA identity required")
        if "text" in request and (
            not isinstance(request["text"], str) or len(request["text"]) > 8192
        ):
            raise ValueError("bounded text required")
        if "expected_text" in request and (
            not isinstance(request["expected_text"], str) or len(request["expected_text"]) > 8192
        ):
            raise ValueError("bounded destination readback required")
        if operation == "context" and type(request["include_current"]) is not bool:
            raise ValueError("explicit full-field capture choice required")
        if operation == "key" and request["key"] not in {
            "select_all",
            "backspace",
            "enter",
            "escape",
            "tab",
        }:
            raise ValueError("fixed keyboard action required")
        if operation == "close_tab" and (
            self.apps[self.target_apps[request["handle"]]].name.casefold() != "notepad.exe"
            or not isinstance(request["expected_title"], str)
            or not 0 < len(request["expected_title"]) <= 1000
        ):
            raise ValueError("Notepad tab and exact observed title required")
        if operation == "mouse_click" and any(
            type(request[k]) not in {int, float} or not 0 <= request[k] <= 1
            for k in ("x_fraction", "y_fraction")
        ):
            raise ValueError("mouse fallback must remain inside the observed element")
        return [self.shell, "-NoProfile", "-NonInteractive", "-STA", "-File", str(BRIDGE_PATH)]

    @staticmethod
    def input(request: dict[str, Any]) -> bytes:
        return base64.b64encode(json.dumps(request, ensure_ascii=False).encode()) + b"\n"

    def observe(self, request: dict[str, Any], *, timeout: float = 15) -> Any:
        """Independent observer process; no successful executor response is consulted."""
        if not 0 < timeout <= 15:
            raise ValueError("observer timeout must be positive and at most 15 seconds")
        env = {key: os.environ[key] for key in ("SystemRoot", "TEMP", "TMP") if key in os.environ}
        result = subprocess.run(
            self.command(request),
            input=self.input(request),
            env=env,
            capture_output=True,
            timeout=min(15, timeout),
        )
        if result.returncode or len(result.stdout) > 128_000:
            raise OSError("bounded UI Automation observation failed")
        return json.loads(result.stdout.decode("utf-8-sig"))

    def catalog(self) -> list[dict[str, Any]]:
        self._authorize()
        return [
            {**asdict(app), "launch_authorized": app.id in self.apps} for app in self.catalog_apps
        ]
