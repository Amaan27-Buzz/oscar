# Changelog

Significant OSCAR milestones are recorded here. Detailed implementation status remains in `docs/ROADMAP.md`.

## Unreleased

### Added

- `ENGINEERING.md` as the canonical system-design/code-quality standard: simplicity, modularity, reuse discipline, typed contracts, explicit state ownership, dependency control, reliability, security, tests, observability, performance and small reversible changes.
- Engineering review gates wired into `AGENTS.md`, development/contribution guidance, slice skill, PR template and repository checks.
- `docs/PERSONAL-POLICY.md` defining open-ended natural-language preferences, policy precedence, conflict handling and the distinction between memory, permission and Protocol.
- `docs/COMMUNICATION.md` defining OSCAR's unified communication layer for calls, messaging, meetings, transcription, system-wide dictation, AI call handling and follow-up work.
- `docs/WORKERS.md` defining temporary/persistent delegated sub-agents, device-mesh execution, Worker collaboration, social-media management and Jev-based self-repair/rerouting.
- `docs/JARVIS-GAP-REVIEW.md` benchmarking OSCAR against the practical VoiceOS interaction baseline and broader MCU JARVIS capability pattern.
- `docs/COMPETITIVE-BENCHMARK.md` comparing the final pre-implementation architecture against VoiceOS, MCU JARVIS, ChatGPT, Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi.
- `docs/EPISTEMIC-INTEGRITY.md` defining evidence-backed reporting, explicit known/inferred/recalled/reported/verified/unknown states, non-yes-man behavior and verification-before-completion rules.
- `docs/RUNTIME-FOUNDATIONS.md` defining the Universal Channel Gateway, Durable Execution Runtime, Capability Catalog + Dynamic Tool Search, Learned Automation Evaluation Pipeline and Artifact / Result Model.
- World Model, Perception Fabric, universal live context/search, canonical entity graph, Executive Planner, Action Ledger/Undo, multi-device voice arbitration, VoiceOS-grade `Dictate / Edit / Ask / Act` Interaction Runtime, teach-by-demonstration, predictive intelligence and self-maintenance added to architecture/roadmap.
- Architecture decisions updated so Workers remain below one OSCAR executive rather than becoming independent assistant silos.
- Durable execution semantics added for checkpoints, leases, heartbeats, reclaim, bounded retry and restart/resume.
- Progressive capability discovery added so OSCAR does not load every tool/plugin/Skill contract into every model context.
- Learned automation promotion now requires evaluation/replay where possible rather than trusting one successful run.
- Finished outputs can be represented as first-class Artifacts/Results with provenance, ownership, version/location and verification state.

### Changed

- Removed `.github/README.md` so GitHub does not surface repository-configuration copy in place of the intended root OSCAR README experience.
- Roadmap now starts with a **software-first OSCAR Core Loop** rather than ESP32/Pico hardware. The first implementation proves `objective → capability → execute → evidence → verify → ledger/artifact → report` before attaching embodiments.
- ESP32/Pico Edge remains a fundamental architecture component but moves later, after Core Loop, Jev, Latch/capability discovery, cloud intelligence, a real machine Worker, and memory/Personal Policy have established stable contracts.
- Early development may run on a development computer for convenience, but the contracts explicitly cannot make that computer OSCAR's permanent host.
- `ENGINEERING.md` and `AGENTS.md` require independent verification where practical and prohibit unqualified completion claims that exceed evidence.
- The new Slice 01 establishes task/capability/action/result/evidence contracts, minimal durable task state, Action Ledger/Artifact foundations and independent verification.
- TypeSafe Jev follows as Slice 02; Latch + Capability Catalog as Slice 03; ChatGPT/SwitchRoute as Slice 04; the first real machine Worker as Slice 05; LRA/Personal Policy as Slice 06; and OSCAR Edge + reflexes as Slice 07.
- Voice, Sunday/communication, Desktop Interaction Runtime, World Model/Perception, Executive Planner/Workers and later reliability slices follow the proven core rather than preceding it.

### Planned

- Slice 01 — **OSCAR Core Loop**: typed objective/task/capability/action/result/evidence contracts, minimal durable execution, Action Ledger/Artifact foundations, independent verification and evidence-backed reporting.

## 2026-09-29 — Repository foundation

### Added

- Canonical OSCAR product definition and JARVIS-inspired capability benchmark.
- Architecture covering Jev, LRA + Supermemory, Latch, SwitchRoute, Sunday, desktop/Worker nodes, OSCAR Edge and Kinetable.
- Continuous single-conversation memory direction rather than chat-sidebar organization.
- Voice, Sentry, Voice Match and low-latency interaction plans.
- Learning layer: procedural memory, portable `SKILL.md`-style Skills, routines and stateful Protocols.
- Capability-based orchestration and specialist delegation.
- Avatar/presence UI specification and brand assets.
- **Quietly Alive** design system in `DESIGN.md`, adapted from Kinetable's Playful Precision principles for OSCAR's blue/yellow ambient identity.
- `TASTE.md` with composition, motion, copy and anti-slop quality rules for coding/design agents.
- Sunday mobile surface direction and state-specific UI guidance.
- Cross-agent context architecture: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, GitHub Copilot instructions, Cursor rule and portable `SKILL.md` workflows.
- Slice-based roadmap and architecture decision records.
- Repository support files, contribution/agent guidance and GitHub templates.

### Status

- Slice 00: complete.
- Slice 01: next — OSCAR Core Loop.
