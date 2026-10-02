# Communication Layer

OSCAR should act as the user's communication layer across calls, meetings, messaging, dictation, follow-up and optional continuity capture. Communication is one capability family owned by the same OSCAR identity, memory, World Model, Personal Policy, Persona, Voice Identity and task state.

## Product rule

> Communication is a first-class OSCAR capability, not a collection of isolated bots or integrations.

Where platform capabilities and permissions allow, OSCAR may cover:

- ordinary phone calls;
- WhatsApp/Telegram/other app calls and messages;
- SMS/text;
- email;
- Zoom/Meet/Teams/Discord-style meetings;
- in-person meeting/conversation capture through authorized microphones;
- system-wide dictation;
- voice notes;
- live transcription;
- structured notes/decisions/action items;
- scheduling/follow-up;
- communication history linked to people/projects/tasks;
- optional Sentry Context Capture / Daily Journal continuity.

Sunday is the primary mobile execution/control surface. Desktop and other nodes can provide equivalent capabilities where technically supported.

## Universal Channel Gateway

Supported communication enters OSCAR through one normalized event/action envelope while preserving channel-specific limits.

Potential adapters include cellular/SMS where permitted, WhatsApp, Telegram, Signal, Discord, Slack/Teams-like channels, email, social DMs/replies and future connectors.

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
→ authorized device automation
→ computer-use / accessibility fallback
→ explicitly unsupported / ask
```

Do not pretend an app exposes call control/audio/message capability when it does not.

## Persona in communication

Persona affects tone and presentation but never permission or truth.

Examples:

- ordinary personal chat may use the user's configured humor/warmth;
- university/professional calls can trigger high formality and low humor;
- security/Sentry events suppress inappropriate playfulness;
- representative/call mode stays concise and professional.

See `docs/PERSONA.md`.

## OSCAR Voice Identity

When OSCAR speaks during calls/meetings/dictation it should preserve the same recognizable Voice Identity used elsewhere. Persona can select speaking style/mode without silently changing OSCAR into another voice.

Where law/platform/policy requires it, OSCAR should identify itself as an AI assistant acting for the user.

## AI call answering

OSCAR may answer calls on the user's behalf when Personal Policy and platform capability permit it.

Example policy:

```text
if unanswered for 4 rings
  and caller is not excluded
  and context permits delegation
then OSCAR may answer
```

Typical flow:

```text
incoming call
→ identify caller/context where possible
→ evaluate permission + Personal Policy
→ continue ringing / silence / answer / escalate
→ if answering: speak within scope
→ collect message/intent
→ optional callback/schedule action
→ create communication result/artifact
→ verify consequential follow-up where possible
→ summarize to user
```

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

OSCAR should provide dictation outside its own UI.

Examples:

```text
"OSCAR, type this..."
"make that shorter"
"replace the last sentence"
"write this more formally"
"send it"
```

Modes may include literal dictation, cleaned dictation, rewrite/edit and command mode. Voice/keyboard remain one context.

## Messaging and email

When permitted, OSCAR may read, draft, send, search and manage communication through structured adapters or authorized device/browser/desktop capabilities.

Current platform state remains authoritative. A notification may expose less capability/content than the underlying app; OSCAR must not infer hidden access.

## Optional daily continuity capture

Sentry may be configured to keep a cross-channel record of the user's day.

This can include, where legitimately available:

- calls and call summaries/transcripts;
- messages/SMS;
- email;
- meetings;
- voice notes;
- in-person conversations;
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

### Source-specific capability

- Phone call metadata and call audio are different capabilities.
- WhatsApp/Telegram message access and call-audio access are different capabilities.
- Email/text can often be represented directly as source records instead of audio.
- In-person conversations require authorized microphones and consent/retention policy.
- Unsupported capture remains unsupported.

## Daily Journal artifact

When enabled, OSCAR may create a daily continuity artifact such as:

```text
2026-10-01
09:20  call — recruiter — callback requested
11:05  meeting — project review — 3 actions
14:40  in-person conversation — unknown/unenrolled speaker — summary retained
17:10  email — university — deadline changed
```

The default journal should favor concise, searchable outcomes over permanent raw-media storage.

Raw audio, transcript, summary and extracted memory each have independent retention controls.

## Consent / privacy

Recording/transcription rules vary by jurisdiction and channel.

OSCAR should support:

- explicit per-source capture settings;
- clear capture state;
- consent/disclosure rules where required;
- person/place/time exclusions;
- pause/stop controls;
- delete/forget controls;
- configurable raw/transcript/summary retention;
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
- unresolved-item notifications.

Each consequential mutation follows Action Ledger + verification rules.

## Context and memory

Communication participates in LRA and World Model.

Useful durable information can include who contacted the user, purpose/outcome, commitments, action items, preferred communication style and pending follow-up.

A full transcript is not automatically durable memory. Retention policy decides what survives.

## Sentry awareness vs capture

```text
Sentry awareness
= persistent local events/presence/context

Communication capture
= authorized content/transcript/recording for specific sources

Daily Journal
= explicit durable cross-source continuity record
```

These remain separate modes even though they can cooperate.

## Epistemic integrity

Examples:

```text
send API reports success
→ REPORTED
→ inspect thread/message state where possible
→ VERIFIED / partially_verified / unknown
```

```text
call Worker says "message taken"
→ preserve transcript/result evidence
→ do not claim callback scheduled unless calendar/source confirms it
```

OSCAR distinguishes drafted vs sent, attempt vs connection, transcript vs verified speaker identity, and suggestion vs actual follow-up mutation.

## Artifact / Result Model

Possible communication artifacts:

- call summary/transcript;
- meeting notes/transcript;
- Daily Journal/day summary;
- follow-up draft;
- sent-message reference;
- scheduling result;
- voice-note/media reference.

Artifacts preserve channel/source IDs, participants, producer, timestamps, provenance and verification state where useful.

## Security / authority

- reading current communication requires granted access;
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

payload rejected
→ repair + bounded retry

auth expired / strong user confirmation required
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

## Club B connector foundation

Structured Gmail/Graph mail, Calendar and Slack operations now have native
connector manifests/adapters through the existing catalog and permission ledger.
Sending is external communication; reads do not grant write authority. OAuth/
service account authentication remains unverified in this cloud run. Bodies and
results are active task context, not default durable communication capture.
Gmail recipient/header read-back and deployed provider push subscriptions remain
PARTIAL. See [CONNECTOR-FABRIC.md](CONNECTOR-FABRIC.md).
