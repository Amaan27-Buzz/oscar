# Research and previous-study critique

Research date: 2026-10-09. Sources are design inputs, not proof of this prototype.

## What was inspected

Project: AGENTS, README, ENGINEERING, PRODUCT, ARCHITECTURE, ROADMAP,
SLICE-NUMBERING, DECISIONS, EPISTEMIC-INTEGRITY, DESIGN, TASTE, EXPRESSION-CORE,
UI-AVATAR, SURFACES, PERSONA, brand README, source SVG and oscar-ui skill.
Historical PR #16: actual 10R.1 contact sheet, REVIEW.md and Exploration.tsx from
its branch. No merge, cherry-pick, modification or dependency.

The owner's companion screenshots are **not attached to the current chat and
were not found in the accepted tree**. Their qualities are taken from the
owner's written brief; no screenshot-level inspection of them is claimed.

## Why A/B/C did not produce character

All nine idle/running/offline captures show the same disc and wink. The image is
loaded as an intact img; state handling changes text, marks, whole-image motion
and surrounding geometry. It has no facial articulation. Container variants
were the experiment's unit of change, so the character had no independent
performance vocabulary. Moving a static wink cannot communicate a restrained
question or concentration. In particular, the wink survives loss of availability
and visually competes with the serious degraded message.

Preserve: actual SVG identity, stable spatial relationship, truthful labels,
reduced-motion/keyboard support, suppression of stale working claims, isolated
synthetic fixtures. Reconsider fundamentally: identical face across state,
container-led personality, resizing as the main expressive event, permanent
status decoration. This slice evaluates the character without those widgets.

## Primary references and transferable principles

- [Disney Animation — animation process](https://www.disneyanimation.com/process/animation/):
  staging, timing, anticipation and follow-through support believable performance.
  Transfer: unequal timing for eyes/puck/shell and a clean readable held pose.
  Do not transfer theatrical exaggeration, emotional storytelling or perpetual
  secondary motion into a desktop companion.
- [Disney Research — realistic interactive gaze](https://la.disneyresearch.com/publication/realistic-and-interactive-robot-gaze/)
  and [paper](https://la.disneyresearch.com/wp-content/uploads/root.pdf): separates
  levels of gaze behavior in an animatronic character. Transfer as a design
  inference: attention can lead posture and hold deliberately. Do not import
  sensing, human tracking, salience inference or lifelike anatomy. OSCAR's gaze
  target in this lab is explicitly chosen by the reviewer.
- [Google Seed Studio / Map — Little Signals](https://experiments.withgoogle.com/little-signals):
  published description of ambient objects communicating with restrained sensory
  cues. Transfer: attention has a budget and information can remain peripheral.
  The page itself failed live opening; the indexed official description was
  available. No film playback or product-hardware inspection is claimed.

These are principle/reference studies, not copied artwork. The laboratory
captures are the only visual evidence of the implemented OSCAR derivative.

## Technique comparison

| Technique | Capability and control | Interruption / reduced motion | Portability, license, complexity |
|---|---|---|---|
| SVG DOM + timestamped requestAnimationFrame | Exact mark/path numbers, deterministic spring sampling, arbitrary scrub | Retarget from sampled geometry/velocity; static equivalent at same logical event | Browser native, no animation license/dependency; math could be translated later, Android feasibility untested |
| CSS transforms / Web Animations | Excellent compositor transforms; poor unified control of custom facial geometry | Cancel/currentTime possible; coordinating many attributes is less direct | Browser native, CSS does not translate to Compose; low setup, higher coordination cost |
| Motion for React | Declarative SVG/transforms and springs, gesture tools | Retargetable animation; MotionConfig reducedMotion | MIT; React-specific runtime, extra dependency, would still need scrub/state arbitration |
| GSAP + MorphSVG | Rich timeline and general path morphing | Strong pause/seek; reduced motion requires explicit policy | No-charge proprietary GSAP license with restrictions; unnecessary for one known cubic path; not a Compose runtime |
| Canvas | Full raster control | Manual timing and reduced-motion policy | Browser native; harder accessibility, tiny-scale inspection and source-art traceability; unjustified here |

Selected: React/TypeScript for controls, SVG for geometry, one finite deterministic
timestamped timeline for motion. No morph library: all mark paths share topology.
No looping idle, no procedural random gaze, no audio or lip sync. This is a lab
implementation detail, **not the 11.3 platform-neutral production contract**.

Current technical primary sources:
[requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame),
[reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion),
[Motion SVG components](https://motion.dev/docs/react-motion-component),
[Motion MIT license](https://github.com/motiondivision/motion/blob/main/LICENSE.md),
[GSAP license](https://gsap.com/community/standard-license/),
[MorphSVG](https://gsap.com/docs/v3/Plugins/MorphSVGPlugin/).
