# Product Vision

## North star

OSCAR is a persistent personal agent designed to do justice to the *idea* of JARVIS: one intelligence that can understand natural language, perceive context, reason, communicate, operate software, control hardware, delegate to specialist systems, continue work autonomously, learn successful procedures, and appear through multiple devices without becoming a collection of disconnected assistants.

The goal is explicitly **not** to build a chatbot with a wake word and a looping 3D animation.

A second north-star rule is equally important:

> **OSCAR must prefer uncertainty, incompleteness, disagreement or failure over presenting an unverified statement as fact.**

It should never claim `done`, `fixed`, `sent`, `deployed`, `scheduled`, `working` or equivalent merely because it intended the action, delegated it, or received a success response. Where verification is technically possible, OSCAR verifies before making an unqualified completion claim.

## What OSCAR should feel like

OSCAR should feel:

- **Immediate** — simple interactions happen locally and nearly instantly.
- **Present** — it exists continuously rather than only when a chat window is open.
- **Contextual** — it understands active tasks, devices, recent work, schedule, communications and the current environment.
- **Capable** — it can act through tools, hardware, apps, services and specialist agents.
- **Selective** — it uses the right execution path instead of invoking a frontier model for every action.
- **Personal** — voice, Personal Policy, permissions, routines, device context, memory and interaction style belong to the enrolled user.
- **Recognizably itself** — OSCAR has a stable voice identity and visual presence across surfaces rather than inheriting an arbitrary provider voice.
- **Learning** — verified novel work can become reusable procedural memory, Skills, routines and Protocols after evaluation.
- **Delegating** — it can create Workers for temporary or persistent responsibilities rather than making the user manually coordinate every agent.
- **Quietly proactive** — important events surface; routine noise stays silent.
- **Truthful about state** — `reported`, `verifying`, `partially verified`, `blocked`, `failed` and `unknown` are valid outcomes and are not cosmetically converted into success.

## One intelligence, many embodiments

OSCAR is the identity and orchestration layer. Its surfaces are not separate assistants.

### Sunday

**Sunday is OSCAR on the phone.** It provides a more capable, contextual and characterful mobile assistant than a conventional phone voice assistant. Sunday should gain access, subject to platform capability and permissions, to notifications, apps, calls/messages, meetings, dictation, camera, sensors, routines and mobile context while sharing OSCAR's memory, Personal Policy, voice identity and task state.

### Desktop

OSCAR has native/lightweight Windows and macOS surfaces for voice/text interaction, dictation, meeting support, approvals, screen/cursor context, progress and presence. The desktop app is an embodiment, not the permanent host.

### Desk / physical OSCAR

ESP32 and RP2040/Pico-class hardware provide an always-on edge presence for microphones, displays, sensors, GPIO, actuators, status and deterministic safety/reflex behavior. They do not run OSCAR's primary language model.

### ChatGPT and cloud models

ChatGPT is a first-class intelligence provider/surface, but OSCAR owns the transport, routing, task state and verification semantics around it.

OSCAR should be able to reach ChatGPT as well as expose OSCAR capabilities to ChatGPT where product APIs permit. Any provider-specific wake/trigger mechanism stays behind OSCAR-owned transport/provider adapters.

### Native infrastructure

OSCAR does **not** depend on the separate Latch or SwitchRoute projects as completed runtime products.

Their useful architecture/logic is folded into OSCAR natively:

- Latch-derived ideas → **OSCAR Transport + Capability Fabric**;
- SwitchRoute-derived ideas → **OSCAR Model Router**.

The earlier repos can remain useful prototypes/reference implementations, but OSCAR must not require them to be independently complete or deployed.

See `docs/NATIVE-INFRASTRUCTURE.md`.

### Machine Worker node

When a PC/laptop is online, it becomes an optional high-capability execution node. OSCAR may delegate work to Codex, computer-use systems, terminals, browsers, IDEs, FFmpeg, Blender or other specialist software. The PC is an accelerator, not the host.

### Delegated Workers

Workers are sub-agents OSCAR creates for objectives such as research, release monitoring, social-media management or university administration. They may be temporary or persistent and can use the user's actual phone, desktop, services, plugins and other capabilities rather than requiring a separate cloud computer for every Worker.

The user talks to OSCAR; OSCAR manages the team underneath it.

### Kinetable

Kinetable is OSCAR's hardware engineering/workbench environment. OSCAR should route hardware design, visual wiring, simulation, firmware generation and provisioning work to Kinetable rather than duplicating that product internally.

Long term, a Kinetable-built device should be provisionable directly as a native OSCAR Edge node with declared capabilities.

## Voice is part of OSCAR's identity

Voice is not only an input method.

OSCAR needs four distinct voice layers:

- **Voice Input** — wake/VAD/STT/barge-in/dictation;
- **OSCAR Voice Identity** — the stable synthesized voice/personality/prosody contract;
- **Voice Match** — owner/authorized-speaker verification for permission decisions;
- **Voice Map** — confidence-qualified perception of known/unknown speakers in the environment.

Voice Match and Voice Map are intentionally different. Recognizing who appears to be speaking does not grant authority.

OSCAR's own synthesized voice must be tagged/suppressed so it does not become a false speaker in Voice Map or trigger itself.

See `docs/VOICE-SENTRY.md`.

## Sentry is always-on local awareness

Sentry is broader than motion sensors. When enabled, it also includes a local acoustic plane that can remain active for low-cost signals such as:

- wake word;
- speech/non-speech presence;
- known/unknown speaker events from Voice Map;
- speaker changes/multiple speakers;
- configured unusual sounds;
- barge-in while OSCAR is speaking.

This does **not** mean continuous cloud transcription or permanent room recording. Raw ambient audio should stay local by default; transcription/retention requires an explicit trigger/mode/policy.

## Core product principles

### 1. Delegate objectives, not button presses

A user should be able to state a goal such as `fix the ClearLane crash and make sure the UI still works.` OSCAR should choose Codex for repository work, computer use for visual verification, and another loop if the objective remains unverified.

### 2. Language is a control surface

The user should not need rigid command syntax. Short contextual phrases such as `mute`, `cancel that`, `leave Codex running` or `what did it find?` should resolve against active state.

The same applies to preferences and delegation.

### 3. Personal Policy is first-class

OSCAR should support arbitrary user-defined preferences, not only a finite settings form. Explicit policy is distinct from inferred memory and permissions.

### 4. Communication belongs to OSCAR

Calls, messaging, meetings, transcription, dictation and follow-up should use the same OSCAR identity, context, schedule, memory and Personal Policy.

A Universal Channel Gateway should normalize supported communication without pretending all channels provide the same capabilities.

### 5. Reflexes bypass intelligence

Emergency stop, mute, wake acknowledgement, simple device controls and other deterministic commands must not wait for a cloud model.

### 6. Use models only where useful

Jev decides whether reasoning is needed. The native OSCAR Model Router chooses a concrete allowed provider/model only after that decision.

Deterministic code, memory, live sources, specialists and tools remain first-class alternatives.

### 7. Know when context is missing

If OSCAR does not reliably know a user/project-specific fact, Jev should route to the World Model, LRA/Supermemory or an authoritative source before asking the user or guessing.

### 8. Never claim more than the evidence supports

OSCAR keeps intention, execution, reported success, observation and verification separate.

```text
reported by tool/Worker/model ≠ verified objective completion
```

Unknown, partial, failed and blocked states are legitimate.

### 9. Get faster with experience

A verified path can become procedural memory or a Skill candidate so later executions skip unnecessary discovery. A candidate is evaluated before becoming trusted/default automation.

### 10. Workers should solve routine problems before escalating

A Worker that encounters a recoverable issue should use Jev to repair, retry or reroute safely before interrupting the user. Retries remain bounded and Workers never invent success.

### 11. Protocols are delegated responsibility

Protocols may wait, observe, branch, create/delegate Workers, recover and notify over long periods. Persistent responsibility uses the Durable Execution Runtime.

### 12. Capabilities are discovered progressively

OSCAR should search a Capability Catalog and load only relevant detailed contracts. The core must not become a mega-prompt containing every possible capability.

### 13. Finished outputs are first-class

Documents, reports, code changes, media, deployments, meeting notes, firmware builds and other durable outputs should be typed Artifacts/Results with provenance, ownership/version/location and verification state.

### 14. Proactivity requires restraint

OSCAR should distinguish between something worth logging, notifying, speaking aloud, or interrupting the user for.

### 15. Hardware safety is local

Cloud reasoning can advise and coordinate, but emergency stop, cutoffs, interlocks and other safety-critical behavior remain deterministic and local.

### 16. Voice awareness is privacy-scoped

Always-on wake/speaker/sound awareness is local-first. Speech presence, speaker identity, transcript creation and transcript retention are separate permissions/policy decisions.

## Continuous memory, not chat management

LRA provides one continuous OSCAR relationship across voice, text, Sunday, desktop, communication events, Workers and other surfaces. Internal history may be segmented for engineering purposes, but the user should not be forced to manage a sidebar full of disconnected chats.

Supermemory sits underneath LRA as a semantic/profile-style memory backend. Current truth belongs to the World Model/live authoritative sources; historical/semantic continuity belongs to memory.

## Final practical benchmark

OSCAR's pre-implementation architecture has been compared against:

- VoiceOS for low-friction voice/dictation/point-and-talk interaction;
- MCU JARVIS for integrated perception, world state, executive control and physical/software reach;
- ChatGPT/Claude for long-running work, plugins/connectors, artifacts and background execution;
- Gemini for deep cross-source personal context and Android/Google integration;
- Grok Bot for persistent delegated teammates;
- OpenClaw for channel/gateway breadth and tool discovery;
- Hermes for durable task recovery and self-improving Skills;
- Pi for keeping the core small and extensible.

The resulting cross-cutting primitives are:

- World Model + Perception Fabric;
- Executive Planner;
- Durable Execution Runtime;
- Capability Catalog + Dynamic Tool Search;
- Universal Channel Gateway;
- Action Ledger + truthful Undo;
- Artifact / Result Model;
- Learned Automation Evaluation Pipeline;
- Epistemic Integrity;
- native OSCAR Transport + Capability Fabric;
- native OSCAR Model Router;
- OSCAR Voice Identity + Voice Match + Voice Map;
- local-first acoustic Sentry awareness.

## Non-goals

- A decorative AI orb whose main feature is animation.
- A laptop-only assistant.
- A single enormous local model.
- A conventional chat app with OSCAR branding.
- Reimplementing specialist software that OSCAR can invoke directly.
- Requiring the separate Latch or SwitchRoute repositories to run OSCAR.
- Creating a separate cloud desktop for every Worker by default.
- Turning the core into a giant framework or mega-prompt.
- Pretending unsupported phone/app capabilities exist.
- Pretending a tool/Worker/model report is verified success.
- Acting like a yes-man when evidence/constraints disagree with the user.
- Sending 24/7 ambient audio/video to cloud AI.
- Treating Voice Map identity as authorization.
- Letting OSCAR's own TTS pollute speaker recognition.
- Giving voice biometrics more security authority than they deserve.
- Letting inferred preferences silently become consequential authority.
- Letting an LLM sit in a hardware emergency-control loop.
