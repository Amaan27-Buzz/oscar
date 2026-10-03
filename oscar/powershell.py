"""Typed PowerShell discovery/operations; never accepts user-authored shell text."""

import base64
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PowerShellManifest:
    id: str
    executable: str
    edition: str
    available: bool
    permissions: tuple[str, ...] = ("machine:host",)
    operations: tuple[str, ...] = ("write_utf8", "file_hash", "environment", "wait")


def discover() -> PowerShellManifest | None:
    if os.name != "nt":
        return None
    for command, edition in (("pwsh.exe", "PowerShell"), ("powershell.exe", "WindowsPowerShell")):
        executable = shutil.which(command)
        if executable and Path(executable).is_file():
            return PowerShellManifest(
                "machine.powershell", str(Path(executable).resolve()), edition, True
            )
    return None


SCRIPT = r"""
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$p = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__PAYLOAD__')) | ConvertFrom-Json
$result = switch ($p.operation) {
 'write_utf8' {
   if ([IO.File]::Exists($p.path)) { throw 'new artifact required' }
   $stream = [IO.File]::Open($p.path,[IO.FileMode]::CreateNew,
                            [IO.FileAccess]::Write,[IO.FileShare]::None)
   try {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes($p.content)
    $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true)
   }
   finally { $stream.Dispose() }
   @{ operation='write_utf8'; bytes=$bytes.Length }
 }
 'file_hash' { @{sha256=(Get-FileHash -LiteralPath $p.path -Algorithm SHA256).Hash.ToLower()} }
 'environment' {
  @{names=@(Get-ChildItem Env: | Select-Object -ExpandProperty Name)
    version=$PSVersionTable.PSVersion.ToString(); cwd=(Get-Location).Path}
 }
 'wait' { Start-Sleep -Milliseconds $p.milliseconds; @{waited=$true} }
 default { throw 'unsupported typed operation' }
}
$result | ConvertTo-Json -Compress -Depth 5
"""


def command(manifest: PowerShellManifest, parameters: dict[str, Any], root: Path) -> list[str]:
    operation = parameters.get("operation")
    fields = {
        "write_utf8": {"operation", "path", "content"},
        "file_hash": {"operation", "path"},
        "environment": {"operation"},
        "wait": {"operation", "milliseconds"},
    }
    if operation not in fields or set(parameters) != fields[operation]:
        raise ValueError("invalid typed PowerShell operation")
    p = dict(parameters)
    if operation in {"write_utf8", "file_hash"}:
        from .windows_files import WindowsScopedFiles

        path = p["path"]
        if not isinstance(path, str):
            raise ValueError("relative artifact required")
        files = WindowsScopedFiles(root)
        parts = files.parts(path)
        with files.pinned(root.joinpath(*parts[:-1])):
            pass
        if operation == "file_hash":
            files.read(path)
        elif files.exists(path):
            raise ValueError("new artifact required")
        p["path"] = str(root.resolve() / path)
    if operation == "write_utf8" and (
        not isinstance(p["content"], str) or len(p["content"].encode()) > 16_000
    ):
        raise ValueError("bounded UTF-8 content required")
    if operation == "wait" and (
        type(p["milliseconds"]) is not int or not 0 <= p["milliseconds"] <= 120_000
    ):
        raise ValueError("bounded wait required")
    payload = base64.b64encode(json.dumps(p).encode()).decode()
    encoded = base64.b64encode(SCRIPT.replace("__PAYLOAD__", payload).encode("utf-16-le")).decode()
    return [
        manifest.executable,
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
        encoded,
    ]
