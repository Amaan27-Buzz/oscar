# Architecture Decisions

This file records decisions that should remain stable unless explicitly revisited. Update it when a future slice changes one of these assumptions.

## ADR-001 — OSCAR is not hardware-only

**Decision:** OSCAR is the full personal-agent system spanning cloud intelligence, phone, computers, edge hardware, memory, tools and environment.

**Reason:** the target is a coherent JARVIS-like capability model, not a robot shell with a chatbot attached.

## ADR-002 — Sunday is OSCAR on the phone

**Decision:** Sunday is a mobile embodiment/surface of OSCAR, not a separate assistant.

**Implication:** identity, memory, task state, permissions and protocols should be shared through OSCAR rather than duplicated into a separate mobile intelligence.

## ADR-003 — Laptop independence

**Decision:** OSCAR must remain operational when the user's laptop/PC is off.

**Implication:** primary availability cannot depend on a desktop daemon or local LLM. PCs join as optional worker nodes.

## ADR-004 — Cloud-first intelligence, edge-first presence

**Decision:** heavy reasoning uses cloud intelligence; low-power edge hardware owns always-on presence, sensors, reflexes and safety.

**Primary planned paths:**

- ChatGPT through Latch
- cloud models through SwitchRoute
- local deterministic logic on edge

Local PC models may exist only as optional support capabilities.

## ADR-005 — ESP32 and Pico have different jobs

**Decision:** ESP32 is the network/audio/event gateway; RP2040/Pico is the deterministic physical controller.

**Reason:** networking/orchestration and deterministic GPIO/safety behavior have different constraints.

## ADR-006 — Latch is the bridge

**Decision:** Latch is the secure integration layer between ChatGPT/cloud coordination and OSCAR devices/workers.

Embedded hardware should use a minimal Latch Edge protocol with outbound connections rather than exposing home-network endpoints publicly.

## ADR-007 — Bidirectional ChatGPT relationship

**Decision:** both directions are required:

```text
ChatGPT → OSCAR
OSCAR → ChatGPT
```

OSCAR → ChatGPT may initially require an indirect trigger/wake mechanism. The workaround must live behind a Latch abstraction so it can be replaced by a direct trigger later.

## ADR-008 — SwitchRoute handles general autonomous model routing

**Decision:** OSCAR can use SwitchRoute independently of ChatGPT for autonomous cloud reasoning, classification, extraction and fallbacks.

**Implication:** ChatGPT is a first-class brain, not the only brain.

## ADR-009 — Use specialist software rather than reimplementing it

**Decision:** OSCAR delegates to the best execution environment: Codex for coding, computer use for GUIs/verification, Kinetable for hardware engineering, connected knowledge tools for their native workspaces, and other specialist software when suitable.

**Reason:** OSCAR should orchestrate expertise rather than become a mediocre clone of every tool.

## ADR-010 — Capability advertisement

**Decision:** nodes, apps, plugins and workers advertise capabilities dynamically.

OSCAR should reason about `codex`, `computer-use`, `camera`, `relay`, `gpu`, `browser`, `kinetable`, plugins, etc. rather than assuming a specific machine or service is always present.

## ADR-011 — Voice and text share state

**Decision:** changing modality does not start a new assistant/session conceptually.

A user may speak a request, type a follow-up and continue verbally with the same active context.

## ADR-012 — Reflex commands bypass LLMs

**Decision:** wake acknowledgement, mute, stop, cancel, emergency behavior and other deterministic reflexes must not wait on ChatGPT/SwitchRoute.

**Reason:** latency, reliability and safety.

## ADR-013 — Voice Match is convenience/auth context, not strong authentication

**Decision:** speaker verification can gate personal commands and Sentry behavior, but critical actions require stronger confirmation such as phone biometric/PIN or explicit approval.

**Additional rule:** emergency stop should remain available even when the speaker is not recognized where doing so improves safety.

## ADR-014 — Sentry is local-first awareness

**Decision:** Sentry Mode continuously observes low-power local events/state and selectively escalates. It must not require continuous raw microphone/camera streaming to cloud AI.

## ADR-015 — Proactivity is scored

**Decision:** events should carry importance, urgency, confidence and interruptibility so OSCAR can choose between silent logging, notification, speech and immediate interruption.

## ADR-016 — Hardware safety is deterministic

**Decision:** emergency stop, cutoffs, interlocks and watchdog behavior stay local and remain functional without Internet/cloud intelligence.

## ADR-017 — LRA owns continuous memory; Supermemory is a backend

**Decision:** LRA is the persistent single-conversation/history architecture. Supermemory supplies semantic/profile-style memory underneath LRA.

**Implication:** internal context segmentation must not force the user into a sidebar of disconnected chats.

## ADR-018 — Jev is intent + epistemic routing

**Decision:** TypeSafe Jev decides among execute, recall, verify, reason, delegate and ask-user paths.

**Core rule:** if OSCAR lacks reliable user/project context, it retrieves or verifies it before guessing.

## ADR-019 — OSCAR learns procedures, not only facts

**Decision:** successful novel executions can be distilled into procedural memory and reusable skills.

**Goal:** repeated tasks become faster, cheaper and more deterministic over time.

## ADR-020 — OSCAR can create reusable workflows safely

**Decision:** OSCAR may create/propose/refine protocols, routines and ecosystem-compatible `SKILL.md`-style skills.

**Constraint:** generated automation cannot grant itself new permissions. Expanded authority requires review/approval.

## ADR-021 — Protocols are stateful responsibilities, not just schedules

**Decision:** OSCAR protocols may wait, observe, branch, delegate, retry, verify and escalate over long periods.

**Reason:** the target is persistent delegated responsibility, not a glorified cron/reminder system.

## ADR-022 — Native desktop surfaces are part of OSCAR

**Decision:** OSCAR will have native/lightweight Windows and macOS surfaces for voice/text, context, approvals and presence.

**Implication:** desktop UI is an embodiment; the machine worker is a capability node. Neither is the permanent host.

## ADR-023 — Kinetable is the hardware workshop

**Decision:** OSCAR should route hardware design/simulation/firmware/provisioning work to Kinetable instead of duplicating Kinetable internally.

**Long-term implication:** Kinetable-built devices should be provisionable as OSCAR/Latch Edge nodes with advertised capabilities.

## ADR-024 — Avatar is functional UI

**Decision:** the blue-shell/yellow-face avatar is a major state/presence interface across Sunday and suitable OSCAR surfaces.

The yellow face uses weighted joystick/puck motion and a designed expression language tied to real system state.

## ADR-025 — Documentation is part of every slice

**Decision:** each completed implementation slice updates:

- `README.md` status table
- relevant architecture/feature docs
- limitations and decisions
- next-slice marker

A slice is not complete while the repository still describes an older system state.
