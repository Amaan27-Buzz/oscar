"""Real deterministic executors and independent verifiers under an explicit filesystem scope."""

import hashlib
import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from time import time
from typing import Any, Protocol

from .contracts import (
    Action,
    ArtifactRef,
    Epistemic,
    Evidence,
    Objective,
    Result,
    TaskState,
    Verification,
    new_id,
)
from .storage import Store


class Cancelled(Exception):
    pass


class Cancellation:
    def __init__(self, store: Store, task_id: str, authorize: Callable[[], None] | None = None):
        self.store, self.task_id = store, task_id
        self.authorize = authorize

    def check(self) -> None:
        if self.store.task(self.task_id).cancelled:
            raise Cancelled("task cancelled")
        if self.authorize is not None:
            try:
                self.authorize()
            except (PermissionError, KeyError):
                raise Cancelled("execution authorization revoked or expired") from None


class Executor(Protocol):
    def __call__(self, action: Action, cancellation: Cancellation) -> Result: ...


_posix_os: Any = os


class ScopedFiles:
    """Directory-FD operations reject symlinks and traversal, including parent symlinks."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def __new__(cls, root: Path) -> "ScopedFiles":
        if os.name == "nt" and cls is ScopedFiles:
            from .windows_files import WindowsScopedFiles

            return super().__new__(WindowsScopedFiles)
        return super().__new__(cls)

    def exists(self, relative: str) -> bool:
        with self.parent(relative) as (parent, name):
            try:
                os.stat(name, dir_fd=parent, follow_symlinks=False)
                return True
            except FileNotFoundError:
                return False

    def names(self, relative: str, pattern: str) -> list[str]:
        with self.directory(relative) as descriptor, os.scandir(descriptor) as entries:
            names: list[str] = []
            for scanned, entry in enumerate(entries):
                if scanned >= 10_000 or len(names) >= 500:
                    raise ValueError("directory result bound exceeded")
                if not entry.is_symlink() and pattern in entry.name:
                    names.append(entry.name)
            return sorted(names)

    @staticmethod
    def parts(relative: str) -> list[str]:
        if not isinstance(relative, str):
            raise ValueError("text workspace path required")
        parts = relative.split("/")
        if (
            not relative
            or relative.startswith("/")
            or any(p in {"", ".", ".."} for p in parts)
            or "\x00" in relative
            or "\\" in relative
        ):
            raise ValueError("path outside authorized workspace")
        return parts

    @contextmanager
    def parent(self, relative: str, create: bool = False) -> Iterator[tuple[int, str]]:
        parts = self.parts(relative)
        descriptor = os.open(self.root, os.O_RDONLY | _posix_os.O_DIRECTORY | _posix_os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=descriptor)
                    except FileExistsError:
                        pass
                next_fd = os.open(
                    part,
                    os.O_RDONLY | _posix_os.O_DIRECTORY | _posix_os.O_NOFOLLOW,
                    dir_fd=descriptor,
                )
                os.close(descriptor)
                descriptor = next_fd
            yield descriptor, parts[-1]
        finally:
            os.close(descriptor)

    @contextmanager
    def directory(self, relative: str = ".") -> Iterator[int]:
        """Scoped directory descriptor for race-resistant listing/search."""
        if relative == ".":
            descriptor = os.open(
                self.root, os.O_RDONLY | _posix_os.O_DIRECTORY | _posix_os.O_NOFOLLOW
            )
        else:
            with self.parent(relative) as (parent, name):
                descriptor = os.open(
                    name, os.O_RDONLY | _posix_os.O_DIRECTORY | _posix_os.O_NOFOLLOW, dir_fd=parent
                )
        try:
            yield descriptor
        finally:
            os.close(descriptor)

    def write(self, relative: str, content: str, cancellation: Cancellation) -> None:
        if len(content.encode()) > 1_000_000:
            raise ValueError("file objective too large")
        with self.parent(relative, create=True) as (parent, name):
            temp_name = f".oscar-{new_id()}"
            descriptor = os.open(
                temp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | _posix_os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            try:
                with os.fdopen(descriptor, "wb") as file:
                    file.write(content.encode())
                    file.flush()
                    os.fsync(file.fileno())
                cancellation.check()
                os.replace(temp_name, name, src_dir_fd=parent, dst_dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temp_name, dir_fd=parent)
                except FileNotFoundError:
                    pass

    def read(self, relative: str) -> bytes:
        with self.parent(relative) as (parent, name):
            descriptor = os.open(
                name, os.O_RDONLY | _posix_os.O_NOFOLLOW | _posix_os.O_NONBLOCK, dir_fd=parent
            )
            with os.fdopen(descriptor, "rb") as file:
                import stat

                if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                    raise ValueError("verification target must be a regular file")
                return file.read(1_000_001)


class FileExecutor:
    def __init__(self, files: ScopedFiles):
        self.files = files

    def __call__(self, action: Action, cancellation: Cancellation) -> Result:
        if set(action.parameters) != {"path", "content"} or not all(
            isinstance(v, str) for v in action.parameters.values()
        ):
            raise ValueError("invalid file action parameters")
        cancellation.check()
        self.files.write(action.parameters["path"], action.parameters["content"], cancellation)
        artifact = ArtifactRef(
            new_id(),
            action.task_id,
            action.capability_id,
            "file",
            str(self.files.root / action.parameters["path"]),
            time(),
        )
        return Result(
            new_id(),
            action.id,
            action.task_id,
            action.correlation_id,
            action.capability_id,
            True,
            artifact=artifact,
        )


def addition_operands(text: str) -> tuple[int, int]:
    match = re.fullmatch(r"(?:what is\s+)?(\d{1,12})\s*\+\s*(\d{1,12})\??", text.lower().strip())
    if not match:
        raise ValueError("unsupported arithmetic expression")
    return int(match[1]), int(match[2])


def addition_executor(action: Action, cancellation: Cancellation) -> Result:
    cancellation.check()
    a, b = addition_operands(action.parameters["expression"])
    return Result(
        new_id(),
        action.id,
        action.task_id,
        action.correlation_id,
        action.capability_id,
        True,
        value=str(a + b),
    )


class Verifier:
    def __init__(self, files: ScopedFiles, clock: Callable[[], float] = time):
        self.files, self.clock = files, clock

    def bind_task(self, task_id: str, parameters: dict[str, Any]) -> None:
        """Bind transient verification resources to the durable task lifecycle."""

    def release_task(self, task_id: str) -> None:
        """Release private resources after completion, failure or cancellation."""

    def verify(self, objective: Objective, result: Result) -> Verification:
        criterion = objective.criterion
        matches: bool | None = None
        content_hash: str | None = None
        artifact_id: str | None = None
        method, detail = "unavailable", "no independent objective verifier configured"
        state, status = TaskState.PARTIALLY_VERIFIED, Epistemic.REPORTED
        if criterion["kind"] == "file_exact":
            if (
                result.artifact
                and result.artifact.kind == "file"
                and result.artifact.task_id == result.task_id
                and result.artifact.location == str(self.files.root / criterion["path"])
            ):
                artifact_id = result.artifact.id
            method = "independent file read and exact byte comparison"
            try:
                actual = self.files.read(criterion["path"])
                content_hash = hashlib.sha256(actual).hexdigest()
                matches = actual == criterion["content"].encode()
                detail = "exact bytes match" if matches else "file contents differ"
            except FileNotFoundError:
                matches, detail = False, "expected file does not exist"
            except (PermissionError, OSError, ValueError):
                detail = "authoritative file state cannot be inspected"
            if matches is not None:
                state = TaskState.VERIFIED if matches else TaskState.FAILED
                status = Epistemic.VERIFIED if matches else Epistemic.KNOWN
        elif criterion["kind"] == "addition":
            a, b = addition_operands(criterion["expression"])
            # Independent decimal-column addition, not the executor's result/message.
            carry, digits = 0, []
            for x, y in zip(str(a)[::-1].ljust(13, "0"), str(b)[::-1].ljust(13, "0"), strict=True):
                carry, digit = divmod(int(x) + int(y) + carry, 10)
                digits.append(str(digit))
            expected = "".join(reversed(digits)).lstrip("0") or "0"
            matches = result.value == expected
            method, detail = "independent decimal-column addition", "arithmetic result compared"
            state = TaskState.VERIFIED if matches else TaskState.FAILED
            status = Epistemic.VERIFIED if matches else Epistemic.KNOWN
        evidence = Evidence(
            new_id(),
            result.task_id,
            result.correlation_id,
            "independent-verifier",
            method,
            self.clock(),
            matches,
            status,
            detail,
            artifact_id,
            content_hash,
        )
        return Verification(state, evidence)
