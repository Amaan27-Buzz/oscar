"""SQLite authority for tasks, ledger, deduplication, leases and content-free route history."""

import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Protocol
from weakref import WeakSet

from .contracts import TERMINAL, TRANSITIONS, Evidence, Task, TaskState, record


class StateConflict(Exception):
    pass


class TaskResources(Protocol):
    """Transient owners observe committed task transitions, never persist their content."""

    def task_transitioned(self, task: Task) -> None: ...


class Store:
    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=5)
        path.chmod(0o600)
        self.lock = RLock()
        self.close_callbacks: list[Callable[[], None]] = []
        self._closed = False
        self.task_resources: WeakSet[TaskResources] = WeakSet()
        # Process-local private payloads. Durable plans carry only a digest; restart fails closed.
        self.transient: dict[str, dict[str, Any]] = {}
        if self.db.execute("PRAGMA user_version").fetchone()[0] not in {0, 1}:
            self.db.close()
            raise StateConflict("unsupported storage schema; explicit migration required")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS records (
                kind TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL,
                PRIMARY KEY(kind, id)
            );
            CREATE TABLE IF NOT EXISTS audit (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL, event TEXT NOT NULL, data TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS tasks_by_state
                ON records(json_extract(data,'$.state')) WHERE kind='task';
            CREATE INDEX IF NOT EXISTS live_leases_by_expiry
                ON records(json_extract(data,'$.expires_at'))
                WHERE kind='lease' AND json_extract(data,'$.active')=1;
            CREATE TABLE IF NOT EXISTS dedup (
                key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                action_id TEXT NOT NULL, state TEXT NOT NULL, result TEXT
            );
            CREATE TABLE IF NOT EXISTS nonces (
                session_id TEXT NOT NULL, nonce TEXT NOT NULL,
                PRIMARY KEY(session_id, nonce)
            );
            PRAGMA user_version=1;
        """)

    @contextmanager
    def transaction(self, *, write: bool = True) -> Iterator[None]:
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            try:
                yield
            except BaseException:
                self.db.execute("ROLLBACK")
                raise
            else:
                self.db.execute("COMMIT")

    def close(self) -> None:
        if self._closed:
            return
        # Stop resource owners before closing the database they use; never join under its lock.
        for callback in list(self.close_callbacks):
            callback()
        self.close_callbacks.clear()
        self.transient.clear()
        with self.lock:
            self.db.close()
            self._closed = True

    def put(self, kind: str, identifier: str, data: dict[str, Any]) -> None:
        with self.lock:
            self.db.execute(
                "INSERT INTO records VALUES (?, ?, ?) "
                "ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data",
                (kind, identifier, json.dumps(data, allow_nan=False)),
            )

    def delete(self, kind: str, identifier: str) -> None:
        """Delete the live record; does not claim secure erasure of WAL/backups."""
        with self.lock:
            self.db.execute("DELETE FROM records WHERE kind=? AND id=?", (kind, identifier))

    def get(self, kind: str, identifier: str) -> dict[str, Any]:
        with self.lock:
            row = self.db.execute(
                "SELECT data FROM records WHERE kind=? AND id=?", (kind, identifier)
            ).fetchone()
        if row is None:
            raise KeyError(f"missing {kind}")
        return dict(json.loads(row[0]))

    def all(self, kind: str) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.db.execute(
                "SELECT data FROM records WHERE kind=? ORDER BY rowid", (kind,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def task(self, identifier: str) -> Task:
        return Task.from_dict(self.get("task", identifier))

    def audit(self, task_id: str, event: str, data: dict[str, Any]) -> None:
        with self.lock:
            self.db.execute(
                "INSERT INTO audit(task_id,event,data) VALUES (?, ?, ?)",
                (task_id, event, json.dumps(data, allow_nan=False)),
            )

    def ledger(self, task_id: str) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.db.execute(
                "SELECT sequence,event,data FROM audit WHERE task_id=? ORDER BY sequence",
                (task_id,),
            ).fetchall()
        return [{"sequence": r[0], "event": r[1], **json.loads(r[2])} for r in rows]

    def transition(
        self,
        identifier: str,
        state: TaskState,
        *,
        blocker: str | None = None,
        evidence: Evidence | None = None,
        expected: TaskState | None = None,
        expected_lease: str | None = None,
        expected_node: str | None = None,
    ) -> Task:
        with self.transaction():
            task = self.task(identifier)
            if expected_node is not None:
                lease = self.get("lease", task.lease_id or "")
                if lease["node_id"] != expected_node:
                    raise PermissionError("task executor changed outside owner control target")
            if expected is not None and task.state != expected:
                raise StateConflict("task state changed; another runner may own it")
            if expected_lease is not None and task.lease_id != expected_lease:
                raise StateConflict("task lease changed; stale runner rejected")
            if evidence is not None and (
                evidence.task_id != task.id or evidence.correlation_id != task.correlation_id
            ):
                raise StateConflict("evidence correlation does not match task")
            if task.state == state:
                return task
            if task.cancelled or task.state in TERMINAL:
                raise StateConflict("task is terminal")
            if state != TaskState.CANCELLED and state not in TRANSITIONS.get(task.state, set()):
                raise StateConflict(f"invalid transition {task.state} -> {state}")
            if state == TaskState.VERIFIED:
                if evidence is None or evidence.task_id != task.id or evidence.matches is not True:
                    raise StateConflict("verified requires matching independent evidence")
                if evidence.status != "VERIFIED":
                    raise StateConflict("verified requires verified evidence")
            previous = task.state
            task.state, task.blocker = state, blocker
            task.cancelled = state == TaskState.CANCELLED
            if state == TaskState.EXECUTING:
                if task.attempts >= task.retry_budget + 1:
                    raise StateConflict("retry budget exhausted")
                task.attempts += 1
            if evidence is not None:
                self.put("evidence", evidence.id, record(evidence))
            self.put("task", task.id, record(task))
            self.audit(
                task.id,
                "transition",
                {
                    "from": previous,
                    "to": state,
                    "blocker": blocker,
                    "evidence_id": evidence.id if evidence else None,
                    "correlation_id": task.correlation_id,
                },
            )
        # Notify only after commit; weak ownership cannot retain an abandoned Fabric.
        for resources in list(self.task_resources):
            resources.task_transitioned(task)
        return task

    def claim_action(self, key: str, fingerprint: str, action_id: str) -> dict[str, Any] | None:
        """Crash ambiguity blocks replay. Completed duplicates reuse the original result."""
        with self.transaction():
            row = self.db.execute(
                "SELECT fingerprint,state,result FROM dedup WHERE key=?", (key,)
            ).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise StateConflict("idempotency key reused with different action")
                if row[1] != "completed":
                    raise StateConflict(
                        "execution outcome unknown; independently inspect before replay"
                    )
                return dict(json.loads(row[2]))
            self.db.execute(
                "INSERT INTO dedup VALUES (?, ?, ?, 'started', NULL)",
                (key, fingerprint, action_id),
            )
        return None

    def complete_action(self, key: str, result: dict[str, Any]) -> None:
        with self.lock:
            self.db.execute(
                "UPDATE dedup SET state='completed',result=? WHERE key=?",
                (json.dumps(result), key),
            )

    def consume_nonce(self, session_id: str, nonce: str) -> None:
        try:
            with self.lock:
                self.db.execute("INSERT INTO nonces VALUES (?, ?)", (session_id, nonce))
        except sqlite3.IntegrityError:
            raise StateConflict("replayed message") from None
