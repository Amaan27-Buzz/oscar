# Memory: LRA + Supermemory + Jev

OSCAR should feel like one continuous relationship, not a collection of disconnected chat threads.

## Product rule

The user-facing primitive is **one persistent OSCAR conversation/history** across voice, text, Sunday, desktop, communications, Workers and physical surfaces.

Internal context may be segmented, archived, summarized or retrieved differently for engineering reasons, but those implementation details must not force the user to manage hundreds of chats.

`New chat`-style behavior, if ever exposed, should reset the immediate working surface without silently deleting durable OSCAR memory.

## LRA role

LRA is the memory/history architecture that owns continuity and context assembly.

Planned responsibilities:

- active live context;
- episodic conversation/task history;
- project/context boundaries;
- durable user profile/relationship memory;
- procedural memory and learned workflows;
- Worker/Protocol history and state refs;
- memory provenance/confidence;
- context assembly before reasoning;
- remember/update/forget flows;
- cross-device continuity.

LRA is the architecture. Supermemory is a backend used by that architecture rather than the product model itself.

## Memory is not Personal Policy

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

LRA/Supermemory can discover patterns and suggest policy changes, but consequential inferred patterns should not silently become authority.

## Active context vs long-term memory

Recent conversation should remain true active context while useful. It should not be prematurely flattened into isolated RAG snippets.

```text
continuous OSCAR surface
        │
        ▼
active live context
        │
        ├─ enough room / still active → keep live
        └─ idle / context pressure    → archive segment
                                      ↓
                             episodic history + memory
```

Exact rollover thresholds remain configurable/benchmark-driven rather than protocol guarantees.

## Supermemory role

Supermemory supplies semantic/profile-style memory capabilities underneath LRA.

Good uses include semantic recall, durable user/project facts, connected memories, profile-like understanding, reflection, prior-outcome retrieval and identifying repeated preference patterns to suggest.

Supermemory is not the sole source of truth for live system state or explicit Personal Policy.

## Jev as epistemic router

Jev is not only an intent classifier. It reasons about whether OSCAR has enough reliable context.

```text
request
  │
  ▼
Jev
  ├─ known        → answer/act
  ├─ world        → current World Model
  ├─ recall       → query LRA/Supermemory
  ├─ verify       → inspect authoritative source/tool
  ├─ reason       → native OSCAR Model Router → configured provider
  ├─ specialist   → specialist capability
  ├─ worker       → delegated Worker
  └─ unknown      → retrieve/ask rather than guess
```

The separate SwitchRoute project is not a runtime dependency; its useful routing concepts are folded into OSCAR's native Model Router.

Core rule:

> Never guess user/project context when it can be retrieved or verified.

## Source authority

Memory is evidence, not universal truth.

A useful authority order is:

```text
hard safety/permission/policy constraints
        >
live authoritative source/state
        >
World Model current evidence
        >
structured OSCAR task/Worker state
        >
recent episodic history
        >
semantic/derived memory
        >
model prior knowledge
```

## Memory classes

OSCAR should distinguish at least:

- **working context** — what is happening now;
- **episodic history** — what happened and when;
- **semantic memory** — durable facts/relationships/learned preferences;
- **project memory** — decisions/conventions/constraints/status;
- **device/environment memory** — stable configuration/names/normal state;
- **communication memory** — calls/meetings/messages outcomes/commitments subject to retention;
- **procedural memory** — how OSCAR successfully completed a task;
- **Worker history/state refs** — delegated outcomes/blockers/artifacts;
- **Protocol state** — long-running autonomous responsibility state.

Explicit Personal Policy is not merely another semantic-memory category.

## Voice identity / Voice Map are not ordinary memory

Speaker-recognition profiles/embeddings used by Voice Match or Voice Map are sensitive biometric-like system data and should not be flattened into generic semantic memory.

LRA may store safe relationship/context facts such as `person X spoke during meeting Y` when retention policy permits, but the underlying speaker embedding/profile stays under the dedicated voice/security retention controls defined in `VOICE-SENTRY.md` and `SECURITY.md`.

Unknown speaker observations should remain confidence-qualified observations rather than invented identity memories.

OSCAR's own TTS output is excluded from speaker identity learning.

## Retrieval quality

Retrieval should not be raw nearest-neighbor similarity only. Ranking can combine semantic relevance, recency, importance, memory type, project/task scope, repetition/confirmation, source authority, confidence and staleness penalty.

The goal is the **smallest useful context**, not history dumping.

## Procedural memory

```text
first execution
→ explore
→ select capabilities/Workers
→ execute
→ verify
→ capture successful path
→ distill reusable procedure
```

Later:

```text
Jev recognizes known/similar procedure
→ retrieve procedural memory / Skill
→ adapt parameters
→ execute faster
→ verify
→ improve/version if a better path was found
```

Procedural memory improves execution without expanding authority.

## Communication retention

Calls, meetings and messages can contain particularly sensitive data.

OSCAR separately controls retention for:

- raw audio;
- full transcript;
- concise summary;
- decisions/action items;
- relationship/context memory;
- Voice Map/speaker-identity data under dedicated voice controls.

The system should prefer the minimum useful durable representation rather than retaining every raw recording indefinitely.

## Privacy and control

Planned controls:

- search memory/history;
- inspect source/provenance;
- correct/edit;
- forget/delete;
- disable categories/providers;
- export where practical;
- clear/reset memory independently from current UI surface.

Memory does not grant permissions or bypass Personal Policy.

## Invariants

1. User-facing continuity is more important than exposing internal session segmentation.
2. Memory is not automatically authoritative.
3. Explicit Personal Policy is distinct from inferred memory.
4. Jev retrieves before guessing.
5. Live/current sources override stale memory when current truth matters.
6. Procedural memory can improve execution but never self-grant authority.
7. Voice, text, Sunday, desktop, communications, Workers and Edge interactions contribute to the same history where policy permits.
8. Sensitive communication data uses explicit retention controls.
9. Voice Match/Voice Map embeddings are dedicated sensitive system data, not generic LRA memories.
10. Model reasoning is selected through OSCAR's native Model Router, not a required external SwitchRoute service.
