<p align="center">
  <img src="assets/brand/oscar-logo.png" width="180" alt="OSCAR logo" />
</p>

<h1 align="center">OSCAR</h1>

<p align="center"><strong>A persistent, multimodal, agentic intelligence spanning your phone, computers, environment and physical hardware.</strong></p>

<p align="center">
  <code>Persistent</code> · <code>Omnipresent</code> · <code>Agentic</code> · <code>Immediate</code> · <code>Learning</code>
</p>

---

## What OSCAR is

OSCAR is an attempt to build a practical real-world interpretation of the *idea* behind JARVIS: not a chatbot with a voice and animated orb, but one intelligence that can perceive context, reason, use tools, delegate work, control software and hardware, keep working in the background, learn successful procedures, and appear through whatever device is available.

The laptop is **not** OSCAR's host. OSCAR remains available when the PC is off. The always-on edge runtime lives on low-power hardware; cloud intelligence supplies heavy cognition; connected devices become execution nodes.

**Sunday is OSCAR on the phone**, not a separate assistant.

OSCAR also avoids the conventional chat-sidebar model. LRA provides one continuous relationship/history underneath voice, text, Sunday, desktop and other surfaces.

## System at a glance

```text
                              OSCAR
                    identity • policy • tasks
                                │
                               Jev
                 intent + epistemic decisions
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
   LRA + Supermemory       Intelligence            Capabilities
  continuity + recall   ChatGPT / SwitchRoute   tools / skills / plugins
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                │
                              Latch
                                │
       ┌────────────────────────┼───────────────────────────┐
       │                        │                           │
   OSCAR Edge                Sunday                 Desktop / Workers
 ESP32 + RP2040              phone              Windows • macOS • agents
       │                                                    │
 sensors / GPIO                                      Codex • Computer Use
       │                                             apps • terminal • IDE
       └────────────── Kinetable / hardware workshop ───────┘
```

## Core capabilities

| Area | Planned capability |
|---|---|
| Natural interaction | Native voice and text, shared context, interruption/barge-in, concise proactive replies |
| Fast reflexes | Wake word, `mute`, `stop`, `cancel`, local device controls and safety paths bypass heavy models |
| Jev routing | Decide whether OSCAR already knows enough, should recall memory, inspect a source, act, reason, delegate or ask the user |
| Continuous memory | LRA + Supermemory: one persistent conversation/history rather than a sidebar of disconnected chats |
| Cloud intelligence | ChatGPT through Latch plus cloud models routed through SwitchRoute |
| Sunday | OSCAR's phone embodiment with phone context, actions, camera, sensors, notifications and biometric approval |
| Desktop | Native Windows and macOS presence with voice/text UI, screen/cursor context, overlays and access to machine capabilities |
| PC workers | Dynamic specialist nodes using Codex, Computer Use, terminal, browser, IDEs, Antigravity and other software |
| Physical world | ESP32/Pico sensors, GPIO, displays, actuators, workbench and environment integrations |
| Kinetable | Hardware design, simulation, firmware/provisioning and registration of new OSCAR-capable devices |
| Sentry | Always-on low-power awareness with local event detection and selective escalation to intelligence |
| Voice Match | User-specific speaker verification for personal commands; stronger confirmation for sensitive actions |
| Learning | First execution may explore; successful procedures are distilled into reusable procedural memory so repeated work gets faster |
| Skills & plugins | Portable `SKILL.md`-style skills, plugins/connectors and specialist capability discovery |
| Protocols & routines | Stateful JARVIS-like protocols, schedules, event triggers and long-running delegated responsibility |
| Self-extension | OSCAR may create/refine skills, routines and protocols while never granting itself new authority |
| Orchestration | Select the best model, app, project, plugin, agent, device or service for each objective rather than doing everything itself |
| Presence UI | OSCAR avatar with expression states; the yellow face moves inside the blue shell like a weighted joystick |
| Reliability | Graceful degradation: PC optional, cloud outages isolated, local safety remains deterministic |

## How OSCAR should work

A simple request should take the shortest valid path:

```text
"mute"                     → local reflex
"email John..."            → Jev → typed action
"what did we decide?"      → Jev → LRA/Supermemory recall
"fix this crash"           → delegate to Codex + verification
"build SceneLab landing"   → SceneLab context + Codex + Impeccable + browser verification
"design this Pico device"  → Kinetable + hardware toolchain
```

The rule is simple: **use the most suitable capability, not the most general model**.

OSCAR should also learn from successful execution:

```text
first time  → explore → execute → verify → distill procedure
next time   → retrieve skill → adapt → execute faster
later       → improve/version the skill from better outcomes
```

## Architecture principles

1. **One intelligence, many embodiments.** Desk hardware, Sunday, desktop apps, ChatGPT and workers are surfaces/nodes of OSCAR.
2. **One continuous relationship.** Voice/text/device switches do not create disconnected memory silos.
3. **Edge for immediacy; cloud for cognition.** Deterministic actions and safety stay local; heavy reasoning goes to ChatGPT/SwitchRoute.
4. **Use the best tool for the job.** OSCAR orchestrates specialists instead of cloning them poorly.
5. **Know when you do not know.** Jev should retrieve/verify missing context or ask the user rather than guess.
6. **Get faster with experience.** Successful work can become procedural memory, skills, routines or protocols.
7. **Perceived latency matters.** Acknowledge immediately, stream recognition/reasoning/TTS, and keep reflex commands off the network path.
8. **Proactive, not noisy.** Sentry scores importance, urgency, confidence and interruptibility before surfacing events.
9. **Permissioned autonomy.** Learned/generated workflows cannot self-grant permissions; critical actions require stronger approval.
10. **The PC is an accelerator, not a dependency.** Turning the laptop off must not turn OSCAR off.

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository foundation, product definition, architecture docs, brand assets and repository support | ✅ Complete |
| 01 | Edge runtime skeleton: ESP32 gateway + Pico deterministic controller + event model | ⏭️ Next |
| 02 | Reflex engine: local intents, command state, hardware-safe execution | Planned |
| 03 | Latch Edge: secure bidirectional OSCAR ↔ Latch transport and capability registry | Planned |
| 04 | Voice core: wake word, VAD, streaming STT/TTS, barge-in, latency instrumentation | Planned |
| 05 | OSCAR core router: Jev intent/epistemic routing, policy and task state | Planned |
| 06 | Cloud brains: ChatGPT wake/response path + SwitchRoute routing/fallbacks | Planned |
| 07 | Sunday: Android/mobile embodiment, notifications, phone actions and continuity | Planned |
| 08 | Desktop + workers: Windows/macOS apps, screen context, Codex, Computer Use, terminal/browser/IDE specialists | Planned |
| 09 | Memory/context: LRA + Supermemory, continuous history, retrieval policy and cross-device continuity | Planned |
| 10 | Sentry Mode: presence/environment/device events, anomaly handling and escalation | Planned |
| 11 | First-run commissioning: permissions, environment discovery, Voice Match and calibration | Planned |
| 12 | Avatar/presence UI: expression language, motion system and voice-state choreography | Planned |
| 13 | Learning layer: procedural memory, `SKILL.md`, plugins, generated skills/routines/protocols and versioning | Planned |
| 14 | Kinetable + environment/workbench: hardware design/provisioning, cameras, sensors, devices and physical actions | Planned |
| 15 | Reliability/security pass: audit, recovery, offline behavior, authorization and safety tests | Planned |
| 16 | Unified alpha: edge + Sunday + desktop + ChatGPT + SwitchRoute + memory + learning + Sentry end-to-end | Planned |

> **Current position:** Slice 00 is complete. Implementation begins with **Slice 01 — Edge runtime skeleton**.

## Documentation

- [Product vision](docs/PRODUCT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Feature inventory](docs/FEATURES.md)
- [Memory: LRA + Supermemory + Jev](docs/MEMORY.md)
- [Orchestration, learning, skills and protocols](docs/ORCHESTRATION.md)
- [Surfaces: Sunday, desktop and edge](docs/SURFACES.md)
- [Voice + Sentry](docs/VOICE-SENTRY.md)
- [First-time setup](docs/ONBOARDING.md)
- [Avatar + interaction language](docs/UI-AVATAR.md)
- [Security + permissions](docs/SECURITY.md)
- [Detailed roadmap](docs/ROADMAP.md)
- [Architecture decisions](docs/DECISIONS.md)

## Repository support

- [Contributing](CONTRIBUTING.md)
- [Coding-agent instructions](AGENTS.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- `.github/` — issue forms, PR template, CODEOWNERS and repository checks
- `.editorconfig`, `.gitattributes`, `.gitignore` — repository-wide development defaults

A project license has intentionally **not** been chosen yet. The repository should not silently adopt an open-source license without an explicit licensing decision.

## Development rule

Every implementation slice updates this README and the affected supporting docs in the **same change**: status, architecture decisions, completed features, limitations and next slice. Documentation is part of the slice definition of done.

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient agent. It is not affiliated with Marvel or the JARVIS trademark/character.</sub></p>
