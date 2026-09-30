# Security + Permissions

OSCAR is intended to act across computers, phones, cloud services and physical hardware. Security is therefore part of the architecture, not a later hardening pass.

## Core rules

1. **Least privilege by capability.** Devices and tools receive only the permissions they need.
2. **Voice is not a password.** Speaker verification is useful for convenience/context, but high-risk actions require stronger confirmation.
3. **Voice Map is not authorization.** Recognizing who appears to be speaking never creates permission.
4. **Safety-critical control stays local.** Emergency stop and hardware interlocks must not depend on cloud reasoning.
5. **Consequential actions are attributable.** OSCAR records what requested an action, which policy allowed it, which node executed it and the result.
6. **Edge nodes connect outward.** Avoid exposing ESP32/Pico/home-network services directly to the Internet.
7. **Fail safe.** Loss of cloud, native transport or a worker must not create a dangerous hardware state.

## Authorization model

Actions declare a risk/authorization class.

| Class | Examples | Typical requirement |
|---|---|---|
| Safety | emergency stop, halt actuator | local + universally reachable where safe |
| Harmless | weather, volume, read public state | configured allow |
| Personal | private calendar/memory/device context | authorized user / Voice Match where appropriate |
| Sensitive | send message, important file change, Sentry config | explicit/contextual confirmation + strong identity evidence |
| Critical | financial/security/destructive actions | phone biometric/PIN or equivalent strong approval; voice alone insufficient |

Policies should be configurable per capability/environment.

## Voice Match threat model

Speaker verification can be attacked with recordings, synthesized speech, replay near a microphone and environmental noise.

Therefore:

- expose confidence scores;
- use liveness/context signals where feasible;
- rate-limit repeated failed identity attempts;
- require stronger factors for critical actions;
- never allow voice alone to disable fundamental safety protections.

## Voice Map privacy and threat model

Voice Map stores or derives speaker-recognition signals that should be treated as sensitive biometric-like data.

Rules:

- local processing/storage is preferred where practical;
- encrypt retained speaker profiles/embeddings at rest where appropriate;
- do not commit/export them into source control or ordinary logs;
- do not silently create named identities from weak ambient matches;
- canonical-person linkage requires deliberate enrollment, strong corroboration or user confirmation;
- support profile deletion/re-enrollment;
- preserve confidence/source-device metadata;
- never use Voice Map recognition itself as authorization;
- OSCAR's own TTS is excluded from Voice Map learning/identity updates.

Unknown voices remain unknown rather than being guessed.

## Native OSCAR transport / networking

The final architecture uses OSCAR-owned Transport + Capability Fabric. The separate Latch project is not a required security boundary/runtime service.

Preferred Edge model:

```text
OSCAR Edge ──authenticated outbound secure session──► OSCAR transport rendezvous
```

Requirements:

- device-scoped credentials;
- credential rotation/revocation;
- per-node identity;
- encrypted transport;
- short-lived session tokens where possible;
- no blanket shared secret across all nodes;
- replay protection for consequential commands;
- correlation IDs and idempotency;
- capability-scoped authorization at authoritative execution boundaries;
- version negotiation and rejection of incompatible/unsafe protocol states.

Useful networking/security lessons from Latch may be reused, but they must satisfy OSCAR's native contracts and tests.

## Native Model Router security

The native OSCAR Model Router may hold access to several providers.

Requirements:

- provider credentials are scoped/stored appropriately;
- models never receive authority merely because they are selected;
- routing/fallback cannot bypass user/provider/privacy policy;
- fallback to a different provider must respect data-sharing constraints;
- provider failure must not silently widen disclosure or permissions;
- model outputs remain reported/inferred evidence until verified where required.

The separate SwitchRoute project is reference/prototype material, not the authoritative policy boundary.

## Secrets

- Keep provider master keys off low-trust nodes where practical.
- Prefer scoped tokens issued through OSCAR Core/native transport.
- Do not commit secrets.
- Redact credentials from logs.
- Separate development and production credentials.
- Support revoking one device without rebuilding the entire system.

## PC worker

A PC worker has broad power and must be treated accordingly.

Controls:

- explicit pairing;
- capability advertisement rather than assumed unrestricted access;
- permission boundaries for filesystem, terminal, computer use and apps;
- visible active-task state;
- bounded autonomous execution;
- approval gates for sensitive operations;
- audit events for commands/file mutations.

Delegating to Codex or another specialist never bypasses OSCAR's permission policy.

## ChatGPT and cloud models

Models provide reasoning, not authority.

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

- emergency stop;
- over-current/thermal cutoffs;
- motor limits/interlocks;
- battery protection;
- relay safety conditions;
- watchdog behavior.

A model may request a safe high-level action, but the local controller validates whether it can execute.

## Sentry privacy

Default principles:

- local wake-word/VAD first;
- local speech-presence/Voice Map/sound-event classification where practical;
- avoid continuous cloud microphone streaming;
- distinguish local acoustic awareness from transcription;
- transcription/retention requires explicit trigger/mode/policy;
- cameras active only according to configured modes/permissions;
- compact events preferred over permanent raw-media retention;
- explicit retention controls for audio/transcripts/images/logs;
- visible state when higher-observation Sentry modes are active.

The following are separate controls, not one `microphone permission`:

```text
wake/VAD locally
speaker recognition / Voice Map
sound-event classification
activated transcription
raw audio retention
transcript retention
```

## OSCAR self-voice safety

OSCAR must not authenticate, map, or respond to its own synthesized voice as if it were an external person.

Use playback reference, echo cancellation, TTS-origin tagging and timing/correlation where feasible.

Self-voice suppression must still allow real human barge-in and emergency stop.

## Protocols / generated skills

Generated automation must declare capabilities, permissions, triggers, cancellation, failure behavior and review/approval when it expands authority.

Generated automation cannot grant itself permissions.

## Audit model

Consequential events should record:

```text
timestamp
event/task ID
requesting surface/user
speaker/auth result if relevant
Voice Map evidence if relevant (without unnecessary biometric material)
OSCAR decision/path
model/tool/capability used
permission decision
worker/device
requested action
result
verification evidence/error/retry state
```

Audit logs should avoid unnecessary raw private content.

## Recovery

OSCAR should detect/expose partial completion rather than claiming success.

Example:

```text
1. Codex changed files          ✓
2. tests passed                 ✓
3. visual verification         ✗ worker disconnected
```

Report partial state and resume safely later.
