"""Outbound Edge polling adapter; compose with existing Grid and policy.

45-byte request: LE boot u32, healthy u8, receipt frame or zeroes, event
frame or zeroes. Replies: 204, or one 20-byte command. TLS is mandatory
except an explicitly selected loopback-only simulator harness.
"""

import ssl
import struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

from .edge import EdgeBridge
from .grid import SessionHandle


def server(
    bridge: EdgeBridge,
    address: tuple[str, int],
    *,
    tls: ssl.SSLContext | None = None,
    simulated: bool = False,
) -> ThreadingHTTPServer:
    if tls is None and (not simulated or address[0] != "127.0.0.1"):
        raise ValueError("Edge listener requires TLS; simulation exception is loopback only")
    lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # Headers contain node secrets; no generic request logging.

        def do_POST(self) -> None:
            self.connection.settimeout(2)
            try:
                if self.path != "/edge/v1/exchange" or self.headers.get("Content-Length") != "45":
                    raise ValueError("invalid request")
                if self.headers.get("Transfer-Encoding") is not None:
                    raise ValueError("chunked request forbidden")
                session_id = self.headers.get("X-OSCAR-Session", "")
                token = self.headers.get("Authorization", "")
                if not token.startswith("Bearer ") or len(token) > 200 or len(session_id) > 64:
                    raise PermissionError("session denied")
                raw = self.rfile.read(45)
                if len(raw) != 45 or raw[4] not in {0, 1}:
                    raise ValueError("invalid body")
                session = SessionHandle(session_id, bridge.node_id, token[7:])
                receipt = raw[5:25] if any(raw[5:25]) else None
                event = raw[25:45] if any(raw[25:45]) else None
                with lock:
                    reply = bridge.exchange(
                        session,
                        struct.unpack("<I", raw[:4])[0],
                        bool(raw[4]),
                        receipt,
                        simulated=simulated,
                    )
                    if event:
                        bridge.event(session, event, simulated=simulated)
                self.send_response(200 if reply else 204)
                self.send_header("Content-Length", str(len(reply) if reply else 0))
                self.end_headers()
                if reply:
                    self.wfile.write(reply)
            except (ValueError, PermissionError, KeyError, OSError):
                self.send_response(403)
                self.send_header("Content-Length", "0")
                self.end_headers()

    listener = ThreadingHTTPServer(address, Handler)
    listener.daemon_threads = True
    if tls:
        listener.socket = tls.wrap_socket(listener.socket, server_side=True)
    return listener
