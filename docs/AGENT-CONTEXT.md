# Coding-agent context

OSCAR keeps one canonical project truth and uses thin agent-specific adapters. The goal is consistency without copying large instruction blocks into every tool.

## Canonical files

| File | Purpose |
|---|---|
| `AGENTS.md` | repository-wide architecture, safety, workflow and documentation rules |
| `ENGINEERING.md` | canonical system-design and code-quality standard |
| `DESIGN.md` | normative visual tokens and durable design-system decisions |
| `TASTE.md` | qualitative UI taste, composition rules and anti-slop quality bar |
| `docs/PRODUCT.md` | product truth and north star |
| `docs/ARCHITECTURE.md` | system boundaries and responsibilities |
| `docs/JARVIS-GAP-REVIEW.md` | JARVIS/VoiceOS system-level gap benchmark |
| `docs/COMPETITIVE-BENCHMARK.md` | final comparison against VoiceOS, MCU JARVIS, ChatGPT/Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi |
| `docs/EPISTEMIC-INTEGRITY.md` | evidence states, verification-before-completion, correction and non-yes-man behavior |
| `docs/RUNTIME-FOUNDATIONS.md` | Universal Channel Gateway, Durable Execution Runtime, Capability Catalog/Search, learned-automation evaluation and Artifact/Result model |
| `docs/ROADMAP.md` | slice order/current implementation state |
| `docs/DECISIONS.md` | stable architecture decisions |
| `docs/MEMORY.md` | LRA/Supermemory/Jev memory and continuity model |
| `docs/PERSONAL-POLICY.md` | explicit user preferences/policy, precedence and editing |
| `docs/COMMUNICATION.md` | calls, meetings, messaging, dictation and communication autonomy |
| `docs/WORKERS.md` | delegated sub-agents, lifecycle, recovery and collaboration |
| `docs/ORCHESTRATION.md` | capability routing, Skills, Workers, routines and Protocols |
| `docs/UI-AVATAR.md` | avatar, expression and state language |
| `docs/SURFACES.md` | Sunday/desktop/edge/Worker surface responsibilities |

Agent-specific files should point back to these rather than becoming independent sources of truth.

## Agent adapters

### Codex / AGENTS-aware agents

`AGENTS.md` is canonical. Implementation work also loads `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`. Add nested `AGENTS.md` files only when a real sub-tree develops materially different rules, for example future `edge/`, `apps/sunday/` or `apps/desktop/` directories.

Do not create nested files prematurely.

### Claude Code

`CLAUDE.md` imports/references the canonical instructions and tells Claude to load design files only for relevant work. Repository implementation is still governed by `ENGINEERING.md` and Epistemic Integrity even when an adapter does not duplicate those rules.

### Gemini CLI

`GEMINI.md` imports the same canonical files through Gemini's context mechanism.

### GitHub Copilot

- `.github/copilot-instructions.md` provides concise repository-wide rules.
- `.github/instructions/ui.instructions.md` adds path-specific UI guidance when Copilot works on frontend/native UI files.

### Cursor

`.cursor/rules/oscar-design.mdc` applies the OSCAR design system to relevant UI files. `AGENTS.md` and `ENGINEERING.md` remain the broader cross-agent sources.

## Portable Skills

OSCAR keeps reusable workflows in open `SKILL.md` form:

```text
skills/
├── oscar-ui/
│   └── SKILL.md
└── oscar-slice/
    └── SKILL.md
```

- `oscar-ui` handles design/implementation/review of OSCAR surfaces.
- `oscar-slice` handles one roadmap slice end to end and applies `ENGINEERING.md`.

Skills are workflow-specific; `AGENTS.md` should not grow into a giant prompt containing every workflow.

## Context-loading rule

Load the least context that is sufficient:

- any implementation task → `ENGINEERING.md` + `docs/EPISTEMIC-INTEGRITY.md` + relevant product/architecture/domain context;
- UI task → core docs + `ENGINEERING.md` + `DESIGN.md` + `TASTE.md` + relevant surface docs;
- edge/hardware task → core docs + `ENGINEERING.md` + hardware/security docs;
- memory task → core docs + `ENGINEERING.md` + `docs/MEMORY.md`;
- preference/policy task → core docs + `ENGINEERING.md` + `docs/PERSONAL-POLICY.md`;
- calls/meetings/messaging/dictation task → core docs + `ENGINEERING.md` + `docs/COMMUNICATION.md` + `docs/RUNTIME-FOUNDATIONS.md` + relevant surface docs;
- Worker/sub-agent task → core docs + `ENGINEERING.md` + `docs/EPISTEMIC-INTEGRITY.md` + `docs/WORKERS.md` + `docs/ORCHESTRATION.md` + `docs/RUNTIME-FOUNDATIONS.md`;
- orchestration/learning task → core docs + `ENGINEERING.md` + `docs/ORCHESTRATION.md` + `docs/RUNTIME-FOUNDATIONS.md`;
- World Model / Perception Fabric / Executive Planner / Action Ledger / Interaction Runtime task → core docs + `ENGINEERING.md` + `docs/ARCHITECTURE.md` + `docs/JARVIS-GAP-REVIEW.md` + `docs/EPISTEMIC-INTEGRITY.md`;
- Durable Runtime / capability search / Channel Gateway / Artifact Model task → core docs + `ENGINEERING.md` + `docs/RUNTIME-FOUNDATIONS.md` + `docs/EPISTEMIC-INTEGRITY.md`.

Do not dump the entire documentation tree into every agent turn. More context is not automatically better.

## Verification rule for agents

Before declaring a repository/runtime task complete:

1. inspect the authoritative resulting state;
2. run relevant tests/checks;
3. distinguish reported success from verified completion;
4. state any unverified surfaces explicitly;
5. update docs only after confirming the architecture/status claim is actually true.

An agent must not claim that it updated "the architecture and roadmap" if it only created one review document.

## Keeping files synchronized

When a durable project rule changes:

1. update the canonical file first;
2. update an adapter only if its routing text is now wrong;
3. avoid copying the entire new rule into every adapter;
4. update README/documentation links if discoverability changes;
5. verify the affected canonical files before claiming the cross-doc update is complete.

When an engineering principle changes system-wide, update `ENGINEERING.md`. When a UI direction changes system-wide, update both `DESIGN.md` and `TASTE.md`; when only one surface changes, keep the global system stable and document the surface-specific decision separately.

When communication, Personal Policy or Worker behavior changes system-wide, update their dedicated domain document plus architecture/decision/roadmap references if the boundary changed.

When the competitive benchmark changes a system-level primitive or priority, reconcile `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md`, `README.md` and the relevant domain docs in the same change.
