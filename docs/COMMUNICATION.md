# Communication Layer

OSCAR should be able to act as the user's communication layer across calls, meetings, messaging, dictation and follow-up work. The goal is not a separate "meeting bot" or "call bot" product. Communication is another capability surface owned by the same OSCAR identity, memory, World Model, Personal Policy and task state.

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

Sunday is the primary mobile execution surface. Desktop machine nodes can provide equivalent meeting/dictation capabilities on Windows/macOS.

## Universal Channel Gateway

OSCAR should not hard-code orchestration separately for every messaging/social/email surface.

The **Universal Channel Gateway** normalizes supported inbound/outbound communication into one event/action envelope while preserving the real limits of each channel.

Potential adapters include:

- cellular/SMS where the platform permits;
- WhatsApp;
- Telegram;
- Signal;
- Discord;
- Slack/Teams-like work channels;
- email;
- social DMs/replies;
- future communication plugins/connectors.

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

Normalization does **not** imply capability parity.

Example:

```text
telegram.message.send    available
whatsapp.call.answer     unsupported on this surface
email.thread.reply       available
signal.message.read      unavailable
```

Each adapter advertises only what is actually supported now.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Capability-first integration order

OSCAR must use the strongest legitimate integration path available for each app/service:

```text
native OS / official API
        ↓
official plugin / connector
        ↓
app automation on a paired device
        ↓
computer-use / accessibility fallback
        ↓
explicitly unsupported / ask user
```

Do not pretend an app exposes call control, audio access or message actions when the platform does not provide them. Do not bypass app security controls.

The Capability Catalog should describe what is actually available now, for example:

```text
phone.call.answer
phone.call.place
whatsapp.message.send
telegram.message.read
meeting.transcribe
meeting.notes
meeting.followup
dictation.insert_text
```

Each capability includes permission/risk metadata and the execution surface that owns it.

## AI call answering

OSCAR may answer calls on the user's behalf when explicitly allowed by Personal Policy and platform capabilities.

A typical policy may be:

```text
if unanswered for 4 rings
  and caller is not excluded by policy
  and current context permits delegation
then OSCAR may answer
```

Context can include:

- caller canonical identity/relationship;
- current calendar event;
- current task/activity;
- quiet/focus/exam/sleep state;
- location/presence where permitted;
- urgency signals;
- user-defined rules;
- disclosure/privacy requirements.

Example:

```text
Incoming call
→ identify caller/context
→ evaluate Personal Policy + permissions
→ continue ringing / silence / answer / escalate
→ if OSCAR answers: converse within scope
→ collect intent/message
→ schedule callback when permitted
→ create communication result/artifact
→ summarize to user
→ store appropriate context with provenance
```

OSCAR should answer appropriately rather than use a fixed voicemail script. If the user is unavailable until a known time and policy permits revealing availability, OSCAR may offer a callback slot without exposing private event names.

AI call handling remains attributable and permission-scoped. Where required by platform policy, user preference or applicable law, OSCAR should identify itself as an AI assistant acting on the user's behalf.

## Call policy examples

Personal Policy should support rules such as:

- "If I do not answer after four rings, answer for me."
- "Never answer family calls for me."
- "If a recruiter calls while I am in class, take a message and offer my next free callback slot."
- "Unknown callers should not be answered while I am asleep."
- "Delivery drivers can still reach me during Sleep Mode."
- "Do not reveal calendar-event titles; only say when I am free."

These rules belong in Personal Policy, not hard-coded call logic.

## Meetings

OSCAR should provide Granola-like meeting intelligence as a native capability across phone/desktop surfaces.

When authorized, it can:

```text
capture authorized audio / meeting stream
→ transcribe
→ identify speakers when feasible
→ maintain live meeting context
→ extract decisions
→ extract action items / owners / dates
→ associate notes with canonical people/projects
→ prepare concise summary
→ create follow-ups/tasks/events when permitted
→ store relevant memory with provenance
```

The meeting surface should support:

- live transcript on demand;
- concise notes while the meeting is running;
- speaker labels where reliable;
- decisions/unresolved questions;
- action-item extraction;
- links/files mentioned where accessible;
- post-meeting summary;
- follow-up drafts/actions;
- searchable history through LRA rather than a separate meeting silo.

Meeting notes/transcripts should become typed Artifacts/Results when durable handoff/search is useful.

Recording/transcription must respect user policy, participant consent requirements and platform rules.

## System-wide dictation

OSCAR should provide Wispr-Flow-like dictation across the device rather than only inside OSCAR's own UI.

Examples:

```text
"OSCAR, type this..."
"make that shorter"
"replace the last sentence"
"write this more formally"
"send it"
```

Dictation uses the best available surface:

- native text insertion/API;
- accessibility/input method;
- desktop automation;
- app-specific integration.

Modes can include:

- literal dictation;
- cleaned dictation;
- rewrite/edit;
- command mode.

The user should be able to move between speech/keyboard without creating a separate context.

## Messaging and app communication

OSCAR should be able to read, draft, send and manage messages across connected communication apps when permitted.

This includes:

- Channel Gateway adapters/structured connectors;
- phone-app actions through Sunday;
- desktop/browser apps through Workers;
- notifications/reply actions;
- voice-note handling.

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

The user should not have to manually copy a meeting decision into another OSCAR subsystem.

## Context and memory

Communication context participates in the same LRA/World Model architecture as the rest of OSCAR.

Useful durable facts may include:

- who contacted the user;
- purpose/outcome;
- commitments made;
- action items;
- preferred communication style for a person/context;
- callback/scheduling state.

Raw audio/full transcripts should have explicit retention controls. Sensitive recordings should not become durable memory merely because OSCAR can store them.

## Epistemic integrity and verification

Communication actions are consequential and must follow `docs/EPISTEMIC-INTEGRITY.md`.

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

OSCAR should clearly distinguish:

- drafted vs sent;
- send requested vs delivery confirmed;
- meeting transcription produced vs speaker labels verified;
- callback suggested vs calendar event actually created;
- call handling attempted vs successfully connected.

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
- sending a routine message may require configured permission;
- answering a call as the user requires explicit delegation policy;
- making commitments/sharing private schedule detail may require stronger constraints;
- account/security changes always require stronger confirmation.

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

Do not repeatedly retry an unavailable service or silently switch to a more privileged path.

Long-running communication responsibilities use the Durable Execution Runtime when they need persistence/recovery.

## Invariants

1. Communication belongs to one OSCAR identity/context, not separate bots.
2. Personal Policy decides user-specific behavior; platform capability decides what is technically possible.
3. Native/official integration is preferred over brittle UI automation.
4. OSCAR never fabricates support for unavailable app/platform capabilities.
5. Channel normalization does not erase per-channel limits.
6. Call/meeting/message autonomy remains permission-scoped and attributable.
7. Voice, dictation, meetings and messaging contribute to the same continuous context where policy allows.
8. Communication success claims cannot exceed verification evidence.
9. Durable communication outputs can be represented as typed Artifacts/Results.
