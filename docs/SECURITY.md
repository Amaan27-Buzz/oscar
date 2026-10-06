# Security + Permissions

OSCAR acts across phones, computers, cloud services, communications and physical hardware. Security is architectural, not a later hardening pass.

## Core rules

1. **Least privilege by capability.** Nodes/tools receive only required authority.
2. **Voice is not a password.** Voice Match can contribute identity evidence; high-risk actions require stronger confirmation.
3. **Voice Map is not authorization.** Recognition never grants permission.
4. **Safety-critical control stays local.** Emergency stop/interlocks do not depend on cloud reasoning.
5. **Consequential actions are attributable.** Record initiator, policy/permission, executor, result and verification.
6. **Nodes connect outward where practical.** Avoid unnecessary inbound exposure on home/Edge devices.
7. **Fail safe and degrade explicitly.** Loss of cloud/phone/desktop/Worker cannot create dangerous state or false success.
8. **Capture is explicit.** Persistent awareness does not silently become persistent recording.
9. **Persona never changes authority.** Character cannot weaken truth, safety, permissions, consent or required confirmation.
10. **Perception, retention and action are separate.** Access to observe current context never silently grants durable storage or mutation authority.

## Authorization classes

| Class | Examples | Typical requirement |
|---|---|---|
| Safety | emergency stop / halt actuator | local and broadly reachable where safe |
| Harmless | weather / simple public read | configured allow |
| Personal | private calendar/memory/device/notification context | authorized user + scoped permission |
| Sensitive | send message / calendar mutation / capture settings / Sentry config | strong identity + explicit/contextual approval or explicit policy |
| Critical | financial/security/destructive actions | OSCAR Mobile biometric/PIN or equivalent strong approval; voice alone insufficient |

## Permission lattice

OSCAR should model at least three independent questions:

```text
CAN PERCEIVE?
CAN RETAIN?
CAN ACT?
```

Examples:

```text
notification listener access
≠ permission to retain notification bodies
≠ permission to reply

calendar read
≠ permission to edit/delete calendar

location access
≠ permission to retain location history

microphone access
≠ ambient STT
≠ raw audio retention

selected Android assistant role
≠ notification access
≠ overlay permission
≠ microphone permission
≠ unrestricted app access
```

Personal Policy may narrow any of these but cannot widen missing OS/provider permission.

See [CHIEF-OF-STAFF.md](CHIEF-OF-STAFF.md).

## Owner authority and Connection Grid

OSCAR Mobile is the preferred everyday owner-control surface for the Connection Grid.

Where supported it can:

- pause autonomous work;
- cancel tasks;
- revoke a node/session/credential;
- change Sentry/capture state;
- approve sensitive actions;
- request remote machine sleep/shutdown;
- inspect what each node is doing.

But OSCAR Mobile does **not** outrank deterministic physical safety.

```text
local emergency/safety interlocks
> owner revocation / strong confirmation
> granted permissions + explicit Personal Policy
> OSCAR Executive / Workers / Persona
```

If OSCAR Mobile is offline, existing authorized work may continue only within already granted scope. No other node may fabricate an owner-critical approval.

## Android / OSCAR Mobile security boundary

OSCAR Mobile should use legitimate platform APIs and explicit user-granted special access.

### Assistant role

If OSCAR Mobile is selected as the Android assistant, treat that as one platform role—not root/system authority. Other permissions remain separate and inspectable.

### Overlay Orb

Application-overlay capability is sensitive UI authority.

- require explicit overlay permission;
- allow quick disable/hide;
- do not use overlay to obscure security prompts or impersonate system UI;
- do not treat overlay visibility as proof of runtime health;
- account for Android/OEM behavior that can reposition or suppress overlays;
- app-specific `hide Orb` rules should not silently disable unrelated OSCAR services.

### Notification listener

Notification-listener access can expose sensitive personal content.

- require explicit user grant;
- support per-app/person/source exclusions;
- avoid durable retention by default unless policy says otherwise;
- treat OTP/password/security-code/banking classes as non-retainable by default;
- do not infer hidden app history/state;
- do not treat notification visibility as permission to send/reply.

### Notification actions / RemoteInput

A reply/send capability exists only when Android exposes a legitimate action or another authorized connector/device capability exists. Sending follows communication permission/Personal Policy and verification semantics.

## Connection Grid transport security

Each Grid node uses:

- explicit pairing;
- per-node identity;
- scoped credentials;
- encrypted transport;
- short-lived session credentials where practical;
- capability-scoped authorization at the target;
- replay protection/idempotency;
- correlation IDs;
- credential rotation/revocation;
- protocol/version negotiation;
- health/lease expiry so dead nodes do not remain trusted as active executors.

Do not use one blanket shared secret across phone, desktop, cloud and Edge.

Cloud compromise must not bypass local safety interlocks.

## Auth Broker and decision-controller authority

OSCAR owns the shared Auth Broker target, with reusable provider adapters and
opaque CredentialRef values. Plugins declare auth profile/scopes/risk/readback;
only trusted broker/transport code resolves raw secrets for required protocol I/O.
Native/server vaults contain secrets; durable state contains references and lifecycle
metadata. Provider/account/tenant/audience boundaries are not erased by reuse.
Ask for minimum initial scopes; subsequent upgrades require appropriate owner
consent and OSCAR permission checks. OAuth consent never overrides Personal Policy,
consequential-action confirmation or local deterministic safety.

The Decision / Epistemic Controller applies these hard deterministic rules.
Laya/Jev or another replaceable classification provider cannot grant permission,
change source authority or waive confirmation. `oscar/jev.py` is historical naming
for OSCAR-owned logic, not an external authority dependency.

GitHub is the first real authentication proof, accepted by the owner in run
`oauth-gate-b-20261004-234817`. Registered device flow, exactly `user:email`, private
reads, restart and local disconnect passed. This is not a fully generalized Auth Broker. Local disconnect deletes a local secret;
provider revocation remains UNKNOWN/PENDING owner action until independent provider
evidence confirms it. See [connector/auth design](CONNECTOR-FABRIC.md).

## Cloud coordinator security

The cloud coordinator is replaceable infrastructure, not a root of unlimited authority.
[DEPLOYMENT.md](DEPLOYMENT.md) separates the Oracle stateful Core candidate from
Vercel bounded Python API/web/relay functions. Neither is deployed in this pass;
the future Home Node cannot bypass Core permissions or local Edge safety.

- provider admin credentials stay out of low-trust nodes;
- cloud adapters expose only scoped OSCAR contracts;
- persistent state is encrypted appropriately;
- secrets/private memory are not replicated to every node by default;
- free-tier deployment must not weaken security simply to avoid cost;
- BYOC deployments use least-privilege cloud IAM/service credentials;
- provider outage/deletion must leave local safety and permitted local capability intact.

## Voice Match threat model

Speaker verification can be attacked using recordings, synthetic speech, replay and noise.

- expose confidence;
- use liveness/context signals where feasible;
- rate-limit repeated failed attempts;
- require stronger factors for critical actions;
- voice alone cannot disable fundamental safety.

## Voice Map privacy

Voice Map profiles/embeddings are sensitive biometric-like data.

- prefer local processing/storage where practical;
- encrypt retained profiles appropriately;
- never commit/export to source control or ordinary logs;
- do not silently name weak ambient matches;
- support deletion/re-enrollment;
- preserve confidence/source provenance;
- never treat recognition as permission;
- exclude OSCAR's own TTS from learning.

## Sentry and continuity-capture privacy

Sentry's persistent awareness and optional recording/capture modes are separate.

### Awareness-only baseline

- local wake/VAD first;
- local speaker/sound/event processing where practical;
- no default continuous cloud microphone stream;
- compact events preferred over raw-media retention.

### Optional Context Capture / Daily Journal

If explicitly enabled, OSCAR may process selected calls/messages/mail/meetings/in-person conversations where technically and legally permitted.

Required controls:

- per-source enablement;
- visible current capture state;
- consent/disclosure policy where required;
- privacy zones/time windows;
- participant/person exclusions;
- fast pause/stop;
- raw audio retention policy;
- transcript retention policy;
- summary/memory retention policy;
- export/delete/forget controls;
- encrypted storage/access control;
- provenance for retained records.

Keep separate:

```text
wake/VAD
Voice Map recognition
sound classification
activated STT
ambient/context STT
raw audio retention
transcript retention
summary retention
memory extraction
```

A generic microphone permission never silently grants all of the above.

### Legal/consent boundary

Recording consent requirements differ by jurisdiction/channel/participant. OSCAR must not be designed around covert recording. Where a source cannot be legitimately captured, the capability remains unavailable.

Deletion claims must reflect actual local/cloud/backups/connected-source behavior; do not say `deleted everywhere` without evidence.

## Chief-of-Staff schedule authority

Calendar/task/schedule automation can become consequential even when individual mutations look harmless.

- reading calendar/free-busy does not grant modification authority;
- `fixed` vs `flexible` schedule classes come from explicit user policy/current source semantics, not model guesswork;
- automatic replanning requires explicit Personal Policy and scoped write permission;
- external communication triggered by a schedule change can require an additional communication permission;
- changed calendar/task state should be independently read back where practical;
- current weather/location/notification evidence may inform planning but never independently grant write/send authority.

## Native Model Router security

- provider credentials are scoped/stored appropriately;
- routing/fallback cannot bypass data-sharing/privacy policy;
- provider failure must not silently widen disclosure;
- models receive reasoning input, not authority;
- model outputs remain reported/inferred until verified where required;
- local/private mode cannot silently fall back to cloud.

## Secrets

- keep provider master keys off low-trust nodes where practical;
- prefer scoped OSCAR-issued tokens for nodes;
- never commit secrets;
- redact credentials from logs;
- separate development/production credentials;
- revoke one node without rebuilding the Grid;
- never expose raw provider keys in UI, telemetry or prompt artifacts.

## PC Worker

A machine node can be extremely powerful.

Controls:

- explicit pairing;
- advertised capabilities rather than assumed unrestricted control;
- filesystem/terminal/computer-use/app scopes;
- visible active task state;
- bounded autonomy;
- approval for sensitive operations;
- audit events for mutations;
- task lease expiry/reclaim;
- remote shutdown only when a real allowed capability exists.

Delegating to Codex/another specialist never bypasses OSCAR permission policy.

Trusted-host execution is not a sandbox merely because cwd/path checks exist.

### Windows local-alpha boundary

The local Worker requires explicit `machine:host` permission and trusted-host
opt-in. It uses a scoped local workspace, native executable allowlist, filtered
environment, timeout/output bounds, reparse-aware files and Win32 Job Object tree
lifetime. Process creation is suspended until job assignment succeeds. No shell
shim, fake POSIX process group or silent job-assignment fallback is used.

These controls **are not a sandbox**. An approved interpreter/agent/Git process
still runs as the laptop user, can access that user's other files/network and may
execute code from the repository. Hostile repositories, concurrent hostile local
writers, hard links, executable replacement, Git internal metadata/config/filter
attacks and malicious specialists are not isolated. Path checks do not restrict
subprocess file access. Git metadata root redirection is rejected; this does not
certify every Git config/object/file as safe. Local SQLite/OS credentials are not
claimed protected against the host account. Job Objects provide process lifetime,
not permissions or containment. No restricted token/AppContainer/container boundary
was installed or claimed. Use only explicitly trusted owner objectives/workspaces.

The Codex acceptance used explicit trusted-host execution (`danger-full-access`)
on a disposable fixture after the laptop's workspace-write invocation behaved as
read-only and produced no mutation. That failure was independently rejected.
Codex's own existing authentication home is supplied only for that capability;
OSCAR provider environment credentials are excluded. Model testimony never verifies
the mutation. Private specialist transcripts/auth/config stay outside Git evidence.

Reference authority still shares coordinator SQLite and loopback HTTP. Completed
results deduplicate; an abrupt mutation with missing result blocks replay even if
the file appears changed. An owner must independently inspect/resolve uncertainty;
clearing started dedup rows is not an automatic recovery strategy. Forget removes
live OSCAR records; SQLite/WAL/backups and physical secure erasure remain unverified.

## Persona security boundary

Persona may change humor, candor, warmth, formality, brevity, initiative, pushback and voice/motion style.

It may **not** reduce factual integrity, suppress required risk/consent disclosure, bypass confirmation, change permissions, turn blocked/failure into success or joke away safety-critical information.

## Models and unstructured output

```text
model recommendation
      ↓
OSCAR typed action proposal
      ↓
policy / permission check
      ↓
optional strong user approval
      ↓
execution
      ↓
verified result
```

Unstructured model text must not become arbitrary shell/GPIO/calendar/message commands directly.

## Physical safety

Keep outside cloud/LLM control loops:

- emergency stop;
- over-current/thermal cutoffs;
- motor limits/interlocks;
- battery protection;
- relay safety conditions;
- watchdog behavior.

A model may request a safe high-level action; the local controller validates execution.

## Audit model

Consequential events should record only what is necessary:

```text
timestamp
correlation/task ID
requesting user/surface
identity evidence if relevant
OSCAR decision/path
capability/model/tool
permission + Personal Policy decision
target executor/node
requested action
execution state
verification/evidence
retry/error state
```

Capture/communication audit should reference content/artifacts rather than copy sensitive raw content into general logs.

## Recovery

OSCAR exposes partial state rather than inventing completion.

```text
Codex changed files       ✓
tests passed              ✓
visual verification       blocked — desktop disconnected
```

The task remains partial/recoverable.

## Invariants

1. No node is trusted merely because it is connected.
2. OSCAR Mobile is owner control, not an override for hardware safety.
3. Cloud is replaceable and least-privileged.
4. Persistent Sentry awareness does not silently enable recording.
5. Recording/capture is explicit, source-specific and retention-controlled.
6. Persona cannot weaken truth/safety/authority.
7. Remote-control claims require a real currently available capability.
8. Completion claims remain evidence-backed.
9. Android assistant/overlay/notification permissions are independent capabilities.
10. Notification visibility is not unrestricted app access.
11. Perception, retention and action are independently controlled.
12. Chief-of-Staff schedule/communication mutations require explicit authority and verification.

## Gate B local completion candidate — 2026-10-04

Native Windows Credential Manager is exercised for synthetic write/read/rotation/expiry/process-reopen/delete. Known runtime secret material is rejected from durable objectives/policy/archive and remains filtered from child environment. Credential Manager does not isolate secrets from the same Windows account or malicious host code. Browser contexts are nonpersistent and origin-scoped; screenshots/downloads are bounded exclusive artifacts, not sandbox claims. UIA uses observed IDs/PID/executable, fixed patterns and bounded input; UIPI/elevation is not bypassed. Notepad broker activation may reuse an existing user process. Neo4j acceptance is an unauthenticated loopback synthetic fixture: NEVER load private history into it. Native vault and SQLite commits cannot be one atomic transaction. Durable enrollment/disconnect intents now precede native mutations, and restart reconciles known references. Ambiguous external exchanges never replay; missing/expired credentials require reauthorization. Local disconnect exposes remote revocation UNKNOWN/owner-action-required. Raw device/access tokens remain exclusively in the native vault. See [crash boundaries and scoped cleanup](GATE-B-HARDENING.md).

Verified local acceptance includes the previously documented typed PowerShell, Notepad/UIA, browser, owner-control, credentials and memory cases. The later owner physical and OAuth runs are accepted in the completion ledger. Slice 05/06 are COMPLETE; Gate B PASS. Remote revocation remains UNKNOWN_OWNER_ACTION_REQUIRED; no private write was authorized. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).


Browser source loading is anchored to the trusted OSCAR package with isolated Python
imports; the artifact cwd remains under MachineScope. Preflight exercises that same
worker and closes an owned headless Chromium process tree. Neither package anchoring
nor cwd scope is a sandbox. Failed browser operations retain only bounded allowlisted
categories, exception classes, exit codes and byte counts, never arbitrary page, URL,
cookie, credential or exception text. See [the focused repair](GATE-B-HARDENING.md).


The owner's final physical/manual machine acceptance PASSED in run
`manual-gate-b-20261004-200734`; desktop/local/public browser phases are VERIFIED.
The [accepted GitHub OAuth/federation path](GATE-B-OAUTH-ACCEPTANCE.md) uses
the existing native vault, opaque references and Connector Fabric; private email
addresses remain transient. The controlled synthetic past count remains RECALLED;
current provider count facts remain REPORTED, with separate source/temporal provenance.
Owner run `oauth-gate-b-20261004-234817` passed real private OAuth and controlled
federation. Slice 06 COMPLETE; Gate B PASS. Remote revocation remains
`UNKNOWN_OWNER_ACTION_REQUIRED`. See [final acceptance](GATE-B-COMPLETION.md).

Full-suite verification exposed asynchronous `KILL_ON_JOB_CLOSE` teardown: the
browser timeout returned before an owned descendant released its artifact cwd.
Job shutdown now explicitly terminates only that job, queries its bounded process
list, rechecks job membership to reject PID reuse and waits on owned process handles
for at most three seconds. Handles close even on drain failure; unrelated owner
processes are never terminated by PID. See Microsoft's
[Job Objects contract](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

## Slice 07 Edge boundary

See [Edge safety/security](EDGE.md) and [owner acceptance](EDGE-HARDWARE-ACCEPTANCE.md).
Physical requests require Grid scope, owner grant, PersonalPolicy and explicit
mutation confirmation. One-day per-node sessions are locally provisioned;
outbound HTTPS validates the owner CA and rejects redirects. UART CRC is
integrity, not authentication. This profile is a physically controlled,
low-energy LED fixture. Local stop latch/safe LOW outrank Core authority.
No remote stop-clear, arbitrary GPIO, dangerous actuator or OTA capability.
Secure boot/NVS encryption/eFuse commissioning is unverified and requires an
owner-reviewed board plan. Never publish ignored NVS CSV/bin, session stores,
Wi-Fi passwords or TLS keys. Physical results remain pending.

## Owner scope decision — 2026-10-05

Slice 07: **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**.
**PHYSICAL EDGE ACCEPTANCE DEFERRED BY OWNER** — `DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`.
Protocol, firmware, Grid integration, ESP32/Pico cross-builds and deterministic
safety contracts in simulation are accepted for continuation. Historical
simulator evidence remains **SIMULATED**. No physical GPIO, watchdog, UART,
E-stop or ESP32/Pico silicon PASS is claimed. Gate C remains **PARTIAL**.

Return to real ESP32/Pico acceptance during Slice 15 physical/device expansion
and/or Slice 16 reliability/security hardening. Physical failure, loss/recovery,
watchdog and safety/reflex verification remain mandatory before Slice 17
Unified Alpha can PASS. The hardware acceptance guide is preserved.
The 2026-10-05 scope authorized Slice 08. The 2026-10-06 owner decision additionally
authorizes Slice 09 software after Slice 08 integration; Slice 10, deployment and
Galaxy Tab Home Node remain outside this work.

## Slice 08 owner closure scope — 2026-10-06

Owner-authorized closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
This is not a physical PASS. Gate C remains **PARTIAL**.
Slice 08 PR #14 integrated after green exact-head CI. Accepted main/work:
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Historical reference research baseline:
`e8ac8f8bca1cb0cb7909523ac6af906ee289366f`.
Existing owner harnesses remain mandatory inputs to later consolidated acceptance.
Microphone, real-room AEC/barge-in/self-wake, owner Match/Map calibration, playback,
Android voice and naturalness remain NOT RUN. Windows reference evidence never
implies Android acceptance. See [Voice Core](VOICE-CORE.md) and
[consolidated Gate C acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 OSCAR Mobile software may begin after clean Slice 08 integration; Slice 09 must
remain a draft and stop before owner/device acceptance. Slice 10, deployment and
Galaxy Tab Home Node are not authorized. Physical Edge remains
`DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`, mandatory before Slice 17 PASS.


## Post-alpha evolution direction

Future Operating Logs are a distinct owner-controlled observability data class.
They should prefer structured metadata about model/tool/plugin/capability/Worker
calls, timing, routing, retries, failures and verification rather than raw content.

Security/privacy rules:

- do not log secrets or credentials;
- conversation/capture data and operating telemetry use separate controls;
- telemetry does not silently become training data;
- promotion into training/evaluation data requires explicit owner authorization,
  minimization/redaction, provenance and a removal/retention policy;
- external model outputs may be used for training only when terms, licensing and
  policy permit.

See [Post-Alpha Evolution](POST-ALPHA-EVOLUTION.md).

## Current Slice 09 — 2026-10-06

Slice 08 PR #14 merged; accepted main/work baseline
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Slice 08 is
**COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**; physical voice is
`DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`, never physical PASS.
OSCAR Mobile Kotlin/Compose rebuild is on `club-c/slice-09-sunday`, draft PR #15
into `work`, **PARTIAL / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**. Core/loopback,
Gradle/JVM/emulated evidence is separate from actual phone/OEM acceptance.
See [OSCAR Mobile foundation](MOBILE-FOUNDATION.md) for implementation, limits and the next owner boundary.
Slice 09 must not merge in this run. Gate C remains PARTIAL. Slice 10, deployment
and Home Node are not started. Post-alpha Operating Logs, specialist-model training
and home-server migration remain documented future work, not implemented.
