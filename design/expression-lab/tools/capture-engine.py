"""Small actual-browser verification set for the reusable event-driven React renderer."""
import hashlib
import io
import json
from pathlib import Path
import socket
import shutil
import subprocess
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parent.parent
ORIGIN = "http://127.0.0.1:1512"
OUTPUT = ROOT / "docs/design/expression/evidence/engine-v1"

def main():
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1",1512)) == 0:
            raise RuntimeError("Port 1512 occupied; refusing another server")
    OUTPUT.mkdir(parents=True,exist_ok=True)
    node=shutil.which('node')
    if node is None:raise RuntimeError('Node is required')
    process=subprocess.Popen([node,"node_modules/vite/bin/vite.js","preview","--host","127.0.0.1","--port","1512","--strictPort"],cwd=LAB,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    errors=[];external=[]
    try:
        for _ in range(100):
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1",1512)) == 0: break
            time.sleep(.1)
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(channel="msedge",headless=True)
            context=browser.new_context(viewport={"width":1280,"height":1000},permissions=[],reduced_motion="no-preference")
            def isolate(route):
                parsed=urlparse(route.request.url)
                if f"{parsed.scheme}://{parsed.netloc}" == ORIGIN:route.continue_()
                else:external.append(route.request.url);route.abort()
            context.route("**/*",isolate)
            page=context.new_page();page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(ORIGIN+"/?engine=1",wait_until="networkidle")
            page.get_by_test_id("engine-atlas").screenshot(path=OUTPUT/"react-reference-atlas.png")
            page.wait_for_timeout(800)
            puck=page.locator('[data-testid="engine-live"] [data-puck]')
            held=puck.get_attribute("transform");page.wait_for_timeout(1200)
            assert puck.get_attribute("transform")==held
            page.get_by_role("button",name="Permitted phrase accent",exact=True).click()
            page.wait_for_timeout(1200)
            assert puck.get_attribute("transform")!=held
            page.get_by_test_id("engine-live").screenshot(path=OUTPUT/"react-permitted-accent.png")
            page.get_by_role("button",name="Mute",exact=True).click()
            assert "muted" in page.locator('[data-testid="engine-live"] svg').get_attribute("aria-label")
            page.wait_for_timeout(800)
            page.get_by_test_id("engine-live").screenshot(path=OUTPUT/"react-muted.png")
            page.emulate_media(reduced_motion="reduce")
            page.get_by_role("button",name="Speech starts",exact=True).click()
            reduced=puck.get_attribute("transform");page.wait_for_timeout(200)
            assert puck.get_attribute("transform")==reduced
            assert not errors and not external,(errors,external)
            page.goto(ORIGIN,wait_until='networkidle')
            page.get_by_role('button',name='Geometry & restraint',exact=True).click()
            page.evaluate("""()=>{
              const mount=document.createElement('div');mount.id='pixel-comparison';
              Object.assign(mount.style,{position:'fixed',left:'0',top:'0',width:'220px',height:'220px',background:'#f7f7f3',zIndex:'100'});
              mount.append(document.querySelector('.identity-pair img').cloneNode(true));document.body.append(mount);
            }""")
            original=Image.open(io.BytesIO(page.locator('#pixel-comparison').screenshot())).convert('RGB')
            page.evaluate("document.querySelector('#pixel-comparison').replaceChildren(document.querySelector('.identity-pair svg').cloneNode(true))")
            derived=Image.open(io.BytesIO(page.locator('#pixel-comparison').screenshot())).convert('RGB')
            difference=ImageChops.difference(original,derived).getbbox()
            assert difference is None,'Neutral derivative must preserve canonical rendered pixels'
            browser.close()
    finally:
        process.terminate();process.wait(timeout=10)
    receipt={"classification":"SIMULATED EVENT-DRIVEN REACT RENDER / NO CORE EXECUTION","checks":["held speech has no repeated choreography","explicit accent moves","new mute stops speech presentation","OS reduced motion is static"],"errors":errors,"external_requests":external,"canonical_sha256":hashlib.sha256((ROOT/'assets/brand/oscar-orb.svg').read_bytes()).hexdigest(),"artifacts":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUTPUT.glob('react-*.png')}}
    receipt['neutral_pixel_difference_bbox']=difference
    receipt['built_sha256']={str(p.relative_to(LAB/'dist')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((LAB/'dist').rglob('*')) if p.is_file()}
    (OUTPUT/'react-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__ == '__main__':main()
