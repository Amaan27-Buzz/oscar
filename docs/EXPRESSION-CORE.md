# OSCAR Expression Core — early Slice 13A

**Status:** PLANNED / OWNER-PRIORITIZED ON 2026-10-09 / NOT IMPLEMENTED.

**Order:** 13A.1 → 13A.2 → 13A.3 → resume 10R.1 Desktop Presence → other 10R and 09R work. The remaining full Presence/Avatar integration is **13B**, scheduled in the original Slice 13 position after Slices 11–12.

This is a deliberate early extraction of the visual/expression foundation, **not** authorization to begin World Model, Sentry, full commissioning, full expressive voice/model evolution or all of Slice 13 early. It does not change Build Gate C's PARTIAL status or waive any device/owner acceptance.

## Design invariant

OSCAR is one persistent intelligence with one recognizable Orb identity across desktop and Android. The canonical asset is `assets/brand/oscar-orb.svg`. Its original blue shell, yellow puck, distinctive markings, proportions and geometry are the identity baseline. **Do not overwrite, silently redraw, recolor or replace this source.** Derived expressive geometry/animation variants are versioned separately, traceable to the original, and subject to owner visual approval; the unmodified canonical expression is always available.

The expression system is not a second assistant, reasoning engine or emotion recognizer. It renders permitted Core state and restrained Persona delivery without inventing capabilities, emotions, listening or work success.

## 13A.1 — Expression vocabulary and mechanics

Create a reviewable visual-language specification, not production behavior.

Two independent channels:

- **Operational/epistemic state (authoritative):** idle/available, attentive, listening, thinking, executing, waiting/needs owner, speaking, muted, unavailable, error. Keep task progress/verification/permission/voice-state distinctions where needed; never invent activity.
- **Expressive delivery (non-authoritative):** composed, curious, amused, concerned, focused, subdued, resting and other carefully justified cues. These describe **OSCAR's delivery**, not a human's detected emotion. No inferred emotional detection or voice identity/Match authority.

Define each expression's eyes/mark geometry, gaze direction, puck orientation, shell/puck offset, timing, velocity, blink/recovery, intensity and interruption behavior. Preserve recognizability at very small compact sizes. Avoid giant cartoon faces, indiscriminate bouncing, new mascot silhouettes, decorative status theatre or colors that contradict real task state.

Document an explicit **state-priority/arbitration matrix**: availability/privacy/mute and consequential owner attention cannot be hidden behind a playful cue; operational status cannot be mistaken for verification or consent. Provide stable fallbacks for missing/ambiguous state and state source/provenance. A cute or positive expression never denotes task VERIFIED unless Core supplies it.

Outputs: expression catalog, reference stills/diagrams, state/event mapping, transition table and visual acceptance criteria.

## 13A.2 — Standalone interactive Expression Lab

Build a **non-executing development-only** interactive prototype of the canonical Orb's permitted expressions and transitions, before changing OSCAR Desktop or Mobile product UIs.

Controls: manually select operational state and delivery cue, scrub transitions, adjust intensity/tempo within safe visual bounds, demonstrate idle recovery, interrupt an animation, toggle reduced motion, try small/DPI-scaled sizes and compare side-by-side. All inputs in this lab are labeled **SIMULATED VISUAL STATE**; do not impersonate real microphone, hearing, cognition, emotion detection, task status or Core execution.

Explore a small number of techniques with objective comparisons, such as SVG transforms/path animation, CSS/Motion and (only if justified) GSAP. Prototype in web/React if efficient for desktop, but do not tie the canonical state specification to React. Prefer free/open tooling and no paid runtime/license obligations. Version assets; keep the original SVG untouched.

Deliverables: interactive lab, screenshots/contact sheets for expression states, short animated preview, performance/reduced-motion checks, design decision record and explicit owner approval gate. **Do not promote a visual concept automatically.**

## 13A.3 — Shared state/render contract

After the expression vocabulary and prototype are owner-reviewed, formalize a platform-neutral typed schema for operational states, delivery cues, event timestamps, priority, transition request, reduced-motion fallback and safe unknown/unavailable behavior.

Keep authority in Core; the expression controller/renderers can **only portray** state. No permission, approval, task verification, memory or Voice Match/Map decision may originate from an expression.

Deliver distinct adapters/renderer contracts for:
- Desktop: Tauri / React / SVG renderer.
- Android: Kotlin / Compose renderer.

Equivalent semantics and recognizable Orb identity on both; platform-native timing and performance. Test transition interruption, state conflicts, small scale, color/contrast, TalkBack/accessibility and reduced motion. **This is a contract/foundation**, not full Mobile/desktop visual redesign or physical-device PASS.

## Return to redesign work

- **10R.1 Desktop compact presence:** revisit the explored B/C compositions using approved expressive states. Preserve the previous three concepts as exploration evidence until a new design is explicitly selected.
- **10R.2–10R.6:** remaining desktop interaction, task, approvals and motion work.
- **09R.1–09R.8 Mobile:** reuse the same expression vocabulary via Compose; keep Android-native layouts and controls.

Individual 10R/09R work may continue in parallel as useful, but expression-dependent visual decisions should wait for 13A review. Both redesign tracks and approved expression integration are required for Slice 17 Unified Alpha PASS.

## 13B — Full Presence integration (original Slice 13 slot)

After Slice 11 World Model and Slice 12 commissioning boundaries, finish full reactive Presence/Avatar behavior: runtime state integration, compact/expanded/overlay/widget treatments, owner settings, multi-device consistency, interruptibility, privacy/attention semantics, accessibility and real-device performance. Do not pull unimplemented World Model/Sentry/commissioning or speculative hardware UI forward into 13A.

## Boundaries / acceptance

- Gate C remains PARTIAL. PR #16 remains draft/unmerged until separate review, tests and exact-head CI can run; current GitHub Actions billing limits do not equal green CI.
- 13A can be accepted only as a **design/prototype foundation** after screenshots and transition behavior are reviewed. Neither desktop WebView rendering nor Android emulation proves physical-device acceptance.
- No Elocution inspection or post-alpha Voice Evolution, specialist training, Operating Logs or Home Server migration.
- All concepts and animation are optional presentation—not permission, evidence, task truth or emergency-control logic.
- Canonical documents: `DESIGN.md`, `TASTE.md`, `docs/ROADMAP.md`, `docs/SURFACES.md`, `docs/BUILD-GATES.md`.
