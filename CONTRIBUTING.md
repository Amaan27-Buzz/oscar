# Contributing to OSCAR

OSCAR is being built slice-by-slice. Contributions should preserve the product architecture rather than introduce isolated features that bypass it.

## Before changing code

Read:

1. `README.md`
2. `ENGINEERING.md`
3. `docs/PRODUCT.md`
4. `docs/ARCHITECTURE.md`
5. `docs/ROADMAP.md`
6. `docs/DECISIONS.md`
7. the domain-specific document for the area being changed

For agent-driven work, also read `AGENTS.md`.

## Engineering bar

Every code change should preserve or improve overall code health.

- Prefer the simplest design that fully solves the current requirement.
- Keep responsibilities cohesive and subsystem coupling low.
- Use typed, validated contracts across important boundaries.
- Reuse actual shared behavior; do not build premature abstraction frameworks.
- Keep external providers/platforms behind narrow adapters when OSCAR needs a stable internal contract.
- Make mutable state ownership and authoritative sources obvious.
- Define failure, timeout, retry, reconnect and cancellation behavior where relevant.
- Add dependencies only when their value exceeds their maintenance/compatibility cost.
- Test public behavior and meaningful failure modes rather than private implementation trivia.
- Prefer small, reversible changes over broad rewrites.

See `ENGINEERING.md` for the complete standard.

## Slice rule

Work on one coherent product slice at a time. A slice is complete only when:

- the scoped implementation is complete;
- important behavior has tests;
- limitations and follow-ups are explicit;
- security/safety implications have been reviewed;
- engineering invariants and failure modes have been considered;
- `README.md` status is updated;
- affected files under `docs/` are updated;
- the next slice or follow-up is clear.

Do not mark a slice complete while the repository documentation still describes an older state.

## Architecture rules

- OSCAR orchestrates specialist tools; it should not reimplement them poorly.
- Controller owns fast intent/epistemic routing decisions.
- OSCAR Event Archive owns canonical memory; semantic/graph indexes are derived.
- OSCAR owns native Transport/Grid; Latch is reference material, not a dependency.
- OSCAR owns native Model Router/fallbacks; SwitchRoute is reference material.
- OSCAR Mobile is OSCAR on the phone, not a separate assistant.
- PCs are optional worker nodes, not OSCAR's host.
- ESP32/Pico own edge presence and deterministic hardware behavior.
- Hardware safety must not depend on an LLM or Internet connection.
- Reflex commands must not traverse the full reasoning stack.
- Learned skills/protocols must never grant themselves new permissions.

## Pull requests

Keep PRs focused. Include:

- what changed;
- why it belongs in the current slice;
- why the chosen design is the simplest suitable option;
- important boundaries/state ownership affected;
- failure behavior considered;
- how it was tested;
- known limitations;
- docs updated;
- screenshots/video for UI changes where useful;
- hardware test notes for embedded changes.

Prefer small, reviewable changes over broad rewrites. Keep unrelated refactors separate when they would obscure the behavioral change.

## Commit style

Use clear imperative messages where practical, for example:

- `feat(edge): add typed Pico heartbeat`
- `feat(voice): add barge-in state machine`
- `docs: update slice 03 capability registry plan`
- `fix(router): avoid memory lookup for known reflex intent`
- `test(edge): cover reconnect backoff`

## Security

Do not commit secrets, API keys, OAuth tokens, voice embeddings, private recordings or user memory/state. See `SECURITY.md` and `docs/SECURITY.md`.

## Owner-approved Slice 07 rescope

Slice 07 is COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION; physical Edge
acceptance is DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED. This explicit owner
decision permits Slice 08 continuation; it does not grant physical PASS or Gate C
PASS. Return during Slice 15/16 and verify before Slice 17 Unified Alpha PASS.
Preserve the [hardware guide](docs/EDGE-HARDWARE-ACCEPTANCE.md) and historical
SIMULATED evidence.
