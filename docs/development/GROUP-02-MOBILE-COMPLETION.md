# Group 2 — Mobile software completion

Owner authorization: 2026-10-11, Slice 13.1–13.8, autonomous software validation,
independent review, checkpoint commits and a draft PR only. Slice 14 is not begun.
Status: **SOFTWARE / REFERENCE CANDIDATE — OWNER AND DEVICE ACCEPTANCE DEFERRED — NOT PRODUCTION READY**.

## Baseline and boundaries

Separate worktree `mobile-completion/oscar`, branch
`build/slice-13-mobile-completion`, exact Group 1 base
`dcfd31bca6fbd8080f4c20bebe3d448e4bd8dc2f`. GitHub readback confirms that
head and Group 1 PR #2 remains open/draft. Original worktrees, origin, main/work,
older PRs and evidence remain untouched.

Read the Group 1 report, independent review, security regressions and cumulative
ledger. Slice 09's Kotlin/Compose `:app`, existing `CoreSession`, scoped
`CoreClient`, Keystore, native confirmation, notification, assistant and audio
adapters are present. `:expression` is the shared native renderer/controller.
No second Android reasoning, memory, task or routing runtime will be created.

Dependency baseline: AGP 8.13.2, Gradle 8.13, Kotlin 2.3.20, Compose BOM
2026.03.00, compile/target SDK 36, min SDK 30, Java 17 bytecode. Versions are
preserved; this is compatibility evidence, not a newest-version claim.

## Design hypothesis

Operate inside Quietly Alive + Playful Precision: one state-driven shared Orb,
restrained native typography, a compact writing surface, one relevant current
item, and deeper task/device/privacy detail on request. Home is not a transcript
or dashboard. The object persists as screens change. Real waiting, execution,
verification, attention, unavailable and mute remain distinct. Character delivery
never creates operational facts. No continuous decorative animation.

Canonical SVG is immutable. Existing shared weighted, interruptible native
expression motion is reused. Android screenshot protection, denial paths,
permission separation and Core signing/authorization remain mandatory.

## Validation policy

Each stage records build, JVM, Compose/emulator, security/Core readback,
lifecycle/stale-callback checks, rendered captures and independent review before
checkpoint. Synthetic screen states are SIMULATED_ONLY; actual isolated
Core/Android readback is REFERENCE_VERIFIED. No phone/OEM/audio/owner PASS.
Curated captures go in `docs/ui/mobile/completion`; raw sequences remain outside
Git with hashes. Sensitive production screens retain FLAG_SECURE.

All unresolved Group 1 manual/device and critical-confirmation obligations carry
forward in the cumulative ledger. A draft candidate is not merge or release
authorization.

## Checkpoints

Phase 0 and 13.1–13.8 results and commits are appended after observable proof.

## Phase 0 — integrity and security

Exact Group 1 baseline rerun in its unchanged worktree: **551 tests, 6 optional
skips, zero failures**. Native Android baseline debug/test APK builds and JVM
checks PASS. Real JVM RSA-PSS/isolated Core readback PASS. The initial concurrent
new-worktree run intentionally saw the newly added discard regression fail;
that red reproduction is not the exact-baseline result.

Independent security review confirmed unintended node-wide Desktop discard and
Mobile private request/result disclosure to replacement sessions. Desktop discard
now matches session and node. New Mobile requests reuse existing Runtime transient
privacy, session provenance, same-session reported context and discard; no parallel
runtime or chat archive. Legacy durable private content is withheld; no destructive
history migration. Full bounded review/request/scope binds the signed descriptor;
oversized review fails before challenge creation. Critical authority remains
BLOCKED because the current Core cannot attest strong owner confirmation.

Independent **118 tests PASS**, Ruff/mypy PASS. See
[baseline review](reviews/GROUP-02-BASELINE.md). Android API 36.1 reference AVD
reproduced the historical SurfaceFlinger `hasReadColorBufferDma` platform crash;
its failed activity/Compose runs are FAILED platform evidence. A separate API 35
reference image is being prepared. No phone acceptance or test PASS inferred.

## 13.1 — Presence / Home

Replaced the static Home image with the existing shared Compose ExpressionPresence.
An opaque epoch-bound adapter maps admitted local readback to resting, attentive,
processing, executing, verifying, waiting and unavailable/error presentation.
Private text/IDs never enter motion events; observations expire, heartbeat updates
do not replay transitions, OS duration scaling and shared reduced-motion/lifecycle
behavior remain intact. One approval-prioritized ongoing item is shown on Home.
The same object persists above secondary screens; no fabricated awareness/voice.

Independent review corrected mismatched decision captions and competing Home
items. It also found the inherited active-microphone revoke gap: capture now checks
both OS and local grants before each delivery, and local revocation stops the
foreground service. Denied-permission Compose regression checks that boundary.
Full synthetic in-flight Voice adapter exercise belongs to 13.5.

Validation: **10 app + 5 expression JVM tests**, **8 app Compose tests** with one
unrequested optional fixture skip, **3 expression emulator tests**, **54 focused
Core/security/Grid tests**, and real JVM/Core readback PASS. A fresh API35 AVD
uses the preserved earlier reference system image via supported `-sysdir`, with
its own data directory. No original AVD reset or cached-user state is reused.
The first API35 install raced initial boot and failed; after boot/unlock readback,
serial module runs pass. API36.1's compositor crash remains failed evidence.

Actual [native captures](../ui/mobile/completion/captures/13-1-home-unavailable.png),
[simulated verification render](../ui/mobile/completion/captures/13-1-verifying-simulated.png),
[receipt](../ui/mobile/completion/evidence/13-1.json) and
[independent review](reviews/13-1-INDEPENDENT.md). Captures assert production
FLAG_SECURE and temporarily clear it only inside disposable instrumentation.
Duplicate disconnected copy and detailed task labeling remain scoped later-stage
refinements, not privacy or execution defects. Phone/motion quality approval is deferred.

## 13.2 — Interaction / recovery

Home presents the latest interaction rather than a transcript archive. Short state
and response excerpts expand into a selectable native reading dialog; REPORTED
and excerpt warnings precede long content. Actual execution, waiting, result
received, verification, partial, blocked and UNKNOWN labels stay distinct. Core
provides same-session continuity. Android stores no reasoning or chat memory.

Only the unsent form draft is encrypted locally using existing AES-GCM/Keystore,
with origin/node/session-bound AAD; it is excluded from saved-state bundles.
Navigation/recreation/background preserve the draft. Replacement source and
discard clear it. Explicit restore disables editing until IO finishes and does
not overwrite an unknown saved draft on interruption. Network/source loss clears
responses/inspection/decisions; local cancellation does not claim remote cancellation.

All transport admissions and credential saves/deletion/public-key creation are
wire-serialized and epoch-fenced. Noncancellable local commits cannot reorder
replacement pairing/deletion. Independent review found and fixed the late-save
old-client race: replacement immediately retires the old client. It also found
and fixed split discard persistence: draft deletion and the pending suppression
marker now commit atomically. A pending Core discard hides private readback even
after new-ViewModel recovery; no automatic action replay occurs. Discard success
requires Core acknowledgement and preserves ongoing verification/execution.

Validation: **12 app + 5 expression JVM**, full API35 app **11 executed / one
optional skipped**, extra long-response case **1 PASS**, final source/draft
regressions **2 PASS**, expression native **3 PASS**, Core/security/Grid **54 PASS**.
Real isolated Core Home → text → response → Activity → Home → discard → foreground
restore passed. It used a Cloud reference executor; Desktop readback is 13.4.
Independent fresh JVM **17 PASS**, interrupted-pairing native PASS. Independent
draft recreation hit an immediate assertion before async restore, then passed an
unchanged isolated retry. The test now waits for actual restored state; corrected
parent rerun passes. Earlier capture-root ambiguity and competing simultaneous
instrumentation failures are retained locally; native modules now run serially.

Actual [short Core interaction](../ui/mobile/completion/captures/13-2-reference-home-response.png),
[simulated long reported reader](../ui/mobile/completion/captures/13-2-long-reported-simulated.png),
[receipt](../ui/mobile/completion/evidence/13-2.json) and
[independent review](reviews/13-2-INDEPENDENT.md). Capture review corrected inherited
purple Material dialog defaults and moved epistemic caveats above long content.
Abrupt process death is exercised during 13.8; physical/native owner use is deferred.

## 13.3 — Activity / consequential decisions

Native Active/Finished supervision and a selectable task inspector expose actual
states, target ownership, evidence references and session-available artifact
metadata. Live ownership requires a current active Grid lease and online node.
Worker progress stays REPORTED; mismatched lease/action, stale timestamp and
prior attempts become explicitly previous checkpoints. Offline execution is
UNKNOWN rather than animated working. Only advertised control actions appear.

Approval review presents complete exact request, plan, consequence, target and
permission scope. Length-framed UTF-8 display digest and task generation are in
the existing signed Core claim; changed display/audience/scope/generation/expiry
fails closed. Reply preview matches the signed text hash. Native confirmation
callbacks are epoch/current-decision fenced and cancelled on disposal. Opening,
dismissing or unavailable Android confirmation grants nothing. Core remains exact
expiry/policy/execution authority; critical-risk strong confirmation stays BLOCKED.

Fresh Core observation qualifies the client clock; local timer timing is advisory
under device clock changes/transport latency. A 250ms admission tolerance does
not extend Core authority. Native testing reproduced a clock-domain rejection,
then passed after correction. It also exposed missing polling restart after local
disconnect/reconnect; foreground pairing now restarts the existing polling loop.

Validation: **15 app + 5 expression JVM**, independent **20 JVM + 18 Core**, focused
Core/Grid/Desktop/reference **56 PASS**, full API35 Compose **13 executed / one
optional fixture skip**, exact native approval/inspection/expiry/denial scenario
PASS. Real Core expiry precedes explicit test-clock effect dispatch; no physical
timing quality claim. The real Android handoff on the insecure reference AVD fails
closed. A separate reference-only RSA signer denies through actual Core HTTP;
canonical cancellation and absence of execution are read back. This is not owner
consent, a fabricated biometric success or an Android signing acceptance claim.

[Independent review](reviews/13-3-INDEPENDENT.md) accepts bounded closure after
ownership, progress, generation and clock corrections. Curated
[approval](../ui/mobile/completion/captures/13-3-reference-approval.png) and
[cancelled readback](../ui/mobile/completion/captures/13-3-reference-denied-readback.png)
retain explicit reference provenance. The new disposable HTTP fixture uses the
existing Core/Runtime/Grid and actual Desktop/Mobile adapters; its separate admin
port supports only signed denial for its own synthetic session. No product API,
owner enrollment, private account or remote deployment was added.

During interruption, WHPX launch failed and software emulation did not boot. After
the owner stopped gaming, the1536MB/2-core reference AVD booted and native checks
resumed. Smaller-memory success is observed; RAM as the cause is an inference.
No host permissions, security settings, original AVD data or app dependency changed.

## 13.4 — Devices and Connection Grid

Compact native nodes disclose current trust, health, advertised capabilities and
associated active tasks. This phone is identified only by the admitted Mobile node;
Cloud/Edge appear only when configured. Home Node remains unsupported. No invented
power, remote revocation or approval authority appears. Local credential removal is
real and is described separately from trusted Core revocation.

Actual Desktop-origin task metadata reaches Mobile over isolated Core HTTP without
its private input or Desktop-session approval. The reference stops and restarts the
Mobile HTTP acceptor; Android clears private state on loss and reads back the same
canonical task after reconnection. JVM app16 + expression5, Core56 and two isolated
native Grid runs pass, including the new reproducible Android runner. API35 native
capture reviewed; no physical remote network or phone claim.

[Capture](../ui/mobile/completion/captures/13-4-reference-grid.png),
[independent review](reviews/group-02/13-4-INDEPENDENT.md).

## 13.5 — Voice presentation and cancellation

Voice invocation opens an explicit native control surface without recording. It
shares the current text draft/Core context. Microphone/audio status comes from the
existing AudioRecord/AudioTrack adapter; permissions, unavailable binding, failure,
listening and speaking remain distinct. Source/background/cancellation retires the
presentation epoch. Delayed service starts, failed terminal status and late audio
focus/capture/output callbacks are fenced; native output cancellation remains
interruptible. No new reasoning, speech model, training or capture runtime.

Android Voice Core binding is uncommissioned: production capture/recognition and
playback are unavailable until legitimately configured. Match/Map/Identity entry
points explain their unavailable commissioning path, with real route readback in
Voice settings. No synthetic success or microphone grant was used.

JVM app20 + expression5 PASS; Core56 PASS; denied voice → cancel → preserved text
native PASS23s. Independent review reproduced callback defects and fixed them with
four small lifecycle regressions. The initial text assertion used exact matching
for a substring and failed; corrected exact-message/state waits pass. Actual
[denied voice capture](../ui/mobile/completion/captures/13-5-voice-denied-reference.png)
reviewed. Acoustic/audio/phone validation remains deferred, not a voice runtime PASS.

## 13.6 — Privacy and permissions

Separate perceive/retain/act controls use legitimate Android permission/settings
flows and independent local grants. Source allowlists exclude every unlisted app;
no raw audio/notification archive is enabled. Sensitive notification content is
redacted from metadata/UI, with content fingerprints still binding exact source
reply actions. Foreground grant changes, source epochs and boundary revisions clear
cached source/reply views. Final reply delivery rechecks actual access and one-use
Core permit. Local revoke cancels audio epochs immediately; persistence failures
remain explicitly unverified. Unsupported retention/routing/camera/location remain
truthful unavailable controls, not decorative switches.

Build/JVM app20+expression5 PASS; native privacy3 PASS and capture rerun1 PASS.
Synthetic policy inputs are SIMULATED_ONLY; actual denied listener/OS permission
state is REFERENCE_VERIFIED. Core56 and full Core558/6 optional skips passed.
Full mypy found a Grid-origin nullable association defect; it is corrected and a
real leased Core-origin task regression now passes. No permission was granted to
make tests pass. [Independent review](reviews/group-02/13-6-INDEPENDENT.md) includes
parent independent inspection of authored privacy changes.

## 13.7 — Settings and system surfaces

Functional local appearance and reduced-motion preferences sit alongside legitimate
permission, notification, assistant-role and accessibility settings. Bounded Persona
preview is explicitly SIMULATED and never saved/applied to Core. Voice Identity,
Match/Map commissioning, model routing and remote policy settings remain Core-owned
and unavailable through the present API. Inert future preference switches were
removed. Diagnostics reveal only public build/connection/count state.

Slice09 inspection found assistant invocation opens MainActivity without recording;
Overlay and widgets are absent, honestly unavailable and owned by Slice16. No full
cross-device Presence runtime was relocated. Unavailable Android handoffs fail
with feedback. Dark/System appearance works; system animator disable plus OSCAR
reduced motion propagate to the existing shared renderer. UTF8 labels and labeled
TalkBack switch corrected after independent review.

App20+expression5 JVM, native Persona/platform/recreation2 PASS (combined smoke3
executed/2 optional process-preparation skips), Core57 and mypy64 PASS. Actual
[Platform](../ui/mobile/completion/captures/13-7-platform-reference.png),
[Persona SIMULATED](../ui/mobile/completion/captures/13-7-persona-preview-simulated.png),
[Accessibility](../ui/mobile/completion/captures/13-7-accessibility-reference.png)
and [independent review](reviews/group-02/13-7-INDEPENDENT.md). Initial preview
assertion was ambiguous between live and simulated Orbs; corrected count passes.
Large-font smoke is distinct from actual display matrix testing in13.8.

## 13.8 — Motion, accessibility and integration

One existing shared expression controller remains on the same screen tree across
navigation; operational truth controls the Orb, with source/epoch expiry and no
private content in expression events. Stable transitions coalesce refreshes; the
renderer sleeps after settling and pauses offscreen/background. No decorative
continuous animation or background polling/capture was added.

Actual window bounds govern narrow/landscape spacing and Orb size. Navigation and
voice/task action rows wrap at large font size. Text follows Android scaling;
headings, selected navigation, state announcements, field labels and reduced-motion
switch semantics are explicit. System disabled animators and OSCAR reduced motion
reach shared held-state rendering. Light selected-text contrast corrected from
4.333 to4.823:1; explicit dark theme now controls native status/navigation icon
appearance. Back/IME/focus handling preserves current context. Native privacy flags
and Android backup/device-transfer exclusions protect private app state.

Genuine API35 display matrix passed720x1280/320dpi,1280x720/160dpi and1280x1800/160dpi,
with injected app font scale1.8, actual visible Android keyboard, field bounds above
keyboard and Voice cancel→preserved text. This is emulator reference, never OEM or
physical display acceptance. Earlier Compose-only captures omitted the system
keyboard; final window captures include it. Android foreground restrictions are
preserved; actual microphone/playback commissioning remains unavailable.

Actual foreground process force-stop and explicit relaunch changed PID5579→5621;
the encrypted synthetic unsent draft recovered. No task mutation is automatically
replayed. This is process replacement proof, not every low-memory/OEM kill path.
The first harness incorrectly used Gradle's post-test-uninstalled APK; it now uses
installed direct instrumentation. A later UI observation was obscured by the
reference image's Messages ANR dialog; stopping only that isolated fixture app
revealed the correctly recovered draft, and a fresh full recovery run passed.

Final full Core559 tests:553 executed/6 optional skips; Ruff/format and mypy64 PASS.
Android app20 + expression5 JVM PASS; full native app25 total/21 executed/4 intentional
skips PASS. Those skips are old optional fixture plus opt-in process helpers/system
animation setting. Process helpers are separately exercised. Full-native initial
failures came from an obsolete Voice-screen expectation and fixture draft
concatenation; updated truthful screen assertions and isolated replacement pass.
All destructive native fixtures now guard emulator hardware. No permissions or
private owner accounts/audio were used. Final expression/system-motion receipts
and independent closure are sealed with delivery evidence below.

[Display matrix](../ui/mobile/completion/evidence/13-8-matrix.json),
[process receipt](../ui/mobile/completion/evidence/13-8-process-recovery.json),
[fresh adversarial review](reviews/group-02/FINAL-INDEPENDENT.md).

## Remaining acceptance and Group3 handoff

No demonstrated P0/P1 is accepted as a manual deferral. Subjective character timing,
owner visual review, sustained TalkBack, phone/OEM lifecycle and background rules,
actual acoustic capture/playback/AEC/barge-in/Match/Map, owner biometric/PIN/signing,
real notification ingestion/replies and physical networking remain consolidated
owner/device acceptance. Existing strong critical-risk confirmation remains
BLOCKED; every unresolved Group1 Windows/Voice/Edge obligation carries forward.

Commissioned Android Voice binding, mutable Core Persona/routing/privacy policy,
remote revocation, overlay/widgets and full cross-device Presence are explicitly
unavailable. This closes the supported visual/control software track, not those
future runtime capabilities or production readiness. No promotion, owner approval,
merge or release is claimed.

Group3 receives shared expression/source contracts, scoped Mobile/Core adapters,
exact review/signing boundaries, private-session regressions, independent reviews,
curated native evidence and cumulative ledger. Canonical Slice14 World Model /
Perception / Sentry must preserve the three independent grants and evidence truth;
15 commissioning,16 full Presence,18 physical expansion and19 hardening own their
remaining runtime/device obligations. Slice14 and Group3 are not begun.

## Reproduction

Use isolated API35 AVD (1536MB/two cores) with Android SDK/JDK21 and pinned Gradle.
`python -m scripts.mobile_completion_android` runs actual isolated Core/Grid HTTP
and native app tests; `--process-recovery` runs installed instrumentation plus real
process replacement. It always targets emulator-5582, not an owner phone. Run
`:expression:connectedDebugAndroidTest` serially, never competing instrumentation.
Display matrix commands change only that reference AVD with `adb -s emulator-5582
shell wm size/density`, run the dark/font/IME test, then reset overrides. System
animator-disable test is opt-in and restores the setting afterwards. Raw synthetic
native stills are archived outside Git with a SHA256 receipt; no motion frame
sequence or acoustic acceptance is inferred from stills.

## Checkpoint commits and final gates

| Stage | Commit |
|---|---|
| Phase0 privacy/security | `0cf44d3` |
| 13.1 Home/shared expression | `d4bf477` |
| 13.2 Interaction/private recovery | `740f08e` |
| 13.3 Task supervision/exact decisions | `0a5ef8c` |
| 13.4 Grid/device truth | `5475926` |
| 13.5 Explicit voice/cancellation | `1ec2eb5` |
| 13.6 Independent privacy grants | `011b342` |
| 13.7 Settings/system surfaces | `5b1c3ec` |

Final gates: Android APK/JVM/lint PASS (20app+5expression JVM;0lint errors,
15 dependency/KTX advisories). Lint's new context-cast rule prompted replacement
with existing Compose LocalActivity; no security/permission lint suppression.
Shared expression native3 PASS; actual Android animator-disabled theme test1 PASS
and original setting restored. Independent final Core57 plus plan/session/discard
attack reproductions PASS; independent native source replacement/Voice2 PASS.
Full app21 executed/4 intentional skips PASS. Core559 total/553 executed/6 optional
skips; Ruff/format/mypy64 and repository links/value-silent secret scan PASS.

Fresh review scores7.5 visual/7 interaction are advisory, not an owner quality PASS.
Demonstrated contrast, system-bar icons, IME evidence and fixture safety issues were
corrected, independently inspected and rerun. No unresolved demonstrated P0/P1.
Canonical Orb byte-matches baseline SHA256
`728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.
Curated still checksum manifest and raw archive receipt accompany final evidence.
The raw archive includes historical intermediate captures, not accepted motion or
physical evidence. Final implementation checkpoint/draft publication readback are
recorded after Git sealing below.
