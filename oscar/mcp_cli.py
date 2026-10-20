"""Trusted local MCP installation review; no remote enrollment or implicit process launch."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .accounts import AccountRegistry
from .connectors import ConnectorFabric, EnvironmentSecrets, RiskLevel
from .mcp_client import MCPPlugins, MCPServerConfig
from .policy import PersonalPolicy
from .storage import Store


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument(
        "operation",
        choices=(
            "list",
            "inspect",
            "register",
            "connect",
            "disconnect",
            "enable",
            "disable",
            "remove",
        ),
    )
    parser.add_argument("identifier", nargs="?")
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--approve-digest")
    args = parser.parse_args()
    store = Store(args.state)
    output: Any
    try:
        accounts = AccountRegistry(store)
        fabric = ConnectorFabric(
            store, EnvironmentSecrets({}), PersonalPolicy(store), accounts=accounts
        )
        plugins = MCPPlugins(
            store, fabric, lambda identifier, generation: accounts.check(identifier, generation)
        )
        if args.operation == "register":
            if not args.registration or args.registration.stat().st_size > 20000:
                parser.error("a bounded --registration JSON file is required")
            data = json.loads(args.registration.read_text(encoding="utf-8"))
            if set(data) != {"config", "reviewed"}:
                parser.error("registration requires config and reviewed tool risks")
            digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            config = dict(data["config"])
            config["arguments"] = tuple(config.get("arguments", ()))
            config["reviewed_files"] = tuple(tuple(p) for p in config.get("reviewed_files", ()))
            reviewed: dict[str, RiskLevel | tuple[RiskLevel, ...]] = {
                name: tuple(RiskLevel(risk) for risk in risks)
                for name, risks in data["reviewed"].items()
            }
            candidate = MCPServerConfig(**config)
            if args.approve_digest != digest:
                print(
                    json.dumps(
                        {"review_required": True, "digest": digest, "registration": data}, indent=2
                    )
                )
                return
            accounts.check(candidate.account_id, candidate.account_generation)
            plugins.register(candidate, reviewed, owner_reviewed=True)
            output = plugins.inspect(candidate.id)
        elif args.operation == "list":
            output = plugins.snapshot()
        else:
            if not args.identifier:
                parser.error("installation identifier is required")
            if args.operation == "connect":
                output = plugins.connect(args.identifier)
            elif args.operation == "inspect":
                output = plugins.inspect(args.identifier)
            elif args.operation in {"enable", "disable"}:
                plugins.enable(args.identifier, args.operation == "enable")
                output = plugins.inspect(args.identifier)
            else:
                getattr(plugins, args.operation)(args.identifier)
                output = {"id": args.identifier, "operation": args.operation}
        print(json.dumps(output, indent=2))
    finally:
        store.close()


if __name__ == "__main__":
    main()
