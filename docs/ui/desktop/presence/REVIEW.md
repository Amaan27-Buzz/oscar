# Slice 12.1 finish review

Date: 2026-10-10. Disposition: **SHIP TO OWNER REVIEW AT CANDIDATE SCOPE**.

The local candidate implements the [brief](BRIEF.md)'s free Orb and transient
writing leaf, using the approved shared expression engine/art and existing native
authority. It is ready for owner inspection, not owner-accepted, integrated or
production-promoted. The default Desktop UI remains unchanged; Slice 12.2 has not
started. This scoped [DESIGN.md](DESIGN.md) records the implementation without
editing the global design system or its Impeccable sidecar.

## Resolved finish findings

All five findings from the independent finish review are resolved in the current
candidate. The finish reviewer independently reran all 25 frontend tests; the
eight tests in [Living.test.tsx](../../../../desktop/src/presence/Living.test.tsx)
cover the narrow behavior, freshness and recovery contracts.

| Finding | Result and evidence |
|---|---|
| Failed retreat left the leaf wedged/inert | Rejected compact confirmation restores the open surface; a later retreat succeeds. Regression test covers failure and retry. |
| Removing the focused composer lost keyboard focus | Local focus recovers to the Orb when task readback removes the input; Escape still retreats. Background owner attention does not steal focus. |
| Interrupted caption masked critical state | Offline, unknown and failed state retain precedence; fresh unresolved state is distinguished from observation expiry. |
| Copy overstated operational certainty | Blockers come from readback; offline explicitly leaves work status unknown; waiting is distinct from executing. Local busy state does not claim Working. |
| Completed result required an unnecessary workspace trip | A bounded, evidence-labelled answer is shown locally. Reported/partial labels remain intact; Inspect result opens deeper detail and Ask again restores the draft. |

The [native result capture](native-verified.png) shows `VERIFIED` and `5` from the
authenticated disposable Core harness. The receipt explicitly records this as
`2+3=5` harness execution, not GUI approval acceptance.

## Validation and provenance

| Check | Supported result | Limit |
|---|---|---|
| Frontend regressions | 25 tests independently PASS; 8 scoped Living tests | Automated behavior evidence, not owner quality acceptance |
| Python/Desktop documentation | 35 Desktop/baseline/presence/canonical-doc tests PASS | Final run uses system Python with cryptography; earlier old-venv skips are not final evidence |
| Shared engine and native checks | Expression Lab 35 tests and Rust 8 tests PASS; Clippy with warnings denied and format PASS | Software checks, not physical acceptance |
| Production and repository checks | Frontend build PASS with fixtures excluded; fixture detector empty; repository/local-link/secret checks PASS | Local checks only |
| Existing native self-check | CNG-PSS signing, UIA/readback, typed Act file, Ask, cancellation, dictate preview, reconnect/native restart/shared tasks and shortcut collision PASS | Microphone NOT RUN; Edit transformation SIMULATED/REPORTED |
| Rendered browser review | Ten labelled synthetic states, no overflow or page errors; DPR 1 / 1.25 / 1.5 | Real Chromium renders of synthetic state; not native OS scaling changes |
| Accessibility variants | Reduced-motion static and forced-colors captures | Captured equivalents; no complete assistive-technology audit claimed |
| Native surface | Real Tauri/WebView2 and authenticated disposable Core | Actual Windows scale 125% only |
| Window dimensions | Rest 132×148 logical / 165×185 physical; interaction 432×384 / 540×480 | Other native DPI, multiple monitors and taskbar configurations NOT RUN |
| Native recovery | Pin/float/edge requests, close-to-tray and shortcut focus restoration PASS; offline/reconnect epoch rotation PASS | No universal desktop-placement or owner workflow acceptance |
| Transparency | WebView alpha 0–255 VERIFIED | Wallpaper compositor capture INCONCLUSIVE; target could not be foregrounded over the owned backdrop |
| Interrupted invoke/retreat | [Sequence GIF](native-invoke-retreat-reinvoke.gif); sampled and distinct encoded frame counts are recorded in the native receipt | Real rendered content aligned bottom-right on a neutral canvas, not an OS desktop recording |
| Ordinary retreat | [Retreat GIF](native-retreat.gif); capture duration and frame accounting are recorded in the native receipt | Coarse frame sampling cannot establish full motion smoothness |
| Quiet rest/performance | 0 puck attribute mutations over 1.2s; native frame scheduling median 6.1ms / p95 6.3ms | WebView scheduling/SVG rest only; no whole-process CPU/GPU or universal frame-rate claim |
| Identity/art | Canonical SVG SHA-256 preserved in [receipt](receipt.json) | No shipped generated raster assets; screenshots are review artifacts |
| Remote exact-head CI | UNAVAILABLE: owner reports GitHub HTTP 403/access restriction | No CI PASS and no bypass attempted |
| Owner acceptance / physical voice | NOT RUN | Real speech/listening, prosody, wallpaper/fullscreen and daily-use quality remain uncommissioned/unaccepted |

Primary evidence is the [browser/artifact receipt](receipt.json),
[native receipt](native-receipt.json), [native invocation](native-invoked.png),
[offline](native-offline.png), [restored](native-restored.png) and
[review sheet](review-sheet.png). The sheet and voice/executing fixtures are
explicitly synthetic, rendered UI. Native captures use the private disposable
test fixture and real authenticated runtime. No owner recording, credential or
private archive is a shipping visual asset.

## Remaining quality limits

The free object gives rest a stronger identity than the old status-widget
composition. The writing leaf has a clear job and stays subordinate to the Orb;
the result now closes a useful local loop. These are reasons to proceed to review,
not evidence that the owner will approve the appearance.

- The (11px) compact caption and secondary hints, (10px) footer and (9px) compact
  error may be too small at the owner's normal viewing distance. The caption still
  feels like a small conventional status badge. Actual legibility is undecided.
- The plain Presence/Close actions, underlined textarea and familiar rounded
  paper sheet remain conventional. Character and motion supply the distinction;
  further chrome styling is not justified before owner feedback.
- Existing Activity/approval becomes an opaque workspace with no finished shared
  transition. Reuse protects exact approval authority, but the handoff is abrupt.
- `PrintWindow` paints alpha margins black. Content GIFs and verified WebView alpha
  cannot prove wallpaper blending, real desktop motion or native edge clipping of
  shadows/focus outlines. Fixed rectangular bounds and transparent hit area need
  owner desktop inspection; click-through and fullscreen heuristics are absent.
- GIF encoding contains fewer distinct frames than sampling. Evaluate the live
  candidate for timing and interruption feel; the GIF is a limited record.
- Fixed sizing and work-area clamping have unit/browser evidence beyond 125%,
  not actual multi-monitor/native scaling acceptance. There is no saved geometry,
  inferred attention or automatic retreat of drafts.

## Owner boundary

Use the [README](README.md) to run the bounded preview or native candidate.
Review tiny-caption legibility, the stable object/leaf relationship, invocation
and rapid retreat/reinvoke, degraded state, result usefulness, and the deeper
workspace seam on the actual desktop. Wallpaper, obstruction/click footprint,
fullscreen, other native DPI and multi-monitor quality remain open.

Owner visual approval, commissioned voice and required remote CI remain distinct
from the recorded local checks. This review authorizes no broader surface
redesign, push, merge, release or subsequent slice.
