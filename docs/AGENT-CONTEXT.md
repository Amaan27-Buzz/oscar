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
expansion is a Gate B requirement. Owner OAuth and final manual
machine acceptance PASSED; Slice 05/06 COMPLETE, Gate B PASS, Slice 07 software is accepted; physical acceptance is deferred by owner, PR 12 MERGED; Gate B frozen PASS. Historical evidence retains its original vocabulary.

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

Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).


The owner's final physical/manual machine acceptance PASSED in run
`manual-gate-b-20261004-200734`; desktop/local/public browser phases are VERIFIED.
The [accepted GitHub OAuth/federation path](GATE-B-OAUTH-ACCEPTANCE.md) uses
the existing native vault, opaque references and Connector Fabric; private email
addresses remain transient. The controlled synthetic past count remains RECALLED;
current provider count facts remain REPORTED, with separate source/temporal provenance.
Owner run `oauth-gate-b-20261004-234817` passed real private OAuth and controlled
federation. Slice 06 COMPLETE; Gate B PASS. Remote revocation remains
`UNKNOWN_OWNER_ACTION_REQUIRED`. See [final acceptance](GATE-B-COMPLETION.md).

## Owner scope decision — 2026-10-05

Slice 07: **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**.
**PHYSICAL EDGE ACCEPTANCE DEFERRED BY OWNER** — `DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`.
Protocol, firmware, Grid integration, ESP32/Pico cross-builds and deterministic
safety contracts in simulation are accepted for continuation. Historical
simulator evidence remains **SIMULATED**. No physical GPIO, watchdog, UART,
E-stop or ESP32/Pico silicon PASS is claimed. Gate C remains **PARTIAL**.

Return to real ESP32/Pico acceptance during Slice 15 physical/device expansion
and/or Slice 16 reliability/security hardening. Physical failure, loss/recovery,
watchdog and safety/reflex verification remain mandatory before Slice 17
Unified Alpha can PASS. The hardware acceptance guide is preserved.
The 2026-10-05 scope authorized Slice 08. The 2026-10-06 owner decision additionally
authorizes Slice 09 software after Slice 08 integration; Slice 10, deployment and
Galaxy Tab Home Node remain outside this work.

## Current Slice 08 — owner scope, 2026-10-06

Owner-authorized closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
This is not a physical PASS. Gate C remains **PARTIAL**.
The quality candidate on `club-c/slice-08-voice`, PR #14 into `work`, is being
validated against baseline `e8ac8f8bca1cb0cb7909523ac6af906ee289366f`.
Existing owner harnesses remain mandatory inputs to later consolidated acceptance.
Microphone, real-room AEC/barge-in/self-wake, owner Match/Map calibration, playback,
Android voice and naturalness remain NOT RUN. Windows reference evidence never
implies Android acceptance. See [Voice Core](VOICE-CORE.md) and
[consolidated Gate C acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 Sunday software may begin after clean Slice 08 integration; Slice 09 must
remain a draft and stop before owner/device acceptance. Slice 10, deployment and
Galaxy Tab Home Node are not authorized. Physical Edge remains
`DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`, mandatory before Slice 17 PASS.


## Post-alpha evolution direction

Durable future direction after stable Slice 17 Unified Alpha:

- Voice Core is cross-platform; Windows is only a reference implementation and
  Android/Sunday must reuse the same contracts through platform adapters.
- Add owner-controlled Operating Logs for model/tool/plugin/capability/Worker
  calls, routing, timing, failure/retry/fallback and verification. Keep them
  separate from conversation/capture/memory data and never silently train on them.
- Use real operating evidence to drive Elocution-informed expressive Voice Identity
  work and a Specialist Model Fabric of smaller task-optimized models.
- Gradually migrate Core, memory, voice, models and orchestration to the owner's
  dedicated home-server laptop; cloud remains explicit escalation for major work.
- This is future post-alpha scope, not a current implementation claim.

Canonical detail: [Post-Alpha Evolution](POST-ALPHA-EVOLUTION.md).
