# OSCAR — Build Gates (current truth 2026-10-18)

**2026-10-21 local candidate:** signed Secure/Full delegation is implemented and
tested with synthetic native credentials; intended-surface integration remains
under acceptance. The earlier “unavailable” statement below is historical.
See the [active completion ledger](development/OSCAR-FULL-SOFTWARE-COMPLETION.md).
Gate classifications remain unchanged.

See [current checklist](CURRENT-STATUS.md), [delivery groups](DELIVERY-PLAN.md), [canonical slices](SLICE-NUMBERING.md) and [roadmap](ROADMAP.md). Gates are **acceptance**; groups are **delivery order**. Green CI only verifies the exercised software environment, not a physical device or deployment.

| Checkpoint | State |
| --- | --- |
| Gate A, Slices 01–04 | **PASS**, documented scope |
| Gate B, Slices 05–06 | **PASS**, local-alpha scope |
| Gate C, Slices 07–10 | **PARTIAL**, physical Edge/voice/owner phone and desktop tests outstanding |
| Design, Slices 11–13 | Character renderer merged; Desktop provisional owner pass, Android UI/UX owner approved |
| Gate D, Slices 14–17 | **PARTIAL**, single Group 3 PR #7 software **MERGED with green CI**; live/owner/remote acceptance pending |
| Gate E, Slices 18–20 | **NOT PASSED**: physical Edge deferred; hardening and full Unified Alpha incomplete |
| Group 6 operational alpha | **NOT VERIFIED**, deliberately narrower Cloud–Desktop–Phone milestone; no Gate C/D/E automatic PASS |

**Owner re-sequencing:** Group 4 Cloud and remote Grid; Group 5 real Desktop/Android + computer use, MCP/plugins, Secure/Full Access, voice, Worker/automation/Chief of Staff; Group 6 scoped alpha; Group 7 dedicated home-server laptop; Group 8 ESP32/Pico and remaining formal acceptance. Critical Internet-facing Slice 19 TLS, auth, privacy and revocation **must be verified in Group 4**, not postponed until Group 8. Physical Slice 18 is **DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED**, software reference **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**. Historical former Slice 17 Unified Alpha is now Slice 20.

---

The current D2/D3–D4 candidate adds authenticated connected software and a scoped
file-execution vertical slice. Its [evidence ledger](development/GROUP-04-D2.md)
separates actual Windows, Linux-container, native ARM64, emulator, hosted and
physical results. A software or emulator result does not close the remaining
owner/device gates. Secure and Full Access remain unavailable.

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

This is a control-path proof, not OSCAR Mobile UI.

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
- OSCAR Mobile owner-control surface shows Connection Grid state;
- start task on Desktop, leave, inspect/control from OSCAR Mobile;
- one supported communication path;
- Dictate/Edit/Ask/Act against real desktop context;
- degraded Grid state when one embodiment goes offline.

**Pass:** phone, desktop, voice and Edge feel like one intelligence with shared task/memory state and owner control.

## Gate D — JARVIS Layer

**2026-10-18:** Group 3 PR #7 merged successfully with green final-head and main CI. Gate D remains **PARTIAL** because live environmental/provider, owner commissioning, physical/OEM, native authoring and production acceptance remain outstanding. See [Group 3 evidence](development/GROUP-03-GATE-D.md). Gate C remains PARTIAL.

**Slices:** 14–17 (World Model, commissioning, full Presence integration and Executive Planner)

Prove current-world awareness, persistent Sentry, commissioning and durable delegated work.

Required scenarios include combining multiple live sources into the World Model, stale-state uncertainty, persistent Sentry without active conversation, capture/privacy boundaries, commissioning, durable Worker inspection, competing objectives, evaluated learned workflow and UI/avatar correspondence to real runtime state.

**Pass:** OSCAR maintains coherent current awareness, durable responsibilities and optional continuity capture without collapsing privacy/evidence boundaries.

**Owner sequencing decision (2026-10-09):** after existing 00–10 foundations,
Slice 11 designs the expressive character; Slice 12 refines Desktop UX and
Slice 13 Mobile UX. These are a **visual/interaction review checkpoint**, not
automatic Gate C or D PASS. Full runtime-bound Presence/Avatar integration is
Slice 16, after Slice 14 World Model and Slice 15 commissioning. See
[canonical numbering](SLICE-NUMBERING.md) and [Expression Core](EXPRESSION-CORE.md).

## Gate E — Unified Alpha

**Slices:** 18–20

Deliberately break the integrated system.

Required scenarios include provider/auth failure, coordinator/node/Edge loss, Grid resync, Action Ledger/Undo, memory-index failure/rebuild, unknown/partial/blocked reporting, voice spoof/false-positive checks, capture retention/deletion, Persona truthfulness regression and one complete end-to-end scenario across perception/communication → World Model/Controller/Memory Fabric → policy/planning → capability/model routing → Grid/Worker/device → ledger/artifact → verification → OSCAR Mobile/voice/text result.

**Pass:** major subsystems operate as one evidence-backed developer alpha and remaining limitations are explicit.

## Status

| Gate / checkpoint | Canonical slices | Status |
|---|---|---|
| Gate A — Brain | 01–04 | **PASS** |
| Gate B — Can Do Work | 05–06 | **PASS for documented local-alpha acceptance** |
| Gate C — Embodied OSCAR | 07–10 | **PARTIAL:** software foundations integrated; Edge/Voice/Mobile/Desktop physical acceptance deferred; legacy PR #16 is archival |
| Design / Character checkpoint | 11–13 | Expression software integrated; Desktop provisionally approved/merged; **Mobile Group 2.5B UI/UX owner APPROVED and PR #6 merged**; physical acceptance remains separate |
| Gate D — JARVIS Layer | 14–17 | **PARTIAL:** integrated software locally verified; live/owner/device acceptance pending |
| Gate E — Unified Alpha | 18–20 | **NOT PASSED**, hardware deferred and acceptance outstanding |

No approved visual prototype proves that OSCAR can execute, perceive, verify,
listen or hold physical safety authority. Conversely, deferring Gate C physical
testing does not prohibit the owner-prioritized Slice 11 design laboratory.
Old gate/slice references in historical evidence preserve their original labels.



## Archived checkpoint history

Dated Gate B/C reports, old owner scope boundaries and former slice names survive in Git history and their specific evidence files. They are **not current execution orders**; the active sequence is in [DELIVERY-PLAN.md](DELIVERY-PLAN.md).
