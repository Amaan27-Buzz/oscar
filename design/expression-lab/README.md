# OSCAR Expression Laboratory

**SIMULATED VISUAL STATE — NO CORE EXECUTION**

Slice 11.1 character language + 11.2 review instrument, now consuming the 11.3
shared engine. V3 direction is approved for continuing engineering; final
cross-device visual quality remains owner review. This is not a production screen.

Requirements: supported Node 24 LTS (24.15+; locally verified 24.19) or Node 26+,
npm, and a browser. No OSCAR services, API keys, microphone or native shell.

```powershell
cd D:\TheDawnlightGroup\DawnlightLabs\oscar\expression
npm ci
npm run build
cd ../design/expression-lab
npm ci
npm test
npm run dev
```

Open `http://127.0.0.1:1511` after starting the local server. `dev` deliberately builds and serves a static preview:
no HMR connection, no inline script exception, no Core connection. Re-run after
source edits. `npm run build` typechecks; `npm run preview` serves an existing build.

## Review

Live study: choose operational and delivery channels independently; compare
requested/resolved state; test unavailable, unknown, mute and owner-attention
conflicts. Play/pause/replay, scrub, change speed, interrupt and return to neutral.
Physical controls bound intensity, weight and explicit gaze targets. None detects
the reviewer, reads their apps or grants authority.

Expression atlas: sixteen derived studies, selectable for live performance.
Geometry & restraint: unchanged source and derivative side-by-side. Size rail:
32/48/64/96/128/192 actual CSS pixels. Reduced motion respects both the local
control and OS preference; state information remains readable and static.

## Architecture

- `src/model.ts`: synthetic studies/vocabulary; imports shared arbitration/motion.
- `src/Orb.tsx`: reexports the shared SVG derivative, preserving source identity.
- `src/EngineProof.tsx`: `/?engine=1` event-driven renderer/fixture inspection.
- `src/Lab.tsx`: reviewer controls and one virtual clock; no runtime adapter.
- `src/*.test.*`: geometry/state/interrupt/component/isolation checks.
- `tools/capture.py`: self-owned built preview + fresh isolated Chromium capture.

The production-facing contract/controller lives in `../../expression/`; an
isolated native sibling lives in `../../mobile/expression/`. Lab controls and
finite demos remain development-only. No Desktop bridge, storage or audio.

## Reproduce evidence

Optional maintainer requirements: Python, Pillow, repository browser extra
(`playwright`), and installed Microsoft Edge. Runtime needs none of them.

```powershell
npm run build
python tools/capture-engine.py
```

The engine tool refuses an occupied port 1512, blocks requests outside its own loopback
origin, uses a fresh browser context with no grants, exercises controls, and writes
three PNG captures plus bundle/artifact hashes under
`docs/design/expression/evidence/engine-v1/`. `capture.py` remains the legacy study
exporter; pass a new iteration name when creating new evidence, preserving archived
v0/v1/v2/v3. Screenshots are actual SVG browser renders; contact strips arrange
captured frames. The GIF is sampled at 10fps for inspection, not a native frame-rate
claim. Initial study-v0/v1 artifacts are historical revision evidence.

Design rationale and owner questions: [brief](../../docs/design/expression/BRIEF.md),
[language](../../docs/design/expression/LANGUAGE.md),
[motion](../../docs/design/expression/MOTION.md),
[research](../../docs/design/expression/RESEARCH.md).
