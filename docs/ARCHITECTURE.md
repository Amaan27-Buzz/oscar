# System Architecture

## Overview

OSCAR is a distributed personal-agent system. No single user computer is assumed to be permanently available. Low-power edge hardware preserves local presence/safety while cloud services provide heavy cognition and rendezvous.

The target is **one coherent ambient intelligence**, not a collection of disconnected assistants, bots or automations.

```text
User / Environment
       │
       ├─ voice / text / screens / sensors / cameras / app events / communications
       ▼
┌────────────────────────────────────────────────────────────┐
│                      PERCEPTION FABRIC                     │
│ current evidence from devices, apps, people and spaces    │
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
LRA + Supermemory   ChatGPT / SwitchRoute      authoritative sources
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
                           Latch
                             │
      ┌──────────────────────┼──────────────────────────┐
      ▼                      ▼                          ▼
  OSCAR Edge               Sunday               Desktop / machine nodes
 ESP32 + Pico              Android               Windows / macOS
      │                      │                            │
 physical world      calls / apps / channels      Codex / Computer Use /
                     meetings / dictation         terminal / apps / IDE
      └──────────── Kinetable + specialist engineering ────┘
```

Cross-cutting layers:

- Epistemic Integrity;
- Personal Policy;
- permissions/safety;
- canonical entity graph;
- audit/provenance;
- learning/evaluation.

See:

- [JARVIS-GAP-REVIEW.md](JARVIS-GAP-REVIEW.md)
- [COMPETITIVE-BENCHMARK.md](COMPETITIVE-BENCHMARK.md)
- [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md)
- [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md)

## 1. OSCAR Core

The core owns the minimum set of responsibilities that must remain globally coherent:

- identity and shared assistant state;
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

It is not the same as memory. LRA/Supermemory records continuity/history; the World Model represents current entities, relationships and state with freshness/provenance.

Entity classes can include:

- people / contacts / organizations;
- places / rooms / zones;
- devices / nodes / sensors;
- applications / services / accounts;
- projects / repositories / workspaces;
- tasks / Workers / Protocols;
- physical objects/components where perception supports them.

Example raw evidence:

```text
calendar: class until 4
phone: user is on campus
PC: online at home
Codex: build running
ESP32: desk unoccupied
mother: calling
```

The World Model should expose this as one coherent situation rather than six unrelated facts.

State entries should carry, where useful:

- source;
- observed time;
- freshness/expiry;
- confidence;
- authoritative/derived status;
- relationship to canonical entities.

Stale state is marked stale/unknown rather than presented as current truth.

## 3. Perception Fabric

The Perception Fabric normalizes current evidence before it reaches the World Model.

Potential inputs, where authorized:

- screen + accessibility-tree state;
- cursor/focus/selected text;
- screenshots / camera observations;
- microphone/audio events;
- device and application events;
- phone location/activity context;
- calendar/communications/notifications;
- Edge sensors and presence;
- Worker/Protocol/task state.

Perception is current evidence, not durable memory. Important observations may later become memory through explicit retention policy.

The Perception Fabric should support multimodal fusion where useful, for example correlating a camera-observed component with workbench sensor/device telemetry.

## 4. Jev decision layer

TypeSafe Jev is the fast typed decision layer for both **intent** and **epistemic state**.

It decides whether OSCAR:

- already has sufficient context;
- can execute a deterministic/local action;
- should query the World Model;
- should query LRA/Supermemory;
- should inspect an authoritative live source/tool;
- should invoke ChatGPT or a SwitchRoute model;
- should delegate to a specialist capability or Worker;
- can safely repair/retry/reroute a blocked Worker;
- should ask the user.

Conceptually:

```text
known      → direct evidence is sufficient
world      → current World Model state
recall     → LRA/Supermemory
verify     → authoritative live source/test
reason     → ChatGPT/SwitchRoute inference
reported   → external agent/tool/device testimony
specialist → Codex/Kinetable/computer-use/etc.
worker     → create/resume delegated Worker
unknown    → retrieve/ask instead of fabricate
```

Jev should reduce latency, unnecessary model calls, noisy escalation and hallucinated user/project context.

## 5. Epistemic Integrity

Epistemic Integrity is a system invariant.

OSCAR must distinguish:

```text
I intended to do it
I started doing it
A tool returned success
A Worker reported success
I observed the resulting state
I verified the objective
```

These are not interchangeable.

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

Rules:

- another agent/tool success result is evidence/testimony, not automatically truth;
- unqualified `Done`/`Fixed` requires verification where verification is technically possible;
- partial verification must be reported as partial;
- memory/inference cannot silently become current verified truth;
- user confidence does not change factual state;
- OSCAR may and should disagree when evidence/constraints require it;
- corrections are explicit and propagated to affected state.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## 6. Memory: LRA + Supermemory

LRA is the persistent single-conversation/history architecture. Supermemory is the semantic/profile-style backend underneath it.

Responsibilities include:

- active live context;
- episodic history;
- project/device/user context;
- procedural memory;
- profile/relationship memory;
- provenance/confidence;
- context assembly;
- remember/update/forget flows;
- cross-device continuity.

The user-facing model is one continuous OSCAR relationship. Internal history may be segmented for context-window management, but that should not force manual chat management.

Memory is not universally authoritative. Live sources and current World Model evidence override stale recalled state when current truth matters.

See [MEMORY.md](MEMORY.md).

## 7. Universal live context/search fabric

OSCAR needs one federated way to ask connected authoritative sources for current information rather than hard-coding every connector into Jev.

Sources can include:

```text
files / drives
mail / messages
calendar
browser state
GitHub / repositories
Notion / Obsidian-like knowledge systems
social accounts
Sunday phone state
Desktop machine state
Edge/device telemetry
Worker/Protocol state
```

Jev requests the smallest relevant live context and preserves source authority/provenance.

Conceptual authority order:

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

- a person across phone contact, Gmail address, Telegram identity and remembered relationship;
- one company across email domain, calendar meetings, GitHub org and notes;
- one device across Latch identity, Sunday pairing and World Model state;
- one project across repository, files, tasks and Worker state.

The entity graph supports World Model coherence, Personal Policy scoping, communication behavior and provenance.

## 9. Personal Policy

Personal Policy is the durable behavior/preference layer.

It is distinct from memory and permissions:

```text
memory      = what OSCAR knows
policy      = how the user wants OSCAR to behave
permission  = what OSCAR is authorized to do
protocol    = persistent autonomous responsibility
```

Personal Policy can be created/edited through normal voice or text and may apply to arbitrary scopes: people, apps, projects, calls, meetings, Workers, locations, Sentry modes, time windows and other user-defined contexts.

Runtime precedence is conceptually:

```text
safety / legal / platform constraints
        >
permissions
        >
explicit Personal Policy
        >
Protocol/routine defaults
        >
inferred preference suggestions
        >
product defaults
```

See [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

## 10. Executive Planner

Workers and Protocols are execution structures beneath OSCAR. The Executive Planner coordinates the total objective set.

Inputs include:

- priority;
- deadlines;
- dependencies;
- resource/device availability;
- user interruptibility;
- cost;
- risk;
- Worker/Protocol state;
- Personal Policy.

The planner may:

- schedule/parallelize work;
- pause or pre-empt lower-priority work;
- resolve resource conflicts;
- move execution to another available device/specialist;
- defer work until prerequisites are available;
- decide when the user actually needs to be interrupted.

The planner does not bypass Jev, permissions or Personal Policy. It decides **what should run and when**, not whether policy can be ignored.

## 11. Durable Execution Runtime

The Durable Execution Runtime makes long-running work survive process restarts, executor loss and temporary provider/device failure.

It owns execution mechanics rather than high-level reasoning.

Durable task state includes, where applicable:

- task/objective ID;
- owner (user / Protocol / Worker / Executive Planner);
- lifecycle state;
- current step/checkpoint;
- dependencies;
- executor lease/ownership;
- heartbeat / last progress;
- retry budget/backoff state;
- cancellation state;
- deadline/expiry;
- required capabilities;
- active execution surface;
- artifact/result references;
- verification state;
- blocker/escalation state.

Runtime behavior includes:

- durable checkpoints;
- bounded retries/backoff;
- leases and heartbeat expiry;
- reclaim of abandoned jobs;
- zombie/stuck-work detection;
- restart/resume;
- idempotency/deduplication where needed;
- durable queues/event delivery where justified;
- explicit compensation/rollback hooks when real.

A task must never remain forever in `working` merely because its executor disappeared.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## 12. Capability Catalog + Dynamic Tool Search

OSCAR may eventually have hundreds/thousands of tools, Skills, plugins, channels, device actions and specialist applications.

Loading all contracts into every prompt is not scalable.

Each capability should expose a lightweight searchable manifest containing fields such as:

- ID/name/summary;
- capability class;
- inputs/outputs;
- permissions/risk;
- supported surfaces;
- availability;
- latency/cost hints;
- reliability/history hints;
- project/workspace affinity;
- reversible/undo metadata;
- provider/plugin/version.

Conceptual flow:

```text
objective
→ required capability classes
→ capability search
→ rank by suitability + availability + policy + reliability + cost/latency
→ load detailed contracts only for finalists
→ execute specialist
```

This is progressive capability loading, not a mega-prompt.

## 13. Intelligence paths

### ChatGPT path

ChatGPT is a first-class reasoning surface through Latch.

Both directions are required:

```text
ChatGPT → Latch → OSCAR
OSCAR → Latch → ChatGPT
```

The wake/trigger transport for OSCAR → ChatGPT remains abstracted behind Latch so implementation can evolve.

### SwitchRoute path

SwitchRoute provides autonomous cloud-model routing:

- fast/cheap classification and extraction;
- stronger reasoning when needed;
- provider/model fallback;
- task-specific routing;
- latency/cost policy.

Local PC models remain optional support capabilities, not core dependencies.

Model/agent outputs enter the system as `REPORTED`/inferred evidence unless independently verified.

## 14. Latch

Latch is OSCAR's secure bridge between ChatGPT/cloud coordination and devices/tools.

Planned responsibilities:

- bidirectional tool/event transport;
- device/session identity;
- permission-aware actions;
- capability registry/catalog feeds;
- event correlation IDs;
- task callbacks;
- audit metadata;
- secure rendezvous without public home-network exposure.

### Latch Edge

Embedded nodes use a small Latch Edge protocol rather than the full Latch runtime.

Preferred network model:

```text
ESP32 ──persistent outbound secure connection──► Latch
```

Example advertised capabilities:

```text
sensor.read
gpio.set
display.show
status.get
protocol.run
voice.state
sentry.state
```

## 15. Action Ledger + Undo

Consequential actions produce structured ledger entries.

Where supported, entries include:

- initiating user/task/Protocol/Worker;
- intent;
- capability/tool/device used;
- permission + Personal Policy decision;
- target/resource;
- before-state reference;
- resulting-state reference;
- execution status;
- verification status/method;
- evidence references;
- limitations/untested surfaces;
- reversible/irreversible flag;
- compensating/undo operation;
- correlation ID + timestamp.

This enables truthful questions such as:

```text
"What did you change?"
"Why did you do that?"
"Did you actually verify it?"
"What is still untested?"
"Undo that."
```

Undo is best-effort and capability-aware. OSCAR must never claim reversibility where the underlying action is irreversible.

## 16. Artifact / Result Model

Finished outputs are first-class typed objects rather than being buried in chat/Worker text.

Examples:

- document/spreadsheet/slides;
- image/video/audio;
- code patch/commit/PR;
- research report;
- meeting notes/transcript;
- deployment;
- hardware/firmware build;
- dataset/model/evaluation output.

Artifact records should include:

- artifact ID/type/name;
- owner task/Worker/Protocol;
- producer capability;
- location/reference;
- version/hash where useful;
- source/provenance;
- verification status;
- permissions/access scope;
- project/entity/task relationships;
- supersedes/derived-from relationships.

Workers pass artifact references instead of repeatedly copying opaque outputs through prompts.

## 17. OSCAR Edge

### ESP32 — gateway / brainstem

Responsibilities:

- Wi-Fi/network connectivity;
- Latch Edge connection;
- wake/VAD/audio front end where supported;
- local event routing;
- short-lived state/cache;
- display/status coordination;
- OTA/configuration;
- communication with Pico/RP2040.

### RP2040/Pico — deterministic controller

Responsibilities:

- GPIO;
- sensors;
- buttons;
- relays;
- motors/actuators;
- deterministic timing;
- hardware interlocks;
- emergency behavior.

The Pico enforces safety even if ESP32, Latch or cloud intelligence fails.

## 18. Sunday

Sunday is OSCAR's mobile embodiment.

Planned capabilities, subject to platform permissions:

- voice/text interaction;
- notifications and proactive alerts;
- phone calls/messages/actions;
- app actions and app-specific automation where permitted;
- WhatsApp/Telegram/other communication surfaces where technically available;
- meetings, transcription and meeting notes;
- system-wide dictation/input assistance;
- camera/microphone;
- device/location/sensor context;
- on-device speech path where suitable;
- biometric confirmation for high-risk actions;
- continuity with desktop/desk/ChatGPT sessions.

Sunday is not a separate identity or memory silo.

See [COMMUNICATION.md](COMMUNICATION.md).

## 19. Universal Channel Gateway

Communication adapters feed one normalized channel abstraction instead of becoming independent subsystems.

Potential channels include:

- cellular/SMS where supported;
- WhatsApp;
- Telegram;
- Signal;
- Discord;
- Slack/Teams-style channels;
- email;
- social DMs/replies;
- future communication plugins.

A normalized channel event includes channel/account/thread/participant IDs, direction, event type, text/transcript/media references, timestamps and supported reply/action capabilities.

The gateway preserves platform-specific limits. It never assumes that because one channel supports `message.send`, another supports `call.answer`.

Integration order remains:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md) and [COMMUNICATION.md](COMMUNICATION.md).

## 20. OSCAR Desktop + Interaction Runtime + machine Worker node

OSCAR Desktop provides native/lightweight Windows and macOS interaction surfaces.

Its Interaction Runtime exposes four primary modes:

```text
Dictate → insert/clean speech into the focused target
Edit    → transform selected/recent text
Ask     → answer about the current screen/selection/context
Act     → operate the current app/device/task
```

Context inputs include:

- active app/window;
- focused control/text field;
- selected text;
- cursor target;
- accessibility tree;
- screenshot/visual context;
- clipboard fallback;
- active task/conversation.

This is the basis for point-and-talk requests such as “what is this?”, “reply to him” and “fix this button”.

The machine Worker runtime advertises capabilities dynamically, for example:

```text
codex
computer-use
terminal / powershell
browser
filesystem
vscode / IDE
python
git
ffmpeg
blender
local-models
gpu
```

The desktop app is an embodiment; the machine Worker node is an execution surface. Neither is OSCAR's permanent host.

## 21. Multi-device voice arbitration

Sunday, desktop and physical OSCAR may hear the same wake word. Exactly one surface should normally own a voice turn.

Arbitration can consider:

- wake confidence;
- signal quality / proximity;
- current active device;
- user interaction/gaze/touch where available;
- room/presence state;
- explicit device priority.

Other surfaces remain synchronized and may take over through explicit handoff or failure.

## 22. Delegated Workers

A delegated **Worker** is a sub-agent OSCAR creates for a specific objective/responsibility. It is different from a machine Worker node.

Examples:

```text
SceneLab Social Worker
ClearLane Release Worker
Research Worker
University Admin Worker
```

A Worker may use the user's actual device mesh instead of owning a mandatory cloud desktop:

```text
Worker
├── Sunday / phone apps
├── Desktop / browser / terminal / Codex
├── APIs / plugins / Channel Gateway
├── ChatGPT / SwitchRoute
├── Kinetable
└── OSCAR Edge
```

Workers can be temporary or persistent, collaborate in parallel, use Skills, participate in Protocols and recover/reroute through Jev before escalating routine problems.

Persistent/long-running Workers use the Durable Execution Runtime for leases, checkpoints, retries, recovery and verification state.

See [WORKERS.md](WORKERS.md).

## 23. Capability-based delegation

OSCAR decomposes tasks by objective and chooses the most suitable capability.

Example:

```text
"Build the SceneLab landing page"
     │
     ├─ project context ─────────► SceneLab workspace
     ├─ implementation ──────────► Codex
     ├─ design expertise ────────► Impeccable plugin
     └─ visual verification ─────► browser/computer use
```

Or:

```text
"Manage SceneLab social media"
     │
     ├─ objective/policy ────────► Social Worker
     ├─ project context ─────────► SceneLab workspace/GitHub
     ├─ publishing ──────────────► Channel/API/plugin/browser/Sunday
     └─ uncertainty/recovery ────► Jev → repair/reroute/ask
```

Detailed capability contracts are loaded only after catalog/search narrows the relevant candidates.

See [ORCHESTRATION.md](ORCHESTRATION.md).

## 24. Communication runtime

Calls, meetings, messaging and dictation share one communication abstraction rather than becoming isolated mini-products.

Personal Policy determines user-specific behavior; platform capability determines what is technically possible; permissions determine what OSCAR may actually do.

The technical media/call path must be validated per platform rather than assumed. Android cellular calls, app calls, audio capture/loopback and VoIP gateway alternatives are separate capability questions.

See [COMMUNICATION.md](COMMUNICATION.md).

## 25. Learning, teach-by-demonstration and procedural memory

Successful execution can become reusable procedure:

```text
explore → execute → verify → distill → candidate
```

OSCAR can also support deliberate teaching where technically possible:

```text
"watch me do this once"
→ observe authorized device actions
→ infer stable intent/steps
→ ask about ambiguous choices
→ create Skill candidate
```

A candidate is not automatically trusted/default.

## 26. Learned Automation Evaluation Pipeline

Generated/improved Skills, routines and Protocols move through a promotion pipeline:

```text
candidate
→ normalize / parameterize
→ replay/evaluate representative cases
→ verify output + safety properties
→ compare with current version
→ permission/policy review
→ promote / reject / keep experimental
```

Rules:

- one successful run can create a candidate, not automatically a trusted default;
- safety/permission requirements are never weakened by learning;
- untestable candidates remain experimental/partially verified;
- worse versions can be rolled back;
- provenance links back to the executions that taught the behavior.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## 27. Protocols, routines, Skills, Workers and plugins

- **tool:** primitive callable capability;
- **Skill:** reusable learned procedure, preferably compatible with `SKILL.md` conventions;
- **Worker:** delegated sub-agent responsible for an objective/job;
- **routine:** recurring/simple event-driven behavior;
- **Protocol:** stateful long-running responsibility with triggers, branching, waiting, recovery and escalation;
- **plugin/connector:** external capability provider.

A Protocol can create Workers; a Worker can use Skills; Skills can invoke tools. OSCAR may create/refine these from successful/repeated workflows subject to policy, permission and evaluation.

## 28. Predictive intelligence

The World Model + Sentry + Executive Planner may eventually support forecast-driven behavior such as:

- likely schedule conflicts;
- deadline risk from current task progress;
- abnormal device/sensor trends;
- likely build/test failure signals;
- preloading relevant context for an upcoming task.

Predictions remain evidence, not authority. Actions still require policy/permission support.

## 29. Self-maintenance

OSCAR should monitor its own operational health:

- authentication expiry;
- broken connectors/channels;
- stale/disappeared capabilities;
- disconnected Edge nodes;
- degraded speech/provider latency;
- storage/state health;
- update failures;
- repeated Worker/Protocol failures;
- stuck Durable Runtime tasks.

It should repair or roll back safe failures when confidence and permissions permit; otherwise ask the user for the minimum required intervention.

## 30. Kinetable + general engineering

Kinetable remains a separate specialist hardware product and is integrated through capability contracts rather than duplicated inside OSCAR.

Long term, OSCAR should route hardware engineering work to Kinetable and register provisioned hardware as new OSCAR-capable nodes.

The same specialist-first rule applies beyond electronics: CAD, 3D, numerical simulation, diagnostics, reconstruction and optimization should be delegated to appropriate engineering/scientific software instead of recreated poorly inside OSCAR.

## 31. Latency tiers

| Tier | Target | Examples |
|---|---:|---|
| Reflex | tens of ms to <100 ms perceived | mute, emergency stop, avatar acknowledgement |
| Local command | ~100–400 ms target | simple device/volume/mode actions |
| Fast intelligence | start response around sub-second where network allows | known tool lookup, short answer |
| Deep task | seconds/minutes as required | coding, research, multi-tool execution |

For deep tasks OSCAR acknowledges immediately and continues asynchronously rather than remaining silent.

## 32. Streaming voice pipeline

Where available:

```text
audio → VAD/wake → arbitration → partial STT → Jev → tool/model stream → chunked TTS → speaker
```

Barge-in stops current speech and returns the owning surface to listening immediately.

## 33. Offline / degradation behavior

- Internet unavailable: local reflexes, safety, sensors and preconfigured routines continue.
- ChatGPT unavailable: SwitchRoute may handle suitable requests.
- SwitchRoute/provider unavailable: ChatGPT or another configured route may handle suitable requests.
- PC offline: desktop-machine capabilities disappear; OSCAR remains alive.
- Sunday offline: phone/app/channel capabilities owned by Sunday disappear; other surfaces remain.
- Edge unavailable: physical capabilities disappear; cloud/mobile/desktop may remain.
- Communication app unavailable: Worker waits/reroutes only to an equivalent authorized path; no silent privilege escalation.
- World Model source stale: mark state stale/unknown instead of presenting old state as current truth.
- Executor disappears: Durable Execution Runtime reclaims/resumes or marks the task blocked/failed; it does not leave fake `working` state.
- Verification unavailable: report `partially_verified`/`unknown`, not `verified`.

## 34. Architectural invariants

1. The laptop is optional.
2. Hardware safety does not depend on a cloud model.
3. Consequential actions are permission-checked, attributable, ledgered and evidence-aware.
4. Voice/text/surfaces share task and memory state.
5. Internal context segmentation does not become a chat-management burden.
6. Nodes/apps/plugins advertise capabilities rather than being hard-coded assumptions.
7. Capability/tool definitions are discovered progressively rather than all loaded into every model context.
8. OSCAR uses specialists when they are better suited than generic reasoning.
9. Jev retrieves/verifies before guessing missing personal/project context.
10. A Worker/tool success report is not automatically verified objective completion.
11. Learned Skills/Protocols/Workers never self-grant permissions.
12. Learned automation is evaluated before trusted promotion.
13. Reflex commands do not traverse the full reasoning stack.
14. Personal Policy is distinct from memory and permission, and is editable through normal conversation.
15. Communication autonomy is platform-capability-aware, permission-scoped and governed by Personal Policy.
16. Delegated Workers belong to OSCAR and use the best available device/service mesh rather than requiring separate cloud computers.
17. Current evidence belongs in the World Model; historical continuity belongs in memory.
18. The Executive Planner coordinates Workers/Protocols; Workers do not become independent top-level assistants.
19. Long-running work has durable task state, bounded retry and recovery/reclaim semantics.
20. Undo is best-effort and truthful: irreversible actions are never presented as reversible.
21. Finished outputs can be represented as typed Artifacts/Results with provenance and verification state.
22. Multiple listening surfaces arbitrate one voice turn rather than all answering independently.
23. Point-and-talk interaction is a first-class desktop/mobile interaction target.
24. Channel adapters share a normalized gateway without erasing platform-specific limits.
25. The strongest user-facing claim must not exceed the strongest available evidence.
26. Unknown, partial, blocked and failed are valid states and must never be converted to success for presentation.
