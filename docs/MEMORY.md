# OSCAR Memory Fabric

OSCAR should feel like one continuous relationship, not a collection of disconnected chat threads. The user-facing primitive is one persistent interaction point across text, voice, Sunday, desktop, communications, Workers and physical surfaces.

Internal segmentation exists only for engineering quality, retrieval, retention and scaling. The user should not have to remember which old chat contains a fact.

## Product invariant

```text
You ↔ OSCAR
```

There is one continuing relationship. Internally OSCAR may create `event_id`, `turn_id`, `episode_id`, `objective_id`, `task_id`, `artifact_id`, `entity_id` and `memory_id` records, but those are implementation details rather than separate assistant identities.

A future UI may expose temporary workspaces or views, but changing views must not silently reset identity or durable memory.

## Ownership rule

OSCAR owns canonical memory. No managed memory vendor, vector database, graph database or model provider owns OSCAR's history.

The canonical source is the **OSCAR Event Archive**. Semantic/vector and temporal/graph systems are derived, replaceable and rebuildable indexes.

```text
                     OSCAR MEMORY FABRIC

one continuous interaction point
             │
             ▼
       Active Context
             │
             ▼
     OSCAR Event Archive
   SQLite + WAL + FTS5 initially
      canonical provenance
             │
      Memory Formation
             │
   ┌─────────┴─────────┐
   ▼                   ▼
Qdrant OSS          Graphiti OSS
hybrid semantic     temporal/entity
retrieval           relationships
                        │
                    Neo4j Community
   └─────────┬─────────┘
             ▼
      Retrieval Fusion
      + local reranker
             │
             ▼
   Controller Memory Preflight
   authority/conflict logic
             │
             ▼
      Context Assembly
             │
             ▼
 reasoning / Executive / action
             │
             ▼
       Claim Verifier
```

## Canonical stack

### OSCAR Event Archive

Initial implementation: SQLite with WAL and FTS5.

The archive stores durable source events and provenance, including where appropriate:

- user turns and explicit corrections;
- OSCAR replies and their evidence references;
- objectives/tasks/actions/results;
- Worker and Protocol events;
- artifacts and verification evidence;
- project/entity references;
- decisions and explicit preferences;
- retained communication/context events permitted by retention policy;
- memory derivations and supersession links.

The archive is the recovery source for derived indexes. Losing Qdrant or the graph store must not erase OSCAR's history.

### Qdrant OSS

Qdrant is the first semantic retrieval index.

Use it for:

- dense semantic retrieval;
- sparse/lexical retrieval where useful;
- hybrid retrieval;
- metadata/project/entity/time filtering;
- candidate generation for reranking.

Qdrant is not authoritative memory. Its records point back to canonical archive IDs.

### Graphiti OSS + Neo4j Community

Graphiti is the first temporal/entity memory index. Neo4j Community is the initial graph store.

Use it for:

- canonical entities and aliases;
- relationships;
- time-varying facts;
- validity windows;
- historical states;
- supersession/correction relationships;
- provenance back to source episodes/events.

The graph is derived state and can be rebuilt from the Event Archive.

### Embeddings and reranking

Embeddings and reranking are replaceable OSCAR capabilities. Prefer local/self-hosted models where practical; cloud models may be selected through the native Model Router under policy.

No embedding or reranking provider becomes an architectural dependency.

## Active Context

One continuous conversation does not mean one infinitely growing prompt.

Active Context is reconstructed dynamically from:

```text
recent conversation
+ current objective/task
+ current project
+ active entities
+ open commitments
+ relevant retrieved episodes/memories
+ Personal Policy required for this objective
+ current World Model/live context
```

Recent useful context remains live. Older context can be archived and later retrieved without becoming a separate user-visible chat.

## Memory classes

OSCAR distinguishes at least:

- **working context** — immediate interaction state;
- **episodic history** — what happened, when and with whom;
- **semantic memory** — durable facts and relationships;
- **preference memory** — explicit or carefully scoped preferences;
- **project memory** — decisions, conventions, constraints and status history;
- **device/environment memory** — durable configuration, not current telemetry;
- **communication memory** — retained decisions/outcomes/commitments under policy;
- **procedural memory** — verified reusable ways of doing work;
- **Worker/Protocol history** — delegated work and durable responsibility history;
- **entity memory** — canonical entities, aliases and evidence-backed relationships.

Personal Policy is not a memory class. Permission is not a memory class. Voice Match/Voice Map embeddings remain dedicated sensitive system data.

## Controller Memory Preflight

The Controller is OSCAR's own Decision / Epistemic Controller. Its current Python
module `oscar/jev.py` has a temporary historical/internal name; TypeSafe Jev is not
a required runtime/API. Replaceable decision models cannot grant memory authority.

Memory retrieval is not left to the language model's intuition.

Every interaction receives a cheap Controller preflight that asks whether the objective depends on personal/history/project/entity context.

Retrieval is mandatory when the request plausibly references:

- something said or decided earlier;
- a known person, project, device, repository or artifact;
- a preference or habit;
- a previous task/result;
- `continue that`, `same as before`, `what did we decide`, `that project`, `my usual`, or equivalent deictic language;
- a correction or prior contradiction.

A deterministic question such as `2 + 2` does not need memory retrieval.

Core rule:

> The reasoning model does not decide whether memory exists. Controller decides whether memory retrieval is required.

## Retrieval ladder

For a memory-dependent request, use bounded escalation:

```text
0. Active Context
1. Structured OSCAR state / entities / tasks / Personal Policy
2. Event Archive exact + SQLite FTS5
3. Qdrant hybrid semantic retrieval
4. Graphiti temporal/entity retrieval
5. Query expansion: aliases, related entities, project names, time ranges
6. Bounded deeper archive reconstruction
7. UNKNOWN
```

Do not jump directly from one empty vector query to `I don't remember`.

### Expected-memory misses

If Controller classifies a request as clearly historical/personal and retrieval returns no useful result:

```text
expected_memory = true
retrieval_hits = insufficient
→ broaden retrieval
→ inspect aliases/entities/time ranges
→ bounded deeper archive search
→ UNKNOWN only after those attempts
```

A retrieval miss is evidence of a retrieval miss, not proof that the memory never existed.

## Retrieval fusion and ranking

Do not rely on raw nearest-neighbor similarity alone.

Candidate ranking may combine:

- exact/lexical match;
- dense semantic similarity;
- graph/entity relation;
- temporal validity;
- project/entity scope;
- recency;
- source authority;
- explicitness/repetition;
- confidence;
- staleness penalty;
- current objective relevance.

Use a replaceable local reranker after broad candidate retrieval when it materially improves precision.

The output should be the smallest useful evidence set, not a transcript dump.

## Evidence-bound recall

A personal/historical factual answer must be traceable to source memory/event evidence.

Conceptually, generated claims carry:

```text
claim
supporting_event_ids[]
supporting_memory_ids[]
evidence_state
confidence
```

If the answer has no supporting retrieved evidence, OSCAR must not present it as remembered fact.

### Recall language invariant

OSCAR must not say or imply `I remember X` unless X was actually retrieved from the Memory Fabric during the current reasoning path or remains in active context with provenance.

Historical data remains `RECALLED` when used in a new answer even if the original source event had stronger evidence. Retrieval does not promote it to current `VERIFIED` truth.

## Authority and freshness

Memory is historical evidence, not universal current truth.

A useful default order is:

```text
hard safety / permission / Personal Policy
> current explicit owner statement for a personal claim
> live authoritative source/state
> current World Model observation
> structured OSCAR task/entity state
> recent directly sourced episode
> temporal graph fact with provenance
> semantic memory
> derived/inferred memory
> model prior
```

Authority is claim-specific. A live filesystem read outranks memory of a file. Current weather outranks an old weather memory. A current explicit preference can supersede an older preference.

The Controller applies OSCAR's hard deterministic, claim-specific authority rules
and determines whether verification/live retrieval is required. A decision model
cannot change live-vs-memory precedence or turn recalled history into current truth.

## Memory formation

After eligible interactions, OSCAR may create memory candidates rather than blindly storing model summaries as truth.

Pipeline:

```text
source event
→ extract candidate
→ classify type/scope
→ resolve entities
→ compare existing memories
→ detect conflict/supersession
→ assign provenance + epistemic state
→ retain under policy
→ update derived indexes
```

Examples:

- `I switched from VS Code to Zed` can create a directly sourced preference update.
- `That UI is too rounded` should not silently become a universal `user hates rounded UI` rule. Keep the narrower scoped observation unless later evidence justifies broader generalization.

Model-derived interpretations remain `INFERRED` unless a stronger source/evidence exists.

## Corrections and supersession

Corrections are first-class.

```text
new owner correction
→ identify challenged fact/memory
→ preserve original source event
→ mark old fact superseded/invalid for current use
→ record correction relation
→ update semantic index
→ update temporal graph
→ future current retrieval favors corrected fact
```

OSCAR does not silently erase history to make the present look consistent.

Temporal questions should still be able to retrieve earlier valid states.

## Entity resolution

A canonical Entity Registry links aliases only when evidence supports the match.

Minimum entity metadata:

```text
entity_id
canonical_name
aliases[]
type
relationships[]
source_event_ids[]
confidence
```

Same names do not prove identity. Unknown or ambiguous entities remain separate until evidence supports a merge.

Controller resolves likely entity IDs before broad historical retrieval when doing so improves precision.

## Background consolidation

Idle/background consolidation may:

- deduplicate equivalent derived memories;
- merge repeated supporting evidence;
- resolve safe entity aliases;
- detect contradictions;
- maintain temporal validity windows;
- generate bounded summaries;
- compact/rebuild derived indexes;
- identify procedure/Skill candidates.

Summaries never replace source events. They retain provenance to originals.

## Procedural memory

```text
first execution
→ explore
→ execute
→ independently verify
→ capture successful path
→ parameterize
→ evaluate
→ candidate Skill/procedure
```

Procedural memory may improve future execution. It never grants new permission or authority.

## Privacy, retention and forget

`CAN PERCEIVE`, `CAN RETAIN` and `CAN ACT` remain independent.

Memory records carry retention metadata where appropriate, including source, scope, reason, expiry and sensitivity class.

Forget/delete behavior must be truthful:

- remove/tombstone the live OSCAR memory record as defined by retention policy;
- remove relevant semantic/graph index entries;
- prevent normal future retrieval;
- preserve only audit/tombstone information required by policy/security;
- do not claim secure disk erasure or deletion from external source systems unless independently verified.

Raw audio, transcripts, summaries, communication memory and Voice Map/Match data remain separately controlled.

## Resilience and rebuild

Derived indexes are disposable from an authority perspective.

Acceptance must include:

- rebuild Qdrant from canonical archive records;
- rebuild Graphiti/Neo4j derived state from canonical events where supported;
- detect index lag/drift;
- preserve archive/event IDs across rebuilds;
- fail closed to archive/FTS/UNKNOWN rather than inventing memory when an index is unavailable.

## Memory evaluation

Memory quality is a tested subsystem, not a vibe.

Maintain synthetic and non-sensitive evaluation sets covering:

- exact long-history recall;
- paraphrased semantic recall;
- temporal current-vs-historical questions;
- preference supersession;
- entity aliases and same-name disambiguation;
- project context switching;
- false-recall rate;
- retrieval-miss escalation;
- stale memory vs authoritative live state;
- corrections;
- forget/delete;
- index rebuild and drift;
- cross-process/device continuity;
- procedural recall without authority expansion.

Track metrics such as recall@k/precision where meaningful, temporal correctness, false-memory claims and UNKNOWN correctness.

## Memory vs other OSCAR systems

```text
Memory          = historical continuity/evidence
World Model     = what is true now
Personal Policy = explicit desired behavior
Permission      = what OSCAR may do
Persona         = how OSCAR expresses itself
Protocol        = durable delegated responsibility
```

None silently substitutes for another.

## Current Club B boundary

The existing `oscar.continuity.LocalMemory` and SQLite-backed records verify selected local retention, restart continuity, evidence state, entity references, live-source precedence and forget of the live OSCAR record for the documented Windows/reference cases.

The archive/index/retrieval implementation is now exercised on this Windows laptop with synthetic retained sources. Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).

Canonical admission rechecks forgotten/expired/inferred and temporally superseded sources even when a recalled object was cached. Context has a total serialized bound and terminal tasks release transient context. Consolidation runs in bounded batches with a durable atomic cursor; it preserves source events and merges only matching evidence inside a batch. Run one consolidation runner per relationship. A completed consolidation pass requires explicit restart. No automatic unbounded daemon, model-extracted global summaries, or private unauthenticated Neo4j deployment is claimed.

Archive writes transactionally advance a per-relationship generation. Retrieval excludes a derived index unless durable CURRENT state, generation, physical projection digest and model identity match. Rebuilds are bounded, idempotent and stamped only after completion; failure preserves canonical history. Outdated/lost/unavailable services fall back through valid archive/context/remaining-index paths, eventually UNKNOWN. A concurrent archive write fences the in-flight recall. See [pre-manual hardening evidence and design](GATE-B-HARDENING.md).

The local default is FastEmbed BGE small v1.5 plus Qdrant BM25 with the IDF modifier, RRF and an ONNX MiniLM cross-encoder. FTS5 remains the canonical lexical path. Sparse embeddings use FastEmbed's document/query APIs, not OSCAR token hashing. Sentence-transformers remains an optional benchmark reference, outside the default memory dependency extra. Offline dense/reranker loaders fingerprint actual model/tokenizer artifacts.

Bounded response context carries claim ID/type, supporting canonical event/memory IDs, retrieval path, confidence, epistemic state and temporal interpretation. Required retrieval failure, empty evidence, unresolved identity and inadmissible cached support produce UNKNOWN. The verifier supports exact sourced assertions, not arbitrary natural-language entailment; RECALLED is never automatically VERIFIED.

The prior planned Supermemory integration has been retired. Historical checkpoint references to it describe the earlier plan, not a current dependency.

## Non-negotiable invariants

1. One user-facing relationship/interaction point; internal segmentation is invisible unless explicitly surfaced for organization.
2. OSCAR owns the canonical Event Archive.
3. Qdrant, Graphiti and graph/vector stores are derived rebuildable indexes, never canonical truth.
4. OSCAR never says `I remember X` without retrieved/active-context evidence for X.
5. Personal/historical factual claims require source event/memory provenance.
6. A failed retrieval is not proof the memory does not exist.
7. Controller escalates retrieval before returning UNKNOWN when historical memory is expected.
8. Live/current authoritative evidence outranks stale memory.
9. History is superseded temporally, not silently overwritten.
10. No single retrieval mechanism is trusted as complete.
11. Derived facts retain provenance and epistemic state.
12. The reasoning model cannot promote inference or recall into current verified fact.
13. Memory does not grant permission, modify Personal Policy or weaken safety.
14. Sensitive voice/communication retention remains separately controlled.
15. Any managed memory service is optional; OSCAR must remain operable with the free/self-hosted stack.


The owner's final physical/manual machine acceptance PASSED in run
`manual-gate-b-20261004-200734`; desktop/local/public browser phases are VERIFIED.
The [prepared GitHub OAuth/federation acceptance](GATE-B-OAUTH-ACCEPTANCE.md) uses
the existing native vault, opaque references and Connector Fabric; private email
addresses remain transient. The controlled synthetic past count remains RECALLED;
current provider count facts remain REPORTED, with separate source/temporal provenance.
Real owner OAuth/private federation is not yet exercised. Gate B remains PARTIAL.
