---
name: oscar-ui
description: Design, implement, review, or refine OSCAR/Sunday/desktop interfaces using OSCAR's Quietly Alive visual system, avatar state language, motion grammar, native-platform behavior, and anti-slop quality bar. Use for any UI, UX, frontend, mobile, desktop, onboarding, Sentry, voice, avatar, or visual-polish task in the OSCAR repository.
---

# OSCAR UI skill

Before work:

1. Read `DESIGN.md` for normative tokens and system rules.
2. Read `TASTE.md` for the qualitative quality bar.
3. Read `docs/UI-AVATAR.md` for avatar/state behavior.
4. Read `docs/SURFACES.md` and the relevant product/surface docs.
5. Inspect existing implementation before changing visual direction.

If Impeccable is available, use it for substantial design/refinement work and follow its bounded visual-review workflow.

## Build rules

- Preserve the **Quietly Alive** direction: minimal, technical, tactile, expressive.
- Give each screen one dominant focal idea.
- Let OSCAR's avatar, real state, timing and motion carry personality.
- Prefer progressive disclosure and contextual controls over permanent panels.
- Keep platform-native behavior on Android, Windows and macOS.
- Voice and text are peers; do not turn voice surfaces into transcript-first chat screens.
- Never fake thinking/listening/working states.
- Respect reduced motion, keyboard/touch access and contrast.

## Reject

- generic AI SaaS dashboards;
- card walls;
- glassmorphism;
- neon/cyberpunk HUDs;
- purple/blue AI gradients;
- sparkle icons as OSCAR;
- fake telemetry;
- random ambient animation;
- permanent chat sidebars as the default IA;
- one responsive web composition stretched across all native surfaces.

## Finish

For substantial UI changes:

1. verify target device classes/viewports;
2. inspect visual hierarchy, state accuracy, motion and native behavior;
3. fix material issues in one bounded batch;
4. update `DESIGN.md`/`TASTE.md` only if the change is intended to become system-wide;
5. update relevant slice/docs before marking complete.
