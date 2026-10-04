"""Explicit native-vault device enrollment. No polling loop or borrowed credentials."""

import argparse
import json
import sys
from pathlib import Path

from .oauth_device import GitHubDeviceFlow
from .secure_credentials import WindowsCredentialStore
from .storage import Store


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--owner-authorized", action="store_true")
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--begin", metavar="REGISTERED_CLIENT_ID")
    command.add_argument("--poll", metavar="TRANSACTION_ID")
    command.add_argument("--disconnect", metavar="CONNECTION_ID")
    args = parser.parse_args()
    store = Store(args.state)
    try:
        flow = GitHubDeviceFlow(store, WindowsCredentialStore())
        if args.begin:
            # Challenge/nonce are displayed only to the interactive owner. Do not redirect
            # this output into acceptance logs or commit it. SQLite keeps a nonce digest.
            result = flow.begin(args.begin, owner_authorized=args.owner_authorized)
        elif args.poll:
            print(
                "Enter the transaction nonce on stdin; one bounded poll follows:", file=sys.stderr
            )
            result = flow.poll_once(
                args.poll,
                sys.stdin.readline(1000).strip(),
                owner_authorized=args.owner_authorized,
            )
            result = {key: value for key, value in result.items() if key != "credential_ref"}
        else:
            flow.disconnect(args.disconnect, owner_authorized=args.owner_authorized)
            result = {"state": "locally_disconnected_provider_revocation_pending"}
        print(json.dumps(result, indent=2))
        return 0
    except (KeyError, PermissionError, ValueError, RuntimeError, OSError):
        print(
            "BLOCKED: enrollment unavailable, unconfirmed, expired or ambiguous. "
            "Inspect local state."
        )
        return 1
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
