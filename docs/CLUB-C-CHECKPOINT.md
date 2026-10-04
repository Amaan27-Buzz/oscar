# Club C checkpoint

## Baseline

Club C starts only after Gate B PASS.

Accepted baseline:

- `main` and `work` synchronized at `97c0622507df3f724ecf0c8b74aa7f4ae7784b08`;
- Gate A PASS;
- Gate B PASS for the documented local-alpha scope;
- Slice 05 COMPLETE;
- Slice 06 COMPLETE;
- owner physical machine acceptance PASSED;
- owner GitHub OAuth/private federation acceptance PASSED.

Historical Gate B evidence remains in `docs/GATE-B-COMPLETION.md` and `docs/evidence/`.

## Current scope — Slice 07

Slice 07 is **OSCAR Edge + reflexes**.

Planned acceptance scope:

- ESP32 gateway/client;
- Pico deterministic controller where used;
- typed ESP32↔Pico events;
- health/capability advertisement;
- GPIO/sensor/display test capabilities;
- watchdog and safe defaults;
- deterministic reflex/emergency-stop path;
- reconnect/offline behavior;
- optional LAN helper/Wake-on-LAN only when a real capability exists;
- simulator coverage;
- physical-device verification.

Out of scope for this slice:

- Slice 08 voice/Voice Identity/Match/Map/Persona runtime;
- Slice 09 Sunday/Android/communication owner controls;
- Slice 10 polished Desktop Interaction Runtime;
- Oracle/Vercel deployment;
- Galaxy Tab Home Node implementation;
- later Gate C acceptance claims.

## Status

- Slice 07: IMPLEMENTATION / physical acceptance pending
- Gate C: PARTIAL / not yet accepted

This checkpoint must be updated with real implementation evidence as Slice 07 progresses. Simulated behavior must not be promoted to physical verification.

## Slice 07 implementation evidence — 2026-10-05

- Starting checkpoint: `9fde9385af6b34c4f76991e2d871ab0909296af5`.
- Existing branch `club-c/slice-07-edge`, draft PR #13; no merge.
- Local Windows shared C reference built using MSVC 19.44 with warnings as errors.
- SIMULATED protocol/controller/Grid acceptance: 20 focused tests PASS.
- Existing OSCAR full regression suite: 447 tests PASS, local Python 3.14.
- ESP-IDF 6.1 and Pico SDK 2.3.1 cross-builds PASS at source revision
  `2ed47351ccf20d680cae73ff43666c7db9a37bbf` in
  [firmware CI run](https://github.com/amaansyed27/oscar/actions/runs/37228712560).
  Pico normal and watchdog variants compiled. Final PR-head checks are authoritative
  in draft PR #13; normal ESP32 artifacts are distinct from watchdog diagnostics.
- Ruff lint/format, strict mypy (51 modules), repository links/secret safety PASS.
- [SIMULATED evidence record](evidence/edge-simulated-2026-10-05.json) includes source hashes.
- Historical Gate B evidence preserved; active status reconciled with merged PR #12.
- Owner physical wiring/flash, silicon watchdog and electrical timing: NOT RUN.
- [Architecture/protocol/research](EDGE.md); [exact owner hardware guide](EDGE-HARDWARE-ACCEPTANCE.md).
- Slice 07 PARTIAL / OWNER_HARDWARE_REQUIRED; Gate C PARTIAL.
- Slices 08–10, Oracle deployment, Galaxy Tab and self-extension not started.
