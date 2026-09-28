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

**Reason:** networking/orchestration and hard real-time-ish GPIO/safety behavior have different constraints.

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

**Decision:** when a paired PC is available, OSCAR should delegate to the best execution environment: Codex for coding, computer use for GUIs/verification, Antigravity or other specialist software for suitable tasks, terminals/IDEs/browsers for direct operations.

**Reason:** OSCAR should orchestrate expertise rather than become a mediocre clone of every tool.

## ADR-010 — Capability advertisement

**Decision:** nodes advertise capabilities dynamically.

OSCAR should reason about `codex`, `computer-use`, `camera`, `relay`, `gpu`, `browser`, etc. rather than assuming a specific machine is always present.

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

## ADR-017 — Memory uses LRA/Supermemory

**Decision:** LRA is the long-term memory/retrieval layer with Supermemory as the planned backend.

**Reason:** OSCAR needs durable cross-device context without stuffing all prior information into every model call.

## ADR-018 — Jev is the fast decision/routing layer

**Decision:** TypeSafe Jev is planned for intent and epistemic routing: execute directly, retrieve memory, inspect another source/tool, invoke a model, delegate, or ask the user.

**Goal:** reduce unnecessary model/orchestration latency.

## ADR-019 — OSCAR can create reusable workflows safely

**Decision:** OSCAR may propose/generate protocols, routines and `SKILL.md`-style skills when useful.

**Constraint:** generated automation cannot grant itself new permissions. Expanded authority requires review/approval.

## ADR-020 — Avatar is functional UI

**Decision:** the blue-shell/yellow-face avatar is a major state/presence interface across Sunday and suitable OSCAR surfaces.

The yellow face uses weighted joystick/puck motion and a designed expression language tied to real system state.

## ADR-021 — Documentation is part of every slice

**Decision:** each completed implementation slice updates:

- `README.md` status table
- relevant architecture/feature docs
- limitations and decisions
- next-slice marker

A slice is not complete while the repository still describes an older system state.
