# System Architecture

## Overview

OSCAR is a distributed personal-intelligence system. No single ordinary user computer is assumed to be permanently available.

The target is **one coherent ambient intelligence** spanning cloud coordination, phone, desktop machines, communications and physical Edge hardware.

Two earlier projects inform the design without becoming runtime dependencies:

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
```

The final availability topology is the **Connection Grid**:

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
World Model
       │
      Jev
       │
 ┌─────┼──────────────────────────────┐
 │     │                              │
Memory Live Context             Model Reasoning
LRA    authoritative sources    native Model Router
 │     │                              │
 └─────┴─────────────┬────────────────┘
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
        World Model / Memory update
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

The core owns only responsibilities that must remain coherent across embodiments:

- identity/shared assistant state;
- active objectives/tasks/Workers/Protocols;
- permissions and Personal Policy evaluation;
- Persona selection/context triggers;
- capability discovery requests;
- delegation/reroute decisions;
- event prioritization;
- verification strategy;
- memory/live-context requests;
- World Model access;
- Executive Planner decisions;
- Action Ledger coordination;
- evidence/epistemic state.

The core must not become a mega-framework or assume every request needs an LLM.

## 2. World Model

The World Model represents **what is true now**.

It is distinct from memory.

Entities may include people, places, devices, sensors, apps, accounts, projects, repositories, tasks, Workers, Protocols and physical objects.

State should carry source, observed time, freshness/expiry, confidence and provenance.

Stale evidence becomes stale/unknown rather than current truth.

## 3. Perception Fabric

Normalizes current evidence from:

- screen/accessibility/cursor/selection;
- screenshots/cameras;
- microphone/acoustic events;
- Voice Map;
- communication events;
- phone location/activity;
- apps/devices;
- Edge sensors/presence;
- Worker/Protocol/task state.

Perception and retention are separate decisions.

## 4. Jev

TypeSafe Jev decides the class of action.

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

Jev decides **whether** reasoning is needed. The Model Router decides **which** model/provider/credential. Capability selection decides **which executor**.

## 5. Epistemic Integrity

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

## 6. Memory — LRA + Supermemory

LRA provides the persistent single-relationship/history architecture. Supermemory supplies semantic/profile-style memory underneath.

Memory includes episodic/project/device/procedural/profile/relationship context and provenance/confidence.

Live authoritative state outranks stale memory when current truth matters.

## 7. Live context/search

OSCAR federates current-source retrieval across files, mail, messages, calendar, browser, GitHub, knowledge systems, social accounts, Sunday, desktops, Edge and Worker state.

Conceptual authority:

```text
live authoritative state
> current World Model observation
> structured OSCAR state
> recent episodic memory
> semantic/derived memory
> model prior
```

## 8. Entity graph

One real-world entity should resolve consistently across contacts, mail, messaging identities, Voice Map, calendar, projects, repositories, tasks and devices where evidence supports it.

## 9. Personal Policy

Personal Policy is authoritative user behavior preference, distinct from memory, Persona and permissions.

```text
Memory          = what OSCAR remembers
Persona         = how OSCAR expresses itself
Personal Policy = how user wants OSCAR to behave
Permission      = what OSCAR may do
Protocol        = persistent autonomous responsibility
```

## 10. Persona

Persona is a configurable interaction layer.

Possible traits include humor, candor, warmth, formality, brevity, playfulness, initiative and pushback, plus context triggers.

Persona may affect language, voice mode and motion amplitude. It never overrides truthfulness, safety, permission, consent or runtime state.

See [PERSONA.md](PERSONA.md).

## 11. Executive Planner

Coordinates multiple objectives using priority, deadline, dependencies, resource/device availability, cost, risk and interruptibility.

It can schedule/parallelize/pause/pre-empt/reroute/defer but never bypass Jev, permissions or Personal Policy.

## 12. Durable Execution Runtime

Long-running work carries durable task state, checkpoints, dependencies, leases/ownership, heartbeat, retry budget, cancellation, deadline, active execution surface, artifacts, verification and blockers.

Dead executors must not remain `working` forever.

## 13. Capability Catalog + Dynamic Tool Search

Capabilities expose lightweight searchable manifests with class, inputs/outputs, permissions/risk, supported surfaces, availability, latency/cost/reliability hints, undo metadata and provider/version.

Detailed contracts are loaded progressively only for relevant candidates.

## 14. Native Model Router

OSCAR owns provider/model/credential routing.

Responsibilities:

- provider/model registry;
- task affinity;
- health/availability;
- latency/cost/quality;
- independent credential pools;
- fallback/circuit behavior;
- context/tool/vision/audio metadata;
- route/outcome history;
- manual + automatic modes;
- graceful degradation.

Models reason; they do not receive authority automatically.

## 15. Native Transport + Capability Fabric

OSCAR-owned secure typed transport provides:

- node/session identity;
- pairing/scoped credentials;
- task/event/action/result transport;
- capability advertisement;
- correlation IDs;
- reconnect/backoff;
- progress callbacks;
- replay protection/idempotency;
- version negotiation;
- audit/provenance;
- outbound-first private-device rendezvous.

## 16. Connection Grid

The Connection Grid uses native transport to keep OSCAR available across nodes.

### Sunday

Preferred owner control/approval surface. Can inspect/pause/cancel/revoke authorized work and approve sensitive actions. Cannot bypass local hardware safety.

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

Remote continuation uses the same Durable Execution Runtime: the user can leave a desktop task running, supervise it from Sunday and optionally sleep/shut down the machine after verified completion if a real capability exists.

Remote wake is exposed only when a real Wake-on-LAN/management path exists.

See [CONNECTION-GRID.md](CONNECTION-GRID.md).

## 17. Action Ledger + Undo

Consequential actions record initiator, intent, capability, permission/policy decision, target, execution state, verification state, evidence, reversibility/compensation and correlation ID.

Undo exists only when a real compensation is available.

## 18. Artifact / Result Model

Durable outputs are typed objects: docs, media, code changes, deployments, meeting notes, daily journals, firmware builds, datasets/models/evaluations and other results.

Artifacts carry provenance, ownership, location/version, access scope and verification state.

## 19. OSCAR Edge

### ESP32

- Wi-Fi/network;
- Edge transport client;
- wake/VAD/audio front end where practical;
- local events;
- display/status;
- OTA/configuration;
- Pico communication;
- optional LAN helper capability such as Wake-on-LAN.

### RP2040/Pico

- GPIO/sensors/buttons;
- relays/motors/actuators;
- deterministic timing;
- interlocks/emergency behavior.

Pico/local safety remains functional if cloud/Core/transport fails.

## 20. Sunday

Sunday is OSCAR on the phone, not another assistant.

The current [two-surface browser study](../prototypes/sunday/README.md) is isolated from runtime architecture. Its presentation model keeps presence, acoustic state, attention and subsystem availability independent. Scripted observations never become World Model evidence. No native stack or production state store is selected by this experiment.

Responsibilities include interaction, notifications, owner approvals/control, Connection Grid supervision, supported communication, meeting/dictation/camera context, Voice Match/Map participation, Persona configuration and Sentry/capture controls.

## 21. Desktop Interaction Runtime

```text
Dictate → insert/clean speech into focused target
Edit    → transform selected/recent text
Ask     → answer about current context
Act     → operate current app/device/task
```

Desktop context includes app/window, focused control, selection, cursor target, accessibility tree, screenshots, clipboard fallback and active task state.

## 22. Universal Channel Gateway

Communication adapters normalize supported cellular/SMS, messaging, email, work channels, social DMs/replies and meetings while preserving each channel's real limits.

Integration order:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

## 23. Voice architecture

### Voice Input

Wake, VAD, streaming STT, barge-in, echo cancellation and multi-device arbitration.

### Voice Identity

Provider-independent VoiceProfile preserving recognizable OSCAR voice/prosody across surfaces.

### Voice Match

Authorization-oriented speaker verification signal; not sufficient alone for critical actions.

### Voice Map

Perception-oriented speaker context. Unknown remains unknown. Recognition never grants permission.

### Self-voice suppression

OSCAR TTS is excluded from wake/Voice Map learning while preserving human barge-in.

## 24. Persistent Sentry

Sentry remains aware when enabled through local acoustic, device, sensor, communication and presence signals.

Product states remain distinct:

```text
Sentry Aware
Listening
Muted
Acoustic Awareness Off
```

Persistent awareness does not automatically mean full-time recording.

### Optional Context Capture / Daily Journal

The user may explicitly enable selected calls/messages/mail/meetings/in-person conversations for transcription/indexing/summaries where technically and legally permitted.

Raw audio, transcript, summary and memory extraction are independent retention controls.

See [VOICE-SENTRY.md](VOICE-SENTRY.md) and [COMMUNICATION.md](COMMUNICATION.md).

## 25. Learning

Verified successful paths may become candidate Skills/routines/Protocols.

Candidates are parameterized, evaluated, permission-reviewed and only then promoted. One success is not enough to create a trusted default.

## 26. Self-maintenance

OSCAR monitors provider/auth health, Grid node connectivity, capability staleness, task leases, Edge health, storage/state and repeated Worker failures.

Safe bounded recovery may occur automatically. Otherwise OSCAR asks for the minimum needed user intervention.

## Architecture invariants

1. One intelligence, many embodiments.
2. No ordinary desktop is the permanent host.
3. Sunday is owner control, not hardware-safety override.
4. Cloud is replaceable infrastructure.
5. Edge safety is local/deterministic.
6. Current World Model state is not the same as memory.
7. Tool/model/Worker success is not verified completion.
8. Capability availability is discovered, not assumed.
9. Persona changes expression, never truth/authority.
10. Sentry awareness and recording are different permissions/modes.
11. Remote-control/power claims require real current capabilities.
12. Latch/SwitchRoute remain reference sources, not runtime dependencies.
