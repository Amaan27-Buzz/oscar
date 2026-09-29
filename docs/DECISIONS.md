# Architecture Decisions

This file records decisions that should remain stable unless explicitly revisited. Update it when a future slice changes one of these assumptions.

## ADR-001 — OSCAR is not hardware-only

**Decision:** OSCAR is the full personal-agent system spanning cloud intelligence, phone, computers, edge hardware, memory, tools and environment.

**Reason:** the target is a coherent JARVIS-like capability model, not a robot shell with a chatbot attached.

## ADR-002 — Sunday is OSCAR on the phone

**Decision:** Sunday is a mobile embodiment/surface of OSCAR, not a separate assistant.

**Implication:** identity, memory, task state, permissions and Protocols should be shared through OSCAR rather than duplicated into a separate mobile intelligence.

## ADR-003 — Laptop independence

**Decision:** OSCAR must remain operational when the user's laptop/PC is off.

**Implication:** primary availability cannot depend on a desktop daemon or local LLM. PCs join as optional Worker nodes.

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

**Decision:** Latch is the secure integration layer between ChatGPT/cloud coordination and OSCAR devices/Workers.

Embedded hardware should use a minimal Latch Edge protocol with outbound connections rather than exposing home-network endpoints publicly.

## ADR-007 — Bidirectional ChatGPT relationship

**Decision:** both directions are required:

```text
ChatGPT → Latch → OSCAR
OSCAR → Latch → ChatGPT
```

OSCAR → ChatGPT may initially require an indirect trigger/wake mechanism. The workaround must live behind a Latch abstraction so it can be replaced by a direct trigger later.

## ADR-008 — SwitchRoute handles general autonomous model routing

**Decision:** OSCAR can use SwitchRoute independently of ChatGPT for autonomous cloud reasoning, classification, extraction and fallbacks.

**Implication:** ChatGPT is a first-class brain, not the only brain.

## ADR-009 — Use specialist software rather than reimplementing it

**Decision:** OSCAR delegates to the best execution environment: Codex for coding, computer use for GUIs/verification, Kinetable for hardware engineering, connected knowledge tools for their native workspaces, and other specialist software when suitable.

**Reason:** OSCAR should orchestrate expertise rather than become a mediocre clone of every tool.

## ADR-010 — Capability advertisement

**Decision:** nodes, apps, plugins and Workers advertise capabilities dynamically.

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

**Decision:** successful novel executions can be distilled into procedural memory and reusable Skills.

**Goal:** repeated tasks become faster, cheaper and more deterministic over time.

## ADR-020 — OSCAR can create reusable workflows safely

**Decision:** OSCAR may create/propose/refine Protocols, routines and ecosystem-compatible `SKILL.md`-style Skills.

**Constraint:** generated automation cannot grant itself new permissions. Expanded authority requires review/approval.

## ADR-021 — Protocols are stateful responsibilities, not just schedules

**Decision:** OSCAR Protocols may wait, observe, branch, delegate, retry, verify and escalate over long periods.

**Reason:** the target is persistent delegated responsibility, not a glorified cron/reminder system.

## ADR-022 — Native desktop surfaces are part of OSCAR

**Decision:** OSCAR will have native/lightweight Windows and macOS surfaces for voice/text, context, approvals and presence.

**Implication:** desktop UI is an embodiment; the machine Worker is a capability node. Neither is the permanent host.

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

## ADR-026 — Quietly Alive is the OSCAR visual system

**Decision:** OSCAR uses the **Quietly Alive** design direction documented in `DESIGN.md` and `TASTE.md`.

**Principles:** restrained/native product clarity, tactile industrial character, friendly expressive feedback and functional honesty. OSCAR's blue-shell/yellow-face avatar is the visual anchor; personality comes from real state, motion and timing rather than generic AI decoration.

**Constraint:** system-wide visual changes update the canonical design files rather than drifting independently across Sunday, desktop and physical surfaces.

## ADR-027 — Agent adapters stay thin; canonical context stays shared

**Decision:** `AGENTS.md` is the canonical repository-wide coding-agent instruction set. `DESIGN.md`, `TASTE.md` and domain docs hold detailed truth. `CLAUDE.md`, `GEMINI.md`, GitHub Copilot instructions and Cursor rules are thin adapters that point back to canonical context.

**Reason:** duplicating large instruction sets across agents creates stale/conflicting project truth and wastes context.

**Implication:** reusable workflows belong in focused `SKILL.md` packages rather than continuously expanding `AGENTS.md`.

## ADR-028 — Engineering favors simple, modular and evolvable code

**Decision:** `ENGINEERING.md` is the canonical engineering/system-design quality bar for OSCAR.

**Principles:** prefer the smallest coherent solution; high cohesion and low coupling; typed and validated boundaries; explicit state ownership; bounded failure/retry behavior; dependency discipline; contract-focused tests; least privilege; measurement before optimization; small reviewable changes.

**Reason:** OSCAR spans firmware, mobile, desktop, cloud and agent runtimes. Durability comes from clear responsibilities and stable contracts, not speculative complexity.

**Constraint:** abstraction, services, extension points and dependencies must solve a current concrete problem. “Future-proofing” that makes today's code harder to understand is not accepted by default.

**Implication:** provider/platform details should be isolated when OSCAR requires a stable internal contract, while shared abstractions should represent proven shared behavior rather than accidental syntactic similarity.

## ADR-029 — Personal Policy is a first-class authoritative behavior layer

**Decision:** explicit user preferences are stored/evaluated as Personal Policy, distinct from semantic memory and distinct from permissions.

**Reason:** OSCAR must support arbitrary natural-language preferences such as call handling, interruption behavior, communication privacy, Worker autonomy and app/project-specific rules without forcing everything into generic settings or unreliable prompt memory.

**Precedence:** safety/legal/platform constraints and permissions remain authoritative; explicit policy is evaluated before inferred preferences/defaults.

**Implication:** LRA/Supermemory may suggest likely preferences from repeated behavior, but consequential inferred patterns do not silently become policy. The user can create, inspect, edit and remove Personal Policy by voice/chat or UI.

## ADR-030 — Communication is one OSCAR subsystem

**Decision:** calls, messaging, meetings, transcription, dictation and communication follow-up belong to a shared OSCAR communication layer.

**Integration order:** native OS/official API → official plugin/connector → authorized device app automation → computer-use/accessibility fallback → unsupported/ask.

**Reason:** the user should not need separate assistant identities for calls, meeting notes, dictation and follow-ups; all should use the same memory, schedule, Personal Policy and task context.

**Constraint:** OSCAR must not claim or emulate capabilities that a phone/app/platform does not actually expose. Communication autonomy remains permission-scoped and attributable.

## ADR-031 — Delegated Workers belong under OSCAR and use the real device mesh

**Decision:** OSCAR may create temporary or persistent sub-agents called Workers for scoped objectives/responsibilities.

**Reason:** persistent teammate-style delegation is useful, but each Worker should not require a separate cloud computer or become another assistant silo.

**Execution model:** a Worker may use Sunday, desktop machine nodes, Codex, Computer Use, plugins/APIs, ChatGPT/SwitchRoute, Kinetable or OSCAR Edge according to capability, policy and availability.

**Recovery:** Jev should allow safe self-repair/rerouting before unnecessary user escalation; retries remain bounded and authority never expands silently.

**Implication:** Workers can collaborate, use Skills and participate in Protocols, while OSCAR remains the top-level coordinator and Personal Policy/permissions remain authoritative.

## ADR-032 — The World Model is the live shared state layer

**Decision:** OSCAR maintains a World Model representing current people, places, devices, apps, projects, tasks, objects and their relationships/state.

**Reason:** JARVIS-like behavior requires one coherent situation model rather than independent facts scattered across memory, devices and connectors.

**Constraint:** current state must carry freshness/provenance/confidence. Stale state is marked stale/unknown rather than presented as current truth.

**Implication:** LRA/Supermemory remains historical/semantic continuity; the World Model is current state.

## ADR-033 — Perception feeds the World Model through a normalized fabric

**Decision:** screen/accessibility state, cursor/selection, camera observations, audio events, phone/app events, location, sensors and task/Worker state enter OSCAR through a Perception Fabric.

**Reason:** each surface should not invent a separate perception model. Multimodal evidence needs one normalized path into current state.

**Constraint:** perception/retention are separate decisions. Observing something does not automatically make it durable memory.

## ADR-034 — OSCAR has an Executive Planner above Workers and Protocols

**Decision:** a global Executive Planner coordinates concurrent objectives using priority, deadlines, dependencies, resources, risk, cost, interruptibility and device availability.

**Reason:** the user should not become the human project manager for a collection of agents.

**Implication:** the Executive Planner may schedule, parallelize, pause, pre-empt or reroute work, but cannot bypass Personal Policy, permissions or Jev.

## ADR-035 — Consequential actions use an Action Ledger; undo is capability-aware

**Decision:** consequential actions are recorded with intent, initiator, target, tool/device, policy/permission decision, verification and reversal metadata where available.

**Reason:** OSCAR should be able to answer “what did you change?”, “why?” and “undo that” truthfully.

**Constraint:** undo is best-effort. Irreversible operations are never represented as reversible. A compensating action is used only when the underlying capability actually supports a safe compensation.

## ADR-036 — Interaction Runtime uses Dictate / Edit / Ask / Act

**Decision:** desktop/mobile interaction converges on four user-facing modes: Dictate, Edit, Ask and Act, powered by focused app/window, selected text, cursor target, accessibility tree, screenshot/visual context and active task state.

**Reason:** OSCAR must at least match the practical VoiceOS-style “point at something and talk about it” interaction baseline.

**Implication:** system-wide dictation, selected-text editing and point-and-talk are core interaction architecture, not isolated features.

## ADR-037 — Exactly one listening surface owns a voice turn

**Decision:** when Sunday, desktop and physical OSCAR hear the same wake/utterance, a multi-device arbitration layer chooses one owning surface.

**Inputs:** wake confidence, signal/proximity, active-device context, presence/user interaction and explicit priority.

**Reason:** omnipresence should feel like one assistant, not several speakers responding at once.

## ADR-038 — Live source retrieval is federated and authority-aware

**Decision:** Jev can query a universal live context/search fabric across connected authoritative sources instead of hard-coding every connector into the reasoning path.

**Reason:** memory alone cannot answer current-state questions reliably.

**Implication:** current authoritative sources outrank stale memory; source provenance is preserved.

## ADR-039 — OSCAR can be taught workflows by demonstration

**Decision:** where device/platform capabilities allow it, the user can deliberately teach a workflow by demonstrating it once; OSCAR infers a Skill candidate, asks about ambiguity, verifies and versions the result.

**Reason:** this extends OSCAR to apps and workflows that lack strong APIs without requiring the user to hand-author automation.

**Constraint:** observed behavior never creates new authority. The resulting Skill remains permission-scoped and inspectable.

## ADR-040 — OSCAR monitors and repairs its own operational health

**Decision:** OSCAR treats expired auth, broken connectors, stale/disappeared capabilities, provider degradation, Edge disconnects, update failure, storage pressure and repeated Worker failures as first-class health state.

**Reason:** an always-present assistant cannot depend on the user manually noticing every infrastructure failure.

**Constraint:** automatic repair/rollback occurs only when safe, bounded and authorized; otherwise OSCAR asks for the minimum intervention needed.

## ADR-041 — Epistemic Integrity is a core invariant

**Decision:** OSCAR distinguishes direct knowledge, inference, recalled memory, external reports, verified evidence and unknown state. Completion claims cannot exceed available verification evidence.

**Reason:** intention, execution, tool success, Worker testimony, observation and verification are different states. Collapsing them causes false success claims and yes-man behavior.

**Implications:**

- `reported success` is not automatically `verified`;
- unqualified `Done`/`Fixed` requires verification where technically possible;
- partial verification is reported as partial;
- unknown is a valid state;
- OSCAR can disagree with the user when evidence/constraints require it;
- corrections are explicit and propagated.

See `docs/EPISTEMIC-INTEGRITY.md`.

## ADR-042 — Communication adapters share a Universal Channel Gateway

**Decision:** supported messaging/email/social channels map into one normalized inbound/outbound event/action abstraction while preserving channel-specific capabilities.

**Reason:** OSCAR should not require bespoke orchestration logic for every new communication surface.

**Constraint:** normalization must never imply unsupported parity. An adapter advertises exactly what that channel/account/surface can do.

## ADR-043 — Long-running work uses a Durable Execution Runtime

**Decision:** tasks that must survive process/device/executor loss use durable state with checkpoints, leases/ownership, heartbeats, bounded retry, cancellation, reclaim and restart/resume semantics.

**Reason:** persistent Workers/Protocols cannot be reliable if `working` exists only in process memory.

**Constraint:** the runtime owns execution mechanics; the Executive Planner owns priority/objective decisions and Workers own objective-specific reasoning.

## ADR-044 — Capability discovery scales through a searchable catalog

**Decision:** capabilities expose lightweight searchable manifests; detailed tool/Skill/plugin contracts are progressively loaded only for a relevant candidate set.

**Reason:** OSCAR may eventually have hundreds/thousands of capabilities. Loading all definitions into every model context is wasteful and brittle.

**Constraint:** search/ranking never bypasses permissions, Personal Policy or availability checks.

## ADR-045 — Learned automation is evaluated before trusted promotion

**Decision:** a successful exploratory execution can create a candidate Skill/routine/Protocol, but trusted/default promotion requires replay/evaluation where possible, safety/permission review, comparison with the current version and rollback support.

**Reason:** one success does not prove a generalized workflow is reliable.

**Constraint:** untestable candidates remain experimental/partially verified rather than silently becoming authoritative defaults.

## ADR-046 — Finished outputs use a first-class Artifact / Result Model

**Decision:** durable outputs such as documents, code changes, research, media, deployments, meeting notes and firmware builds can be represented as typed artifacts with provenance, version/location, ownership and verification state.

**Reason:** Workers and Protocols need to hand off durable results without burying them in chat text or copying opaque blobs repeatedly.

**Implication:** artifacts can be linked to projects/entities/tasks and reused by later Workers while preserving source and verification metadata.

## ADR-047 — Device mesh is primary; cloud Worker computers are optional capabilities

**Decision:** OSCAR's execution foundation remains the user's actual device/service mesh. A future cloud Worker node may be added as another advertised capability, not as a permanent architectural dependency.

**Reason:** OSCAR's identity is persistent intelligence spanning the user's real phone, computers, edge hardware and services rather than one cloud desktop per agent.

**Implication:** when a real device is offline, its capabilities disappear; OSCAR reroutes only through equivalent authorized capabilities and remains truthful about what is unavailable.
