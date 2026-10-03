<p align="center">
  <img src="assets/brand/oscar-logo.png" width="180" alt="OSCAR logo" />
</p>

<h1 align="center">OSCAR</h1>

<p align="center"><strong>A persistent, multimodal, agentic intelligence spanning phone, computers, communications, environment and physical hardware.</strong></p>

<p align="center"><code>Persistent</code> · <code>Context-aware</code> · <code>Agentic</code> · <code>Immediate</code> · <code>Learning</code> · <code>Evidence-backed</code></p>

---

## What OSCAR is

OSCAR is a practical interpretation of the *idea* behind JARVIS: one intelligence that can perceive current context, reason, communicate, use tools, delegate work, operate software/hardware, keep working in the background, coordinate the user's day and appear through whichever trusted device is available.

It is **not** a chatbot with a wake word, a laptop-only agent or a decorative orb.

OSCAR's truth rule:

> **Know what you know, know why you know it, verify what can be verified, and never claim more than the evidence supports.**

A tool, Worker or model saying `success` is not automatically proof that the objective is complete.

## Ambient Chief of Staff

OSCAR should be continuously available and quietly useful. With explicit permission, current context can include:

```text
time / date / timezone
weather
calendar + free/busy
tasks / deadlines / dependencies
location / mobility
notifications + communications
media / activity / focus signals
device + Connection Grid state
Workers / Protocols
Sentry / Edge observations
```

The goal is not to dump this information back to the user. OSCAR should combine it into useful decisions: protect focus time, detect schedule conflicts, manage flexible blocks, surface changed commitments, account for travel/weather, summarize what was missed and update tasks/calendar when policy allows.

Proactivity is graduated:

```text
observe silently
→ inform
→ suggest
→ act within policy
→ interrupt only when justified
```

A core privacy/authority rule is:

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

Notification access does not imply permission to store or reply. Calendar read access does not imply permission to modify. Microphone permission does not imply continuous transcription or raw-audio retention.

See [`docs/CHIEF-OF-STAFF.md`](docs/CHIEF-OF-STAFF.md).

## One intelligence, one Connection Grid

```text
                         OSCAR
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      Sunday            Cloud             Desktop(s)
 owner control       rendezvous/state      high compute
        │                                     │
        └──────────────────┬──────────────────┘
                           ▼
                       OSCAR Edge
                  local reflex / safety
```

- **Sunday** — OSCAR on the phone; preferred owner-control, approval, notification and Chief-of-Staff surface.
- **Cloud** — replaceable free-tier/paid/BYOC rendezvous and durable coordination.
- **Desktop** — optional high-capability execution: Codex, terminal, filesystem, browser/computer use, apps, GPU/local models.
- **Edge** — ESP32/Pico local wake, sensors, GPIO, reflexes and deterministic safety.

No ordinary laptop/desktop is OSCAR's permanent host. Losing one node should reduce capability, not silently erase OSCAR.

See [`docs/CONNECTION-GRID.md`](docs/CONNECTION-GRID.md).

## Sunday — phone embodiment

Sunday should feel **present, not launched**.

On Android, the product direction is to use legitimate platform capabilities where supported and explicitly granted:

- selected assistant role / voice-interaction architecture;
- an optional OSCAR Orb application overlay;
- attention-aware Orb retreat during video, reading, presentation or focus contexts;
- hidden edge/hotspot/assistant/voice invocation and natural reappearance;
- configurable home-screen widgets;
- notification-listener context;
- real notification reply actions when exposed;
- biometric/PIN confirmation for sensitive owner actions.

Notification visibility is not unrestricted WhatsApp/app access. OEM/device behavior remains unverified until tested on target hardware.

See [`docs/SUNDAY-DESIGN.md`](docs/SUNDAY-DESIGN.md), [`docs/SURFACES.md`](docs/SURFACES.md) and [`docs/CHIEF-OF-STAFF.md`](docs/CHIEF-OF-STAFF.md).

## Native infrastructure

OSCAR does **not** require the separate Latch or SwitchRoute projects as runtime products.

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
```

Providers, models and credentials are replaceable runtime resources. Jev decides whether reasoning/retrieval/execution is needed; the Model Router only chooses a provider/model after a model path is selected.

Freshness-sensitive questions must use current authoritative evidence when reasonably available. Provider manifests are bootstrap metadata, not permanent truth.

See [`docs/NATIVE-INFRASTRUCTURE.md`](docs/NATIVE-INFRASTRUCTURE.md), [`docs/MODEL-ROUTING.md`](docs/MODEL-ROUTING.md) and [`docs/SEARCH-FRESHNESS.md`](docs/SEARCH-FRESHNESS.md).

## System at a glance

```text
User / Environment
      ↓
Perception Fabric → World Model
      ↓
     Jev
      ↓
Memory / Live Context / Search / Model Router
      ↓
OSCAR Executive + Personal Policy
      ↓
Durable Execution Runtime
      ↓
Capability Catalog + Workers / Skills / Protocols
      ↓
Connection Grid
      ↓
Apps / Channels / Devices / Specialists
      ↓
Action Ledger + Artifact/Result
      ↓
Verification
      ↓
World Model / Memory update
      ↓
evidence-backed result
```

## Voice, Sentry and continuity

```text
Voice Input     = wake / VAD / STT / barge-in
OSCAR Voice     = stable provider-independent voice identity
Voice Match     = authorization-oriented speaker evidence
Voice Map       = perception-oriented speaker context
Sentry          = persistent local-first awareness
```

Keep these product states distinct:

```text
Sentry Aware
Listening
Muted
Acoustic Awareness Off
Context Capture
Daily Journal
```

Persistent awareness does not automatically mean persistent recording. Raw audio, transcript, summary and memory extraction each have separate controls.

See [`docs/VOICE-SENTRY.md`](docs/VOICE-SENTRY.md), [`docs/COMMUNICATION.md`](docs/COMMUNICATION.md) and [`docs/SECURITY.md`](docs/SECURITY.md).

## Persona and Personal Policy

```text
Persona         = how OSCAR expresses itself
Personal Policy = how the user wants OSCAR to behave
Permission      = what OSCAR may do
Memory          = what OSCAR retains/recalls
```

Persona may be witty, solemn, warm, formal, blunt or custom. **Truthfulness is not a slider.** Persona never changes factual integrity, permissions, required confirmation or safety.

Personal Policy can govern interruption, schedule flexibility, communications, capture, Worker autonomy, remote continuation and other behavior within granted capability.

See [`docs/PERSONA.md`](docs/PERSONA.md) and [`docs/PERSONAL-POLICY.md`](docs/PERSONAL-POLICY.md).

## Core capability map

| Area | Direction |
|---|---|
| Chief of Staff | Time/weather/calendar/tasks/notifications/context → schedule/task/communication coordination within policy |
| Connection Grid | Sunday + replaceable cloud + Desktop + Edge availability/control fabric |
| Epistemic Integrity | Known/inferred/recalled/reported/verified/unknown remain distinct |
| Jev | Decide execute/retrieve/verify/reason/delegate/ask path |
| Search / freshness | Current authoritative evidence outranks stale manifests/model priors |
| Model Router | Adaptive provider/model/credential routing with real health/quota/funding evidence |
| Machine Workers | Filesystem/Git/terminal/Codex/browser/apps as discovered capabilities |
| Sunday | Android embodiment, assistant presence, Orb/widgets, notifications, owner control |
| Desktop | Dictate / Edit / Ask / Act + machine capability surface |
| World Model | Live current-state graph with freshness/provenance |
| LRA + Supermemory | Historical/personal continuity; never current authority by itself |
| Communication | Calls/messages/email/meetings/dictation/follow-up where supported |
| Voice/Sentry | Persistent local awareness, stable voice identity, barge-in, capture controls |
| Workers/Executive | Durable delegated responsibilities + priority/dependency coordination |
| Edge | Sensors/GPIO/actuators with deterministic local safety |
| Learning | Verified procedures become evaluated reusable Skills/Protocols |

## Design language

OSCAR uses **Quietly Alive + Playful Precision**:

- 70% restraint / whitespace;
- 20% tactile industrial precision;
- 10% approachable personality;
- warm cream/off-white materials + graphite typography;
- OSCAR blue/yellow reserved for identity/presence/state;
- shared geometry and weighted physical motion;
- no generic AI dashboard, card wall, glass/neon/purple-gradient slop or fake telemetry.

> **State A should physically become State B where practical.**

Simplicity must never become lack of craftsmanship.

See [`DESIGN.md`](DESIGN.md), [`TASTE.md`](TASTE.md), [`docs/SUNDAY-DESIGN.md`](docs/SUNDAY-DESIGN.md) and [`docs/UI-AVATAR.md`](docs/UI-AVATAR.md).

## Current build status

The repository foundation and Club A Brain are merged into `main`.

- **Gate A — PASS** for the current Club A foundation: Core Loop, TypeSafe Jev, reference Transport/Grid, adaptive model routing, real multi-provider evidence and source-qualified Tavily/live-search acceptance.
- **Gate B — PARTIAL**: the reviewed Club B reference foundation is merged. Separate-process POSIX Worker, Git/file/terminal reference execution, restart/reclaim, local memory/Personal Policy/entity continuity and Connector Fabric are verified for their scoped reference cases. Windows, a real useful authenticated Codex task, browser/computer use, private service accounts/OAuth, Supermemory and natural-language policy acceptance remain outstanding.

The detailed evidence and limitations live in [`docs/CLUB-A-CHECKPOINT.md`](docs/CLUB-A-CHECKPOINT.md) and [`docs/CLUB-B-CHECKPOINT.md`](docs/CLUB-B-CHECKPOINT.md).

## Roadmap

| Slice | Deliverable | Status |
|---:|---|---|
| 00 | Repository/architecture foundation | ✅ Complete |
| 01 | OSCAR Core Loop | ✅ Verified scoped foundation |
| 02 | TypeSafe Jev | ✅ Verified typed/freshness foundation |
| 03 | Native Transport + Catalog + Grid foundation | Reference verified; public deployment partial |
| 04 | Native Model Router + cloud intelligence | ✅ Gate A accepted; broader deployment/metadata evolves |
| 05 | Real machine Worker + remote continuation | Reference verified; Windows/real specialist/browser partial |
| 06 | LRA/Supermemory + Personal Policy + live context | Local/reference verified; Supermemory/OAuth/NL policy partial |
| 07 | OSCAR Edge + reflexes | Planned |
| 08 | Voice Core + Identity + Match/Map + Persona runtime | Planned |
| 09 | Sunday + communication + Grid owner controls | Planned |
| 10 | Desktop Interaction Runtime | Planned |
| 11 | World Model + Perception + Sentry + Daily Journal | Planned |
| 12 | Commissioning/setup | Planned |
| 13 | Avatar/presence UI | Planned |
| 14 | Executive Planner + durable Workers + learning | Planned |
| 15 | Physical/device expansion + specialist engineering | Planned |
| 16 | Reliability/security/truthfulness hardening | Planned |
| 17 | Unified alpha | Planned |

See [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`docs/BUILD-GATES.md`](docs/BUILD-GATES.md).

## Review / development

Run from the repository root with Python 3.12+:

```sh
python -m pip install '.[dev]'
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m unittest discover -s tests -t . -v
python -m scripts.check_repository
```

Reference Club B checks:

```sh
python -m scripts.verify_worker_reference --report .oscar/worker-review.json
python -m scripts.verify_club_b --report .oscar/club-b-review.json
python -m unittest tests.test_connectors tests.test_connector_http -v
```

A slice is not complete because an agent says it is complete. Implementation, tests, limitations, documentation and authoritative resulting state must agree.

## Canonical documentation

- [Product](docs/PRODUCT.md)
- [Ambient Chief of Staff](docs/CHIEF-OF-STAFF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Build gates](docs/BUILD-GATES.md)
- [Epistemic Integrity](docs/EPISTEMIC-INTEGRITY.md)
- [Search + freshness](docs/SEARCH-FRESHNESS.md)
- [Connection Grid](docs/CONNECTION-GRID.md)
- [Model routing](docs/MODEL-ROUTING.md)
- [Sunday design](docs/SUNDAY-DESIGN.md)
- [Surfaces](docs/SURFACES.md)
- [Communication](docs/COMMUNICATION.md)
- [Memory](docs/MEMORY.md)
- [Personal Policy](docs/PERSONAL-POLICY.md)
- [Persona](docs/PERSONA.md)
- [Voice + Sentry](docs/VOICE-SENTRY.md)
- [Workers](docs/WORKERS.md)
- [Orchestration](docs/ORCHESTRATION.md)
- [Onboarding](docs/ONBOARDING.md)
- [Security](docs/SECURITY.md)
- [Design system](DESIGN.md)
- [Taste / quality bar](TASTE.md)

---

<p align="center"><sub>OSCAR is an original project inspired by the goal of building a genuinely capable ambient intelligence.</sub></p>
