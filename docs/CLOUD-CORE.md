# Persistent Cloud Core and connected Grid: deployment and commissioning

This candidate composes the existing Python OSCAR Core, with D2's bounded outbound
Grid transport and scoped file Worker. It is not a second backend, owner enrollment
acceptance, or an Oracle deployment.
Current implementation and evidence are tracked in [status](CURRENT-STATUS.md) and
[delivery plan](DELIVERY-PLAN.md). [Connected software evidence](development/GROUP-04-D2.md)
separates actual process/TLS/native/emulator runs from later commissioning.

## Runtime boundary and dependencies

| Existing component | D1 composition / deployment boundary |
| --- | --- |
| `Harness`, Controller, Model Router, Registry | Same implementations; reviewed provider manifest; optional injected provider credentials |
| `Store`, SQLite Event Archive, Memory Fabric | One persistent data directory, one identity, process-lifetime writer lock, WAL/FTS5, canonical retrieval |
| Grid, Policy, Transport, math executor | Short-lived scoped authenticated diagnostics; no arbitrary public executor or Worker control |
| Runtime, Workers, Executive, scheduler | Durable existing state; interrupted leases recovered conservatively; uncertain mutations require verification rather than replay |
| Native Windows credential store | Read-only mounted server credential adapter; no Windows Credential Manager assumption |
| Windows machine/browser/UIA/capture | Unavailable on Linux; D2 must attach an authenticated real Windows Worker |
| Qdrant/Graphiti/Neo4j/embedding/reranking | Optional derived services; absent services leave explicit canonical-only retrieval |

The runtime uses existing OSCAR source and public model configuration on
digest-pinned Python 3.12.15 / Debian Bookworm slim. D2 reuses the existing pinned
`mobile` cryptography extra for RSA proof-of-possession and approval verification;
the image constrains its CFFI/parser transitive versions and requires binary wheels.
Builds download those small runtime dependencies, with no models or audio/ML/UI
stack. The acceptance target adds repository tests, not another Core implementation.

`deploy/cloud/compose.yaml` runs UID/GID 10001, drops capabilities, disallows
privilege escalation, makes the image read-only, bounds temporary storage, process
count, CPU, memory and log rotation, and restarts after failure. The only writable
durable mount is `/var/lib/oscar`. A regular unpublished Docker bridge permits
outbound provider traffic; **there is no Core host port**. Docker/host administrators
remain trusted. Do not attach unrelated containers to the Core bridge.

Default container budgets are 1 CPU / 1 GiB RAM for Core and 0.5 CPU / 256 MiB for
TLS ingress, with 64 MiB and 16 MiB temporary filesystems respectively. Leave
additional host/daemon/filesystem-cache headroom. These are enforced operating
budgets, not a measured production minimum or a promise that every future workload
fits. Canonical archive capacity grows with retained history; choose storage and
retention from actual usage and restore requirements.

The optional `compose.tls.yaml` adds digest-pinned Caddy 2.11.7 with only ports 80/443.
Only `/v1/*` and `/v2/grid/*` reach the Core; Core permits exactly Grid's two POST
routes and named D1 diagnostic routes. Private health, old loopback adapters and
unknown paths return 404. Authentication, scope, expiry/revocation and replay checks
apply behind TLS. Forwarded HTTPS is only meaningful on this isolated backend
network; never publish port 8080 or run the Core directly on a public interface.
The proxy adds header/body/time bounds. Core adds its own strict parsing, body,
concurrency and rate bounds. Access logs are disabled; categorical Core diagnostics
do not contain request bodies, credentials or private exception text.

The supplied `tls-proxy` production mode requires port **8080**, matching the image
health check, Compose and Caddy upstream; another port fails configuration before
state initialization. The separate `loopback` mode supports explicitly configured
unprivileged ports for private host/reference verification. It is not supported by
the supplied Compose/TLS package and must never become a public direct-Core listener.

Missing/malformed authentication is rejected before any database lookup. Invalid,
expired or revoked clients do not consume authenticated allowances or write nonces.
After successful Grid and deployment-binding validation, admission permits at most
60 requests per node per minute and 120 in total; rate rejection precedes nonce
insertion. Eight concurrent connections and three-second socket timeouts still
bound unauthenticated work. These controls preserve commissioning availability under
the tested request pressure; they are not an Internet denial-of-service guarantee.

## Prepare a Linux host (owner commissioning)

Use an approved 64-bit Linux VM, preferably the current Ubuntu 24.04 LTS ARM64 image
offered for the selected A1 shape. Docker Engine and Compose v2 are host
prerequisites; follow [Docker's Ubuntu installation instructions](https://docs.docker.com/engine/install/ubuntu/).
Keep the checkout/code, configuration/secrets and persistent state separate.
Use local ext4/XFS block storage with ordinary filesystem locking and fsync;
do not put live SQLite on NFS, a shared multi-host volume or an object-store mount.

The following commands are for an explicitly approved owner commissioning session,
not actions performed by the implementation run. Review paths before using `sudo`:

```sh
sudo install -d -o 10001 -g 10001 -m 0700 /srv/oscar/data /srv/oscar/secrets /srv/oscar/backups
sudo install -d -o 10001 -g 10001 -m 0700 /srv/oscar/tls-data /srv/oscar/tls-config
sudo install -d -o root -g 10001 -m 0750 /etc/oscar
sudo install -o root -g 10001 -m 0640 deploy/cloud/cloud.example.json /etc/oscar/cloud.json
sudo install -o root -g 10001 -m 0640 config/development-models.json /etc/oscar/models.json
```

Edit `/etc/oscar/cloud.json`: replace the invalid identity and domain placeholders
with the owner's chosen stable Core ID and approved hostname; review every provider
and account policy in `/etc/oscar/models.json`. Do not create a second identity if
an existing canonical Core already owns history: stop the original writer and plan
an explicit, validated migration first. New cloud initialization is only for an
owner-approved new canonical data directory. Missing/mismatched identities, unsafe
paths, unsupported schemas and invalid production configuration fail startup.

Provider keys are optional. For each approved key, put a private regular JSON file
containing exactly `secret` (the value) and `expires_at` (Unix seconds or null) in
`/srv/oscar/secrets`, owned by UID 10001 with mode 0600, and map the existing provider
environment name to that opaque filename in `provider_secrets`. Never put values
in production configuration, image layers, shell command arguments, Compose
environment variables or the checkout. An empty mapping enables no external
provider account. The Core does not enroll providers, discover owner secrets or
invent credentials.

Set only nonsecret operational paths in the commissioning shell:

```sh
export OSCAR_CONFIG=/etc/oscar/cloud.json
export OSCAR_MODELS=/etc/oscar/models.json
export OSCAR_SECRETS=/srv/oscar/secrets
export OSCAR_DATA=/srv/oscar/data
export OSCAR_IMAGE="oscar-cloud:$(git rev-parse HEAD)"
docker compose -f deploy/cloud/compose.yaml config --quiet
docker compose -f deploy/cloud/compose.yaml build
docker compose -f deploy/cloud/compose.yaml run --rm --no-deps core python -m oscar.cloud --config /etc/oscar/cloud.json --initialize
docker compose -f deploy/cloud/compose.yaml up -d --wait
docker compose -f deploy/cloud/compose.yaml ps
docker compose -f deploy/cloud/compose.yaml exec -T core python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/readyz', timeout=3).read().decode())"
```

Initialization does not create an owner/device enrollment token. The offline
`python -m oscar.cloud --help` exposes explicit short-lived client commissioning
and revocation commands. An operator must choose the node, expiry and private
credential-output path. Generated credentials must stay outside source control
and logs. These diagnostics are not Android/Desktop enrollment or Full Access.

For explicitly approved diagnostic commissioning, first create a private
UID/GID-10001 directory `/srv/oscar/commissioning`, then stop the Core and run:

```sh
docker compose -f deploy/cloud/compose.yaml stop core
docker compose -f deploy/cloud/compose.yaml run --rm --no-deps --volume /srv/oscar/commissioning:/commissioning core python -m oscar.cloud --config /etc/oscar/cloud.json --enroll-client --node-id OWNER_CHOSEN_LOWERCASE_NODE_ID --ttl 3600 --credential-output /commissioning/diagnostic-client.json
docker compose -f deploy/cloud/compose.yaml up -d --wait
```

Replace the invalid uppercase node placeholder with the operator's actual chosen
bounded lowercase node ID. The credential authorizes only deployment inspection,
bounded arithmetic probes and their explicit diagnostic retention. Do not print
or commit it. To revoke it, stop the service, run the same offline command with
`--revoke-client --node-id OWNER_CHOSEN_LOWERCASE_NODE_ID`, then start and verify
that the old credential is rejected. Client expiry is at most 24 hours; default
TTL is one hour. New credential-output files must not already exist. On Linux the
parent must be owned by the service UID with mode 0700. Directory descriptors and
no-follow/exclusive creation protect traversal and output replacement; the private
file and directory are synced before the existing Grid session transaction commits.
The deployment binding commits in that same transaction. Host administrators and
the service UID remain trusted; Windows reference tests rely on private directory ACLs.

Delivery failure or process interruption rolls back the new session and binding;
previous valid credentials are preserved. A failed/interrupted attempt may leave a
private partial file or a complete **unusable** credential, and an unpaired node
record. Never infer enrollment success from file existence. Retry explicitly with
the same eligible diagnostic node and a **new output filename**; existing files are
never overwritten or automatically deleted. Content-free attempt/failure/delivery
audit records distinguish completed transactions; an attempt without delivery is
incomplete. Revoked or unrelated node identities require an explicit new identity.
That D1 workflow does not grant remote device authority. The separate D2 enrollment
endpoint accepts only a trusted operator's short-lived invitation and proof from
its exact pinned device key; it cannot initiate owner trust by itself.

Existing local Core execution enrollment expires after seven days. Startup and
restart **do not renew** expired/revoked execution authority. The service reports
unready when that authority is unavailable; it must not silently regain authority.
After an operator reviews the unavailable state and deliberately approves renewal:

```sh
docker compose -f deploy/cloud/compose.yaml stop core
docker compose -f deploy/cloud/compose.yaml run --rm --no-deps core python -m oscar.cloud --config /etc/oscar/cloud.json --renew-execution
docker compose -f deploy/cloud/compose.yaml up -d --wait
```

This offline local reenrollment is an operational requirement of the current D1
candidate, not standing owner delegation or D2 distributed credential renewal.
Do not hide it behind an unattended renewal timer. Inspect readiness and a scoped
authenticated request after renewal.

## Connected device invitations (separate owner commissioning)

Use [protocol 2](development/GROUP-04-D2-PROTOCOL.md) and the native connection UI
to export a device-generated transport public key and installation identity.
Independently review the fingerprint, exact role, workspace and requested retention.
Transport proof and native owner-confirmation keys are separate; add an owner key
only when its actual native confirmation boundary is acceptable. Synthetic PEM
fixture keys never establish real owner or hardware-backed acceptance.

With the Core stopped, create a new private output in the existing UID/GID-10001
commissioning directory. Example for an explicitly approved Desktop enrollment:

```sh
docker compose -f deploy/cloud/compose.yaml stop core
docker compose -f deploy/cloud/compose.yaml run --rm --no-deps --volume /srv/oscar/commissioning:/commissioning core python -m oscar.remote_grid invite --config /etc/oscar/cloud.json --node OWNER_CHOSEN_NODE --role desktop --installation DEVICE_INSTALLATION_ID --public-key-file /commissioning/device-public.txt --workspace OWNER_CHOSEN_WORKSPACE_ID --retain --output /commissioning/new-device-invitation.json
docker compose -f deploy/cloud/compose.yaml up -d --wait
```

Replace placeholders with the reviewed bounded identities; the Desktop's absolute
workspace remains local, and the Core knows only its opaque workspace ID. The
public-key file contains base64 DER. `--retain` is explicit relationship history
sharing/retention consent, not authority inferred from a connection. For Android
choose `--role mobile` and omit `--workspace`; do not perform this on the owner's
phone during the software integration run. Transfer the invitation privately to
the exact device and complete its key-signed enrollment within five minutes.
Invitation replay, expiry, wrong key or mismatched identity fails closed.

Sessions have bounded expiry and rotation fences their predecessors. A lost
rotation response or revoked enrollment requires explicit trusted recovery; do
not copy another device's session or weaken TLS. Use `--recover` only after the
operator reviews replacement key/identity and revocation. Backup restoration
invalidates remote sessions and invitations; recover deliberately without running
the original and restored writers together. D1 diagnostic credentials do not
authorize these device operations. Secure/Full Access stays inactive.

Enrollment consumes a valid invitation before one atomic node/session/device
binding commit. A failed commit preserves previous credentials but the consumed
invitation cannot be retried. Lost replies require a fresh operator-issued
invitation (and explicit `--recover` when the identity exists). Never infer a
successful connection from a consumed invitation or a partial legacy node row.
See [failure/restart evidence](development/GROUP-04-D2-CLOSURE.md).

## TLS and network commissioning (separate owner authorization)

First verify the private service, backup/restore and credential rejection on the
actual host. Only after explicit approval, assign the approved domain's A/AAAA
records, constrain SSH to owner addresses, and permit TCP 80/443 in both host
firewall and OCI security rules. Keep 8080, SQLite, Qdrant and Neo4j private.
Docker published ports interact with host firewall rules; verify the actual
external port exposure, not just a UFW status message. No firewall or DNS command
is automated by these assets.

```sh
export OSCAR_DOMAIN=OWNER_APPROVED_HOSTNAME
export OSCAR_TLS_DATA=/srv/oscar/tls-data
export OSCAR_TLS_CONFIG=/srv/oscar/tls-config
export OSCAR_INGRESS_IMAGE="oscar-cloud-ingress:$(git rev-parse HEAD)"
docker compose -f deploy/cloud/compose.yaml -f deploy/cloud/compose.tls.yaml config --quiet
docker compose -f deploy/cloud/compose.yaml -f deploy/cloud/compose.tls.yaml build ingress
docker compose -f deploy/cloud/compose.yaml -f deploy/cloud/compose.tls.yaml up -d --wait
```

Caddy obtains and renews certificates on the real domain; preserve its private
certificate data. [Automatic HTTPS requirements](https://caddyserver.com/docs/automatic-https)
include authoritative DNS and reachable challenge ports. A local proxy validation
is not a certificate issuance or public network acceptance. From an independent
host, verify TLS chain/hostname, unauthenticated rejection, valid scoped request,
expiry/revocation/replay rejection and 404 for health and legacy endpoints. Never
disable certificate verification to make commissioning pass.

## Backup, restore, storage and upgrades

Both SQLite files, identity, authority/session state, artifacts and durable runtime
records belong to the same canonical volume. A WAL file must not be copied alone
or discarded while live. The maintenance CLI acquires the same single-writer
lock, requires the service stopped, uses SQLite's backup API, validates schemas,
identity and database integrity, and creates a file-hashed snapshot. External
provider secret files are separate and excluded; treat snapshots as private
because canonical history and OSCAR authority material are sensitive.

```sh
docker compose -f deploy/cloud/compose.yaml stop core
docker compose -f deploy/cloud/compose.yaml run --rm --no-deps --volume /srv/oscar/backups:/backups core python -m oscar.cloud_state backup --data-dir /var/lib/oscar --backup /backups/OWNER_CHOSEN_NEW_SNAPSHOT
docker compose -f deploy/cloud/compose.yaml up -d --wait
```

Copy verified snapshots to an owner-approved independent encrypted destination.
Backups on the same VM/volume do not protect against reclamation or disk loss.
Monitor disk usage with `df -h`, volume usage with `du -sh /srv/oscar/data`,
container memory/CPU with `docker stats --no-stream`, and bounded categorical logs
with `docker compose -f deploy/cloud/compose.yaml logs --tail 100 core`. Plan
backup retention explicitly; no script silently deletes canonical history.

For restore, keep the original writer stopped and fenced. Restore into a **new**
empty destination, never overlay an existing Core. Example using an owner-created
writable restore parent and a trusted snapshot:

```sh
docker run --rm --user 10001:10001 --read-only --cap-drop ALL --network none --tmpfs /tmp:rw,size=64m --volume /srv/oscar/backups:/backups:ro --volume /srv/oscar/restore:/restore "$OSCAR_IMAGE" python -m oscar.cloud_state restore --backup /backups/OWNER_CHOSEN_SNAPSHOT --data-dir /restore/data
```

Set `OSCAR_DATA` to the restored directory after independently checking restore
integrity; retain the same configured Core ID and separately injected secrets.
Start exactly one writer, verify prior archive retrieval and task/Worker/schedule
states, then invalidate transferred or obsolete credentials as appropriate. A
filesystem lock prevents two processes sharing one local volume; it cannot fence
independently cloned volumes. **Do not start original and restored copies together.**

Before upgrading: record the running image ID, stop and back up, build/tag the
reviewed Git commit, then start and verify readiness, identity, old history,
failure/restart and authenticated requests. Keep the previous image and snapshot.
For rollback, stop the candidate, choose the previous image and a new independently
restored compatible snapshot. Never downgrade a database in place or discard new
events silently; reconcile any post-snapshot canonical history before switching.

## Oracle Always Free preparation (official sources checked 2026-10-18)

The current [Oracle Always Free compute and storage documentation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
lists **1,500 A1 OCPU-hours and 9,000 GB-hours monthly**, equivalent to **2 OCPUs /
12 GB RAM** for Always Free tenancies, in the home region. It lists 200 GB combined
boot/block storage and five combined volume backups. Do not rely on older 4/24
guides. The actual account's displayed eligibility, limits and capacity remain
unverified. Capacity shortages do not authorize paid upgrade or automatic retry
provisioning. Allocate storage for OS, archive growth and recovery rather than
consuming the entire allowance on the initial boot disk.

Idle Always Free compute can be reclaimed after seven days under Oracle's listed
CPU/network/memory conditions. Independent backups and tested restoration are
required; artificial load to evade reclamation is inappropriate. Free-tier
availability is not an uptime guarantee. [Trial-end rules](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)
also require resource limits and eligibility to be checked before relying on an
instance after trial expiry.

Owner provisioning checklist: authenticate the actual tenancy; confirm home
region, A1 capacity, current Always Free eligibility and quotas; choose an approved
ARM64 OS and bounded shape; review persistent volume placement/retention and backup
budget; provision VM/network/SSH under explicit authorization; install the runtime;
execute private acceptance; then separately approve domain, TLS and ingress.
Verify independently after VM restart and restore. No Oracle account, capacity,
billing, firewall, DNS or deployed TLS acceptance is implied by software CI.

## Optional memory services and ARM64 limits

Canonical SQLite retrieval remains available without any optional package or
service. Qdrant and Graphiti indexes remain derived and rebuildable from canonical
records; their absence must never be reported as proof that a memory never existed.

| Component | Compatibility evidence / capacity boundary |
| --- | --- |
| Python/SQLite Core | Pinned Python image publishes Linux amd64 and arm64 manifests; actual ARM64 CI must run service/persistence tests, not only build/import |
| Qdrant | [Official requirements](https://qdrant.tech/documentation/installation/) support AArch64 and POSIX block storage; workload-dependent sizing requires vector/index/payload measurement |
| Graphiti / Neo4j | Graphiti 0.30.2 metadata supports Python 3.10+ with Neo4j 5.26+; [Neo4j requirements](https://neo4j.com/docs/operations-manual/current/installation/requirements/) support ARM64 and list 2 GB RAM / 10 GB storage as cloud minima; graph size, page cache/JVM and concurrent Core workload require measurement |
| FastEmbed 0.8.1 | Python 3.12 compatible universal wheel; ONNX Runtime, NumPy, tokenizers and model artifacts are additional architecture-sensitive dependencies; existing OSCAR adapters bound CPU threads to two |
| Embedding/reranking reference | Sentence Transformers 6.1.0 metadata supports Python 3.10+; PyTorch/Transformers/SciPy and model weights are substantial independent dependencies |

Package metadata is checked against published [Qdrant client](https://pypi.org/project/qdrant-client/1.19.1/),
[Graphiti](https://pypi.org/project/graphiti-core/0.30.2/),
[FastEmbed](https://pypi.org/project/fastembed/0.8.1/) and
[Sentence Transformers](https://pypi.org/project/sentence-transformers/6.1.0/).
Universal Python wheels alone do not prove transitive native wheels, inference,
models, memory usage or Oracle fit. These optional services are not started by the
D1 package. Deploy them separately on a private network only after their own
version/image, credentials, model provenance and resource acceptance; preserve the
canonical-only degraded state until then. No full-memory-stack free-tier fit is
claimed.

On 2026-10-18, a Linux Python 3.12.15 container with temporary pip 26.2.1
successfully cross-resolved **52 binary wheels** for the pinned `memory` extra
packages and all transitives using CPython 3.12 / Linux ARM64 tags. This included
NumPy 2.5.4, ONNX Runtime 1.31.0, grpcio 1.84.0 and tokenizers 0.23.3. The published
wheel metadata supports packaging feasibility; this was a dry run, not ARM64
inference or a server-memory benchmark. The base image's pip 25 could not resolve
the current NumPy candidates, and Windows cross-resolution incorrectly applied
Windows-only dependency markers; neither result establishes Linux incompatibility.
The Core image itself was not changed to install these optional packages or pip.

To repeat that bounded metadata-only audit in a disposable Linux container:

```sh
docker run --rm oscar-cloud:local sh -c 'python -m pip install --target /tmp/audit-pip pip==26.2.1 && PYTHONPATH=/tmp/audit-pip python -m pip install --dry-run --ignore-installed --only-binary=:all: --platform manylinux_2_28_aarch64 --platform manylinux_2_27_aarch64 --platform manylinux_2_17_aarch64 --platform manylinux2014_aarch64 --platform any --python-version 3.12 --implementation cp --abi cp312 --abi abi3 --abi none qdrant-client==1.19.1 graphiti-core==0.30.2 fastembed==0.8.1'
```

## Optional native account enrollment

The local software candidate accepts public OAuth application registrations via
`auth_config`, an absolute JSON path outside the canonical data directory. Copy
and administer [the example](../config/oauth-providers.example.json): replace
native client IDs, the explicit Microsoft tenant UUID and exact registered
numeric-loopback redirects. Endpoints are fixed by OSCAR. The all-zero tenant in
the example is a placeholder, not a commissioned tenant. Service IDs must match
the installed manifests (`google.gmail`, `google.calendar`, `google.drive`,
other explicitly present Google families, or `microsoft.graph`). Scope ceilings
are explicit and never imply a grant before provider consent. Native Desktop
holds callback codes outside React; real consent remains a commissioning step.

In Cloud configuration, `auth_config` and `credential_key_ref` are an optional
pair. The latter names a private JSON file in the existing `secret_dir`, with
the same injected-secret format: `{"secret":"BASE64_OF_32_RANDOM_BYTES",
"expires_at":null}`. Provision this key through the approved secret-management
procedure, mount it read-only and retain it separately from data backups. Never
place the key, provider client secrets, refresh/access tokens or real callback
codes in source, public config, command arguments or logs.

Account tokens are encrypted using AES-GCM in `data_dir/account-credentials`;
opaque references and current account generations remain in canonical SQLite.
Files are bounded, privately permissioned, atomically replaced and authenticated
against their opaque reference. Account disconnect fences metadata before remote
revocation and local token removal. Provider revocation response is reported
evidence, not independent proof. The existing offline state backup includes the
encrypted credential files; restore requires the separately retained same key.
Losing or changing that key requires account reauthorization. Backup possession
alone must not grant token access. Existing injected administrator credentials
remain read-only and separately mounted.

Local Windows composition with `--auth-config` stores the vault master key in
Windows Credential Manager and uses the same encrypted token files. Restored
canonical metadata retains its original native key reference; copying data to a
different host does not copy native key custody. No automatic provider enrollment
or secret generation occurs in a web/native request.

## Reproduce software acceptance

```sh
python -m pip install '.[dev,mobile]'
docker build --target runtime -f deploy/cloud/Dockerfile -t oscar-cloud:local .
docker build --target acceptance -f deploy/cloud/Dockerfile -t oscar-cloud-acceptance:local .
docker build --target ingress -f deploy/cloud/Dockerfile -t oscar-cloud-ingress:local .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 --memory 1g --cpus 1 --tmpfs /tmp:rw,size=128m,mode=1777 oscar-cloud-acceptance:local
python -m scripts.verify_cloud_ingress --core-image oscar-cloud:local --ingress-image oscar-cloud-ingress:local
python -m scripts.verify_connected_grid
python -m unittest tests.test_cloud tests.test_cloud_acceptance tests.test_cloud_state tests.test_cloud_platform tests.test_cloud_recovery tests.test_cloud_enrollment tests.test_cloud_admission tests.test_remote_grid tests.test_remote_worker -v
```

The ingress check starts actual Core and Caddy containers on an internal Docker
network with **no published ports**, trusts the generated local CA properly, tests
canonical public-443 redirects with an untrusted Host, authentication rejection,
private/legacy-path rejection, D1 diagnostics, actual Grid device proof/enrollment,
runtime arithmetic/archive writes and separate TLS readback. It restarts Core and
confirms the same D1 and D2 tasks remain. It removes
only its generated containers, volume and network, including on failure. It uses
synthetic credentials and does not contact an owner provider or public CA.

The Cloud workflow builds and runs these contracts on native Ubuntu x86_64 and
ARM64 runners. Successful CI proves that runner/runtime and the tested local
boundary. The separate-process suite additionally executes the real scoped Worker
and independent filesystem readback over trusted TLS, including process death
after a mutation and no replay after Core/Worker restart. These local environments
do not prove an independent Oracle host, public certificate, native UI acceptance
or owner commissioning. Preserve exact-head CI and each native platform's evidence
in the [connected ledger](development/GROUP-04-D2.md).

Historical D1 initial Linux x86_64 verification on 2026-10-18 passed all **31 Cloud
tests** in the Python 3.12.15 acceptance image under UID 10001, read-only filesystem,
dropped capabilities, no new privileges, 1 GiB RAM and one CPU. The actual private
Core/Caddy TLS check also passed. After the small synthetic request and restart,
Docker reported Core **27.14 MiB / 1 GiB** and ingress **14.11 MiB / 256 MiB**.
These are container memory snapshots, not peak/RSS benchmarks or production sizing.
The inspected amd64 image `Size` fields were 47,782,283 bytes (Core) and 43,104,770
bytes (ingress). Native ARM64 CI and Oracle commissioning evidence are separate.
The corrected engineering closure expands acceptance to **44 Cloud tests**;
all 44 passed locally on constrained Linux without skips, and Windows full
regression ran 728 tests with 15 platform/optional skips. See the [closure ledger](development/GROUP-04-D1.md)
and [PR #8 receipt](https://github.com/Amaan27-Buzz/oscar/pull/8) for final-head and
post-merge native CI; these supersede the initial candidate counts.
