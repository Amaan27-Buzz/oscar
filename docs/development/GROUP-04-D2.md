# Group 4/D2 + Group 5/D3–D4 — connected software integration

The owner authorized this software integration on 2026-10-18 after merged D1
[PR #8](https://github.com/Amaan27-Buzz/oscar/pull/8). Delivery is a focused draft
PR, with no automatic merge. The [D1 ledger](GROUP-04-D1.md) remains historical
evidence. Canonical slices 00–20, Gate C/D PARTIAL and Gate E NOT PASSED remain.

## Architecture and dependency audit

| Boundary | Existing implementation to extend | Constraint |
| --- | --- | --- |
| Persistent Core | `CloudCore` composes `Harness`, Controller, Grid, Policy, Runtime, Executive and Router | One process-lifetime canonical writer; no second Core or scheduler |
| Authority and recovery | Grid scoped sessions, replay nonces, durable leases and Store task state | Device identity is distinct from a bearer credential; target checks remain independent |
| Canonical history | Event Archive SQLite WAL/FULL/FTS5 and existing Memory Fabric | Native caches are projections; model and semantic-index absence stay explicit |
| TLS ingress | Existing bounded `CloudHTTPServer` and digest-pinned Caddy | Expose only named versioned interfaces; keep privileged reference routes private |
| Windows execution | Existing machine/files/Git/PowerShell/UIA/browser contracts and native CNG signing | A Linux Core cannot advertise Windows capabilities; no arbitrary remote shell |
| Native clients | Existing Tauri Rust IPC and Android Kotlin/Compose, Keystore and owner-confirmation foundations | Preserve approved native UI and the Orb; UI state grants no authority |
| Deployment acceptance | Existing Docker Core/Caddy trusted-local-CA harness | Nonroot, read-only, bounded containers; no public host ports or provisioning |

The D1 diagnostic-client command grants diagnostics only; it is not owner-device
enrollment. The existing reference listeners bind loopback and must not be
forwarded to the Internet. The new transport extends these authoritative
components rather than introducing another database, broker or relationship store.

## Evidence boundaries

Receipts below identify the exercised source/environment. The last published
source is [676a0b16cb3be46f151ec9b998a79c2c503c134e](https://github.com/Amaan27-Buzz/oscar/commit/676a0b16cb3be46f151ec9b998a79c2c503c134e).
The owner stopped GitHub Actions after quota exhaustion and directed the remaining
work to stay local. Running Windows, Desktop and Android emulator checks were
cancelled; completed checks below remain valid for their named source. Subsequent
local Core/native clock handling, harness corrections and this evidence update
are unpublished. No additional
CI run or push is part of this continuation. A running socket, executor report,
build, earlier-head CI result or emulator result cannot establish a stronger
acceptance class.

| Environment / acceptance | Status |
| --- | --- |
| Local Python 3.12 regression | SOFTWARE_VERIFIED in the local continuation after `676a0b1`: suite of 772 tests reported OK in 240.396 seconds: 757 executed passes and 15 explicit optional-platform/dependency skips; receipt `.oscar/d2-regression-final-772.log`; includes the Core Presence observation and seven Android host-harness tests |
| Current D2 unit and protocol tests | SOFTWARE_VERIFIED: latest 25 Core tests passed in 12.922 seconds; 15 existing Presence/Worker tests passed; included in the completed local regression |
| Separate Core / Worker / client process acceptance | SOFTWARE_VERIFIED: latest two actual trusted-CA TLS process tests passed on Windows in 24.927 seconds |
| Windows Worker actual scoped file read/write and independent readback | SOFTWARE_VERIFIED: actual disposable files, synthetic scoped signed approval and independent readback; unknown mutation is not replayed |
| Linux x86_64 constrained-container Core and actual private TLS | CI_VERIFIED at `676a0b1`: 81 tests passed in 52.709 seconds on actual x86_64, UID 10001/read-only/one CPU/1 GiB; packaged Caddy Grid TLS and restart readback passed ([job](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957564/job/117797805716)) |
| Native Linux ARM64 runtime and private TLS | CI_VERIFIED at `676a0b1`: 81 tests passed in 57.962 seconds on actual aarch64, same constraints; packaged Caddy Grid TLS and restart readback passed ([job](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957564/job/117797806017)); no QEMU claim |
| Native Windows CNG / DPAPI process interoperability | SOFTWARE_VERIFIED: actual native key enrollment, signing, protected session reopen, production Worker, read/write/readback, canonical history and same Core Presence source/transition/generation/expiry inspection; latest native fixture passed |
| Tauri/Rust and TypeScript checks | SOFTWARE_VERIFIED: Rust 23 tests, exact all-target Clippy/rustfmt, Vite build/typecheck and 93 frontend tests passed, including native authenticated clock observation and unchanged canonical Presence rendering with skew/expiry; remaining `676a0b1` Desktop CI cancelled at the owner's direction |
| Android compile, JVM and lint | SOFTWARE_VERIFIED: 48 JVM tests (42 app + six expression), zero failures/errors/skips; lint, debug APK and instrumentation APK passed. Final build receipt `.oscar/d2-mobile-final.log` (16 seconds). `676a0b1` [Android reference build](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957565/job/117797805672) also passed |
| Disposable Android emulator / Keystore / recreation | EMULATED: all five actual API 35 stages passed on explicitly identified `emulator-5590` / `oscar_d2_disposable_local_20261019`: native Keystore proof; live trusted-CA HTTPS enrollment, canonical Presence/history, actual Worker read and Activity recreation; process-death restoration; Core-loss private withdrawal; revoke/logout with exact Keystore/cache removal and independent authenticated Core revoked/offline readback. Receipt `.oscar/d2-android-final.log`; general instrumentation regression recorded separately below |
| General Android instrumentation | EMULATED: final Gradle run succeeded in 3 minutes 50 seconds; app JUnit XML records 46 cases, zero failures/errors and 12 prerequisite skips; expression XML records four cases, zero failures/errors/skips, including actual supplied-clock render/expiry. Receipt `.oscar/d2-android-instrumentation-complete.log`. Skips comprise four external Grid stages (separately passed above), four legacy reference-fixture cases, one explicit loopback fixture, two process-prepare cases and one system-animation prerequisite; none establishes a PASS by itself |
| Canonical network Presence | SOFTWARE_VERIFIED / EMULATED: unchanged canonical source, transition, generation and expiry cross the scoped/Policy-checked snapshot and signed operation. Actual Windows and Android fixtures validate the projection. Authenticated observation plus monotonic elapsed/transport age handles device-clock skew while preserving strict 250 ms future validation and original expiry |
| Privacy-safe failure diagnostics | SOFTWARE_VERIFIED: fixed categories, capped volatile counters and per-category log suppression; Cloud/admission/diagnostics 13 tests passed in 12.789 seconds, including no unauthenticated canonical writes or private content in logs |
| General provider-backed natural-language generation | NOT_VERIFIED; no owner credentials commissioned |
| Independent hosted Internet topology / Oracle | NOT_RUN; not provisioned |
| Owner physical phone / biometrics / hardware-backed keys / OEM | NOT_RUN; prohibited in this run |
| Full PC control, Secure / Full Access, real audio, physical Edge | NOT_RUN; outside this bounded integration |

The completed [native Linux run](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957564)
records exact source `676a0b1`. Observed Caddy snapshots were Core 30.51 MiB /
ingress 18.32 MiB on x86_64 and Core 29.71 MiB / ingress 13.8 MiB on ARM64. These
are bounded observed samples, not a sustained-production capacity claim.
The same source's [Ubuntu Brain job](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957575/job/117797806441)
and [Mobile Core boundary job](https://github.com/Amaan27-Buzz/oscar/actions/runs/39168957565/job/117797805773)
completed successfully. The remaining Windows Brain, Desktop and Android emulator
jobs were intentionally cancelled; overall CI is PARTIAL, not green. Earlier
generic Android instrumentation passed with 11 explicit prerequisite skips;
that receipt does not establish the connected Core fixture.

Historical [first-candidate native Linux CI](https://github.com/Amaan27-Buzz/oscar/actions/runs/39143491095)
at `ed38df1` passed 77 tests per architecture in 63.087 seconds (x86_64) and
56.780 seconds (aarch64), with Core/ingress memory samples of 29.52/16.55 MiB and
30.07/13.13 MiB respectively. Earlier local Linux acceptance passed 46 tests in
72.276 seconds and the private Caddy fixture passed. The latest 81-test native
run above is the current Linux receipt. The full local Python suite's 15 skips
cover three POSIX-permission cases on Windows, nine optional voice/numeric/reference
cases and three optional Playwright cases; they are not counted as executed passes.
The earlier `676a0b1` local regression reported 765 tests OK in 235.763 seconds
(750 executed passes, 15 skips; `.oscar/d2-regression-676a0b1.log`). The final local
772-test receipt includes subsequent unpublished Core/fixture changes; CI at
`676a0b1` does not cover those changes.

## Reproduce process and native verification

```sh
python -m pip install '.[dev,mobile]'
python -m scripts.verify_connected_grid
python -m scripts.verify_desktop_grid
docker build --target runtime -f deploy/cloud/Dockerfile -t oscar-cloud:local .
docker build --target acceptance -f deploy/cloud/Dockerfile -t oscar-cloud-acceptance:local .
docker build --target ingress -f deploy/cloud/Dockerfile -t oscar-cloud-ingress:local .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 --memory 1g --cpus 1 --tmpfs /tmp:rw,size=128m,mode=1777 oscar-cloud-acceptance:local
python -m scripts.verify_cloud_ingress --core-image oscar-cloud:local --ingress-image oscar-cloud-ingress:local
```

The native script requires the actual debug Tauri executable built by the existing
Desktop checks. It runs CNG transport and separate owner signing, DPAPI session
reopen, the production Windows Worker connection path and scoped filesystem
execution over a trusted test CA. Keys and state are generated only for the
fixture. Native signing in this fixture is software/reference confirmation;
Windows Hello owner-biometric acceptance remains NOT_RUN.

The general process suite launches independent actual Core and Worker processes.
The Core test bootstrap wraps the real bounded HTTP server socket in TLS; this
test-only injection leaves production configuration unchanged. A separate actual
Caddy/Core container harness tests the packaged TLS boundary with no published
ports. Neither topology is an independent Internet host.

The crash test terminates the Worker after its real mutation, before result
delivery. Restart blocks the ambiguous canonical task. An independently changed
file marker survives Worker restart and a subsequent actual read, proving the old
mutation was not silently replayed. Exact Windows test-process trees are stopped
because a virtual-environment launcher can own a child interpreter holding state.

For an explicitly identified disposable Android emulator with both debug APKs
installed, run `python -m scripts.verify_android_grid --serial emulator-5590
--adb ABSOLUTE_ADB_PATH`. The script checks the ADB inventory, emulator property
and AVD identity before any app operation. It exports only the emulator's public
Keystore identity, creates a trusted offline invitation, starts the actual TLS
Core and independent Worker, and reverses exactly the fixture port. It checks
native enrollment, actual Worker read/evidence, recreation, process restoration,
Core loss, revoke and key/cache deletion. Missing prerequisites, assumptions,
skips and zero-test instrumentation fail acceptance. Assertion receipts are kept
privately under ignored `.oscar/d2-android/`; credentials are not printed.

## Security and failure review

The assertions below map to actual test names and implementations. They describe
the exercised software boundary, not independent penetration-test certification.

| Boundary | Evidence / conclusion |
| --- | --- |
| Enrollment trust | `test_enrollment_proof_single_use_and_role_binding` and expiry tests reject wrong keys, replay, role substitution and expired invitations |
| Signed requests | `test_request_proof_replay_and_changed_body` binds exact request bytes; invalid proofs do not consume valid-device admission in the HTTP test |
| Device/session lifetime | Rotation/revocation/recovery, rollback-on-rotation-failure and restore tests fence old sessions; trusted recovery is explicit |
| Target authority | Core and Worker tests reject wrong target/session/workspace/capability/digest/deadline, withdrawn capability and local-policy denial |
| Ask approval | Expired/revoked requester, changed action and changed generation tests reject stale or substituted signed review; approval is not standing authority |
| Cancellation | Cancelled/wrong-node deliveries cannot execute; checks immediately before replacement preserve the original file after revocation |
| Independent verification | Actual filesystem readback detects changed results; native and process fixtures verify both read-only and approved reversible operations |
| Replay / crash | Duplicate submission/delivery is idempotent; durable execution claims and separate-process crash/restart preserve an independently changed file marker |
| Canonical history / privacy | Cross-client cursor resume, no-archive-grant redaction, forgotten-source generation reset, readable result provenance and oversized-event cursor tests preserve one archive |
| Canonical Presence | Existing source, transition ID, generation and expiry pass through; live `presence:read` and Personal Policy are separate from archive/retention/action scopes; native renderers validate freshness and withdraw missing state |
| Failure diagnostics | Fixed category/count logs suppress repeats for 60 seconds; counters saturate and use bounded keys; malformed pressure leaves canonical records/audit/nonces and verified admission unchanged |
| Runtime boundary | Exact routes, bounded bodies/responses/concurrency, protocol mismatch and unconfigured-production rejection remain fail closed; no inbound Worker listener |

No unresolved vulnerability is asserted fixed merely by a successful connection.
CI is partial after the owner's stop; local receipts retain their own evidence
class. Production owner trust, Internet reachability,
physical key backing and biometric/OEM behavior remain unverified external
acceptance. The only connected executable capabilities are bounded file reads and
Ask-approved writes; arbitrary shell, general computer control and standing
Secure/Full Access remain unavailable.

The disposable emulator was shut down and the final ADB inventory is empty; no
physical device was targeted. Automatic approval review rejected removal of the
new task AVD directory with `blocked by policy`. Its approximately 4.21 GB of
synthetic emulator state remains ignored at `.oscar/d2-local-avd-20261019/`.
The pre-existing API 35 image and prior AVDs were preserved. Test receipts remain
under ignored `.oscar/`; no fixture credentials or recordings are committed.

Initial candidate CI exposed a concurrent result-retention/snapshot repair race,
a strict Rust Windows-size cast lint failure, and Android's platform-specific RSA
PSS algorithm naming mismatch. The source corrections are implemented and local
checks above passed; these failures remain part of the receipt. Final-source
Linux CI completed, remaining platform CI was cancelled at the owner's direction,
and actual Android interoperability subsequently passed locally.
Authenticated references to unavailable objects fail as authorization denial
rather than exposing internal key errors.

Local Android acceptance also exposed three concrete fixture/client issues. The
launcher now reinstalls both APKs after Gradle's connected-test teardown. A real
host/emulator clock offset exceeded the canonical 250 ms future tolerance;
authenticated observation timestamps and monotonic clocks now preserve the
unchanged event's lifetime on both native clients. The revoke assertion now waits
for completed credential/key removal, rather than racing the earlier preference
clear. All five connected stages then passed, including independent Core readback
of the revoked, offline device. Seven host tests reject false acceptance and
preserve explicit emulator targeting and redacted failure diagnostics.

The broader native run initially caught a large-text IME test timing failure;
the unchanged case passed in isolation. Fixture setup now awaits completed local
credential removal and an actually visible keyboard before typing. The new
renderer test awaits observable expired state instead of assuming a fixed sleep
has also completed the UI update, and still checks the event did not expire
early. Text, layout, lifecycle and exact expiry assertions remain. The complete
app and expression instrumentation rerun then passed with the explicit skips
listed above.

Required Ruff checks and formatting for `oscar tests scripts` passed across 199 files; an extra repository-wide audit reported 60 pre-existing style errors and two formatting failures in unchanged `design/expression-lab/tools/capture.py` and `capture-engine.py`, outside the required runtime/CI scope, and those files were left unchanged.

## Final engineering report

1. **Starting main:** `36c3883377cc0e29b25e095bf53caa6a09f902ae` (merged D1 PR #8). Last published source is `676a0b16cb3be46f151ec9b998a79c2c503c134e`; local continuation changes are unpublished. The [PR commit log](https://github.com/Amaan27-Buzz/oscar/pull/9/commits) and linked receipts identify the exercised source.
2. **Branch / draft:** `codex/group-04-d2-connected-grid`; [draft PR #9](https://github.com/Amaan27-Buzz/oscar/pull/9), initially published at `ed38df1`, last pushed at `676a0b1`. No automatic merge or further push; remaining work stays local at the owner's direction.
3. **Reuse:** existing `CloudCore` composition, Grid, Store, Runtime, Controller, Policy and Event Archive remain authoritative. New components adapt authenticated remote transport and native projections; no second Core/archive/scheduler.
4. **Transport:** [Grid protocol 2](GROUP-04-D2-PROTOCOL.md), exact HTTPS POST endpoints, bounded outbound polling, durable IDs/cursors and authenticated target checks. Windows/Android need no inbound port.
5. **Enrollment:** trusted offline short-lived single-use invitations, device proof of possession, role/workspace/scopes, independent owner key, expiry, rotation, revocation and recovery fences.
6. **Windows Worker:** actual native CNG signing and DPAPI connection reopen; production outbound Worker advertises only scoped file read/write. Existing other typed Windows tools remain local.
7. **Android:** existing approved Compose surfaces, native Keystore proof, encrypted state, canonical cursor synchronization and separate exact owner-review binding. Emulator results are recorded separately above.
8. **Execution:** actual separate-process read and approved file mutation, durable task/result and independent network/host readback; native Windows acceptance uses its production credential path.
9. **Conversation / memory:** same Core relationship and ordered canonical source/result events observed by clients; reconnect/cursor deduplication, retention redaction and forget-generation replacement tested.
10. **Presence / task state:** current node/task views and the existing canonical Presence contract cross the authenticated boundary. Presence has separate scope/Policy checks and retains Core source, transition, generation and expiry; actual native Windows and Android validate this same projection. Authenticated clock observations and monotonic elapsed time preserve expiry across device-clock skew. Leased liveness and verified/blocked/unknown task states come from Core; caches grant no authority.
11. **Approval / cancel / revoke:** exact action/session/target/generation/digest review, expiry and current policy rechecks; cancellation and revocation stop future dispatch but cannot undo an already performed effect.
12. **Recovery:** actual Worker crash after effect, before delivery, followed by Core/Worker restart blocks ambiguity and preserves the independently changed marker; no automatic mutation replay.
13. **Linux / ARM64:** actual native x86_64 and aarch64 jobs each passed 81 tests and packaged Caddy TLS/restart acceptance at `676a0b1`, in 52.709 and 57.962 seconds respectively; exact jobs and observed memory above.
14. **Windows native:** CNG/DPAPI real-process HTTPS and latest canonical Presence/clock fixture passed; Rust 23, frontend 93, build/typecheck/Clippy/rustfmt passed locally. Authenticated Core time is anchored to local monotonic elapsed time without changing canonical events; original expiry and strict future tolerance remain enforced. The remaining final-source Windows CI was intentionally cancelled. Synthetic native signing is not owner biometric acceptance.
15. **Android verification:** 48 JVM tests (42 app + six expression), lint and both APKs passed locally; the published Android build and Core boundary CI passed for `676a0b1`. Seven host tests cover emulator guards, installation, sanitized diagnostics, skip rejection and independent revocation verification. All five actual emulator/Core/Worker stages passed with no skips. General app XML records 46 cases with 12 explicit prerequisite skips and zero failures; expression XML records four cases with no skips/failures. Hardware/OEM and owner-phone tests are forbidden in this run.
16. **CI and local closure:** `676a0b1` native Linux x86_64/ARM64, Ubuntu Brain, Android build and Mobile Core boundary jobs passed. The owner stopped Actions after quota exhaustion; running Windows Brain, Desktop and Android emulator jobs were cancelled and are not required to rerun in this local continuation. Overall CI remains PARTIAL. The final local Python suite reported 772 tests OK in 240.396 seconds: 757 executed passes and 15 explicit skips. Linked CI receipts do not cover unpublished local changes.
17. **Defects / limits:** initial Windows/Python/Android failures and source corrections are preserved above; final Windows CI remains incomplete by owner direction, while actual local Windows and Android interoperability passed. Independent production security assessment, real owner trust and Internet topology are unverified. No general provider inference is claimed without a configured provider; unavailable routes remain blocked. The external commissioning boundary is unchanged.
18. **Oracle boundary:** no account/VM credentials, provisioning, public ingress, DNS or independent hosted topology was commissioned. Isolated containers establish software compatibility only.
19. **Physical Android boundary:** owner phone was not accessed, paired, installed, enrolled or used for biometrics/data. Emulator software acceptance cannot replace owner/device acceptance.
20. **Next commissioning:** review/merge separately; authorize hosted installation, restore-safe one-writer commissioning, trusted owner/device enrollment and independent-network verification, then execute the later physical checklist below. Full Group 5 and formal Gates C/D/E remain open.

## Later owner-device acceptance checklist — do not execute in this run

After separately authorized hosted commissioning, verify the actual TLS endpoint
from an independent network, explicit owner enrollment, reviewed device scopes,
same relationship/task/history on Windows and the physical Android phone, local
credential storage and logout, process recreation, missed-event catch-up,
foreground/background and OEM behavior, exact signed approval and independent
readback, cancellation/revocation/expiry and no replay after unknown mutation.
Exercise real biometrics and hardware-backed key claims only on the authorized
device. Capture separate owner and physical receipts without private credentials.

Before phone acceptance, preserve a tested backup and confirm one canonical
writer. Never run the original and a restored Core volume concurrently. Verify
that stale/restored device sessions cannot regain revoked authority.
