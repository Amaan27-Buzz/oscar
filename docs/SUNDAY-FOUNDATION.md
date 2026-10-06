# Slice 09 Sunday Android foundation

Status: **PARTIAL / INITIAL_SOFTWARE_FOUNDATION_IMPLEMENTED**. No physical Android acceptance.
Branch: `club-c/slice-09-sunday`, draft PR #15 into `work`; do not merge this slice.
Accepted Slice 08 baseline: `92a11aa05083f1983186976ba64bd30aa9f1f2a0`.
Slice 08 head: `db918b508ccdec81a06d81a9cc24aff69e8aad79`, merged via PR #14.
All seven exact-head checks passed. Main/work were independently read back equal.
Gate C remains **PARTIAL**.

## Architecture and completion boundary

Sunday is a native Android embodiment and owner-control client of existing OSCAR
Grid, Controller, Runtime, Personal Policy, Memory and Voice contracts. It has no
second planner, model router, task store or memory brain. Real device pairing,
permissions, biometrics/PIN, assistant invocation, microphone/playback, AEC,
Bluetooth and notification reply behavior stop at the consolidated owner boundary.

The initial software path is a real app/project, protected session storage,
source-qualified Core state, bounded text handoff, task inspection and signed
owner approval/cancellation. The first text executor reuses existing harmless
integer-addition intent and Runtime verification; general conversation and broader
mutations remain explicit composition boundaries, not fabricated success.

Core grants are rechecked per request. Android Keystore signing and platform
biometric/device-credential confirmation bind a one-use short-lived Core challenge
to a current task/plan. A signature does not grant permission or override Personal
Policy. No public remote pairing endpoint may mint owner authority. Enrollment is
a trusted Core operation and actual owner/device enrollment is NOT RUN.

Notification perception, retention and reply authority remain independent.
Only real exposed free-form RemoteInput/PendingIntent replies may execute, after
separate Core policy and owner confirmation. Local notification state is transient;
no raw notification archive, unrestricted app access or AccessibilityService.
Offline clients do not queue approvals/sends for later automatic execution.

## Selected Android/runtime direction

- Native Java/platform Android APIs, no React Native/web brain or UI framework dependency.
- Existing local JDK 21 and Android SDK 36; min SDK 30, target/compile SDK 36.
- Pinned AGP 8.13.2/Gradle 8.13 project compatibility, plus a local SDK-native build path.
- Android Keystore AES-GCM credentials; RSA/SHA-256 owner challenge signatures.
- Platform BiometricPrompt with strong biometric/device credential confirmation.
- AudioRecord/AudioTrack, audio focus, communication-device routing and native AEC
  availability/effect binding behind portable Voice boundaries.
- Selected-assistant VoiceInteractionService/session path, notification listener
  and foreground microphone lifecycle use legitimate separately granted APIs.
- The canonical OSCAR Orb and existing Quietly Alive design language; UI state
  follows actual connectivity/task/permission state.

## Current authoritative API research — 2026-10-06

[VoiceInteractionService](https://developer.android.com/reference/android/service/voice/VoiceInteractionService)
requires user selection/system binding and does not grant unrelated permissions.
[NotificationListenerService](https://developer.android.com/reference/android/service/notification/NotificationListenerService)
and [RemoteInput](https://developer.android.com/reference/android/app/RemoteInput)
only expose supported notification/context/reply actions, not arbitrary app access.
[Microphone foreground services](https://developer.android.com/develop/background-work/services/fgs/service-types)
require RECORD_AUDIO/foreground-service permissions and while-in-use eligibility;
ordinary background/boot auto-start is restricted. No continuous listening claim.
[AcousticEchoCanceler](https://developer.android.com/reference/android/media/audiofx/AcousticEchoCanceler)
is endpoint/device dependent: availability or successful construction is not room acceptance.
[Biometric cryptography](https://developer.android.com/identity/sign-in/biometric-auth)
distinguishes CryptoObject authentication and timed device-credential authorization.
[AGP 8.13 compatibility](https://developer.android.com/build/releases/agp-8-13-0-release-notes)
supports SDK 36.1 and Gradle 8.13; this foundation uses the locally installed SDK 36.

Android/Sunday is first-class. Windows evidence never implies Android verification.
Neural inference may be on-device where a binding/model is validated, or use an
advertised authenticated Desktop/LAN capability; loss is explicit degradation.
Home-server migration, Operating Logs and specialist training remain
[post-alpha](POST-ALPHA-EVOLUTION.md), unimplemented. See the
[consolidated Gate C acceptance plan](GATE-C-CONSOLIDATED-ACCEPTANCE.md).

## Implemented initial path and actual evidence

`oscar/sunday.py` is a bounded adapter of existing Grid/Runtime/PersonalPolicy,
with no mobile task engine. The native Java app calls the same Core and shows
current source-qualified state. Native AudioRecord/AudioTrack, audio focus,
AEC availability/binding, headset routing, foreground-service and selected-assistant
boundaries compile against SDK 36. The recognizer/binding is explicitly
**not commissioned**; no on-device wake/STT/TTS or autonomous Android voice is claimed.

Session credentials use Android Keystore AES-GCM and backup is disabled. Owner
confirmation uses a Keystore RSA-PSS/SHA-256 key with MGF1/SHA-256 and 32-byte salt.
The biometric/device-credential path uses a **15-second authentication window**,
not per-use CryptoObject proof or hardware attestation. Core enrollment is trusted
and out-of-band; a signed challenge never grants missing permission. Older/OEM
PSS/MGF1 support can fail closed and is unverified until device commissioning.

Core checks current role/scopes, one-use challenge expiry, task/plan fingerprint,
policy after confirmation and target authorization. Text receipts are hash-only,
request identity changes/replays are rejected, and pending text tasks are bounded.
Snapshot, inspect, approve/cancel and reply permits use existing task/ledger state.
Approvals currently execute only the adapter's harmless addition plans; inspection
and cancellation reuse existing controlled target state. Broader consequential
approval and conversational/recall composition are not implemented by this client.

Notification context defaults OFF with an explicit package allowlist. Retention is
OFF. Reply authority is a separate switch plus Core communications/reply grants,
Personal Policy and signed owner confirmation. The target rechecks the current
notification/content/action fingerprint, real free-form RemoteInput/PendingIntent,
permit lifetime and one-use consumption. A send accepted by Android is only
**REPORTED / delivery NOT_VERIFIED**. No actual notification send was run here.

The native app follows the canonical Orb SVG unchanged, native controls and the
existing warm design world. It retains no second chat/task database, rejects
untrusted/cleartext remote origins, uses no redirect/mutation retry, and fences
background/stale UI requests. Local disconnect is not remote revocation.

[Nonprivate evidence](evidence/sunday-reference-2026-10-06.json):

- local SDK/JDK compile, DEX, APK packaging, debug signing/verification and exact
  Orb bytes PASS; this is a reference APK, not a production signing/release claim;
- six real Core/loopback security cases PASS with pinned cryptography 50.0.2;
- shared Java/Python RSA-PSS interoperability led to independently VERIFIED Core
  result 5, using a synthetic JVM key (not Android owner biometrics/Keystore signing);
- local full regression 489 tests PASS, seven optional/platform checks skipped;
- Ruff/format/strict mypy/repository/local links/secret/diff checks PASS;
- isolated temporary Android 36.1 emulator launched the native app, saved an
  encrypted scoped session (plaintext token/origin absent from preferences),
  restored it after process restart, created a planned Core task from text and
  displayed verified result/evidence readback. These are **EMULATED / REFERENCE**;
- portrait was visually inspected; landscape capture/behavior remains unverified.

The original AVD was full and was left untouched. A fresh temporary AVD needed
three-button navigation to avoid its image's `mapper.ranchu` / RegionSampling
`hasReadColorBufferDma` assertion. This was an isolated emulator workaround;
Sunday does not change navigation on real phones and no OEM support is inferred.

## Reproduce without touching an owner phone

```powershell
py -3.12 -m venv .tmp/sunday-env
.tmp/sunday-env/Scripts/python.exe -m pip install '.[dev,sunday]'
.tmp/sunday-env/Scripts/python.exe -m unittest tests.test_sunday -v
.tmp/sunday-env/Scripts/python.exe -m scripts.sunday_reference
python -m scripts.build_sunday
```

The SDK-native build uses installed SDK 36/build-tools 36.0.0/JDK 21, writes a new
ignored `.tmp/sunday-sdk-*` output and verifies the reference APK. The Gradle
8.13/AGP 8.13.2 project is configured; **Gradle execution was NOT RUN locally**.
`--serve-emulator-fixture` creates an explicitly temporary software-only Core,
synthetic scoped session and bounded 15-minute loopback fixture. It is not deployment,
production enrollment or a permanent development-laptop host. No real credentials
are borrowed; fixture tokens, private keys, APKs and screenshots stay out of Git.

## Next genuine owner/device boundary

No owner action is required during this software run. Later consolidated acceptance
requires a trusted real Core origin/TLS and registered phone public key/session,
then owner interaction on the actual phone for lock/Keystore/PSS support,
biometric/PIN signing, assistant selection/invocation, permission grant/revocation,
notification sources and one legitimate reply/readback, foreground lifecycle,
headset routing and voice runtime commissioning. Android microphone/playback,
room AEC, barge-in/self-wake, Match/Map, naturalness and Grid handoff/arbitration
remain required and NOT RUN on real hardware. Surface recognition is not authority.
Slice 09 remains PARTIAL/draft. Do not merge it. Gate C remains PARTIAL.
