# Group 5 C1/C2 — Android native capability foundation

2026-10-20. Local software candidate on the unmerged D2 dependency. Ask remains
the only active mode. This document does not establish owner-phone, OEM, hosted,
release, Google Play or full-phone-control acceptance.

## Ownership and inventory

The existing Compose app, CoreSession, Grid 2 client, Keystore SessionVault,
signed owner review, NotificationBoundary, assistant role and Companion remain
the integration points. Core still owns catalog selection, policy, tasks,
canonical history and independent verification. No Android planner, task store,
credential system or standing delegation is added.

| Interface | Implementation and current limit |
| --- | --- |
| `android.app.launch` | Explicit Activity launch, selected package and exact component |
| `android.link.open` | Exact HTTPS app link to a reviewed component; file/content/credential-bearing links rejected |
| `android.share.text` | Bounded plain text to a reviewed component; no arbitrary URI/file grants |
| Incoming Android sharesheet | `text/plain` becomes an unsent OSCAR draft; never submits a task or grants authority |
| Selected-app discovery | Bounded launcher resolution for an already selected package; Android package visibility still applies |
| `android.ui.inspect` | User-enabled AccessibilityService, bounded transient visible-node observation, selected package and perception grant |
| `android.ui.click` / `android.ui.set_text` | One exact non-sensitive resource-ID target; separate action grant; fresh app/window and node checks |
| Notifications | Existing source-scoped NotificationBoundary and reviewed replies reused; no notifications read in this run |
| Assistant and Companion | Existing legitimate role/service/foreground restrictions reused; no owner commissioning |
| MediaProjection / coordinate gestures | Unavailable; no screen recording request or gesture capability is advertised |
| Native remote dispatch | Unavailable until the existing Core/Grid can deliver and recheck an exact approved native operation |

`NativeCapability` provides stable versioned IDs, executor, supported state,
permission, availability, Ask mode, side-effect/retry and readback descriptions.
These are adapter manifests for Core's catalog, not a second authority registry.
All production statuses currently remain blocked by the missing commissioned
Core execution binding, even when local or Android permissions are present.

## Admission, lifecycle and evidence

`NativeAction` binds request/task/node/session, Core task generation and authority
epoch, a process-local lifecycle generation, a maximum 60-second monotonic
deadline, capability, exact package/target and bounded value. `NativeActionGate`
requires the entire action to match a trusted live Core authorization callback.
The production callback defaults to deny. Synthetic tests supply explicit test
authorization; they are not owner signatures or standing delegation.

Admission is bounded and one-use for the current lifecycle generation. Permission
changes, local revocation, backgrounding, cancellation and process replacement
fence continuation. Permissions and current Core authorization are checked again
before dispatch and while traversing a UI. App/window focus and resource identity
are rechecked immediately before mutation. Unlisted, password, sensitive,
invisible, stale and ambiguous controls fail closed. Service events are discarded;
there is no continuous event capture, logging or retained screen content.

CoreSession owns the adapter lifecycle. Existing Privacy and Android Presence
settings expose separate app-action, inspection and accessibility-action grants,
selected-app exclusions, Android service state and execution blockers. Android
accessibility settings open only after the user presses the control. The app
does not enable the service itself. Revoke OSCAR grants clears all local app
grants and the selected-app list; OS access and remote grants remain separate.

Native dispatch and accessibility action returns are `reported`, never verified.
Inspection observations are transient and bounded to 128 nodes and 256 characters
per node. An independent target readback is required to verify a task. Cancelling
cannot undo an Intent or action Android already accepted. No offline mutation
queue or automatic replay is introduced.

## Official platform research

Reviewed official documentation on 2026-10-20. App compile/target API 36,
minimum API 30; emulator acceptance targets API 35. Existing pinned Gradle 8.13,
AGP 8.13.2 and Kotlin 2.3.20 remain unchanged.

- [Android AccessibilityService](https://developer.android.com/guide/topics/ui/accessibility/service): service declaration and explicit system activation; window retrieval needs the declared capability. Gestures require a separate capability which this implementation disables.
- [Background Activity starts](https://developer.android.com/guide/components/activities/background-starts): native dispatch stays foreground and never bypasses Android launch restrictions.
- [Package visibility](https://developer.android.com/training/package-visibility/declaring): launcher intent visibility is declared; runtime discovery queries only an already selected app, without `QUERY_ALL_PACKAGES`.
- [MediaProjection](https://developer.android.com/media/grow/media-projection): per-session system consent and service restrictions apply; capture remains unimplemented.
- [Google Play AccessibilityService policy](https://support.google.com/googleplay/android-developer/answer/10964491): non-accessibility tools require disclosure/consent and declaration, and autonomous initiation/planning/execution through this API is prohibited. OSCAR declares `isAccessibilityTool=false`. This foundation permits deterministic exact reviewed operations, not autonomous accessibility control. Distribution approval and any later C3 capability set need separate review; OS support alone establishes neither.

## Local verification

`scripts.group05_android_reference` refuses any target except the named disposable
AVD `oscar_group05_capability_api35` at `emulator-5582`, then checks qemu, API 35 and
boot completion. Every ADB call specifies that serial; no device inventory or
physical-phone access is used. It builds locally, installs synthetic debug/test
APKs, runs only `NativeCapabilitiesTest`, and uninstalls those packages afterwards.
The fixture Activity exists only in debug/review builds, rejects non-emulator
hardware and is not exported. Production release builds contain no fixture.

The existing AVD named `oscar_group02_api35` actually resolved to an API 36.1
image and remained offline. It was stopped by its explicit emulator serial. A
new isolated AVD under ignored `.tmp/group05-android-avd` uses the already cached
API 35 system image; no SDK download, real account, phone or audio access occurs.

Final local run: **52 JVM tests passed, zero skipped; Android lint and both debug
APKs built; 7 instrumentation tests passed, zero failed/skipped** on that API 35
AVD. The receipt is `.oscar/group05/android-capabilities.json`; build and
instrumentation logs are alongside it. The script uninstalled its two synthetic
packages. The exact named emulator was shut down after acceptance; its isolated
AVD files remain in the ignored test directory.

Earlier instrumentation attempts failed and remain recorded: monitor/Activity
reuse and foreground-focus checks failed during fixture iteration. A later cold
boot also failed focus admission. A direct screenshot of the named emulator
confirmed a **System UI isn't responding** dialog while concurrent host builds
were running. After dismissing that emulator-only dialog and establishing actual
foreground readiness, all seven checks passed. Production foreground checks were
preserved; no failed focus check was relabeled as a successful native action.
The harness wakes/unlocks only this disposable emulator before instrumentation.

The seven checks exercise exact foreground launch, HTTPS link, scoped text share,
stale session/task/epoch/deadline and lifecycle/grant rejection, inaccessible UI
denial, and the review-only synthetic form. They do not exercise an enabled real
AccessibilityService modifying another application's nodes. Local raw logs and
receipts live in ignored `.oscar/group05/` and `.tmp/group05-*`; they contain
synthetic data only.

## Later physical commissioning checklist — not executed

- Explicit owner authorization for a named physical device and installation.
- Trusted hosted Core enrollment with an independently verified device/session.
- Owner biometric/PIN review and exact native-operation verification binding.
- Explicit selected-app grants; separate perception, retention and action review.
- User-driven Android accessibility disclosure/activation, OEM restrictions and sensitive-window checks.
- Revoke locally/remotely while idle and during a bounded operation; prove stale work cannot resume after re-enabling.
- Real target-app result readback, app-account verification and failure/ambiguity handling.
- Separate microphone/camera/media/notification/assistant/background acceptance only when specifically authorized.
- Review distribution-policy eligibility before any Play publication or standing-autonomy expansion.

Physical/OEM/owner credentials and signatures, MediaProjection, actual
AccessibilityService node mutation, live notifications, real audio/camera,
remote native dispatch, hosted commissioning and release remain NOT_RUN or
unavailable. Emulator instrumentation never satisfies those boundaries.
