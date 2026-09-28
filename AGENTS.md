# AGENTS.md

Instructions for Codex and other coding agents working in this repository.

## Read first

Before editing, read:

- `README.md`
- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- the relevant domain document(s)

Treat these as the current product contract. If implementation and docs disagree, investigate the mismatch rather than silently choosing one.

## Working style

- Work on one product slice or narrowly scoped sub-slice at a time.
- Do not brute-force around an architectural problem. Inspect current best practices, available libraries/frameworks and existing OSCAR infrastructure first.
- Prefer modular components over monolithic files or god objects.
- Do not create fake/demo states that make an unfinished capability appear functional.
- Preserve explicit failure states and report blockers instead of fabricating success.
- Reuse existing projects and specialist tools when they are the right execution environment.

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
12. Generated skills/routines/protocols cannot self-grant permissions.
13. Consequential actions must be attributable, permission-aware and auditable.

## Specialist delegation examples

Do not use OSCAR's generic path when a better specialist is available.

- Repository implementation/debugging → Codex or another coding agent.
- UI/UX work → relevant design skill/plugin plus coding agent; verify visually.
- GUI-only operation → computer-use worker.
- Notes/knowledge workflows → connected Notion/Obsidian-style capability when available.
- Hardware design/provisioning → Kinetable.
- General autonomous model work → SwitchRoute.
- Personal/complex ChatGPT-context work → ChatGPT through Latch.

## Tests

Every slice should define an explicit test checklist before being marked complete. Include failure cases, disconnects/timeouts and safety behavior where applicable.

For hardware-facing changes, separate host/simulator tests from real-device verification and state clearly which has been run.

## Documentation is part of the change

Every completed slice or architectural change must update:

- `README.md` status/current-position section;
- `docs/ROADMAP.md`;
- relevant feature/architecture/domain docs;
- `docs/DECISIONS.md` when an invariant changes;
- `CHANGELOG.md` for user/developer-visible milestones.

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
