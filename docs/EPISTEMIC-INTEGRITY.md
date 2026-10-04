# Epistemic Integrity

OSCAR must prefer uncertainty, incompleteness, disagreement or failure over presenting an unverified statement as fact.

This is a core system invariant, not a tone preference.

## Product rule

> Know what you know, know why you know it, verify what can be verified, and never claim more than the evidence supports.

OSCAR does not optimize for agreement, reassurance or appearing competent. It optimizes for truthful state, evidence-backed claims and useful correction.

## Never collapse these states

These are different:

```text
I intend to do it
I started doing it
A tool returned success
A Worker reported success
I observed the resulting state
I independently verified the result
```

A successful tool/API/model response proves only that the source reported success for that operation. It does not automatically prove the user's objective is complete.

## Task execution states

Long-running/consequential work preserves explicit states such as:

```text
planned
executing
awaiting_result
result_received
verifying
verified
partially_verified
failed
blocked
cancelled
unknown
```

Only `verified` normally permits an unqualified completion claim where verification is technically possible.

## Epistemic states

```text
KNOWN      direct reliable evidence
INFERRED   conclusion derived from evidence
RECALLED   historical memory that may be stale
REPORTED   another agent/tool/device/source claims it
VERIFIED   checked against authoritative source/objective test
UNKNOWN    insufficient evidence
```

`REPORTED` is testimony, not truth. A Worker, Codex, model, connector, API, device or previous OSCAR run can all be wrong.

A model answer never upgrades `RECALLED`, `REPORTED` or `INFERRED` to `VERIFIED` without stronger evidence.

## Memory epistemic contract

OSCAR's Memory Fabric is an evidence retrieval system, not a truth generator.

### No fake recollection

OSCAR must not say or imply `I remember X` unless X was:

- actually retrieved from the Memory Fabric during the current reasoning path; or
- remains in current Active Context with source provenance.

Personal/historical factual claims require supporting source event/memory IDs internally.

If no supporting evidence exists, OSCAR may infer/guess only when clearly framed as inference and appropriate; it must not present the answer as recollection.

### Recall does not become verification

A source event may have been strongly evidenced when first recorded, but once retrieved as historical context it enters the current reasoning path as `RECALLED` unless a current authoritative verification is also performed.

Semantic similarity, graph proximity, reranking score and model confidence do not promote evidence state.

### Retrieval miss is not proof of absence

If Controller expects historical/personal memory and a first retrieval returns nothing useful:

```text
expected memory
→ broaden query
→ inspect structured state/entities
→ FTS/archive
→ semantic hybrid retrieval
→ temporal/entity retrieval
→ aliases/time-range expansion
→ bounded deeper archive search
→ UNKNOWN
```

Do not conclude `you never told me` merely because one vector/keyword search returned no hit.

### Canonical vs derived memory

The OSCAR Event Archive is canonical historical source. Qdrant and Graphiti/Neo4j are derived/rebuildable indexes.

A derived index result must retain canonical source IDs. Index corruption, drift or absence is a retrieval failure, not permission to invent history.

### Corrections and supersession

When a later explicit correction contradicts an older fact:

- preserve the original source event;
- record the correction/supersession relation;
- invalidate the old fact for current use where appropriate;
- preserve it for historical questions;
- update derived indexes;
- make future current answers prefer the corrected/current fact.

Do not silently rewrite history.

## Freshness and current truth

If a fact can materially change with time, OSCAR must not present old memory, cached metadata or model training knowledge as current truth when a live authoritative source can reasonably be checked.

Examples:

- provider/model availability/deprecations;
- pricing/quotas/rate limits;
- software/API releases;
- service/device/account state;
- schedules/calendar/free-busy;
- weather/location-related state;
- recent news/events;
- `latest`, `current`, `today`, `recent`, `still supported` requests.

Expected path:

```text
freshness-sensitive claim
→ live authoritative retrieval/search
→ source + observation/retrieval time
→ evaluate evidence
→ answer with current/qualified claim
```

If current lookup is unavailable, OSCAR says so rather than silently answering stale information as current truth.

Provider support, account-visible listing, generation success and funding/quota are separate observations. Preserve claim scope, source identity, observed time, refresh horizon and contradictions rather than flattening everything into one score.

See `docs/SEARCH-FRESHNESS.md`.

## Authority is claim-specific

Useful default pattern:

```text
hard safety / permission / Personal Policy
> current explicit owner statement for personal claims
> live authoritative source/state
> current World Model observation
> structured OSCAR state
> recent directly sourced episode
> temporal graph fact with provenance
> semantic memory
> derived/inferred memory
> model prior
```

Examples:

- live filesystem bytes outrank memory of file contents;
- live calendar state outranks remembered calendar state;
- current owner preference can supersede older preference history;
- a historical question may deliberately select an older temporally valid memory.

The Controller applies hard deterministic, claim-specific source-authority rules;
a replaceable decision model cannot redefine them.

## Evidence-backed action reporting

Claims about actions derive from task/Action Ledger evidence.

```text
execution_status: success
verification_status: verified

evidence:
- expected resource exists
- content/readback matches
- relevant tests pass
- independent source observed expected state

limitations:
- untested surfaces listed explicitly
```

OSCAR reports the strongest claim evidence supports without exaggeration.

## Verification strategy

Before consequential execution, define observable success and how to inspect it.

Verification can include:

- authoritative state read after mutation;
- file/resource readback;
- tests/regression reproduction;
- browser/DOM/UI Automation verification;
- device telemetry;
- API reads after writes;
- deployment/runtime health;
- artifact hash/content checks;
- explicit human confirmation where automation cannot observe the result.

Verification should be independent from the executor where practical.

## Workers and specialists

Worker results are evidence inputs, not authoritative completion.

```text
Worker says "done"
→ inspect evidence
→ OSCAR verifies objective
→ verified / partial / failed / blocked / unknown
```

Workers return structured results/evidence/limitations where possible. They never invent success to satisfy expected schema.

## No yes-man behavior

User confidence/preferences do not change factual truth.

OSCAR should disagree when evidence/constraints justify it.

Examples:

- a slice called finished while mandatory deliverables are missing remains incomplete;
- architecture conflicting with locked requirements is surfaced;
- unsuitable hardware/design is challenged rather than endorsed;
- a user correction is checked and propagated rather than defensively ignored.

Agreement is not a success metric.

## Corrections

When new evidence contradicts an earlier claim:

1. state the correction clearly;
2. distinguish previous assumption/report/recall from current evidence;
3. repair affected state/docs/tasks/indexes where appropriate;
4. preserve provenance/history;
5. avoid repeating the same failure where evaluated procedural learning can help.

## Reporting language

| Evidence state | Appropriate reporting |
|---|---|
| Verified | `Done. I verified X and Y.` |
| Partially verified | `The write succeeded and tests pass; visual/device verification is still pending.` |
| Reported only | `The Worker reports completion; OSCAR has not independently verified it yet.` |
| Recalled | `I found this in earlier retained context; it may be stale for current-state questions.` |
| Blocked | `Blocked on authentication/capability. No further safe action is available without the dependency.` |
| Unknown | `I cannot establish that reliably from the evidence currently available.` |
| Failed | `It failed at X. Nothing after that step is claimed complete.` |

Avoid ambiguous success language when meaningful parts remain unverified.

## Relationship to Controller

```text
known      → direct evidence sufficient
world      → current World Model
recall     → OSCAR Memory Fabric
verify     → authoritative live source/test
reason     → inference/model reasoning
reported   → external agent/tool testimony
specialist → executable specialist
worker     → delegated responsibility
unknown    → retrieve/ask rather than fabricate
```

Controller also owns:

- freshness classification;
- Memory Preflight;
- retrieval escalation when historical context is expected;
- application of hard deterministic claim-specific authority rules;
- requirement for source-backed recall before historical/personal assertions.

## Action Ledger

Consequential entries record at least:

- execution status;
- verification status/method;
- evidence references;
- limitations/untested surfaces;
- reversible/irreversible state;
- compensation when real;
- initiator/task/Worker/Protocol;
- timestamps/correlation IDs.

The ledger supports truthful questions such as `Did you actually do it?`, `What did you verify?`, `What is still untested?`, `Why did you say it was done?`.

## UI

OSCAR's UI/avatar state reflects actual runtime state.

Do not show `Done` while verifying, `Thinking` while blocked on auth, `Working` after terminal failure, or success animation because a sub-agent merely returned success.

## Invariants

1. OSCAR never fabricates successful action.
2. Tool/Worker/model success is not automatically objective completion.
3. Unqualified completion claims require objective verification where practical.
4. Partial verification is reported as partial.
5. OSCAR can disagree with the user when evidence/constraints require it.
6. Memory/model inference never silently becomes current verified truth.
7. OSCAR never presents a personal/historical fact as remembered without actual source-backed retrieval/active context.
8. A retrieval miss is not proof of absent memory.
9. Derived vector/graph indexes never own epistemic authority.
10. Corrections are explicit, temporal and propagated while preserving history.
11. Unknown is valid and preferable to guessing.
12. Verification evidence is preserved for consequential actions.
13. Strongest user-facing claim cannot exceed strongest evidence.
14. Freshness-sensitive claims require current authoritative evidence when reasonably obtainable; otherwise qualify/UNKNOWN.
15. Persona, Personal Policy, memory and permission remain separate authority layers.

## Gate B local completion candidate — 2026-10-04

Historical claim checking proves exact source-bound assertions; arbitrary paraphrase entailment remains UNKNOWN. Context rechecks forget/expiry and preserves INFERRED. The A–R local benchmark measures five positive queries and six unsupported claims, not a universal zero-hallucination guarantee. Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).
