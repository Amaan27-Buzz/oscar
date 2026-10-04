# Changelog

Significant OSCAR milestones are recorded here. Detailed implementation status is canonical in `docs/ROADMAP.md`; detailed acceptance evidence remains in `docs/evidence/` and Git history.

## 2026-10-04 — Gate B local completion candidate

Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](docs/GATE-B-COMPLETION.md).

## 2026-10-04 — OSCAR Memory Fabric architecture replaces managed memory dependency

- Retired the planned Supermemory dependency from active architecture.
- Made the OSCAR Event Archive the canonical historical source using SQLite + WAL + FTS5 initially.
- Selected Qdrant OSS as the first rebuildable semantic/hybrid retrieval index.
- Selected Graphiti OSS + Neo4j Community as the first rebuildable temporal/entity memory index.
- Defined replaceable local/self-hosted embedding and reranking boundaries.
- Added Jev Memory Preflight so historical/personal/project/entity/artifact/preference references trigger retrieval before factual recall claims.
- Defined bounded retrieval escalation: Active Context → structured OSCAR state → FTS/archive → Qdrant hybrid → Graphiti temporal/entity → alias/time expansion → bounded deep archive → UNKNOWN.
- Added the invariant that an empty retrieval is not proof memory never existed.
- Added evidence-bound recall: no `I remember X` without retrieved/active source evidence; historical/personal claims retain source event/memory IDs.
- Defined corrections/supersession, entity resolution, candidate memory formation, background consolidation, forget/tombstone and derived-index rebuild/drift semantics.
- Added a Memory Fabric evaluation plan covering exact/paraphrase recall, temporal correctness, aliases/disambiguation, false recall, expected-memory misses, correction, forget, rebuild and live-vs-memory authority.
- Rebased Gate B/roadmap/architecture/product/agent instructions around finishing the full planned Slice 05–06 scope before Club C.

## 2026-10-04 — Native Windows Club B acceptance foundation

- Added native Windows Worker path with reparse-aware file handling, explicit executable allowlist, filtered environment, suspended process creation and Job Object process-tree lifetime.
- Verified filesystem/Git/process behavior, cancellation, timeout/output bounds and descendant cleanup on Windows.
- Ran a useful authenticated Codex specialist objective against a disposable repository and independently verified behavior/Git/file state rather than trusting Codex testimony.
- Verified actual coordinator/Worker restart and completed-result recovery without duplicate mutation.
- Verified abrupt post-mutation Worker death blocks replay rather than guessing outcome.
- Verified selected local memory continuity across process restart, RECALLED semantics, live-filesystem precedence and truthful forget of the live OSCAR row.
- Added bounded owner-confirmed natural-language policy authoring for the accepted local scope.
- Preserved trusted-host execution as explicitly **not an OS sandbox**.
- Gate B remained PARTIAL because full browser/computer-use/app/owner-control/memory/policy/private-service acceptance was still incomplete.

## 2026-10-03 — Club B reference foundation

- Added native Connector Fabric foundations with Google plus thin Microsoft/GitHub/Slack/Notion/MCP adapters.
- Added separate-process reference Machine Worker over real loopback HTTP with scoped files/Git/terminal, checkpoints/leases, pause/resume/cancel and restart/reclaim semantics.
- Added selected local memory, explicit structured Personal Policy, live federation and evidence-backed entity mappings.
- Preserved provider/private payloads outside durable action state through referenced transient context.
- Verified lost-result recovery and independent artifact/Git checks for the reference scenario.
- Kept private accounts, public remote deployment and broader machine/policy/memory capabilities explicitly partial.

## 2026-10-03 — Gate A accepted

- Completed the freshness/search correction after stale provider-model assumptions were discovered.
- Added fresh provider inventory, account-product/shared-quota semantics and source/scope/time/TTL/conflict metadata.
- Verified current multi-provider generation for the accepted foundation.
- Added replaceable Tavily search integration and source-qualified current-evidence acceptance.
- Preserved public provider facts, account-visible inventory, generation access and funding/quota as separate evidence scopes.
- Gate A became PASS for the documented Brain foundation.

## 2026-10-02 — Club A Brain foundation

- Added typed Core/SQLite objective/task/action/result/evidence contracts.
- Added independent verification and Action Ledger/Artifact foundations.
- Added TypeSafe Jev routing.
- Added authenticated loopback reference transport, capability advertisement, replay/idempotency, cancellation, Grid availability and durable leases/reclaim.
- Added adaptive native Model Router with multiple routing modes, credential pools and bounded fallback.
- Added contract/failure/reference-network tests and secret-safe repository checks.

## 2026-09-29 — Repository foundation

- Established OSCAR product/architecture/engineering/design direction.
- Established one-intelligence/many-embodiments topology: Sunday, replaceable cloud coordination, Desktop nodes and OSCAR Edge.
- Established Voice/Sentry/Persona/Personal Policy/Workers/Protocols/World Model/Perception/Executive/Action Ledger/Artifact directions.
- Established Quietly Alive + Playful Precision design language.
- Added slice roadmap, Build Gates and thin coding-agent adapter architecture.

## Current status

```text
Gate A — Brain          PASS
Gate B — Can Do Work    PARTIAL — current work
Gate C — Embodied       planned after Gate B PASS
Gate D — JARVIS Layer   planned
Gate E — Unified Alpha  planned
```

Current Gate B completion order is defined in `docs/ROADMAP.md` and `docs/BUILD-GATES.md`.
