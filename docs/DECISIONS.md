# Architecture Decisions

This file records decisions that should remain stable unless explicitly revisited. Update it when a future slice changes one of these assumptions.

## ADR-001 — OSCAR is not hardware-only

**Decision:** OSCAR is the full personal-agent system spanning cloud intelligence, phone, computers, edge hardware, memory, tools and environment.

**Reason:** the target is a coherent JARVIS-like capability model, not a robot shell with a chatbot attached.

## ADR-002 — Sunday is OSCAR on the phone

**Decision:** Sunday is a mobile embodiment/surface of OSCAR, not a separate assistant.

**Implication:** identity, memory, task state, permissions and Protocols are shared through OSCAR.

## ADR-003 — Laptop independence

**Decision:** OSCAR must remain operational when the user's laptop/PC is off.

**Implication:** primary availability cannot depend on a desktop daemon or local LLM. PCs join as optional Worker nodes.

## ADR-004 — Cloud-first intelligence, edge-first presence

**Decision:** heavy reasoning uses cloud intelligence; low-power edge hardware owns always-on presence, sensors, reflexes and safety.

**Primary planned paths:**

- ChatGPT and other configured providers through OSCAR-owned provider/transport adapters;
- native OSCAR Model Router for provider/model selection;
- local deterministic logic on Edge.

Local PC models may exist only as optional support capabilities.

## ADR-005 — ESP32 and Pico have different jobs

**Decision:** ESP32 is the network/audio/event gateway; RP2040/Pico is the deterministic physical controller.

**Reason:** networking/orchestration and deterministic GPIO/safety behavior have different constraints.

## ADR-006 — Transport is native OSCAR infrastructure

**Decision:** OSCAR owns its secure Transport + Capability Fabric. The separate Latch project is reference/prototype material whose useful architecture/logic may be folded into OSCAR; it is not a required runtime dependency.

**Responsibilities:** bidirectional typed events/actions/results, node identity, pairing/scoped credentials, capability advertisement, correlation IDs, reconnect/backoff, progress callbacks, audit/provenance and secure outbound rendezvous for private devices.

**Implication:** embedded hardware uses a small native OSCAR Edge transport/client rather than depending on a separately deployed Latch service.

## ADR-007 — Bidirectional ChatGPT relationship

**Decision:** OSCAR should support both directions where product APIs permit:

```text
ChatGPT/provider surface → OSCAR-owned adapter → OSCAR
OSCAR → OSCAR-owned adapter → ChatGPT/provider surface
```

A provider-specific wake/trigger workaround stays behind the native transport/provider boundary so it can be replaced later without changing OSCAR Core.

## ADR-008 — Model routing is native OSCAR infrastructure

**Decision:** OSCAR owns model/provider routing. The separate SwitchRoute project is reference/prototype material whose useful architecture/logic may be folded into OSCAR; it is not a required runtime dependency.

**Responsibilities:** provider/model registry, task suitability, latency/cost/quality policy, health/availability, fallback chains, capability/context metadata and route telemetry.

**Implication:** ChatGPT is a first-class intelligence provider, not the only brain. Jev decides whether reasoning is needed; the native Model Router decides which allowed model/provider to use.

## ADR-009 — Use specialist software rather than reimplementing it

**Decision:** OSCAR delegates to the best execution environment: Codex for coding, computer use for GUIs/verification, installed or connected engineering tools for hardware/design/simulation, connected knowledge tools for their native workspaces, and other specialist software when suitable.

**Reason:** OSCAR should orchestrate expertise rather than become a mediocre clone of every tool.

## ADR-010 — Capability advertisement

**Decision:** nodes, apps, plugins and Workers advertise capabilities dynamically.

OSCAR should reason about capabilities such as `codex`, `computer-use`, `camera`, `relay`, `gpu`, `browser`, `cad`, `circuit-sim`, `device-provision`, plugins and other tools rather than assuming a specific machine or service is always present.

## ADR-011 — Voice and text share state

**Decision:** changing modality does not start a new assistant/session conceptually.

## ADR-012 — Reflex commands bypass LLMs

**Decision:** wake acknowledgement, mute, stop, cancel, emergency behavior and other deterministic reflexes must not wait on cloud-model reasoning.

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

## ADR-022 — Native desktop surfaces are part of OSCAR

**Decision:** OSCAR will have native/lightweight Windows and macOS surfaces for voice/text, context, approvals and presence.

**Implication:** desktop UI is an embodiment; the machine Worker is a capability node. Neither is the permanent host.

## ADR-023 — Hardware and engineering capabilities are tool-agnostic

**Decision:** OSCAR controls physical systems through native Edge/device capability contracts and delegates hardware design, CAD, circuit work, simulation, firmware, diagnostics and provisioning to whichever installed or connected specialist tools are actually available.

**Reason:** no dedicated hardware-workbench product should become an architectural dependency. Engineering tools are replaceable capabilities discovered through the same catalog as other software and devices.

**Implication:** devices should be provisionable as native OSCAR nodes with advertised capabilities regardless of which engineering tool was used to design or program them.

## ADR-024 — Avatar is functional UI

**Decision:** the blue-shell/yellow-face avatar is a major state/presence interface across Sunday and suitable OSCAR surfaces.

The yellow face uses weighted joystick/puck motion and a designed expression language tied to real system state.

## ADR-025 — Documentation is part of every slice

**Decision:** each completed implementation slice updates README status, relevant architecture/feature docs, limitations/decisions and the next-slice marker.

A slice is not complete while the repository still describes an older system state.

## ADR-026 — Quietly Alive is the OSCAR visual system

**Decision:** OSCAR uses the **Quietly Alive** design direction documented in `DESIGN.md` and `TASTE.md`.

## ADR-027 — Agent adapters stay thin; canonical context stays shared

**Decision:** `AGENTS.md` is the canonical repository-wide coding-agent instruction set. `DESIGN.md`, `TASTE.md` and domain docs hold detailed truth. Agent-specific files remain thin adapters.

## ADR-028 — Engineering favors simple, modular and evolvable code

**Decision:** `ENGINEERING.md` is the canonical engineering/system-design quality bar for OSCAR.

**Principles:** smallest coherent solution; high cohesion/low coupling; typed validated boundaries; explicit state ownership; bounded failure/retry behavior; dependency discipline; contract-focused tests; least privilege; measurement before optimization; small reversible changes.

## ADR-029 — Personal Policy is a first-class authoritative behavior layer

**Decision:** explicit user preferences are stored/evaluated as Personal Policy, distinct from semantic memory and permissions.

**Precedence:** safety/legal/platform constraints and permissions remain authoritative; explicit policy is evaluated before inferred preferences/defaults.

## ADR-030 — Communication is one OSCAR subsystem

**Decision:** calls, messaging, meetings, transcription, dictation and communication follow-up belong to a shared OSCAR communication layer.

**Integration order:** native OS/official API → official plugin/connector → authorized device app automation → computer-use/accessibility fallback → unsupported/ask.

## ADR-031 — Delegated Workers belong under OSCAR and use the real device mesh

**Decision:** OSCAR may create temporary or persistent sub-agents called Workers for scoped objectives/responsibilities.

**Execution model:** a Worker may use Sunday, desktop machine nodes, Codex, Computer Use, plugins/APIs, ChatGPT/native Model Router, installed/connected specialist applications or OSCAR Edge according to capability, policy and availability.

**Recovery:** Jev should allow safe self-repair/rerouting before unnecessary user escalation; retries remain bounded and authority never expands silently.

## ADR-032 — The World Model is the live shared state layer

**Decision:** OSCAR maintains a World Model representing current people, places, devices, apps, projects, tasks, objects and their relationships/state.

**Constraint:** current state carries freshness/provenance/confidence. Stale state becomes stale/unknown rather than current truth.

## ADR-033 — Perception feeds the World Model through a normalized fabric

**Decision:** screen/accessibility state, cursor/selection, camera observations, audio events, Voice Map events, phone/app events, location, sensors and task/Worker state enter OSCAR through a Perception Fabric.

**Constraint:** perception and retention are separate decisions.

## ADR-034 — OSCAR has an Executive Planner above Workers and Protocols

**Decision:** a global Executive Planner coordinates concurrent objectives using priority, deadlines, dependencies, resources, risk, cost, interruptibility and device availability.

## ADR-035 — Consequential actions use an Action Ledger; undo is capability-aware

**Decision:** consequential actions are recorded with intent, initiator, target, capability/tool/device, policy/permission decision, verification and reversal metadata where available.

**Constraint:** undo is best-effort. Irreversible operations are never represented as reversible.

## ADR-036 — Interaction Runtime uses Dictate / Edit / Ask / Act

**Decision:** desktop/mobile interaction converges on four user-facing modes: Dictate, Edit, Ask and Act, powered by focused app/window, selected text, cursor target, accessibility tree, screenshot/visual context and active task state.

## ADR-037 — Exactly one listening surface owns a voice turn

**Decision:** when Sunday, desktop and physical OSCAR hear the same wake/utterance, a multi-device arbitration layer chooses one owning surface.

**Inputs:** wake confidence, signal/proximity, active-device context, presence/user interaction and explicit priority.

## ADR-038 — Live source retrieval is federated and authority-aware

**Decision:** Jev can query a universal live context/search fabric across connected authoritative sources instead of hard-coding every connector into the reasoning path.

## ADR-039 — OSCAR can be taught workflows by demonstration

**Decision:** where capabilities allow it, the user can deliberately teach a workflow by demonstrating it once; OSCAR infers a Skill candidate, asks about ambiguity, verifies and versions the result.

**Constraint:** observed behavior never creates new authority.

## ADR-040 — OSCAR monitors and repairs its own operational health

**Decision:** OSCAR treats expired auth, broken adapters/connectors, stale/disappeared capabilities, provider degradation, Edge disconnects, update failure, storage pressure and repeated Worker failures as first-class health state.

**Constraint:** automatic repair/rollback occurs only when safe, bounded and authorized.

## ADR-041 — Epistemic Integrity is a core invariant

**Decision:** OSCAR distinguishes direct knowledge, inference, recalled memory, external reports, verified evidence and unknown state. Completion claims cannot exceed available verification evidence.

**Implications:** reported success is not automatically verified; partial verification is reported as partial; unknown is valid; OSCAR can disagree when evidence/constraints require it; corrections are explicit.

See `docs/EPISTEMIC-INTEGRITY.md`.

## ADR-042 — Communication adapters share a Universal Channel Gateway

**Decision:** supported messaging/email/social channels map into one normalized inbound/outbound event/action abstraction while preserving channel-specific capabilities.

## ADR-043 — Long-running work uses a Durable Execution Runtime

**Decision:** tasks that must survive process/device/executor loss use durable state with checkpoints, leases/ownership, heartbeats, bounded retry, cancellation, reclaim and restart/resume semantics.

## ADR-044 — Capability discovery scales through a searchable catalog

**Decision:** capabilities expose lightweight searchable manifests; detailed tool/Skill/plugin contracts are progressively loaded only for a relevant candidate set.

## ADR-045 — Learned automation is evaluated before trusted promotion

**Decision:** a successful exploratory execution can create a candidate Skill/routine/Protocol, but trusted/default promotion requires evaluation where possible, safety/permission review, comparison and rollback support.

## ADR-046 — Finished outputs use a first-class Artifact / Result Model

**Decision:** durable outputs such as documents, code changes, research, media, deployments, meeting notes and firmware builds can be represented as typed artifacts with provenance, version/location, ownership and verification state.

## ADR-047 — Device mesh is primary; cloud Worker computers are optional capabilities

**Decision:** OSCAR's execution foundation remains the user's actual device/service mesh. A future cloud Worker node may be added as another advertised capability, not as a permanent architectural dependency.

## ADR-048 — Latch and SwitchRoute are references, not required products

**Decision:** OSCAR may reuse proven ideas/code from Amaan's Latch and SwitchRoute projects, but the final transport/capability and model-routing subsystems are native OSCAR modules.

**Reason:** both projects are still evolving, and the useful architecture is already understood. Requiring separate deployed products would introduce artificial coupling and a false availability dependency.

**Constraint:** do not preserve a service boundary merely because a prototype had one. Reuse only what still fits OSCAR's contracts and tests.

See `docs/NATIVE-INFRASTRUCTURE.md`.

## ADR-049 — Voice Map and Voice Match are different systems

**Decision:** Voice Match is authorization-oriented speaker verification; Voice Map is perception-oriented speaker recognition/context.

**Reason:** `I think this is person X` and `person X is authorized to perform action Y` are different claims.

**Rules:**

- Voice Map recognition never grants permission;
- unknown speakers remain unknown instead of guessed;
- canonical-person linkage requires sufficient evidence/confirmation;
- voice profiles/embeddings are sensitive and retention-controlled;
- speaker confidence remains explicit.

## ADR-050 — OSCAR owns a stable Voice Identity

**Decision:** OSCAR's synthesized voice is a provider-independent product identity represented by a `VoiceProfile`, not whatever default voice a TTS provider happens to expose.

**VoiceProfile includes where supported:** voice/model reference, prosody/modulation, rate/rhythm, pronunciation controls, contextual speaking modes, fallback mapping and version.

**Constraint:** provider fallbacks should preserve identity as closely as possible and report material degradation rather than silently becoming a different voice.

## ADR-051 — Sentry includes local always-on acoustic awareness

**Decision:** when enabled, Sentry's local perception plane continuously supports low-cost acoustic signals such as wake word, VAD/speech presence, Voice Map known/unknown speaker events, speaker changes/multiple speakers, configured sound-event classes and barge-in.

**Privacy rule:** always-on acoustic awareness does not imply continuous cloud transcription or raw-audio retention. Speech presence, speaker identity, transcription and retention are separate policy/permission decisions.

**Self-voice rule:** OSCAR's own TTS must be tagged/suppressed so it does not trigger itself or pollute Voice Map. Self-voice suppression must still allow human barge-in.

## ADR-052 — Model routing, capability selection and Jev are separate decisions

**Decision:** OSCAR keeps three boundaries distinct:

```text
Jev                  → what class of action is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

**Reason:** model-provider keys, local runtimes, coding agents, terminal/computer-use and installed applications have different execution semantics and should not be flattened into one generic provider list.

**Implication:** coding agents such as Codex, Claude Code and OpenCode are discovered/selected as capabilities. The native Model Router is used only after a model-reasoning path is selected.

See `docs/MODEL-ROUTING.md`.

## ADR-053 — Providers may use independent credential pools

**Decision:** a single provider may own multiple credential slots, each with independent validity, health, rate/quota/capacity, cooldown, usage and observed latency state where measurable.

**Rules:**

- raw credentials never appear in UI/telemetry/logs;
- stable masked slot IDs are used for diagnostics;
- one failing credential does not automatically disable the whole provider;
- unknown quota is not unlimited;
- unknown price is not free;
- automatic routing and explicit manual provider/model selection both remain available.

The initial local development pool is defined by `.env.example`; the real `.env` remains local-only.

## ADR-054 — Build Gates are manual acceptance milestones above slices

**Decision:** detailed roadmap slices remain the unit of implementation, while five Build Gates group them for explicit manual end-to-end verification:

```text
Gate A — Brain          Slices 01–04
Gate B — Can Do Work    Slices 05–06
Gate C — Embodied OSCAR Slices 07–10
Gate D — JARVIS Layer   Slices 11–14
Gate E — Unified Alpha  Slices 15–17
```

**Reason:** OSCAR is being built rapidly, but fast iteration must still stop at meaningful integration points where real combined behavior is tested manually.

**Constraint:** a 2–3 day developer-alpha target does not weaken slice exit conditions, safety boundaries or epistemic-integrity rules. Partial work remains partial.

See `docs/BUILD-GATES.md`.

## ADR-055 — Connection Grid is OSCAR's availability and remote-control fabric

**Decision:** Sunday, replaceable cloud coordination, desktop nodes and OSCAR Edge form one Connection Grid over OSCAR-owned transport/capability contracts.

**Roles:** Sunday is the preferred everyday owner-control/approval surface; cloud provides portable rendezvous/durable coordination; desktops provide high-capability execution; Edge provides local perception/reflex/safety.

**Constraint:** no Grid node is unrestricted merely because it is connected. Capability scope and permission are rechecked at the authoritative target.

**Availability rule:** ordinary node loss degrades capabilities explicitly rather than making one hidden desktop/cloud process the permanent host.

See `docs/CONNECTION-GRID.md`.

## ADR-056 — Remote continuation and machine power actions require durable state and real capabilities

**Decision:** long-running desktop work can continue while the user leaves and can be supervised from Sunday/cloud through the Durable Execution Runtime and Connection Grid.

**Rules:**

- progress/control uses durable task IDs, checkpoints and leases;
- executor disappearance becomes waiting/blocked/reclaimable, never false completion;
- sleep/shutdown is offered only when the online machine exposes a permitted capability;
- remote wake is offered only when Wake-on-LAN or another approved real power-management path exists;
- Sunday can pause/cancel/revoke user-authorized work but cannot override deterministic hardware safety.

## ADR-057 — Sentry is persistent awareness; continuity capture is an explicit separate layer

**Decision:** Sentry is persistently aware when enabled, but awareness, conversational Listening and durable recording/capture are separate states/capabilities.

OSCAR may offer explicit `Context Capture` and `Daily Journal` modes for selected calls/messages/email/meetings/in-person conversations where technically and legally available.

**Privacy rules:**

- capture is source-specific and permission/consent-aware;
- unsupported call/app capture remains unsupported;
- raw audio, transcript, summary and memory extraction have independent retention controls;
- capture can be paused/deleted/excluded by source/person/place/time;
- the product is not designed around covert recording.

## ADR-058 — Persona is configurable presentation, not truth or authority

**Decision:** OSCAR exposes a user-configurable PersonaProfile for traits such as humor, candor, warmth, formality, brevity, playfulness, initiative and pushback, with context triggers.

**Constraint:** Persona cannot reduce Epistemic Integrity, change permissions, bypass confirmation/consent or make failure/blocked state look successful.

**Boundary:**

```text
Persona         = how OSCAR expresses itself
Personal Policy = how user wants OSCAR to behave
Permission      = what OSCAR is allowed to do
Memory          = what OSCAR retains/recalls
```

See `docs/PERSONA.md`.

## ADR-059 — Club A uses a small native Python/SQLite foundation

**Problem:** Slice 00 had product contracts but no runtime. Club A needs real durable execution, independent verification, authenticated reference transport and adaptable routing without a distributed stack.

**Decision:** use Python 3.12 standard-library dataclasses/enums, SQLite transactions and bounded HTTP adapters. Keep Jev, capability discovery/dispatch, model routing, verification and durable state as distinct responsibilities. Use an explicit POSIX filesystem scope for the representative proof. Provider/model inventory is versioned JSON data; credentials remain opaque environment-backed runtime material.

**Trade-offs:** no runtime dependency graph or external service is needed. The reference node shares the coordinator store and binds only to loopback; this proves protocol/state contracts but is not an Internet coordinator or physical-device integration. Pairing is a trusted coordinator API, not remote self-enrollment. SQLite is single-authority storage, not a replication scheme. Windows/mobile/Edge execution and a public TLS/outbound rendezvous adapter remain later or partial work.

**Failure/recovery:** provider failure and credential failure have distinct bounded fallback semantics. Streaming never splices a second generation after meaningful output. Dead node leases produce blocked/reclaimable tasks, not completion. Started action records with unknown crash outcomes prevent automatic replay. File artifacts receive the hash from the same independent verification read; reported results remain reported even when independent evidence verifies the objective.

**Evolution:** preserve version-1 wire contracts; a breaking protocol/storage change needs an explicit migration. The development manifest is replaceable and does not define OSCAR’s permanent provider/model boundary. Initial model quality/limits are configuration with provenance, not verified benchmarks. The initial Gate A foundation review passed; the post-Gate-A correction explicitly downgrades current live acceptance to PARTIAL, as recorded in [CLUB-A-CHECKPOINT.md](CLUB-A-CHECKPOINT.md). The 2026-10-02 review criteria accept the reference Transport/Grid stage and defer public-coordinator deployment acceptance to later Grid integration. Public TLS/outbound rendezvous and embodied nodes remain unverified. No Slice 05 work is included.

## ADR-060 — Current provider facts require scoped discovery and live evidence

**Problem:** retired model IDs made earlier access failures insufficient to diagnose
credential health. Multiple keys also do not establish independent quota capacity.

**Decision:** treat manifests as sourced bootstrap/retirement seeds; require fresh
hosted inventories, per-credential availability/pricing/limits and separate bounded
generation observations. Group credentials by account product/quota pool with
conservative unknown topology. Jev routes freshness-sensitive requests through a
provider-agnostic live-source capability before reasoning; missing evidence remains
UNKNOWN. Sources retain authority, time, scope, TTL and contradictions.

**Limits:** public support/listing/generation/funding are separate claims. Search
ranking is not verification. Native inventory retrieval and the bounded Tavily
adapter are implemented; actual Tavily and combined public-web acceptance remain
UNVERIFIED because keys are absent. Failed
live runs and superseded provider-health interpretations are preserved explicitly.
Detailed contracts are owned by [MODEL-ROUTING.md](MODEL-ROUTING.md) and
[SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md).

## ADR-061 — Connector, Worker and continuity foundations extend native contracts

**Problem:** Club B needs useful machine/service work and persistent continuity
without competing execution registries or promoting testimony into truth.

**Decision:** connectors supply existing Grid capabilities; machine executors use
existing Dispatcher/Actions/leases/dedup/Runtime/Verifier. Private connector bodies
stay in transient referenced context. Local LRA, explicit Personal Policy and small
evidence-bound entity records use existing SQLite. Structured Jev capability
intents contain no hard-coded provider selection.

**Trade-offs:** the reference uses separate processes and real loopback HTTP with
shared SQLite, not independent network stores/public deployment. Subprocess scope
is explicitly opted-in trusted host authority, not an OS sandbox. Local memory is
bounded lexical retrieval behind a semantic-backend contract. Auth enrollment,
Windows, natural-language policy and Supermemory service remain unverified.

**Recovery/privacy:** completed lost results deduplicate; started uncertain effects
block replay. Verification requires independent correlated state. Retrieved memory
stays RECALLED; fresh API testimony can outrank stale memory without becoming
VERIFIED. Retention/deletion applies to live records, not a claim of secure erasure.
No destructive migration is needed; these are additive version-1 records and
controls. Rollback removes new composition paths, leaving historical task evidence.
