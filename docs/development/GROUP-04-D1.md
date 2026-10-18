# Group 4/D1 — persistent Cloud Core engineering evidence

Starting main: `94ce220509a15b3930630f8bbc96700fad882c44`, fetched from
`Amaan27-Buzz/oscar` on 2026-10-18. Branch: `codex/group-04-d1-cloud-core`.
The engineering closure below supersedes the initial candidate review. Oracle is not provisioned, and D2/Group 5
are not implemented by this change. Gate C/D remain PARTIAL and Gate E NOT PASSED.

## Actual implementation and dependency map

```text
explicit production config + exclusive local volume lock
  -> existing Harness (portable lifecycle, injected credentials, deferred start)
     -> Store/core.sqlite (tasks, leases, nonces, dedup, authority, Workers/schedules)
     -> EventArchive/core.archive.sqlite (canonical history, WAL/FULL, FTS5)
     -> Runtime / Controller / Policy / MemoryFabric
     -> Registry / CredentialPool / Router / HTTP providers (optional)
     -> Dispatcher / scoped files / math / independent Verifier
     -> WorldRuntime + shared Presence + Executive / durable scheduling
  -> bounded private HTTP diagnostics -> optional Caddy TLS ingress
```

Critical blockers addressed: hardcoded reference node ID; Windows-only Vault
fallback; ambient developer credentials; uncontrolled process composition;
unfenced canonical data directories; archive schema-version omission; unsafe
exposure of reference HTTP; interrupted tasks without leases; non-atomic
cross-database admission; consistent all-state backup/restore. Existing engines
remain authoritative. No new task engine, ownership system or arbitrary public
Worker control was created.

## Production and authority boundary

- Missing/corrupt/incompatible config, manifest, identity or schemas fail closed.
  Initialization is explicit and refuses nonempty or partial volumes. An operator
  chooses installation identity; software does not manufacture owner enrollment.
- Mounted secrets are private regular files with explicit expiry; no secret values
  enter images, configuration, diagnostics or canonical events. Models/search use
  explicit injection, with dynamic resolvers for mounted-key revocation.
- Core has no published host port in Compose. Optional TLS proxy permits `/v1/*`
  only; private health and legacy/debug/enrollment/executor routes remain absent.
- Diagnostic sessions use existing Grid credentials, deployment binding, scopes,
  expiry/revocation, timestamp checks and durable nonce rejection. Arithmetic action
  and synthetic archive retention require separate grants and Personal Policy.
  Bounded request bodies, timeouts, connection count and global admission rate
  constrain resource use. Logs are categorical and content-free.
- Existing internal execution enrollment is not made permanent: live tokens rotate
  under the existing seven-day enrollment bound; expiry/revocation fails readiness
  and requires explicit stopped-service `--renew-execution`. Offline initialization,
  client administration and renewal do not execute due schedules.

## Persistence and recovery

The installation identity is checked against both canonical databases before
startup. Exclusive local filesystem locking fences service and maintenance
processes. SQLite WAL/FTS5 and FULL synchronization remain canonical. Optional
Qdrant/Graphiti/Neo4j/embedding/reranking are absent and reported unavailable;
canonical retrieval still works, and derived services remain separately deployable
and rebuildable using existing adapters. No full-stack Oracle capacity claim.

Recovery precedes background execution. Interrupted local leases are released and
tasks become BLOCKED/UNKNOWN; an execution marked before its lease is also blocked.
Existing dedup STARTED records prevent blind replay after a consequential mutation
with a lost result. Exact diagnostic retries bind the same task and repair an
archive-admission gap; inspection reports conflict until repair, not false success.

Backups require stopped service and the same volume lock. Both SQLite snapshots,
identity, session/dedup state, Worker/schedule state and artifacts are hashed,
validated and atomically published. Restore independently validates schema,
identity, integrity, FTS5 and file inventory into a new destination. Existing
destinations are preserved. Secrets are injected separately. Snapshots are private
and need owner-managed off-host encryption/retention. Local locks cannot fence
independently cloned volumes; original and restored copies must never run together.

## Acceptance and reproducible commands

The automated Cloud suite exercises all 15 requested classes using real Core,
SQLite, threads, subprocesses and sockets: fresh initialization, archive read/write,
boundary request, restart identity/history, Worker/schedule restore, interrupted
execution, ambiguous mutation without duplicate replay, bad/revoked/expired auth,
private reference endpoints, missing indexes, backup/independent restore,
shutdown/resource release, corrupt config/state, and Windows capability absence.
Failure injection patches live test processes only; production has no crash hook.

```sh
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m scripts.check_repository
python -m unittest discover -s tests -t . -v
python -m unittest tests.test_cloud tests.test_cloud_acceptance tests.test_cloud_state tests.test_cloud_platform tests.test_cloud_recovery tests.test_cloud_enrollment tests.test_cloud_admission -v
docker build --target runtime -f deploy/cloud/Dockerfile -t oscar-cloud:local .
docker build --target acceptance -f deploy/cloud/Dockerfile -t oscar-cloud-acceptance:local .
docker build --target ingress -f deploy/cloud/Dockerfile -t oscar-cloud-ingress:local .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 --memory 1g --cpus 1 --tmpfs /tmp:rw,size=128m,mode=1777 oscar-cloud-acceptance:local
python -m scripts.verify_cloud_ingress --core-image oscar-cloud:local --ingress-image oscar-cloud-ingress:local
```

The TLS acceptance uses actual Core/Caddy containers on a private Docker network,
no published ports, a trusted local CA with certificate verification enabled,
authenticated probe/independent readback and real container restart. It is local
network acceptance, not independently hosted Cloud/Desktop operation.

## Verification ledger

Windows Python 3.12.10 full regression: **715 tests, PASS, 13 platform/optional
skips**, using the documented `.[dev,mobile]` dependencies in an isolated ignored
environment. Ruff, format, strict mypy and repository/secret checks passed.
Linux x86_64 constrained-container Cloud acceptance: **31 tests PASS**, plus actual
private trusted-CA TLS, independent readback and container restart. Native ARM64
also passed all 31 Cloud tests and actual TLS on `ubuntu-24.04-arm` (`aarch64`),
not emulation. Optional memory dependency resolution found 52 compatible ARM64
binary wheels; this is availability evidence, not inference, index service runtime
or workload-fit acceptance.

Starting-main CI: repository, Markdown, Brain, voice, Edge and Mobile succeeded.
Desktop failed waiting 60 seconds for the disposable WPF fixture readiness before
Harness construction (`39068366433`); exact underlying startup cause is UNKNOWN.
This starting-main failure is not attributed to the D1 change.

Initial native CI receipt: [x86_64 and ARM64 Cloud jobs](https://github.com/Amaan27-Buzz/oscar/actions/runs/39070203322)
passed on `700f1dff3c5ca74ff09b658c1bb618c3cbfa419a`; ARM64 executed 31 tests in
21.405 seconds and the verified local TLS round-trip. Subsequent changes read probe
values from actual persisted executor results and strengthen deployment resource
assertions; focused regression passed. [Draft PR #8 checks](https://github.com/Amaan27-Buzz/oscar/pull/8/checks)
are authoritative for its latest head. No earlier-head receipt substitutes for
green final-head checks, and no CI result constitutes Oracle deployment acceptance.

## Final independent engineering closure — 2026-10-18

Fresh starting main was `94ce220509a15b3930630f8bbc96700fad882c44`; PR #8 started
at `ea24e639a71b742d8ad9040bfe1cda1b5d497419`, draft and mergeable, with no GitHub
review comments. All eight workflows had passed on that starting head. The owner
then authorized reviewed, CI-gated integration of this existing PR, superseding
the draft-only stop. The initial 31-test/715-test receipts above remain historical.

Three defects were confirmed and corrected:

1. Offline enrollment committed authority before credential delivery. Output now
   reserves a new private file in an owned 0700 Linux directory before client
   authorization changes, using descriptor traversal, no-follow and exclusive
   creation. The existing Grid pairing transaction invokes delivery before commit:
   file/directory fsync and path/inode validation precede session/binding commit.
   Delivery errors and process death roll back new authorization, preserving prior
   valid sessions. An unpaired node and invalid partial/complete output may remain;
   explicit retries use a new filename. Attempt/failure/delivery audit records have
   no token or file content. There is no new remote enrollment authority or API.
2. Configurable production ports disagreed with the packaged health/proxy port.
   `tls-proxy` now requires 8080 before initialization; separate private loopback
   verification retains explicit alternative unprivileged ports.
3. Unauthenticated traffic exhausted the shared request allowance. Cheap malformed
   rejection precedes DB access, and only authenticated/bound clients consume the
   existing 120/minute total allowance, with 60/node/minute fairness. Rate rejection
   precedes durable nonce insertion. Eight connections/three-second timeouts remain.

New coverage includes existing/unwritable output, partial writes, sync failure,
session creation failure, explicit retry, subprocess interruption/restart,
preservation of prior sessions, symlink/path replacement, production port rejection
and 363 unauthenticated requests followed by healthy authorized access. The Cloud
suite now contains **44 tests**, exercising actual Core/SQLite/process/socket
components. The Linux constrained-container run passed all 44 without skips, plus
real trusted-CA Core/Caddy TLS, independent readback and restart. Windows focused
execution ran 44 with three POSIX-only skips; skipped checks are not Windows evidence.
The complete Windows Python 3.12.10 regression ran **728 tests, OK, 15
platform/optional skips** in 331.035 seconds. Strengthened enrollment failure-point
checks also passed separately, and the final Linux suite passed 44 in 42.310
seconds. Ruff, formatting (188 files), strict mypy and repository/local-link/secret
checks passed. Approved Desktop, Android, expression and Orb files are unchanged.

Focused adjacent review covered lifecycle/draining, identity/locking, mounted-key
revocation, execution renewal, partial initialization, backup/restore integrity,
SQLite and cross-database admission, Docker isolation, proxy/header trust and
readiness/resource bounds. No additional reproducible critical/high D1 defect was
found. Local locks still do not fence independently cloned volumes, and optional
memory services still require separate runtime/capacity acceptance.

The [existing PR #8](https://github.com/Amaan27-Buzz/oscar/pull/8) closure receipt
records the exact corrected final head, full regression counts, native ARM64/x86_64
workflow links, resulting merge SHA and post-merge main checks. Integration requires
all applicable final-head checks successful, no unresolved critical/high issue,
reconciliation with current main and unchanged design/authority/data contracts.
No waiver, physical acceptance or hosted Oracle PASS is implied by software PASS.

## External D1 acceptance and D2 handoff

Remaining D1 acceptance: owner-authenticated tenancy/eligibility/A1 capacity;
approved host/volume provisioning; real VM lifecycle and independent network
tests; domain/public certificate and authorized firewall rules; owner-secret
commissioning and external backup/restore; actual operational monitoring and
workload sizing. [Ready-to-execute operations and Oracle guide](../CLOUD-CORE.md)
contains exact deployment/upgrade/rollback commands and current official limits.
No cloud billing, account enrollment, firewall, DNS or paid procurement was changed.

D2 should reuse the same Core/Grid/Store/Archive/Policy/Executive and replace the
bounded diagnostic ingress with explicitly designed outbound Desktop sessions,
Android enrollment, scoped identities, target-side checks, distributed revocation,
replay/fencing, offline/partition recovery, task/Presence synchronization and
independent remote result verification. D1 diagnostic clients are not owner devices
and cannot authorize a remote Worker. Preserve the one canonical writer during
future home-server migration. Computer-use expansion, MCP marketplace and Full
Access activation remain Group 5 work.
