# System Architecture

## Overview

OSCAR is a distributed personal-agent system. No single user computer is assumed to be permanently available. The low-power edge runtime preserves local presence/safety while cloud services provide cognition and rendezvous.

The target is one coherent ambient intelligence, not a set of disconnected assistants or agents.

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
                  intent + epistemic routing
                             │
      ┌──────────────────────┼─────────────────────────┐
      │                      │                         │
 memory/history          intelligence              live context
      │                      │                         │
LRA + Supermemory   ChatGPT / SwitchRoute      authoritative sources
      └──────────────────────┼─────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────┐
│                    OSCAR EXECUTIVE                         │
│ identity • tasks • Personal Policy • Executive Planner    │
│ Workers • protocols • capabilities • permissions          │
└────────────────────────────┬───────────────────────────────┘
                             │
                        Action Ledger
                             │
                           Latch
                             │
      ┌──────────────────────┼──────────────────────────┐
      ▼                      ▼                          ▼
  OSCAR Edge               Sunday               Desktop / machine nodes
 ESP32 + Pico              Android               Windows / macOS
      │                      │                            │
 physical world     calls / apps / meetings      Codex / Computer Use /
                    messages / dictation         terminal / apps / IDE
      └────────────── Kinetable + specialist engineering ────┘
```

See [JARVIS-GAP-REVIEW.md](JARVIS-GAP-REVIEW.md) for the system-level benchmark that motivated the World Model, Perception Fabric, Executive Planner, Action Ledger/Undo and Interaction Runtime.

## 1. OSCAR Core

The core owns:

- identity and shared assistant state
- active task/protocol/Worker state
- Personal Policy evaluation
- capability discovery
- permission/policy checks
- delegation decisions
- event prioritization
- recovery/retry decisions
- verification strategy
- memory/context requests
- World Model access
- Executive Planner decisions
- Action Ledger coordination

The core must not assume every request requires an LLM.

## 2. World Model

The World Model is OSCAR's live representation of **what is true now**.

It is not the same as memory. LRA/Supermemory records continuity and history; the World Model represents current entities, relationships and state with freshness/provenance.

Entity classes can include:

- people / contacts / organizations
- places / rooms / zones
- devices / nodes / sensors
- applications / services / accounts
- projects / repositories / workspaces
- tasks / Workers / Protocols
- physical objects/components where perception supports them

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

- source
- observed time
- freshness/expiry
- confidence
- authoritative/derived status
- relationship to canonical entities

## 3. Perception Fabric

The Perception Fabric normalizes current evidence before it reaches the World Model.

Potential inputs, where authorized:

- screen + accessibility-tree state
- cursor/focus/selected text
- screenshots / camera observations
- microphone/audio events
- device and application events
- phone location/activity context
- calendar/communications/notifications
- Edge sensors and presence
- Worker/Protocol/task state

Perception is current evidence, not durable memory. Important observations may later become memory through explicit retention policy.

The Perception Fabric should support multimodal fusion where useful, for example correlating a camera-observed component with workbench sensor/device telemetry.

## 4. Jev decision layer

TypeSafe Jev is the fast typed decision layer for both **intent** and **epistemic state**.

It should decide whether OSCAR:

- already has sufficient context
- can execute a deterministic/local action
- should query the World Model
- should query LRA/Supermemory
- should inspect an authoritative live source/tool
- should invoke ChatGPT or a SwitchRoute model
- should delegate to a specialist capability or Worker
- can safely repair/retry/reroute a blocked Worker
- should ask the user

Conceptually:

```text
known      → answer/act
world      → current World Model state
recall     → LRA/Supermemory
verify     → live source/tool
reason     → ChatGPT/SwitchRoute
specialist → Codex/Kinetable/computer-use/etc.
worker     → create/resume delegated Worker
unknown    → ask user
```

This is intended to reduce latency, unnecessary model calls, noisy escalation and hallucinated user/project context.

## 5. Memory: LRA + Supermemory

LRA is the persistent single-conversation/history architecture. Supermemory is the semantic/profile-style backend underneath it.

Responsibilities include:

- active live context
- episodic history
- project/device/user context
- procedural memory
- profile/relationship memory
- provenance/confidence
- context assembly
- remember/update/forget flows
- cross-device continuity

The user-facing model is one continuous OSCAR relationship. Internal history may be segmented for context-window management, but that should not force manual chat management.

Memory is not universally authoritative. Live sources and current World Model evidence should override stale recalled state when current truth matters.

See [MEMORY.md](MEMORY.md).

## 6. Universal live context/search fabric

OSCAR needs one federated way to ask connected authoritative sources for current information rather than hard-coding every connector into Jev.

Examples:

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

Jev should be able to request the smallest relevant live context and preserve source authority/provenance.

Conceptual authority order:

```text
live authoritative state
> World Model current observation
> structured OSCAR state
> recent episodic memory
> semantic/derived memory
> model prior knowledge
```

## 7. Personal Policy

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
protocol/routine defaults
        >
inferred preference suggestions
        >
product defaults
```

See [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

## 8. Executive Planner

Workers and Protocols are execution structures beneath OSCAR. The Executive Planner coordinates the total objective set.

Inputs include:

- priority
- deadlines
- dependencies
- resource/device availability
- user interruptibility
- cost
- risk
- Worker/Protocol state
- Personal Policy

The planner may:

- schedule/parallelize work
- pause or pre-empt lower-priority work
- resolve resource conflicts
- move execution to another available device/specialist
- defer work until prerequisites are available
- decide when the user needs to be interrupted

The planner does not bypass Jev, permissions or Personal Policy. It organizes work inside those boundaries.

## 9. Intelligence paths

### ChatGPT path

ChatGPT is a first-class reasoning surface through Latch.

Both directions are required:

```text
ChatGPT → Latch → OSCAR
OSCAR → Latch → ChatGPT
```

The wake/trigger transport for OSCAR → ChatGPT should remain abstracted behind Latch so implementation can evolve without changing OSCAR.

### SwitchRoute path

SwitchRoute provides autonomous cloud-model routing:

- fast/cheap classification and extraction
- stronger reasoning when needed
- provider/model fallback
- task-specific routing
- latency/cost policy

Local PC models remain optional support capabilities, not core dependencies.

## 10. Latch

Latch is OSCAR's secure bridge between ChatGPT/cloud coordination and devices/tools.

Planned responsibilities:

- bidirectional tool/event transport
- device/session identity
- permission-aware actions
- capability registry
- event correlation IDs
- task callbacks
- audit metadata
- secure rendezvous without public home-network exposure

### Latch Edge

Embedded nodes should use a small Latch Edge protocol rather than the full Latch runtime.

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

## 11. Action Ledger + Undo

Consequential actions should produce structured ledger entries.

Where supported, entries should include:

- initiating user/task/Protocol/Worker
- intent
- capability/tool/device used
- permission + Personal Policy decision
- target/resource
- before-state reference
- resulting-state reference
- verification result
- reversible/irreversible flag
- compensating/undo operation
- correlation ID + timestamp

This enables meaningful questions such as:

```text
"What did you change?"
"Why did you do that?"
"Undo that."
```

Undo is best-effort and capability-aware. OSCAR must never claim reversibility where the underlying action is irreversible.

## 12. OSCAR Edge

### ESP32 — gateway / brainstem

Responsibilities:

- Wi-Fi/network connectivity
- Latch Edge connection
- wake/VAD/audio front end where supported
- local event routing
- short-lived state/cache
- display/status coordination
- OTA/configuration
- communication with Pico/RP2040

### RP2040/Pico — deterministic controller

Responsibilities:

- GPIO
- sensors
- buttons
- relays
- motors/actuators
- deterministic timing
- hardware interlocks
- emergency behavior

The Pico must enforce safety even if ESP32, Latch or cloud intelligence fails.

## 13. Sunday

Sunday is OSCAR's mobile embodiment.

Planned capabilities, subject to platform permissions:

- voice/text interaction
- notifications and proactive alerts
- phone calls/messages/actions
- app actions and app-specific automation where permitted
- WhatsApp/Telegram/other communication surfaces where technically available
- meetings, transcription and meeting notes
- system-wide dictation/input assistance
- camera/microphone
- device/location/sensor context
- on-device speech path where suitable
- biometric confirmation for high-risk actions
- continuity with desktop/desk/ChatGPT sessions

Sunday is not a separate identity or memory silo.

See [COMMUNICATION.md](COMMUNICATION.md).

## 14. OSCAR Desktop + Interaction Runtime + machine Worker node

OSCAR Desktop provides native/lightweight Windows and macOS interaction surfaces.

Its Interaction Runtime should expose four primary modes:

```text
Dictate → insert/clean speech into the focused target
Edit    → transform selected/recent text
Ask     → answer about the current screen/selection/context
Act     → operate the current app/device/task
```

Context inputs include:

- active app/window
- focused control/text field
- selected text
- cursor target
- accessibility tree
- screenshot/visual context
- clipboard fallback
- active task/conversation

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

## 15. Multi-device voice arbitration

Sunday, desktop and physical OSCAR may hear the same wake word. Exactly one surface should normally own a voice turn.

Arbitration can consider:

- wake confidence
- signal quality / proximity
- current active device
- user interaction/gaze/touch where available
- room/presence state
- explicit device priority

Other surfaces remain synchronized and may take over through explicit handoff or failure.

## 16. Delegated Workers

A delegated **Worker** is a sub-agent OSCAR creates for a specific objective/responsibility. It is different from a machine Worker node.

Examples:

```text
SceneLab Social Worker
ClearLane Release Worker
Research Worker
University Admin Worker
```

A delegated Worker may use the user's actual device mesh instead of owning a cloud desktop:

```text
Worker
├── Sunday / phone apps
├── Desktop / browser / terminal / Codex
├── APIs / plugins
├── ChatGPT / SwitchRoute
├── Kinetable
└── OSCAR Edge
```

Workers can be temporary or persistent, collaborate in parallel, use skills, participate in Protocols and recover/reroute through Jev before escalating routine problems to the user.

See [WORKERS.md](WORKERS.md).

## 17. Capability-based delegation

OSCAR should decompose tasks by objective and choose the most suitable capability.

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
     ├─ publishing ──────────────► API/plugin/browser/Sunday
     └─ uncertainty/recovery ────► Jev → repair/reroute/ask
```

See [ORCHESTRATION.md](ORCHESTRATION.md).

## 18. Communication runtime

Calls, meetings, messaging and dictation should share one communication abstraction rather than become isolated mini-products.

Integration order:

```text
native OS / official API
→ official plugin/connector
→ app automation on paired device
→ computer-use/accessibility fallback
→ unsupported/ask
```

Personal Policy determines user-specific behavior; platform capability determines what is technically possible; permissions determine what OSCAR may actually do.

The technical media/call path must be validated per platform rather than assumed. Android cellular calls, app calls, audio capture/loopback and VoIP gateway alternatives are separate capability questions.

See [COMMUNICATION.md](COMMUNICATION.md).

## 19. Learning, teach-by-demonstration and procedural memory

Successful execution can become reusable procedure:

```text
explore → execute → verify → distill → store
```

Later similar requests can retrieve the known path, adapt parameters and skip unnecessary discovery.

OSCAR should also support deliberate teaching where technically possible:

```text
"watch me do this once"
→ observe authorized device actions
→ infer stable intent/steps
→ ask about ambiguous choices
→ create Skill candidate
→ verify
→ save/version
```

Skills/Protocols/Workers may improve over time, but cannot self-grant authority.

## 20. Protocols, routines, skills, Workers and plugins

- **tool:** primitive callable capability
- **skill:** reusable learned procedure, preferably compatible with `SKILL.md` conventions
- **Worker:** delegated sub-agent responsible for an objective/job
- **routine:** recurring/simple event-driven behavior
- **protocol:** stateful long-running responsibility with triggers, branching, waiting, recovery and escalation
- **plugin/connector:** external capability provider

A Protocol can create Workers; a Worker can use Skills; Skills can invoke tools. OSCAR may create/refine these from successful/repeated workflows subject to policy and permission review.

## 21. Predictive intelligence

The World Model + Sentry + Executive Planner may eventually support forecast-driven behavior such as:

- likely schedule conflicts
- deadline risk from current task progress
- abnormal device/sensor trends
- likely build/test failure signals
- preloading relevant context for an upcoming task

Predictions remain evidence, not authority. Actions still require policy/permission support.

## 22. Self-maintenance

OSCAR should monitor its own operational health:

- authentication expiry
- broken connectors
- stale/disappeared capabilities
- disconnected Edge nodes
- degraded speech/provider latency
- storage/state health
- update failures
- repeated Worker/Protocol failures

It should repair or roll back safe failures when confidence and permissions permit; otherwise ask the user for the minimum required intervention.

## 23. Kinetable + general engineering

Kinetable remains a separate specialist hardware product and is integrated through capability contracts rather than duplicated inside OSCAR.

Long term, OSCAR should be able to route hardware engineering work to Kinetable and register provisioned hardware as new OSCAR-capable nodes.

The same specialist-first rule applies beyond electronics: CAD, 3D, numerical simulation, diagnostics, reconstruction and optimization should be delegated to appropriate engineering/scientific software instead of recreated poorly inside OSCAR.

## 24. Latency tiers

| Tier | Target | Examples |
|---|---:|---|
| Reflex | tens of ms to <100 ms perceived | mute, emergency stop, avatar acknowledgement |
| Local command | ~100–400 ms target | simple device/volume/mode actions |
| Fast intelligence | start response around sub-second where network allows | known tool lookup, short answer |
| Deep task | seconds/minutes as required | coding, research, multi-tool execution |

For deep tasks OSCAR should acknowledge immediately and continue asynchronously rather than remaining silent.

## 25. Streaming voice pipeline

Where available:

```text
audio → VAD/wake → arbitration → partial STT → Jev → tool/model stream → chunked TTS → speaker
```

Barge-in must stop current speech and return the owning surface to listening immediately.

## 26. Offline / degradation behavior

- Internet unavailable: local reflexes, safety, sensors and preconfigured routines continue.
- ChatGPT unavailable: SwitchRoute may handle suitable requests.
- SwitchRoute/provider unavailable: ChatGPT or another configured route may handle suitable requests.
- PC offline: desktop-machine capabilities disappear; OSCAR remains alive.
- Sunday offline: phone/app/communication capabilities owned by Sunday disappear; other surfaces remain.
- Edge unavailable: physical capabilities disappear; cloud/mobile/desktop may remain.
- Communication app unavailable: Worker waits/reroutes only to an equivalent authorized path; no silent privilege escalation.
- World Model source stale: mark state stale/unknown instead of presenting old state as current truth.

## 27. Architectural invariants

1. The laptop is optional.
2. Hardware safety does not depend on a cloud model.
3. Consequential actions are permission-checked, attributable and ledgered.
4. Voice/text/surfaces share task and memory state.
5. Internal context segmentation does not become a chat-management burden.
6. Nodes/apps/plugins advertise capabilities rather than being hard-coded assumptions.
7. OSCAR uses specialists when they are better suited than generic reasoning.
8. Jev retrieves/verifies before guessing missing personal/project context.
9. Learned Skills/Protocols/Workers never self-grant permissions.
10. Reflex commands do not traverse the full reasoning stack.
11. Personal Policy is distinct from memory and permission, and is editable through normal conversation.
12. Communication autonomy is platform-capability-aware, permission-scoped and governed by Personal Policy.
13. Delegated Workers belong to OSCAR and use the best available device/service mesh rather than requiring separate cloud computers.
14. Current evidence belongs in the World Model; historical continuity belongs in memory.
15. The Executive Planner coordinates Workers/Protocols; Workers do not become independent top-level assistants.
16. Undo is best-effort and truthful: irreversible actions are never presented as reversible.
17. Multiple listening surfaces arbitrate one voice turn rather than all answering independently.
18. Point-and-talk interaction is a first-class desktop/mobile interaction target.
