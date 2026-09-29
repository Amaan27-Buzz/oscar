# AGENTS.md

Canonical repository instructions for Codex and other coding agents working on OSCAR.

Keep this file short enough to be useful in every task. Detailed product/design/domain truth lives in the linked docs and should be loaded only when relevant.

## Read first

For any implementation task, read:

- `README.md`
- `ENGINEERING.md` — canonical engineering quality/system-design standard
- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/EPISTEMIC-INTEGRITY.md`
- the relevant domain document(s)

For any orchestration/Worker/Protocol/runtime task, additionally read:

- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/ORCHESTRATION.md`
- `docs/WORKERS.md` where relevant

For any UI, UX, motion, frontend, mobile or desktop-surface task, additionally read:

- `DESIGN.md` — normative visual system and tokens
- `TASTE.md` — qualitative quality bar and anti-slop rules
- `docs/UI-AVATAR.md` — OSCAR avatar/state language
- `docs/SURFACES.md` — embodiment/surface responsibilities

Treat these files as the current product contract. If implementation and docs disagree, investigate the mismatch rather than silently choosing one.

## Working style

- Work on one product slice or narrowly scoped sub-slice at a time.
- Do not brute-force around an architectural problem. Inspect current best practices, libraries/frameworks and existing OSCAR infrastructure first.
- Prefer the smallest coherent design that solves the current requirement.
- Prefer modular components with high cohesion and low coupling over monolithic files, god objects or fragmented wrapper layers.
- Do not add abstractions, services, extension points or dependencies for hypothetical future needs.
- Do not create fake/demo states that make an unfinished capability appear functional.
- Preserve explicit failure states and report blockers instead of fabricating success.
- Reuse existing projects and specialist tools when they are the right execution environment.
- Before adding a dependency, explain why the existing stack is insufficient.
- Preserve native platform conventions unless the OSCAR design system intentionally overrides them.

## Evidence and completion claims

A tool call, commit, Worker response or model message is **not automatically proof that the user's objective is complete**.

For every meaningful task:

1. define the observable completion condition;
2. execute;
3. inspect the resulting authoritative state;
4. run tests/visual/device verification where relevant;
5. report the strongest claim the evidence supports.

Use explicit distinctions such as:

```text
reported success
verified
partially verified
failed
blocked
unknown
```

Do not say `done`, `fixed`, `all set`, `works` or equivalent when the result is only reported or partially verified.

If a sub-agent says it completed work, verify the resulting files/tests/runtime state rather than trusting the report blindly.

If verification is impossible, state that limitation explicitly.

Do not agree with the user merely because they assert something is complete/correct. Check the repository/runtime evidence first.

See `docs/EPISTEMIC-INTEGRITY.md`.

## Engineering quality

`ENGINEERING.md` is normative for implementation quality. In particular:

- keep critical paths lean and understandable;
- make subsystem boundaries typed, explicit and evolvable;
- centralize real shared invariants without premature abstraction;
- keep provider/platform specifics behind narrow adapters when OSCAR needs a stable internal contract;
- make mutable state ownership and authoritative sources obvious;
- design timeout/retry/reconnect/cancellation/failure behavior intentionally;
- validate at trust boundaries and fail safely;
- measure critical-path performance before optimizing;
- write tests around contracts and meaningful failure modes, not private implementation trivia;
- prefer small reviewable changes and separate broad refactors from feature work when practical.

Do not “future-proof” the code by making it harder to understand today.

## Core invariants

Do not violate these without an explicit architecture decision update:

1. Laptop/desktop workers are optional.
2. Hardware safety is local and deterministic.
3. Reflex actions do not wait for a frontier model.
4. Voice and text share the same OSCAR task/context state.
5. Sunday is OSCAR's mobile embodiment, not a separate assistant.
6. LRA + Supermemory provide continuous memory/history.
7. Jev decides whether OSCAR knows enough, should retrieve/verify, delegate, reason or ask.
8. Latch is the bridge for ChatGPT/device/tool interaction.
9. SwitchRoute supplies general model routing.
10. Nodes advertise capabilities dynamically.
11. OSCAR chooses the best specialist rather than doing everything itself.
12. Generated Skills/routines/Protocols cannot self-grant permissions.
13. Consequential actions must be attributable, permission-aware and auditable.
14. Completion claims cannot exceed available verification evidence.
15. Workers/Protocols use the Durable Execution Runtime for long-running work where persistence/recovery is required.
16. Capability discovery scales through a catalog/search path rather than a mega-prompt containing every tool.
17. Learned automation is evaluated before trusted promotion.
18. Finished outputs use typed artifact/result references where appropriate.

## Specialist delegation

Do not use OSCAR's generic path when a better specialist is available.

- Repository implementation/debugging → Codex or another coding agent.
- UI/UX work → Impeccable/design tooling + coding agent; verify visually.
- GUI-only operation → computer-use worker.
- Notes/knowledge workflows → connected Notion/Obsidian-style capability when available.
- Hardware design/provisioning → Kinetable.
- General autonomous model work → SwitchRoute.
- Personal/complex ChatGPT-context work → ChatGPT through Latch.

A representative rule: if the user asks for a SceneLab landing page and Codex has the SceneLab project plus an appropriate design skill/plugin, delegate there rather than reproducing a weaker implementation through OSCAR itself.

## UI and design quality

- The durable direction is **Quietly Alive**: minimal, technical, tactile and expressive.
- Personality comes from OSCAR's avatar, state, motion, timing and physicality — not generic AI decoration.
- Avoid dashboard gravity: no default wall of cards, permanent chat sidebar, glassmorphism, neon HUD, purple AI gradients or fake telemetry.
- Use one dominant focal idea per surface and progressive disclosure for secondary detail.
- UI state must reflect real runtime state. Never animate `thinking`, `working` or `done` when the system is actually blocked, failed or still verifying.
- Desktop and mobile are different compositions sharing one identity; do not merely stretch one into the other.
- For substantial UI work, use the Impeccable workflow when available and perform bounded visual verification before declaring completion.

## Tests

Every slice should define an explicit test checklist before being marked complete. Include failure cases, disconnects/timeouts, cancellation/retry/idempotency where relevant, and safety behavior where applicable.

For hardware-facing changes, separate host/simulator tests from real-device verification and state clearly which has been run.

For UI work, include target viewport/device verification, reduced-motion behavior, keyboard/touch access where relevant, and screenshots/visual inspection when tooling allows.

For learned Skills/routines/Protocols, include candidate evaluation/replay where practical before promoting a new version to trusted/default use.

## Documentation is part of the change

Every completed slice or architectural change must update:

- `README.md` status/current-position section;
- `docs/ROADMAP.md`;
- relevant feature/architecture/domain docs;
- `docs/DECISIONS.md` when an invariant changes;
- `CHANGELOG.md` for user/developer-visible milestones.

A system-wide engineering-rule change updates `ENGINEERING.md`. A system-wide visual change updates `DESIGN.md` and, when it changes qualitative direction, `TASTE.md`.

Do not leave documentation updates for a later cleanup pass.

## Secrets and personal data

Never commit:

- API/provider keys;
- OAuth tokens;
- device credentials;
- private memory exports;
- raw personal conversation archives;
- voice biometric embeddings;
- private camera/microphone recordings;
- `.env` files containing secrets.

Use ignored local fixtures or synthetic test data.
