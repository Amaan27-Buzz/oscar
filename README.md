<p align="center">
  <img src="assets/brand/oscar-logo.png" width="180" alt="OSCAR logo" />
</p>

<h1 align="center">OSCAR</h1>

<p align="center"><strong>A persistent, multimodal, agentic intelligence spanning your phone, computers, communications, environment and physical hardware.</strong></p>

<p align="center"><code>Persistent</code> · <code>Omnipresent</code> · <code>Agentic</code> · <code>Immediate</code> · <code>Learning</code> · <code>Evidence-backed</code></p>

---

## What OSCAR is

OSCAR is an attempt to build a practical real-world interpretation of the *idea* behind JARVIS: not a chatbot with a voice and animated orb, but one intelligence that can perceive context, reason, communicate, use tools, delegate work, control software/hardware, keep working in the background, learn procedures and appear through whatever trusted device is available.

The laptop is **not** OSCAR's host. Desktop machines are optional high-capability execution nodes. Sunday is OSCAR on the phone. Edge hardware preserves local presence/reflex/safety. A replaceable cloud coordinator can provide rendezvous/durable coordination.

OSCAR's truth rule:

> **Know what you know, know why you know it, verify what can be verified, and never claim more than the evidence supports.**

A tool, Worker or model saying `success` is not automatically proof that the objective is complete.

## One intelligence, one Connection Grid

OSCAR's availability model is the **Connection Grid**:

```text
                         OSCAR
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      Sunday            Cloud             Desktop(s)
 owner controls      rendezvous/state      high compute
        │                                     │
        └──────────────────┬──────────────────┘
                           ▼
                       OSCAR Edge
                  local reflex / safety
```

- **Sunday** — preferred owner control surface, approvals, notifications and remote supervision.
- **Cloud** — replaceable free-tier/paid/BYOC rendezvous and durable coordination.
- **Desktop** — Codex, terminal, filesystem, browser, computer use, installed apps, GPU/local models.
- **Edge** — ESP32/Pico local wake/sensors/GPIO/reflex/safety.

The goal is graceful degradation: losing one ordinary node should reduce capabilities, not silently erase OSCAR.

Example:

```text
start Codex/build/render on Desktop
→ leave home with Sunday
→ task keeps running
→ inspect / approve / pause / cancel remotely
→ OSCAR verifies result
→ optionally sleep/shut down Desktop if a real permitted capability exists
```

Remote wake/power-on is only exposed when Wake-on-LAN or another legitimate power-management capability actually exists.

See [`docs/CONNECTION-GRID.md`](docs/CONNECTION-GRID.md).

## Native infrastructure

OSCAR does **not** require the separate Latch or SwitchRoute projects as runtime products.

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
```

Their repos remain useful reference/prototype sources only.

See [`docs/NATIVE-INFRASTRUCTURE.md`](docs/NATIVE-INFRASTRUCTURE.md) and [`docs/MODEL-ROUTING.md`](docs/MODEL-ROUTING.md).

## System at a glance

```text
User / Environment
      ↓
Perception Fabric → World Model
      ↓
     Jev
      ↓
Memory / Live Context / Model Router
      ↓
OSCAR Executive + Personal Policy
      ↓
Durable Execution Runtime
      ↓
Capability Catalog + Workers / Skills / Protocols
      ↓
Connection Grid
  ├─ Sunday
  ├─ Cloud
  ├─ Desktop nodes
  └─ Edge
      ↓
Actions / Channels / Apps / Devices / Specialists
      ↓
Action Ledger + Artifact/Result
      ↓
Verification
      ↓
World Model / Memory update
      ↓
evidence-backed result
```

## Voice + persistent Sentry

Voice is not one `TTS/STT` checkbox.

```text
Voice Input     = wake / VAD / STT / barge-in
OSCAR Voice     = stable provider-independent voice identity
Voice Match     = authorization-oriented speaker verification
Voice Map       = perception-oriented speaker recognition
Sentry          = persistent local-first awareness
```

Important product states remain distinct:

```text
Sentry Aware        = persistent local acoustic/event awareness may be active
Listening           = active conversational STT
Muted               = ordinary conversational listening suppressed; configured local reflex commands may remain
Awareness Off       = local acoustic plane actually disabled
Typing              = another input modality; does not automatically disable Sentry
```

### Optional Context Capture / Daily Journal

For users who explicitly want comprehensive continuity, OSCAR can support source-by-source capture of calls, messages/email, meetings and ordinary in-person conversations **where platform capability, permission, consent and law allow**.

```text
Awareness only
→ no continuous transcript retention

Context capture
→ selected sources transcribed/indexed/summarized; raw media minimized

Daily journal
→ explicit durable cross-channel continuity timeline
```

Raw audio, transcript, summary and memory extraction each have separate retention controls. Capture must never be silently enabled by a generic microphone permission.

See [`docs/VOICE-SENTRY.md`](docs/VOICE-SENTRY.md), [`docs/COMMUNICATION.md`](docs/COMMUNICATION.md) and [`docs/SECURITY.md`](docs/SECURITY.md).

## Persona — OSCAR can have character

OSCAR's character is configurable rather than hard-coded.

The user can make OSCAR wry, solemn, warm, formal, playful, blunt or custom through natural language or manual controls.

Example:

```text
"Be drier and less chatty."
"No jokes on university calls."
"Be blunt when reviewing code."
"When Sentry alerts me, be serious and direct."
```

Useful traits include Humor, Candor, Warmth, Formality, Brevity, Playfulness, Initiative and Pushback, with context triggers.

**Truthfulness is not a slider.** Epistemic Integrity, safety, permissions and Personal Policy always outrank Persona.

See [`docs/PERSONA.md`](docs/PERSONA.md).

## Core capabilities

| Area | Planned capability |
|---|---|
| Natural interaction | Voice/text in one continuous context, low-latency interruption and proactive replies |
| Connection Grid | Sunday + replaceable cloud + Desktop + Edge availability/control fabric |
| Remote continuation | Long-running machine work continues while user leaves; remote inspect/approve/cancel |
| Epistemic Integrity | Known/inferred/recalled/reported/verified/unknown kept distinct |
| Jev | Decide execute/retrieve/verify/reason/delegate/ask path |
| Native Model Router | Automatic/manual provider/model/credential routing |
| Capability Catalog | Discover only currently available tools/nodes/apps |
| Desktop | Dictate / Edit / Ask / Act, screen/cursor context, machine capabilities |
| Sunday | Phone embodiment, owner controls, communication, Sentry, approvals |
| Voice Identity | Stable OSCAR voice across surfaces/providers |
| Voice Match / Voice Map | Authorization signal vs perception identity map |
| Persistent Sentry | Local-first awareness across acoustic/device/environment events |
| Context Capture / Daily Journal | Optional explicit cross-channel continuity capture with retention controls |
| Persona | Configurable character + context triggers, never reducing truth/safety |
| World Model | Live current-state graph with freshness/provenance |
| LRA + Supermemory | Continuous historical/personal context |
| Personal Policy | Explicit behavior rules separate from memory/Persona/permissions |
| Communication | Calls/messages/email/meetings/dictation/follow-up where supported |
| Workers | Temporary/persistent delegated responsibilities |
| Executive Planner | Coordinate priorities/dependencies/resources across objectives |
| Durable Runtime | Checkpoints/leases/retries/reclaim/restart for long-running work |
| Action Ledger + Undo | Attributable consequential actions and real compensation only where supported |
| Artifact / Result Model | Durable docs/code/media/results with provenance/verification |
| Edge / physical world | Sensors/GPIO/displays/actuators with deterministic local safety |
| Learning | Verified procedures become evaluated reusable Skills/Protocols |
| Self-maintenance | Diagnose broken providers/nodes/auth and recover safely |

## Design language — Quietly Alive

OSCAR uses **Quietly Alive + Playful Precision**:

- **70% restraint / whitespace** — calm hierarchy and editorial typography;
- **20% tactile industrial precision** — physical cause/effect and material honesty;
- **10% approachable personality** — warmth without becoming mascot-led.

Warm cream/off-white materials and graphite typography do most of the work. OSCAR blue/yellow is reserved for identity/presence/state.

Motion is structural:

> **State A should physically become State B where practical.**

Shared geometry, weighted springs, contextual expansion and continuous state transitions make the product feel alive without decorative animation.

The blue-shell/yellow-puck avatar is a weighted presence object, not a giant mascot.

No generic AI dashboards, permanent chat sidebar, card wall, glassmorphism, obvious neumorphism, neon HUD, purple AI gradient or fake telemetry.

Design development follows Kaizen: study real shipping patterns → build one real surface → inspect → improve the largest weakness → verify → expand.

Image-generation reference prompts live in [`image-prompts/`](image-prompts/README.md); coded UI remains the product source of truth.

See [`DESIGN.md`](DESIGN.md), [`TASTE.md`](TASTE.md), [`docs/SUNDAY-DESIGN.md`](docs/SUNDAY-DESIGN.md) and [`docs/UI-AVATAR.md`](docs/UI-AVATAR.md).

## Engineering philosophy

> **Simple boundaries, strong contracts, boring reliability.**

Beautiful enough to feel premium. Simple enough to reason about. Robust enough to abuse. Graceful when degraded.

See [`ENGINEERING.md`](ENGINEERING.md).

## Planned slices

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository/architecture foundation | ✅ Complete |
| 01 | OSCAR Core Loop | ⏭️ Next |
| 02 | TypeSafe Jev | Planned |
| 03 | Native Transport + Capability Catalog + Connection Grid foundation | Planned |
| 04 | Native Model Router + cloud intelligence | Planned |
| 05 | Real machine Worker + remote continuation | Planned |
| 06 | LRA/Supermemory + Personal Policy + live context | Planned |
| 07 | OSCAR Edge + reflexes | Planned |
| 08 | Voice Core + Voice Identity + Voice Match/Map + Persona runtime | Planned |
| 09 | Sunday + communications + Grid owner controls | Planned |
| 10 | Desktop Interaction Runtime | Planned |
| 11 | World Model + Perception + persistent Sentry + optional Daily Journal | Planned |
| 12 | Commissioning/setup | Planned |
| 13 | Avatar/presence UI | Planned |
| 14 | Executive Planner + durable Workers + learning | Planned |
| 15 | Physical/device expansion + specialist engineering | Planned |
| 16 | Reliability/security/truthfulness hardening | Planned |
| 17 | Unified alpha | Planned |

Manual integration checkpoints are in [`docs/BUILD-GATES.md`](docs/BUILD-GATES.md).

## Documentation

- [Product](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Connection Grid](docs/CONNECTION-GRID.md)
- [Native infrastructure](docs/NATIVE-INFRASTRUCTURE.md)
- [Model routing](docs/MODEL-ROUTING.md)
- [Voice + Sentry](docs/VOICE-SENTRY.md)
- [Persona](docs/PERSONA.md)
- [Communication](docs/COMMUNICATION.md)
- [Memory](docs/MEMORY.md)
- [Personal Policy](docs/PERSONAL-POLICY.md)
- [Workers](docs/WORKERS.md)
- [Orchestration](docs/ORCHESTRATION.md)
- [Surfaces](docs/SURFACES.md)
- [Onboarding](docs/ONBOARDING.md)
- [Security](docs/SECURITY.md)
- [Epistemic Integrity](docs/EPISTEMIC-INTEGRITY.md)
- [Design system](DESIGN.md)
- [Taste](TASTE.md)
- [Image prompt library](image-prompts/README.md)

## Development rule

A slice is not complete because an agent says it is complete. Implementation, tests, limitations, documentation and authoritative resulting state must agree.

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient intelligence.</sub></p>
