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
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__PAYLOAD__'))|ConvertFrom-Json
$root=[Windows.Automation.AutomationElement]::RootElement
function Describe($e) {
 $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($e)
 $parentId=$null
 if ($null -ne $parent) {$parentId=(@($parent.GetRuntimeId()) -join '.')}
 $text=$null; $v=$null
 if (-not $e.Current.IsPassword -and
     $e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$v)) {
  $text=$v.Current.Value
 }
 else {
  $t=$null
  if (-not $e.Current.IsPassword -and
      $e.TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$t)) {
   $text=$t.DocumentRange.GetText(8192)
  }
 }
 @{runtime_id=(@($e.GetRuntimeId()) -join '.');parent_runtime_id=$parentId;name=$e.Current.Name
   type=$e.Current.ControlType.ProgrammaticName; automation_id=$e.Current.AutomationId
   pid=$e.Current.ProcessId;handle=$e.Current.NativeWindowHandle
   enabled=$e.Current.IsEnabled;password=$e.Current.IsPassword;text=$text;
   offscreen=$e.Current.IsOffscreen;
   patterns=@($e.GetSupportedPatterns()|ForEach-Object {$_.ProgrammaticName})}
}
if ($p.operation -eq 'windows') {
 $all=$root.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
 $result=@(); for ($i=0;$i -lt [Math]::Min($all.Count,100);$i++) { $result+=Describe $all[$i] }
 ConvertTo-Json -InputObject @($result) -Compress -Depth 6; exit
}
if ($p.operation -eq 'focused') {
 Describe ([Windows.Automation.AutomationElement]::FocusedElement) |
  ConvertTo-Json -Compress -Depth 6;exit
}
$window=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$p.handle)
if ($null -eq $window -or $window.Current.ProcessId -ne $p.pid) { throw 'target identity changed' }
if ($p.operation -eq 'tree') {
 $queue=[Collections.Generic.Queue[object]]::new();$queue.Enqueue(@{e=$window;depth=0});$result=@()
 $walker=[Windows.Automation.TreeWalker]::ControlViewWalker
 while ($queue.Count -gt 0 -and $result.Count -lt 200) {
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
$element=$null
$queue=[Collections.Generic.Queue[object]]::new();$queue.Enqueue(@{e=$window;depth=0})
$walker=[Windows.Automation.TreeWalker]::ControlViewWalker;$visited=0
while ($queue.Count -gt 0 -and $visited++ -lt 500) {
 $item=$queue.Dequeue()
 if ((@($item.e.GetRuntimeId()) -join '.') -eq $p.runtime_id) {$element=$item.e;break}
 if ($item.depth -lt 8) {
  $child=$walker.GetFirstChild($item.e);$count=0
  while ($null -ne $child -and $count++ -lt 100 -and $queue.Count -lt 500) {
   $queue.Enqueue(@{e=$child;depth=$item.depth+1});$child=$walker.GetNextSibling($child)
  }
 }
}
if ($null -eq $element -or $element.Current.ProcessId -ne $p.pid -or $element.Current.IsPassword) {
 throw 'target unavailable/unsafe'
}
switch ($p.operation) {
 'read' { Describe $element |ConvertTo-Json -Compress -Depth 6 }
 'focus_snapshot' {
  $beforeWindow=Describe $window;$beforeEditor=Describe $element
  $focused=[Windows.Automation.AutomationElement]::FocusedElement
  $focus=@{pid=0;handle=0;runtime_id=$null}
  if ($null -ne $focused) {
   $focus=@{pid=$focused.Current.ProcessId;handle=$focused.Current.NativeWindowHandle;
    runtime_id=(@($focused.GetRuntimeId()) -join '.')}
  }
  @{windows=@($beforeWindow,(Describe $window));
    editors=@($beforeEditor,(Describe $element));focused=$focus} |
   ConvertTo-Json -Compress -Depth 6
 }
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
 'select' {
  $pattern=$null
  if (-not $element.TryGetCurrentPattern(
    [Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pattern)) {throw 'select unsupported'}
  $pattern.Select();@{status='REPORTED';operation='select'}|ConvertTo-Json -Compress
 }
 'key' {
  Add-Type -AssemblyName System.Windows.Forms
  $element.SetFocus()
  $focused=[Windows.Automation.AutomationElement]::FocusedElement
  if ($focused.Current.ProcessId -ne $p.pid -or
      (@($focused.GetRuntimeId()) -join '.') -ne $p.runtime_id) {throw 'focus changed'}
  $keys=@{select_all='^a';backspace='{BACKSPACE}';enter='{ENTER}';escape='{ESC}';tab='{TAB}'}
  [Windows.Forms.SendKeys]::SendWait($keys[$p.key])
  @{status='REPORTED';operation='key'}|ConvertTo-Json -Compress
 }
 'close_tab' {
  if ($window.Current.Name -ne $p.expected_title) {throw 'active tab title changed'}
  $element.SetFocus()
  $focused=[Windows.Automation.AutomationElement]::FocusedElement
  if ($focused.Current.ProcessId -ne $p.pid -or
      (@($focused.GetRuntimeId()) -join '.') -ne $p.runtime_id) {throw 'focus changed'}
  Add-Type -AssemblyName System.Windows.Forms
  [Windows.Forms.SendKeys]::SendWait('^w')
  @{status='REPORTED';operation='close_tab'}|ConvertTo-Json -Compress
 }
 'mouse_click' {
  if ($element.Current.IsOffscreen) {throw 'offscreen mouse target'}
  $rect=$element.Current.BoundingRectangle
  if ($rect.Width -le 0 -or $rect.Height -le 0 -or
      $rect.Width -gt 50000 -or $rect.Height -gt 50000) {throw 'invalid bounded rectangle'}
  $element.SetFocus()
  if ([Windows.Automation.AutomationElement]::FocusedElement.Current.ProcessId -ne $p.pid) {
   throw 'target process not focused'
  }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class OscarPointer {
 [StructLayout(LayoutKind.Sequential)] public struct Mouse {
  public int dx,dy; public uint data,flags,time; public UIntPtr extra;
 }
 [StructLayout(LayoutKind.Sequential)] public struct Input {public uint type;public Mouse mouse;}
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll",SetLastError=true)]
 public static extern uint SendInput(uint count,Input[] input,int size);
 public static bool Click() {
  var a=new Input[2]; a[0].mouse.flags=2; a[1].mouse.flags=4;
  return SendInput(2,a,Marshal.SizeOf(typeof(Input)))==2;
 }
}
'@
  $x=[int]($rect.X+$rect.Width*$p.x_fraction);$y=[int]($rect.Y+$rect.Height*$p.y_fraction)
  if ([Math]::Abs($x) -gt 32767 -or [Math]::Abs($y) -gt 32767) {throw 'coordinate bound'}
  if (-not [OscarPointer]::SetCursorPos($x,$y) -or -not [OscarPointer]::Click()) {
   throw 'input rejected by Windows'
  }
  @{status='REPORTED';operation='mouse_click';x=$x;y=$y}|ConvertTo-Json -Compress
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
   [Windows.Forms.SendKeys]::SendWait('^a{BACKSPACE}')
   if ($escaped.Length -gt 0) {[Windows.Forms.SendKeys]::SendWait($escaped)}
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
        }
        operation = request.get("operation")
        if operation not in fields or set(request) != fields[operation] | {"operation"}:
            raise ValueError("invalid desktop operation")
        if operation not in {"windows", "focused"}:
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
        payload = base64.b64encode(json.dumps(request).encode()).decode()
        script = base64.b64encode(BRIDGE.replace("__PAYLOAD__", payload).encode("utf-16-le"))
        return [self.shell, "-NoProfile", "-NonInteractive", "-EncodedCommand", script.decode()]

    def observe(self, request: dict[str, Any], *, timeout: float = 15) -> Any:
        """Independent observer process; no successful executor response is consulted."""
        if not 0 < timeout <= 15:
            raise ValueError("observer timeout must be positive and at most 15 seconds")
        env = {key: os.environ[key] for key in ("SystemRoot", "TEMP", "TMP") if key in os.environ}
        result = subprocess.run(
            self.command(request), env=env, capture_output=True, timeout=min(15, timeout)
        )
        if result.returncode or len(result.stdout) > 128_000:
            raise OSError("bounded UI Automation observation failed")
        return json.loads(result.stdout.decode("utf-8-sig"))

    def catalog(self) -> list[dict[str, Any]]:
        self._authorize()
        return [
            {**asdict(app), "launch_authorized": app.id in self.apps} for app in self.catalog_apps
        ]
