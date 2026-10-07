# Architecture Decisions

This file contains the **current active architecture decisions** for OSCAR. Retired/superseded decisions remain available in Git history and historical Gate/checkpoint evidence; they are not kept as active instructions merely for archival convenience.

When a durable architecture assumption changes, update this file and the affected canonical domain docs in the same change.

## ADR-001 — OSCAR is one distributed personal intelligence

**Decision:** OSCAR spans cloud coordination, phone, computers, communications, memory, tools, environment and Edge hardware as one system.

**Implications:**

- OSCAR Mobile is OSCAR on the phone, not a second assistant;
- Desktop machines are optional capability nodes, not the permanent host;
- cloud is replaceable infrastructure, not identity;
- Edge provides local presence/reflex/safety where used.

## ADR-002 — User experience is one continuous relationship

**Decision:** voice, text, OSCAR Mobile, desktop, communications, Workers and physical surfaces share one continuing OSCAR relationship.

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

## ADR-004 — OSCAR owns the Decision / Epistemic Controller

**Decision:** OSCAR owns intent/epistemic routing and decides whether a request requires known/world/recall/verify/reason/reported/specialist/worker/unknown paths and whether memory retrieval is mandatory.

The Controller owns intent classification, memory preflight, freshness/live-source
decisions, evidence and verification requirements, capability class, ambiguity/
ASK-vs-ACT decisions and model-tier recommendations. Safety, permissions,
Personal Policy, live-vs-memory precedence, confirmations and consequential-action
rules remain hard deterministic authority. Model routing and executor selection
remain separate. `oscar/jev.py` is an unchanged historical/internal module name
for OSCAR's deterministic logic; no TypeSafe Jev runtime/API is required.

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
Controller           → what class of action/evidence is needed?
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

**Decision:** OSCAR Mobile, replaceable cloud coordination, Desktop nodes and Edge form one Connection Grid over OSCAR-owned transport/capability contracts.

```text
OSCAR Mobile      = preferred owner control / approvals / notifications
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

## ADR-028 — OSCAR Mobile is OSCAR on Android, not a separate assistant

**Decision:** OSCAR Mobile is the primary everyday phone embodiment/owner-control surface.

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

PASS for the documented local-alpha scope. Verified scoped foundations include native Windows machine execution, useful Codex delegation with independent verification, cancellation, restart/recovery, ambiguity blocking, local selected-memory continuity and bounded owner-reviewed policy interpretation.

Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

Club C does not begin until Gate B mandatory acceptance passes.


## ADR-036 — Decision models are replaceable beneath OSCAR's controller

**Decision:** after Gate B PASS, run a separate System-1 evaluation of current
deterministic control versus Laya versus deterministic + Laya hybrid. No Laya/Jev
model/provider owns OSCAR's authority semantics, and no such evaluation or runtime
dependency begins during Gate B. Current `jev.py` naming stays until a later scoped
rename. Historical checkpoints retain the terminology used when they were written.

## ADR-037 — Shared authentication, reusable provider adapters

**Decision:** OSCAR owns the target Auth Broker and opaque CredentialRef boundary;
plugins declare provider, auth type/profile, required incremental scopes,
capabilities, risk and independent readback rather than each building OAuth.
Google authentication is shared by Gmail/Calendar/Drive/Contacts; Microsoft by
Outlook/Calendar/OneDrive/Teams; GitHub by GitHub capabilities. Provider/account/
tenant/audience boundaries and permissions remain explicit. Native/server vaults
hold raw secrets; only trusted broker/transport code resolves them for protocol I/O.
Local disconnect never implies provider revocation without evidence.

GitHub is the first intended real Gate B auth proof, not the universal auth design.
The existing native vault, enrollment state machine and provider protocols are
foundations; full broker/provider expansion is later work and not a new Gate B
requirement. Owner GitHub OAuth acceptance passed in run `oauth-gate-b-20261004-234817`;
remote revocation remains UNKNOWN_OWNER_ACTION_REQUIRED.

## ADR-038 — Free-first replaceable deployment and deferred Home Node

**Decision:** Oracle Always Free is the preferred first persistent/stateful Core
candidate; Vercel Hobby Python/Fluid Functions are a bounded web/API/callback/
webhook/relay candidate. Official allowances and lifecycle constraints checked on
2026-10-04 live in [DEPLOYMENT.md](DEPLOYMENT.md). Neither host is OSCAR's identity,
a deployment claim or a paid baseline requirement.

The owner's Samsung Galaxy Tab S6 Lite (2021) becomes a possible Home Node only
after OSCAR is fully deployed and the main Core architecture is operational.
OSCAR Mobile remains the everyday phone embodiment, Desktop the execution Worker, and
ESP32/Pico the local deterministic Edge. The tablet does not imply the full
Qdrant/Neo4j/ML stack is practical on Android. Deployment, Home Node, decision-model
evaluation and full Auth Broker expansion are not Gate B completion requirements.

## ADR-039 — Native Edge gateway and shared deterministic controller

Decision (2026-10-05): ESP-IDF 6.1 ESP32 gateway plus Pico SDK 2.3.1 RP2040
controller. Short 3.3 V 115200 UART is the reference link after comparing UART,
I2C and SPI. Host reference and firmware compile the same bounded version-1 C
codec/parser/controller. Native Grid and PersonalPolicy govern Core requests;
local stop/safe-state remains independent. No full Python runtime on ESP32,
managed framework or dangerous actuator profile. See [comparison](EDGE.md).
Owner rescope accepts the simulated software foundation for continuation; physical acceptance remains mandatory before Unified Alpha.

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

## Slice 08 owner closure scope — 2026-10-06

Owner-authorized closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
This is not a physical PASS. Gate C remains **PARTIAL**.
Slice 08 PR #14 integrated after green exact-head CI. Accepted main/work:
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Historical reference research baseline:
`e8ac8f8bca1cb0cb7909523ac6af906ee289366f`.
Existing owner harnesses remain mandatory inputs to later consolidated acceptance.
Microphone, real-room AEC/barge-in/self-wake, owner Match/Map calibration, playback,
Android voice and naturalness remain NOT RUN. Windows reference evidence never
implies Android acceptance. See [Voice Core](VOICE-CORE.md) and
[consolidated Gate C acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 OSCAR Mobile software may begin after clean Slice 08 integration; Slice 09 must
remain a draft and stop before owner/device acceptance. Slice 10, deployment and
Galaxy Tab Home Node are not authorized. Physical Edge remains
`DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`, mandatory before Slice 17 PASS.


## Post-alpha evolution direction

### Decision — Voice Core is platform-neutral

Windows is the first exercised reference, not the product boundary. Android/OSCAR Mobile
must consume the same Voice Core contracts through native adapters. Linux/macOS and
future Home Node surfaces follow the same rule. Platform acceptance remains
independent.

### Decision — Operating telemetry is separate from captured content

After stable Unified Alpha, OSCAR may record owner-controlled structured Operating
Logs describing calls, routes, tools/plugins/capabilities, Workers, timing,
fallbacks, failures and verification. This is a separate data class from
conversation recording, Context Capture, Daily Journal and Memory. Telemetry is
not training data unless the owner explicitly promotes it under defined
provenance/redaction/retention rules.

### Decision — specialize locally before assuming a giant local model

Real sustained usage should identify repeatable task families where smaller
specialist models can outperform a general model for latency, resource use or
quality. Promote specialists only through evals and keep them replaceable behind
OSCAR contracts. Over time orchestration itself may migrate to optimized local
models.

The long-term host is the owner's dedicated home-server laptop, with cloud models
kept as explicit escalation for difficult/major work rather than a mandatory
dependency.

See [Post-Alpha Evolution](POST-ALPHA-EVOLUTION.md).

## Current Slice 09 — 2026-10-06

Slice 08 PR #14 merged; accepted main/work baseline
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Slice 08 is
**COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**; physical voice is
`DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`, never physical PASS.
OSCAR Mobile Kotlin/Compose rebuild is on `club-c/slice-09-sunday`, draft PR #15
into `work`, **PARTIAL / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**. Core/loopback,
Gradle/JVM/emulated evidence is separate from actual phone/OEM acceptance.
See [OSCAR Mobile foundation](MOBILE-FOUNDATION.md) for implementation, limits and the next owner boundary.
Slice 09 must not merge in this run. Gate C remains PARTIAL. Slice 10, deployment
and Home Node are not started. Post-alpha Operating Logs, specialist-model training
and home-server migration remain documented future work, not implemented.

## OSCAR Mobile naming and application composition — 2026-10-06

The owner retired Sunday as the active product name and rejected its initial UI.
The product/app is OSCAR; technical distinction OSCAR Mobile. Active project and
package names migrate to mobile; historical evidence and compatibility contracts
remain intact. The existing branch/PR identity is retained.

Use Kotlin/Compose, coroutines/Flow and native supported Android mechanisms. Four
primary destinations (OSCAR, Activity, Devices, Settings), contextual approvals and
independent screen composables keep one continuous presence and allow a later
visual redesign without changing Core/runtime authority. CoreSession owns transient
readback, never reasoning/memory/policy. Existing security/audio boundaries are reused.

New package identity requires later scoped re-enrollment; no secret copying or
implicit authority upgrade. Legacy record keys preserve replay/consumption fences.
Raw retention remains off. The canonical Orb is unchanged with nine state hooks;
expressive animation remains Slice 13. Text reasoning/retrieval stays in existing
scoped Core capabilities and responses remain REPORTED without independent evidence.
PR #15 stays an owner-review candidate, not physical acceptance.
See [implementation and migration](MOBILE-FOUNDATION.md).
