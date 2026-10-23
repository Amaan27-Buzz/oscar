"""Owner-reviewed native management over the existing Auth/Fabric/Grid authorities."""

import base64
import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from .accounts import Account
from .connectors import RiskLevel
from .contracts import new_id
from .mcp_client import MCPServerConfig
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
        "providers": h.auth.catalog() if h.auth else [],
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

    def _rebind_resource_plugins(
        self, account: Account, node: str, session: str, scope: str
    ) -> None:
        if account.identity_class != "resource-grant":
            return
        store = self.h.store
        for installed in store.all("mcp_installation"):
            config = self.h.plugins._config(installed)
            if config.account_id != account.id:
                continue
            self.h.plugins.disconnect(installed["id"], expected_config=config)
            bindings = [b for b in account.services.values() if b.audience == config.url]
            if len(bindings) == 1:
                with store.transaction():
                    self._authority(node, session, scope)
                    self.h.accounts.check(account.id, account.generation)
                    current = store.get("mcp_installation", installed["id"])
                    if self.h.plugins._config(current) != config:
                        raise PermissionError("MCP binding changed during authorization")
                    current["config"].update(
                        account_generation=account.generation,
                        credential_ref=bindings[0].credential_ref,
                    )
                    current["health"] = "disconnected"
                    store.put("mcp_installation", installed["id"], current)

    def _current_owner(
        self,
        node: str,
        session: str,
        scope: str,
        key: str | None = None,
    ) -> frozenset[str]:
        try:
            s = self.h.store.get("session", session)
            n = self.h.store.get("node", node)
        except KeyError:
            raise PermissionError("current owner session required") from None
        if (
            s["node_id"] != node
            or s["revoked"]
            or n["revoked"]
            or not n["paired"]
            or s["expires_at"] <= self.h.grid.clock()
            or scope not in s["scopes"]
            or scope not in n["scopes"]
        ):
            raise PermissionError("current owner session required")
        if scope == "grid:approve":
            binding = self.h.store.get("remote_device", node)
            if binding["owner_id"] != self.h.runtime.relationship_id:
                raise PermissionError("current owner relationship required")
            current_key = binding["owner_public_key"]
        else:
            binding = self.h.store.get("sunday_key", node)
            current_key = binding["public_key"]
        if binding["session_id"] != session or not current_key or (key and key != current_key):
            raise PermissionError("current owner key enrollment required")
        return frozenset(s["scopes"]) & frozenset(n["scopes"])

    def _authority(self, node: str, session: str, scope: str) -> None:
        grants = self._current_owner(node, session, scope)
        if (
            not PersonalPolicy(self.h.store)
            .evaluate(
                "connections.manage",
                (scope,),
                grants,
                {"node": node},
                confirmed=True,
            )
            .allowed
        ):
            raise PermissionError("connection management policy denied")

    def material(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if set(payload) != {"operation", "id", "value"}:
            raise ValueError("exact connection change required")
        operation, identifier, value = payload["operation"], payload["id"], payload["value"]
        if not isinstance(identifier, str) or not identifier or len(identifier) > 200:
            raise ValueError("bounded connection identifier required")
        if not isinstance(value, str) or len(value.encode()) > 20_000:
            raise ValueError("bounded management value required")
        if operation == "begin_account":
            if self.h.auth is None:
                raise PermissionError("configured Auth Broker required")
            provider = self.h.auth.providers[identifier]
            options = self._enrollment(value)
            if (provider.provider == "mcp-resource") != (
                options["identity_class"] == "resource-grant"
            ):
                raise PermissionError("resource access and provider person identity are distinct")
            if not provider.allowed_scopes or not set(options["scopes"]) <= set(
                provider.allowed_scopes
            ):
                raise PermissionError("configured permission choices required")
            state = {"provider": asdict(provider), "options": options}
            revision, target = 1, provider.provider + " / " + provider.service
            if options.get("account_id"):
                account = self.h.accounts.get(options["account_id"])
                state["account"] = asdict(account)
                revision = account.generation
        elif operation == "register_plugin":
            config, reviewed = self._registration(value)
            if config.id != identifier:
                raise ValueError("plugin identifier mismatch")
            self.h.accounts.check(config.account_id, config.account_generation)
            if any(r["id"] == identifier for r in self.h.store.all("mcp_installation")):
                raise ValueError("plugin already installed")
            state = {"config": asdict(config), "reviewed": reviewed}
            revision, target = config.account_generation, config.name
        elif operation in {
            "rename_account",
            "default_account",
            "disconnect_account",
            "refresh_account",
        }:
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

    @staticmethod
    def _enrollment(value: str) -> dict[str, Any]:
        options = json.loads(value)
        if (
            not isinstance(options, dict)
            or set(options) - {"alias", "scopes", "identity_class", "account_id"}
            or not {"alias", "scopes", "identity_class"} <= set(options)
        ):
            raise ValueError("exact account enrollment options required")
        if (
            not isinstance(options["scopes"], list)
            or not options["scopes"]
            or any(not isinstance(s, str) for s in options["scopes"])
        ):
            raise ValueError("select explicit service permissions")
        if options["identity_class"] not in {"owner-delegated", "oscar-owned", "resource-grant"}:
            raise ValueError("interactive account identity class required")
        return options

    def _registration(
        self,
        value: str,
    ) -> tuple[MCPServerConfig, dict[str, RiskLevel | tuple[RiskLevel, ...]]]:
        data = json.loads(value)
        if not isinstance(data, dict) or set(data) != {"config", "reviewed"}:
            raise ValueError("reviewed server configuration required")
        config = dict(data["config"])
        # Fixture bypasses and opaque vault references cannot be submitted by a native client.
        if config.get("fixture_origin") or config.get("credential_ref"):
            raise PermissionError("server credentials require trusted account provisioning")
        account = self.h.accounts.check(config["account_id"], config["account_generation"])
        if account.identity_class == "resource-grant":
            bindings = [b for b in account.services.values() if b.audience == config.get("url")]
            if len(bindings) != 1 or not config.get("url"):
                raise PermissionError("exact MCP resource grant required")
            config["credential_ref"] = bindings[0].credential_ref
        config["arguments"] = tuple(config.get("arguments", ()))
        config["reviewed_files"] = tuple(tuple(p) for p in config.get("reviewed_files", ()))
        candidate = MCPServerConfig(**config)
        if not isinstance(data["reviewed"], dict) or len(data["reviewed"]) > 200:
            raise ValueError("bounded explicit tool permissions required")
        reviewed: dict[str, RiskLevel | tuple[RiskLevel, ...]] = {}
        for name, risks in data["reviewed"].items():
            if not isinstance(risks, list) or not risks or len(risks) > 6:
                raise ValueError("explicit tool consequences required")
            reviewed[name] = tuple(RiskLevel(risk) for risk in risks)
        return candidate, reviewed

    def challenge(
        self,
        node: str,
        session: str,
        scope: str,
        grants: frozenset[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        with self.h.store.transaction():
            return self._challenge(node, session, scope, grants, payload)

    def _challenge(
        self,
        node: str,
        session: str,
        scope: str,
        grants: frozenset[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        grants = grants & self._current_owner(node, session, scope)
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
        deferred = None
        with store.transaction():
            grants = grants & self._current_owner(node, session, scope, key)
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
            elif operation in {"begin_account", "refresh_account", "register_plugin"}:
                deferred = change
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
        extra: dict[str, Any] = {}
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
                self.h.ensure_connections()
            else:
                self.h.plugins.disconnect(identifier, expected_config=plugin_config)
        elif deferred is not None:
            if operation == "register_plugin":
                config, reviewed = self._registration(value)
                self.h.plugins.register(config, reviewed, owner_reviewed=True)
                message = "Server registered. Review connect to discover its permitted tools."
            elif operation == "begin_account":
                if self.h.auth is None:
                    raise PermissionError("Auth Broker unavailable")
                options = self._enrollment(value)
                self._authority(node, session, scope)
                enrollment = self.h.auth.begin(
                    identifier,
                    frozenset(options["scopes"]),
                    owner_authorized=True,
                    alias=options["alias"],
                    identity_class=options["identity_class"],
                    account_id=options.get("account_id"),
                )
                store.put(
                    "native_auth_pending",
                    enrollment["id"],
                    {
                        "id": enrollment["id"],
                        "node": node,
                        "session": session,
                        "scope": scope,
                        "used": False,
                    },
                )
                extra["enrollment"] = enrollment
                status, message = "pending", "Continue in your browser to connect this account."
            else:
                if self.h.auth is None:
                    raise PermissionError("Auth Broker unavailable")
                account = self.h.accounts.get(identifier)
                candidates = [
                    c
                    for c in store.all("auth_broker_connection")
                    if c["account_id"] == identifier
                    and c["state"] == "ready"
                    and c.get("generation") == account.generation
                    and (not value or self.h.auth.providers[c["provider_id"]].service == value)
                ]
                if len(candidates) != 1:
                    raise PermissionError("choose an unambiguous service to reconnect")
                refreshed = self.h.auth.refresh(
                    candidates[0]["id"],
                    owner_authorized=True,
                    authority_check=lambda: self._authority(node, session, scope),
                )
                self._rebind_resource_plugins(refreshed, node, session, scope)
                self.h.ensure_connections()
                message = "Service credentials refreshed. Previous sessions need reconnecting."
        store.audit(
            "connections",
            "owner_connection_result",
            {"node_id": node, "operation": operation, "id": identifier, "status": status},
        )
        return {"connections": snapshot(self.h), "message": message, "status": status, **extra}

    def oauth_callback(
        self,
        node: str,
        session: str,
        scope: str,
        grants: frozenset[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if set(payload) not in ({"id", "state", "code"}, {"id", "state", "code", "iss"}) or any(
            not isinstance(v, str) or not v or len(v) > 8000 for v in payload.values()
        ):
            raise ValueError("bounded native OAuth callback required")
        if self.h.auth is None:
            raise PermissionError("Auth Broker unavailable")
        with self.h.store.transaction():
            grants = grants & self._current_owner(node, session, scope)
            pending = self.h.store.get("native_auth_pending", payload["id"])
            if pending["used"] or (pending["node"], pending["session"], pending["scope"]) != (
                node,
                session,
                scope,
            ):
                raise PermissionError("OAuth callback owner/session mismatch")
            decision = PersonalPolicy(self.h.store).evaluate(
                "connections.manage",
                (scope,),
                grants,
                {"node": node},
                confirmed=True,
            )
            if not decision.allowed:
                raise PermissionError("account connection policy denied")
            self.h.store.put("native_auth_pending", payload["id"], {**pending, "used": True})
        account = self.h.auth.complete(
            payload["id"],
            payload["state"],
            payload["code"],
            owner_authorized=True,
            authority_check=lambda: self._authority(node, session, scope),
            issuer=payload.get("iss"),
        )
        self._rebind_resource_plugins(account, node, session, scope)
        self.h.ensure_connections()
        self.h.store.audit(
            "connections",
            "account_connected",
            {
                "node_id": node,
                "account_id": account.id,
                "generation": account.generation,
            },
        )
        return {
            "connections": snapshot(self.h),
            "status": "verified",
            "message": (
                "MCP resource access connected. Provider person identity was not verified."
                if account.identity_class == "resource-grant"
                else "Account connected."
            ),
        }
