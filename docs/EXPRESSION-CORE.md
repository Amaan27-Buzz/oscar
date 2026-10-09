# OSCAR Expression / Character System — Slice 11

**Status:** NEXT / DESIGN FIRST / NOT YET IMPLEMENTED. Canonical IDs are defined in [Slice Numbering](SLICE-NUMBERING.md).

**Order:** 11.1 → 11.2 → owner visual review → 11.3 → 12.1 Desktop Presence → rest of Slice 12 → Slice 13 Mobile. **Full cross-device Avatar/Presence integration is Slice 16** after World Model Slice 14 and commissioning Slice 15.

This is the current single sequential Slice 11, not an extra slice layered on top of old 13A/13B labels. It does **not** authorize World Model, Sentry, full commissioning, or expressive voice-model evolution. It does not change Build Gate C's PARTIAL status or waive any device/owner acceptance.

## Design invariant

OSCAR is one persistent intelligence with one recognizable Orb identity across desktop and Android. The canonical asset is `assets/brand/oscar-orb.svg`. Its original blue shell, yellow puck, distinctive markings, proportions and geometry are the identity baseline. **Do not overwrite, silently redraw, recolor or replace this source.** Derived expressive geometry/animation variants are versioned separately, traceable to the original, and subject to owner visual approval; the unmodified canonical expression is always available.

The expression system is not a second assistant, reasoning engine or emotion recognizer. It renders permitted Core state and restrained Persona delivery without inventing capabilities, emotions, listening or work success.

## 11.1 — Expression vocabulary and character mechanics

Create a reviewable visual-language specification, not production behavior.

Two independent channels:

- **Operational/epistemic state (authoritative):** idle/available, attentive, listening, thinking, executing, waiting/needs owner, speaking, muted, unavailable, error. Keep task progress/verification/permission/voice-state distinctions where needed; never invent activity.
- **Expressive delivery (non-authoritative):** composed, curious, amused, concerned, focused, subdued, resting and other carefully justified cues. These describe **OSCAR's delivery**, not a human's detected emotion. No inferred emotional detection or voice identity/Match authority.

Define each expression's eyes/mark geometry, gaze direction, puck orientation, shell/puck offset, timing, velocity, blink/recovery, intensity and interruption behavior. Preserve recognizability at very small compact sizes. Avoid giant cartoon faces, indiscriminate bouncing, new mascot silhouettes, decorative status theatre or colors that contradict real task state.

Document an explicit **state-priority/arbitration matrix**: availability/privacy/mute and consequential owner attention cannot be hidden behind a playful cue; operational status cannot be mistaken for verification or consent. Provide stable fallbacks for missing/ambiguous state and state source/provenance. A cute or positive expression never denotes task VERIFIED unless Core supplies it.

Outputs: expression catalog, reference stills/diagrams, state/event mapping, transition table and visual acceptance criteria.

## 11.2 — Standalone interactive Expression Lab

Build a **non-executing development-only** interactive prototype of the canonical Orb's permitted expressions and transitions, before changing OSCAR Desktop or Mobile product UIs.

Controls: manually select operational state and delivery cue, scrub transitions, adjust intensity/tempo within safe visual bounds, demonstrate idle recovery, interrupt an animation, toggle reduced motion, try small/DPI-scaled sizes and compare side-by-side. All inputs in this lab are labeled **SIMULATED VISUAL STATE**; do not impersonate real microphone, hearing, cognition, emotion detection, task status or Core execution.

Explore a small number of techniques with objective comparisons, such as SVG transforms/path animation, CSS/Motion and (only if justified) GSAP. Prototype in web/React if efficient for desktop, but do not tie the canonical state specification to React. Prefer free/open tooling and no paid runtime/license obligations. Version assets; keep the original SVG untouched.

Deliverables: interactive lab, screenshots/contact sheets for expression states, short animated preview, performance/reduced-motion checks, design decision record and explicit owner approval gate. **Do not promote a visual concept automatically.**

## 11.3 — Shared state/render contract

After the expression vocabulary and prototype are owner-reviewed, formalize a platform-neutral typed schema for operational states, delivery cues, event timestamps, priority, transition request, reduced-motion fallback and safe unknown/unavailable behavior.

Keep authority in Core; the expression controller/renderers can **only portray** state. No permission, approval, task verification, memory or Voice Match/Map decision may originate from an expression.

Deliver distinct adapters/renderer contracts for:
- Desktop: Tauri / React / SVG renderer.
- Android: Kotlin / Compose renderer.

Equivalent semantics and recognizable Orb identity on both; platform-native timing and performance. Test transition interruption, state conflicts, small scale, color/contrast, TalkBack/accessibility and reduced motion. **This is a contract/foundation**, not full Mobile/desktop visual redesign or physical-device PASS.

## Return to redesigned experiences

- **12.1 Desktop compact presence:** revisit the existing A/B/C experiments using approved expressive states. The old `10R.1` files are historical evidence, not a signed-off layout.
- **12.2–12.6 Desktop:** Ask, Dictate/Edit, Act/Context, Activity/Approvals and final motion/accessibility.
- **13.1–13.8 Mobile:** reuse the shared expression vocabulary through Compose, with native Android presentation.

Both UI slices and the approved Expression System are required before Slice 20 Unified Alpha PASS.

## Slice 16 — Full Presence integration (later position)

After Slice 14 World Model and Slice 15 commissioning, finish runtime-aware cross-device Presence: compact/expanded/overlay/widget treatments, owner settings, privacy/attention semantics, real-device performance and integrated acceptance. Slice 11 supplies character language and renderer contracts only; it does not fake perception or production deployment.

## Boundaries / acceptance

- Gate C remains PARTIAL. PR #16 remains draft/unmerged until separate review, tests and exact-head CI can run; current GitHub Actions billing limits do not equal green CI.
- Slice 11 can be accepted only as a **design/prototype foundation** after screenshots and transition behavior are reviewed. Neither desktop WebView rendering nor Android emulation proves physical-device acceptance.
- No Elocution inspection or post-alpha Voice Evolution, specialist training, Operating Logs or Home Server migration.
- All concepts and animation are optional presentation—not permission, evidence, task truth or emergency-control logic.

## Character study and deliberate design standard

The owner provided reference screenshots of a small blue expressive desktop companion that appears in the desktop environment alongside quick controls. This **illustrates character, spontaneous-looking responsiveness, nonverbal communication and presence independent of a large chat window**. It is **not** authorization to copy an existing mascot, pixel-art silhouette or copyrighted interface, and it is not permission to replace the canonical OSCAR Orb.

The prior desktop A/B/C concepts were too generic: an unchanged smiling Orb on beige rounded cards, with only labels/status changing, reads as AI-generated UI rather than an autonomous character. **Do not report a similar three-layout exercise as complete character design.**

For future high-effort Sol 6.1 / Codex prompts:

- Examine source SVG path structure, existing art/design contracts, real reference screenshots and the small-scale device constraints. Articulate character traits and behavioral principles **before coding**.
- Seek expressive vocabulary, not random smiley faces: gaze, asymmetric facial movement, anticipation, attention, blinking, delayed responses, microexpressions, shift of center of mass, hesitation and recovery.
- Plan animation and interaction with studied timing, transitions, holds and interruptions. Distinguish expression (a way of speaking/acting) from real sensed human emotion, intent, consent or task status.
- Produce coherent concept rationale, animated state transitions, legibility tests at compact size, reduced-motion fallbacks and iterations guided by visual critique. Do not stop at the first passing implementation or synthetic screenshot.
- Use free/open libraries only when they materially improve the outcome; implementation technique follows the desired movement and character, not vice versa.
- Keep source art immutable and working prototypes isolated; owner must review before production migration.
- Canonical documents: `DESIGN.md`, `TASTE.md`, `docs/ROADMAP.md`, `docs/SURFACES.md`, `docs/BUILD-GATES.md`.
