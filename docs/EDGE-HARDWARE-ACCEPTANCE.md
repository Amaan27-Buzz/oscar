# Slice 07 owner hardware acceptance

**Status: DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED.** Initial Windows inventory found
no `Win32_SerialPort` devices; that does not prove no boards exist elsewhere.
ESP-IDF and Pico SDK/toolchains were not detected in the initial shell. Host C
simulation uses installed Visual Studio 2022 Build Tools. Firmware cross-build
CI is a separate check; neither compilation nor simulation proves electrical
behavior. Stop before owner wiring, BOOTSEL, reset, flashing and observations.

## Exact reference hardware

- **Espressif ESP32-DevKitC V4 with ESP32-WROOM-32E**, not a WROVER module
  (GPIO16/17 can have different use on other modules). See official
  [DevKitC guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html).
- **Raspberry Pi Pico, original RP2040, non-W**, headered variant or soldered
  headers; `PICO_BOARD=pico`. See official
  [Pico board documentation](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/microcontrollers/pico-series.adoc).
- Two USB data cables matching those boards, two USB ports, breadboard and
  jumper wires; one LED, one 1 kΩ LED resistor, one 10 kΩ pulldown resistor,
  two momentary switches, optional 10 kΩ potentiometer for ADC demonstration.
- Digital multimeter/logic analyzer strongly useful for output/reset timing.
  No relay, motor, heater, mains or other powered actuator is part of acceptance.
- Isolated 2.4 GHz WPA2 test LAN reachable from the local Core HTTPS listener.

Confirm actual markings with the owner before using this pin map. Firmware
selects ESP32 UART1 TX17/RX16 and Pico UART0 TX GP0/RX GP1. A different board
needs an explicitly reviewed pin profile and separate acceptance.

## Exact wiring (power disconnected)

| ESP32 / component | Pico / component |
| --- | --- |
| ESP32 GPIO17 (TX) | Pico GP1 (RX), physical pin 2 |
| ESP32 GPIO16 (RX) | Pico GP0 (TX), physical pin 1 |
| ESP32 GND | Pico GND, physical pin 3 |
| Pico GP15, physical pin 20 | 1 kΩ resistor → LED anode; LED cathode → GND |
| Pico GP15 | 10 kΩ resistor → GND (reset/high-impedance safe LOW) |
| Pico GP14, physical pin 19 | momentary test-input switch → GND |
| Pico GP13, physical pin 17 | momentary interlock/E-stop switch → GND |
| Pico GP26 / ADC0, physical pin 31 | optional potentiometer wiper |
| Potentiometer ends | Pico 3V3(OUT), pin 36, and AGND pin 33 |

Without the potentiometer, connect GP26 to AGND; an unconnected ADC is floating
and cannot establish a meaningful sensor value. Both boards use their own USB
power. Connect grounds only; **do not connect their 5 V/3.3 V power rails**.
Signal levels must remain 3.3 V. Firmware pull-ups hold switch inputs high.
The switch is a harmless local stop primitive for this LED, not a certified
emergency-stop installation. Owner must inspect physical wiring first.

## Windows build and flash commands

Commands assume repository root
`D:\TheDawnlightGroup\DawnlightLabs\oscar`. Install the official toolchains
under `C:\Tools` if absent; do not borrow another project's private config.
Use the official [ESP-IDF Windows installation guide](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32/get-started/windows-setup.html)
and [Pico SDK setup](https://github.com/raspberrypi/pico-sdk).
Install ESP-IDF 6.1 with its tools using Espressif's installer/EIM, and Pico's
Arm GNU Toolchain, CMake and Ninja. Cross-builds require these installed tools;
ordinary Python/CMake alone is insufficient.

ESP-IDF PowerShell (adjust the installation path only if installed elsewhere):

```powershell
Set-Location D:\TheDawnlightGroup\DawnlightLabs\oscar
& C:\Tools\esp-idf-v6.1\export.ps1
idf.py -C edge/esp32 set-target esp32
idf.py -C edge/esp32 build
Get-CimInstance Win32_SerialPort | Select-Object DeviceID,Name
# OWNER: replace COM7 with the observed ESP32 port, then flash.
idf.py -C edge/esp32 -p COM7 flash
```

Pico SDK and build, with `arm-none-eabi-gcc` on PATH:

```powershell
git clone --branch 2.3.1 --depth 1 --recurse-submodules https://github.com/raspberrypi/pico-sdk.git C:\Tools\pico-sdk-2.3.1
$env:PICO_SDK_PATH = 'C:\Tools\pico-sdk-2.3.1'
cmake -S edge/pico -B .tmp/pico -G Ninja -DPICO_BOARD=pico -DCMAKE_BUILD_TYPE=Release
cmake --build .tmp/pico
# OWNER: hold BOOTSEL while connecting Pico USB. Observe RPI-RP2 drive.
Get-Volume | Where-Object FileSystemLabel -eq RPI-RP2 | Select-Object DriveLetter,FileSystemLabel
# OWNER: replace R: with that observed drive. This writes firmware and reboots Pico.
Copy-Item -LiteralPath .tmp/pico/oscar_edge_pico.uf2 -Destination R:\
```

Local TLS acceptance fixture (replace `192.168.1.20` with the actual Core LAN
IPv4 address, which must match the provisioning URL and certificate SAN):

```powershell
New-Item -ItemType Directory -Force .oscar/edge
& 'C:\Program Files\Git\usr\bin\openssl.exe' req -x509 -newkey rsa:2048 -sha256 -nodes -days 2 -keyout .oscar/edge/core-key.pem -out .oscar/edge/core-cert.pem -subj '/CN=OSCAR Edge Acceptance' -addext 'subjectAltName=IP:192.168.1.20'
# Protect fixture credentials with an owner-only Windows ACL.
$edgeOwnerAccount = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls .oscar/edge /inheritance:r /grant:r "${edgeOwnerAccount}:(OI)(CI)F"
python -m scripts.edge_owner enroll
# Enter owner Wi-Fi settings and https://192.168.1.20:8443/edge/v1/exchange.
# An explicit one-day Grid session is generated locally; no account OAuth occurs.
python "$env:IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py" generate .oscar/edge/provision.csv .oscar/edge/provision.bin 0x6000
# OWNER: flash only the NVS partition at the standard project offset.
python -m esptool --chip esp32 --port COM7 write-flash 0x9000 .oscar/edge/provision.bin
python -m scripts.edge_owner serve
```

Confirm generated partition table has NVS `0x9000`, size `0x6000` before that
flash. The checked project uses the IDF default single-app partition table;
changing partitions requires changing this command. Keep `provision.csv/bin`,
Core database and TLS keys ignored/local. Windows Firewall may need an owner
approved private-LAN rule for port 8443; no public service or Oracle deployment
is required. If ESP32 TLS certificate validation fails due to clock/certificate
dates, preserve verification: synchronize gateway time via configured SNTP
(firmware uses the default pool) and inspect LAN reachability rather than disabling TLS.

Host simulator and existing regression checks:

```powershell
cmake -S edge/simulator -B .tmp/edge-host -G 'Visual Studio 17 2022' -A x64
cmake --build .tmp/edge-host --config Release
python -m unittest tests.test_edge -v
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m unittest discover -s tests -t . -v
python -m scripts.check_repository
```

## Short owner acceptance sequence

Record board markings, SDK/tool versions, firmware commit/artifact hashes,
wiring photograph and timestamps in an ignored local record first. The owner
console sends only commands typed by the owner; each physical mutation is an
explicit confirmation under the native PersonalPolicy boundary.

1. Inspect wiring unpowered; connect USB. LED stays OFF during boot/reset.
   Run Core console; `state` shows Desk Edge online and controller health.
2. Type `health`, then `state`; type `input`, wait, then `state`. Press/release
   GP14 switch and repeat input. Separate physical observation matches 0/1.
3. Type `on`; observe LED HIGH. Type `output`, wait, then `state` for separate
   GPIO readback. Type `off` and repeat readback. ACK alone is only REPORTED.
4. Type `sensor`; compare ADC extremes with potentiometer at GND/3.3 V, or
   grounded input near zero. Inspect `state` for source-backed sensor events.
5. Type `on`, then `reflex`: LED becomes LOW. Type `on`, then press GP13:
   LED becomes LOW locally. New HIGH requests must fail. Release switch:
   latch stays set. Only owner Pico reset with switch released clears it.
6. Type `on`; stop Core console or disconnect Wi-Fi. LED must become LOW;
   capture elapsed time. Restore Core: health/capabilities recover, LED remains
   LOW. No pending HIGH is replayed. Restart ESP32 and Pico separately; repeat.
7. Type `on`; disconnect ESP32 TX↔Pico RX. LED must become LOW within the
   1500 ms lease plus loop latency. Reconnect; no output restoration. Disconnect
   the other UART direction and verify gateway degraded/advertisement withdrawal.
8. Use the optional watchdog test builds below. Do not infer watchdog expiry from
   cable disconnect. Verify actual reset and LOW output with a logic analyzer;
   until exercised, silicon watchdog expiry remains UNVERIFIED.
9. Type `stop`: local latch holds LOW across Core and gateway reconnect. Owner
   Pico reset with interlock released can clear it; it must still boot LOW.
10. Stop the console and run `python -m scripts.edge_owner disconnect` to revoke
    the local test node/session before retaining fixture files. Removing ESP32 NVS requires an
    owner-approved erase; it is not performed automatically. Capture results as
    VERIFIED / FAILED / UNKNOWN per step, never infer whole-slice PASS.

Owner must return observations for mandatory physical scenarios. A physical
failure prevents physical acceptance and Unified Alpha PASS; a simulator result never substitutes for it.

## Explicit watchdog fault builds (owner only)

On this LED-only fixture, the Pico test build accepts GP12 pulled to GND as a
deliberate feed failure. It first forces GP15 LOW. GP11 emits a 100 ms HIGH boot
marker for logic-analyzer reset measurement; it is diagnostic only, unconnected
to any actuator. Release GP12 after observing the watchdog reset, then reflash
the ordinary build. Holding it LOW repeatedly resets the board.

```powershell
cmake -S edge/pico -B .tmp/pico-watchdog -G Ninja -DPICO_BOARD=pico -DEDGE_WATCHDOG_TEST=ON
cmake --build .tmp/pico-watchdog
# OWNER: BOOTSEL and confirm the drive again.
Copy-Item -LiteralPath .tmp/pico-watchdog/oscar_edge_pico.uf2 -Destination R:\
```

For ESP32, enable `OSCAR Edge test profile → Owner watchdog fault test` in
menuconfig, rebuild/flash, then briefly ground GPIO27 on this exact board. The
link task sends SAFE_STATE and deliberately suspends; its subscribed five-second
task watchdog must panic/reset. Capture `Task watchdog` and reset evidence in
the USB monitor; release GPIO27 to avoid repeated resets. Rebuild with the option
OFF and reflash before continuing ordinary acceptance.

```powershell
idf.py -C edge/esp32 menuconfig
idf.py -C edge/esp32 build
idf.py -C edge/esp32 -p COM7 flash monitor
```

These opt-in diagnostic pins are not runtime capabilities or remote tools.

## Owner scope decision — 2026-10-05

Slice 07: **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**.
**PHYSICAL EDGE ACCEPTANCE DEFERRED BY OWNER** — `DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`.
Protocol, firmware, Grid integration, ESP32/Pico cross-builds and deterministic
safety contracts in simulation are accepted for continuation. Historical
simulator evidence remains **SIMULATED**. No physical GPIO, watchdog, UART,
E-stop or ESP32/Pico silicon PASS is claimed. Gate C remains **PARTIAL**.

Return to real ESP32/Pico acceptance during Slice 15 physical/device expansion
and/or Slice 16 reliability/security hardening. Physical failure, loss/recovery,
watchdog and safety/reflex verification remain mandatory before Slice 17
Unified Alpha can PASS. The hardware acceptance guide is preserved.
The owner authorizes Slice 08 after Slice 07 integration; Slice 09/10, deployment
and Galaxy Tab Home Node remain outside this work.
