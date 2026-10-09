# OSCAR Taste

## Current character-first quality bar (2026-10-09)

A warm minimalist UI with the same pasted static smile, status labels and
rounded beige cards **does not count as OSCAR character design**. Before
surrounding interface redesign (Slices 12 Desktop / 13 Mobile), implement and
critically review the genuine expression vocabulary in **Slice 11**.

The desktop-companion screenshots provided by the owner illustrate character
responding to context outside a chat window; they are *behavioral references*
and must never be copied as artwork. Carefully design gaze, microexpressions,
puck mass/settling, attention, anticipation, hesitation, reaction to interruption,
idle rest, recovery and reduced motion. Expressions remain honest about
Core truth and actual permissions.

For GPT-6.1 Sol / High-effort design sessions: research actual interaction
patterns, analyze art geometry, document several reasoned hypotheses, prototype
real animated behaviors, self-critique weak/AI-looking output, iterate, and
show the owner a rigorous comparison before promoting anything. Do not stop
because a screenshot looks passable or tests compile.

[Canonical schedule](docs/SLICE-NUMBERING.md) ·
[Expression plan](docs/EXPRESSION-CORE.md).



This file is the opinionated quality bar for agents designing or reviewing OSCAR surfaces. `DESIGN.md` is normative; this file explains what “good” should feel like when several implementations satisfy the rules.

## The taste in one line

**Warm, minimal and precise — but unmistakably alive.**

OSCAR should feel less like software with an AI feature and more like a responsive object/intelligence that quietly inhabits the device.

## Reference blend

Use references only as principles, never templates:

- **70% restraint / native clarity** — confident whitespace, typography, hierarchy, minimal chrome, finish;
- **20% tactile industrial character** — physical cause/effect, precise controls, satisfying movement, material honesty;
- **10% approachable personality** — warmth, expression and acknowledgement without becoming cute-first.

The result is **Playful Precision** inside the broader **Quietly Alive** identity.

The interface should feel premium and personal while remaining simple enough to use every day. Fun comes from response, motion and physicality rather than decoration.

## What should be memorable

If somebody sees OSCAR for ten seconds, they should remember:

1. the blue shell + yellow puck;
2. the puck behaving like a weighted object rather than a sticker/mascot;
3. how little UI surrounded the important thing;
4. how naturally one state transformed into the next;
5. that the software felt composed and useful rather than “AI-themed.”

If they instead remember cards, gradients, giant microphone buttons, chat bubbles or a mascot filling the screen, the design missed.

## Composition rules

### One dominant idea

Every surface should have one primary job.

Examples:

- OSCAR Mobile Home → OSCAR presence + whether anything matters now.
- Listening → an active conversational turn.
- Sentry → current awareness + the one meaningful event.
- Worker detail → responsibility + current meaningful state.
- Permission → consequence + decision.

Do not give five things equal visual weight.

### Whitespace must be intentional

Whitespace is structure, not “nothing to put here.”

Large empty regions are only good when they improve hierarchy, pacing or focus. A mostly empty generated screen with weak composition is not restraint.

### UI appears when needed

Prefer:

`state → contextual control → action → detail on demand`

rather than:

`navigation + toolbar + card grid + status rail + assistant panel`.

### Avoid dashboard gravity

Coding agents tend to turn capable products into dashboards. Resist by default.

A normal OSCAR surface should not become a collection of:

- status cards;
- metrics tiles;
- mini-panels;
- feature boxes;
- badges;
- fake telemetry;
- graphs added for visual interest.

Use the task, object, timeline, conversation state or current environment itself as the interface whenever possible.

## Personality rules

OSCAR is expressive, not mascot-led.

- Calm motion and the canonical Orb appearance are the default.
- The [canonical Orb](assets/brand/oscar-orb.svg) includes a curved wink. Any
  animated wink should acknowledge a real interaction and derive from that source.
- Happy is brief and earned.
- Thinking is focused, not cartoon confusion.
- Sentry is calm and watchful, not angry/security-theatre.
- Errors are clear and composed.
- Serious work reduces playful movement rather than changing the product into another identity.

Character must never reduce trust.

## Presence rules

OSCAR is often already present.

Do not frame ordinary use around a giant `Talk to OSCAR` button or a `Type instead` fork.

Differentiate:

- **Sentry aware** — local wake/VAD/hot-command/Voice Map/sound-event awareness may be active;
- **Listening** — an actual conversational turn is active and STT is running;
- **Muted** — normal conversational listening is off, while permitted local reflex/safety commands may remain;
- **Acoustic awareness disabled** — local acoustic processing is genuinely disabled;
- **Typing** — merely another input mode for the same OSCAR context.

The UI must not imply that typing turns voice architecture off or that Sentry awareness means OSCAR is transcribing the room.

## Motion taste

Motion is one of OSCAR’s primary materials.

### Continuous interface principle

Prefer **state continuity** over page replacement.

Good examples:

- the OSCAR object shifts toward attention, then the listening surface grows from that same region;
- a compact task expands into its detail rather than jumping to an unrelated composition;
- a desktop presence indicator grows into a contextual overlay from its actual origin;
- `Working` tightens into `Verifying`, then resolves into a result without teleporting the UI.

The best transition explains causality.

### Good motion

- shared-element continuity;
- geometry morphing;
- weighted springs;
- meaningful overshoot/settling;
- gesture-linked movement;
- contextual expansion;
- content choreography;
- acknowledgement before cloud response;
- quiet state-driven movement.

### Bad motion

- generic fades between unrelated screens;
- random spring animation;
- bouncing every control;
- endless breathing everywhere;
- decorative particles;
- loading spinners used instead of real state;
- parallax merely because it looks expensive;
- animation that delays the user;
- motion continuing when nothing is happening.

The avatar can be the most animated object, but everything around it still earns motion.

### Motion under load

The product should still feel good when resources are constrained.

- animation never owns correctness;
- interaction begins immediately;
- reduced-motion mode remains complete;
- low-power/degraded surfaces may simplify movement;
- no expensive visual effect is allowed to make ordinary interaction fragile.

## Color taste

Color is identity/state, not decoration.

- Warm cream/off-white canvas does most of the work.
- Graphite/near-black carries typography.
- Blue = OSCAR presence/focus.
- Yellow = OSCAR face/warm acknowledgement.
- Red = face detail or actual critical state.
- Muted orange = warning/attention where useful.

Do not turn every action blue. Do not add a fashionable second accent palette because a screen “needs more color.”

State light may be atmospheric, but it should resemble physical light cast by an object, not a generic gradient background.

## Material taste

The product may feel physical without becoming skeuomorphic.

Good:

- paper-like warm canvas;
- painted/satin surfaces;
- tiny contact shadows;
- restrained hardware-like controls where appropriate;
- subtle tonal depth.

Bad:

- obvious neumorphism;
- glossy toy rendering;
- giant shadows;
- glass-card stacks;
- bevels everywhere;
- visual hierarchy that disappears when shadows are removed.

## Typography taste

Typography should do more work than containers.

- Large statements are sparse and editorial.
- Operational headings are compact.
- Body copy is short.
- Labels are direct.
- Technical values use mono selectively.
- Avoid futuristic fonts, tracked-out uppercase interfaces and giant marketing type inside everyday product surfaces.

If hierarchy requires five font styles in one compact view, simplify the hierarchy.

## Surface taste

### OSCAR Mobile / mobile

- Feels like native personal system software, not a web app in a phone frame.
- OSCAR feels present without occupying half the display.
- Voice and text are peers, not mutually exclusive modes.
- Bottom navigation exists only if actual information architecture requires it.
- Haptics and transitions reinforce state.
- Sentry awareness is visible without looking like surveillance software.
- Permission/security moments use platform-native patterns.

### Desktop / Windows / macOS

- OSCAR lives comfortably as a compact presence/overlay and deeper workspace when needed.
- The overlay should grow from context rather than open as an unrelated floating chatbot.
- Selection, cursor, current app and task state should feel native to the machine.
- Desktop must not be mobile stretched wider.
- Windows and macOS share identity without pretending platform conventions are identical.

### Physical OSCAR

- Small displays simplify the same expression/state system.
- Physical controls should be direct and satisfying.
- Hardware state beats ornamental animation.

## Copy taste

OSCAR speaks like a competent assistant that is already there.

Prefer:

- `I’m here.`
- `Listening.`
- `Looking into it.`
- `One task is still running.`
- `Nothing needs your attention.`
- `The desk is quiet.`
- `Turn it off?`

Avoid:

- `Great! I’d be happy to assist you with that.`
- `Initiating autonomous workflow…`
- `AI-powered insight`
- `Smart intelligence`
- giant permanent `Talk to OSCAR` CTAs;
- `Type instead` copy that falsely implies typing disables voice/Sentry.

## Design workflow taste

Do not try to “finish the whole product” in a design pass.

Use Kaizen:

```text
study real shipping products
→ build one or two real surfaces
→ inspect
→ identify the biggest weakness
→ fix only that weakness
→ verify again
→ repeat
```

When available:

- use Appllama MCP/App Design Skill to study real mobile patterns before drawing;
- use Impeccable for critique and anti-slop review;
- treat both as design-development tools, never OSCAR runtime dependencies.

Once a promising direction exists, prefer real coded UI over dozens of generated mockups. Static image generation is useful for original supporting artwork/illustration, not as the source of truth for the entire application interface.

## Durability taste

Beautiful UI that collapses under real content is unfinished.

Always test:

- long titles/content;
- no tasks;
- many background tasks;
- offline devices;
- network/provider/microphone unavailable;
- simultaneous alert + ongoing work;
- blocked/partial/unknown verification;
- reduced motion;
- rapid voice/text switching.

The product should degrade calmly rather than becoming a pile of banners/modals.

## Anti-slop test

Reject or redesign if three or more are true:

- it could be a generic AI SaaS template with the logo swapped;
- the avatar is decorative or dominates utility;
- everything is in rounded cards;
- there is a giant microphone/chat CTA despite ambient presence;
- there are multiple permanent sidebars/panels;
- AI is represented by sparkle icons;
- fake metrics/telemetry are used for visual interest;
- glass blur or glow does most of the visual work;
- the screen looks like a HUD, poster, moodboard or movie prop;
- animation continues even when nothing is happening;
- whitespace is empty rather than composed;
- copy is longer than the action it explains;
- mobile and desktop are the same composition at different widths;
- unrelated personal projects appear as placeholder design content;
- the UI says `Done` while the system is still verifying.

## Agent rule

For UI work, an agent should read `DESIGN.md`, this file, `docs/UI-AVATAR.md`, `docs/SURFACES.md`, and the relevant platform/domain docs before writing code.

Research first when the visual path is uncertain. Build the smallest real surface that can test the idea. Visually verify it. Iterate through small improvements. Do not lock a pattern because a mockup looked good once.
