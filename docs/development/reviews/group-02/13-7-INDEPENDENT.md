# Slice 13.7 independent secondary-surface review

Status: ACCEPT bounded SOFTWARE_VERIFIED / REFERENCE_VERIFIED closure after the
corrections below; no demonstrated P0/P1 in the inspected scope. This review is
independent of implementation and does not grant owner,
physical phone, OEM, audio or assistant-role acceptance.

## Actual native evidence inspected

Inspected the native `13-5-voice-denied-reference.png` and
`13-6-reference-privacy.png` captures before the detailed connected-path review.
Both are readable and preserve denied/uncommissioned states. Voice visibly says
opening the surface does not record, and provides cancellation/text continuation.
Privacy visibly separates Android permission from OSCAR perception, source
allowlisting and reply authority. The privacy still is scrolled and therefore is
not a complete cross-screen or IME acceptance artifact.

## Architecture and authority

`SecondarySettings.kt` adds only local appearance preferences, a clearly labeled
SIMULATED expression preview and read-only diagnostics. Persona preview uses the
existing shared expression renderer with a FIXTURE source. It neither stores a
persona preference nor invokes Core; its copy says explicitly that the selection
is not saved or applied. Core policy, truth, memory and authority remain unchanged.

Theme and reduced-motion settings are functional SharedPreferences controls.
Observers update Compose when preferences change. Dark/system appearance uses
actual Android system theme; OSCAR reduction and Android animation suppression are
combined. The shared renderer separately observes MotionDurationScale and suspends
with lifecycle. Held poses have no continuous frame loop; only an in-progress
transition or a single freshness deadline schedules work.

Diagnostics expose link, readback availability, task count, Android/API and actual
BuildConfig version. They expose no tokens, notification bodies, voice profiles or
private prompts. Mutable model routing, Core persona and local/cloud policy are
unavailable rather than decorative switches. Existing notification/perception
controls keep their separate grant and live-source rechecks.

The existing assistant service/session handoff opens MainActivity and does not
start recording. The recognition service truthfully reports unavailable without a
commissioned binding. Platform settings distinguish legitimate assistant selection
from listening permission and identify absent overlay/widgets as Slice 16 runtime
work. No full cross-device Presence runtime was introduced.

## Findings raised to the implementer

- P2: the reduced-motion switch initially exposed an unlabeled TalkBack on/off
  node; its visible Text was a separate semantics node. Requested a content
  description and a native semantics assertion.
- P2: Android accessibility and assistant-role settings launchers initially lacked
  unavailable feedback if the platform flow throws. Requested the same guarded
  handoff behavior already used by Privacy.
- Native Platform test expected `Overlay · unavailable` while the initial source
  still said `not implemented`. The source now names unavailable Slice 16 runtime
  ownership; final native results must validate that exact readback.

## Independent automated validation

Ran `:app:testDebugUnitTest :expression:testDebugUnitTest` independently: Gradle
passed in 5 seconds. App JVM suites reran **20 tests, zero failures/errors/skips**.
Expression result was up-to-date, not independently re-executed by this command.
Receipt: `.tmp/13-7-independent-jvm.log`.

No connected test was run by this reviewer while the parent held the emulator;
parallel connected runners can steal focus and invalidate native results.

Independently inspected the final source corrections and parent-produced native
JUnit XML: `SettingsIntegrationTest` has **5 total / 3 executed / 2 intentional
process-preparation skips**, zero failures/errors. The two Slice 13.7 executed
tests cover unsaved bounded Persona, real absent Platform readback and labeled
reduced-motion persistence through Activity recreation. The third is a Slice 13.8
dark/font-scale smoke check. It changes font scale to 1.8 with the actual device
density, but does not rotate or change window size; it is not landscape acceptance.

The initial Persona test had an ambiguous single-node query because both the
live persistent Orb and preview Orb intentionally have the shared expression
description. Final test asserts the actual two nodes; this corrects the test
selector rather than removing continuity. The failed attempt is not a product
PASS. Parent reports final Gradle duration 44 seconds.

Reviewed actual native `13-7-persona-preview-simulated.png`,
`13-7-platform-reference.png` and `13-7-accessibility-reference.png`:
the preview's SIMULATED/unsaved warning is prominent, the live character remains
above it, Platform explicitly says assistant not selected and overlay/widgets
unavailable under Slice 16, and reduced-motion is visibly enabled after recreation.
Text and controls are legible with restrained hierarchy and no decorative metrics.
These settings are copy-heavy and vertically scrolled; compactness is a final UX
advisory. The Platform still is scrolled to content and cannot prove full top/bottom
geometry by itself.

Both P2 findings are corrected: the motion switch now exposes its actual label
and the native test finds it by content description; platform launchers catch
unavailable flows with truthful no-role-change feedback. No demonstrated unresolved
software defect remains in this review scope.

Not checked: real phone/OEM settings and assistant invocation, actual owner voice
enrollment, sustained TalkBack navigation and physical audio. Remaining risk:
reference UI evidence cannot establish these consolidated owner/device obligations.
