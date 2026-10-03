# Coding-agent context

OSCAR keeps one canonical project truth and uses thin agent-specific adapters. Do not duplicate the whole architecture into every tool prompt.

## Canonical files

| File | Purpose |
|---|---|
| `AGENTS.md` | repository-wide workflow, truth, safety and coding-agent rules |
| `ENGINEERING.md` | system-design/code-quality standard |
| `DESIGN.md` | normative visual tokens and durable design rules |
| `TASTE.md` | qualitative quality / motion / anti-slop bar |
| `docs/PRODUCT.md` | product north star |
| `docs/CHIEF-OF-STAFF.md` | ambient context, commitments, schedule/proactivity and Sunday system-presence contract |
| `docs/ARCHITECTURE.md` | system boundaries and ownership |
| `docs/ROADMAP.md` | implementation order/current slice |
| `docs/BUILD-GATES.md` | cross-slice manual verification checkpoints |
| `docs/DECISIONS.md` | durable architecture decisions |
| `docs/EPISTEMIC-INTEGRITY.md` | evidence/verification/non-yes-man contract |
| `docs/RUNTIME-FOUNDATIONS.md` | durable tasks, capabilities, channels, artifacts and automation evaluation |
| `docs/NATIVE-INFRASTRUCTURE.md` | native transport and model-routing infrastructure |
| `docs/CONNECTION-GRID.md` | Sunday/cloud/desktop/Edge availability and remote-control fabric |
| `docs/MODEL-ROUTING.md` | provider/model/credential routing |
| `docs/SEARCH-FRESHNESS.md` | current-source/freshness authority contract |
| `docs/MEMORY.md` | LRA/Supermemory continuity |
| `docs/PERSONAL-POLICY.md` | explicit user behavioral rules |
| `docs/PERSONA.md` | configurable OSCAR character/presentation |
| `docs/VOICE-SENTRY.md` | voice layers, persistent Sentry and optional continuity capture |
| `docs/COMMUNICATION.md` | calls/messages/email/meetings/dictation/capture |
| `docs/CONNECTOR-FABRIC.md` | structured service/API connector boundary |
| `docs/WORKERS.md` | delegated Worker lifecycle/recovery |
| `docs/ORCHESTRATION.md` | routing, Skills, Workers, routines and Protocols |
| `docs/SURFACES.md` | Sunday/desktop/cloud/Edge surface roles |
| `docs/SUNDAY-DESIGN.md` | Sunday mobile interaction direction |
| `docs/UI-AVATAR.md` | avatar/state/motion language |
| `docs/ONBOARDING.md` | commissioning |
| `docs/SECURITY.md` | permissions, transport, capture/Grid security |
| `docs/FEATURES.md` | comprehensive capability backlog |
| `docs/CLUB-A-CHECKPOINT.md` | historical Gate A evidence and corrections |
| `docs/CLUB-B-CHECKPOINT.md` | historical/current Club B evidence and limits |
| `image-prompts/` | optional visual-reference prompt library, not implementation truth |

Agent-specific files should point back to these rather than becoming independent product definitions.

## Context loading

More context is not automatically better. Load `AGENTS.md`, `ENGINEERING.md`, `docs/EPISTEMIC-INTEGRITY.md` and the relevant domain docs.

### Ambient / schedule / proactive assistance / Sunday context

- `docs/CHIEF-OF-STAFF.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/PERSONAL-POLICY.md`
- `docs/COMMUNICATION.md`
- `docs/SURFACES.md`
- `docs/SECURITY.md`

### Transport / remote nodes / availability

- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/SECURITY.md`

### Model providers / current facts / credentials

- `docs/MODEL-ROUTING.md`
- `docs/SEARCH-FRESHNESS.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/EPISTEMIC-INTEGRITY.md`

### Voice / Sentry / capture / communication

- `docs/VOICE-SENTRY.md`
- `docs/COMMUNICATION.md`
- `docs/SECURITY.md`
- relevant surface docs;
- `docs/ONBOARDING.md` for commissioning.

### Persona / UI / motion

- `docs/PERSONA.md`
- `DESIGN.md`
- `TASTE.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/UI-AVATAR.md`
- relevant surfaces.

### Memory / policy / entities

- `docs/MEMORY.md`
- `docs/PERSONAL-POLICY.md`
- `docs/PERSONA.md` when presentation and behavior risk being conflated.

### Workers / orchestration

- `docs/WORKERS.md`
- `docs/ORCHESTRATION.md`
- `docs/RUNTIME-FOUNDATIONS.md`

### Current Gate B work

- `docs/CLUB-B-CHECKPOINT.md`
- `docs/CONNECTOR-FABRIC.md`
- `docs/ROADMAP.md`

## Durable architectural rules

### Native infrastructure

Do not revive separate Latch/SwitchRoute runtime dependencies.

```text
Latch architecture/logic       → OSCAR Transport + Capability Fabric
SwitchRoute architecture/logic → OSCAR Model Router
```

### Three routing decisions remain separate

```text
Jev                  → what class of action is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

Coding agents, terminal, computer use and installed applications are executable capabilities, not provider keys.

### Connection Grid

```text
Sunday      = preferred owner control / approvals / notifications
Cloud       = replaceable rendezvous + durable coordination
Desktop     = high-capability execution
Edge        = local awareness / reflex / safety
```

No desktop is a hidden permanent host. Nodes advertise only real capabilities. Executor loss expires leases rather than leaving false `working` state. Power/wake claims require a real current capability.

### Chief of Staff

OSCAR should coordinate authorized current context across time/weather/calendar/tasks/notifications/communication/device/activity/Workers rather than behave only as a prompt-response app.

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

Current decisions are freshness-qualified. Proactivity is graded from silent observation through inform/suggest/act/interrupt. Schedule/message mutations require explicit authority and verification.

### Sentry / capture

Keep separate:

```text
Sentry Aware
Listening
Muted
Acoustic Awareness Off
Context Capture
Daily Journal
```

Awareness does not automatically mean recording. Raw audio, transcript, summary and memory extraction are separate retention decisions.

### Persona

```text
Persona         = how OSCAR expresses itself
Personal Policy = how user wants OSCAR to behave
Permission      = what OSCAR may do
Memory          = what OSCAR retains/recalls
```

Persona never lowers truth, safety, consent or authority requirements.

### Freshness

When current truth matters, use current authoritative sources where reasonably obtainable. Cached manifests, memory and model priors do not become current truth merely because they are convenient.

### Evidence / completion

For meaningful work:

1. define observable completion;
2. execute;
3. inspect authoritative resulting state;
4. run relevant tests/device/visual/source checks;
5. report the strongest claim evidence supports.

Worker/model/tool success is testimony until the objective is independently verified where practical.

## Design direction

Canonical direction is **Quietly Alive + Playful Precision**.

- 70% restraint/whitespace;
- 20% tactile industrial precision;
- 10% approachable personality;
- warm cream/off-white materials;
- graphite typography;
- OSCAR blue/yellow reserved for identity/presence/state;
- fluid shared-geometry motion;
- weighted avatar/puck;
- progressive disclosure.

Simplicity must preserve craftsmanship. Avoid generic AI dashboards, permanent chat sidebars, card walls, glass/neon/purple gradients, obvious neumorphism, fake telemetry and mascot-led layouts.

## Adapter files are intentional

- `AGENTS.md` is canonical for AGENTS-aware coding agents.
- `CLAUDE.md`, `GEMINI.md`, Copilot instructions and Cursor rules are deliberately thin adapters.
- Do **not** delete them as redundant merely because they point to the same canonical rules.
- Historical Gate/checkpoint/evidence docs are provenance and should not be deleted as `old docs` unless their evidence has been explicitly archived elsewhere.

## Propagation rules

When a durable rule changes, update the canonical owner first and reconcile only affected docs/adapters.

- ambient Chief-of-Staff/context/schedule → `CHIEF-OF-STAFF.md`, then Product/Architecture/Roadmap/Sunday/Surfaces/Policy/Communication/Security as affected;
- Connection Grid/availability → `CONNECTION-GRID.md` + affected architecture/security/surface docs;
- Sentry/capture → `VOICE-SENTRY.md` + Communication/Security/Onboarding/relevant surfaces;
- Persona → `PERSONA.md` + affected product/policy/surface docs;
- model routing/freshness → `MODEL-ROUTING.md` + `SEARCH-FRESHNESS.md` + affected infrastructure/roadmap docs;
- system-wide design → `DESIGN.md` + `TASTE.md` + affected surface docs;
- engineering invariant → `ENGINEERING.md`;
- architecture invariant → `DECISIONS.md` plus affected architecture/domain docs.

After propagation, re-read the resulting canonical files before claiming completion.
