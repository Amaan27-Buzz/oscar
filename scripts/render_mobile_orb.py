"""Render the canonical SVG unchanged for native Android display; no generated/reinterpreted art.

Optional maintainer tool: install the repository's browser extra and Chromium/Edge.
The runtime APK has no browser dependency. Source/render digests fence stale artwork.
"""

import hashlib
import json
from pathlib import Path


def main() -> int:
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parents[1]
    source = root / "assets/brand/oscar-orb.svg"
    output = root / "mobile/app/src/main/res/drawable-nodpi/oscar_orb.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        try:
            context = browser.new_context(
                viewport={"width": 582, "height": 582}, device_scale_factor=2
            )
            context.set_offline(True)
            page = context.new_page()
            page.set_content(
                '<html><body style="margin:0;background:transparent">'
                + source.read_text(encoding="utf-8")
                + "</body></html>"
            )
            page.locator("svg").screenshot(path=str(output), omit_background=True)
            receipt = {
                "source": "assets/brand/oscar-orb.svg",
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "render_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "renderer": "Chromium " + browser.version,
                "size": [1164, 1164],
                "geometry": "unchanged canonical SVG; intrinsic size, 2x raster",
            }
            (root / "mobile/orb-render.json").write_text(
                json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(receipt, indent=2))
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
