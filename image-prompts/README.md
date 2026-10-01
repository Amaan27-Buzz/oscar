# OSCAR Image Prompts

This folder contains page/surface prompts for visual exploration and reference generation.

These prompts are **not** a replacement for coded UI. OSCAR's current design workflow is:

```text
study real shipping patterns
→ build/refine real UI
→ use image generation only where a visual reference is useful
→ inspect visually
→ Kaizen iteration
```

Use one prompt at a time. Do not mass-generate the entire library and treat the results as a finished design system.

## Canonical design context

Before using any prompt, read:

- `DESIGN.md`
- `TASTE.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/UI-AVATAR.md`
- `docs/SURFACES.md`
- `docs/VOICE-SENTRY.md`
- `docs/CONNECTION-GRID.md`
- `docs/PERSONA.md`

## Global visual direction

**Quietly Alive + Playful Precision**

- warm cream/off-white material world;
- graphite/near-black typography;
- OSCAR blue/yellow reserved for identity/presence/state;
- minimal red expression/critical accents;
- broad intentional whitespace;
- restrained tactile industrial details;
- premium native-product finish;
- fluid state-driven motion implied through shared geometry;
- one dominant idea per screen;
- progressive disclosure rather than dashboard density.

Do not use:

- glassmorphism;
- purple/blue AI gradients;
- cyberpunk/neon HUDs;
- generic AI SaaS dashboards;
- giant mascot layouts;
- permanent chat sidebars;
- card walls;
- fake telemetry/analytics;
- generic sparkle AI iconography;
- obvious 2020-style neumorphism.

## OSCAR presence object

The avatar is a blue shell with a yellow weighted puck/face and restrained red expression marks.

It should feel like a precision physical/digital object rather than a children's mascot. The yellow puck moves with believable spring/inertia and communicates attention/state.

Do not make the avatar occupy most of every screen.

## Content rules

- Use neutral OSCAR-native content unless a page requires otherwise.
- Do not inject unrelated project names into examples.
- Keep text short enough that image generation can render the composition cleanly.
- Runtime states must remain truthful: `Working`, `Waiting`, `Verifying`, `Blocked`, `Failed` and `Done` are different.
- `Done` should not appear before verification where verification is possible.
- Voice `Listening` is different from Sentry acoustic awareness.
- Persona is expression/tone, not factual truth or permission.

## Prompt files

- `web.md` — public website and web/account surfaces.
- `sunday-mobile.md` — Sunday mobile app.
- `desktop.md` — desktop presence, overlays and management surfaces.
- `system-surfaces.md` — onboarding, Sentry, Workers, memory, Personal Policy, Persona, Connection Grid, devices, ledger and degraded states.

Each prompt is intended as a **single image generation request** unless it explicitly asks for a small state sequence.
