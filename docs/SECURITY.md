# Security + Permissions

OSCAR is intended to act across computers, phones, cloud services and physical hardware. Security is therefore part of the architecture, not a later hardening pass.

## Core rules

1. **Least privilege by capability.** Devices and tools receive only the permissions they need.
2. **Voice is not a password.** Speaker verification is useful for convenience and context, but high-risk actions require stronger confirmation.
3. **Safety-critical control stays local.** Emergency stop and hardware interlocks must not depend on cloud reasoning.
4. **Consequential actions are attributable.** OSCAR records what requested an action, which policy allowed it, which node executed it and the result.
5. **Edge nodes should connect outward.** Avoid exposing ESP32/Pico/home-network services directly to the Internet.
6. **Fail safe.** Loss of cloud, Latch or a worker must not create a dangerous hardware state.

## Authorization model

Actions should declare a risk/authorization class.

| Class | Examples | Typical requirement |
|---|---|---|
| Safety | emergency stop, halt actuator | local + universally reachable where safe |
| Harmless | weather, volume, read public state | configured allow |
| Personal | private calendar/memory/device context | authorized user / Voice Match where appropriate |
| Sensitive | send message, important file change, Sentry config | explicit/contextual confirmation + strong speaker match |
| Critical | financial/security/destructive actions | phone biometric/PIN or equivalent strong approval; voice alone insufficient |

Policies should be configurable per capability and per environment.

## Voice Match threat model

Speaker verification can be attacked with:

- recordings
- high-quality synthesized speech
- replay near a microphone
- environmental noise that causes false matches

Therefore:

- expose confidence scores
- use liveness/context signals where feasible
- rate-limit repeated failed identity attempts
- require stronger factors for critical actions
- never allow voice alone to disable fundamental safety protections

## Latch / networking

Preferred model:

```text
OSCAR Edge ──authenticated outbound secure session──► Latch
```

Requirements:

- device-scoped credentials
- credential rotation/revocation
- per-node identity
- encrypted transport
- short-lived session tokens where possible
- no blanket shared secret across all OSCAR nodes
- replay protection for consequential commands
- correlation IDs and idempotency for actions

## Secrets

- Keep provider master keys off low-trust nodes where practical.
- Prefer scoped tokens issued through Latch/OSCAR Core.
- Do not commit secrets to the repository.
- Redact credentials from logs.
- Separate development and production credentials.
- Support revoking one device without rebuilding the entire system.

## PC worker

A PC worker has broad power and must be treated accordingly.

Controls:

- explicit pairing
- capability advertisement rather than assumed unrestricted access
- permission boundaries for filesystem, terminal, computer use and apps
- visible active-task state
- bounded autonomous execution
- approval gates for sensitive operations
- audit events for launches/commands/file mutations

OSCAR should prefer a specialist worker such as Codex for coding, but delegation does not bypass OSCAR's permission policy.

## ChatGPT and cloud models

Models provide reasoning, not authority.

Before an external model can trigger a consequential action:

```text
model recommendation
      ↓
OSCAR typed action proposal
      ↓
policy / permission check
      ↓
optional user confirmation
      ↓
execution
      ↓
verified result
```

Unstructured model text must not directly become arbitrary shell/GPIO commands.

## Physical safety

Keep the following outside the cloud control loop:

- emergency stop
- over-current cutoffs
- thermal cutoffs
- motor limits/interlocks
- battery protection
- relay safety conditions
- watchdog behavior

A cloud model may request a safe high-level action, but the local controller validates whether it can be executed.

## Sentry privacy

Default principles:

- local wake-word/VAD first
- avoid continuous cloud microphone streaming
- cameras only active according to configured modes/permissions
- event summaries preferred over permanent raw-media retention
- explicit retention controls for recordings/images/logs
- visible state when higher-observation Sentry modes are active

## Protocols / generated skills

OSCAR may create or propose routines and skills, but generated automation must include:

- declared capabilities
- permission requirements
- trigger conditions
- cancellation path
- failure behavior
- review/approval when it expands authority

A generated skill cannot grant itself permissions.

## Audit model

Consequential events should record:

```text
timestamp
event/task ID
requesting surface/user
speaker/auth result if relevant
OSCAR decision/path
model/tool used
permission decision
worker/device
requested action
result
error/retry state
```

Audit logs should avoid storing unnecessary raw private content.

## Recovery

OSCAR should detect and expose partial completion.

Example:

```text
1. Codex changed files          ✓
2. tests passed                 ✓
3. computer-use verification   ✗ worker disconnected
```

Report the incomplete state and resume safely later rather than claiming success.
