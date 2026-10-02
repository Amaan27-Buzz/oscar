"""Versioned manifests, independent from provider implementations and the core runtime."""

import ipaddress
import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .models import Funding, ModelSpec, ProviderSpec


class Registry:
    def __init__(self, providers: list[ProviderSpec], models: list[ModelSpec]):
        self.providers = {p.id: p for p in providers}
        if len(self.providers) != len(providers):
            raise ValueError("duplicate provider identifier")
        self.replace_models(models)

    def replace_models(self, models: list[ModelSpec]) -> None:
        index = {(m.provider_id, m.id): m for m in models}
        if len(index) != len(models) or any(m.provider_id not in self.providers for m in models):
            raise ValueError("invalid model inventory")
        self.models = index

    @classmethod
    def load(cls, path: Path) -> "Registry":
        data = json.loads(path.read_text())
        if (
            not isinstance(data, dict)
            or set(data) != {"version", "providers", "models"}
            or data["version"] != 1
        ):
            raise ValueError("unsupported registry manifest")
        providers: list[ProviderSpec] = []
        for item in data["providers"]:
            provider = ProviderSpec(**item)
            if any(
                type(flag) is not bool
                for flag in (provider.local, provider.private, provider.enabled)
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
            providers.append(provider)
        models: list[ModelSpec] = []
        for item in data["models"]:
            converted: dict[str, Any] = {
                **item,
                "capabilities": frozenset(item["capabilities"]),
                "funding": Funding(item.get("funding", "unknown")),
            }
            model = ModelSpec(**converted)
            if (
                not isinstance(model.id, str)
                or not model.id
                or len(model.id) > 200
                or not re.fullmatch(r"[a-zA-Z0-9/_.:@-]+", model.id)
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
        return cls(providers, models)
