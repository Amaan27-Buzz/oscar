# Changelog

Significant OSCAR milestones are recorded here. Detailed implementation status remains in `docs/ROADMAP.md`.

## Unreleased

### Added

- Isolated, dependency-free Sunday Home + Sentry/Awareness interaction study, with official shipping-product research using the Appllama skills, independent presence/acoustic/attention states, weighted puck settling, contextual disclosures, shared text/voice preview and robustness fixtures. Browser verification is separate from native/device acceptance; manual visual review remains pending and Slice 00.5 is not complete.

- `ENGINEERING.md` as the canonical system-design/code-quality standard.
- `docs/PERSONAL-POLICY.md` for open-ended natural-language preferences and policy precedence.
- `docs/COMMUNICATION.md` for calls, messaging, meetings, transcription, dictation and AI call handling.
- `docs/WORKERS.md` for temporary/persistent delegated sub-agents and self-repair/rerouting.
- `docs/JARVIS-GAP-REVIEW.md` benchmarking OSCAR against VoiceOS and MCU JARVIS.
- `docs/COMPETITIVE-BENCHMARK.md` comparing VoiceOS, MCU JARVIS, ChatGPT, Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi.
- `docs/EPISTEMIC-INTEGRITY.md` defining evidence-backed reporting, explicit uncertainty and non-yes-man behavior.
- `docs/RUNTIME-FOUNDATIONS.md` defining Universal Channel Gateway, Durable Execution Runtime, Capability Catalog, Learned Automation Evaluation and Artifact/Result Model.
- `docs/NATIVE-INFRASTRUCTURE.md` defining native OSCAR Transport + Capability Fabric and native OSCAR Model Router, with Latch/SwitchRoute retained only as reference/prototype sources.
- `docs/MODEL-ROUTING.md` defining provider classes, multi-key credential pools, automatic/manual routing modes, task/model affinity, fallback semantics, local runtimes, coding-agent executors and usage/history requirements.
- `docs/BUILD-GATES.md` grouping the detailed slices into five manual verification milestones for the fast developer-alpha build.
- `.env.example` with placeholder-only local development slots for GroqCloud, OpenRouter, NVIDIA NIM, Google AI Studio, Z.ai, Ollama Cloud and local Ollama/LM Studio/vLLM endpoints.
- World Model, Perception Fabric, live-context search, entity graph, Executive Planner, Action Ledger/Undo, VoiceOS-grade `Dictate / Edit / Ask / Act`, teach-by-demonstration, predictive intelligence and self-maintenance added to the architecture.
- Full voice architecture: Voice Input, stable OSCAR Voice Identity, Voice Match, Voice Map and self-voice suppression.
- Always-on local acoustic Sentry plane for wake/VAD, speaker presence/classification, configured sound events and barge-in without default continuous cloud transcription.
- Voice Map privacy/retention rules and explicit separation from authorization.
- Voice Identity fallback/degradation rules so TTS provider choice does not silently redefine OSCAR's voice.

### Changed

- Added restrained state-specific eye/mouth shapes to the Sunday study avatar, with reduced-motion support.

- Simplified the two Sunday study surfaces after manual feedback: centered physical presence, shorter state copy, compact input and Awareness controls, with explanations disclosed on demand.

- Sunday visual evaluation now uses compact physical presence and a 70/20/10 restraint/tactile/personality blend. Local Sentry awareness, conversational Listening, conversation mute and software acoustic-awareness off remain distinct.

- Removed `.github/README.md` so the intended root README is surfaced.
- Roadmap starts software-first with the OSCAR Core Loop rather than ESP32/Pico hardware.
- **Latch is no longer described as a required bridge/service.** Its useful architecture/logic is folded into native OSCAR Transport + Capability Fabric.
- **SwitchRoute is no longer described as a required routing service.** Its useful architecture/logic is folded into the native OSCAR Model Router.
- Native model routing now explicitly separates Jev decision class, capability/executor selection and provider/model/credential selection.
- Provider connections may use independent credential pools with per-slot health/quota/rate/usage state while raw secrets remain local and masked.
- Routing profiles now include Auto, Fast, Balanced, Heavy Duty, Free First, Cheap, Local, Private, Manual and Specialist behavior.
- Coding agents such as Codex, Claude Code and OpenCode are modeled as executable capabilities rather than flattened into ordinary model-provider keys.
- ChatGPT is now described as a provider/surface reached through OSCAR-owned adapters rather than through a mandatory Latch deployment; ChatGPT-to-OSCAR uses an OSCAR-owned plugin/connector.
- ESP32/Pico Edge uses a small native OSCAR transport/client rather than `Latch Edge` as a required external runtime.
- Detailed slices remain the engineering unit while Gate A–E provide explicit cross-slice manual acceptance points.
- Slice 03 is now Native OSCAR Transport + Capability Catalog.
- Slice 04 is now Native OSCAR Model Router + cloud intelligence.
- Slice 08 now explicitly builds OSCAR Voice Identity, Voice Match, Voice Map, self-voice suppression and multi-device arbitration.
- Slice 11 now explicitly builds Sentry's local acoustic plane and feeds speaker/audio events into Perception/World Model.
- Slice 12 commissioning now validates Voice Identity, Voice Match, optional Voice Map, self-voice suppression and acoustic-Sentry privacy settings.
- Hardware and engineering work now uses native OSCAR Edge/device capabilities plus whichever installed or connected specialist applications are actually available; OSCAR has no dedicated hardware-workbench project dependency.
- Slice 15 is physical/device capability expansion and general specialist engineering rather than integration with a separate workbench product.
- `ENGINEERING.md`/`AGENTS.md` completion rules continue to require independent verification where practical.

### Planned

- Slice 01 — **OSCAR Core Loop**: typed objective/task/capability/action/result/evidence contracts, minimal durable execution, Action Ledger/Artifact foundations, independent verification and evidence-backed reporting.
- Gate A manual verification after Slices 01–04, followed by Gate B–E as the larger developer-alpha milestones.

## 2026-09-29 — Repository foundation

### Added

- Canonical OSCAR product definition and JARVIS-inspired capability benchmark.
- Architecture covering Jev, LRA + Supermemory, cloud/model routing, Sunday, desktop/Worker nodes, OSCAR Edge and general physical/device capabilities.
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
