# Product Vision

## North star

OSCAR is a persistent personal intelligence designed to do justice to the *idea* of JARVIS: one intelligence that understands natural language, perceives context, reasons, communicates, operates software, controls hardware, delegates to specialist systems, keeps working autonomously, learns successful procedures and appears through whichever trusted device is available.

It is explicitly **not** a chatbot with a wake word, a laptop-only agent or a decorative animated orb.

A second north-star rule is non-negotiable:

> **OSCAR must prefer uncertainty, incompleteness, disagreement or failure over presenting an unverified statement as fact.**

Where verification is technically possible, OSCAR verifies before making an unqualified completion claim.

## What OSCAR should feel like

- **Immediate** — reflexes and simple interactions happen locally and quickly.
- **Present** — OSCAR exists continuously rather than only while a chat window is open.
- **Contextual** — it understands active work, devices, communications, schedule and environment.
- **Capable** — it acts through tools, apps, cloud services, Workers and physical devices.
- **Selective** — it uses the best capability rather than invoking a frontier model for everything.
- **Personal** — voice, Persona, Personal Policy, permissions, memory and interaction style belong to the user.
- **Recognizably itself** — one voice/visual/character identity persists across surfaces.
- **Learning** — verified procedures can become evaluated reusable Skills/routines/Protocols.
- **Delegating** — Workers can own temporary or persistent responsibilities underneath OSCAR.
- **Quietly proactive** — important events surface; routine noise stays quiet.
- **Truthful about state** — `reported`, `verifying`, `partially verified`, `blocked`, `failed` and `unknown` remain real outcomes.
- **Hard to kill** — ordinary loss of a phone, desktop, cloud node or Edge node degrades capability instead of silently erasing the system.

## Ambient Chief of Staff

OSCAR should behave like a continuously available personal Chief of Staff, not an app the user repeatedly opens to coordinate each part of life manually.

Authorized current context may include time/date/timezone, weather, calendar, tasks/deadlines, location/mobility, notifications, calls/messages/email, current media/activity state, device/Connection Grid state, Workers/Protocols and Sentry/Edge observations.

OSCAR should combine these into one freshness-qualified picture of the user's day and, within Personal Policy and real capability, help with:

- schedule conflict detection and replanning;
- task/deadline prioritization;
- focus/study/build blocks;
- preparation/travel/weather buffers;
- commitments extracted from communication;
- morning/day briefs and `what did I miss?` summaries;
- proactive warnings when plans are becoming unrealistic;
- bounded automatic calendar/task changes when explicitly authorized;
- communication follow-up and schedule updates after verified changes.

Proactivity is graduated:

```text
observe silently
→ inform
→ suggest
→ act within policy
→ interrupt only when justified
```

Attention matters. OSCAR should avoid unnecessary visual or spoken interruption while the user is watching video, reading, presenting, driving, sleeping or explicitly focusing when evidence supports that state.

A core permission rule is:

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

Notification access does not imply permission to retain notification content or reply. Calendar read access does not imply permission to modify events. Microphone permission does not imply continuous transcription or raw-audio retention.

See `docs/CHIEF-OF-STAFF.md`.

## One intelligence, many embodiments

### Sunday

**Sunday is OSCAR on the phone.** It is the primary everyday owner-control surface because the phone usually remains with the user while laptops and desktops come and go.

Subject to platform support and permissions, Sunday provides voice/text, notifications, calls/messages, meetings, camera/sensors, biometric approval, remote task supervision, Connection Grid controls and the strongest everyday Chief-of-Staff presence.

On Android, Sunday should use legitimate platform capabilities where supported: the assistant role/voice-interaction path, optional application overlay for the OSCAR Orb, home-screen widgets, notification-listener context and actionable notification replies when a real reply action exists. OEM/device behavior must be verified on target hardware rather than assumed.

The Orb is persistent presence, not permanent obstruction. It may retreat to an edge anchor/hidden hotspot during video, reading, presentations or focus contexts and return immediately when invoked.

Sunday can pause/cancel autonomous work, revoke nodes/sessions and issue owner-level remote controls. It does **not** override deterministic hardware safety.

### Desktop

OSCAR has native/lightweight Windows and macOS surfaces for interaction, dictation, approvals, screen/cursor context, task progress and presence.

A desktop machine is an optional high-capability node exposing Codex, terminal, filesystem, browser, computer use, installed apps, GPU/local models and other capabilities. It is never the permanent OSCAR host.

### Desk / physical OSCAR

ESP32 + RP2040/Pico-class hardware provide persistent local presence, sensors, wake/VAD, GPIO/actuators and deterministic safety/reflex behavior. The Edge layer does not run OSCAR's primary language model.

### Cloud

A replaceable cloud coordinator can provide rendezvous, durable coordination, remote command routing and notification fan-out. OSCAR should support free-tier, paid and bring-your-own-cloud deployment rather than depending on one vendor.

See `docs/CONNECTION-GRID.md`.

### ChatGPT and model providers

ChatGPT is a first-class intelligence provider/surface, but OSCAR owns transport, routing, task state, permissions and verification semantics around it.

### Native infrastructure

OSCAR does not depend on the separate Latch or SwitchRoute projects as runtime products.

- Latch-derived ideas → **OSCAR Transport + Capability Fabric**.
- SwitchRoute-derived ideas → **OSCAR Model Router**.

The earlier repos remain reference/prototype sources only.

See `docs/NATIVE-INFRASTRUCTURE.md`.

## Connection Grid — OSCAR should not disappear with one node

Sunday, cloud coordination, desktop nodes and Edge form the **OSCAR Connection Grid**.

```text
Sunday ─┬─ Cloud coordinator
        ├─ Desktop / machine nodes
        └─ OSCAR Edge
```

Nodes advertise capabilities dynamically and communicate through OSCAR-owned transport.

The user should be able to leave a desktop task running, walk away with Sunday, inspect/approve/cancel remotely, receive the verified result and optionally let OSCAR sleep/shut down the machine when policy and real machine capabilities allow.

Remote wake/power-on is available only when a real mechanism such as Wake-on-LAN, another always-on LAN node or approved remote-management capability exists.

The product target is graceful availability, not an impossible claim of literal 100% uptime.

## Persona — character is configurable

OSCAR should be capable of character: dry, witty, solemn, warm, formal, playful, blunt or custom.

The user can shape it conversationally or manually through traits such as humor, candor, warmth, formality, brevity, playfulness, initiative and pushback, with context-specific triggers.

```text
"Be drier and less chatty."
"No jokes on university calls."
"When Sentry alerts me, be direct and serious."
```

Persona changes **how OSCAR expresses itself**, not whether it tells the truth or what it is authorized to do.

Epistemic Integrity, safety, permissions and Personal Policy outrank Persona.

See `docs/PERSONA.md`.

## Voice is part of OSCAR's identity

Voice has four distinct layers:

- **Voice Input** — wake/VAD/STT/barge-in/dictation.
- **OSCAR Voice Identity** — stable provider-independent voice/prosody contract.
- **Voice Match** — authorization-oriented owner/authorized-speaker verification.
- **Voice Map** — perception-oriented confidence-qualified speaker recognition.

Voice Match and Voice Map are intentionally different. Recognizing someone never grants authority by itself.

Persona may change tone, humor, formality and speaking mode while preserving the same OSCAR Voice Identity.

See `docs/VOICE-SENTRY.md` and `docs/PERSONA.md`.

## Sentry — persistent awareness, with optional continuity capture

Sentry means OSCAR is persistently aware when enabled, not merely waiting for a button press.

Its local perception plane can continuously support low-cost signals such as:

- wake/hot/reflex commands;
- speech/non-speech presence;
- Voice Map known/unknown speaker events;
- configured sound classes;
- motion/device/environment events;
- barge-in while OSCAR speaks.

This **awareness layer is not automatically a full-time cloud transcript**.

OSCAR may additionally support explicit opt-in capture modes for the user who wants a comprehensive personal continuity record:

- phone calls where audio access/recording is technically and legally permitted;
- WhatsApp/other app calls where the platform exposes legitimate capture capability;
- messages, text and email through authorized channel access;
- meetings;
- voice notes;
- ordinary in-person conversations through authorized microphones;
- day-to-day event summaries.

Capture is policy-scoped and source-specific. Recording/transcription legality, participant consent, platform limits and retention settings remain explicit.

Suggested modes:

```text
Awareness only
→ local event awareness; no continuous transcript retention

Context capture
→ authorized transcription/summaries; raw media minimized/ephemeral

Daily journal
→ explicitly enabled durable cross-channel continuity capture with retention controls
```

Raw audio, transcripts, summaries and derived memory are separate retention decisions.

See `docs/VOICE-SENTRY.md`, `docs/COMMUNICATION.md` and `docs/SECURITY.md`.

## Core product principles

### 1. Delegate objectives, not button presses

A user states the goal; OSCAR chooses the strongest legitimate execution path and verifies the result where practical.

### 2. Language is a control surface

Short contextual phrases such as `mute`, `cancel that`, `leave it running`, `what did it find?`, `be more serious` or `forget the last conversation` should resolve against active state and policy.

### 3. Personal Policy is first-class

Explicit behavioral rules are distinct from memory, Persona and permissions.

```text
Persona       = how OSCAR expresses itself
Personal Policy = how the user wants OSCAR to behave
Permission    = what OSCAR is authorized to do
Memory        = what OSCAR retains/recalls
```

### 4. Communication belongs to OSCAR

Calls, messaging, meetings, transcription, dictation, follow-up and optional daily continuity capture share one identity/context architecture.

### 5. Reflexes bypass intelligence

Emergency stop, wake acknowledgement, mute/stop/cancel and deterministic local controls do not wait for cloud reasoning.

### 6. Use models only where useful

Jev decides whether reasoning is needed. The Model Router chooses a provider/model only after that decision.

### 7. Know when context is missing

OSCAR queries World Model, memory or authoritative live sources instead of guessing personal/current facts.

### 8. Never claim more than evidence supports

```text
reported by tool/Worker/model ≠ verified objective completion
```

### 9. Get faster with experience

Verified procedures may become evaluated reusable automation.

### 10. Workers recover before escalating

Recoverable failures are repaired/rerouted with bounded retries before interrupting the user.

### 11. Protocols are delegated responsibility

Protocols may wait, observe, branch, delegate, verify and escalate over long periods using durable execution.

### 12. Capabilities are discovered progressively

The core searches a Capability Catalog rather than loading a mega-prompt of every tool.

### 13. Finished outputs are first-class

Durable outputs are typed Artifacts/Results with provenance and verification state.

### 14. Proactivity requires restraint

OSCAR distinguishes between silent context update, passive presence, notification, haptic, speech and urgent interruption.

### 15. Hardware safety is local

Cloud coordination never replaces deterministic local interlocks/emergency control.

### 16. Capture is explicit and inspectable

Awareness, transcription, raw-media retention, transcript retention and memory extraction are separate controls. Continuous capture is never silently enabled by a generic microphone permission.

### 17. Availability is distributed

No ordinary laptop/desktop is the permanent host. Sunday, cloud coordination and Edge provide complementary availability roles through the Connection Grid.

### 18. Perception, retention and action are separate

Being able to observe current context never silently creates durable memory or authority to mutate the underlying source.

### 19. OSCAR coordinates the day, not just individual requests

The Executive Planner should use authorized current commitments/context to help protect focus, detect conflicts, surface deadlines and replan within policy rather than waiting for every problem to become an explicit prompt.

## Continuous memory, not chat management

LRA provides one continuous OSCAR relationship across voice, text, Sunday, desktop, communications, Workers, Sentry capture and other surfaces.

Supermemory sits underneath LRA for semantic/profile-style continuity. Current truth belongs to the World Model/live sources; historical continuity belongs to memory.

## Practical benchmark

OSCAR's architecture is informed by practical interaction/runtime patterns from VoiceOS, JARVIS-like integrated perception/executive behavior, modern long-running agent systems, device assistants and small extensible agent cores.

The durable primitives are:

- World Model + Perception Fabric;
- Ambient Chief-of-Staff context/commitment model;
- Executive Planner;
- Durable Execution Runtime;
- Capability Catalog + Dynamic Tool Search;
- Universal Channel Gateway;
- Action Ledger + truthful Undo;
- Artifact / Result Model;
- Learned Automation Evaluation Pipeline;
- Epistemic Integrity;
- native Transport + Capability Fabric;
- native Model Router;
- Connection Grid;
- Voice Identity + Voice Match + Voice Map;
- persistent Sentry awareness + explicit capture modes;
- configurable Persona.

## Non-goals

- decorative AI-orb software;
- laptop-only availability;
- a conventional chat app with OSCAR branding;
- an intrusive always-on overlay that obstructs the user's content;
- reimplementing specialist software OSCAR can invoke;
- mandatory external Latch/SwitchRoute services;
- one cloud computer per Worker;
- one vendor-specific cloud host;
- unsupported claims about phone/app/control capability;
- treating notification visibility as unrestricted access to an app;
- conflating perception permission with retention/action authority;
- treating external success reports as verified facts;
- yes-man behavior;
- covert or silently enabled recording;
- treating Voice Map identity as permission;
- letting Persona reduce truthfulness/safety;
- putting an LLM in a hardware emergency-control loop.
