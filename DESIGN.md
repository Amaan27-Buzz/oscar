---
name: OSCAR
description: Quietly Alive — warm, restrained, tactile software with continuous state-driven motion.
colors:
  desktop-workspace: "#F5F1E7"
  desktop-rail: "#ECE7DD"
  desktop-foreground: "#1A1B18"
  desktop-selection: "#DED7C9"
  canvas: "#F5F1E7"
  canvas-raised: "#FAF7EF"
  surface: "#FFFDF8"
  ink: "#1A1B18"
  graphite: "#77766B"
  hairline: "#DDD7CA"
  oscar-blue: "#2F8FF5"
  oscar-blue-deep: "#1D6FD6"
  oscar-yellow: "#FFC83D"
  expression-red: "#EF4348"
  warning: "#D98B45"
  critical: "#D94F45"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "clamp(2.5rem, 6vw, 4.5rem)"
    fontWeight: 600
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0"
  mono:
    fontFamily: "ui-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.45
rounded:
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "24px"
  round: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
  4xl: "96px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "12px 18px"
  button-secondary:
    backgroundColor: "{colors.canvas-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "12px 18px"
---

# Design System: OSCAR

## Active Desktop architecture — Group 2.5A

Desktop now separates a tiny expressive **Companion** from a full **Workspace**.
The Companion never contains chat, task lists, approvals or settings pages.
Workspace must use the existing warm-paper canvas (`#F5F1E7`), raised canvas
(`#FAF7EF`), ink (`#1A1B18`) and surface (`#FFFDF8`). Owner feedback restored
these canonical values and rejected excess rounded/modal-style components.
Platform Segoe UI carries the Operate/Read hierarchy. Matching warm graphite
dark mode is implemented, with canvas `#1C1E1B`, rail `#23251F`, surface
`#292C25` and paper text `#F3EFE5`. Theme and shortcut choices persist natively. These
requirements do not recolor the canonical Orb or redesign Mobile. Previous
presence-expansion layouts and unapproved Workspace treatments are historical evidence.

See [functional ownership and native boundaries](docs/design/DESKTOP-COMPANION-WORKSPACE.md)
and [actual native review packet](docs/ui/desktop/workspace/README.md).
The rejected [image references](desktop/design/workspace-screens/README.md)
remain archived locally; the actual native packet is the current review surface.
The candidate requires owner visual acceptance before merge.

The [canonical OSCAR Orb](assets/brand/oscar-orb.svg) defines the actual intended
Orb appearance. Use or derive variants from that source; interface tokens above
must not recolor it. See the [brand asset contract](assets/brand/README.md).

## North star

**Quietly Alive.**

OSCAR should feel like a calm piece of advanced personal technology that is already present, not an app that waits to be launched and not a chatbot wrapped in a mascot.

The durable design blend is:

- **70% restraint and whitespace** — confident hierarchy, typography, calm composition, minimal chrome;
- **20% tactile industrial precision** — physical cause/effect, material honesty, precise controls, satisfying state changes;
- **10% approachable personality** — warmth, expression and immediate acknowledgement without becoming childish.

The result should feel premium, warm, sparse, editorial, tactile and professional enough for daily use. Personality comes from state, voice, motion, timing and the OSCAR object — not from decorative AI styling.

## Character before interface chrome — Slice 11

The owner explicitly rejects a static, identical smiling Orb pasted onto three
beige rounded widgets. The old desktop A/B/C screenshots are **unapproved
engineering concepts**, not the final OSCAR character. A useful reference is
a small expressive desktop companion that can signal attention and respond
nonverbally while the larger application remains elsewhere. Study the **quality
of presence and response**, do not reproduce the reference's pixel mascot.

Character work comes **before** final Desktop Slice 12 / Mobile Slice 13
visual styling. Establish the eyes/mark language, gaze, subtle asymmetry,
center-of-mass and puck motion, anticipation, thoughtful timing, blink/recovery,
quiet rest, interruptibility and reduced-motion equivalents in Slice 11.
A smile that never changes conveys no meaningful state. Animations must reflect
actual authoritative operational events; a Persona delivery cue must not
imply a human emotion was detected or a task was verified.

The canonical `assets/brand/oscar-orb.svg` remains unchanged. New reviewed
expressive variants are separately versioned and must remain recognizably OSCAR;
changing the brand identity is an explicit owner decision.

**Quality requirement for GPT-6.1 Sol / High effort:** inspect assets and real
interaction references first; write a design hypothesis; design a coherent
character/movement system; implement a narrow expressive prototype; capture
and critically evaluate motion, timing and tiny-size legibility; iterate
substantively before asking the owner to approve. Do not optimize for speed,
concept count, easy generic cards or automated screenshot PASS.

See [Slice 11 Expression Core](docs/EXPRESSION-CORE.md) and
[canonical slice numbering](docs/SLICE-NUMBERING.md).

## Playful precision

OSCAR can be playful, but playfulness must come from **response and physicality**, not decoration.

Good character:

- a weighted puck shifts toward attention;
- a compact surface expands from the thing that caused it;
- a state resolves cleanly after verification;
- haptics/motion acknowledge input immediately;
- a quiet interface becomes active only when needed.

Bad character:

- giant mascot layouts;
- cartoon-first expressions;
- decorative bouncing;
- sparkles, particles or gradients used as shorthand for intelligence;
- UI that feels like a concept board instead of shipping software.

## Materials and palette

The default world is warm and neutral.

### Neutrals

- **Warm Canvas** `#F5F1E7` — primary app background.
- **Raised Canvas** `#FAF7EF` — subtle elevated/contained areas.
- **Surface** `#FFFDF8` — focused sheets or controls where needed.
- **Ink** `#1A1B18` — primary text and strong controls.
- **Graphite** `#77766B` — secondary text and metadata.
- **Hairline** `#DDD7CA` — restrained separation.

### Identity

- **OSCAR Blue** `#2F8FF5` — presence, active focus and the avatar shell.
- **Deep OSCAR Blue** `#1D6FD6` — pressed/strong presence where required.
- **Presence Yellow** `#FFC83D` — avatar face/puck and rare acknowledgement.
- **Expression Red** `#EF4348` — narrow expression marks, not general UI chrome.
- **Muted Orange** `#D98B45` — warnings/attention where appropriate.

The neutral material system should do most of the work. Blue is OSCAR's presence, not the default color for every button.

### Material rules

Use restrained physical material cues:

- warm paper-like canvas;
- softly painted polymer/satin plastic;
- occasional anodized or rubber-like control surfaces where functionally justified;
- low-contrast contact shadows;
- tiny elevation changes;
- minimal borders.

Do not use obvious neumorphism, glassmorphism, giant soft shadows, glossy toy rendering, cyberpunk lighting or floating card stacks.

**Test:** if removing shadows destroys hierarchy, the layout is wrong. Hierarchy must come from typography, spacing, geometry, alignment, grouping and contrast.

## Typography

Typography should carry more hierarchy than containers.

- Use a sophisticated platform-native/system sans.
- Keep display type sparse and editorial.
- Operational screens should become tighter and quieter.
- Body copy should be short.
- Labels should be direct.
- Use mono only for genuinely technical values.
- Avoid futuristic fonts, tracked-out microtext, giant operational headings and marketing-style type inside everyday product surfaces.

If a compact screen requires many text styles to explain itself, simplify the product hierarchy.

## Composition

Every surface gets **one dominant idea**.

Examples:

- OSCAR Mobile Home → OSCAR presence + whether anything needs attention.
- Listening → an active conversational turn.
- Sentry → current awareness + the one thing worth surfacing.
- Worker detail → responsibility + current meaningful state.
- Permission → consequence + decision.

Prefer:

`state → contextual control → action → detail on demand`

not:

`sidebar + topbar + cards + metrics + graphs + AI panel`.

Whitespace must feel intentional. Large empty areas that exist only because the generator had nothing to place are not restraint.

## Progressive disclosure

Normal state should be extremely simple. Complexity exists one layer deeper.

Example:

```text
Everything is quiet.
  ↓ inspect
Why OSCAR believes that.
  ↓ inspect deeper
Device/source/evidence detail.
```

Do not put World Model, evidence, capability and telemetry detail on the first surface simply because the system has those concepts.

## OSCAR object / avatar

OSCAR's blue shell + yellow puck is a functional presence object, not a mascot illustration.

- keep it small-to-medium in everyday surfaces;
- scale it up only when a dedicated interaction moment justifies it;
- use position, weighting and motion before facial expression;
- keep facial marks minimal;
- preserve the canonical Orb's curved wink; avoid unrelated added expressions;
- serious work should reduce playful movement, not change the identity.

The puck behaves like a **weighted magnetic/joystick object** with inertia, slight overshoot and controlled settling.

## Presence, voice and Sentry semantics

Do not design OSCAR around a permanent `Talk to OSCAR` / `Type instead` choice. OSCAR may already be locally aware.

Keep these states distinct:

### Sentry aware

Local low-cost acoustic awareness may be active for wake word, VAD/speech presence, Voice Map events, configured sound events and deterministic hot/reflex commands. This does **not** imply active cloud STT or continuous transcription.

### Listening

A conversational turn is active and speech recognition is running. The UI should clearly show this state.

### Muted

Normal conversational listening is disabled. Allowed safety/reflex/hot commands may remain locally available according to policy. Do not imply the microphone is physically dead unless that is truly the selected privacy state.

### Acoustic awareness disabled

Local acoustic processing is actually disabled. This should be visually distinct from ordinary mute.

### Text

Typing is another input modality for the same OSCAR turn/context. Typing does not imply voice/Sentry has been turned off.

The interface should make OSCAR feel **already present** rather than forcing the user through a giant microphone CTA.

## Fluid motion / continuous interface

Motion is a first-class design material.

Core rule:

> **State A should physically become State B where practical.**

Prefer:

- shared-element transitions;
- geometry morphing;
- contextual expansion from the source element;
- weighted spring motion;
- gesture-linked motion;
- velocity continuity;
- content choreography;
- subtle depth/material response;
- continuous transitions between listening, working, verifying and resolved states.

Avoid:

- screen-wide fades as the default transition;
- teleporting elements;
- random spring/bounce effects;
- decorative particles;
- gratuitous parallax;
- loading theatre that hides real state;
- animation that delays interaction.

Motion must communicate causality: the user should understand where an element came from and where it went.

### Motion character

- **Idle** — almost still; subtle life only.
- **Listening** — focused tension/orientation toward input.
- **Thinking/working** — deliberate movement, not a generic spinner.
- **Verifying** — tighter, more precise movement.
- **Waiting** — relaxed/suspended.
- **Alert** — immediate but controlled.
- **Blocked** — visibly constrained/stalled, not falsely busy.
- **Done** — calm resolution only after verification where applicable.

Typical UI transitions should usually begin within **120–220 ms**; avatar/physical transitions may settle over **180–450 ms** depending on distance and meaning.

### Motion performance

Fluid does not mean heavy.

- interaction begins immediately;
- animation never blocks the underlying action;
- runtime truth must not depend on animation completion;
- prefer compositor-friendly transforms/opacity where possible;
- avoid expensive full-screen blur/filter effects;
- degrade gracefully on low-power/degraded surfaces;
- respect OS reduced-motion preferences;
- the interface must remain fully usable with motion disabled.

## Platform translation

Shared identity does not mean identical layouts.

### OSCAR Mobile / mobile

- feels native and thumb-aware;
- voice/text are peers, not mutually exclusive modes;
- use sheets/notifications/native permission patterns when appropriate;
- avoid generic bottom-tab productivity templates unless the IA truly needs them;
- keep OSCAR present without dedicating most of the screen to the avatar.

### Desktop

- OSCAR can exist as a compact ambient overlay and a deeper workspace when needed;
- contextual expansion should preserve spatial continuity;
- selection/cursor/app context should feel native to the machine;
- do not stretch the mobile composition into a desktop dashboard.

### Physical / Edge

- simplify the same state language;
- prefer direct hardware state over ornamental animation;
- deterministic safety never depends on presentation.

## Reliability as a design property

OSCAR should feel durable under abuse, not merely beautiful in the happy path.

Design every surface for:

- long task names/content;
- zero tasks and many background tasks;
- offline/degraded devices;
- unavailable microphone/network/provider;
- simultaneous alerts and work;
- rapid voice/text switching;
- reduced motion;
- stale/unknown/partial verification states.

The UI should degrade calmly instead of collapsing into modal/error chaos.

Product principle:

> **Beautiful enough to feel premium. Simple enough to reason about. Robust enough to abuse. Graceful when degraded.**

## Design development workflow

Do not attempt to design dozens of screens up front.

Use a Kaizen loop:

```text
research real shipping patterns
→ build one or two real surfaces
→ inspect on target device/viewport
→ critique
→ make a focused improvement
→ verify again
→ repeat
```

For UI work:

- study real shipping applications before drawing when a design-research tool is available;
- Appllama MCP/App Design Skill may be used as a research aid when connected;
- Impeccable may be used as a design critic when available;
- these tools are development aids, not product/runtime dependencies;
- build real UI in code once a direction is promising;
- do not mass-generate the whole product as static images;
- use image generation for original supporting assets/illustrations/hero imagery where valuable, not as the canonical UI system;
- establish patterns only after they survive actual implementation and visual review.

Motion is developed with layout, not sprinkled on as a final polish pass.

## Anti-slop gate

Reject or redesign if several are true:

- it could be a generic AI SaaS template with the logo swapped;
- the avatar dominates the product rather than serving it;
- the composition is a card grid/dashboard wall;
- the interface relies on purple/blue glow, glass or fake telemetry;
- there is a giant microphone/chat CTA despite OSCAR already being present;
- mobile is merely desktop scaled down or vice versa;
- blue buttons appear everywhere;
- whitespace feels accidental;
- the screen looks like a poster/moodboard instead of daily-use software;
- animation continues with no meaningful state change;
- the UI says `Working`/`Done` while runtime evidence says blocked/verifying/partial.

## Do

- make the interface quiet until it needs to respond;
- use typography and composition before containers;
- let motion explain state and causality;
- preserve one intelligence across voice, text, mobile, desktop and physical surfaces;
- progressively reveal complexity;
- use real system state to drive labels/avatar/motion;
- test degraded/long-content/low-power states early;
- visually inspect on real target sizes before calling UI work complete.

## Don't

- build a chatbot shell;
- build a generic AI dashboard;
- use a permanent chat sidebar as the main information architecture;
- fill screens with KPI cards, fake graphs or feature boxes;
- make Sentry look militaristic or surveillance-heavy;
- make OSCAR childish because it has a face;
- use another personal project as placeholder content for OSCAR design exploration;
- mass-produce static mockups before the visual language has survived implementation;
- copy reference products literally. Borrow principles and patterns, not surfaces.

### Owner-feedback Workspace rhythm — 2026-10-13

The Workspace toolbar has balanced 24px edge insets; page content shares an
860px measure with 32px gutters, reducing to 24px on narrow Windows windows.
Page headings use one scale. Stable scrollbar gutters preserve the content axis
between Conversation and scrollable tools. Section/control groups use 24/32px
spacing. Devices is an executor-scoped capability catalog with disclosure rows,
not a device-health dashboard. Preferences uses visual appearance previews,
native shortcut state and distinct voice/presence/privacy groups.

Navigation selection glides over 260ms; routes settle over 220ms and capability
details over 180ms. Motion follows owner interaction, never fabricates activity.
Reduced motion removes movement and smooth scrolling. Diagonal arrow glyphs
are not used for local navigation or window controls.

### Current owner material correction — 2026-10-13

The owner explicitly selects restrained neumorphism across the Workspace.
Raised buttons, recessed fields and pressed selections use paired directional
soft shadows on the canonical paper/graphite surfaces. Orb blue is an accent:
light primary `#236891`, dark primary `#A8D3E9`, selected surface `#E2E9E7` /
`#293B40`. Explicit boundaries and focus outlines remain; low-contrast decorative
shadows never carry the only state information. This supersedes earlier flat
control styling. Devices uses executor/capability selection with a focused
inspector, superseding the rejected full-width capability-row layout.

### Owner correction to control depth and product copy — 2026-10-13

The owner rejected heavy inset controls. The active treatment uses one subtle
raised button shadow and explicit field boundaries. Selection uses accent color
and border; button shadows never simulate recessed dents. The composer is a
content-sized, bounded textarea with no resize handle. Act uses grouped fields
and inspectable permission details. Activity uses task selection and a focused
result/approval pane. The prior control-depth descriptions are historical.

Developer session banners/internal labels are not the default product layout.
Real outcome status and unavailable capabilities remain visible. Exact approval
material is preserved; identifiers and verification metadata remain inspectable.
Native reference-session metadata is preserved and disclosed in QA evidence.

### Act composition — owner revision 2026-10-13

Act is a focused operation editor, not a stacked administration form. File
writing groups destination and exact content into one work surface. Context
and permission details form a compact support area. Selectors appear only for
real multiple choices or an explicitly cleared/withdrawn selection. Other
operation-specific inputs and typed requests remain intact. All prior Act
layout descriptions are historical; owner visual acceptance remains pending.
