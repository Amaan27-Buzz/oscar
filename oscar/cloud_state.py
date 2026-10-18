"""Single-writer Cloud Core state and stopped-service, WAL-safe backup/restore.

Snapshots contain private canonical history and must be protected like the data
volume. External provider secrets are injected separately and are not restored.
The lock coordinates OSCAR service/maintenance processes on one local filesystem;
it is not distributed fencing for cloned volumes or network filesystems.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
from importlib import import_module
from pathlib import Path, PurePosixPath
from types import TracebackType
from typing import BinaryIO

from .event_archive import EventArchive
from .storage import StateConflict, Store

STATE_NAME = "core.sqlite"
ARCHIVE_NAME = "core.archive.sqlite"
IDENTITY_NAME = "core-identity.json"
LOCK_NAME = ".core.lock"
MANIFEST_NAME = "backup-manifest.json"


class DataDirectoryLock:
    """Hold for the full service lifetime; never unlink a possibly locked inode."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.file: BinaryIO | None = None

    def __enter__(self) -> "DataDirectoryLock":
        if self.data_dir.is_symlink():
            raise StateConflict("data directory must not be a symlink")
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.data_dir / LOCK_NAME
        if path.is_symlink():
            raise StateConflict("Core lock must not be a symlink")
        handle = path.open("a+b")
        try:
            path.chmod(0o600)
            if path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                msvcrt = import_module("msvcrt")
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl = import_module("fcntl")
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as failure:
            handle.close()
            raise StateConflict(
                "Core state is already in use; stop service before maintenance"
            ) from failure
        self.file = handle
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.file:
            self.file.close()
            self.file = None


def _core_id(identifier: object) -> str:
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", identifier):
        raise ValueError("explicit bounded Core identity required")
    return identifier


def _sync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _read_identity(data_dir: Path) -> str:
    path = data_dir / IDENTITY_NAME
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024:
        raise StateConflict("missing or invalid Core identity; restore a complete volume")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"version", "core_id"} or value["version"] != 1:
        raise StateConflict("unsupported Core identity")
    return _core_id(value["core_id"])


def initialize_identity(
    data_dir: Path, configured_core_id: str, *, initialize: bool = False
) -> str:
    """Call under DataDirectoryLock; never manufacture an owner or enroll authority.

    Initialization creates only empty existing Store/archive schemas and a configured
    installation identity. Partial/mismatched volumes require explicit recovery.
    """
    identifier = _core_id(configured_core_id)
    if (data_dir / IDENTITY_NAME).exists():
        if _read_identity(data_dir) != identifier:
            raise StateConflict("configured Core identity does not match persistent volume")
        validate_state(data_dir)
        return identifier
    if not initialize:
        raise StateConflict("Core is not initialized; explicit initialization required")
    if any(path.name != LOCK_NAME for path in data_dir.iterdir()):
        raise StateConflict("initialization requires an empty data directory")
    store = Store(data_dir / STATE_NAME)
    try:
        store.put("cloud_identity", "core", {"id": identifier, "version": 1})
        archive = EventArchive(data_dir / ARCHIVE_NAME)
        try:
            with archive.db:
                archive.db.execute(
                    "INSERT INTO archive_metadata(key,value) VALUES('cloud_core_id',?)",
                    (identifier,),
                )
        finally:
            archive.close()
    finally:
        store.close()
    path = data_dir / IDENTITY_NAME
    with path.open("x", encoding="utf-8") as handle:
        path.chmod(0o600)
        json.dump({"version": 1, "core_id": identifier}, handle)
        handle.flush()
        os.fsync(handle.fileno())
    _sync_directory(data_dir)
    validate_state(data_dir)
    return identifier


def _database(path: Path) -> sqlite3.Connection:
    if path.is_symlink() or not path.is_file():
        raise StateConflict("incomplete Core volume; both canonical databases are required")
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)


def validate_state(data_dir: Path) -> str:
    """Read-only independent schema, integrity, FTS5 and identity verification."""
    identifier = _read_identity(data_dir)
    for filename in (STATE_NAME, ARCHIVE_NAME):
        connection = _database(data_dir / filename)
        try:
            if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise StateConflict("unsupported Core database schema")
            if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise StateConflict("Core database integrity check failed")
            if connection.execute("PRAGMA foreign_key_check").fetchone():
                raise StateConflict("Core database foreign key check failed")
            if filename == STATE_NAME:
                row = connection.execute(
                    "SELECT data FROM records WHERE kind='cloud_identity' AND id='core'"
                ).fetchone()
                actual = json.loads(row[0]).get("id") if row else None
            else:
                row = connection.execute(
                    "SELECT value FROM archive_metadata WHERE key='cloud_core_id'"
                ).fetchone()
                actual = row[0] if row else None
                connection.execute(
                    "SELECT memory_id FROM archive_fts WHERE archive_fts MATCH ? LIMIT 1",
                    ('"compatibility"',),
                ).fetchall()
            if actual != identifier:
                raise StateConflict("canonical databases belong to a different Core identity")
        finally:
            connection.close()
    return identifier


def _files(root: Path) -> list[Path]:
    if root.is_symlink() or root.is_junction() or not root.is_dir():
        raise StateConflict("state snapshots require a regular directory")
    paths = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise StateConflict("state snapshots reject symlinks and junctions")
        if path.is_dir():
            continue
        if not path.is_file():
            raise StateConflict("state snapshots require regular files")
        paths.append(path)
    return paths


def _hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _publish(staging: Path, destination: Path) -> None:
    for path in _files(staging):
        with path.open("r+b") as handle:
            os.fsync(handle.fileno())
    for path in sorted(staging.rglob("*"), reverse=True):
        if path.is_dir():
            _sync_directory(path)
    _sync_directory(staging)
    staging.rename(destination)
    _sync_directory(destination.parent)


def _separate(source: Path, destination: Path) -> None:
    if (
        source.resolve() == destination.resolve()
        or source.resolve() in destination.resolve().parents
    ):
        raise ValueError("snapshot/restore destination must be outside source directory")
    if destination.exists():
        raise FileExistsError("destination must not exist; existing state is never overwritten")


def backup_state(data_dir: Path, destination: Path) -> None:
    """Stop service first. Lock excludes live writers across both canonical databases."""
    _separate(data_dir, destination)
    with DataDirectoryLock(data_dir):
        if (data_dir / MANIFEST_NAME).exists():
            raise StateConflict("backup manifest is reserved for snapshot directories")
        identifier = validate_state(data_dir)
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        staging = Path(tempfile.mkdtemp(prefix=".oscar-backup-", dir=destination.parent))
        try:
            for source in _files(data_dir):
                if (
                    source == data_dir / LOCK_NAME
                    or source.name
                    in {
                        name + suffix
                        for name in (STATE_NAME, ARCHIVE_NAME)
                        for suffix in ("-wal", "-shm")
                    }
                    and source.parent == data_dir
                ):
                    continue
                target = staging / source.relative_to(data_dir)
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                if source.name in {STATE_NAME, ARCHIVE_NAME} and source.parent == data_dir:
                    connection = _database(source)
                    snapshot = sqlite3.connect(target)
                    try:
                        connection.backup(snapshot)
                    finally:
                        snapshot.close()
                        connection.close()
                else:
                    shutil.copyfile(source, target)
                target.chmod(0o600)
            validate_state(staging)
            manifest = {
                "version": 1,
                "core_id": identifier,
                "files": {p.relative_to(staging).as_posix(): _hash(p) for p in _files(staging)},
            }
            path = staging / MANIFEST_NAME
            path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
            path.chmod(0o600)
            _publish(staging, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)


def restore_state(snapshot: Path, destination: Path) -> None:
    """Validate a trusted snapshot and atomically publish to a new offline volume.

    Never start the original and restored volumes together: filesystem locks cannot
    fence independent copies. Transfer ownership before starting restored OSCAR.
    """
    _separate(snapshot, destination)
    paths = _files(snapshot)
    manifest_path = snapshot / MANIFEST_NAME
    if manifest_path.stat().st_size > 16_000_000:
        raise ValueError("backup manifest exceeds bound")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"version", "core_id", "files"}
        or manifest["version"] != 1
        or not isinstance(manifest["files"], dict)
    ):
        raise ValueError("unsupported backup manifest")
    files = manifest["files"]
    if set(files) != {p.relative_to(snapshot).as_posix() for p in paths if p != manifest_path}:
        raise ValueError("backup file inventory mismatch")
    for relative, expected in files.items():
        parts = PurePosixPath(relative)
        if (
            parts.is_absolute()
            or ".." in parts.parts
            or "\\" in relative
            or ":" in relative
            or parts.as_posix() != relative
            or not isinstance(expected, str)
            or not re.fullmatch(r"[a-f0-9]{64}", expected)
            or _hash(snapshot / relative) != expected
        ):
            raise ValueError("backup file hash or path validation failed")
    if validate_state(snapshot) != manifest["core_id"]:
        raise StateConflict("backup identity mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix=".oscar-restore-", dir=destination.parent))
    try:
        for relative, expected in files.items():
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(snapshot / relative, target)
            target.chmod(0o600)
            if _hash(target) != expected:
                raise ValueError("backup changed during restore")
        validate_state(staging)
        # A backup cannot restore old device authority or reusable enrollment proofs.
        recovered = Store(staging / STATE_NAME)
        try:
            with recovered.transaction():
                devices = {r["node_id"] for r in recovered.all("remote_device")}
                for session in recovered.all("session"):
                    if session["node_id"] in devices:
                        recovered.put("session", session["id"], {**session, "revoked": True})
                for invitation in recovered.all("remote_invitation"):
                    recovered.delete("remote_invitation", invitation["id"])
        finally:
            recovered.close()
        _publish(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("backup", "restore"))
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.operation == "backup":
            backup_state(args.data_dir, args.backup)
        else:
            restore_state(args.backup, args.data_dir)
    except (OSError, ValueError, sqlite3.Error, StateConflict):
        parser.exit(
            1, "state maintenance failed; check offline volume, identity and backup integrity\n"
        )
    print(json.dumps({"operation": args.operation, "status": "verified"}))


if __name__ == "__main__":
    main()
