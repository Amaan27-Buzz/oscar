# Personal Policy and Preferences

OSCAR's preferences must be more capable than a settings page full of generic toggles. The user should be able to describe how OSCAR should **behave** in natural language and have those rules become durable, inspectable policy.

## Product rule

> If the user can clearly describe a behavioral preference, OSCAR should be able to represent it without requiring the preference to fit a predefined category.

Examples:

- `Do not call me before 9 unless it is important.`
- `When I am studying, interrupt me only for family or something urgent.`
- `If a recruiter calls and I do not answer, you can answer for me.`
- `Never answer calls from my parents yourself.`
- `For university meetings, always make detailed notes.`
- `For casual calls, do not keep transcripts.`
- `If someone asks when I am free, share free slots but never event names.`
- `When I leave home, keep approved desktop jobs running and tell me on Sunday when they finish.`
- `After a verified overnight render, shut down the desktop.`
- `Keep daily summaries of meetings and calls, but delete raw audio after transcription.`

The user should not need to learn the internal schema.

## Policy is not Persona, memory, permission or Protocol

| Concept | Meaning |
|---|---|
| Memory | what OSCAR knows/recalls |
| Persona | how OSCAR expresses itself |
| Personal Policy | how the user wants OSCAR to behave |
| Permission | what OSCAR is authorized to do |
| Protocol | persistent autonomous responsibility/process |
| Routine | recurring/simple behavior |

Example:

```text
Memory:      "Amaan usually declines calls while studying."
Persona:     "Be concise and dry during coding work."
Policy:      "Do not answer calls while I am studying."
Permission:  "OSCAR may answer phone calls on my behalf."
Protocol:    "When a call arrives during study time, apply my call rules."
```

A learned pattern does not automatically become authority.

See `PERSONA.md` for expression/character configuration.

## Natural-language authoring

Examples:

```text
"Do not answer unknown callers while I am asleep."
"Actually, delivery drivers can still get through."
"Keep approved coding tasks running when I leave the house."
"Never shut my desktop down if another user session is active."
"Pause Daily Journal at the university cafeteria."
"Do not keep raw audio from casual conversations."
```

Conceptual flow:

```text
user instruction
→ Jev recognizes durable policy change
→ resolve scope/conflicts
→ concise interpretation when needed
→ persist rule
→ apply immediately where safe
```

The user can later ask `Why did you do that?`, inspect/edit the rule or remove it.

## Open-ended scopes

Policies may apply to:

- global behavior;
- person/contact/relationship;
- app/service/channel;
- project;
- Worker/Protocol;
- device/node;
- Connection Grid role;
- remote continuation/power behavior;
- location/environment;
- calendar/context state;
- Sentry mode;
- capture source/retention mode;
- time window;
- task category;
- arbitrary user-defined context.

Specific explicit rules normally override broader explicit rules, subject to higher-order constraints.

## Precedence

```text
hard safety / legal / platform constraints
        >
explicit permission boundaries / owner revocation
        >
explicit user Personal Policy (most specific applicable)
        >
Protocol/routine defaults
        >
learned/inferred suggestions
        >
product defaults
```

Persona does not sit in this authority chain because Persona changes presentation rather than action authority. It is applied only after the allowed behavior/path is resolved.

## Connection Grid policy examples

Personal Policy can govern remote continuation without turning node connectivity into blanket authority.

Examples:

```text
"If a Codex task is already approved, keep it running after I leave."
"Ask before shutting down my desktop during the day."
"At night, shut it down after the verified task finishes unless another task is active."
"Never wake the desktop just to answer a nonurgent question."
```

These rules apply only if the target node currently advertises the required capability.

`keep running` does not create a power-control or Wake-on-LAN capability that does not exist.

Sunday owner pause/cancel/revoke controls remain bounded by permissions and cannot override local hardware emergency safety.

See `CONNECTION-GRID.md`.

## Sentry / Context Capture / Daily Journal policy

Personal Policy can control capture behavior by source, place, person and time.

Examples:

```text
"Keep meeting transcripts for 30 days."
"For ordinary in-person conversations, retain summaries but not raw audio."
"Do not capture conversations with this person."
"Pause Context Capture when I am in the library."
"Keep email and message context in my Daily Journal, but never copy passwords or OTPs into memory."
```

Important boundary:

- Policy can narrow behavior within existing capability/permission.
- Policy cannot make an unsupported app expose call audio.
- Policy cannot override recording-consent/legal constraints.
- Awareness, transcription, raw audio, transcript, summary and memory retention remain separate controls.

See `VOICE-SENTRY.md` and `COMMUNICATION.md`.

## Persona boundary

Requests such as:

```text
"Be funnier."
"Be more direct when reviewing my code."
"No jokes when Sentry alerts me."
```

belong primarily to Persona, not Personal Policy, unless they also encode a consequential behavioral constraint.

A natural-language request can therefore update both layers when needed, but the stored meanings remain separate.

Example:

```text
"On university calls, be formal and never promise a deadline for me."

Persona rule: formal / low humor for university calls
Policy rule: do not commit user to deadlines without explicit approval
```

## Conflicts and updates

- explicit beats inferred;
- specific beats general;
- newer explicit rule can replace older same-scope policy;
- owner revocation and permission/safety constraints cannot be overridden by ordinary preference edits;
- consequential ambiguity is surfaced rather than guessed;
- policy changes should update/supersede relevant rules rather than accumulate contradictions forever.

Preserve provenance/history where useful for explanation/rollback.

## Setup

Commissioning should seed only high-value rules:

- interruption/quiet hours;
- calls/messages autonomy;
- meeting/capture retention;
- schedule/privacy disclosure;
- send/publish confirmation;
- Worker autonomy;
- Sentry behavior;
- Connection Grid remote-continuation/power preferences.

Persona setup is separate but nearby in the onboarding flow.

## Learned preferences

Repeated observed behavior can become a **suggestion**, not hidden consequential policy.

Example:

```text
repeatedly pauses nonurgent alerts while studying
→ OSCAR suggests a study-time rule
→ user approves
→ explicit policy is created
```

Low-risk presentation tendencies belong in Persona and may also be suggested rather than silently rewritten when they materially change OSCAR's character.

## Policy record

A durable policy record can include:

- user intent/rule;
- normalized conditions;
- scope;
- action/constraint;
- priority/specificity;
- provenance;
- explicit vs inferred/suggested status;
- created/updated time;
- permission dependencies;
- conflict/supersedes metadata;
- optional expiry.

The exact representation is implementation-specific.

## Runtime evaluation

Before a consequential action:

```text
objective / event
→ current platform/capability
→ permission / owner revocation state
→ applicable Personal Policy
→ Protocol/Worker state
→ Jev / Executive decision
→ execute / ask / defer / block
→ Persona shapes presentation only
```

Examples include incoming calls, Worker publishing, meeting/capture start, schedule disclosure, remote desktop shutdown and user interruption.

## UI

The Personal Policy surface exists for visibility/control, not mandatory configuration.

Useful presentation:

```text
Calls
  Answer after 4 rings                  On
  Never answer family                   On

Remote work
  Keep approved desktop tasks running  On
  Shutdown after verified overnight job Ask

Capture
  Meetings: keep summary                Always
  Casual conversation raw audio         Never
```

The user can still change any rule by ordinary voice/text.

## Privacy / transparency

OSCAR should explain:

- which rule affected a decision;
- where it came from;
- what permission/capability allowed or blocked the action;
- whether a rule was explicit or inferred;
- which Persona rule affected tone separately from action policy.

Sensitive policy is personal data and follows OSCAR privacy/retention controls.

## Invariants

1. Personal Policy is open-ended.
2. Voice/text can create, edit, inspect and remove it.
3. Personal Policy is distinct from Persona, memory, permission and Protocol.
4. Policy cannot self-grant capabilities/permissions.
5. Safety/legal/platform constraints remain authoritative.
6. Connection Grid rules never invent unavailable remote-control/power capability.
7. Capture policy cannot bypass consent/legal/platform limits.
8. Conflicts are resolved deliberately, not by prompt order.
9. The user can inspect/change durable policy.
