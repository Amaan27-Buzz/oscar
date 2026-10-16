# System Architecture

## Group 3 current-state backend candidate — 2026-10-16

The scoped Slice 14 candidate adds `world_model.py`, `perception.py`,
`perception_adapters.py` and `sentry.py`. Current pointers reference the canonical
Event Archive when retention is granted; otherwise values remain transient.
Sentry produces policy-bounded proposals, with no independent action authority.
Existing Python Core, Controller, Memory Fabric, Grid and UI contracts remain
authoritative. See [implementation and acceptance boundary](development/GROUP-03-GATE-D.md).

**Mobile acceptance update — 2026-10-16:** Group 2.5B UI/UX is explicitly
**APPROVED / PASS**. [Final closure](ui/mobile/group25b/FINAL-CLOSURE.md) records
the theme correction and lifecycle investigation. This supersedes earlier
visual-review-pending statements; physical commissioning, remote CI and Gate C
remain separate.

## Group 2.5 reconciliation — 2026-10-14

Core owns one continuous multimodal personal intelligence and delegates subordinate responsibilities to Workers/specialists. The approved tiny Companion is expressive presence; the separate Workspace centers Conversation with contextual operations, Automations, operational Activity, Devices and Preferences. [The interaction and authority decision](decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) records implementation ownership, canonical history composition and the corrected access model.

Ask / Secure / Full Access, awareness, Worker autonomy and capture/retention are independent. Genuine Full Access requires signed standing owner delegation and immediate revocation; it is currently unavailable because exact-action approval/critical blockers remain. No alternate Core, memory store or agent framework is introduced.


> **Current — 2026-10-15:** The 00–20 [canonical roadmap](SLICE-NUMBERING.md) is authoritative. Desktop Groups 1–2 and Group 2.5A Companion/Workspace are merged into `main`; the owner accepted the neumorphic Desktop UI **provisionally**. Mobile Group 2.5B is a production Kotlin/Compose implementation candidate using the selected Codex ImageGen/Figma baseline, with native phone evidence and owner visual review pending. The Gemini Argon prototype is rejected, not an architectural or reusable component source. Mobile preserves the existing Core, Grid, signed decisions, native capabilities and shared Expression boundary; see [the implementation ledger](ui/mobile/group25b/README.md). Slice 14 Sentry and Slice 17 persistent Workers remain planned. Future [Adaptive Interface Engine](ADAPTIVE-INTERFACE.md) spans 16/17/19/20; **not implemented**. Earlier candidate PR references are historical evidence. Gate C physical and final integrated design acceptance remain open.

## Desktop foundation — Slice 10 integrated software reference

Tauri/Rust/React-TypeScript presentation and explicit OS context adapters connect to the existing OSCAR Core. Core owns Controller, memory, tasks, policy, permission, routing and evidence; Runtime/Dispatcher resolve bounded process-local private inputs only after durable authorization. Desktop does not duplicate Worker/browser/UIA execution. See [Desktop foundation](DESKTOP-FOUNDATION.md).

## Overview

OSCAR is a distributed personal-intelligence system: one coherent intelligence spanning cloud coordination, phone, desktop machines, communications and physical Edge hardware. No ordinary user computer is assumed to be permanently available.

OSCAR owns its core infrastructure. Earlier projects or external frameworks may provide ideas/adapters but do not own OSCAR's identity, task state, memory, authority or verification semantics.

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
managed memory systems  → optional adapters only
```

## Connection topology

```text
                         User
                          │
                       OSCAR Mobile
              owner control / approvals
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Cloud           Desktop(s)        Edge
 rendezvous/state     high compute    local reflex/safety
          └───────────────┼────────────────┘
                          ▼
                OSCAR Connection Grid
```

No Grid member owns OSCAR's identity by itself.

## Canonical control/data flow

```text
User / Environment
       │
       ▼
Perception Fabric
       │
       ▼
World Model + current commitments / attention
       │
      Controller
       │
 ┌─────┼──────────────────────────────────────────┐
 │     │                    │                     │
 │     │                    │                     │
Memory Fabric          Live Context/Search   Model Reasoning
historical evidence    current authority     native Model Router
 │     │                    │                     │
 └─────┴────────────────────┴──────────┬──────────┘
                                      ▼
                                OSCAR Executive
                    Personal Policy • Persona • permissions
                                      │
                                      ▼
                             Durable Execution Runtime
                                      │
                                      ▼
                         Capability Catalog + Tool Search
                              Workers / Skills / Protocols
                                      │
                                      ▼
                               Connection Grid
                         OSCAR Mobile • Cloud • Desktop • Edge
                                      │
                                      ▼
                    Apps / Channels / Devices / Specialists
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                    Action Ledger          Artifact / Result
                          └───────────┬───────────┘
                                      ▼
                                  Verification
                                      │
               World Model / commitments / Memory Fabric update
                                      │
                             evidence-backed report
```

Cross-cutting layers:

- Epistemic Integrity;
- permissions/safety;
- Personal Policy;
- Persona;
- canonical entity identity;
- audit/provenance;
- learning/evaluation;
- privacy/retention.

## 1. OSCAR Core

Core owns responsibilities that must remain coherent across embodiments:

- identity/shared assistant state;
- one continuous user relationship/interaction point;
- active objectives/tasks/Workers/Protocols;
- permission and Personal Policy evaluation;
- Persona selection/context triggers;
- Controller routing and evidence requirements;
- capability discovery/delegation/reroute decisions;
- event prioritization;
- verification strategy;
- Memory Fabric/live-context requests;
- World Model access;
- Executive decisions;
- Action Ledger coordination;
- evidence/epistemic state.

Core must not become a mega-framework or assume every request requires an LLM.

## 2. World Model — what is true now

The World Model represents current state and is distinct from memory.

Entities/state may include people, places, devices, apps/services/accounts, projects/repositories, tasks/Workers/Protocols, calendar events, commitments, communication threads, activity/focus state and physical objects where supported.

Every current-state claim should carry source, observed time, freshness/expiry, confidence/authority and provenance as appropriate. Stale evidence becomes stale/unknown rather than current truth.

## 3. Perception Fabric

Normalizes current evidence from screen/accessibility/cursor/selection, screenshots/cameras, microphone/acoustic events, Voice Map, time/date/timezone, weather, calendar/tasks, authorized notifications, phone location/activity/media state, calls/messages/email/meetings, apps/devices, Edge sensors and Worker/task state.

Perception and retention are separate decisions. Observation does not itself create durable memory or authority to act.

## 4. OSCAR Memory Fabric — historical continuity

OSCAR exposes one continuing relationship while maintaining structured internal history.

### Canonical store

The **OSCAR Event Archive** is canonical historical memory. Initial implementation uses SQLite + WAL + FTS5.

Canonical events include retained user turns, corrections, objectives/actions/results, artifacts/evidence, project/entity references, decisions/preferences and other retained history under policy.

### Derived semantic index

Qdrant OSS is the first semantic/hybrid retrieval index. It is rebuildable derived state and stores references back to canonical archive IDs.

### Derived temporal/entity index

Graphiti OSS + Neo4j Community are the first temporal/entity memory index. They model entities, aliases, relationships, temporal validity and supersession while retaining source-event provenance.

### Replaceable ML components

Embedding and reranking models are replaceable OSCAR capabilities. They may be local/self-hosted or selected through the native Model Router under policy.

### Memory ownership invariant

```text
OSCAR Event Archive = canonical history
Qdrant              = derived retrieval index
Graphiti/Neo4j      = derived temporal/entity index
```

Losing either derived index must not erase OSCAR's history. Derived indexes are rebuildable.

See [MEMORY.md](MEMORY.md).

## 5. Decision / Epistemic Controller — intent + evidence routing

OSCAR owns the **Decision / Epistemic Controller** (shortened to **Controller**
throughout active docs). It owns intent classification, memory preflight,
freshness/live-source decisions, evidence requirements, capability class,
verification requirements, ambiguity/ASK-vs-ACT decisions and model-tier
recommendations. The Model Router still selects the actual provider/model;
capability selection still chooses the executor.

The current implementation is OSCAR-owned deterministic Python logic in
`oscar/jev.py`. That module name is a temporary historical/internal name, not a
TypeSafe Jev runtime/API dependency. It is not renamed in this Gate B pass.

Hard deterministic rules remain authoritative for safety, permissions, Personal
Policy, live-vs-memory authority, required confirmation and consequential actions.
A decision model may propose a classification; it cannot override these rules.
After Gate B PASS, a separate System-1 evaluation will compare the current
deterministic controller, Laya, and deterministic + Laya hybrid. Laya, Jev or a
similar decision model is a replaceable implementation/provider beneath OSCAR's
controller, never the owner of its authority semantics. No such model is selected,
required or evaluated here. Model-tier recommendation is a controller contract;
this does not claim a new implemented model recommendation path tonight.

The controller decides what kind of evidence/action path is required:

```text
known      → direct evidence sufficient
world      → current World Model
recall     → OSCAR Memory Fabric
verify     → authoritative source/test
reason     → native Model Router
reported   → external testimony
specialist → coding/computer-use/installed app/etc.
worker     → delegated Worker
unknown    → retrieve/ask instead of fabricate
```

Controller also performs a **Memory Preflight**. If the request plausibly depends on previous user/project/entity/task/artifact/preference/history context, retrieval is mandatory before a historical/personal claim is generated.

The reasoning model does not decide whether memory exists.

Retrieval escalation is bounded:

```text
active context
→ structured OSCAR state/entities/tasks/policy
→ Event Archive exact/FTS5
→ Qdrant hybrid
→ Graphiti temporal/entity
→ alias/entity/time-range expansion
→ bounded deep archive reconstruction
→ UNKNOWN
```

An empty retrieval result is not proof that memory never existed.

Controller, capability selection and Model Router remain separate decisions.

## 6. Evidence-bound recall

Historical/personal claims require evidence provenance.

Conceptually a generated historical claim carries:

```text
claim
supporting_event_ids[]
supporting_memory_ids[]
evidence_state
confidence
```

OSCAR must not say or imply `I remember X` unless X was retrieved during the current reasoning path or remains in active context with source provenance.

Retrieved historical information remains `RECALLED`; retrieval does not promote it to current `VERIFIED` truth.

## 7. Memory formation, correction and consolidation

Memory extraction is candidate formation, not automatic truth:

```text
source event
→ extract candidate
→ scope/classify
→ resolve entities
→ compare/conflict check
→ provenance + epistemic state
→ retention decision
→ update derived indexes
```

Corrections preserve history:

```text
new correction
→ link challenged fact
→ preserve old source event
→ supersede old current fact
→ update temporal validity
→ update semantic/graph indexes
```

Background consolidation may deduplicate derived memories, merge supporting evidence, resolve safe aliases, detect contradictions, maintain temporal windows, generate provenance-backed summaries and rebuild indexes. It never replaces source events.

## 8. Authority and freshness

Memory is evidence, not universal current truth.

Default authority pattern:

```text
hard safety / permission / Personal Policy
> current explicit owner statement for personal claims
> live authoritative state
> current World Model observation
> structured OSCAR state
> recent directly sourced episode
> temporal graph fact with provenance
> semantic memory
> inferred memory
> model prior
```

Authority is claim-specific. Live filesystem, calendar, device, weather or account state outranks memory of that state.

## 9. Entity identity

One real-world entity should resolve consistently across contacts, messaging identities, Voice Map, calendar, projects, repositories, tasks and devices only where evidence supports the mapping.

Canonical entity records carry stable IDs, names/aliases, type, evidence, relationships and confidence. Same labels do not prove identity. Ambiguous entities remain distinct.

Entity resolution improves both World Model and Memory Fabric retrieval but never fabricates identity.

## 10. Epistemic Integrity

Task/result states remain explicit:

```text
planned
executing
awaiting_result
result_received
verifying
verified
partially_verified
failed
blocked
cancelled
unknown
```

Evidence states remain distinct:

```text
KNOWN
INFERRED
RECALLED
REPORTED
VERIFIED
UNKNOWN
```

Tool/model/Worker/API success is testimony, not objective proof. Model reasoning cannot promote `RECALLED`, `INFERRED` or `REPORTED` into `VERIFIED` without evidence.

## 11. Ambient Chief-of-Staff context

OSCAR uses current World Model evidence to coordinate the user's day rather than only answer isolated prompts.

```text
current context + commitments
→ detect conflict / opportunity / risk
→ grade urgency + interruptibility
→ Personal Policy / permission
→ stay quiet / inform / suggest / act / interrupt
→ verify mutation
→ update current state
```

The Executive may rearrange flexible work only when real capability and explicit policy allow it.

See [CHIEF-OF-STAFF.md](CHIEF-OF-STAFF.md).

## 12. Personal Policy

```text
Memory          = historical continuity/evidence
World Model     = current truth model
Persona         = expression
Personal Policy = how the user wants OSCAR to behave
Permission      = what OSCAR may do
Protocol        = durable autonomous responsibility
```

Personal Policy can constrain behavior but cannot grant a missing permission. Memory can suggest policy candidates but cannot silently create authority.

## 13. Executive Planner

Coordinates multiple objectives/commitments using priority, deadline, dependencies, flexibility, resource/device availability, cost, risk and interruptibility.

It may schedule, parallelize, pause, pre-empt, reroute, defer and—where policy permits—replan flexible work. It never bypasses Controller, permissions or Personal Policy.

## 14. Durable Execution Runtime

Long-running work carries durable task state, checkpoints, dependencies, leases/ownership, heartbeat, retry budget, cancellation, deadline, execution surface, artifacts, verification and blockers.

Dead executors do not remain `working` forever. Ambiguous consequential work is not blindly replayed.

## 15. Capability Catalog + Dynamic Tool Search

Capabilities expose searchable lightweight manifests with class, inputs/outputs, permissions/risk, surfaces, availability, latency/cost/reliability hints, undo metadata and provider/version.

Detailed contracts are loaded only for relevant finalists.

## 16. Native Model Router

Owns provider/model/credential routing with dynamic inventory, health/availability, latency/cost/quality, account-product/quota-pool state, fallback/circuit behavior and route history.

Models reason; they do not receive authority automatically.

## 17. Native Transport + Capability Fabric

OSCAR-owned typed transport provides node/session identity, pairing/scoped credentials, task/event/action/result transport, capability advertisement, correlation IDs, reconnect/backoff, progress, replay protection/idempotency, version negotiation, audit/provenance and outbound-first private-device rendezvous.

## Shared Auth Broker and provider adapters

OSCAR's target Auth Broker owns shared OAuth2/PKCE, Device Flow, API key,
MCP/session authentication, refresh/expiry, incremental scope upgrades,
disconnect/revocation state and the native/server vault abstraction. Connectors
carry an opaque CredentialRef and provider/auth profile/scopes/capabilities/risk/
readback declarations; plugins do not independently implement every auth lifecycle.
Trusted broker/provider transport code resolves secrets only where protocol I/O
requires them. Raw tokens do not go to plugins when an opaque reference suffices.

One provider adapter is reused across related capabilities: Google for Gmail,
Calendar, Drive and Contacts; Microsoft for Outlook, Calendar, OneDrive and Teams;
GitHub for GitHub capabilities. Account/tenant/audience/scopes remain explicit;
shared provider code does not merge identities or authorize unrelated scopes.
GitHub device OAuth is only the first intended real Gate B authentication proof,
accepted in owner run `oauth-gate-b-20261004-234817`. The full broker expansion is a future design,
not a claim that every auth mode/provider is implemented. See
[CONNECTOR-FABRIC.md](CONNECTOR-FABRIC.md) and [SECURITY.md](SECURITY.md).

## 18. Connection Grid

### OSCAR Mobile

Preferred owner-control/approval surface and strongest everyday Chief-of-Staff embodiment. It can inspect/pause/cancel/revoke authorized work but cannot bypass local hardware safety.

### Cloud coordinator

Replaceable persistent Core coordination owns identity/state/memory/task
coordination above the Grid. The preferred free-first stateful host candidate is
Oracle Always Free; Vercel Python Functions are a separate bounded API/web/relay
candidate. Neither is deployed or mandatory. See [DEPLOYMENT.md](DEPLOYMENT.md).

### Desktop nodes

High-capability execution: coding agents, terminal, filesystem, browser, computer use, installed apps, GPU/local models and long-running work.

### Future Home Node

The owner's Samsung Galaxy Tab S6 Lite (2021) is a future always-on local Grid
node and LAN/Bluetooth/ESP32/Pico bridge where Android permits. Build only after
OSCAR is fully deployed and the main Core architecture is operational. Do not
assume it runs the canonical Qdrant + Neo4j + ML stack or makes Android system
privilege available. It is not a Gate B requirement.

### Edge

ESP32/Pico are nerves/reflexes/sensors/actuators, not full OSCAR Core hosts.
Hardware safety is local and deterministic. Edge capabilities may provide local
wake/Sentry signals, sensors, GPIO, actuators and safety/reflex behavior where
actually implemented and advertised.

Availability can degrade:

```text
FULL → CONNECTED → LOCAL → REFLEX_ONLY → OFFLINE
```

See [CONNECTION-GRID.md](CONNECTION-GRID.md).

## 19. Action Ledger + Artifact/Result Model

Consequential actions record initiator, intent, capability, permission/policy decision, target, execution state, verification state, evidence, reversibility/compensation and correlation ID.

Durable outputs are typed artifacts with provenance, ownership, location/version and verification state. Undo exists only when real compensation exists.

## 20. Communication

Supported communication adapters normalize calls/messages/email/meetings while preserving channel limits.

Integration order:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

Notification visibility never implies unrestricted app access.

## 21. Voice / Sentry

- **Voice Input** — wake, VAD, STT, barge-in, echo cancellation.
- **Voice Identity** — stable provider-independent VoiceProfile.
- **Voice Match** — authorization-oriented speaker evidence.
- **Voice Map** — perception-oriented speaker context; recognition never grants permission.
- **Sentry** — persistent local-first awareness when enabled.

Awareness, transcription, raw audio retention, transcript retention, summaries and memory extraction are separate controls.

## 22. OSCAR Mobile / Android

OSCAR Mobile is OSCAR on the phone, not another assistant.

Target platform integrations where legitimate and explicitly granted include assistant-role/voice interaction, optional Orb overlay, attention-aware retreat/reappearance, widgets, notification-listener context, legitimate notification replies, biometric/PIN approval and Connection Grid supervision.

## 23. Desktop Interaction Runtime

```text
Dictate → insert/clean speech into focused target
Edit    → transform selected/recent text
Ask     → answer about current context
Act     → operate current app/device/task
```

Desktop context may include app/window, focused control, selection, accessibility tree, screenshots, clipboard fallback and active task state.

## Future Adaptive Interface Engine — planned presentation composition

The [Adaptive Interface Engine](ADAPTIVE-INTERFACE.md) will let the Controller/Executive choose a **typed, bounded, versioned interactive UI description** rendered through trusted Desktop React/Tauri and native Android Compose components. It can adapt comparisons, schedules, diagrams, charts, task/Worker displays and device controls **inside the one ongoing conversation**, with accessible textual fallback.

AIE is a **presentation projection**, not a second planner, memory system, security principal or tool executor. Component actions always resolve to typed Core intents; target capabilities and Personal Policy retain authority, signing, readback, epoch/revocation and verification. Generated layout/data is untrusted; no arbitrary executable code. Scheduled for Slice 16 shared presentation foundation, 17 intent-driven composition, 19 hardening, 20 integrated validation. No current implementation claim.

## 24. Edge

ESP32-class nodes own network/audio/event gateway responsibilities; RP2040/Pico-class controllers own deterministic physical timing, GPIO and local safety where used. Local safety remains functional if cloud/Core/transport fails.

## 25. Learning

Verified successful paths may become candidate Skills/routines/Protocols only after parameterization, evaluation and permission review. One successful run is not enough for trusted promotion.

## 26. Self-maintenance

OSCAR monitors provider/auth health, Grid connectivity, capability staleness, task leases, Edge health, storage state, Memory Fabric index health/drift and repeated Worker failures. Safe bounded repair/rebuild may occur automatically where authorized.

## Current implementation boundary

### Gate A

**PASS.** Core Loop/Controller/reference Grid, adaptive model routing and source-qualified search/freshness acceptance are verified for their documented scope.

### Gate B

**PASS for documented local-alpha scope.** Verified scoped work includes native Windows file/process/Git execution, useful Codex delegation with independent verification, cancellation, coordinator/Worker restart/recovery, ambiguous mutation blocking, local selected memory continuity and bounded owner-reviewed policy authoring.

Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

Gate B is frozen PASS; Slice 07 software is accepted for continuation; physical acceptance is owner-deferred.

## Architecture invariants

The [pre-manual Gate B patch](GATE-B-HARDENING.md) retains the chosen framework boundaries.
Canonical archive generation and physical derived-index proofs gate recall; one scoped
projection serves one relationship, and stale projections are excluded. FastEmbed replaces
the default Torch ML runtime after bounded A–R comparison. Native credential enrollment
uses durable intents and restart reconciliation across the SQLite/vault boundary.
Final physical/manual machine acceptance PASSED in the owner run on 2026-10-04.
Owner OAuth/private federation PASSED; Gate B is PASS for the documented scope.
Remote provider revocation remains UNKNOWN_OWNER_ACTION_REQUIRED. See
[the accepted path](GATE-B-OAUTH-ACCEPTANCE.md).

1. One intelligence, many embodiments.
2. One continuing user relationship/interaction point.
3. No ordinary desktop is the permanent host.
4. Cloud is replaceable infrastructure.
5. Edge safety is local/deterministic.
6. World Model current state is distinct from historical memory.
7. OSCAR Event Archive is canonical memory history; vector/graph indexes are derived/rebuildable.
8. Personal/historical recall claims require retrieved evidence provenance.
9. Failed memory retrieval is not proof of absence.
10. Tool/model/Worker success is not verified completion.
11. Capability availability is discovered, not assumed.
12. Persona changes expression, never truth/authority.
13. Sentry awareness and recording are different permissions/modes.
14. Freshness-sensitive current facts use live authoritative evidence when reasonably available.
15. `CAN PERCEIVE`, `CAN RETAIN` and `CAN ACT` are independent boundaries.
16. Notification access never implies unrestricted source-app access.
17. A gate is completed end-to-end before development advances to the next Club unless the owner explicitly changes the plan.

## Club C / Slice 07 Edge composition

Gate B is frozen PASS. Core/Grid → outbound HTTPS ESP32 gateway → typed 3.3 V
UART → deterministic Pico GPIO/ADC/interlock controller. These are Edge nodes,
never Core hosts. Shared C wire/parser/controller contracts run in firmware and
host reference simulation. See [Edge architecture](EDGE.md) and [owner physical
acceptance](EDGE-HARDWARE-ACCEPTANCE.md). Native Grid scopes, PersonalPolicy and
Action Ledger guard physical requests; local safety needs no model/network.

Capability Evolution remains future non-blocking backlog: OSCAR may detect
repeated capability gaps or inefficient browser/computer/phone automation and
propose a Skill/plugin/MCP/native adapter. A Builder Worker such as Codex may
build it only after owner authorization, tests and permission review. Generated
capabilities gain no authority automatically. No self-extension in Slice 07.

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

## Capability Evolution — future backlog

Repeated inefficient or impossible browser/computer/phone workflows may produce
an owner-reviewable proposal:

```text
existing Skill sufficient? → create/refine Skill
API/native integration better? → propose Plugin / MCP / provider adapter
device integration needed? → propose native capability
```

Only after owner authorization may a Builder Worker such as Codex build it.
Generated capabilities gain **zero authority automatically**. Promotion requires
permission review, OAuth/API scopes, credential boundary, Personal Policy,
verification, tests, capability registration and rollback/removal. This is future
architecture/backlog work, not current self-modification.

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

### Voice portability invariant

Voice Core is surface-independent. Wake/VAD, STT, Voice Identity/TTS, barge-in,
self-voice suppression, Voice Match, Voice Map, Persona, policy and arbitration
remain shared contracts across Windows, Android/OSCAR Mobile, Linux/macOS and future
Home Node surfaces. Platform-specific audio, lifecycle, permissions, AEC and
hardware acceleration live behind adapters.

Windows is a current reference implementation only. Android/OSCAR Mobile is a first-class
target. Windows evidence never implies Android verification.

### Post-alpha adaptive local intelligence

After stable Unified Alpha use, owner-controlled Operating Logs should provide
structured evidence about model/provider routes, capability/plugin/Worker calls,
latency, fallback/retry behavior, verification outcomes, failures and recurring
capability gaps. Operating telemetry is not conversation capture and must not
silently become training data.

Measured gaps drive two optimization tracks:

- **Voice Evolution:** use Elocution findings to improve OSCAR's original,
  expressive, natural, cross-surface Voice Identity.
- **Specialist Model Fabric:** train/fine-tune/distill smaller models for recurring
  OSCAR task families only when measured evals show a real advantage.

The target deployment progressively moves persistent Core, Memory Fabric, voice,
specialist models and orchestration onto the owner's dedicated home-server laptop.
Cloud models remain replaceable escalation for major/frontier work.

See [Post-Alpha Evolution](POST-ALPHA-EVOLUTION.md).

## Historical Slice 09 checkpoint — 2026-10-06 (superseded)

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

## OSCAR Mobile application boundary

Native Kotlin/Compose UI and Android adapters exchange scoped state/commands with
Core; they do not implement a second intelligence. MainActivity owns composition
only. CoreSession owns foreground session/readback StateFlow; typed decoding rejects
invalid remote payloads. Screen composables consume state/actions independently.
Keystore, OwnerConfirmation, notification and portable PCM/audio adapters are
platform boundaries. New package identities require explicit trusted enrollment.
See [Mobile architecture](MOBILE-FOUNDATION.md).
