# Architecture Decisions

This file contains the **current active architecture decisions** for OSCAR. Retired/superseded decisions remain available in Git history and historical Gate/checkpoint evidence; they are not kept as active instructions merely for archival convenience.

When a durable architecture assumption changes, update this file and the affected canonical domain docs in the same change.

## ADR-001 — OSCAR is one distributed personal intelligence

**Decision:** OSCAR spans cloud coordination, phone, computers, communications, memory, tools, environment and Edge hardware as one system.

**Implications:**

- Sunday is OSCAR on the phone, not a second assistant;
- Desktop machines are optional capability nodes, not the permanent host;
- cloud is replaceable infrastructure, not identity;
- Edge provides local presence/reflex/safety where used.

## ADR-002 — User experience is one continuous relationship

**Decision:** voice, text, Sunday, desktop, communications, Workers and physical surfaces share one continuing OSCAR relationship.

The user is not required to create/manage chat threads to preserve or retrieve memory.

Internal turns/episodes/projects/objectives/tasks/entities remain structured for scaling, retrieval and provenance.

## ADR-003 — OSCAR owns the canonical Memory Fabric

**Decision:** OSCAR owns canonical long-term history; no managed memory vendor is required.

Initial stack:

```text
canonical OSCAR Event Archive
SQLite + WAL + FTS5
      │
      ├─ Qdrant OSS semantic/hybrid derived index
      └─ Graphiti OSS + Neo4j Community temporal/entity derived index
```

Embedding/reranking are replaceable OSCAR capabilities.

**Constraint:** vector/graph indexes are rebuildable derived state and never the sole source of memory truth.

**Supersedes:** the earlier LRA + Supermemory backend formulation. Historical references to that formulation describe the old plan only.

See `docs/MEMORY.md`.

## ADR-004 — Jev owns memory preflight and epistemic retrieval routing

**Decision:** TypeSafe Jev decides whether a request requires known/world/recall/verify/reason/reported/specialist/worker/unknown paths and whether memory retrieval is mandatory.

For personal/historical/project/entity/artifact/preference references, retrieval precedes historical factual claims.

Bounded recall escalation:

```text
active context
→ structured OSCAR state/entities/tasks/policy
→ canonical Event Archive exact/FTS5
→ Qdrant hybrid
→ Graphiti temporal/entity
→ alias/entity/time-range expansion
→ bounded deeper archive reconstruction
→ UNKNOWN
```

A retrieval miss is not proof memory does not exist.

## ADR-005 — Recalled claims are evidence-bound

**Decision:** OSCAR must not say or imply `I remember X` unless X was actually retrieved or remains in Active Context with source provenance.

Personal/historical claims retain source event/memory IDs internally. Retrieved history remains `RECALLED` in the current reasoning path; similarity/reranking/model confidence never promotes it to current `VERIFIED` truth.

## ADR-006 — World Model and Memory are separate

**Decision:** World Model represents current state; Memory Fabric represents historical continuity/evidence.

**Constraint:** live authoritative state outranks stale memory when current truth matters. Historical questions may intentionally select older temporally valid facts.

## ADR-007 — Corrections supersede; history is preserved

**Decision:** corrections link to challenged facts/events, update current validity and derived indexes, and preserve the original source history for temporal questions.

Do not silently rewrite history.

## ADR-008 — Memory formation produces candidates, not truth

**Decision:** model-assisted extraction creates scoped candidates with source provenance and epistemic state.

Pipeline:

```text
source event
→ extract candidate
→ scope/classify
→ entity resolution
→ conflict/supersession check
→ provenance + evidence state
→ retention decision
→ derived-index update
```

Overgeneralization is a defect. Inference remains `INFERRED` unless stronger evidence exists.

## ADR-009 — Personal Policy, Permission, Persona and Memory are different authority layers

```text
Memory          = historical continuity/evidence
World Model     = current state
Personal Policy = explicit desired behavior
Permission      = what OSCAR may do
Persona         = how OSCAR expresses itself
Protocol        = durable delegated responsibility
```

None silently grants/substitutes for another.

## ADR-010 — Epistemic Integrity is a system invariant

**Decision:** OSCAR distinguishes KNOWN, INFERRED, RECALLED, REPORTED, VERIFIED and UNKNOWN, and preserves explicit task lifecycle states.

Tool/model/Worker/API success is testimony, not automatic objective completion.

Unknown/failure/disagreement is preferable to fabricated certainty.

See `docs/EPISTEMIC-INTEGRITY.md`.

## ADR-011 — Transport and capability fabric are native OSCAR infrastructure

**Decision:** OSCAR owns typed task/event/action/result transport, node/session identity, pairing/scoped credentials, capability advertisement, correlation, reconnect/backoff, progress, replay protection/idempotency and audit/provenance.

Latch remains reference/prototype material, not a required runtime.

## ADR-012 — Model routing is native and separate from capability routing

**Decision:** keep three boundaries distinct:

```text
Jev                  → what class of action/evidence is needed?
Capability selection → which executor/tool/device should act?
Model Router         → which provider/model/credential should reason?
```

SwitchRoute remains reference/prototype material, not a required runtime.

Coding agents, terminal, computer-use and installed apps are executable capabilities, not model-provider entries.

## ADR-013 — Freshness-sensitive current facts require live evidence

**Decision:** when a fact can materially change, retrieve current authoritative evidence where reasonably available before answering from memory/cache/model prior.

Provider support, account-visible listing, generation access, funding/quota and current service state remain separate observations.

Tavily is one replaceable search adapter, not an architectural dependency.

See `docs/SEARCH-FRESHNESS.md`.

## ADR-014 — Connection Grid is OSCAR's availability/control fabric

**Decision:** Sunday, replaceable cloud coordination, Desktop nodes and Edge form one Connection Grid over OSCAR-owned transport/capability contracts.

```text
Sunday      = preferred owner control / approvals / notifications
Cloud       = replaceable rendezvous + durable coordination
Desktop     = high-capability execution
Edge        = local awareness / reflex / safety
```

No connected node gains unrestricted authority. Capability scope and permission are rechecked at authoritative targets.

Availability degrades explicitly rather than hiding a permanent host.

See `docs/CONNECTION-GRID.md`.

## ADR-015 — Long-running work uses a Durable Execution Runtime

**Decision:** durable work carries task IDs, checkpoints, dependencies, leases/ownership, heartbeats, bounded retry, cancellation, reclaim/restart semantics, artifacts and verification state.

Ambiguous consequential work is not blindly replayed. Dead executors do not remain falsely `working`.

## ADR-016 — Use specialist software rather than reimplement it

**Decision:** OSCAR delegates to the strongest legitimate environment: coding agents for code, computer-use for GUIs, installed/connected engineering tools, native connectors/APIs, browser runtime, model providers or Edge capabilities as appropriate.

Capabilities advertise dynamically rather than being assumed always available.

## ADR-017 — Machine execution is capability-scoped and truthful about isolation

**Decision:** Desktop Workers expose scoped filesystem/Git/terminal/browser/computer-use/installed-app capabilities.

Trusted-host execution is **not** a sandbox. Cwd restriction, allowlists, Job Objects, UI Automation and browser isolation improve boundaries but are not represented as OS-level hostile-code containment unless separately proven.

## ADR-018 — Personal Policy interpretation requires owner confirmation

**Decision:** open-ended natural-language policy is interpreted into a bounded structured candidate, shown to the owner and activated only after explicit confirmation.

Policy cannot grant missing permission, bypass strong confirmation, weaken hard safety or be overridden by Persona/memory.

## ADR-019 — Communication is one OSCAR subsystem

**Decision:** calls, messages, email, meetings, dictation and communication follow-up share a Universal Channel Gateway while preserving real channel capabilities.

Integration order:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

Notification visibility never implies unrestricted access to the source app.

## ADR-020 — Sentry awareness and durable capture are separate

**Decision:** Sentry may provide persistent local awareness when enabled, while conversational Listening, raw recording, transcription, summaries and memory extraction remain separately controlled.

The product is not designed around covert recording.

## ADR-021 — Voice Identity, Voice Match and Voice Map are separate systems

- Voice Identity is OSCAR's stable provider-independent speaking identity.
- Voice Match is authorization-oriented speaker evidence.
- Voice Map is perception-oriented speaker context.

Recognition never grants permission. Unknown speakers remain unknown. Voice embeddings/profiles are sensitive dedicated data, not generic Memory Fabric records.

## ADR-022 — Hardware safety is deterministic/local

**Decision:** emergency stop, cutoffs, interlocks, watchdog behavior and other physical safety functions remain local and functional without cloud/model reasoning.

No LLM sits in the mandatory emergency-control loop.

## ADR-023 — Persona affects expression, not truth or authority

**Decision:** Persona may change humor, candor, warmth, formality, brevity, playfulness, initiative and pushback, but cannot reduce Epistemic Integrity, permissions, consent or safety.

## ADR-024 — Executive Planner coordinates objectives above Workers/Protocols

**Decision:** Executive Planner coordinates concurrent objectives using priority, deadline, dependencies, resources, flexibility, cost, risk, interruptibility and device availability.

It may replan flexible work only where Personal Policy and real capabilities allow it.

## ADR-025 — Consequential actions use Action Ledger and truthful Undo

**Decision:** consequential actions record initiator, intent, target, capability, permission/policy decision, execution, verification, evidence and reversibility/compensation metadata.

Undo exists only where a real compensation exists.

## ADR-026 — Finished outputs use first-class Artifact/Result records

**Decision:** documents, code changes, research, media, deployments, notes, firmware, datasets/models/evaluations and other durable outputs may be typed artifacts with provenance, ownership, location/version and verification state.

## ADR-027 — Learned automation is evaluated before trusted promotion

**Decision:** successful exploratory work can create candidate Skills/routines/Protocols, but trusted/default promotion requires parameterization, evaluation, safety/permission review and rollback where practical.

One success is not enough to create trusted automation.

## ADR-028 — Sunday is OSCAR on Android, not a separate assistant

**Decision:** Sunday is the primary everyday phone embodiment/owner-control surface.

Where supported and explicitly granted it may use Android assistant/voice interaction, optional Orb overlay, widgets, notification context, legitimate notification replies, biometric/PIN approval and Grid supervision.

OEM/device behavior is not claimed until exercised on target hardware.

## ADR-029 — Perception, retention and action are independent

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

Reading a notification/calendar/screen/location does not itself grant retention or mutation authority.

## ADR-030 — Documentation and evidence are part of slice completion

**Decision:** each completed slice updates code, tests, authoritative evidence and affected canonical docs. A slice is not complete while the repository describes an older active architecture.

Historical checkpoint/evidence files remain provenance. Retired architecture is removed from active canonical instructions or explicitly marked superseded.

## ADR-031 — Gates are completed end-to-end before the next Club

**Decision:** Build Gates remain manual acceptance milestones above slices.

```text
Gate A — Brain          Slices 01–04
Gate B — Can Do Work    Slices 05–06
Gate C — Embodied OSCAR Slices 07–10
Gate D — JARVIS Layer   Slices 11–14
Gate E — Unified Alpha  Slices 15–17
```

A partial gate is not skipped because it is demoable or because a short-term alpha deadline is approaching. Mandatory planned work is completed/verified, genuinely blocked, or explicitly re-scoped by the owner before advancing.

## ADR-032 — Design direction is Quietly Alive + Playful Precision

**Decision:** `DESIGN.md` and `TASTE.md` own OSCAR's visual/motion quality bar: restrained warm materials, graphite typography, blue/yellow identity, weighted physical motion, progressive disclosure and no generic AI-dashboard/card-wall/neon slop.

## ADR-033 — Agent adapters remain thin

**Decision:** `AGENTS.md` is the repository-wide coding-agent instruction set. `CLAUDE.md`, `GEMINI.md`, Cursor/Copilot adapters and similar files point back to canonical docs instead of duplicating architecture.

## ADR-034 — Engineering favors modular, evolvable code

**Decision:** `ENGINEERING.md` owns code/system-design quality: smallest coherent solution, high cohesion/low coupling, typed validated boundaries, explicit state ownership, bounded failure/retry, dependency discipline, contract-focused tests, least privilege and small reversible changes.

## ADR-035 — Generation-fenced local memory and recoverable vault enrollment

**Decision:** retain SQLite/WAL/FTS5, Qdrant, Graphiti/Neo4j, Playwright and native Windows
UIA/Credential Manager. Use FastEmbed 0.8.1 BGE small v1.5 and MiniLM reranking as the local
default after equal A–R fixture quality; sentence-transformers 6.1.0 is a separate optional
comparison backend. Replace hand-hashed lexical vectors with supported Qdrant BM25 document
and query embeddings plus IDF, dense/sparse RRF and reranking.

Canonical writes advance durable archive generations. Derived projections are usable only
with matching generation/model identity and physical completion digest. Failure never rolls
back canonical history. Scoped Graphiti ownership and namespaced IDs protect unrelated data.
Persist enrollment/disconnect intent before native vault mutation and reconcile on restart;
never replay an ambiguous external token exchange or invent remote revocation confirmation.
See [measurements, versions and limits](GATE-B-HARDENING.md). This changes no Gate B completion
claim and grants no owner/private/manual acceptance.

## Current accepted boundaries

### Gate A

PASS for the documented Brain foundation.

### Gate B

PARTIAL. Verified scoped foundations include native Windows machine execution, useful Codex delegation with independent verification, cancellation, restart/recovery, ambiguity blocking, local selected-memory continuity and bounded owner-reviewed policy interpretation.

Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

Club C does not begin until Gate B mandatory acceptance passes.
