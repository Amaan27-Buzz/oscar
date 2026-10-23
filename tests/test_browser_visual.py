"""Pixel-bound browser fallback through reviewed, signed outbound Grid tasks."""

import base64
import hashlib
import importlib.util
import json
import ssl
import struct
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen

from oscar.browser_worker import validate
from oscar.cloud_http import CloudHTTPServer
from oscar.remote_client import GridClient
from tests import test_connected_acceptance as connected_fixture
from tests import test_remote_machine as machine_fixture
from tests.test_remote_grid import signature


class BrowserVisualContractTests(unittest.TestCase):
    def test_pixel_target_rejects_bad_hash_coordinates_viewport_and_origin(self):
        step = {
            "operation": "visual_click",
            "url": "https://example.com/canvas",
            "sha256": "a" * 64,
            "width": 1280,
            "height": 720,
            "x": 300,
            "y": 80,
        }
        request = {
            "origins": ["https://example.com"],
            "steps": [step],
            "timeout": 30,
            "max_text": 1000,
        }
        validate(request)
        for changes in (
            {"sha256": "invalid"},
            {"sha256": "A" * 64},
            {"x": True},
            {"y": -1},
            {"x": 1280},
            {"y": 720},
            {"width": 10000},
            {"height": 0},
            {"x": float("nan")},
            {"url": "https://other.example/canvas"},
            {"script": "document.cookie"},
        ):
            with self.subTest(changes=changes), self.assertRaises((ValueError, PermissionError)):
                validate({**request, "steps": [{**step, **changes}]})


@unittest.skipUnless(importlib.util.find_spec("playwright"), "optional installed Playwright")
class BrowserVisualAcceptanceTests(unittest.TestCase):
    setUp = machine_fixture.RemoteMachineExecutionTests.setUp
    enroll = machine_fixture.RemoteMachineExecutionTests.enroll
    start_worker = machine_fixture.RemoteMachineExecutionTests.start_worker
    submit = machine_fixture.RemoteMachineExecutionTests.submit
    approve = machine_fixture.RemoteMachineExecutionTests.approve
    finish = machine_fixture.RemoteMachineExecutionTests.finish

    def test_actual_canvas_click_requires_matching_frame_and_never_replays(self):
        connected_fixture.ConnectedAcceptanceTests.certificate(self)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(self.ca, self.root / "tls-key.pem")
        grid_server = CloudHTTPServer(self.core)
        grid_server.socket = tls.wrap_socket(grid_server.socket, server_side=True)
        grid_server.start()
        self.addCleanup(grid_server.close)
        endpoint = f"https://127.0.0.1:{self.core.config.listen_port}"
        self.desktop, self.owner = (
            GridClient(
                endpoint,
                client.session,
                lambda value: base64.b64decode(signature(self.transport_key, value)),
                ssl_context=self.context,
            )
            for client in (self.desktop, self.owner)
        )
        effects = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                if self.path == "/observed":
                    self.wfile.write(json.dumps(effects).encode())
                    return
                self.wfile.write(b"""<!doctype html><body style="margin:0;background:white">
                <canvas id="surface" width="400" height="160"></canvas>
                <output id="receipt">Waiting</output><script>
                const c=document.querySelector('canvas'),g=c.getContext('2d');
                g.fillStyle='#b42727';g.fillRect(0,0,190,160);
                g.fillStyle='#168245';g.fillRect(210,0,190,160);
                c.onclick=async e=>{
                  const box=c.getBoundingClientRect(),x=e.clientX-box.left,y=e.clientY-box.top;
                  if(x>=210 && x<400 && y>=0 && y<160){
                    await fetch('/effect',{method:'POST',body:'accepted'});
                    const out=document.querySelector('output');
                    out.textContent='Accepted';out.dataset.completed='true';
                  }
                };</script>""")

            def do_POST(self):
                effects.append(self.rfile.read(int(self.headers["Content-Length"])).decode())
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        web = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(web.server_close)
        self.addCleanup(web.shutdown)
        Thread(target=web.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{web.server_port}"
        url = origin + "/canvas"
        self.start_worker(("machine.browser",), browser=True)

        def task(steps):
            return self.submit(
                "browser",
                {
                    "request": {
                        "origins": [origin],
                        "timeout": 30,
                        "max_text": 1000,
                        "steps": [
                            {"operation": "navigate", "url": url},
                            {"operation": "wait", "selector": "#surface"},
                            *steps,
                        ],
                    }
                },
            )

        capture = task([{"operation": "screenshot", "path": "observed.png"}])
        self.assertFalse((self.workspace / "observed.png").exists())
        self.approve(capture)
        self.assertEqual("partially_verified", self.finish(capture)["state"])
        image = (self.workspace / "observed.png").read_bytes()
        self.assertTrue(image.startswith(b"\x89PNG"))
        width, height = struct.unpack(">II", image[16:24])
        target = {
            "operation": "visual_click",
            "url": url,
            "sha256": hashlib.sha256(image).hexdigest(),
            "width": width,
            "height": height,
            "x": 300,
            "y": 80,
        }
        for mismatch in ({"sha256": "0" * 64}, {"width": width + 1}, {"url": origin + "/other"}):
            stale = task([{**target, **mismatch}])
            self.approve(stale)
            self.assertEqual("failed", self.finish(stale)["state"])
            self.assertEqual([], effects)
        clicked = task(
            [
                target,
                {"operation": "wait", "selector": "#receipt[data-completed]"},
                {"operation": "inspect"},
            ]
        )
        self.assertEqual([], effects)
        self.approve(clicked)
        self.assertEqual("partially_verified", self.finish(clicked)["state"])
        with urlopen(origin + "/observed", timeout=5) as response:
            self.assertEqual(["accepted"], json.load(response))
        for _ in range(3):
            self.worker.step()
        self.assertEqual(["accepted"], effects)
