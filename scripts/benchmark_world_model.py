"""Bounded local benchmark. Synthetic values; real SQLite and Controller execution."""

import argparse
import json
import statistics
import tracemalloc
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter, time

from oscar.event_archive import EventArchive
from oscar.jev import Intent, decide
from oscar.perception import PerceptionFabric, PerceptionSource
from oscar.policy import PersonalPolicy
from oscar.storage import Store
from oscar.world_model import Observation, ObservationKind, WorldModel


def run(samples: int = 100) -> dict[str, object]:
    if type(samples) is not int or not 20 <= samples <= 1000:
        raise ValueError("20-1000 bounded benchmark samples required")
    with TemporaryDirectory() as folder:
        root = Path(folder)
        store, archive = Store(root / "state.sqlite"), EventArchive(root / "archive.sqlite")
        try:
            world = WorldModel(store, archive, "synthetic-benchmark")
            fabric = PerceptionFabric(world, PersonalPolicy(store))
            for group in range(16):
                entities = tuple(f"device:{group}:{i}" for i in range(32))
                source = PerceptionSource(
                    f"fixture:{group}",
                    entities,
                    ("status",),
                    (ObservationKind.DEVICE,),
                    perceive=True,
                    events_per_minute=600,
                )
                epoch = fabric.register(source, owner_authorized=True)
                fabric.connect(source.id, epoch, lease_seconds=300)
                for index, entity in enumerate(entities):
                    instant = time()
                    fabric.ingest(
                        Observation(
                            f"event:{index}",
                            source.id,
                            epoch,
                            index + 1,
                            entity,
                            "status",
                            ObservationKind.DEVICE,
                            "online",
                            instant,
                            instant + 300,
                            1,
                        )
                    )
            durations = []
            tracemalloc.start()
            for _ in range(samples):
                start = perf_counter()
                result = world.resolve("device:0:0", "status")
                assert result.value == "online" and result.simulated
                assert decide(Intent("2 + 3")).capability_kind == "addition"
                durations.append((perf_counter() - start) * 1000)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            start = perf_counter()
            fabric.disconnect("fixture:0", 1)
            assert world.resolve("device:0:0", "status").state == "unavailable"
            fabric.connect("fixture:0", 1)
            assert world.resolve("device:0:0", "status").value == "online"
            reconnect = (perf_counter() - start) * 1000
            ordered = sorted(durations)
            return {
                "classification": "SIMULATED",
                "storage": "real local SQLite/WAL",
                "samples": samples,
                "current_rows": 512,
                "success_rate": 1.0,
                "state_assertion_accuracy": 1.0,
                "model_invocations": 0,
                "external_tool_invocations": 0,
                "p50_ms": statistics.median(durations),
                "p95_ms": ordered[int(0.95 * (samples - 1))],
                "peak_traced_bytes": peak,
                "disconnect_reconnect_ms": reconnect,
            }
        finally:
            store.close()
            archive.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = run()
    text = json.dumps(receipt, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
