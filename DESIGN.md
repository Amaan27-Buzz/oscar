---
name: OSCAR
description: Quietly alive ambient intelligence — minimal, tactile, expressive and precise.
colors:
  canvas: "#F7F9FC"
  surface: "#FFFFFF"
  ink: "#0D1B3D"
  graphite: "#66708C"
  hairline: "#DCE3EE"
  oscar-blue: "#2F8FF5"
  oscar-blue-deep: "#1D6FD6"
  oscar-yellow: "#FFC83D"
  expression-red: "#EF4348"
  warning: "#F59E42"
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
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.01em"
  mono:
    fontFamily: "ui-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.45
rounded:
  sm: "10px"
  md: "14px"
  lg: "20px"
  xl: "28px"
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
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "12px 18px"
  voice-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: "12px 16px"
---

# Design System: OSCAR

## Overview

**Creative North Star: “Quietly Alive.”**

OSCAR should feel like a calm piece of advanced personal technology that happens to have character. The interface is sparse, highly legible and deeply responsive. Personality comes from motion, timing, expression, physicality and state — not from visual clutter, fake telemetry, gradients, glass panels or a wall of cards.

The durable blend is **60% Apple-like restraint and native clarity, 20% Teenage Engineering-like tactile industrial character, 10% Duolingo-like friendliness and immediate feedback, and 10% Braun/Dieter Rams-like functional honesty**. These are principle references only; OSCAR must not copy another product’s UI.

The current Sunday concept establishes the intended personality: bright neutral surfaces, deep navy typography, OSCAR blue as the interactive/presence color, yellow as the face/presence accent, minimal red expression marks, large negative space, soft natural depth and a single dominant animated avatar. Kinetable’s “Playful Precision” is the closest existing sibling language, but OSCAR replaces cream/lime hardware materiality with a cleaner blue/yellow ambient-computing identity.

**Key characteristics:**

- minimal structure, high responsiveness;
- one dominant focal element per screen;
- native-feeling controls and platform conventions;
- playful motion with physically believable inertia;
- soft, premium depth rather than glossy spectacle;
- progressive disclosure instead of permanent panels;
- concise human copy;
- serious states that become calmer and more focused, not more visually aggressive.

## Colors

OSCAR is mostly neutral. Color is reserved for identity, state and action.

### Primary

- **OSCAR Blue** (`#2F8FF5`): primary interactive emphasis, focus, listening, active state and the avatar shell.
- **Deep OSCAR Blue** (`#1D6FD6`): pressed/strong emphasis, high-contrast blue states and compact controls.

### Secondary

- **Presence Yellow** (`#FFC83D`): the avatar face, warmth, successful acknowledgement and rare moments of delight. It is not a generic CTA color.
- **Expression Red** (`#EF4348`): facial expression marks and narrow character cues. Do not spread it through ordinary UI chrome.

### Neutral

- **Air Canvas** (`#F7F9FC`): default app canvas.
- **Pure Surface** (`#FFFFFF`): raised or focused surfaces.
- **Deep Ink** (`#0D1B3D`): primary typography and strong controls.
- **Graphite** (`#66708C`): secondary copy and metadata.
- **Hairline** (`#DCE3EE`): dividers and subtle borders.

### Named rules

**The Presence Rule.** Blue and yellow signal OSCAR’s presence; they are not decorative wallpaper.

**The Red Restraint Rule.** Red is expression or genuinely critical state. If a screen looks “red-themed,” it is wrong.

**The No AI Gradient Rule.** Do not use purple/blue glow gradients, aurora backgrounds, glassmorphism or neon bloom as shorthand for intelligence. Soft physical light or a restrained state halo is allowed when it explains depth or attention.

**Dark mode.** Use deep graphite/navy neutrals, not pure black cyberpunk. Preserve readable, tactile surfaces and keep avatar colors controlled rather than glowing.

## Typography

**Display Font:** native/system sans stack.
**Body Font:** native/system sans stack.
**Technical Font:** platform-native mono stack.

**Character:** confident, clear, slightly rounded through spacing and weight rather than novelty type. OSCAR should feel advanced because of composition and behavior, not because every label looks “futuristic.”

### Hierarchy

- **Display** — 40–72 px, 600, tight tracking; sparse hero statements, onboarding moments, major empty states.
- **H1** — 32–44 px, 600; top-level surface title.
- **H2** — 24–32 px, 600; major section.
- **H3** — 18–22 px, 600; local task/state group.
- **Body** — 15–17 px, 400; conversational copy and explanations.
- **UI** — 13–15 px, 500–600; controls and compact status.
- **Micro** — 11–12 px, 500; secondary metadata only.
- **Mono** — 12–14 px; technical values, logs and code views only.

Avoid all-caps except for tiny technical/status labels where it materially improves scanning. Avoid excessive letter spacing. Avoid “tech startup” display typography.

## Layout

Use a 4 px base grid with a primary rhythm of `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96`.

The default surface should usually contain:

1. one clear focal state or object;
2. one contextual control region;
3. one obvious next action;
4. secondary detail only when requested.

On Sunday and voice surfaces, the avatar is usually the hero. On desktop, the current task/state may share the stage with the avatar, but the app must never collapse into a dense assistant dashboard.

Prefer contextual sheets, inspectors, transient rails and native disclosures over permanent sidebars. A sidebar is justified only when the task genuinely requires persistent navigation, not because desktop software “normally has one.”

Use generous whitespace. Marketing/onboarding can be significantly airier than operational screens. Technical views may become denser, but must preserve hierarchy and direct manipulation.

## Elevation & Depth

Depth should feel physical and soft:

- broad, low-contrast shadows;
- subtle contact shadows beneath the avatar/puck;
- restrained tonal layering;
- minimal borders;
- no floating glass-card stacks.

Raised surfaces exist to explain focus, grouping or physical separation. Do not create a card just to hold every piece of content.

The avatar may use more dimensionality than surrounding UI because it is a character/object. Its blue shell and yellow face can carry soft highlights and shadow, but should remain clean enough to work at icon size.

## Shapes

The visual language is soft but not pill-everything.

- buttons: ~10–14 px radius by default;
- contextual panels/sheets: ~14–20 px;
- voice input surfaces: larger soft radius is allowed;
- compact status chips: pill only when the semantics are genuinely chip-like;
- avatar: circular shell + circular face/puck is intentional and iconic;
- hardware/desktop controls may use more manufactured, tactile geometry where useful.

Avoid generic SaaS rounded-card grids. Avoid decorative blobs unrelated to the avatar or actual state.

## Components

### OSCAR avatar

The blue shell/yellow face is a primary interface primitive. The yellow face moves inside the shell like a weighted joystick or magnetic puck. It communicates attention, listening, thinking, speaking, success, confusion, sentry/alert, sleep, mute and error through position, expression and motion.

Motion should have weight: spring, inertia, slight overshoot, quick settling. Direction should have meaning. Random ambient motion is not intelligence.

### Voice surface

The voice interface is a conversation surface, not a transcript-first chat screen. Prefer:

- avatar/state first;
- one concise state label;
- waveform only while it carries live information;
- obvious mic/stop/cancel affordances;
- transcript/details on demand.

### Cards and panels

Use sparingly and contextually. Prefer one meaningful surface over several small cards. If a card exists, it should own a task, state or actionable object.

### Buttons

Primary actions are confident and compact. Use deep ink or OSCAR blue depending on the surface. Avoid giant gradient CTAs, pill buttons by default, excessive icon-only controls or generic sparkle icons.

### Icons

Use simple line icons with consistent optical weight. Familiar platform/system metaphors are preferred. The avatar should represent OSCAR itself; do not use a sparkle/wand icon as the default AI symbol.

### Copy

Short, direct and human:

- `I’m here.`
- `Looking into it.`
- `Keep Codex running.`
- `Turn Sentry off.`
- `Ask OSCAR…`

Avoid corporate workflow language, unnecessary confirmation copy and anthropomorphic filler that slows the user down.

### Motion

Most UI transitions: **120–220 ms**.
Avatar/physical state transitions: **180–450 ms** depending on travel and meaning.
Longer transitions are reserved for onboarding or deliberate scene changes.

Animate cause and effect, not decoration. Respect reduced motion. Never hide critical state behind animation timing.

## Do's and Don'ts

### Do

- make the interface feel quiet until it needs to respond;
- let the avatar carry character while the rest of the UI remains disciplined;
- use real system state to drive animation and labels;
- use progressive disclosure;
- keep controls native and obvious;
- make voice, touch, keyboard and text feel like one system;
- create one memorable interaction per surface rather than ten micro-effects;
- visually verify desktop and mobile/native states before calling UI work complete.

### Don’t

- build a generic AI SaaS dashboard;
- use a permanent chat sidebar as the main information architecture;
- use glassmorphism, neon HUDs, purple gradients or meaningless particle fields;
- fill screens with KPI cards, fake telemetry or feature grids;
- make every control rounded/pill-shaped;
- use heavy decorative illustrations when the avatar, task or real object can carry the screen;
- make Sentry look militaristic or cyberpunk;
- make OSCAR childish just because it has a friendly face;
- let personality interfere with safety, clarity or speed;
- copy Apple, Teenage Engineering, Duolingo or Braun literally. Borrow principles, not surfaces.
