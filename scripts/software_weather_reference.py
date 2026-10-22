"""Explicit public Sydney forecast acceptance; no owner location or account is used."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.harness import Harness
from oscar.sentry import AwarenessMode, SentrySettings, SentryState


def main() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        with Harness(
            root / "core.sqlite",
            root / "files",
            Path("config/development-models.json"),
            start_services=False,
        ) as h:
            config = {
                "id": "public-sydney-weather",
                "adapter": "weather",
                "entity_id": "weather:public-sydney",
                "interval_seconds": 600,
                "retain": False,
                "retention_seconds": 3600,
                "latitude": -33.8688,
                "longitude": 151.2093,
                "place": "Sydney public reference",
            }
            review = h.world.review_source(config)
            h.world.configure_native_source(config, owner_authorized=True)
            h.world.sentry.configure(
                SentrySettings(AwarenessMode.SENTRY, SentryState.AWARE, (config["id"],)),
                owner_authorized=True,
            )
            counts = h.world.tick()
            source = h.world.brief()["sources"][0]
            assert counts["polled"] == 1 and source["state"] == "current", counts
            value = json.loads(source["value"])
            assert value["kind"] == "forecast" and value["credit"] == "MET Norway · CC BY 4.0"
            assert source["epistemic"] == "REPORTED" and source["account_id"] is None
            assert h.archive.db.execute("SELECT count(*) FROM archive_events").fetchone()[0] == 0
            evidence = source["evidence"][0]
            assert evidence["id"] and evidence["observed_at"] <= time() < evidence["fresh_until"]
            receipt = {
                "status": "PUBLIC_PROVIDER_READ_VERIFIED",
                "observed_at": time(),
                "source": review["endpoint"],
                "configuration": config,
                "report": value,
                "evidence": evidence,
                "retained_events": 0,
                "owner_location": False,
                "owner_activation": False,
                "tls": "verified host CA trust; SSL_CERT_FILE may supply an installed CA bundle",
                "boundary": (
                    "Public forecast acquisition; no personal weather or physical acceptance"
                ),
                "sha256": {
                    name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                    for name in (
                        "oscar/ambient.py",
                        "oscar/world_runtime.py",
                        "scripts/software_weather_reference.py",
                    )
                },
            }
            target = Path("docs/evidence/software-completion/weather-2026-10-21.json")
            target.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"status": receipt["status"], "receipt": str(target)}))


if __name__ == "__main__":
    main()
