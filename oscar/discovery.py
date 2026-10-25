"""Bounded native inventory/account reads. Never retains raw provider bodies or key metadata."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from http.client import HTTPException
from time import monotonic, time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener

from .freshness import Authority, SourceRef
from .http_client import NoRedirects
from .models import (
    DiscoveredModel,
    Failure,
    Funding,
    Inventory,
    ProviderError,
    ProviderSpec,
    RateLimits,
)
from .providers import count, error_category


@dataclass(frozen=True)
class AccountObservation:
    source: SourceRef
    free_tier: bool | None = None
    limits: RateLimits | None = None
    credit_cap_remaining: float | None = None


class HTTPDiscovery:
    def __init__(self, clock: Callable[[], float] = time):
        self.opener = build_opener(NoRedirects())
        self.clock = clock

    def _get(
        self,
        provider: ProviderSpec,
        secret: str,
        path: str,
        timeout: float,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"User-Agent": "OSCAR/0.1", "Accept": "application/json"}
        if secret:
            headers["x-goog-api-key" if provider.adapter == "google" else "Authorization"] = (
                secret if provider.adapter == "google" else "Bearer " + secret
            )
        if payload is not None:
            headers["Content-Type"] = "application/json"
        try:
            with self.opener.open(
                Request(
                    provider.base_url.rstrip("/") + path,
                    data=json.dumps(payload).encode() if payload is not None else None,
                    headers=headers,
                ),
                timeout=timeout,
            ) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ProviderError(Failure.CAPABILITY)
                data = json.loads(raw)
                if not isinstance(data, dict) or "error" in data:
                    raise ProviderError(Failure.CAPABILITY)
                return data
        except HTTPError as error:
            error.close()
            raise ProviderError(
                error_category(error.code, error.headers), http_status=error.code
            ) from None
        except URLError as error:
            policy = "Tunnel connection failed: 403" in str(error.reason)
            raise ProviderError(Failure.NETWORK_POLICY if policy else Failure.NETWORK) from None
        except (HTTPException, OSError):
            raise ProviderError(Failure.NETWORK) from None
        except (ValueError, TypeError, AttributeError):
            raise ProviderError(Failure.CAPABILITY) from None

    def local_ollama_capabilities(
        self, provider: ProviderSpec, model: str, secret: str, timeout: float
    ) -> frozenset[str]:
        """A loopback server can proxy cloud models; inspect before private disclosure."""
        return frozenset(
            self._local_ollama_metadata(provider, model, secret, timeout)["capabilities"]
        )

    def _local_ollama_metadata(
        self, provider: ProviderSpec, model: str, secret: str, timeout: float
    ) -> dict[str, Any]:
        if not provider.local or provider.adapter != "ollama":
            raise ProviderError(Failure.CAPABILITY)
        data = self._get(provider, secret, "/show", timeout, payload={"model": model})
        capabilities = data.get("capabilities")
        if (
            any(data.get(key, "") != "" for key in ("remote_host", "remote_model"))
            or not isinstance(capabilities, list)
            or len(capabilities) > 32
            or any(not isinstance(c, str) or not 1 <= len(c) <= 64 for c in capabilities)
        ):
            raise ProviderError(Failure.CAPABILITY)
        return data

    @staticmethod
    def _model(item: Any, provider: ProviderSpec) -> DiscoveredModel:
        if not isinstance(item, dict):
            raise ProviderError(Failure.CAPABILITY)
        identifier = item.get("id", item.get("name", ""))
        if not isinstance(identifier, str) or not re.fullmatch(
            r"[a-zA-Z0-9/_.:@~-]{1,200}", identifier
        ):
            raise ProviderError(Failure.CAPABILITY)
        identifier = identifier.removeprefix("models/")
        caps: set[str] = set()
        if provider.adapter == "google" and "generateContent" in item.get(
            "supportedGenerationMethods", []
        ):
            caps.add("text")
        if provider.id == "openrouter":
            if "text" in item.get("architecture", {}).get("output_modalities", ["text"]):
                caps.add("text")
            if "response_format" in item.get("supported_parameters", []):
                caps.add("structured")
        context = count(
            item.get("inputTokenLimit", item.get("context_window", item.get("context_length")))
        )
        output = count(
            item.get(
                "outputTokenLimit",
                item.get(
                    "max_completion_tokens",
                    item.get("top_provider", {}).get("max_completion_tokens"),
                ),
            )
        )
        funding = Funding.UNKNOWN
        pricing = item.get("pricing", {})
        if provider.id == "openrouter" and pricing:
            try:
                # Zero token pricing alone is insufficient when request/tool fees exist.
                if (
                    "prompt" in pricing
                    and "completion" in pricing
                    and all(float(n) == 0 for n in pricing.values())
                ):
                    funding = Funding.FREE
            except (ValueError, TypeError):
                pass
        active = item.get("active")
        return DiscoveredModel(
            identifier,
            frozenset(caps),
            context,
            output,
            funding,
            active if type(active) is bool else None,
        )

    def inventory(
        self, provider: ProviderSpec, slot: str, secret: str, timeout: float = 10
    ) -> Inventory:
        deadline = monotonic() + timeout
        path = (
            "/tags"
            if provider.adapter == "ollama"
            else "/models/user"
            if provider.id == "openrouter"
            else "/models"
        )
        next_path, pages = path, 0
        rows: list[DiscoveredModel] = []
        for _ in range(10):
            data = self._get(provider, secret, next_path, timeout)
            entries = data.get("data", data.get("models"))
            if not isinstance(entries, list):
                raise ProviderError(Failure.CAPABILITY)
            rows.extend(self._model(item, provider) for item in entries)
            pages += 1
            token = data.get("nextPageToken")
            if not token:
                break
            if provider.adapter != "google" or not isinstance(token, str) or len(token) > 2048:
                raise ProviderError(Failure.CAPABILITY)
            next_path = path + "?pageSize=1000&pageToken=" + quote(token, safe="")
        source = SourceRef(
            provider.base_url.rstrip("/") + path,
            Authority.LIVE_API,
            "account",
            self.clock(),
            provider.inventory_ttl_seconds,
        )
        if secret and any(secret in model.id for model in rows):
            raise ProviderError(Failure.CAPABILITY)
        if len({m.id for m in rows}) != len(rows):
            raise ProviderError(Failure.CAPABILITY)
        if provider.local and provider.adapter == "ollama":
            if len(rows) > 64:
                raise ProviderError(Failure.CAPABILITY)
            enriched = []
            for model in rows:
                try:
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise ProviderError(Failure.NETWORK)
                    metadata = self._local_ollama_metadata(provider, model.id, secret, remaining)
                    declared = metadata["capabilities"]
                    caps = {"text", "structured"} if "completion" in declared else set()
                    if caps and "vision" in declared:
                        caps.add("vision")
                    info = metadata.get("model_info", {})
                    architecture = (
                        info.get("general.architecture") if isinstance(info, dict) else None
                    )
                    context = (
                        count(info.get(architecture + ".context_length"))
                        if isinstance(architecture, str) and len(architecture) <= 80
                        else None
                    )
                    enriched.append(
                        replace(
                            model,
                            capabilities=frozenset(caps),
                            context_limit=context or None,
                            # Ollama num_predict shares the model's total context envelope.
                            output_limit=context or None,
                            funding=Funding.LOCAL,
                            active=bool(caps),
                        )
                    )
                except ProviderError:
                    # Keep listed identity, but never activate unavailable or forwarded metadata.
                    enriched.append(replace(model, active=False))
            rows = enriched
        links = data.get("links", {})
        complete = not bool(token) and isinstance(links, dict) and not bool(links.get("next"))
        return Inventory(provider.id, slot, source, tuple(rows), complete, pages)

    def account(
        self, provider: ProviderSpec, secret: str, timeout: float = 10
    ) -> AccountObservation | None:
        if provider.id != "openrouter":
            return None  # No invented balance endpoints or entitlement heuristics.
        data = self._get(provider, secret, "/key", timeout).get("data", {})
        if not isinstance(data, dict):
            raise ProviderError(Failure.CAPABILITY)
        daily = data.get("free_model_daily_requests", {})
        if not isinstance(daily, dict):
            daily = {}
        now = self.clock()
        source = SourceRef(
            provider.base_url.rstrip("/") + "/key", Authority.LIVE_API, "account", now
        )
        cap = data.get("limit_remaining")
        return AccountObservation(
            source,
            data.get("is_free_tier") if type(data.get("is_free_tier")) is bool else None,
            RateLimits(
                request_limit=count(daily.get("limit")),
                remaining_requests=count(daily.get("remaining")),
                requests_reset_at=(int(now / 86400) + 1) * 86400,
                request_window="day",
                source=source.identity,
            ),
            float(cap)
            if isinstance(cap, int | float) and not isinstance(cap, bool) and cap >= 0
            else None,
        )
