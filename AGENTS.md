# AGENTS.md — active development instructions (2026-10-18)

**Read before any OSCAR work:** [Current status](docs/CURRENT-STATUS.md), [new delivery groups](docs/DELIVERY-PLAN.md), [canonical slices](docs/SLICE-NUMBERING.md), [roadmap](docs/ROADMAP.md), [build gates](docs/BUILD-GATES.md) and [deployment](docs/DEPLOYMENT.md).

## Current owner sequencing and authorization

- Software foundations Slices **00–17 are integrated**. Single **Group 3 Slices 14–17, PR #7 is MERGED**, not a draft requiring completion. GitHub Actions was enabled; final-head and main CI passed. **Gate C/D PARTIAL**, Gate E NOT PASSED.
- Next **Group 4 D1** persistent secure Cloud Core (Oracle Always Free preferred **candidate**, not deployed), then **D2** authenticated remote Grid. **Group 5** real Desktop/Android and owner onboarding, full computer use, plugins/MCP, Secure/Full Access, real voice, Sentry, automation and Chief of Staff. **Group 6** scoped operational alpha. **Group 7** dedicated home-server laptop *when available*. **Group 8** ESP32/Pico physical acceptance and remaining formal gates.
- **Keep canonical slices 00–20**. Delivery stages D1–D4/C1–C4 and Groups 4–8 are not renumbered slices. Physical **Slice 18 is deferred, not cancelled**; remote-facing Slice 19 hardening is mandatory in Group 4. A scoped alpha must not claim full Slice 20 / Gate E PASS while mandatory physical acceptance remains incomplete.
- Preserve **one authoritative OSCAR** identity/Core, Controller, Event Archive/Memory, Grid, Policy, Executive, native app designs and canonical Orb. Any capability claiming full PC control, connector authorization or Full Access requires actual enforcement and independent verification.
- Existing Ask is current. **Full Access** is owner-authorized autonomy over technically available capabilities **without OSCAR per-action prompts** once properly activated; it cannot bypass OS/provider constraints, external mandatory approval, provenance, revocation or deterministic physical safety. Perception, retention and action grants are separate.
- The active Group 4/D1 engineering closure authorizes correcting and integrating **PR #8** only after reviewed fixes, successful exact-head CI and reconciliation with main, followed by post-merge main CI. This supersedes the earlier draft-only restriction. Oracle procurement/provisioning, cloud billing, public firewall/DNS changes, owner/provider enrollment, firmware flashing, real audio capture and release remain separately authorized commissioning work. Stop after D1 software closure; do not begin D2 in this run.
- **All obsolete PR-specific and dated run prohibitions from 2026-10-04 through 2026-10-17 are superseded**; read historical implementation/evidence receipts for provenance, not as current instructions. Preserve that history in Git. Don't add another Group 3 or resurrect PR #7.

## Durable engineering standards

## Read first

For implementation work read:

- `README.md`
- `ENGINEERING.md`
- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/EPISTEMIC-INTEGRITY.md`
- relevant domain docs.

Load additionally when relevant:

### Memory / continuity / entities

- `docs/MEMORY.md`
- `docs/PERSONAL-POLICY.md`
- `docs/CLUB-B-CHECKPOINT.md`

### Transport / availability / routing

- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/MODEL-ROUTING.md`
- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/SEARCH-FRESHNESS.md`

### Ambient context / schedule / communication

- `docs/CHIEF-OF-STAFF.md`
- `docs/PERSONAL-POLICY.md`
- `docs/COMMUNICATION.md`
- `docs/CONNECTOR-FABRIC.md`
- `docs/SURFACES.md`

### Voice / Sentry

- `docs/VOICE-SENTRY.md`
- `docs/COMMUNICATION.md`
- `docs/ONBOARDING.md`
- `docs/SECURITY.md`

### Persona / UI / motion

- `DESIGN.md`
- `TASTE.md`
- `docs/PERSONA.md`
- `docs/UI-AVATAR.md`
- `docs/MOBILE-DESIGN.md`

### Workers / orchestration

- `docs/ORCHESTRATION.md`
- `docs/WORKERS.md`
- `docs/RUNTIME-FOUNDATIONS.md`

Treat these as current product contract. If code/docs/evidence disagree, investigate rather than silently choosing the convenient version.

## Development rule

OSCAR is built gate-by-gate, end-to-end.

```text
finish planned slice/gate
→ verify mandatory acceptance
→ integrate
→ update canonical docs/evidence
→ advance
→ later expand/harden
```

The owner explicitly re-scoped the post-Group-3 execution order: Groups 4–6 deliver a *scoped* Cloud–Desktop–Phone alpha before Group 7 home-server and Group 8 physical Edge. Unfinished original Gate C/D/E obligations remain PARTIAL and cannot be silently treated as passed.

## Working style

- One coherent slice/sub-slice at a time.
- Inspect existing infrastructure before inventing replacements.
- Prefer the smallest robust design.
- High cohesion / low coupling; avoid god objects and wrapper forests.
- Do not create fake/demo states that imply unfinished capability works.
- Preserve failure, blocked, partial and unknown states.
- Use specialist tools when they are the right executor.
- Do not add a dependency without a concrete reason.
- Update durable docs in the same change when a real invariant changes.
- Freshness-sensitive objectives retrieve current authoritative evidence before relying on memory/model priors.

## Native infrastructure

Do not make Latch, SwitchRoute, a managed memory vendor, LangGraph, Letta or another agent framework a required OSCAR runtime.

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
Memory services         → optional adapters behind OSCAR-owned Memory Fabric
```

OSCAR owns identity, task state, memory provenance, authority and verification.

## OSCAR-owned controller

Controller means OSCAR's Decision / Epistemic Controller, implemented today by
OSCAR-owned deterministic logic in `oscar/jev.py` (temporary historical/internal
name). No TypeSafe Jev runtime/API is required. Hard safety, permission, Personal
Policy, live-vs-memory, confirmation and consequential-action rules are authoritative.
Laya/Jev decision providers are replaceable implementations beneath this boundary;
System-1 evaluation starts only after Gate B PASS.

See [deployment](docs/DEPLOYMENT.md) and [shared auth](docs/CONNECTOR-FABRIC.md).
Oracle persistent Core deployment and authenticated remote Grid are now the Group 4 priority; Vercel remains complementary. Galaxy Tab, Home Node and physical Edge are later work and not retroactive Gate B requirements. Do not implement the Tab node before
OSCAR is fully deployed and its main Core architecture is operational.

## Three routing decisions remain separate

```text
Controller           → what class of action/evidence is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

Coding agents, terminal, computer use and installed applications are executable capabilities, not provider keys.

## OSCAR Memory Fabric

Canonical memory architecture is defined in `docs/MEMORY.md`.

### Ownership

- OSCAR Event Archive is canonical history.
- Initial canonical store: SQLite + WAL + FTS5.
- Qdrant OSS is the first semantic/hybrid derived index.
- Graphiti OSS + Neo4j Community are the first temporal/entity derived index.
- Embeddings/rerankers are replaceable local/provider capabilities.
- Derived indexes must be rebuildable from canonical events.
- No managed memory service is required.

### One interaction point

The product exposes one continuous OSCAR relationship. Internal events/episodes/projects/tasks are structured for scaling and retrieval but do not force `new chat` management on the user.

### Controller Memory Preflight

Do not let the reasoning model casually decide whether it remembers something.

If a request plausibly depends on prior user/project/entity/task/artifact/preference/history context, Controller routes through memory retrieval before answering.

Examples requiring retrieval include:

- `continue that`;
- `same as before`;
- `what did we decide?`;
- references to an existing project/person/device/artifact;
- personal preferences/history;
- corrections or contradictions.

### Retrieval ladder

Use bounded escalation:

```text
active context
→ structured OSCAR state/entities/tasks/policy
→ Event Archive exact/FTS5
→ Qdrant hybrid
→ Graphiti temporal/entity
→ alias/entity/time-range query expansion
→ bounded deep archive reconstruction
→ UNKNOWN
```

An empty search result is not proof that memory never existed.

### Recall truth rules

- Never say or imply `I remember X` unless X was actually retrieved or remains in active context with provenance.
- Personal/historical factual claims require source event/memory evidence.
- Retrieved historical material is `RECALLED`; retrieval does not make it current `VERIFIED` truth.
- Live authoritative state outranks stale memory when current truth matters.
- The reasoning model cannot promote inference into fact.
- Derived memory/index records retain canonical source IDs.
- Corrections supersede historical facts temporally rather than silently rewriting history.
- Memory does not grant permission or create Personal Policy.

### Memory formation

Model extraction produces candidates, not automatic truth:

```text
source event
→ extract
→ scope/classify
→ resolve entities
→ compare/conflict check
→ provenance + epistemic state
→ retention decision
→ update derived indexes
```

Overgeneralization is a defect. `I dislike this rounded UI` does not automatically become `user hates all rounded UI`.

### Memory evaluation

Gate B must include meaningful tests for exact recall, paraphrase recall, temporal supersession, entity alias/disambiguation, retrieval-miss escalation, stale-memory-vs-live, corrections, forget/delete, rebuild/drift and false-recall behavior.

## Connection Grid

OSCAR availability spans:

```text
OSCAR Mobile      = preferred owner control / approvals / notifications
Cloud       = replaceable rendezvous + durable coordination
Desktop     = high-capability execution
Edge        = local presence / reflex / safety
```

Rules:

- no ordinary desktop is the permanent host;
- nodes advertise only real current capabilities;
- cross-node control is scoped and rechecked at the target;
- executor loss expires leases rather than leaving false `working` state;
- remote sleep/shutdown/wake is offered only when a real capability exists;
- availability degrades explicitly rather than pretending a dead node is alive.

## Ambient Chief-of-Staff invariant

OSCAR continuously integrates authorized current context and helps coordinate the user's day.

Potential live inputs include time/date/timezone, weather, calendar, tasks/deadlines, location/mobility, device/app/media state, notifications, communications, Worker/Protocol state and Sentry/Edge observations.

Rules:

- volatile context is freshness-qualified and source-backed;
- weak activity signals remain uncertain rather than mind-reading;
- perception, durable retention and authority to act are separate grants;
- schedule/task/communication mutations require capability + permission/Personal Policy + verification;
- proactivity ranges from silent context update to inform/suggest/act/interrupt rather than one global switch;
- attention state should reduce unnecessary interruption and obstruction.

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

## Evidence and completion claims

A tool call, commit, Worker/model message or API `success` is not proof of the objective.

For meaningful work:

1. define observable completion;
2. execute;
3. inspect authoritative resulting state;
4. run appropriate tests/device/visual/source verification;
5. report only what evidence supports.

Preserve `reported`, `verifying`, `verified`, `partially_verified`, `failed`, `blocked` and `unknown` distinctions.

Do not say `done`, `fixed` or `works` when evidence is only partial/reported.

## Core invariants

1. One intelligence, many embodiments.
2. Laptop/desktop nodes are optional.
3. Hardware safety is local/deterministic.
4. Voice and text share task/context state.
5. OSCAR Mobile is OSCAR on the phone, not a second assistant.
6. OSCAR owns the canonical Memory Fabric and one continuous relationship.
7. World Model owns current-state representation; memory is historical evidence, not current truth by default.
8. Controller chooses execute/retrieve/verify/reason/delegate/ask class and performs memory preflight when required.
9. Model routing and executable capability selection are separate.
10. Nodes advertise capabilities dynamically.
11. Consequential actions are permission-aware, attributable and evidence-backed.
12. Long-running work uses Durable Execution Runtime when persistence/recovery matters.
13. Voice Match and Voice Map are distinct; recognition is not authorization.
14. OSCAR owns stable Voice Identity independent of TTS vendor.
15. Sentry awareness, active Listening and durable capture are distinct.
16. Persona changes expression, never truth/safety/permission.
17. Freshness-sensitive claims require live authoritative retrieval when reasonably available.
18. `CAN PERCEIVE`, `CAN RETAIN` and `CAN ACT` are independent.
19. A failed memory retrieval is not proof of absence.
20. Any historical/personal answer presented as recalled requires evidence provenance.

## Search / freshness

Search is a first-class capability, not an excuse for stale reasoning.

- classify whether current/live truth matters;
- prefer authoritative APIs/live sources over summaries when available;
- preserve source identity, relevant timestamps and observation time;
- cached manifests/memory/model priors are not current authority;
- if live lookup is unavailable, report stale/UNKNOWN rather than guess;
- Tavily is an implemented replaceable search adapter, not an architectural dependency.

See `docs/SEARCH-FRESHNESS.md`.

## OSCAR Mobile / Android

OSCAR Mobile uses legitimate Android platform capabilities rather than pretending to have system privilege. Assistant role, overlay, widgets, notification access, replies, microphone/camera and retention/action authority remain separate permissions/capabilities. OEM-specific behavior is unverified until exercised on the target device.

## Persona / voice / Sentry

Persona may affect humor, candor, warmth, formality, brevity, playfulness, initiative and pushback, but never truth/safety/permission.

Voice Input, Voice Identity, Voice Match and Voice Map remain separate contracts. Unknown speakers remain unknown. Voice profiles/embeddings are sensitive. OSCAR's own TTS is excluded from wake/Voice Map loops while human barge-in remains functional.

Persistent Sentry awareness does not imply continuous cloud transcription or raw-audio retention.

## Specialist delegation

Examples:

- repository implementation/debugging → Codex/coding capability;
- GUI-only operation → computer-use capability;
- knowledge workspace → native connector/plugin;
- model reasoning → Controller then native Model Router;
- physical action → advertised Edge/device capability.

## UI / design quality

Durable direction: **Quietly Alive + Playful Precision**.

Use [the canonical OSCAR Orb](assets/brand/oscar-orb.svg) for scalable identity
artwork. Derive future variants from it rather than recreating the Orb; preserve
its core visual identity. See [brand assets](assets/brand/README.md).

Avoid generic AI dashboards, card walls, glass/neon/purple-gradient slop and fake telemetry. Simplicity must preserve craftsmanship. UI/avatar state reflects real runtime state.

## Testing expectations

Every slice has explicit acceptance including relevant failure/reconnect/cancellation/idempotency/safety cases.

Where relevant test:

- provider/node loss;
- Grid reconnect/lease expiry;
- remote task continuation/cancel;
- freshness vs stale cache/model prior;
- memory exact/semantic/temporal/entity retrieval;
- expected-memory miss escalation;
- correction/supersession/forget/rebuild;
- browser/computer-use verification;
- wake/VAD/STT/TTS/barge-in;
- Android assistant/overlay/widget/notification behavior on real hardware;
- schedule mutation readback;
- simulator vs real hardware separately.

## Secrets / personal data

Never commit or casually log API/provider keys, OAuth/device credentials, private memory exports, raw conversation archives, Voice Map embeddings/profiles, private recordings or local `.env` secrets.

Use ignored local fixtures or synthetic test data.

## Historical evidence, not instructions

Prior task-specific owners' stop boundaries, previous PR SHAs, Group 2.5 iteration notes, and the old “Slice 17 Unified Alpha” number are preserved in repository Git history and dated reports. The canonical Alpha milestone is **Slice 20**; a smaller Group 6 Cloud–Desktop–Phone **operational alpha** can be accepted without pretending to have physically verified Slice 18. Review [delivery plan](docs/DELIVERY-PLAN.md) for exact outstanding checklists.
