# Contributing to OSCAR

OSCAR is being built slice-by-slice. Contributions should preserve the product architecture rather than introduce isolated features that bypass it.

## Before changing code

Read:

1. `README.md`
2. `docs/PRODUCT.md`
3. `docs/ARCHITECTURE.md`
4. `docs/ROADMAP.md`
5. `docs/DECISIONS.md`
6. the domain-specific document for the area being changed

For agent-driven work, also read `AGENTS.md`.

## Slice rule

Work on one coherent product slice at a time. A slice is complete only when:

- the scoped implementation is complete;
- important behavior has tests;
- limitations and follow-ups are explicit;
- security/safety implications have been reviewed;
- `README.md` status is updated;
- affected files under `docs/` are updated;
- the next slice or follow-up is clear.

Do not mark a slice complete while the repository documentation still describes an older state.

## Architecture rules

- OSCAR orchestrates specialist tools; it should not reimplement them poorly.
- Jev owns fast intent/epistemic routing decisions.
- LRA + Supermemory own long-term continuity and recall.
- Latch is the bridge between OSCAR, ChatGPT and execution nodes.
- SwitchRoute handles general model routing/fallbacks.
- Sunday is OSCAR on the phone, not a separate assistant.
- PCs are optional worker nodes, not OSCAR's host.
- ESP32/Pico own edge presence and deterministic hardware behavior.
- Hardware safety must not depend on an LLM or Internet connection.
- Reflex commands must not traverse the full reasoning stack.
- Learned skills/protocols must never grant themselves new permissions.

## Pull requests

Keep PRs focused. Include:

- what changed;
- why it belongs in the current slice;
- how it was tested;
- known limitations;
- docs updated;
- screenshots/video for UI changes where useful;
- hardware test notes for embedded changes.

Prefer small, reviewable changes over broad rewrites.

## Commit style

Use clear imperative messages where practical, for example:

- `feat(edge): add typed Pico heartbeat`
- `feat(voice): add barge-in state machine`
- `docs: update slice 03 capability registry plan`
- `fix(router): avoid memory lookup for known reflex intent`
- `test(edge): cover reconnect backoff`

## Security

Do not commit secrets, API keys, OAuth tokens, voice embeddings, private recordings or user memory/state. See `SECURITY.md` and `docs/SECURITY.md`.
