"""Small native adapters: OpenAI-compatible, Google generateContent and Ollama chat.

HTTP errors are categorical. No remote body, URL with credentials, or exception text is logged.
TLS and inherited proxy/CA settings are preserved; redirects are rejected.
"""

import json
from collections.abc import Callable
from http.client import HTTPException
from time import monotonic
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
    if status == 429:
        try:
            data = json.loads(body)
            if data.get("error", {}).get("code") in {"insufficient_quota", "quota_exceeded"}:
                return Failure.QUOTA
        except (ValueError, AttributeError, TypeError):
            pass
        return Failure.RATE_LIMIT
    if status in {401, 403}:
        return Failure.CREDENTIAL
    if status == 404:
        return Failure.MODEL
    if status in {400, 422}:
        return Failure.CAPABILITY
    if status >= 500:
        return Failure.PROVIDER
    return Failure.NETWORK


class HTTPAdapter:
    def __init__(self, kind: str):
        if kind not in {"openai", "google", "ollama"}:
            raise ValueError("unsupported adapter")
        self.kind = kind
        self.opener = build_opener(NoRedirects())

    def _request(
        self, provider: ProviderSpec, model: str, secret: str, request: ModelRequest, stream: bool
    ) -> Request:
        body: dict[str, Any]
        headers = {"Content-Type": "application/json"}
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
                if "structured" in request.required:
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
        check_cancel()
        emitted = False
        deadline = monotonic() + timeout
        try:
            with self.opener.open(
                self._request(provider, model, secret, request, sink is not None), timeout=timeout
            ) as response:
                raw, pending, texts = bytearray(), bytearray(), []
                last: dict[str, Any] = {}
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
                        if not isinstance(last, dict) or "error" in last:
                            raise ProviderError(Failure.PROVIDER, emitted=emitted)
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
                    if not isinstance(last, dict) or "error" in last:
                        raise ProviderError(Failure.PROVIDER)
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
                )
        except HTTPError as error:
            try:
                body = error.read(4096)
            except (HTTPException, OSError):
                body = b""
            category = error_category(error.code, error.headers, body)
            raw_retry = error.headers.get("Retry-After", "30")
            retry = float(raw_retry) if raw_retry.isdecimal() else 30.0
            raise ProviderError(category, retry_after=min(3600, retry), emitted=emitted) from None
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
        path = "/tags" if self.kind == "ollama" else "/models"
        headers = (
            {"x-goog-api-key": secret}
            if self.kind == "google"
            else {"Authorization": "Bearer " + secret}
        )
        request = Request(provider.base_url.rstrip("/") + path, headers=headers)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                data = json.loads(response.read(2_000_001))
            entries = data.get("data", data.get("models", []))
            models = [str(item.get("id", item.get("name", ""))) for item in entries]
            return [m.removeprefix("models/") for m in models if m]
        except HTTPError as error:
            raise ProviderError(error_category(error.code, error.headers)) from None
        except URLError as error:
            policy = "Tunnel connection failed: 403" in str(error.reason)
            raise ProviderError(Failure.NETWORK_POLICY if policy else Failure.NETWORK) from None
        except (HTTPException, OSError, ValueError, TypeError, AttributeError):
            raise ProviderError(Failure.NETWORK) from None
