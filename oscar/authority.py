"""Signed standing delegation in the canonical Store, independent of capture/retention."""

import base64
import json
from typing import Any

from .contracts import TaskState, new_id
from .grid import Grid, SessionHandle
from .mobile import display_digest, fingerprint
from .policy import PersonalPolicy
from .storage import Store


class StandingAuthority:
    def __init__(self, store: Store, grid: Grid, relationship: str = "owner"):
        self.store, self.grid, self.relationship = store, grid, relationship

    def _state(self) -> dict[str, Any]:
        try:
            return self.store.get("standing_authority", self.relationship)
        except KeyError:
            return {"epoch": 0, "mode": "ask", "grant_id": None}

    def _session(self, node: str, session: str) -> dict[str, Any]:
        identity, credential = self.store.get("node", node), self.store.get("session", session)
        if (
            identity["revoked"]
            or credential["revoked"]
            or credential["node_id"] != node
            or credential["expires_at"] <= self.grid.clock()
        ):
            raise PermissionError("standing delegation device/session unavailable")
        return credential

    def _owner(self, node: str, session: str, scope: str, grants: frozenset[str]) -> str:
        credential = self._session(node, session)
        actual = set(credential["scopes"]) & set(self.store.get("node", node)["scopes"])
        if (
            scope not in actual
            or scope not in grants
            or not (scope == "grid:approve" or scope.startswith("control:approve:"))
        ):
            raise PermissionError("enrolled owner approval scope required")
        try:
            remote = self.store.get("remote_device", node)
        except KeyError:
            owner = self.store.get("sunday_key", node)
            if owner["session_id"] != session:
                raise PermissionError("owner key session changed") from None
            return str(owner["public_key"])
        if remote["session_id"] != session or remote["owner_id"] != self.relationship:
            raise PermissionError("owner relationship or session changed")
        key = remote.get("owner_public_key")
        if not key:
            raise PermissionError("independently enrolled owner key required")
        return str(key)

    def _coverage(self, selections: Any) -> list[dict[str, Any]]:
        if not isinstance(selections, list) or not 1 <= len(selections) <= 256:
            raise ValueError("bounded exact capability coverage required")
        resolved = []
        for selected in selections:
            if not isinstance(selected, dict) or set(selected) != {
                "node_id",
                "session_id",
                "capability_id",
            }:
                raise ValueError("exact executor session/capability selection required")
            node, session, cap_id = (
                selected[k] for k in ("node_id", "session_id", "capability_id")
            )
            credential = self._session(node, session)
            identity = self.store.get("node", node)
            caps = [cap for cap in identity["capabilities"] if cap["id"] == cap_id]
            if len(caps) != 1 or not set(caps[0]["permissions"]) <= (
                set(credential["scopes"]) & set(identity["scopes"])
            ):
                raise PermissionError("capability missing or executor lacks actual permissions")
            resolved.append({**selected, "contract": fingerprint(caps[0])})
        if len({fingerprint(item) for item in resolved}) != len(resolved):
            raise ValueError("duplicate capability coverage")
        return sorted(resolved, key=lambda item: (item["node_id"], item["capability_id"]))

    def _accounts(self, identifiers: Any) -> list[dict[str, Any]]:
        if (
            not isinstance(identifiers, list)
            or len(identifiers) > 128
            or any(not isinstance(identifier, str) for identifier in identifiers)
            or len(set(identifiers)) != len(identifiers)
        ):
            raise ValueError("explicit bounded account identities required")
        result = []
        for identifier in sorted(identifiers):
            account = self.store.get("connected_account", identifier)
            if account["status"] != "connected" or account["owner_id"] != self.relationship:
                raise PermissionError("account unavailable or belongs to another owner")
            result.append({"id": identifier, "generation": account["generation"]})
        return result

    def material(self, payload: dict[str, Any]) -> dict[str, Any]:
        if set(payload) != {
            "mode",
            "lifetime_seconds",
            "capabilities",
            "account_ids",
            "resolve_ask_rules",
        }:
            raise ValueError("exact standing delegation request required")
        mode, lifetime = payload["mode"], payload["lifetime_seconds"]
        if (
            mode not in {"ask", "secure", "full"}
            or type(lifetime) is not int
            or not 60 <= lifetime <= 28800
        ):
            raise ValueError(
                "supported mode and lifetime between one minute and eight hours required"
            )
        rules = PersonalPolicy(self.store).rules()
        asking = sorted(rule.id for rule in rules if rule.enabled and rule.effect == "ask")
        resolved = payload["resolve_ask_rules"]
        if (
            not isinstance(resolved, list)
            or resolved != sorted(set(resolved))
            or (mode == "full" and resolved != asking or mode != "full" and resolved)
        ):
            raise ValueError("Full Access must explicitly resolve every existing ASK constraint")
        return {
            "change": payload,
            "task_id": self.relationship,
            "target": "OSCAR " + mode.title() + " access",
            "relationship": self.relationship,
            "capabilities": self._coverage(payload["capabilities"]) if mode != "ask" else [],
            "accounts": self._accounts(payload["account_ids"]) if mode != "ask" else [],
            "policy_digest": fingerprint(self.store.all("personal_policy")),
            "epoch": self._state()["epoch"],
        }

    def challenge(
        self, node: str, session: str, scope: str, grants: frozenset[str], payload: dict[str, Any]
    ) -> dict[str, Any]:
        key = self._owner(node, session, scope, grants)
        material = self.material(payload)
        review = json.dumps(material, sort_keys=True, separators=(",", ":"))
        if len(review.encode()) > 24000:
            raise ValueError("delegation exceeds safe exact review size")
        description = (
            "Activate "
            + payload["mode"].title()
            + " access for "
            + str(payload["lifetime_seconds"])
            + " seconds. "
            + (
                "Supported consequential operations proceed without OSCAR action prompts. "
                if payload["mode"] == "full"
                else "Protected operations still require confirmation. "
            )
            + "OS/provider permissions, local safety and separate capture/retention "
            "grants remain enforced."
        )
        expires = round((self.grid.clock() + 30) * 1000)
        claim = {
            "version": 2,
            "node_id": node,
            "session_id": session,
            "operation": "approve",
            "scope": scope,
            "generation": material["epoch"],
            "material": material,
            "nonce": new_id(),
            "expires_at_ms": expires,
            "display_digest": display_digest(
                "approve", scope, material["target"], review, description
            ),
        }
        identifier = new_id()
        encoded = base64.b64encode(
            json.dumps(claim, sort_keys=True, separators=(",", ":")).encode()
        ).decode()
        self.store.put(
            "authority_review",
            identifier,
            {"payload": encoded, "used": False, "key": fingerprint(key)},
        )
        return {
            "challenge_id": identifier,
            "signing_payload": encoded,
            "expires_at_ms": expires,
            "operation": "approve",
            "target": material["target"],
            "description": description,
            "scope": scope,
            "generation": material["epoch"],
            "review": review,
            "exact_request": description,
            "capability": "authority.manage",
            "reason": "Explicit signed owner standing delegation",
            "consequence": description,
            "policy_reason": "Exact capability, account, device, session and lifetime coverage",
            "evidence_state": "PLANNED",
        }

    def complete(
        self,
        node: str,
        session: str,
        key: str,
        scope: str,
        grants: frozenset[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        from .remote_grid import verify_signature

        if set(payload) != {"challenge_id", "signature"}:
            raise ValueError("exact signed activation required")
        with self.store.transaction():
            trusted = self._owner(node, session, scope, grants)
            row = self.store.get("authority_review", payload["challenge_id"])
            body = base64.b64decode(row["payload"], validate=True)
            claim = json.loads(body)
            if (
                row["used"]
                or key != trusted
                or fingerprint(key) != row["key"]
                or (claim["node_id"], claim["session_id"], claim["scope"]) != (node, session, scope)
                or claim["expires_at_ms"] <= self.grid.clock() * 1000
            ):
                raise PermissionError("activation expired, replayed or belongs to another owner")
            verify_signature(key, payload["signature"], body)
            material = self.material(claim["material"]["change"])
            if material != claim["material"]:
                raise PermissionError(
                    "authority, policy, capability or account changed since review"
                )
            state = {
                "epoch": material["epoch"] + 1,
                "mode": material["change"]["mode"],
                "grant_id": new_id(),
                "relationship": self.relationship,
                "owner_node": node,
                "owner_session": session,
                "scope": scope,
                "expires_at_ms": round(
                    (self.grid.clock() + material["change"]["lifetime_seconds"]) * 1000
                ),
                "material": material,
                "signature": payload["signature"],
                "signing_payload": row["payload"],
                "key": row["key"],
            }
            self.store.put("authority_review", payload["challenge_id"], {**row, "used": True})
            self.store.put("standing_authority", self.relationship, state)
            self.store.audit(
                "",
                "owner_standing_delegation",
                {k: state[k] for k in ("epoch", "mode", "grant_id", "owner_node", "expires_at_ms")},
            )
        return {"authority": self.snapshot()}

    def revoke(self, node: str, session: str, scope: str, grants: frozenset[str]) -> dict[str, Any]:
        with self.store.transaction():
            self._owner(node, session, scope, grants)
            state = {"epoch": self._state()["epoch"] + 1, "mode": "ask", "grant_id": None}
            self.store.put("standing_authority", self.relationship, state)
            self.store.audit(
                "",
                "standing_delegation_revoked",
                {
                    **state,
                    "node_id": node,
                    "in_flight": "cooperative cancellation; irreversible effects require readback",
                },
            )
        return {"authority": self.snapshot()}

    def _active(self) -> dict[str, Any]:
        state = self._state()
        if state["mode"] == "ask" or state["expires_at_ms"] <= self.grid.clock() * 1000:
            raise PermissionError("standing authority absent or expired")
        key = self._owner(
            state["owner_node"], state["owner_session"], state["scope"], frozenset({state["scope"]})
        )
        if fingerprint(key) != state["key"] or state["material"]["policy_digest"] != fingerprint(
            self.store.all("personal_policy")
        ):
            raise PermissionError("owner key or Personal Policy changed; activation required")
        if (
            self._accounts([account["id"] for account in state["material"]["accounts"]])
            != state["material"]["accounts"]
        ):
            raise PermissionError("account generation changed")
        return state

    def snapshot(self) -> dict[str, Any]:
        state = self._state()
        try:
            active = self._active()
            return {
                k: active[k] for k in ("mode", "epoch", "grant_id", "owner_node", "expires_at_ms")
            } | {
                "status": "active",
                "capabilities": active["material"]["capabilities"],
                "accounts": active["material"]["accounts"],
            }
        except (PermissionError, KeyError):
            return {
                "mode": "ask",
                "epoch": state["epoch"],
                "grant_id": None,
                "status": "inactive",
                "capabilities": [],
                "accounts": [],
            }

    def permits(
        self, capability: dict[str, Any], executor: SessionHandle, *, task_id: str | None = None
    ) -> bool:
        try:
            state = self._active()
            self.grid.authenticate(executor, "execute")
            if not any(
                node["id"] == executor.node_id and node["status"] in {"online", "degraded"}
                for node in self.grid.nodes()
            ):
                return False
            covered = {
                "node_id": executor.node_id,
                "session_id": executor.id,
                "capability_id": capability["id"],
                "contract": fingerprint(capability),
            }
            if covered not in state["material"]["capabilities"] or not any(
                fingerprint(capability) == fingerprint(current)
                for current in self.store.get("node", executor.node_id)["capabilities"]
            ):
                return False
            if state["mode"] == "secure" and capability["risk"] in {"high", "critical"}:
                return False
            granted = frozenset(self.store.get("session", executor.id)["scopes"]) & frozenset(
                self.store.get("node", executor.node_id)["scopes"]
            )
            for identifier in (capability["id"], *capability["permissions"]):
                if (
                    not PersonalPolicy(self.store)
                    .evaluate(
                        identifier,
                        tuple(capability["permissions"]),
                        granted,
                        {"node": executor.node_id, "target": executor.node_id},
                        confirmed=state["mode"] == "full",
                        now=self.grid.clock(),
                    )
                    .allowed
                ):
                    return False
            if task_id is not None:
                task = self.store.task(task_id)
                pin = self.store.get("task_authority", task_id)
                generation = task.attempts + (task.state == TaskState.PLANNED)
                if (
                    task.cancelled
                    or pin["epoch"] != state["epoch"]
                    or pin["grant_id"] != state["grant_id"]
                    or pin["capability"] != covered
                    or pin["task_generation"] != generation
                ):
                    return False
            return True
        except (PermissionError, KeyError):
            return False

    def bind(
        self, task_id: str, capability: dict[str, Any], executor: SessionHandle
    ) -> dict[str, Any] | None:
        with self.store.transaction():
            try:
                previous = self.store.get("task_authority", task_id)
            except KeyError:
                previous = None
            if previous:
                self.check_task(task_id, capability, executor)
                return {k: v for k, v in previous.items() if k != "capability"}
            if not self.permits(capability, executor):
                return None
            state, task = self._active(), self.store.task(task_id)
            parameters = self.store.get("plan", task_id)["parameters"]
            parameters = self.store.transient.get(task_id, {}).get("parameters", parameters)
            account_id = parameters.get("account_id")
            try:
                installation = self.store.get("mcp_installation", capability["id"].split(":", 1)[0])
                account_id = installation["config"]["account_id"]
            except KeyError:
                pass
            if account_id and account_id not in {
                account["id"] for account in state["material"]["accounts"]
            }:
                raise PermissionError("task account is outside signed delegation")
            pin = {
                k: state[k]
                for k in (
                    "grant_id",
                    "epoch",
                    "mode",
                    "owner_node",
                    "owner_session",
                    "expires_at_ms",
                )
            }
            pin.update(
                task_generation=task.attempts + (task.state == TaskState.PLANNED),
                capability={
                    "node_id": executor.node_id,
                    "session_id": executor.id,
                    "capability_id": capability["id"],
                    "contract": fingerprint(capability),
                },
            )
            self.store.put("task_authority", task_id, pin)
            self.store.audit(task_id, "owner_delegation_authorized", pin)
            return {k: v for k, v in pin.items() if k != "capability"}

    def check_task(self, task_id: str, capability: dict[str, Any], executor: SessionHandle) -> None:
        try:
            self.store.get("task_authority", task_id)
        except KeyError:
            return
        if not self.permits(capability, executor, task_id=task_id):
            raise PermissionError("standing authority revoked, expired or changed")


def check_task_authority(
    store: Store, grid: Grid, task_id: str, capability: dict[str, Any], executor: SessionHandle
) -> None:
    try:
        relationship = store.get("task_relationship", task_id)["relationship"]
    except KeyError:
        relationship = "owner"
    StandingAuthority(store, grid, relationship).check_task(task_id, capability, executor)


def delegated_confirmation(
    store: Store, grid: Grid, task_id: str, capability: dict[str, Any], executor: SessionHandle
) -> bool:
    try:
        relationship = store.get("task_relationship", task_id)["relationship"]
        store.get("task_authority", task_id)
    except KeyError:
        return False
    authority = StandingAuthority(store, grid, relationship)
    authority.check_task(task_id, capability, executor)
    return authority.permits(capability, executor, task_id=task_id)


def check_task_account(
    store: Store, task_id: str, account_id: str | None, generation: int | None
) -> None:
    """Every account-bearing Fabric executor must retain the signed account ceiling."""
    try:
        pin = store.get("task_authority", task_id)
    except KeyError:
        return
    if account_id is None:
        return
    relationship = store.get("task_relationship", task_id)["relationship"]
    state = store.get("standing_authority", relationship)
    if (
        pin["epoch"] != state["epoch"]
        or pin["grant_id"] != state["grant_id"]
        or ({"id": account_id, "generation": generation} not in state["material"]["accounts"])
    ):
        raise PermissionError("executor account is outside signed standing delegation")
