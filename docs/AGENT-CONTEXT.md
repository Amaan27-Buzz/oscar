# Coding-agent context

OSCAR keeps one canonical project truth and uses thin agent-specific adapters. The goal is consistency without copying large instruction blocks into every tool.

## Canonical files

| File | Purpose |
|---|---|
| `AGENTS.md` | repository-wide architecture, safety, workflow and documentation rules |
| `DESIGN.md` | normative visual tokens and durable design-system decisions |
| `TASTE.md` | qualitative UI taste, composition rules and anti-slop quality bar |
| `docs/PRODUCT.md` | product truth and north star |
| `docs/ARCHITECTURE.md` | system boundaries and responsibilities |
| `docs/ROADMAP.md` | slice order/current implementation state |
| `docs/DECISIONS.md` | stable architecture decisions |
| `docs/UI-AVATAR.md` | avatar, expression and state language |
| `docs/SURFACES.md` | Sunday/desktop/edge surface responsibilities |

Agent-specific files should point back to these rather than becoming independent sources of truth.

## Agent adapters

### Codex / AGENTS-aware agents

`AGENTS.md` is canonical. Add nested `AGENTS.md` files only when a real sub-tree develops materially different rules, for example future `edge/`, `apps/sunday/` or `apps/desktop/` directories.

Do not create nested files prematurely.

### Claude Code

`CLAUDE.md` imports/references the canonical instructions and tells Claude to load design files only for relevant work.

### Gemini CLI

`GEMINI.md` imports the same canonical files through Gemini's context mechanism.

### GitHub Copilot

- `.github/copilot-instructions.md` provides concise repository-wide rules.
- `.github/instructions/ui.instructions.md` adds path-specific UI guidance when Copilot works on frontend/native UI files.

### Cursor

`.cursor/rules/oscar-design.mdc` applies the OSCAR design system to relevant UI files. `AGENTS.md` remains the broader cross-agent source.

## Portable skills

OSCAR also keeps reusable workflows in open `SKILL.md` form:

```text
skills/
├── oscar-ui/
│   └── SKILL.md
└── oscar-slice/
    └── SKILL.md
```

- `oscar-ui` handles design/implementation/review of OSCAR surfaces.
- `oscar-slice` handles one roadmap slice end to end.

Skills are workflow-specific; `AGENTS.md` should not grow into a giant prompt containing every workflow.

## Context-loading rule

Load the least context that is sufficient:

- architecture/backend task → core product/architecture/domain docs;
- UI task → core docs + `DESIGN.md` + `TASTE.md` + relevant surface docs;
- edge/hardware task → core docs + hardware/security docs;
- memory task → core docs + `docs/MEMORY.md`;
- orchestration/learning task → core docs + `docs/ORCHESTRATION.md`.

Do not dump the entire documentation tree into every agent turn. More context is not automatically better.

## Keeping files synchronized

When a durable project rule changes:

1. update the canonical file first;
2. update an adapter only if its routing text is now wrong;
3. avoid copying the entire new rule into every adapter;
4. update README/documentation links if discoverability changes.

When a UI direction changes system-wide, update both `DESIGN.md` and `TASTE.md`; when only one surface changes, keep the global system stable and document the surface-specific decision separately.
