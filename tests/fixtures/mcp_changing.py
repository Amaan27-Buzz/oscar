"""Trusted fixture whose discovery changes across server restart."""

import sys
from pathlib import Path

from mcp.server import MCPServer

server = MCPServer("OSCAR changing-schema fixture")

if Path(sys.argv[1]).exists():

    @server.tool(name="lookup")
    def changed_lookup(topic: int) -> str:
        return str(topic)
else:

    @server.tool(name="lookup")
    def original_lookup(topic: str) -> str:
        return topic


if __name__ == "__main__":
    server.run()
