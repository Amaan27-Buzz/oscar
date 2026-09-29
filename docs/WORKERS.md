# Workers

Workers are delegated sub-agents OSCAR creates and manages for specific responsibilities. They provide the "persistent teammate" capability found in systems such as Grok Bot, but OSCAR should use the user's actual device/capability mesh rather than assume every worker owns a separate cloud computer.

## Product rule

> The user talks to OSCAR. OSCAR creates, coordinates and manages the team underneath it.

Workers are not separate assistant identities or chat silos. They operate under OSCAR's memory, policy, permissions and task ownership.

## What a Worker is

A Worker is an objective envelope containing:

- goal/responsibility
- relevant context
- allowed capabilities
- permission boundaries
- preferred specialists/models
- execution surfaces
- state/lifecycle
- verification requirements
- escalation rules
- memory/provenance

A Worker may use one or many tools/agents/devices.

Example:

```text
Worker: SceneLab Social
Goal: manage SceneLab social presence

Uses:
- X / LinkedIn connectors or browser/app automation
- SceneLab GitHub/project context
- image generation
- research tools
- Sunday or desktop worker when app-only access is required

Allowed:
- monitor mentions
- draft posts
- answer routine questions
- publish ordinary feature posts (if Personal Policy permits)

Ask first:
- major announcements
- commitments/promises
- controversial topics
- security/account changes

Escalation:
recover locally → reroute specialist → ask OSCAR/user if still blocked
```

## Worker types

Workers can be temporary or persistent.

```text
"Research these laptops."
→ temporary research Worker

"Watch ClearLane CI tonight."
→ task Worker that expires when the objective completes

"Manage SceneLab social media."
→ persistent Worker

"Handle university scheduling for me."
→ persistent responsibility Worker
```

Workers can sleep when idle and resume when their trigger/objective requires them.

## Creation should be easy

The primary creation interface is ordinary voice or chat.

Examples:

- "OSCAR, make a worker that watches ClearLane releases and fixes recoverable CI failures."
- "Create someone to manage SceneLab social media, but ask before major announcements."
- "Have a worker keep track of internship applications and tell me what I need to do."

OSCAR should infer the initial worker definition from the request, existing Personal Policy, available capabilities and relevant project context.

For consequential autonomy, OSCAR should summarize the resulting scope/permissions before activation when necessary.

## Device mesh, not mandatory cloud desktops

A Worker does not inherently own a virtual machine.

It plans against currently available OSCAR capabilities:

```text
Sunday
- phone apps
- calls/messages
- notifications
- camera/location

Desktop worker
- browser
- terminal
- filesystem
- Codex
- Computer Use
- IDEs/apps

OSCAR Edge
- sensors
- physical actions

Cloud/services
- ChatGPT
- SwitchRoute models
- APIs/plugins/connectors
```

The same Worker may move execution between these surfaces as availability changes.

Example:

```text
Social Worker
→ use official API when connected
→ otherwise use browser worker
→ otherwise use authorized phone app through Sunday
→ if none are available, wait/escalate
```

No worker should silently switch to a more privileged execution path merely because another path failed.

## Workers orchestrate specialists

A Worker is not necessarily another generic LLM.

Examples:

```text
Coding Worker      → Codex + repository + tests
Design Worker      → Codex + Impeccable + visual verification
Research Worker    → ChatGPT/research path
Phone Worker       → Sunday
GUI Worker         → Computer Use
Hardware Worker    → Kinetable + edge tools
Social Worker      → APIs/plugins/browser/phone apps
```

The Worker owns the objective; the specialist owns execution expertise.

## Parallel collaboration

OSCAR may create multiple Workers for one objective and let them collaborate.

Example:

```text
Objective: launch Kinetable

OSCAR
├── Research Worker
├── Coding Worker
├── Design Worker
└── Social Worker
```

Workers can:

- exchange task artifacts/context through OSCAR
- hand work off
- wait on dependencies
- run independently in parallel
- report structured progress

OSCAR remains the top-level coordinator and resolves conflicting priorities/policies.

## Worker vs tool vs skill vs routine vs protocol

| Concept | Meaning |
|---|---|
| Tool | Primitive callable capability |
| Skill | Reusable procedure for doing something |
| Worker | Delegated sub-agent responsible for an objective/job |
| Routine | Recurring/simple behavior |
| Protocol | Stateful persistent responsibility/process |

A protocol may create Workers. A Worker may use Skills. A Skill may invoke Tools. A persistent Worker may itself be governed by one or more Protocols.

Example:

```text
Protocol: ClearLane release
→ create Build Worker
→ create QA Worker
→ create Social Worker
→ coordinate dependencies
→ verify release
→ stop/sleep Workers when done
```

## Jev and autonomous recovery

Workers should not bother the user for routine recoverable problems.

```text
Worker encounters issue
        ↓
Jev evaluates
        ↓
Can fix safely/confidently?
  yes → repair/retry → verify → continue
  no  → is another capability better?
          yes → reroute/delegate
          no  → ask OSCAR/user for the minimum intervention needed
```

Examples:

```text
image format rejected
→ convert image
→ bounded retry
→ verify
→ continue
```

```text
account login expired and passkey required
→ cannot safely recover
→ ask user to authenticate
→ resume after confirmation
```

A Worker must never invent success or remain stuck in an unbounded retry loop.

## Social-media management

Workers may manage social media when connected capabilities and permissions permit.

Potential responsibilities:

- monitor mentions/replies
- research relevant developments
- draft posts
- prepare media
- schedule content
- publish permitted content
- answer permitted routine messages/comments
- coordinate product-release announcements
- summarize performance/community feedback

Personal Policy controls what may happen without confirmation.

Example:

```text
ordinary SceneLab feature post → publish automatically
major launch announcement       → ask
controversial/political reply   → never publish automatically
security/account change         → strong confirmation
```

## Learning

Workers should improve through OSCAR's procedural-memory/skill system.

```text
novel Worker task
→ explore
→ successful execution
→ verify
→ distill reusable Skill
→ future Workers reuse Skill
```

A learned Skill may be shared by multiple Workers when its scope and permissions are compatible.

Workers can also propose better routines/protocols after repeated work, but generated automation cannot broaden authority on its own.

## State and persistence

Worker state should include at least:

- identity/name
- objective
- lifecycle status
- current step/blocker
- owner protocol/task
- context references
- capability requirements
- permission scope
- last activity
- completion condition
- retry/escalation state
- artifacts/results

Important state must survive process/device restarts when the Worker owns a long-running responsibility.

## UI

Workers need a simple management surface, not an agent-dashboard wall.

Example:

```text
Workers

SceneLab Social      Active
ClearLane Release    Waiting for CI
University Admin     Idle
Research             Working
```

Opening a Worker should show only the useful information:

```text
SceneLab Social
Managing SceneLab's social accounts

Now
Watching launch replies

Can use
X · LinkedIn · GitHub · Image generation

Autonomy
Routine replies        ✓
Draft posts            ✓
Ordinary publishing    ✓
Major announcements    Ask

Recent
Responded to 3 questions
Prepared tomorrow's post
```

Users can create, pause, resume, edit or remove Workers using either UI or natural language.

## Permissions and audit

Workers inherit only explicitly available OSCAR capabilities/permissions.

They cannot:

- self-grant new permissions
- bypass Personal Policy
- bypass approval gates
- silently adopt a more privileged user/device identity

Consequential actions should remain attributable to:

- OSCAR task/protocol
- Worker
- capability/tool used
- initiating user/policy
- timestamp/result

## Invariants

1. Workers belong to OSCAR; they are not separate assistant silos.
2. Workers use the best available real device/service capability instead of requiring a cloud computer.
3. Creation and editing should work through normal voice/chat.
4. Jev enables self-repair/rerouting before unnecessary user escalation.
5. Workers can collaborate and hand off work while OSCAR owns the top-level objective.
6. Workers may use/create Skills and participate in Protocols, but cannot broaden their own permissions.
7. Worker state and progress remain inspectable in a simple UI.
8. Temporary Workers should disappear/retire when their objective is complete; persistent Workers remain only when they own a continuing responsibility.
