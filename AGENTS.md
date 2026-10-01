# AGENTS.md

Canonical repository instructions for Codex and other coding agents working on OSCAR.

Keep this file short enough to be useful in every task. Detailed product/design/domain truth lives in linked docs and should be loaded only when relevant.

## Read first

For any implementation task, read:

- `README.md`
- `ENGINEERING.md`
- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/EPISTEMIC-INTEGRITY.md`
- relevant domain documents.

For transport/model-routing/capability work additionally read:

- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/RUNTIME-FOUNDATIONS.md`

For voice/audio/Sentry work additionally read:

- `docs/VOICE-SENTRY.md`
- `docs/ONBOARDING.md` where commissioning/privacy matters.

For orchestration/Worker/Protocol work additionally read:

- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/ORCHESTRATION.md`
- `docs/WORKERS.md` where relevant.

For UI/UX/motion/mobile/desktop work additionally read:

- `DESIGN.md`
- `TASTE.md`
- `docs/UI-AVATAR.md`
- `docs/SURFACES.md`
- `docs/SUNDAY-DESIGN.md` for Sunday/mobile work.

Treat these files as the current product contract. If implementation and docs disagree, investigate the mismatch rather than silently choosing one.

## Working style

- Work on one product slice or narrowly scoped sub-slice at a time.
- Do not brute-force around an architectural problem. Inspect existing OSCAR infrastructure and appropriate libraries/frameworks first.
- Prefer the smallest coherent design that solves the current requirement.
- Prefer modular components with high cohesion/low coupling over god objects or wrapper forests.
- Do not add abstractions/services/dependencies for hypothetical future needs.
- Do not create fake/demo states that make unfinished capability appear functional.
- Preserve explicit failure states and report blockers instead of fabricating success.
- Reuse specialist tools when they are the right execution environment.
- Before adding a dependency, explain why the existing stack is insufficient.

## Native infrastructure rule

Do **not** treat Amaan's separate `Latch` or `SwitchRoute` repositories as required runtime dependencies.

Canonical OSCAR architecture is:

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
```

The separate repositories may be inspected for proven patterns/code/tests, but reuse must be folded into OSCAR behind OSCAR-owned contracts.

Do not preserve an external service boundary solely because a prototype had one.

See `docs/NATIVE-INFRASTRUCTURE.md` and ADR-006/008/048.

## Evidence and completion claims

A tool call, commit, Worker response or model message is **not automatically proof that the user's objective is complete**.

For every meaningful task:

1. define observable completion condition;
2. execute;
3. inspect authoritative resulting state;
4. run tests/visual/device verification where relevant;
5. report the strongest claim evidence supports.

Use explicit distinctions such as `reported success`, `verified`, `partially verified`, `failed`, `blocked`, `unknown`.

Do not say `done`, `fixed`, `all set`, `works` or equivalent when only reported/partial.

If a sub-agent says it completed work, verify resulting files/tests/runtime state rather than trusting the report blindly.

If verification is impossible, state the limitation.

Do not agree with the user merely because they assert something is complete/correct. Check evidence first.

## Engineering quality

`ENGINEERING.md` is normative. In particular:

- keep critical paths lean/understandable;
- make subsystem boundaries typed, explicit and evolvable;
- centralize real shared invariants without premature abstraction;
- isolate provider/platform specifics behind narrow adapters when OSCAR needs stable contracts;
- make state ownership/authoritative sources obvious;
- design timeout/retry/reconnect/cancellation/failure intentionally;
- validate trust boundaries and fail safely;
- measure critical-path performance before optimizing;
- test contracts and meaningful failure modes;
- prefer small reviewable changes.

## Core invariants

Do not violate these without an explicit architecture decision update:

1. Laptop/desktop workers are optional.
2. Hardware safety is local/deterministic.
3. Reflex actions do not wait for a frontier model.
4. Voice and text share OSCAR task/context state.
5. Sunday is OSCAR's mobile embodiment, not a separate assistant.
6. LRA + Supermemory provide continuous memory/history.
7. Jev decides whether OSCAR should execute/retrieve/verify/reason/delegate/ask.
8. OSCAR Transport + Capability Fabric is native infrastructure; Latch is reference/prototype material.
9. OSCAR Model Router is native infrastructure; SwitchRoute is reference/prototype material.
10. Nodes advertise capabilities dynamically.
11. OSCAR chooses the best specialist rather than doing everything itself.
12. Generated Skills/routines/Protocols cannot self-grant permissions.
13. Consequential actions are attributable, permission-aware and auditable.
14. Completion claims cannot exceed verification evidence.
15. Long-running work uses Durable Execution Runtime where persistence/recovery is required.
16. Capability discovery scales through catalog/search rather than a mega-prompt.
17. Learned automation is evaluated before trusted promotion.
18. Durable outputs use typed artifact/result references where appropriate.
19. Voice Match and Voice Map are distinct: recognition is not authorization.
20. OSCAR owns a stable provider-independent Voice Identity.
21. Always-on Sentry acoustic awareness is local-first and does not imply continuous cloud transcription/recording.
22. OSCAR's own TTS is excluded from Voice Map learning/recognition while real barge-in remains functional.
23. UI truth follows runtime truth: `Working`, `Verifying`, `Blocked`, `Partial` and `Done` must not be cosmetically collapsed.
24. OSCAR may be acoustically aware without being in an active conversational `Listening` state.

## Voice/audio implementation rules

When working on voice:

- treat `Voice Input`, `OSCAR Voice Identity`, `Voice Match` and `Voice Map` as separate contracts;
- keep Voice Match authorization-oriented and Voice Map perception-oriented;
- unknown speakers remain unknown instead of guessed;
- voice embeddings/profiles are sensitive data;
- do not equate speech presence with permission to transcribe or retain;
- preserve self-voice suppression via playback reference/echo cancellation/TTS tagging where possible;
- do not hard-code OSCAR's character to one provider's default TTS voice;
- fallback voices/providers must expose degradation rather than silently changing identity;
- test barge-in while OSCAR is speaking;
- keep `Sentry aware`, `Listening`, `Muted` and `Acoustic awareness disabled` semantically distinct.

## Specialist delegation

Do not use OSCAR's generic path when a better specialist is available.

- Repository implementation/debugging → Codex or another coding agent.
- UI/UX research → real shipping-product references first; use Appllama MCP/App Design Skill when available.
- UI/UX critique → Impeccable or another suitable design-review capability when available.
- UI implementation → coding agent; verify visually on target viewport/device.
- GUI-only operation → computer-use worker.
- Knowledge workflows → connected native tool/plugin when available.
- Hardware design/provisioning → installed or connected engineering tools plus OSCAR Edge/device capabilities.
- General model work → Jev selects reasoning class → native OSCAR Model Router selects provider.
- Personal/complex ChatGPT-context work → ChatGPT provider adapter where appropriate.

Design-research/critique tools are development aids, not runtime OSCAR dependencies.

## UI and design quality

The durable direction is **Quietly Alive** with **Playful Precision**:

- roughly 70% restraint/whitespace, 20% tactile industrial character, 10% approachable personality;
- warm cream/off-white material world, graphite typography, OSCAR blue/yellow used sparingly;
- personality from state, motion, timing, voice and the avatar/presence object — not generic AI decoration;
- one dominant focal idea per surface;
- progressive disclosure for secondary detail;
- desktop/mobile are different compositions sharing one identity;
- Sentry is calm ambient awareness, not surveillance/security-dashboard theatre;
- the avatar is a weighted presence object, not a giant mascot;
- avoid obvious neumorphism, glassmorphism, neon HUDs, purple gradients, card walls and fake telemetry.

### Presence and input semantics

Do not design ordinary mobile use around a permanent `Talk to OSCAR` / `Type instead` fork.

- `Sentry aware` may keep local wake/VAD/hot-command/Voice Map/sound-event processing active without cloud transcription.
- `Listening` means an active conversational turn/STT.
- `Muted` disables ordinary conversational listening but may preserve allowed local reflex/safety commands.
- `Acoustic awareness disabled` means the local acoustic plane is actually off.
- Typing is another modality for the same OSCAR context, not a voice-off mode.

### Fluid motion

Motion is part of product structure, not a later polish pass.

Prefer:

- shared-element transitions;
- geometry morphing;
- contextual expansion;
- weighted spring/inertia;
- gesture-linked motion;
- velocity continuity;
- state A physically becoming state B where practical.

Avoid generic fade-everything transitions, random bounce/springs, decorative particles and animation that delays input.

Animation must never own runtime correctness and the UI must remain complete under reduced motion.

### Kaizen design workflow

Do not design dozens of screens up front.

Use:

```text
research real shipping patterns
→ build one or two real surfaces
→ inspect visually
→ fix the biggest weakness
→ verify again
→ repeat
```

Once a direction is promising, prefer real coded UI over mass-generated static mockups. Image generation is appropriate for original supporting assets/illustration/hero imagery, not as the canonical interface system.

For substantial UI work, test robustness with long content, empty state, many background tasks, offline/degraded capabilities, reduced motion and conflicting simultaneous states.

## Tests

Every slice defines an explicit test checklist before being marked complete. Include failure cases, disconnects/timeouts, cancellation/retry/idempotency and safety behavior where applicable.

For hardware-facing changes, separate simulator tests from real-device verification.

For voice/audio changes include, as relevant:

- wake/VAD latency;
- STT/TTS latency;
- barge-in;
- echo/self-voice suppression;
- Voice Match false accept/reject behavior;
- Voice Map unknown/known/multiple-speaker behavior;
- no-continuous-cloud-audio default;
- fallback Voice Identity behavior.

For UI work include:

- target viewport/device visual verification;
- reduced motion;
- long/empty/degraded states;
- real runtime-state mapping;
- fluid transition behavior where implemented;
- interaction responsiveness under ordinary load.

For learned automation include evaluation/replay where practical before trusted promotion.

## Documentation is part of the change

Every completed slice or architectural change updates:

- `README.md` status/current position;
- `docs/ROADMAP.md`;
- relevant feature/architecture/domain docs;
- `docs/DECISIONS.md` when an invariant changes;
- `CHANGELOG.md` for visible milestones.

Do not leave documentation updates for a later cleanup pass.

## Secrets and personal data

Never commit:

- API/provider keys;
- OAuth tokens;
- device credentials;
- private memory exports;
- raw personal conversation archives;
- voice biometric embeddings/Voice Map profiles;
- private camera/microphone recordings;
- `.env` files containing secrets.

Use ignored local fixtures or synthetic test data.
