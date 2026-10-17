# Group 4/D1 — persistent Cloud Core engineering evidence

Starting main: `94ce220509a15b3930630f8bbc96700fad882c44`, fetched from
`Amaan27-Buzz/oscar` on 2026-10-18. Branch: `codex/group-04-d1-cloud-core`.
This is a software candidate for review; Oracle is not provisioned, and D2/Group 5
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
python -m unittest tests.test_cloud tests.test_cloud_acceptance tests.test_cloud_state tests.test_cloud_platform tests.test_cloud_recovery -v
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

Implementation-time Windows Python 3.12, Linux x86_64 constrained-container and
actual private TLS tests passed their exercised scope. Native ARM64 and exact
final-head repository CI results are recorded below when available. Base images
publish genuine ARM64 manifests; optional memory dependency resolution verifies
wheel availability only, not inference or service resource fit.

Starting-main CI: repository, Markdown, Brain, voice, Edge and Mobile succeeded.
Desktop failed waiting 60 seconds for the disposable WPF fixture readiness before
Harness construction (`39068366433`); exact underlying startup cause is UNKNOWN.
This starting-main failure is not attributed to the D1 change.

Final-head CI: pending the draft PR workflow runs. This line is not a green CI claim.

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
