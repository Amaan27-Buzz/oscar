# Claude Code context

@AGENTS.md

Use `AGENTS.md` as the canonical repository-wide instruction set. For implementation/system-design work, also load:

- `ENGINEERING.md`
- `docs/EPISTEMIC-INTEGRITY.md`

When the task touches orchestration, Workers, Protocols, channels or long-running execution, also load `docs/RUNTIME-FOUNDATIONS.md` plus the relevant domain docs.

When the task touches UI, UX, motion, OSCAR Mobile, desktop apps or frontend implementation, also load:

- `DESIGN.md`
- `TASTE.md`
- `docs/UI-AVATAR.md`
- `docs/SURFACES.md`

When the task touches a subsystem, load only the relevant domain docs rather than pulling the entire repository documentation into context.

Do not duplicate durable project rules into this file. Update `AGENTS.md`, `ENGINEERING.md`, `DESIGN.md`, `TASTE.md` or the relevant domain doc instead so Codex, Claude, Gemini, Copilot and Cursor stay aligned.
