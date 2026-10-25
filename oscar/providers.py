"""Small native adapters: OpenAI-compatible, Google generateContent and Ollama chat.

HTTP errors are categorical. No remote body, URL with credentials, or exception text is logged.
TLS and inherited proxy/CA settings are preserved; redirects are rejected.
"""

import json
import re
from collections.abc import Callable
from datetime import UTC
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from time import monotonic, time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener

from .http_client import NoRedirects
from .models import (
    Failure,
    ModelRequest,
    ProviderError,
    ProviderResponse,
    ProviderSpec,
    RateLimits,
    StreamSink,
)


class Adapter(Protocol):
    def generate(
        self,
        provider: ProviderSpec,
        model: str,
        secret: str,
        request: ModelRequest,
        timeout: float,
        check_cancel: Callable[[], None],
        sink: StreamSink | None = None,
    ) -> ProviderResponse: ...


def count(value: Any) -> int | None:
    return value if type(value) is int and 0 <= value <= 10**12 else None


def header_count(headers: Any, name: str) -> int | None:
    raw = headers.get(name)
    if raw is not None and raw.isdecimal():
        return count(int(raw))
    return None


def error_category(status: int, headers: Any, body: bytes = b"") -> Failure:
    if headers.get("x-mitmproxy-blocked-reason") or headers.get("x-deny-reason"):
        return Failure.NETWORK_POLICY
    code = business_code(body)
    if code in {"model_decommissioned", "model_not_found", "model_not_active", "1211", "1221"}:
        return Failure.MODEL
    if code == "1315":
        return Failure.PRODUCT
    if code in {
        "insufficient_quota",
        "quota_exceeded",
        "1113",
        "1308",
        "1310",
        "1316",
        "1317",
        "1318",
        "1319",
        "1320",
        "1321",
    }:
        return Failure.QUOTA
    if code == "1305":
        return Failure.CAPACITY
    if code in {"1311", "1309", "1314"}:
        return Failure.PRODUCT
    if status in {402, 429}:
        if (
            code in {"1302", "rate_limit_exceeded"}
            or headers.get("Retry-After")
            or headers.get("x-ratelimit-remaining-requests") == "0"
            or headers.get("x-ratelimit-remaining") == "0"
        ):
            return Failure.RATE_LIMIT
        if status == 402:
            return Failure.FUNDING
        return Failure.UNKNOWN_LIMIT
    if status == 401:
        return Failure.CREDENTIAL
    if status == 403:
        return Failure.ACCESS  # Access denial is not proof that a credential is invalid.
    if status == 404:
        return Failure.MODEL
    if status in {400, 422}:
        return Failure.CAPABILITY
    if status >= 500:
        return Failure.PROVIDER
    return Failure.NETWORK


def business_code(body: bytes) -> str | None:
    try:
        code = str(json.loads(body).get("error", {}).get("code"))
        if code in {
            "insufficient_quota",
            "quota_exceeded",
            "model_decommissioned",
            "model_not_found",
            "model_not_active",
            "rate_limit_exceeded",
        } or code in {
            str(n)
            for n in [
                1113,
                1211,
                1220,
                1221,
                1302,
                1305,
                1308,
                1309,
                1310,
                1311,
                1313,
                1314,
                1315,
                1316,
                1317,
                1318,
                1319,
                1320,
                1321,
            ]
        }:
            return code
    except (ValueError, AttributeError, TypeError):
        pass
    return None


def reset_time(raw: str | None, now: float) -> float | None:
    if not raw:
        return None
    if re.fullmatch(r"(?:\d+(?:\.\d+)?(?:ms|[smhd]))+", raw):
        units = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400}
        return now + sum(
            float(n) * units[u] for n, u in re.findall(r"(\d+(?:\.\d+)?)(ms|[smhd])", raw)
        )
    try:
        return parsedate_to_datetime(raw).replace(tzinfo=UTC).timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def rate_limits(headers: Any, provider: str, now: float | None = None) -> RateLimits:
    now = time() if now is None else now
    retry = headers.get("Retry-After")
    retry_seconds = float(retry) if retry and re.fullmatch(r"\d+(?:\.\d+)?", retry) else None
    if retry_seconds is None and retry:
        reset = reset_time(retry, now)
        retry_seconds = max(0, reset - now) if reset is not None else None
    generic_reset = headers.get("x-ratelimit-reset")
    # Generic numeric reset headers do not establish seconds versus milliseconds.
    # Preserve a bounded numeric hint; do not invent a reset horizon without units.
    generic_reset_at = reset_time(generic_reset, now)
    generic_reset_hint = (
        generic_reset
        if generic_reset and re.fullmatch(r"\d{1,20}(?:\.\d{1,6})?", generic_reset)
        else None
    )
    request_limit = header_count(headers, "x-ratelimit-limit-requests")
    remaining_requests = header_count(headers, "x-ratelimit-remaining-requests")
    return RateLimits(
        request_limit if request_limit is not None else header_count(headers, "x-ratelimit-limit"),
        header_count(headers, "x-ratelimit-limit-tokens"),
        remaining_requests
        if remaining_requests is not None
        else header_count(headers, "x-ratelimit-remaining"),
        header_count(headers, "x-ratelimit-remaining-tokens"),
        reset_time(headers.get("x-ratelimit-reset-requests"), now) or generic_reset_at,
        reset_time(headers.get("x-ratelimit-reset-tokens"), now),
        retry_seconds,
        "day" if provider == "groq" else "UNKNOWN",
        "minute" if provider == "groq" else "UNKNOWN",
        request_reset_hint=generic_reset_hint,
    )


def safe_identity(value: Any) -> str | None:
    return (
        value
        if isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9/_.:@~ -]{1,200}", value)
        else None
    )


def inline_error(data: dict[str, Any], headers: Any, provider: str, emitted: bool) -> ProviderError:
    """Some aggregators return a backing error inside HTTP 200; retain safe metadata only."""
    body = json.dumps(data).encode()
    code = data.get("error", {}).get("code") if isinstance(data.get("error"), dict) else None
    status = (
        int(str(code))
        if str(code) in {"400", "401", "402", "403", "404", "429", "500", "502", "503"}
        else 500
    )
    limits = rate_limits(headers, provider)
    category = error_category(status, headers, body)
    if category == Failure.CREDENTIAL:
        category = Failure.ACCESS  # An inline/backing 401 does not prove our API key invalid.
    return ProviderError(
        category,
        emitted=emitted,
        http_status=200,
        business_code=business_code(body),
        rate_limits=limits,
    )


class HTTPAdapter:
    def __init__(self, kind: str):
        if kind not in {"openai", "google", "ollama"}:
            raise ValueError("unsupported adapter")
        self.kind = kind
        self.opener = build_opener(NoRedirects())

    def _request(
        self, provider: ProviderSpec, model: str, secret: str, request: ModelRequest, stream: bool
    ) -> Request:
        if request.ollama_think is not None and self.kind != "ollama":
            raise ProviderError(Failure.CAPABILITY)
        body: dict[str, Any]
        headers = {"Content-Type": "application/json", "User-Agent": "OSCAR/0.1"}
        root = provider.base_url.rstrip("/")
        if self.kind == "google":
            if secret:
                headers["x-goog-api-key"] = secret
            operation = "streamGenerateContent?alt=sse" if stream else "generateContent"
            url = f"{root}/models/{quote(model, safe='')}:{operation}"
            config: dict[str, Any] = {"maxOutputTokens": request.max_output_tokens}
            if "structured" in request.required:
                config["responseMimeType"] = "application/json"
            body = {
                "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
                "generationConfig": config,
            }
        else:
            if secret:
                headers["Authorization"] = "Bearer " + secret
            url = root + ("/chat" if self.kind == "ollama" else "/chat/completions")
            body = {
                "model": model,
                "messages": [{"role": "user", "content": request.prompt}],
                "stream": stream,
            }
            if self.kind == "ollama":
                body["options"] = {"num_predict": request.max_output_tokens}
                if request.ollama_think is not None:
                    body["think"] = request.ollama_think
                if "structured" in request.required:
                    if request.executive_plan:
                        from .planning_contract import executive_plan_schema

                        body["format"] = executive_plan_schema(
                            observation_only=request.executive_observation
                        )
                        body["options"]["temperature"] = 0
                    else:
                        body["format"] = "json"
            else:
                body["max_tokens"] = request.max_output_tokens
                if "structured" in request.required:
                    body["response_format"] = {"type": "json_object"}
        return Request(url, json.dumps(body).encode(), headers, method="POST")

    def _text(self, data: dict[str, Any], streaming: bool = False) -> str:
        if self.kind == "google":
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            return "".join(
                part.get("text", "") for part in candidates[0].get("content", {}).get("parts", [])
            )
        if self.kind == "ollama":
            content = data.get("message", {}).get("content", "")
            if not isinstance(content, str):
                raise ProviderError(Failure.CAPABILITY)
            return content
        choices = data.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("delta" if streaming else "message", {})
        content = message.get("content", "")
        if content is None:
            return ""
        if not isinstance(content, str):
            raise ProviderError(Failure.CAPABILITY)
        return content

    def generate(
        self,
        provider: ProviderSpec,
        model: str,
        secret: str,
        request: ModelRequest,
        timeout: float,
        check_cancel: Callable[[], None],
        sink: StreamSink | None = None,
    ) -> ProviderResponse:
        if request.required - {"text", "structured"}:
            raise ProviderError(Failure.CAPABILITY)
        if provider.id == "ollama-cloud" and "structured" in request.required:
            raise ProviderError(Failure.CAPABILITY)  # Official cloud docs exclude this feature.
        check_cancel()
        emitted = False
        deadline = monotonic() + timeout
        try:
            with self.opener.open(
                self._request(provider, model, secret, request, sink is not None), timeout=timeout
            ) as response:
                raw, pending, texts = bytearray(), bytearray(), []
                last: dict[str, Any] = {}
                actual_model: str | None = None
                actual_provider: str | None = None
                complete_stream = False
                while True:
                    check_cancel()
                    if monotonic() > deadline:
                        raise ProviderError(Failure.NETWORK, emitted=emitted)
                    chunk = response.read1(65536)
                    if not chunk:
                        break
                    raw.extend(chunk)
                    if len(raw) > 2_000_000:
                        raise ProviderError(Failure.CAPABILITY, emitted=emitted)
                    if sink is None:
                        continue
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line, _, rest = pending.partition(b"\n")
                        pending = bytearray(rest)
                        line = line.strip()
                        if self.kind != "ollama":
                            if not line.startswith(b"data:"):
                                continue
                            line = line[5:].strip()
                        if line == b"[DONE]":
                            complete_stream = True
                            continue
                        if not line:
                            continue
                        last = json.loads(line)
                        if not isinstance(last, dict):
                            raise ProviderError(Failure.PROVIDER, emitted=emitted)
                        if "error" in last:
                            raise inline_error(last, response.headers, provider.id, emitted)
                        actual_model = (
                            safe_identity(last.get("modelVersion", last.get("model")))
                            or actual_model
                        )
                        actual_provider = safe_identity(last.get("provider")) or actual_provider
                        text = self._text(last, streaming=True)
                        if text:
                            emitted = True
                            texts.append(text)
                            sink(text)
                        if (
                            last.get("done") is True
                            or any(c.get("finish_reason") for c in last.get("choices", []))
                            or any(c.get("finishReason") for c in last.get("candidates", []))
                        ):
                            complete_stream = True
                if sink is None:
                    last = json.loads(raw)
                    if not isinstance(last, dict):
                        raise ProviderError(Failure.PROVIDER)
                    if "error" in last:
                        raise inline_error(last, response.headers, provider.id, False)
                    actual_model = safe_identity(last.get("modelVersion", last.get("model")))
                    actual_provider = safe_identity(last.get("provider"))
                    text = self._text(last)
                else:
                    if not complete_stream:
                        raise ProviderError(Failure.NETWORK, emitted=emitted)
                    text = "".join(texts)
                if not text.strip():
                    raise ProviderError(Failure.CAPABILITY, emitted=emitted)
                structured: bool | None = None
                if "structured" in request.required:
                    try:
                        structured = isinstance(json.loads(text), dict | list)
                    except ValueError:
                        structured = False
                    if not structured:
                        raise ProviderError(Failure.STRUCTURED, emitted=emitted)
                usage = last.get("usage", last.get("usageMetadata", {}))
                input_tokens = count(usage.get("prompt_tokens", usage.get("promptTokenCount")))
                output_tokens = count(
                    usage.get("completion_tokens", usage.get("candidatesTokenCount"))
                )
                if self.kind == "ollama":
                    input_tokens, output_tokens = (
                        count(last.get("prompt_eval_count")),
                        count(last.get("eval_count")),
                    )
                return ProviderResponse(
                    text,
                    input_tokens,
                    output_tokens,
                    header_count(response.headers, "x-ratelimit-remaining-requests"),
                    header_count(response.headers, "x-ratelimit-remaining-tokens"),
                    structured_ok=structured,
                    actual_model=actual_model,
                    actual_provider=actual_provider,
                    rate_limits=rate_limits(response.headers, provider.id),
                )
        except HTTPError as error:
            try:
                body = error.read(4096)
            except (HTTPException, OSError):
                body = b""
            finally:
                error.close()
            category = error_category(error.code, error.headers, body)
            limits = rate_limits(error.headers, provider.id)
            raise ProviderError(
                category,
                retry_after=min(3600, limits.retry_after or 30),
                emitted=emitted,
                http_status=error.code,
                business_code=business_code(body),
                rate_limits=limits,
            ) from None
        except URLError as error:
            # CONNECT policy denial is raised by urllib before any provider HTTP response.
            policy = "Tunnel connection failed: 403" in str(error.reason)
            raise ProviderError(
                Failure.NETWORK_POLICY if policy else Failure.NETWORK, emitted=emitted
            ) from None
        except (HTTPException, TimeoutError, OSError):
            raise ProviderError(Failure.NETWORK, emitted=emitted) from None
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ProviderError(Failure.CAPABILITY, emitted=emitted) from None

    def discover(self, provider: ProviderSpec, secret: str, timeout: float = 10) -> list[str]:
        """Compatibility view of the canonical bounded/paginated native inventory read."""
        from .discovery import HTTPDiscovery

        discovery = HTTPDiscovery()
        discovery.opener = self.opener
        inventory = discovery.inventory(provider, "inventory-read", secret, timeout)
        return [model.id for model in inventory.models]
