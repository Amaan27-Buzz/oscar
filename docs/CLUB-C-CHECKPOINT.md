# Club C checkpoint

## Latest continuation — 2026-10-07

Slice 09 software is accepted at `7043b9663fe6474e3457c7aa578e733f7a5a4c1a`. Slice 10 now has a Windows software/reference candidate with WPF/CNG and registered Worker/UIA evidence, not owner desktop acceptance. Edge, Voice and Mobile physical acceptance remain owner-deferred and Gate C is PARTIAL. This continuation supersedes older next-slice restrictions only for the explicitly authorized Slice 10 draft. See [Desktop foundation](DESKTOP-FOUNDATION.md).

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

## Accepted Slice 07 scope

Slice 07 is **OSCAR Edge + reflexes**.

Original Slice 07 scope (physical verification is rescheduled by owner below):

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
- physical-device verification, owner-deferred to Slice 15/16.

Out of scope for this slice:

- Slice 08 voice/Voice Identity/Match/Map/Persona runtime;
- Slice 09 OSCAR Mobile/Android/communication owner controls;
- Slice 10 polished Desktop Interaction Runtime;
- Oracle/Vercel deployment;
- Galaxy Tab Home Node implementation;
- later Gate C acceptance claims.

## Status

- Slice 07: COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION; physical DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED
- Gate C: PARTIAL / not yet accepted

This checkpoint must be updated with real implementation evidence as Slice 07 progresses. Simulated behavior must not be promoted to physical verification.

## Historical Slice 07 implementation evidence — 2026-10-05

The pre-rescope observations below are preserved; the owner decision supersedes
the historical status and scope restrictions, not the recorded evidence.

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
The 2026-10-05 scope authorized Slice 08. The 2026-10-06 owner decision additionally
authorizes Slice 09 software after Slice 08 integration; Slice 10, deployment and
Galaxy Tab Home Node remain outside this work.

## Slice 08 owner closure scope — 2026-10-06

Owner-authorized closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
This is not a physical PASS. Gate C remains **PARTIAL**.
Slice 08 PR #14 integrated after green exact-head CI. Accepted main/work:
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Historical reference research baseline:
`e8ac8f8bca1cb0cb7909523ac6af906ee289366f`.
Existing owner harnesses remain mandatory inputs to later consolidated acceptance.
Microphone, real-room AEC/barge-in/self-wake, owner Match/Map calibration, playback,
Android voice and naturalness remain NOT RUN. Windows reference evidence never
implies Android acceptance. See [Voice Core](VOICE-CORE.md) and
[consolidated Gate C acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 OSCAR Mobile software may begin after clean Slice 08 integration; Slice 09 must
remain a draft and stop before owner/device acceptance. Slice 10, deployment and
Galaxy Tab Home Node are not authorized. Physical Edge remains
`DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`, mandatory before Slice 17 PASS.

## Current Slice 09 — 2026-10-06

Slice 08 PR #14 merged; accepted main/work baseline
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Slice 08 is
**COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**; physical voice is
`DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`, never physical PASS.
OSCAR Mobile Kotlin/Compose rebuild is on `club-c/slice-09-sunday`, draft PR #15
into `work`, **PARTIAL / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**. Core/loopback,
Gradle/JVM/emulated evidence is separate from actual phone/OEM acceptance.
See [OSCAR Mobile foundation](MOBILE-FOUNDATION.md) for implementation, limits and the next owner boundary.
Slice 09 must not merge in this run. Gate C remains PARTIAL. Slice 10, deployment
and Home Node are not started. Post-alpha Operating Logs, specialist-model training
and home-server migration remain documented future work, not implemented.

## OSCAR Mobile owner-review candidate — 2026-10-07

Slice 09 is **SOFTWARE OWNER-REVIEW CANDIDATE / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**,
not merged. Native Kotlin/Compose application, scoped Core text/task/approval flow,
encrypted session restore and canonical Orb are source-bound in
[the rebuilt Mobile evidence](evidence/mobile-rebuild-reference-2026-10-07.json).
497 Python regressions, eight JVM checks and six isolated API 35 software cases
passed; a separate live loopback readback case passed. Android 36.1 emulator
snapshot failure remains incomplete platform evidence. Real phone, biometric,
assistant, notifications/replies and audio/voice/OEM acceptance remain deferred.
Gate C remains PARTIAL; Slice 10 and post-alpha model/server work are not started.
