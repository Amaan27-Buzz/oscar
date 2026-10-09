# Consolidated Gate C embodiment acceptance

Status: **DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED**.
Gate C remains **PARTIAL**. Software/reference closure is not physical PASS.
Owner decision: 2026-10-06. Run after the relevant embodiments exist, without
repeated isolated device interruptions during software foundation work.

## Retained acceptance requirements

1. Real Windows microphone/capture, wake/VAD and improved local STT on owner speech.
2. Preferred neural OSCAR voice/playback, pronunciation, consistency, pauses,
   rhythm and sentence modulation: owner listening/naturalness review.
3. Real-room echo/AEC, human barge-in/stop latency, preserved human prefix and
   own-output/self-wake suppression; test headset/speaker and quiet double-talk.
4. Owner Voice Match enrollment/negative/uncertain cases and separately permitted
   Voice Map linkage/unknown/change/multiple-speaker behavior; no authority from Map.
5. OSCAR Mobile/Android microphone, playback, background/lifecycle/permission revocation,
   audio focus, Bluetooth/headset routing and supported native AEC on target OEM.
6. Grid handoff/arbitration, stale/lost node/lease expiry/reconnect, remote task
   inspect/approve/cancel, Android biometric/PIN boundary and degraded/offline UI.
7. One real supported communication/reply path with explicit permission and readback.
8. Later Desktop Interaction integration, plus the retained physical Edge failure,
   recovery/watchdog/safety acceptance in Slice 18/19 before Slice 20 PASS.

## Evidence and tools

Retain [Voice Core owner harness](VOICE-CORE.md#exact-windows-owner-acceptance),
`scripts/voice_owner.py`, `scripts/voice_setup.py`, Voice/Edge regressions and
[physical Edge guide](EDGE-HARDWARE-ACCEPTANCE.md). No model weights, raw owner
speech, generated WAVs or enrollment embeddings enter Git.

Record endpoint/device/OS/model revision, permission scope, source/observation
 time, latency, authoritative resulting task state and limitations for each step.
Use SIMULATED for deterministic simulations, REFERENCE for fixture/model runs,
REPORTED for unverified transcripts/provider messages, VERIFIED only for observed
resulting state, and DEFERRED_BY_OWNER for these pending physical tests.

Windows evidence does not imply Android or room acceptance. Naturalness remains
`REFERENCE / OWNER_NATURALNESS_ACCEPTANCE_NOT_RUN` until owner listening. Failures
must be repaired or explicitly rescoped by the owner; no fabricated PASS.

Operating Logs, specialist training and home-server migration remain future
[post-alpha work](POST-ALPHA-EVOLUTION.md), not part of this acceptance deferral.

## OSCAR Mobile rebuilt application acceptance

The active app is OSCAR, package io.dawnlight.oscar.mobile. Historical Sunday
evidence is preserved; its UI is retired. Use the prepared
[Mobile owner checklist](MOBILE-OWNER-ACCEPTANCE.md) during the consolidated owner
run. Pairing, biometrics/PIN, Android permission interactions, assistant selection,
notification replies, physical audio/Bluetooth/AEC and Match/Map remain
OWNER_DEVICE_ACCEPTANCE_NOT_RUN. Emulator/software tests never promote Gate C PASS.
