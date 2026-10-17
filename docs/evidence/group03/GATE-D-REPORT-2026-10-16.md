# Gate D integrated software report - 2026-10-16

**Gate D: PARTIAL. Gate C: PARTIAL.** Canonical Slices 14-17 now have integrated,
locally verified software. Owner/live/device/production acceptance remains open.
Branch `codex/group-03-gate-d`; [draft PR7](https://github.com/Amaan27-Buzz/oscar/pull/7) remains unmerged.
Implementation commit: `c23dc4a64e45311104d7ba0798f20f4a763ffd9b`. Later evidence-only commits can advance the PR.

| Slice | Implemented and locally verified | Remaining |
|---|---|---|
| 14 | Normal Core/Controller, authorized bounded source lifecycle, quiet Sentry and canonical retention | Owner environmental enrollment, capture/delivery and production acceptance |
| 15 | Resumable setup, identity/pairing, provider/native Vault, Persona/preferences/policy/logical voice | Owner providers, physical pairing, Voice Match/Map and audio calibration |
| 16 | Shared leased Presence, validated typed AIE/native renderers, opt-in Android overlay | Device/OEM/visual/power/accessibility acceptance; home widgets unavailable |
| 17 | Reviewed bounded DAG/Worker execution, schedules, recovery, context gates, replanning and verified workflow reuse | Native authoring unavailable; owner/live-model/environment/production acceptance |

## Verification

- Final Python regression: **665 passed, 6 skipped, 0 failed** (671 ran, 159.648s).
- Final Grid/Executive/cross-slice focused rerun: 44 passed, 0 failed.
- Desktop: 85 frontend tests, TypeScript/Vite build, Rust format/Clippy and 16 Rust tests passed; Windows debug executable built.
- Android: 30 JVM tests passed; debug and instrumentation APK assembly and lint passed. No emulator/device execution. Existing old instrumentation results were not counted.
- Ruff lint/format (175 files), strict mypy (74 modules), repository/link/secret checks and diff checks passed.
- Git integrity passed; existing dangling recoverable objects were preserved. Installed Desktop/expression npm audit reported no vulnerabilities.
- Remote exact-head CI is **UNKNOWN**: Code Review connector denied workspace GitHub access. No CI PASS or diagnostic CLI fallback is claimed.

The [continuation receipt](verification-continuation.json) lists exact skips,
commands, local log hashes, artifact hashes, warnings and security/failure coverage.
The six skips are optional local/prepared voice executor checks, outside the
authorized no-audio/model-preparation run. Existing Python HTTP fault fixtures
emitted ResourceWarnings for HTTPError cleanup; no tests failed.

## Runtime evidence

Real execution includes disposable SQLite/WAL and one canonical Event Archive,
exact file writes/readback, arithmetic, authenticated loopback HTTP, separate
Core/Worker processes and restart. The cross-slice test composes real identity,
setup, local Grid/task perception, scoped surface reads, Presence/AIE, a reviewed
file/math DAG, revocation and durable restart with no duplicate work.

Provider fault responses, injected context, model planner JSON and phone enrollment
are labeled synthetic/reference fixtures. Headless Chromium uses local fixture
pages. Native Windows credential tests use disposable credentials; no owner account
was enrolled. No real camera, microphone, OEM feed, phone or Edge acceptance is
implied. Software tests cover stale/offline state, source revocation during
acquisition, permission changes, Worker/capability withdrawal, cancellation,
concurrent admission and ambiguous-mutation fencing.

Final review corrected pairing lost updates, stale reaper disconnects and a
disconnect/reconnect race that could block newly admitted work. These have
deterministic regression tests. Memory remains historical; fresh context and
relationship/session grants remain independently checked.

## Reproducible local measurements

Baseline `5899798a3200173547ee3493689e20222fe3d1b1` versus implementation above, Python 3.14.2,
3 warm-ups and 30 samples per operation. Timings include real local task creation,
execution and independent verification. Run `python -m scripts.benchmark_group03`.
The [raw report](end-to-end-benchmark.json) records source hashes and both p95s.

| Operation | Baseline median ms | Candidate median ms | Candidate p95 ms |
|---|---:|---:|---:|
| arithmetic_local | 13.702 | 18.854 | 21.018 |
| file_local | 32.488 | 27.378 | 31.635 |
| arithmetic_loopback_http | 93.473 | 90.297 | 95.61 |
| presence_and_typed_view | Unavailable | 2.888 | 4.196 |
| reviewed_executive_goal | Unavailable | 33.864 | 44.582 |

Common-workload CPU: 3.344 -> 3.328 seconds;
peak traced Python allocation: 2,702,946 -> 2,318,527 bytes.
Candidate idle CPU: 0.0 seconds over 2.1 seconds.
Local arithmetic shows added task-path overhead; other timing variations are not
evidence of a general speed improvement. New Presence/Executive operations have no prior
implementation comparison. CPU includes common workload/startup; candidate-only
operations have separate totals in the raw report. Imports precede tracemalloc.
Process order, warm caches and concurrent laptop load are uncontrolled. Allocation
is not total RSS or battery; this is not a device/inference/production benchmark.
The short idle sample and coarse CPU counter cannot establish sustained idle or
power consumption.

## Open acceptance and product limits

- Gate C and Gate D remain PARTIAL; owner/device/live/production acceptance is separate.
- Native schedule creation/editing and home widgets remain unavailable; trusted-local reviewed CLI is the working Executive control path.
- No live model inference, owner provider enrollment, physical camera/audio/Edge or phone/emulator execution in this continuation.
- Cooperative cancellation cannot undo an indivisible external action; ambiguous mutations require inspection.
- Local interval scheduling runs only while this Core is running; no hosted service or laptop wake was installed.
- Benchmark is instrumented local latency and Python allocations, not RSS, battery, device, inference or production performance.

Owner acceptance still requires genuine source/provider enrollment, physical
pairing, Android overlay permissions and show/hide/dismiss/disable behavior, OEM
foreground/background/power/accessibility checks, approved-surface visual review,
Voice Match/Map/audio/biometric and physical Edge checks. No new OS grants or owner
credentials were created. Gate D cannot PASS from these software checks alone.
Native schedule authoring is a software product limitation; trusted-local reviewed
CLI operations work today. See [Executive workflow](../../EXECUTIVE-RUNTIME.md)
and [run history](../../development/GROUP-03-GATE-D.md). No merge or Group 4.
