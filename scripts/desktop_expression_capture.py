"""Six labelled synthetic readbacks through the real Desktop adapter/React renderer."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/integration"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 1420))
    node = shutil.which("node")
    assert node
    server = subprocess.Popen(
        [
            node,
            str(ROOT / "desktop/node_modules/vite/bin/vite.js"),
            "--host",
            "127.0.0.1",
            "--port",
            "1420",
            "--strictPort",
        ],
        cwd=ROOT / "desktop",
        stdout=subprocess.DEVNULL,
    )
    try:
        with sync_playwright() as p:
            edge = Path(os.environ["ProgramFiles(x86)"]) / "Microsoft/Edge/Application/msedge.exe"
            browser = p.chromium.launch(executable_path=str(edge))
            context = browser.new_context(viewport={"width": 420, "height": 170})
            context.route(
                "**/*",
                lambda r: r.continue_()
                if r.request.url.startswith("http://127.0.0.1:1420/")
                else r.abort(),
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            for _ in range(100):
                try:
                    page.goto("http://127.0.0.1:1420/?integration=available")
                    break
                except Exception:
                    assert server.poll() is None
                    time.sleep(0.1)
            entries = []
            for state, operation in [
                ("available", "attentive"),
                ("working", "executing"),
                ("waiting", "waiting"),
                ("speaking", "speaking"),
                ("unavailable", "unavailable"),
                ("interrupted", "attentive"),
            ]:
                page.goto(f"http://127.0.0.1:1420/?integration={state}")
                orb = page.get_by_role("img", name=f"SIMULATED — OSCAR: {operation}.", exact=False)
                orb.wait_for()
                page.wait_for_timeout(850)
                path = OUTPUT / f"fixture-{state}.png"
                page.screenshot(path=str(path))
                entries.append(
                    {
                        "file": path.name,
                        "state": state,
                        "evidence": "SIMULATED_DESKTOP_READBACK_REAL_REACT",
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
            page.goto("http://127.0.0.1:1420/?integration=speaking")
            page.wait_for_timeout(6100)
            assert "speaking" in page.get_by_role("img").get_attribute("aria-label")
            page.wait_for_timeout(2200)
            assert "unknown" in page.get_by_role("img").get_attribute("aria-label")
            page.emulate_media(reduced_motion="reduce")
            page.goto("http://127.0.0.1:1420/?integration=working")
            orb = page.get_by_role("img")
            orb.wait_for()
            page.wait_for_timeout(100)
            pose = orb.locator('[data-puck="true"]').get_attribute("transform")
            page.wait_for_timeout(300)
            assert pose == orb.locator('[data-puck="true"]').get_attribute("transform")
            assert not errors, errors
            browser.close()
            sheet = Image.new("RGB", (840, 510), "white")
            for i, entry in enumerate(entries):
                with Image.open(OUTPUT / entry["file"]) as frame:
                    sheet.paste(frame, ((i % 2) * 420, (i // 2) * 170))
            sheet.save(OUTPUT / "fixture-sheet.png")
            (OUTPUT / "fixture-receipt.json").write_text(
                json.dumps(
                    {
                        "evidence": "SIMULATED / no Core execution or audio",
                        "images": entries,
                        "long_speech_hold": "PASS at 6.1 seconds",
                        "expiry": "PASS at 8.3 seconds",
                        "reduced_motion": "PASS static pose",
                        "page_errors": errors,
                    },
                    indent=2,
                )
                + "\n"
            )
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    main()
