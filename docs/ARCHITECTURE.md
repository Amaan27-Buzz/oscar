# System Architecture

## Overview

OSCAR is a distributed personal-agent system. No single user computer is assumed to be permanently available. The low-power edge runtime preserves local presence/safety while cloud services provide cognition and rendezvous.

```text
User / Environment
       │
       ├─ voice / text / sensors / cameras / app events / communications
       ▼
┌────────────────────────────────────────────────────────────┐
│                       OSCAR CORE                           │
│ identity • task state • Personal Policy • protocols       │
└────────────────────────────┬───────────────────────────────┘
                             │
                            Jev
                  intent + epistemic routing
                             │
      ┌──────────────────────┼─────────────────────────┐
      │                      │                         │
 memory/context          intelligence             orchestration
      │                      │                         │
LRA + Supermemory   ChatGPT / SwitchRoute   tools / skills / Workers /
                                            plugins / protocols
      └──────────────────────┼─────────────────────────┘
                             │
                           Latch
                             │
      ┌──────────────────────┼──────────────────────────┐
      ▼                      ▼                          ▼
  OSCAR Edge               Sunday               Desktop / Worker nodes
 ESP32 + Pico              Android               Windows / macOS
      │                      │                            │
 physical world     calls / apps / meetings      Codex / Computer Use /
                    messages / dictation         terminal / apps / IDE
      └────────────── Kinetable hardware workshop ───────┘
```

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

The core must not assume every request requires an LLM.

## 2. Jev decision layer

TypeSafe Jev is the fast typed decision layer for both **intent** and **epistemic state**.

It should decide whether OSCAR:

- already has sufficient context
- can execute a deterministic/local action
- should query LRA/Supermemory
- should inspect an authoritative source/tool
- should invoke ChatGPT or a SwitchRoute model
- should delegate to a specialist capability or Worker
- can safely repair/retry/reroute a blocked Worker
- should ask the user

Conceptually:

```text
known      → answer/act
recall     → LRA/Supermemory
verify     → live source/tool
reason     → ChatGPT/SwitchRoute
specialist → Codex/Kinetable/computer-use/etc.
worker     → create/resume delegated Worker
unknown    → ask user
```

This is intended to reduce latency, unnecessary model calls, noisy escalation and hallucinated user/project context.

## 3. Memory: LRA + Supermemory

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

Memory is not universally authoritative. Live sources should override stale recalled state when current truth matters.

See [MEMORY.md](MEMORY.md).

## 4. Personal Policy

Personal Policy is the durable behavior/preference layer.

It is distinct from memory and permissions:

```text
memory      = what OSCAR knows
policy      = how the user wants OSCAR to behave
permission  = what OSCAR is authorized to do
protocol    = persistent autonomous responsibility
```

Personal Policy can be created/edited through normal voice or text and may apply to arbitrary scopes: people, apps, projects, calls, meetings, workers, locations, Sentry modes, time windows and other user-defined contexts.

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

## 5. Intelligence paths

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

## 6. Latch

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

## 7. OSCAR Edge

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

## 8. Sunday

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

## 9. OSCAR Desktop + machine Worker node

OSCAR Desktop provides native/lightweight Windows and macOS interaction surfaces.

Planned UI responsibilities:

- voice/text interaction
- avatar/presence
- system-wide dictation
- meeting participation/transcription where supported
- screen/cursor/selection/active-window context
- task progress
- approval surfaces
- notifications
- Sunday handoff

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

## 10. Delegated Workers

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

Workers can be temporary or persistent, collaborate in parallel, use skills, participate in protocols and recover/reroute through Jev before escalating routine problems to the user.

See [WORKERS.md](WORKERS.md).

## 11. Capability-based delegation

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

## 12. Communication runtime

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

See [COMMUNICATION.md](COMMUNICATION.md).

## 13. Learning and procedural memory

Successful execution can become reusable procedure:

```text
explore → execute → verify → distill → store
```

Later similar requests can retrieve the known path, adapt parameters and skip unnecessary discovery.

Skills/protocols/Workers may improve over time, but cannot self-grant authority.

## 14. Protocols, routines, skills, Workers and plugins

- **tool:** primitive callable capability
- **skill:** reusable learned procedure, preferably compatible with `SKILL.md` conventions
- **Worker:** delegated sub-agent responsible for an objective/job
- **routine:** recurring/simple event-driven behavior
- **protocol:** stateful long-running responsibility with triggers, branching, waiting, recovery and escalation
- **plugin/connector:** external capability provider

A protocol can create Workers; a Worker can use skills; skills can invoke tools. OSCAR may create/refine these from successful/repeated workflows subject to policy and permission review.

## 15. Kinetable

Kinetable remains a separate specialist hardware product and is integrated through capability contracts rather than duplicated inside OSCAR.

Long term, OSCAR should be able to route hardware engineering work to Kinetable and register provisioned hardware as new OSCAR-capable nodes.

## 16. Latency tiers

| Tier | Target | Examples |
|---|---:|---|
| Reflex | tens of ms to <100 ms perceived | mute, emergency stop, avatar acknowledgement |
| Local command | ~100–400 ms target | simple device/volume/mode actions |
| Fast intelligence | start response around sub-second where network allows | known tool lookup, short answer |
| Deep task | seconds/minutes as required | coding, research, multi-tool execution |

For deep tasks OSCAR should acknowledge immediately and continue asynchronously rather than remaining silent.

## 17. Streaming voice pipeline

Where available:

```text
audio → VAD/wake → partial STT → Jev → tool/model stream → chunked TTS → speaker
```

Barge-in must stop current speech and return the system to listening immediately.

## 18. Offline / degradation behavior

- Internet unavailable: local reflexes, safety, sensors and preconfigured routines continue.
- ChatGPT unavailable: SwitchRoute may handle suitable requests.
- SwitchRoute/provider unavailable: ChatGPT or another configured route may handle suitable requests.
- PC offline: desktop-machine capabilities disappear; OSCAR remains alive.
- Sunday offline: phone/app/communication capabilities owned by Sunday disappear; other surfaces remain.
- Edge unavailable: physical capabilities disappear; cloud/mobile/desktop may remain.
- Communication app unavailable: Worker waits/reroutes only to an equivalent authorized path; no silent privilege escalation.

## 19. Architectural invariants

1. The laptop is optional.
2. Hardware safety does not depend on a cloud model.
3. Consequential actions are permission-checked and attributable.
4. Voice/text/surfaces share task and memory state.
5. Internal context segmentation does not become a chat-management burden.
6. Nodes/apps/plugins advertise capabilities rather than being hard-coded assumptions.
7. OSCAR uses specialists when they are better suited than generic reasoning.
8. Jev retrieves/verifies before guessing missing personal/project context.
9. Learned skills/protocols/Workers never self-grant permissions.
10. Reflex commands do not traverse the full reasoning stack.
11. Personal Policy is distinct from memory and permission, and is editable through normal conversation.
12. Communication autonomy is platform-capability-aware, permission-scoped and governed by Personal Policy.
13. Delegated Workers belong to OSCAR and use the best available device/service mesh rather than requiring separate cloud computers.
