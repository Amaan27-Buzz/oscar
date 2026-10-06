# Slice 09 Sunday Android foundation

Status: **PARTIAL / SOFTWARE_FOUNDATION_IN_PROGRESS**. No physical Android acceptance.
Branch: `club-c/slice-09-sunday`, draft PR into `work`; do not merge this slice.
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
