# Orchestration, Learning, Skills, Workers and Protocols

**Current delivery (2026-10-18):** [checked status](CURRENT-STATUS.md) and [delivery groups](DELIVERY-PLAN.md). The existing local Worker/Executive is **software integrated**, but remote Workers, native schedule authoring, real provider-connected automation and Secure/Full Access are not accepted. Group 5 completes them after Group 4 remote Grid.

## Group 3 software — 2026-10-16 (PR #7 merged 2026-10-17)

The [Executive runtime](EXECUTIVE-RUNTIME.md) now supplies reviewed commitments,
typed/model-assisted plan candidates, scoped Worker assignment/reservations,
durable one-time/recurring scheduling, exact-task retries, cancellation and
recovery through existing Runtime/Dispatcher. Current context predicates, reviewed
replanning and read-only briefs preserve freshness/authority. Workflow learning
requires separate retention and independently verified replay; its canonical
events remain distinct from current state. Native surfaces expose readback;
native activation/editing controls remain unavailable. This supersedes the dated
future-integration wording below only for this implemented bounded scope.

## Group 2.5 owner correction — 2026-10-14 (historical planning context)

Conversation is the one owner interaction point. Controller, Memory Fabric, Executive, Durable Runtime and Grid retain their established ownership. Tools, Skills, Routines, Workers and Protocols remain different internal concepts; Automations offers concise responsibility/lifecycle inspection instead of a second agent framework.

Future automation records must link trigger/schedule, responsibility, Worker/Protocol, task, authority grant/epoch, checkpoint and verification evidence. Creation, pause/resume, changes and removal require real Core commands and readback. Existing exact-action execution plus Group 3 **bounded durable Executive planning, Worker scopes/schedules and recovery** are integrated; native responsibility creation/editing, live contextual integrations and generalized autonomous lifecycle remain future work. Access mode, Worker autonomy, awareness and retention must travel as distinct contracts.

See [the interaction and authority decision](decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) for ownership, implemented boundaries and required integrations. Earlier dated checkpoints remain historical.


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

OSCAR Mobile
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
Controller classifies objective/context needs
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
phone/app workflow   → OSCAR Mobile
communication        → Channel Gateway + best native adapter
hardware design      → installed/connected engineering capability
physical action      → OSCAR Edge
research             → research capability + model reasoning when needed
cheap classification → Controller / fast model only when necessary
```

## Native model routing

Controller decides whether model reasoning is needed.

Only then does OSCAR's native Model Router choose an allowed provider/model based on suitability, capability, latency, cost, quality, availability and policy.

```text
Controller: reason
  ↓
OSCAR Model Router
  ↓
ChatGPT / another configured provider
```

The separate SwitchRoute project is reference/prototype material, not a required deployed service.

## Native transport

Cross-device/worker execution uses OSCAR's native Transport + Capability Fabric.

It carries typed task/event/action/result/progress messages to OSCAR Mobile, desktop nodes, Edge, cloud/background executors and adapters.

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
- OSCAR Mobile/phone capabilities;
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

## Controller and Worker recovery

```text
Worker encounters issue
→ Controller evaluates
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
3. Controller decides whether reasoning/delegation/retrieval/verification is needed.
4. Native Model Router selects concrete model/provider only after a model path is chosen.
5. Native Transport + Capability Fabric carries cross-device execution.
6. Latch/SwitchRoute are reference architectures, not required runtime services.
7. Persistent work uses Durable Runtime.
8. Worker/model/tool success remains reported until verified where verification matters.
9. Capability discovery is progressive.
10. Generated automation cannot self-grant authority.
11. Learned automation is evaluated before trusted promotion.
