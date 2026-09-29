# Memory: LRA + Supermemory + Jev

OSCAR should feel like one continuous relationship, not a collection of disconnected chat threads.

## Product rule

The user-facing primitive is **one persistent OSCAR conversation/history** across voice, text, Sunday, desktop, communications, Workers and physical surfaces.

Internal context may be segmented, archived, summarized or retrieved differently for engineering reasons, but those implementation details must not force the user to manage hundreds of chats.

`New chat`-style behavior, if ever exposed, should reset the immediate working surface without silently deleting durable OSCAR memory.

## LRA role

LRA is the memory/history architecture that owns continuity and context assembly.

Planned responsibilities:

- active live context
- episodic conversation/task history
- project/context boundaries
- durable user profile/relationship memory
- procedural memory and learned workflows
- Worker/protocol history and state references
- memory provenance/confidence
- context assembly before reasoning
- remember/update/forget flows
- cross-device continuity

LRA is the architecture. Supermemory is a backend used by that architecture rather than the product model itself.

## Memory is not Personal Policy

OSCAR must distinguish inferred/remembered information from explicit user instructions about behavior.

```text
Memory
= what OSCAR knows or recalls

Personal Policy
= how the user explicitly wants OSCAR to behave

Permission
= what OSCAR is authorized to do

Protocol
= a durable autonomous responsibility/process
```

Example:

```text
Memory:      "Amaan usually silences calls while studying."
Policy:      "Do not answer calls while I am studying."
Permission:  "OSCAR may answer calls on my behalf."
Protocol:    "Apply my call rules whenever a call arrives."
```

LRA/Supermemory can discover patterns and suggest policy changes, but consequential inferred patterns should not silently become authority.

See [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

## Active context vs long-term memory

Recent conversation should remain true active context while it is useful. It should not be prematurely flattened into isolated RAG snippets.

Conceptually:

```text
continuous OSCAR surface
        │
        ▼
active live context
        │
        ├─ enough room / still active → keep live
        │
        └─ idle / context pressure → archive segment
                                  │
                                  ▼
                         episodic history + memory
```

Earlier LRA planning used roughly a long idle window or large context threshold before rollover. Exact thresholds should remain configurable and benchmark-driven rather than becoming protocol guarantees.

## Supermemory role

Supermemory supplies semantic/profile-style memory capabilities underneath LRA.

Good uses include:

- semantic recall
- durable user/project facts
- connected memories
- profile-like understanding
- derived memory/reflection
- retrieving related prior outcomes
- identifying repeated preference patterns to suggest to the user

Supermemory should **not** be treated as the sole source of truth for live system state or explicit Personal Policy.

## Jev as epistemic router

Jev is not only an intent classifier. It should explicitly reason about whether OSCAR has enough reliable context.

```text
request
  │
  ▼
Jev
  ├─ known        → answer/act
  ├─ recall       → query LRA/Supermemory
  ├─ verify       → inspect authoritative source/tool
  ├─ reason       → ChatGPT/SwitchRoute/specialist
  ├─ delegate     → Worker/specialist route
  └─ unknown      → ask user
```

This is a core anti-hallucination rule:

> Never guess user/project context when it can be retrieved or verified.

Example:

```text
"What did we decide about LRA?"
        ↓
Jev detects missing local context
        ↓
LRA retrieves relevant history
        ↓
OSCAR answers from recovered context
```

If retrieval cannot resolve the ambiguity, OSCAR asks the user rather than inventing an answer.

## Source authority

Memory is evidence, not universal truth.

A useful authority order is:

```text
hard safety/permission/policy constraints
        >
live authoritative source/state
        >
structured OSCAR task/Worker state
        >
recent episodic history
        >
semantic/derived memory
        >
model prior knowledge
```

For example, if memory says a repository uses one framework but the current repository says another, current repository state wins. If memory suggests a preferred call behavior but explicit Personal Policy says otherwise, policy wins.

## Memory classes

OSCAR should be able to distinguish at least:

- **working context** — what is happening right now
- **episodic history** — what happened and when
- **semantic memory** — durable facts/relationships/learned preferences
- **project memory** — decisions, conventions, constraints and status
- **device/environment memory** — stable configuration, names and normal state
- **communication memory** — calls/meetings/messages outcomes and commitments, subject to retention policy
- **procedural memory** — how OSCAR successfully completed a task
- **Worker history/state references** — delegated objective outcomes, blockers and reusable artifacts
- **protocol state** — state belonging to long-running autonomous responsibilities

Explicit Personal Policy is intentionally not treated as just another semantic-memory category.

## Retrieval quality

Retrieval should not be raw nearest-neighbor similarity only. Ranking can combine:

- semantic relevance
- recency
- importance
- memory type
- project/task scope
- repetition/confirmation
- source authority
- confidence
- staleness penalty

The goal is to retrieve the **smallest useful context**, not dump history indiscriminately into every model call.

## Procedural memory

When OSCAR completes something new successfully, it should preserve the useful procedure, not only the outcome.

```text
first execution
→ explore
→ select tools/Workers
→ execute
→ verify
→ capture successful path
→ distill reusable procedure
```

On later similar tasks:

```text
Jev recognizes known/similar procedure
→ retrieve procedural memory / skill
→ adapt parameters
→ execute faster
→ verify
→ improve/version if a better path was found
```

This is how OSCAR becomes faster and more capable with use.

## Communication retention

Calls, meetings and messages can contain particularly sensitive data.

OSCAR should separately control retention for:

- raw audio
- full transcript
- concise summary
- decisions/action items
- relationship/context memory

The system should prefer storing the minimum useful durable representation rather than retaining every raw recording indefinitely.

See [COMMUNICATION.md](COMMUNICATION.md).

## Privacy and control

The user must be able to inspect and control durable memory.

Planned controls:

- search memory/history
- inspect source/provenance
- correct/edit
- forget/delete
- disable categories/providers
- export where practical
- clear/reset memory independently from the current UI surface

Memory should not silently grant permissions or bypass Personal Policy/action policy.

## Invariants

1. User-facing continuity is more important than exposing internal session segmentation.
2. Memory is not automatically authoritative.
3. Explicit Personal Policy is distinct from inferred memory.
4. Jev retrieves before guessing.
5. Live sources override stale memory when current truth matters.
6. Procedural memory can improve execution, but never self-grant authority.
7. Voice, text, Sunday, desktop, communications, Workers and edge interactions contribute to the same OSCAR history where policy permits.
8. Sensitive communication data uses explicit retention controls rather than default permanent raw storage.
