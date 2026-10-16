# Slice 13 — OSCAR Mobile Visual / Interaction Design

**Current Group 2.5B scope — 2026-10-14:** production Compose implementation of the selected Codex ImageGen/Figma 15 hero experiences. Gemini Argon is rejected. See [Group 2.5B implementation and evidence](ui/mobile/group25b/README.md). The dated Group 2 results below remain historical foundation evidence.

Status: **GROUP 2 SOFTWARE / REFERENCE CANDIDATE / OWNER VISUAL AND DEVICE ACCEPTANCE DEFERRED / REQUIRED BEFORE SLICE 20 UNIFIED ALPHA PASS**.

Owner authorization 2026-10-11 covers autonomous 13.1–13.8 software/reference
implementation and a draft PR, with consolidated manual acceptance. See
[Group 2](development/GROUP-02-MOBILE-COMPLETION.md) and the
[cumulative ledger](development/SOFTWARE-ALPHA-ACCEPTANCE-LEDGER.md).

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
- Slice 11 establishes the shared expression vocabulary, dev-only lab and typed Desktop/Compose rendering contract **before** expression-dependent redesign; full runtime/overlay/widget Presence integration remains **Slice 16**, after Slices 14–15. See [Expression Core](EXPRESSION-CORE.md).
- Do not independently invent Mobile-only expressions or alter the canonical Orb.
- Every redesign sub-slice must retain functional accessibility and truthful degraded states.
- Visual work may run in parallel with Slices 10–16, but the complete redesign must be integrated and accepted before Slice 20 Unified Alpha PASS.

## 13.1 — Presence / Home + Orb

Establish the mobile visual language around the Orb and OSCAR state **using the approved Slice 11 expression vocabulary/contract**. Defer expression-specific final visual choices until Slice 11 is reviewed.

Scope:
- home/presence composition;
- hierarchy, spacing and typography;
- Orb placement, scale and state transitions;
- text/voice entry;
- contextual task/approval indicators;
- listening/thinking/speaking/waiting/degraded visual hooks;
- motion baseline and reduced-motion behavior.

Do not independently implement the full Slice 16 Presence/Avatar system here.

## 13.2 — Interaction

Refine OSCAR interaction without turning it into a conventional chatbot.

Scope:
- user input and progressive response presentation;
- task/result/evidence distinction;
- interruption/cancel/retry states;
- long-content handling;
- keyboard/insets and one-handed use;
- interaction transitions.

## 13.3 — Activity + Approvals

Create a clear operational surface for ongoing work and consequential decisions.

Scope:
- running/waiting/completed/failed/blocked/cancelled states;
- inspect/cancel/retry actions;
- approval consequence/target/reason/policy presentation;
- biometric/PIN confirmation handoff;
- clear verified/reported/unknown distinctions.

No visual affordance may imply broader authority than the underlying contract.

## 13.4 — Devices / Connection Grid

Refine owner understanding of OSCAR's embodiments.

Scope:
- this phone, desktop, future Home Node and Edge presentation;
- connection/degraded/offline states;
- capabilities and active work;
- pairing/trust state;
- legitimate controls only.

Do not invent power, wake or remote-control capability.

## 13.5 — Voice

Refine the mobile Voice experience around the existing Voice Core boundary.

Scope:
- listening state;
- microphone/output route state;
- Voice Identity presentation;
- Match/Map enrollment/status;
- interruption/barge-in preferences;
- local/private/degraded states.

No Elocution/custom-model work before post-alpha.

## 13.6 — Privacy + Permissions

Make perceive/retain/act boundaries understandable and inspectable.

Scope:
- Android runtime permission state;
- OSCAR grants and retention controls;
- notification listener/reply boundaries;
- microphone, camera, location and future Sentry states;
- revocation/degraded behavior;
- no fake enabled states.

## 13.7 — Settings + System Surfaces

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

## 13.8 — Motion, Accessibility + Final Mobile Polish

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
visual refinement remains open. Early Slice 11 is a shared visual dependency; the original
Slice 16 Presence integration remains in its later roadmap position. Slice 10 and later
backend/runtime work may proceed without misrepresenting visual acceptance.

## Numbering and visual quality

This was formerly the `09R` track. Canonical identifiers are now `13.1–13.8`; historical screenshots/doc evidence may retain `09R` names. See [Slice Numbering](SLICE-NUMBERING.md).

Do not repeat generic rounded-card AI UI or static happy-face Orb designs. Adopt the reviewed Slice 11 character language; communicate actual operational state by meaningful microexpression, timing, movement and interruption with a native Compose implementation. Use studied screen references, interaction prototypes and owner critique rather than rushing. No unapproved Core/security changes.
