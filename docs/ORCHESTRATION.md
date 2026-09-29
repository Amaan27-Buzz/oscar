# Orchestration, Learning, Skills, Workers and Protocols

OSCAR should not attempt to become a mediocre implementation of every specialist tool. Its job is to understand the objective, choose the best available capability, coordinate it, verify the result and learn from successful execution.

## Capability registry

Every connected worker, app, plugin, device or service should advertise capabilities dynamically.

Examples:

```text
Codex
- coding
- repository editing
- tests
- debugging
- project-specific plugins

Desktop worker node
- computer-use
- terminal
- browser
- filesystem
- IDE
- Blender
- FFmpeg

Sunday
- notifications
- phone actions
- calls/messages
- phone apps
- camera
- microphone
- location/context
- biometric approval

OSCAR Edge
- sensors
- GPIO
- displays
- relays
- motors
- Sentry events

Kinetable
- hardware design
- visual wiring
- simulation
- firmware generation
- device provisioning
```

Capability metadata should eventually include availability, latency, cost, permissions, reliability, supported input/output types and task suitability.

## Routing by suitability

The central rule is:

> Use the best available specialist for the objective, not the most general model.

Example: build a SceneLab landing page.

```text
objective
  ↓
Jev understands task + context
  ↓
OSCAR discovers:
- SceneLab project/repository
- Codex subscription
- Impeccable plugin
- browser/computer-use verification
  ↓
OSCAR selects that route
  ↓
Codex builds with project + plugin context
  ↓
OSCAR verifies visually/functionally
  ↓
result + learned procedure
```

OSCAR should not generate the page through a generic chat response merely because it technically can.

The same idea applies elsewhere:

```text
coding               → Codex / coding specialist
notes/knowledge      → connected Notion/Obsidian-like system when appropriate
email/calendar       → structured service connector
GUI-only workflow    → computer use
phone/app workflow   → Sunday when it is the best execution surface
hardware design      → Kinetable
physical action      → OSCAR Edge
research             → suitable research/model path
cheap classification → Jev / fast routed model
```

## Execution loop

A robust delegated task follows:

```text
understand objective
→ discover capabilities
→ choose route
→ provide relevant context
→ delegate
→ observe progress
→ verify independently where practical
→ recover/re-route on failure
→ report only what matters
→ learn from successful execution
```

For long work, OSCAR should remain the owner of the objective even while specialists perform the steps.

## Workers

A **Worker** is a delegated sub-agent OSCAR creates for an objective or responsibility. It is not necessarily another generic model and does not inherently own a cloud computer.

A Worker may coordinate:

- Codex
- Computer Use
- browser/terminal/apps
- Sunday/phone capabilities
- plugins/connectors/APIs
- ChatGPT/SwitchRoute
- Kinetable
- OSCAR Edge

Workers can be temporary, task-scoped or persistent.

```text
"Research these five laptops"
→ temporary research Worker

"Watch ClearLane CI tonight"
→ task Worker

"Manage SceneLab social media"
→ persistent Worker
```

Workers operate under OSCAR's Personal Policy and permission system. They can be created and edited through ordinary voice/chat and inspected through a lightweight management UI.

See [WORKERS.md](WORKERS.md).

## Worker collaboration

OSCAR may create several Workers for one objective:

```text
Launch Kinetable
├── Research Worker
├── Coding Worker
├── Design Worker
└── Social Worker
```

Workers may run in parallel, wait on dependencies, exchange artifacts/context and hand work off. OSCAR remains the top-level coordinator and resolves conflicts.

## Jev and worker recovery

Workers should not escalate routine recoverable failures to the user.

```text
Worker encounters issue
→ Jev evaluates
→ safe/confident self-fix? → repair/retry/verify
→ better capability exists? → reroute/delegate
→ otherwise ask OSCAR/user for minimum required intervention
```

Retries must be bounded. Workers must never invent success or silently switch to a more privileged capability path.

## Tools vs skills vs workers vs routines vs protocols

### Tool

A primitive capability OSCAR can invoke.

Examples: `gmail.send`, `gpio.set`, browser click, terminal command, `codex.run`.

### Skill

A reusable learned procedure for achieving a goal, ideally portable and inspectable using the ecosystem's `SKILL.md`-style convention where suitable.

A skill may combine multiple tools/workers.

### Worker

A delegated sub-agent that owns a scoped objective/job and may combine specialists, tools, devices and skills.

### Routine

A recurring or simple event-driven behavior.

Examples:

- every morning prepare a concise agenda
- when the laptop comes online, advertise Codex availability
- at bedtime switch Sentry behavior

### Protocol

A persistent, stateful autonomous responsibility that may wait, observe, branch, delegate, recover and escalate over time.

Example:

```text
Protocol: release-watch
Objective: get the release safely deployed

watch CI
→ if failed, investigate
→ create/delegate Worker for recoverable fix
→ rerun tests
→ wait for deployment
→ verify live result
→ notify user only if blocked or complete
```

This is intentionally more capable than a basic scheduled action.

## Self-created skills, workers, routines and protocols

OSCAR may create or propose reusable automation when:

- the user explicitly asks it to delegate or remember a workflow
- a successful novel procedure is worth reusing
- repeated behavior reveals a stable pattern
- an existing skill can be improved from a better verified path
- an objective is large enough to deserve a temporary or persistent Worker

Creation flow:

```text
objective/history
→ identify reusable responsibility/procedure
→ normalize parameters + preconditions
→ define required capabilities
→ define Personal Policy + permissions/risk
→ define verification
→ create Worker/skill/routine/protocol candidate
→ validate
→ activate within existing authority
```

Generated automation **cannot grant itself new permissions**.

## Learning: first time vs next time

The first execution of a novel task may be exploratory and slow.

```text
first time
→ investigate environment
→ try suitable capability
→ recover from mistakes
→ verify success
→ capture path
```

Later:

```text
same/similar task
→ retrieve known procedure
→ fill parameters
→ skip unnecessary discovery
→ use deterministic steps where possible
→ invoke AI only for uncertainty
→ verify
```

The goal is for repeated tasks to become measurably faster, cheaper and more reliable.

## Skill representation

Portable skills should keep human-readable instructions and machine-readable metadata where practical.

A skill should be able to declare:

- purpose
- triggers/applicability
- required capabilities
- input parameters
- preconditions
- procedure
- verification
- permissions/risk class
- failure/recovery strategy
- provenance
- version

The exact schema should remain compatible with widely used `SKILL.md` conventions where possible rather than inventing an unnecessary closed format.

## Plugin/connector support

OSCAR should discover and use plugins/connectors exposed by its host environments.

A plugin is not merely another menu item. It expands the capability registry and may become part of learned skills/protocols/Workers.

Examples include mail, calendar, GitHub, cloud storage, knowledge tools, communication services and future third-party systems.

## Projects and specialist context

Workers often have useful context OSCAR should preserve rather than flattening into a prompt.

Examples:

- Codex project/repository context
- plugin configuration such as Impeccable
- IDE workspace state
- Kinetable project/inventory
- Notion/Obsidian workspace
- GitHub repository and issues
- social/account context available through approved connectors

OSCAR should route the objective to the environment that already has the correct context whenever possible.

## Personal Policy

Worker autonomy is constrained by [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

Examples:

```text
ordinary SceneLab feature post → Worker may publish
major announcement              → ask
controversial reply              → never auto-publish
security/account change          → strong confirmation
```

Preferences may narrow behavior but cannot create permissions that do not already exist.

## Verification

Delegation is not completion.

OSCAR should verify outcomes using an independent signal when practical:

- tests after code changes
- browser/computer-use inspection after UI work
- file/state checks after desktop actions
- API/result checks after communication/social actions
- sensor feedback after physical actions
- deployment health checks after release

If verification fails, OSCAR may retry, route to another capability or ask the user depending on policy.

## Permissions and safety

Learning never overrides authorization.

A learned skill/protocol/Worker records what permissions it requires; it does not create them.

Critical or destructive steps still follow OSCAR's policy layer, Voice Match rules and stronger confirmation requirements.

## Design target

OSCAR should gradually evolve from:

```text
"I can use these tools"
```

to:

```text
"I know the best way to accomplish this for this user, with these tools, in this environment, and I can delegate the work to the right team."
```
