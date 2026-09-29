# Runtime Foundations

This document defines five cross-cutting primitives identified during the final competitive review of VoiceOS, ChatGPT/Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi.

These are not separate products or agent silos. They are infrastructure that lets OSCAR scale without turning the core into a giant prompt or a brittle collection of one-off integrations.

## 1. Universal Channel Gateway

OSCAR should not hard-code every communication surface independently forever.

The Channel Gateway provides one normalized inbound/outbound abstraction for channels such as:

- phone/SMS where platform support exists;
- WhatsApp;
- Telegram;
- Signal;
- Discord;
- Slack/Teams-style work channels;
- email;
- social DMs/replies;
- future communication plugins/connectors.

Each adapter maps native platform capabilities into a common envelope:

```text
ChannelEvent
- channel_id
- account_id
- conversation/thread ID
- canonical participant/entity IDs
- sender
- recipients
- direction
- message/call/event type
- text/transcript/media references
- timestamps
- reply/action capabilities
- permission/risk metadata
- source-specific IDs
```

The gateway is not allowed to pretend all channels support the same operations. Capability discovery remains explicit.

Example:

```text
telegram.message.send        available
whatsapp.call.answer         unsupported on this surface
email.thread.reply           available
signal.message.read          unavailable
```

The integration order remains:

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

A durable task should carry:

- task/objective ID;
- owner (user / Protocol / Worker / Executive Planner);
- lifecycle state;
- current step/checkpoint;
- dependencies;
- leases/ownership where multiple executors can compete;
- heartbeat/last progress;
- retry budget;
- cancellation state;
- deadline/expiry;
- required capabilities;
- current execution surface;
- artifact/result references;
- verification state;
- blocker/escalation state.

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

The runtime should support:

- persisted checkpoints for long-running work;
- bounded retries/backoff;
- heartbeats for active Workers;
- lease expiry and reclaim of abandoned jobs;
- zombie/stuck-work detection;
- restart/resume after process or device loss;
- explicit compensation/rollback hooks where applicable;
- deduplication/idempotency for repeated delivery;
- durable queues/event delivery where the task warrants it.

A task must never remain forever in `working` because its executor disappeared.

### Separation of concerns

```text
Executive Planner → decides what should run and priority
Durable Runtime   → makes the work survive and progress safely
Worker            → owns/delegates objective-specific reasoning/execution
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
provider/plugin owner
version
```

Jev/Workers should search the catalog first and load the detailed contract only for a small relevant candidate set.

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

- Latch tools;
- Sunday/device capabilities;
- desktop machine capabilities;
- Edge hardware actions;
- plugins/connectors;
- `SKILL.md` Skills;
- external specialist agents/apps;
- Channel Gateway adapters;
- Kinetable/engineering tools.

## 4. Learned Automation Evaluation Pipeline

OSCAR can create or improve Skills, routines and Protocols, but generated automation should not be promoted merely because one exploratory run succeeded.

Use a promotion pipeline:

```text
successful execution
→ candidate extraction
→ normalize/parameterize
→ replay or evaluate on representative cases
→ verify expected output + safety properties
→ compare against current version
→ permission/policy review
→ promote / reject / keep experimental
```

A candidate should record:

- source executions/provenance;
- assumptions/preconditions;
- required capabilities;
- test/evaluation cases;
- success/failure metrics;
- latency/cost metrics where meaningful;
- permissions required;
- known limitations;
- rollback target/version.

### Promotion rules

- One successful run can create a candidate, not automatically a trusted default.
- New versions should not silently replace a more reliable existing Skill.
- Safety/permission requirements are never weakened by learning.
- If evaluation is impossible, label the Skill experimental/partially verified.
- Learned automation can be rolled back when reliability regresses.

## 5. Artifact / Result Model

OSCAR should treat finished outputs as first-class objects rather than burying them in chat history.

Examples:

- document;
- spreadsheet;
- slide deck;
- image/video/audio;
- code patch/commit/PR;
- research report;
- meeting notes/transcript;
- design asset;
- deployment;
- hardware/firmware build;
- dataset/model/evaluation output.

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

Example:

```text
Research Worker → verified research artifact
        ↓
Launch Worker → uses artifact as source
        ↓
Social Worker → derives post drafts
```

The Artifact Model also helps OSCAR answer:

```text
"Where is the final deck?"
"Which version did you send?"
"What changed from the previous report?"
"Is this output verified?"
```

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
```

Running through all of it:

- Epistemic Integrity;
- Personal Policy;
- permissions;
- entity graph;
- audit/provenance;
- learning/evaluation.

## Invariants

1. Channels are normalized without erasing platform-specific capability limits.
2. Long-running work has durable state, bounded retries and reclaim/recovery semantics.
3. Capability definitions are discovered progressively rather than loaded globally into every model prompt.
4. Learned automation is evaluated before trusted promotion.
5. Artifacts/results are first-class typed objects with provenance and verification state.
6. None of these primitives can self-grant permissions.
7. The core remains small: these layers provide explicit contracts rather than one giant orchestration framework.