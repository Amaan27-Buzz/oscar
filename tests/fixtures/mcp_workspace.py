"""Trusted separate-process scoped writer. Scope enforcement is independent of its receipt."""

import hashlib
import os
import sys
from pathlib import Path

from mcp.server import MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from oscar.capabilities import ScopedFiles  # noqa: E402

server = MCPServer("OSCAR synthetic workspace", version="1")
files = ScopedFiles(Path(sys.argv[1]))
account = sys.argv[2]


class Check:
    def check(self) -> None:
        pass


@server.tool()
def read_file(path: str) -> dict[str, str | int]:
    content = files.read(path)
    return {"account_id": account, "content": content.decode(), "pid": os.getpid()}


@server.tool()
def write_file(path: str, content: str) -> dict[str, str | int]:
    files.write(path, content, Check())  # type: ignore[arg-type]
    return {
        "account_id": account,
        "path": path,
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
        "pid": os.getpid(),
    }


if __name__ == "__main__":
    server.run()
