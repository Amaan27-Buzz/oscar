# Orchestration, Learning, Skills, Workers and Protocols

OSCAR should not attempt to become a mediocre implementation of every specialist tool. Its job is to understand the objective, choose the best available capability, coordinate it, verify the result and learn from successful execution.

## Capability Catalog + Dynamic Tool Search

Every connected Worker, app, plugin, device, channel or service advertises capabilities dynamically through lightweight manifests.

Examples:

```text
Codex
- coding
- repository editing
- tests
- debugging
- project-specific plugins

Desktop machine node
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

Capability metadata should include, where useful:

- ID/name/summary;
- capability class;
- inputs/outputs;
- availability;
- supported execution surfaces;
- latency/cost hints;
- permissions/risk;
- reliability/history hints;
- project/workspace affinity;
- reversible/undo metadata;
- provider/plugin/version.

OSCAR should **search the catalog first** and load detailed contracts only for a small relevant candidate set. It should not dump every tool/plugin/Skill definition into every model context.

Conceptually:

```text
objective
→ required capability classes
→ capability search
→ rank by suitability + availability + policy + reliability + latency/cost
→ load detailed contracts for finalists
→ execute specialist
```

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Routing by suitability

The central rule is:

> Use the best available specialist for the objective, not the most general model.

Example: build a SceneLab landing page.

```text
objective
  ↓
Jev understands task + context
  ↓
Capability Catalog finds:
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
Artifact/Result + learned procedure candidate
```

OSCAR should not generate the page through a generic chat response merely because it technically can.

The same idea applies elsewhere:

```text
coding               → Codex / coding specialist
notes/knowledge      → connected Notion/Obsidian-like system when appropriate
email/calendar       → structured service connector
GUI-only workflow    → computer use
phone/app workflow   → Sunday when it is the best execution surface
communication        → Universal Channel Gateway + best native adapter
hardware design      → Kinetable
physical action      → OSCAR Edge
research             → suitable research/model path
cheap classification → Jev / fast routed model
```

## Execution loop

A robust delegated task follows:

```text
understand objective
→ define completion/verification condition
→ discover capabilities
→ choose route
→ provide relevant context
→ persist task state if long-running
→ delegate
→ observe progress
→ collect reported result
→ verify independently where practical
→ recover/re-route on failure
→ record Action Ledger + Artifacts/Results
→ report only what evidence supports
→ learn from verified successful execution
```

For long work, OSCAR remains the owner of the objective even while specialists perform steps.

## Durable Execution Runtime

Workers/Protocols/tasks that must survive process/device loss use the Durable Execution Runtime.

It tracks, where relevant:

- task/objective ID;
- owner;
- lifecycle state;
- checkpoint/current step;
- dependencies;
- executor lease/ownership;
- heartbeat/last progress;
- retry budget/backoff state;
- cancellation state;
- deadline/expiry;
- required capabilities;
- current execution surface;
- artifact/result references;
- verification state;
- blocker/escalation state.

It provides:

- durable checkpoints;
- bounded retries;
- heartbeats;
- reclaim after lease expiry;
- zombie/stuck-work detection;
- restart/resume;
- idempotency/deduplication where needed;
- durable queues/event delivery when justified.

The Executive Planner decides **what should run and priority**. The Durable Runtime makes the execution survive safely.

## Workers

A **Worker** is a delegated sub-agent OSCAR creates for an objective or responsibility. It is not necessarily another generic model and does not inherently own a cloud computer.

A Worker may coordinate:

- Codex;
- Computer Use;
- browser/terminal/apps;
- Sunday/phone capabilities;
- plugins/connectors/APIs;
- Universal Channel Gateway;
- ChatGPT/SwitchRoute;
- Kinetable;
- OSCAR Edge.

Workers can be temporary, task-scoped or persistent.

```text
"Research these five laptops"
→ temporary Research Worker

"Watch ClearLane CI tonight"
→ task Worker

"Manage SceneLab social media"
→ persistent Worker
```

Workers operate under OSCAR's Personal Policy and permission system. They can be created/edited through ordinary voice/chat and inspected through a lightweight management UI.

Persistent Workers use the Durable Execution Runtime for recovery/checkpoints rather than relying on one process remaining alive.

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

Workers may run in parallel, wait on dependencies, exchange Artifact/Result references and hand work off. OSCAR remains the top-level coordinator and resolves conflicts.

## Jev and Worker recovery

Workers should not escalate routine recoverable failures unnecessarily.

```text
Worker encounters issue
→ Jev evaluates
→ safe/confident self-fix? → repair/retry/verify
→ better capability exists? → reroute/delegate
→ otherwise ask OSCAR/user for minimum required intervention
```

Retries must be bounded. Workers must never invent success or silently switch to a more privileged capability path.

A Worker saying `done` produces a **reported result**, not automatic verified completion.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## Tool vs Skill vs Worker vs routine vs Protocol

### Tool

Primitive callable capability, e.g. `gmail.send`, `gpio.set`, browser click, terminal command, `codex.run`.

### Skill

Reusable learned procedure for achieving a goal, ideally portable and inspectable using ecosystem `SKILL.md` conventions where suitable.

### Worker

Delegated sub-agent that owns a scoped objective/job and may combine specialists, tools, devices and Skills.

### Routine

Recurring or simple event-driven behavior.

Examples:

- every morning prepare a concise agenda;
- when the laptop comes online, advertise Codex availability;
- at bedtime switch Sentry behavior.

### Protocol

Persistent, stateful autonomous responsibility that may wait, observe, branch, delegate, recover and escalate over time.

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
→ notify user only if blocked or verified complete
```

This is intentionally more capable than a basic scheduled action.

## Self-created Skills, Workers, routines and Protocols

OSCAR may create/propose reusable automation when:

- the user explicitly asks it to delegate or remember a workflow;
- a verified novel procedure is worth reusing;
- repeated behavior reveals a stable pattern;
- an existing Skill can be improved from a better verified path;
- an objective is large enough to deserve a temporary/persistent Worker.

Creation flow:

```text
objective/history
→ identify reusable responsibility/procedure
→ normalize parameters + preconditions
→ define required capabilities
→ define Personal Policy + permissions/risk
→ define verification
→ create Worker/Skill/routine/Protocol candidate
→ evaluate
→ promote / reject / keep experimental
→ activate within existing authority
```

Generated automation **cannot grant itself new permissions**.

## Learned Automation Evaluation Pipeline

One successful run can create a candidate. It does not automatically create a trusted/default automation.

Promotion pipeline:

```text
candidate
→ normalize / parameterize
→ replay/evaluate representative cases where possible
→ verify output + safety properties
→ compare against current version
→ permission/policy review
→ promote / reject / keep experimental
```

Candidates should preserve:

- source execution/provenance;
- assumptions/preconditions;
- required capabilities;
- evaluation cases/results;
- latency/cost/reliability metrics where meaningful;
- permissions/risk;
- limitations;
- rollback target/version.

Untestable candidates remain experimental/partially verified.

## Learning: first time vs next time

The first execution of a novel task may be exploratory and slow.

```text
first time
→ investigate environment
→ try suitable capability
→ recover from mistakes
→ verify success
→ capture path
→ candidate
```

Later, after promotion:

```text
same/similar task
→ retrieve known Skill
→ fill parameters
→ skip unnecessary discovery
→ use deterministic steps where possible
→ invoke AI only for uncertainty
→ verify
```

The goal is repeated tasks becoming measurably faster, cheaper and more reliable.

## Skill representation

Portable Skills should keep human-readable instructions and machine-readable metadata where practical.

A Skill should declare, where applicable:

- purpose;
- triggers/applicability;
- required capabilities;
- input parameters;
- preconditions;
- procedure;
- verification;
- permissions/risk class;
- failure/recovery strategy;
- provenance;
- version;
- evaluation status.

The schema should remain compatible with widely used `SKILL.md` conventions where possible rather than inventing an unnecessary closed format.

## Artifact / Result Model

Durable outputs should be represented as typed Artifacts/Results rather than hidden inside Worker text.

Examples:

- document/report;
- spreadsheet/slides;
- image/video/audio;
- code patch/commit/PR;
- deployment;
- meeting notes/transcript;
- firmware/hardware build;
- dataset/model/evaluation output.

Artifact records include, where useful:

- artifact ID/type/name;
- owner task/Worker/Protocol;
- producer capability;
- location/reference;
- version/hash;
- source/provenance;
- verification state;
- access scope;
- project/entity/task links;
- derived-from/supersedes links.

Workers hand off artifact references rather than repeatedly copying opaque payloads into prompts.

## Plugin/connector support

OSCAR should discover/use plugins/connectors exposed by host environments.

A plugin is not merely another menu item. It expands the Capability Catalog and may participate in learned Skills/Protocols/Workers.

Examples include mail, calendar, GitHub, cloud storage, knowledge tools, communication services and future third-party systems.

## Projects and specialist context

Workers often have useful context OSCAR should preserve rather than flattening into a prompt.

Examples:

- Codex project/repository context;
- plugin configuration such as Impeccable;
- IDE workspace state;
- Kinetable project/inventory;
- Notion/Obsidian workspace;
- GitHub repository/issues;
- social/account context through approved connectors.

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

- tests after code changes;
- browser/computer-use inspection after UI work;
- file/state checks after desktop actions;
- API/result checks after communication/social actions;
- sensor feedback after physical actions;
- deployment health checks after release.

If verification fails, OSCAR may retry, reroute or ask depending on policy.

If verification covers only part of the objective, the final state is `partially_verified`, not `verified`.

## Permissions and safety

Learning never overrides authorization.

A learned Skill/Protocol/Worker records required permissions; it does not create them.

Critical/destructive steps still follow OSCAR's policy layer, Voice Match rules and stronger confirmation requirements.

## Design target

OSCAR should gradually evolve from:

```text
"I can use these tools"
```

to:

```text
"I know the best verified way to accomplish this for this user, with these tools, in this environment, and I can delegate the work to the right team without claiming more than the evidence supports."
```
