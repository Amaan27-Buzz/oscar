# Workers

Workers are delegated sub-agents OSCAR creates and manages for specific responsibilities. They provide persistent-teammate capability similar to systems such as Grok Bot, but OSCAR uses the user's actual device/capability mesh rather than assuming every Worker owns a separate cloud computer.

## Product rule

> The user talks to OSCAR. OSCAR creates, coordinates and manages the team underneath it.

Workers are not separate assistant identities or chat silos. They operate under OSCAR's memory, World Model, Personal Policy, permissions, Executive Planner and task ownership.

## What a Worker is

A Worker is an objective envelope containing:

- goal/responsibility;
- relevant context;
- allowed capabilities;
- permission boundaries;
- preferred specialists/models;
- execution surfaces;
- durable state/lifecycle;
- verification requirements;
- escalation rules;
- memory/provenance;
- artifact/result references.

A Worker may use one or many tools/agents/devices.

Example:

```text
Worker: SceneLab Social
Goal: manage SceneLab social presence

Uses:
- X / LinkedIn adapters through Channel Gateway when available
- SceneLab GitHub/project context
- image generation
- research tools
- Sunday or desktop node when app-only access is required

Allowed:
- monitor mentions
- draft posts
- answer routine questions
- publish ordinary feature posts if Personal Policy permits

Ask first:
- major announcements
- commitments/promises
- controversial topics
- security/account changes

Escalation:
recover locally → reroute specialist → ask OSCAR/user if still blocked
```

## Worker types

```text
"Research these laptops."            → temporary Research Worker
"Watch ClearLane CI tonight."        → task Worker
"Manage SceneLab social media."      → persistent Worker
"Handle university scheduling."     → persistent responsibility Worker
```

Workers can sleep when idle and resume when triggers/objectives require them.

## Creation should be easy

The primary creation interface is ordinary voice or chat.

OSCAR should infer the initial Worker definition from the request, existing Personal Policy, current World Model/context and available capabilities.

For consequential autonomy, OSCAR summarizes resulting scope/permissions before activation when necessary.

## Device mesh, not mandatory cloud desktops

A Worker does not inherently own a virtual machine.

It plans against currently available OSCAR capabilities:

```text
Sunday
- phone apps
- calls/messages
- notifications
- camera/location

Desktop machine node
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
- native OSCAR Model Router → ChatGPT / other allowed providers
- APIs/plugins/connectors
```

The same Worker may move execution between these surfaces as availability changes.

No Worker should silently switch to a more privileged execution path merely because another path failed.

A future cloud Worker computer may exist as another advertised capability, but it is not foundational.

## Workers orchestrate specialists

A Worker is not necessarily another generic LLM.

```text
Coding Worker      → Codex + repository + tests
Design Worker      → Codex + Impeccable + visual verification
Research Worker    → research capability + native model routing when useful
Phone Worker       → Sunday
GUI Worker         → Computer Use
Hardware Worker    → OSCAR Edge + installed engineering/device tools
Social Worker      → Channel/API/plugin/browser/phone capabilities
```

The Worker owns the objective; the specialist owns execution expertise.

## Capability discovery

Workers should not carry every tool/plugin/Skill definition in context.

They query OSCAR's Capability Catalog, rank candidates by suitability/availability/policy/reliability/latency/cost, and load detailed contracts only for relevant finalists.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Parallel collaboration

OSCAR may create multiple Workers for one objective:

```text
Objective: ship OSCAR Desktop

OSCAR Executive
├── Research Worker
├── Coding Worker
├── Design Worker
└── Test Worker
```

Workers can exchange Artifact/Result references, hand work off, wait on dependencies, run independently in parallel and report structured progress/evidence.

The Executive Planner remains the top-level coordinator and resolves conflicts/priorities.

## Durable Execution Runtime

Persistent/task Workers use OSCAR's Durable Execution Runtime so responsibility does not disappear when a process/device/executor dies.

Durable Worker state includes, where relevant:

- Worker ID/name;
- objective;
- lifecycle state;
- current step/checkpoint;
- owner Protocol/task;
- dependency state;
- executor lease/heartbeat;
- context references;
- capability requirements;
- permission scope;
- retry budget/backoff;
- cancellation state;
- completion condition;
- verification state;
- blocker/escalation state;
- artifact/result references.

The runtime provides persisted checkpoints, heartbeats, lease expiry/reclaim, stuck/zombie detection, restart/resume, bounded retries and idempotency/deduplication where needed.

A Worker must not remain indefinitely `Working` because its executor vanished.

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
          no  → ask OSCAR/user for minimum intervention
```

Retries are bounded. Workers never invent success.

## Epistemic integrity

A Worker's `success` response is **reported evidence**, not automatically verified completion.

```text
Worker reports done
→ OSCAR inspects evidence/result
→ independent verification where practical
→ verified / partially_verified / failed / blocked / unknown
→ report only that state
```

Workers should return structured results including execution status, evidence refs, Artifact/Result refs, limitations, blockers and suggested verification method.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## Worker vs Tool vs Skill vs Routine vs Protocol

| Concept | Meaning |
|---|---|
| Tool | Primitive callable capability |
| Skill | Reusable procedure for doing something |
| Worker | Delegated sub-agent responsible for an objective/job |
| Routine | Recurring/simple behavior |
| Protocol | Stateful persistent responsibility/process |

A Protocol may create Workers. A Worker may use Skills. A Skill may invoke Tools.

## Social-media management

Workers may manage social media when connected capabilities and permissions permit.

Potential responsibilities include monitoring mentions/replies, research, drafting posts, preparing media, scheduling/publishing permitted content, routine replies, release coordination and summarizing feedback/performance.

Personal Policy controls what may happen without confirmation.

## Learning

```text
novel Worker task
→ explore
→ execute
→ verify
→ distill candidate Skill
→ evaluate/replay where possible
→ promote / reject / keep experimental
→ future Workers reuse promoted Skill
```

A learned Skill may be shared by multiple Workers when scope/permissions are compatible. Generated automation cannot broaden authority on its own.

## Artifact / Result handoff

Workers exchange typed Artifact/Result references for durable outputs instead of copying large opaque payloads through prompts.

Artifacts preserve producer, location/version, provenance, owner task/Worker and verification state.

## UI

Workers need a simple management surface, not an agent-dashboard wall.

Example:

```text
Workers

SceneLab Social      Active
ClearLane Release    Waiting for CI
University Admin     Idle
Research             Verifying
```

Opening a Worker should show current responsibility, execution surface, checkpoint, usable capabilities, autonomy boundaries and verification state.

Users can create, pause, resume, edit or remove Workers using UI or natural language.

## Permissions and audit

Workers inherit only explicitly available OSCAR capabilities/permissions.

They cannot self-grant permissions, bypass Personal Policy/approval gates or silently adopt a more privileged identity.

Consequential actions remain attributable to OSCAR task/Protocol, Worker, capability/tool, initiating user/policy, timestamp/result and verification evidence.

## Invariants

1. Workers belong to OSCAR; they are not separate assistant silos.
2. Workers use the best available real device/service capability instead of requiring a cloud computer.
3. Creation/editing work through normal voice/chat.
4. Jev enables self-repair/rerouting before unnecessary escalation.
5. Workers can collaborate while Executive Planner owns global coordination.
6. Persistent Workers use durable execution state/recovery semantics.
7. Workers search capabilities progressively rather than loading every tool definition.
8. Worker `success` is reported evidence until verified.
9. Workers may use/create Skills and participate in Protocols, but cannot broaden permissions.
10. Worker state/progress/evidence remain inspectable.
11. Temporary Workers retire when complete; persistent Workers remain only for continuing responsibility.
12. Model reasoning is accessed through OSCAR's native Model Router, not by depending on a separate SwitchRoute runtime.
13. Cross-device execution is carried by OSCAR-owned transport/capability contracts, not a separately required Latch service.
