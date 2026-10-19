# Connected Grid protocol 2

Implementation contract for Group 4/D2 and the connected native foundations.
Core, Runtime, Grid, Policy, Store and Event Archive remain authoritative. HTTPS
bounded outbound polling reuses the D1 private service and Caddy TLS boundary;
Windows, Android and Linux need no inbound device port or broker. At most one
action is returned per poll, no uncertain mutation is automatically redelivered.

## Enrollment

The device generates an RSA 2048–4096 key; public key is base64 DER (PKCS1 or
SPKI), signatures RSA-PSS SHA256, MGF1 SHA256, salt length 32. Transport keys and
user-confirmation keys are independent. Export only the public key.

Trusted offline operator creates an invitation with `python -m oscar.remote_grid
invite --config CONFIG --node NODE --role desktop|mobile --installation ID
--public-key-file PUBLIC_KEY_FILE --output PRIVATE_INVITATION --retain`.
For Desktop add `--workspace ID`; actual absolute workspace stays local.
Optional `--owner-key-file PUBLIC_KEY_FILE` binds an existing native owner
confirmation key. No standing Secure/Full Access is granted. Operator validates
the device fingerprint and chooses role, workspace and retention explicitly.
This is separate from D1 diagnostic enrollment. Core must be stopped for the
offline authority operation. A fresh invitation is required after revocation,
lost credential rotation response or explicit recovery.

Invitation JSON: `version:2,core_id,node_id,role,installation_id,workspace,
public_key,challenge_id,signing_payload,expires_at_ms`.
`signing_payload` is base64 opaque bytes. POST `/v2/grid/enroll` JSON:
`{version:2,challenge_id,signature}` with signature over decoded signing_payload.
Invitation is pre-bound to the exact device key, role, installation and scopes;
five-minute expiry, single use. Response session JSON:
`{version:2,core_id,node_id,session_id,token,expires_at_ms,scopes}`.
Native client adds `url` locally, validates expected core_id and stores securely.

## Authenticated requests

POST `/v2/grid/request` body UTF8 JSON, <=32768 bytes:
`{version:2,operation,request_id,payload}`. Request IDs are UUID strings or
32-character hex IDs. Response <=262144 bytes; errors are categories only.
No redirects, query strings or credentials in URLs. Production clients require
trusted HTTPS; loopback HTTP is limited to existing debug/reference tests.

Headers: `Authorization: Bearer TOKEN`, `X-Oscar-Node`, `X-Oscar-Session`,
`X-Oscar-Nonce` (32 hex), `X-Oscar-Time` (integer epoch milliseconds),
`X-Oscar-Signature` (base64). Signature covers the UTF8 bytes, no final newline:

```text
OSCAR-GRID-2
POST
/v2/grid/request
NODE
SESSION
NONCE
TIME
SHA256_HEX_OF_EXACT_BODY_BYTES
```

Every request rechecks Grid session, pinned device key, scope, timestamp +/-60s,
single-use nonce and bounded rate admission. Session rotation fences old
sessions immediately; a lost response requires re-enrollment, never fallback.

## Client operations

- `snapshot {cursor:0,archive_generation:PREVIOUS_GENERATION}`: `version,core_id,node_id,relationship_id,nodes,tasks,
  events,cursor,reset,archive_generation,providers,observed_at_ms` and optional
  `presence`. Cursor is monotonically ordered
  archive sequence; reset instructs cache replacement after forget/generation
  changes. Clients always replace current task/node projections. No cache grants
  authority. Only explicitly enrolled relationship-sharing/retention grants read
  archive. Without archive sharing, nodes/status remain available but events and
  retained task details/results are redacted. Snapshot foreground polling every 5 seconds; bounded exponential
  backoff with jitter on failure, stop on revoked/expired credentials.
- `presence {}` returns the existing canonical Core Presence snapshot with a v2
  observation field: `{version:1,visible,expression,observed_at_ms}`. The Core
  samples `observed_at_ms` after obtaining the canonical snapshot; the existing
  expression is unchanged. This operation and the optional snapshot field
  independently require live `presence:read` scope and Personal Policy approval.
  Denied presence is omitted from snapshot; the dedicated operation returns an
  authority denial. The existing expression source ID, publication generation,
  transition ID, event time and 30-second expiry pass through unchanged. Native
  clients validate freshness/generation and withdraw stale or missing expression.
  Remote clients anchor Core time to the authenticated server observation and
  local monotonic elapsed time, accounting for transport age rather than assuming
  synchronized device wall clocks. This mapping does not rewrite expression
  timestamps, renew expiry, or relax the canonical 250 ms future tolerance;
  connection loss and missing/stale observations withdraw private Presence.
  Clients do not invent an operational state. This grant enables no overlay,
  microphone, capture, retention or action permission.
- `inspect {task_id}`: task projection described below.
- `submit {text,kind,target,parameters,retain}`: kind is `file_read`, `file_write`,
  `addition` or `text`; target is exact Desktop node for file tasks, Core ID for
  addition/text. `parameters` is `{path}` / `{path,content}` / `{expression}` /
  `{}`. Retain must be explicit true and granted. Same request_id and same body
  returns same task; changed body conflicts. File payload is bounded to 8192
  UTF8 bytes. File reads use a separate network readback before verified state.
  Text uses existing Core model routing; missing provider remains unavailable.
- `challenge {task_id,operation:"approve"}`: existing native owner-signing shape
  `challenge_id,signing_payload,expires_at_ms,operation,description,target,
  capability,reason,consequence,policy_reason,confirmation,review,exact_request,
  scope,generation`. Claim binds node/session, exact task/action plan, capability,
  target, review digest, expiry and current authority. `complete
  {challenge_id,signature}` consumes once and starts only that task. An enrolled
  owner key and real native confirmation are required; emulator trust is labeled
  separately. Synthetic integration keys are explicitly software-only.
- `cancel {task_id}`: recheck control scope; returns projection; cancellation
  cannot undo an effect already performed. Worker checks again before mutation.
- `rotate {}` returns fresh session and revokes the old one atomically.
- `disconnect {}` withdraws liveness, preserving enrollment.
- `revoke {}` revokes this node and its sessions; logout also deletes local key
  material and credential cache. Re-enrollment requires trusted operator action.

Task projection: `task_id,state,retained_available,description,target,capability,approval_required,
review_digest,action_id,deadline_ms,result,evidence,blocker,generation,correlation_id`.
`retained_available:false` means forgotten or sharing denied: no result/evidence
or approval is exposed, and clients must not claim proof of completion from this
redacted view. Event text is a readable projection; original canonical result
and evidence remain in the Event Archive, subject to retention/forget rules.
Result uses existing Result record (REPORTED); evidence uses existing Evidence.
Only Core independent verification transitions a task to verified. Clients show
blocked, unknown, failed, revoked and offline as actual states.

## Desktop Worker operations

Worker uses the same authenticated endpoint and device session; it never opens
an inbound port. Locally configured scope/workspace and explicit capability
allowlist must agree with invitation. Only file read/write are enabled in this
bounded vertical slice; existing other Windows tools remain available locally.

- `advertise {workspace,capabilities:[Capability records]}` validates each against
  owner enrollment and known contracts. Empty capabilities withdraws them.
- `poll {}` heartbeats and returns `{delivery:null}` or `{delivery:...}`. Poll
  every 2 seconds while connected, exponential jittered backoff after failure.
- Delivery: `id,kind:"action"|"readback",node_id,session_id,task_id,action,
  lease_id,deadline_ms,workspace,review_digest,approved,parameters`.
  Action is the canonical Action record. Readback parameters contain `{path}`.
- `check {delivery_id}` returns `{authorized:true}` only for current session,
  exact target, capability advertisement, lease, task state, live deadline,
  policy, signed approval and original requester authority. Call immediately
  before side effects and during cancellable work. Failure means stop.
- `deliver {delivery_id,result}` for action: existing Result record, matching
  action/task/correlation/executor, only REPORTED. For readback: result is
  `{content:UTF8_STRING}` read independently from the actual scoped filesystem.
  Duplicate identical delivery is idempotent; conflicting delivery rejected.
  Expired, revoked or cancelled receipt never revives a task. Lost response is
  inspected through canonical task state and local execution journal.

Worker persists execution-only claims before side effects. Claimed delivery is
not replayed after process death. Core restart fences remote in-flight leases
and blocks ambiguous tasks; queued approval requires a fresh task/review. Backup
restore invalidates remote sessions and invitations. No automatic reclamation
of uncertain mutations. Missing independent readback leaves UNKNOWN/BLOCKED.

## Failure diagnostics

HTTP failures produce fixed category/count diagnostics, without request bodies,
paths, headers, credentials, node identities or exception text. Process-local
counters saturate at 2^31−1, use a fixed category set and emit at most one log per
category in 60 seconds. They reset on process restart; deployment log rotation
bounds retained diagnostics. Rejected unauthenticated traffic creates no durable
audit/nonce rows or verified-device admission entries. Trusted enrollment,
successful pairing and signed owner confirmation retain their existing canonical
audit records; sanitized HTTP diagnostics do not replace them.
