"""Trusted synthetic knowledge server: no owner credentials or external services."""

import asyncio
import os
import sys

from mcp.server import MCPServer

server = MCPServer("OSCAR synthetic knowledge", version="1")
account = sys.argv[1]


@server.tool()
def lookup(topic: str) -> dict[str, str | int | bool]:
    return {
        "account_id": account,
        "topic": topic,
        "answer": "Synthetic research fact",
        "pid": os.getpid(),
        "secret_inherited": bool(os.environ.get("OSCAR_MCP_TEST_SECRET")),
    }


@server.tool()
async def delay(seconds: int) -> str:
    await asyncio.sleep(seconds)
    return "finished"


@server.tool(name="MixedCase")
def mixed_case(topic: str) -> str:
    return topic


@server.resource("knowledge://fixture/fact")
def fact() -> str:
    return "Synthetic resource fact for " + account


@server.prompt()
def research(topic: str) -> str:
    return "Research synthetic topic: " + topic


if __name__ == "__main__":
    if len(sys.argv) > 2:
        server.run("streamable-http", port=int(sys.argv[2]), stateless_http=True)
    else:
        server.run()
