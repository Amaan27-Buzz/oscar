# Club B checkpoint

**Current status: Slice 05 PARTIAL · Slice 06 PARTIAL · Gate B PARTIAL.**

Gate A remains PASS. No Slice 07/Club C implementation is accepted until Gate B's mandatory end-to-end acceptance passes.

This checkpoint is the current summary. Detailed earlier reference/Windows evidence is preserved in machine-readable evidence files and Git history rather than duplicated as an active architecture plan.

## Preserved evidence

- [Club B reference evidence — 2026-10-03](evidence/club-b-reference-2026-10-03.json)
- [Club B Windows evidence — 2026-10-04](evidence/club-b-windows-2026-10-04.json)

These evidence artifacts remain historical observations. They do not automatically verify later architecture or capabilities.

## Accepted scoped foundations

### Slice 05 — machine/continuation

Verified for the documented Windows/reference scope:

- real scoped file read/write/list/search and UTF-8 handling;
- traversal/reparse/junction/symlink safety checks documented in the Windows acceptance;
- explicit executable allowlist and filtered environment;
- native Windows Job Object process-tree control;
- timeout/output bounds and descendant cleanup;
- Git status/diff/log/commit;
- useful authenticated Codex specialist objective on a disposable repository;
- executor result remained REPORTED while independent behavioral/Git/file evidence established the accepted result;
- real cancellation of a Codex subprocess;
- coordinator/Worker restart and recovery of a completed result without duplicate mutation;
- ambiguous post-mutation Worker loss BLOCKED replay;
- Windows pause semantics truthfully limited to cooperative pause before the next subprocess rather than fake arbitrary-process suspension;
- trusted-host execution explicitly documented as **not an OS sandbox**.

The final merged baseline also received Windows/Ubuntu CI acceptance after stabilizing the disconnect race in the reference test.

### Slice 06 — continuity/policy foundation

Verified for the documented local/reference scope:

- selected local memory survives process restart;
- retrieved historical content remains RECALLED;
- live filesystem state outranks stale retained text;
- forget removes the live OSCAR record without a secure-erasure claim;
- explicit structured Personal Policy persists across restart;
- missing permissions and equal-authority policy conflicts block;
- bounded message/send natural-language policy templates require shown interpretation and exact owner confirmation;
- ambiguous/changed/conflicting interpretations do not silently activate.

This foundation remains useful, but it is not the completed production memory/policy architecture.

## Memory architecture correction

The earlier plan to integrate Supermemory has been **retired**. It is not a current Gate B dependency.

OSCAR now owns a free/self-hosted Memory Fabric:

```text
canonical OSCAR Event Archive
SQLite + WAL + FTS5
      │
      ├─ Qdrant OSS semantic/hybrid derived index
      └─ Graphiti OSS + Neo4j Community temporal/entity derived index
                │
        Retrieval Fusion + local reranker
                │
        Jev Memory Preflight
                │
          Context Assembly
                │
          Claim Verification
```

Qdrant and Graphiti/Neo4j are derived/rebuildable indexes. The Event Archive is canonical historical source/provenance.

The previous `MemoryBackend`/Supermemory language in older evidence and Git history describes the previous design, not current intent.

See [MEMORY.md](MEMORY.md).

## Remaining mandatory Slice 05 acceptance

Gate B completion still requires:

1. **Typed PowerShell/terminal**
   - discover legitimate installed executable;
   - allowlisted bounded execution;
   - cwd/environment/output/timeout/cancel evidence;
   - no inherited OSCAR provider credentials.

2. **Installed-app catalog**
   - discover apps from legitimate Windows sources;
   - stable OSCAR app identity/provenance;
   - launch/availability semantics;
   - do not infer capabilities merely from executable presence;
   - harmless real-app acceptance.

3. **Windows computer use**
   - UI Automation first;
   - bounded window/element inspection;
   - focus/read/invoke/set-value where legitimate;
   - keyboard/mouse fallback only when structured automation is unavailable;
   - independent resulting-state verification.

4. **Typed browser runtime**
   - isolated profile/context;
   - navigate/inspect/click/fill/submit/wait/screenshot/close;
   - cancellation/timeouts/output bounds;
   - deterministic local fixture and bounded public-page acceptance;
   - independent DOM/state verification;
   - browser remains distinct from Search.

5. **Owner-control continuation**
   - separate control process observes a real long-running task;
   - control disconnect does not destroy permitted work;
   - coordinator/control reconnects to the same durable task;
   - pause/resume only where semantics are real, or cancel;
   - no duplicate execution;
   - independently verified final state.

6. **Power-control contract where implemented**
   - only expose real detected capability;
   - sleep/shutdown/restart are high-risk and explicitly owner-confirmed;
   - physical shutdown/sleep need not be automated merely for Gate B.

## Remaining mandatory Slice 06 acceptance

### A. Canonical Event Archive

- SQLite WAL canonical event history;
- FTS5 historical exact/full-text retrieval;
- stable event/turn/episode/entity/memory/source IDs;
- provenance/evidence/retention metadata;
- corrections/supersession links.

### B. Qdrant OSS semantic retrieval

- dense + sparse/hybrid retrieval where appropriate;
- metadata filters;
- canonical archive IDs on indexed records;
- rebuild and drift/lag detection.

### C. Graphiti + Neo4j temporal/entity memory

- canonical entities/aliases;
- relationships and temporal validity;
- current-vs-historical fact retrieval;
- correction/supersession propagation;
- source-event provenance;
- same-name/ambiguous entities remain separate without evidence.

### D. Local/replaceable embeddings and reranker

- provider-independent interfaces;
- local/self-hosted default where practical;
- cloud/model-router path optional rather than required.

### E. Jev Memory Preflight / retrieval planner

For history/personal/project/entity/artifact/preference context:

```text
Active Context
→ structured OSCAR state/entities/tasks/policy
→ Event Archive exact/FTS5
→ Qdrant hybrid
→ Graphiti temporal/entity
→ alias/entity/time-range expansion
→ bounded deep archive reconstruction
→ UNKNOWN
```

Required invariants:

- an empty first retrieval is not proof memory never existed;
- `I remember X` requires actually retrieved/active provenance;
- personal/historical claims retain source IDs;
- recall remains RECALLED in the current reasoning path;
- live authoritative current state outranks stale memory;
- model reasoning cannot promote inference into fact.

### F. Memory Writer/consolidation

- source-backed candidate extraction;
- scope/overgeneralization checks;
- entity resolution;
- contradiction/supersession handling;
- background dedup/evidence merge/summary/index maintenance;
- source events remain canonical.

### G. Forget/rebuild/resilience

- truthful forget/tombstone semantics;
- remove relevant vector/graph derived entries;
- no false secure-erasure/external-deletion claim;
- rebuild Qdrant and temporal/entity derived state from canonical archive;
- derived-index failure falls back to archive/FTS/UNKNOWN, never invented recall.

### H. Memory evaluation suite

Synthetic/non-sensitive benchmark coverage:

- exact long-history recall;
- paraphrase semantic recall;
- temporal current-vs-history;
- preference supersession;
- aliases/same-name disambiguation;
- project switching;
- false-memory claims;
- expected-memory miss escalation;
- stale-memory-vs-live;
- correction;
- forget;
- index rebuild/drift;
- cross-process continuity.

### I. Open-ended Personal Policy

```text
natural-language rule
→ bounded structured candidate
→ show interpretation
→ exact owner confirmation
→ active policy
```

Support broader conditions/scope/effects, ambiguity rejection, equal-authority conflict blocking and expiry where expressed. Policy still cannot grant permission or bypass safety/confirmation.

### J. Real private connector/OAuth lifecycle

At least one useful private provider end-to-end:

- current official OAuth flow;
- minimal scopes;
- PKCE/device/system-browser flow as appropriate;
- state/nonce validation;
- expiry/refresh/revoke where supported;
- secure platform credential boundary;
- no raw token in model prompts, memory, ledger, logs or repository;
- harmless private read;
- one reversible write/readback/cleanup only after explicit owner approval.

### K. Live-context federation

Demonstrate a real conflict where stale recall says X and current authoritative evidence says Y. Current answer must use Y while preserving historical recall/provenance.

At minimum combine current local project/file/task state, one authenticated private source when available and public/search evidence when relevant.

## Gate B pass rule

Gate B becomes PASS only after the required Slice 05/06 scenarios above are genuinely exercised and evidence-backed.

Automated test count alone is insufficient.

A genuinely blocked external/owner-auth dependency remains explicit and must be completed before Club C unless the owner deliberately re-scopes the plan.

## Current next step

```text
finish Slice 05 machine gaps
→ implement/verify production Memory Fabric
→ finish open-ended policy
→ complete real OAuth/private connector + secure storage
→ live-context-vs-memory federation
→ full Gate B acceptance
→ update evidence/docs
→ merge/review
→ Gate B PASS
→ only then Slice 07 / Club C
```
