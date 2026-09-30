# JARVIS / VoiceOS Gap Review

This document is a product/architecture benchmark for OSCAR. It records the system-level gaps between the OSCAR plan, a practical real-world interpretation of MCU JARVIS, and the interaction baseline demonstrated by products such as VoiceOS.

It is not an implementation-status claim. Most capabilities below are planned, not built.

This was the first major gap review. The later cross-product review is recorded in [COMPETITIVE-BENCHMARK.md](COMPETITIVE-BENCHMARK.md) and adds the runtime/integrity primitives in [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md) and [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## Current position

OSCAR already has a broad planned architecture: persistent memory, Personal Policy, communication, delegated Workers, Protocols/routines/Skills, physical hardware, Sentry, Sunday, desktop machine nodes, cloud-model providers, Kinetable and cross-device continuity.

Two implementation clarifications now apply:

- Latch is reference/prototype architecture; its useful transport/capability logic is folded into native OSCAR Transport + Capability Fabric.
- SwitchRoute is reference/prototype architecture; its useful provider-routing logic is folded into the native OSCAR Model Router.

See [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md).

Voice is also now modeled as more than STT/TTS: OSCAR has Voice Input, stable OSCAR Voice Identity, authorization-oriented Voice Match, perception-oriented Voice Map and a local-first acoustic Sentry plane. See [VOICE-SENTRY.md](VOICE-SENTRY.md).

The remaining gap is less about adding isolated integrations and more about making every capability behave like **one omnipresent intelligence**.

VoiceOS is an important interaction benchmark because it demonstrates the practical baseline OSCAR must at least match on desktop: system-wide dictation/editing, selected-text/context interaction, cursor/screen awareness, agentic execution and confirmations. MCU JARVIS is the broader capability benchmark: one system that continuously integrates perception, memory, engineering, environment, communication, planning and action.

External references used for this benchmark:

- VoiceOS product/interaction direction: https://www.voiceos.com/
- VoiceOS operating-system direction: https://www.voiceos.com/blog/how-voiceos-is-building-the-voice-operating-system
- MCU JARVIS capability pattern: film/research benchmark already captured in OSCAR planning; no external fan-wiki URL is embedded here because that site blocks automated link validation.

## Gap review

| Missing / underdefined layer | Current OSCAR state | Why it matters | Priority |
|---|---|---|---|
| **Interaction Runtime** | Dictation, screen/cursor context and voice are planned, but separately | Needs a first-class `Dictate / Edit / Ask / Act` runtime: cursor target, selected text, focused field, app context, insertion, rewriting, undo and clipboard/accessibility fallback. This is the practical VoiceOS baseline. | **P0** |
| **Point-and-talk context** | Screen/cursor/selection context exists conceptually | Requests such as “what is this?”, “reply to him” or “fix this button” should resolve from cursor + accessibility tree + screenshot + selection without requiring the user to explain the target. | **P0** |
| **Multi-device voice arbitration** | Sunday, desktop and Edge can all become voice surfaces | If multiple OSCAR devices hear the wake word, exactly one should respond. Selection needs proximity, acoustic confidence, active-device context, user state and explicit device priority, with seamless handoff. | **P0** |
| **Voice identity + ambient speaker context** | Earlier planning had STT/TTS, Voice Match and basic known/unknown speaker events | JARVIS-like presence needs a stable OSCAR speaking identity plus a distinct Voice Map for confidence-qualified speaker context. OSCAR must also suppress its own TTS from wake/speaker recognition. | **P0** |
| **Local acoustic Sentry** | Earlier Sentry planning focused heavily on wake word and physical/environment sensors | Always-on local awareness should include speech presence, known/unknown speaker events, speaker changes and configured sound classes without implying continuous cloud transcription or recording. | **P0** |
| **Universal live context/search fabric** | LRA memory + individual connectors | Memory is not enough. OSCAR needs federated live retrieval across files, mail, messages, notes, browser, GitHub, calendar, social accounts, devices and other connected systems, with live-source authority. | **P0** |
| **Telephony / meeting media architecture** | Desired behavior is documented | The technical path still needs to be proven per platform: Android call control, app-call limitations, audio capture/loopback, Meet/Zoom/WhatsApp/Telegram boundaries, VoIP gateways and consent/platform restrictions. | **P0** |
| **Action Ledger + universal Undo** | Audit, permissions and idempotency exist conceptually | “OSCAR, undo that” should work wherever technically possible. Consequential actions need before/after state, verification, attribution and a compensating/reversal operation when one exists. | **P0** |
| **World Model / Digital Twin** | Device/environment/project memory exists, but not one unified live model | This is the largest JARVIS-style gap. OSCAR needs a live graph of people, places, devices, apps, projects, objects, tasks, relationships and current state. | **P1** |
| **Multimodal spatial perception** | Cameras/screens/sensors are capability inputs | OSCAR must understand scenes, not merely receive images. This needs persistent vision, object/component recognition, spatial context and fusion across camera, screen, audio and sensor signals. | **P1** |
| **Executive Planner** | Protocols + Workers are strong | A global executive must prioritize objectives, deadlines, dependencies, devices, cost, risk and user attention across all Workers/Protocols, including pause/pre-emption/reordering. | **P1** |
| **Predictive intelligence** | Sentry mainly reacts to events | JARVIS-like behavior should anticipate deadline risk, schedule conflicts, likely build failures, abnormal sensor trends and likely next actions: **forecast → prepare**, not only event → reaction. | **P1** |
| **Teach OSCAR by demonstration** | OSCAR learns from successful executions | “Watch me do this once” should let OSCAR observe a desktop/phone workflow, infer a reusable Skill, ask about ambiguity and save a verified procedure. | **P1** |
| **General engineering/simulation runtime** | Kinetable + Codex cover electronics/software | A broader JARVIS-style engineering layer should route CAD, 3D, numerical simulation, diagnostics, reconstruction, optimization and scientific tools to appropriate specialists. | **P1** |
| **Self-maintenance / self-diagnostics** | Recovery exists mostly per Worker | OSCAR itself should monitor expired auth, broken connectors/adapters, stale capabilities, edge-node failures, bad updates, latency/storage health and configuration drift, repairing or rolling back safely where possible. | **P1** |
| **Authoritative entity / relationship graph** | LRA + Personal Policy know people/preferences | A person across contact/email/messaging/Voice Map identity, a company relationship, device/account ownership and communication history should resolve to canonical entities. | **P1** |
| **Health / wearable integration** | Not yet a defined subsystem | Optional later capability: phone/watch/health data can support context and safety, but must be explicitly permissioned and privacy-sensitive. | **P2** |
| **Home / robotics / vehicle ecosystem** | Edge can control generic hardware | Later capability contracts should cover smart-home systems, robots, cameras, drones/vehicles and room infrastructure without making any one vendor mandatory. | **P2** |

## Core architectural addition: World Model

OSCAR has many strong subsystems:

```text
Memory
Tools
Workers
Devices
Protocols
Personal Policy
```

Those need a shared live representation of **what is true now**.

```text
                    OSCAR
                      │
                    Jev
                      │
              ┌──── World Model ────┐
              │                     │
        Perception Fabric         Memory
              │                     │
 screens / cameras / audio      LRA / Supermemory
 Voice Map / sensors / apps
              │
              ▼
       "What is true now?"
              │
              ▼
        Executive Planner
              │
       Workers / Protocols
              │
            Actions
              │
        Action Ledger
              │
      observe / verify / undo
              └──────────────► World Model
```

Example raw facts:

```text
calendar: class until 4
phone: user is on campus
PC: online at home
Codex: build running
ESP32: desk unoccupied
Voice Map: unknown speaker detected near desk
mother: calling
```

The World Model should let OSCAR understand this as one situation rather than disconnected facts.

## Perception Fabric

The Perception Fabric is the ingestion/normalization layer feeding the World Model.

It should combine, where authorized:

- screen + accessibility-tree state;
- cursor, focus and selected text;
- camera frames / scene observations;
- microphone/acoustic events;
- Voice Map speaker-presence/context events;
- device and application events;
- phone location/activity context;
- calendar, communications and notifications;
- sensors / presence / environment telemetry;
- Worker/Protocol/task state.

Perception is not memory. Perception is current evidence; LRA/Supermemory provides continuity and historical evidence.

## Voice identity, Voice Map and Sentry

Voice is part of OSCAR's product identity and perception system.

```text
Voice Input          = wake / VAD / STT / barge-in
OSCAR Voice Identity = stable synthesized identity / prosody / fallback
Voice Match          = authorization-oriented speaker verification
Voice Map            = perception-oriented speaker recognition/context
Acoustic Sentry      = local wake/speech/speaker/sound event plane
```

Recognition does not imply authorization. Voice Map unknowns remain unknown, confidence remains explicit, and sensitive voice profiles have dedicated retention/security controls.

Sentry may listen locally for low-cost acoustic events while raw room audio and full transcription remain off-cloud/unretained by default unless explicitly activated by policy/mode.

OSCAR's own TTS must be excluded from Voice Map learning and should not retrigger wake behavior, while real barge-in remains possible.

## Universal live context/search fabric

Jev should be able to query a federated live-source layer instead of individually knowing every connector.

Examples:

```text
"Where is the latest SceneLab launch copy?"
→ search project files + knowledge systems + recent messages + GitHub

"Did they ever send the internship form?"
→ search mail + messages + files

"What is currently running at home?"
→ query live device/Worker state, not stale memory
```

Authority remains source-aware: current live state outranks stale recalled memory when current truth matters.

## Interaction Runtime

OSCAR needs a unified desktop/mobile interaction layer with four primary modes:

```text
Dictate  → insert/clean natural speech into the focused target
Edit     → transform selected/recent text
Ask      → answer about the current screen/selection/context
Act      → operate the current app/device/task
```

The runtime should understand focused application/window, focused text field, selected text, cursor target, accessibility tree, screenshot/visual context, clipboard when needed and active task/conversation.

## Multi-device voice arbitration

Wake/listen events from Sunday, desktop and physical OSCAR should participate in one arbitration protocol.

Selection can consider wake-word confidence, microphone signal quality, proximity, active device/surface, user interaction, room/presence state and explicit device preference.

Only one surface should normally speak/own the turn. Other devices remain synchronized and can take over through handoff/failure.

## Action Ledger and Undo

Every consequential action should produce a structured ledger entry containing, where applicable, initiating user/task/Protocol/Worker, capability/device, intent, policy/permission decision, target, before/result state refs, execution/verification evidence, reversibility/compensation and timestamp/correlation ID.

Undo is best-effort and capability-aware; OSCAR must never pretend an irreversible operation can be reversed.

## Executive Planner

Workers remain below OSCAR. The Executive Planner coordinates the total objective set using priority, deadline, dependencies, resource/device availability, user interruptibility, risk, cost, Worker/Protocol state and Personal Policy.

It can schedule/parallelize, pause/pre-empt, resolve resource conflicts, reroute, defer and decide when the user actually needs interruption.

## Predictive intelligence

Sentry and World Model should eventually support forecast-driven assistance such as calendar-collision risk, build/device anomaly trends, deadline risk and prefetching relevant context.

Predictions do not become authority. Personal Policy and permissions still govern actions.

## Teach by demonstration

```text
"OSCAR, watch how I do this."
→ observe authorized desktop/phone actions
→ identify intent + stable steps
→ ask about ambiguous choices
→ build Skill candidate
→ replay/evaluate in safe/test context when possible
→ verify
→ promote/version only when justified
```

## Self-maintenance

OSCAR should monitor its own operation and detect/repair, where safe, expired auth, broken adapters, stale capabilities, disconnected Edge nodes, degraded model/speech latency, state/storage health, update failures and repeated Worker failures.

## Final benchmark extension

The later comparison against ChatGPT/Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi identified five more cross-cutting primitives plus one behavioral invariant:

1. **Universal Channel Gateway** — normalize supported communication channels without erasing platform-specific limits.
2. **Durable Execution Runtime** — checkpoints, leases, heartbeats, reclaim, bounded retry and restart/resume for long-running work.
3. **Capability Catalog + Dynamic Tool Search** — progressive capability loading rather than a mega-prompt containing every tool.
4. **Learned Automation Evaluation Pipeline** — candidate → replay/evaluate → compare → policy/safety review → promote/reject/rollback.
5. **Artifact / Result Model** — typed durable outputs with provenance, ownership/version/location and verification state.
6. **Epistemic Integrity** — never collapse intention, execution, reported success, observation and verified completion; never claim more than evidence supports.

A later architecture correction also made the Latch/SwitchRoute-derived layers native to OSCAR and completed the voice model around Voice Identity, Voice Match, Voice Map and local acoustic Sentry.

See:

- [COMPETITIVE-BENCHMARK.md](COMPETITIVE-BENCHMARK.md)
- [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md)
- [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md)
- [VOICE-SENTRY.md](VOICE-SENTRY.md)
- [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ROADMAP.md](ROADMAP.md)

## Post-alpha expansion

Two major domains remain later-stage rather than destabilizing the first unified alpha:

1. **Health/wearables** — highly permissioned personal physiological/activity context.
2. **Home/robotics/vehicles** — standardized capability contracts for rooms, smart-home systems, robots, cameras, drones and vehicles.

## Direction

Do not respond to competitor releases by continuously adding isolated features.

The architecture is intentionally centered on explicit primitives and a coherent loop rather than a collection of branded dependencies.

The immediate implementation priority remains proving the fundamental loop.

**Slice 01 is still next.**
