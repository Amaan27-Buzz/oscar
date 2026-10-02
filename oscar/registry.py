"""Versioned manifests, independent from provider implementations and the core runtime."""

import ipaddress
import json
import math
import re
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .freshness import Authority, SourceRef
from .models import DiscoveredModel, Funding, Inventory, ModelSpec, ProviderSpec
from .storage import Store


class Registry:
    def __init__(
        self, providers: list[ProviderSpec], models: list[ModelSpec], store: Store | None = None
    ):
        self.providers = {p.id: p for p in providers}
        if len(self.providers) != len(providers):
            raise ValueError("duplicate provider identifier")
        self.replace_models(models)
        self.store = store
        self.inventories: dict[tuple[str, str], Inventory] = {}
        self.probes: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.conflicts: list[dict[str, Any]] = []
        if store:
            for data in store.all("model_inventory"):
                if data["provider"] in self.providers:
                    self.apply_inventory(self.inventory_from_record(data))
            for data in store.all("generation_probe"):
                self.probes[(data["provider"], data["model"], data["slot"])] = data

    @staticmethod
    def inventory_from_record(data: dict[str, Any]) -> Inventory:
        return Inventory(
            data["provider"],
            data["slot"],
            SourceRef(**{**data["source"], "authority": Authority(data["source"]["authority"])}),
            tuple(
                DiscoveredModel(
                    **{
                        **m,
                        "capabilities": frozenset(m["capabilities"]),
                        "funding": Funding(m["funding"]),
                    }
                )
                for m in data["models"]
            ),
            data["complete"],
            data["pages"],
        )

    @staticmethod
    def inventory_record(inventory: Inventory) -> dict[str, Any]:
        data = asdict(inventory)
        for model in data["models"]:
            model["capabilities"] = sorted(model["capabilities"])
        return data

    def apply_inventory(self, inventory: Inventory) -> None:
        """Absence is authoritative only for a complete snapshot of this slot/product."""
        if inventory.provider not in self.providers:
            raise ValueError("inventory provider is not configured")
        provider = self.providers[inventory.provider]
        if inventory.slot not in provider.credential_envs and not provider.local:
            raise ValueError("inventory slot is not configured")
        key = inventory.provider, inventory.slot
        previous = self.inventories.get(key)
        if previous and previous.source.observed_at > inventory.source.observed_at:
            return
        ids = {m.id for m in inventory.models}
        if len(ids) != len(inventory.models):
            raise ValueError("duplicate discovered model")
        for model in list(self.models.values()):
            if (
                model.provider_id == inventory.provider
                and inventory.complete
                and model.id not in ids
            ):
                conflict: dict[str, Any] = {
                    "provider": inventory.provider,
                    "model": model.id,
                    "slot": inventory.slot,
                    "cached_source": model.provenance,
                    "live_source": asdict(inventory.source),
                    "resolution": "absent in complete live inventory; cached availability rejected",
                }
                self.conflicts = (self.conflicts + [conflict])[-200:]
                if self.store:
                    self.store.put("inventory_conflict", "/".join((*key, model.id)), conflict)
        for discovered in inventory.models:
            model_key = inventory.provider, discovered.id
            seed = self.models.get(model_key)
            if seed and seed.retired:
                conflict = {
                    "provider": inventory.provider,
                    "model": discovered.id,
                    "slot": inventory.slot,
                    "live_source": asdict(inventory.source),
                    "retirement_source": asdict(seed.retirement_source)
                    if seed.retirement_source
                    else None,
                    "resolution": (
                        "official retirement overrides inventory listing; excluded from routing"
                    ),
                }
                self.conflicts = (self.conflicts + [conflict])[-200:]
                if self.store:
                    self.store.put("inventory_conflict", "/".join((*key, discovered.id)), conflict)
            if seed is None:
                seed = ModelSpec(
                    inventory.provider,
                    discovered.id,
                    discovered.capabilities,
                    1 if "text" in discovered.capabilities else None,
                    {},
                    funding=discovered.funding,
                    funding_source=inventory.source
                    if discovered.funding != Funding.UNKNOWN
                    else None,
                    provenance="discovered candidate; unbenchmarked conservative tier 1",
                )
            # Fresh API limits/zero pricing outrank a cached seed. Missing fields do not
            # manufacture limits, capabilities, quality or account entitlements.
            if (
                seed.metadata_source is None
                or inventory.source.observed_at >= seed.metadata_source.observed_at
            ):
                self.models[model_key] = replace(
                    seed,
                    capabilities=seed.capabilities | discovered.capabilities,
                    context_limit=discovered.context_limit
                    if discovered.context_limit is not None
                    else seed.context_limit,
                    output_limit=discovered.output_limit
                    if discovered.output_limit is not None
                    else seed.output_limit,
                    funding=discovered.funding
                    if inventory.provider == "openrouter"
                    else seed.funding,
                    funding_source=inventory.source
                    if inventory.provider == "openrouter"
                    else seed.funding_source,
                    metadata_source=inventory.source,
                )
        self.inventories[key] = inventory
        if self.store:
            self.store.put("model_inventory", "/".join(key), self.inventory_record(inventory))

    def availability(self, provider: str, model: str, slot: str, now: float) -> str:
        spec = self.models[(provider, model)]
        if spec.retired:
            return "retired"
        inventory = self.inventories.get((provider, slot))
        if inventory is None or not inventory.source.current(now):
            return (
                "UNKNOWN / potentially stale"
                if self.providers[provider].discovery_required
                else "configured fallback"
            )
        entry = next((m for m in inventory.models if m.id == model), None)
        if entry is None:
            return "unavailable" if inventory.complete else "UNKNOWN / incomplete inventory"
        if entry.active is False:
            return "unavailable"
        probe = self.probes.get((provider, model, slot))
        if (
            probe
            and 0 <= now - probe["observed_at"] <= self.providers[provider].inventory_ttl_seconds
            and probe["success"] is False
        ):
            return "unavailable"
        return "listed via credential; generation entitlement not implied"

    def model_for_slot(self, provider: str, model: str, slot: str, now: float) -> ModelSpec:
        """Account fields cannot borrow another credential's pricing or limits."""
        spec = self.models[(provider, model)]
        if not self.providers[provider].discovery_required:
            return spec  # Explicit trusted/offline configuration.
        inventory = self.inventories.get((provider, slot))
        entry = (
            next((m for m in inventory.models if m.id == model), None)
            if inventory and inventory.source.current(now)
            else None
        )
        seed = self.seeds.get((provider, model))
        seed_current = bool(seed and seed.metadata_source and seed.metadata_source.current(now))
        capabilities = entry.capabilities if entry else frozenset()
        if seed and seed_current:
            capabilities |= seed.capabilities
        return replace(
            spec,
            capabilities=capabilities,
            context_limit=entry.context_limit
            if entry and entry.context_limit is not None
            else seed.context_limit
            if seed and seed_current
            else None,
            output_limit=entry.output_limit
            if entry and entry.output_limit is not None
            else seed.output_limit
            if seed and seed_current
            else None,
            funding=entry.funding if provider == "openrouter" and entry else spec.funding,
            funding_source=inventory.source
            if provider == "openrouter" and entry and inventory
            else spec.funding_source,
            price_per_million=0
            if provider == "openrouter" and entry and entry.funding == Funding.FREE
            else None
            if provider == "openrouter"
            else spec.price_per_million,
        )

    def observe_generation(
        self,
        provider: str,
        model: str,
        slot: str,
        now: float,
        success: bool,
        category: str | None = None,
    ) -> None:
        data = {
            "provider": provider,
            "model": model,
            "slot": slot,
            "observed_at": now,
            "success": success,
            "category": category,
            "source": self.providers[provider].base_url,
            "scope": "account",
        }
        self.probes[(provider, model, slot)] = data
        if success:
            self.models[(provider, model)] = replace(
                self.models[(provider, model)], last_verified=now
            )
        if self.store:
            self.store.put("generation_probe", "/".join((provider, slot, model)), data)

    def replace_models(self, models: list[ModelSpec]) -> None:
        index = {(m.provider_id, m.id): m for m in models}
        if len(index) != len(models) or any(m.provider_id not in self.providers for m in models):
            raise ValueError("invalid model inventory")
        self.models = index
        self.seeds = index.copy()

    @classmethod
    def load(cls, path: Path, store: Store | None = None) -> "Registry":
        data = json.loads(path.read_text())
        if (
            not isinstance(data, dict)
            or set(data) != {"version", "providers", "models"}
            or data["version"] != 1
        ):
            raise ValueError("unsupported registry manifest")
        providers: list[ProviderSpec] = []
        for item in data["providers"]:
            provider = ProviderSpec(
                **{
                    **item,
                    "allowed_tasks": tuple(item["allowed_tasks"])
                    if item.get("allowed_tasks") is not None
                    else None,
                }
            )
            if any(
                type(flag) is not bool
                for flag in (
                    provider.local,
                    provider.private,
                    provider.enabled,
                    provider.discovery_required,
                )
            ):
                raise ValueError("provider flags must be booleans")
            if not re.fullmatch(r"[a-z0-9_-]{1,64}", provider.id):
                raise ValueError("invalid provider identifier")
            parsed = urlparse(provider.base_url)
            if (
                parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
                or not parsed.hostname
                or parsed.scheme not in {"http", "https"}
            ):
                raise ValueError("endpoint must not contain credentials/query/fragment")
            if not provider.local and parsed.scheme != "https":
                raise ValueError("hosted endpoints require TLS")
            if provider.local and parsed.hostname != "localhost":
                try:
                    address = ipaddress.ip_address(parsed.hostname)
                except ValueError:
                    raise ValueError(
                        "local endpoints require an explicit private/loopback IP"
                    ) from None
                if not address.is_private and not address.is_loopback:
                    raise ValueError("public hosted endpoint cannot be marked local")
            if any(
                not re.fullmatch(r"[A-Z][A-Z0-9_]*", env)
                for env in provider.credential_envs.values()
            ):
                raise ValueError("credential references must be environment variable names")
            if any(
                not re.fullmatch(r"[a-z0-9_-]{1,64}", slot) for slot in provider.credential_envs
            ):
                raise ValueError("invalid masked slot identifier")
            if provider.inventory_ttl_seconds <= 0 or not math.isfinite(
                provider.inventory_ttl_seconds
            ):
                raise ValueError("invalid inventory TTL")
            if set(provider.credential_pools) - set(provider.credential_envs):
                raise ValueError("quota pool references an unknown slot")
            for pool in [provider.quota_pool, *provider.credential_pools.values()]:
                if pool is not None and not re.fullmatch(r"[a-z0-9/_-]{1,100}", pool):
                    raise ValueError("invalid quota pool identifier")
            providers.append(provider)
        models: list[ModelSpec] = []
        for item in data["models"]:
            converted: dict[str, Any] = {
                **item,
                "capabilities": frozenset(item["capabilities"]),
                "funding": Funding(item.get("funding", "unknown")),
            }
            for field in ("metadata_source", "funding_source", "retirement_source"):
                if item.get(field) is not None:
                    source = item[field]
                    converted[field] = SourceRef(
                        **{**source, "authority": Authority(source["authority"])}
                    )
            model = ModelSpec(**converted)
            if type(model.retired) is not bool:
                raise ValueError("retirement flag must be boolean")
            if (
                not isinstance(model.id, str)
                or not model.id
                or len(model.id) > 200
                or not re.fullmatch(r"[a-zA-Z0-9/_.:@~-]+", model.id)
                or not model.capabilities
                or not model.provenance
            ):
                raise ValueError("invalid model metadata")
            if model.quality is not None and (
                type(model.quality) is not int or not 1 <= model.quality <= 5
            ):
                raise ValueError("invalid quality tier")
            for number in (
                model.price_per_million,
                model.latency_ms,
                model.reliability,
                model.context_limit,
                model.output_limit,
                *model.affinities.values(),
            ):
                if number is not None and (not math.isfinite(number) or number < 0):
                    raise ValueError("invalid numeric metadata")
            if any(not 0 <= value <= 1 for value in model.affinities.values()):
                raise ValueError("affinities must be between zero and one")
            if model.reliability is not None and not 0 <= model.reliability <= 1:
                raise ValueError("invalid reliability")
            models.append(model)
        return cls(providers, models, store)
