# Communication Layer

OSCAR should be able to act as the user's communication layer across calls, meetings, messaging, dictation and follow-up work. The goal is not a separate meeting/call bot product. Communication is another capability surface owned by the same OSCAR identity, memory, World Model, Personal Policy, Voice Identity and task state.

## Product rule

> Communication is a first-class OSCAR capability, not a collection of isolated integrations.

OSCAR should eventually cover, where platform capabilities and permissions allow:

- ordinary phone calls;
- WhatsApp calls/messages;
- Telegram calls/messages;
- other phone communication apps;
- Zoom, Google Meet, Teams, Discord and similar meetings;
- in-person meeting capture through an authorized microphone/device;
- system-wide dictation;
- voice notes;
- live transcription;
- structured meeting notes;
- decisions/action-item extraction;
- scheduling/follow-up;
- communication history linked to people, projects and tasks.

Sunday is the primary mobile execution surface. Desktop nodes can provide equivalent meeting/dictation capabilities.

## Universal Channel Gateway

OSCAR should not hard-code orchestration separately for every messaging/social/email surface.

The Universal Channel Gateway normalizes supported inbound/outbound communication into one event/action envelope while preserving the real limits of each channel.

Potential adapters include cellular/SMS where permitted, WhatsApp, Telegram, Signal, Discord, Slack/Teams-like channels, email, social DMs/replies and future plugins/connectors.

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
```

Normalization does not imply capability parity. Each adapter advertises only what is actually supported now.

## Capability-first integration order

```text
native OS / official API
→ official plugin / connector
→ app automation on a paired device
→ computer-use / accessibility fallback
→ explicitly unsupported / ask user
```

Do not pretend an app exposes call control, audio access or message actions when it does not.

The Capability Catalog should describe actual capabilities such as `phone.call.answer`, `whatsapp.message.send`, `meeting.transcribe`, `meeting.notes`, `dictation.insert_text`, including permission/risk metadata and execution surface.

## OSCAR Voice Identity in communication

When OSCAR speaks during calls, meetings, dictation feedback or other communication, it should use the same stable Voice Identity used elsewhere.

The underlying TTS provider may differ by platform, but the product goal is one recognizably consistent OSCAR voice.

Communication-specific speaking modes may include:

- normal conversational;
- concise representative/call mode;
- focused professional mode;
- alert/urgent clarification mode.

The voice should not silently become a different personality because a phone/meeting surface uses another provider.

Where required by platform rules, law or user preference, OSCAR should identify itself as an AI assistant acting on the user's behalf.

## AI call answering

OSCAR may answer calls on the user's behalf when explicitly allowed by Personal Policy and platform capabilities.

A typical policy may be:

```text
if unanswered for 4 rings
  and caller is not excluded by policy
  and current context permits delegation
then OSCAR may answer
```

Context can include caller canonical identity/relationship, current calendar/task state, location/presence, urgency signals, user rules and disclosure/privacy requirements.

Example:

```text
Incoming call
→ identify caller/context
→ evaluate Personal Policy + permissions
→ continue ringing / silence / answer / escalate
→ if OSCAR answers: converse within scope using OSCAR Voice Identity
→ collect intent/message
→ schedule callback when permitted
→ create communication result/artifact
→ summarize to user
→ store appropriate context with provenance
```

AI call handling remains attributable and permission-scoped.

## Call policy examples

Personal Policy should support rules such as:

- `If I do not answer after four rings, answer for me.`
- `Never answer family calls for me.`
- `If a recruiter calls while I am in class, take a message and offer my next free callback slot.`
- `Unknown callers should not be answered while I am asleep.`
- `Delivery drivers can still reach me during Sleep Mode.`
- `Do not reveal calendar-event titles; only say when I am free.`

These belong in Personal Policy, not hard-coded call logic.

## Meetings

OSCAR should provide meeting intelligence as a native capability across phone/desktop surfaces.

When authorized:

```text
capture authorized audio / meeting stream
→ transcribe
→ diarize speakers
→ use Voice Map signals where available
→ maintain live meeting context
→ extract decisions/actions
→ associate notes with canonical people/projects
→ prepare summary
→ create follow-ups/tasks/events when permitted
→ store relevant memory with provenance
```

### Voice Map and speaker labels

Voice Map may improve speaker labeling when a known enrolled speaker is present, but:

- Voice Map is evidence, not certainty;
- unknown voices remain unknown;
- acoustic recognition does not grant communication authority;
- diarization and identity are separate steps;
- speaker labels should remain confidence-qualified;
- OSCAR's own TTS is excluded from speaker mapping;
- linking a speaker to a canonical person requires sufficient evidence/confirmation;
- participant consent/retention requirements still apply.

Meeting notes/transcripts should become typed Artifacts/Results when durable handoff/search is useful.

## System-wide dictation

OSCAR should provide system-wide dictation across the device rather than only inside OSCAR's own UI.

Examples:

```text
"OSCAR, type this..."
"make that shorter"
"replace the last sentence"
"write this more formally"
"send it"
```

Dictation uses the best available surface: native text insertion/API, accessibility/input method, desktop automation or app-specific integration.

Modes can include literal dictation, cleaned dictation, rewrite/edit and command mode.

The user should be able to move between speech/keyboard without creating a separate context.

## Messaging and app communication

OSCAR should be able to read, draft, send and manage messages across connected communication apps when permitted.

This includes Channel Gateway adapters/structured connectors, phone-app actions through Sunday, desktop/browser apps through Workers, notifications/reply actions and voice-note handling.

OSCAR should use canonical relationships, communication preferences and active context when deciding tone, urgency and whether to interrupt.

## Follow-up and scheduling

Communication does not end when a call/meeting/message ends.

OSCAR may, within permissions:

- create callback reminders;
- find calendar availability;
- schedule meetings;
- draft/send follow-ups;
- update project/task context;
- record commitments;
- notify the user of unresolved items.

## Context and memory

Communication context participates in the same LRA/World Model architecture as the rest of OSCAR.

Useful durable facts may include who contacted the user, purpose/outcome, commitments, action items, preferred communication style and callback/scheduling state.

Raw audio/full transcripts have explicit retention controls. Sensitive recordings do not become durable memory merely because OSCAR can store them.

Voice Map embeddings/profiles are separately sensitive and follow `docs/VOICE-SENTRY.md` retention/privacy rules.

## Always-on acoustic awareness vs communication capture

Sentry's local acoustic plane and deliberate communication recording are different modes.

```text
Sentry acoustic awareness
= local wake / VAD / speaker-event / sound-event signals

Communication capture
= authorized transcription/recording for a call, meeting, voice note or explicit request
```

The existence of Sentry voice awareness must never silently enable full-time meeting/room transcription.

## Epistemic integrity and verification

Communication actions follow `docs/EPISTEMIC-INTEGRITY.md`.

Examples:

```text
send API reports success
→ REPORTED
→ query message/thread state when possible
→ VERIFIED / partially_verified / unknown
```

```text
call Worker says "message taken"
→ preserve transcript/result evidence
→ do not claim a callback was scheduled unless calendar/source state confirms it
```

OSCAR distinguishes drafted vs sent, send requested vs delivery confirmed, transcript produced vs speaker identity verified, callback suggested vs event created, and call attempt vs successful connection.

## Artifact / Result Model

Communication outputs can be first-class artifacts:

- call summary/transcript;
- meeting notes/transcript;
- follow-up draft;
- sent-message reference;
- scheduling result;
- media/voice-note reference.

Artifacts preserve source/channel IDs, canonical participants, producer, timestamps, provenance and verification state where useful.

## Security and authorization

Communication actions need clear authority.

Examples:

- reading a notification may be low risk;
- sending routine messages may require configured permission;
- answering a call as the user requires explicit delegation policy;
- making commitments/sharing private schedule details may require stronger constraints;
- account/security changes require stronger confirmation.

Voice Match may be one identity signal. Voice Map alone is never authorization.

OSCAR's permission layer is authoritative. Personal preferences may narrow authority but cannot grant permissions that do not already exist.

## Failure handling

OSCAR resolves routine recoverable problems itself when safe:

```text
app unavailable
→ choose another equivalent authorized surface if available

message format rejected
→ repair payload
→ bounded retry

login expired / passkey required
→ ask user for minimum needed intervention
```

Do not repeatedly retry unavailable services or silently switch to a more privileged path.

Long-running communication responsibilities use Durable Execution Runtime when persistence/recovery matters.

## Invariants

1. Communication belongs to one OSCAR identity/context, not separate bots.
2. Personal Policy decides user-specific behavior; platform capability decides what is technically possible.
3. Native/official integration is preferred over brittle UI automation.
4. OSCAR never fabricates support for unavailable app/platform capabilities.
5. Channel normalization does not erase per-channel limits.
6. Call/meeting/message autonomy remains permission-scoped and attributable.
7. Voice, dictation, meetings and messaging contribute to the same continuous context where policy allows.
8. Communication success claims cannot exceed verification evidence.
9. Durable communication outputs can be typed Artifacts/Results.
10. Voice Map can assist speaker context but never creates authority.
11. OSCAR's own synthesized voice is excluded from speaker identification/diarization learning.
12. Sentry's always-on acoustic awareness does not silently enable continuous communication transcription/recording.
