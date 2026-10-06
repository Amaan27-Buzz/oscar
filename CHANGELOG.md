# Changelog

## 2026-10-06 — Slice 08 software/reference quality closure

- Reconciled authoritative post-alpha docs; preserved future scope and voice portability.
- Benchmarked local RTX 5060 Whisper/Distil/Parakeet and Kokoro/Piper/emergency speech.
- Selected turbo quality STT and original Kokoro reference identity, with explicit fallbacks.
- Fixed utterance playback reuse and cancellation fencing; preserved owner harnesses.
- Physical voice acceptance is owner-deferred to the consolidated Gate C run; no physical PASS.

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
The quality candidate on `club-c/slice-08-voice`, PR #14 into `work`, has measured
local reference evidence against baseline `e8ac8f8bca1cb0cb7909523ac6af906ee289366f`;
integration requires green exact-head CI.
Existing owner harnesses remain mandatory inputs to later consolidated acceptance.
Microphone, real-room AEC/barge-in/self-wake, owner Match/Map calibration, playback,
Android voice and naturalness remain NOT RUN. Windows reference evidence never
implies Android acceptance. See [Voice Core](docs/VOICE-CORE.md) and
[consolidated Gate C acceptance](docs/GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 Sunday software may begin after clean Slice 08 integration; Slice 09 must
remain a draft and stop before owner/device acceptance. Slice 10, deployment and
Galaxy Tab Home Node are not authorized. Physical Edge remains
`DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`, mandatory before Slice 17 PASS.
