# Changelog

Significant OSCAR milestones are recorded here. Detailed implementation status remains in `docs/ROADMAP.md`.

## Unreleased

### Added

- Isolated, dependency-free Sunday Home + Sentry/Awareness interaction study, with official shipping-product research using the Appllama skills, independent presence/acoustic/attention states, weighted puck settling, contextual disclosures, shared text/voice preview and robustness fixtures. Browser verification is separate from native/device acceptance; manual visual review remains pending and Slice 00.5 is not complete.

- `docs/CONNECTION-GRID.md` defining OSCAR's Sunday/cloud/desktop/Edge availability and remote-control fabric, graceful degradation, remote continuation and portable free-tier/paid/BYOC cloud coordination.
- `docs/PERSONA.md` defining user-configurable character traits, context triggers, original starting profiles and the invariant that Persona cannot reduce truthfulness, safety or permission requirements.
- `image-prompts/` reference library covering web, Sunday, desktop and system surfaces; image prompts are development references while coded UI remains the product source of truth.
- Optional Sentry `Context Capture` and `Daily Journal` modes for explicitly enabled cross-channel continuity capture where platform capability, consent and law permit it.
- Daily continuity retention model separating raw audio, transcript, summary and memory extraction.
- Sunday owner-control semantics for pause/cancel/revoke/approval across the Connection Grid.
- Remote continuation semantics for long-running desktop/Codex/build/render work, including optional post-verification sleep/shutdown and capability-gated Wake-on-LAN.
- `ENGINEERING.md` as the canonical system-design/code-quality standard.
- `docs/PERSONAL-POLICY.md` for open-ended natural-language preferences and policy precedence.
- `docs/COMMUNICATION.md` for calls, messaging, meetings, transcription, dictation and communication continuity.
- `docs/WORKERS.md` for temporary/persistent delegated sub-agents and self-repair/rerouting.
- `docs/JARVIS-GAP-REVIEW.md` benchmarking OSCAR against VoiceOS and MCU JARVIS.
- `docs/COMPETITIVE-BENCHMARK.md` comparing relevant assistant/agent systems.
- `docs/EPISTEMIC-INTEGRITY.md` defining evidence-backed reporting, explicit uncertainty and non-yes-man behavior.
- `docs/RUNTIME-FOUNDATIONS.md` defining Universal Channel Gateway, Durable Execution Runtime, Capability Catalog, Learned Automation Evaluation and Artifact/Result Model.
- `docs/NATIVE-INFRASTRUCTURE.md` defining native OSCAR Transport + Capability Fabric and native OSCAR Model Router, with Latch/SwitchRoute retained only as reference/prototype sources.
- `docs/MODEL-ROUTING.md` defining provider classes, multi-key credential pools, automatic/manual routing modes, task/model affinity, fallback semantics, local runtimes, coding-agent executors and usage/history requirements.
- `docs/BUILD-GATES.md` grouping detailed slices into five manual verification milestones.
- `.env.example` with placeholder-only development slots for GroqCloud, OpenRouter, NVIDIA NIM, Google AI Studio, Z.ai, Ollama Cloud and local Ollama/LM Studio/vLLM endpoints.
- World Model, Perception Fabric, live-context search, entity graph, Executive Planner, Action Ledger/Undo, `Dictate / Edit / Ask / Act`, teach-by-demonstration, predictive intelligence and self-maintenance architecture.
- Voice Input, stable OSCAR Voice Identity, Voice Match, Voice Map and self-voice suppression.
- Persistent local acoustic Sentry plane for wake/VAD, speaker presence/classification, configured sound events and barge-in without default continuous cloud transcription.
- Continuous-interface motion language: shared geometry, contextual expansion, weighted springs, velocity continuity and state-driven motion.
- Explicit UI distinction between `Sentry Aware`, conversational `Listening`, `Muted`, `Acoustic Awareness Off` and text input.
- Kaizen UI workflow: study shipping patterns, build a small real surface, visually inspect, improve the largest weakness and expand only after the pattern survives implementation.

### Changed

- Added restrained state-specific eye/mouth shapes to the Sunday study avatar, with reduced-motion support.

- Simplified the two Sunday study surfaces after manual feedback: centered physical presence, shorter state copy, compact input and Awareness controls, with explanations disclosed on demand.

- Sunday visual evaluation now uses compact physical presence and a 70/20/10 restraint/tactile/personality blend. Local Sentry awareness, conversational Listening, conversation mute and software acoustic-awareness off remain distinct.

- Architecture now treats **Connection Grid** as the availability/control topology over native transport rather than leaving remote continuity implicit.
- Slice 03 now includes Connection Grid/coordinator foundations; Slice 05 includes real remote continuation; Slice 09 includes Sunday Grid owner controls; Slice 11 includes optional continuity capture; Slice 12 commissions Grid/Persona/capture; Slice 16 explicitly stress-tests Grid/capture/Persona failure boundaries.
- Sentry is now explicitly defined as persistent JARVIS-like awareness when enabled, while recording/transcription remains a separate explicit capability/policy choice.
- Communication docs now support optional day-to-day continuity capture across calls/messages/mail/meetings/in-person conversation only where actual platform access, permission, consent and law allow.
- Sunday is the preferred everyday owner control/kill-switch surface, while deterministic local hardware safety remains above phone/cloud commands.
- Cloud coordination is provider-portable and may use free-tier, paid or user-owned deployment; no single cloud vendor is architectural identity.
- Persona is now a first-class configurable presentation layer distinct from Personal Policy, memory and permissions.
- Removed `.github/README.md` so the intended root README is surfaced.
- Roadmap starts software-first with the OSCAR Core Loop rather than ESP32/Pico hardware.
- **Latch is no longer a required bridge/service.** Its useful architecture/logic is folded into native OSCAR Transport + Capability Fabric.
- **SwitchRoute is no longer a required routing service.** Its useful architecture/logic is folded into the native OSCAR Model Router.
- Native model routing explicitly separates Jev decision class, capability/executor selection and provider/model/credential selection.
- Provider connections may use independent credential pools with per-slot health/quota/rate/usage state while secrets remain local/masked.
- Routing profiles include Auto, Fast, Balanced, Heavy Duty, Free First, Cheap, Local, Private, Manual and Specialist.
- Coding agents such as Codex, Claude Code and OpenCode are executable capabilities rather than ordinary provider-key entries.
- ChatGPT is a provider/surface reached through OSCAR-owned adapters; ChatGPT-to-OSCAR uses an OSCAR-owned plugin/connector path.
- ESP32/Pico Edge uses a small native OSCAR client rather than a required external Latch Edge runtime.
- Detailed slices remain the engineering unit while Gate A–E provide manual integration checkpoints.
- Hardware/engineering work uses native Edge/device capabilities plus replaceable installed/connected specialist software; no dedicated hardware-workbench project is required.
- `ENGINEERING.md`/`AGENTS.md` completion rules require independent verification where practical.
- `DESIGN.md`, `TASTE.md`, `docs/SUNDAY-DESIGN.md`, `docs/UI-AVATAR.md` and `docs/SURFACES.md` define **Quietly Alive + Playful Precision**: roughly 70% restraint/whitespace, 20% tactile industrial precision and 10% approachable personality.
- OSCAR's material palette favors warm cream/off-white surfaces and graphite typography, with blue/yellow reserved for identity/state.
- The avatar is a small/medium weighted presence object rather than a giant mascot.
- Fluid motion is part of layout/state architecture, not a post-build polish pass; UI remains correct when motion is disabled.
- Sunday is presence-first rather than a `Talk to OSCAR` launcher: Sentry may already be locally aware while active conversational `Listening` remains distinct.
- UI research may use Appllama/App Design and Impeccable as development aids, but real coded surfaces become source of truth once direction is promising.

### Planned

- Slice 01 — **OSCAR Core Loop**: typed objective/task/capability/action/result/evidence contracts, minimal durable execution, Action Ledger/Artifact foundations, independent verification and evidence-backed reporting.
- Gate A manual verification after Slices 01–04, followed by Gate B–E as larger developer-alpha milestones.

## 2026-09-29 — Repository foundation

### Added

- Canonical OSCAR product definition and JARVIS-inspired capability benchmark.
- Architecture covering Jev, LRA + Supermemory, cloud/model routing, Sunday, desktop/Worker nodes, OSCAR Edge and physical/device capabilities.
- Continuous single-conversation memory direction rather than chat-sidebar organization.
- Voice, Sentry, Voice Match and low-latency interaction plans.
- Learning layer: procedural memory, portable `SKILL.md`-style Skills, routines and stateful Protocols.
- Capability-based orchestration and specialist delegation.
- Avatar/presence UI specification and brand assets.
- **Quietly Alive** design system in `DESIGN.md` and `TASTE.md`.
- Cross-agent context architecture: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Copilot instructions, Cursor rule and portable Skills.
- Slice-based roadmap and architecture decision records.
- Repository support files, contribution/agent guidance and GitHub templates.

### Status

- Slice 00: complete.
- Slice 01: next — OSCAR Core Loop.
