"""Native and deployment-injected credentials; durable records hold opaque references."""

import ctypes
import json
import math
import os
import re
import stat
import sys
from collections.abc import Callable
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from .credentials import SecretMaterial


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


@dataclass(frozen=True)
class SecretValue:
    value: str

    def __repr__(self) -> str:
        return "SecretValue(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"


class InjectedCredentialStore:
    """Read-only private JSON secret mounts, administered outside the Core API.

    Each opaque reference names a file containing secret and expires_at fields.
    Reads reopen the mount so replacement, expiry and removal take effect immediately.
    This is a server injection adapter, not an enrollment or writable Linux keychain.
    """

    def __init__(self, root: Path, *, clock: Callable[[], float] = time):
        self.root, self.clock = root, clock
        self.material = SecretMaterial()
        self._check(root, directory=True)

    @staticmethod
    def _check(path: Path, *, directory: bool = False) -> None:
        metadata = path.lstat()
        expected = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected(metadata.st_mode):
            raise PermissionError("private regular credential mount required")
        if sys.platform != "win32" and (
            metadata.st_uid not in {0, os.geteuid()} or metadata.st_mode & 0o077
        ):
            raise PermissionError("credential mount must be private to root or service owner")

    def read(self, reference: str, *, allow_expired: bool = False) -> SecretValue:
        if not isinstance(reference, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", reference):
            raise ValueError("opaque credential reference required")
        self._check(self.root, directory=True)
        path = self.root / reference
        try:
            self._check(path)
            descriptor = os.open(
                path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            )
        except FileNotFoundError:
            raise KeyError("OSCAR credential unavailable") from None
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or sys.platform != "win32"
                and (metadata.st_uid not in {0, os.geteuid()} or metadata.st_mode & 0o077)
            ):
                raise PermissionError("private regular credential mount required")
            raw = stream.read(4097)
        if len(raw) > 4096:
            raise ValueError("bounded credential payload required")
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ValueError("invalid credential payload") from None
        if not isinstance(data, dict) or set(data) != {"secret", "expires_at"}:
            raise ValueError("explicit credential payload fields required")
        secret, expiry = data["secret"], data["expires_at"]
        if (
            not isinstance(secret, str)
            or not secret
            or len(secret.encode()) > 2000
            or "\x00" in secret
            or expiry is not None
            and (
                type(expiry) not in {int, float}
                or expiry < 0
                or expiry > 10**12
                or not math.isfinite(expiry)
            )
        ):
            raise ValueError("bounded credential payload required")
        if not allow_expired and expiry is not None and expiry <= self.clock():
            raise PermissionError("credential expired")
        self.material.remember(secret)
        return SecretValue(secret)

    def put(
        self, secret: str, *, expires_at: float | None = None, reference: str | None = None
    ) -> str:
        raise PermissionError("credential injection is administered outside the Core")

    def delete(self, reference: str) -> None:
        raise PermissionError("credential revocation requires removing the administered mount")


class WindowsCredentialStore:
    PREFIX = "OSCAR/credential/"

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("native Windows secure credential store unavailable")
        win32: Any = ctypes
        self.material = SecretMaterial()
        self.api = win32.WinDLL("advapi32", use_last_error=True)
        pointer = ctypes.POINTER(_Credential)
        self.api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
        self.api.CredWriteW.restype = wintypes.BOOL
        self.api.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(pointer),
        ]
        self.api.CredReadW.restype = wintypes.BOOL
        self.api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.api.CredDeleteW.restype = wintypes.BOOL
        self.api.CredFree.argtypes = [ctypes.c_void_p]

    def _target(self, reference: str) -> str:
        if len(reference) != 32 or any(c not in "0123456789abcdef" for c in reference):
            raise ValueError("opaque OSCAR credential reference required")
        return self.PREFIX + reference

    def put(
        self, secret: str, *, expires_at: float | None = None, reference: str | None = None
    ) -> str:
        reference = reference or uuid4().hex
        target = self._target(reference)
        payload = json.dumps({"secret": secret, "expires_at": expires_at}).encode()
        if not secret or "\x00" in secret or len(payload) > 2500:
            raise ValueError("bounded credential payload required")
        self.material.remember(secret)
        blob = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
        credential = _Credential()
        credential.Type, credential.TargetName = 1, target
        credential.CredentialBlobSize, credential.CredentialBlob = len(payload), blob
        credential.Persist, credential.UserName = 2, "OSCAR"
        if not self.api.CredWriteW(ctypes.byref(credential), 0):
            raise OSError("native credential write failed")
        return reference

    def read(self, reference: str, *, allow_expired: bool = False) -> SecretValue:
        target = self._target(reference)
        pointer = ctypes.POINTER(_Credential)()
        if not self.api.CredReadW(target, 1, 0, ctypes.byref(pointer)):
            raise KeyError("OSCAR credential unavailable")
        try:
            data = json.loads(
                ctypes.string_at(
                    pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize
                )
            )
            if (
                not allow_expired
                and data["expires_at"] is not None
                and data["expires_at"] <= time()
            ):
                raise PermissionError("credential expired")
            value = str(data["secret"])
            self.material.remember(value)
            return SecretValue(value)
        finally:
            self.api.CredFree(pointer)

    def delete(self, reference: str) -> None:
        if not self.api.CredDeleteW(self._target(reference), 1, 0):
            # Deletion is idempotent only for the documented missing-item error.
            win32: Any = ctypes
            if win32.get_last_error() != 1168:
                raise OSError("native credential deletion failed")
