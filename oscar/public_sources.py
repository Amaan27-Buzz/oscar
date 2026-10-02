"""Small credential-free reads of official pages selected by search.

Returned text is a bounded source excerpt, not independently verified fact.
No page body is persisted here, and redirects never leave the selected source.
"""

import re
from collections.abc import Callable
from html.parser import HTMLParser
from http.client import HTTPException
from math import isfinite
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from .http_client import NoRedirects
from .models import Failure, ProviderError

OFFICIAL_HOSTS = frozenset(
    {
        "console.groq.com",
        "openrouter.ai",
        "ai.google.dev",
        "build.nvidia.com",
        "docs.api.nvidia.com",
        "docs.z.ai",
        "docs.ollama.com",
        "ollama.com",
    }
)
_BODY_LIMIT = 500_000
_EXCERPT_LIMIT = 1500
_TOPICS = re.compile(
    r"\b(model\w*|free|developer\w*|pricing|prices?|quota\w*|rates?|subscriptions?"
    r"|deprecat\w*|retir\w*|limits?)\b",
    re.IGNORECASE,
)
_CHALLENGE = re.compile(
    r"just a moment|enable javascript|verify you are human|checking your browser"
    r"|attention required|access denied|403 forbidden|404 not found",
    re.IGNORECASE,
)


class _VisibleText(HTMLParser):
    _ignored = {"script", "style", "header", "nav", "footer", "svg", "noscript", "aside"}
    _void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta"}
    _blocks = {"p", "li", "div", "section", "article", "br", "tr", "table"} | {
        f"h{n}" for n in range(1, 7)
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden: list[str] = []
        self.parts: list[str] = []
        self.paragraphs: list[str] = []

    def flush(self) -> None:
        text = " ".join(" ".join(self.parts).split())
        if text:
            self.paragraphs.append(text)
        self.parts.clear()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.hidden:
            if tag not in self._void:
                self.hidden.append(tag)
            return
        attributes = dict(attrs)
        if tag in self._ignored or attributes.get("role") in {
            "navigation",
            "banner",
            "contentinfo",
        }:
            if tag not in self._void:
                self.hidden.append(tag)
            return
        if tag in self._blocks:
            self.flush()

    def handle_endtag(self, tag: str) -> None:
        if self.hidden:
            if tag in self.hidden:
                index = len(self.hidden) - 1 - self.hidden[::-1].index(tag)
                del self.hidden[index:]
            return
        if tag in self._blocks:
            self.flush()

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def _identity(text: str) -> str:
    return text


def _meaningful(text: str) -> bool:
    return len(text) >= 40 and len(re.findall(r"[A-Za-z]{2,}", text)) >= 6


def read_official_page(
    url: str,
    timeout: float,
    *,
    opener: Any = None,
    redact: Callable[[str], str] = _identity,
) -> str:
    """Read an exact official HTTPS page and return at most 1,500 characters.

    ``opener`` is injectable for isolated HTTP contract tests; production uses
    the no-redirect transport. ``redact`` runs before excerpt truncation.
    """
    try:
        parsed = urlsplit(url)
        if (
            len(url) > 2048
            or parsed.scheme != "https"
            or parsed.hostname not in OFFICIAL_HOSTS
            or parsed.port not in {None, 443}
            or parsed.username is not None
            or parsed.password is not None
            or "?" in url
            or "#" in url
            or not isfinite(timeout)
            or timeout <= 0
        ):
            raise ProviderError(Failure.CAPABILITY)
        client = opener if opener is not None else build_opener(NoRedirects())
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html, text/plain, text/markdown",
                "Accept-Encoding": "identity",
            },
        )
        with client.open(request, timeout=min(timeout, 15)) as response:
            if opener is None and response.geturl() != url:
                raise ProviderError(Failure.CAPABILITY)
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if mime not in {"text/html", "text/plain", "text/markdown"}:
                raise ProviderError(Failure.CAPABILITY)
            encoding = response.headers.get("Content-Encoding", "identity").lower().strip()
            if encoding not in {"", "identity"}:
                raise ProviderError(Failure.CAPABILITY)
            raw = response.read(_BODY_LIMIT + 1)
            if len(raw) > _BODY_LIMIT:
                raise ProviderError(Failure.CAPABILITY)
            text = redact(raw.decode("utf-8", errors="replace"))
        if mime == "text/html":
            parser = _VisibleText()
            parser.feed(text)
            parser.close()
            parser.flush()
            paragraphs = parser.paragraphs
        else:
            paragraphs = [" ".join(p.split()) for p in text.splitlines() if p.strip()]
        # Redact after rendering too: HTML entities can encode otherwise opaque values.
        paragraphs = [redact(p) for p in paragraphs]
        selected = [p for p in paragraphs if _meaningful(p) and _TOPICS.search(p)]
        if not selected:
            combined = redact(" ".join(paragraphs))
            if not _meaningful(combined) or not _TOPICS.search(combined):
                raise ProviderError(Failure.CAPABILITY)
            selected = [combined]
        excerpt = redact("\n".join(selected))
        if _CHALLENGE.search(excerpt[:200]):
            raise ProviderError(Failure.CAPABILITY)
        return excerpt[:_EXCERPT_LIMIT]
    except HTTPError as error:
        status = error.code
        error.close()
        raise ProviderError(Failure.NETWORK, http_status=status) from None
    except (URLError, HTTPException, OSError):
        raise ProviderError(Failure.NETWORK) from None
    except (ValueError, TypeError, AttributeError):
        raise ProviderError(Failure.CAPABILITY) from None
