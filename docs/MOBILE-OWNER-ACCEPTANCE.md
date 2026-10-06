# OSCAR Mobile — consolidated owner acceptance

**Prepared only. OWNER_DEVICE_ACCEPTANCE_NOT_RUN. Gate C PARTIAL.**
Combine with [Windows/Voice/Edge acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Do not run autonomously or interrupt the owner during software implementation.

1. Install reviewed OSCAR APK on the chosen phone/OEM. Record OS/API/OEM/version
   and APK digest. Preserve retired app state until owner-approved removal/revocation.
2. Configure device lock. Show public identity from Settings → About and enroll it
   through trusted `Mobile.register_owner_key(..., owner_authorized=True)` with
   explicit owner authorization. Issue narrow `mobile:*`, heartbeat and per-target
   control scopes with expiry. HTTPS outside isolated debug loopback; no credentials
   in reports/logcat/source.
3. Pair, verify Core readback, encrypted storage and restart. Test expiry/revocation,
   local disconnect and independent remote revocation. Local deletion is not remote
   revocation or secure erasure.
4. Review harmless task source/target/consequence. Deny biometric/PIN and cancel
   prompt; exercise unavailable confirmation. Confirm one decision and inspect
   independent evidence. Changed generation/policy, stale challenge, wrong target
   and replay must reject without mutation.
5. Exercise approve/deny/cancel and eligible retry (fresh execution approval), node
   loss/reconnect, Core loss and process restart. No queued offline approval/send.
6. Grant/deny/revoke microphone, notifications and headset separately. Check
   perceive/retain/act isolation, allowlist/exclusions and lock-screen privacy.
7. Use only a harmless owner-authorized source notification exposing RemoteInput.
   Deny then confirm a reply; change content/action/text and expire/replay/revoke
   permit. Record handoff REPORTED until independent delivery verification.
8. Select assistant role when owner is ready. Check invocation/lock-screen/OEM
   restrictions. Overlay/widgets are unimplemented; do not mark them PASS.
9. Commission a real portable Voice Core binding before audio acceptance. Test
   microphone/playback, route/Bluetooth, native effects, real-room AEC, human
   interruption, self-wake, Match/Map calibration and owner naturalness.
10. Check portrait/landscape, large font/TalkBack, keyboard/insets, navigation,
    alerts, background/foreground and privacy. EMULATED stays separate from physical.

Every item records source/time/exact candidate/expected/actual/evidence class.
Failed, unknown and deferred items stay explicit. Emulator/navigation success
cannot promote the consolidated Gate C to PASS.
