"""Capture the built, isolated lab in a fresh browser and self-owned preview server.

Screenshots are actual browser output. Sheets/GIFs arrange those captures; they
do not invent art. No attachment to an existing server or user browser session.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.parse import urlparse

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:1511"


def seek(page, milliseconds):
    pause = page.get_by_role("button", name="Pause", exact=True)
    if pause.count():
        pause.click()
    slider = page.get_by_label("Scrub transition")
    slider.evaluate("""(el, value) => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, value);
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", str(milliseconds))
    page.wait_for_function("([value]) => document.querySelector('[aria-label=\"Scrub transition\"]').value === value", arg=[str(milliseconds)])
    page.get_by_role("button", name="Play", exact=True).wait_for()


def sheet(paths, destination, columns=4, labels=None):
    images = [Image.open(p).convert("RGB") for p in paths]
    width, height = max(i.width for i in images), max(i.height for i in images)
    canvas = Image.new("RGB", (columns * width, ((len(images) + columns - 1) // columns) * (height + 30)), "#f7f7f3")
    draw = ImageDraw.Draw(canvas)
    for index, image in enumerate(images):
        x, y = index % columns * width, index // columns * (height + 30)
        canvas.paste(image, (x, y))
        draw.text((x + 12, y + height + 6), (labels or [p.stem for p in paths])[index], fill="#222923")
    canvas.save(destination)


def preview_frame(path):
    with Image.open(path) as source:
        frame=source.convert('RGB')
        return frame.resize((600,round(frame.height*600/frame.width)))


def capture(iteration, node):
    output = ROOT / "docs/design/expression/evidence" / iteration
    output.mkdir(parents=True, exist_ok=True)
    if not (LAB / "dist/index.html").exists():
        raise RuntimeError("Build first: npm run build")
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 1511)) == 0:
            raise RuntimeError("Port 1511 is occupied. Refusing to attach to another server.")
    receipt = {"iteration": iteration, "classification": "SIMULATED VISUAL STATE — NO CORE EXECUTION",
               "capture": "fresh Chromium / own built Vite preview / deterministic timeline samples",
               "canonical_sha256": hashlib.sha256((ROOT / "assets/brand/oscar-orb.svg").read_bytes()).hexdigest(),
               "built_sha256": {str(p.relative_to(LAB / 'dist')): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((LAB / "dist").rglob("*")) if p.is_file()},
               "checks": [], "external_requests": [], "errors": []}
    with tempfile.TemporaryDirectory(prefix="oscar-expression-") as temporary:
        log_path = Path(temporary) / "preview.log"
        with log_path.open("w") as log:
            server = subprocess.Popen([node, "node_modules/vite/bin/vite.js", "preview", "--host", "127.0.0.1", "--port", "1511", "--strictPort"], cwd=LAB, stdout=log, stderr=log,
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                for _ in range(100):
                    with socket.socket() as probe:
                        if probe.connect_ex(("127.0.0.1", 1511)) == 0:
                            break
                    if server.poll() is not None:
                        raise RuntimeError(log_path.read_text())
                    time.sleep(.1)
                else:
                    raise RuntimeError("Preview did not start")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(channel="msedge", headless=True)
                    receipt["browser"] = browser.version
                    context = browser.new_context(viewport={"width": 1440, "height": 1050}, device_scale_factor=1,
                                                  permissions=[], reduced_motion="no-preference")
                    def isolate(route):
                        parsed = urlparse(route.request.url)
                        if f"{parsed.scheme}://{parsed.netloc}" == ORIGIN:
                            route.continue_()
                        else:
                            receipt["external_requests"].append(route.request.url)
                            route.abort()
                    context.route("**/*", isolate)
                    page = context.new_page()
                    page.on("pageerror", lambda error: receipt["errors"].append(str(error)))
                    page.on("console", lambda message: receipt["errors"].append(message.text) if message.type == "error" else None)
                    response = page.goto(ORIGIN, wait_until="networkidle")
                    assert "microphone=()" in response.headers.get("permissions-policy", "")
                    page.get_by_test_id("stage").wait_for()
                    page.screenshot(path=output / "desktop.png", full_page=True)
                    page.get_by_role("button", name="Geometry & restraint", exact=True).click()
                    original = Path(temporary) / "canonical.png"
                    derived = Path(temporary) / "neutral-derivative.png"
                    # Place both at the same integer pixel origin; side-by-side layout can add raster phase differences.
                    page.evaluate("""()=>{
                      const mount=document.createElement('div');mount.id='pixel-comparison';
                      Object.assign(mount.style,{position:'fixed',left:'0',top:'0',width:'220px',height:'220px',background:'#f7f7f3',zIndex:'100'});
                      mount.append(document.querySelector('.identity-pair img').cloneNode(true));document.body.append(mount);
                    }""")
                    page.locator('#pixel-comparison').screenshot(path=original)
                    page.evaluate("""()=>{const mount=document.querySelector('#pixel-comparison');mount.replaceChildren(document.querySelector('.identity-pair svg').cloneNode(true));}""")
                    page.locator('#pixel-comparison').screenshot(path=derived)
                    page.evaluate("document.querySelector('#pixel-comparison').remove()")
                    difference = ImageChops.difference(Image.open(original).convert('RGB'), Image.open(derived).convert('RGB'))
                    receipt["neutral_pixel_difference_bbox"] = difference.getbbox()
                    if iteration in {'candidate-v2','motion-v3'}:
                        if difference.getbbox() is not None:
                            shutil.copyfile(original,output/'canonical-diagnostic.png')
                            shutil.copyfile(derived,output/'neutral-diagnostic.png')
                            difference.save(output/'neutral-difference.png')
                            print('Neutral difference:',difference.getbbox())
                        assert difference.getbbox() is None, "Neutral derivative must match canonical rendered pixels"
                        for name in ['canonical-diagnostic.png','neutral-diagnostic.png','neutral-difference.png']:
                            diagnostic=output/name
                            if diagnostic.exists():
                                diagnostic.unlink()
                    receipt["checks"].append("neutral source/derivative pixel comparison recorded")
                    page.get_by_role("button", name="Expression atlas", exact=True).click()
                    page.mouse.move(1400, 40)
                    page.get_by_test_id("atlas").screenshot(path=output / "expression-contact-sheet.png")
                    assert page.get_by_test_id("atlas").get_by_role("button").count() == 16
                    receipt["checks"].append("all 16 expressions rendered")
                    page.get_by_role("button", name="Live study", exact=True).click()
                    page.get_by_label("Expressive delivery").select_option("curious")
                    seek(page, 1800)
                    page.get_by_test_id("stage").screenshot(path=output / "curious.png")
                    scale_paths = []
                    for delivery, operation in [("curious", "available"), ("focused", "verifying"), ("subdued", "unavailable")]:
                        page.get_by_label("Operational state").select_option(operation)
                        page.get_by_label("Expressive delivery").select_option(delivery)
                        seek(page, 1800)
                        path = output / f"scale-{operation}.png"
                        page.get_by_test_id("scale").screenshot(path=path)
                        scale_paths.append(path)
                    sheet(scale_paths, output / "small-scale-comparison.png", 1)
                    page.get_by_label("Operational state").select_option("available")
                    page.get_by_label("Transition sequence").select_option("4")
                    page.get_by_role("button", name="Run sequence", exact=True).click()
                    # Real-time playback and pause are exercised separately from seek captures.
                    page.wait_for_timeout(350)
                    assert int(page.get_by_label("Scrub transition").input_value()) > 0
                    page.get_by_role("button", name="Pause", exact=True).click()
                    before = int(page.get_by_label("Scrub transition").input_value())
                    page.wait_for_timeout(100)
                    assert int(page.get_by_label("Scrub transition").input_value()) == before
                    receipt["checks"].append("real-time playback advances and pause holds")
                    frames = []
                    for index, milliseconds in enumerate(range(0, 4451, 100)):
                        seek(page, milliseconds)
                        path = Path(temporary) / f"frame-{index:03}.png"
                        page.get_by_test_id("stage").screenshot(path=path)
                        frames.append(path)
                    gif_frames = [preview_frame(p) for p in frames]
                    gif_frames[0].save(output / "curiosity-recovery.gif", save_all=True, append_images=gif_frames[1:], duration=100, loop=0)
                    page.get_by_label("Transition sequence").select_option("3")
                    page.get_by_role("button", name="Run sequence", exact=True).click()
                    transition_paths = []
                    times = [0, 1400, 1600, 1680, 1850, 2050, 2250, 2950]
                    for index, milliseconds in enumerate(times):
                        seek(page, milliseconds)
                        path = Path(temporary) / f"interrupt-{index:03}.png"
                        page.get_by_test_id("stage").screenshot(path=path)
                        transition_paths.append(path)
                    sheet(transition_paths, output / "interruption-sequence.png", 4, [f"{t} ms" for t in times])
                    if iteration in {'candidate-v2','motion-v3'}:
                        # New owner-authorized eye opening and freer finite puck travel.
                        page.get_by_label('Operational state').select_option('speaking')
                        page.get_by_label('Expressive delivery').select_option('composed')
                        speech_frames=[]
                        speech_end=5200 if iteration=='motion-v3' else 1800
                        for index, milliseconds in enumerate(range(0,speech_end+1,100)):
                            seek(page, milliseconds)
                            path=Path(temporary) / f'speech-{index:03}.png'
                            page.get_by_test_id('stage').screenshot(path=path)
                            speech_frames.append(path)
                        images=[preview_frame(p) for p in speech_frames]
                        images[0].save(output / 'speaking-puck.gif',save_all=True,append_images=images[1:],duration=100,loop=0)
                        indices=[0,6,12,17,23,34,45,52] if iteration=='motion-v3' else [0,3,6,9,12,18]
                        sheet([speech_frames[i] for i in indices],output / 'speaking-frames.png',4 if iteration=='motion-v3' else 3,[f'{i*100} ms' for i in indices])
                        page.get_by_label('Operational state').select_option('available')
                        page.get_by_label('Expressive delivery').select_option('surprised')
                        reaction_paths=[]
                        for index, milliseconds in enumerate([0,100,400,850,1000,1550,2650]):
                            seek(page,milliseconds)
                            path=Path(temporary)/f'reaction-{index:03}.png'
                            page.get_by_test_id('stage').screenshot(path=path)
                            reaction_paths.append(path)
                        assert page.get_by_test_id('resolved').inner_text()=='available / composed'
                        sheet(reaction_paths,output/'surprise-recovery.png',4,['acquire','100 ms','peak / hold','release begins','recovery','settled','final stillness'])
                        page.get_by_label('Expressive delivery').select_option('asleep')
                        rest_paths=[]
                        for index,intensity in enumerate(['0.35','0.75','1']):
                            control=page.get_by_label('Expression intensity')
                            control.evaluate("""(el,value)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}));}""",intensity)
                            seek(page,1800)
                            path=Path(temporary)/f'rest-{index}.png'
                            page.get_by_test_id('scale').screenshot(path=path)
                            rest_paths.append(path)
                        sheet(rest_paths,output/'closed-rest-intensity.png',1,['intensity .35','intensity .75','intensity 1.0'])
                        control.evaluate("""el=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,'.75');el.dispatchEvent(new Event('input',{bubbles:true}));}""")
                        page.get_by_label('Transition sequence').select_option('3')
                        page.get_by_role('button',name='Run sequence',exact=True).click()
                    page.get_by_label("Reduced motion", exact=True).check()
                    reduced_paths = []
                    for index, milliseconds in enumerate([1400, 1600, 1850, 2950]):
                        seek(page, milliseconds)
                        path = Path(temporary) / f"reduced-{index}.png"
                        page.get_by_test_id("stage").screenshot(path=path)
                        reduced_paths.append(path)
                    sheet(reduced_paths, output / "reduced-motion.png", 4, ["thinking", "interrupted", "held interruption", "attentive"])
                    transforms = []
                    for milliseconds in [1600, 1800, 2050]:
                        seek(page, milliseconds)
                        transforms.append(page.locator('.character [data-puck]').get_attribute('transform'))
                    assert len(set(transforms)) == 1
                    receipt["checks"].append("reduced motion holds one static pose per event")
                    page.get_by_label("Reduced motion", exact=True).uncheck()
                    page.get_by_label("Availability boundary").select_option("unavailable")
                    page.get_by_label("Operational state").select_option("speaking")
                    assert page.get_by_test_id("resolved").inner_text() == "unavailable / subdued"
                    page.get_by_label("Availability boundary").select_option("unknown")
                    assert page.get_by_test_id("resolved").inner_text() == "unknown / hesitant"
                    page.get_by_label("Availability boundary").select_option("available")
                    page.get_by_label("Conversational mute", exact=True).check()
                    assert page.get_by_test_id("resolved").inner_text() == "muted / composed"
                    page.get_by_label("Owner attention required", exact=True).check()
                    assert page.get_by_test_id("resolved").inner_text() == "waiting · conversational mute / subdued"
                    page.get_by_role("button", name="Interrupt", exact=True).click()
                    assert "waiting" in page.get_by_test_id("resolved").inner_text()
                    receipt["checks"].append("unavailable / unknown / mute / owner attention override speech and interruption")
                    page.get_by_label("Conversational mute", exact=True).uncheck()
                    page.get_by_label("Owner attention required", exact=True).uncheck()
                    page.get_by_role("button", name="Return to neutral", exact=True).click()
                    seek(page, 1800)
                    # Native keyboard behavior: focus, slider seek and button activation.
                    slider = page.get_by_label("Scrub transition")
                    slider.focus(); slider.press("Home"); slider.press("ArrowRight")
                    assert slider.input_value() == "1"
                    page.get_by_role("button", name="Return to neutral", exact=True).focus()
                    page.keyboard.press("Enter")
                    assert page.get_by_test_id("resolved").inner_text() == "available / composed"
                    receipt["checks"].append("keyboard slider seek and button activation")
                    seek(page, 1800)
                    page.set_viewport_size({"width": 390, "height": 844})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    page.screenshot(path=output / "mobile.png", full_page=True)
                    receipt["checks"].append("390px responsive lab without horizontal overflow")
                    page.emulate_media(reduced_motion="reduce", forced_colors="active")
                    expect(page.get_by_label("Reduced motion", exact=True)).to_be_disabled()
                    page.screenshot(path=output / "system-reduced-forced-colors.png", full_page=True)
                    receipt["checks"].append("OS reduced motion and forced colors")
                    if iteration in {'candidate-v2','motion-v3'}:
                        page.emulate_media(reduced_motion='no-preference',forced_colors='none')
                        page.set_viewport_size({'width':1280,'height':900})
                        page.get_by_role('button',name='Return to neutral',exact=True).click()
                        seek(page,1800)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.screenshot(path=output/'desktop-1280.png',full_page=True)
                        receipt['checks'].append('1280px responsive viewport')
                    context.close(); browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)
    if iteration in {'candidate-v2','motion-v3'}:
        studies=[output.parent/name/'expression-contact-sheet.png' for name in ['study-v0','study-v1',iteration]]
        if all(path.exists() for path in studies):
            sheet(studies,output/'iteration-comparison.png',3,['v0: scaled disc / shallow tension','v1: clipping lid / separate timing',f'{iteration}: open wink / recovery / freer puck'])
        if iteration=='motion-v3':
            sheet([output.parent/'candidate-v2/speaking-frames.png',output/'speaking-frames.png'],output/'motion-before-after.png',1,['v2: subtle one-second movement','v3: broad four-second phrase performance'])
    receipt["artifacts"] = {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in sorted(output.glob("*")) if p.suffix in {".png", ".gif"}}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if receipt["errors"] or receipt["external_requests"]:
        raise RuntimeError(json.dumps(receipt, indent=2))
    print(json.dumps({"output": str(output), "checks": receipt["checks"], "errors": receipt["errors"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", choices=["study-v0", "study-v1", "candidate-v2", "motion-v3"], default="motion-v3")
    parser.add_argument("--node", default=shutil.which("node"))
    args = parser.parse_args()
    capture(args.iteration, args.node)
