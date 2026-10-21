"""Writable account credentials encrypted under a separately protected service key."""

import json
import math
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from time import time
from typing import TYPE_CHECKING

from .credentials import SecretMaterial
from .secure_credentials import InjectedCredentialStore, SecretValue

if TYPE_CHECKING:
    from .oauth_device import Vault


class EncryptedCredentialStore:
    def __init__(self, root: Path, key: bytes, fallback: "Vault"):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if len(key) != 32:
            raise ValueError("separately protected 256-bit credential key required")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        InjectedCredentialStore._check(root, directory=True)
        self.root, self.cipher, self.fallback = root, AESGCM(key), fallback
        self.material = SecretMaterial()

    def path(self, reference: str) -> Path:
        if not isinstance(reference, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", reference):
            raise ValueError("opaque credential reference required")
        InjectedCredentialStore._check(self.root, directory=True)
        return self.root / reference

    @staticmethod
    def payload(secret: str, expiry: float | None) -> dict[str, str | float | None]:
        if (
            not isinstance(secret, str)
            or not secret
            or "\x00" in secret
            or len(secret.encode()) > 16384
            or expiry is not None
            and (
                type(expiry) not in {int, float}
                or not math.isfinite(expiry)
                or not 0 <= expiry <= 10**12
            )
        ):
            raise ValueError("bounded credential payload required")
        return {"secret": secret, "expires_at": expiry}

    def put(
        self, secret: str, *, expires_at: float | None = None, reference: str | None = None
    ) -> str:
        reference = reference if reference is not None else secrets.token_hex(16)
        path = self.path(reference)
        payload = json.dumps(self.payload(secret, expires_at)).encode()
        self.material.remember(secret)
        nonce = secrets.token_bytes(12)
        encrypted = nonce + self.cipher.encrypt(nonce, payload, reference.encode())
        temporary = self.root / ("pending_" + secrets.token_hex(16))
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encrypted)
                stream.flush()
                os.fsync(stream.fileno())
            if path.exists() or path.is_symlink():
                InjectedCredentialStore._check(path)
            os.replace(temporary, path)
            if sys.platform != "win32":
                directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)
        return reference

    def read(self, reference: str, *, allow_expired: bool = False) -> SecretValue:
        from cryptography.exceptions import InvalidTag

        path = self.path(reference)
        try:
            InjectedCredentialStore._check(path)
            descriptor = os.open(
                path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            )
        except FileNotFoundError:
            return self.fallback.read(reference, allow_expired=allow_expired)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or sys.platform != "win32"
                and (metadata.st_uid not in {0, os.geteuid()} or metadata.st_mode & 0o077)
            ):
                raise PermissionError("private regular credential mount required")
            encrypted = stream.read(32769)
        if not 28 <= len(encrypted) <= 32768:
            raise PermissionError("credential integrity check failed")
        try:
            data = json.loads(
                self.cipher.decrypt(encrypted[:12], encrypted[12:], reference.encode())
            )
        except (InvalidTag, ValueError, UnicodeError):
            raise PermissionError("credential integrity check failed") from None
        if not isinstance(data, dict) or set(data) != {"secret", "expires_at"}:
            raise PermissionError("credential integrity check failed")
        self.payload(data["secret"], data["expires_at"])
        if not allow_expired and data["expires_at"] is not None and data["expires_at"] <= time():
            raise PermissionError("credential expired")
        self.material.remember(data["secret"])
        return SecretValue(data["secret"])

    def delete(self, reference: str) -> None:
        path = self.path(reference)
        try:
            InjectedCredentialStore._check(path)
        except FileNotFoundError:
            try:
                self.fallback.read(reference, allow_expired=True)
            except KeyError:
                return
            self.fallback.delete(reference)
        else:
            path.unlink()
