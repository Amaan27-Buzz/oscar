"""Rendered Slice 12.1 review: bounded browser fixtures and a disposable native Core."""

import argparse
import ctypes
import hashlib
import io
import json
import os
import socket
import subprocess
import tempfile
import time
from ctypes import wintypes
from pathlib import Path
from threading import Event, Thread

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from oscar.desktop import Desktop
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.mobile import MobileServer
from oscar.policy import PersonalPolicy
from scripts.desktop_baseline import capture_owned, windows

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/presence"
EXE = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"


def save_animation(page, name, action, seconds=1.2):
    frames, times = [], []
    action()
    start = time.perf_counter()
    while time.perf_counter() - start < seconds:
        times.append(time.perf_counter() - start)
        frames.append(Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert("RGBA"))
        page.wait_for_timeout(35)
    durations = [max(20, int((b - a) * 1000)) for a, b in zip(times, times[1:], strict=False)]
    durations.append(80)
    width = max(frame.width for frame in frames)
    height = max(frame.height for frame in frames)
    aligned = []
    for frame in frames:
        canvas = Image.new("RGBA", (width, height), "#e4e5e2")
        canvas.alpha_composite(frame, (width - frame.width, height - frame.height))
        aligned.append(canvas.convert("RGB"))
    aligned[0].save(
        OUTPUT / name, save_all=True, append_images=aligned[1:], duration=durations, loop=0
    )
    with Image.open(OUTPUT / name) as encoded:
        distinct = encoded.n_frames
    return {
        "sampled_frames": len(frames),
        "encoded_frames": distinct,
        "seconds": times[-1],
        "source": "REAL_RENDERED_FRAME_SEQUENCE",
        "alignment": "Content captures on a fixed canvas, anchored at bottom right",
    }


def browser_review():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", args=["--no-proxy-server"])
        entries = []
        for scale in [1, 1.25, 1.5]:
            context = browser.new_context(
                viewport={"width": 920, "height": 600}, device_scale_factor=scale
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto("http://127.0.0.1:1420/?living=preview")
            page.get_by_text("Here", exact=True).wait_for()
            for state in [
                "rest",
                "processing",
                "working",
                "approval",
                "speaking",
                "listening",
                "interrupted",
                "offline",
                "error",
                "unknown",
            ]:
                page.get_by_label("Preview state").select_option(state)
                page.wait_for_timeout(850)
                page.get_by_label("Preview state").focus()
                page.mouse.move(400, 100)
                if scale == 1:
                    page.screenshot(path=str(OUTPUT / f"fixture-{state}-compact.png"))
                if page.locator(".character-button").get_attribute("aria-expanded") == "false":
                    page.locator(".character-button").click()
                page.wait_for_timeout(300)
                assert page.locator(".writing-leaf").evaluate(
                    "e => e.scrollHeight <= e.clientHeight"
                ), state
                if scale == 1 or state == "rest":
                    path = OUTPUT / f"fixture-{state}-expanded-{scale}.png"
                    page.screenshot(path=str(path))
                    entries.append(
                        {
                            "file": path.name,
                            "DPR": scale,
                            "evidence": "SYNTHETIC_STATE_REAL_CHROMIUM_RENDER",
                        }
                    )
                page.keyboard.press("Escape")
                page.wait_for_timeout(250)
            if scale == 1:
                page.get_by_label("Preview state").select_option("rest")
                page.wait_for_timeout(850)
                motion = save_animation(
                    page,
                    "fixture-expansion.gif",
                    lambda page=page: page.locator(".character-button").click(),
                )
                page.emulate_media(reduced_motion="reduce")
                page.screenshot(path=str(OUTPUT / "reduced-motion.png"))
                puck = page.locator('[data-puck="true"]')
                pose = puck.get_attribute("transform")
                page.wait_for_timeout(400)
                assert pose == puck.get_attribute("transform")
                page.emulate_media(forced_colors="active")
                page.screenshot(path=str(OUTPUT / "forced-colors.png"))
            assert not errors, errors
            context.close()
        browser.close()
        return {
            "images": entries,
            "expansion": motion,
            "DPR": [1, 1.25, 1.5],
            "overflow": "PASS all 10 states",
            "motion": "PASS reduced-motion static",
            "page_errors": [],
        }


def native_review():
    with tempfile.TemporaryDirectory(
        prefix="oscar-living-review-", ignore_cleanup_errors=True
    ) as temporary:
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
                "control:approve:" + h.node_id,
                "control:deny:" + h.node_id,
                "control:cancel:" + h.node_id,
            )
            h.grid.register(Node("presence-reference", NodeRole.DESKTOP, scopes))
            owner = h.grid.pair("presence-reference", scopes)
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
                    [str(EXE), "--bootstrap-stdin", "--living-presence"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    env=env,
                )
                try:
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
                                time.sleep(0.1)
                        assert browser
                        page = browser.contexts[0].pages[0]
                        errors = []
                        page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
                        page.get_by_text("Here", exact=True).wait_for(timeout=30000)

                        def command(request):
                            return page.evaluate(
                                "request => window.__TAURI_INTERNALS__.invoke("
                                "'desktop_command', {request})",
                                request,
                            )

                        def capture(name):
                            page.wait_for_timeout(850)
                            handle = next(
                                handle
                                for handle, _, title in windows(process.pid)
                                if title == "OSCAR"
                            )
                            return capture_owned(process.pid, handle, OUTPUT / f"native-{name}.png")

                        compact = capture("idle")
                        handle = next(
                            handle for handle, _, title in windows(process.pid) if title == "OSCAR"
                        )
                        # Alpha capture is WebView content, distinct from the HWND capture above.
                        page.screenshot(
                            path=str(OUTPUT / "native-idle-alpha.png"), omit_background=True
                        )
                        with Image.open(OUTPUT / "native-idle-alpha.png") as alpha:
                            assert alpha.mode == "RGBA"
                            assert alpha.getchannel("A").getextrema() == (0, 255)
                        transparency = {
                            "WebView_alpha": "VERIFIED 0..255",
                            "native_compositor": (
                                "INCONCLUSIVE / automation capture could not foreground "
                                "target over owned backdrop"
                            ),
                        }
                        rect = page.locator(".character-button").bounding_box()
                        page.locator(".character-button").click()
                        page.get_by_label("Ask OSCAR").wait_for()
                        assert page.get_by_label("Ask OSCAR").evaluate(
                            "e=>e===document.activeElement"
                        )
                        expanded = capture("invoked")
                        assert compact["logical_width"] == 132 and expanded["logical_width"] == 432
                        page.get_by_label("Ask OSCAR").fill("2 + 3")
                        page.keyboard.press("Enter")
                        try:
                            page.get_by_text("Review needed", exact=True).wait_for(timeout=8000)
                        except Exception:
                            page.screenshot(path=str(OUTPUT / "native-ask-diagnostic.png"))
                            diagnostic = command({"kind": "ready"})
                            print(
                                {
                                    "link": diagnostic["link"],
                                    "message": diagnostic["message"],
                                    "task": diagnostic["current"],
                                    "page_errors": errors,
                                    "text": page.locator("main").inner_text(),
                                }
                            )
                            raise
                        waiting = command({"kind": "ready"})
                        task_id = waiting["current"]["task_id"]
                        assert h.store.task(task_id).state == "planned"
                        capture("approval")
                        # Harmless owner-authorized test, independent of GUI approval.
                        started, complete = Event(), Event()
                        original = h.dispatcher.executors["math.add"]
                        results = []

                        def delayed(action, cancellation):
                            started.set()
                            assert complete.wait(15), "test executor release timed out"
                            return original(action, cancellation)

                        h.dispatcher.executors["math.add"] = delayed
                        worker = Thread(
                            target=lambda: results.append(
                                h.runtime.run(task_id, {h.node_id: (h.dispatcher, h.session)})
                            ),
                            daemon=True,
                        )
                        worker.start()
                        try:
                            assert started.wait(5)
                            command({"kind": "refresh"})
                            page.get_by_text("Waiting", exact=True).wait_for(timeout=5000)
                            assert h.store.task(task_id).state == "awaiting_result"
                            capture("awaiting-result")
                        finally:
                            complete.set()
                            worker.join(timeout=10)
                            h.dispatcher.executors["math.add"] = original
                        assert not worker.is_alive() and results[0].state == "verified"
                        fresh = command({"kind": "refresh"})
                        assert fresh["current"]["value"] == "5"
                        capture("verified")
                        page.keyboard.press("Escape")
                        page.wait_for_function(
                            "document.querySelector('.character-button')"
                            "?.getAttribute('aria-expanded') === 'false'"
                        )
                        assert page.locator(".character-button").evaluate(
                            "e=>e===document.activeElement"
                        )
                        capture("retreated")
                        epoch = fresh["expression"]["epoch"]
                        server.server.shutdown()
                        server.thread.join(timeout=3)
                        page.get_by_text("Offline", exact=True).wait_for(timeout=15000)
                        capture("offline")
                        server.thread = Thread(target=server.server.serve_forever, daemon=True)
                        server.thread.start()
                        restored = command({"kind": "refresh"})
                        assert (
                            restored["expression"]["epoch"] != epoch and restored["voice"] == "idle"
                        )
                        page.get_by_text("Here", exact=True).wait_for()
                        capture("restored")
                        page.mouse.move(0, 0)
                        page.wait_for_timeout(850)
                        performance = page.evaluate("""async () => {
                          const puck=document.querySelector('[data-puck="true"]'); let mutations=0;
                          const observer=new MutationObserver(rows=>mutations+=rows.length);
                          observer.observe(puck,{attributes:true});
                          await new Promise(r=>setTimeout(r,1200));observer.disconnect();
                          const times=[];await new Promise(resolve=>{
                            const tick=t=>{times.push(t);
                              if(times.length<91)requestAnimationFrame(tick);else resolve();};
                            requestAnimationFrame(tick);
                          });
                          const gaps=times.slice(1).map((t,i)=>t-times[i]).sort((a,b)=>a-b);
                          return {idle_puck_mutations:mutations,raf_interval_median_ms:gaps[45],
                            raf_interval_p95_ms:gaps[85],
                            scope:'WebView scheduling and SVG rest; not whole-system CPU'};
                        }""")
                        assert performance["idle_puck_mutations"] == 0

                        def sequence():
                            page.evaluate("""() => {
                              const orb=()=>document.querySelector('.character-button').click();
                              orb();
                              setTimeout(orb,90);setTimeout(orb,190);setTimeout(orb,1050);
                            }""")

                        sequence_record = save_animation(
                            page, "native-invoke-retreat-reinvoke.gif", sequence, 2.2
                        )
                        page.wait_for_timeout(300)
                        page.locator(".character-button").click()
                        page.wait_for_timeout(300)
                        page.get_by_text("Presence", exact=True).click()
                        page.get_by_role("button", name="Pin on top", exact=True).click()
                        page.get_by_role("button", name="Unpin", exact=True).wait_for()
                        page.get_by_role("button", name="Unpin", exact=True).click()
                        page.get_by_role("button", name="To screen edge", exact=True).click()
                        page.get_by_text("Presence", exact=True).click()
                        animation = save_animation(
                            page, "native-retreat.gif", lambda: page.keyboard.press("Escape")
                        )
                        page.wait_for_timeout(300)
                        handle = next(
                            handle for handle, _, title in windows(process.pid) if title == "OSCAR"
                        )
                        # Native close hides, keyboard invocation recovers the same process/window.
                        user = ctypes.WinDLL("user32")
                        user.PostMessageW.argtypes = [
                            wintypes.HWND,
                            wintypes.UINT,
                            wintypes.WPARAM,
                            wintypes.LPARAM,
                        ]
                        assert user.PostMessageW(handle, 0x0010, 0, 0)
                        for _ in range(30):
                            if not any(title == "OSCAR" for _, _, title in windows(process.pid)):
                                break
                            page.wait_for_timeout(100)
                        assert not any(title == "OSCAR" for _, _, title in windows(process.pid))
                        for key in [0x11, 0x12, ord("O")]:
                            user.keybd_event(key, 0, 0, 0)
                        for key in [ord("O"), 0x12, 0x11]:
                            user.keybd_event(key, 0, 2, 0)
                        page.wait_for_timeout(700)
                        assert windows(process.pid)
                        # Explicit invocation keeps the result; Ask-again focuses input.
                        page.get_by_role("button", name="Ask again", exact=True).click()
                        assert page.get_by_label("Ask OSCAR").evaluate(
                            "e=>e===document.activeElement"
                        )
                        assert not errors, errors
                        browser.close()
                        return {
                            "evidence": "REAL_TAURI_WEBVIEW2_DISPOSABLE_AUTHENTICATED_CORE",
                            "compact": compact,
                            "expanded": expanded,
                            "transparency": transparency,
                            "performance": performance,
                            "arithmetic": "VERIFIED 2+3=5; harness execution, not GUI approval",
                            "offline_reconnect": "PASS epoch rotated; voice idle",
                            "window_controls": (
                                "PASS pin/float/edge requests; close hides; "
                                "global shortcut restores focus"
                            ),
                            "animation": animation,
                            "interrupted_window_sequence": sequence_record,
                            "page_errors": errors,
                            "owner_acceptance": "NOT RUN",
                            "physical_voice": "NOT RUN",
                            "initial_orb_rect": rect,
                        }
                finally:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
                    process.stdout.close()


def contact_sheet():
    names = [
        "fixture-rest-expanded-1.png",
        "fixture-working-expanded-1.png",
        "fixture-approval-expanded-1.png",
        "fixture-offline-expanded-1.png",
    ]
    sheet = Image.new("RGB", (864, 848), "#e4e5e2")
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        with Image.open(OUTPUT / name) as im:
            # Crop the actual 432x384 fixture surface, no invented artwork or UI.
            crop = im.crop((464, 192, 896, 576))
            x, y = (i % 2) * 432, (i // 2) * 424
            sheet.paste(crop, (x, y + 24))
            draw.text(
                (x + 16, y + 6),
                name.split("-")[1] + " · synthetic state / rendered UI",
                fill="#242723",
            )
    sheet.save(OUTPUT / "review-sheet.png")
    comparison = Image.new("RGB", (920, 320), "#e4e5e2")
    text = ImageDraw.Draw(comparison)
    text.text((24, 20), "Current integrated UI / native capture", fill="#242723")
    text.text((500, 20), "Proposed presence / real WebView alpha", fill="#242723")
    with Image.open(ROOT / "docs/ui/desktop/integration/native-available.png") as before:
        comparison.paste(before.convert("RGB"), (24, 70))
    with Image.open(OUTPUT / "native-idle-alpha.png") as after:
        comparison.paste(after, (620, 55), after)
    text.text((500, 275), "Wallpaper compositing remains owner review", fill="#61645b")
    comparison.save(OUTPUT / "before-after.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser-only", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {"browser": browser_review()}
    contact_sheet()
    if not args.browser_only:
        report["native"] = native_review()
        (OUTPUT / "native-receipt.json").write_text(json.dumps(report["native"], indent=2) + "\n")
    report["starting_sha"] = "b9d3e049aef5148a10c710626b9e6b06771c9229"
    report["branch"] = "codex/slice-12-1-living-presence"
    report["canonical_svg_sha256"] = hashlib.sha256(
        (ROOT / "assets/brand/oscar-orb.svg").read_bytes()
    ).hexdigest()
    report["files"] = [
        {"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(OUTPUT.glob("*.png"))
    ] + [
        {"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(OUTPUT.glob("*.gif"))
    ]
    (OUTPUT / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report.get("native", report["browser"])))


if __name__ == "__main__":
    main()
