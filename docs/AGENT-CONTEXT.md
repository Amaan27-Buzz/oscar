# Coding-agent context

OSCAR keeps one canonical project truth and uses thin agent-specific adapters. Do not duplicate the whole architecture into every tool prompt.

## Canonical files

| File | Purpose |
|---|---|
| `AGENTS.md` | repository-wide workflow, truth, safety and coding-agent rules |
| `ENGINEERING.md` | system-design/code-quality standard |
| `DESIGN.md` | visual tokens and durable design rules |
| [brand assets](../assets/brand/README.md) | canonical OSCAR Orb SVG and compatibility asset rules |
| `TASTE.md` | qualitative quality/motion/anti-slop bar |
| `docs/PRODUCT.md` | product north star |
| `docs/CHIEF-OF-STAFF.md` | ambient context, commitments, schedule/proactivity and Sunday presence |
| `docs/ARCHITECTURE.md` | system boundaries and OSCAR-owned Decision / Epistemic Controller |
| [deployment](DEPLOYMENT.md) | free-first replaceable Core/API hosts and deferred Home Node |
| `docs/MEMORY.md` | OSCAR-owned one-relationship Memory Fabric |
| `docs/ROADMAP.md` | implementation order/current slice |
| `docs/BUILD-GATES.md` | cross-slice manual verification checkpoints |
| `docs/DECISIONS.md` | durable architecture decisions |
| `docs/EPISTEMIC-INTEGRITY.md` | evidence/verification/non-yes-man contract |
| `docs/RUNTIME-FOUNDATIONS.md` | durable tasks, capabilities, channels, artifacts and automation evaluation |
| `docs/NATIVE-INFRASTRUCTURE.md` | native transport/model-routing infrastructure |
| `docs/CONNECTION-GRID.md` | Sunday/cloud/desktop/Edge availability/control fabric |
| `docs/MODEL-ROUTING.md` | provider/model/credential routing |
| `docs/SEARCH-FRESHNESS.md` | current-source/freshness authority contract |
| `docs/PERSONAL-POLICY.md` | explicit user behavioral rules |
| `docs/PERSONA.md` | configurable OSCAR character/presentation |
| `docs/VOICE-SENTRY.md` | voice layers, persistent Sentry and optional capture |
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
| `docs/CLUB-A-CHECKPOINT.md` | historical Gate A evidence/corrections |
| `docs/CLUB-B-CHECKPOINT.md` | historical/current Gate B evidence and limits |
| `image-prompts/` | optional visual-reference prompt library, not implementation truth |

Agent-specific files point back to these rather than becoming independent definitions.

## Reconciled ownership and current boundary

Controller means OSCAR's Decision / Epistemic Controller. `oscar/jev.py` is an
unchanged historical/internal filename; no TypeSafe Jev runtime/API is required.
Laya/Jev decision providers remain replaceable beneath OSCAR's hard deterministic
authority rules, with evaluation only after Gate B PASS. Auth Broker/provider/vault
expansion is a target design, not implemented universal authentication.

Oracle is the preferred free-first persistent Core candidate; Vercel supports
Python/Fluid bounded web/API/relay workloads. The Galaxy Tab S6 Lite (2021) is a
future Home Node only after full deployment and operational Core architecture.
None of deployment, Tab implementation, decision-model evaluation or full broker
expansion is a Gate B requirement. Owner OAuth is NOT STARTED, final manual
acceptance OUTSTANDING, Slice 05 COMPLETE, Slice 06/Gate B PARTIAL, Slice 07 NOT
STARTED, PR 12 DRAFT/UNMERGED. Historical evidence retains its original vocabulary.

## Context loading

More context is not automatically better. Load `AGENTS.md`, `ENGINEERING.md`, `docs/EPISTEMIC-INTEGRITY.md` and relevant domain docs.

### Memory / continuity / entities

- `docs/MEMORY.md`
- `docs/PERSONAL-POLICY.md`
- `docs/ARCHITECTURE.md`
- `docs/CLUB-B-CHECKPOINT.md` for current acceptance evidence.

### Ambient / schedule / Sunday

- `docs/CHIEF-OF-STAFF.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/PERSONAL-POLICY.md`
- `docs/COMMUNICATION.md`
- `docs/SURFACES.md`
- `docs/SECURITY.md`

### Transport / remote nodes

- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/SECURITY.md`

### Model providers / current facts

- `docs/MODEL-ROUTING.md`
- `docs/SEARCH-FRESHNESS.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/EPISTEMIC-INTEGRITY.md`

### Voice / Sentry / capture

- `docs/VOICE-SENTRY.md`
- `docs/COMMUNICATION.md`
- `docs/SECURITY.md`
- relevant surface docs.

### Persona / UI / motion

- `docs/PERSONA.md`
- `DESIGN.md`
- `TASTE.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/UI-AVATAR.md`

### Workers / orchestration

- `docs/WORKERS.md`
- `docs/ORCHESTRATION.md`
- `docs/RUNTIME-FOUNDATIONS.md`

## Durable development rule

Finish the current planned gate end-to-end before advancing to the next Club.

```text
implement
→ verify required scenarios
→ integrate
→ update evidence/docs
→ PASS
→ next Club
```

Do not use an alpha/demo deadline as justification for silently turning mandatory work into future hardening.

## Memory architecture

OSCAR owns memory continuity.

```text
one interaction point
→ Active Context
→ canonical OSCAR Event Archive (SQLite/WAL/FTS5 initially)
→ derived Qdrant semantic/hybrid index
→ derived Graphiti + Neo4j temporal/entity index
→ Retrieval Fusion / local reranker
→ Controller Memory Preflight + authority checks
→ Context Assembly
→ reasoning/action
→ Claim Verification
```

Rules:

- canonical Event Archive survives derived-index replacement/loss;
- Qdrant/Graphiti/Neo4j are rebuildable indexes, not truth owners;
- no managed memory service is mandatory;
- personal/history references trigger Controller retrieval before reasoning;
- failed first retrieval is not proof of absent memory;
- retrieval broadens through structured state → FTS/archive → Qdrant → Graphiti → aliases/time expansion → bounded deep archive → UNKNOWN;
- no `I remember X` without actually retrieved/active evidence;
- personal/historical claims retain source IDs;
- live authoritative current state outranks stale recall;
- memory extraction creates candidates with provenance, never unsupported truth;
- corrections supersede prior current facts while preserving historical source events;
- memory cannot grant permission or create Personal Policy.

See `docs/MEMORY.md`.

## Routing boundaries

```text
Controller           → what class of action/evidence is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

Coding agents, terminal, computer use and installed applications are executable capabilities, not provider keys.

Memory retrieval is also not model routing: Controller can require recall before any reasoning model is selected.

## Connection Grid

```text
Sunday      = preferred owner control / approvals / notifications
Cloud       = replaceable rendezvous + durable coordination
Desktop     = high-capability execution
Edge        = local awareness / reflex / safety
```

No desktop is a hidden permanent host. Executor loss expires leases rather than leaving false `working` state. Power/wake claims require real current capability.

## Chief of Staff

OSCAR coordinates authorized current context across time/weather/calendar/tasks/notifications/communication/device/activity/Workers rather than behaving only as prompt-response software.

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

Current decisions are freshness-qualified. Proactivity is graded from silent observation through inform/suggest/act/interrupt. Mutations require authority and verification.

## World Model vs Memory

```text
World Model = what is true now from current evidence
Memory      = historical continuity/evidence
```

Do not answer current-state questions from stale memory when a live source is reasonably available.

## Persona / Policy / Permission

```text
Persona         = how OSCAR expresses itself
Personal Policy = how user wants OSCAR to behave
Permission      = what OSCAR may do
Memory          = what OSCAR retains/recalls
```

None silently substitutes for another.

## Freshness

When current truth matters, use current authoritative sources where reasonably obtainable. Cached manifests, memory and model priors do not become current truth merely because they are convenient.

## Evidence / completion

For meaningful work:

1. define observable completion;
2. execute;
3. inspect authoritative resulting state;
4. run relevant tests/device/visual/source checks;
5. report the strongest claim evidence supports.

Worker/model/tool success is testimony until independently verified where practical.

## Sentry / capture

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

## Design direction

Canonical direction is **Quietly Alive + Playful Precision**.

Avoid generic AI dashboards, permanent chat sidebars, card walls, glass/neon/purple gradients, fake telemetry and mascot-led layouts. Simplicity must preserve craftsmanship.

## Adapter files are intentional

- `AGENTS.md` is canonical for AGENTS-aware coding agents.
- `CLAUDE.md`, `GEMINI.md`, Copilot instructions and Cursor rules are thin adapters.
- Do not delete them merely because they point to shared canonical rules.
- Historical Gate/checkpoint/evidence docs are provenance and should not be deleted as `old docs`; supersede stale plans explicitly.

## Propagation rules

When a durable rule changes, update the canonical owner first and reconcile affected docs/adapters.

- memory/continuity/retrieval → `MEMORY.md`, then Product/Architecture/Epistemic/Roadmap/Build Gates/Features/Agents as affected;
- Chief-of-Staff/context/schedule → `CHIEF-OF-STAFF.md` plus affected product/surface/policy docs;
- Grid/availability → `CONNECTION-GRID.md` + affected architecture/security/surface docs;
- Sentry/capture → `VOICE-SENTRY.md` + Communication/Security/Onboarding;
- Persona → `PERSONA.md` + affected product/policy/surface docs;
- model routing/freshness → `MODEL-ROUTING.md` + `SEARCH-FRESHNESS.md`;
- system design → `DESIGN.md` + `TASTE.md`;
- engineering invariant → `ENGINEERING.md`;
- architecture decision → `DECISIONS.md` plus affected domain docs.

After propagation, re-read canonical files before claiming completion.

## Gate B local completion candidate — 2026-10-04

Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).


The owner's final physical/manual machine acceptance PASSED in run
`manual-gate-b-20261004-200734`; desktop/local/public browser phases are VERIFIED.
The [prepared GitHub OAuth/federation acceptance](GATE-B-OAUTH-ACCEPTANCE.md) uses
the existing native vault, opaque references and Connector Fabric; private email
addresses remain transient. The controlled synthetic past count remains RECALLED;
current provider count facts remain REPORTED, with separate source/temporal provenance.
Real owner OAuth/private federation is not yet exercised. Gate B remains PARTIAL.
