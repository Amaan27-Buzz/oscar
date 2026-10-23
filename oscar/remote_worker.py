"""Outbound scoped file Worker; Core owns tasks, policy, leases and verification."""

import argparse
import ctypes
import json
import os
import random
import sqlite3
import ssl
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import Event
from time import time
from typing import Any, Protocol

from .capabilities import Cancellation, FileExecutor, ScopedFiles
from .contracts import Action, Capability, Result, new_id, record
from .mobile import fingerprint
from .storage import StateConflict


class WindowsNativeSigner:
    """Open the native app's existing nonexportable CNG key; never create authority."""

    def __init__(self, installation: str):
        if (
            os.name != "nt"
            or not installation
            or len(installation) > 80
            or any(not c.isascii() or not (c.isalnum() or c == "-") for c in installation)
        ):
            raise ValueError("Windows native installation required")
        win32: Any = ctypes
        self.cng = win32.WinDLL("ncrypt.dll")
        self.provider, self.key = ctypes.c_size_t(), ctypes.c_size_t()
        self.cng.NCryptOpenStorageProvider.argtypes = [
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_wchar_p,
            ctypes.c_uint32,
        ]
        self.cng.NCryptOpenKey.argtypes = [
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        self.cng.NCryptFreeObject.argtypes = [ctypes.c_size_t]
        self.cng.NCryptSignHash.argtypes = [
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_uint32,
        ]
        if self.cng.NCryptOpenStorageProvider(
            ctypes.byref(self.provider), "Microsoft Software Key Storage Provider", 0
        ):
            raise PermissionError("native key provider unavailable")
        if self.cng.NCryptOpenKey(
            self.provider,
            ctypes.byref(self.key),
            f"Dawnlight.OSCAR.{installation}-transport",
            0,
            64,
        ):
            self.close()
            raise PermissionError("native enrollment key unavailable; enroll in Desktop first")

    def close(self) -> None:
        for handle in (self.key, self.provider):
            if handle.value:
                self.cng.NCryptFreeObject(handle)
                handle.value = 0

    def __call__(self, body: bytes) -> bytes:
        import hashlib

        class PSS(ctypes.Structure):
            _fields_ = [("algorithm", ctypes.c_wchar_p), ("salt", ctypes.c_uint32)]

        if len(body) > 16384 or not self.key.value:
            raise PermissionError("native signing boundary rejected")
        digest = hashlib.sha256(body).digest()
        padding, size = PSS("SHA256", 32), ctypes.c_uint32()
        if self.cng.NCryptSignHash(
            self.key,
            ctypes.byref(padding),
            digest,
            len(digest),
            None,
            0,
            ctypes.byref(size),
            8 | 64,
        ):
            raise PermissionError("native proof unavailable")
        signature = ctypes.create_string_buffer(size.value)
        if self.cng.NCryptSignHash(
            self.key,
            ctypes.byref(padding),
            digest,
            len(digest),
            signature,
            size.value,
            ctypes.byref(size),
            8 | 64,
        ):
            raise PermissionError("native proof unavailable")
        return signature.raw[: size.value]


def native_connection(path: Path) -> dict[str, Any]:
    if os.name != "nt":
        raise OSError("Windows native credential storage required")
    raw = path.read_bytes()
    if not 0 < len(raw) <= 32768:
        raise ValueError("native credential boundary rejected")

    class Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_uint32), ("data", ctypes.c_void_p)]

    win32: Any = ctypes
    crypt, kernel = win32.WinDLL("crypt32.dll"), win32.WinDLL("kernel32.dll")
    crypt.CryptUnprotectData.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(Blob),
    ]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    source = ctypes.create_string_buffer(raw)
    original, output = Blob(len(raw), ctypes.cast(source, ctypes.c_void_p)), Blob()
    if not crypt.CryptUnprotectData(
        ctypes.byref(original), None, None, None, None, 1, ctypes.byref(output)
    ):
        raise PermissionError("native connection cannot be unlocked")
    try:
        if output.size > 32768:
            raise ValueError("native credential boundary rejected")
        value = json.loads(ctypes.string_at(output.data, output.size))
        if not isinstance(value, dict):
            raise ValueError("native connection object required")
        return dict(value)
    finally:
        ctypes.memset(output.data, 0, output.size)
        kernel.LocalFree(output.data)


class Client(Protocol):
    session: dict[str, Any]

    def request(
        self, operation: str, payload: dict[str, Any], request_id: str | None = None
    ) -> dict[str, Any]: ...


class RemoteCancellation(Cancellation):
    def __init__(self, check: Callable[[], None]):
        self.guard = check

    def check(self) -> None:
        self.guard()


class RemoteWorker:
    capability_ids = frozenset({"machine.files.read", "machine.files.write"})

    def __init__(
        self,
        client: Client,
        workspace: Path,
        workspace_id: str,
        journal: Path,
        *,
        capabilities: tuple[str, ...] = ("machine.files.read", "machine.files.write"),
        local_authorize: Callable[[Action], bool] | None = None,
    ):
        if not workspace.is_absolute() or not workspace.is_dir():
            raise ValueError("existing absolute workspace required")
        if not workspace_id or len(workspace_id) > 128:
            raise ValueError("bounded enrolled workspace identity required")
        if not capabilities or not set(capabilities) <= self.capability_ids:
            raise PermissionError("only explicitly enrolled capabilities are available")
        if journal.resolve().is_relative_to(workspace.resolve()):
            raise ValueError("execution journal must be outside the remotely writable workspace")
        self.client, self.workspace_id = client, workspace_id
        self.files = ScopedFiles(workspace)
        self.allowed = frozenset(capabilities)
        self.local_authorize = local_authorize
        self.journal = sqlite3.connect(journal, isolation_level=None)
        self.journal.execute("PRAGMA journal_mode=WAL")
        self.journal.execute("PRAGMA synchronous=FULL")
        self.journal.execute(
            "CREATE TABLE IF NOT EXISTS execution_claim "
            "(action_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT)"
        )
        self.status = "offline"

    def close(self) -> None:
        self.journal.close()

    def advertise(self) -> None:
        node = self.client.session["node_id"]
        capabilities = [
            record(
                Capability(
                    identifier,
                    identifier,
                    "Explicit scoped remote file operation",
                    "machine",
                    node,
                    ("files:write" if identifier.endswith("write") else "files:read",),
                    "file_write" if identifier.endswith("write") else "file_read",
                    "file" if identifier.endswith("write") else "reference",
                    "high" if identifier.endswith("write") else "low",
                )
            )
            for identifier in sorted(self.allowed)
        ]
        self.client.request(
            "advertise", {"workspace": self.workspace_id, "capabilities": capabilities}
        )
        self.status = "online"

    def validate(self, delivery: dict[str, Any]) -> Action:
        if set(delivery) - {"authority"} != {
            "id",
            "kind",
            "node_id",
            "session_id",
            "task_id",
            "action",
            "lease_id",
            "deadline_ms",
            "workspace",
            "review_digest",
            "approved",
            "parameters",
        }:
            raise ValueError("invalid delivery contract")
        authority = delivery.get("authority")
        if authority is not None:
            if (
                not isinstance(authority, dict)
                or set(authority)
                != {
                    "grant_id",
                    "epoch",
                    "mode",
                    "task_generation",
                    "owner_node",
                    "owner_session",
                    "expires_at_ms",
                }
                or (
                    authority["mode"] not in {"secure", "full"}
                    or type(authority["epoch"]) is not int
                    or authority["epoch"] < 1
                    or type(authority["task_generation"]) is not int
                    or authority["task_generation"] < 1
                    or type(authority["expires_at_ms"]) is not int
                    or authority["expires_at_ms"] <= time() * 1000
                    or any(
                        not isinstance(authority[k], str) or not authority[k]
                        for k in ("grant_id", "owner_node", "owner_session")
                    )
                )
            ):
                raise PermissionError("invalid or expired standing authority delivery")
        if (
            delivery["node_id"] != self.client.session["node_id"]
            or delivery["session_id"] != self.client.session["session_id"]
            or delivery["workspace"] != self.workspace_id
            or delivery["kind"] not in {"action", "readback"}
            or type(delivery["deadline_ms"]) is not int
            or not time() * 1000 < delivery["deadline_ms"] <= time() * 1000 + 120_000
            or not isinstance(delivery["lease_id"], str)
            or not delivery["lease_id"]
            or type(delivery["approved"]) is not bool
        ):
            raise PermissionError("delivery target, lease or deadline rejected")
        if not isinstance(delivery["action"], dict):
            raise ValueError("canonical action required")
        action = Action(**delivery["action"])
        if action.task_id != delivery["task_id"] or action.capability_id not in self.allowed:
            raise PermissionError("unadvertised or unrelated action")
        expected = fingerprint(
            {
                "action": record(action),
                "target": delivery["node_id"],
                "workspace": self.workspace_id,
                "deadline_ms": delivery["deadline_ms"],
            }
        )
        if delivery["review_digest"] != expected:
            raise PermissionError("exact action review digest mismatch")
        self.validate_effect(action, delivery)
        if self.local_authorize is not None and not self.local_authorize(action):
            raise PermissionError("local Personal Policy denied execution")
        return action

    def validate_effect(self, action: Action, delivery: dict[str, Any]) -> None:
        authority = delivery.get("authority")
        fields = {"path", "content"} if action.capability_id.endswith("write") else {"path"}
        parameters = action.parameters
        if not isinstance(parameters, dict) or set(parameters) != fields:
            raise ValueError("bounded file operation required")
        if not isinstance(parameters["path"], str) or not 0 < len(parameters["path"]) <= 240:
            raise ValueError("bounded relative file path required")
        # Existing platform traversal checks reject Windows aliases, reparses and POSIX symlinks.
        if "content" in parameters and (
            not isinstance(parameters["content"], str) or len(parameters["content"].encode()) > 8192
        ):
            raise ValueError("bounded UTF8 content required")
        if (
            action.capability_id.endswith("write")
            and not delivery["approved"]
            and not (authority is not None and authority["mode"] == "full")
        ):
            raise PermissionError("Ask requires exact current owner approval")
        if delivery["kind"] == "readback" and delivery["parameters"] != {
            "path": parameters["path"]
        }:
            raise PermissionError("readback must inspect the original action target")
        if delivery["kind"] == "action" and delivery["parameters"] != parameters:
            raise PermissionError("delivery parameters changed after review")

    def execute(self, delivery: dict[str, Any]) -> dict[str, Any]:
        action = self.validate(delivery)

        def authorize() -> None:
            self.validate(delivery)
            check = {"delivery_id": delivery["id"]}
            if delivery.get("authority") is not None:
                check["authority"] = delivery["authority"]
            expected = {
                "authorized": True,
                **(
                    {"authority": delivery["authority"]}
                    if delivery.get("authority") is not None
                    else {}
                ),
            }
            if self.client.request("check", check) != expected:
                raise PermissionError("remote authority unavailable")

        authorize()
        if delivery["kind"] == "readback":
            observed = self.readback_effect(action, delivery)
            authorize()
            return observed
        digest = fingerprint(record(action))
        previous = self.journal.execute(
            "SELECT fingerprint,result FROM execution_claim WHERE action_id=?", (action.id,)
        ).fetchone()
        if previous:
            if previous[0] != digest:
                raise StateConflict("action identity reused with changed material")
            if previous[1] is None:
                raise StateConflict("execution outcome UNKNOWN; independent readback required")
            return dict(json.loads(previous[1]))
        self.journal.execute(
            "INSERT INTO execution_claim(action_id,fingerprint) VALUES (?,?)", (action.id, digest)
        )
        cancellation = RemoteCancellation(authorize)
        result = self.execute_effect(action, cancellation)
        receipt = record(result)
        self.journal.execute(
            "UPDATE execution_claim SET result=? WHERE action_id=?",
            (json.dumps(receipt, allow_nan=False), action.id),
        )
        return receipt

    def readback_effect(self, action: Action, delivery: dict[str, Any]) -> dict[str, Any]:
        data = self.files.read(action.parameters["path"])
        if len(data) > 8192:
            raise ValueError("readback exceeds permitted content boundary")
        return {"content": data.decode("utf-8", errors="strict")}

    def execute_effect(self, action: Action, cancellation: Cancellation) -> Result:
        if action.capability_id == "machine.files.write":
            result = FileExecutor(self.files)(action, cancellation)
            if result.artifact:
                result = replace(
                    result,
                    artifact=replace(
                        result.artifact,
                        location=f"workspace:{self.workspace_id}/{action.parameters['path']}",
                    ),
                )
        else:
            data = self.files.read(action.parameters["path"])
            if len(data) > 8192:
                raise ValueError("read exceeds permitted content boundary")
            result = Result(
                new_id(),
                action.id,
                action.task_id,
                action.correlation_id,
                action.capability_id,
                True,
                value=data.decode("utf-8", errors="strict"),
            )
        return result

    def step(self) -> bool:
        response = self.client.request("poll", {})
        if "advertise_required" in response:
            if (
                set(response) != {"delivery", "advertise_required"}
                or response["advertise_required"] is not True
                or response["delivery"] is not None
            ):
                raise PermissionError("invalid Worker registration response")
            # Core explicitly confirms this poll claimed nothing. Do not retry an
            # ambiguous poll/effect; only rebuild the lost executor registration.
            self.advertise()
            return False
        delivery = response["delivery"]
        self.status = "online"
        if delivery is None:
            return False
        receipt = self.execute(delivery)
        self.client.request("deliver", {"delivery_id": delivery["id"], "result": receipt})
        return True

    def run(self, stop: Event) -> None:
        delay = 2.0
        advertised = False
        try:
            while not stop.is_set():
                try:
                    if not advertised:
                        self.advertise()
                        advertised = True
                    self.step()
                    delay = 2
                except PermissionError:
                    self.status = "revoked_or_expired"
                    return
                except (OSError, ValueError, KeyError, StateConflict):
                    self.status = "degraded"
                    advertised = False
                    delay = min(delay * 2, 30)
                stop.wait(delay * random.uniform(0.8, 1.2))
        finally:
            self.status = "offline"
            try:
                self.client.request("disconnect", {})
            except (OSError, PermissionError, ValueError, KeyError):
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Scoped outbound OSCAR file Worker")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--config", type=Path, help="Private explicitly synthetic PEM fixture configuration"
    )
    source.add_argument("--connection", type=Path, help="Native Desktop DPAPI connection file")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--workspace-id")
    parser.add_argument("--journal", type=Path)
    parser.add_argument(
        "--fixture-ca", type=Path, help="Trusted CA for explicitly synthetic native fixture only"
    )
    args = parser.parse_args()
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        from .remote_client import GridClient

        if args.connection:
            if not args.workspace or not args.workspace_id or not args.journal:
                raise ValueError(
                    "explicit local workspace, enrollment binding and execution journal required"
                )
            connection = native_connection(args.connection)
            native_signer = WindowsNativeSigner(connection["installation_id"])
            context = None
            if args.fixture_ca:
                if not connection["installation_id"].startswith("fixture-"):
                    raise PermissionError("custom CA limited to synthetic native fixture")
                context = ssl.create_default_context(cafile=str(args.fixture_ca))
            client = GridClient(
                connection["url"], connection["session"], native_signer, ssl_context=context
            )
            worker = RemoteWorker(client, args.workspace, args.workspace_id, args.journal)
            try:
                worker.run(Event())
            except KeyboardInterrupt:
                pass
            finally:
                worker.close()
                native_signer.close()
            return 0
        raw = args.config.read_bytes()
        if len(raw) > 32768:
            raise ValueError("private fixture configuration exceeds boundary")
        config = json.loads(raw)
        if config.get("synthetic") is not True:
            raise PermissionError("PEM signer requires an explicitly synthetic test identity")
        key = serialization.load_pem_private_key(
            Path(config["key_file"]).read_bytes(), password=None
        )
        if not isinstance(key, rsa.RSAPrivateKey):
            raise ValueError("RSA signing key required")

        def sign(body: bytes) -> bytes:
            return key.sign(
                body,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )

        context = ssl.create_default_context(cafile=config.get("ca_file"))
        client = GridClient(config["url"], config["session"], sign, ssl_context=context)
        worker = RemoteWorker(
            client, Path(config["workspace"]), config["workspace_id"], Path(config["journal"])
        )
        try:
            worker.run(Event())
        except KeyboardInterrupt:
            pass
        finally:
            worker.close()
        return 0
    except (OSError, ValueError, PermissionError, KeyError):
        print("Worker unavailable; inspect enrollment and local scope")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
