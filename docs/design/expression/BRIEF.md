# Slice 11.1–11.2 — Character study

Status: **DESIGN PROPOSAL / SIMULATED LAB / OWNER VISUAL APPROVAL REQUIRED**.
Starting SHA: `45bb1459f61308291fec6e4e5885b6c77b707478` (verified origin/main and origin/work).
Branch: `design/slice-11-expression`. No production renderer contract (11.3).

## Character hypothesis

OSCAR notices before it performs. Attention leads with the red marks; the weighted
yellow puck follows; the blue shell has the least movement. Personality comes
from that ordering, the unequal marks, and the willingness to stop moving.
It is a composed presence with a dry, occasional playful inflection. It does not
seek reassurance, act hurt when ignored, celebrate unverified work, or stare at
the user continuously. Quiet is an authored behavior, not missing animation.

The lab is an evaluation instrument. The Orb leads a neutral stage, controls are
flat and peripheral, and all operational information is readable separately.
It is not a proposed Desktop window or Mobile screen. System typography inherits
DESIGN.md; identity gradients belong only to the source artwork.

## Source geometry, not a replacement mascot

The 582-square SVG places the blue shell at (288,292), radius 264. Its painted
radial highlight originates at 36%/17%. The ochre puck side is (374,289), radius
187; the yellow front is (381,289), radius 177. This 7-unit inset makes the left
rim visibly heavier. A shadow (-7,+15), blur 7, grounds it against the shell.
The yellow highlight originates at 42%/32%.

There is **no mouth**. A red disc at (299,275), radius 42, is paired with a much
smaller cubic wink: M426 276 C444 261,465 258,485 272, stroke 21. Their asymmetry
is the strongest differentiator. Symmetric eyes plus a smile would erase it.

Versioned studies v1/v2 retain every shell/puck circle, gradient and shadow value.
Only the movable group and two red marks change. The canonical source remains
available alongside the derivative. Its SHA-256 is
`728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.
No pupils, mouth, eyebrows, limbs, costume or separate head are introduced.
Changing the wink curvature/opening and disc aperture is an **explicit expressive
derivative proposal**, not approved brand art. Owner review must decide whether
the asymmetric mark remains legible as an eye in serious states.

## Owner steering during this study

On 2026-10-09 the owner additionally authorized opening the blinked eye and
freer, fun yellow-puck movement while active or speaking. Candidate v2 unfolds
the wink into a **smaller** second eye, retaining the unequal proportions and
canonical resting wink. Activity and speech have bounded, finite arcing puck
travel; privacy, seriousness and degraded-state restrictions still apply.
This authorizes exploration, **not visual acceptance or starting 11.3**.

## Three approaches considered

1. Move the intact brand image. Safest identity preservation; insufficient facial
   vocabulary. This is the historical failure, retained only as a comparison.
2. Two-mark articulation (selected for study). Lid/aperture, arc tension/opening, unequal
   mark displacement, puck orientation and timed return. Retains the signature;
   concern and speech are deliberately abstract and need owner interpretation.
3. Replace unequal marks with symmetric eyes and a mouth. Easier literal emotion
   and speech, but becomes a familiar emoji/robot face; rejected. Later owner
   permission unfolds the existing smaller mark without a mouth or pupils.

## Process and boundaries

A: read actual project/source, inspect historical rendered A/B/C and their code,
research primary animation/gaze/ambient-presence sources and current tooling.
B: establish this hypothesis and the geometry/state/motion rules before code.
C: implement isolated movement studies with repeatable timeline samples.
D/E: capture and inspect actual browser output, revise at least twice for named
character/motion deficiencies, preserving before/after evidence.
F: deliver lab, tests, artifacts and critique for owner visual review.

Only lab source, its own package/config/tests/capture tool, expression documents
and current Slice 11 status links may change. No existing caller consumes this
prototype. No runtime, microphone, credential, personal-data or native bridge
imports. No persistent storage, capability execution, emotion detection or
permission semantics. PR #16 is inspected read-only and remains untouched.
Canonical 00–20 numbering and Gate C PARTIAL remain intact.

## Visual acceptance questions

- Does the one-disc/one-arc face still read as OSCAR at 32–48px?
- Is serious concentration sufficiently distinct without looking angry?
- Does the gaze → puck → shell ordering feel attentive rather than restless?
- Are concerned/unsure useful, restrained delivery cues rather than cartoon pain?
- Is the newly opened smaller eye still recognizably OSCAR?
- Is the freer mouthless speaking arc playful enough without becoming distracting?
- Which expressions need less amplitude before any 11.3 work?

Owner acceptance is not inferred from build, tests, critique or screenshots.
