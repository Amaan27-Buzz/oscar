# Roadmap

This roadmap is slice-based. Each slice must leave OSCAR coherent/testable and update affected canonical docs in the same change.

All implementation follows `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`.

Related contracts:

- `docs/BUILD-GATES.md`
- `docs/PRODUCT.md`
- `docs/CHIEF-OF-STAFF.md`
- `docs/ARCHITECTURE.md`
- `docs/MEMORY.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/MODEL-ROUTING.md`
- `docs/SEARCH-FRESHNESS.md`
- `docs/VOICE-SENTRY.md`
- `docs/PERSONA.md`
- `docs/RUNTIME-FOUNDATIONS.md`

## Development principle

Build OSCAR's nervous system first, finish each planned gate end-to-end, then attach the next embodiment.

```text
objective / event
→ current context + Jev
→ memory/live retrieval/capability/model decision
→ permission + Personal Policy
→ execute
→ receive result
→ collect evidence
→ verify
→ update World Model / Memory Fabric / commitments
→ report only what evidence supports
```

A partial gate is not skipped merely because it is demoable. Mandatory planned work is completed, verified and integrated before the next Club begins unless the owner explicitly changes scope.

Early development may run on a development PC for convenience. The PC is never OSCAR's permanent host.

## Status legend

- ✅ accepted/verified for stated scope
- 🚧 implemented foundation, broader slice still incomplete
- ⏭️ current next work
- ◻️ planned

## Slice 00 — Repository / architecture foundation ✅

Established product/architecture/engineering/design rules, Epistemic Integrity, World Model/Perception direction, Personal Policy, Workers/Protocols, Durable Execution Runtime, Capability Catalog, Action Ledger, Artifact Model, native transport/model-routing direction, Connection Grid, Persona and build gates.

## Slice 01 — OSCAR Core Loop ✅

Verified evidence-backed objective → action → result → independent verification loop. Fake executor success cannot become verified completion.

See [Club A checkpoint](CLUB-A-CHECKPOINT.md).

## Slice 02 — TypeSafe Jev ✅

Verified typed deterministic/epistemic routing for known/world/recall/verify/reason/reported/specialist/worker/unknown paths, with conservative handling of missing capability and freshness-sensitive retrieval.

Jev is now also the architectural owner of Memory Preflight/retrieval escalation requirements defined in [MEMORY.md](MEMORY.md); the production Memory Fabric implementation is Slice 06 work.

## Slice 03 — Native Transport + Capability Catalog + Connection Grid foundation ✅

Slice 03 is accepted and complete for its planned reference foundation. Public deployment remains later deployment scope.

Verified behavior includes scoped pairing/auth, capability advertisement/search, replay protection, correlation, cancellation, progress, heartbeats, durable leases, disconnect/expiry/reclaim and explicit availability states.

Later deployment work still includes public TLS/outbound rendezvous, independent network-node stores and real Sunday/Desktop/Edge deployment.

## Slice 04 — Native Model Router + cloud intelligence ✅/🚧

**Gate A accepted for the current foundation.**

Implemented/verified scope includes:

- provider/model/credential registry and multi-key pools;
- account-product/shared-quota semantics;
- Auto/Fast/Balanced/Heavy Duty/Free First/Cheap/Local/Private/Manual/Specialist modes;
- bounded fallback and real provider evidence;
- dynamic/fresh inventory rather than stale model seeds;
- Tavily behind a replaceable search-provider boundary;
- source/time/provenance-qualified current search;
- UNKNOWN rather than stale model-prior fabrication.

**Gate A — PASS.**

## Slice 05 — Real machine Worker + remote continuation ✅

**COMPLETE for Windows local-alpha acceptance in this candidate.** Typed PowerShell, registered Notepad/UIA, browser fixture/public-page work and separate owner-control continuation have now been exercised. See [completion ledger](GATE-B-COMPLETION.md). Trusted-host execution is not a sandbox; independent network stores, phone/power and hostile-host isolation remain unverified.

Already verified in the local Windows pass:

- reparse-aware filesystem operations;
- native Job Object process-tree control;
- Git work;
- useful Codex bug repair independently tested;
- cancellation;
- coordinator/Worker OS-process restart and recovery;
- no duplicate accepted mutation on lost-result recovery;
- ambiguous post-mutation Worker loss blocks replay;
- explicit trusted-host boundary rather than fake sandbox claims.

### Slice 05 acceptance contract — exercised for stated local scope

#### 05A — Typed terminal / PowerShell

- discover legitimate installed PowerShell executable;
- expose as typed/allowlisted terminal capability;
- bounded harmless real execution;
- cwd/environment/output/timeout/cancel verification;
- no OSCAR provider credentials inherited.

#### 05B — Installed application catalog

- discover real installed apps from legitimate Windows sources;
- stable app IDs and provenance;
- launch/availability metadata;
- do not infer capabilities merely from executable presence;
- real harmless app acceptance such as Notepad if present.

#### 05C — Windows computer use

- structured Windows UI Automation first;
- bounded top-level window/element inspection;
- focus/read/invoke/set-value where legitimate;
- keyboard/mouse fallback only when structured automation is unavailable;
- independent UI state verification;
- no polished Slice 10 UI work yet.

#### 05D — Typed browser runtime

- isolated browser context;
- navigate/inspect URL/title/DOM/text;
- click/fill/submit/wait/screenshot/close;
- cancellation/timeouts/output bounds;
- deterministic local-fixture acceptance;
- bounded public-page acceptance;
- independent post-action DOM/state verification;
- browser capability stays distinct from OSCAR Search.

#### 05E — Owner-control / long-running continuation

Using existing Grid contracts and a separate control process:

```text
start bounded long-running task
→ control client observes task/progress/node state
→ control client disconnects
→ permitted Worker continues
→ control client/coordinator reconnects
→ same task recovered
→ pause/resume where genuinely supported or cancel
→ no duplicate execution
→ independently verified final state
```

This proves OSCAR is conceptually independent of the computer executing the task.

#### 05F — Power-control contract

Sleep/shutdown/restart may be modeled only if real OS capability exists. These are high-risk and require explicit owner confirmation. Do not shut down the development machine merely to satisfy automated Gate B acceptance.

## Slice 06 — OSCAR Memory Fabric + Personal Policy + live context ⏭️

The previous planned managed-memory backend has been retired. OSCAR now owns a free/self-hosted Memory Fabric.

Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

### 06A — Canonical Event Archive

Implement/verify:

- SQLite WAL canonical event history;
- FTS5 exact/full-text recall;
- stable event/turn/episode/entity/memory/source IDs;
- provenance and epistemic state;
- retention metadata;
- correction/supersession relationships;
- archive remains recoverable independent of derived indexes.

### 06B — Qdrant OSS semantic index

Implement as derived/rebuildable state:

- dense semantic retrieval;
- sparse/lexical component where useful;
- hybrid retrieval;
- project/entity/time/type filters;
- canonical archive IDs on every indexed record;
- index rebuild and drift detection.

### 06C — Graphiti + Neo4j Community temporal/entity index

Implement as derived/rebuildable state:

- canonical entities/aliases;
- relationships;
- temporal validity;
- current-vs-historical facts;
- correction/supersession propagation;
- source-event provenance;
- ambiguous/same-name entities remain separate until evidence supports linking.

### 06D — Local embeddings + reranker boundary

- replaceable embedding interface;
- replaceable reranker interface;
- local/self-hosted default where practical;
- optional Model Router/provider paths without architectural dependence;
- no provider-specific memory truth.

### 06E — Jev Memory Preflight + Retrieval Planner

Every interaction gets a cheap memory-dependency classification.

Mandatory recall path when personal/history/project/entity/artifact/preference context may matter:

```text
active context
→ structured OSCAR state/entities/tasks/policy
→ Event Archive exact/FTS5
→ Qdrant hybrid
→ Graphiti temporal/entity
→ alias/entity/time-range expansion
→ bounded deeper archive reconstruction
→ UNKNOWN
```

An empty first retrieval is not proof of absent memory.

### 06F — Evidence-bound recalled claims

- no `I remember X` unless X was actually retrieved/active with provenance;
- historical/personal claims bind to source event/memory IDs;
- recalled evidence remains RECALLED in the current answer;
- model reasoning cannot promote recall/inference to verified fact;
- current authoritative live state outranks stale memory.

### 06G — Memory Writer + consolidation

- source events generate scoped candidates, not automatic truth;
- entity resolution before generalization;
- contradiction detection;
- temporal supersession rather than history rewriting;
- background dedup/evidence merge/summary/index maintenance;
- source events remain canonical.

### 06H — Forget / rebuild / resilience

- remove/tombstone live OSCAR memory according to retention policy;
- remove relevant vector/graph index entries;
- no false secure-erasure claim;
- rebuild Qdrant and temporal graph from canonical archive;
- fail closed to FTS/archive/UNKNOWN when a derived index is unavailable.

### 06I — Memory evaluation suite

Benchmark with synthetic/non-sensitive histories:

- exact recall;
- paraphrased semantic recall;
- temporal current-vs-history;
- preference supersession;
- entity aliases/same-name disambiguation;
- project switching;
- false-memory claims;
- expected-memory miss escalation;
- stale-memory-vs-live;
- correction;
- forget;
- index rebuild/drift;
- cross-process continuity.

### 06J — Open-ended Personal Policy

Complete the safe interpretation path:

```text
natural-language rule
→ bounded structured candidate
→ show exact interpretation
→ explicit owner confirmation
→ active rule
```

Support scoped conditions/effects, ambiguity rejection, equal-authority conflict blocking and expiry where stated. A policy cannot grant permission, bypass strong confirmation or weaken hard safety.

### 06K — Real private connector + OAuth lifecycle

Complete at least one genuinely useful private service end-to-end using current official auth flows:

- proper OAuth/PKCE/device/system-browser flow as appropriate;
- minimal scopes;
- state/nonce validation;
- refresh/expiry/revoke lifecycle where supported;
- platform secure-credential boundary;
- no raw token in model prompts, memory, ledger, logs or repository;
- harmless bounded private read acceptance;
- one reversible write/readback/cleanup only with explicit owner approval.

### 06L — Live context federation

Demonstrate authoritative current evidence defeating stale recall while preserving historical provenance.

At minimum combine current local project/file/task state, one authenticated private source when available and public/search evidence where appropriate.

This is the Gate B continuity foundation, not the full Slice 11 World Model.

## Gate B completion condition

Gate B becomes PASS only when required Slice 05 and Slice 06 acceptance is genuinely exercised and evidence-backed.

A green unit suite alone is insufficient.

Once Gate B passes, merge/review/freeze its accepted baseline before Slice 07 begins.

## Slice 07 — OSCAR Edge + reflexes ◻️

Starts only after Gate B PASS.

Deliverables:

- ESP32 gateway/client;
- Pico deterministic controller where used;
- typed ESP32↔Pico events;
- health/capability advertisement;
- GPIO/sensor/display test capabilities;
- watchdog/safe defaults;
- reflex/emergency-stop path;
- reconnect/offline behavior;
- optional LAN helper/Wake-on-LAN only when real;
- simulator + physical-device verification.

## Slice 08 — Voice Core + Voice Identity + Voice Match/Map + Persona runtime ◻️

Deliverables include wake/VAD/STT, barge-in/echo cancellation, stable VoiceProfile, speaking modes/fallback, Voice Match, Voice Map, self-voice suppression, multi-device arbitration and Persona runtime/context triggers.

## Slice 09 — Sunday + communication + Connection Grid owner controls ◻️

Native Android embodiment including assistant role where supported, OSCAR Orb overlay, attention-aware retreat, widgets, notification listener, legitimate notification replies, voice/text continuity, biometric/PIN approvals, Grid owner controls, remote task supervision, initial communication actions and Samsung/OEM real-device acceptance.

## Slice 10 — Desktop Interaction Runtime ◻️

Polished native desktop embodiment: ambient presence, Dictate/Edit/Ask/Act, focused app/window/selection/accessibility/screenshot context, approvals/task progress and fluid state transformations.

## Slice 11 — World Model + Perception Fabric + persistent Sentry + optional Daily Journal ◻️

Coherent current truth across people/places/devices/apps/projects/tasks/commitments, freshness/provenance, screen/device/sensor/location/communication/acoustic inputs, time/weather/calendar/tasks/notifications/media state, Sentry modes and optional retention-controlled Context Capture/Daily Journal.

## Slice 12 — Commissioning / setup ◻️

Identity, Persona, Personal Policy starter rules, Voice Identity/Match/Map, Connection Grid pairing, model/cloud setup, Sunday/Desktop/Edge pairing, Sentry/capture setup and human-readable perceive/retain/act permission matrix.

## Slice 13 — Avatar / presence UI ◻️

Reusable blue-shell/yellow-puck presence with weighted motion, real runtime states, reduced motion and compact/overlay/widget variants. Avatar expresses real state; it never substitutes for it.

## Slice 14 — Executive Planner + durable Workers + learning ◻️

Priority/deadline/dependency planning, explicit commitment model, schedule conflicts, focus blocks, travel/weather-aware planning, policy-bounded automatic replanning, proactive brief, interruption policy, Worker lifecycle/recovery and evaluated learned automation.

## Slice 15 — Physical/device expansion + specialist engineering ◻️

Broaden Edge/device onboarding, smart-home/environment adapters, cameras/sensors/actuators and specialist CAD/circuit/simulation/3D/numerical/diagnostic routing.

## Slice 16 — Reliability/security/truthfulness hardening ◻️

Deliberately break providers, auth, Grid nodes, leases, Workers, Memory Fabric derived indexes, capture sources, persona/voice identity, privacy/retention, notification/assistant/overlay permissions and physical paths. Verify graceful degradation, revocation and no false-success behavior.

## Slice 17 — Unified alpha ◻️

Run one end-to-end scenario across:

```text
perception / communication
→ World Model / Chief-of-Staff context / Jev
→ Memory Fabric / live evidence
→ Personal Policy + Persona
→ Executive / Durable Runtime
→ capability / search / model routing
→ Connection Grid node
→ Worker / device / action
→ ledger / artifact
→ verification
→ voice/text/Sunday report
```

## Review clubs

| Club | Slices | Focus | Status |
|---|---:|---|---|
| A — Brain | 01–04 | Core + Jev + Transport/Grid foundation + adaptive Model Router | **PASS** |
| B — Can Do Work | 05–06 | Real machine/continuation + Memory Fabric + policy/live context | **PARTIAL — current work** |
| C — Embodied Core | 07–08 | Edge/reflexes + Voice/Identity/Persona | Planned after Gate B PASS |
| D1 — Sunday | 09 | Android embodiment + communication + owner controls | Planned |
| D2 — Desktop | 10 | Desktop interaction runtime | Planned |
| E1 — Awareness | 11–13 | World Model/Sentry + commissioning + presence | Planned |
| E2 — Executive | 14 | Chief-of-Staff planner + Workers + learning | Planned |
| F — Unified Alpha | 15–17 | Physical expansion + hardening + integrated alpha | Planned |

Manual integration checkpoints remain in [BUILD-GATES.md](BUILD-GATES.md).

## Current next step

Owner OAuth client registration/authorization → private connector lifecycle → private live-authority federation → reconcile acceptance/CI → review. Gate B remains PARTIAL; no Slice 07.

The original ordered acceptance sequence below remains a contract, not a list of unimplemented items:

```text
05 machine gaps
→ PowerShell
→ installed apps
→ Windows UI Automation
→ browser
→ owner-control continuation

06 Memory Fabric
→ Event Archive/WAL/FTS5
→ Qdrant
→ Graphiti + Neo4j
→ local embeddings/reranker
→ Jev Memory Preflight/retrieval escalation
→ evidence-bound claims
→ Memory Writer/consolidation
→ correction/forget/rebuild/evals

06 policy/private context
→ open-ended Personal Policy
→ real OAuth/private connector
→ secure credential boundary
→ live-authority-vs-memory federation

→ full Gate B manual acceptance
→ review/merge
→ Gate B PASS
→ only then Club C / Slice 07
```
