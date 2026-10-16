# Group 3 — Gate D engineering run

Owner authorization: 2026-10-16 unattended local backend work through canonical
Slices 14–17, in dependency order. This supersedes older dated prohibitions only
within this scope. Base: `257349f82a96293c3737d446dca18ce46f098b04`, verified by
fetch and merged PR #6 readback. Branch: `codex/group-03-gate-d`. No merge/release.
Approved Mobile/Desktop UI, artwork and Orb are preserved. No device, emulator,
microphone/camera, owner account, host configuration or paid infrastructure work.

## Implementation and acceptance

| Slice | Implemented | Verified | Remaining |
|---|---|---|---|
| 14 | Bounded typed World Model, permission-aware Perception, headless Sentry, existing live-context adapter | Local SQLite and synthetic source failure scenarios; see receipts | Full service integration, real multi-source acceptance, capture/journal, production admission |
| 15 | Not started | Not run | Recoverable commissioning using existing Grid/Vault boundaries |
| 16 | Not started | Not run | Shared subscriptions, Presence and typed AIE descriptors |
| 17 | Not started | Not run | Executive responsibilities/schedules using existing Runtime |

Gate D is **PARTIAL**; Gate C remains **PARTIAL**. Headless software/reference
evidence does not establish physical, owner, live environmental or production PASS.

## Slice 14 ownership and safety

`world_model.py` owns current projections and explicit current/stale/unavailable/
unknown/conflicting states. `perception.py` owns source configuration, leases,
generation/sequence fencing, deduplication, source rate limits and independent
perceive/retain/act grants. `sentry.py` owns quiet mode and escalation **proposals**.
`perception_adapters.py` bridges existing authorized `LiveContextSource` contracts,
including actual `StateContextSource` Grid snapshots, rather than replacing them.

All are **trusted local composition APIs**. Source IDs, epochs and evidence refs
are provenance, not authentication. There is no network admission endpoint. Any
future remote source must authenticate and bind its identity through the existing
Grid/transport boundary before ingestion. Configuration never grants Full Access.
No notification, speech, action or capture is executed by these modules.

Current pointers store identity, expiry and canonical event references, not another
history. Without retention, content exists only in a bounded process cache; after
restart it is unavailable. With retention, the Event Archive owns the only durable
observation payload. Existing Memory Fabric retrieval stays historical/RECALLED;
current status never falls back to a memory as present truth. Reported source data
never becomes VERIFIED simply because ingestion succeeded. Simulated sources are
explicit and cannot displace real source reports. Conflicting peer reports remain
conflicting until superseded/expired; this implementation does not infer resolution.

Bounds: 64 registered sources, 512 current pointers, 128 recent receipts/source,
1–600 events/source/minute, 2 KiB values, 1 hour maximum freshness, 5 minute maximum
connection lease, 2,048 retained observation payloads/relationship and 7 day maximum
retention. Ingestion is synchronous: capacity returns explicit backpressure rather
than building an unbounded queue. Renewals are caller-driven; no daemon is installed.
`EventArchive.purge_expired_events()` removes expired event/dependent-memory payloads
and invalidates derived generations. Call it during explicit maintenance; stale
derived indexes cannot bypass canonical admission. Tombstones/WAL/backups are not
securely erased. Revocation drops current access immediately; separately authorized
historical retention expires or can be forgotten through existing Memory Fabric.

Archive append precedes the current-pointer transaction commit across separate
SQLite stores. A failed projection may leave a retained canonical observation but
no current claim. Retrying the exact event repairs it idempotently, including at
history capacity. Nothing infers current state from an orphan event. Uncommitted
volatile content is not published. Corrupt cross-relationship pointers fail closed.

Sentry configuration is versioned/generation-fenced and survives restart. Manual,
Trigger-only and Sentry are separate from Passive/Aware/Guard/Away/Sleep state.
Minimum confidence, exact configured trigger keys, cooldown, quiet Sleep behavior,
source act grant and current Personal Policy gate interruption proposals. Final
admission rechecks configuration and source grants in one SQLite transaction.
These settings do not activate real environmental monitoring or delivery.

## Verification and continuation

Baseline: `python -m unittest discover -s tests -t .` ran 569 tests in 218.479 s;
563 passed, 6 skipped, 0 failed. Log: ignored `.oscar/group03-baseline-tests.log`.
New Slice 14 tests exercise real disposable SQLite; source/event fixtures remain
**SIMULATED**. The native Grid adapter reads real local Core records and tests
revocation readback; it does not contact a device. No new dependency was added.

Commands:

```powershell
python -m unittest tests.test_world_model -v
python -m scripts.benchmark_world_model --output docs/evidence/group03/world-before.json
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m unittest discover -s tests -t .
python -m scripts.check_repository
```

Machine-readable continuation: [progress.json](../evidence/group03/progress.json).
Slice 14 checkpoint: full offline regression ran **602 tests in 124.948 s**, with
596 passes, 6 skips, no failures. Subsequent review corrections and additional
cases passed the focused **36-test** suite. Ruff lint/format, strict mypy across
68 modules, repository/link/secret checks and diff checks passed. Existing baseline
lint/format defects in three files were repaired without product behavior changes
(one unused loop name and formatting in Desktop and asset tooling).

Independent review found and drove regression coverage for cross-connection
revocation/configuration races, cross-relationship corrupt pointers, commit-stage
volatile rollback, canonical capacity recovery and authorization before acquisition.
The adapter checks before retrieval and rechecks the captured epoch afterward,
including empty replies. An in-progress synchronous external callback is not
forcibly interrupted; revoked/changed output is rejected. Real capture cancellation
and authenticated remote source admission remain unimplemented.

Measured 100 comparable synthetic samples with 512 current rows and real SQLite:
[before](../evidence/group03/world-before.json) p50 4.708 ms / p95 5.713 ms;
[after](../evidence/group03/world-after.json) p50 0.404 ms / p95 0.474 ms.
SQL filtering avoids deserializing every current row per lookup. Both runs assert
the selected value and deterministic Controller route with zero model/external
tool calls. Disconnect/reconnect was 6.827 → 2.709 ms. Traced allocation peaks were
4,272,744 → 3,701,741 bytes; this is benchmark allocation, not total process RSS.
No browser or Codex speed-parity claim is made. Benchmark fixtures are SIMULATED.

Transaction design follows [SQLite transaction semantics](https://www.sqlite.org/lang_transaction.html)
and Python's sqlite3 documentation; the existing Store owns explicit transactions.
Full Slice 14 and Gate D acceptance remain distinct from this scoped checkpoint.
