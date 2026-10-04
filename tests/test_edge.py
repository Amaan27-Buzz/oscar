import tempfile
import unittest
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from edge.simulator.model import ROOT, Gateway, Pico, reference_binary
from oscar.edge import KINDS, EdgeBridge
from oscar.edge_http import server
from oscar.edge_protocol import Frame, Kind
from oscar.grid import Grid, Node, NodeRole
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.storage import Store


class EdgeProtocolTests(unittest.TestCase):
    def test_source_contract_and_all_roundtrips(self) -> None:
        source = (ROOT / "edge/protocol/edge.h").read_text()
        for kind in Kind:
            self.assertRegex(source, rf"#define EDGE_{kind.name} {kind.value}\b")
            frame = Frame(kind, 123, 456, 1, 42)
            self.assertEqual(Frame.decode(frame.encode()), frame)
        self.assertIn("#define EDGE_VERSION 1", source)
        self.assertIn("#define EDGE_FRAME_SIZE 20", source)

    def test_crc_version_magic_bounds(self) -> None:
        wire = Frame(Kind.HEALTH, 1, 1).encode()
        for index in range(20):
            bad = bytearray(wire)
            bad[index] ^= 1
            with self.assertRaises(ValueError):
                Frame.decode(bytes(bad))
        for bad in (wire[:19], wire + b"x", b"", bytes(1000)):
            with self.assertRaises(ValueError):
                Frame.decode(bad)
        for session, seq, channel, value in (
            (0, 1, 0, 0),
            (1, 0, 0, 0),
            (1, 1, 65536, 0),
            (1, 1, 0, -1),
        ):
            with self.assertRaises(ValueError):
                Frame(Kind.HEALTH, session, seq, channel, value).encode()


class FirmwareReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.binary = reference_binary()

    def setUp(self) -> None:
        self.pico = Pico(self.binary)
        self.addCleanup(self.pico.close)
        self.gateway = Gateway(self.pico)
        self.assertEqual(self.gateway.connect().reply.kind, Kind.ACK)  # type: ignore[union-attr]

    def test_configured_gpio_sensor_capabilities(self) -> None:
        self.assertEqual(self.gateway.send(Kind.CAPABILITIES).reply.value, 0x3F)  # type: ignore[union-attr]
        self.assertEqual(self.gateway.send(Kind.SENSOR_SAMPLE, 2).reply.value, 123)  # type: ignore[union-attr]
        self.assertTrue(self.gateway.send(Kind.GPIO_READ, 0).reply.value)  # type: ignore[union-attr]
        self.assertTrue(self.gateway.send(Kind.GPIO_WRITE, 1, 1).output)
        self.assertTrue(self.gateway.send(Kind.GPIO_READ, 1).reply.value)  # type: ignore[union-attr]
        self.assertFalse(self.gateway.send(Kind.DISPLAY, 1, 0).output)
        self.assertEqual(self.gateway.send(Kind.GPIO_WRITE, 15, 1).reply.kind, Kind.ERROR)  # type: ignore[union-attr]

    def test_duplicate_delay_ack_drop_retry(self) -> None:
        result = self.gateway.send(Kind.GPIO_WRITE, 1, 1, duplicate=True, delay_ack=True)
        self.assertEqual(result.writes, 1)
        self.assertEqual(self.gateway.send(Kind.DISPLAY, 1, 0, drop=2).writes, 2)

    def test_corrupt_timeout_and_stream_resync(self) -> None:
        self.assertIsNone(self.gateway.send(Kind.GPIO_WRITE, 1, 1, corrupt=True).reply)
        self.assertIsNone(self.gateway.send(Kind.HEALTH, drop=3).reply)
        wire = Frame(Kind.HEALTH, 100, 100).encode()
        self.assertIsNotNone(self.pico.step(700, b"garbage" + wire).reply)
        self.assertIsNone(self.pico.step(800, wire[:10]).reply)
        self.assertIsNone(self.pico.step(1001, wire[10:]).reply)
        self.assertIsNotNone(self.pico.step(1100, wire).reply)

    def test_firmware_rejects_version_unknown_crc_and_oversize_noise(self) -> None:
        import binascii
        import struct

        wire = Frame(Kind.HEALTH, 100, 100).encode()
        for index, value in ((2, 2), (3, 99)):
            body = bytearray(wire[:18])
            body[index] = value
            bad = bytes(body) + struct.pack("<H", binascii.crc_hqx(body, 0xFFFF))
            self.assertIsNone(self.pico.step(0, bad).reply)
        self.assertIsNone(self.pico.step(0, bytes(40)).reply)

    def test_core_loss_safe_then_reconnect_without_replaying_output(self) -> None:
        self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        self.assertFalse(self.gateway.loss(core=True).output)
        with self.assertRaises(PermissionError):
            self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        self.gateway.core = True
        self.assertFalse(self.gateway.reset().output)
        self.assertTrue(self.gateway.send(Kind.GPIO_WRITE, 1, 1).output)

    def test_link_loss_watchdog_and_reset(self) -> None:
        self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        lost = self.gateway.loss(link=True)
        self.assertFalse(lost.output)
        self.assertFalse(lost.connected)
        self.gateway.link = True
        self.assertFalse(self.gateway.reset().output)
        self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        self.assertFalse(self.pico.step(self.gateway.now, reset=True).output)
        self.assertEqual(self.gateway.send(Kind.HEALTH).reply.kind, Kind.ERROR)  # type: ignore[union-attr]
        self.assertFalse(self.gateway.reset().output)

    def test_stop_interlock_reflex_latch(self) -> None:
        self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        self.assertFalse(self.gateway.send(Kind.REFLEX_TRIGGER).output)
        self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        self.assertTrue(self.pico.step(10, interlock=True).stopped)
        self.assertEqual(self.gateway.send(Kind.GPIO_WRITE, 1, 1).reply.kind, Kind.ERROR)  # type: ignore[union-attr]
        self.assertTrue(self.gateway.reset().stopped)
        self.assertTrue(self.gateway.send(Kind.E_STOP).stopped)
        self.assertFalse(self.gateway.send(Kind.SAFE_STATE).output)

    def test_replay_and_conflicting_duplicate(self) -> None:
        self.gateway.send(Kind.GPIO_WRITE, 1, 1)
        seq = self.gateway.sequence
        self.assertEqual(
            self.pico.step(0, Frame(Kind.GPIO_WRITE, 100, seq, 1, 0).encode()).reply.kind,
            Kind.ERROR,
        )  # type: ignore[union-attr]
        self.gateway.send(Kind.SAFE_STATE)
        self.assertFalse(self.pico.step(0, Frame(Kind.GPIO_WRITE, 99, seq, 1, 1).encode()).output)

    def test_bounded_events(self) -> None:
        for seq in range(1, 20):
            self.gateway.forward(Frame(Kind.EVENT, 100, seq, 2, seq))
        self.assertEqual(len(self.gateway.events), 8)
        self.assertEqual(self.gateway.dropped_events, 11)


class EdgeIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / "core.db")
        self.addCleanup(self.store.close)
        self.now = 100.0
        self.grid = Grid(self.store, clock=lambda: self.now, heartbeat_ttl=2)
        self.scopes = ("heartbeat", "advertise", *KINDS)
        self.grid.register(Node("desk-edge", NodeRole.EDGE, self.scopes))
        self.session = self.grid.pair("desk-edge", self.scopes)
        self.policy = PersonalPolicy(self.store)
        self.bridge = EdgeBridge(self.grid, self.policy, "desk-edge")
        self.bridge.exchange(self.session, 100, True, simulated=True)

    def queue(self) -> str:
        return self.bridge.queue(
            "edge.gpio.write", 1, 1, granted=frozenset({"edge.gpio.write"}), confirmed=True
        )

    def test_grid_advertisement_health_withdrawal_expiry(self) -> None:
        self.assertEqual(len(self.grid.search("edge.gpio.write")), 1)
        self.bridge.exchange(self.session, 100, False)
        self.assertEqual(self.grid.search("edge.gpio.write"), [])
        self.assertEqual(self.bridge.state()["pico"], "unknown/degraded")
        self.bridge.exchange(self.session, 100, True)
        self.now += 3
        self.assertEqual(self.grid.search("edge.gpio.read"), [])
        with self.assertRaises(PermissionError):
            self.queue()

    def test_permission_confirmation_policy_and_target_scope(self) -> None:
        for granted, confirmed in ((frozenset(), True), (frozenset({"edge.gpio.write"}), False)):
            with self.assertRaises(PermissionError):
                self.bridge.queue("edge.gpio.write", 1, 1, granted=granted, confirmed=confirmed)
        self.queue()
        self.policy.save(
            PolicyRule("deny", "edge.gpio.write", PolicyEffect.DENY, "owner", 100, 100, {}),
            owner_authorized=True,
        )
        self.assertIsNone(self.bridge.exchange(self.session, 100, True))
        with self.assertRaises(PermissionError):
            self.queue()
        self.grid.revoke("desk-edge")
        with self.assertRaises(PermissionError):
            self.bridge.exchange(self.session, 100, True)

    def test_queue_expiry_reboot_and_receipt_evidence(self) -> None:
        self.queue()
        with self.assertRaises(ValueError):
            self.queue()
        raw = self.bridge.exchange(self.session, 100, True)
        assert raw
        frame = Frame.decode(raw)
        receipt = Frame(Kind.ACK, frame.session, frame.sequence, frame.channel, 1).encode()
        self.bridge.exchange(self.session, 100, True, receipt, simulated=True)
        self.bridge.exchange(self.session, 100, True, receipt, simulated=True)
        evidence = [e for e in self.store.ledger("") if e["event"] == "edge_receipt"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["evidence"], "SIMULATED")
        self.queue()
        self.now += 1
        self.assertIsNone(self.bridge.exchange(self.session, 100, True))
        self.queue()
        self.assertIsNone(self.bridge.exchange(self.session, 101, True))

    def test_event_provenance_replay_and_bounded_channels(self) -> None:
        raw = Frame(Kind.EVENT, 100, 1, 2, 123).encode()
        self.bridge.event(self.session, raw, simulated=True)
        self.bridge.event(self.session, raw, simulated=True)
        self.assertEqual(len([e for e in self.store.ledger("") if e["event"] == "edge_event"]), 1)
        with self.assertRaises(ValueError):
            self.bridge.event(self.session, Frame(Kind.EVENT, 100, 1, 2, 124).encode())
        with self.assertRaises(ValueError):
            self.bridge.queue("edge.gpio.write", 15, 1, granted=frozenset(KINDS), confirmed=True)

    def test_real_loopback_exchange_and_auth_denial(self) -> None:
        listener = server(self.bridge, ("127.0.0.1", 0), simulated=True)
        thread = Thread(target=listener.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(listener.server_close)
        self.addCleanup(listener.shutdown)
        self.queue()
        url = f"http://127.0.0.1:{listener.server_port}/edge/v1/exchange"
        raw = (100).to_bytes(4, "little") + b"\x01" + bytes(40)
        headers = {
            "Authorization": "Bearer " + self.session.token,
            "X-OSCAR-Session": self.session.id,
        }
        with urlopen(Request(url, raw, headers), timeout=3) as response:
            self.assertEqual(Frame.decode(response.read()).kind, Kind.GPIO_WRITE)
        with self.assertRaises(HTTPError):
            urlopen(Request(url, raw, {**headers, "Authorization": "Bearer wrong"}), timeout=3)
        with self.assertRaises(ValueError):
            server(self.bridge, ("0.0.0.0", 0))

    def test_core_restart_fences_pending_and_preserves_sequence(self) -> None:
        action = self.queue()
        prior = self.bridge.pending
        assert prior
        replacement = EdgeBridge(self.grid, self.policy, "desk-edge")
        self.assertIsNone(replacement.pending)
        self.assertIsNone(replacement.exchange(self.session, 100, True))
        receipt = Frame(Kind.ACK, 100, prior.frame.sequence, 1, 1).encode()
        replacement.exchange(self.session, 100, True, receipt)
        replacement.queue(
            "edge.gpio.write", 1, 0, granted=frozenset({"edge.gpio.write"}), confirmed=True
        )
        assert replacement.pending
        self.assertGreater(replacement.pending.frame.sequence, prior.frame.sequence)
        evidence = [e for e in self.store.ledger("") if e.get("action_id") == action]
        self.assertEqual(evidence[-1]["status"], "unknown")

    def test_delivery_rechecks_scoped_session_and_expiry(self) -> None:
        self.queue()
        read_session = self.grid.pair("desk-edge", ("heartbeat", "advertise", "edge.gpio.read"))
        with self.assertRaises(PermissionError):
            self.bridge.exchange(read_session, 100, True)
        self.now += 86401
        with self.assertRaises(PermissionError):
            self.bridge.exchange(self.session, 100, True)


if __name__ == "__main__":
    unittest.main()
