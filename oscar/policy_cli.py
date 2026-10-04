"""Owner-facing policy proposal and exact confirmation. No proposal activates itself."""

import argparse
import json
import os
from pathlib import Path

from .credentials import CredentialPool
from .discovery import HTTPDiscovery
from .models import RoutingPolicy
from .policy import PersonalPolicy
from .policy_interpretation import OpenPolicyAuthoring, RouterPolicyInterpreter
from .providers import HTTPAdapter
from .registry import Registry
from .router import Router, RouteUnavailable
from .storage import Store


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("config/development-models.json"))
    parser.add_argument("--provider", default="groq")
    parser.add_argument("--env-file", type=Path)
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--propose")
    command.add_argument("--confirm")
    parser.add_argument("--digest")
    args = parser.parse_args()
    store = Store(args.state)
    try:
        registry = Registry.load(args.manifest, store)
        source = dict(os.environ)
        if args.env_file:
            # Explicit opt-in; no shell evaluation, token values never appear in output/state.
            for line in args.env_file.read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition("=")
                if separator and key.strip().isidentifier():
                    source[key.strip()] = value.strip().strip("\"'")
        pool = CredentialPool(list(registry.providers.values()), source, store)
        router = Router(
            registry,
            pool,
            {kind: HTTPAdapter(kind) for kind in {"openai", "google", "ollama"}},
            store,
            discovery=HTTPDiscovery(),
        )
        author = OpenPolicyAuthoring(
            PersonalPolicy(store, redact=pool.redact),
            RouterPolicyInterpreter(
                router,
                RoutingPolicy(
                    allowed_providers=frozenset({args.provider}), max_attempts=2, timeout_seconds=30
                ),
            ),
        )
        if args.propose:
            candidate = author.propose(args.propose)
            print(json.dumps(candidate, indent=2))
            print(
                "INACTIVE: review the exact interpretation, "
                "then explicitly confirm its ID and digest."
            )
        else:
            if not args.digest:
                raise ValueError("exact review digest required")
            author.confirm(args.confirm, args.digest, owner_authorized=True)
            print(json.dumps({"candidate_id": args.confirm, "state": "owner-confirmed"}))
        return 0
    except (RouteUnavailable, ValueError, PermissionError) as failure:
        print("BLOCKED: " + str(failure))
        return 1
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
