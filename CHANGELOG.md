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
- Roadmap slices now incorporate the system-level JARVIS gaps and the final competitor-derived runtime primitives without changing the immediate next implementation target.
- `ENGINEERING.md` and `AGENTS.md` now require independent verification where practical and prohibit unqualified completion claims that exceed evidence.
- Slice 05 now establishes Epistemic Integrity, Action Ledger evidence state, Artifact/Result foundations and the first durable task substrate.
- Slice 07 now includes the Universal Channel Gateway.
- Slice 13 now includes durable Worker recovery, dynamic capability search and learned-automation evaluation/promotion.
- Slice 15 now explicitly tests truthfulness/verification-state integrity in addition to reliability/security.

### Planned

- Slice 01 — OSCAR Edge runtime skeleton: ESP32 gateway + RP2040/Pico controller + typed event model.

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
- Slice 01: next.
