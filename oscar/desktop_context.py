"""Explicit Windows observations. No timer, content archive or coordinate capture."""

import ctypes
import math
import os
from ctypes import wintypes
from dataclasses import dataclass
from enum import StrEnum
from time import time
from typing import Any

from .windows_desktop import WindowsDesktop


class ContextSource(StrEnum):
    FOREGROUND = "foreground"
    SELECTION = "selection"
    FOCUSED = "focused"
    CLIPBOARD = "clipboard"
    BROWSER = "browser"
    FILE = "file"
    NODE = "node"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True)
class DesktopContext:
    id: str
    source: ContextSource
    observed_at: float
    scope: str
    provenance: str
    permission: str
    text: str | None = None
    destination: tuple[int, int, str] | None = None
    original: str | None = None
    selection_start: int | None = None
    ttl: float = 15

    def __post_init__(self) -> None:
        if (
            not self.id
            or not isinstance(self.source, ContextSource)
            or not self.scope
            or not self.provenance
            or self.permission not in {"granted", "denied", "unavailable"}
            or not math.isfinite(self.observed_at)
            or self.observed_at < 0
            or not math.isfinite(self.ttl)
            or not 0 < self.ttl <= 30
            or any(v is not None and len(v) > 8192 for v in (self.text, self.original))
        ):
            raise ValueError("invalid bounded context")
        if self.destination is not None and (
            len(self.destination) != 3
            or any(type(value) is not int or value <= 0 for value in self.destination[:2])
            or not isinstance(self.destination[2], str)
            or not 0 < len(self.destination[2]) <= 200
        ):
            raise ValueError("invalid destination identity")
        if self.selection_start is not None and (
            type(self.selection_start) is not int or not 0 <= self.selection_start <= 8192
        ):
            raise ValueError("invalid structured selection offset")

    def fresh(self, now: float) -> bool:
        return self.permission == "granted" and 0 <= now - self.observed_at < self.ttl

    def view(self, now: float) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "timestamp": self.observed_at,
            "scope": self.scope,
            "provenance": self.provenance,
            "freshness": "fresh" if self.fresh(now) else "stale/unavailable",
            "permission": self.permission,
            "text": self.text,
            "retained": False,
        }


class WindowsContext:
    def __init__(self, desktop: WindowsDesktop):
        self.desktop = desktop

    def foreground(self) -> tuple[int, int, str]:
        if os.name != "nt":
            raise OSError("Windows unavailable")
        win32: Any = ctypes
        user = win32.WinDLL("user32", use_last_error=True)
        user.GetForegroundWindow.restype = wintypes.HWND
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        handle = user.GetForegroundWindow()
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(pid))
        title = ctypes.create_unicode_buffer(1024)
        user.GetWindowTextW(handle, title, len(title))
        if not handle or not pid.value:
            raise OSError("foreground unavailable")
        return int(handle), pid.value, title.value

    def capture(
        self, source: ContextSource, identifier: str, target: tuple[int, int, str] | None = None
    ) -> DesktopContext:
        handle, pid, title = self.foreground() if target is None else (target[0], target[1], "")
        scope = f"window:{handle}/process:{pid}"
        now = time()
        if source == ContextSource.FOREGROUND:
            # Titles are also private; never retain or treat them as instructions.
            return DesktopContext(
                identifier,
                source,
                now,
                scope,
                "user32:GetForegroundWindow/GetWindowTextW",
                "granted",
                title,
            )
        if source not in {ContextSource.SELECTION, ContextSource.FOCUSED}:
            raise ValueError("source requires its own explicit capability")
        if self.desktop.targets.get(handle) != pid:
            raise PermissionError("content capture requires a registered Worker app/window")
        if target is None:
            focused = self.desktop.observe({"operation": "focused_identity"})
            if focused["pid"] != pid or focused["password"]:
                raise PermissionError("focused element is unsafe or outside foreground")
            identity = str(focused["runtime_id"])
        else:
            identity = target[2]
        data = self.desktop.observe(
            {
                "operation": "context",
                "handle": handle,
                "pid": pid,
                "runtime_id": identity,
                "include_current": source == ContextSource.FOCUSED,
            }
        )
        if target is None and self.foreground()[:2] != (handle, pid):
            raise ValueError("foreground changed during observation")
        element = data["element"]
        text = data["selected"] if source == ContextSource.SELECTION else element["text"]
        if (
            not isinstance(text, str)
            or len(text) > 8192
            or source == ContextSource.SELECTION
            and not text
        ):
            return DesktopContext(
                identifier, source, now, scope, "UIA:TextPattern/ValuePattern", "unavailable"
            )
        original = element["text"]
        start = data["start"] if source == ContextSource.SELECTION else None
        destination = (
            (handle, pid, identity)
            if source == ContextSource.FOCUSED
            and "ValuePatternIdentifiers.Pattern" in (element["patterns"])
            else None
        )
        return DesktopContext(
            identifier,
            source,
            now,
            scope,
            "UIA:TextPattern/ValuePattern" + ("/explicit target" if target else "/foreground"),
            "granted",
            text,
            destination,
            original,
            start,
        )
