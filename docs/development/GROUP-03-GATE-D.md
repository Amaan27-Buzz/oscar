# Group 3 — Gate D engineering run

**2026-10-17 engineering closure:** see the [closure handoff](GROUP-03-ENGINEERING-CLOSURE.md)
and current [Gate D report](../evidence/group03/GATE-D-REPORT.md). The 2026-10-16
measurements and receipts below remain historical checkpoints.

Published as [draft PR #7](https://github.com/Amaan27-Buzz/oscar/pull/7), targeting
main; **not merged**. Runtime continuation checkpoints include `e3fb826` (14),
`c7f1a8b` (15), `993a38c` (16), and the Executive delivery recorded in
[the continuation receipt](../evidence/group03/verification-continuation.json).
The Code Review connector
denied GitHub access for this workspace, so remote CI is **UNKNOWN**, not PASS.
Git push and PR state/head readback succeeded through the existing repository
workflow. Later documentation-only commits may advance the branch head.

Owner authorization: 2026-10-16 unattended local backend work through canonical
Slices 14–17, in dependency order. This supersedes older dated prohibitions only
within this scope. Base: `257349f82a96293c3737d446dca18ce46f098b04`, verified by
fetch and merged PR #6 readback. Branch: `codex/group-03-gate-d`. No merge/release.
Approved Mobile/Desktop UI, artwork and Orb are preserved. No device, emulator,
microphone/camera, owner account, host configuration or paid infrastructure work.

## Runtime continuation — 2026-10-16

The consolidated [Gate D report](../evidence/group03/GATE-D-REPORT.md) and
[continuation receipt](../evidence/group03/verification-continuation.json) record
the final integrated verification. Earlier counts below remain checkpoint history.

Slice 14 now composes into the normal `Harness`: one canonical Event Archive,
Controller current-state reads, scoped Desktop/Mobile reads and a bounded background
runner. Explicitly enrolled Core/Grid/task and selected-file subscriptions recover
after restart, disconnect on shutdown/revocation, fence stale runners/acquisitions,
and maintain retention expiry. Manual/Trigger-only modes prevent ambient file reads
before acquisition. No environmental permission is inferred from setup.

`python -m oscar watch-core grid --retain`, `sources`, `world --entity core --key
grid.state` and `serve --seconds 60` exercise the local path. No daemon is installed.
Full regression: 632 ran, 626 passed, 6 skipped, no failures (131.057 s).
Ruff, format, mypy and repository checks passed. See
[runtime receipt](../evidence/group03/slice14-runtime.json).

The current continuation additionally authorizes software setup, shared Presence/AIE,
an explicit opt-in Android Companion overlay implementation/build and Executive.
Physical/OEM/environmental acceptance remains separate; no merge or Group 4.

## Implementation and acceptance

| Slice | Implemented | Verified | Remaining |
|---|---|---|---|
| 14 | Normal Core/Controller lifecycle, bounded authorized source subscriptions, recovery, retention expiry, quiet Sentry proposals | Real local Core/Grid/tasks/files/SQLite; synthetic fault injection and scoped surface reads | Owner live environmental enrollment, capture/optional Journal acceptance and production admission |
| 15 | Recoverable identity/pairing, provider/native Vault composition, Persona/preferences, policy, logical voice and explicit Sentry setup | Setup/revocation tests, disposable native credential regression and simulated device enrollment | Owner account/provider probes, physical pairing, Voice Match/Map and audio calibration |
| 16 | Shared leased Presence, typed AIE, native renderers and explicit opt-in Android Companion overlay | React/Compose contract tests, Windows/Rust and Android build/JVM/lint checks | Overlay/OEM/power/accessibility/visual acceptance on devices; home widgets remain unavailable |
| 17 | Reviewed DAGs, bounded deterministic/model-assisted planning, real Worker assignment, schedules, cancellation/recovery, context gates, replanning, brief and evaluated workflow reuse | Actual local file/arithmetic executors, canonical verification, restart, concurrent DB runners, authority/failure tests; model output fixture only | Owner/native authoring acceptance, live model/environment/provider scenarios and production operation |

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
than building an unbounded queue. The normal bounded runner renews authorized
subscriptions; no daemon is installed.
`EventArchive.purge_expired_events()` removes expired event/dependent-memory payloads
and invalidates derived generations. The normal runner invokes maintenance; stale
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

## Historical foundation verification and continuation

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
Slice 14 checkpoint `e34e665`: full offline regression ran **602 tests in 124.948 s**, with
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

Final focused coverage has **38 World Model/Sentry tests** plus **11 commissioning
tests**. Additional checks prove retained state from a fresh Python process,
reject escalation of a fixture displaced by a real source report, and keep
unverified adapter testimony at a conservative confidence. The commissioning
review also found and verified the in-flight cancellation correction below.

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

Final regression: **618 ran / 612 passed / 6 skipped / 0 failed**, 124.393 s on
Windows Python 3.14.2 / SQLite 3.50.4. The final scope-removal readback change also
passed its 11-test commissioning rerun. Lint/format, strict mypy (69 modules),
repository/link/secret and diff checks pass. Detailed machine-readable
[verification receipt](../evidence/group03/verification.json) records commands and
boundaries. Final benchmark [recheck](../evidence/group03/world-final.json):
p50 **0.400 ms**, p95 **0.466 ms**, versus original **4.708 / 5.713 ms** at 512 rows.

## Slice 15 first vertical slice

`commissioning.py` adds a bounded trusted-local state machine: review_pending →
pairing → paired, with expired/blocked/revoked outcomes. One immutable Core
**instance identifier** binds one relationship; this is not a signing key, owner
authentication or replacement account system. Exact review digests bind node,
scopes, independent requested grants, simulation label, Core identity, expiry and
preallocated session identity. Existing Grid node registration and capability
advertisement remain authoritative. Configuration-only grants do not activate
perception, retention, action policy or Full Access.

`Grid.pair(session_id=...)` is backward-compatible and rejects reuse rather than
overwriting credentials. Pairing intent is durable before token creation. After
an interrupted pairing, explicit `recover()` waits out the 30-second in-flight
fence, revokes that exact session and blocks the setup for renewed owner review.
It never reconstructs or serializes a token. Pending reviews resume across actual
Store close/reopen; expired/altered/replayed/cross-device reviews fail closed.
Readback distinguishes configured from operational, authenticates a supplied
opaque handle and filters capabilities to its reviewed scopes. Missing handles,
offline devices and remaining setup work cannot become an operational claim.

Revocation transactionally fences the owned session and enrollment, preserving
unrelated sessions. Existing Dispatcher cancellation now rechecks current execute
and capability grants at cooperative executor checkpoints. Tests revoke after
admission and independently verify the file was never created. A callback already
inside an indivisible external action cannot be retroactively undone; no claim of
instant rollback is made. Ambiguous mutations keep existing durable dedup fences.
This paragraph describes the historical first commissioning checkpoint. Normal
provider/Vault, Persona, policy, logical voice and Sentry composition is now
implemented by `SetupRuntime`; physical voice enrollment remains pending.

## Browser execution measurement

[Browser receipt](../evidence/group03/browser-plans.json) compares two anonymous
local fixture reads as separate existing browser plans versus one existing batched
plan. Real headless Chromium and OSCAR's actual bounded browser executor were used;
all DOM values and origins were asserted. Five samples per mode, alternated order:
p50 **1,086.268 → 539.342 ms**, tool invocations **2 → 1**, no model calls, 100%
fixture success. p95 is the maximum of this small sample: **3,625.722 → 548.891 ms**;
the first separate-plan run includes cold-start overhead. This demonstrates reuse
of existing batching, not a new browser runtime, production mutation benchmark or
Codex parity. Browser memory/reconnect were not measured. All test browsers and
the disposable fixture server close at the end.

## Integrated continuation and remaining acceptance

[Executive runtime](../EXECUTIVE-RUNTIME.md) records the runnable local workflow,
exact review commands, bounds, current-context admission, retained workflow
candidates, independently verified replay and remaining product limitations.
[Presence evidence](../evidence/group03/slice16-presence.md) separates native
builds from device execution. [End-to-end measurements](../evidence/group03/end-to-end-benchmark.json)
compare the same local tasks against reviewed head `5899798`; CPU/Python allocation
and measurement limits are included. New Presence/Executive timings have no prior
implementation baseline. No production latency or inference claim is made.

Native surfaces expose truthful readback. Native schedule creation/editing remains
unavailable; trusted-local exact reviewed commands provide the working control
path. No standing Full Access, environmental capture, owner credential enrollment,
physical/OEM acceptance, hosted operation or Gate D PASS is inferred. The
continuation's cross-slice test exercises real Core identity/setup, actual local
Grid/task sources, one archive, scoped phone-reference readback, Presence/AIE,
verified file/math DAG execution, revocation and durable restart.
