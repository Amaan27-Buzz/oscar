"""Owner-operated GitHub device/private-read acceptance. Never borrows authentication."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from time import sleep, time
from traceback import extract_tb
from typing import Any

from oscar.capabilities import Cancellation
from oscar.connector_providers import github_manifest as public_manifest
from oscar.connectors import ConnectorFabric, ConnectorHTTP, ConnectorInstance, CredentialRef
from oscar.context_sources import ConnectorContextSource
from oscar.continuity import LiveContextFederation
from oscar.contracts import Action, Epistemic, Task, new_id, record
from oscar.event_archive import EventArchive, MemoryWriter, SourceEvent
from oscar.fabric_backend import FabricBackend
from oscar.memory_fabric import HistoricalClaim, MemoryFabric
from oscar.oauth_device import GitHubDeviceFlow, Vault, VaultResolver, github_manifest
from oscar.policy import PersonalPolicy
from oscar.secure_credentials import WindowsCredentialStore
from oscar.storage import Store


class AcceptanceError(RuntimeError):
    def __init__(self, check: str):
        self.check = check
        super().__init__(check)


def check(condition: bool, name: str) -> None:
    if not condition:
        raise AcceptanceError(name)


def save(root: Path, name: str, value: dict[str, Any]) -> None:
    (root / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def enroll(
    flow: GitHubDeviceFlow,
    client_id: str,
    confirm: Callable[[], str],
    show: Callable[[str], None] = print,
    wait: Callable[[float], None] = sleep,
) -> dict[str, Any]:
    try:
        challenge = flow.begin(client_id, owner_authorized=True, scopes=frozenset({"user:email"}))
    except (OSError, RuntimeError, ValueError, PermissionError):
        raise AcceptanceError("oauth.device_begin") from None
    check(
        challenge["url"] == "https://github.com/login/device"
        and re.fullmatch(r"[A-Z0-9]{4}-[A-Z0-9]{4}", challenge["user_code"]) is not None,
        "oauth.challenge_contract",
    )
    # Nothing else from the challenge, especially device code/nonce, reaches stdout.
    show(challenge["url"])
    show(challenge["user_code"])
    check(confirm() == "AUTHORIZED", "oauth.owner_confirmation")
    for _ in range(720):
        pending = flow.store.get("oauth_pending", challenge["id"])
        remaining = pending["expires_at"] - flow.clock()
        check(remaining > 0, "oauth.expired")
        wait(min(remaining, max(0, pending["next_poll"] - flow.clock())))
        check(flow.clock() < pending["expires_at"], "oauth.expired")
        try:
            connection = flow.poll_once(challenge["id"], challenge["nonce"], owner_authorized=True)
        except (OSError, RuntimeError, ValueError, PermissionError):
            state = flow.store.get("oauth_pending", challenge["id"])["state"]
            category = {
                "ambiguous": "oauth.exchange_ambiguous",
                "unexpected_token_provider_review_required": "oauth.token_contract",
                "rejected": "oauth.authorization_rejected",
                "expired": "oauth.expired",
            }.get(state, "oauth.poll_failed")
            raise AcceptanceError(category) from None
        if connection["state"] == "ready":
            check(connection["scopes"] == ["user:email"], "oauth.minimum_scope")
            return connection
    raise AcceptanceError("oauth.poll_bound")


class Reads:
    """Reduce private payloads to safe metadata before leaving the transient outcome."""

    def __init__(
        self,
        store: Store,
        vault: Vault,
        connection: dict[str, Any],
        http: ConnectorHTTP | None = None,
    ):
        check(connection["state"] == "ready", "oauth.connection_ready")
        check(connection["scopes"] == ["user:email"], "oauth.minimum_scope")
        self.store = store
        self.resolver = VaultResolver(vault)
        self.fabric = ConnectorFabric(store, self.resolver, PersonalPolicy(store), http)
        self.fabric.install(
            ConnectorInstance(
                "private",
                github_manifest(),
                CredentialRef(connection["credential_ref"]),
                frozenset(connection["scopes"]),
            )
        )
        self.fabric.install(ConnectorInstance("public", public_manifest(public=True)))

    def close(self) -> None:
        self.fabric.outcomes.clear()
        self.resolver.close()
        self.store.task_resources.discard(self.fabric)

    def read(self, name: str, fixture_id: str):
        public = name == "github.repositories.get"
        instance = "public" if public else "private"
        parameters = {"path": {"owner": "python", "repo": "cpython"}} if public else {}
        if name == "github.emails":
            parameters = {"query": {"per_page": 100, "page": 1}}
        task = Task(new_id(), new_id(), new_id())
        self.store.put("task", task.id, record(task))
        action = Action(
            new_id(),
            task.id,
            task.correlation_id,
            instance + ":" + name,
            parameters,
            task.id,
            "owner",
        )
        outcome = self.fabric.execute(
            instance,
            name,
            action,
            Cancellation(self.store, task.id),
            frozenset({"connectors:read"}),
        )
        try:
            check(outcome.result.success and outcome.source is not None, "private_read." + name)
            check(outcome.result.status == Epistemic.REPORTED, "private_read.reported")
            payload = outcome.payload
            if name == "github.owner":
                check(
                    type(payload.get("id")) is int
                    and payload["id"] > 0
                    and isinstance(payload.get("login"), str)
                    and bool(payload["login"]),
                    "private_read.user_contract",
                )
                safe = {
                    "identity_sha256": hashlib.sha256(
                        (fixture_id + ":" + str(payload["id"])).encode()
                    ).hexdigest()
                }
            elif name == "github.emails":
                items = payload.get("items")
                check(isinstance(items, list) and len(items) <= 100, "private_read.emails_bound")
                check(
                    all(
                        isinstance(item, dict)
                        and isinstance(item.get("email"), str)
                        and 0 < len(item["email"]) <= 320
                        and type(item.get("verified")) is bool
                        and type(item.get("primary")) is bool
                        for item in items
                    ),
                    "private_read.emails_contract",
                )
                safe = {"email_count_page1": len(items), "page": 1, "per_page": 100}
            else:
                check(
                    payload.get("full_name") == "python/cpython", "public_read.repository_contract"
                )
                safe = {"repository_matches": True}
            return replace(outcome, payload=safe)
        finally:
            outcome.payload.clear()
            self.fabric.release_task(task.id)


def snapshot(reads: Reads, fixture_id: str) -> dict[str, Any]:
    owner = reads.read("github.owner", fixture_id)
    emails = reads.read("github.emails", fixture_id)
    return {
        **owner.payload,
        **emails.payload,
        "read_contract": "VERIFIED",
        "provider_facts": "REPORTED",
        "sources": [owner.source.identity, emails.source.identity],
        "observed_at": emails.source.observed_at,
    }


def federation(root: Path, reads: Reads, fixture_id: str) -> dict[str, Any]:
    archive = EventArchive(root / "archive.sqlite")
    try:
        now = time()
        event = SourceEvent(
            fixture_id,
            "-1",
            "synthetic-controlled-stale-fixture",
            now - 60,
            project_id=fixture_id,
            context_key="connector:email_count_page1",
        )
        archive.append(event, retain_authorized=True)
        memory = MemoryWriter(archive).retain(
            (event.id,),
            "-1",
            "semantic",
            project=fixture_id,
            inferred=False,
            retain_authorized=True,
        )
        fabric = MemoryFabric(archive)
        sources = (
            ConnectorContextSource(
                lambda _: reads.read("github.emails", fixture_id),
                fixture_id,
                ("email_count_page1",),
            ),
            ConnectorContextSource(
                lambda _: reads.read("github.repositories.get", fixture_id),
                fixture_id,
                ("repository_matches",),
            ),
        )
        # Give public/private sources distinct IDs for the existing federation contract.
        sources[1].id = "public-github-fixture"
        context = LiveContextFederation(FabricBackend(fabric, fixture_id), sources).assemble(
            new_id(), "-1", fixture_id
        )
        current = context.resolve(event.context_key, time())
        check(
            current is not None
            and current.source.identity == "https://api.github.com/user/emails"
            and current.state == Epistemic.REPORTED
            and int(current.value) >= 0,
            "federation.current_private_source",
        )
        public = context.resolve("connector:repository_matches", time())
        check(
            public is not None and public.value == "true" and public.state == Epistemic.REPORTED,
            "federation.public_composition",
        )
        historical = fabric.retrieve(fixture_id, "-1", project=fixture_id, at=now - 30)
        claim = HistoricalClaim(
            "-1",
            (event.id,),
            (memory.id,),
            Epistemic.RECALLED,
            1,
            retrieval_paths=historical.hits[0].paths if historical.hits else (),
            temporal_interpretation="retrieval_time",
        )
        check(
            fabric.check_claim(claim, historical) == Epistemic.RECALLED,
            "federation.historical_evidence",
        )
        check(archive.event(event.id) == event, "federation.history_unchanged")
        return {
            "composition_checks": "VERIFIED",
            "now": {
                "value": int(current.value),
                "source": current.source.identity,
                "status": current.state,
            },
            "history": {
                "value": -1,
                "event_id": event.id,
                "memory_id": memory.id,
                "source": event.source,
                "status": "RECALLED",
                "synthetic": True,
            },
            "conflict": (
                "NOW uses current authenticated GitHub page-one count; "
                "HISTORY retrieves the controlled synthetic archive event. "
                "History is not rewritten."
            ),
            "public": {"source": public.source.identity, "status": public.state},
        }
    finally:
        archive.close()


def disconnect(store: Store, vault: Vault, identifier: str) -> dict[str, Any]:
    flow = GitHubDeviceFlow(store, vault)
    connection = store.get("oauth_connection", identifier)
    flow.disconnect(identifier, owner_authorized=True)
    try:
        vault.read(connection["credential_ref"], allow_expired=True)
    except KeyError:
        pass
    else:
        raise AcceptanceError("disconnect.credential_absent")
    saved = store.get("oauth_connection", identifier)
    check(
        saved["state"] == "locally_disconnected_provider_revocation_pending",
        "disconnect.local_state",
    )
    return {
        "local_credential": "DELETED_AND_ABSENCE_CHECKED",
        "remote_revocation": saved["remote_revocation"],
    }


def cleanup(root: Path, vault: Vault) -> None:
    with_store = Store(root / "oauth.sqlite")
    try:
        GitHubDeviceFlow(with_store, vault)
        for connection in with_store.all("oauth_connection"):
            disconnect(with_store, vault, connection["id"])
        for pending in with_store.all("oauth_pending"):
            vault.delete(pending["device_ref"])
            try:
                vault.read(pending["device_ref"], allow_expired=True)
            except KeyError:
                pass
            else:
                raise AcceptanceError("cleanup.device_credential_absent")
            if pending["state"] == "pending":
                pending["state"] = "rejected"
                with_store.put("oauth_pending", pending["id"], pending)
    finally:
        with_store.close()


def restart_read(root: Path, vault: Vault, http: ConnectorHTTP | None = None) -> dict[str, Any]:
    checkpoint = json.loads((root / "checkpoint.json").read_text(encoding="utf-8"))
    check(
        re.fullmatch(r"[a-f0-9]{32}", checkpoint["fixture_id"]) is not None,
        "restart.fixture_identity",
    )
    store = Store(root / "oauth.sqlite")
    reads = None
    try:
        GitHubDeviceFlow(store, vault)
        connection = store.get("oauth_connection", checkpoint["connection_id"])
        reads = Reads(store, vault, connection, http)
        observed = snapshot(reads, checkpoint["fixture_id"])
        check(observed["identity_sha256"] == checkpoint["identity_sha256"], "restart.same_account")
        save(root, "restart.json", observed)
        return observed
    finally:
        if reads:
            reads.close()
        store.close()


def run(root: Path, client_id: str, vault: Vault) -> dict[str, Any]:
    store = Store(root / "oauth.sqlite")
    reads = None
    try:
        fixture_id = new_id()
        save(root, "fixture.json", {"fixture_id": fixture_id})
        flow = GitHubDeviceFlow(store, vault)
        save(root, "progress.json", {"phase": "oauth.enrollment"})
        connection = enroll(
            flow,
            client_id,
            lambda: input("After GitHub approval, type AUTHORIZED to start polling: ").strip(),
        )
        reads = Reads(store, vault, connection)
        save(root, "progress.json", {"phase": "private_read.initial"})
        initial = snapshot(reads, fixture_id)
        save(root, "initial.json", initial)
        save(
            root,
            "checkpoint.json",
            {
                "fixture_id": fixture_id,
                "connection_id": connection["id"],
                "identity_sha256": initial["identity_sha256"],
            },
        )
        reads.close()
        reads = None
        store.close()
        # A new process reopens storage and the native vault; no token travels in argv/env.
        save(root, "progress.json", {"phase": "restart.private_read"})
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.verify_gate_b_oauth",
                "--root",
                str(root),
                "--restart-read",
                "--owner-authorized",
            ],
            cwd=Path(__file__).resolve().parents[1],
            env={
                k: os.environ[k] for k in ("PATH", "SystemRoot", "TEMP", "TMP") if k in os.environ
            },
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        check(completed.returncode == 0, "restart.private_read")
        store = Store(root / "oauth.sqlite")
        flow = GitHubDeviceFlow(store, vault)
        reads = Reads(store, vault, store.get("oauth_connection", connection["id"]))
        save(root, "progress.json", {"phase": "federation.composition"})
        composed = federation(root, reads, fixture_id)
        reads.close()
        reads = None
        save(root, "progress.json", {"phase": "disconnect.local"})
        disconnected = disconnect(store, vault, connection["id"])
        return {
            "status": "PRIVATE_READ_LIFECYCLE_AND_FEDERATION_CHECKS_PASSED",
            "fixture_id": fixture_id,
            "initial": initial,
            "restart": json.loads((root / "restart.json").read_text()),
            "federation": composed,
            "disconnect": disconnected,
            "gate_b": "PARTIAL",
            "scope": (
                "authenticated bounded read contracts and controlled "
                "synthetic-history composition; no writes"
            ),
        }
    finally:
        if reads:
            reads.close()
        store.close()


def failure_record(root: Path, failure: BaseException) -> dict[str, Any]:
    progress = root / "progress.json"
    category = (
        failure.check
        if isinstance(failure, AcceptanceError)
        else (
            json.loads(progress.read_text())["phase"]
            if progress.exists()
            else "restart.private_read"
        )
    )
    return {
        "status": "FAILED",
        "check": category,
        "phase": category.split(".")[0],
        "root": str(root),
        "exception_type": type(failure).__name__,
        "traceback": [
            {"file": frame.filename, "line": frame.lineno, "function": frame.name}
            for frame in extract_tb(failure.__traceback__)
        ],
        "private_payload": "NOT_RETAINED",
        "remote_revocation": "UNKNOWN_OWNER_ACTION_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--client-id")
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--restart-read", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    check(os.name == "nt", "precondition.windows_native_vault")
    check(args.owner_authorized, "precondition.explicit_owner_authority")
    root = args.root.resolve()
    if args.restart_read:
        check(root.is_dir() and (root / "checkpoint.json").is_file(), "restart.checkpoint")
    else:
        check(
            isinstance(args.client_id, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]{10,100}", args.client_id) is not None,
            "precondition.registered_client_id",
        )
        check(not root.exists(), "precondition.fresh_root")
        check(sys.stdin.isatty(), "precondition.interactive_owner_terminal")
        root.mkdir(parents=True, exist_ok=False)
        print("Artifact/evidence root: " + str(root))
    try:
        vault = WindowsCredentialStore()
    except OSError:
        raise AcceptanceError("precondition.native_vault_unavailable") from None
    error = None
    report = None
    try:
        if args.restart_read:
            restart_read(root, vault)
        else:
            report = run(root, args.client_id, vault)
    except (Exception, KeyboardInterrupt) as failure:
        error = failure_record(root, failure)
    finally:
        if not args.restart_read:
            try:
                cleanup(root, vault)
                if error:
                    error["cleanup"] = "owned native credentials absence checked"
            except Exception:
                error = error or failure_record(root, AcceptanceError("cleanup.native_credential"))
                error["cleanup"] = "FAILED: review owned opaque credential references"
    if error:
        save(root, "restart-failure.json" if args.restart_read else "failure.json", error)
        print(error["check"])
        return 1
    if report:
        save(root, "report.json", report)
        print(
            "Acceptance checks passed; local credential deleted. "
            "Remote revocation requires owner review."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AcceptanceError as error:
        print(error.check)
        raise SystemExit(1) from None
