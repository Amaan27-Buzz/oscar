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
| `docs/COMPETITIVE-BENCHMARK.md` | comparison against VoiceOS, MCU JARVIS, ChatGPT/Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi |
| `docs/EPISTEMIC-INTEGRITY.md` | evidence states, verification-before-completion, correction and non-yes-man behavior |
| `docs/RUNTIME-FOUNDATIONS.md` | Channel Gateway, Durable Runtime, Capability Catalog/Search, automation evaluation and Artifact/Result model |
| `docs/NATIVE-INFRASTRUCTURE.md` | native OSCAR Transport + Capability Fabric and native Model Router; Latch/SwitchRoute are reference/prototype inputs, not required runtimes |
| `docs/MODEL-ROUTING.md` | provider classes, credential pools, automatic/manual modes, model/task affinity, fallback, usage/history and local development credential contract |
| `docs/BUILD-GATES.md` | cross-slice manual verification milestones for the fast developer-alpha build |
| `docs/VOICE-SENTRY.md` | Voice Input, OSCAR Voice Identity, Voice Match, Voice Map, self-voice suppression and local acoustic Sentry |
| `docs/ROADMAP.md` | slice order/current implementation state |
| `docs/DECISIONS.md` | stable architecture decisions |
| `docs/MEMORY.md` | LRA/Supermemory/Jev memory and continuity model |
| `docs/PERSONAL-POLICY.md` | explicit user preferences/policy, precedence and editing |
| `docs/COMMUNICATION.md` | calls, meetings, messaging, dictation and communication autonomy |
| `docs/WORKERS.md` | delegated sub-agents, lifecycle, recovery and collaboration |
| `docs/ORCHESTRATION.md` | capability routing, Skills, Workers, routines and Protocols |
| `docs/UI-AVATAR.md` | avatar, expression and state language |
| `docs/SURFACES.md` | Sunday/desktop/edge/Worker surface responsibilities |
| `docs/SECURITY.md` | security, permissions, transport and voice/privacy boundaries |
| `docs/ONBOARDING.md` | first-run commissioning including voice and Sentry calibration |

Agent-specific files should point back to these rather than becoming independent sources of truth.

## Agent adapters

### Codex / AGENTS-aware agents

`AGENTS.md` is canonical. Implementation work also loads `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`. Add nested `AGENTS.md` files only when a real sub-tree develops materially different rules, for example future `edge/`, `apps/sunday/` or `apps/desktop/` directories.

Do not create nested files prematurely.

### Claude Code

`CLAUDE.md` imports/references canonical instructions and tells Claude to load design files only for relevant work. Repository implementation remains governed by `ENGINEERING.md` and Epistemic Integrity even when an adapter does not duplicate those rules.

### Gemini CLI

`GEMINI.md` imports the same canonical files through Gemini's context mechanism.

### GitHub Copilot

- `.github/copilot-instructions.md` provides concise repository-wide rules.
- `.github/instructions/ui.instructions.md` adds path-specific UI guidance for frontend/native UI files.

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

Skills are workflow-specific; `AGENTS.md` should not grow into a giant prompt containing every workflow.

## Context-loading rule

Load the least context sufficient for the task:

- any implementation task → `ENGINEERING.md` + `docs/EPISTEMIC-INTEGRITY.md` + relevant product/architecture/domain context;
- UI task → core docs + `DESIGN.md` + `TASTE.md` + relevant surface docs;
- edge/hardware task → core docs + `docs/NATIVE-INFRASTRUCTURE.md` + hardware/security docs;
- transport/capability-node/pairing task → `docs/NATIVE-INFRASTRUCTURE.md` + `docs/RUNTIME-FOUNDATIONS.md` + `docs/SECURITY.md`;
- model-provider/routing/credential-pool task → `docs/MODEL-ROUTING.md` + `docs/NATIVE-INFRASTRUCTURE.md` + `docs/EPISTEMIC-INTEGRITY.md`;
- coding-agent/executor selection task → `docs/MODEL-ROUTING.md` + `docs/ORCHESTRATION.md` + relevant machine-node context;
- voice/STT/TTS/Voice Match/Voice Map/Sentry task → `docs/VOICE-SENTRY.md` + `docs/SECURITY.md` + relevant surface docs; include `docs/ONBOARDING.md` when enrollment/calibration is involved;
- memory task → `docs/MEMORY.md`;
- preference/policy task → `docs/PERSONAL-POLICY.md`;
- calls/meetings/messaging/dictation task → `docs/COMMUNICATION.md` + `docs/VOICE-SENTRY.md` where audio/speaker identity is involved + relevant surface docs;
- Worker/sub-agent task → `docs/WORKERS.md` + `docs/ORCHESTRATION.md` + `docs/RUNTIME-FOUNDATIONS.md`;
- orchestration/learning task → `docs/ORCHESTRATION.md` + `docs/RUNTIME-FOUNDATIONS.md`;
- World Model / Perception / Executive Planner / Action Ledger / Interaction Runtime task → `docs/ARCHITECTURE.md` + `docs/JARVIS-GAP-REVIEW.md` + `docs/EPISTEMIC-INTEGRITY.md`;
- Durable Runtime / capability search / Channel Gateway / Artifact Model task → `docs/RUNTIME-FOUNDATIONS.md` + `docs/EPISTEMIC-INTEGRITY.md`;
- cross-slice manual acceptance work → `docs/BUILD-GATES.md` + the detailed slices in `docs/ROADMAP.md`.

Do not dump the entire documentation tree into every agent turn. More context is not automatically better.

## Native infrastructure rule

Do not revive the old assumption that OSCAR directly depends on separate Latch/SwitchRoute deployments.

Canonical mapping:

```text
Latch architecture/logic       → OSCAR Transport + Capability Fabric
SwitchRoute architecture/logic → OSCAR Model Router
```

The earlier repositories may be inspected for useful code, tests or design lessons, but a new OSCAR implementation should adopt those ideas behind OSCAR-owned contracts rather than preserve a legacy service boundary by default.

ChatGPT reaches OSCAR through an OSCAR-owned plugin/connector and transport boundary. The plugin is an interface into OSCAR, not OSCAR's intelligence or host.

## Model-routing rule

Do not collapse these decisions:

```text
Jev                  → what class of action is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

Provider keys, local runtimes and coding agents are different capability classes.

The developer may supply multiple local credential slots in `.env` for real integration testing. Never commit, print, snapshot or expose those values. Use `.env.example` only as the placeholder contract.

Routing must support automatic and manual control, preserve provider/model/credential provenance, keep unknown quota/cost/latency unknown, and never treat a model/provider success response as verified task completion.

See `docs/MODEL-ROUTING.md`.

## Build-gate rule

Detailed slices remain the implementation unit. `docs/BUILD-GATES.md` groups them into manual verification milestones:

```text
Gate A — Brain          Slices 01–04
Gate B — Can Do Work    Slices 05–06
Gate C — Embodied OSCAR Slices 07–10
Gate D — JARVIS Layer   Slices 11–14
Gate E — Unified Alpha  Slices 15–17
```

A fast 2–3 day developer-alpha sprint is a target for vertical proof, not permission to skip manual checks or relabel partial work as complete.

## Voice model rule

Do not collapse all voice work into `STT/TTS`.

The canonical distinction is:

```text
Voice Input          wake / VAD / STT / barge-in
OSCAR Voice Identity stable synthesized identity / prosody / fallback
Voice Match          authorization-oriented speaker verification
Voice Map            perception-oriented speaker recognition/context
Acoustic Sentry      local always-on wake/speech/speaker/sound events
```

Voice Map recognition never grants permission. Speaker embeddings/profiles are sensitive. OSCAR's own TTS must be excluded from speaker learning/recognition while real user barge-in remains possible.

Always-on acoustic awareness is local-first and does not imply continuous cloud transcription or raw-audio retention.

## Verification rule for agents

Before declaring a repository/runtime task complete:

1. inspect authoritative resulting state;
2. run relevant tests/checks;
3. distinguish reported success from verified completion;
4. state any unverified surfaces explicitly;
5. update docs only after confirming the architecture/status claim is actually true.

An agent must not claim that it updated `the architecture and roadmap` if it only created one review document.

## Keeping files synchronized

When a durable project rule changes:

1. update the canonical file first;
2. update an adapter only if its routing text is now wrong;
3. avoid copying the entire new rule into every adapter;
4. update README/documentation links if discoverability changes;
5. verify affected canonical files before claiming propagation is complete.

Specific propagation rules:

- native transport/model-routing boundary change → reconcile `NATIVE-INFRASTRUCTURE.md`, `MODEL-ROUTING.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md`, README and affected runtime/orchestration docs;
- provider/credential/routing-mode change → update `MODEL-ROUTING.md` first, then reconcile roadmap/features/UI data requirements where affected;
- build-gate/manual acceptance change → update `BUILD-GATES.md` and affected slice exit conditions where needed;
- voice/Voice Match/Voice Map/Sentry boundary change → reconcile `VOICE-SENTRY.md`, `ARCHITECTURE.md`, `FEATURES.md`, `ROADMAP.md`, `SECURITY.md`, `ONBOARDING.md`, relevant surface/communication docs and README;
- system-wide engineering rule → update `ENGINEERING.md`;
- system-wide visual direction → update `DESIGN.md` and, when qualitative direction changes, `TASTE.md`;
- communication/Personal Policy/Worker behavior → update dedicated domain doc plus architecture/decision/roadmap references if the boundary changed;
- competitive benchmark changes a system-level primitive → reconcile architecture, roadmap, decisions, README and relevant domain docs in the same change.
