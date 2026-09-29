# Personal Policy and Preferences

OSCAR's preferences must be substantially more capable than a settings page full of generic toggles. The user should be able to describe how OSCAR should behave in natural language, during setup or later, and have those rules become durable, inspectable policy.

## Product rule

> If the user can clearly describe a preference, OSCAR should be able to represent it without requiring the preference to fit a predefined category.

Examples:

- "Do not call me before 9 unless it is important."
- "When I am studying, interrupt me only for family or something urgent."
- "If a recruiter calls and I do not answer, you can answer for me."
- "Never answer calls from my parents yourself."
- "For university meetings, always make detailed notes."
- "For casual calls, do not keep transcripts."
- "When replying to professors, be slightly more formal than I normally am."
- "If someone asks when I am free, share free slots but never calendar-event names."
- "When I say I am working, keep Codex jobs running but suppress routine notifications."

The underlying system may organize policy structurally, but the user should not need to learn that schema.

## Preferences are not the same as memory, permission or protocol

OSCAR must keep these concepts distinct:

| Concept | Meaning |
|---|---|
| Memory | Something OSCAR knows or recalls |
| Preference / policy | How the user wants OSCAR to behave |
| Permission | What OSCAR is authorized to do |
| Protocol | A persistent autonomous responsibility/process |
| Routine | A recurring/simple behavior |

Example:

```text
Memory:      "Amaan usually declines calls while studying."
Preference:  "Do not answer calls while I am studying."
Permission:  "OSCAR may answer phone calls on my behalf."
Protocol:    "When a call arrives during study time, apply my call-handling rules."
```

A learned pattern does not automatically become authority.

## Natural-language authoring

Policy should be editable through ordinary voice or chat.

Examples:

```text
"OSCAR, from now on do not answer unknown callers while I am asleep."
"Actually, delivery drivers can still get through."
"For SceneLab posts, stop asking before ordinary feature updates."
"Never let a worker publish anything political."
```

OSCAR should:

```text
user instruction
→ Jev recognizes durable policy change
→ resolve scope and conflicts
→ show/voice a concise interpretation when needed
→ persist rule
→ apply it immediately where safe
```

The user can later ask:

- "What are my call preferences?"
- "Why did you not answer that call?"
- "Change the rule for recruiters."
- "Remove the thing about delivery drivers."

## Open-ended scopes

Policies may apply at different scopes:

- global
- person/contact/relationship
- app/service
- project
- device/surface
- communication channel
- location/environment
- calendar/context state
- Sentry mode
- worker
- skill/routine/protocol
- time window
- task category
- arbitrary user-defined context

More specific policy normally overrides a more general preference, subject to safety and permission constraints.

Example:

```text
Global:      do not interrupt while studying
Specific:    family may interrupt while studying
More specific: mother may always call through
```

## Precedence

OSCAR should resolve behavior in this order conceptually:

```text
hard safety / legal / platform constraints
        >
explicit permission boundaries
        >
explicit user policy (most specific applicable rule)
        >
protocol/routine defaults
        >
learned/inferred preference suggestions
        >
product defaults
```

An explicit user preference may narrow behavior but must not create authority that the permission system has not granted.

## Conflicts and updates

Policy changes should update the relevant rule rather than accumulating contradictory instructions forever.

When rules conflict:

- explicit beats inferred
- specific beats general
- newer explicit policy can replace older policy at the same scope
- safety/permission constraints cannot be overridden by ordinary preference edits
- unresolved consequential ambiguity should be surfaced rather than guessed

OSCAR should preserve enough history/provenance to explain why a policy currently has its value and allow rollback where useful.

## Setup

First-run setup should seed only the highest-value preferences and make clear that anything can be changed later by simply telling OSCAR.

Useful setup prompts include:

- response style and verbosity
- spoken vs visual acknowledgement
- interruption/quiet-hour behavior
- calls and messaging autonomy
- meeting transcription/note defaults
- what may be sent/published without confirmation
- schedule/privacy disclosure rules
- Sentry behavior
- worker autonomy defaults

Do not force the user through dozens of categories up front.

## Learned preferences

LRA/Supermemory can detect repeated patterns, but inferred behavior should be treated as a suggestion rather than hidden policy when it affects consequential actions.

Example:

```text
OSCAR observes repeated manual silencing of non-urgent calls during study
→ proposes: "Want me to automatically silence non-urgent calls while you study?"
→ user approves
→ explicit policy is created
```

Low-risk presentation preferences may be learned more automatically where the user has allowed that behavior, but they remain inspectable and editable.

## Personal Policy engine

A policy record should be able to carry:

- user intent / rule
- normalized condition(s)
- scope
- action/constraint
- priority/specificity
- provenance
- explicit vs inferred status
- created/updated time
- permission dependencies
- conflict metadata
- optional expiry

The exact storage representation should remain implementation-specific. The user-facing abstraction is simply: "this is how I want OSCAR to behave."

## Runtime evaluation

Before a consequential action, OSCAR should evaluate:

```text
objective / event
→ platform capability
→ permission
→ applicable Personal Policy
→ protocol/worker state
→ Jev decision
→ execute / ask / defer / block
```

Examples:

- incoming phone call
- worker about to publish a social post
- meeting transcription starting
- sharing schedule availability
- interrupting the user during focus time
- replying to a message on the user's behalf

## UI

Preferences should be manageable in a simple Personal Policy surface, but the UI is for visibility and control rather than mandatory configuration.

Useful views:

```text
Calls
  Answer after 4 rings                  On
  Never answer family                   On
  Recruiters: take message + callback   On

Privacy
  Share free/busy slots                 Allowed
  Share event titles                    Never
```

The user should still be able to change any of these by voice/text without opening the settings screen.

## Privacy and transparency

OSCAR should be able to explain:

- which rule affected a decision
- where the rule came from
- what permission allowed or blocked the action
- whether the rule was explicit or inferred

Sensitive preferences are personal data and should follow the same privacy/retention protections as other user context.

## Invariants

1. Preferences are open-ended, not limited to predefined settings categories.
2. Voice/chat can create, edit, inspect and remove policy.
3. Explicit preferences are distinct from inferred memory.
4. Preferences cannot self-grant permissions.
5. Safety and platform constraints remain authoritative.
6. Policy conflicts are resolved deliberately rather than by arbitrary prompt order.
7. The user can always inspect and change durable Personal Policy.
