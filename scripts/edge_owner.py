"""Owner-invoked local Edge enrollment/acceptance console; never autonomous flashing.

Provisioning material is written only under ignored .oscar/edge. No secret values
are printed. No physical command is queued until the owner types it explicitly.
"""

import argparse
import csv
import getpass
import json
import ssl
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from oscar.edge import KINDS, EdgeBridge
from oscar.edge_http import server
from oscar.grid import Grid, Node, NodeRole
from oscar.policy import PersonalPolicy
from oscar.storage import Store


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("enroll", "serve", "disconnect"))
    parser.add_argument("--directory", type=Path, default=Path(".oscar/edge"))
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8443)
    args = parser.parse_args()
    directory = args.directory.resolve()
    expected = (Path.cwd() / ".oscar/edge").resolve()
    if directory != expected:
        raise ValueError("acceptance secrets must stay in ignored .oscar/edge")
    directory.mkdir(parents=True, exist_ok=True)
    store = Store(directory / "core.db")
    grid = Grid(store, heartbeat_ttl=2)
    node_id = "desk-edge"
    if args.mode == "disconnect":
        grid.revoke(node_id)
        store.close()
        print("Local test node revoked. Firmware NVS and files preserved for owner cleanup.")
        return 0
    if args.mode == "enroll":
        if (directory / "provision.csv").exists():
            raise ValueError(
                "existing provisioning preserved; revoke deliberately before replacing"
            )
        ssid = input("Owner Wi-Fi SSID: ")
        password = getpass.getpass("Owner Wi-Fi password: ")
        url = input("HTTPS Core URL, including /edge/v1/exchange: ")
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.path != "/edge/v1/exchange"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("explicit HTTPS exchange URL required")
        ca = (directory / "core-cert.pem").read_text()
        values = {
            "ssid": ssid,
            "password": password,
            "url": url,
            "node": node_id,
            "ca": ca,
        }
        if any(
            len(values[k].encode()) >= n
            for k, n in (("ssid", 33), ("password", 65), ("url", 256), ("ca", 2048))
        ):
            raise ValueError("provisioning exceeds firmware bound")
        scopes = ("heartbeat", "advertise", *KINDS)
        try:
            grid.store.get("node", node_id)
        except KeyError:
            grid.register(Node(node_id, NodeRole.EDGE, scopes))
        session = grid.pair(node_id, scopes, ttl=86400)
        values.update(session=session.id, token=session.token)
        path = directory / "provision.csv"
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(["key", "type", "encoding", "value"])
            writer.writerow(["oscar", "namespace", "", ""])
            for key, value in values.items():
                writer.writerow([key, "data", "string", value])
        path.chmod(0o600)
        print(
            "Local one-day node session created. Ignored provisioning CSV ready; values suppressed."
        )
        store.close()
        return 0
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(directory / "core-cert.pem", directory / "core-key.pem")
    bridge = EdgeBridge(grid, PersonalPolicy(store), node_id)
    listener = server(bridge, (args.bind, args.port), tls=tls)
    thread = Thread(target=listener.serve_forever, daemon=True)
    thread.start()
    print("Owner commands: health, input, output, on, off, sensor, reflex, stop, state, quit")
    commands = {
        "health": ("edge.health", 0, 0),
        "input": ("edge.gpio.read", 0, 0),
        "output": ("edge.gpio.read", 1, 0),
        "on": ("edge.gpio.write", 1, 1),
        "off": ("edge.gpio.write", 1, 0),
        "sensor": ("edge.sensor.read", 2, 0),
        "reflex": ("edge.reflex.test", 0, 0),
        "stop": ("edge.stop", 0, 0),
    }
    try:
        while True:
            command = input("edge> ").strip()
            if command == "quit":
                break
            if command == "state":
                print(json.dumps(bridge.state(), indent=2))
                print(json.dumps(store.ledger("")[-8:], indent=2))
                continue
            if command not in commands:
                print("Unknown command")
                continue
            capability, channel, value = commands[command]
            try:
                identifier = bridge.queue(
                    capability, channel, value, granted=frozenset({capability}), confirmed=True
                )
                print(
                    f"Queued {identifier}; ACK is REPORTED. Use output plus owner visual readback."
                )
            except (PermissionError, ValueError, KeyError) as error:
                print(type(error).__name__ + ": " + str(error))
    finally:
        listener.shutdown()
        listener.server_close()
        thread.join(timeout=3)
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
