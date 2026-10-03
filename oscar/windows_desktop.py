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

BRIDGE = r"""
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__PAYLOAD__'))|ConvertFrom-Json
$root=[Windows.Automation.AutomationElement]::RootElement
function Describe($e) {
 $text=$null; $v=$null
 if ($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$v)) {
  $text=$v.Current.Value
 }
 else {
  $t=$null
  if ($e.TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$t)) {
   $text=$t.DocumentRange.GetText(8192)
  }
 }
 @{runtime_id=(@($e.GetRuntimeId()) -join '.');name=$e.Current.Name
   type=$e.Current.ControlType.ProgrammaticName; automation_id=$e.Current.AutomationId
   pid=$e.Current.ProcessId;handle=$e.Current.NativeWindowHandle
   enabled=$e.Current.IsEnabled;password=$e.Current.IsPassword;text=$text;
   patterns=@($e.GetSupportedPatterns()|ForEach-Object {$_.ProgrammaticName})}
}
if ($p.operation -eq 'windows') {
 $all=$root.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
 $result=@(); for ($i=0;$i -lt [Math]::Min($all.Count,100);$i++) { $result+=Describe $all[$i] }
 ConvertTo-Json -InputObject @($result) -Compress -Depth 6; exit
}
$window=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$p.handle)
if ($null -eq $window -or $window.Current.ProcessId -ne $p.pid) { throw 'target identity changed' }
if ($p.operation -eq 'tree') {
 $queue=[Collections.Generic.Queue[object]]::new();$queue.Enqueue(@{e=$window;depth=0});$result=@()
 $walker=[Windows.Automation.TreeWalker]::ControlViewWalker
 while ($queue.Count -gt 0 -and $result.Count -lt 100) {
  $item=$queue.Dequeue();$result+=Describe $item.e
  if ($item.depth -lt 8) {
   $child=$walker.GetFirstChild($item.e);$count=0
   while ($null -ne $child -and $count -lt 100) {
    $queue.Enqueue(@{e=$child;depth=$item.depth+1});$count++;$child=$walker.GetNextSibling($child)
   }
  }
 }
 ConvertTo-Json -InputObject @($result) -Compress -Depth 6;exit
}
if ($p.operation -eq 'close') {
 $pattern=$null
 if (-not $window.TryGetCurrentPattern(
  [Windows.Automation.WindowPattern]::Pattern,[ref]$pattern)) { throw 'no window pattern' }
 $pattern.Close(); @{operation='close';status='REPORTED'}|ConvertTo-Json -Compress;exit
}
$elements=$window.FindAll([Windows.Automation.TreeScope]::Descendants,
                         [Windows.Automation.Condition]::TrueCondition)
$element=$null
for ($i=0;$i -lt [Math]::Min($elements.Count,500);$i++) {
 if ((@($elements[$i].GetRuntimeId()) -join '.') -eq $p.runtime_id) {$element=$elements[$i];break}
}
if ($null -eq $element -or $element.Current.ProcessId -ne $p.pid -or $element.Current.IsPassword) {
 throw 'target unavailable/unsafe'
}
switch ($p.operation) {
 'read' { Describe $element |ConvertTo-Json -Compress -Depth 6 }
 'focus' {
  $element.SetFocus()
  Describe ([Windows.Automation.AutomationElement]::FocusedElement) |
   ConvertTo-Json -Compress -Depth 6
 }
 'invoke' {
  $pattern=$null
  if (-not $element.TryGetCurrentPattern(
   [Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {throw 'invoke unsupported'}
  $pattern.Invoke();@{status='REPORTED'}|ConvertTo-Json -Compress
 }
 'set_text' {
  $pattern=$null
  if ($element.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)) {
   if ($pattern.Current.IsReadOnly) {throw 'read-only target'}; $pattern.SetValue($p.text)
  } else {
   if ($element.Current.ControlType.ProgrammaticName -notin @(
    'ControlType.Edit','ControlType.Document')) {throw 'text fallback requires editor'}
   Add-Type -AssemblyName System.Windows.Forms
   $element.SetFocus()
   $focused=[Windows.Automation.AutomationElement]::FocusedElement
   if ($focused.Current.ProcessId -ne $p.pid -or
    (@($focused.GetRuntimeId()) -join '.') -ne $p.runtime_id) {throw 'focus not verified'}
   $escaped=''; foreach ($c in $p.text.ToCharArray()) {
    if ('+^%~()[]{}'.Contains([string]$c)) { $escaped+='{'+$c+'}' } else {$escaped+=$c}
   }
   [Windows.Forms.SendKeys]::SendWait('^a');[Windows.Forms.SendKeys]::SendWait($escaped)
  }
  @{status='REPORTED';operation='set_text'}|ConvertTo-Json -Compress
 }
 default {throw 'unsupported typed desktop operation'}
}
"""


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
    def __init__(self, *, permissions: frozenset[str], allowed_apps: tuple[InstalledApp, ...]):
        if os.name != "nt":
            raise OSError("Windows desktop unavailable")
        self.permissions, self.apps = permissions, {app.id: app for app in allowed_apps}
        self.targets: dict[int, int] = {}
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

    def launch(self, app_id: str, *, arguments: tuple[str, ...] = ()) -> subprocess.Popen[bytes]:
        self._authorize()
        app = self.apps[app_id]
        if not app.available or app.launch_type != "native_exe" or arguments:
            raise ValueError("only discovered native app launch without arguments is admitted")
        env = {
            key: os.environ[key]
            for key in ("SystemRoot", "TEMP", "TMP", "PATH")
            if key in os.environ
        }
        return subprocess.Popen(
            [app.activation],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def bind(self, handle: int, pid: int, app_id: str) -> None:
        """Target must match a discovered app's actual process executable."""
        self._authorize()
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

    def command(self, request: dict[str, Any]) -> list[str]:
        self._authorize()
        fields = {
            "windows": set(),
            "tree": {"handle", "pid"},
            "close": {"handle", "pid"},
            "read": {"handle", "pid", "runtime_id"},
            "focus": {"handle", "pid", "runtime_id"},
            "invoke": {"handle", "pid", "runtime_id"},
            "set_text": {"handle", "pid", "runtime_id", "text"},
        }
        operation = request.get("operation")
        if operation not in fields or set(request) != fields[operation] | {"operation"}:
            raise ValueError("invalid desktop operation")
        if operation != "windows" and self.targets.get(request["handle"]) != request["pid"]:
            raise PermissionError("unbound desktop target")
        if "runtime_id" in request and (
            not isinstance(request["runtime_id"], str) or len(request["runtime_id"]) > 200
        ):
            raise ValueError("bounded UIA identity required")
        if "text" in request and (
            not isinstance(request["text"], str) or len(request["text"]) > 8192
        ):
            raise ValueError("bounded text required")
        payload = base64.b64encode(json.dumps(request).encode()).decode()
        script = base64.b64encode(BRIDGE.replace("__PAYLOAD__", payload).encode("utf-16-le"))
        return [self.shell, "-NoProfile", "-NonInteractive", "-EncodedCommand", script.decode()]

    def observe(self, request: dict[str, Any]) -> Any:
        """Independent observer process; no successful executor response is consulted."""
        env = {key: os.environ[key] for key in ("SystemRoot", "TEMP", "TMP") if key in os.environ}
        result = subprocess.run(self.command(request), env=env, capture_output=True, timeout=15)
        if result.returncode or len(result.stdout) > 128_000:
            raise OSError("bounded UI Automation observation failed")
        return json.loads(result.stdout.decode("utf-8-sig"))

    def catalog(self) -> list[dict[str, Any]]:
        self._authorize()
        return [asdict(app) for app in self.apps.values()]
