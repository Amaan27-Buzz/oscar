"""Bounded D1 commissioning transport. Grid owns credentials; D2 owns remote execution."""

import json
import math
import re
import sqlite3
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import BoundedSemaphore, Lock, Thread
from time import monotonic, time
from typing import TYPE_CHECKING, Any

from .grid import SessionHandle
from .storage import StateConflict

if TYPE_CHECKING:
    from socket import socket

    from .cloud import CloudCore


class CloudHTTPServer(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True
    request_queue_size = 8

    def __init__(self, core: "CloudCore"):
        self.core = core
        self.slots = BoundedSemaphore(8)
        self.rate_lock = Lock()
        self.arrivals: deque[float] = deque()
        super().__init__((core.config.listen_host, core.config.listen_port), CloudHandler)
        self.thread = Thread(target=self.serve_forever, name="oscar-cloud-http", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def allowed(self) -> bool:
        with self.rate_lock:
            now = monotonic()
            while self.arrivals and self.arrivals[0] <= now - 60:
                self.arrivals.popleft()
            if len(self.arrivals) >= 120:
                return False
            self.arrivals.append(now)
            return True

    def get_request(self) -> tuple["socket", Any]:
        connection, address = super().get_request()
        connection.settimeout(3)
        return connection, address

    def process_request(self, request: Any, client_address: Any) -> None:
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.core.harness.archive.close_thread()
            self.slots.release()

    def handle_error(self, request: Any, client_address: Any) -> None:
        # Default traceback logging can include private exception/request material.
        from .cloud import diagnostic

        diagnostic("http_request_failed", category="internal_error")

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        self.thread.join(timeout=5)


class CloudHandler(BaseHTTPRequestHandler):
    server: CloudHTTPServer
    server_version = "OSCAR"
    sys_version = ""
    protocol_version = "HTTP/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self.reply(code, {"error": "request_rejected"})

    def reply(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, allow_nan=False, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_GET(self) -> None:
        self.dispatch()

    def do_POST(self) -> None:
        self.dispatch()

    def authenticate(self, scope: str) -> SessionHandle:
        from .cloud import strict_object

        required = (
            "Authorization",
            "X-Oscar-Node",
            "X-Oscar-Session",
            "X-Oscar-Nonce",
            "X-Oscar-Time",
            "Host",
        )
        if any(len(self.headers.get_all(k, [])) != 1 for k in required):
            raise PermissionError("explicit authentication headers required")
        auth = self.headers["Authorization"]
        node, identifier = self.headers["X-Oscar-Node"], self.headers["X-Oscar-Session"]
        nonce, sent = self.headers["X-Oscar-Nonce"], self.headers["X-Oscar-Time"]
        if (
            not re.fullmatch(r"Bearer [A-Za-z0-9_-]{32,128}", auth)
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,63}", node)
            or not re.fullmatch(r"[a-f0-9]{32}", identifier)
            or not re.fullmatch(r"[a-f0-9]{32}", nonce)
            or not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,9})?", sent)
        ):
            raise PermissionError("invalid credentials")
        instant = float(sent)
        if not math.isfinite(instant) or abs(time() - instant) > 60:
            raise PermissionError("expired request")
        session = SessionHandle(identifier, node, auth.removeprefix("Bearer "))
        h = self.server.core.harness
        with h.store.transaction():
            h.grid.authenticate(session, scope)
            # Deployment scopes are not remote owner/device enrollment or delegation.
            binding = h.store.get("cloud_client", node)
            if binding != {"core_id": self.server.core.config.core_id}:
                raise PermissionError("deployment client binding denied")
            h.store.consume_nonce(identifier, nonce)
        # Keep parsing helper import out of initialization to avoid a composition cycle.
        self.parse_json = strict_object
        return session

    def dispatch(self) -> None:
        core, config = self.server.core, self.server.core.config
        try:
            if len(self.path) > 256 or "?" in self.path or "#" in self.path:
                raise ValueError("unsupported target")
            if len(self.headers.get_all("Host", [])) != 1:
                raise ValueError("one Host header required")
            host = self.headers["Host"]
            if not re.fullmatch(r"[a-z0-9.-]+(?::[0-9]{1,5})?", host) or (
                host.split(":")[0] not in config.allowed_hosts
            ):
                raise ValueError("host denied")
            if any(
                len(self.headers.get_all(k, [])) > 1
                for k in (
                    "Content-Length",
                    "Content-Type",
                    "Transfer-Encoding",
                    "X-Forwarded-Proto",
                )
            ):
                raise ValueError("duplicate framing")
            if "Transfer-Encoding" in self.headers:
                raise ValueError("transfer encoding unsupported")
            if self.path in {"/healthz", "/readyz"}:
                if self.client_address[0] != "127.0.0.1" or self.command != "GET":
                    self.reply(404, {"error": "not_found"})
                    return
                healthy = self.path == "/healthz" or core.ready()
                self.reply(200 if healthy else 503, {"status": "ok" if healthy else "unavailable"})
                return
            if not self.server.allowed():
                self.reply(429, {"error": "rate_limited"})
                return
            if config.ingress == "tls-proxy" and self.headers.get("X-Forwarded-Proto") != "https":
                raise PermissionError("TLS ingress required")
            # Match exact endpoint/method pairs; reference APIs never share this listener.
            probe = re.fullmatch(r"/v1/probes/([a-f0-9]{32})", self.path)
            if self.command == "GET" and self.path == "/v1/status":
                self.authenticate("cloud:inspect")
                self.reply(200, core.status())
            elif self.command == "GET" and probe:
                session = self.authenticate("cloud:inspect")
                self.reply(200, core.inspect_probe(session, probe[1]))
            elif self.command == "POST" and self.path == "/v1/probes":
                session = self.authenticate("cloud:probe")
                length = self.headers.get("Content-Length", "")
                if not re.fullmatch(r"[0-9]{1,5}", length) or not 1 <= int(length) <= 4096:
                    self.reply(413, {"error": "body_limit"})
                    return
                if self.headers.get("Content-Type") != "application/json":
                    raise ValueError("JSON content type required")
                body = self.rfile.read(int(length))
                if len(body) != int(length):
                    raise ValueError("incomplete body")
                data = json.loads(body, object_pairs_hook=self.parse_json)
                if not isinstance(data, dict):
                    raise ValueError("JSON object required")
                self.reply(200, core.probe(session, data))
            else:
                self.reply(404, {"error": "not_found"})
        except (PermissionError, KeyError):
            self.reply(401, {"error": "authentication_or_scope_denied"})
        except StateConflict:
            self.reply(409, {"error": "conflict_inspect_before_retry"})
        except (ValueError, TypeError, UnicodeError, RecursionError):
            self.reply(400, {"error": "invalid_request"})
        except (OSError, sqlite3.Error):
            self.reply(503, {"error": "temporarily_unavailable"})
