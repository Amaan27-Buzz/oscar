# Workers

## Group 3 runtime — 2026-10-16

Named Worker scope and lifecycle now compose through the existing Core, Grid,
Dispatcher and canonical Tasks. Exact capability contracts, independent grants,
current policy and one live reservation per Worker constrain execution. Real
local files/arithmetic, concurrent admission, revocation, loss/restart and
ambiguous-result blocking are tested. Schedules run only while Core is active;
no fake cloud Worker or standing Full Access is created. See
[Executive commands, evidence and limitations](EXECUTIVE-RUNTIME.md).

## Group 2.5 owner correction — 2026-10-14

OSCAR is the sole personal intelligence and top-level coordinator. Named Workers/specialists carry subordinate responsibilities, never independent conversation identities. Automations is the management view for one-time delegated jobs, schedules, event triggers, watches, persistent Workers, supervised/autonomous Workers and continuing Protocols; conversation is the primary creation/instruction interface. A manually prepared file write remains immediate tool use.

Worker autonomy (Manual / Supervised / Autonomous) is independent of Ask / Secure / Full Access and awareness. Every Worker inherits and rechecks Core authority. Full Access will use owner delegation rather than per-action approvals; Workers cannot activate it themselves. Current runtime/task/cancellation/recovery foundations do not implement the complete persistent named-Worker scheduler or management lifecycle. Unsupported controls are absent.

See [the interaction and authority decision](decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) for ownership, implemented boundaries and required integrations. Earlier dated checkpoints remain historical.


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
- OSCAR Mobile or desktop node when app-only access is required

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
OSCAR Mobile
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
Phone Worker       → OSCAR Mobile
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

## Controller and autonomous recovery

Workers should not bother the user for routine recoverable problems.

```text
Worker encounters issue
        ↓
Controller evaluates
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
4. Controller enables self-repair/rerouting before unnecessary escalation.
5. Workers can collaborate while Executive Planner owns global coordination.
6. Persistent Workers use durable execution state/recovery semantics.
7. Workers search capabilities progressively rather than loading every tool definition.
8. Worker `success` is reported evidence until verified.
9. Workers may use/create Skills and participate in Protocols, but cannot broaden permissions.
10. Worker state/progress/evidence remain inspectable.
11. Temporary Workers retire when complete; persistent Workers remain only for continuing responsibility.
12. Model reasoning is accessed through OSCAR's native Model Router, not by depending on a separate SwitchRoute runtime.
13. Cross-device execution is carried by OSCAR-owned transport/capability contracts, not a separately required Latch service.

## Club B POSIX reference machine foundation

`oscar.machine` composes real executors with the existing Dispatcher/Grid/Runtime.
Allowed filesystem root uses the existing directory-FD ScopedFiles; traversal and
symlinks are rejected. Capabilities include bounded file read/write/list/filename
search, configured executable/agent discovery and, with explicit `machine:host`
permission/configuration, terminal/Git/repository tasks and discovered CLI agents.
No power capability is advertised. The repository reference task creates one new
file in a clean Git repository and commits it; Core independently checks exact
file bytes, HEAD tree, new commit identity and clean status.

**Terminal/agent scope is trusted host execution, not an OS sandbox.** A configured
executable such as Python can access host resources beyond cwd. It is disabled
unless the owner opts into trusted execution; do not pair an untrusted principal
with `machine:host`. Isolated OS/container/user execution remains future deployment
work. Git hooks/signing/global config are disabled for reference work; this does
not make arbitrary hostile repositories safe.

Processes use explicit cwd, executable allowlist, timeout, bounded output,
filtered environment and process-group cancellation. Progress carries native
correlation/lease IDs, renews the current lease and stores content-free checkpoints.
HTTP pause/resume/cancel uses existing authenticated transport; pause is cooperative
between file/Git steps and SIGSTOP/SIGCONT for a running POSIX subprocess. Timeouts
include paused wall time. Completed lost results are recovered through existing
durable deduplication; started/crash-ambiguous actions require inspection, not
blind replay. Scope, correlation, nonce and stale owner checks remain at the target.

`python -m scripts.verify_worker_reference` runs Core plus a separate Worker
process over real loopback HTTP with temporary Git/SQLite state. A lost result,
Core/Worker restart, reconnect/reclaim, completed duplicate replay, authoritative
Git/file verification, HTTP controls and mid-command disconnect are exercised.
This is **reference network Worker verification**, with shared SQLite authority.
Independent stores, public TLS/outbound rendezvous, Windows/user-machine runtime,
GUI/browser work and real coding-agent task acceptance remain **UNVERIFIED**.
Installed agent `--version` proves invocation only, not authenticated coding work.

## Windows local-alpha Worker — 2026-10-04

Windows uses `WindowsScopedFiles`, not POSIX directory-FD emulation. It rejects
traversal, drive/UNC/device/alternate-stream aliases and all encountered reparse
points, including junctions and parent/leaf symlinks. Ancestors are opened with
`CreateFileW`, `OPEN_REPARSE_POINT`, read access and no delete sharing for the
operation; real tests prove pinned directories cannot be renamed. File writes
use a flushed temporary file and entry replacement. This assumes a trusted local
workspace, not a hostile filesystem or OS sandbox.

Only configured absolute native `.exe` paths run, without a shell. Windows jobs
start suspended, are assigned to a non-inheritable Job Object with
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, then resume through documented thread APIs.
Assignment failure rejects execution. Descendants cannot opt into breakaway.
Cancellation, timeout, output failure, parent exit and abrupt Worker OS-process
death close the job and terminate its process tree. Output drains through a
bounded pipe-reader queue; environment inheritance uses an explicit allowlist.
Codex gets its own explicitly configured `CODEX_HOME`, not OSCAR provider keys.
Native Codex binaries can be configured directly; `.cmd`/`.ps1` shims do not run.

Windows pause means **before the next subprocess**, including an initially paused
task. A currently running arbitrary Windows process is not suspended. Control
acknowledgments expose `pause_semantics`; file atomic operations are not pausable.
Timeout includes pre-start paused wall time. Cancellation remains available while
paused. POSIX process-group pause behavior is preserved independently.

The useful Codex objective repaired a nested interval merge in a disposable repo.
Its report stayed REPORTED. Core independently checked nine behavioral cases,
input immutability, invalid-input rejection, sole-file Git diff and baseline HEAD
before VERIFIED. Lost result/restart recovery kept the same artifact hash and one
execution. Real Codex cancellation and invalid invocation were exercised separately.
See [local acceptance evidence](evidence/club-b-windows-2026-10-04.json) and
[checkpoint](CLUB-B-CHECKPOINT.md). Browser and Notepad/UIA now have current laptop evidence in the [completion ledger](GATE-B-COMPLETION.md). Independent node stores, public remote transport, power and phone supervision remain unverified.

Windows API research uses Microsoft's [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and [reparse/file operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations)
contracts; platform claims above additionally require the recorded actual laptop tests.

## Gate B local completion candidate — 2026-10-04

InteractiveWorker composes typed PowerShell, application IDs, UIA and browser operations with existing Worker leases/dedup/Job Objects. Discovery is not launch authority: app IDs and selected executables require explicit allowlists. Browser capability is advertised only after the selected interpreter loads the actual source-anchored OSCAR package entrypoint and launches/closes Chromium. The artifact cwd remains scoped; no editable install or global PYTHONPATH is required. Bounded failures retain allowlisted diagnostic metadata only. See [the browser launch repair](GATE-B-HARDENING.md). Browser artifact creation uses pinned directories and native CREATE_NEW; anonymous anchor downloads enforce streaming bounds. App activation can broker into an existing user process and is not contained by a new Job. Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

## Current Slice 08 — 2026-10-06

Owner closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
Quality candidate is under validation in PR #14. Gate C remains PARTIAL.
See [Voice Core](VOICE-CORE.md), [quality pass](VOICE-QUALITY.md) and
[consolidated acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 software is authorized after Slice 08 integration; device acceptance is
owner-deferred. This statement describes the historical Slice 07/08 acceptance boundary. Current Slice 10 Desktop runtime is a draft PR; deployment and Home Node remain deferred. See [canonical numbering](SLICE-NUMBERING.md).
