# Orchestration, Learning, Skills, Workers and Protocols

OSCAR should not become a mediocre implementation of every specialist tool. Its job is to understand the objective, choose the best available capability, coordinate it, verify the result and learn from successful execution.

## Capability Catalog + Dynamic Tool Search

Every connected Worker, app, plugin, device, channel or service advertises capabilities through lightweight manifests.

Examples:

```text
Codex
- coding
- repository editing
- tests
- debugging

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
- camera/microphone
- location/context
- biometric approval

OSCAR Edge
- sensors
- GPIO
- displays
- relays
- motors
- Sentry events

Engineering applications
- CAD / circuit / simulation when installed or connected
- firmware toolchains
- diagnostics
- device provisioning
```

Capability metadata may include ID/name/summary, class, inputs/outputs, availability, surfaces, latency/cost, permissions/risk, reliability/history, project affinity, undo metadata and adapter/version.

OSCAR searches the catalog first and loads detailed contracts only for a small relevant candidate set.

## Routing by suitability

> Use the best available specialist for the objective, not the most general model.

Example:

```text
objective: build SceneLab landing page
  ↓
Jev classifies objective/context needs
  ↓
Capability Catalog finds
- SceneLab project/repository
- Codex
- Impeccable
- browser/computer-use verification
  ↓
OSCAR selects route
  ↓
Codex + design specialist execute
  ↓
OSCAR verifies visually/functionally
  ↓
Artifact/Result + possible learned Skill candidate
```

Other examples:

```text
coding               → Codex / coding specialist
notes/knowledge      → connected native knowledge tool
email/calendar       → structured service adapter
GUI-only workflow    → computer use
phone/app workflow   → Sunday
communication        → Channel Gateway + best native adapter
hardware design      → installed/connected engineering capability
physical action      → OSCAR Edge
research             → research capability + model reasoning when needed
cheap classification → Jev / fast model only when necessary
```

## Native model routing

Jev decides whether model reasoning is needed.

Only then does OSCAR's native Model Router choose an allowed provider/model based on suitability, capability, latency, cost, quality, availability and policy.

```text
Jev: reason
  ↓
OSCAR Model Router
  ↓
ChatGPT / another configured provider
```

The separate SwitchRoute project is reference/prototype material, not a required deployed service.

## Native transport

Cross-device/worker execution uses OSCAR's native Transport + Capability Fabric.

It carries typed task/event/action/result/progress messages to Sunday, desktop nodes, Edge, cloud/background executors and adapters.

The separate Latch project is reference/prototype material, not a required deployed service.

See [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md).

## Execution loop

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

For long work, OSCAR remains owner of the objective even while specialists perform steps.

## Durable Execution Runtime

Workers/Protocols/tasks that must survive process/device loss use Durable Execution Runtime.

It tracks task/objective ID, owner, lifecycle, checkpoint/current step, dependencies, executor lease/ownership, heartbeat, retry budget, cancellation, deadline, required capabilities, current surface, artifact/result refs, verification state and blocker/escalation state.

It provides checkpoints, bounded retries, heartbeats, reclaim, zombie detection, restart/resume, idempotency/deduplication and durable queues when justified.

Executive Planner decides **what should run and priority**. Durable Runtime makes execution survive safely.

## Workers

A Worker is a delegated sub-agent OSCAR creates for an objective or responsibility. It is not necessarily another generic model and does not inherently own a cloud computer.

A Worker may coordinate:

- Codex;
- Computer Use;
- browser/terminal/apps;
- Sunday/phone capabilities;
- plugins/connectors/APIs;
- Universal Channel Gateway;
- native OSCAR Model Router → ChatGPT/other providers;
- installed/connected specialist applications;
- OSCAR Edge.

Workers can be temporary, task-scoped or persistent and operate under Personal Policy/permissions.

See [WORKERS.md](WORKERS.md).

## Worker collaboration

OSCAR may create several Workers for one objective:

```text
Ship ClearLane release
├── Research Worker
├── Coding Worker
├── Design Worker
└── Release Worker
```

Workers may run in parallel, wait on dependencies, exchange Artifact/Result references and hand work off. Executive Planner remains the top-level coordinator.

## Jev and Worker recovery

```text
Worker encounters issue
→ Jev evaluates
→ safe/confident self-fix? → repair/retry/verify
→ better capability?       → reroute/delegate
→ otherwise                → ask for minimum intervention
```

Retries are bounded. Workers never invent success or silently escalate privilege.

A Worker saying `done` produces a **reported result**, not automatic verified completion.

## Tool vs Skill vs Worker vs Routine vs Protocol

### Tool
Primitive callable capability.

### Skill
Reusable learned procedure, preferably portable/inspectable using `SKILL.md` conventions where suitable.

### Worker
Delegated sub-agent owning a scoped objective/job.

### Routine
Recurring or simple event-driven behavior.

### Protocol
Persistent stateful responsibility that may wait, observe, branch, delegate, recover and escalate over time.

A Protocol may create Workers; a Worker may use Skills; a Skill may invoke Tools.

## Self-created automation

OSCAR may create/propose reusable automation when:

- user explicitly asks;
- a verified novel procedure is worth reusing;
- repeated behavior reveals a stable pattern;
- an existing Skill can be improved from a better verified path;
- an objective deserves a temporary/persistent Worker.

Creation flow:

```text
objective/history
→ identify reusable responsibility/procedure
→ normalize parameters/preconditions
→ define required capabilities
→ define policy/permissions/risk
→ define verification
→ create candidate
→ evaluate
→ promote / reject / keep experimental
→ activate within existing authority
```

## Teach by demonstration

Where authorized observation is technically available:

```text
"watch me do this once"
→ capture actions/context
→ infer stable intent/steps
→ ask about ambiguity
→ create Skill candidate
→ replay/evaluate
→ promote only after verification
```

Observed behavior never creates new authority.

## Learned Automation Evaluation Pipeline

One successful run creates a candidate, not automatically a trusted default.

```text
candidate
→ normalize/parameterize
→ representative replay/evaluation
→ verify outputs/safety
→ compare with current trusted version
→ policy/permission review
→ promote / reject / experimental
```

Preserve provenance, assumptions, limitations, metrics and rollback target.

## Artifacts as handoff

Workers and Protocols should pass typed Artifact/Result references instead of copying opaque outputs repeatedly through prompts.

This preserves producer, version/location, provenance, verification and ownership.

## Voice-driven orchestration

Voice commands enter the same task/orchestration contracts as text.

Voice Match may influence authorization; Voice Map may provide environmental/person context; neither changes task truth semantics.

Always-on Sentry acoustic awareness can trigger Protocol/Worker evaluation from compact local events without continuously uploading room audio.

## Invariants

1. OSCAR remains the top-level objective owner.
2. Specialist capability beats generic imitation.
3. Jev decides whether reasoning/delegation/retrieval/verification is needed.
4. Native Model Router selects concrete model/provider only after a model path is chosen.
5. Native Transport + Capability Fabric carries cross-device execution.
6. Latch/SwitchRoute are reference architectures, not required runtime services.
7. Persistent work uses Durable Runtime.
8. Worker/model/tool success remains reported until verified where verification matters.
9. Capability discovery is progressive.
10. Generated automation cannot self-grant authority.
11. Learned automation is evaluated before trusted promotion.
