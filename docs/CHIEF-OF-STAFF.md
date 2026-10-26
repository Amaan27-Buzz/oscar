# Ambient Chief of Staff

The local software-completion candidate now connects explicitly authorized clock
and connected-account calendar observations to the existing World Runtime and
Sentry, with a bounded read-only day brief and conflict evidence. Native source
creation uses signed review; perception, retention and action remain independent.
[Implementation, local checks and remaining live-source gaps](development/SOFTWARE-AMBIENT-CONTEXT.md)
distinguish this candidate from real-provider, owner and operational acceptance.

The read-only day brief derives a bounded attention order from selected current task reports: Microsoft overdue/today deadlines, reported high importance, Google scheduled today/earlier, then upcoming and undated/unclear work. Completed tasks are omitted; unknown provider status remains incomplete coverage. This describes reported dates and importance, not the user's personal priorities or task effort. It does not change provider priorities, schedule blocks or send messages.

Google Tasks `due` is a scheduled day rather than a deadline, according to the [official resource contract](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks). Core emits `scheduled_date`; legacy Google-derived `due_date` reports receive the same interpretation. Date-only scheduled days require one unambiguous current selected clock timezone for comparison and never become midnight deadline timestamps. Microsoft timed deadlines need an explicit offset or recognized timezone; ambiguous/nonexistent DST times remain unknown. Unknown Windows timezone names remain reported. Calendar overlap checks use the same qualified-instant rule.

The derived attention list expires at supporting evidence expiry, the next local
date boundary or the next timed deadline, whichever comes first. Both native
clients hide it after expiry or source/account withdrawal. Task IDs retain their
source IDs; titles are resolved from the same currently authorized source report.
Only eight tasks are presented; partial provider lists, omitted tasks and unknown
due times remain explicit. This improves day-to-day coordination without claiming
general autonomous reprioritization or schedule replanning acceptance.

OSCAR should behave as a continuously available, context-aware personal Chief of Staff, not as a chatbot the user repeatedly opens and prompts.

This document owns the durable product contract for day-to-day context awareness, schedule/task coordination, interruption behavior and proactive assistance. OSCAR Mobile, World Model, Perception Fabric, Communication, Personal Policy and the Executive Planner implement different parts of this contract.

## North star

> OSCAR should understand the user's current situation from authorized live context, coordinate time/tasks/communications within policy, and surface itself only when useful.

Normal use should feel like one capable assistant already present across the user's day:

```text
observe current context
â†’ update World Model
â†’ detect conflicts / opportunities / commitments
â†’ decide whether to stay quiet, inform, suggest or act
â†’ apply permission + Personal Policy
â†’ execute through real capabilities
â†’ verify consequential changes
â†’ update schedule/tasks/context
â†’ report only what matters
```

The user should be able to say things like:

```text
"Move my afternoon around so I can finish this assignment."
"Keep the football match free and move anything flexible."
"I am running late; fix what you can and tell anyone who actually needs to know."
"Do not interrupt me while I am reading unless it is urgent."
"Summarize what I missed and update my tasks."
```

OSCAR should not require the user to manually coordinate five separate calendar, weather, task, notification and communication tools when it has the legitimate capabilities to do so.

## Live context inputs

Current context may include, where authorized and technically available:

- local time, date, timezone and daypart;
- weather and forecast;
- calendar events, free/busy state and travel buffers;
- tasks, deadlines, priorities, dependencies and overdue state;
- current/next commitments;
- location, mobility and arrival/departure signals;
- phone/device state and Connection Grid availability;
- foreground/app/activity context where legitimately exposed;
- active media sessions and playback state;
- reading/focus/presentation/driving/sleep contexts when evidence supports them;
- notifications and notification ranking;
- calls/messages/email/meeting events;
- Worker/Protocol/task state;
- Sentry/Edge/environment observations;
- explicitly retained routines/preferences and historical context.

Current truth belongs in the World Model/live-source layer. Historical patterns belong in memory. A recalled fact must not silently become current state.

## Freshness

Time, weather, calendar, task status, transport, notifications, prices, availability and similar volatile facts require current evidence when they materially affect a decision.

Conceptual authority:

```text
live authoritative API/device state
> current World Model observation
> structured OSCAR state
> recent episodic memory
> semantic/derived memory
> model prior
```

When a current source is unavailable, OSCAR should say the relevant state is stale/unknown rather than confidently planning from obsolete information.

## Chief-of-Staff schedule management

OSCAR should be able to reason over the user's day as one schedule, not isolated calendar rows.

Capabilities may include:

- create/update/cancel calendar events when permitted;
- create/update/complete tasks;
- detect overlaps and impossible travel/time assumptions;
- reserve focus/study/build blocks;
- move flexible blocks around fixed commitments;
- add realistic preparation/travel/buffer time;
- account for deadlines and task dependencies;
- account for weather/location where relevant;
- detect when a long-running Worker changes the day's plan;
- surface commitments extracted from communication;
- prepare a morning/day brief and end-of-day carry-over;
- proactively warn about schedule risk;
- propose or perform bounded replanning according to Personal Policy.

A schedule mutation is consequential. The user may grant broad policy such as `you can move my study blocks automatically`, but OSCAR must not infer blanket authority from mere calendar read access.

## Commitment model

A useful Chief of Staff tracks more than calendar events:

```text
commitment
â”œâ”€ fixed event
â”œâ”€ flexible block
â”œâ”€ task/deadline
â”œâ”€ communication follow-up
â”œâ”€ Worker/Protocol dependency
â”œâ”€ travel/preparation buffer
â””â”€ tentative/awaiting confirmation
```

Commitments should carry source, owner, deadline/time window, flexibility, priority, confidence, dependencies and mutation authority where known.

## Proactivity levels

Proactivity is not binary.

```text
observe only
â†’ update context silently

inform
â†’ concise notification/status

suggest
â†’ propose a change and wait

act within policy
â†’ make an authorized low-risk change and verify it

interrupt
â†’ actively surface only when urgency/importance justifies it
```

Personal Policy can vary these levels by person, app, project, time, place, urgency and activity.

## Attention and interruption model

OSCAR should understand whether the user is available to be interrupted.

Evidence can include:

- active video/media session;
- reading/focus app state where available;
- presentation or screen-sharing state;
- driving/navigation context;
- call/meeting state;
- sleep/quiet hours;
- explicit Focus/Do Not Disturb state;
- current task/Worker urgency;
- manual `do not disturb me` instructions.

Attention state is evidence, not mind reading. Weak signals should produce conservative behavior.

The output hierarchy is:

```text
silent context update
â†’ passive visual presence
â†’ notification
â†’ haptic
â†’ spoken interruption
â†’ urgent escalation
```

## OSCAR Mobile: Android embodiment

OSCAR Mobile should become the strongest everyday embodiment of this Chief-of-Staff behavior.

### Selected Android assistant

Where Android/device policy supports it, OSCAR Mobile should qualify for the Android assistant role and use the platform voice-interaction contracts rather than faking a default-assistant experience.

Target direction:

- `RoleManager.ROLE_ASSISTANT` where available;
- `VoiceInteractionService` / associated voice-interaction session architecture where appropriate;
- user-controlled selection of OSCAR as the phone assistant;
- lightweight always-available service behavior, with heavyweight UI/work delegated out of the persistent service path;
- explicit OEM/device acceptance because invocation gestures and assistant behavior can vary.

### OSCAR Orb overlay

OSCAR Mobile may expose a persistent OSCAR Orb using legitimate Android overlay capability when the user grants it.

The Orb is not a permanent intrusive bubble. Its presence is attention-aware:

```text
normal context
â†’ visible compact Orb

video / reading / presentation / focused content
â†’ Orb retreats toward an edge anchor or hidden hotspot

user invokes by gesture / edge target / assistant invocation / voice
â†’ Orb returns immediately

context ends
â†’ Orb may reappear naturally according to policy
```

The system may reposition or hide overlay windows, so overlay state is best-effort UI, not a correctness dependency.

### Home-screen widgets

OSCAR Mobile should support configurable Android widgets, including small/medium/large forms, for glanceable state and direct actions.

Examples:

- next commitment + travel/buffer warning;
- today progress / task focus;
- one-tap OSCAR invocation;
- current Worker/task state;
- Sentry/privacy state;
- Connection Grid health;
- compact Orb/presence widget;
- morning brief / `what needs me now?`.

Widgets remain lightweight and state-driven; they are not miniature dashboards.

### Notification awareness

With explicit notification-listener access, OSCAR Mobile may ingest notification events/content exposed by Android into the Perception Fabric.

Rules:

- permission to observe a notification does not imply permission to retain or reply;
- source/app/person exclusions are first-class;
- OTP/password/security-code classes should be excluded from durable memory by default;
- sensitive apps can be excluded entirely;
- notification content is current evidence, not proof of hidden app state;
- notification ranking/ongoing state may inform interruption decisions.

### Notification replies

When an existing notification legitimately exposes a reply action/`RemoteInput`, OSCAR may draft or send through that action according to permissions and Personal Policy.

If the app does not expose an actionable reply, OSCAR must use an official connector/API, another authorized capability, or report that direct reply is unavailable. Notification access is not unrestricted WhatsApp/app access.

### Media/activity awareness

An enabled notification listener can support access to active media-session information on Android. OSCAR Mobile may use media/playback state as one attention signal for Orb retreat and interruption policy.

`media active` does not automatically mean `never interrupt`; urgency and explicit policy still matter.

## Communication awareness

OSCAR should be able to summarize and triage calls/messages/email/notifications that it is authorized to observe.

Potential behavior:

- `what did I miss?` summary grouped by importance/person/project;
- extract commitments/tasks from messages;
- detect changed plans/deadlines;
- draft replies;
- send replies when authority exists;
- defer nonurgent messages during focus;
- surface urgent family/work/university items;
- update calendar/tasks after verified communication changes.

Deep access remains channel-specific. Notification visibility, official API access, device automation and call/audio capture are different capabilities.

## Permission lattice: perceive, retain, act

These are separate grants:

```text
CAN PERCEIVE â‰  CAN RETAIN â‰  CAN ACT
```

Examples:

```text
notification access
â‰  permission to save notification content
â‰  permission to reply

calendar read
â‰  permission to modify calendar

location access
â‰  permission to retain location history

microphone permission
â‰  permission to continuously transcribe
â‰  permission to store raw audio
```

Every implementation should preserve these boundaries in UI, policy and runtime contracts.

## Personal Policy examples

```text
"Do not interrupt me while I am watching a match unless family calls twice."
"You may move study blocks automatically, but never move class or appointments."
"Always ask before replying to my university faculty."
"You can reply to routine delivery messages without asking."
"Never retain banking notifications."
"Hide the Orb while I am reading, but keep the edge hotspot active."
"Give me a morning brief only after I wake up."
```

Natural-language interpretation itself is not authority. Consequential durable rules require an owner-confirmed structured interpretation until a safer proven authoring path exists.

## Executive integration

The Executive Planner should consume current context and commitments rather than waiting for explicit user prompts.

Examples:

```text
rain + commute + class start
â†’ warn earlier / suggest departure buffer

meeting cancelled
â†’ free block becomes available
â†’ suggest or schedule high-priority work

assignment deadline tonight + unfinished task
â†’ protect focus time
â†’ defer low-priority interruptions

message changes meeting time
â†’ verify source
â†’ update World Model
â†’ propose/perform calendar change under policy
```

The planner should optimize for user intent, not maximum automation.

## Privacy controls

OSCAR Mobile should provide fast controls for:

- pause proactive awareness;
- disable notification source/app/person;
- mute conversational listening;
- disable acoustic awareness;
- pause Context Capture/Daily Journal;
- disable Orb overlay;
- switch to suggestion-only schedule mode;
- revoke communication action authority;
- forget retained context where technically possible.

The user should always be able to understand what OSCAR is observing, what it is retaining and what it may act on.

## Implementation boundaries

- Use native/official platform mechanisms before brittle accessibility/UI automation.
- Treat OEM-specific Android assistant/overlay behavior as unverified until tested on target devices.
- Do not make overlay visibility a correctness dependency.
- Do not infer app-private state from notifications.
- Do not silently convert observed patterns into authority.
- Do not retain sensitive notification content merely because it was available to Perception Fabric.
- Do not claim a schedule/message mutation until authoritative readback/evidence supports it.

## Acceptance scenarios

Future OSCAR Mobile/Executive acceptance should include at least:

1. OSCAR selected as Android assistant on a real supported device.
2. Orb overlay appears, retreats during active media/focus context and remains invokable.
3. A configurable home widget reflects real current state after process restart.
4. Notification listener ingests an allowed message and excludes a blocked source.
5. A notification with a legitimate reply action can be drafted/sent under policy; one without such action does not fabricate capability.
6. Calendar + task + weather context produces a sourced schedule warning.
7. A flexible block can be moved under explicit policy and verified by calendar readback.
8. A fixed event is not moved without authority.
9. `what did I miss?` summarizes only authorized current sources and distinguishes UNKNOWN/unavailable channels.
10. Perceive/retain/act controls can be changed independently and survive restart.

## Invariants

1. OSCAR is a Chief of Staff, not merely an on-demand chat surface.
2. Current context is freshness-qualified and source-backed.
3. Perception, retention and action authority are separate.
4. Proactivity is policy-bounded and interruption-aware.
5. OSCAR Mobile should be present without being visually intrusive.
6. Android assistant/overlay/widget/notification capabilities are platform-specific and must be verified on target devices.
7. Notification access never implies unrestricted app access.
8. Schedule and communication mutations require real capability, authority and verification.
9. Weak context signals do not justify confident claims about the user's activity.
10. The user can quickly make OSCAR quieter, less observant or less autonomous.

## Connected task awareness (2026-10-24)

The native `connected_tasks` source reads a signed, exact account-generation and
selected task-list binding through the existing Fabric. Google requires its
Tasks readonly scope; Microsoft requires `Tasks.Read`. It observes the first
eight tasks, marks additional pages incomplete and never follows them. Provider
default filters still limit coverage. Google due dates have no exact deadline
time; Microsoft times keep their provider timezone without conversion. Selected
fields exclude private notes/body; retention is independent and actions stay off.

Desktop and Android expose source setup and current briefing. Polling requires
explicit source selection in Sentry (or its selected trigger); stale evidence,
permission epochs and account drift withdraw visible content. This is read-only
context, with no automatic priority or schedule decision. See the
[acceptance receipt](evidence/software-completion/tasks-briefing-2026-10-24.json).


The native model-Worker path can now independently verify explicitly approved timed event creation and time-only Google/Microsoft moves after current account observations. Signed Ask or scoped synthetic standing authority owns the mutation; calendar observations never grant flexibility or action permission. Unsupported event shapes, concurrent-editor/ETag protection, general flexible-versus-fixed commitment reasoning and sustained daily-use acceptance remain open. [Calendar evidence](evidence/software-completion/calendar-verification-2026-10-26.json).
