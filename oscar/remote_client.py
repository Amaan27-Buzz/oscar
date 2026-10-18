"""Bounded outbound Grid client; credentials never enter URLs or diagnostic messages."""

import base64
import hashlib
import json
import secrets
import ssl
from collections.abc import Callable
from http.client import HTTPException
from time import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, Request, build_opener

from .contracts import new_id
from .http_client import NoRedirects
from .storage import StateConflict


def request_proof(node: str, session: str, nonce: str, instant: str, body: bytes) -> bytes:
    return "\n".join(
        (
            "OSCAR-GRID-2",
            "POST",
            "/v2/grid/request",
            node,
            session,
            nonce,
            instant,
            hashlib.sha256(body).hexdigest(),
        )
    ).encode()


class GridClient:
    def __init__(
        self,
        endpoint: str,
        session: dict[str, Any],
        signer: Callable[[bytes], bytes],
        ssl_context: ssl.SSLContext | None = None,
    ):
        url = urlsplit(endpoint)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.path
            or url.query
            or url.fragment
            or endpoint.endswith("/")
        ):
            raise ValueError("trusted HTTPS Core origin required")
        self.endpoint, self.session, self.signer = endpoint, dict(session), signer
        self.opener = build_opener(NoRedirects(), HTTPSHandler(context=ssl_context))

    def _post(self, path: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        if len(body) > 32768:
            raise ValueError("Grid request exceeds bound")
        request = Request(
            self.endpoint + path,
            body,
            headers={
                "Content-Type": "application/json",
                **headers,
            },
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=8) as response:
                raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError("Grid response exceeds bound")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError("Grid object response required")
                return dict(result)
        except HTTPError as error:
            error.close()
            if error.code == 401:
                raise PermissionError("Grid credential revoked, expired or proof denied") from None
            if error.code == 403:
                raise StateConflict("Grid action denied; inspect current authority") from None
            raise OSError(f"Grid request rejected ({error.code}); inspect before retry") from None
        except (URLError, HTTPException, TimeoutError):
            raise OSError("Grid unavailable; outcome UNKNOWN; inspect before retry") from None

    def enroll(
        self,
        invitation: dict[str, Any],
        signer: Callable[[bytes], bytes] | None = None,
    ) -> dict[str, Any]:
        sign = signer or self.signer
        body = json.dumps(
            {
                "version": 2,
                "challenge_id": invitation["challenge_id"],
                "signature": base64.b64encode(
                    sign(
                        base64.b64decode(
                            invitation["signing_payload"],
                            validate=True,
                        )
                    )
                ).decode(),
            },
            separators=(",", ":"),
        ).encode()
        session = self._post("/v2/grid/enroll", body, {})
        if (
            session.get("core_id") != invitation["core_id"]
            or (session.get("node_id") != invitation["node_id"])
            or session.get("version") != 2
        ):
            raise PermissionError("Grid enrollment identity mismatch")
        self.session = session
        return dict(session)

    def request(
        self,
        operation: str,
        payload: dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(
            {
                "version": 2,
                "operation": operation,
                "request_id": request_id or new_id(),
                "payload": payload,
            },
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        nonce, instant = secrets.token_hex(16), str(int(time() * 1000))
        node, session = self.session["node_id"], self.session["session_id"]
        signature = base64.b64encode(
            self.signer(
                request_proof(
                    node,
                    session,
                    nonce,
                    instant,
                    body,
                )
            )
        ).decode()
        return self._post(
            "/v2/grid/request",
            body,
            {
                "Authorization": "Bearer " + self.session["token"],
                "X-Oscar-Node": node,
                "X-Oscar-Session": session,
                "X-Oscar-Nonce": nonce,
                "X-Oscar-Time": instant,
                "X-Oscar-Signature": signature,
            },
        )
