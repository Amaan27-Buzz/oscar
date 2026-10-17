# Gate D final engineering closure - 2026-10-17

**Gate C PARTIAL; Gate D PARTIAL.** The Group 3 software closure is locally
verified. [PR7](https://github.com/Amaan27-Buzz/oscar/pull/7) remains draft/unmerged
on `codex/group-03-gate-d`. Software implementation SHA: `4a72cb351a93d444405e55b1fc64d5cb2dedf035`.
Subsequent documentation-only commits advance the delivery head recorded in PR7.
Fetched main/merged PR6: `257349f82a96293c3737d446dca18ce46f098b04`.
Group 2.5B Mobile UI/UX is owner APPROVED; physical/device acceptance is separate.

| Area | Fix | Verification | Remaining |
|---|---|---|---|
| Internal execution sessions | Independent live scoped rotation; one-hour tokens, seven-day enrollment, bounded old-token drain | 1/2/8/24 simulated hours; real restart and no-repeat mutation; revoked/expired authority denied | Explicit local reenrollment after expiry/long sleep; cooperative in-flight limits |
| Presence polling | Persist transitions; reserve publication generations; indexed reads and stable transition identity | Concurrent read/write-count, publisher replacement, TS/Kotlin freshness/replay tests | Owner/device/power acceptance; one reservation write per 1,024 unchanged publications |
| Android Companion | Attach only after authorized fresh Core/local admission; request fencing, watchdog, dismissal and cleanup | 31 app + 6 Expression JVM tests; APK assembly/lint; no device connected | Actual FGS, permission/lock/network/notification/OEM behavior deferred |
| Performance | Reduce World/heartbeat writes and indexed live-lease lookup, retaining verification/auth/dedup | Alternating normal/quiet fresh processes; p50/p95, SQL writes, CPU and Windows working set | Instrumented laptop limits; no battery/device/provider/inference or speed-parity claim |
| Cross-slice integration | Fence expired task before lease release; contain executor defects and preserve ambiguity | Full suite, real process kill/restart, source revoke/recovery, cancellation and independent readback | External indivisible actions cannot be undone; ambiguous outcomes need inspection |

## Verification and evidence classification

Final Python: **678 passed, 0 failed, 6 skipped** (684 tests,
166.202s). Focused closure suite: **76 passed**. Desktop: **86 frontend and
16 Rust tests**, TypeScript/build, format/Clippy and Windows debug executable
passed. Android: **37 JVM tests**, debug/AndroidTest APK assembly and lint passed.
No connected ADB device was present; no emulator/device test was run.
Ruff lint/format (177 files), strict mypy (74 modules), repository/link/secret
checks and Git integrity passed. Existing recoverable dangling objects retained.
Native npm audit reported zero installed package vulnerabilities. Canonical
SVG/native PNG hashes and approved artwork/style files are unchanged.

The [machine-readable receipt](closure-verification.json) gives exact commands,
six optional voice skips, hashes, classifications and limits. Earlier failing
checks drove corrections; final checks pass without disabling tests or assertions.
Existing HTTP fault fixtures still emit HTTPError cleanup ResourceWarnings.
This is not a warning-free or exhaustive vulnerability-audit claim.

Multi-hour tests advance clocks deterministically while using actual SQLite,
Core/World/Presence/Workers and verified local execution. They are not a real-day
soak. A separate real process was killed after an actual file mutation; restart
and explicit retry preserved the original action/dedup identity and file timestamp
without another executor invocation. Actual local file/HTTP/browser/credential
execution is distinct from injected faults, phone/model fixtures and JVM overlay
contracts. No owner provider, physical capture, OEM or production PASS is claimed.

## Performance

Baseline is reviewed head `d2e686c7d8c2f67dea13d1551d52b5759831d279`, measured
with this same script and environment. Four repetitions, alternating revision
order, fresh processes and three warm-ups per operation. Normal mode includes
an authorized actual local Grid source and background services; quiet mode stops
those services. SQL trace instrumentation is identical; tracemalloc is disabled.
The older 13.70 -> 18.85ms arithmetic receipt remains historical and used different
instrumentation, so it is not directly compared to these absolute timings.

Reproduce: `python -m scripts.benchmark_group03_closure --repeats 4`.
[Raw measurements, profiles and resource samples](closure-benchmark.json).

| Mode / operation | Baseline p50 / p95 ms | Closure p50 / p95 ms | Samples / errors |
|---|---:|---:|---:|
| normal: arithmetic | 15.706 / 22.928 | 11.749 / 17.980 | 160 / 0 |
| normal: file | 23.704 / 30.557 | 22.204 / 30.197 | 160 / 0 |
| normal: loopback_http | 97.693 / 126.052 | 97.366 / 121.336 | 160 / 0 |
| normal: reviewed_executive_goal | 25.579 / 33.295 | 17.750 / 23.710 | 160 / 0 |
| normal: presence_unchanged | 1.601 / 3.307 | 0.025 / 0.042 | 800 / 0 |
| normal: presence_eight_subscribers | 15.045 / 24.552 | 0.037 / 1.383 | 800 / 0 |
| normal: presence_transition_projection | 1.568 / 2.958 | 0.535 / 0.853 | 40 / 0 |
| quiet: arithmetic | 12.182 / 15.388 | 11.251 / 17.068 | 160 / 0 |
| quiet: file | 21.414 / 33.157 | 20.930 / 28.325 | 160 / 0 |
| quiet: loopback_http | 94.802 / 124.967 | 97.425 / 129.284 | 160 / 0 |
| quiet: reviewed_executive_goal | 18.907 / 26.757 | 17.410 / 23.613 | 160 / 0 |
| quiet: presence_unchanged | 1.617 / 3.251 | 0.039 / 0.139 | 800 / 0 |
| quiet: presence_eight_subscribers | 15.224 / 27.771 | 0.062 / 2.000 | 800 / 0 |
| quiet: presence_transition_projection | 1.903 / 4.332 | 0.563 / 0.986 | 40 / 0 |

| Revision / mode | Cold startup / first task ms | Common CPU s | Common SQL writes | Warm RSS / final peak working set MiB | Idle writes per 3s sample | Writes per 200 unchanged Presence reads |
|---|---:|---:|---:|---:|---|---|
| baseline normal | 296.27 / 16.00 | 4.3906 | 5162.5 | 117.69 / 118.88 | 9, 9, 9, 9 | 200, 200, 200, 200 |
| baseline quiet | 286.13 / 11.62 | 4.1641 | 4472 | 117.63 / 118.84 | 0, 0, 0, 0 | 200, 200, 200, 200 |
| candidate normal | 288.01 / 13.18 | 4.2578 | 4347 | 117.84 / 118.90 | 0, 0, 0, 0 | 0, 0, 0, 0 |
| candidate quiet | 290.67 / 10.65 | 4.1250 | 4343 | 117.46 / 118.51 | 0, 0, 0, 0 | 0, 0, 0, 0 |

Initial profiling exposed repeated World runner writes and historical lease JSON
deserialization. The correction preserves authorization, independent verification,
canonical evidence and idempotency. SQLite query plans confirm indexed active-task
and live-lease searches. Presence now performs zero writes in each measured batch
of 200 unchanged reads; reserving each next block of 1,024 publications still
requires a durable write. Meaningful transitions persist immediately.

Cold samples are Harness construction and the first task, not an OS cache flush.
RSS is the actual process working set including imports/runtime, excluding executor child processes; peak is Windows
peak working set, not total machine memory or retained application allocation.
SQL write counts are traced Core Store statements, not physical WAL/page writes.
CPU counters and the short three-second idle samples are coarse. Laptop caches/load/thermal
state remain uncontrolled. Compare p95 and quiet-mode variations as well as p50;
no general speed parity, zero idle cost, battery or leak-free day-long soak is
claimed. These are deterministic local operations, with no inference/provider or
physical-device performance claim.


## Measurement variance and full-cadence idle

The [initial two-repeat run](closure-benchmark-initial.json) is preserved. Its
pooled normal arithmetic median regressed 15.949 -> 23.360ms, while its paired
per-repeat medians improved (45.081 -> 36.141 and 13.608 -> 11.232ms). Profiles
showed large variation in SQLite time for essentially the same statement counts.
That suggests storage/load interference, without proving its external cause.
The four-repeat confirmation above isolates baseline extraction to runtime/config
and retains all confirmation samples. Quiet-mode HTTP and arithmetic p95 still
regress in the confirmation; the table reports them instead of claiming universal gains.

A separate [35-second idle measurement](closure-idle-benchmark.json) covers the
10-second session, 20-second World runner and 30-second maintenance cadences with
the same authorized local Grid source. One sample per revision, no device or
model calls. Reproduce with `python -m scripts.benchmark_group03_closure --iterations
10 --repeats 1 --idle-seconds 35 --mode normal --output
docs/evidence/group03/closure-idle-benchmark.json` (one command).

| Revision | Idle wall s | CPU s | Core Store SQL writes | RSS MiB |
|---|---:|---:|---:|---:|
| baseline | 35.000 | 0.1406 | 127 | 50.02 |
| candidate | 35.001 | 0.1094 | 28 | 48.64 |

These longer samples still do not establish day-long power, memory-leak or production acceptance.

## Delivery, remaining acceptance and recommendation

The owner subsequently authorized repository Actions and genuine CI integration.
The [Actions integration record](ACTIONS-INTEGRATION.md) records settings,
trigger and corrections from the first actual runs. The separate Code Review
connector remains unavailable; this later authorization permits authenticated
GitHub CLI/API diagnostics. PR #7 records terminal final-head job results and the
integration decision. No queued/skipped job or empty checks response implies PASS.

Software is ready for owner merge review after final-head CI is verified or
explicitly waived and the listed deferrals are accepted. **Do not merge
automatically.** Gate C and Gate D remain PARTIAL.

Internal tokens remain finite (one hour); renewal needs current live authority
within the seven-day enrollment, and expired/revoked authority or long downtime
requires explicit local reenrollment. Old tokens cannot create new actions and
cannot outlive their original expiry. Cancellation is cooperative; ambiguous
external effects require independent inspection. Android service/permission/lock/
network/notification/OEM, physical audio/biometric/Edge, live environmental/provider
and production acceptance remain pending. Native schedule authoring/widgets and
standing Full Access remain unavailable. No Group 4 or Codex Cloud.

See [closure handoff](../../development/GROUP-03-ENGINEERING-CLOSURE.md),
[run history](../../development/GROUP-03-GATE-D.md) and
[preserved 2026-10-16 report](GATE-D-REPORT-2026-10-16.md).
