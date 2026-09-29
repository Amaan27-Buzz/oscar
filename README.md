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
                        User / Environment
                               │
                       Perception Fabric
                               │
                           World Model
                  "what is true right now?"
                               │
                              Jev
                 intent + epistemic decisions
                               │
       ┌───────────────────────┼────────────────────────┐
       │                       │                        │
  LRA + Supermemory       Intelligence            Live context
 continuity + recall   ChatGPT / SwitchRoute   authoritative sources
       └───────────────────────┼────────────────────────┘
                               │
                        OSCAR Executive
       Personal Policy • Executive Planner • Workers • Protocols
                               │
                         Action Ledger
                               │
                             Latch
                               │
      ┌────────────────────────┼──────────────────────────┐
      │                        │                          │
  OSCAR Edge                Sunday                Desktop / machine nodes
ESP32 + RP2040              phone             Windows • macOS • agents
      │                       │                           │
sensors / GPIO       calls • apps • meetings      Codex • Computer Use
                     messages • dictation         apps • terminal • IDE
      └──────────── Kinetable + specialist engineering ──┘
```

## Core capabilities

| Area | Planned capability |
|---|---|
| Natural interaction | Native voice and text, shared context, interruption/barge-in, concise proactive replies |
| Interaction Runtime | `Dictate / Edit / Ask / Act`, selected-text editing, cursor/focus context, point-and-talk and system-wide insertion |
| Fast reflexes | Wake word, `mute`, `stop`, `cancel`, local device controls and safety paths bypass heavy models |
| Multi-device voice | Sunday, desktop and physical OSCAR arbitrate one owning voice surface per turn |
| Jev routing | Decide whether OSCAR already knows enough, should use current World Model state, recall memory, inspect a source, act, reason, delegate, repair/reroute or ask |
| World Model | Live graph of people, places, devices, apps, projects, objects, tasks and relationships with freshness/provenance |
| Perception Fabric | Screen/accessibility state, cursor/selection, cameras, audio events, apps, devices, location and sensors feed one current-state layer |
| Live context/search | Federated current-source retrieval across connected files, mail, messages, notes, browser, GitHub, calendar, devices and services |
| Continuous memory | LRA + Supermemory: one persistent conversation/history rather than a sidebar of disconnected chats |
| Entity graph | Canonical people/contact/account/company/device/project identities resolved across systems |
| Personal Policy | Open-ended user preferences editable by voice/chat; distinct from memory and permissions; applicable to arbitrary contexts |
| Communication | Phone/app calls, messaging, meetings, dictation, transcription, notes and follow-up where platform support permits |
| AI call handling | Answer after user-defined conditions such as N rings; use schedule/context/relationships; take messages, offer callbacks and summarize |
| Executive Planner | Prioritize and schedule Workers/Protocols across deadlines, dependencies, devices, cost, risk and user interruptibility |
| Action Ledger + Undo | Consequential actions are attributable and expose a real compensating/undo action wherever the capability supports one |
| Cloud intelligence | ChatGPT through Latch plus cloud models routed through SwitchRoute |
| Sunday | OSCAR's phone embodiment with phone/app context, calls/messages, meetings, dictation, camera, sensors, notifications and biometric approval |
| Desktop | Native Windows/macOS presence with VoiceOS-grade interaction, screen/cursor context, overlays and machine capabilities |
| Machine nodes | Dynamic capability-bearing computers using Codex, Computer Use, terminal, browser, IDEs, Antigravity and other software |
| Delegated Workers | Temporary or persistent sub-agents created by OSCAR to own objectives; use the real device/service mesh rather than mandatory cloud computers |
| Worker collaboration | Multiple Workers can run in parallel, hand work off, wait on dependencies and use shared Skills while OSCAR coordinates the goal |
| Social management | Optional scoped Worker for monitoring, drafting, replying, scheduling/publishing and release coordination within Personal Policy |
| Teach by demonstration | “Watch me do this once” can become a verified, permission-scoped Skill where platform observation supports it |
| Predictive intelligence | Forecast schedule/task/device risk and prepare before failure rather than only reacting after events |
| Physical world | ESP32/Pico sensors, GPIO, displays, actuators, workbench and environment integrations |
| Kinetable + engineering | Hardware design/provisioning plus routing to CAD, 3D, numerical/simulation/diagnostic specialists when suitable |
| Sentry | Always-on low-power awareness with local event detection and selective escalation to intelligence |
| Voice Match | User-specific speaker verification for personal commands; stronger confirmation for sensitive actions |
| Learning | Successful procedures are distilled into reusable procedural memory so repeated work gets faster |
| Skills & plugins | Portable `SKILL.md`-style skills, plugins/connectors and specialist capability discovery |
| Protocols & routines | Stateful JARVIS-like protocols, schedules, event triggers and long-running delegated responsibility |
| Self-extension | OSCAR may create/refine Workers, Skills, routines and Protocols while never granting itself new authority |
| Self-maintenance | Detect broken auth/connectors/nodes/providers, repair or roll back safe failures, and ask only when intervention is truly needed |
| Reliability | Graceful degradation: PC optional, cloud outages isolated, local safety remains deterministic |

## How OSCAR should work

A simple request should take the shortest valid path:

```text
"mute"                         → local reflex
"what is this?"                → cursor + accessibility + visual context
"email John..."                → Jev → typed action
"what did we decide?"          → Jev → LRA/Supermemory recall
"what is running at home?"     → Jev → live World Model/source state
"undo that"                    → Action Ledger → real compensating action if supported
"fix this crash"               → delegate to Codex + verification
"build SceneLab landing"       → SceneLab context + Codex + Impeccable + browser verification
"manage SceneLab socials"      → persistent Social Worker + Personal Policy
"answer calls after 4 rings"   → Personal Policy + communication runtime
"type this in WhatsApp"        → Sunday/native input/app capability
"design this Pico device"      → Kinetable + hardware toolchain
```

The rule is simple: **use the most suitable capability, not the most general model**.

## The JARVIS gap

OSCAR already has many pieces of the target system. The remaining architectural challenge is making them behave like **one intelligence**.

The current system-level priorities are:

> **World Model → Perception Fabric → Executive Planner → Action Ledger/Undo → VoiceOS-grade Interaction Runtime**

This means OSCAR should not just know that a calendar event, PC build, phone location, incoming call and desk sensor exist independently. It should understand one coherent situation and choose the right action using current evidence, memory, Personal Policy and permissions.

See [`docs/JARVIS-GAP-REVIEW.md`](docs/JARVIS-GAP-REVIEW.md).

## Workers

Workers are delegated sub-agents OSCAR creates for a job or ongoing responsibility.

```text
"Research these laptops"          → temporary Research Worker
"Watch ClearLane CI tonight"      → task Worker
"Manage SceneLab social media"    → persistent Social Worker
"Handle university scheduling"   → persistent Admin Worker
```

A Worker is not inherently another generic LLM and does not require its own cloud computer. It can use Sunday, a desktop machine node, Codex, Computer Use, APIs/plugins, ChatGPT/SwitchRoute, Kinetable or OSCAR Edge.

Workers self-repair/reroute safe recoverable failures through Jev before escalating to the user. The Executive Planner coordinates Workers when several objectives compete for the same devices, tools or user attention.

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

OSCAR keeps **memory**, **preferences/policy**, **permissions** and **Protocols** distinct. Learned patterns may suggest a new policy, but they do not silently become authority.

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

The blue-shell/yellow-face OSCAR avatar is the visual anchor. The yellow face moves inside the blue shell like a weighted puck/joystick and communicates attention and state.

No generic AI dashboard, card wall, permanent chat sidebar, glassmorphism, neon HUD, purple AI gradient or fake telemetry.

See [`DESIGN.md`](DESIGN.md), [`TASTE.md`](TASTE.md) and [`docs/SUNDAY-DESIGN.md`](docs/SUNDAY-DESIGN.md).

## Engineering philosophy

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

See [`ENGINEERING.md`](ENGINEERING.md).

## Architecture principles

1. **One intelligence, many embodiments.** Desk hardware, Sunday, desktop apps, ChatGPT and Workers are surfaces/nodes of OSCAR.
2. **One continuous relationship.** Voice/text/device/communication switches do not create disconnected memory silos.
3. **Current truth is explicit.** The World Model + live sources represent what is true now; memory represents continuity/history.
4. **Edge for immediacy; cloud for cognition.** Deterministic actions and safety stay local; heavy reasoning goes to ChatGPT/SwitchRoute.
5. **Use the best tool for the job.** OSCAR orchestrates specialists instead of cloning them poorly.
6. **Know when you do not know.** Jev retrieves/validates current or historical context rather than guessing.
7. **One executive, many Workers.** The Executive Planner coordinates competing objectives so the user does not manage a swarm manually.
8. **Actions are accountable.** Consequential changes enter the Action Ledger and expose truthful undo/compensation where supported.
9. **Get faster with experience.** Successful work can become procedural memory, Skills, routines or Protocols.
10. **Perceived latency matters.** Acknowledge immediately, stream recognition/reasoning/TTS, and keep reflex commands off the network path.
11. **Proactive, not noisy.** Sentry scores importance, urgency, confidence and interruptibility before surfacing events.
12. **Permissioned autonomy.** Learned/generated workflows and Workers cannot self-grant permissions; critical actions require stronger approval.
13. **Personal Policy is first-class.** Arbitrary durable behavioral preferences can be stated naturally and remain distinct from memory/permission.
14. **Communication is integrated.** Calls, meetings, messaging and dictation use the same identity/context/policy system.
15. **The PC is an accelerator, not a dependency.** Turning the laptop off must not turn OSCAR off.

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository foundation, product/design/engineering definition, JARVIS/VoiceOS benchmark, architecture docs and coding-agent support | ✅ Complete |
| 01 | Edge runtime skeleton: ESP32 gateway + Pico deterministic controller + event model | ⏭️ Next |
| 02 | Reflex engine: local intents, command state, hardware-safe execution | Planned |
| 03 | Latch Edge: secure transport and capability registry | Planned |
| 04 | Voice core + multi-device voice arbitration | Planned |
| 05 | OSCAR core/Jev + Personal Policy hooks + Action Ledger/Undo foundation | Planned |
| 06 | Cloud brains: ChatGPT path + SwitchRoute routing/fallbacks | Planned |
| 07 | Sunday + communication: real phone/app/call/meeting capability boundaries | Planned |
| 08 | Desktop + VoiceOS-grade Interaction Runtime + machine nodes | Planned |
| 09 | LRA/Supermemory + Personal Policy + live context/search + canonical entity graph | Planned |
| 10 | World Model + Perception Fabric + Sentry/predictive intelligence | Planned |
| 11 | First-run commissioning + Voice Match + autonomy preferences | Planned |
| 12 | Avatar/presence UI and voice-state choreography | Planned |
| 13 | Executive Planner + Workers + learning + teach-by-demonstration + Skills/Protocols | Planned |
| 14 | Kinetable + spatial/workbench perception + general engineering/simulation routing | Planned |
| 15 | Self-maintenance + reliability/security + Action Ledger integrity | Planned |
| 16 | Unified alpha: all layers operating as one coherent OSCAR system | Planned |

> **Current position:** Slice 00 is complete. Implementation begins with **Slice 01 — Edge runtime skeleton**.

## Documentation

- [Product vision](docs/PRODUCT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [JARVIS / VoiceOS gap review](docs/JARVIS-GAP-REVIEW.md)
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
