"""Windows local-alpha files: reject reparses; pin ancestors against rename/delete.

This is a trusted local workspace boundary, not isolation from hostile host code.
"""

import ctypes
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .capabilities import Cancellation, ScopedFiles
from .contracts import new_id

_win32: Any = ctypes


def is_reparse(path: Path) -> bool:
    metadata: Any = path.lstat()
    return bool(metadata.st_file_attributes & 0x400)


class WindowsScopedFiles(ScopedFiles):
    def __init__(self, root: Path):
        # Do not resolve away a junction before inspecting it.
        self.root = Path(os.path.abspath(root))
        if self.root.drive.startswith("\\\\"):
            raise ValueError("local Windows workspace required")
        with self.pinned(self.root, create=True):
            pass

    @staticmethod
    def parts(relative: str) -> list[str]:
        parts = relative.split("/")
        if not relative or any(
            not p
            or p in {".", ".."}
            or any(c in p for c in '\\:<>"|?*\x00')
            or any(ord(c) < 32 for c in p)
            or p.endswith((" ", "."))
            or re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", p, re.I)
            for p in parts
        ):
            raise ValueError("path outside authorized workspace")
        return parts

    @contextmanager
    def pinned(self, path: Path, create: bool = False) -> Iterator[None]:
        """Open every ancestor without following a reparse, denying delete sharing."""
        from ctypes import wintypes

        kernel = _win32.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handles = []
        try:
            ancestors = [*reversed(path.parents), path]
            for ancestor in ancestors:
                if create and not ancestor.exists():
                    ancestor.mkdir()
                handle = kernel.CreateFileW(
                    str(ancestor), 0x80000000, 3, None, 3, 0x02200000, None
                )  # SHARE_READ|WRITE; OPEN_REPARSE_POINT|BACKUP_SEMANTICS
                if handle == ctypes.c_void_p(-1).value:
                    raise _win32.WinError(_win32.get_last_error())
                handles.append(handle)
                if is_reparse(ancestor):
                    raise PermissionError("reparse point denied")
            yield
        finally:
            for handle in reversed(handles):
                kernel.CloseHandle(handle)

    @contextmanager
    def checked_directory(self, relative: str = ".", create: bool = False) -> Iterator[Path]:
        target = self.root if relative == "." else self.root.joinpath(*self.parts(relative))
        with self.pinned(target, create):
            if not target.is_dir():
                raise ValueError("directory required")
            yield target

    def exists(self, relative: str) -> bool:
        parts = self.parts(relative)
        with self.checked_directory("/".join(parts[:-1]) or ".") as parent:
            try:
                (parent / parts[-1]).lstat()
                return True
            except FileNotFoundError:
                return False

    def names(self, relative: str, pattern: str) -> list[str]:
        with self.checked_directory(relative) as directory, os.scandir(directory) as entries:
            names: list[str] = []
            for scanned, entry in enumerate(entries):
                if scanned >= 10_000 or len(names) >= 500:
                    raise ValueError("directory result bound exceeded")
                if not is_reparse(Path(entry.path)) and pattern in entry.name:
                    names.append(entry.name)
            return sorted(names)

    def read(self, relative: str) -> bytes:
        parts = self.parts(relative)
        with self.checked_directory("/".join(parts[:-1]) or ".") as parent:
            target = parent / parts[-1]
            # The leaf handle prevents replacing it between inspection and the read.
            with self.pinned(target):
                if not target.is_file():
                    raise ValueError("regular file required")
                with target.open("rb") as stream:
                    return stream.read(1_000_001)

    def write(self, relative: str, content: str, cancellation: Cancellation) -> None:
        if len(content.encode()) > 1_000_000:
            raise ValueError("file objective too large")
        parts = self.parts(relative)
        with self.checked_directory("/".join(parts[:-1]) or ".", True) as parent:
            target = parent / parts[-1]
            if target.exists() or target.is_symlink():
                if is_reparse(target):
                    raise PermissionError("reparse point denied")
                if not target.is_file():
                    raise ValueError("regular file required")
            temporary = parent / (".oscar-" + new_id())
            try:
                with temporary.open("xb") as stream:
                    stream.write(content.encode())
                    stream.flush()
                    os.fsync(stream.fileno())
                cancellation.check()
                # Replace replaces the directory entry rather than following a leaf link.
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
