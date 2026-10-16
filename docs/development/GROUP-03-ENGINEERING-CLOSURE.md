# Group 3 engineering closure - 2026-10-17

This is a corrective review of the integrated Slices 14-17 candidate, starting
from fetched `d2e686c7d8c2f67dea13d1551d52b5759831d279` on existing draft PR7.
Main and merged PR6 are `257349f82a96293c3737d446dca18ce46f098b04`.
The working tree was clean. No replacement PR, merge, release or Group 4.

## Findings and corrections

| Area | Fix | Verification | Remaining |
|---|---|---|---|
| Internal execution sessions | Independent Core maintenance; live scoped token rotation before one-hour expiry; seven-day enrollment ceiling; revocation/expiry require explicit new enrollment | Real SQLite and deterministic 1/2/8/24-hour execution; old-token and concurrent-rotation denial; real restart and crash-after-mutation tests | Long sleep/expired enrollment requires explicit local reenrollment; no remote/session authority is renewed automatically |
| Presence polling | Separate persisted state generation, publication sequence and transition identity; reserve 1,024 publications; indexed active-state reads; consistent read transactions | Concurrent unique publications, unchanged read write-count assertions, restart fencing and TS/Kotlin renderer freshness/replay tests | Owner/device visual/power acceptance; rare generation reservations still write |
| Android Companion | Attach only after local permissions/opt-in/unlock/pairing and fresh authorized canonical Presence; request fencing, expiry watchdog, notification dismissal and cleanup | Native build/lint/JVM admission/request tests; existing CoreClient transport tests | No connected device; real foreground-service, network, lock, notification, permission and OEM acceptance deferred |
| Performance | Reduce World lease rewrites and duplicate heartbeat writes; indexed live-lease lookup; preserve all action/verification/dedup checks | Reproducible alternating baseline/candidate normal/quiet processes, SQL write counts, p50/p95, CPU and Windows working set | Instrumented laptop results; no inference, production, battery or device parity |
| Cross-slice integration | Fence task state before releasing expired leases; contain unexpected executor exceptions as ambiguous outcomes; release reservations | Full regression plus multi-hour Core/World/Presence/Worker tests, exact file readback, revoked sources, process kill/restart and no repeated mutation | Cooperative external cancellation; ambiguous mutations need inspection |

The existing Desktop resize-failure recovery test exposed a timing race: the
failure message could appear before the retreat flag reset. Both are now updated
together, without changing visual design or weakening the test.

## Authority and compatibility

Only the trusted local Core enrolls renewable internal execution sessions. Mobile
and other ordinary Grid sessions keep their existing finite, nonrenewable policy.
Each internal token lasts at most one hour; maintenance checks every ten seconds,
and rotates when at most fifteen minutes remain. The enrollment lasts at most
seven days. Revocation and node/session scope changes remain authoritative.
Expired or revoked managed authority is not repaired by the maintenance loop.

Rotation preserves the session identity and current scopes, stores only token
digests, and updates the shared in-process handle. The old token can authenticate
only an already-active lease captured at rotation, while that lease remains live
and no later than the token's original expiry. At most 256 draining leases are
admitted; capacity failure retains the existing credential and requires capacity
to recover before its expiry. Existing canonical action/task/dedup identity owns
mutation admission across rotation. Normal trusted-local restart creates a fresh
scoped session and revokes the prior managed session; expired/revoked enrollment
requires explicit `python -m oscar serve --reenroll-execution`. Revoked nodes remain
denied. No credential is put in Worker definitions, logs or evidence.

The single Core remains authoritative. Read-only Presence polls keep increasing
the Expression publication generation and renewing a bounded lease; a stable
transition ID prevents replay. The persisted state generation changes only with
meaningful operational/preferences changes. Reserved publication ceilings fence
old publishers after restart. The version 1 Expression contract stays unchanged,
including stale-generation rejection. Native tests cover generation jumps and
freshness without a new gesture. Canonical Orb bytes and approved layouts remain
unchanged; the only existing TSX behavior correction is resize-failure recovery.

The Android foreground notification may say Connecting while acquiring Presence;
no floating window is attached until admission succeeds. A synchronized in-process
request token is not restored after process death. Cancellation/hide invalidates
late callbacks; stale starts cannot cancel a newer request. Core Presence alone
is read; no microphone, conversation, signing, execution or background-start
exemption is introduced. Actual Android service behavior still needs a device.

## Evidence and handoff

The current [Gate D report](../evidence/group03/GATE-D-REPORT.md) records final
counts, source SHA, measurements and recommendation. Machine-readable
[closure verification](../evidence/group03/closure-verification.json) and
[benchmark samples](../evidence/group03/closure-benchmark.json) retain exact
commands, classifications, artifact/log hashes and limitations. Earlier
verification and benchmark receipts are preserved. The
[2026-10-16 report](../evidence/group03/GATE-D-REPORT-2026-10-16.md) is historical.

Group 2.5B Mobile UI/UX is owner APPROVED and PR6 is merged. That does not establish
physical audio/biometric/OEM acceptance or acceptance of the newly integrated
overlay. Gate C and Gate D remain PARTIAL. Native schedule authoring/widgets,
signed standing Full Access, environmental capture/delivery, live providers and
production acceptance remain explicit separate limits. Remote CI is UNKNOWN
unless the final-head check genuinely succeeds; no CLI diagnostic fallback.
