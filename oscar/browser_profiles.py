"""Trusted account-to-profile binding, outside the executable's artifact workspace."""

import hashlib
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .accounts import AccountRegistry
from .cloud_state import DataDirectoryLock
from .windows_files import WindowsScopedFiles, is_reparse


class BrowserProfiles:
    def __init__(self, accounts: AccountRegistry, root: Path):
        self.accounts = accounts
        self.root = Path(os.path.abspath(root))

    def check(self, parameters: dict[str, Any]) -> str:
        if set(parameters) != {"request", "account_id", "account_generation"}:
            raise PermissionError("exact account-bound browser request required")
        account = self.accounts.check(parameters["account_id"], parameters["account_generation"])
        # Generation changes cannot silently reuse a previously authenticated profile.
        return hashlib.sha256((account.id + ":" + str(account.generation)).encode()).hexdigest()

    @contextmanager
    def open(self, parameters: dict[str, Any], workspace: Path) -> Iterator[Path]:
        name = self.check(parameters)
        workspace = workspace.resolve()
        if self.root.is_relative_to(workspace) or workspace.is_relative_to(self.root):
            raise PermissionError("browser credentials must be separate from artifacts")
        if os.name == "nt":
            files = WindowsScopedFiles(self.root)
            with files.checked_directory(name, create=True) as directory:
                with DataDirectoryLock(directory):
                    if (directory / "chromium").exists() and is_reparse(directory / "chromium"):
                        raise PermissionError("browser profile reparse rejected")
                    yield directory / "chromium"
        else:
            # Pin and reject each symlink ancestor before Chromium receives the path.
            for ancestor in [*reversed(self.root.parents), self.root]:
                if ancestor.is_symlink():
                    raise PermissionError("browser profile symlink rejected")
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            directory = self.root / name
            if directory.is_symlink():
                raise PermissionError("browser profile symlink rejected")
            with DataDirectoryLock(directory):
                if directory.stat().st_mode & 0o077:
                    raise PermissionError("browser profile must be private")
                if (directory / "chromium").is_symlink():
                    raise PermissionError("browser profile symlink rejected")
                yield directory / "chromium"
