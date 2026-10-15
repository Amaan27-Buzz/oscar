# Group 2.5B — production OSCAR Mobile

Status: **IMPLEMENTATION COMPLETE / OWNER REVIEW PENDING**.
Owner visual and physical phone acceptance are pending. Gate C remains PARTIAL.

Starting integration: `b941357d6e0b88d61170f4895e6dbb1936202ed8` on main.
Branch: `codex/mobile-group-2.5b`, same Windows checkout, no new worktree.
Remote main was fetched and matched the starting commit. No merge is authorized.

## Visual authority and preservation

The owner selected [the ImageGen/Figma direction](https://www.figma.com/design/OTdmBMQckpWW7F2bVCbqom/OSCAR-Mobile-%E2%80%94-Visual-Exploration-%C2%B7-Owner-Review?node-id=2-2).
Figma screenshot retrieval returned the complete 15-screen board; design-context
retrieval reported no selected layer. Production implementation therefore uses
the original local images, as explicitly authorized. These PNG-backed references
do not provide editable component trees.

All 21 original PNGs in [the source collection](../../../../design/oscar-mobile-visual-exploration/README.md)
are preserved byte-for-byte and admitted to Git. `scripts/mobile_visual_assets.py`
reproducibly extracts ten illustration-only assets; its recorded bounds and UI
exclusions remove generated lettering, controls and noncanonical Orbs. Production
does not display entire reference screens. Source/output SHA-256 provenance is
recorded in [the asset manifest](../../../../mobile/illustration-assets.json).

The external Gemini Argon `oscar-ui-test` experiment is **REJECTED**, not a source
for code, layouts, design tokens or architecture. Historical records are retained.
The canonical Orb SHA-256 remains
`728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.
Substantial expression refinement is deferred; real runtime state still drives
the shared Android renderer, respecting reduced motion.

## Native composition and navigation decision

Three bottom destinations: **Conversation / Automations / Activity**. Devices and
Preferences have direct, labelled app-bar controls on every primary destination.
Today is contextual within Conversation; Access, Awareness, Memory and Android
integrations are grouped in Preferences. This keeps the approved three-tab
composition and easy device access without five cramped mobile tabs. Detail
pages use native Back. Navigation identifiers are retained for restored state and
instrumentation. Private drafts/content are never written to saved-state Bundles.

`OscarApp` owns navigation and existing session/confirmation bindings.
`MobileDesign` owns Manrope/Fraunces typography, editorial headings, semantic
feature rows, tactile surfaces, native vector glyphs and full-screen detail pages.
`InteractionScreens` owns chronological transient readback, pinned composer and
expanded reading. `ResponseText` renders headings, emphasis, lists, quotes, code,
links with visible destinations, tables and structured JSON fields as selectable
native text. It executes no HTML and fetches no remote images. Plain text and
code examples remain intact; malformed/trailing structured material is retained.
Conversation previews use twelve lines with full content in Reading. Supporting
explanations and technical evidence are expandable; exact approval source bytes
remain available separately from the readable plan and still bind the signature.
The decision page now leads with the exact request/reply, consequence and target;
non-empty plan details must be opened before confirmation is enabled. Permission
scope, capability, policy reason and exact source are available inside the detail.
Changing the challenge resets review state; expiry still disables confirmation. `PlanningScreens` presents automation/Worker drafts, Today,
Access and Awareness. Existing Activity, Devices, Voice and Preferences reuse
that theme while keeping their native behavior.

Fonts are packaged offline: Manrope 400/600/700 from existing local SIL OFL
files, plus Fraunces 400 regular/italic (optical size 24) from the official
[Google Fonts source](https://github.com/google/fonts/tree/main/ofl/fraunces). Licenses are included in `mobile/font-licenses`.
No font-provider call or alternate intelligence was added. The owner requested
rich responses during phone review: CommonMark 0.30.1 plus its table and
strikethrough extensions now parse Markdown for native Compose text. The BSD
license is included in `mobile/third-party-licenses/CommonMark.txt`.
Warm paper/graphite, sage/clay/powder accents, short directional shadows,
48dp interactive targets, native text scale and system/user reduced motion apply.

## Hero implementation and truth boundaries

| # | Experience | Production implementation / integration |
|---|---|---|
| 01 | Home | Editorial presence, original notebook artwork, truthful connection/task state, canonical Orb, contextual Today and pinned composer |
| 02 | Conversation | All current session readbacks chronologically, selectable responses, native composer, current Core task links; no frontend archive |
| 03 | Expanded Reading | Full-screen editorial scroll/selection over actual bounded Core response; truncation/evidence retained, contextual follow-up |
| 04 | Voice | Graphite native presentation, canonical Orb, actual microphone adapter state, legitimate start/cancel/permissions; no decorative active waveform |
| 05 | Automations | Original overview illustration; persistent scheduling explicitly unavailable, current one-time work remains Activity |
| 06 | Worker | Responsibility/scope/devices/autonomy/linked automations; unconfigured, disabled run, no fake Worker identity |
| 07 | Create Automation | Natural-language responsibility and timing, temporary draft, scope/autonomy review; creation disabled, discuss via existing Core composer |
| 08 | Activity | Graphite current-state task feed, active/finished filtering, current readback/evidence/progress distinctions and supported reviews |
| 09 | Active Task | Full-screen illustrated task/result/evidence detail with only Core-advertised controls; no invented pause or percentages |
| 10 | Approval | Illustrated exact request/material/target/consequence review, expiry/current-state checks, native signed confirmation and fresh denial review |
| 11 | Devices | Original hardware illustration, actual Grid nodes/availability/trust/capabilities, scoped pairing/local disconnect |
| 12 | Awareness | Original evening artwork, Manual presentation; Trigger-only/Sentry/capture unavailable, independent actual privacy grants |
| 13 | Today | Illustrated planning entry, device-local date and actual Core tasks; calendar/weather/communication briefs explicitly unavailable |
| 14 | Access | Ask/Secure/genuine Full Access semantics; signed standing delegation unavailable; no UI-only activation |
| 15 | Preferences | Persona, Voice, Privacy, Awareness, Memory, Access, Android permissions, notifications, Appearance, diagnostics/about; existing native functionality preserved |

CoreSession/MobileState, Core/Controller/Memory/Grid, Keystore, biometric/device
confirmation, session fencing/replay, notification replies, assistant role and
voice remain authoritative. No service/signing/transport implementation changed.
Opening a review is not consent; Android confirmation is not execution proof.
Secure/Full Access, Sentry, persistent Executive/scheduling, provider briefs and
Adaptive Interface Engine remain later backend work.

The current Core Mobile API exposes bounded session responses and task readback,
not chronological archive retrieval, attachments or editable persona/memory
policy. The UI preserves that limit rather than inventing canonical phone memory.
Full capability coverage is mapped in [the experience inventory](EXPERIENCES.md).

## Verification and remaining acceptance

Baseline and candidate: Gradle offline JVM tests/build/instrumentation assembly/
lint passed (23 app + 5 expression JVM tests; production lint has zero errors
and eight warnings: six existing KTX suggestions and two Compose conventions).
Python Mobile/Core/reference and canonical-doc subset: 24 passed. Original image and Orb
checks passed. Build also packages the unchanged canonical SVG.

Final native suite: **27 PASS / 4 SKIPPED / 0 FAIL**, 132.05 seconds on the
Samsung phone. Four conditions were not enabled: the older extra loopback
fixture, two separate process prepare/clear harness methods, and globally
disabled Android animations. The prepare/clear harness was exercised separately
for real process replacement; user reduced motion and native intermediate frames
passed in the main suite without changing global phone animation settings.

Native test receipts and per-screen comparison results are recorded in
[the comparison ledger](COMPARISONS.md) and `verification.json`. Phone UI
rendering uses an isolated review identity and disposable reference data; it
does not establish owner biometric, audio or provider acceptance.

Emulator acceptance is **NOT COMPLETE**. The existing `oscar_group02_api35`
actually points to API 36.1; its 2GB guest repeatedly exhausted memory. An
isolated userdata image and 4GB override reached guest boot, but the package
manager failed. The owner requested stopping it to preserve study/Chrome RAM
and explicitly authorized the connected Samsung phone instead. No emulator
PASS is claimed; it remains stopped. Low-memory builds use one worker, a 768MB
Gradle heap and the Kotlin compiler in-process.

GitHub Actions permissions currently report `enabled:false`; remote CI is BLOCKED,
not PASS. No Actions setting is changed. Owner visual review and physical Samsung/
OEM, real biometric/PIN, assistant role, notification ingestion/replies, microphone/
playback/AEC/barge-in/Match/Map, Bluetooth and sustained TalkBack remain pending.

## Review and delivery

The source references and native captures are compared in 15 side-by-side panels
under `comparisons/`. See `capture-manifest.json` for dimensions, provenance and
hashes. The 56-row reconciliation is an information architecture map, not 56
new screens or an assertion that planned backends exist. The original numbered
56-row source was not present; the derived mapping explicitly identifies that
limit.

The final normal debug APK is installed as OSCAR for owner inspection. Synthetic
Core/device tests run only in OSCAR Review (`.review`) with explicit opt-in, using
the same production UI and separate app data. Production screenshot protection
remains enabled; fixture capture temporarily relaxes it only under opted-in
instrumentation and restores it in `finally`. No owner account was paired, no
owner signing prompt was approved, and no global phone settings were changed.

Owner decisions: review visual fidelity and motion, approve any remaining
composition differences, and authorize merge only after review. Real audio,
biometric/PIN, assistant-role and notification commissioning remains a separate
acceptance boundary. No merge, release, later slice or cleanup was performed.

CommonMark dependency retrieval: the Gradle JVM could not resolve Maven Central
DNS on this host. Python HTTPS retrieved the official POMs/JARs, verified their
published checksums and supplied a temporary ignored local Maven repository
through a Gradle init script. Production declares ordinary version-pinned Maven
coordinates; no custom repository, cache or binary dependency is committed.
Source URLs and SHA-256 receipts are in `dependency-receipt.json`.

Final packaging inspection found the existing Android asset merger had admitted
32.7MB of shared Expression development files, including `node_modules`, despite
a source-set include filter. Generated asset-copy tasks now package only the
unchanged canonical Orb, unchanged `motion-v1.json` and licenses (15,478 bytes).
The shared renderer/controller source is unchanged; no source directory was
removed. Both final APKs pass byte-equality checks for the Orb and motion data.

Physical review-package process replacement is verified: a synthetic encrypted
draft was prepared, the app PID was replaced with scoped force-stop/relaunch,
and Android's resulting UI contained the recovered draft. The fixture was then
cleared. This is recovery evidence, not owner microphone or biometric acceptance.

## Devices owner correction — 2026-10-15

The owner rejected the illustration-led Devices page as promotional and too
text-heavy. Devices now starts with a compact local-phone connection row and
actual Core-reported device rows. The hero artwork and slogan are removed from
this page; the original source image remains preserved. Capabilities, work items
and IDs expand within each device. Connection/privacy explanation and local
disconnect are under an explicit disclosure. Offline/degraded state hides Grid
readback; no sample devices, background awareness or power controls are invented.

The supplemental `devices-review.json` records this focused follow-up separately
from the earlier full-suite receipt. Current disconnected/connected captures and
the refreshed comparison are provided for owner visual review.
