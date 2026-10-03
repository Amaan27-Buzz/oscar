# System Architecture

## Overview

OSCAR is a distributed personal-intelligence system: one coherent intelligence spanning cloud coordination, phone, desktop machines, communications and physical Edge hardware. No ordinary user computer is assumed to be permanently available.

Two earlier projects inform the design without becoming runtime dependencies:

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
```

The availability topology is the **Connection Grid**:

```text
                         User
                          │
                       Sunday
              owner control / approvals
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Cloud           Desktop(s)        Edge
 rendezvous/state     high compute    local reflex/safety
          └───────────────┼────────────────┘
                          ▼
                OSCAR Connection Grid
```

No Grid member owns OSCAR's identity by itself.

## Canonical control/data flow

```text
User / Environment
       │
       ▼
Perception Fabric
       │
       ▼
World Model + current commitments / attention
       │
      Jev
       │
 ┌─────┼────────────────────────────────────┐
 │     │                                    │
Memory Live Context / Search          Model Reasoning
LRA    authoritative current sources   native Model Router
 │     │                                    │
 └─────┴──────────────┬─────────────────────┘
                      ▼
                OSCAR Executive
      Personal Policy • Persona • permissions
                      │
                      ▼
             Durable Execution Runtime
                      │
                      ▼
         Capability Catalog + Tool Search
                      │
           Workers / Skills / Protocols
                      │
                      ▼
               Connection Grid
       Sunday • Cloud • Desktop • Edge
                      │
                      ▼
      Apps / Channels / Devices / Specialists
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    Action Ledger          Artifact / Result
          └───────────┬───────────┘
                      ▼
                  Verification
                      │
      World Model / commitments / memory update
                      │
             evidence-backed report
```

Cross-cutting layers:

- Epistemic Integrity;
- permissions/safety;
- Personal Policy;
- Persona;
- canonical entity graph;
- audit/provenance;
- learning/evaluation;
- privacy/retention.

## 1. OSCAR Core

Core owns only responsibilities that must remain coherent across embodiments:

- identity/shared assistant state;
- active objectives/tasks/Workers/Protocols;
- permission and Personal Policy evaluation;
- Persona selection/context triggers;
- capability discovery requests;
- delegation/reroute decisions;
- event prioritization;
- verification strategy;
- memory/live-context requests;
- World Model access;
- Executive decisions;
- Action Ledger coordination;
- evidence/epistemic state.

Core must not become a mega-framework or assume every request requires an LLM.

## 2. World Model — what is true now

The World Model represents current state and is distinct from memory.

Entities/state may include:

- people/contacts/organizations;
- places/rooms/location;
- devices/nodes/sensors;
- apps/services/accounts;
- projects/repositories;
- tasks/Workers/Protocols;
- calendar events and commitments;
- flexible schedule blocks and deadlines;
- communication threads/events;
- media/activity/focus state where evidence supports it;
- physical objects where supported.

Every current-state claim should carry source, observed time, freshness/expiry, confidence/authority and provenance as appropriate. Stale evidence becomes stale/unknown rather than current truth.

## 3. Perception Fabric

Normalizes current evidence from:

- screen/accessibility/cursor/selection;
- screenshots/cameras;
- microphone/acoustic events;
- Voice Map;
- time/date/timezone;
- weather/current external context;
- calendar/free-busy/tasks/deadlines;
- notification events/content where authorized;
- phone location/activity/media state;
- calls/messages/email/meeting events;
- apps/devices;
- Edge sensors/presence;
- Worker/Protocol/task state.

Perception and retention are separate decisions. Observation of a notification/location/audio event does not itself create durable memory or authority to act.

## 4. Ambient Chief-of-Staff context

OSCAR should use current World Model evidence to coordinate the user's day, not just answer isolated prompts.

A commitment can represent a fixed event, flexible block, task/deadline, communication follow-up, Worker dependency or preparation/travel buffer.

Conceptual loop:

```text
current context + commitments
→ detect conflict / opportunity / risk
→ grade urgency + interruptibility
→ Personal Policy / permission
→ stay quiet / inform / suggest / act / interrupt
→ verify any mutation
→ update current state
```

The Executive may rearrange flexible work only when real capability and explicit policy allow it. It may never infer calendar-write or message-send authority merely because those sources are readable.

See [CHIEF-OF-STAFF.md](CHIEF-OF-STAFF.md).

## 5. Jev

TypeSafe Jev decides the class of action:

```text
known      → direct evidence sufficient
world      → current World Model
recall     → LRA/Supermemory
verify     → authoritative source/test
reason     → native Model Router
reported   → external testimony
specialist → Codex/computer-use/installed app/etc.
worker     → delegated Worker
unknown    → retrieve/ask instead of fabricate
```

Jev decides **whether** reasoning/retrieval/execution is needed. The Model Router decides **which** model/provider/credential only after a model path is chosen. Capability selection decides **which executor**.

## 6. Epistemic Integrity

Task/result states remain explicit:

```text
planned
executing
awaiting_result
result_received
verifying
verified
partially_verified
failed
blocked
cancelled
unknown
```

Evidence states remain distinct:

```text
KNOWN
INFERRED
RECALLED
REPORTED
VERIFIED
UNKNOWN
```

Another agent/tool/model saying `success` is evidence, not objective proof.

## 7. Memory — LRA + Supermemory

LRA provides persistent single-relationship/history architecture. Supermemory is the intended semantic/profile-style backend underneath it.

Memory may include episodic/project/device/procedural/profile/relationship context and provenance/confidence. Current authoritative state always outranks stale memory when current truth matters.

The current Club B reference implements a local backend boundary; a real Supermemory service remains partial until actually integrated and verified.

## 8. Live context and search

OSCAR federates current retrieval across files, mail, messages, calendar, browser, GitHub, knowledge systems, public web/search, Sunday, desktops, Edge and Worker state.

Authority is claim-specific, but a useful default is:

```text
live authoritative state
> current World Model observation
> structured OSCAR state
> recent episodic memory
> semantic/derived memory
> model prior
```

Freshness-sensitive information is retrieved rather than guessed from stale manifests/model priors. Tavily is one replaceable search adapter, not an architectural dependency.

## 9. Entity graph

One real-world entity should resolve consistently across contacts, mail, messaging identities, Voice Map, calendar, projects, repositories, tasks and devices only where evidence supports the mapping.

Same labels alone do not prove identity.

## 10. Personal Policy

```text
Memory          = what OSCAR remembers
Persona         = how OSCAR expresses itself
Personal Policy = how user wants OSCAR to behave
Permission      = what OSCAR may do
Protocol        = persistent autonomous responsibility
```

Personal Policy can govern interruption, schedule flexibility, communications, capture/retention, Worker autonomy and remote continuation within granted capability. Policy cannot grant a missing permission.

## 11. Persona

Persona may affect language, voice mode and motion amplitude. It never overrides truthfulness, safety, permission, consent or runtime state.

See [PERSONA.md](PERSONA.md).

## 12. Executive Planner

Coordinates multiple objectives and commitments using priority, deadline, dependencies, flexibility, resource/device availability, cost, risk and interruptibility.

It may schedule, parallelize, pause, pre-empt, reroute, defer and—where policy permits—replan flexible schedule/task blocks. It never bypasses Jev, permissions or Personal Policy.

## 13. Durable Execution Runtime

Long-running work carries durable task state, checkpoints, dependencies, leases/ownership, heartbeat, retry budget, cancellation, deadline, active execution surface, artifacts, verification and blockers.

Dead executors must not remain `working` forever. Ambiguous consequential work must not be blindly replayed.

## 14. Capability Catalog + Dynamic Tool Search

Capabilities expose lightweight searchable manifests with class, inputs/outputs, permissions/risk, surfaces, availability, latency/cost/reliability hints, undo metadata and provider/version.

Detailed contracts are loaded only for relevant finalists.

## 15. Native Model Router

Owns provider/model/credential routing with dynamic inventory, health/availability, latency/cost/quality, account-product/quota-pool state, fallback/circuit behavior, context/tool/vision/audio metadata and route history.

Models reason; they do not receive authority automatically.

## 16. Native Transport + Capability Fabric

OSCAR-owned secure typed transport provides node/session identity, pairing/scoped credentials, task/event/action/result transport, capability advertisement, correlation IDs, reconnect/backoff, progress, replay protection/idempotency, version negotiation, audit/provenance and outbound-first private-device rendezvous.

## 17. Connection Grid

### Sunday

Preferred owner-control/approval surface and strongest everyday Chief-of-Staff embodiment. Can inspect/pause/cancel/revoke authorized work and approve sensitive actions. Cannot bypass local hardware safety.

### Cloud coordinator

Replaceable rendezvous/durable coordination. May be free-tier, paid or BYOC.

### Desktop nodes

High-capability execution: coding agents, terminal, filesystem, browser, computer use, installed apps, GPU/local models and long-running work.

### Edge

Persistent local wake/Sentry signals, sensors/GPIO/actuators and deterministic safety/reflexes.

Availability can degrade through:

```text
FULL → CONNECTED → LOCAL → REFLEX_ONLY → OFFLINE
```

Remote continuation uses the same Durable Execution Runtime. Remote wake/power is exposed only when a real mechanism exists.

See [CONNECTION-GRID.md](CONNECTION-GRID.md).

## 18. Action Ledger + Undo

Consequential actions record initiator, intent, capability, permission/policy decision, target, execution state, verification state, evidence, reversibility/compensation and correlation ID.

Undo exists only when a real compensation is available.

## 19. Artifact / Result Model

Durable outputs include docs, media, code changes, deployments, meeting/call notes, Daily Journals, firmware builds, datasets/models/evaluations and other results. Artifacts carry provenance, ownership, location/version and verification state.

## 20. OSCAR Edge

### ESP32

Network/Edge transport, wake/VAD/audio front end where practical, local events, display/status, OTA/configuration, Pico communication and optional LAN helper capability such as Wake-on-LAN.

### RP2040/Pico

GPIO/sensors/buttons, relays/motors/actuators, deterministic timing and local interlocks/emergency behavior.

Local safety remains functional if cloud/Core/transport fails.

## 21. Sunday / Android

Sunday is OSCAR on the phone, not another assistant.

Target platform integration, where supported and explicitly granted:

- Android assistant role / voice-interaction contracts;
- optional OSCAR Orb application overlay;
- attention-aware overlay retreat/hide/reappearance;
- configurable home-screen widgets;
- notification-listener current context;
- legitimate notification `RemoteInput` replies;
- biometric/PIN owner approvals;
- Connection Grid supervision;
- calls/messages/email/meeting capability where legitimately available;
- Sentry/capture/privacy controls.

Android assistant, overlay, notification and microphone permissions remain separate. Notification visibility never implies unrestricted source-app access.

See [SUNDAY-DESIGN.md](SUNDAY-DESIGN.md) and [CHIEF-OF-STAFF.md](CHIEF-OF-STAFF.md).

## 22. Desktop Interaction Runtime

```text
Dictate → insert/clean speech into focused target
Edit    → transform selected/recent text
Ask     → answer about current context
Act     → operate current app/device/task
```

Desktop context may include app/window, focused control, selection, cursor target, accessibility tree, screenshots, clipboard fallback and active task state.

## 23. Universal Channel Gateway

Communication adapters normalize supported cellular/SMS, messaging, email, work channels, social DMs/replies and meetings while preserving each channel's real limits.

Integration order:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

## 24. Voice architecture

- **Voice Input** — wake, VAD, STT, barge-in, echo cancellation.
- **Voice Identity** — stable provider-independent VoiceProfile.
- **Voice Match** — authorization-oriented speaker evidence.
- **Voice Map** — perception-oriented speaker context; recognition never grants permission.
- **Self-voice suppression** — OSCAR TTS excluded from wake/Voice Map loops while preserving human barge-in.

## 25. Persistent Sentry + optional capture

Sentry remains aware when enabled through local acoustic, device, sensor, communication and presence signals.

```text
Sentry Aware
Listening
Muted
Acoustic Awareness Off
```

Persistent awareness does not automatically mean recording. Optional Context Capture / Daily Journal may retain selected calls/messages/mail/meetings/in-person conversations only where technically/legal/policy permitted.

Raw audio, transcript, summary and memory extraction are independent controls.

## 26. Learning

Verified successful paths may become candidate Skills/routines/Protocols only after parameterization, evaluation and permission review. One success is not enough to create a trusted default.

## 27. Self-maintenance

OSCAR monitors provider/auth health, Grid connectivity, capability staleness, task leases, Edge health, storage/state and repeated Worker failures. Safe bounded recovery may occur automatically; otherwise ask for minimum user intervention.

## Current implementation boundary

### Gate A

PASS for the current Brain foundation: Core Loop/Jev/reference Grid, adaptive model routing and real source-qualified search/freshness acceptance are verified for their documented scope.

### Gate B

PARTIAL. The merged reference foundation includes:

- Connector Fabric namespaced capabilities through existing Grid/Dispatcher contracts;
- transient task-owned private connector input;
- manifest/account/resource/executor-bound readback verification;
- POSIX reference machine Worker with files/Git/terminal and separate-process continuation;
- local selected memory, explicit structured Personal Policy and entity continuity.

The local Windows pass verifies native Worker execution, useful Codex work, independent behavioral/Git verification, actual coordinator/Worker OS-process restart and bounded owner-reviewed policy authoring. Still partial: browser/computer use, private account/OAuth flows, Supermemory and open-ended policy interpretation. See the local checkpoint below the preserved reference evidence.

See [CLUB-B-CHECKPOINT.md](CLUB-B-CHECKPOINT.md).

## Architecture invariants

1. One intelligence, many embodiments.
2. No ordinary desktop is the permanent host.
3. Sunday is owner control, not hardware-safety override.
4. Cloud is replaceable infrastructure.
5. Edge safety is local/deterministic.
6. Current World Model state is not memory.
7. Tool/model/Worker success is not verified completion.
8. Capability availability is discovered, not assumed.
9. Persona changes expression, never truth/authority.
10. Sentry awareness and recording are different permissions/modes.
11. Remote-control/power claims require real current capabilities.
12. Latch/SwitchRoute remain reference sources, not runtime dependencies.
13. Freshness-sensitive current facts use current authoritative evidence when reasonably available.
14. `CAN PERCEIVE`, `CAN RETAIN` and `CAN ACT` are independent boundaries.
15. Chief-of-Staff proactivity is attention-aware and policy-bounded.
16. Notification access never implies unrestricted access to the source app.
