# OSCAR Taste

This file is the opinionated quality bar for agents designing or reviewing OSCAR surfaces. `DESIGN.md` is the normative design system. This file explains what “good” should feel like when multiple valid implementations satisfy the tokens.

## The taste in one line

**Minimal, technical and calm — but unmistakably alive.**

OSCAR should feel less like software with an AI feature and more like a responsive object/intelligence that inhabits the device.

## Reference blend

Use these only as principles, never as templates to copy:

- **Apple** — restraint, typography, native clarity, confidence, whitespace, finish.
- **Teenage Engineering** — tactile controls, physical metaphor, playful industrial precision, delightful state changes.
- **Duolingo** — character, readable emotional feedback, immediate acknowledgement, friendliness without requiring explanation.
- **Braun / Dieter Rams** — useful hierarchy, honest function, legible controls, nothing decorative without a job.

For OSCAR, the result is ambient and personal: clean white/soft-neutral surfaces, OSCAR blue/yellow identity, the avatar as presence, and few visible technical controls until they are needed. Playfulness comes from response, movement and cause/effect rather than clutter.

## What should be memorable

If somebody sees OSCAR for ten seconds, they should remember:

1. the **blue shell + yellow face**;
2. the face physically moving inside the shell like a weighted puck;
3. how little UI surrounded it;
4. how quickly the interface reacted to them;
5. that it felt useful and composed rather than “AI-themed.”

If they instead remember glowing gradients, cards, floating glass panels or a generic waveform, the design missed.

## Composition rules

### One hero

Every screen should have one dominant idea.

Examples:

- Sunday Home → OSCAR/avatar + current presence.
- Listening → listening state.
- Thinking/working → current task state.
- Sentry → awareness/state + the one thing that needs attention.
- Permission request → consequence + decision.

Do not give five things equal visual weight.

### UI appears when needed

Prefer:

`state → contextual control → action`

rather than:

`navigation + sidebar + toolbar + card grid + status rail + assistant panel`.

Advanced detail can exist, but it should reveal itself progressively.

### Avoid dashboard gravity

Coding agents tend to turn capable products into dashboards. Resist that by default.

A screen should not become a collection of:

- status cards;
- metrics tiles;
- mini-panels;
- feature boxes;
- badges;
- graphs;
- verbose labels.

Use the object, task, timeline or conversation state itself as the interface whenever possible.

## Personality rules

OSCAR is expressive, not cute-first.

- Neutral is the default.
- A wink is an acknowledgement, not permanent branding.
- Happy is brief and earned.
- Thinking is focused, not cartoon confusion.
- Sentry is calm and alert, not angry/security-theatre.
- Errors are clear and composed.
- Serious work reduces playful movement rather than changing the product into a different visual identity.

Character must never reduce trust.

## Motion taste

Motion is one of OSCAR’s primary materials.

Good motion:

- tells you where OSCAR is paying attention;
- acknowledges speech before the cloud responds;
- shows a physical cause and effect;
- has weight and settling;
- stops immediately on barge-in;
- becomes quieter during focus or Sentry.

Bad motion:

- random floating;
- endless breathing everywhere;
- loading spinners used instead of real state;
- looping waveform theatre when no audio is active;
- parallax merely because it looks expensive;
- scattered hover effects with no shared grammar.

The avatar should be the most animated object on most surfaces. Everything around it earns motion.

## Color taste

Color is state and identity, not decoration.

- Blue = OSCAR presence, active interaction, focus.
- Yellow = face, warmth, acknowledgement.
- Red = face detail or actual critical state.
- Neutral canvas does most of the work.

Do not add a second fashionable accent palette because a screen “needs more color.”

State halos can be soft and atmospheric, but they should resemble light cast by an object, not a generic gradient background.

## Typography taste

Typography should feel product-native and calm.

- Large statements are sparse and confident.
- Body copy is short.
- Labels are direct.
- Technical values can use mono selectively.
- Avoid “futuristic” fonts, sci-fi uppercase interfaces and tracked-out microtext everywhere.
- Avoid huge marketing typography inside operational product surfaces.

If hierarchy requires five font styles in one compact screen, simplify the hierarchy.

## Surface taste

### Sunday / mobile

- Feels like a native personal assistant, not a web app inside a phone frame.
- Avatar/state dominates.
- Bottom navigation exists only if the actual information architecture warrants it.
- Voice and text are peers.
- Haptics and transitions should reinforce state.
- Permission/security moments use native patterns.

### Desktop / macOS / Windows

- OSCAR should live comfortably as a compact overlay, command/presence surface and deeper app when needed.
- Do not stretch the mobile screen into a giant desktop dashboard.
- Cursor selection, current app and screen context should feel native to the machine.
- Windows and macOS may share identity without pretending their native conventions are identical.

### Physical OSCAR

- Small displays simplify the same expression/state system rather than inventing another brand.
- Physical buttons/knobs should be satisfying and direct.
- Hardware state beats ornamental animation.

## Copy taste

OSCAR speaks like a competent assistant that already understands the task.

Prefer:

- `I’m here.`
- `Listening.`
- `Looking into it.`
- `Codex is still running.`
- `Your soldering station is still on.`
- `Turn it off?`

Avoid:

- `Great! I’d be happy to assist you with that.`
- `Initiating autonomous workflow…`
- `AI-powered insight`
- `Smart intelligence`
- unnecessary explanations of obvious UI.

## Anti-slop test

Reject or redesign the surface if three or more are true:

- it could be an AI SaaS template with the logo swapped;
- the interface relies on purple/blue gradient glow;
- everything is in rounded cards;
- the avatar is decorative rather than tied to system state;
- there are multiple permanent sidebars/panels;
- “AI” is represented by sparkle icons;
- fake metrics/telemetry are used for visual interest;
- glass blur is doing most of the visual work;
- the screen looks like a HUD, cyberpunk console or movie prop;
- animation continues even when nothing is happening;
- copy is longer than the action it explains;
- mobile and desktop are the same composition at different widths.

## Agent rule

For UI work, an agent should read `DESIGN.md`, this file, `docs/UI-AVATAR.md`, and the relevant surface/product docs before writing code. If the requested design conflicts with these files, the explicit user request wins; update the durable design documentation only when the change is intended to become system-wide.
