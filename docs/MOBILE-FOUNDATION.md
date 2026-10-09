# OSCAR Mobile — Slice 09

> **Historical implementation report, recorded during PR #15 review
> (2026-10-07).** PR #15 subsequently merged. SHA/branch/status language
> below describes the original candidate, not today's branch state.
> Current plan: [00–20](SLICE-NUMBERING.md), with Slice 11 Character,
> Slice 12 Desktop UX, Slice 13 Mobile UX, Slice 16 full Presence;
> current Mobile physical owner acceptance is still deferred.


App/product **OSCAR**; technical distinction **OSCAR Mobile**.
Branch `club-c/slice-09-sunday`, draft PR #15 into `work` is retained as the existing
review identity. Accepted main/work: `92a11aa05083f1983186976ba64bd30aa9f1f2a0`;
initial candidate `305f730ed6bd559271be3b0a2d56cf0a6f49d563`.
The former Sunday UI is retired. Its dated [reference evidence](evidence/sunday-reference-2026-10-06.json)
is historical, not acceptance of the rebuild. Gate C **PARTIAL**;
**OWNER_DEVICE_ACCEPTANCE_NOT_RUN**.

## Architecture

`OSCAR Mobile UI / Android adapters ↔ scoped Grid session ↔ OSCAR Core`.
Core owns identity, canonical memory, Controller, policy, routing, tasks, authority
and evidence. The phone owns Android UI, permissions, confirmation, notifications
and audio/device lifecycle. No phone brain, model router or private task archive.

Project `mobile/`, module `:app`, namespace/application ID
`io.dawnlight.oscar.mobile`, launcher **OSCAR**. Compile/target SDK 36, min API 30,
Java 17 bytecode, AGP 8.13.2, Gradle 8.13, Kotlin/Compose compiler 2.3.20,
Compose BOM 2026.03.00, Activity 1.12.4, Lifecycle 2.10.0, coroutines 1.10.2.
Pinned compatible baseline, not a claim all versions are newest.

`MainActivity` only composes the app and foreground lifecycle. `CoreSession` owns
transient session/readback StateFlow and bounded jobs. Typed `MobileState` validates
remote payloads. `OwnerConfirmation` owns platform authentication. Useful Java
Keystore/signing, notification and audio adapters remain. Screen composables accept
state/actions independently; Core does not depend on Compose or visual composition.

## Navigation and surfaces

Four primary destinations: **OSCAR / Activity / Devices / Settings**. Contextual
approval dialogs; Voice, Privacy, Notifications, Android presence and About are
Settings sections. Navigation restores across recreation; credentials, input and
interaction text are excluded from saved instance state.

- **OSCAR:** canonical Orb, actual connection/task presence, text input, progressive
  request state, voice entry, contextual request indicator and task/result readback.
  No thread management or dominant chatbot bubbles.
- **Activity:** Core task states, inspect, evidence/result distinction and advertised
  approve/deny/cancel/retry. Retry restores a plan; another fresh signed approval
  executes it. Completed/cancelled tasks cannot silently execute again.
- **Approvals:** what, why, Core/capability, target, consequence, policy and one-use
  biometric/PIN requirement. Confirmation grants no permanent authority.
- **Devices:** current node state, pairing and available capabilities. Offline nodes
  withdraw execution; no invented Home Node, wake or power controls.
- **Voice:** accepted logical identity, real OS microphone/routing permission,
  unavailable Android binding/Match/Map and explicitly saved preference intent.
- **Privacy:** separate **can perceive / can retain / can act**, notification
  allowlist, microphone perception and reply grants. Raw retention off; unconfigured
  location/camera/Sentry remain unavailable.
- **Settings:** native, restrained controls, accessibility settings, public identity,
  local disconnect, platform selection and acceptance/about state.

Text passes through the existing Core Controller. Permitted addition, model
reasoning and live retrieval use advertised Core capabilities and their actual
grants; unsupported/unavailable routes return BLOCKED. Each executable proposal
requires scoped signed approval. Reasoning responses stay REPORTED, separate from
independently verified results. Mandatory memory/live retrieval cannot silently
fall back to stale reasoning. No phone model/planner or invented recall is added.
Pending tasks persist in Core. Progress is real operation/task state, not synthetic
token streaming. General conversational memory composition and production remote
hosting still depend on commissioned Core capabilities, not an app UI promise.

## Security, lifecycle and degradation

Core rechecks role/scopes per request. HTTPS required; only debug loopback HTTP
allowed. No redirects or automatic mutation retries; bounded requests/responses
and strict task/node/challenge decoding. Core owns canonical cancel/verification.

Keystore AES-256-GCM seals scoped credentials; backup disabled and sensitive screen
content excluded from screenshots/task previews. RSA-PSS/SHA-256, MGF1/SHA-256,
32-byte salt signs exact Core challenge bytes. Strong biometric or device credential
opens a 15-second Keystore authentication window, not per-use CryptoObject proof or
hardware attestation. OEM support may fail closed. Enrollment is trusted Core-only.

Nonce/session/scope/expiry/task-plan generation fences are one-use. Policy and
target authority are checked again after signature. Hash-only receipts reject
duplicate/mismatched mutations. Hash-only admission is reserved before mutation;
after a crash the caller must inspect, never blindly replay. Long-running existing
Core execution occurs outside admission locking so inspect/cancel remains available.
Execution is fenced to the exact reviewed target. Old source/operation Personal
Policy rules still constrain renamed decisions. Local disconnect deletes credentials; remote
revocation remains separate.

Leaving foreground cancels polling, transport and pending confirmation, clears
transient snapshot/interaction/approval and advances the local epoch. Stale callbacks
cannot restore authority. Resume reads fresh Core state. No offline approval/send
queue. Stop waiting locally does not claim to stop remote execution; inspect before
retry. Core/cloud/desktop loss is explicit degraded/unavailable state. No background
push/rendezvous deployment or persistent-phone reasoning is claimed.

## Notifications, assistant and Voice

Owner-visible task alerts derive only from observed Core transitions, separate
local preference and Android notification permission/channel. Generic private
content opens current inspection. Polling is foreground-only.

Listener access is explicit, source-allowlisted and transient. Only real free-form
RemoteInput/PendingIntent replies with the correct creator/source may execute.
Current content/action fingerprint, permit expiry/text hash, local grants and
one-use consumption are rechecked. Handoff **REPORTED / delivery NOT_VERIFIED**.
There is no unrestricted source-app access or Accessibility automation.

Selected assistant role / VoiceInteractionService opens the same surface. Recognition
explicitly reports unavailable until commissioned. Overlay/widgets are documented,
unimplemented; OEM invocation/background behavior awaits device acceptance.

Canonical `assets/brand/oscar-orb.svg` is packaged byte-for-byte. Native Compose displays
a deterministic 2x PNG render of that unchanged SVG, preserving gradients/shadow and
geometry. `mobile/orb-render.json` binds both digests; builds reject stale artwork.
`scripts.render_mobile_orb` is an optional maintainer render tool, not a runtime browser.
This replaces the failing WebView renderer; no artwork is redrawn/reinterpreted.
Nine-state hooks: idle, attentive, listening,
thinking, speaking, waiting, muted, unavailable, error/attention. Current mapping uses
only justified connection/task states. Expressive Orb/character design is now Slice 11; full cross-device Presence is Slice 16. Native Mobile experience redesign is Slice 13. See [canonical numbering](SLICE-NUMBERING.md).

AudioRecord/AudioTrack, focus/session, native AEC availability, headset routing and
user-started microphone foreground service remain portable Voice adapters. Android
binding is absent; microphone/STT/TTS is not fabricated. PCM origin/reference and
separate capture/output generations preserve suppression/barge-in boundaries.
Windows reference is never Android/room acceptance. No Elocution inspection or work.

## Rename and rollback

Active project/package/docs/scripts/workflow names migrate. Legacy Python imports,
NodeRole.SUNDAY, `sunday_*` database keys, scoped enrollment aliases and `/v1/sunday`
remain compatibility contracts to preserve keys, challenge consumption and replay
fences. New enrollments use NodeRole.MOBILE, `mobile:*`, `/v1/mobile`.

The new application ID is a separate security principal and cannot read the retired
app's Keystore/preferences. No secret copy or silent authority migration. Later
owner commissioning issues/enrolls a new scoped identity and revokes the old one.
This run does not uninstall the owner's app. Rollback can restore source/APK for
inspection, never revive revoked grants or erase consumed challenges. No history
or database rewrite occurs; dated evidence retains its original names.

## Checks and owner boundary

```powershell
python -m pip install '.[dev,mobile]'
python -m unittest tests.test_mobile tests.test_grid -v
python -m scripts.mobile_reference
python -m scripts.build_mobile
```

Gradle runs JVM tests, app/test APK compile and Android lint, then compares packaged
Orb bytes. `mobile/gradlew connectedDebugAndroidTest` exercises software navigation,
restoration, unavailable voice/Core and sealed credentials. JVM/Core signing uses
synthetic temporary keys. Generated APKs, credentials, captures/emulators are ignored.

See [mobile owner acceptance](MOBILE-OWNER-ACCEPTANCE.md) and preserved
[consolidated Gate C acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md). Physical pairing,
biometric/PIN, listener/replies, assistant selection, microphone/playback, Bluetooth,
real AEC/barge-in, Match/Map and naturalness are NOT RUN. Gate C cannot PASS before
required real embodiment acceptance succeeds.

## Official API research — 2026-10-06

- [Compose setup](https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler),
  [AGP compatibility](https://developer.android.com/build/releases/agp-8-13-0-release-notes).
- [Assistant role](https://developer.android.com/reference/android/app/role/RoleManager),
  [VoiceInteractionService](https://developer.android.com/reference/android/service/voice/VoiceInteractionService).
- [Notification permission](https://developer.android.com/develop/ui/compose/notifications/notification-permission),
  [reply actions](https://developer.android.com/develop/ui/compose/notifications/create-notification),
  [NotificationListenerService](https://developer.android.com/reference/android/service/notification/NotificationListenerService).
- [Foreground restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start),
  [native AEC](https://developer.android.com/reference/android/media/audiofx/AcousticEchoCanceler),
  [widgets](https://developer.android.com/develop/ui/views/appwidgets/overview),
  [overlay permission](https://developer.android.com/reference/android/provider/Settings).

[AndroidX Test release notes](https://developer.android.com/jetpack/androidx/releases/test)
were checked on 2026-10-07. Espresso 3.7.0 is explicitly pinned for the Android 16
InputManager compatibility fix; it is test infrastructure only.

Operating Logs, Elocution/model research, specialist/Singularity training and
home-server migration remain post-alpha only. Slice 10 is not started.

## Owner-review candidate evidence — 2026-10-07

**SOFTWARE OWNER-REVIEW CANDIDATE / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**.
PR #15 remains draft and unmerged; main/work remain the accepted Slice 08 baseline.
[Source-bound evidence](evidence/mobile-rebuild-reference-2026-10-07.json) records:

- 497 Python regressions PASS, nine optional/platform checks skipped; 13 Mobile
  Core/security cases include existing Router reasoning, concurrent cancellation,
  legacy policy constraints, replay, crash admission and scoped target execution.
- Eight JVM checks PASS, including actual Core snapshot decoding; APK/test-APK,
  Android lint (zero errors), packaged SVG bytes/native-render digests PASS.
- Six software cases PASS on isolated API 35, plus one explicitly configured live
  loopback/Core readback case PASS. The opt-in case is skipped without its disposable
  fixture. Native Keystore AES-GCM storage is EMULATED, not owner signing acceptance.
- Actual app pairing, Core task submission, scoped approval details, process restart
  and encrypted session/task restore PASS in the disposable emulator. Task 4 + 5
  remained planned; no biometric/PIN confirmation or phone-side execution is claimed.
- Canonical Orb visibly renders through native Compose; the renderer/export tool
  preserves the original SVG geometry, gradients and shadow.
- API 36.1 testing was interrupted by the installed image's native task-snapshot
  crash (`hasReadColorBufferDma`); five cases completed before abort. This remains
  INCOMPLETE_PLATFORM_FAILURE, not API 36.1 or real-device PASS.

Exact final-head checks are authoritative in [PR #15](https://github.com/amaansyed27/oscar/pull/15).
Emulator/software/reference results never satisfy the deferred physical owner gate.
