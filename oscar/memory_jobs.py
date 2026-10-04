"""One bounded restartable consolidation batch; no perpetual host required."""

import argparse
import json
from pathlib import Path

from .event_archive import EventArchive, MemoryWriter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--relationship", required=True)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--restart-completed-pass", action="store_true")
    args = parser.parse_args()
    archive = EventArchive(args.archive)
    try:
        job = MemoryWriter(archive).consolidate_step(
            args.relationship, batch_size=args.batch_size, restart=args.restart_completed_pass
        )
        print(json.dumps({"checkpoint": job, "index_rebuild_required": bool(job["merged"])}))
        return 0
    finally:
        archive.close()


if __name__ == "__main__":
    raise SystemExit(main())
