<p align="center">
  <img src="assets/brand/oscar-logo.png" width="180" alt="OSCAR logo" />
</p>

<h1 align="center">OSCAR</h1>

<p align="center"><strong>A persistent, multimodal, agentic intelligence spanning your phone, computers, communications, environment and physical hardware.</strong></p>

<p align="center">
  <code>Persistent</code> · <code>Omnipresent</code> · <code>Agentic</code> · <code>Immediate</code> · <code>Learning</code> · <code>Evidence-backed</code>
</p>

---

## What OSCAR is

OSCAR is an attempt to build a practical real-world interpretation of the *idea* behind JARVIS: not a chatbot with a voice and animated orb, but one intelligence that can perceive context, reason, communicate, use tools, delegate work, control software and hardware, keep working in the background, learn successful procedures, and appear through whatever device is available.

The laptop is **not** OSCAR's host. OSCAR remains available when the PC is off. The always-on edge runtime lives on low-power hardware; cloud intelligence supplies heavy cognition; connected devices become execution nodes.

**Sunday is OSCAR on the phone**, not a separate assistant.

OSCAR avoids the conventional chat-sidebar model. LRA provides one continuous relationship/history underneath voice, text, Sunday, desktop, communications and other surfaces.

And OSCAR has one non-negotiable truth rule:

> **Know what you know, know why you know it, verify what can be verified, and never claim more than the evidence supports.**

A tool, Worker or model saying `success` is not automatically proof that the user's objective is complete.

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
      Personal Policy • Executive Planner • objectives
                               │
                  Durable Execution Runtime
       tasks • checkpoints • leases • retries • recovery
                               │
                 Capability Catalog + Tool Search
                               │
             Workers • Skills • Protocols • Channels
                               │
       Actions / Devices / APIs / Specialists / Kinetable
                               │
              ┌────────────────┴────────────────┐
              │                                 │
        Action Ledger                  Artifact / Result Model
              └────────────────┬────────────────┘
                               │
                           Verification
                               │
                World Model / Memory update
                               │
                    evidence-backed report
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
| Natural interaction | Native voice and text, shared context, interruption/barge-in and concise proactive replies |
| Interaction Runtime | `Dictate / Edit / Ask / Act`, selected-text editing, cursor/focus context, point-and-talk and system-wide insertion |
| Fast reflexes | Wake word, `mute`, `stop`, `cancel`, local device controls and safety paths bypass heavy models |
| Multi-device voice | Sunday, desktop and physical OSCAR arbitrate one owning voice surface per turn |
| Epistemic Integrity | Distinguish known/inferred/recalled/reported/verified/unknown; never claim completion beyond evidence |
| Jev routing | Decide whether OSCAR already knows enough, should use World Model state, recall memory, inspect a source, act, reason, delegate, repair/reroute or ask |
| World Model | Live graph of people, places, devices, apps, projects, objects, tasks and relationships with freshness/provenance |
| Perception Fabric | Screens, accessibility state, cursor/selection, cameras, audio events, apps, devices, location and sensors feed one current-state layer |
| Live context/search | Federated retrieval across connected files, mail, messages, notes, browser, GitHub, calendar, devices and services |
| Continuous memory | LRA + Supermemory: one persistent conversation/history rather than disconnected chats |
| Entity graph | Canonical people/contact/account/company/device/project identities resolved across systems |
| Personal Policy | Open-ended user preferences editable by voice/chat; distinct from memory and permissions |
| Executive Planner | Prioritize and schedule Workers/Protocols across deadlines, dependencies, devices, cost, risk and interruptibility |
| Durable Execution Runtime | Long-running task state, checkpoints, leases, heartbeats, reclaim, bounded retries and crash resume |
| Capability Catalog + Tool Search | Search lightweight capability manifests and progressively load only relevant detailed contracts |
| Communication | Phone/app calls, messaging, meetings, dictation, transcription, notes and follow-up where platform support permits |
| Universal Channel Gateway | One normalized inbound/outbound abstraction across supported messaging/email/social channels without hiding platform limits |
| AI call handling | Answer after user-defined conditions such as N rings; use schedule/context/relationships; take messages, offer callbacks and summarize |
| Action Ledger + Undo | Consequential actions are attributable, evidence-aware and expose real compensation/undo only where supported |
| Artifact / Result Model | Finished docs, code, reports, media, deployments and other outputs become typed durable objects with provenance/version/verification |
| Cloud intelligence | ChatGPT through Latch plus cloud models routed through SwitchRoute |
| Sunday | OSCAR's phone embodiment with phone/app context, calls/messages, meetings, dictation, camera, sensors, notifications and biometric approval |
| Desktop | Native Windows/macOS presence with VoiceOS-grade interaction, screen/cursor context, overlays and machine capabilities |
| Machine nodes | Dynamic capability-bearing computers using Codex, Computer Use, terminal, browser, IDEs and other software |
| Delegated Workers | Temporary or persistent sub-agents created by OSCAR to own objectives; use the real device/service mesh rather than mandatory cloud computers |
| Worker collaboration | Multiple Workers can run in parallel, hand work off, wait on dependencies and use shared Skills while OSCAR coordinates the goal |
| Social management | Optional scoped Worker for monitoring, drafting, replying, scheduling/publishing and release coordination within Personal Policy |
| Teach by demonstration | “Watch me do this once” can become a verified, permission-scoped Skill where platform observation supports it |
| Learned Automation Evaluation | Candidate → replay/evaluate → compare → safety/permission review → promote/reject/rollback |
| Predictive intelligence | Forecast schedule/task/device risk and prepare before failure rather than only reacting afterward |
| Physical world | ESP32/Pico sensors, GPIO, displays, actuators, workbench and environment integrations |
| Kinetable + engineering | Hardware design/provisioning plus routing to CAD, 3D, numerical/simulation/diagnostic specialists when suitable |
| Sentry | Always-on low-power awareness with local event detection and selective escalation to intelligence |
| Voice Match | User-specific speaker verification for personal commands; stronger confirmation for sensitive actions |
| Learning | Successful procedures are distilled into reusable procedural memory so repeated work gets faster |
| Skills & plugins | Portable `SKILL.md`-style Skills, plugins/connectors and specialist capability discovery |
| Protocols & routines | Stateful JARVIS-like Protocols, schedules, event triggers and long-running delegated responsibility |
| Self-extension | OSCAR may create/refine Workers, Skills, routines and Protocols while never granting itself new authority |
| Self-maintenance | Detect broken auth/connectors/nodes/providers, repair or roll back safe failures, and ask only when intervention is truly needed |
| Reliability | Graceful degradation: PC optional, cloud outages isolated, local safety deterministic |

## How OSCAR should work

A simple request should take the shortest valid path:

```text
"mute"                         → local reflex
"what is this?"                → cursor + accessibility + visual context
"email John..."                → Jev → typed action
"what did we decide?"          → Jev → LRA/Supermemory recall
"what is running at home?"     → Jev → live World Model/source state
"undo that"                    → Action Ledger → real compensation if supported
"fix this crash"               → Codex → tests → verification → report
"build SceneLab landing"       → SceneLab + Codex + Impeccable + browser verification
"manage SceneLab socials"      → persistent Social Worker + Personal Policy
"answer calls after 4 rings"   → Personal Policy + communication runtime
"type this in WhatsApp"        → Sunday/channel/app capability
"design this Pico device"      → Kinetable + hardware toolchain
```

The routing rule is simple:

> **Use the most suitable capability, not the most general model.**

The reporting rule is just as important:

```text
planned
→ executing
→ result received
→ verifying
→ verified / partially verified / failed / blocked / unknown
```

Only the evidence-backed state should reach the user as the final claim.

## The competitive architecture benchmark

The current design has been reviewed against VoiceOS, MCU JARVIS, ChatGPT, Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi.

The final system-level additions from that review are:

> **World Model → Perception Fabric → Executive Planner → Durable Execution Runtime → Capability Search → Channel Gateway → Action Ledger + Artifact Model → Verification**

These sit alongside the existing Jev, LRA/Supermemory, Personal Policy, Workers, Protocols, Sunday, Latch, SwitchRoute, Edge and Kinetable layers.

The point is not to collect competitor features. The point is to make OSCAR behave like **one intelligence** while keeping the core small and specialist-first.

See:

- [`docs/JARVIS-GAP-REVIEW.md`](docs/JARVIS-GAP-REVIEW.md)
- [`docs/COMPETITIVE-BENCHMARK.md`](docs/COMPETITIVE-BENCHMARK.md)
- [`docs/RUNTIME-FOUNDATIONS.md`](docs/RUNTIME-FOUNDATIONS.md)
- [`docs/EPISTEMIC-INTEGRITY.md`](docs/EPISTEMIC-INTEGRITY.md)

## Workers

Workers are delegated sub-agents OSCAR creates for a job or ongoing responsibility.

```text
"Research these laptops"          → temporary Research Worker
"Watch ClearLane CI tonight"      → task Worker
"Manage SceneLab social media"    → persistent Social Worker
"Handle university scheduling"   → persistent Admin Worker
```

A Worker is not inherently another generic LLM and does not require its own cloud computer. It can use Sunday, a desktop machine node, Codex, Computer Use, APIs/plugins, ChatGPT/SwitchRoute, Kinetable or OSCAR Edge.

Workers self-repair/reroute safe recoverable failures through Jev before escalating. The Executive Planner coordinates competing objectives; the Durable Execution Runtime keeps long-running work recoverable; and OSCAR independently verifies completion where practical.

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

The Universal Channel Gateway normalizes supported inbound/outbound communication while preserving per-platform capability limits.

OSCAR must never pretend a phone/app exposes a capability that it does not actually provide.

See [`docs/COMMUNICATION.md`](docs/COMMUNICATION.md) and [`docs/RUNTIME-FOUNDATIONS.md`](docs/RUNTIME-FOUNDATIONS.md).

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
- use typed/validated contracts and explicit state ownership;
- isolate provider/platform details behind narrow adapters where a stable OSCAR contract is needed;
- design timeout/retry/reconnect/cancellation/recovery intentionally;
- keep dependencies justified and replaceable;
- test contracts and meaningful failure cases;
- verify outcomes rather than trusting executor reports;
- measure critical-path latency before adding optimization complexity;
- use least privilege and fail-safe defaults;
- prefer small reviewable/reversible changes over broad rewrites.

See [`ENGINEERING.md`](ENGINEERING.md).

## Architecture principles

1. **One intelligence, many embodiments.** Desk hardware, Sunday, desktop apps, ChatGPT and Workers are surfaces/nodes of OSCAR.
2. **One continuous relationship.** Voice/text/device/communication switches do not create disconnected memory silos.
3. **Current truth is explicit.** The World Model + live sources represent what is true now; memory represents continuity/history.
4. **Evidence before claims.** Reported success is not verified completion; user-facing claims cannot exceed evidence.
5. **Edge for immediacy; cloud for cognition.** Deterministic actions and safety stay local; heavy reasoning goes to ChatGPT/SwitchRoute.
6. **Use the best tool for the job.** OSCAR orchestrates specialists instead of cloning them poorly.
7. **Know when you do not know.** Jev retrieves/verifies current or historical context rather than guessing.
8. **One executive, many Workers.** The Executive Planner coordinates competing objectives so the user does not manage a swarm manually.
9. **Long-running work is durable.** Checkpoints, leases, recovery and bounded retries prevent zombie/stuck tasks.
10. **Capabilities are discovered progressively.** Search lightweight manifests; do not dump every tool into model context.
11. **Actions are accountable.** Consequential changes enter the Action Ledger and expose truthful undo only where supported.
12. **Artifacts are first-class.** Finished outputs carry provenance, version and verification state.
13. **Learning is evaluated.** Generated automation is tested/promoted deliberately rather than trusted after one success.
14. **Perceived latency matters.** Acknowledge immediately, stream recognition/reasoning/TTS, and keep reflex commands off the network path.
15. **Proactive, not noisy.** Sentry scores importance, urgency, confidence and interruptibility before surfacing events.
16. **Permissioned autonomy.** Learned/generated workflows and Workers cannot self-grant permissions; critical actions require stronger approval.
17. **Personal Policy is first-class.** Arbitrary durable behavioral preferences can be stated naturally and remain distinct from memory/permission.
18. **Communication is integrated.** Calls, meetings, messaging and dictation use the same identity/context/policy system.
19. **The PC is an accelerator, not a dependency.** Turning the laptop off must not turn OSCAR off.
20. **No yes-man behavior.** User confidence does not override evidence, constraints or safety.

## Implementation strategy

OSCAR is built **core-loop first**, not hardware-first. The early implementation may run on a development computer, but the contracts cannot assume that computer permanently hosts OSCAR.

The first thing to prove is:

```text
objective
→ choose capability
→ execute
→ observe result
→ verify independently where practical
→ record action/artifact
→ report only what the evidence supports
```

Once that nervous system works, cloud intelligence, machine Workers, memory, Edge hardware, voice, Sunday and perception attach to the same contracts.

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository foundation, final competitive architecture, Epistemic Integrity, runtime primitives and coding-agent support | ✅ Complete |
| 01 | OSCAR Core Loop: typed task/capability/action/result/evidence contracts + verification + ledger/artifact foundations | ⏭️ Next |
| 02 | TypeSafe Jev: intent + epistemic routing over the proven Core Loop | Planned |
| 03 | Latch + Capability Catalog: external nodes, capability advertisement/search and progressive contract loading | Planned |
| 04 | Cloud intelligence: ChatGPT path + SwitchRoute routing/fallbacks | Planned |
| 05 | First real machine Worker: Windows node + terminal/files/Git/Codex/browser + independent verification | Planned |
| 06 | LRA/Supermemory + Personal Policy + live context/search + initial entity graph | Planned |
| 07 | OSCAR Edge + reflexes: ESP32 gateway + Pico deterministic controller + Latch Edge + hardware safety | Planned |
| 08 | Voice core + multi-device voice arbitration | Planned |
| 09 | Sunday + communication + Universal Channel Gateway | Planned |
| 10 | Desktop VoiceOS-grade `Dictate / Edit / Ask / Act` Interaction Runtime | Planned |
| 11 | World Model + Perception Fabric + Sentry/predictive intelligence | Planned |
| 12 | First-run commissioning + Voice Match + autonomy preferences | Planned |
| 13 | Avatar/presence UI with truthful Working/Verifying/Blocked/Done states | Planned |
| 14 | Executive Planner + durable Workers + capability search + learning/evaluation + Skills/Protocols | Planned |
| 15 | Kinetable + spatial/workbench perception + general engineering/simulation routing | Planned |
| 16 | Self-maintenance + reliability/security + truthfulness/verification pass | Planned |
| 17 | Unified alpha: all layers operating as one coherent, evidence-backed OSCAR system | Planned |

> **Current position:** Slice 00 is complete. Implementation begins with **Slice 01 — OSCAR Core Loop**.

## Documentation

- [Product vision](docs/PRODUCT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [JARVIS / VoiceOS gap review](docs/JARVIS-GAP-REVIEW.md)
- [Final competitive benchmark](docs/COMPETITIVE-BENCHMARK.md)
- [Runtime foundations](docs/RUNTIME-FOUNDATIONS.md)
- [Epistemic Integrity](docs/EPISTEMIC-INTEGRITY.md)
- [Feature inventory](docs/FEATURES.md)
- [Engineering standard](ENGINEERING.md)
- [Design system](DESIGN.md)
- [Design taste / quality bar](TASTE.md)
- [Sunday visual direction](docs/SUNDAY-DESIGN.md)
- [Memory: LRA + Supermemory + Jev](docs/MEMORY.md)
- [Personal Policy / preferences](docs/PERSONAL-POLICY.md)
- [Communication layer](docs/COMMUNICATION.md)
- [Delegated Workers](docs/WORKERS.md)
- [Orchestration, learning, Skills and Protocols](docs/ORCHESTRATION.md)
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
- [Portable agent Skills](skills/)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- `.github/` — Copilot instructions, path-specific instructions, issue forms, PR template, CODEOWNERS and repository checks
- `.cursor/rules/` — Cursor project rules
- `.editorconfig`, `.gitattributes`, `.gitignore` — repository-wide development defaults

A project license has intentionally **not** been chosen yet. The repository should not silently adopt an open-source license without an explicit licensing decision.

## Development rule

Every implementation slice updates this README and the affected supporting docs in the **same change**: status, architecture decisions, completed features, limitations, verification evidence and next slice. Documentation is part of the slice definition of done.

A slice is not complete because an agent says it is complete. The exit condition must be verified against repository/runtime/device evidence wherever verification is possible.

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient agent.</sub></p>