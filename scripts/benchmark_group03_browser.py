"""Compare equivalent fixture reads as separate plans versus an existing batched plan."""

import argparse
import json
import statistics
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from time import perf_counter
from typing import Any

from oscar.browser_worker import run


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/first", "/second"}:
            self.send_error(404)
            return
        body = (
            "<html><head><title>OSCAR benchmark</title></head><body>"
            + self.path[1:]
            + " synthetic fixture</body></html>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass


def benchmark(samples: int = 5) -> dict[str, Any]:
    if type(samples) is not int or not 3 <= samples <= 10:
        raise ValueError("3-10 bounded browser samples required")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    timings: dict[str, list[float]] = {"separate_plans": [], "batched_plan": []}
    origin = "http://127.0.0.1:" + str(server.server_port)
    try:
        with TemporaryDirectory() as folder:
            for sample in range(samples):
                # Alternate order so the candidate does not always benefit from warm caches.
                for mode in list(timings) if sample % 2 == 0 else list(reversed(timings)):
                    paths = (
                        [["first"], ["second"]]
                        if mode == "separate_plans"
                        else [["first", "second"]]
                    )
                    start = perf_counter()
                    observations = []
                    for group in paths:
                        steps = [
                            step
                            for path in group
                            for step in (
                                {"operation": "navigate", "url": origin + "/" + path},
                                {"operation": "inspect"},
                            )
                        ]
                        result = run(
                            {"origins": [origin], "steps": steps, "timeout": 15, "max_text": 200},
                            Path(folder),
                        )
                        observations.extend(result["observations"])
                    assert len(observations) == 2
                    for path, observation in zip(("first", "second"), observations, strict=True):
                        assert observation["text"].strip() == path + " synthetic fixture"
                        assert observation["url"] == origin + "/" + path
                    timings[mode].append((perf_counter() - start) * 1000)
        return {
            "classification": "VERIFIED_REAL_LOCAL",
            "source_data": "SIMULATED",
            "executor": "existing oscar.browser_worker.run / isolated headless Chromium",
            "samples_per_mode": samples,
            "pages_per_task": 2,
            "model_invocations": 0,
            "results": {
                mode: {
                    "p50_ms": statistics.median(values),
                    "p95_ms": sorted(values)[-1],
                    "success_rate": 1.0,
                    "state_assertion_accuracy": 1.0,
                    "tool_invocations_per_task": 2 if mode == "separate_plans" else 1,
                    "samples_ms": values,
                }
                for mode, values in timings.items()
            },
            "limits": (
                "Five samples; p95 uses maximum. Read-only anonymous fixture, "
                "no mutation/auth parity claim; memory and reconnect not measured."
            ),
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = json.dumps(benchmark(), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
