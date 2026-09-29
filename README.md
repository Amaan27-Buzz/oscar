<p align="center">
  <img src="assets/brand/oscar-logo.png" width="180" alt="OSCAR logo" />
</p>

<h1 align="center">OSCAR</h1>

<p align="center"><strong>A persistent, multimodal, agentic intelligence spanning your phone, computers, communications, environment and physical hardware.</strong></p>

<p align="center">
  <code>Persistent</code> · <code>Omnipresent</code> · <code>Agentic</code> · <code>Immediate</code> · <code>Learning</code>
</p>

---

## What OSCAR is

OSCAR is an attempt to build a practical real-world interpretation of the *idea* behind JARVIS: not a chatbot with a voice and animated orb, but one intelligence that can perceive context, reason, communicate, use tools, delegate work, control software and hardware, keep working in the background, learn successful procedures, and appear through whatever device is available.

The laptop is **not** OSCAR's host. OSCAR remains available when the PC is off. The always-on edge runtime lives on low-power hardware; cloud intelligence supplies heavy cognition; connected devices become execution nodes.

**Sunday is OSCAR on the phone**, not a separate assistant.

OSCAR also avoids the conventional chat-sidebar model. LRA provides one continuous relationship/history underneath voice, text, Sunday, desktop, communications and other surfaces.

## System at a glance

```text
                              OSCAR
             identity • tasks • Personal Policy
                                │
                               Jev
                 intent + epistemic decisions
                                │
        ┌───────────────────────┼──────────────────────────┐
        │                       │                          │
   LRA + Supermemory       Intelligence              Orchestration
  continuity + recall   ChatGPT / SwitchRoute   tools / skills / Workers /
                                               plugins / protocols
        └───────────────────────┼──────────────────────────┘
                                │
                              Latch
                                │
       ┌────────────────────────┼───────────────────────────┐
       │                        │                           │
   OSCAR Edge                Sunday                 Desktop / machine nodes
 ESP32 + RP2040              phone              Windows • macOS • agents
       │                       │                            │
 sensors / GPIO       calls • apps • meetings       Codex • Computer Use
                      messages • dictation          apps • terminal • IDE
       └────────────── Kinetable / hardware workshop ───────┘
```

## Core capabilities

| Area | Planned capability |
|---|---|
| Natural interaction | Native voice and text, shared context, interruption/barge-in, concise proactive replies |
| Fast reflexes | Wake word, `mute`, `stop`, `cancel`, local device controls and safety paths bypass heavy models |
| Jev routing | Decide whether OSCAR already knows enough, should recall memory, inspect a source, act, reason, delegate, repair/reroute or ask the user |
| Continuous memory | LRA + Supermemory: one persistent conversation/history rather than a sidebar of disconnected chats |
| Personal Policy | Open-ended user preferences editable by voice/chat; distinct from memory and permissions; applicable to arbitrary contexts |
| Communication | Phone/app calls, messaging, meetings, dictation, transcription, notes and follow-up where platform support permits |
| AI call handling | Answer after user-defined conditions such as N rings; use schedule/context/relationships; take messages, offer callbacks and summarize |
| Cloud intelligence | ChatGPT through Latch plus cloud models routed through SwitchRoute |
| Sunday | OSCAR's phone embodiment with phone/app context, calls/messages, meetings, dictation, camera, sensors, notifications and biometric approval |
| Desktop | Native Windows and macOS presence with voice/text UI, dictation, meeting support, screen/cursor context, overlays and machine capabilities |
| Machine nodes | Dynamic capability-bearing computers using Codex, Computer Use, terminal, browser, IDEs, Antigravity and other software |
| Delegated Workers | Temporary or persistent sub-agents created by OSCAR to own objectives; use the real device/service mesh rather than mandatory cloud computers |
| Worker collaboration | Multiple Workers can run in parallel, hand work off, wait on dependencies and use shared Skills while OSCAR coordinates the goal |
| Social management | Optional scoped Worker for monitoring, drafting, replying, scheduling/publishing and release coordination within Personal Policy |
| Physical world | ESP32/Pico sensors, GPIO, displays, actuators, workbench and environment integrations |
| Kinetable | Hardware design, simulation, firmware/provisioning and registration of new OSCAR-capable devices |
| Sentry | Always-on low-power awareness with local event detection and selective escalation to intelligence |
| Voice Match | User-specific speaker verification for personal commands; stronger confirmation for sensitive actions |
| Learning | First execution may explore; successful procedures are distilled into reusable procedural memory so repeated work gets faster |
| Skills & plugins | Portable `SKILL.md`-style skills, plugins/connectors and specialist capability discovery |
| Protocols & routines | Stateful JARVIS-like protocols, schedules, event triggers and long-running delegated responsibility |
| Self-extension | OSCAR may create/refine Workers, skills, routines and protocols while never granting itself new authority |
| Orchestration | Select the best model, app, project, plugin, agent, device or service for each objective rather than doing everything itself |
| Presence UI | OSCAR avatar with expression states; the yellow face moves inside the blue shell like a weighted joystick |
| Reliability | Graceful degradation: PC optional, cloud outages isolated, local safety remains deterministic |

## How OSCAR should work

A simple request should take the shortest valid path:

```text
"mute"                       → local reflex
"email John..."              → Jev → typed action
"what did we decide?"        → Jev → LRA/Supermemory recall
"fix this crash"             → delegate to Codex + verification
"build SceneLab landing"     → SceneLab context + Codex + Impeccable + browser verification
"manage SceneLab socials"    → persistent Social Worker + Personal Policy
"answer calls after 4 rings" → Personal Policy + communication runtime
"type this in WhatsApp"      → Sunday/native input/app capability
"design this Pico device"    → Kinetable + hardware toolchain
```

The rule is simple: **use the most suitable capability, not the most general model**.

OSCAR should also learn from successful execution:

```text
first time  → explore → execute → verify → distill procedure
next time   → retrieve skill → adapt → execute faster
later       → improve/version the skill from better outcomes
```

## Workers

Workers are delegated sub-agents OSCAR creates for a job or ongoing responsibility.

```text
"Research these laptops"          → temporary Research Worker
"Watch ClearLane CI tonight"      → task Worker
"Manage SceneLab social media"    → persistent Social Worker
"Handle university scheduling"   → persistent Admin Worker
```

A Worker is not inherently another generic LLM and does not require its own cloud computer. It can use Sunday, a desktop machine node, Codex, Computer Use, APIs/plugins, ChatGPT/SwitchRoute, Kinetable or OSCAR Edge.

Workers self-repair/reroute safe recoverable failures through Jev before escalating to the user. They remain permission-scoped, inspectable and manageable through voice/chat or a simple UI.

See [`docs/WORKERS.md`](docs/WORKERS.md).

## Personal Policy

Preferences should be as easy to change as talking to OSCAR:

```text
"Don't answer family calls for me."
"If a recruiter calls while I'm in class, take a message."
"For university meetings, keep detailed notes."
"Never reveal calendar-event names, only free time."
"Let the SceneLab worker publish ordinary feature posts without asking."
```

OSCAR keeps **memory**, **preferences/policy**, **permissions** and **protocols** distinct. Learned patterns may suggest a new policy, but they do not silently become authority.

See [`docs/PERSONAL-POLICY.md`](docs/PERSONAL-POLICY.md).

## Communication

OSCAR should absorb the useful parts of dedicated call, meeting and dictation tools into one continuous system:

```text
calls / WhatsApp / Telegram / other apps
meetings / transcription / notes / follow-ups
system-wide dictation / rewrite / commands
messages / voice notes / scheduling
```

Integration preference is:

```text
native OS / official API
→ official plugin/connector
→ app automation on a paired device
→ computer-use/accessibility fallback
→ explicitly unsupported / ask user
```

OSCAR must never pretend a phone/app exposes a capability that it does not actually provide.

See [`docs/COMMUNICATION.md`](docs/COMMUNICATION.md).

## Design language — Quietly Alive

OSCAR uses a minimal, technical and tactile design language with character coming from **state, motion, timing and the avatar**, not generic AI decoration.

Directional blend:

- **60% restrained/native product design** — whitespace, hierarchy, clarity, finish;
- **20% tactile industrial character** — physical response, clear affordances, weighted motion;
- **10% friendly character/feedback** — expressive but credible;
- **10% functional honesty** — controls and state should explain themselves.

The blue-shell/yellow-face OSCAR avatar is the visual anchor. The yellow face moves inside the blue shell like a weighted puck/joystick and communicates attention and state. Sunday uses bright neutral surfaces, deep navy copy, restrained OSCAR blue, presence yellow and minimal red expression marks.

No generic AI dashboard, card wall, permanent chat sidebar, glassmorphism, neon HUD, purple AI gradient or fake telemetry.

See [`DESIGN.md`](DESIGN.md), [`TASTE.md`](TASTE.md) and [`docs/SUNDAY-DESIGN.md`](docs/SUNDAY-DESIGN.md).

## Engineering philosophy

OSCAR is meant to become a long-lived system across embedded hardware, mobile, desktop, cloud services and agent runtimes. The engineering rule is therefore:

> **Simple boundaries, strong contracts, boring reliability.**

In practice:

- prefer the smallest coherent solution over speculative future-proofing;
- build modules around clear responsibilities with high cohesion and low coupling;
- reuse proven shared behavior, not accidental code similarity;
- use typed/validated contracts and explicit state ownership across subsystem boundaries;
- isolate provider/platform details behind narrow adapters when a stable OSCAR contract is needed;
- design timeout, retry, reconnect, cancellation and failure states intentionally;
- keep dependencies justified and replaceable;
- test contracts and meaningful failure cases rather than implementation trivia;
- measure critical-path latency before adding optimization complexity;
- use least privilege and fail-safe defaults;
- prefer small reviewable/reversible changes over broad rewrites.

`ENGINEERING.md` is the canonical quality standard for both humans and coding agents.

## Architecture principles

1. **One intelligence, many embodiments.** Desk hardware, Sunday, desktop apps, ChatGPT and workers are surfaces/nodes of OSCAR.
2. **One continuous relationship.** Voice/text/device/communication switches do not create disconnected memory silos.
3. **Edge for immediacy; cloud for cognition.** Deterministic actions and safety stay local; heavy reasoning goes to ChatGPT/SwitchRoute.
4. **Use the best tool for the job.** OSCAR orchestrates specialists instead of cloning them poorly.
5. **Know when you do not know.** Jev should retrieve/verify missing context or ask the user rather than guess.
6. **Get faster with experience.** Successful work can become procedural memory, skills, routines or protocols.
7. **Perceived latency matters.** Acknowledge immediately, stream recognition/reasoning/TTS, and keep reflex commands off the network path.
8. **Proactive, not noisy.** Sentry scores importance, urgency, confidence and interruptibility before surfacing events.
9. **Permissioned autonomy.** Learned/generated workflows and Workers cannot self-grant permissions; critical actions require stronger approval.
10. **Personal Policy is first-class.** The user can state arbitrary durable behavioral preferences naturally; policy is distinct from memory and permission.
11. **Communication is integrated.** Calls, meetings, messaging and dictation use the same identity/context/policy system.
12. **The PC is an accelerator, not a dependency.** Turning the laptop off must not turn OSCAR off.

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository foundation, product/design/engineering definition, architecture docs, brand assets and coding-agent support | ✅ Complete |
| 01 | Edge runtime skeleton: ESP32 gateway + Pico deterministic controller + event model | ⏭️ Next |
| 02 | Reflex engine: local intents, command state, hardware-safe execution | Planned |
| 03 | Latch Edge: secure bidirectional OSCAR ↔ Latch transport and capability registry | Planned |
| 04 | Voice core: wake word, VAD, streaming STT/TTS, barge-in, latency instrumentation | Planned |
| 05 | OSCAR core router: Jev routing, Personal Policy hooks, capability selection and task state | Planned |
| 06 | Cloud brains: ChatGPT wake/response path + SwitchRoute routing/fallbacks | Planned |
| 07 | Sunday + communication: Android embodiment, phone/app actions, calls/messages, meetings, dictation and continuity | Planned |
| 08 | Desktop + machine nodes: Windows/macOS apps, screen context, dictation/meetings, Codex, Computer Use, terminal/browser/IDE specialists | Planned |
| 09 | Memory/context + Personal Policy: LRA + Supermemory, durable preferences, retrieval policy and cross-device continuity | Planned |
| 10 | Sentry Mode: presence/environment/device events, anomaly handling and escalation | Planned |
| 11 | First-run commissioning: permissions, preferences, communication defaults, environment discovery, Voice Match and calibration | Planned |
| 12 | Avatar/presence UI: expression language, motion system and voice-state choreography | Planned |
| 13 | Workers + learning: delegated sub-agents, procedural memory, `SKILL.md`, plugins, generated skills/routines/protocols and versioning | Planned |
| 14 | Kinetable + environment/workbench: hardware design/provisioning, cameras, sensors, devices and physical actions | Planned |
| 15 | Reliability/security pass: audit, recovery, offline behavior, authorization and safety tests | Planned |
| 16 | Unified alpha: edge + communication + Sunday + desktop + Workers + cloud + memory/policy + learning + Sentry end-to-end | Planned |

> **Current position:** Slice 00 is complete. Implementation begins with **Slice 01 — Edge runtime skeleton**.

## Documentation

- [Product vision](docs/PRODUCT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Feature inventory](docs/FEATURES.md)
- [Engineering standard](ENGINEERING.md)
- [Design system](DESIGN.md)
- [Design taste / quality bar](TASTE.md)
- [Sunday visual direction](docs/SUNDAY-DESIGN.md)
- [Memory: LRA + Supermemory + Jev](docs/MEMORY.md)
- [Personal Policy / preferences](docs/PERSONAL-POLICY.md)
- [Communication layer](docs/COMMUNICATION.md)
- [Delegated Workers](docs/WORKERS.md)
- [Orchestration, learning, skills and protocols](docs/ORCHESTRATION.md)
- [Surfaces: Sunday, desktop and edge](docs/SURFACES.md)
- [Voice + Sentry](docs/VOICE-SENTRY.md)
- [First-time setup](docs/ONBOARDING.md)
- [Avatar + interaction language](docs/UI-AVATAR.md)
- [Coding-agent context](docs/AGENT-CONTEXT.md)
- [Security + permissions](docs/SECURITY.md)
- [Detailed roadmap](docs/ROADMAP.md)
- [Architecture decisions](docs/DECISIONS.md)

## Repository support

- [Development guide](DEVELOPMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Engineering standard](ENGINEERING.md)
- [Canonical coding-agent instructions](AGENTS.md)
- [Claude Code adapter](CLAUDE.md)
- [Gemini CLI adapter](GEMINI.md)
- [Portable agent skills](skills/)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- `.github/` — Copilot instructions, path-specific instructions, issue forms, PR template, CODEOWNERS and repository checks
- `.cursor/rules/` — Cursor project rules
- `.editorconfig`, `.gitattributes`, `.gitignore` — repository-wide development defaults

A project license has intentionally **not** been chosen yet. The repository should not silently adopt an open-source license without an explicit licensing decision.

## Development rule

Every implementation slice updates this README and the affected supporting docs in the **same change**: status, architecture decisions, completed features, limitations and next slice. Documentation is part of the slice definition of done.

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient agent. It is not affiliated with Marvel or the JARVIS trademark/character.</sub></p>
