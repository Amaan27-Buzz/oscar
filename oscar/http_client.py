"""Shared HTTP security rule: credentials never follow redirects to another destination."""

from typing import Any
from urllib.request import HTTPRedirectHandler


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None
