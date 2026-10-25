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

### Conversation action routing

Desktop and authenticated Grid conversation use the same planner route. Stacked
courtesy phrases such as "could you please" are removed before the existing action
and explicit Worker/device grammar. Questions and recall stay outside this action
route. Normalization adds no authority: memory preflight, Ask review and exact
standing delegation still govern every model disclosure and effect.

### Private connector arguments

Conversation planning can select current account-bound reviewed MCP tools and
native HTTPS operations. MCP arguments follow reviewed tool schemas; HTTPS
arguments follow the existing fixed endpoint envelope, with exact owner review
of the body. Core stages arguments
before saving the model result, and Executive steps retain only opaque references.
An exact signed plan review shows the private arguments without retaining its raw
payload in the canonical store. Ask still requires applicable action confirmation,
available through the existing signed review in Desktop and Android;
signed Full Access must cover the executor, capability and account generation.
These one-shot immediate calls expire after 120 seconds and remain only reported
unless an independent verifier exists. They cannot become observation evidence or
implicitly authorize another account. See [Connector Fabric](CONNECTOR-FABRIC.md#model-authored-connector-execution).

### Verified observations and private continuation

Reviewed adaptive conversation planning may request a pure observation stage
with `{"steps":[...],"observe":true}`. The current text boundary accepts one to
four scoped `machine.files.read` reads, `math.add` calculations or `machine.apps`
registered-target queries, without effects or result substitutions. App queries use
only `{"request":{"operation":"targets","query":"name"}}`: up to eight
currently registered targets with bounded names, availability and launch authority,
explicit truncation, and no executable paths or unregistered app inventory. A
separate native query must match before Core verifies this observation. A single
temporary Worker persists through observation,
private replanning and final action review. Completing an observation does not
complete the original objective.

Ask reviews the exact observation, model continuation and final effects. Matching
signed Full Access advances those same stages without per-action prompts. Both
recheck current owner/executor sessions, capability contracts, Personal Policy,
delegation and evidence before model disclosure and effects. References belong
to the same reviewed continuation and owner. Three observation stages are the
maximum; observations expire after 120 seconds. Unverified, changed, oversized or
known credential-bearing output cannot enter the continuation. Each result is
limited to 4 KiB and total encoded context to 16 KiB.

The initial review discloses the selected private model sources. Raw tool data is
attached transiently at model execution; canonical planning prompts retain exact
result/evidence references. The model treats observations as untrusted data and
returns a new validated plan; data cannot grant authority. New dependencies refer
only to steps in that response. Arbitrary tool feedback, semantic objective
verification and unrestricted discovery remain outside this bounded loop.

Selected `machine.screen` captures can now be observation stages. Core separately
reads the exact retained PNG artifact in 6,000-byte chunks, validates its framing,
checksums, pixel stream, dimensions and SHA-256, and pins the result/evidence.
VERIFIED means those captured bytes were inspected, not that depicted text is true.
The bounded text context carries metadata and target identity; image bytes travel
as typed private model input, never as instructions or canonical planning text.
Current capture/retention permissions, owner, executor, policy, delegation and
provenance are checked again at disclosure. Withdrawal blocks continuation.

Vision currently routes only to configured local Ollama models explicitly
advertising `vision` with LOCAL funding. Hosted vision is unavailable. Admission
conservatively reserves one input token per pixel in addition to prompt bytes;
large screenshots may exceed the selected model's context and fail closed.
Core accepts non-interlaced 8-bit RGB/RGBA PNGs up to 1 MB and 4096 by 2160 pixels,
matching the existing native capture bounds. Model context admission is separate.
At most four images enter a request. The model executor holds at most 16 PNGs,
usable for 120 seconds; shutdown clears that cache. Core restart or cache loss
requires a fresh capture, never replay of a prior effect. Worker artifacts and
authenticated transport receipts remain retained under the capture's retention
grant; cache expiry is not deletion of those retained records.

The resulting visual plan uses existing exact-frame native input. Target-side
recapture rejects changed pixels, geometry, identity or foreground before one
click. A click report remains PARTIAL until objective-specific independent
readback establishes the outcome. Synthetic HTTP planning acceptance and installed
model image accuracy are separate evidence.

When `machine.desktop` is separately selected, a plan may explicitly request
`focus_window` with the same registered, bound handle/PID before input. This is
an authorized action, never an implicit side effect of screenshot capture or
clicking. A separate read-only `focus_check` process returns only the actual
foreground window/process identity; Core compares it with the selected target.
Verified focus can release a dependent click, whose native guard still checks
foreground, obstruction and exact pixels again. Focus is momentary and can be
withdrawn by user/OS activity. No focus bypass or automatic click retry is added.

Ollama image requests use its documented `/generate` API. A local reproduction
showed Qwen chat returning fenced Markdown despite `format:json` with thinking
disabled; `/generate` enforced JSON on the same synthetic image. Strict JSON,
coordinate and target checks remain mandatory; formatted output can still be wrong.

The model may propose a native app launch using a discovered exact target ID and
an optional existing scoped artifact. Current native allowlists, supported launch
operations, executable availability and permissions are rechecked at execution.
Observation cannot grant launch authority. Launch reporting remains partially
verified; a broader app objective still needs its own independent resulting-state
check. Adaptive prompts include a complete read-only response example; examples
never expand the selected capabilities or authorize their placeholder arguments.

## Selected-window control observations

`machine.controls` exposes a bounded UIA view of an already registered, bound
Windows target. Its separate contract requires host/control, capture and retention
grants. The Desktop sharing option never grants those scopes; an enrollment that
lacks them cannot enable it. The exact positive window handle/PID and a label
substring identify the query. No global desktop inventory is disclosed.

At most eight controls and 4 KiB are returned, with runtime IDs, bounded labels
and nonpassword text. Coverage is explicitly limited by the native tree scan and
truncation; absence is not proof that a control does not exist. A separate native
observer repeats the selected query before private replanning. Current authority,
source provenance and the normal observation expiry are rechecked before I/O.
Edits use the separately selected `machine.desktop` contract, including its
expected-text check and independent readback; inspection cannot actuate controls.

This supports inspection → private replan → checked edit in one Worker. The
window must already be selected and bound; arbitrary app discovery and visual
reasoning are separate work. Current-information action goals use the live-read
preflight below; pure live-state questions retain Controller retrieval routing.

## Live-information execution preflight

The Ollama decoding schema leaves the instruction text upper bound to Executive's
authoritative 4,096-character validation. Encoding that limit as a grammar repeat
was rejected by the installed runtime. Other decoding structure, output budgets,
typed intent validation, native admission and signed authority remain enforced.

Current/live action goals require adaptive private continuation and at least one
selected file, directory, app, bound-window or anonymous browser reader. Manual
planning defaults these goals to adaptive stages and includes that disclosure in
the signed review. Explicitly disabling stages or lacking a private route blocks
planning before model I/O. The first accepted response must contain only supported
read observations; a direct effect, arithmetic or recalled history cannot satisfy
this gate. Pure current-information questions retain the ordinary retrieval route.

Initial current-information planning shows only selected readers and their read
examples. For structured Ollama planning, phase-specific decoding requests one
initial read (or clarification), pins its capability/kind and narrows file/app/
control parameter shapes. Anonymous browser step semantics still require native
validation. This is an output constraint, never authority or proof of meaning.
After independent verification, private continuation restores the reviewed effect
capabilities and normal adaptive schema. Later stages retain the existing one-to-
four observation and three-stage limits. Other adapters retain their supported
structured-output contract and deterministic admission checks.

After independent verification, source IDs, observation times and expiry accompany
the bounded values. Existing provenance, authority, private-routing and 120-second
stage-expiry checks apply before continuation and effects. These are observations
as of capture, not a guarantee that the world remains unchanged. The gate verifies
the source class, not semantic relevance or model accuracy. Checked native edits
also compare expected text before mutation. Public search and connector context
are not yet supported observation-stage inputs; an unavailable relevant reader
must produce clarification rather than invented facts.

## Scoped file discovery observations

Adaptive Workers can list one authorized directory or search its filenames, then
use separately verified names to choose the next read. Existing scoped-file
implementations enforce directory/reparse boundaries and scan/result limits.
Search uses a filename substring, not a glob or recursive content search. Both
remote execution and independent readback reject more than 4 KiB of names; no
silently truncated inventory reaches planning. A changed listing fails exact
comparison. Current file-read authority and the same private-continuation
checks apply before model disclosure and effects. This enables discovery → read
→ act within one Worker, without granting arbitrary terminal output as context.

## Anonymous browser observations

Adaptive Workers can read a scoped static page and independently repeat the read
before private replanning. This uses the existing browser executor with an exact
`read_only: true` request: one granted origin, navigate then inspect, at most
15 seconds and 2,048 text characters. A fresh anonymous context disables page
JavaScript, permits only GET/HEAD on that origin and cannot attach an account
profile or an effect-verification receipt. Text/title truncation is explicit;
dynamic pages may be incomplete. A changing second read fails verification.

Page content remains untrusted source data. Current observation authority,
freshness, signed Ask reviews or matching Full delegation, private model routing
and final effect authorization all remain required. Navigation is a scoped web
read; it cannot guarantee that a server implements GET without side effects.
Authenticated browser workflows and submissions use their existing effect path.

## Memory-dependent execution

Execution requests can pass Controller memory preflight and continue into the
same reviewed Worker. This requires the current Core `memory.recall` capability,
independent `memory:read` permission and, for Full Access, explicit standing
coverage of recall as well as the selected actions. Pure recall, live-state and
verification questions retain their Controller routes.

Before planning, bounded sourced recall selects at most 8 KiB of history.
Only private model routes may receive it. Values retain their actual epistemic
and source states; history is untrusted data, never current truth or permission.
Durable plans and continuation goals retain source IDs and digests rather than
another copy of memory content. Each model boundary and effect rechecks current
recall authority, the selected capability contract and canonical retrieval/source
digests. Forgetting, correction, expiry, policy denial or source drift stops the
pending work. Empty retrieval is UNKNOWN and blocks dependent execution; it does
not prove no relevant history ever existed. Verified tool observations can be
combined with recalled history without promoting the latter into verified truth.

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
