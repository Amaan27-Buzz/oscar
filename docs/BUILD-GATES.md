# Build Gates

Build Gates group detailed roadmap slices into larger manual verification checkpoints. They do not replace slice exit conditions.

At each Gate:

1. run automated tests;
2. run required manual scenarios;
3. inspect authoritative resulting state;
4. record blockers/limitations;
5. do not upgrade simulated/reported behavior to verified real behavior;
6. complete the planned mandatory scope before advancing to the next Club unless the owner explicitly re-scopes the plan.

A gate is not `PASS` because the implementation is demoable.

## Gate A — Brain

**Slices:** 01–04

Prove:

```text
request
→ Controller
→ capability/model/retrieval decision
→ native transport/router
→ execution
→ evidence
→ verification
→ truthful report
```

Required acceptance includes canonical file verification, fake-success rejection, deterministic requests avoiding unnecessary models, automatic/manual model routing, provider/credential fallback, Local mode without silent cloud fallback, reference Grid connect/disconnect, durable objective preservation, secret-safe route history and freshness-sensitive live search.

**Pass:** native core/transport/model/search foundation works without required Latch/SwitchRoute deployment, current information is refreshed when needed and remote/reference node loss does not erase objective state.

**Current:** **PASS.** See [CLUB-A-CHECKPOINT.md](CLUB-A-CHECKPOINT.md).

Public TLS/rendezvous, independent remote stores and physical deployment remain later integration acceptance rather than retroactively making Gate A partial.

## Gate B — Can Do Work

**Slices:** 05–06

Gate B proves that OSCAR can do useful verified work through a replaceable machine node while preserving continuous memory, policy and live-context authority.

Gate B must be completed end-to-end before Club C starts.

### B1 — Real machine work

Required manual acceptance:

- real repository bug delegated to a coding specialist and independently tested;
- scoped filesystem/Git work;
- typed terminal/PowerShell capability;
- installed application discovered/selected as an app capability rather than generic host command;
- structured Windows computer-use/UI Automation on a harmless real application;
- typed browser capability against a deterministic local fixture plus bounded public page;
- independent readback/observation after browser/desktop mutation;
- machine node disconnect mid-task → BLOCKED/recoverable, not false success;
- ambiguous consequential mutation is not blindly replayed;
- cancellation stops the actual process tree;
- no duplicate mutation after restart/lost-result recovery.

### B2 — Long-running continuation and owner control

Using existing Connection Grid contracts and a separate control process:

```text
start bounded long-running task
→ owner-control observes task/progress/node
→ owner-control disconnects
→ Worker continues within existing authorization
→ coordinator/control reconnects
→ same task state recovered
→ pause/resume where genuinely supported or cancel
→ no duplicate execution
→ independently verified final state
```

This is a control-path proof, not Sunday UI.

Optional physical sleep/shutdown acceptance may remain manual-pending; do not shut down the development machine merely to make Gate B green. The typed power capability, if present, must remain high risk and owner-confirmed.

### B3 — Canonical Memory Fabric

Required architecture:

```text
OSCAR Event Archive
SQLite + WAL + FTS5
      │
      ├── Qdrant OSS semantic/hybrid derived index
      └── Graphiti OSS + Neo4j Community temporal/entity derived index
```

The Event Archive is canonical. Vector/graph indexes are rebuildable derived state.

Required acceptance:

- durable source event with stable provenance IDs;
- exact/FTS retrieval;
- paraphrased/hybrid Qdrant retrieval;
- temporal/entity Graphiti retrieval;
- current fact vs historical fact correctly distinguished;
- preference correction/supersession preserves old history but changes current answer;
- same-name/alias entity tests do not merge identities without evidence;
- restart preserves canonical continuity;
- Qdrant/graph index rebuild from canonical archive;
- stale/failed derived index falls back truthfully rather than inventing memory;
- forget removes/tombstones active OSCAR memory/index state according to policy without false secure-erasure claims.

### B4 — Controller memory reliability

Controller must perform memory dependency preflight rather than let the reasoning model guess whether memory exists.

Required behavior:

```text
historical/personal reference
→ retrieval mandatory
→ active context
→ structured state/entities/tasks/policy
→ FTS/exact archive
→ Qdrant hybrid
→ Graphiti temporal/entity
→ bounded query expansion/deep archive
→ UNKNOWN
```

Required tests:

- `continue that`/`same as before`/existing project references trigger retrieval;
- deterministic unrelated questions avoid unnecessary memory work;
- empty first retrieval triggers bounded expansion rather than `not remembered`;
- no `I remember X` without retrieved/active source evidence;
- personal/historical claims expose source event/memory provenance internally;
- recalled historical material remains `RECALLED` in the current reasoning path;
- live authoritative current state outranks stale memory;
- reasoning/model output cannot promote inference into fact.

### B5 — Memory Writer and evaluation

Required acceptance:

- memory extraction creates provenance-bound candidates, not model-authored truth;
- scoped preference inference does not overgeneralize;
- corrections propagate to semantic/temporal indexes;
- background consolidation preserves source events;
- synthetic/non-sensitive evaluation covers exact recall, paraphrase recall, temporal correctness, alias/disambiguation, project switching, expected-memory miss escalation, false recall, correction, forget, rebuild/drift and live-vs-memory authority.

### B6 — Personal Policy

Required acceptance:

```text
natural-language policy
→ bounded structured candidate
→ show interpretation
→ exact owner confirmation
→ active policy
```

Test representative open-ended rules, scope/conditions, ambiguity, conflicting equal-authority rules, expiry and later real behavior.

Policy cannot grant missing permission, bypass strong confirmation, weaken hard safety or be overridden by Persona/memory.

### B7 — Real private connector / OAuth

Complete at least one useful private service end-to-end using a current official auth flow.

Required acceptance:

- minimal scopes;
- PKCE/device/system-browser flow as appropriate;
- state/nonce validation;
- token expiry/refresh/revoke where supported;
- platform secure-credential boundary;
- raw tokens never enter Git, model prompts, memory, Action Ledger or logs;
- harmless private read;
- one reversible write/readback/cleanup only after owner approval.

If owner authorization is required, STOP only at that interactive authorization point; do not fake account acceptance.

### B8 — Live context vs memory

Demonstrate a real conflict:

```text
memory says X
current authoritative source says Y
→ OSCAR answers Y for current-state question
→ memory stays historical/RECALLED
→ provenance explains the conflict
```

At minimum federate current local project/file/task state, one authenticated private source when available and public/search evidence when relevant.

### Gate B pass condition

**PASS** only when mandatory Slice 05 and Slice 06 scenarios above are genuinely accepted and recorded.

Automated tests are necessary but insufficient.

A genuinely unavailable external/private step remains BLOCKED/PARTIAL until completed; it is not silently deferred to Club C.

**Current: PASS for documented local-alpha acceptance.** Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

See [CLUB-B-CHECKPOINT.md](CLUB-B-CHECKPOINT.md), [ROADMAP.md](ROADMAP.md) and [MEMORY.md](MEMORY.md).

## Gate C — Embodied OSCAR

**Slices:** 07–10

Starts only after Gate B PASS.

Prove physical, voice, mobile and desktop embodiments share one OSCAR.

Required scenarios include:

- ESP32/Pico capability advertisement and safe physical action with local safety;
- wake OSCAR by voice and complete a real task;
- barge-in/self-voice suppression;
- Voice Match vs Voice Map distinction;
- multi-device voice arbitration;
- Persona changes expression without changing truth/permission;
- Sunday owner-control surface shows Connection Grid state;
- start task on Desktop, leave, inspect/control from Sunday;
- one supported communication path;
- Dictate/Edit/Ask/Act against real desktop context;
- degraded Grid state when one embodiment goes offline.

**Pass:** phone, desktop, voice and Edge feel like one intelligence with shared task/memory state and owner control.

## Gate D — JARVIS Layer

**Slices:** 11–14

Prove current-world awareness, persistent Sentry, commissioning and durable delegated work.

Required scenarios include combining multiple live sources into the World Model, stale-state uncertainty, persistent Sentry without active conversation, capture/privacy boundaries, commissioning, durable Worker inspection, competing objectives, evaluated learned workflow and UI/avatar correspondence to real runtime state.

**Pass:** OSCAR maintains coherent current awareness, durable responsibilities and optional continuity capture without collapsing privacy/evidence boundaries.

## Gate E — Unified Alpha

**Slices:** 15–17

Deliberately break the integrated system.

Required scenarios include provider/auth failure, coordinator/node/Edge loss, Grid resync, Action Ledger/Undo, memory-index failure/rebuild, unknown/partial/blocked reporting, voice spoof/false-positive checks, capture retention/deletion, Persona truthfulness regression and one complete end-to-end scenario across perception/communication → World Model/Controller/Memory Fabric → policy/planning → capability/model routing → Grid/Worker/device → ledger/artifact → verification → Sunday/voice/text result.

**Pass:** major subsystems operate as one evidence-backed developer alpha and remaining limitations are explicit.

## Status

| Gate | Slices | Status |
|---|---|---|
| Gate A — Brain | 01–04 | **PASS** |
| Gate B — Can Do Work | 05–06 | **PASS for documented local-alpha acceptance** |
| Gate C — Embodied OSCAR | 07–10 | PARTIAL; Slice 07 software accepted, physical deferred; 08 next, 09–10 unbuilt |
| Gate D — JARVIS Layer | 11–14 | Planned |
| Gate E — Unified Alpha | 15–17 | Planned |


## Reconciliation boundary — 2026-10-04

The OSCAR-owned Decision / Epistemic Controller applies hard deterministic authority
rules; `oscar/jev.py` is a historical/internal module name, not a TypeSafe Jev
dependency. Separate deterministic/Laya/hybrid evaluation starts only after Gate B
PASS. GitHub is the first intended private authentication proof; the shared Auth
Broker/provider architecture does not require independent OAuth per plugin.

[Deployment architecture](DEPLOYMENT.md) selects free-first Oracle persistent Core
and Vercel bounded Python/web/API/relay candidates. Deployment, the future Galaxy
Tab S6 Lite Home Node, decision-model evaluation and full Auth Broker expansion are
not additional Gate B requirements. Build the Tab node only after OSCAR is fully
deployed and its main Core architecture is operational.

Slice 05/06 COMPLETE; Gate B PASS for the documented local-alpha scope. Owner
physical machine run `manual-gate-b-20261004-200734` and OAuth/federation run
`oauth-gate-b-20261004-234817` passed. Remote revocation remains unknown, optional
private writes were not authorized, Slice 07 software is accepted; physical acceptance is deferred by owner and PR 12 MERGED; Gate B frozen PASS. The harness repair at
`c9cb7d2d20fb444cce98e2749eeea5425d4a0ee1` is independently reviewed with 25 focused
regressions passing and exact-head CI green; it is not a physical acceptance PASS.
The prior owner focus failure and its evidence remain unchanged.

See [owner OAuth acceptance](GATE-B-OAUTH-ACCEPTANCE.md) and
[physical machine PASS evidence](evidence/gate-b-owner-machine-pass-2026-10-04.json).
The reported prior stale OSCAR fixture was not mutated; it does not invalidate the PASS.

## Club C current boundary — 2026-10-05

Gate C PARTIAL; Slice 07 closure/integration and Slice 08 authorized after frozen Gate B PASS. Edge host
simulation and firmware compilation are separate evidence classes; neither
grants physical PASS. Owner ESP32/Pico acceptance is mandatory: [exact hardware
sequence](EDGE-HARDWARE-ACCEPTANCE.md). Slices 08–10 not started. See [checkpoint](CLUB-C-CHECKPOINT.md).

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
The owner authorizes Slice 08 after Slice 07 integration; Slice 09/10, deployment
and Galaxy Tab Home Node remain outside this work.
