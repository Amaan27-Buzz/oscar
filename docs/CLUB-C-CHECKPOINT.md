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

- Slice 07: NOT STARTED
- Gate C: PARTIAL / not yet accepted

This checkpoint must be updated with real implementation evidence as Slice 07 progresses. Simulated behavior must not be promoted to physical verification.
