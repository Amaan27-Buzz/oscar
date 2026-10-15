# Hero comparison ledger

References are the approved original ImageGen/Figma screens. Native captures
come from the owner's Samsung SM-S721B, Android 16 / API36, 1080×2340, using
the isolated `io.dawnlight.oscar.mobile.review` package and production Compose
code. They are **real-device UI evidence with disposable/synthetic data**, not
owner biometric/voice/provider acceptance. Owner visual approval is pending.

Source originals are 841×1870. Comparison panels preserve aspect ratio and use
equal display widths; no production screenshot was stretched or painted over.
The status-bar/inset and aspect-ratio differences remain visible. The canonical
renderer replaces the generated Orb illustrations, so raster expression details
are deliberately not copied from the concepts.

| # | Reference / native | Differences found and corrections | Remaining truthful differences |
|---|---|---|---|
| 01 | [Home](comparisons/01-oscar-home.jpg) | Matched warm palette, editorial greeting/side Orb and original notebook. Replaced heavy accent font with Fraunces 400 italic; pinned composer, tactile material and compacting motion | No fabricated owner greeting/calendar appointment; offline connection state |
| 02 | [Conversation](comparisons/02-continuous-conversation.jpg) | Chronological native text, powder user messages, selectable responses, pinned composer, task references | Bounded current-session Core readback; archived history and attachments not exposed |
| 03 | [Reading](comparisons/03-expanded-reading.jpg) | Native full-screen reading/selection/scroll; original notebook artwork; actual complete bounded response and follow-up | Content supplied by Core or explicit test fixture, no hardcoded article; independent evidence distinctions |
| 04 | [Voice](comparisons/04-voice-interaction.jpg) | Graphite immersive composition, centred canonical Orb/status, lighter editorial accent and actual start/cancel/grant controls | Microphone off/uncommissioned adapter; no fabricated waveform, playback or active-listening indicator |
| 05 | [Automations](comparisons/05-automations-overview.jpg) | Original checklist artwork, restrained sage button, responsibility navigation; removed irrelevant repeated connection footer | Persistent scheduling unavailable; no fake active example schedules |
| 06 | [Worker](comparisons/06-worker-detail.jpg) | Woven original identity artwork, editorial side composition, responsibility/scope/devices/autonomy/link rows | Worker unconfigured, Run unavailable; does not invent Morning Brief or a chatbot personality |
| 07 | [Create](comparisons/07-create-automation.jpg) | Native responsibility/timing draft, canonical side Orb, scope/autonomy/access review; keyboard-aware scrolling | Creation unavailable; temporary draft can be discussed with Core, never deployed as a schedule |
| 08 | [Activity](comparisons/08-activity-feed.jpg) | Graphite theme/sage filters and tactile timeline rows; removed duplicated descriptions and primary debugger metadata | Current Core work or honest disconnected feed, no invented sample events |
| 09 | [Task](comparisons/09-active-task.jpg) | Original laptop artwork, full-screen task/status/result/evidence; fresh Core-advertised actions | No invented pause/progress; target/verification detail reflects actual readback |
| 10 | [Decision](comparisons/10-approval-decision.jpg) | Original decision artwork, exact reviewed material/consequences, sage native confirmation, fresh denial review and expiry | No tap-as-execution, no fabricated calendar mutation; biometric/PIN activation not silently passed |
| 11 | [Devices](comparisons/11-devices.jpg) | Owner correction removes the promotional hero/slogan; compact local-phone status and actual expandable device rows; connection action and on-demand details | Original concept retained as history; current owner direction supersedes its Devices composition. No sample connections or power/wake claims |
| 12 | [Awareness](comparisons/12-sentry-awareness.jpg) | Original evening-room artwork, graphite surface, sage Manual selection and independent privacy rows | Sentry/trigger/capture uncommissioned; no false activation or observation |
| 13 | [Today](comparisons/13-today-chief-of-staff.jpg) | Illustrated day path, editorial date/heading and native planning entry; fixed inherited scroll clipping | Provider/calendar/weather/communications unavailable, no invented commitments |
| 14 | [Access](comparisons/14-access-modes.jpg) | Canonical Orb, Ask/Secure/genuine Full Access semantics, clear unavailable activation | Signed delegation/revocation not integrated; controls cannot bypass confirmation |
| 15 | [Preferences](comparisons/15-preferences.jpg) | Original stationery artwork beside editorial heading; coherent semantic list and appearance/privacy/system access; fixed inherited scroll clipping | Core-only persona/memory settings remain unavailable; Android integrations retain native boundaries |

Native images and comparison panels are indexed by `capture-manifest.json` after
the final device run. Initial captures exposed stale page scroll positions,
heavy accent typography and keyboard-resized comparison framing; the corrected
captures are used for delivery. Actual role, audio, biometric and notification
commissioning remain separate acceptance work.

Motion uses current-content entry transforms (220ms/8dp), selection colour
transitions (180ms), responsive row presses (120ms), tactile/expansion sizing
(180–220ms) and the existing state-driven Orb renderer. No outgoing private page
is retained across an authority/source epoch. Reduced-motion mode renders
immediately. Native frame sampling verifies intermediate and settled frames.

Review-visible differences: Devices and Preferences retain the three-tab bar
for immediate return to primary work; concepts show fewer controls on those
secondary views. Native rows use compact vector glyphs, and illustration crops,
spacing and text lengths differ where real unavailable states replace reference
examples. These are review candidates, not pixel-perfect or owner-approved
claims. Conversation/Reading/Task/Decision hero fixtures exercise production
composables with labelled synthetic inputs; the separate Core-flow captures
exercise the full app scaffold against a real disposable Core/Grid HTTP runtime.

The owner's phone review identified overly dense supporting copy and raw
Markdown/JSON presentation. Responses now use native rich text, twelve-line
conversation previews and complete expanded reading. Voice, planning, authority
and task technical explanations use expandable detail. Exact approval material
remains selectable and available alongside its readable structured view. Native
rich-response and adversarial/malformed-input tests cover the correction.

The subsequent owner correction specifically rejected the dense decision page.
Its new first view has side artwork, an exact request/reply card, consequence,
target and secure controls. Full plan/scope/policy material is expandable, and a
non-empty plan must be opened before confirmation is enabled. Exact source bytes
remain available; a new challenge resets review state and expiry still disables
confirmation. Collapsed and expanded Core-flow captures are separate evidence.
