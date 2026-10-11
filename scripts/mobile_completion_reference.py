"""Disposable Group 2 Core/Grid HTTP fixture. Synthetic keys never mean owner consent."""

import argparse
import base64
import json
import secrets
import tempfile
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from time import monotonic
from urllib.request import Request, urlopen

from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.mobile import Mobile, MobileServer
from oscar.policy import PersonalPolicy


def run(*, serve: bool = False) -> dict:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    with (
        tempfile.TemporaryDirectory(prefix="group02-reference-") as directory,
        ExitStack() as stack,
    ):
        root = Path(directory)
        h = stack.enter_context(
            Harness(root / "core.db", root / "workspace", Path("config/development-models.json"))
        )
        target = h.node_id
        common = (
            "heartbeat",
            "math",
            "control:inspect:" + target,
            "control:approve:" + target,
            "control:cancel:" + target,
        )
        mobile_scopes = (*common, "mobile:connect", "mobile:inspect", "mobile:text")
        desktop_scopes = (*common, "desktop:connect", "desktop:inspect", "desktop:text")
        h.grid.register(Node("reference-mobile-software", NodeRole.MOBILE, mobile_scopes))
        h.grid.register(Node("group02-reference-desktop", NodeRole.DESKTOP, desktop_scopes))
        owner = h.grid.pair("reference-mobile-software", mobile_scopes)
        desk = h.grid.pair("group02-reference-desktop", desktop_scopes)
        targets = {target: (h.dispatcher, h.session)}
        mobile = Mobile(h.runtime, PersonalPolicy(h.store), targets)
        desktop = Desktop(h.runtime, PersonalPolicy(h.store), targets)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = base64.b64encode(
            key.public_key().public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).decode()
        mobile.register_owner_key(owner, public, owner_authorized=True)
        desktop.register_owner_key(desk, public, owner_authorized=True)
        mobile_server = stack.enter_context(MobileServer(mobile))
        desktop_server = stack.enter_context(MobileServer(desktop))

        def post(server, session, operation, payload):
            body = {
                "version": 1,
                "request_id": secrets.token_hex(16),
                "operation": operation,
                "payload": payload,
            }
            headers = {
                "Authorization": "Bearer " + session.token,
                "X-Oscar-Node": session.node_id,
                "X-Oscar-Session": session.id,
            }
            request = Request(
                server.url + ("/v1/desktop" if server is desktop_server else "/v1/mobile"),
                data=json.dumps(body).encode(),
                headers=headers,
            )
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read())

        def signed(server, session, task_id, operation):
            challenge = post(
                server, session, "challenge", {"operation": operation, "task_id": task_id}
            )
            signature = key.sign(
                base64.b64decode(challenge["signing_payload"]),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
            return post(
                server,
                session,
                "complete",
                {
                    "challenge_id": challenge["challenge_id"],
                    "signature": base64.b64encode(signature).decode(),
                },
            )

        math = post(mobile_server, owner, "text", {"text": "2 + 3"})
        result = signed(mobile_server, owner, math["task_id"], "approve")
        assert result["state"] == "verified" and result["value"] == "5" and result["evidence_ids"]
        desk_task = post(
            desktop_server, desk, "interact", {"mode": "Ask", "text": "8 + 9", "context_id": ""}
        )
        shared = post(mobile_server, owner, "inspect", {"task_id": desk_task["task_id"]})
        assert (
            shared["state"] == "planned"
            and "approve" not in shared["actions"]
            and "8 + 9" not in json.dumps(shared)
        )
        denied = post(mobile_server, owner, "text", {"text": "10 + 11"})
        outcome = signed(mobile_server, owner, denied["task_id"], "deny")
        assert outcome["state"] == "cancelled"
        assert not any(row["task_id"] == denied["task_id"] for row in h.store.all("action"))
        report = {
            "classification": "REFERENCE_VERIFIED",
            "http_core_math_readback": True,
            "desktop_origin_shared_task": True,
            "signed_reference_denial_without_execution": True,
            "owner_biometric_pin": "NOT_RUN",
            "physical_devices": "NOT_RUN",
        }
        if not serve:
            return report

        control_token = secrets.token_urlsafe(32)

        class Control(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    self.connection.settimeout(5)
                    length = int(self.headers.get("Content-Length", "0"))
                    if (
                        self.headers.get("X-Reference-Token") != control_token
                        or not 0 < length <= 1024
                    ):
                        raise PermissionError("reference fixture admission denied")
                    command = json.loads(self.rfile.read(length))
                    if set(command) != {"operation", "task_id"} or command["operation"] != "deny":
                        raise ValueError("fixture supports signed denial only")
                    if not mobile.private_for(owner, command["task_id"]):
                        raise PermissionError("task is not this disposable session's request")
                    data = json.dumps(
                        signed(mobile_server, owner, command["task_id"], "deny")
                    ).encode()
                    self.send_response(200)
                except (PermissionError, ValueError, KeyError):
                    data = b'{"error":"reference_denial_unavailable"}'
                    self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        control = ThreadingHTTPServer(("127.0.0.1", 0), Control)
        control_thread = Thread(target=control.serve_forever, daemon=True)
        control_thread.start()
        output = Path(".oscar/mobile")
        output.mkdir(parents=True, exist_ok=True)
        fixture = {
            "url": mobile_server.url,
            "node_id": owner.node_id,
            "session_id": owner.id,
            "token": owner.token,
            "control_url": f"http://127.0.0.1:{control.server_port}",
            "control_token": control_token,
            "desktop_task_id": desk_task["task_id"],
        }
        (output / "group02-session.json").write_text(json.dumps(fixture), encoding="utf-8")
        (output / "group02-reference.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print("REFERENCE_ONLY_CORE_GRID_HTTP_READY", flush=True)
        try:
            deadline = monotonic() + 1800
            while monotonic() < deadline:
                h.grid.heartbeat(h.session)
                h.grid.heartbeat(desk)
                Event().wait(5)
        finally:
            control.shutdown()
            control.server_close()
            control_thread.join(timeout=3)
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(serve=args.serve), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
