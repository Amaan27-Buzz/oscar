# Claude Code context

@AGENTS.md

Use `AGENTS.md` as the canonical repository-wide instruction set.

When the task touches UI, UX, motion, Sunday, desktop apps or frontend implementation, also load:

- `DESIGN.md`
- `TASTE.md`
- `docs/UI-AVATAR.md`
- `docs/SURFACES.md`

When the task touches a subsystem, load only the relevant domain docs rather than pulling the entire repository documentation into context.

Do not duplicate durable project rules into this file. Update `AGENTS.md`, `DESIGN.md`, `TASTE.md` or the relevant domain doc instead so Codex, Claude, Gemini, Copilot and Cursor stay aligned.
