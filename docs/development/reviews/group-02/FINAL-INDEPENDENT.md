# Group 2 — fresh independent adversarial review

Date: 2026-10-11. Base `dcfd31bca6fbd8080f4c20bebe3d448e4bd8dc2f`.
Reviewed candidate: checkpoint `5b1c3ec4904626d7aaaee0d6f65f5d0d22951ec7`
plus the Slice 13.8 worktree and corrections below. This review is separate from
the prior sub-slice reviewer.

## Capture-first assessment

Before reading implementation summaries, this reviewer opened actual curated
native captures: 13.3 full approval and cancelled readback, 13.4 Grid, 13.5 denied
Voice, 13.6 Privacy, 13.7 Accessibility/Platform, and 13.8 dark large-text/IME.
These are API35 reference emulator renders; synthetic requests, Persona preview
and test-controlled font state do not become physical phone or owner acceptance.

The native hierarchy is coherent: a single shared character, restrained warm/dark
surfaces, readable exact consequential review, compact device rows with disclosed
details, and clear unavailable permission/runtime states. The full review exposes
request, plan, consequence, actual target and permission scope before confirmation.
The Grid capture does not present its Desktop-origin task as phone-owned execution.
Privacy separates perception, retention and action. Unsupported platform features
and uncommissioned Voice are explicit rather than fabricated working toggles.

Advisory reference score: **7.5/10 visual hierarchy, 7/10 interaction clarity**.
This is a critique, not a completion threshold. Voice and Platform use long
engineering explanations; tighter progressive disclosure would improve everyday
use. Static captures do not establish natural motion, sustained use, TalkBack
experience, owner preference or acoustic quality.

## Findings and correction status

- **P2, demonstrated: selected light navigation text contrast.** The reviewed
  light secondary `#1D6FD6` against paper `#F5F1E7` computes **4.333:1** using
  WCAG sRGB relative luminance. Default button text is below the 4.5:1 normal-text
  threshold. Reported promptly and corrected to `#1B68C8`; independently
  recalculated **4.823:1**, PASS. Dark secondary is 8.426:1 and body secondary
  text is 5.653:1. Resolved in Slice 13.8.
- **P2, corrected evidence gap: actual IME visibility.** The first large-text IME capture
  contains no visible keyboard. `performTextInput` plus text assertion alone does
  not prove Android IME/inset handling. Requested actual keyboard visibility,
  insets and actionable controls in the final native matrix. Independently opened
  final narrow and landscape actual UiAutomation captures: both show Android's
  keyboard, the field above it and usable wrapped navigation. Test code now
  asserts actual IME visibility plus field bounds against keyboard top. Matrix
  logs PASS at 720x1280/320dpi, 1280x720/160dpi and 1280x1800/160dpi with app font
  scale 1.8. No broken keyboard behavior was demonstrated.
- **P2, investigated and corrected: fixed-row controls under large text.** Voice
  Start/Cancel and Activity Inspect/Review initially used fixed Rows. Requested
  native narrow/large-font coverage and wrapping. Voice/Presence/Activity filter
  and action controls now use FlowRow; actual narrow Voice capture shows Start
  and Cancel wrapped and readable, landscape shows them side by side. Matrix
  verifies cancellation preserves the text draft. No overflow was asserted from
  source inspection alone; Activity action wrapping was source-reviewed.
- **P2, demonstrated: dark system status icon contrast.** Actual dark IME
  captures showed black clock/status icons on dark app background. The reviewer
  and implementer independently identified the system-theme versus app-theme
  mismatch. OscarTheme now sets platform system-bar light-icon appearance from
  its actual dark preference/System state. Independently opened the corrected
  actual-window `13-8-ime-large-text-reference.png`: clock/status icons are white
  on dark, keyboard visible, field above it. Resolved.
- **P2, fixture protection:** the legacy `MobileEmulatedTest` writes and forgets
  the app credential vault and changes local grants. Requested the same emulator
  admission guard as new native test classes, preventing fixture code from
  running on an owner phone. The same `ranchu`/`goldfish` guard is now present in
  that legacy class and was independently read back. Resolved. No owner phone
  was connected or used by this review. The supported runner targets only the
  isolated `emulator-5582`; direct Gradle installation/uninstallation on a physical
  phone is not an authorized acceptance path.

No unresolved demonstrated P0/P1 remains in the reviewed software/reference
scope. Demonstrated P2 contrast defects and evidence gaps above are corrected.
This does not substitute for physical checks or owner judgement.

## Authority, privacy and lifecycle review

Inspected CoreSession, CoreClient, SessionVault, MobileState, Approval,
ApprovalDialog, OwnerConfirmation, NativeVoice, MicrophoneService,
NotificationBoundary, privacy/settings controls, Home/Activity/Grid, shared
expression integration, manifest, Core Mobile/Desktop changes and reference runners.

The app keeps one ViewModel/state flow and existing serialized client; no Android
reasoning agent, duplicate task runtime or conversation-memory database was added.
Core owns task execution, memory, policy and verification. Source replacement,
foreground exit and unavailable readback retire private epochs and clear responses,
inspectors and decisions. Unsent drafts are AES-GCM sealed with origin/node/session
AAD, while source replacement and local disconnect clear recovery material.
Atomic pending-discard suppression survives restoration rather than presenting
unconfirmed Core erasure as success.

Signed review binds exact UTF8 display material, actual target/scope, private plan
digest, task generation and session. Opening a review grants nothing. Legitimate
Android confirmation is unavailable on the insecure reference AVD and fails closed;
the separate synthetic RSA reference signer is not Android/owner consent. Core
rechecks descriptor, scope, policy, expiry and replay before execution. Critical
capabilities remain rejected without verified strong confirmation.

Notification source access, allowlists and reply authority stay independent. UI
metadata hides content, exact source/content/action fingerprints reject replacement,
and native delivery rechecks current platform access plus one-use permit. Replies
are REPORTED handoff, never VERIFIED delivery. No real account/message/recording or
broad platform permission was used for these checks.

Voice capture is explicitly started, requires platform and local grants plus a
commissioned binding, and rejects delayed starts/stale service and audio epochs.
The binding is currently absent: denial/cancellation and adapter admission are
tested, but actual recognition/playback/Match/Map/audio-route accuracy are not.
The service is not exported and is non-sticky. Assistant invocation only opens
the surface. Overlay/widget runtime is absent and remains Slice16-owned.

## Independent execution

- `python -m unittest tests.test_mobile tests.test_mobile_completion_reference
  tests.test_desktop_completion tests.test_grid -q`: **57 tests PASS**, 17.779s,
  zero failures/skips. Output retained in ignored `.tmp/final-review-core-tests.log`.
- Additional independently authored assert-based Core attack reproduction:
  a private plan mutated after signed review raises `StateConflict`, leaves the
  task planned and creates no action; a second session on the same node sees no
  original request/plan and cannot approve; its discard preserves the first
  session's transient; the original-session discard removes it without implicitly
  cancelling the canonical task. **PASS**, real isolated Core/store, synthetic key.
  Script retained in ignored `.tmp/final-review-adversarial.py`. Initial direct
  script invocation lacked repository import path; execution from repository
  Python context passed without product changes.
- Independently calculated palette contrast from the actual source values;
  `.tmp/final-review-contrast.py` reproduces the ratios above.
- Canonical Orb bytes independently match the verified base, SHA256
  `728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.
- Independently inspected real three-size matrix logs (**one native case PASS**
  per size, 39s/34s/33s), matrix receipt and narrow/landscape keyboard and Voice
  captures. The matrix changes actual emulator window size/density; the app font
  scale is test-controlled. These are reference layout checks, not physical display
  acceptance. The runner restores original emulator dimensions in `finally`.
- Independently read the process-recovery runner, its test helper and receipt:
  disposable unpaired app PID **5579 -> 5621**, actual force-stop then explicit
  relaunch, encrypted unsent draft visible after replacement. This proves the
  unpaired recovery path; it is not an Android low-memory/OEM recovery simulation
  or proof of every commissioned remote-session restore. Initial harness problems
  and correction remain documented by the implementer.
- Independently read back the corrected full app native result: **25 XML cases,
  21 executed, 4 intentional skips, zero failures**, Gradle 3m. Skips are the old
  optional fixture, two opt-in process helpers and the system-animation-disabled
  case requiring separate settings. The previous full run failed two assertions:
  old Voice surface text and a draft test that appended to correctly restored
  earlier fixture text. Test expectations/isolation were corrected; neither was
  misreported as an application defect or physical PASS.
- No emulator run was launched concurrently with the parent's native matrix.
  The corrected actual window capture, three-size matrix and process receipt have
  now been independently read back.
- Fresh independent selected native rerun on API35 using a new isolated reference
  service: `MobileCompletionTest#replacementPairingAndDisconnectCannotRestoreOldSecrets`
  and `MobileEmulatedTest#disconnectedAndVoiceUnavailableNeverAdvertiseSuccess`:
  **2 PASS, zero failures/skips**, Gradle 42s. The former checks interrupted pairing,
  source-bound encrypted recovery rejection, disconnect/save ordering and stopped
  source restoration; the latter checks truthful denied/uncommissioned Voice and
  disabled send. Current legacy emulator guard compiled and did not skip this AVD.
  Output retained in ignored `.tmp/final-review-native.log`. Emulator released for
  the remaining parent expression/system-motion checks.

## Review conclusion

The reviewed software/reference candidate may proceed to its draft PR after the
remaining parent-wide gate results are recorded. No unresolved demonstrated P0/P1
or demonstrated contrast defect remains. The engineering explanations in secondary
surfaces are a UX advisory; they do not create authority or hide unsupported
functionality. Full Android Voice commissioning, Overlay/widget Presence runtime,
owner/device acceptance and critical strong confirmation remain explicitly outside
this candidate's verified capabilities.

## Acceptance boundary

Software/reference closure remains distinct from production or owner acceptance.
Carry every Group1 ledger obligation forward, especially strong critical-risk
confirmation BLOCKED, Windows foreground/DPI/assistive technology, physical Voice,
Edge safety, Android phone/OEM and distribution. Owner biometric/PIN enrollment,
real listener replies, microphone revocation during real PCM, AEC/barge-in,
Bluetooth routing and subjective motion require consolidated device acceptance.
There is no Slice14 implementation or release authorization in this review.
