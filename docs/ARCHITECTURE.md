# System Architecture

## Overview

OSCAR is a distributed personal-agent system. No single user computer is assumed to be permanently available. The low-power edge runtime preserves local presence/safety while cloud services provide cognition and rendezvous.

```text
User / Environment
       │
       ├─ voice / text / sensors / cameras / app events
       ▼
┌────────────────────────────────────────────────────────────┐
│                       OSCAR CORE                           │
│ identity • policy • task state • delegation • protocols   │
└────────────────────────────┬───────────────────────────────┘
                             │
                            Jev
                  intent + epistemic routing
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      memory/context     intelligence       capabilities
          │                  │                  │
  LRA + Supermemory   ChatGPT / SwitchRoute   tools/plugins/
                                             skills/workers
          └──────────────────┼──────────────────┘
                             │
                           Latch
                             │
      ┌──────────────────────┼──────────────────────────┐
      ▼                      ▼                          ▼
  OSCAR Edge               Sunday               Desktop / Workers
 ESP32 + Pico              Android               Windows / macOS
      │                                                   │
 physical world                                  Codex / Computer Use /
      │                                          terminal / apps / IDE
      └────────────── Kinetable hardware workshop ───────┘
```

## 1. OSCAR Core

The core owns:

- identity and shared assistant state
- active task/protocol state
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
- should delegate to a specialist capability
- should ask the user

Conceptually:

```text
known     → answer/act
recall    → LRA/Supermemory
verify    → live source/tool
reason    → ChatGPT/SwitchRoute
specialist→ Codex/Kinetable/computer-use/etc.
unknown   → ask user
```

This is intended to reduce latency, unnecessary model calls and hallucinated user/project context.

## 3. Memory: LRA + Supermemory

LRA is the persistent single-conversation/history architecture. Supermemory is the semantic/profile-style backend underneath it.

Responsibilities include:

- active live context
- episodic history
- project/device/user context
- procedural memory
- profile/preferences
- provenance/confidence
- context assembly
- remember/update/forget flows
- cross-device continuity

The user-facing model is one continuous OSCAR relationship. Internal history may be segmented for context-window management, but that should not force manual chat management.

Memory is not universally authoritative. Live sources should override stale recalled state when current truth matters.

See [MEMORY.md](MEMORY.md).

## 4. Intelligence paths

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

## 5. Latch

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

## 6. OSCAR Edge

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

## 7. Sunday

Sunday is OSCAR's mobile embodiment.

Planned capabilities, subject to platform permissions:

- voice/text interaction
- notifications and proactive alerts
- phone calls/messages/actions
- camera/microphone
- device/location/sensor context
- on-device speech path where suitable
- biometric confirmation for high-risk actions
- continuity with desktop/desk/ChatGPT sessions

Sunday is not a separate identity or memory silo.

## 8. OSCAR Desktop + PC Worker

OSCAR Desktop provides native/lightweight Windows and macOS interaction surfaces.

Planned UI responsibilities:

- voice/text interaction
- avatar/presence
- screen/cursor/selection/active-window context
- task progress
- approval surfaces
- notifications
- Sunday handoff

The worker runtime advertises machine capabilities dynamically, for example:

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

The desktop app is an embodiment; the worker is an execution node. Neither is OSCAR's permanent host.

## 9. Capability-based delegation

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
"Design an OLED presence detector"
     │
     ├─ component inventory ─────► Kinetable
     ├─ circuit/simulation ──────► Kinetable
     ├─ firmware/provisioning ───► Kinetable/edge toolchain
     └─ runtime capability ──────► OSCAR/Latch Edge
```

See [ORCHESTRATION.md](ORCHESTRATION.md).

## 10. Learning and procedural memory

Successful execution can become reusable procedure:

```text
explore → execute → verify → distill → store
```

Later similar requests can retrieve the known path, adapt parameters and skip unnecessary discovery.

Skills/protocols may improve over time, but cannot self-grant authority.

## 11. Protocols, routines, skills and plugins

- **tool:** primitive callable capability
- **skill:** reusable learned procedure, preferably compatible with `SKILL.md` conventions
- **routine:** recurring/simple event-driven behavior
- **protocol:** stateful long-running responsibility with triggers, branching, waiting, recovery and escalation
- **plugin/connector:** external capability provider

OSCAR may create or refine these from successful/repeated workflows subject to policy and permission review.

## 12. Kinetable

Kinetable remains a separate specialist hardware product and is integrated through capability contracts rather than duplicated inside OSCAR.

Long term, OSCAR should be able to route hardware engineering work to Kinetable and register provisioned hardware as new OSCAR-capable nodes.

## 13. Latency tiers

| Tier | Target | Examples |
|---|---:|---|
| Reflex | tens of ms to <100 ms perceived | mute, emergency stop, avatar acknowledgement |
| Local command | ~100–400 ms target | simple device/volume/mode actions |
| Fast intelligence | start response around sub-second where network allows | known tool lookup, short answer |
| Deep task | seconds/minutes as required | coding, research, multi-tool execution |

For deep tasks OSCAR should acknowledge immediately and continue asynchronously rather than remaining silent.

## 14. Streaming voice pipeline

Where available:

```text
audio → VAD/wake → partial STT → Jev → tool/model stream → chunked TTS → speaker
```

Barge-in must stop current speech and return the system to listening immediately.

## 15. Offline / degradation behavior

- Internet unavailable: local reflexes, safety, sensors and preconfigured routines continue.
- ChatGPT unavailable: SwitchRoute may handle suitable requests.
- SwitchRoute/provider unavailable: ChatGPT or another configured route may handle suitable requests.
- PC offline: desktop-worker capabilities disappear; OSCAR remains alive.
- Sunday offline: phone capabilities disappear; other surfaces remain.
- Edge unavailable: physical capabilities disappear; cloud/mobile/desktop may remain.

## 16. Architectural invariants

1. The laptop is optional.
2. Hardware safety does not depend on a cloud model.
3. Consequential actions are permission-checked and attributable.
4. Voice/text/surfaces share task and memory state.
5. Internal context segmentation does not become a chat-management burden.
6. Nodes/apps/plugins advertise capabilities rather than being hard-coded assumptions.
7. OSCAR uses specialists when they are better suited than generic reasoning.
8. Jev retrieves/verifies before guessing missing personal/project context.
9. Learned skills/protocols never self-grant permissions.
10. Reflex commands do not traverse the full reasoning stack.
