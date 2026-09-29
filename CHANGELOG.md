# Changelog

Significant OSCAR milestones are recorded here. Detailed implementation status remains in `docs/ROADMAP.md`.

## Unreleased

### Added

- `ENGINEERING.md` as the canonical system-design/code-quality standard: simplicity, modularity, reuse discipline, typed contracts, explicit state ownership, dependency control, reliability, security, tests, observability, performance and small reversible changes.
- Engineering review gates wired into `AGENTS.md`, development/contribution guidance, slice skill, PR template and repository checks.
- `docs/PERSONAL-POLICY.md` defining open-ended natural-language preferences, policy precedence, conflict handling and the distinction between memory, permission and protocol.
- `docs/COMMUNICATION.md` defining OSCAR's unified communication layer for calls, messaging, meetings, transcription, system-wide dictation, AI call handling and follow-up work.
- `docs/WORKERS.md` defining temporary/persistent delegated sub-agents, device-mesh execution, Worker collaboration, social-media management and Jev-based self-repair/rerouting.
- `docs/JARVIS-GAP-REVIEW.md` benchmarking OSCAR against the practical VoiceOS interaction baseline and the broader MCU JARVIS capability pattern.
- World Model, Perception Fabric, universal live context/search, canonical entity graph, Executive Planner, Action Ledger/Undo, multi-device voice arbitration, VoiceOS-grade `Dictate / Edit / Ask / Act` interaction runtime, teach-by-demonstration, predictive intelligence and self-maintenance added to the architecture/roadmap.
- Architecture decisions updated so Workers remain below one OSCAR executive rather than becoming independent assistant silos.

### Changed

- Removed `.github/README.md` so GitHub does not surface repository-configuration copy in place of the intended root OSCAR README experience.
- Roadmap slices now incorporate the system-level JARVIS gaps without changing the immediate next implementation target.

### Planned

- Slice 01 — OSCAR Edge runtime skeleton: ESP32 gateway + RP2040/Pico controller + typed event model.

## 2026-09-29 — Repository foundation

### Added

- Canonical OSCAR product definition and JARVIS-inspired capability benchmark.
- Architecture covering Jev, LRA + Supermemory, Latch, SwitchRoute, Sunday, desktop/worker nodes, OSCAR Edge and Kinetable.
- Continuous single-conversation memory direction rather than chat-sidebar organization.
- Voice, Sentry, Voice Match and low-latency interaction plans.
- Learning layer: procedural memory, portable `SKILL.md`-style skills, routines and stateful protocols.
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
