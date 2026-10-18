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

Results below must be updated from actual final-source runs. A running socket,
executor report, build, old-head CI result or emulator result cannot establish a
stronger acceptance class.

| Environment / acceptance | Status |
| --- | --- |
| Current D2 unit and protocol tests | SOFTWARE_VERIFIED: 22 focused Core tests passed in 40.060 seconds; final-head regression/CI receipts pending |
| Separate Core / Worker / client process acceptance | SOFTWARE_VERIFIED: two actual trusted-CA TLS process tests passed on Windows in 25.632 seconds |
| Windows Worker actual scoped file read/write and independent readback | SOFTWARE_VERIFIED: actual disposable files, synthetic scoped signed approval and independent readback; unknown mutation is not replayed |
| Linux x86_64 constrained-container Core and actual private TLS | SOFTWARE_VERIFIED: 46 tests passed in 72.276 seconds under UID 10001, read-only image, one CPU / 1 GiB; Caddy trusted-CA Grid enrollment/task/restart readback passed (Core 29.56 MiB, ingress 13.51 MiB observed); final-source rerun pending |
| Native Linux ARM64 runtime and private TLS | NOT_RUN for D2; requires native runner receipt |
| Native Windows CNG / DPAPI process interoperability | SOFTWARE_VERIFIED: actual native key enrollment, signing, protected session reopen, production Worker, read/write/readback and native history inspection; see commands below |
| Tauri/Rust and TypeScript checks | Native checks tracked separately; final-source receipt pending |
| Android compile, JVM and lint | SOFTWARE_VERIFIED: 38 JVM tests, lint, debug APK and instrumentation APK passed; final-head CI pending |
| Disposable Android emulator / Keystore / recreation | NOT_RUN for D2 |
| General provider-backed natural-language generation | NOT_VERIFIED; no owner credentials commissioned |
| Independent hosted Internet topology / Oracle | NOT_RUN; not provisioned |
| Owner physical phone / biometrics / hardware-backed keys / OEM | NOT_RUN; prohibited in this run |
| Full PC control, Secure / Full Access, real audio, physical Edge | NOT_RUN; outside this bounded integration |

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
| Runtime boundary | Exact routes, bounded bodies/responses/concurrency, protocol mismatch and unconfigured-production rejection remain fail closed; no inbound Worker listener |

No unresolved vulnerability is asserted fixed merely by a successful connection.
Review still requires final-head checks. Production owner trust, Internet reachability,
physical key backing and biometric/OEM behavior remain unverified external
acceptance. The only connected executable capabilities are bounded file reads and
Ask-approved writes; arbitrary shell, general computer control and standing
Secure/Full Access remain unavailable.

## Final engineering report

1. **Starting main:** `36c3883377cc0e29b25e095bf53caa6a09f902ae` (merged D1 PR #8). Final PR head is recorded with the exact-head CI receipt after commit.
2. **Branch / draft:** `codex/group-04-d2-connected-grid`; draft PR URL pending publication by the integration owner. No automatic merge.
3. **Reuse:** existing `CloudCore` composition, Grid, Store, Runtime, Controller, Policy and Event Archive remain authoritative. New components adapt authenticated remote transport and native projections; no second Core/archive/scheduler.
4. **Transport:** [Grid protocol 2](GROUP-04-D2-PROTOCOL.md), exact HTTPS POST endpoints, bounded outbound polling, durable IDs/cursors and authenticated target checks. Windows/Android need no inbound port.
5. **Enrollment:** trusted offline short-lived single-use invitations, device proof of possession, role/workspace/scopes, independent owner key, expiry, rotation, revocation and recovery fences.
6. **Windows Worker:** actual native CNG signing and DPAPI connection reopen; production outbound Worker advertises only scoped file read/write. Existing other typed Windows tools remain local.
7. **Android:** existing approved Compose surfaces, native Keystore proof, encrypted state, canonical cursor synchronization and separate exact owner-review binding. Emulator results are recorded separately above.
8. **Execution:** actual separate-process read and approved file mutation, durable task/result and independent network/host readback; native Windows acceptance uses its production credential path.
9. **Conversation / memory:** same Core relationship and ordered canonical source/result events observed by clients; reconnect/cursor deduplication, retention redaction and forget-generation replacement tested.
10. **Presence / task state:** current node and task projections replace local views; leased online/offline/degraded state and verified/blocked/unknown outcomes come from Core. Client caches grant no authority.
11. **Approval / cancel / revoke:** exact action/session/target/generation/digest review, expiry and current policy rechecks; cancellation and revocation stop future dispatch but cannot undo an already performed effect.
12. **Recovery:** actual Worker crash after effect, before delivery, followed by Core/Worker restart blocks ambiguity and preserves the independently changed marker; no automatic mutation replay.
13. **Linux / ARM64:** constrained local x86_64 Docker and private Caddy TLS receipts above; native ARM64 requires the dedicated CI runner receipt and remains NOT_RUN until obtained.
14. **Windows native:** CNG/DPAPI real-process HTTPS receipt above; Rust/Tauri/TypeScript final-source checks and exact-head CI recorded separately when complete. Synthetic native signing is not owner biometric acceptance.
15. **Android verification:** Gradle/JVM/lint/APK receipts above; emulator external-fixture tests reject skipped prerequisites. Hardware/OEM and owner-phone tests are forbidden in this run.
16. **Final-head CI:** pending committed head and linked runs. Older merged D1/Group 3 CI cannot establish this candidate's result.
17. **Defects / limits:** no claim of general provider inference without a configured provider; unavailable routes remain blocked. Final CI and the explicit external commissioning boundary remain open until matching receipts exist.
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
