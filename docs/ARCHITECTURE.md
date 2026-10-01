# System Architecture

## Overview

OSCAR is a distributed personal-agent system. No single user computer is assumed to be permanently available. Low-power edge hardware preserves local presence/safety while cloud services provide heavy cognition and rendezvous.

The target is **one coherent ambient intelligence**, not a collection of disconnected assistants, bots or automations.

Two earlier projects inform the design without becoming runtime dependencies:

- the useful architecture/logic from **Latch** is folded into OSCAR as the native **Transport + Capability Fabric**;
- the useful architecture/logic from **SwitchRoute** is folded into OSCAR as the native **Model Router**.

OSCAR must not require either external repository to be complete or separately deployed.

```text
User / Environment
       │
       ├─ voice / text / screens / sensors / cameras / app events / communications
       ▼
┌────────────────────────────────────────────────────────────┐
│                      PERCEPTION FABRIC                     │
│ screen • audio • Voice Map • devices • apps • sensors     │
└────────────────────────────┬───────────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────┐
│                       WORLD MODEL                          │
│ people • places • devices • apps • projects • tasks       │
│ relationships • current state • freshness • provenance    │
└────────────────────────────┬───────────────────────────────┘
                             │
                            Jev
                intent + epistemic decisions
                             │
      ┌──────────────────────┼──────────────────────────┐
      │                      │                          │
 memory/history          intelligence               live context
      │                      │                          │
LRA + Supermemory   ChatGPT / Model Router     authoritative sources
      └──────────────────────┼──────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────┐
│                    OSCAR EXECUTIVE                         │
│ identity • Personal Policy • Executive Planner            │
│ permissions • Workers • Protocols • objectives            │
└────────────────────────────┬───────────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────┐
│                 DURABLE EXECUTION RUNTIME                  │
│ tasks • checkpoints • leases • retries • recovery         │
└────────────────────────────┬───────────────────────────────┘
                             ▼
              Capability Catalog + Tool Search
                             │
      ┌──────────────────────┼──────────────────────────┐
      │                      │                          │
   Workers                Skills                   Protocols
      └──────────────────────┼──────────────────────────┘
                             ▼
        Actions / Channels / Devices / Specialists
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
   Action Ledger                         Artifact / Result Model
         │                                       │
         └───────────────────┬───────────────────┘
                             ▼
                         verification
                             │
                  World Model / Memory update
                             │
                    evidence-backed report
                             │
             OSCAR Transport + Capability Fabric
                             │
      ┌──────────────────────┼──────────────────────────┐
      ▼                      ▼                          ▼
  OSCAR Edge               Sunday               Desktop / machine nodes
 ESP32 + Pico              Android               Windows / macOS
      │                      │                            │
 physical world      calls / apps / channels      Codex / Computer Use /
                     meetings / dictation         terminal / apps / IDE
```

Physical hardware is controlled through native Edge/device capability contracts. Engineering/design/simulation software participates as ordinary installed or connected specialist capabilities, not as a mandatory workbench product.

Cross-cutting layers:

- Epistemic Integrity;
- Personal Policy;
- permissions/safety;
- canonical entity graph;
- Voice Identity / Voice Match / Voice Map;
- audit/provenance;
- learning/evaluation.

See:

- [JARVIS-GAP-REVIEW.md](JARVIS-GAP-REVIEW.md)
- [COMPETITIVE-BENCHMARK.md](COMPETITIVE-BENCHMARK.md)
- [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md)
- [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md)
- [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md)
- [VOICE-SENTRY.md](VOICE-SENTRY.md)

## 1. OSCAR Core

The core owns the minimum responsibilities that must remain globally coherent:

- identity/shared assistant state;
- active objectives/tasks/Protocols/Workers;
- Personal Policy evaluation;
- permission/policy checks;
- capability discovery requests;
- delegation decisions;
- event prioritization;
- recovery/reroute decisions;
- verification strategy;
- memory/context requests;
- World Model access;
- Executive Planner decisions;
- Action Ledger coordination;
- epistemic/evidence state.

The core must not assume every request requires an LLM and must not grow into a giant framework. Breadth comes from explicit primitives, adapters and specialist capabilities.

## 2. World Model

The World Model is OSCAR's live representation of **what is true now**.

It is not memory. LRA/Supermemory records continuity/history; the World Model represents current entities, relationships and state with freshness/provenance.

Entity classes can include people, contacts, organizations, places, devices, sensors, apps, accounts, projects, repositories, tasks, Workers, Protocols and physical objects/components where perception supports them.

State entries should carry, where useful:

- source;
- observed time;
- freshness/expiry;
- confidence;
- authoritative/derived status;
- relationship to canonical entities.

Stale state becomes stale/unknown rather than current truth.

## 3. Perception Fabric

The Perception Fabric normalizes current evidence before it reaches the World Model.

Inputs may include:

- screen + accessibility-tree state;
- cursor/focus/selected text;
- screenshots/cameras;
- microphone/acoustic events;
- Voice Map speaker events;
- application/device events;
- phone location/activity context;
- calendar/communications/notifications;
- Edge sensors/presence;
- Worker/Protocol/task state.

Perception is current evidence, not durable memory. Retention is a separate policy decision.

## 4. Jev decision layer

TypeSafe Jev is the fast typed decision layer for **intent** and **epistemic state**.

It decides whether OSCAR:

- already has enough evidence;
- can execute a deterministic/local action;
- should query the World Model;
- should query LRA/Supermemory;
- should inspect a live source/tool;
- should invoke model reasoning;
- should delegate to a specialist capability/Worker;
- can safely repair/retry/reroute blocked work;
- should ask the user.

Conceptually:

```text
known      → direct evidence is sufficient
world      → current World Model state
recall     → LRA/Supermemory
verify     → authoritative live source/test
reason     → native Model Router → provider
reported   → external agent/tool/device testimony
specialist → Codex/computer-use/installed apps/etc.
worker     → create/resume delegated Worker
unknown    → retrieve/ask instead of fabricate
```

Jev decides **whether** a model path is needed. The native Model Router decides **which** provider/model after that decision.

## 5. Epistemic Integrity

Epistemic Integrity is a system invariant.

OSCAR must distinguish intention, started execution, reported success, observed state and independently verified objective completion.

Task states can include:

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

Claim/evidence states can include:

```text
KNOWN
INFERRED
RECALLED
REPORTED
VERIFIED
UNKNOWN
```

Another agent/tool success result is testimony/evidence, not automatically truth.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## 6. Memory: LRA + Supermemory

LRA is the persistent single-conversation/history architecture. Supermemory is the semantic/profile-style backend underneath it.

Responsibilities include active context, episodic history, project/device/user context, procedural memory, profile/relationship memory, provenance/confidence, context assembly and cross-device continuity.

Memory is not universally authoritative. Live sources and current World Model evidence override stale recalled state when current truth matters.

## 7. Universal live context/search fabric

OSCAR needs one federated way to ask connected authoritative sources for current information rather than hard-coding every connector into Jev.

Sources may include files/drives, mail/messages, calendar, browser state, GitHub, knowledge systems, social accounts, Sunday phone state, desktop machine state, Edge telemetry and Worker/Protocol state.

Authority order is conceptually:

```text
live authoritative state
> World Model current observation
> structured OSCAR state
> recent episodic memory
> semantic/derived memory
> model prior knowledge
```

## 8. Canonical entity / relationship graph

One real-world entity should resolve consistently across systems.

Examples:

- a person across phone contact, email, messaging account, Voice Map identity and remembered relationship;
- one company across email domain, calendar meetings, GitHub org and notes;
- one device across OSCAR transport identity, Sunday pairing and World Model state;
- one project across repository, files, tasks and Worker state.

## 9. Personal Policy

Personal Policy is the durable behavior/preference layer, distinct from memory and permissions.

```text
memory      = what OSCAR knows
policy      = how the user wants OSCAR to behave
permission  = what OSCAR is authorized to do
protocol    = persistent autonomous responsibility
```

Personal Policy can apply to people, apps, projects, calls, meetings, Workers, locations, Sentry modes, voice behavior, time windows and other contexts.

## 10. Executive Planner

The Executive Planner coordinates the total objective set across Workers/Protocols/tasks using priority, deadlines, dependencies, resource/device availability, user interruptibility, cost, risk and Personal Policy.

It may schedule, parallelize, pause, pre-empt, reroute or defer work but never bypass policy/permissions/Jev.

## 11. Durable Execution Runtime

The Durable Execution Runtime makes long-running work survive process restarts, executor loss and temporary provider/device failure.

Durable task state includes lifecycle state, checkpoints, dependencies, executor ownership/leases, heartbeats, retry budget, cancellation, deadline, required capabilities, active surface, artifact/result refs, verification state and blocker/escalation state.

A task must never remain forever in `working` because its executor disappeared.

## 12. Capability Catalog + Dynamic Tool Search

Capabilities expose lightweight searchable manifests with ID/name/summary, capability class, inputs/outputs, permissions/risk, surfaces, availability, latency/cost/reliability hints, project affinity, undo metadata, provider/adapter and version.

Detailed contracts are loaded only for a small candidate set.

## 13. Native OSCAR Model Router

The Model Router is native OSCAR infrastructure based on the useful architecture/logic learned from SwitchRoute.

It is **not** a dependency on a separate SwitchRoute deployment.

Responsibilities:

- provider/model registry;
- task/capability suitability;
- latency/cost/quality policy;
- provider health/availability;
- fallback chains;
- context/capability metadata;
- routing telemetry/history;
- user/project/provider policy;
- graceful degradation.

Flow:

```text
Jev: reasoning needed
        ↓
OSCAR Model Router
        ↓
provider adapter (ChatGPT / other configured model)
        ↓
REPORTED / INFERRED result
        ↓
verification when required
```

ChatGPT is an important intelligence provider/surface, not OSCAR's sole brain and not the owner of OSCAR task state.

## 14. Native OSCAR Transport + Capability Fabric

This subsystem is native OSCAR infrastructure based on the useful architecture/logic learned from Latch.

It is **not** a dependency on a separate Latch deployment.

Responsibilities:

- bidirectional task/event/action/result transport;
- node/session identity;
- pairing/scoped credentials;
- capability advertisement;
- correlation IDs;
- progress/stream callbacks;
- permission-aware dispatch;
- audit/provenance metadata;
- reconnect/backoff;
- cancellation/control messages;
- secure outbound rendezvous for private devices.

Conceptually:

```text
OSCAR Core
  ↓
native Transport + Capability Fabric
  ├─ Sunday
  ├─ Desktop nodes
  ├─ Edge
  ├─ cloud/background workers
  └─ external adapters/providers
```

A ChatGPT-specific wake/trigger implementation detail sits behind this boundary and can evolve without changing OSCAR Core.

See [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md).

## 15. Action Ledger + Undo

Consequential actions produce structured ledger entries including initiator, intent, capability, permission/policy decision, target, before/result state refs, execution/verification state, evidence, limitations, reversibility/compensation metadata and correlation ID.

Undo is best-effort and capability-aware.

## 16. Artifact / Result Model

Finished outputs are first-class typed objects rather than being buried in chat/Worker text.

Examples include documents, spreadsheets/slides, media, code patches/commits/PRs, research, meeting notes, deployments, firmware builds and datasets/models/evaluations.

Artifacts carry provenance, owner, producer capability, location/version, verification state, access scope and relationships.

## 17. OSCAR Edge

### ESP32 — gateway / brainstem

Responsibilities:

- Wi-Fi/network connectivity;
- native OSCAR Edge transport client;
- wake/VAD/audio front end where supported;
- local event routing;
- short-lived state/cache;
- display/status coordination;
- OTA/configuration;
- communication with Pico/RP2040.

### RP2040/Pico — deterministic controller

Responsibilities:

- GPIO/sensors/buttons;
- relays/motors/actuators;
- deterministic timing;
- hardware interlocks;
- emergency behavior.

The Pico enforces safety even if ESP32, OSCAR Core, transport or cloud intelligence fails.

## 18. Sunday

Sunday is OSCAR's mobile embodiment, not a separate assistant.

The current [two-surface browser study](../prototypes/sunday/README.md) is isolated from runtime architecture. Its presentation model keeps presence, acoustic state, attention and subsystem availability independent. Scripted observations never become World Model evidence. No native stack or production state store is selected by this experiment.

Planned capabilities include voice/text, notifications, phone calls/messages/actions, app automation where permitted, meetings/transcription, dictation, camera/microphone, phone context, Voice Match/Voice Map participation, biometric confirmation and continuity with other OSCAR surfaces.

## 19. Universal Channel Gateway

Communication adapters feed one normalized channel abstraction while preserving platform-specific limits.

Potential channels include cellular/SMS, WhatsApp, Telegram, Signal, Discord, Slack/Teams-like channels, email, social DMs/replies and future adapters.

Integration order remains:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

## 20. OSCAR Desktop + Interaction Runtime + machine Worker node

The desktop Interaction Runtime exposes:

```text
Dictate → insert/clean speech into focused target
Edit    → transform selected/recent text
Ask     → answer about current screen/selection/context
Act     → operate current app/device/task
```

Context includes app/window, focused control, selected text, cursor target, accessibility tree, screenshots, clipboard fallback and active task state.

Machine nodes advertise capabilities such as Codex, computer use, terminal/PowerShell, browser, filesystem, IDEs, Python, Git, FFmpeg, Blender, local models and GPU support.

The desktop embodiment and machine execution node are not OSCAR's permanent host.

## 21. Voice architecture

Voice has four distinct layers:

### 21.1 Voice Input

- wake word;
- VAD;
- streaming STT;
- barge-in;
- echo cancellation;
- multi-device arbitration.

### 21.2 OSCAR Voice Identity

OSCAR owns a provider-independent `VoiceProfile` defining a stable synthesized voice identity, prosody/modulation policy, speaking rate/rhythm, pronunciation controls, contextual speaking modes and fallback mapping.

The goal is one recognizably consistent OSCAR voice across Sunday, desktop and desk surfaces even if underlying TTS providers change.

OSCAR's voice should be natural and expressive through modulation/timing/pacing, not theatrically emotional by default.

### 21.3 Voice Match

Voice Match is an authorization-oriented speaker-verification signal for the owner/authorized speakers. It is not sufficient alone for critical actions.

### 21.4 Voice Map

Voice Map is a perception-oriented speaker layer answering `who appears to be speaking?`.

Possible states include:

```text
owner
known_person
recognized_but_unverified
unknown_speaker
multiple_speakers
uncertain
```

Voice Map may link a speaker profile to the canonical entity graph only with sufficient evidence/confirmation. It never grants permissions by itself.

Voice profiles/embeddings are sensitive and require retention/privacy controls.

### 21.5 Self-voice suppression

OSCAR must distinguish its own TTS from external speech using playback reference, echo cancellation, TTS-origin tagging and correlation where possible.

OSCAR's own voice must never be learned as a person in Voice Map.

Self-voice suppression must still allow real barge-in.

See [VOICE-SENTRY.md](VOICE-SENTRY.md).

## 22. Multi-device voice arbitration

Sunday, desktop and physical OSCAR may hear the same wake word. Exactly one surface should normally own a voice turn.

Arbitration can consider wake confidence, signal/proximity, active device, user interaction, room/presence state and explicit device priority.

## 23. Sentry acoustic plane

Sentry is not only physical sensor monitoring. When enabled, it also consumes **always-on local acoustic awareness**.

Local low-cost signals may include:

- wake word;
- speech/non-speech presence;
- Voice Map known/unknown speaker classification;
- speaker changes/multiple speakers;
- configured unusual sound classes;
- acoustic activity useful for presence;
- barge-in during OSCAR speech.

These signals feed compact events to Perception/World Model. They do not imply continuous cloud transcription or raw-audio retention.

Speech presence, speaker identity and permission to transcribe/retain content are separate decisions.

## 24. Delegated Workers

Workers are objective/responsibility sub-agents owned by OSCAR. They can use Sunday, desktop/browser/terminal/Codex, APIs/plugins/channels, ChatGPT/native Model Router, installed/connected specialist applications and OSCAR Edge.

Persistent Workers use the Durable Execution Runtime for leases, checkpoints, retries, recovery and verification state.

## 25. Capability-based delegation

OSCAR decomposes objectives and chooses the most suitable specialist. Detailed capability contracts load only after catalog/search narrows candidates.

## 26. Communication runtime

Calls, meetings, messaging and dictation share one communication abstraction. Personal Policy determines desired behavior; platform capability determines what is technically possible; permissions determine what OSCAR may do.

## 27. Learning and teach-by-demonstration

Verified successful execution can become reusable procedural memory/Skill candidates. Deliberate `watch me do this once` teaching is supported where the platform can observe authorized actions.

## 28. Learned Automation Evaluation Pipeline

Generated/improved Skills/routines/Protocols move through candidate → normalize/parameterize → replay/evaluate → verify safety/output → compare → policy/permission review → promote/reject/experimental.

## 29. Protocols, routines, Skills, Workers and plugins

- **tool:** primitive callable capability;
- **Skill:** reusable learned procedure;
- **Worker:** delegated sub-agent;
- **routine:** recurring/simple event-driven behavior;
- **Protocol:** stateful long-running responsibility;
- **plugin/connector:** external capability provider.

## 30. Predictive intelligence

World Model + Sentry + Executive Planner may support schedule conflict prediction, deadline risk, device/sensor anomaly trends, build-failure indicators and quiet context prefetching.

Predictions remain evidence, not authority.

## 31. Self-maintenance

OSCAR monitors expired auth, broken adapters/channels, stale capabilities, disconnected nodes, degraded speech/model-provider latency, storage/state health, update failures and stuck tasks.

Safe repair/rollback can be automatic only when bounded, authorized and evidence-backed.

## 32. Physical/device + general engineering

OSCAR controls and observes physical systems through native Edge/device capability contracts. Additional sensors, relays, displays, actuators, cameras and custom embedded nodes join the same Transport + Capability Fabric and advertise what they can actually do.

Hardware design, CAD, circuit work, firmware, 3D, numerical simulation, diagnostics, reconstruction and optimization route to suitable installed or connected specialist software discovered through the Capability Catalog. No dedicated engineering/workbench product is a required OSCAR dependency.

## 33. Latency tiers

| Tier | Target | Examples |
|---|---:|---|
| Reflex | tens of ms to <100 ms perceived | mute, emergency stop, avatar acknowledgement |
| Local command | ~100–400 ms target | simple device/volume/mode actions |
| Fast intelligence | begin around sub-second where network allows | known tool lookup, short answer |
| Deep task | seconds/minutes as required | coding, research, multi-tool execution |

## 34. Streaming voice pipeline

```text
audio
→ local wake/VAD + self-voice suppression + Voice Map event
→ arbitration
→ activated partial STT
→ Jev
→ capability/model stream
→ OSCAR VoiceProfile / chunked TTS
→ speaker
```

Barge-in stops current speech and returns the owning surface to listening immediately.

## 35. Offline / degradation behavior

- Internet unavailable: local reflexes, safety, sensors and configured acoustic/Sentry primitives continue.
- ChatGPT unavailable: native Model Router may choose another configured provider.
- model providers unavailable: deterministic/local/tool paths continue where possible.
- PC offline: desktop-machine capabilities disappear; OSCAR remains alive.
- Sunday offline: phone-owned capabilities disappear; other surfaces remain.
- Edge unavailable: physical capabilities disappear; cloud/mobile/desktop may remain.
- transport adapter fails: affected node capability disappears/reconnects without changing OSCAR identity.
- World Model source stale: mark stale/unknown.
- executor disappears: Durable Runtime reclaims/resumes or marks blocked/failed.
- verification unavailable: report partial/unknown.
- preferred TTS unavailable: use allowed fallback and report material Voice Identity degradation where relevant.

## 36. Architectural invariants

1. The laptop is optional.
2. Hardware safety does not depend on a cloud model.
3. Consequential actions are permission-checked, attributable, ledgered and evidence-aware.
4. Voice/text/surfaces share task and memory state.
5. Internal context segmentation does not become a chat-management burden.
6. Nodes/apps/plugins advertise capabilities rather than being hard-coded assumptions.
7. Capability definitions are discovered progressively.
8. OSCAR uses specialists when better suited than generic reasoning.
9. Jev retrieves/verifies before guessing missing personal/project context.
10. A Worker/tool/model success report is not automatically verified completion.
11. Learned Skills/Protocols/Workers never self-grant permissions.
12. Reflex commands do not traverse the full reasoning stack.
13. Personal Policy is distinct from memory and permission.
14. Communication autonomy is platform-capability-aware and permission-scoped.
15. Workers belong to OSCAR and use the best available device/service mesh.
16. Current evidence belongs in World Model; historical continuity belongs in memory.
17. Executive Planner coordinates Workers/Protocols.
18. Long-running work has durable state and bounded recovery.
19. Undo is truthful/best-effort.
20. Finished outputs can be typed Artifacts/Results.
21. Multiple listening surfaces arbitrate one voice turn.
22. Point-and-talk is a first-class interaction target.
23. Channel adapters share a gateway without erasing platform limits.
24. The strongest user-facing claim cannot exceed evidence.
25. Unknown/partial/blocked/failed are valid states.
26. Native OSCAR transport replaces any requirement for a separately deployed Latch runtime.
27. Native OSCAR Model Router replaces any requirement for a separately deployed SwitchRoute runtime.
28. Voice Match and Voice Map are different: recognition does not imply authorization.
29. Sentry's acoustic awareness is local-first; continuous raw room audio is not uploaded by default.
30. OSCAR's own synthesized voice is excluded from external-speaker recognition/learning.
31. OSCAR Voice Identity is a stable product contract independent of a particular TTS provider.
32. Physical/device control is native OSCAR capability work; engineering applications are replaceable specialist capabilities rather than architectural dependencies.
