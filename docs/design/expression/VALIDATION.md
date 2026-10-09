# Slice 11 validation record

## Current 11.3 engineering validation — 2026-10-09

Starting reviewed head: `d992795af3508778a38498f1f9e05d85091c2806`.
Branch: `design/slice-11-expression`; [draft PR #17](https://github.com/amaansyed27/oscar/pull/17) into `work`.
V3 direction is owner-approved for engineering continuation, not blanket visual
acceptance. Slice 11.3 is a reusable presentation foundation, not actual Core,
voice, Desktop bridge or Mobile screen integration. Gate C remains PARTIAL.

- Shared ESM/declarations, plain Node core import, lab TypeScript/Vite build: PASS.
- 35 Vitest tests: PASS, retaining the 22 reviewed-v3 checks and adding contract,
  source/generation/freshness/priority, held speech, explicit accents, heartbeat,
  cancellation, invalidation, finite/reduced reaction recovery and React continuity.
- Shared TypeScript/Kotlin fixtures: 16 original poses, five event traces, eight
  strict malformed-wire inputs. Kotlin numeric agreement tolerance: 0.00001.
- Native JVM tests: five tests PASS. Isolated Compose library/test-APK and accepted
  `:app:compileDebugKotlin`: PASS. `:app` does not consume the expression module.
- API 35 Google APIs x86_64 emulator: three native instrumentation tests PASS,
  zero failures/errors/skips. Actual Compose atlas/compact drawing, lifecycle
  invalidation/new mute semantics and strict Android JSON admission verified.
- Fresh Edge/Chromium render/playback: PASS. Long speech stays held, a permitted
  accent performs broad travel, newer mute stops speech, OS reduced motion is static.
  No external requests or page errors; source hash unchanged and normalized neutral
  canonical/derivative pixel-difference bounding box is null.
- Repository required-file/link/value-silent secret checks, four canonical-numbering
  tests and whitespace checks: PASS. Synthetic runtime imports contain no data,
  audio, Core or execution adapters. Capture tool executed successfully.

[Browser receipt](evidence/engine-v1/react-receipt.json) binds the rendered captures
to the built bundle and canonical hash. The parent inspected the actual React and
native Compose atlases; native anti-aliasing, blur and gradient rasterization differ.
Original v0/v1/v2/v3 evidence is preserved unchanged. Shared sampled geometry and
semantics agree; physical performance, TalkBack, owner naturalness and final target
DPI/cross-device graphical quality remain outstanding.

The initial owned API 36.1 emulator rendered the atlas and completed two test
methods without assertion failures, but graphics DMA/system snapshot crashes
aborted instrumentation teardown. This attempt is **PARTIAL**, not a runner PASS.
The separate API 35 run completed successfully; its native receipt records the
test counts, source/fixture hashes and actual rendered atlas hash.

[Native validation receipt](evidence/engine-v1/android-receipt.json).

### Remote and integration boundary

**LOCAL VALIDATION PASS / REMOTE CI NOT EXECUTED**. At implementation head
`5cd3255220f2b92a5352f87e4142965791550ea3`, both
[synthetic-lab](https://github.com/amaansyed27/oscar/actions/runs/37933229447/job/113828820305)
and [native-expression](https://github.com/amaansyed27/oscar/actions/runs/37933229447/job/113828820794)
have empty step lists. Their failure annotations state that recent account
payments failed or the spending limit needs increasing; the jobs were not started.
This is not a test-run failure. No exact-head CI green or merge approval is claimed.
PR #16 remains open/draft at
`e334c858195091c21cee5aa35b308b5933cc44bd`, read-only and unchanged.
Neither PR merges automatically. Slice 12/13 screen adoption and real runtime
adapters are future authorized work; no production UI is modified here.

## Historical Slice 11.1–11.2 validation record


Status: **LOCAL VALIDATION PASS / REMOTE CI NOT EXECUTED**.
Design status: **OWNER VISUAL APPROVAL REQUIRED**, not final character acceptance.

Baseline: `45bb1459f61308291fec6e4e5885b6c77b707478`.
Initial v2 implementation: `71b999ca605e968b81a9efc7e3ef8ddd47447a24`.
Branch: `design/slice-11-expression`.
[Draft PR #17 into work](https://github.com/amaansyed27/oscar/pull/17).
Historical documentation-only follow-up did not change v2. The subsequent owner
motion revision changes the lab and is captured separately below.

## Owner motion revision — v3

The owner rejected the prior motion as too slight and authorized broader travel.
V3 uses authored phrase/engagement trajectories, default intensity 1.0, and
continuous performed-pose/velocity handoffs between sequence events.
Measured default 340px-stage travel: speech 66.9px x / 61.5px y; executing 61.9px x /
41.1px y. Tests assert a minimum visible displacement as well as bounded geometry.

TypeScript/build and **22 lab tests PASS**. Fresh browser capture checks PASS;
see [v3 receipt](evidence/motion-v3/receipt.json). Canonical bytes and normalized
neutral rendering are unchanged. The independent review found no motion rebuild
necessary but caught GIF aspect-ratio distortion; v3 exports now preserve aspect.
Earlier v0/v1/v2 GIFs are historical and geometrically distorted; use current v3
GIFs or the earlier undistorted PNG sheets. Owner character approval remains pending.

## Initial v2 local checks

- Node 24.19 LTS, npm lockfile: TypeScript + Vite production build PASS.
- 20 Vitest tests PASS: exhaustive operation/delivery degradation combinations,
  mute/owner attention, no success/perception promotion, bounded geometry at
  weight/intensity extremes, interruption pose/velocity continuity, recovery
  cancellation, closed rest, invalid-state fallback, reduced motion, component
  controls and physical slider association, runtime import/API isolation and
  canonical SVG SHA-256 integrity.
- Existing canonical-slice documentation suite: 4 tests PASS.
- Repository required-file, local Markdown link, removed-reference and
  value-silent secret checks PASS; git whitespace checks PASS.
- Maintainer capture script Python compile and actual execution PASS.
- Fresh Chromium 154.0.4258.62 via installed Edge: real-time playback/pause,
  seek, conflicts, keyboard, all 16 studies, OS reduced motion/forced colors,
  390/1280/1440px layouts PASS; no external requests or browser console/page errors.
- Final evidence hashes match files and the built bundle. Normalized neutral
  derivative/source pixel comparison has no difference. Canonical SVG bytes
  remain SHA-256 `728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.
- Independent scoped critique scored its four original findings resolved;
  separate read-only documentation consistency pass completed. Neither reran
  parent tests or certified owner naturalness.

See [capture receipt](evidence/candidate-v2/receipt.json),
[review](REVIEW.md), and [visual packet](README.md).

## Remote CI

GitHub created failure check records, but the jobs did **not execute**. On the
implementation SHA, both the
[Expression lab job](https://github.com/amaansyed27/oscar/actions/runs/37904526461/job/113734670320)
and [repository job](https://github.com/amaansyed27/oscar/actions/runs/37904526381/job/113734669684)
had empty step lists. Their annotations identify failed account payments or the
spending limit as the cause. This is not a test failure or an exact-head green CI.
The PR must not merge automatically.

## Preserved boundaries

PR #16 stayed open/draft with head
`e334c858195091c21cee5aa35b308b5933cc44bd`; no modification, merge or cherry-pick.
Core/Controller/Memory/Runtime/Grid/permissions/Worker/Voice, Mobile/Desktop,
canonical artwork and durable DESIGN/TASTE are absent from the diff.
Pre-existing untracked `.serena/` files and ignored/generated Desktop remnants
are preserved. No cleanup of owner state occurs.

Not run: real Core integration, microphone/audio/lip sync, Tauri/Android/native
or physical-device acceptance, owner naturalness, continuous native performance,
companion-screenshot fidelity. No 11.3, Slice 12, deployment or later work.
Gate C remains PARTIAL. The character is a proposal awaiting owner review.
