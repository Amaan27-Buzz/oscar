"""Windows Credential Manager. Durable OSCAR records carry opaque references only."""

import ctypes
import json
import os
from ctypes import wintypes
from dataclasses import dataclass
from time import time
from typing import Any
from uuid import uuid4


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


class WindowsCredentialStore:
    PREFIX = "OSCAR/credential/"

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("native Windows secure credential store unavailable")
        win32: Any = ctypes
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
            return SecretValue(str(data["secret"]))
        finally:
            self.api.CredFree(pointer)

    def delete(self, reference: str) -> None:
        if not self.api.CredDeleteW(self._target(reference), 1, 0):
            # Deletion is idempotent only for the documented missing-item error.
            win32: Any = ctypes
            if win32.get_last_error() != 1168:
                raise OSError("native credential deletion failed")
