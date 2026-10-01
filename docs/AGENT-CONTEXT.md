# Coding-agent context

OSCAR keeps one canonical project truth and uses thin agent-specific adapters. Do not duplicate the whole architecture into every tool prompt.

## Canonical files

| File | Purpose |
|---|---|
| `AGENTS.md` | repository-wide workflow, safety, truth and coding-agent rules |
| `ENGINEERING.md` | system-design/code-quality standard |
| `DESIGN.md` | normative visual tokens and durable design rules |
| `TASTE.md` | qualitative taste / anti-slop / motion quality bar |
| `docs/PRODUCT.md` | product north star |
| `docs/ARCHITECTURE.md` | system boundaries and ownership |
| `docs/ROADMAP.md` | implementation order/current slice |
| `docs/BUILD-GATES.md` | cross-slice manual verification checkpoints |
| `docs/DECISIONS.md` | durable architecture decisions |
| `docs/EPISTEMIC-INTEGRITY.md` | evidence/verification/non-yes-man contract |
| `docs/RUNTIME-FOUNDATIONS.md` | durable tasks, capability search, channels, artifacts, automation evaluation |
| `docs/NATIVE-INFRASTRUCTURE.md` | native OSCAR transport and model-routing infrastructure |
| `docs/CONNECTION-GRID.md` | Sunday/cloud/desktop/Edge availability and remote-control fabric |
| `docs/MODEL-ROUTING.md` | provider/model/credential routing |
| `docs/MEMORY.md` | LRA/Supermemory continuity |
| `docs/PERSONAL-POLICY.md` | explicit user behavioral rules |
| `docs/PERSONA.md` | configurable OSCAR character/presentation |
| `docs/VOICE-SENTRY.md` | voice layers, persistent Sentry and optional continuity capture |
| `docs/COMMUNICATION.md` | calls/messages/email/meetings/dictation/capture |
| `docs/WORKERS.md` | delegated Worker lifecycle/recovery |
| `docs/ORCHESTRATION.md` | routing, Skills, Workers, routines and Protocols |
| `docs/SURFACES.md` | Sunday/desktop/cloud/Edge surface roles |
| `docs/SUNDAY-DESIGN.md` | Sunday mobile interaction direction |
| `docs/UI-AVATAR.md` | avatar/state/motion language |
| `docs/ONBOARDING.md` | commissioning |
| `docs/SECURITY.md` | permissions, transport, voice/capture/Grid security |
| `docs/FEATURES.md` | comprehensive capability backlog |
| `image-prompts/` | optional visual-reference prompt library; not implementation truth |

Agent-specific files should point back to these rather than becoming independent product definitions.

## Context loading

Load only the context needed for the task.

### Any implementation

- `ENGINEERING.md`
- `docs/EPISTEMIC-INTEGRITY.md`
- relevant product/architecture/domain docs.

### Transport / remote nodes / cloud / availability

- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/SECURITY.md`

### Model providers / credentials / routing

- `docs/MODEL-ROUTING.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/EPISTEMIC-INTEGRITY.md`

### Voice / Sentry / recording / communication

- `docs/VOICE-SENTRY.md`
- `docs/COMMUNICATION.md`
- `docs/SECURITY.md`
- relevant surface docs;
- `docs/ONBOARDING.md` when enrollment/configuration is involved.

### Persona / interaction design

- `docs/PERSONA.md`
- `DESIGN.md`
- `TASTE.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/UI-AVATAR.md`
- relevant surfaces.

### Memory / policy

- `docs/MEMORY.md`
- `docs/PERSONAL-POLICY.md`
- `docs/PERSONA.md` if tone/style and behavior rules risk being conflated.

### Workers / orchestration

- `docs/WORKERS.md`
- `docs/ORCHESTRATION.md`
- `docs/RUNTIME-FOUNDATIONS.md`

### Manual acceptance

- `docs/BUILD-GATES.md`
- relevant detailed slices in `docs/ROADMAP.md`.

More context is not automatically better.

## Native infrastructure rule

Do not revive separate Latch/SwitchRoute runtime dependencies.

```text
Latch architecture/logic       → OSCAR Transport + Capability Fabric
SwitchRoute architecture/logic → OSCAR Model Router
```

ChatGPT reaches OSCAR through an OSCAR-owned connector/transport boundary. The connector is a doorway, not OSCAR's host/intelligence.

## Three routing decisions stay separate

```text
Jev                  → what class of action is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

Coding agents, terminal, computer use and installed applications are executable capabilities, not provider keys.

## Connection Grid rule

```text
Sunday      = preferred owner control / approvals / notifications
Cloud       = replaceable rendezvous + durable coordination
Desktop     = high-capability execution
Edge        = local awareness / reflex / safety
```

- no desktop is a hidden permanent host;
- cloud may be free-tier, paid or BYOC;
- cross-node actions remain capability/permission scoped;
- Sunday can pause/cancel/revoke owner-authorized work but not override deterministic hardware safety;
- remote sleep/shutdown/wake is shown only when a real target capability exists;
- executor loss must expire/reclaim task leases instead of leaving false `working` state;
- degraded availability is explicit.

## Sentry / capture rule

Sentry means persistent local-first awareness when enabled.

Keep separate:

```text
Sentry Aware
Listening
Muted
Acoustic Awareness Off
Context Capture
Daily Journal
```

Awareness does not automatically mean recording.

Optional capture may include selected calls/messages/email/meetings/in-person conversations only where platform capability, permission, consent and law allow.

Keep raw audio, transcript, summary and memory extraction retention separate. Unsupported app/call capture remains unsupported. Do not design covert capture as the default.

## Persona rule

Persona changes **presentation**, not truth or authority.

Possible traits: humor, candor, warmth, formality, brevity, playfulness, initiative, pushback.

```text
Persona         = how OSCAR expresses itself
Personal Policy = how user wants OSCAR to behave
Permission      = what OSCAR may do
Memory          = what OSCAR retains/recalls
```

Epistemic Integrity, safety, consent and permission cannot be lowered by Persona configuration.

## Evidence / completion rule

For meaningful work:

1. define observable completion;
2. execute;
3. inspect authoritative resulting state;
4. run relevant tests/device/visual/source checks;
5. report the strongest claim evidence supports.

A model/tool/Worker/commit response is not automatically objective proof.

Use `reported`, `verifying`, `verified`, `partially verified`, `failed`, `blocked`, `unknown` accurately.

## Design rule

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

Avoid generic AI dashboards, permanent chat sidebars, card walls, glass/neon/purple gradients, obvious neumorphism, fake telemetry and mascot-led layouts.

Use Kaizen for UI: research shipping patterns → build one real surface → visually inspect → improve biggest weakness → verify → expand.

`image-prompts/` can aid exploration; coded UI is product truth once implementation exists.

## Adapter files

- `AGENTS.md` is canonical for AGENTS-aware coding agents.
- `CLAUDE.md`, `GEMINI.md`, Copilot instructions and Cursor rules stay thin adapters.
- Nested `AGENTS.md` files should appear only when a real subtree develops materially different rules.

## Portable Skills

Reusable workflows live under `skills/` and should not bloat global agent context.

## Propagation rules

When a durable rule changes, update the canonical domain doc first, then reconcile only affected docs/adapters.

- Connection Grid/availability → `CONNECTION-GRID.md`, `NATIVE-INFRASTRUCTURE.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `BUILD-GATES.md`, `SECURITY.md`, `SURFACES.md`, README.
- Sentry/capture → `VOICE-SENTRY.md`, `COMMUNICATION.md`, `SECURITY.md`, `ONBOARDING.md`, `FEATURES.md`, `ROADMAP.md`, relevant surfaces, README.
- Persona → `PERSONA.md`, `PRODUCT.md`, `PERSONAL-POLICY.md`, `VOICE-SENTRY.md`, `SURFACES.md`, onboarding/design docs where relevant.
- Model routing/credentials → `MODEL-ROUTING.md`, native infrastructure, roadmap/features/UI data requirements.
- System-wide design → `DESIGN.md` + `TASTE.md` + affected surface docs.
- Engineering invariant → `ENGINEERING.md`.
- Architecture invariant → `DECISIONS.md` plus affected architecture/roadmap/domain docs.

After propagation, re-read the resulting canonical files before claiming completion.
