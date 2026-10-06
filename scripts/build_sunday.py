"""Build/verify a local reference APK using installed JDK/Android SDK, no device or deploy."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def run(arguments: list[str], output: Path | None = None) -> None:
    result = subprocess.run(arguments, check=True, capture_output=True, text=True, timeout=180)
    if output:
        output.write_text(result.stdout, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path)
    parser.add_argument("--javac", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sdk = args.sdk or Path(os.environ.get("ANDROID_HOME", os.environ.get("ANDROID_SDK_ROOT", "")))
    sdk = sdk.resolve()
    compiler = args.javac or Path(shutil.which("javac") or "")
    compiler = compiler.resolve()
    java = compiler.parent / ("java.exe" if os.name == "nt" else "java")
    jar = compiler.parent / ("jar.exe" if os.name == "nt" else "jar")
    keytool = compiler.parent / ("keytool.exe" if os.name == "nt" else "keytool")
    tools = sdk / "build-tools/36.0.0"
    android = sdk / "platforms/android-36/android.jar"
    executable = ".exe" if os.name == "nt" else ""
    if not all(
        p.is_file() for p in (compiler, java, jar, keytool, android, tools / ("aapt2" + executable))
    ):
        raise RuntimeError("installed JDK and Android SDK 36/build-tools 36.0.0 required")
    temporary = root / ".tmp"
    temporary.mkdir(exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix="sunday-sdk-", dir=temporary)).resolve()
    if not build.is_relative_to(temporary.resolve()):
        raise ValueError("reference build output escaped workspace")
    app = root / "sunday/app/src/main"
    generated, classes, dex = (build / name for name in ("generated", "classes", "dex"))
    for directory in (generated, classes, dex):
        directory.mkdir()
    manifest = ET.parse(app / "AndroidManifest.xml")
    manifest.getroot().set("package", "io.dawnlight.oscar.sunday")
    application = manifest.find("application")
    if application is None:
        raise ValueError("Android application manifest required")
    application.set("{http://schemas.android.com/apk/res/android}debuggable", "true")
    manifest.write(build / "AndroidManifest.xml", encoding="utf-8", xml_declaration=True)
    aapt = str(tools / ("aapt2" + executable))
    run([aapt, "compile", "--dir", str(app / "res"), "-o", str(build / "resources.zip")])
    run(
        [
            aapt,
            "link",
            "-I",
            str(android),
            "--manifest",
            str(build / "AndroidManifest.xml"),
            "--min-sdk-version",
            "30",
            "--target-sdk-version",
            "36",
            "--version-code",
            "1",
            "--version-name",
            "0.1.0-foundation",
            "--java",
            str(generated),
            "-o",
            str(build / "unsigned.apk"),
            str(build / "resources.zip"),
        ]
    )
    package = generated / "io/dawnlight/oscar/sunday"
    package.mkdir(parents=True, exist_ok=True)
    (package / "BuildConfig.java").write_text(
        "package io.dawnlight.oscar.sunday; public final class BuildConfig { "
        "public static final boolean DEBUG=true; }\n",
        encoding="utf-8",
    )
    sources = [*app.rglob("*.java"), *generated.rglob("*.java")]
    run(
        [
            str(compiler),
            "--release",
            "17",
            "-encoding",
            "UTF-8",
            "-classpath",
            str(android),
            "-d",
            str(classes),
            *map(str, sources),
        ]
    )
    run([str(jar), "--create", "--file", str(build / "classes.jar"), "-C", str(classes), "."])
    run(
        [
            str(java),
            "-cp",
            str(tools / "lib/d8.jar"),
            "com.android.tools.r8.D8",
            "--debug",
            "--lib",
            str(android),
            "--min-api",
            "30",
            "--output",
            str(dex),
            str(build / "classes.jar"),
        ]
    )
    orb = root / "assets/brand/oscar-orb.svg"
    with zipfile.ZipFile(build / "unsigned.apk", "a") as archive:
        archive.write(orb, "assets/oscar-orb.svg")
        for file in dex.glob("*.dex"):
            archive.write(file, file.name)
    run(
        [
            str(tools / ("zipalign" + executable)),
            "-f",
            "4",
            str(build / "unsigned.apk"),
            str(build / "aligned.apk"),
        ]
    )
    run(
        [
            str(keytool),
            "-genkeypair",
            "-keystore",
            str(build / "debug.jks"),
            "-storepass",
            "android",
            "-keypass",
            "android",
            "-alias",
            "reference",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-dname",
            "CN=OSCAR Local Reference",
            "-validity",
            "30",
        ]
    )
    signer = [str(java), "-jar", str(tools / "lib/apksigner.jar")]
    apk = build / "oscar-sunday-reference.apk"
    run(
        [
            *signer,
            "sign",
            "--ks",
            str(build / "debug.jks"),
            "--ks-pass",
            "pass:android",
            "--key-pass",
            "pass:android",
            "--out",
            str(apk),
            str(build / "aligned.apk"),
        ]
    )
    run([*signer, "verify", "--verbose", str(apk)], build / "signature-verification.txt")
    run([aapt, "dump", "badging", str(apk)], build / "package-verification.txt")
    with zipfile.ZipFile(apk) as archive:
        if (
            archive.read("assets/oscar-orb.svg") != orb.read_bytes()
            or "classes.dex" not in archive.namelist()
        ):
            raise ValueError("compiled app/brand source verification failed")
    report = {
        "evidence_class": "REFERENCE_LOCAL_ANDROID_BUILD",
        "apk": str(apk),
        "apk_sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
        "bytes": apk.stat().st_size,
        "sdk": 36,
        "min_sdk": 30,
        "source_sha256": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in app.rglob("*")
            if p.is_file()
        },
        "signature": "VERIFIED_DEBUG_REFERENCE_ONLY",
        "canonical_orb": "EXACT_SOURCE_BYTES",
        "device_install": "NOT_RUN",
        "owner_android_acceptance": "DEFERRED_BY_OWNER",
    }
    output = root / ".oscar/sunday"
    output.mkdir(parents=True, exist_ok=True)
    (output / "build-reference.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "source_sha256"}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as failure:
        print(failure.stderr)
        raise SystemExit(failure.returncode) from None
