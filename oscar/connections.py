"""Owner-reviewed native management over the existing Auth/Fabric/Grid authorities."""

import base64
import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from .contracts import new_id
from .mobile import display_digest, fingerprint
from .policy import PersonalPolicy

if TYPE_CHECKING:
    from .harness import Harness


def snapshot(h: "Harness") -> dict[str, Any]:
    accounts = []
    for account in h.accounts.list_accounts():
        services = [
            {
                "id": name,
                "scopes": list(binding.scopes),
                "expires_at": binding.expires_at,
                "restrictions": list(binding.denied_capabilities),
            }
            for name, binding in account.services.items()
        ]
        accounts.append(
            {
                key: value
                for key, value in asdict(account).items()
                if key not in {"services", "browser_profile_id"}
            }
            | {"services": services}
        )
    plugins = [
        {
            key: plugin[key]
            for key in ("id", "name", "account_id", "enabled", "health", "transport", "permissions")
        }
        | {
            "tools": [{"name": tool["name"]} for tool in plugin["tools"]],
            "activity": plugin["activity"][-5:],
        }
        for plugin in h.plugins.snapshot()
    ]
    result = {
        "identity": asdict(h.accounts.operational_identity(h.runtime.relationship_id)),
        "accounts": accounts,
        "plugins": plugins,
        "access": "Ask",
        "observed_at_ms": round(h.grid.clock() * 1000),
        "enrollment": "Provider setup requires a configured trusted Auth Broker",
        "credential_deletion": "available" if h.auth is not None else "unavailable",
        "accounts_total": len(accounts),
        "plugins_total": len(plugins),
        "truncated": False,
    }
    # Management replies share the native 64 KB response boundary with review metadata.
    while len(json.dumps(result).encode()) > 40_000 and (accounts or plugins):
        result["truncated"] = True
        if plugins:
            plugins.pop()
        else:
            accounts.pop()
    return result


class Connections:
    def __init__(self, h: "Harness"):
        self.h = h

    def material(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if set(payload) != {"operation", "id", "value"}:
            raise ValueError("exact connection change required")
        operation, identifier, value = payload["operation"], payload["id"], payload["value"]
        if not isinstance(value, str) or len(value) > 500:
            raise ValueError("bounded management value required")
        if operation in {"rename_account", "default_account", "disconnect_account"}:
            account = self.h.accounts.get(identifier)
            revision = account.generation
            target = account.alias
            state = asdict(account)
        elif operation in {"connect_plugin", "disable_plugin", "enable_plugin", "remove_plugin"}:
            state = self.h.store.get("mcp_installation", identifier)
            revision = state["config"]["account_generation"]
            target = identifier
        else:
            raise ValueError("unsupported connection change")
        return {
            "task_id": identifier,
            "target": target,
            "change": payload,
            "digest": fingerprint(state),
        }, revision

    def challenge(
        self,
        node: str,
        session: str,
        scope: str,
        grants: frozenset[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        material, generation = self.material(payload)
        decision = PersonalPolicy(self.h.store).evaluate(
            "connections.manage",
            (scope,),
            grants,
            {"node": node},
            confirmed=True,
        )
        if not decision.allowed:
            raise PermissionError("connection management policy denied")
        review = json.dumps(payload, sort_keys=True)
        description = payload["operation"].replace("_", " ").capitalize()
        expires = round((self.h.grid.clock() + 30) * 1000)
        claim = {
            "version": 2,
            "node_id": node,
            "session_id": session,
            "operation": "approve",
            "scope": scope,
            "generation": generation,
            "material": material,
            "nonce": new_id(),
            "expires_at_ms": expires,
            "display_digest": display_digest(
                "approve", scope, material["target"], review, description
            ),
        }
        encoded = base64.b64encode(
            json.dumps(claim, sort_keys=True, separators=(",", ":")).encode()
        ).decode()
        identifier = new_id()
        self.h.store.put("connection_review", identifier, {"payload": encoded, "used": False})
        return {
            "challenge_id": identifier,
            "signing_payload": encoded,
            "expires_at_ms": expires,
            "operation": "approve",
            "target": material["target"],
            "description": description,
            "scope": scope,
            "generation": generation,
            "review": review,
            "exact_request": description,
            "capability": "connections.manage",
            "reason": "Change this connection using your current Ask authority",
            "consequence": description + ": " + material["target"],
            "policy_reason": "Exact signed review; current permissions rechecked",
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
            raise ValueError("exact signed connection change required")
        store = self.h.store
        disconnected = None
        plugin_config = None
        with store.transaction():
            row = store.get("connection_review", payload["challenge_id"])
            body = base64.b64decode(row["payload"], validate=True)
            claim = json.loads(body)
            if (
                row["used"]
                or claim["node_id"] != node
                or claim["session_id"] != session
                or claim["scope"] != scope
                or claim["expires_at_ms"] <= self.h.grid.clock() * 1000
            ):
                raise PermissionError("connection review expired or consumed")
            verify_signature(key, payload["signature"], body)
            material, generation = self.material(claim["material"]["change"])
            if material != claim["material"] or generation != claim["generation"]:
                raise PermissionError("connection changed since review")
            decision = PersonalPolicy(store).evaluate(
                "connections.manage",
                (scope,),
                grants,
                {"node": node},
                confirmed=True,
                confirmation_required=True,
            )
            if not decision.allowed:
                raise PermissionError("connection management policy denied")
            store.put("connection_review", payload["challenge_id"], {**row, "used": True})
            change = material["change"]
            identifier, operation, value = change["id"], change["operation"], change["value"]
            if operation == "rename_account":
                self.h.accounts.rename(identifier, value)
            elif operation == "default_account":
                self.h.accounts.set_default(identifier, value)
            elif operation == "disconnect_account":
                disconnected = self.h.accounts.disconnect(identifier)
            else:
                plugin_config = self.h.plugins._config(store.get("mcp_installation", identifier))
                if operation in {"enable_plugin", "disable_plugin"}:
                    self.h.plugins.set_enabled_local(identifier, operation == "enable_plugin")
                elif operation == "remove_plugin":
                    self.h.plugins.remove_local(identifier)
            store.audit(
                "connections",
                "owner_connection_change",
                {"node_id": node, "operation": operation, "id": identifier},
            )
        message = "Connection state updated"
        status = "verified"
        # Network/native-vault I/O happens after the signed local mutation commits.
        if disconnected is not None:
            if self.h.auth is None:
                self.h.accounts.credential_deletion(
                    identifier, disconnected.generation, "deletion_unavailable"
                )
                status = "partially_verified"
                message = (
                    "Account disabled. Local credential deletion is unavailable; "
                    "provider revocation is unknown."
                )
            else:
                try:
                    self.h.auth.finish_disconnect(disconnected)
                    message = (
                        "Account disabled and local credentials deleted; "
                        "provider revocation is unknown."
                    )
                except (OSError, PermissionError):
                    status = "partially_verified"
                    message = (
                        "Account disabled. Local credential deletion could not be verified; "
                        "provider revocation is unknown."
                    )
        elif plugin_config is not None:
            if operation == "connect_plugin":
                self.h.plugins.connect(identifier, expected_config=plugin_config)
            else:
                self.h.plugins.disconnect(identifier, expected_config=plugin_config)
        store.audit(
            "connections",
            "owner_connection_result",
            {"node_id": node, "operation": operation, "id": identifier, "status": status},
        )
        return {"connections": snapshot(self.h), "message": message, "status": status}
