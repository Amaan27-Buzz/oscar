<p align="center">
  <img src="assets/brand/oscar-logo.png" width="180" alt="OSCAR logo" />
</p>

<h1 align="center">OSCAR</h1>

<p align="center"><strong>A persistent, multimodal, agentic intelligence that spans your phone, computers, environment and physical hardware.</strong></p>

<p align="center">
  <code>Persistent</code> · <code>Omnipresent</code> · <code>Agentic</code> · <code>Immediate</code>
</p>

---

## What OSCAR is

OSCAR is an attempt to build a practical real-world interpretation of the *idea* behind JARVIS: not a chatbot wearing a voice and an animated orb, but one intelligence that can perceive context, reason, use tools, delegate work, control software and hardware, keep working in the background, and appear through whatever device is available.

The laptop is **not** OSCAR's host. OSCAR remains available when the PC is off. The always-on edge runtime lives on low-power hardware; cloud intelligence supplies the heavy reasoning; connected devices become execution nodes.

**Sunday is OSCAR on the phone**, not a separate assistant.

## System at a glance

```text
                         ┌───────────────┐
                         │     OSCAR     │
                         │ core + policy │
                         └───────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
        ChatGPT / Latch     SwitchRoute        Memory / LRA
        reasoning + tools   cloud models       + Supermemory
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                              Latch
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
      OSCAR Edge             Sunday               PC Worker
    ESP32 + RP2040            phone          Codex / Computer Use /
   sensors + control       mobile presence    Antigravity / apps
```

## Core capabilities

| Area | Planned capability |
|---|---|
| Natural interaction | Native voice and text, conversational context, interruption/barge-in, concise proactive replies |
| Fast reflexes | Wake word, `mute`, `stop`, `cancel`, local device controls and safety paths bypass the LLM |
| Cloud intelligence | ChatGPT through Latch plus cloud models routed through SwitchRoute |
| Mobile | Sunday: OSCAR's phone embodiment with phone context, actions, camera, sensors and notifications |
| Computer work | Optional PC worker that can use Codex, computer use, terminals, browsers, IDEs, Antigravity and specialist software |
| Physical world | ESP32/Pico sensors, GPIO, displays, actuators, workbench and future environment integrations |
| Sentry | Always-on low-power awareness with local event detection and selective escalation to cloud intelligence |
| Voice Match | User-specific speaker verification for personal commands; stronger confirmation for sensitive actions |
| Memory | Long-term retrieval through LRA/Supermemory with context-aware retrieval decisions |
| Skills & protocols | Reusable routines, `SKILL.md`-style skills, plugins and user-approved protocols; OSCAR may propose/create new reusable workflows |
| Delegation | Select the best model, device, app or agent for a task rather than trying to do everything itself |
| Presence UI | OSCAR avatar with expression states; the yellow face moves inside the blue shell like a weighted joystick |
| Reliability | Graceful degradation: PC optional, cloud outages isolated, local safety remains deterministic |

## Architecture principles

1. **One intelligence, many embodiments.** Desk hardware, Sunday, ChatGPT and PCs are surfaces/nodes of OSCAR.
2. **Edge for immediacy; cloud for cognition.** Deterministic actions and safety stay local. Heavy reasoning goes to ChatGPT/SwitchRoute.
3. **Use the best tool for the job.** OSCAR should delegate to Codex, computer use, apps, models or hardware rather than forcing a general model through unsuitable work.
4. **Perceived latency matters.** Acknowledge immediately, stream recognition/reasoning/TTS, and keep reflex commands off the network path.
5. **Proactive, not noisy.** Sentry scores importance, urgency, confidence and interruptibility before surfacing events.
6. **Permissioned autonomy.** Voice Match improves convenience but is not treated as cryptographic authentication.
7. **The PC is an accelerator, not a dependency.** Turning the laptop off must not turn OSCAR off.

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository foundation, product definition, architecture docs, brand assets | ✅ Complete |
| 01 | Edge runtime skeleton: ESP32 gateway + Pico deterministic controller + event model | ⏭️ Next |
| 02 | Reflex engine: local intents, command state, hardware-safe execution | Planned |
| 03 | Latch Edge: secure bidirectional OSCAR ↔ Latch transport and device capability registry | Planned |
| 04 | Voice core: wake word, VAD, streaming STT/TTS, barge-in, latency instrumentation | Planned |
| 05 | OSCAR core router: intent/epistemic routing, policy, task state, Jev integration | Planned |
| 06 | Cloud brains: ChatGPT wake/response path + SwitchRoute model routing/fallbacks | Planned |
| 07 | Sunday: Android/mobile embodiment, notifications, phone actions and continuity | Planned |
| 08 | PC Worker: dynamic capabilities + Codex, computer use, terminal, browser, IDE and specialist apps | Planned |
| 09 | Memory/context: LRA + Supermemory, retrieval policy and cross-device continuity | Planned |
| 10 | Sentry Mode: presence/environment/device events, anomaly handling and escalation | Planned |
| 11 | First-run commissioning: permissions, environment discovery, Voice Match and calibration | Planned |
| 12 | Avatar/presence UI: expression language, motion system and voice-state choreography | Planned |
| 13 | Protocols, routines, skills and plugins: reusable + safely generated workflows | Planned |
| 14 | Environment/workbench integration: cameras, sensors, devices and physical actions | Planned |
| 15 | Reliability/security pass: audit, recovery, offline behavior, authorization and safety tests | Planned |
| 16 | Unified alpha: edge + Sunday + ChatGPT + SwitchRoute + PC worker end-to-end | Planned |

> **Current position:** Slice 00 is complete. Implementation begins with **Slice 01 — Edge runtime skeleton**.

## Documentation

- [Product vision](docs/PRODUCT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Feature inventory](docs/FEATURES.md)
- [Voice + Sentry](docs/VOICE-SENTRY.md)
- [First-time setup](docs/ONBOARDING.md)
- [Avatar + interaction language](docs/UI-AVATAR.md)
- [Security + permissions](docs/SECURITY.md)
- [Detailed roadmap](docs/ROADMAP.md)
- [Architecture decisions](docs/DECISIONS.md)

## Development rule

Every implementation slice should update this README and the affected supporting docs in the **same change**: status, architecture decisions, completed features, limitations and the next slice. Documentation is part of the slice's definition of done.

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient agent. It is not affiliated with Marvel or the JARVIS trademark/character.</sub></p>
