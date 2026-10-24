"""Trusted account-to-profile binding, outside the executable's artifact workspace."""

import hashlib
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .accounts import AccountRegistry
from .cloud_state import DataDirectoryLock
from .windows_files import WindowsScopedFiles, is_reparse


class BrowserProfiles:
    def __init__(
        self,
        accounts: AccountRegistry | None,
        root: Path,
        *,
        authorize: Callable[[str, int], None] | None = None,
    ):
        if (accounts is None) == (authorize is None):
            raise ValueError("one authoritative account checker required")
        self.accounts = accounts
        self.authorize = authorize
        self.root = Path(os.path.abspath(root))

    def check(self, parameters: dict[str, Any]) -> str:
        required = {"request", "account_id", "account_generation"}
        if not required <= parameters.keys() or parameters.keys() - required - {"verification"}:
            raise PermissionError("exact account-bound browser request required")
        identifier, generation = parameters["account_id"], parameters["account_generation"]
        if (
            not isinstance(identifier, str)
            or not identifier
            or type(generation) is not int
            or generation < 1
        ):
            raise PermissionError("current account identity required")
        if self.authorize is not None:
            self.authorize(identifier, generation)
        else:
            assert self.accounts is not None
            account = self.accounts.check(identifier, generation)
            identifier, generation = account.id, account.generation
        # Generation changes cannot silently reuse a previously authenticated profile.
        return hashlib.sha256((identifier + ":" + str(generation)).encode()).hexdigest()

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
