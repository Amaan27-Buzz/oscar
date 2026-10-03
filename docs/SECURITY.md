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
| Critical | financial/security/destructive actions | Sunday biometric/PIN or equivalent strong approval; voice alone insufficient |

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

Sunday is the preferred everyday owner-control surface for the Connection Grid.

Where supported it can:

- pause autonomous work;
- cancel tasks;
- revoke a node/session/credential;
- change Sentry/capture state;
- approve sensitive actions;
- request remote machine sleep/shutdown;
- inspect what each node is doing.

But Sunday does **not** outrank deterministic physical safety.

```text
local emergency/safety interlocks
> owner revocation / strong confirmation
> granted permissions + explicit Personal Policy
> OSCAR Executive / Workers / Persona
```

If Sunday is offline, existing authorized work may continue only within already granted scope. No other node may fabricate an owner-critical approval.

## Android / Sunday security boundary

Sunday should use legitimate platform APIs and explicit user-granted special access.

### Assistant role

If Sunday is selected as the Android assistant, treat that as one platform role—not root/system authority. Other permissions remain separate and inspectable.

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

## Cloud coordinator security

The cloud coordinator is replaceable infrastructure, not a root of unlimited authority.

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
2. Sunday is owner control, not an override for hardware safety.
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
