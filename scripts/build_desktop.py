"""Build the Windows Tauri product. Toolchain cache is local; no installer/release claim."""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks", action="store_true")
    args = parser.parse_args()
    directory = ROOT / "desktop"
    node = ROOT / ".oscar/toolchains/node-v24.21.0-win-x64"
    env = dict(os.environ)
    if node.is_dir():
        env["PATH"] = str(node) + os.pathsep + env.get("PATH", "")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm", path=env["PATH"])
    if npm is None:
        raise RuntimeError("supported Node.js LTS/npm required")

    def run(command: list[str]) -> None:
        subprocess.run(command, cwd=directory, env=env, check=True)

    run([npm, "ci"])
    # Rust's bundled context macro also runs during Clippy/tests on a clean checkout.
    run([npm, "run", "build"])
    bundled = "".join(p.read_text(encoding="utf-8") for p in (directory / "dist").rglob("*.js"))
    if "fixture-context" in bundled or "DEVELOPMENT SHOWCASE" in bundled:
        raise RuntimeError("development showcase must not enter the production frontend bundle")
    if args.checks:
        run([npm, "run", "typecheck"])
        run([npm, "test"])
        run(["cargo", "+1.99.0", "fmt", "--manifest-path", "src-tauri/Cargo.toml", "--", "--check"])
        run(
            [
                "cargo",
                "+1.99.0",
                "clippy",
                "--manifest-path",
                "src-tauri/Cargo.toml",
                "--all-targets",
                "--",
                "-D",
                "warnings",
            ]
        )
        run(["cargo", "+1.99.0", "test", "--manifest-path", "src-tauri/Cargo.toml", "--locked"])
    run([npm, "run", "tauri", "build", "--", "--debug", "--no-bundle"])
    executable = directory / "src-tauri/target/debug/oscar-desktop.exe"
    if os.name == "nt" and not executable.is_file():
        raise RuntimeError("Windows debug executable was not produced")
    print("Tauri debug executable built; production installer acceptance NOT RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
