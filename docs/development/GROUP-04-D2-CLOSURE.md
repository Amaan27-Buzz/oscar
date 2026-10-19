# D2 final local integration candidate — 2026-10-19

This is a local software closure, not a GitHub PR approval, hosted deployment or
owner-device acceptance. Ask is the only active authority mode. Slices 00–20,
Gate C/D PARTIAL and Gate E NOT PASSED are unchanged.

## 1. Local branch and source revision

`codex/group-04-d2-connected-grid` started clean at
`c6580477dd1477aabd1f3d3485de47b74a952f1f`, one unpublished commit ahead of PR #9.
The corrections and tests are committed as
`076082df91e0b46f7b8bbdd4602a16dcc298170a`. Final documentation is a subsequent
local commit with identical runtime/test sources. The final handoff records its
exact HEAD and a machine-readable ignored receipt at `.oscar/d2-closure-final.json`.

## 2. Published PR and original history

Read-only GitHub metadata confirmed [draft PR #9](https://github.com/Amaan27-Buzz/oscar/pull/9)
is OPEN at `676a0b16cb3be46f151ec9b998a79c2c503c134e`; main is
`36c3883377cc0e29b25e095bf53caa6a09f902ae`. Both remain ancestors of the local
candidate. Original branches/history were preserved; `git fsck --full --strict`
passed, with existing dangling objects retained. No reset, rewrite or cleanup.

## 3. Enrollment atomicity finding and correction

The starting implementation committed invitation consumption, node replacement
and old-session revocation before session creation and remote binding. A failed
pair or binding write could strand an enrollment and destroy valid prior authority.

A valid proof now consumes the invitation once, then existing `Grid.pair` owns
one Store transaction for node preparation, old-session fencing, new session and
device binding. Its trusted preparation callback extends the existing trusted
delivery callback; ordinary callers retain their previous behavior. SQLite WAL
and FULL synchronization remain authoritative. No new database or token store.

An authority failure rolls back all replacement changes and preserves a valid
prior identity; the invitation stays consumed. A fresh trusted invitation is
required, with explicit recovery if the node exists. A response lost after commit
leaves one complete binding; tokens are hashed at rest and cannot be fetched by
replaying the proof. Explicit recovery atomically fences those inaccessible
credentials. Missing/mismatched legacy bindings still fail independent Grid and
remote-device authentication checks.

Five new tests cover eight injected pairing/write failure combinations, ten real
`os._exit` crash points across initial/replacement enrollment, lost replies,
restart, actual SQLite commit denial, rotation/recovery concurrency and revocation
cleanup failure. They inspect durable node/session/binding records after reopening
Core, not merely raised exceptions. The 31-test enrollment/Grid focused run passed;
these tests also passed in the full Windows and Linux regressions.

## 4. Security, clock and recovery corrections

- Revocation commits node/session denial and removal of pending recovery
  invitations together, before lease/task cleanup. A cleanup crash cannot let a
  previously issued recovery proof silently restore a revoked identity.
- Store now rolls back an active transaction after a failed COMMIT, including
  SQLite errors, while avoiding an invalid rollback after SQLite already aborted.
- Successive native clock observations retain a nondecreasing Core-time floor.
  An older observation combined with a bounded wall-clock rollback cannot renew
  an expired canonical event. Desktop and Android regressions cover both skew
  directions, delayed observations, rollback, expiry and fresh recovery.
- Server timestamps and the 250 ms future tolerance remain unchanged. Transport
  age is charged against the original lease. Missing Presence/permission and
  disconnected clients withdraw state. Process restoration obtains fresh Core
  time; no elapsed-time anchor is restored from disk. The approved Orb is unchanged.

Source review covered `remote_grid`, `remote_client`, `remote_worker`, HTTP,
cloud restore, Grid/Store/Runtime/Policy/archive, native TLS/signing/storage and
owner-review binding. Device proof is separate from exact action authority.
Roles, installation/Core IDs, workspace, capabilities, requester/target sessions,
approval digest/expiry/generation, revocation and pre-effect checks remain enforced.
No transport path grants Secure/Full Access or arbitrary commands.

Exact routes, bounded JSON/request/response parsing, no redirects, normal TLS
certificate/hostname checks, durable nonces, authenticated rate admission, eight
HTTP connections, bounded execution slots/queues and jittered reconnect remain.
Proxy headers are trusted only on the isolated unpublished Core backend. Logs
remain categorical; native credentials stay CNG/DPAPI or Keystore/AES-GCM. Same-OS
account compromise and host administrator control remain outside vault isolation.
This source-backed review is not production penetration-test certification.

## 5. Canonical memory and concurrency

The earlier shared adapter lock correctly serializes result retention against
snapshot repair, preserving one deterministic canonical result event and one
derived episode. Event Archive remains canonical; derived memory/indexes can lag
after a crash and are repaired/rebuilt rather than treated as a second history.
Store and archive are separate existing databases; no cross-database atomicity
claim is made.

A further correction gives snapshot tombstones, history and retained-detail
reads one archive read transaction. A deterministic WAL interleaving test commits
forget on another connection between generation and event reads: the in-flight
response keeps one committed generation, and the next response resets/withdraws
forgotten content. Existing concurrent polling/completion, cancellation, node
loss, lease expiry, rotation, archive retention and index/recovery regressions
passed. Client caches remain projections with no authority.

## 6. Desktop software

Rust **23 passed, zero ignored**; all-target/all-feature Clippy with warnings denied
and rustfmt passed. Frontend **94 passed across 17 files**, with TypeScript and
Vite production build passing. Native transport clock bounds and React supplied
clock expiry/replay cases passed. Companion/Workspace designs were preserved.

The real Windows native fixture reopened encrypted credentials across Rust
processes, used persistent CNG signing, enrolled through trusted-CA HTTPS, and
observed canonical history, tasks and Presence. Synthetic fixture owner signing
does not establish real Windows owner-confirmation acceptance.

## 7. Android software and emulator

Gradle build/lint, debug APK and instrumentation APK passed; **49 JVM tests**
(43 app + six expression), zero failures/errors/skips. The native Core clock
floor is used by CoreSession and the separate Companion projection.

All **five connected checks passed with no skips** on explicit disposable API 35
`emulator-5590`, AVD `oscar_d2_disposable_local_20261019`: real Keystore proof,
TLS/Core/Worker readback and Activity recreation, process restoration, Core-loss
private withdrawal, and revoke/logout with independent Core revoked/offline
readback. Production certificate/hostname verification stayed enabled.

Broader instrumentation passed in **3m26s**. App XML records **46 cases: 34 passed,
12 skipped, zero failures/errors**; expression XML records **four passed, no skips**.
Large-text/visible-keyboard and native supplied-clock renderer
assertions remain meaningful. No assertions were weakened or tests newly skipped.

## 8. Actual Windows Worker evidence

Independent trusted-CA HTTPS Core and production Windows Worker processes passed
both integration tests in **27.112 seconds**. Disposable file read and exact
synthetic Ask-approved write had separate Core readback and host filesystem
inspection. Canonical task/history/Presence reached native clients. A Worker
crash after mutation, lost receipt and Core restart preserved the independently
changed marker and did not replay an uncertain write.

Focused tests reject wrong target/session/workspace, altered action/readback,
traversal and reparse/symlink escapes, revoked pre-replacement authority, local
policy denial, cancellation and duplicate delivery. The durable Worker journal
stays outside its writable workspace. Generic PC control was not added.

## 9. Linux and ARM64

The current source passed **87 tests, no skips, in 58.400 seconds** on local Linux
x86_64 Docker, UID 10001, read-only filesystem, dropped capabilities,
no-new-privileges, 128 PID limit, one CPU, 1 GiB RAM and bounded tmpfs.
Packaged Core/Caddy trusted-CA TLS, exact protocol 2 enrollment/request endpoints,
persisted task state and restart readback passed on a private network with no
published ports. Unconfigured Core startup was rejected; Caddy validation passed.
Observed fixture memory: Core 29.59 MiB / 1 GiB, ingress 14.7 MiB / 256 MiB;
these are observations, not production sizing guarantees.

**Current-head native ARM64: NOT_RERUN.** The previous genuine aarch64 CI receipt
at `676a0b1` passed 81 tests in 57.962 seconds and packaged TLS/restart checks.
That historical [ARM64 job](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957564/job/117797806017)
does not prove the new source. No Oracle or native ARM64 hardware was accessed.

## 10. Local regression receipts

All paths below are ignored local synthetic receipts, not committed credentials.
Runtime/test source is `076082d`; the final commit adds documentation only.

| Check | Result | Receipt under `.oscar/` |
| --- | --- | --- |
| Full Python 3.12 | 778 total, **763 passed / 15 skipped**, 245.551 s | `d2-closure-python.log` |
| Focused enrollment/Grid | 31 passed, 29.253 s | `d2-closure-atomic-concurrency.log` |
| Real Core/Worker processes | 2 passed, 27.112 s | `d2-closure-process.log` |
| Native Windows CNG/DPAPI/Worker | SOFTWARE_VERIFIED | `d2-closure-windows-grid.log` |
| Rust | 23 passed; Clippy/rustfmt passed | `d2-closure-rust.log` |
| Frontend | 94 passed; typecheck/build passed | `d2-closure-frontend.log` |
| Android JVM/lint/APKs | 49 passed; build successful, 1m13s | `d2-closure-mobile.log` |
| Connected emulator | 5 stages passed, no skips | `d2-closure-android.log` |
| Broader emulator | App 34 passed / 12 skipped; expression 4 passed; 3m26s | `d2-closure-instrumentation-verified.log` |
| Linux container | 87 passed, no skips | `d2-closure-linux.log` |
| Packaged private TLS/restart | verified | `d2-closure-ingress.log` |

Required Ruff checks and formatting passed for 200 Python files; strict mypy
passed for 89 source files, including the required native build/reference scripts.
Repository links/secret hygiene and final diff checks passed at finalization.

## 11. Skipped and unavailable checks

Python's 15 skips: three POSIX-permission cases on Windows (covered by the Linux
container run), nine optional voice/numeric/reference cases and three optional
Playwright cases. They are not executed passes. Android prerequisite skips retain
their individual XML reasons; separately supplied connected fixtures do not make
the general run's skipped cases executed passes.

The twelve app skips are four external connected Grid stages (separately passed
with their real fixture), four legacy reference-fixture stages, one explicit
loopback fixture, two process-death setup/cleanup stages and one system-disabled
animation prerequisite. The fifth connected acceptance stage is the real native
Keystore proof. All four expression renderer tests ran, including monotonic-clock
expiry. Gradle's progress summary counts skipped cases again; authoritative JUnit
XML is used here rather than treating the progress number as executed tests.

Historical failures remain in [the implementation ledger](GROUP-04-D2.md): API
36.1 SurfaceFlinger boot failure, Android RSA-PSS provider mismatch, native skew,
large-text keyboard timing and archive-retention concurrency. The tested API 35
AVD avoids the image failure; source/fixture corrections have matching receipts.
This run's first broader Android command failed before tests because PowerShell
split an unquoted Gradle property. The argument was quoted and the corrected
command retained its separate log; this was a launcher error, not an app failure.

## 12. Remaining issues and residuals

No unresolved critical/high software defect was found in this bounded closure.
Release blockers are final-head CI (withheld), hosted commissioning and actual
owner-device/security acceptance; local success cannot discharge them. Existing
extra repository-wide Ruff findings in unchanged expression-lab capture tools
remain outside the required `oscar tests scripts` gate (previously 60 style
findings/two format failures); this closure did not modify or rerun that scope.

The task-owned AVD directory is
`D:\TheDawnlightGroup\DawnlightLabs\oscar\.oscar\d2-local-avd-20261019`.
It held exactly 4,210,607,057 bytes before reuse. Prior automatic approval review
blocked its deletion; no removal was retried or bypassed. It is separate from
the preserved SDK, pre-existing API 35 system image and unrelated AVDs. Removal
must remain a separate allowed action after confirming no process uses it.
Final emulator shutdown/inventory and retained size are in the handoff receipt.
The emulator was explicitly stopped after verification; final ADB inventory was
empty. Retained synthetic AVD files measured 4,613,063,633 bytes after reuse.
Its owned directory is identifiable and removable when deletion is allowed and
no emulator holds it; no SDK system image is inside this deletion target.

## 13. Local commits

This run created `076082d fix(grid): make enrollment recovery atomic and fence
stale projections`, followed by a documentation/evidence-only closure commit.
The prior unpublished `c658047` remains intact. The final handoff lists both new
full SHAs and the final divergence from the published PR head.

## 14. Publication and CI

**No push, remote branch edit, workflow dispatch/rerun, new PR, merge or protection
change occurred.** PR #9 remains draft/unmerged. Earlier CI at `676a0b1` includes
Linux x86_64/ARM64, Ubuntu Brain, Android build and Mobile Core checks. Windows
Brain, Desktop and Android emulator jobs were cancelled when the owner stopped
Actions after quota exhaustion; cancellation is not PASS. Earlier failed attempts
and the later successful local receipts are distinct. **Final local head CI:
NOT_RUN / WITHHELD_BY_OWNER.**

## 15. D2 software classification

**SOFTWARE_VERIFIED_LOCAL** for authenticated protocol 2, scoped enrollment and
recovery, outbound Windows file Worker, native connected-client software,
independent readback, canonical history/Presence and tested failure/restart paths.
**PR/CI acceptance: INCOMPLETE.** Independent hosted-network acceptance remains
NOT_RUN. This is a coherent integration candidate, not full Group 5 completion.

## 16. Owner-device classification

**OWNER_DEVICE_ACCEPTANCE_NOT_RUN.** No physical phone pairing, ADB operation,
installation, biometric test, camera/microphone, notification access or personal
data was used. Emulator Keystore does not prove physical hardware backing.
Actual Windows owner confirmation and real owner/provider enrollment also remain
separate commissioning work.

## 17. Oracle commissioning readiness

The software package/runbooks are ready for a separate approved commissioning
run. Account eligibility, regional A1 availability, quotas and actual capacity
remain UNKNOWN until checked with the owner account. No account, VM, billing,
public firewall, DNS or Oracle credentials were changed here. Local Docker
evidence cannot establish Oracle operation or current free-tier availability.

## 18. Precise next milestone and local checklist

**Next: Cloud commissioning and connected-client operation**, followed directly
by Group 5 C1 broader observed computer use, C2 usable MCP/plugins/connectors,
C3 genuine signed Secure/Full Access, and C4 real voice, native Workers/automations,
Chief of Staff, Sentry and adaptive interaction. Those product requirements remain
explicit and unfinished.

Local candidate checklist:

- Review scoped diff against main; preserve approved UI and original history.
- Verify required checks, no tracked secrets/fixtures, diff hygiene and clean Git.
- Retain exact local SHAs, revision-bound receipts and unrun acceptance states.
- Leave PR #9 draft; do not push or use Actions until explicitly authorized.

When Actions is available and publication is authorized:

1. Recheck live main/PR/local references and review any new divergence. Integrate
   safely if required; do not rewrite published history or weaken protections.
2. Push this existing branch once. Existing PR workflows should supply the exact
   new-head checks; avoid unnecessary dispatches or duplicate runs.
3. Require Brain/platform checks, genuine Linux x86_64 and ARM64 containers/TLS,
   Windows native CNG/DPAPI/Worker, Desktop and Android build/emulator jobs for that
   exact SHA. Inspect skipped cases and independent execution evidence.
4. Reconcile draft description/evidence with that source and obtain separate merge
   authorization. Do not reuse old CI as new-head acceptance.

Separate commissioning run:

1. Verify owner Oracle account/Always Free eligibility, region and actual ARM64
   capacity; request approval for the concrete provisioning and network changes.
2. Provision the approved Linux instance/storage and one Core writer, hardened
   private backend, approved TLS ingress/DNS and bounded resources.
3. Establish encrypted off-host backup, then restore independently with old device
   authority fenced and no simultaneous canonical writers.
4. Bootstrap the actual owner, review fingerprints/scopes and enroll approved
   Windows Desktop; exercise real remote task/recovery over an independent network.
5. Connect a disposable Android emulator to the hosted Core where supported.
   Physical Android acceptance remains a later explicitly authorized run.
