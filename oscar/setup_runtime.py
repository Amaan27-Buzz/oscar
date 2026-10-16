"""Trusted-local first-run composition. Configuration never supplies action authority."""

import json
import re
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from .commissioning import Commissioning
from .contracts import new_id
from .credentials import CredentialPool, redact_runtime_secrets
from .oauth_device import Vault
from .policy import PersonalPolicy, PolicyRule
from .secure_credentials import WindowsCredentialStore
from .storage import StateConflict
from .voice_contracts import VoiceProfile
from .voice_identity import PersonaProfile

if TYPE_CHECKING:
    from .runtime import Runtime


class SetupRuntime:
    def __init__(self, runtime: "Runtime", pool: CredentialPool, vault: Vault | None = None):
        self.runtime, self.store, self.pool = runtime, runtime.store, pool
        self.relationship, self.vault = runtime.relationship_id, vault
        self.commissioning = Commissioning(runtime.grid, self.relationship)
        for row in self.store.all("setup_provider"):
            if row["relationship"] == self.relationship and row["slot"] in pool.slots:
                self._bind(row["slot"])

    def _vault(self) -> Vault:
        if self.vault is None:
            self.vault = WindowsCredentialStore()
        return self.vault

    def _key(self, section: str) -> str:
        return json.dumps([self.relationship, section])

    def _owner(self, authorized: bool) -> None:
        self.commissioning.initialize(owner_authorized=authorized)

    def configure(self, section: str, data: dict[str, Any], *, owner_authorized: bool) -> None:
        self._owner(owner_authorized)
        encoded = json.dumps(data, allow_nan=False)
        if len(encoded) > 4096 or redact_runtime_secrets(encoded) != encoded:
            raise ValueError("bounded non-secret configuration required")
        if section == "persona":
            if set(data) - {"name", "warmth", "formality", "brevity", "style"}:
                raise ValueError("unsupported Persona setting")
            for key in ("name", "style"):
                if key in data and not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", str(data[key])):
                    raise ValueError("bounded Persona label required")
            if any(
                type(data[k]) is not int for k in ("warmth", "formality", "brevity") if k in data
            ):
                raise ValueError("integer Persona traits required")
            data = asdict(PersonaProfile(**data))
        elif section == "preferences":
            if set(data) != {"reduced_motion", "show_presence"} or any(
                type(v) is not bool for v in data.values()
            ):
                raise ValueError("explicit supported preferences required")
        elif section == "voice":
            if set(data) - {"mode", "rate", "local_only", "interruptible"}:
                raise ValueError("voice setup cannot change identity, enroll or start capture")
            if any(type(data[k]) is not bool for k in ("local_only", "interruptible") if k in data):
                raise ValueError("boolean voice preferences required")
            from .voice_identity import oscar_voice_profile

            if "rate" in data and type(data["rate"]) not in {int, float}:
                raise ValueError("numeric voice rate required")
            profile = VoiceProfile(**{**asdict(oscar_voice_profile()), **data})
            data = {k: asdict(profile)[k] for k in ("mode", "rate", "local_only", "interruptible")}
        else:
            raise ValueError("unsupported setup section")
        with self.store.transaction():
            self.store.put(
                "setup",
                self._key(section),
                {"section": section, "relationship": self.relationship, "data": data},
            )
            self.store.audit("", "setup_configured", {"section": section})

    def policy(self, rule: PolicyRule, *, owner_authorized: bool) -> None:
        self._owner(owner_authorized)
        # One Core relationship; use the existing policy owner and preserve exact typed rules.
        PersonalPolicy(self.store).save(rule, owner_authorized=owner_authorized)
        self.store.put(
            "setup",
            self._key("policy"),
            {"section": "policy", "relationship": self.relationship, "data": {}},
        )

    def _bind(self, slot: str) -> None:
        def resolve() -> str:
            before = self.store.get("setup_provider", self._key(slot))
            if before["state"] != "configured":
                return ""
            value = self._vault().read(before["reference"]).value
            after = self.store.get("setup_provider", self._key(slot))
            if before != after:
                raise PermissionError("provider configuration changed during acquisition")
            return value

        self.pool.bind_resolver(slot, resolve)

    def provider(self, slot: str, secret: str, *, owner_authorized: bool) -> None:
        self._owner(owner_authorized)
        if (
            slot not in self.pool.slots
            or not secret
            or len(secret.encode()) > 2000
            or "\x00" in secret
        ):
            raise ValueError("known masked slot and bounded credential required")
        key = self._key(slot)
        with self.store.transaction():
            try:
                prior = self.store.get("setup_provider", key)
                if prior["state"] != "revoked":
                    raise StateConflict("revoke the existing provider binding before replacement")
            except KeyError:
                pass
            row = {
                "relationship": self.relationship,
                "slot": slot,
                "reference": new_id(),
                "state": "writing",
            }
            self.store.put("setup_provider", key, row)
        self._bind(slot)
        self._vault().put(secret, reference=row["reference"])
        with self.store.transaction():
            current = self.store.get("setup_provider", key)
            if current != row:
                self._vault().delete(row["reference"])
                raise StateConflict("provider binding revoked during write")
            self.store.put("setup_provider", key, {**row, "state": "configured"})
        self.pool.secret_for_adapter(slot)

    def revoke_provider(self, slot: str, *, owner_authorized: bool) -> None:
        self._owner(owner_authorized)
        key = self._key(slot)
        with self.store.transaction():
            row = self.store.get("setup_provider", key)
            self.store.put("setup_provider", key, {**row, "state": "revoking"})
        self._vault().delete(row["reference"])
        with self.store.transaction():
            if self.store.get("setup_provider", key) == {**row, "state": "revoking"}:
                self.store.put("setup_provider", key, {**row, "state": "revoked"})

    def recover(self) -> int:
        count = self.commissioning.recover()
        for row in self.store.all("setup_provider"):
            if row["relationship"] == self.relationship and row["state"] in {"writing", "revoking"}:
                self.revoke_provider(row["slot"], owner_authorized=True)
                count += 1
        return count

    def profile(self, section: str) -> dict[str, Any]:
        return dict(self.store.get("setup", self._key(section))["data"])

    def voice_profile(self) -> VoiceProfile:
        from .voice_identity import oscar_voice_profile

        try:
            settings = self.profile("voice")
        except KeyError:
            settings = {}
        return VoiceProfile(**{**asdict(oscar_voice_profile()), **settings})

    def snapshot(self) -> dict[str, Any]:
        sections = {
            r["section"] for r in self.store.all("setup") if r["relationship"] == self.relationship
        }
        bindings = [
            r for r in self.store.all("setup_provider") if r["relationship"] == self.relationship
        ]
        try:
            identity = self.store.get("core_identity", "core")
            identity_ready = identity["relationship"] == self.relationship
        except KeyError:
            identity_ready = False
        source = self.runtime.world.snapshot() if self.runtime.world else None
        paired = [
            r
            for r in self.store.all("commissioning")
            if r["relationship"] == self.relationship and r["state"] == "paired"
        ]
        live_nodes = {
            n["id"] for n in self.runtime.grid.nodes() if n["status"] in {"online", "degraded"}
        }
        connected = False
        for row in paired:
            try:
                session = self.store.get("session", row["session_id"])
                connected |= not session["revoked"] and row["node_id"] in live_nodes
            except KeyError:
                pass
        available = [
            r["slot"]
            for r in bindings
            if r["slot"] in self.pool.slots and bool(self.pool.secret_for_adapter(r["slot"]))
        ]
        operational = any(
            self.pool.slots[s].health == "healthy"
            and self.pool.eligible(s)
            and self.pool.slots[s].last_use is not None
            and 0 <= self.runtime.grid.clock() - float(self.pool.slots[s].last_use or 0) <= 300
            for s in available
        )
        return {
            "version": 1,
            "identity": {"configured": identity_ready, "operational": identity_ready},
            "pairing": {
                "configured": bool(paired),
                "connected": connected,
            },
            "provider": {
                "configured": any(r["state"] == "configured" for r in bindings),
                "credential_available": bool(available),
                "operational": operational,
                "verification": "recent_generation_observed"
                if operational
                else "live_provider_probe_required",
            },
            "persona": {"configured": "persona" in sections, "operational": "persona" in sections},
            "preferences": {"configured": "preferences" in sections},
            "policy": {
                "configured": "policy" in sections,
                "total_rules": len(PersonalPolicy(self.store).rules()),
                "full_access": "unavailable",
            },
            "sentry": {
                "configured": bool(source and source["sources"]),
                "mode": self.runtime.world.sentry.settings().mode.value
                if self.runtime.world
                else "unavailable",
            },
            "voice": {
                "configured": "voice" in sections,
                "operational": False,
                "verification": "owner_audio_match_map_calibration_required",
            },
            "resume": "configuration_preserved_authority_rechecked",
        }
