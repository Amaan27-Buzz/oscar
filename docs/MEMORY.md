# Memory: LRA + Supermemory + Jev

OSCAR should feel like one continuous relationship, not a collection of disconnected chat threads.

## Product rule

The user-facing primitive is **one persistent OSCAR conversation/history** across voice, text, Sunday, desktop and physical surfaces.

Internal context may be segmented, archived, summarized or retrieved differently for engineering reasons, but those implementation details must not force the user to manage hundreds of chats.

`New chat`-style behavior, if ever exposed, should reset the immediate working surface without silently deleting durable OSCAR memory.

## LRA role

LRA is the memory/history architecture that owns continuity and context assembly.

Planned responsibilities:

- active live context
- episodic conversation/task history
- project/context boundaries
- durable user profile/preferences
- procedural memory and learned workflows
- memory provenance/confidence
- context assembly before reasoning
- remember/update/forget flows
- cross-device continuity

LRA is the architecture. Supermemory is a backend used by that architecture rather than the product model itself.

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

Supermemory should **not** be treated as the sole source of truth for live system state.

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
live authoritative source/state
        >
structured OSCAR state
        >
recent episodic history
        >
semantic/derived memory
        >
model prior knowledge
```

For example, if memory says a repository uses one framework but the current repository says another, current repository state wins.

## Memory classes

OSCAR should be able to distinguish at least:

- **working context** — what is happening right now
- **episodic history** — what happened and when
- **semantic memory** — durable facts/preferences/relationships
- **project memory** — decisions, conventions, constraints and status
- **device/environment memory** — stable configuration, names and normal state
- **procedural memory** — how OSCAR successfully completed a task
- **protocol state** — state belonging to long-running autonomous responsibilities

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
→ select tools/workers
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

Memory should not silently grant permissions or bypass action policy.

## Invariants

1. User-facing continuity is more important than exposing internal session segmentation.
2. Memory is not automatically authoritative.
3. Jev retrieves before guessing.
4. Live sources override stale memory when current truth matters.
5. Procedural memory can improve execution, but never self-grant authority.
6. Voice, text, Sunday, desktop and edge interactions contribute to the same OSCAR history where policy permits.
