# GitHub repository configuration

This directory contains repository-level collaboration, agent and validation configuration.

- `CODEOWNERS` — default ownership/review responsibility.
- `PULL_REQUEST_TEMPLATE.md` — slice-aware PR checklist.
- `ISSUE_TEMPLATE/` — bug, feature, documentation and slice-task forms.
- `copilot-instructions.md` — concise repository-wide GitHub Copilot context.
- `instructions/ui.instructions.md` — path-specific UI/design rules for Copilot.
- `workflows/docs-check.yml` — lightweight repository-contract checks.

Canonical cross-agent project rules live in `../AGENTS.md`. Visual truth lives in `../DESIGN.md` and `../TASTE.md`. Agent-specific files stay intentionally thin so the repository does not develop several conflicting instruction systems.

See `../docs/AGENT-CONTEXT.md` for the complete Codex/Claude/Gemini/Copilot/Cursor context layout.
