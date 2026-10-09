---
name: OSCAR Living Desktop Presence — Slice 12.1 candidate
description: A scoped expression of Quietly Alive; a small Orb with a transient writing leaf.
colors:
  leaf: "#fffdf8"
  text: "#242723"
  secondary: "#61645b"
  hover: "#e8e4d9"
  primary-hover: "#3c413a"
  focus: "#1d6fd6"
  attention: "#ffc83d"
  input-rule: "#c5c3b9"
  error: "#8c312a"
typography:
  headline:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  body:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
  caption:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: "16px"
rounded:
  control: "3px"
  leaf: "12px"
spacing:
  small: "8px"
  inset: "16px"
  wide: "24px"
components:
  button-primary:
    backgroundColor: "{colors.text}"
    textColor: "{colors.leaf}"
    rounded: "{rounded.control}"
    padding: "7px 12px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  writing-leaf:
    backgroundColor: "{colors.leaf}"
    textColor: "{colors.text}"
    rounded: "{rounded.leaf}"
    padding: "18px 24px 16px"
---

# Design System: OSCAR Living Desktop Presence

## Overview

**Creative North Star: "Quietly Alive"**

This documents the implemented, proposed Slice 12.1 surface on 2026-10-10. It is
an ordinary scoped extension of the [canonical design](../../../../DESIGN.md)
and [taste](../../../../TASTE.md), not an approved replacement visual world.
The [brief](BRIEF.md) settles the direction: OSCAR is the object the user invokes;
controls grow from its location, then leave it present afterward.

The approved shared character renderer and existing art carry personality. Warm
paper appears only when writing, inspecting state or receiving a short answer.
The canonical SVG remains unchanged. No new raster artwork, font or dependency
ships with this surface. Real rendered captures, including explicitly labelled
synthetic state fixtures, are its visual evidence.

**Key Characteristics:**

- One small presence object; one transient writing leaf.
- Platform typography, short direct actions and restrained material depth.
- Operational truth from Core; local gaze and delivery never confer authority.
- Interruptible retreat, preserved draft and accessible recovery.

## Colors

The frontmatter records scoped values extracted from
[living.css](../../../../desktop/src/presence/living.css). It does not change the
global token values or recolor the shared expression artwork.

### Primary

Deep blue marks keyboard focus and the input caret/rule. The character retains
its existing blue shell, yellow puck and red expression marks from the shared
renderer; those asset colors are not replaced by these interface tokens.

### Secondary

Presence yellow marks the compact owner-review caption and text selection.
It identifies attention rather than claiming approval or completion.

### Neutral

Warm paper supports the leaf, menu and compact caption. Scoped graphite carries
words and the primary action; darker secondary text keeps small metadata readable.
Tonal hover and the input rule provide quiet interaction cues. Muted red carries
actual request errors.

**The Truthful Caption Rule.** Attention, failure, unavailability and unknown state
take precedence over a local interruption cue. The executing pose requires an
executing observation; `awaiting_result` reads Waiting.

## Typography

**Display and Body Font:** Segoe UI, with platform system/sans fallbacks.
No display font or global typography change is introduced.

The compact headline is medium weight; it establishes the current interaction
without a marketing-sized statement. The input and answer are slightly larger
(15px). Primary actions are semibold (13px); ordinary controls use (12px).
Secondary hints and the caption use (11px); the footer uses (10px).

The compact error fallback uses (9px) and the caption remains a legibility risk.
These are observed implementation values, not a new minimum text-size policy.
The owner must judge them at the actual desktop viewing distance. The answer is
rendered in a bounded `pre` region; richer typography belongs to the existing
workspace rather than this candidate.

## Layout

Native rest is (132×148 logical pixels); interaction is (432×384). The leaf has
an outer inset of (16px) and a bottom reserve of (112px), yielding (400×256).
The character is (76px) inside a (92×84) button, with a short caption beneath it.
The Orb's containing object sits (20px) from the right and (25px) from the bottom.

Rust resizing preserves the bottom-right anchor and clamps to the current
monitor work area; explicit edge placement uses an (18px) work-area inset.
Expansion therefore grows up and left from the resting object. Clamping on a
small work area may move that anchor. The leaf scrolls when content needs room,
headlines and task copy wrap, and answer height is bounded (80px) with scrolling.
There is no fabricated responsive breakpoint system.

The header supplies drag, Presence settings and retreat. The body shows one of
the composer, current work/blocker, review request, unavailable state or labelled
answer. The footer opens the existing workspace. Approval attention remains
compact until explicitly invoked and never requests OS focus by itself.

## Elevation & Depth

Depth is local and restrained: leaf shadow `0 6px 12px #171d2625`, menu shadow
`0 4px 10px #171d2630`, and character SVG contact shadow
`0 3px 2px #151a2020`. Typography and placement establish hierarchy before shadows.
No blur, glass or native DWM shadow effect is promised. Windows screenshot black
margins are a `PrintWindow` capture limitation, not the intended surface material.

## Shapes

The leaf retains the canonical gently curved sheet shape; compact controls and
caption use tighter corners from the extracted scoped tokens. The input is flat
with a bottom rule. The character button is circular while its native host remains
a rectangle; alpha margins are not promised to accept click-through.

**The Stable Object Rule.** Preserve the Orb's position through normal invoke and
retreat. Movement should explain interaction rather than decorate idle time.

## Components

### Character and caption

`ExpressionPresence` uses the shared `ExpressionController`. The
`DesktopExpressionAdapter` fences generations, epochs and freshness before text
or actions are accepted. An expired observation becomes unknown and removes
actionable stale copy. Bounded pointer gaze and quiet hover/invocation delivery
change presentation only; they do not extend freshness or change operation.

### Writing leaf and controls

Entry uses transforms from the bottom-right origin (220ms,
`cubic-bezier(.16,1,.3,1)`) with opacity (140ms). Retreat shifts toward the object
(180ms). Reinvo­cation clears the pending retreat, and rejected compact confirmation
restores the open leaf. Reduced motion removes the transform/transition and
retreat delay. Resting expression settles rather than looping indefinitely.

Buttons have a visible blue focus outline (2px, offset 2px); the input has a
label and focused rule. Hidden or retreating leaf controls are inert. Invocation
focuses the input when present; if an asynchronous task removes the focused input,
focus returns locally to the Orb. Escape preserves draft and running work.
Forced colors use system surface/text/button colors while keeping identity art.

### Work, review and answer

Core readback supplies blockers and outcome labels. A bounded local result shows
its supplied epistemic label, with Inspect result and Ask again; it does not
promote reported text into verified fact. Ask again restores the existing draft.
Review opens the existing exact approval/native confirmation path. Activity and
approval hand off to `App`, preserving authority and minimizing this slice.

### Native boundary and tradeoffs

Rust owns transparency, placement, resizing, pin/float/hide and tray recovery.
React owns this composition. Credentials and signing remain outside React.
The new surface is debug/DEV-only; preview fixtures reject execution, approval
and native window operations. The default UI and broader Ask/Edit/Act/Activity
layout are unchanged.

This reuse leaves a visible seam: deeper work becomes the existing opaque warm
workspace rather than a finished continuous leaf-to-workspace morph. The plain
Presence/Close links, familiar underlined composer and tiny caption also remain
conventional. Their refinement depends on owner review, not a global redesign.

## Do's and Don'ts

- **Do** keep the character dominant at rest and disclose controls on invocation.
- **Do** preserve blocked, failed, partial, offline and unknown state explicitly.
- **Do** treat this document's tokens as scoped candidate values awaiting review.
- **Don't** change canonical Orb art or global tokens through this extension.
- **Don't** infer attention, capture context, pin automatically or cancel work on retreat.
- **Don't** treat rendered voice fixtures as commissioned speech/listening.
- **Don't** promote the candidate before owner visual/device review and required CI.

See [REVIEW.md](REVIEW.md) for the finish disposition and evidence limits.
