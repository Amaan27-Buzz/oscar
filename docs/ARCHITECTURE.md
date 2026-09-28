# System Architecture

## Overview

OSCAR is a distributed personal-agent system. No single device is assumed to be permanently available except the low-power edge runtime and cloud rendezvous services.

```text
User / Environment
       │
       ├─ voice / text / sensors / cameras / app events
       ▼
┌────────────────────────────────────────────────────────────┐
│                       OSCAR CORE                           │
│ intent • context • policy • task state • delegation       │
└───────────────┬──────────────────┬─────────────────────────┘
                │                  │
          intelligence         memory/context
                │                  │
      ┌─────────┴─────────┐   LRA / Supermemory
      ▼                   ▼
 ChatGPT via Latch   SwitchRoute models
      │                   │
      └─────────┬─────────┘
                ▼
              Latch
                │
   ┌────────────┼───────────────────────────────┐
   ▼            ▼                               ▼
OSCAR Edge    Sunday                        PC Worker
ESP32/Pico    Android                  Codex / computer use /
                                       terminal / apps / GPU
```

## 1. OSCAR Core

The core owns the high-level state of the assistant:

- active conversation/task context
- intent and action planning
- capability discovery
- permission/policy checks
- delegation decisions
- event prioritization
- protocol/routine execution
- memory retrieval decisions
- result verification and retry/recovery

The core must not assume that every request requires an LLM.

### Jev decision layer

The planned TypeSafe Jev integration acts as a fast intent/epistemic decision layer. It should decide whether OSCAR:

- already has sufficient context
- can execute a deterministic/local intent
- should query LRA/Supermemory
- should inspect another source/tool
- should use ChatGPT or a SwitchRoute model
- should delegate to a specialist worker
- should ask the user

The purpose is to avoid unnecessary orchestration and model calls while keeping decisions explicit and testable.

## 2. Memory: LRA + Supermemory

LRA is the planned long-term memory/retrieval layer. Supermemory is the retrieval backend under that layer.

Responsibilities:

- durable user/project/device context
- cross-device continuity
- task history and important outcomes
- protocol/routine definitions
- retrieval based on relevance, not indiscriminate context injection
- provenance and confidence where possible

OSCAR should never treat memory as automatically correct. Retrieval is one possible evidence source.

## 3. Intelligence paths

### ChatGPT path

ChatGPT is a first-class reasoning surface connected through Latch.

Two directions are required:

```text
ChatGPT → Latch → OSCAR
OSCAR → Latch → ChatGPT
```

ChatGPT should be usable for complex personal reasoning, research, long-running Work-style tasks, and situations where the user's ChatGPT context is valuable.

The inbound OSCAR → ChatGPT wake transport is deliberately abstracted behind Latch. If the current ChatGPT product requires an indirect event trigger, Latch owns that workaround. A future direct trigger can replace it without changing OSCAR.

### SwitchRoute path

SwitchRoute provides general cloud-model routing for autonomous OSCAR activity:

- fast/cheap model for classification and extraction
- stronger models for reasoning when needed
- provider/model fallback
- task-specific routing
- cost/latency policy

Local models are not required for core OSCAR operation.

## 4. Latch

Latch is OSCAR's secure bridge between ChatGPT/cloud services and devices/tools.

Planned responsibilities:

- bidirectional tool/event transport
- device/session identity
- permission-aware actions
- capability registry
- event correlation IDs
- task callbacks
- audit metadata
- secure rendezvous without exposing home devices directly to the public Internet

### Latch Edge

Embedded nodes should use a tiny Latch Edge protocol rather than hosting the full Latch runtime.

Preferred networking model:

```text
ESP32 ──persistent outbound secure connection──► Latch
```

This avoids inbound port forwarding and public ESP32 endpoints.

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

## 5. OSCAR Edge

### ESP32: gateway / brainstem

Responsibilities:

- Wi-Fi/network connectivity
- Latch Edge connection
- wake-word/VAD/audio front end where supported
- local event routing
- short-lived state/cache
- display/status coordination
- OTA/configuration
- communication with Pico/RP2040

### RP2040/Pico: deterministic controller

Responsibilities:

- GPIO
- sensors
- buttons
- relays
- motors/actuators
- deterministic timing
- hardware interlocks
- emergency behavior

The Pico should remain able to enforce safety even if ESP32, Latch or the cloud fails.

## 6. Sunday

Sunday is OSCAR's mobile embodiment.

Planned capabilities, subject to platform permissions:

- voice/text interaction
- notifications and proactive alerts
- phone calls/messages/actions
- camera and microphone
- device/location/sensor context
- Android on-device speech capabilities where suitable
- biometric confirmation for high-risk actions
- continuity with desk/ChatGPT/PC sessions

Sunday is not a separate identity or memory silo.

## 7. PC Worker

The PC worker connects opportunistically through Latch and advertises capabilities dynamically.

Example:

```text
node: PC-Amaan
online: true
capabilities:
  - codex
  - computer-use
  - antigravity
  - powershell
  - terminal
  - browser
  - vscode
  - git
  - python
  - ffmpeg
  - blender
  - local-models
  - filesystem
  - gpu: RTX-class
```

OSCAR delegates to it only when useful. If the node disappears, core OSCAR remains available.

## 8. Capability-based delegation

A task should be decomposed by objective and capability, not by product branding.

Example:

```text
"Fix the app crash and verify the UI"
     │
     ├─ inspect repo / code change ─► Codex
     ├─ run application ────────────► PC worker
     ├─ visual verification ────────► computer use
     └─ summarize / decide retry ───► OSCAR core
```

The same mechanism supports future devices or cloud workers without changing the orchestration model.

## 9. Latency tiers

| Tier | Target | Examples |
|---|---:|---|
| Reflex | tens of ms to <100 ms perceived | mute, emergency stop, avatar acknowledgement |
| Local command | ~100–400 ms target | simple device/volume/mode actions |
| Fast intelligence | start response around sub-second where network allows | known tool lookup, short answer |
| Deep task | seconds/minutes as required | coding, research, multi-tool execution |

For deep tasks OSCAR should acknowledge immediately and continue asynchronously rather than remaining silent.

## 10. Streaming pipeline

Where available, voice should be fully streamed:

```text
audio → VAD/wake → partial STT → intent → streamed model/tool result → chunked TTS → speaker
```

Barge-in must stop current speech and return the system to listening immediately.

## 11. Offline / degradation behavior

- Internet unavailable: local reflexes, safety, sensors and preconfigured routines continue.
- ChatGPT unavailable: SwitchRoute may handle suitable requests.
- SwitchRoute/provider unavailable: ChatGPT or another configured route may handle suitable requests.
- PC offline: PC-only capabilities disappear from the registry; OSCAR remains alive.
- Sunday offline: phone capabilities disappear; desk/cloud state remains.
- Edge gateway unavailable: physical-node capabilities disappear; cloud/mobile/PC surfaces may remain.

## 12. Protocols, routines, skills and plugins

OSCAR should support reusable high-level behaviors:

- protocols: stateful named procedures such as `leaving_home`
- routines: recurring or event-driven automations
- skills: portable `SKILL.md`-style capability instructions/contracts
- plugins/connectors: access to external services and tools

OSCAR may propose or generate a new reusable protocol/skill after repeated or explicit user workflows, but activation must respect permissions and review requirements.

## 13. Architectural invariants

1. The laptop is optional.
2. Hardware safety does not depend on a cloud model.
3. Every consequential action is attributable and permission-checked.
4. Voice and text share task/conversation state.
5. All nodes advertise capabilities rather than being hard-coded assumptions.
6. Provider-specific APIs sit behind OSCAR/Latch abstractions where practical.
7. Reflex commands do not traverse the full reasoning stack.
