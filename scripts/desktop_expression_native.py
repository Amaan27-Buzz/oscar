"""Actual Tauri/WebView readback from a disposable, harmless arithmetic Core."""

import io
import json
import os
import socket
import subprocess
import tempfile
from pathlib import Path
from threading import Thread

from PIL import Image
from playwright.sync_api import sync_playwright

from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.mobile import MobileServer
from oscar.policy import PersonalPolicy
from scripts.desktop_baseline import capture_owned, windows

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/integration"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="oscar-expression-native-") as temporary:
        path = Path(temporary)
        with Harness(
            path / "core.db", path / "workspace", ROOT / "config/development-models.json"
        ) as h:
            scopes = (
                "heartbeat",
                "desktop:connect",
                "desktop:inspect",
                "desktop:text",
                "math",
                "control:inspect:" + h.node_id,
            )
            h.grid.register(Node("expression-reference", NodeRole.DESKTOP, scopes))
            owner = h.grid.pair("expression-reference", scopes)
            core = Desktop(
                h.runtime, PersonalPolicy(h.store), {h.node_id: (h.dispatcher, h.session)}
            )
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                debug_port = probe.getsockname()[1]
            env = dict(os.environ)
            env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={debug_port}"
            env["WEBVIEW2_USER_DATA_FOLDER"] = str(path / "webview")
            with MobileServer(core) as server:
                process = subprocess.Popen(
                    [
                        str(ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"),
                        "--bootstrap-stdin",
                        "--isolated-preferences",
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    env=env,
                )
                try:
                    assert process.stdout and process.stdin
                    public = json.loads(process.stdout.readline())
                    assert set(public) == {"owner_public_key"}
                    core.register_owner_key(
                        owner, public["owner_public_key"], owner_authorized=True
                    )
                    process.stdin.write(
                        json.dumps(
                            {
                                "url": server.url,
                                "node": owner.node_id,
                                "session": owner.id,
                                "token": owner.token,
                                "reference": True,
                            }
                        )
                        + "\n"
                    )
                    process.stdin.flush()
                    process.stdin.close()
                    with sync_playwright() as p:
                        browser = None
                        for _ in range(100):
                            try:
                                browser = p.chromium.connect_over_cdp(
                                    f"http://127.0.0.1:{debug_port}", timeout=1000
                                )
                                break
                            except Exception:
                                assert process.poll() is None
                                import time

                                time.sleep(0.1)
                        assert browser
                        page = browser.contexts[0].pages[0]
                        errors: list[str] = []
                        page.on("pageerror", lambda error: errors.append(str(error)))

                        def command(request: dict) -> dict:
                            return page.evaluate(
                                "request => window.__TAURI_INTERNALS__.invoke("
                                "'desktop_command', {request})",
                                request,
                            )

                        def capture(name: str, operation: str) -> None:
                            page.get_by_role(
                                "img", name=f"OSCAR: {operation}.", exact=False
                            ).wait_for(timeout=30000)
                            page.wait_for_timeout(800)
                            owned = windows(process.pid)
                            handle = next(handle for handle, _, title in owned if title == "OSCAR")
                            capture_owned(process.pid, handle, OUTPUT / f"native-{name}.png")

                        page.wait_for_function("!!window.__TAURI_INTERNALS__")
                        command({"kind": "refresh"})
                        capture("available", "attentive")
                        pending = command(
                            {"kind": "interact", "mode": "Ask", "text": "2 + 3", "context_id": ""}
                        )
                        task_id = pending["current"]["task_id"]
                        assert h.store.task(task_id).state == "planned"
                        capture("waiting", "waiting")
                        # Owner-authorized deterministic harness execution; no GUI approval claim.
                        result = h.runtime.run(task_id, {h.node_id: (h.dispatcher, h.session)})
                        assert result.state == "verified"
                        fresh = command({"kind": "refresh"})
                        assert fresh["current"]["value"] == "5"
                        capture("verified-readback", "attentive")
                        epoch = fresh["expression"]["epoch"]
                        server.server.shutdown()
                        server.thread.join(timeout=3)
                        capture("unavailable", "unavailable")
                        server.thread = Thread(target=server.server.serve_forever, daemon=True)
                        server.thread.start()
                        restored = command({"kind": "refresh"})
                        assert restored["expression"]["epoch"] != epoch
                        assert restored["voice"] == "idle"
                        capture("reconnected", "attentive")
                        frames = []
                        command(
                            {"kind": "interact", "mode": "Ask", "text": "3 + 4", "context_id": ""}
                        )
                        for _ in range(12):
                            frames.append(Image.open(io.BytesIO(page.screenshot())).convert("RGB"))
                            page.wait_for_timeout(60)
                        frames[0].save(
                            OUTPUT / "native-attention-transition.gif",
                            save_all=True,
                            append_images=frames[1:],
                            duration=80,
                            loop=0,
                        )
                        assert not errors, errors
                        (OUTPUT / "native-receipt.json").write_text(
                            json.dumps(
                                {
                                    "evidence": "REFERENCE_REAL_TAURI_AND_DISPOSABLE_CORE",
                                    "arithmetic": "VERIFIED 2 + 3 = 5 by Core readback",
                                    "execution_authority": (
                                        "Owner-authorized harmless deterministic test harness; "
                                        "native signed control "
                                        "tested separately by desktop_tauri self-check; "
                                        "no owner GUI acceptance"
                                    ),
                                    "native_states": [
                                        "available",
                                        "waiting",
                                        "verified-readback",
                                        "unavailable",
                                        "reconnected",
                                    ],
                                    "epoch_rotation": "PASS",
                                    "voice_after_reconnect": "idle",
                                    "audio": "NOT RUN; no adapter",
                                    "page_errors": errors,
                                    "owner_acceptance": "NOT RUN",
                                },
                                indent=2,
                            )
                            + "\n"
                        )
                        browser.close()
                finally:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
                    process.stdout.close()


if __name__ == "__main__":
    main()
