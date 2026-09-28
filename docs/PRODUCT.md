# Product Vision

## North star

OSCAR is a persistent personal agent designed to do justice to the *idea* of JARVIS: one intelligence that can understand natural language, perceive context, reason, operate software, control hardware, delegate to specialist systems, continue work autonomously, and appear through multiple devices without becoming a collection of disconnected assistants.

The goal is explicitly **not** to build a chatbot with a wake word and a looping 3D animation.

## What OSCAR should feel like

OSCAR should feel:

- **Immediate** — simple interactions happen locally and nearly instantly.
- **Present** — it exists continuously rather than only when a chat window is open.
- **Contextual** — it understands active tasks, devices, recent work and the current environment.
- **Capable** — it can act through tools, hardware, apps, services and specialist agents.
- **Selective** — it uses the right execution path instead of invoking a frontier model for every action.
- **Personal** — voice, permissions, routines, device context, memory and interaction style belong to the enrolled user.
- **Quietly proactive** — important events surface; routine noise stays silent.

## One intelligence, many embodiments

OSCAR is the identity and orchestration layer. Its surfaces are not separate assistants.

### Sunday

**Sunday is OSCAR on the phone.** It exists to provide a more capable, contextual and characterful mobile assistant than a conventional phone voice assistant. Sunday should gain access, subject to permissions, to notifications, apps, calls/messages, camera, sensors, routines and mobile context while sharing OSCAR's memory and task state.

### Desk / physical OSCAR

ESP32 and RP2040/Pico-class hardware provide an always-on edge presence for microphones, displays, sensors, GPIO, actuators, status and deterministic safety/reflex behavior. They do not run OSCAR's primary language model.

### ChatGPT

ChatGPT is a first-class intelligence surface through Latch. OSCAR should be able to reach ChatGPT as well as ChatGPT reaching OSCAR. Until a direct trigger path is available, Latch may abstract an indirect wake mechanism so the transport can be replaced later without changing OSCAR's higher-level contract.

### PC worker

When the user's PC/laptop is online, it becomes an optional high-capability execution node. OSCAR may delegate work to Codex, computer-use systems, Antigravity, terminals, browsers, IDEs, FFmpeg, Blender or other specialist software. The PC is an accelerator, not the host.

## Core product principles

### 1. Delegate objectives, not button presses

A user should be able to state a goal such as “fix the ClearLane crash and make sure the UI still works.” OSCAR should decide that repository work belongs with Codex, visual verification belongs with computer use, and final validation may require another loop.

### 2. Language is a control surface

The user should not need rigid command syntax for ordinary interaction. Short contextual phrases such as “mute”, “cancel that”, “leave Codex running” or “what did it find?” should resolve against the active state.

### 3. Reflexes bypass intelligence

Emergency stop, mute, simple device controls and other deterministic commands must not wait for ChatGPT or another cloud model.

### 4. Use models only where useful

OSCAR should route between deterministic code, Jev-style intent/context decisions, ChatGPT, SwitchRoute models, memory retrieval, tools and specialist workers. More orchestration is not automatically better.

### 5. Proactivity requires restraint

OSCAR should distinguish between something worth logging, notifying, speaking aloud, or interrupting the user for. Sentry Mode should make OSCAR present without making it noisy.

### 6. Hardware safety is local

Cloud reasoning can advise and coordinate, but emergency stop, over-current/temperature cutoffs, relay interlocks and other safety-critical behavior remain deterministic and local.

## Practical JARVIS capability benchmark

The inspiration is the *capability pattern* demonstrated by JARVIS across the Iron Man films and *Age of Ultron*: natural-language control, engineering assistance, environment control, suit/device telemetry, scientific analysis, proactive warnings, research, remote operation, autonomous routines, multi-agent coordination, cyber defense, persistence and delegated work.

OSCAR adapts that pattern to real systems the user actually owns:

- computers and development tools
- phone and mobile context
- cloud AI and ChatGPT
- memory and retrieval
- cameras and sensors
- ESP32/Pico hardware
- workbench devices
- software agents and plugins
- future smart-home/environment integrations

## Non-goals

- A decorative “AI orb” whose main feature is animation.
- A laptop-only assistant.
- A single enormous local model.
- Reimplementing specialist software that OSCAR can invoke directly.
- Sending 24/7 ambient audio/video to cloud AI.
- Giving voice biometrics more security authority than they deserve.
- Letting an LLM sit in a hardware emergency-control loop.
