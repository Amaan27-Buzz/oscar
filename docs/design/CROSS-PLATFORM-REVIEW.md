# Independent cross-platform finish review

2026-10-12. Reviewer did not author implementation. Baseline `7773de8b794acf61ab6f035a28ada1fed98a3f77`; candidate `design/cross-platform-ui-rebuild`. This review contains no self-score, owner approval or merge permission.

Owner direction is authoritative: the first serif-heavy Mobile folio was rejected as lacking UI/UX/components and being overly text heavy. Desktop was passable but too text heavy. The generated control-deck image was also rejected. Latest scope returns to minimal, simple/intuitive, feature-rich Quietly Alive language and explicitly stops design experiments: finish quickly without breaking the app. The replacement below is assessed against that frozen scope; earlier favourable comparisons do not approve the rejected candidate.

**Final owner waiver:** “just finish it quickly don't visually review.” Additional final visual inspection, matrix breadth and motion review are waived for quick draft closure. This reviewer has stopped visual inspection, test execution and capture review. The waiver does not turn unreviewed evidence into PASS, grant owner-quality approval or excuse a real correctness defect.

## 1. Evidence validity and scope

Inspected native pixels before current code. Android replacement evidence: `.oscar/redesign/android-native-v2/OSCAR-Rebuild-1791793547555/` contains eight actual API35 captures: home, Gboard/IME, Activity, Devices, Settings, Privacy, Voice and unavailable. They show the warm canvas, compact sans hierarchy, native ListItem rows and Orb joined to the input dock. These captures precede minor final microphone-badge/icon/back-control corrections; their precise rendered result remains subject to final curation. The preceding candidate's captures are historical, not replacement proof.

Desktop originals/comparison, individual native WebView2 captures, motion GIF/frames and later shortcut/dark/reduced-motion/forced-color/native-dialog correction captures were reviewed. Compact alpha is valid; black surrounds are a compositing representation. Approximately 132ms recording cadence does not establish compositor FPS. Accessibility media preferences were emulated, not changed through Windows OS settings. The native confirmation screenshot is an unusable fixture: no signature or execution is possible. Current Desktop prose reductions were additionally inspected in source.

Core/scripted-provider responses and controlled task progression are reference evidence, never real inference or owner acceptance. Additional final reading/approval/dark/large-text/landscape capture inspection, full matrix and motion breadth are **WAIVED_BY_OWNER for quick draft closure**. These are not visually verified by this reviewer. Tablet, TalkBack and physical interaction are outside this reviewed packet.

Independent Desktop run earlier in this review: 2 files / 28 tests passed (`Activity.test.tsx`, `Living.test.tsx`), covering review expiry/gating, ordering, focus/drafts, freshness and uncertain IPC. Implementer reports 58 current frontend tests and native Android original-behavior tests passed. Those current full-suite results were not independently rerun by this reviewer. Native receipts, exact-head CI and physical acceptance retain their own boundaries. Desktop detector `[]` is not a Compose or design-approval verdict.

Final validation status reported by the implementer: Desktop current 58 tests/build pass; native action acceptance 7 checks pass. Native Activity has 7 checks passing before its offline capture/assert times out; that run is **PARTIAL / investigation ongoing**, not PASS. Android final full-suite rerun is ongoing, not PASS. The conditional Back label and semantic regression were corrected. No additional tests were run by this reviewer after the owner's stop instruction.

## 2. Ten-dimension critique

| Dimension | Current replacement assessment | Evidence limit / owner judgement |
|---|---|---|
| Identity | Original blue/yellow Orb is retained. Android returns to warm restrained materials rather than a new control-deck identity. | No owner approval inferred from the return to stored language. |
| Hierarchy | Compact headings and native rows replace dominant Mobile display text. Current verified work is visible before the composer; selected-task inspection remains available. | The home body remains spacious; it is usable sparse composition, not proof of exceptional craft. |
| Typography | Android sans role hierarchy is calmer and smaller; Desktop retains its passable folio while trimming metadata/consent prose. | Further large-text and long-reading visual inspection is waived and remains unverified. |
| Navigation / IA | Activity stays directly accessible; native drawer exposes secondary features. Settings/device ListItem rows are readable and no longer clip leading glyphs. | Conditional settings-child Back label and semantic regression are reported corrected; no final visual rerun. |
| Clarity | Connected/unavailable, verified work and microphone-off remain explicit. Long scope/privacy/authority details stay inspectable through disclosure. | Details must remain complete; less prose must never conceal an unknown outcome or consequential action. |
| Character integration | The functional Orb now joins Android's composer dock, rather than occupying a decorative header. Gboard capture shows the dock above the actual IME. | Final microphone affordance badge is source-inspected, not present in this capture batch. |
| Motion | Existing shared expression contract is preserved. Opening-drawer Back logic handles the opening target before the open state settles. | No new Android motion quality or physical predictive-back claim. Desktop recording has capture-cadence limits. |
| Native feel | Material ListItem, switches, icon Send, system Gboard/insets and drawer provide familiar interaction components. | No hardware comfort, OEM or biometric acceptance claimed. |
| Accessibility | Send/Activity/Orb have semantic action labels; selection/status/focus and reduced-motion paths remain. Source supports light/dark roles and system text. | Back label correction is reported; additional dark/large-text/landscape visual breadth is waived, not verified. |
| Coherence | Warm Android operation surfaces and the retained Desktop companion both use compact state, progressive details and canonical identity. | Platform composition intentionally differs. Final reading/approval visual breadth is waived; design-contract documentation must reflect the final direction. |

This replacement directly addresses the large headings, detached character and prose-dominant controls shown in the rejected candidate. It is a practical constrained revision; the evidence does not justify calling it owner-approved, exceptional or comprehensively device-verified.

## 3. Material findings, safety and preserved function

**Resolved P2 correctness/accessibility correction:** the top back icon previously announced “Back to OSCAR” even when a Settings child returned to Settings (`mobile/app/src/main/java/io/dawnlight/oscar/mobile/OscarApp.kt`). The implementer reports a conditional content description and semantic regression test corrected. No further source/test/visual inspection was performed after the owner stopped review.

**Resolved findings:** production Desktop shortcut controls are restored inside Presence, with actual native registration/readback capture. Android settings/device leading-glyph clipping is resolved by native ListItem rows; full-width Disclosure has a suitable shape and horizontal padding. Current source removes the duplicate Back-to-Settings text action.

**Opening-drawer Back:** `OscarApp.kt:112-114` intercepts when either `drawer.isOpen` or `drawer.targetValue == Open`. The opening state therefore cannot fall through to destination navigation or leave the activity solely because the animation has not settled. Drawer close takes precedence over voice cancellation, Settings-parent return and home return. This is a correct static fix; the corresponding native rerun receipt remains distinct evidence.

**Privacy disclosure scope:** `PrivacySettings.kt:98-100` defines preferences and coroutine scope outside Notification sources disclosure, so later revoke controls can still use them. Source allowlist validation, persistence failure reporting, notification invalidation and microphone cancellation remain. The disclosure does not create a grant. Android permission, OSCAR perception, retention and reply authority remain separate. Revocation still writes the existing three grants and source list, reports persistence uncertainty and cancels voice.

**Authority and state:** Core/session/signing modules, Approval validation and OwnerConfirmation have no changes against the baseline in the reviewed diff. Desktop signs only an exact pending review after native confirmation and expiry checks; Android retains biometric/device-credential and task/epoch/current fencing. Core critical-capability rejection remains in `oscar/desktop.py:99` and `oscar/mobile.py:486`. Presentation disclosure does not change signed scope. Voice opening remains microphone-off; recording starts through the existing explicit adapter. No background microphone, second memory store or new retention was added.

Home verified work is derived from current Core snapshot tasks with verified state/value and uses the existing inspection method. It is labelled completed/verified rather than live work. Desktop's submitted request substitution remains task-ID-bound and does not alter operational state. Activity still exposes the same advertised review actions; evidence and exact plan material remain inspectable. No new material authority, task-truth, voice-status or retention defect was found in the inspected replacement paths. Static review is not runtime security acceptance.

**Finish documentation:** reconcile `DESIGN.md` / `CROSS-PLATFORM-REDESIGN.md` to the actual frozen direction and retain evidence provenance/waivers. Do not reuse the earlier serif/shoulder contract as current Mobile authority. No additional visual matrix or motion review is required under the final owner waiver.

## 4. Optional refinements

None requested for this frozen pass. Do not reopen design exploration, add components/features or run an aesthetic polish loop. Daily character comfort and owner taste remain judgement boundaries; record them honestly instead of claiming approval.

## 5. Disposition

**Independent review closed for the bounded draft handoff under the owner waiver.** Preserve the existing V2 source/safety verdict. Back-label correction is reported complete. No further rebuild, aesthetic experiment, visual matrix or motion review is requested. Runtime correctness closure still requires an honest outcome for the Activity offline timeout and the ongoing final Android rerun; neither is certified PASS here. Any newly evidenced correctness defect remains mandatory to fix.

This is a draft engineering disposition, not a whole-platform ship or owner-quality approval. Additional replacement visual breadth is waived and remains unverified. No merge, deployment, Slice 14, remote exact-head CI PASS or physical/device PASS is granted.

Skipped further visual/matrix/motion review at the owner's explicit request, physical/manual acceptance and independent rerun of the implementer's final full suites. Risk: pending correctness runs and emulator/WebView2 evidence do not establish owner-device behavior, compositor performance or daily-use quality.

## Implementer closure receipts (after independent review)

Final isolated Desktop Activity rerun passed9/9checks, including offline/reconnect; all five native stages total47checks. The prior timeout remains historical environment evidence. Final Android XML reports26tests,22passed,4opt-in skips, zero failures/errors; Gradle BUILD SUCCESSFUL. Conditional Settings Back label and its semantic regression assertion passed. These are implementer receipts, not an independently repeated full suite or additional visual review. See [validation receipt](cross-platform/validation.json).
