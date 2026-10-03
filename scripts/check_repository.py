"""Offline repository checks and a value-silent credential scan; never reads .env."""

import os
import re
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root, text=True
    ).splitlines()
    files = sorted(set(files))
    failures = []
    workflow = (root / ".github/workflows/docs-check.yml").read_text(encoding="utf-8")
    required = re.search(r"required=\((.*?)\)", workflow, re.DOTALL)
    if required is None:
        failures.append("required file contract unavailable")
    else:
        for name in required.group(1).split():
            if not (root / name).is_file():
                failures.append("required file absent: " + name)
    names = re.findall(
        r"^([A-Z][A-Z0-9_]*API_KEY[A-Z0-9_]*)=",
        (root / ".env.example").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    material = [os.environ[name].encode() for name in names if os.environ.get(name)]
    secret_pattern = re.compile(
        rb"(?:gsk_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})"
    )
    removed = ("kine" + "table").encode()
    sensitive_found = False
    for name in files:
        path = root / name
        if name == ".env" or name.startswith(".env.") and name != ".env.example":
            sensitive_found = True
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(value in data for value in material) or secret_pattern.search(data):
            sensitive_found = True
        if b"\x00" in data:
            continue
        if removed.lower() in data.lower():
            failures.append("removed-project reference: " + name)
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)", data.decode()):
                target = target.strip("<>").split("#")[0]
                if not target or re.match(r"[a-z]+:", target) or target.startswith("/"):
                    continue
                if not (path.parent / target).exists():
                    failures.append("broken local Markdown link in " + name)
    if sensitive_found:
        failures.append("secret-safety FAIL (material and locations suppressed)")
    for failure in sorted(set(failures)):
        print(failure)
    if failures:
        return 1
    print("Repository required files, local Markdown links and removed references: PASS")
    print("Secret-safety of tracked and non-ignored files: PASS (no material printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
