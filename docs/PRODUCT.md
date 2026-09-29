# Product Vision

## North star

OSCAR is a persistent personal agent designed to do justice to the *idea* of JARVIS: one intelligence that can understand natural language, perceive context, reason, communicate, operate software, control hardware, delegate to specialist systems, continue work autonomously, learn successful procedures, and appear through multiple devices without becoming a collection of disconnected assistants.

The goal is explicitly **not** to build a chatbot with a wake word and a looping 3D animation.

## What OSCAR should feel like

OSCAR should feel:

- **Immediate** — simple interactions happen locally and nearly instantly.
- **Present** — it exists continuously rather than only when a chat window is open.
- **Contextual** — it understands active tasks, devices, recent work, schedule, communications and the current environment.
- **Capable** — it can act through tools, hardware, apps, services and specialist agents.
- **Selective** — it uses the right execution path instead of invoking a frontier model for every action.
- **Personal** — voice, Personal Policy, permissions, routines, device context, memory and interaction style belong to the enrolled user.
- **Learning** — novel successful work can become reusable procedural memory, skills, routines and protocols.
- **Delegating** — it can create Workers for temporary or persistent responsibilities rather than making the user manually coordinate every agent.
- **Quietly proactive** — important events surface; routine noise stays silent.

## One intelligence, many embodiments

OSCAR is the identity and orchestration layer. Its surfaces are not separate assistants.

### Sunday

**Sunday is OSCAR on the phone.** It provides a more capable, contextual and characterful mobile assistant than a conventional phone voice assistant. Sunday should gain access, subject to platform capability and permissions, to notifications, apps, calls/messages, meetings, dictation, camera, sensors, routines and mobile context while sharing OSCAR's memory, Personal Policy and task state.

### Desktop

OSCAR has native/lightweight Windows and macOS surfaces for voice/text interaction, dictation, meeting support, approvals, screen/cursor context, progress and presence. The desktop app is an embodiment, not the permanent host.

### Desk / physical OSCAR

ESP32 and RP2040/Pico-class hardware provide an always-on edge presence for microphones, displays, sensors, GPIO, actuators, status and deterministic safety/reflex behavior. They do not run OSCAR's primary language model.

### ChatGPT

ChatGPT is a first-class intelligence surface through Latch. OSCAR should be able to reach ChatGPT as well as ChatGPT reaching OSCAR. Until a direct trigger path is available, Latch may abstract an indirect wake mechanism so the transport can be replaced later without changing OSCAR's higher-level contract.

### Machine worker node

When a PC/laptop is online, it becomes an optional high-capability execution node. OSCAR may delegate work to Codex, computer-use systems, Antigravity, terminals, browsers, IDEs, FFmpeg, Blender or other specialist software. The PC is an accelerator, not the host.

### Delegated Workers

Workers are sub-agents OSCAR creates for objectives such as research, release monitoring, social-media management or university administration. They may be temporary or persistent and can use the user's actual phone, desktop, services, plugins and other capabilities rather than requiring a separate cloud computer for every Worker.

The user talks to OSCAR; OSCAR manages the team underneath it.

### Kinetable

Kinetable is OSCAR's hardware engineering/workbench environment. OSCAR should route hardware design, visual wiring, simulation, firmware generation and provisioning work to Kinetable rather than duplicating that product internally.

Long term, a Kinetable-built device should be provisionable directly as an OSCAR/Latch Edge node with declared capabilities.

## Core product principles

### 1. Delegate objectives, not button presses

A user should be able to state a goal such as “fix the ClearLane crash and make sure the UI still works.” OSCAR should decide that repository work belongs with Codex, visual verification belongs with computer use, and final validation may require another loop.

For something like “build a landing page for SceneLab,” OSCAR should use the SceneLab project context, Codex, the Impeccable plugin and browser verification when those are the best available capabilities.

### 2. Language is a control surface

The user should not need rigid command syntax for ordinary interaction. Short contextual phrases such as “mute”, “cancel that”, “leave Codex running” or “what did it find?” should resolve against the active state.

The same rule applies to preferences and delegation:

```text
"Don't answer family calls for me."
"Let the SceneLab worker publish ordinary feature posts."
"Create someone to watch ClearLane releases tonight."
```

### 3. Personal Policy is first-class

OSCAR should support arbitrary user-defined preferences, not only a finite settings form. Explicit policy is distinct from inferred memory and distinct from permissions.

The user can create, inspect, edit or remove durable behavior rules using normal voice/chat.

### 4. Communication belongs to OSCAR

Calls, messaging, meetings, transcription, dictation and follow-up should use the same OSCAR identity, context, schedule, memory and Personal Policy rather than forcing the user into separate assistant products.

OSCAR should prefer native/official integration paths and never pretend a platform/app exposes a capability that it does not.

### 5. Reflexes bypass intelligence

Emergency stop, mute, simple device controls and other deterministic commands must not wait for ChatGPT or another cloud model.

### 6. Use models only where useful

OSCAR routes between deterministic code, Jev intent/epistemic decisions, ChatGPT, SwitchRoute models, memory retrieval, tools and specialist Workers. More orchestration is not automatically better.

### 7. Know when context is missing

If OSCAR does not reliably know a user/project-specific fact, Jev should route to LRA/Supermemory or an authoritative source before asking the user. Guessing from vague model memory is a failure mode.

### 8. Get faster with experience

The first time OSCAR completes a novel task may involve exploration. A successful verified path can then become procedural memory or a reusable skill so later executions skip unnecessary discovery.

### 9. Workers should solve routine problems before escalating

A Worker that encounters a recoverable issue should use Jev to repair, retry or reroute safely before interrupting the user. Escalation is for ambiguity, blocked authentication, new authority or genuinely unresolved problems.

Retries remain bounded and Workers never invent success.

### 10. Protocols are delegated responsibility

OSCAR's protocols should be able to wait, observe, branch, create/delegate Workers, recover and notify over long periods. They are more capable than simple reminders or scheduled prompts.

### 11. Proactivity requires restraint

OSCAR should distinguish between something worth logging, notifying, speaking aloud, or interrupting the user for. Sentry Mode should make OSCAR present without making it noisy.

### 12. Hardware safety is local

Cloud reasoning can advise and coordinate, but emergency stop, over-current/temperature cutoffs, relay interlocks and other safety-critical behavior remain deterministic and local.

## Continuous memory, not chat management

LRA provides one continuous OSCAR relationship across voice, text, Sunday, desktop, communication events, Workers and other surfaces. Internal history may be segmented for engineering purposes, but the user should not be forced to manage a sidebar full of disconnected chats just to recover context.

Supermemory sits underneath LRA as a semantic/profile-style memory backend. Jev decides when recall or live verification is needed.

Personal Policy remains a separate authoritative behavior layer rather than being treated as merely another inferred memory.

## Practical JARVIS capability benchmark

The inspiration is the *capability pattern* demonstrated by JARVIS across the Iron Man films and *Age of Ultron*: natural-language control, engineering assistance, environment control, device telemetry, scientific analysis, proactive warnings, research, communication, remote operation, autonomous routines, multi-agent coordination, persistence and delegated work.

OSCAR adapts that pattern to real systems the user actually owns:

- computers and development tools
- phone and mobile context
- calls, meetings, messages and dictation
- cloud AI and ChatGPT
- memory and Personal Policy
- cameras and sensors
- ESP32/Pico hardware
- Kinetable/workbench tooling
- software agents, Workers, skills and plugins
- future smart-home/environment integrations

## Non-goals

- A decorative “AI orb” whose main feature is animation.
- A laptop-only assistant.
- A single enormous local model.
- A conventional chat app with OSCAR branding.
- Reimplementing specialist software that OSCAR can invoke directly.
- Creating a separate cloud desktop for every delegated Worker by default.
- Pretending unsupported phone/app capabilities exist.
- Sending 24/7 ambient audio/video to cloud AI.
- Giving voice biometrics more security authority than they deserve.
- Letting inferred preferences silently become consequential authority.
- Letting an LLM sit in a hardware emergency-control loop.
