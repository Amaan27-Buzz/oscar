"""Extract illustration-only rectangles; preserve every approved source byte."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "design/oscar-mobile-visual-exploration/screens"
    output = root / "mobile/app/src/main/res/drawable-nodpi"
    # Rectangles exclude text, controls and the generated (noncanonical) Orb.
    crops = {
        "home": ("01-oscar-home.png", (0, 550, 841, 990)),
        "automations": ("05-automations-overview.png", (0, 375, 841, 750)),
        "worker": ("06-worker-detail.png", (320, 180, 841, 615)),
        "reading": ("03-expanded-reading.png", (575, 335, 841, 600)),
        "devices": ("11-devices.png", (215, 165, 841, 690)),
        "awareness": ("12-sentry-awareness.png", (450, 140, 841, 775)),
        "today": ("13-today-chief-of-staff.png", (420, 170, 841, 650)),
        "preferences": ("15-preferences.png", (465, 280, 841, 650)),
        "task": ("09-active-task.png", (340, 205, 841, 710)),
        "decision": ("10-approval-decision.png", (420, 185, 841, 705)),
    }
    manifest = {}
    exclusions = {
        "worker": [(320, 550, 560, 615)],
        "reading": [(575, 560, 660, 600)],
        "today": [(420, 550, 500, 650)],
    }
    for name, (file, bounds) in crops.items():
        original = source / file
        target = output / f"illustration_{name}.png"
        with Image.open(original) as image:
            assert image.size == (841, 1870)
            crop = image.crop(bounds).convert("RGBA")
            mask = ImageDraw.Draw(crop)
            for left, top, right, bottom in exclusions.get(name, []):
                mask.rectangle(
                    (left - bounds[0], top - bounds[1], right - bounds[0], bottom - bounds[1]),
                    fill=(0, 0, 0, 0),
                )
            crop.save(target)
        manifest[name] = {
            "source": str(original.relative_to(root)).replace("\\", "/"),
            "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "bounds": bounds,
            "excluded_ui_rectangles": exclusions.get(name, []),
            "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    (root / "mobile/illustration-assets.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
