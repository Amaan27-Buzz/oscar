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

The laptop is **not** OSCAR's host. OSCAR remains available when the PC is off. Connected computers become optional execution nodes; low-power Edge hardware eventually provides persistent local presence/safety; cloud intelligence supplies heavy cognition.

**Sunday is OSCAR on the phone**, not a separate assistant.

OSCAR avoids the conventional chat-sidebar model. LRA provides one continuous relationship/history underneath voice, text, Sunday, desktop, communications and other surfaces.

OSCAR also has one non-negotiable truth rule:

> **Know what you know, know why you know it, verify what can be verified, and never claim more than the evidence supports.**

A tool, Worker or model saying `success` is not automatically proof that the user's objective is complete.

## Important infrastructure clarification

OSCAR does **not** require the separate Latch or SwitchRoute projects as completed runtime products.

Their useful architecture and logic are folded into OSCAR natively:

- Latch-derived design → **OSCAR Transport + Capability Fabric**;
- SwitchRoute-derived design → **OSCAR Model Router**.

Those repositories remain useful prototypes/reference implementations, but OSCAR owns the final task, transport, capability and model-routing contracts.

See [`docs/NATIVE-INFRASTRUCTURE.md`](docs/NATIVE-INFRASTRUCTURE.md).

## System at a glance

```text
                        User / Environment
                               │
                       Perception Fabric
            screen • audio • Voice Map • sensors
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
 continuity + recall   native Model Router     authoritative sources
                           │
                       providers
                    ChatGPT / others
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
             OSCAR Transport + Capability Fabric
                               │
      ┌────────────────────────┼──────────────────────────┐
      │                        │                          │
  OSCAR Edge                Sunday                Desktop / machine nodes
ESP32 + RP2040              phone             Windows • macOS • agents
      │                       │                           │
sensors / GPIO       calls • apps • meetings      Codex • Computer Use
                     messages • dictation         apps • terminal • IDE
```

## Core capabilities

| Area | Planned capability |
|---|---|
| Natural interaction | Native voice and text, shared context, interruption/barge-in and concise proactive replies |
| OSCAR Voice Identity | Stable provider-independent synthesized voice, prosody/modulation policy, pronunciation controls and contextual speaking modes |
| Voice Match | Owner/authorized-speaker verification used as one authorization signal, never sole high-risk authentication |
| Voice Map | Local confidence-qualified map of owner/known/unknown speakers linked to canonical people only when evidence/consent supports it |
| Acoustic Sentry | Always-on local wake/speech/speaker/sound awareness when enabled, without default continuous cloud transcription |
| Interaction Runtime | `Dictate / Edit / Ask / Act`, selected-text editing, cursor/focus context, point-and-talk and system-wide insertion |
| Fast reflexes | Wake word, `mute`, `stop`, `cancel`, local controls and safety paths bypass heavy models |
| Multi-device voice | Sunday, desktop and physical OSCAR arbitrate one owning voice surface per turn |
| Epistemic Integrity | Distinguish known/inferred/recalled/reported/verified/unknown; never claim completion beyond evidence |
| Jev routing | Decide whether to execute, retrieve, verify, reason, delegate, repair/reroute or ask |
| Native Model Router | Provider/model routing by capability, quality, latency, cost, availability and policy |
| Native Transport | Typed secure task/event/result transport and capability advertisement across Sunday, desktop, Edge and other nodes |
| World Model | Live graph of people, places, devices, apps, projects, objects, tasks and relationships with freshness/provenance |
| Perception Fabric | Screens, accessibility, cursor/selection, cameras, audio events, Voice Map, apps, devices, location and sensors feed one current-state layer |
| Live context/search | Federated retrieval across files, mail, messages, notes, browser, GitHub, calendar, devices and services |
| Continuous memory | LRA + Supermemory: one persistent conversation/history rather than disconnected chats |
| Entity graph | Canonical people/contact/account/company/device/project identities resolved across systems |
| Personal Policy | Open-ended user preferences editable by voice/chat; distinct from memory and permissions |
| Executive Planner | Prioritize and schedule Workers/Protocols across deadlines, dependencies, devices, cost, risk and interruptibility |
| Durable Execution Runtime | Long-running task state, checkpoints, leases, heartbeats, reclaim, bounded retries and crash resume |
| Capability Catalog + Tool Search | Search lightweight capability manifests and progressively load only relevant detailed contracts |
| Communication | Calls, messaging, meetings, dictation, transcription, notes and follow-up where platform support permits |
| Universal Channel Gateway | Normalized communication abstraction without hiding platform-specific capability limits |
| Action Ledger + Undo | Consequential actions are attributable, evidence-aware and expose real compensation only where supported |
| Artifact / Result Model | Finished docs, code, reports, media, deployments and other outputs become typed durable objects with provenance/version/verification |
| Sunday | OSCAR's phone embodiment with phone/app context, communications, dictation, camera, sensors and biometric approval |
| Desktop | Native Windows/macOS presence with VoiceOS-grade interaction, screen/cursor context, overlays and machine capabilities |
| Delegated Workers | Temporary/persistent sub-agents using the real device/service mesh rather than mandatory cloud computers |
| Teach by demonstration | `watch me do this once` can become a verified, permission-scoped Skill candidate |
| Predictive intelligence | Forecast schedule/task/device risk and prepare before failure rather than only reacting |
| Physical world | ESP32/Pico sensors, GPIO, displays, actuators, workbench and environment integrations |
| Sentry | Always-on low-power local awareness across acoustic, device, presence and physical events |
| Learning | Verified procedures become reusable memory/Skills and improve repeated work |
| Protocols & routines | Stateful long-running responsibilities, schedules and event triggers |
| Self-maintenance | Detect broken auth/adapters/nodes/providers, repair/rollback safe failures and ask only when needed |

## Voice is part of OSCAR's identity

Voice is not one checkbox called `TTS`.

```text
Voice Input     = wake / VAD / STT / barge-in
OSCAR Voice     = stable synthesized identity + prosody
Voice Match     = authorization-oriented speaker verification
Voice Map       = perception-oriented known/unknown speaker map
Acoustic Sentry = local always-on event plane consuming wake/speech/Voice Map/sound events
```

OSCAR's own generated voice must be tagged/suppressed so it does not trigger itself or become a false speaker in Voice Map.

Speech presence, speaker recognition, transcription and transcript retention are separate decisions.

See [`docs/VOICE-SENTRY.md`](docs/VOICE-SENTRY.md).

## How OSCAR should work

```text
"mute"                         → local reflex
"what is this?"                → cursor + accessibility + visual context
"email John..."                → Jev → typed capability
"what did we decide?"          → Jev → LRA/Supermemory
"what is running at home?"     → Jev → live World Model/source state
"undo that"                    → Action Ledger → real compensation if supported
"fix this crash"               → Codex → tests → independent verification → report
"manage SceneLab socials"      → persistent Social Worker + Personal Policy
"answer calls after 4 rings"   → Personal Policy + communication runtime
"design this Pico device"      → Kinetable + hardware toolchain
```

Routing rule:

> **Use the most suitable capability, not the most general model.**

Reporting rule:

```text
planned
→ executing
→ result received
→ verifying
→ verified / partially verified / failed / blocked / unknown
```

Only the evidence-backed state should reach the user as the final claim.

## Workers

Workers are delegated sub-agents OSCAR creates for a job or ongoing responsibility.

```text
"Research these laptops"          → temporary Research Worker
"Watch ClearLane CI tonight"      → task Worker
"Manage SceneLab social media"    → persistent Social Worker
"Handle university scheduling"   → persistent Admin Worker
```

A Worker is not inherently another generic LLM and does not require its own cloud computer. It can use Sunday, machine nodes, Codex, Computer Use, APIs/plugins, native model routing, Kinetable or OSCAR Edge.

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

OSCAR keeps **memory**, **preferences/policy**, **permissions** and **Protocols** distinct.

See [`docs/PERSONAL-POLICY.md`](docs/PERSONAL-POLICY.md).

## Design language — Quietly Alive

OSCAR uses a minimal, technical and tactile design language with character coming from **state, motion, timing, voice and the avatar**, not generic AI decoration.

Directional blend:

- **60% restrained/native product design**;
- **20% tactile industrial character**;
- **10% friendly character/feedback**;
- **10% functional honesty**.

The blue-shell/yellow-face OSCAR avatar is the visual anchor. No generic AI dashboard, permanent chat sidebar, glassmorphism, neon HUD, purple AI gradient or fake telemetry.

See [`DESIGN.md`](DESIGN.md), [`TASTE.md`](TASTE.md) and [`docs/SUNDAY-DESIGN.md`](docs/SUNDAY-DESIGN.md).

## Engineering philosophy

> **Simple boundaries, strong contracts, boring reliability.**

- prefer the smallest coherent solution;
- high cohesion / low coupling;
- typed/validated contracts and explicit state ownership;
- bounded retry/reconnect/cancellation/recovery;
- least privilege and fail-safe defaults;
- test meaningful failure paths;
- verify outcomes rather than trusting executor reports;
- measure critical-path latency before optimizing;
- prefer small reviewable/reversible changes.

See [`ENGINEERING.md`](ENGINEERING.md).

## Architecture principles

1. **One intelligence, many embodiments.**
2. **One continuous relationship.**
3. **Current truth is explicit.**
4. **Evidence before claims.**
5. **Edge for immediacy; cloud for cognition.**
6. **Use the best tool for the job.**
7. **Know when you do not know.**
8. **One executive, many Workers.**
9. **Long-running work is durable.**
10. **Capabilities are discovered progressively.**
11. **Actions are accountable.**
12. **Artifacts are first-class.**
13. **Learning is evaluated.**
14. **Perceived latency matters.**
15. **Proactive, not noisy.**
16. **Permissioned autonomy.**
17. **Personal Policy is first-class.**
18. **Communication is integrated.**
19. **The PC is an accelerator, not a dependency.**
20. **No yes-man behavior.**
21. **Transport and model routing are native OSCAR infrastructure.** Latch/SwitchRoute are reference architectures, not required deployments.
22. **Voice Match ≠ Voice Map.** Recognition does not imply authorization.
23. **OSCAR has a stable voice identity.** TTS provider choice must not define the character/product identity.
24. **Sentry listens locally first.** Always-on acoustic awareness does not mean always-on cloud transcription.

## Implementation strategy

OSCAR is built **core-loop first**, not hardware-first.

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

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository foundation and architecture | ✅ Complete |
| 01 | OSCAR Core Loop | ⏭️ Next |
| 02 | TypeSafe Jev | Planned |
| 03 | Native OSCAR Transport + Capability Catalog | Planned |
| 04 | Native OSCAR Model Router + cloud intelligence | Planned |
| 05 | First real machine Worker | Planned |
| 06 | LRA/Supermemory + Personal Policy + live context | Planned |
| 07 | OSCAR Edge + reflexes | Planned |
| 08 | Voice Core + OSCAR Voice Identity + Voice Match + Voice Map + multi-device arbitration | Planned |
| 09 | Sunday + communication + Universal Channel Gateway | Planned |
| 10 | Desktop VoiceOS-grade `Dictate / Edit / Ask / Act` Interaction Runtime | Planned |
| 11 | World Model + Perception Fabric + acoustic/physical Sentry | Planned |
| 12 | First-run commissioning + Voice Match/Voice Map/Voice Identity calibration | Planned |
| 13 | Avatar/presence UI | Planned |
| 14 | Executive Planner + durable Workers + learning/evaluation + Skills/Protocols | Planned |
| 15 | Kinetable + spatial/workbench + general engineering/simulation routing | Planned |
| 16 | Self-maintenance + reliability/security + truthfulness/voice robustness pass | Planned |
| 17 | Unified alpha | Planned |

> **Current position:** Slice 00 is complete. Implementation begins with **Slice 01 — OSCAR Core Loop**.

## Documentation

- [Product vision](docs/PRODUCT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Native OSCAR infrastructure](docs/NATIVE-INFRASTRUCTURE.md)
- [Voice + Sentry](docs/VOICE-SENTRY.md)
- [JARVIS / VoiceOS gap review](docs/JARVIS-GAP-REVIEW.md)
- [Final competitive benchmark](docs/COMPETITIVE-BENCHMARK.md)
- [Runtime foundations](docs/RUNTIME-FOUNDATIONS.md)
- [Epistemic Integrity](docs/EPISTEMIC-INTEGRITY.md)
- [Feature inventory](docs/FEATURES.md)
- [Engineering standard](ENGINEERING.md)
- [Design system](DESIGN.md)
- [Memory](docs/MEMORY.md)
- [Personal Policy](docs/PERSONAL-POLICY.md)
- [Communication](docs/COMMUNICATION.md)
- [Workers](docs/WORKERS.md)
- [Orchestration](docs/ORCHESTRATION.md)
- [Surfaces](docs/SURFACES.md)
- [Onboarding](docs/ONBOARDING.md)
- [Avatar](docs/UI-AVATAR.md)
- [Security](docs/SECURITY.md)
- [Detailed roadmap](docs/ROADMAP.md)
- [Architecture decisions](docs/DECISIONS.md)

## Development rule

Every implementation slice updates this README and affected docs in the **same change**: status, architecture decisions, completed features, limitations, verification evidence and next slice.

A slice is not complete because an agent says it is complete. Its exit condition must be verified against repository/runtime/device evidence wherever possible.

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient agent.</sub></p>
