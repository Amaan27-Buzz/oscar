# Slice 12.1 quality recovery — independent review

**Advisory recommendation: ACCEPT CANDIDATE for owner visual review. Supported design score: 7.9/10 (79/100).** This is acceptance of a bounded review candidate, not owner approval, production promotion, merge permission, or permission to begin 12.2.

Date: 2026-10-11, Asia/Calcutta. Reviewed working tree: `fix/slice-12-1-presence-quality`, based on `5fea2071e891adf0fac7f9838ee556c9a60e1e1c`. Recovery code was uncommitted at the visual freeze. The historical 6.7 reports and source captures remain unchanged.

## Independence and freeze

This reviewer did not implement the recovery and did not read its source, tests, implementation summary, or change description before the visual assessment. First read: global `DESIGN.md`, `TASTE.md`, `docs/EXPRESSION-CORE.md`, and `docs/DESKTOP-UI-REDESIGN.md`. Original native/state images were inspected before the historical independent verdict. The new assessment uses the final captures and factual native records, rather than the historical score as a target.

**Ten scores and the design recommendation were frozen at 2026-10-10 19:46 UTC, before source/test inspection.** No further agent delegation occurred. Computer Use and Windows input were not used; the owner expressly excluded them. A Product Design audit workflow kept observations tied to images and separated visual evidence from implementation evidence.

The native records at freeze were:

- `evidence/native-suite.json`: SHA-256 `de04d5d1af0f1fe4cef7aa34a3c353aa34c47aa4cedddebbf749360e9639fdfd`.
- `evidence/native-interrupt-suite.json`: SHA-256 `3c3a6355d41301de1f8437239a0e819ad9fac6adeb0a75b7fdc7ea0fc4d353ba`.

## What was actually inspected

All **15 final `after-*.png` captures** and both native reduced-motion/forced-colors captures were opened individually at original resolution. Thirteen manifest-selected raw motion frames were also opened at original size. Additional temporal comparisons used 48 raw-frame Orb crops generated in memory, and 12 decoded encoded frames from each of the three GIFs. Those inspection crops did not modify or replace source evidence.

All final raw frame files were decoded for dimensions and a limited blue-object-presence check. None lacked blue-object pixels. This is a narrow automated absence check, not a visual assertion that every frame is unclipped or beautiful. Every frame was not personally inspected. GIF timing was decoded for every encoded frame. The older contact sheets contain earlier timings and an earlier approval layout; they were inspected but excluded as proof of the final version. Final manifest-selected files take precedence over orphan files or composites.

| Final recording | Raw samples / span | Encoded playback | Supported observation |
|---|---:|---:|---|
| [Invoke/retreat](evidence/native-invoke-retreat.gif) | 353; 11–3771 ms | 126 frames; 3860 ms | Repeated leaf entry/exit and reinvocation retain the draft and Orb; the final sequence returns to an expanded, usable composer. |
| [Weighted work](evidence/native-weighted-work.gif) | 448; 17–9273 ms | 155 frames; 9440 ms | Awake approval changes to a compressed asymmetric working face; puck displacement/rotation develops and recovers; verified result returns to an open-eyed rest. |
| [Interruption/recovery](evidence/native-interrupt-recovery.gif) | 466; 9–5729 ms | 144 frames; 5800 ms | Authoritative result supersedes the active phrase; the work marks recover to rest and the result remains visible through retreat/reinvocation. |

Raw median sampling gaps are 11/12/11 ms respectively, but the largest gaps are 104/2921/495 ms. The work GIF contains a 4700 ms encoded hold. These files are substantially more informative than the original coarse three-frame clips, but are **not uninterrupted native compositor recordings or proof of sustained frame rate**. I inspected timestamped frames and encoded holds; I did not perform a human subjective playback-speed smoothness review. That judgement remains with the owner.

The source is actual Tauri/WebView2 renderer/CDP and native IPC against an authenticated disposable Core. It is stronger than a synthetic browser fixture. It does not establish OS focus ownership, transparent through-click, tray behavior, work-area placement, multi-monitor/DPI migration, or whole-desktop composition. The reported scale is one 1.25 case; this is not a native DPI coverage claim.

## Ten-category score

Equal weighting; no target score was supplied. Scores judge demonstrated quality and include the stated evidence limits.

| Category | /10 | Evidence-based reason |
|---|---:|---|
| Identity | 8.5 | Distinctive blue shell/yellow offset puck survives compact size; canonical wink at rest and restrained asymmetric derivatives remain recognizably OSCAR. |
| Expression/personality | 7.5 | Awake approval is clearly stronger than the old sleepy attention pose; working displacement and asymmetric marks are now visible. Broader native gaze/blink/reactive delivery is still not demonstrated. |
| Motion | 7.5 | Final raw/encoded sequences show authored travel, rotation and bounded recovery rather than pose substitution alone. Subjective timing, weight and compositor smoothness remain unapproved; capture gaps limit the claim. |
| Responsiveness | 8.5 | Blocked/denied outcomes visibly explain what happened, offer a next step and retain the request. Ten reported native cycles retain the draft without the stale warning; DOM editor focus is supported, OS focus is not. |
| Composition | 8 | One warm leaf, one main state and one principal action retain the quiet presence direction. Fixed-height sparse states and the conventional paper leaf are competent rather than exceptional. |
| Typography | 8 | Original-resolution captions, action labels and body copy are more legible and deliberate. Small low-emphasis footer text still merits ordinary-distance owner inspection. |
| Compact | 8 | Independent object remains ambient; the awake approval pose plus yellow text label is explicit. The separate white status plaque remains visually generic, though useful and readable. |
| Expansion/retreat | 8 | Multiple complete cycles and preserved draft improve the evidence materially; the Orb remains present in sampled transitions. Entry/exit still relies primarily on leaf scale/opacity, and native spatial continuity is not proven by renderer crops. |
| Windows integration | 7 | Real native renderer/IPC, acknowledgement, bounded placement requests and recovery are supported. OS keyboard focus, hotkey delivery, tray, compositor/hit regions and configuration coverage remain separate unexercised boundaries. |
| Coherence | 8 | Blocked, denied, waiting, offline, failed, reported and verified remain distinct; opening approval grants nothing. At freeze, the review destination was not visibly task-specific in its first viewport; this P2 was resolved afterward without rescoring. |

**Total: 79/100; mean: 7.9/10.** This is a material improvement in demonstrated usefulness and character over the historical packet, not a claim of complete desktop product quality.

## Original failures and current correction evidence

1. **Blocked Ask — correction demonstrated in this bounded run.** The original [no-feedback capture](../independent-evidence/14-native-blocked-no-feedback.png) and new before capture show an unchanged ready composer. [After blocked](evidence/after-blocked.png) instead says the request did not start, exposes Core's exact capability-unavailable explanation, preserves the draft and provides Check availability / Edit request. The factual record pairs this with no tasks and zero actions. [Permission denied](evidence/after-denied.png) is deliberately different and warns that repeating the request cannot grant access. No fake Working or task is presented.
2. **Reinvocation warning — bounded replay is clean; intermittent cause is not independently reproduced.** The historical [warning capture](../independent-evidence/07-native-reinvoke-warning.png) remains valid evidence of the original failure. [After reinvocation](evidence/after-reinvoke.png) shows the retained draft, usable Ask and no obsolete warning or scrollbar. The new suite reports ten rapid/settled native cycles. The separate baseline run reportedly failed to reproduce the intermittent warning in twelve cycles. Therefore this review does not claim an independently reproduced native before/after race; deterministic regression evidence and clean new native replay must remain separate.
3. **Subdued approval — visual correction demonstrated.** [Final compact approval](evidence/after-approval-compact.png) has open asymmetric eyes and a slight attentive lift, visibly distinct from waiting/offline slit marks. [Expanded approval](evidence/after-approval.png) quotes the submitted `2 + 3` request and states that full details must be reviewed and opening review grants nothing. This portrays owner attention without a happy consent/success cue.
4. **Character/continuity — improved, bounded demonstration.** The final motion sequences show real rendered internal movement and result interruption/recovery. The earlier blank-object sample is not repeated in the inspected final samples or the limited all-frame blue-presence check. That does not establish a universal disappearance/clipping fix or sustained animation acceptance.

## Remaining findings

**No new observed P0 or P1 in the inspected recovery states.** The former two P1s have the bounded correction evidence above. Three P2 concerns existed at freeze; the review-destination issue was corrected and independently verified afterward. The other two remain owner/finish boundaries, rather than proven implementation failures.

- **P2 at freeze — Review destination was not visually established; RESOLVED POST-FREEZE.** [After exact review](evidence/after-exact-review.png) shows the generic expanded Interact/context/Ask workbench in its first viewport. No specific decision, submitted request or approval control is visible there. The original record proved that opening did not confirm, but did not visually prove a direct review handoff. The scoped correction and new [visible review capture](evidence/corrected-review-route.png) now establish that handoff; see post-freeze verification.
- **P2 — Motion feel and Windows integration remain owner boundaries.** The timestamps establish recorded poses and holds, not human playback quality or native compositor smoothness. Full-rate owner playback, ordinary-distance compact recognition, background focus/hit behavior, tray and supported native configurations remain unestablished. The owner's no-Computer-Use decision does not turn these into PASS. Preserve the explicit boundary when presenting the candidate.
- **P2 — Presence finish is still conventional.** The white/yellow text plaque feels attached rather than materially integrated with the object; footer metadata and repeated secondary routes remain visually utilitarian. Improve only if the owner finds the normal-distance result weak; retain explicit state and prototype honesty. This is finish work, not a reason for a new renderer, palette, mascot or general redesign.

## Bounded flow and owner readiness

The reviewed flow is: compact rest → composer/draft → repeated retreat/reinvoke → blocked capability → separate permission denial → awake approval → review opening without consent → executing → waiting/verified/reported/failed → Core disconnect → failed state restored on reconnect → bounded presence-menu requests → captured accessibility equivalents. The final captures support those states. The post-freeze correction also makes the actual review visible; OS behavior limits remain.

The candidate is ready for a focused owner review of **12.1**, especially the object at actual desktop distance and the three recordings. Keep the free Orb and the single-leaf hierarchy. Do not call the broader Desktop experience accepted, promote it, merge it, or begin 12.2 from this advisory verdict alone.

Not independently checked at visual freeze: implementation/security correctness, automated tests, remote exact-head CI, real inference, owner GUI approval, voice/device commissioning or sustained owner use. Those are not implied by native renderer captures or the reported check count.

## Post-freeze verification

After freezing the scores, I read the presence handler, its focused regressions, native command handoff and App review rendering. The presence button sends the actual pending task ID through `review`; native code obtains that task's review and opens Approval mode. It does not confirm. The review section was rendered below generic Context/Ask content with no focus/scroll handoff, supporting the observed P2 as a visibility problem rather than a wrong-task or authorization failure.

I independently ran `npm test -- --run src/presence/Living.test.tsx` from `desktop`: **18 tests passed; exit 0**. These cover acknowledgement ordering, stale retreat failure, blocked/denied/unknown feedback, failed resizing, draft/focus recovery, exact review command and submitted-request binding. They support correctness at their test boundary and did not change the design score.

The narrow post-freeze correction adds an opt-in `focusReview` prop, passed only by the Living workspace. App focuses and scrolls its actual approval section once when the review ID changes; the default App entry retains `false`. The presence-scoped scroll margin accommodates the sticky return control. I inspected this change and its regression; it introduces no task decision or permission authority.

I then inspected [corrected-review-route.png](evidence/corrected-review-route.png) at original resolution and [review-route-receipt.json](evidence/review-route-receipt.json). Owner decision, scoped capability/consequence/policy, exact `2 + 3` material and the native-confirmation path are visible in the first viewport. The authenticated disposable Core readback remains `planned` with zero actions. The four native assertions establish rendered section focus/visibility and no decision; they do not establish OS keyboard focus or owner GUI approval.

An independent `npm test -- --run src/App.test.tsx` run passed **7 tests; exit 0**, including the opt-in review handoff regression. **The review-destination P2 is resolved at this bounded source/renderer/Core boundary. Frozen scores remain 7.9/10.** Remaining P2s are owner motion/native OS acceptance and plaque/footer finish. No additional observed material correctness failure was found in this scoped verification. This was not a general security audit or full independent test-suite run.
