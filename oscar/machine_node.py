"""Separate-process reference Worker. Shared SQLite/loopback is not public deployment.

Trusted composition supplies the short-lived session via a pipe, never argv/env/files.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from time import sleep

from .grid import Grid, SessionHandle
from .machine import MachineScope, MachineWorker
from .storage import Store
from .transport import Dispatcher, ReferenceServer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--trusted-host", action="store_true")
    parser.add_argument("--executable", action="append", default=[])
    parser.add_argument("--codex-home", type=Path)
    args = parser.parse_args()
    bootstrap = json.loads(sys.stdin.readline(8192))
    session = SessionHandle(bootstrap["id"], bootstrap["node_id"], bootstrap["token"])
    store = Store(args.state)
    grid = Grid(store)
    worker = MachineWorker(
        store,
        grid,
        session,
        MachineScope(
            args.workspace, args.trusted_host, tuple(args.executable), codex_home=args.codex_home
        ),
    )
    grid.advertise(session, worker.capabilities())
    dispatcher = Dispatcher(
        store,
        grid,
        session.node_id,
        worker.executors(),
        pause_semantics="before-next-subprocess" if os.name == "nt" else "POSIX-process-group",
    )
    try:
        with ReferenceServer(dispatcher) as server:
            print(
                json.dumps(
                    {
                        "url": server.url,
                        "capabilities": [c.id for c in worker.capabilities()],
                        "agents": sorted(worker.agents),
                    }
                ),
                flush=True,
            )
            while True:
                grid.heartbeat(session)
                sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
