# Runtime Foundations

This document defines five cross-cutting primitives identified during the competitive review of VoiceOS, ChatGPT/Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi.

These are not separate products or agent silos. They are infrastructure that lets OSCAR scale without turning the core into a giant prompt or a brittle collection of one-off integrations.

Transport and model routing are also OSCAR-owned native infrastructure; see [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md).

## 1. Universal Channel Gateway

OSCAR should not hard-code every communication surface independently forever.

The Channel Gateway provides one normalized inbound/outbound abstraction for channels such as phone/SMS where supported, WhatsApp, Telegram, Signal, Discord, work channels, email, social DMs/replies and future adapters.

Each adapter maps native platform capabilities into a common envelope:

```text
ChannelEvent
- channel_id
- account_id
- conversation/thread ID
- canonical participant/entity IDs
- sender / recipients
- direction
- message/call/event type
- text/transcript/media references
- timestamps
- reply/action capabilities
- permission/risk metadata
- source-specific IDs
```

The gateway is not allowed to pretend all channels support the same operations. Capability discovery remains explicit.

Integration order:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

Channel events feed the entity graph, World Model, LRA and Personal Policy as appropriate.

## 2. Durable Execution Runtime

Workers, Protocols and long-running objectives need a runtime that survives process restarts, device loss and temporary provider failure.

The Durable Execution Runtime owns execution mechanics, not high-level intelligence.

A durable task can carry task/objective ID, owner, lifecycle state, checkpoint, dependencies, lease/ownership, heartbeat, retry budget, cancellation, deadline, required capabilities, current surface, artifact/result refs, verification state and blocker/escalation state.

Core lifecycle states can include:

```text
queued
running
waiting
blocked
verifying
completed
failed
cancelled
abandoned/reclaimable
```

### Recovery

The runtime should support persisted checkpoints, bounded retries/backoff, heartbeats, lease expiry/reclaim, zombie detection, restart/resume, compensation hooks when real, idempotency/deduplication and durable queues/event delivery where warranted.

A task must never remain forever in `working` because its executor disappeared.

### Separation of concerns

```text
Executive Planner → decides what should run and priority
Durable Runtime   → makes work survive and progress safely
Worker            → owns/delegates objective-specific work
Capability        → performs concrete operation
Action Ledger     → records consequential changes + verification
```

## 3. Capability Catalog + Dynamic Tool Search

OSCAR may eventually have hundreds or thousands of tools, Skills, plugins, device capabilities and specialist applications. Loading every definition into every model context is not scalable.

Every capability should have a lightweight searchable manifest containing fields such as:

```text
id
name
summary
capability class
inputs/outputs
required permissions
risk level
supported surfaces
latency/cost hints
reliability/history hints
availability
project/workspace affinity
reversible/undo metadata
adapter/provider owner
version
```

Jev/Workers search the catalog first and load the detailed contract only for a small relevant candidate set.

Conceptual flow:

```text
objective
→ typed intent / required capability classes
→ capability search
→ rank by suitability + availability + policy + reliability + cost/latency
→ load detailed contracts for finalists
→ execute specialist
```

This is **progressive capability loading**, not a mega-prompt.

The catalog includes:

- native OSCAR transport/node capabilities;
- Sunday/device capabilities;
- desktop machine capabilities;
- Edge hardware actions;
- plugins/connectors;
- `SKILL.md` Skills;
- external specialist agents/apps;
- Channel Gateway adapters;
- installed/connected engineering tools;
- model-provider capabilities exposed through the native OSCAR Model Router where appropriate.

## 4. Learned Automation Evaluation Pipeline

OSCAR can create or improve Skills, routines and Protocols, but generated automation should not be promoted merely because one exploratory run succeeded.

```text
successful execution
→ candidate extraction
→ normalize/parameterize
→ replay/evaluate representative cases
→ verify expected output + safety properties
→ compare against current version
→ permission/policy review
→ promote / reject / keep experimental
```

A candidate should record source provenance, assumptions/preconditions, required capabilities, evaluation cases, success/failure metrics, latency/cost where meaningful, permissions, known limitations and rollback target/version.

### Promotion rules

- One success can create a candidate, not automatically a trusted default.
- New versions should not silently replace a more reliable Skill.
- Safety/permission requirements are never weakened by learning.
- If evaluation is impossible, label the Skill experimental/partially verified.
- Learned automation can be rolled back when reliability regresses.

## 5. Artifact / Result Model

OSCAR should treat finished outputs as first-class objects rather than burying them in chat history.

Examples include documents, spreadsheets, slides, media, code changes, research, meeting notes, design assets, deployments, firmware builds and datasets/models/evaluations.

A standard artifact record should include:

```text
artifact_id
kind
name
owner task/Worker/Protocol
producer capability
location/reference
version
created/updated time
source/provenance
verification status
content hash/version ID where useful
permissions/access scope
relationships to projects/entities/tasks
supersedes / derived-from links
```

Workers should pass artifact references rather than repeatedly copying opaque blobs through prompts.

## Relationship to the rest of OSCAR

```text
User / Environment
        ↓
Perception Fabric → World Model
        ↓
       Jev
        ↓
Executive Planner
        ↓
Durable Execution Runtime
        ↓
Workers / Protocols / Skills
        ↓
Capability Catalog + Tool Search
        ↓
Capabilities / Channels / Devices / Specialists
        ↓
Action Ledger + Artifact/Result Model
        ↓
verify → memory/world model → report
        ↓
OSCAR Transport + Capability Fabric when cross-node work is needed
```

Running through all of it:

- Epistemic Integrity;
- Personal Policy;
- permissions;
- entity graph;
- audit/provenance;
- learning/evaluation;
- voice/privacy rules where acoustic data is involved.

## Invariants

1. Channels are normalized without erasing platform-specific limits.
2. Long-running work has durable state, bounded retries and reclaim/recovery semantics.
3. Capability definitions are discovered progressively rather than globally loaded.
4. Learned automation is evaluated before trusted promotion.
5. Artifacts/results are typed objects with provenance/verification state.
6. None of these primitives can self-grant permissions.
7. The core remains small: explicit contracts rather than one giant orchestration framework.
8. Native OSCAR transport/capability contracts replace any requirement for a separately deployed Latch runtime.
9. Native OSCAR Model Router replaces any requirement for a separately deployed SwitchRoute runtime.
10. Engineering/design tools are ordinary replaceable specialist capabilities; no dedicated workbench product is required.

## Club B reference continuation and privacy

The native runtime now accepts explicit structured capability objectives through
Jev, preserving the existing durable task/plan/Action/Result/evidence path. Grid
renewal fences the current unexpired lease; Worker progress stores metadata-only
checkpoints. Authenticated pause/resume extends the existing version-1 envelope
additively; older targets reject unsupported controls. No storage migration or
second task engine was introduced. Completed response loss can reclaim the same
Action and reuse durable dedup results. Started ambiguous mutations cannot replay.

Connector private inputs are staged as transient references. Losing active input
context blocks instead of recovering private content from durable history. Worker
process logs and connector bodies never become generic router/ledger telemetry.
Memory retention is selected separately. See [CLUB-B-CHECKPOINT.md](CLUB-B-CHECKPOINT.md).

## Gate B local completion candidate — 2026-10-04

OwnerControl uses existing Grid/Runtime leases, target-scoped owner grants and separate processes. Cancellation atomically rechecks executor identity in the task transition. Windows pause is cooperative before the next subprocess, not arbitrary process suspension. Canonical consolidation has bounded durable checkpoints; failure rolls back the checkpoint and evidence merge together. Derived generations are invalidated after consolidation and rebuilt explicitly. Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).
