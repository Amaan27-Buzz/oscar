"""Reproducible owner-only Windows alpha bundle; never includes configuration secrets."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-desktop-build", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise OSError("Build this Windows alpha on Windows")
    output = ROOT / ".oscar/alpha"
    if not output.resolve().is_relative_to(ROOT.resolve()) or any(
        path.is_symlink() for path in (ROOT / ".oscar", output)
    ):
        raise PermissionError(
            "Alpha output must stay inside the repository's owned build directory"
        )
    output.mkdir(parents=True, exist_ok=True)
    config = ROOT / ".env.local"
    original = hashlib.sha256(config.read_bytes()).digest() if config.is_file() else None
    if not args.skip_desktop_build:
        subprocess.run([sys.executable, "-m", "scripts.build_desktop"], cwd=ROOT, check=True)
    desktop = ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    if not desktop.is_file():
        raise FileNotFoundError("Build the actual native Desktop before packaging")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        "OSCAR",
        "--distpath",
        str(output / "dist"),
        "--workpath",
        str(output / "work"),
        "--specpath",
        str(output / "spec"),
        "--paths",
        str(ROOT),
        "--collect-submodules",
        "oscar",
        "--collect-submodules",
        "cryptography",
        "--collect-submodules",
        "dotenv",
        "--exclude-module",
        "torch",
        "--exclude-module",
        "tensorflow",
        "--exclude-module",
        "sentence_transformers",
    ]
    # The cloud alpha does not ship optional local inference/plotting UI engines.
    for module in ("matplotlib", "PyQt6", "PySide6", "numpy", "scipy", "pandas"):
        command += ["--exclude-module", module]
    for path in (ROOT / "oscar").glob("*.ps1"):
        command += ["--add-data", str(path) + os.pathsep + "oscar"]
    command += [str(ROOT / "scripts/start_oscar.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    package = output / "dist/OSCAR"
    destination = package / "desktop/src-tauri/target/debug/oscar-desktop.exe"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(desktop, destination)
    (package / "config").mkdir(exist_ok=True)
    shutil.copy2(
        ROOT / "config/development-models.json", package / "config/development-models.json"
    )
    for name in ("LICENSE", "NOTICE"):
        if (ROOT / name).is_file():
            shutil.copy2(ROOT / name, package / name)
    instructions = """OSCAR Windows development alpha (unsigned; owner testing only)

Extract the entire folder and run OSCAR.exe. Keep its _internal folder beside it.
OSCAR.exe starts the persistent Core, Workspace and Companion together.
Quit through Workspace Preferences or the tray to stop the owned runtime.

Windows 10/11 and Microsoft Edge WebView2 Runtime are required.
Python and Ollama are not required for conversation in this bundle.
Cloud inference is restricted to verified-free routes; paid/local fallback is disabled.
Messages and relevant context are sent to your selected cloud provider.

State and history: %LOCALAPPDATA%\\DawnlightLabs\\OSCAR
Provider credentials: Windows Credential Manager via OSCAR's Vault.
No project credential file, database, owner key or private recording is included.
Existing secure provider bindings on this Windows account are reused.
A new account needs secure provider setup; no keys are bundled or invented.

Diagnostic check from PowerShell:
  .\\OSCAR.exe --check --provider openrouter

Upgrade: quit OSCAR, extract the new package into a separate application folder,
then launch it. Keep the LocalAppData directory and Windows credentials.
Uninstall: quit and remove only the extracted application folder. This preserves
your history and Vault. Data/credential removal is a separate explicit operation.

This is not production signing, installer certification or full alpha acceptance.
"""
    (package / "READ-ME.txt").write_text(instructions, encoding="utf-8")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    files = sorted(path for path in package.rglob("*") if path.is_file())
    for path in files:
        if path.name.lower().startswith(".env") or path.suffix.lower() in {
            ".db",
            ".sqlite",
            ".credentials",
        }:
            raise RuntimeError(
                "Runtime configuration or private state must never enter an alpha package"
            )
    manifest = {
        "build": "unsigned Windows development alpha",
        "source_head": head,
        "working_tree_dirty": dirty,
        "built_at": datetime.now(UTC).isoformat(),
        "desktop_sha256": hashlib.sha256(desktop.read_bytes()).hexdigest(),
        "files": {
            str(path.relative_to(package)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in files
        },
    }
    (package / "build-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive_path = output / "OSCAR-0.1.0-alpha-windows-x64.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                archive.write(path, "OSCAR/" + str(path.relative_to(package)))
    if original is not None and hashlib.sha256(config.read_bytes()).digest() != original:
        raise RuntimeError(
            "Existing configuration changed during packaging; inspect before continuing"
        )
    print("Owner-test bundle:", archive_path)
    print("Launch:", package / "OSCAR.exe")
    print("No release, signing or complete alpha acceptance is claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
