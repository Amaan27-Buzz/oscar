# Critical evaluation and revision record

**Owner visual approval pending.** Technical checks and design critique are not
acceptance of the character. Evidence is actual isolated Chromium rendering.

## Study v0 — initial mechanics

The first atlas showed meaningful puck/gaze variation but the red disc narrowed
as an ellipse. That reads as squashed artwork rather than a directed lid. Focus
and concern were still too close to a relaxed wink; concern's shallow curve was
particularly ambiguous. Face and gaze used the same 240ms timing, undermining
the principle that attention leads posture. The lab was usable but the character
needed a mechanical revision.

## Revision cycle 1 — lids, tension and timing

Changed the disc mechanism from ellipse scaling to a clipping lid over the
original round mark, with an independently angled lid. Reworked concern's arc
control points and the focus/verification aperture. Separated gaze acquisition
(95ms), arc tension (170ms), lid change (210ms) and weighted puck/shell response.
Shell effective weight increased relative to puck. These changes affect face
geometry and motion sequencing, not interface decoration.

The v1 actual atlas confirms that serious states now have a recognizable lid
instead of a small oval. Concern's small arc bends rather than keeping the idle
wink. The tiny contact sheets still show that the full sixteen-label vocabulary
cannot be read from a 32px face alone. The vocabulary therefore describes
performance roles, not sixteen universally distinguishable static emotions.

## Revision cycle 2

The independent reviewer found two P1 character issues: standalone surprise,
amusement and pleasure ended in an indefinite hold; and generic intensity
blending meant asleep never fully closed its eye. It also identified simultaneous
gaze/puck onset and mobile controls being separated from the character by the
entire specimen rail. Its disposition was **FIX / RECAPTURE at prototype scope**.

Changes:

- Added authored reaction → hold → recovery beats, preserving operational truth.
  New events replace the entire timeline, including queued recovery.
- Made closed-eye rest a posture invariant at intensity .35/.75/1; closure becomes
  a quiet curved mark, not a faint engaged aperture. Blink closes both marks.
- Added a 45ms eye lead before physical travel from rest. Moving interruptions
  preserve velocity and skip that delay, with immediate semantic cancellation.
- Moved primary state/conflict controls directly after transport on narrow
  layouts, kept secondary controls below specimens, and labeled compact samples.
- Applied subsequent owner steering: wink opens into a smaller eye; speech and
  executing have finite playful puck arcs with greater travel. Neutral still
  returns to the exact original source geometry. No mouth or pupils were added.

Capture also found physical range labels pointing to their output elements.
Explicit input associations fixed keyboard/accessibility targeting; a component
regression and actual capture exercise all physical controls.

An exact neutral comparison initially differed because side-by-side specimens
were rasterized at different fractional pixel phases. At a shared integer origin,
source and derivative match pixel-for-pixel. Source bytes retain the original hash.
This is a render-geometry check, not owner design acceptance.

Final independent verdict is recorded in [review](REVIEW.md). No automatic visual
acceptance or production compatibility is claimed.

## Owner revision — v3 broader movement

The owner rejected v2's motion as too slight despite the prior scope-limited
review. That feedback outranks the earlier reviewer verdict. The old speaking
accent lasted only one second and its source-unit amplitude translated to a
small screen displacement. Simply raising a few values would still produce a
short, easily missed performance.

V3 authors a longer broad phrase trajectory and a separate active engagement
sweep: anticipation, high/low travel, counter-lean and follow-through. The default
intensity is now 1.0. Attention, curiosity and surprise also have clearer posture.
Sequence transitions sample actual travel and velocity rather than snapping to
the prior static target. Tests require meaningful minimum default displacement,
not merely finite coordinates. Rest/privacy/degraded states retain their restrictions.
New evidence lives in `evidence/motion-v3/`; v2 evidence remains intact.

## Evidence scope

`evidence/study-v0/` and `evidence/study-v1/` preserve the implemented iterations.
`evidence/candidate-v2/` includes their comparison, opened-eye atlas, reaction
recovery, playful speech, closed-rest intensity and reduced-motion studies.
Receipts bind compiled assets and PNG/GIF hashes. GIFs arrange deterministic
100ms browser timeline samples; real-time play/pause is tested separately.
No screenshot is generated artwork or a real Core/device state. Owner companion
images were unavailable in this chat; only their written intent was available.
