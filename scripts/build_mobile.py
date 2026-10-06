"""Build/test the pinned Kotlin/Compose project; inspect reference APK and canonical Orb bytes."""

import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    wrapper = root / "mobile" / ("gradlew.bat" if os.name == "nt" else "gradlew")
    command = [
        str(wrapper),
        "--no-daemon",
        "testDebugUnitTest",
        "assembleDebug",
        "assembleDebugAndroidTest",
        "lintDebug",
    ]
    if os.name != "nt":
        command.insert(0, "sh")
    subprocess.run(command, cwd=root / "mobile", check=True, timeout=1800)
    apk = root / "mobile/app/build/outputs/apk/debug/app-debug.apk"
    with zipfile.ZipFile(apk) as archive:
        orb = archive.read("assets/oscar-orb.svg")
        if orb != (root / "assets/brand/oscar-orb.svg").read_bytes():
            raise RuntimeError("Canonical Orb asset changed during packaging")
    output = root / ".oscar/mobile"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "evidence_class": "REFERENCE",
        "apk_sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
        "orb_sha256": hashlib.sha256(orb).hexdigest(),
        "package": "io.dawnlight.oscar.mobile",
        "build": "Kotlin/Compose Gradle debug reference, not production signing",
        "owner_device_acceptance": "OWNER_DEVICE_ACCEPTANCE_NOT_RUN",
    }
    (output / "build-reference.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
