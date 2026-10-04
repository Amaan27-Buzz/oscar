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
- `You may move study blocks automatically, but never move class or appointments.`
- `Do not interrupt me while I am watching a match unless family calls twice.`
- `Hide the Orb while I am reading, but keep the edge hotspot available.`
- `Never retain banking notifications.`
- `Always ask before replying to university faculty.`

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

## Natural-language authoring

Examples:

```text
"Do not answer unknown callers while I am asleep."
"Actually, delivery drivers can still get through."
"Keep approved coding tasks running when I leave the house."
"Never shut my desktop down if another user session is active."
"Pause Daily Journal at the university cafeteria."
"Do not keep raw audio from casual conversations."
"Move flexible study blocks if an urgent deadline appears, but never move class."
"Keep the Orb hidden in YouTube and Kindle unless I invoke it."
```

Safe conceptual flow for consequential durable rules:

```text
user instruction
→ Controller recognizes durable policy change
→ interpret candidate structured rule
→ resolve scope/conflicts/permission dependencies
→ show concise interpretation when material
→ owner confirms
→ persist rule
→ apply immediately where safe
```

Model interpretation itself is not authority. Ambiguous consequential policy should remain a candidate until owner-confirmed.

The user can later ask `Why did you do that?`, inspect/edit the rule or remove it.

## Open-ended scopes

Policies may apply to:

- global behavior;
- person/contact/relationship;
- app/service/channel;
- notification source/app/person;
- project;
- Worker/Protocol;
- device/node;
- Connection Grid role;
- remote continuation/power behavior;
- Android Orb/overlay presence;
- home-screen/widget behavior;
- location/environment;
- calendar/context state;
- schedule commitment type (`fixed`, `flexible`, deadline, follow-up);
- attention/interruption state;
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

Persona does not sit in this authority chain because Persona changes presentation rather than action authority.

## Perceive / retain / act

Policy can narrow behavior independently across three axes:

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

Examples:

```text
"You can read delivery notifications, but do not save them."
"You can see my university calendar, but never move class."
"You can summarize WhatsApp notifications, but ask before replying."
"You can use location for travel buffers, but do not retain location history."
```

A read permission never silently becomes write/send authority. A perception source never automatically becomes durable memory.

See [CHIEF-OF-STAFF.md](CHIEF-OF-STAFF.md).

## Chief-of-Staff / schedule policy

Personal Policy is the boundary between useful schedule autonomy and arbitrary calendar mutation.

Examples:

```text
"Treat class, appointments and football matches as fixed."
"Study blocks are flexible; move them if necessary."
"Keep at least 30 minutes between university and anything across town."
"Protect two hours before tomorrow's deadline."
"Do not schedule deep work after midnight."
"If a meeting is cancelled, you can fill the time with my highest-priority task."
```

The Executive may only act on a schedule source if the current capability and permission allow it. `flexible` is user policy, not a model guess.

Changes remain Action-Ledger-backed and should be independently read back where practical before being reported as complete.

## Attention / interruption policy

Policies may map current evidence to output level:

```text
silent update
notification
haptic
speech
urgent escalation
```

Examples:

```text
"While I am watching a match, keep nonurgent work silent."
"During class, only family or a security alert may interrupt."
"If I am driving, speak urgent schedule changes instead of showing a long notification."
"Do not wake me for routine Worker completion."
```

Weak activity evidence should result in conservative behavior rather than overconfident assumptions.

## Sunday / Orb / notification policy

Examples:

```text
"Hide the Orb in video and reading apps."
"Keep the edge hotspot active even while the Orb is hidden."
"Never retain notifications from banking apps."
"Summarize university and family notifications, ignore promotional ones."
"You may reply to routine delivery messages if a real notification reply action exists."
"Always ask before sending a message to faculty."
```

Policy cannot make Android expose an unavailable `RemoteInput`, call-audio stream or app-private message store.

## Connection Grid policy

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

## Sentry / Context Capture / Daily Journal policy

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

## Persona boundary

Requests such as:

```text
"Be funnier."
"Be more direct when reviewing my code."
"No jokes when Sentry alerts me."
```

belong primarily to Persona, not Personal Policy, unless they also encode a consequential behavioral constraint.

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

- interruption/quiet/focus behavior;
- fixed vs flexible schedule classes;
- schedule autonomy level (suggest-only vs bounded auto-replan);
- calls/messages autonomy;
- notification source/retention/reply boundaries;
- Orb/overlay presence behavior;
- meeting/capture retention;
- schedule/privacy disclosure;
- send/publish confirmation;
- Worker autonomy;
- Sentry behavior;
- Connection Grid remote-continuation/power preferences.

Persona setup is separate but nearby.

## Learned preferences

Repeated observed behavior can become a **suggestion**, not hidden consequential policy.

```text
repeatedly pauses nonurgent alerts while studying
→ OSCAR suggests a study-time rule
→ user approves
→ explicit policy is created
```

A repeated manually rescheduled calendar pattern does not silently grant future calendar mutation authority.

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

## Runtime evaluation

Before a consequential action:

```text
objective / event
→ current platform/capability
→ current World Model / attention / commitment state
→ permission / owner revocation state
→ applicable Personal Policy
→ Protocol/Worker state
→ Controller / Executive decision
→ execute / ask / defer / block
→ verify mutation where practical
→ Persona shapes presentation only
```

## UI

The Personal Policy surface exists for visibility/control, not mandatory configuration.

Useful presentation can group real rules around Calls, Schedule, Notifications, Remote work, Orb/Presence and Capture, while preserving natural-language editing.

The user should be able to ask `why did you move this?`, `why did you interrupt me?`, `what rule let you reply?` and receive the relevant policy/evidence explanation.

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
10. Perception, retention and action can be independently narrowed.
11. Schedule autonomy requires explicit policy; readability is not edit authority.
12. Natural-language model interpretation does not become consequential authority until appropriately owner-confirmed.

## Club B structured reference implementation

`oscar.policy.PersonalPolicy` currently persists explicit owner-authorized structured rules separately from memory. Capability scope, exact context conditions, priority, source, timestamps, enabled/expiry and preference are supported. Hard constraints and missing permission/required confirmation block before policy; specific explicit rules precede broad ones. Equal-ranking conflicts block with rule IDs. Model/inferred candidates cannot become authority.

Connector mutations and machine executors recheck policy at execution. `ask` needs confirmation; `deny` remains denied even with confirmation. Preference values can be evaluated but are not automatically interpreted/applied to unrelated subsystems.

Open-ended bounded model interpretation now produces inactive candidates through the native Model Router. Exact trusted-owner confirmation is required; ambiguity/conflict/expiry block. Numeric constraints never grant capabilities. General quiet-hour parsing, Sunday approval identity and a policy UI remain unverified. The bounded local message/send editor below supersedes the original unimplemented status for those exact phrases only. The reference editor is the typed `save(..., owner_authorized=True)` composition API; it is not a remotely exposed unauthenticated approval endpoint.

## Bounded local owner-review authoring — 2026-10-04

`oscar.policy_authoring.PolicyAuthoring` now recognizes a deliberately small set of
exact message/send phrases, including `Never send messages without asking me.`
It persists an inactive candidate and shows the structured interpretation:
`connectors:external-communication` → ASK, covering current Connector Fabric
mail/messages and communicating calendar mutations. The interpretation explicitly
excludes arbitrary terminal/agent sending and grants no new permission.

The trusted local editor is runnable with:

```sh
python -m oscar.policy_authoring --state .oscar/owner-policy.sqlite --text "Never send messages without asking me."
```

It prints the candidate and requires the owner to type `CONFIRM`. Only the exact
pending review digest can activate; altered/stale/replayed confirmations and
contradictory existing equal-scope rules reject activation. Ambiguous exceptions,
compound instructions and unrecognized phrases request clarification rather than
guessing. Confirmed rules persist across actual coordinator-process restart and
affect later policy evaluation. Permissions remain an independent prerequisite;
equal-ranking structured policy conflicts still BLOCK. This local owner editor
is not a remote identity/approval service. The model-backed candidate path below supersedes the model-parsing limitation. General arbitrary language semantics, quiet hours, policy UI and Sunday biometric authorization remain partial/unverified.

## Gate B local completion candidate — 2026-10-04

`python -m oscar.policy_cli --state <isolated.sqlite> --provider <provider> --propose <rule>` shows an inactive interpretation. Separate `--confirm <candidate-id> --digest <exact-digest>` activates only that unexpired candidate. The live native Model Router acceptance used a synthetic ASK-before-file-write rule; reopening and an independently absent artifact proved actual Worker enforcement. Model parsing does not grant authority. Owner identity here is a trusted local composition/CLI boundary, not remote biometrics. Broad initial wording was rejected for clarification. Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).
