# Communication Layer

OSCAR should act as the user's communication layer across calls, meetings, messaging, notifications, dictation, follow-up and optional continuity capture. Communication is one capability family owned by the same OSCAR identity, World Model, Personal Policy, Persona, Voice Identity and task state.

## Product rule

> Communication is a first-class OSCAR capability, not a collection of isolated bots or integrations.

Where platform capability and permission allow, OSCAR may cover:

- ordinary phone calls;
- WhatsApp/Telegram/other app calls and messages;
- SMS/text;
- email;
- Android notifications as a current event source;
- Zoom/Meet/Teams/Discord-style meetings;
- in-person meeting/conversation capture through authorized microphones;
- system-wide dictation;
- voice notes;
- live transcription;
- structured notes/decisions/action items;
- scheduling/follow-up;
- communication history linked to people/projects/tasks;
- optional Sentry Context Capture / Daily Journal continuity.

OSCAR Mobile is the primary mobile execution/control surface. Desktop and other nodes can provide equivalent capabilities where technically supported.

## Executable mail and calendar subset

The existing Desktop request input and authenticated Cloud Grid text request path
accept bounded explicit Google/Microsoft mail and calendar requests. They compile
into existing account-bound Connector Fabric capabilities and canonical Runtime
tasks. Ask uses the existing signed native exact-parameter review. Supported forms,
independent readback checks, scope and retention boundaries, and synthetic HTTP
acceptance are documented in
[communication integration](development/SOFTWARE-COMMUNICATION-INTEGRATION.md).
Real account commissioning and recipient delivery are not established by that evidence.

## Universal Channel Gateway

Supported communication enters OSCAR through one normalized event/action envelope while preserving channel-specific limits.

A normalized event can include:

```text
channel_id
account_id
conversation/thread_id
canonical participant/entity IDs
sender / recipients
direction
event type
text/transcript/media references
timestamps
reply/action capabilities
permission/risk metadata
source-specific IDs
capture/retention policy refs
```

Normalization does not imply capability parity.

## Integration order

```text
native OS / official API
→ official plugin / connector
→ authorized device automation / notification action
→ computer-use / accessibility fallback
→ explicitly unsupported / ask
```

Do not pretend an app exposes call control/audio/message capability when it does not.

## Android notification awareness

With explicit notification-listener access, OSCAR Mobile may treat Android notification events/content as current communication evidence.

This can support:

- `what did I miss?` summaries;
- urgency/importance triage;
- grouping by person/project/source;
- extracting commitments or changed deadlines;
- detecting a changed meeting or delivery state;
- deciding whether to interrupt during focus;
- presenting a legitimate reply action where Android exposes one.

Critical boundary:

```text
notification visibility
≠ unrestricted app data access
≠ durable retention permission
≠ reply/send authority
```

A WhatsApp notification is evidence of what Android exposed in that notification, not proof OSCAR can browse arbitrary WhatsApp history or control WhatsApp calls.

Source/app/person exclusions are first-class. Banking, OTP, password/security-code and similar sensitive content should not become durable memory by default.

## Notification replies

If an existing notification exposes a legitimate reply action/Android `RemoteInput`, OSCAR may draft or send through that action according to granted permission and Personal Policy.

If no reply action exists:

```text
official connector/API available → use it
otherwise authorized device/computer capability exists → use that
otherwise → direct reply unavailable / ask
```

Do not invent a writable channel from notification read access.

Drafted, send-attempted, accepted-by-API and independently observed sent/delivered are different evidence states.

## Persona in communication

Persona affects tone and presentation but never permission or truth.

Examples:

- ordinary personal chat may use configured humor/warmth;
- university/professional calls can trigger high formality and low humor;
- security/Sentry events suppress inappropriate playfulness;
- representative/call mode stays concise and professional.

See `PERSONA.md`.

## OSCAR Voice Identity

When OSCAR speaks during calls/meetings/dictation it should preserve the same recognizable Voice Identity used elsewhere. Persona can select speaking style without silently changing OSCAR into another voice.

Where law/platform/policy requires it, OSCAR should identify itself as an AI assistant acting for the user.

## AI call answering

OSCAR may answer calls on the user's behalf only when Personal Policy and platform capability genuinely permit it.

Conceptual flow:

```text
incoming call
→ identify caller/context where possible
→ evaluate capability + permission + policy
→ continue ringing / silence / answer / escalate
→ if answering: speak within scope
→ collect message/intent
→ optional callback/schedule action
→ create communication result/artifact
→ verify consequential follow-up where possible
→ summarize to user
```

Unsupported call audio/control remains unsupported.

## Meetings and in-person conversations

When authorized:

```text
capture allowed audio/meeting stream
→ transcribe
→ diarize
→ use Voice Map evidence where available
→ maintain live context
→ extract decisions/tasks
→ associate with people/projects
→ create summary/artifact
→ perform follow-ups when permitted
→ retain according to policy
```

Voice Map improves context but remains confidence-qualified and never grants authority.

## System-wide dictation

OSCAR should provide dictation outside its own UI where platform capability exists.

Examples:

```text
"OSCAR, type this..."
"make that shorter"
"replace the last sentence"
"write this more formally"
"send it"
```

Literal dictation, cleaned dictation, rewrite/edit and command mode remain distinct enough that `send it` triggers the required communication permission/policy boundary.

## Messaging and email

When permitted, OSCAR may read, search, draft, send and manage communication through structured adapters or authorized device/browser/desktop capabilities.

Current platform state remains authoritative. A notification may expose less capability/content than the underlying app; OSCAR must not infer hidden access.

## Communication → commitments → schedule

Communication participates in the Chief-of-Staff commitment model.

Potential extracted commitments:

- meeting time changed;
- callback requested;
- assignment deadline moved;
- recruiter expects response;
- delivery requires presence;
- task promised to another person;
- travel/change affects later schedule.

Flow:

```text
message/call/email/notification evidence
→ extract candidate commitment
→ preserve source/confidence
→ verify current source when consequential
→ update World Model / task state
→ suggest or perform calendar/task mutation under Personal Policy
→ read back mutation where practical
```

A model inference such as `they probably want a meeting tomorrow` does not become a verified calendar fact.

See [CHIEF-OF-STAFF.md](CHIEF-OF-STAFF.md).

## What did I miss?

OSCAR should be able to synthesize authorized communication/notification context into a concise catch-up rather than replaying a chronological feed.

Useful grouping can include:

```text
Needs action
Changed plans
Important FYI
Routine / suppressed
Unavailable sources
```

The summary must distinguish channels that were genuinely observed from channels unavailable due to permission/platform/offline state.

## Optional daily continuity capture

Sentry may be configured to keep a cross-channel record of the user's day.

Potential sources where legitimately available:

- calls and call summaries/transcripts;
- messages/SMS;
- email;
- meetings;
- voice notes;
- in-person conversations;
- selected notification-derived events;
- commitments/actions extracted from those sources.

This is not one unconditional `record everything` feature.

### Capture levels

```text
Awareness only
→ communication events can inform current context; no continuous transcript retention

Context capture
→ selected sources are indexed/transcribed/summarized; raw media minimized

Daily journal
→ explicit durable continuity timeline across selected sources
```

Raw audio, transcript, summary, notification content and extracted memory each have independent retention controls.

## Daily Journal artifact

A daily continuity artifact should favor concise, searchable outcomes over permanent raw-media storage. It may include calls, meetings, communications and schedule changes with source/provenance where useful.

## Consent / privacy

Recording/transcription rules vary by jurisdiction and channel.

OSCAR should support:

- explicit per-source capture settings;
- clear capture state;
- notification/app/person source exclusions;
- consent/disclosure rules where required;
- person/place/time exclusions;
- pause/stop controls;
- configurable raw/transcript/summary/notification retention;
- export/delete/forget controls;
- encryption/access controls;
- transparent provenance.

OSCAR must not be designed around covert recording.

## Follow-up and scheduling

Communication may create, within permission:

- callback tasks;
- calendar availability checks;
- meetings;
- follow-up drafts/sends;
- project/task updates;
- commitments;
- unresolved-item notifications;
- schedule changes caused by verified communication updates.

Each consequential mutation follows Action Ledger + verification rules.

## Context and memory

Useful durable information can include who contacted the user, purpose/outcome, commitments, action items, preferred communication style and pending follow-up.

A full transcript or notification body is not automatically durable memory. Retention policy decides what survives.

## Sentry awareness vs capture

```text
Sentry awareness
= persistent local events/presence/context

Communication awareness
= current authorized calls/messages/email/notification events

Communication capture
= authorized content/transcript/recording for selected sources

Daily Journal
= explicit durable cross-source continuity record
```

These remain separate even when they cooperate.

## Epistemic integrity

Examples:

```text
send API reports success
→ REPORTED
→ inspect thread/message state where possible
→ VERIFIED / partially_verified / unknown
```

```text
notification says meeting moved
→ current notification evidence
→ verify calendar/thread if mutation matters
→ do not silently replace calendar truth from one ambiguous notification
```

OSCAR distinguishes drafted vs sent, attempt vs connection, transcript vs verified speaker identity, suggestion vs actual follow-up mutation and notification evidence vs source-app truth.

## Artifact / Result Model

Possible communication artifacts:

- call summary/transcript;
- meeting notes/transcript;
- Daily Journal/day summary;
- follow-up draft;
- sent-message reference;
- scheduling result;
- notification-derived commitment;
- voice-note/media reference.

Artifacts preserve source IDs, participants, producer, timestamps, provenance and verification state where useful.

## Security / authority

- reading current communication requires granted access;
- notification access is its own sensitive permission;
- sending/answering requires explicit authority/Personal Policy;
- making commitments or revealing private context may require stronger confirmation;
- capture/retention changes are sensitive settings;
- Voice Match may contribute identity evidence;
- Voice Map alone never grants permission;
- Persona never expands authority.

## Failure handling

```text
adapter unavailable
→ try equivalent authorized path if one exists

notification has no reply action
→ use another legitimate integration or report unavailable

payload rejected
→ repair + bounded retry

auth expired / strong confirmation required
→ ask for minimum intervention

source does not expose call audio
→ do not fabricate transcript capture
```

Long-running communication responsibilities use Durable Execution Runtime where persistence matters.

## Invariants

1. Communication belongs to one OSCAR identity/context.
2. Platform capability decides what is technically possible.
3. Personal Policy decides user-specific behavior within permission.
4. Persona affects tone, not authority/truth.
5. Native/official integration is preferred over brittle automation.
6. Channel normalization never erases channel limits.
7. Capture is source-specific, explicit and retention-controlled.
8. Sentry awareness does not silently enable recording.
9. Voice Map supports context, never permission.
10. Communication success claims cannot exceed verification evidence.
11. Notification visibility is not unrestricted source-app access.
12. Notification observation, retention and reply authority are independent.
13. Communication-derived schedule/task changes remain source-qualified and verified where consequential.

## Club B connector foundation

Structured Gmail/Graph mail, Calendar and Slack operations have native connector manifests/adapters through the existing catalog and permission ledger. Sending is external communication; reads do not grant write authority. OAuth/service-account authentication remains unverified in the current reference. Bodies/results are active task context, not default durable communication capture.

Gmail recipient/header read-back, deployed provider push subscriptions and real private account acceptance remain PARTIAL. See [CONNECTOR-FABRIC.md](CONNECTOR-FABRIC.md).

## Historical Slice 09 checkpoint — 2026-10-06 (superseded)

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
