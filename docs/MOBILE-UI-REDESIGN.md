# OSCAR Mobile UI Redesign Track

Status: **PLANNED / NON-BLOCKING FOR SLICES 10–16 / REQUIRED BEFORE SLICE 17 PASS**.

Slice 09 established the Android product/runtime foundation. This track refines the
actual OSCAR Mobile experience without reopening Core, Grid, authority, policy,
security, Voice Core or Android service architecture.

The app remains **OSCAR**. **OSCAR Mobile** is only the technical distinction.

## Rules

- Redesign Compose UI/UX section by section.
- Preserve Core authority and current typed state/action boundaries.
- Do not move reasoning, policy, memory, task authority or model routing into Android.
- Do not widen permissions or capability scopes to make a design work.
- Keep the canonical `assets/brand/oscar-orb.svg` unchanged.
- Full expressive Orb/facial/personality behavior remains Slice 13.
- Every redesign sub-slice must retain functional accessibility and truthful degraded states.
- Visual work may run in parallel with Slices 10–16, but the complete redesign must be integrated and accepted before Slice 17 Unified Alpha PASS.

## 09R.1 — Presence / Home + Orb

Establish the mobile visual language around the Orb and OSCAR state.

Scope:
- home/presence composition;
- hierarchy, spacing and typography;
- Orb placement, scale and state transitions;
- text/voice entry;
- contextual task/approval indicators;
- listening/thinking/speaking/waiting/degraded visual hooks;
- motion baseline and reduced-motion behavior.

Do not implement Slice 13 expressive faces here.

## 09R.2 — Interaction

Refine OSCAR interaction without turning it into a conventional chatbot.

Scope:
- user input and progressive response presentation;
- task/result/evidence distinction;
- interruption/cancel/retry states;
- long-content handling;
- keyboard/insets and one-handed use;
- interaction transitions.

## 09R.3 — Activity + Approvals

Create a clear operational surface for ongoing work and consequential decisions.

Scope:
- running/waiting/completed/failed/blocked/cancelled states;
- inspect/cancel/retry actions;
- approval consequence/target/reason/policy presentation;
- biometric/PIN confirmation handoff;
- clear verified/reported/unknown distinctions.

No visual affordance may imply broader authority than the underlying contract.

## 09R.4 — Devices / Connection Grid

Refine owner understanding of OSCAR's embodiments.

Scope:
- this phone, desktop, future Home Node and Edge presentation;
- connection/degraded/offline states;
- capabilities and active work;
- pairing/trust state;
- legitimate controls only.

Do not invent power, wake or remote-control capability.

## 09R.5 — Voice

Refine the mobile Voice experience around the existing Voice Core boundary.

Scope:
- listening state;
- microphone/output route state;
- Voice Identity presentation;
- Match/Map enrollment/status;
- interruption/barge-in preferences;
- local/private/degraded states.

No Elocution/custom-model work before post-alpha.

## 09R.6 — Privacy + Permissions

Make perceive/retain/act boundaries understandable and inspectable.

Scope:
- Android runtime permission state;
- OSCAR grants and retention controls;
- notification listener/reply boundaries;
- microphone, camera, location and future Sentry states;
- revocation/degraded behavior;
- no fake enabled states.

## 09R.7 — Settings + System Surfaces

Refine secondary product surfaces.

Scope:
- Persona;
- Voice;
- notifications;
- devices;
- local/cloud preference;
- accessibility;
- diagnostics/about;
- assistant-role entry points;
- widgets/overlay only when implemented by their owning slice.

Keep settings restrained rather than exposing internal architecture.

## 09R.8 — Motion, Accessibility + Final Mobile Polish

Cross-screen convergence pass.

Scope:
- coherent transitions and motion;
- animation performance;
- TalkBack/semantics;
- large text;
- contrast;
- portrait/landscape;
- keyboard/insets;
- loading/error/degraded consistency;
- screenshot/privacy behavior;
- final owner visual review.

## Acceptance

The redesign track is complete only when:

1. all eight sub-slices are integrated into the Android app;
2. existing Mobile security/runtime tests remain green;
3. visual changes do not change Core authority or permission scope;
4. accessibility and reduced-motion paths are functional;
5. real-device visual/interaction review is completed during the consolidated owner acceptance phase.

Until then Slice 09's software/runtime foundation remains accepted, while mobile
visual refinement remains open. Slice 10 and later backend/runtime work may proceed.
