# OSCAR Edge — Slice 07

Current scope: Core/Grid → ESP32 gateway → UART → Pico deterministic controller.
These boards are Edge nodes, never Core hosts. Gate A/B remain frozen PASS.
Slice 07 is PARTIAL until owner physical acceptance; simulator success cannot
complete this slice. Voice, Sunday/Android, Desktop Interaction, deployment and
Galaxy Tab work are excluded. Wake-on-LAN is not advertised or implemented.

## Framework and link decision

Official sources retrieved 2026-10-05:

- [ESP-IDF 6.1 release](https://github.com/espressif/esp-idf/releases/tag/v6.1)
  and [Pico SDK 2.3.1 release](https://github.com/raspberrypi/pico-sdk/releases/tag/2.3.1)
  are the pinned reference frameworks. ESP-IDF supplies native Wi-Fi/TLS,
  bounded UART buffers and FreeRTOS tasks without an Arduino layer. Pico SDK
  keeps GPIO, ADC, timing and watchdog local with minimal C dependencies.
- [UART driver](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32/api-reference/peripherals/uart.html),
  [I2C driver](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32/api-reference/peripherals/i2c.html),
  [SPI driver](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32/api-reference/peripherals/spi_master.html)
  and [Pico hardware APIs](https://github.com/raspberrypi/pico-sdk/tree/2.3.1/src/rp2_common)
  informed the comparison below. This is an engineering choice for a short desk
  link, not a universal transport preference.

| Link | Advantages here | Costs here | Decision |
| --- | --- | --- | --- |
| UART, 3.3 V, 115200 8N1 | TX/RX/GND, full duplex, unsolicited controller events, independent clocks, simple capture | explicit framing/CRC, bounded receiver and loss detection needed | selected for short reference wiring |
| I2C | two signal wires, addressed peripheral ecosystem | pull-ups, shared/open-drain bus, controller normally polls, stuck-bus recovery | better for gateway sensors than safety-controller peer link |
| SPI | high bandwidth, clocked transfers | clock/select plus data wires, master scheduling and extra event-ready signal/polling | unnecessary bandwidth/coordination for 20-byte commands |

UART is not galvanically isolated or suitable for arbitrary long/noisy wiring.
CRC detects corruption; it does not authenticate a physically compromised link.

## Shared wire contract

[`edge.h`](../edge/protocol/edge.h) is the wire constant source of truth.
The Python codec's contract test checks numeric kinds/version/size against it.
Firmware and host reference compile the same codec, streaming parser and Pico
controller. There is no second safety engine in the simulator.

| Offset | Bytes | Meaning |
| --- | ---: | --- |
| 0 | 2 | ASCII `OE` |
| 2 | 1 | protocol version, exactly 1 |
| 3 | 1 | message kind |
| 4 | 4 | nonzero gateway boot/session ID, little endian |
| 8 | 4 | nonzero sequence/correlation ID, little endian |
| 12 | 2 | configured logical channel, little endian |
| 14 | 4 | unsigned value, little endian |
| 18 | 2 | CRC-16/CCITT-FALSE over bytes 0–17, init FFFF/poly 1021, little endian |

Fixed maximum and exact frame size: **20 bytes**. Kinds 1–13:
HELLO, HEALTH, CAPABILITIES, GPIO_READ, GPIO_WRITE, SENSOR_SAMPLE, EVENT,
SAFE_STATE, REFLEX_TRIGGER, E_STOP, ACK, ERROR, DISPLAY. No arbitrary pin numbers
or unbounded strings are accepted by Pico. HELLO value is protocol version 1.
HEALTH bits: bit 1 stop latched, bit 2 output HIGH. CAPABILITIES bitmap 0x3F
identifies this fixed reference profile (input/output/sensor/LED/reflex/stop).
ERROR value 1 is a rejected request; it never acknowledges a mutation.

Logical channel 0 = digital input, 1 = configured harmless output/status LED,
2 = raw ADC sample (0–4095 on reference Pico). Reads require value 0; output
and display accept only 0/1. Reflex/safe/stop use channel/value 0.
EVENT reports channel 0 input change, channel 1 stop-latch value 2, or channel 2
ADC sample. Gateway assigns a monotonic event correlation sequence per boot so
a Pico reset cannot collide with earlier Core event identifiers. Events carry an independent sequence space, not an action ACK.
Source wall-clock timestamp is unavailable on Pico; Core records receipt time
and preserves device evidence as REPORTED rather than current VERIFIED truth.

The parser resynchronizes with a sliding bounded 20-byte window and discards
partial frames after a 100 ms gap. Invalid version/kind/CRC/session/zero sequence
is silently discarded. Semantically invalid valid frames return ERROR.
Stop-and-wait uses up to three identical transmissions, each 100 ms ACK timeout.
Pico returns the cached reply for an exact last-command duplicate; conflicting
duplicates/older sequence numbers fail. Core correlation and gateway maintenance
sequence spaces are mapped separately. Sequence rollover requires a fresh
gateway boot/session; no wraparound commands are allowed.

Boot resets outputs LOW. HELLO/reconnect resets output LOW; it never restores a
prior HIGH. Pico link lease expires at 1500 ms. Only a new accepted command
refreshes it: malformed, duplicate or stale frames cannot keep output energized.
Session ID is restart fencing, not authentication. A new HELLO is trusted only
on the physically controlled reference UART. This is a low-energy prototype,
not a certified industrial safety controller.

## Gateway and native OSCAR integration

The gateway contains separate FreeRTOS link and network tasks. Link task has
higher priority; network/TLS waits cannot suppress Pico's deterministic safety.
Requests/receipts are bounded to one, event queue to eight, UART RX to 256 bytes.
Overflow drops an event/command rather than building an offline physical-action
backlog. Pico bounds serial work to 40 bytes per safety-loop iteration.

The ESP32 uses outbound HTTPS POST `/edge/v1/exchange`, pinned owner CA and no
redirects. A 45-byte request contains boot u32, healthy u8, optional 20-byte
receipt and optional 20-byte event (zeroes mean absent). Response is 204 or one
20-byte command. Headers carry explicit node identity plus the existing opaque Grid session and bearer token.
Protocol route is versioned; incompatible physical versions cannot negotiate.
Network timeout 700 ms; exchanges slower than 1000 ms cannot refresh Core
authority. Poll period 250 ms; HTTP retry backoff 250/500/1000/2000/4000 ms.
No Core response for 1000 ms means gateway emits SAFE_STATE and stops ordinary
link work; Pico independently expires its link lease if gateway/link is lost.

`oscar.edge.EdgeBridge` composes `Grid`, existing Capability contracts,
`PersonalPolicy` and the existing SQLite Action Ledger. It registers no new
framework. Owner pairing uses `Grid.pair`; firmware cannot enroll itself or
expand its permissions. Every queued operation checks owner grants and Personal
Policy; every mutation requires explicit confirmation. Delivery rechecks policy,
node/session scopes, health, boot and a one-second command expiry. Reboot/loss
discards pending work with UNKNOWN evidence. Core restart persists the sequence
fence but never replays a pending physical request. Late receipts remain UNKNOWN. No resumed backlog energizes GPIO.

The advertised test profile is `edge.gpio.read`, `edge.gpio.write`,
`edge.sensor.read`, `edge.display`, `edge.health`, `edge.reflex.status`,
`edge.reflex.test`, `edge.stop`. The adapter withdraws capabilities when the
controller is degraded; Grid heartbeat TTL removes dead gateway capabilities.
Actual physical board/profile matching still requires owner acceptance. An ACK
enters the ledger as REPORTED (or explicitly SIMULATED); it never completes a
physical objective as VERIFIED. Owner visual observation and separate GPIO
readback are required. The owner console is a local acceptance composition,
not a deployed Core or general conversational controller integration.

## Safety, watchdog and authority

Reference output is only a resistor-limited LED. GP15 has external 10 kΩ
pulldown, providing LOW while reset/high impedance. GP13 pulled LOW latches
E-stop locally; firmware must be reset with the interlock released to clear it.
No remote command or HELLO clears that latch. GP14 is the harmless test input.
Reflex test only forces LOW. It cannot trigger a dangerous actuator or change
the configured rule. SAFE_STATE is LOW without clearing a latched stop.

Pico has a 1000 ms hardware watchdog, fed only by the bounded safety loop;
communication lease expiry is a separate 1500 ms software deadline. ESP32
subscribes both tasks to its five-second panic/reset task watchdog. Idle/interrupt
watchdog defaults remain enabled. See official
[ESP watchdog guidance](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32/api-reference/system/wdts.html)
and [Pico watchdog APIs](https://github.com/raspberrypi/pico-sdk/blob/2.3.1/src/rp2_common/hardware_watchdog/include/hardware/watchdog.h).
Register-level watchdog expiry, electrical timing and boot transients require
physical acceptance; the host simulator verifies safety state logic and reset
semantics, not silicon watchdog behavior.

## Provisioning, firmware versions and update boundary

Per-node one-day Grid sessions, an owner CA, node identity and Wi-Fi settings are
loaded from a dedicated NVS namespace. Missing provisioning fails closed. NVS
errors never silently erase existing credentials. The owner-invoked harness
writes ignored local NVS-generation material; never commit that CSV/bin/database
or TLS keys. The initial provisioning route is explicit local USB flashing.

ESP-IDF offers secure BLE/SoftAP provisioning; current
[network provisioning](https://github.com/espressif/idf-extra-components/tree/master/network_provisioning)
supports security schemes. This slice avoids a new wireless enrollment service:
OSCAR Grid remains pairing authority. NVS encryption, secure boot/flash encryption
and manufacturing eFuse operations need an explicit board/security commissioning
plan. They are not silently enabled or claimed proven here. Prototype physical
possession exposes credentials; use an isolated test LAN and revoke test sessions.

[ESP HTTPS OTA](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32/api-reference/system/esp_https_ota.html)
supports later signed/versioned update work. This slice uses owner USB updates
and pinned SDK versions; no remote OTA/update capability is advertised. Protocol
version mismatch fails closed and gateway project version is 0.1.0. Pico reference
is RP2040/PICO_BOARD=pico. SDK supports Pico 2 but no Pico 2 electrical/firmware
acceptance is claimed; do not substitute silently.

## Evidence and owner boundary

See [hardware acceptance](EDGE-HARDWARE-ACCEPTANCE.md) for exact parts, wiring,
Windows commands and manual observations. See [Club C checkpoint](CLUB-C-CHECKPOINT.md)
for checks and current status. Simulator scenarios must stay labeled SIMULATED.
