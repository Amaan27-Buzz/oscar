# Gate B pre-manual hardening — 2026-10-04

> Original-repository PR/run URLs below are historical identifiers retained verbatim.
> They are no longer accessible after repository migration and are not current CI evidence.

> Current status reconciliation, 2026-10-05: PR #12 is merged at `97c0622507df3f724ecf0c8b74aa7f4ae7784b08`; Gate B is frozen PASS. Slice 05/06 COMPLETE. Slice 07 software is accepted for continuation; physical Edge acceptance is DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED. Slice 08 is authorized after integration. The dated evidence below retains its historical status wording.

Starting branch/PR head: `447ad2eef86deeab2cc924bc88c4f5afb123b687`.
Branch: `gate-b/completion`; draft PR 12 (historical reference: `https://github.com/amaansyed27/oscar/pull/12`)
targets `work`. This pass does not perform physical/manual desktop acceptance,
owner OAuth authorization, merge, or Slice 07 work.

**Slice 05 COMPLETE; Slice 06 PARTIAL; Gate B PARTIAL.** Prior scoped acceptance
remains historical evidence. Owner/private/manual acceptance is still required.

Current status supersedes the historical pass statuses below: Slice 05/06 COMPLETE;
Gate B PASS after owner machine and OAuth/federation acceptance. See
[the final independent review](GATE-B-COMPLETION.md). Earlier failures/evidence are preserved.

## Dependency decision

Official package metadata was checked on this pass: Playwright 1.63.0,
qdrant-client 1.19.1, graphiti-core 0.30.2, sentence-transformers 6.1.0,
FastEmbed 0.8.1. Retain Playwright, native Microsoft UI Automation, Windows
Credential Manager, canonical SQLite/WAL/FTS5, Qdrant and Graphiti/Neo4j.
No orchestration framework replaces OSCAR or Jev.

FastEmbed 0.8.1 is pinned in the `memory` extra. It supplies supported
`Qdrant/bm25`, dense ONNX embeddings and an ONNX cross-encoder. The separate
`memory-reference` extra contains sentence-transformers 6.1.0 solely for
reproducing the baseline/model comparison; it is not a second default runtime.
The existing immutable Neo4j image reports **2026.09.0** and passes the native
Graphiti 0.30.2 path. No speculative Neo4j upgrade was needed.

Sources: [FastEmbed releases](https://github.com/qdrant/fastembed/releases),
[Playwright releases](https://github.com/microsoft/playwright-python/releases),
[Graphiti releases](https://github.com/getzep/graphiti/releases),
[Neo4j releases](https://neo4j.com/release-notes/),
[Qdrant hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/),
[Qdrant hybrid baseline](https://qdrant.tech/course/beginners/module-3/hybrid-search-in-qdrant/).

## Bounded model comparison

`scripts/benchmark_memory.py` runs the same actual A–R synthetic evaluation for
three candidates. The optional third candidate isolates the runtime change by
using the same MiniLM dense model through ONNX. Five positive retrieval queries
and six unsupported assertions are a small fixture, not a general quality claim.

| Candidate | Dense top-5 | Full retrieval top-5 | Unsupported accepted | Dense batch median | Rerank batch median |
| --- | --- | --- | --- | --- | --- |
| sentence-transformers MiniLM + existing cross-encoder | 5/5 | 5/5 | 0/6 | 11.61 ms | 10.28 ms |
| FastEmbed BGE small v1.5 + Xenova MiniLM L6 | 5/5 | 5/5 | 0/6 | 9.94 ms | 6.76 ms |
| FastEmbed MiniLM + Xenova MiniLM L6 | 5/5 | 5/5 | 0/6 | 5.62 ms | 8.11 ms |

All three pass A–R, the three temporal cases and entity cases. BM25 alone hits
4/5; semantic retrieval supplies the paraphrase case. Batch timing uses two short
texts and five samples, with ordinary laptop background activity. An earlier
measurement reversed the small BGE/Torch dense timing difference; these numbers
do not establish a universal performance ranking.

Default: **FastEmbed BAAI/bge-small-en-v1.5**, **Qdrant/bm25 + Qdrant IDF**,
RRF, **FastEmbed Xenova/ms-marco-MiniLM-L-6-v2**. Equivalent fixture quality and
one ONNX runtime justify replacing the Torch default. BGE's tested ONNX artifact
is 66,465,124 bytes versus MiniLM's 90,387,630 bytes; its supported input limit
is 512 tokens versus MiniLM's 256. This favors BGE's size/context tradeoff despite
MiniLM's faster tiny dense batch; improved long-input quality is not claimed.
The reranker artifact is 90,992,115 bytes. In the final sequential cached run,
construction took 10.60 seconds for the Torch pair, 0.57 seconds for BGE/ONNX and
0.56 seconds for MiniLM/ONNX. The first Torch construction includes SDK imports.
Separate fresh-process observations were 30.53 seconds versus 1.90 seconds before
adding artifact fingerprints; these are single observations with background load,
not a standardized cold-start ranking. Initial ONNX download/load took 146 seconds
for BGE/reranker and a further 91 seconds for the optional MiniLM candidate.
Model startup/download observations,
artifact revisions and complete fixture results are in the evidence JSON.

Dense/reranker loaders are offline by default. Preload public models explicitly,
then set `FASTEMBED_CACHE_PATH` to that cache. Their identities fingerprint the
actual ONNX/tokenizer artifacts, so changing a cached model fences old projections.
EmbeddingProvider, SparseEmbeddingProvider and Reranker remain replaceable.

## Generation integrity and failure behavior

SQLite triggers advance a per-relationship archive generation in the same
transaction as canonical event, memory, entity or alias changes. This covers
retention, correction, consolidation and forget. Derived states record relationship,
adapter/model identity, generation, digest, state and update time.

Rebuild writes REBUILDING before touching the index. It reads at most 10,000
canonical records; an oversized rebuild is refused, and Graphiti rebuild has a
300-second cancellation deadline. Completion stamps a physical
projection digest last, then records CURRENT in SQLite. A crash before either
stamp cannot manufacture freshness. Failure records FAILED without undoing
canonical history. Concurrent archive writes leave a generation mismatch, and a
write during retrieval fences that recall as UNKNOWN. There is no automatic
unbounded rebuild daemon.

Retrieval requires matching archive generation, durable CURRENT state and actual
physical digest/model identity. Otherwise the index is explicitly OUTDATED and
excluded. Active/structured context, FTS5/exact archive and remaining valid indexes
continue. Lost Qdrant storage, separate service failures, embedding and reranker
failures are exercised. No fallback to a model guess is admitted.

## Graphiti compatibility and isolation

The old adapter's `reference_time=None` was saved through Graphiti's public
EntityEdge API. Neo4j does not retain a property with a null value; Graphiti's
native vector/fulltext projections then read a missing property and emitted
01N52. The warning reproduced before the patch. Edges now explicitly carry
canonical reference time, validity intervals and source-episode references.
Native acceptance runs without these warnings; no logging filter hides them.

The database target is explicit. All episode/entity/object/edge UUIDs are
namespaced by OSCAR projection group. A group/collection represents one relationship;
cross-relationship rebuilds, including an empty unrelated relationship, are blocked.
Only ownership-labelled projection nodes are reset. Foreign relationships touching
owned nodes block destructive rebuild rather than being detached. Forget deletes
only owned matching edges. A second group and an unrelated same-group node survive
repeated rebuilds. No database-wide clear is used.

Graphiti LLM extraction remains disabled. OSCAR's validated Memory Writer owns
canonical facts; graph search returns canonical IDs for independent admission.

## Credential enrollment/recovery

Enrollment stores a durable intent and predetermined opaque vault reference before
writing native credentials. Device enrollment progresses through enrolling_device
to pending. Token exchange has a durable polling intent; a lost external response
is failed/ambiguous and never automatically replayed. Validated token metadata is
persisted as enrolling_token before vault write, then ready/authorized is committed
before the obsolete device reference is deleted.

Restart deliberately aborts undelivered device enrollment. A staged validated token
with a matching native entry can become ready; a missing/expired entry requires
reauthorization. Authorized device-reference cleanup is idempotent. Local disconnect
persists revoke_pending before native deletion, then local-disconnected state.
Fault injection covers twelve boundaries, and a real child-process crash after a
native token write recovers without another provider request. SQLite never contains
device/access token bytes.

Remote revocation stays UNKNOWN/owner-action-required. This registered-client device
flow cannot confirm provider revocation without additional provider credentials.
Local deletion is not a logout-everywhere claim. The vault/SQLite pair is recoverable,
not an atomic cross-store transaction or protection from a malicious same-account host.

## Claim and manual-harness boundaries

The bounded response context retains claim ID/type, canonical event/memory IDs,
retrieval paths, epistemic state, confidence and temporal interpretation. Claims
must match current canonical evidence at the requested historical instant. Empty
support, failed required retrieval, unresolved entities, forgotten/expired or
superseded cached support produce UNKNOWN. A lucky exact guess without retrieval
is unsupported. RECALLED remains distinct from VERIFIED; arbitrary paraphrase
entailment remains outside this exact-source verifier.

Each manual run has a unique fixture ID and exclusive evidence root. Mutations
require the bound PID/window, current fixture title and unchanged fixture editor
content. Stale prior fixture windows are reported, not closed. Ambiguous close or
discard state stops for owner review. Own browser/server resources are cleaned;
actions and failure metadata remain for debugging. Worker operations are bounded
and new actions stop at the overall deadline. A failed precondition is explicit;
an existing root is refused. This pass tests the harness's ownership guards,
but does not run physical/manual desktop acceptance.

Owner command from the repository root:

```powershell
$root = ".oscar\manual-gate-b-" + (Get-Date -Format "yyyyMMdd-HHmmss")
python -m scripts.verify_gate_b_interactive --root $root --desktop
```

Remaining mandatory work includes owner manual review, registered-client private
OAuth/readback/revocation limitations, private live-authority federation and broader
continuous conversational acceptance. Sunday/Android/OEM, voice, hardware and private
cloud accounts remain unverified. Do not start Slice 07 or merge PR 12.

## Automated quality evidence

The full Windows suite passes **384 tests**. Ruff, format, strict mypy (48 source
files), repository/local Markdown contracts, value-silent secret scan and Git diff
checks pass. A–R runs pass for all three candidates; native index acceptance covers
exact identifiers, IDF, scope, temporal/source readback, reopen, drift/rebuild, forget,
group isolation and injected local ML outages. The additional unit regressions
include canonical process interruption, concurrent-write fencing, physical marker
loss, separate index outages, unsupported claims, twelve enrollment/disconnect fault
boundaries and a native-vault process crash. Full results and artifact hashes live in
[the synthetic evidence bundle](evidence/gate-b-hardening-2026-10-04.json).
CI must be checked at the latest PR head; manual/OAuth acceptance remains absent.


## Owner manual failure and focused harness repair (2026-10-04)

The owner run `.oscar/manual-gate-b-20261004-175011` is a **failed manual
acceptance attempt that exposed harness defects**, not a capability PASS.
Direct-file invocation failed to resolve `oscar.interactive_worker`; repository-root
module invocation entered the harness. Five successful REPORTED actions ended at
`desktop mouse_click`, followed by the one-shot independent focus assertion.
The synthetic fixture remained zero bytes. The old failure record contains a blank
`AssertionError`; it did not retain the actual focused PID, so asynchronous settling
is a possible cause rather than a proven explanation of the Windows focus state.
See [the bounded failure evidence](evidence/gate-b-manual-harness-failure-2026-10-04.json).
The original ignored owner evidence root is preserved unchanged.

The documented command above now uses the package module. Automated `--help`
invocation from the repository root checks imports without driving the desktop or
changing global `PYTHONPATH`. After a typed click, independent read-only UIA snapshots
poll for at most three seconds with short sleeps and remaining-budget subprocess
limits. Each snapshot brackets focus with exact window PID/handle, fixture title,
editor runtime ID and empty-content checks. The previously observed focus may
remain briefly while settling; it never counts as success. A different foreign PID
or changed fixture identity blocks immediately. Only the exact bound PID passes.
No retry click or focus mutation is added.

All acceptance assertions are named checks. Failure evidence records phase/check,
exception type, safe expected/observed summaries, traceback file/line/function,
fixture/target identity, last successful action/capability, actions path, evidence
root and cleanup state. Text/title/URL content is represented by hashes and lengths;
private desktop contents and arbitrary exception messages are not dumped.
Stale OSCAR windows are reported and remain for owner review; no prior or unrelated
window is closed. Failed roots are never reused or erased.

Automated harness regressions cover delayed focus, foreign focus, timeout, before/
after identity changes, stale-window protection, diagnostic persistence, safe rerun,
observer timeout propagation and native PowerShell syntax parsing without executing
UI actions. These tests do not constitute physical acceptance.
Slice 05 remains COMPLETE for its recorded Windows local-alpha scope; Slice 06 and
Gate B remain PARTIAL. Final owner manual acceptance and private OAuth acceptance
remain outstanding. This repair does not authorize or start OAuth or Slice 07.


Focused repair automated evidence: **397 Windows tests pass in 87.992 seconds**;
the focused harness/hardening selection passes 25 tests, including 13 new harness
regressions. Ruff, format, strict mypy (48 source files), repository contracts,
local Markdown links, secret scan and Git diff checks pass. Cross-platform and
external-link CI must match the final repair head on draft PR 12. No physical
manual rerun was performed by the agent.

## Owner desktop success and browser launch repair (2026-10-04)

The owner rerun `.oscar/manual-gate-b-20261004-190338` passed the owned Notepad
sub-phase: binding, independent focus/text/empty-text readback, owned tab closure
and empty fixture deletion. Its SQLite evidence includes independent test-tab
absence; `actions.json` alone does not contain the final verification update.
No stale fixture windows were reported. The first local browser action failed at
`runtime.operation`. **Overall final manual acceptance remains outstanding.**
The original owner evidence directory remains unchanged. See
[the bounded browser repair evidence](evidence/gate-b-browser-launch-repair-2026-10-04.json).

Independent reproduction showed direct-file execution of `oscar/browser_worker.py`
from an artifact directory fails with `ModuleNotFoundError: No module named 'oscar'`.
The acceptance venv could resolve the source and masked this failure; a fresh venv
without pip or OSCAR reproduced it. The owner's original generic failure did not
retain subprocess stderr, so its exact stderr cannot be reconstructed.

`InteractiveWorker` now invokes a fixed OSCAR-owned package entrypoint. Python
isolated mode (`-I`) excludes cwd, user-site and `PYTHONPATH`; standard importlib
package loading anchors `oscar.browser_worker` to this Worker's trusted source
package, separately from the artifact cwd. No `sys.path` modification, global
`PYTHONPATH` or editable installation is required. Dependencies still must be
installed in the explicitly allowed interpreter. The Machine Worker's executable,
cwd, environment, timeout, output and Job Object authorization remains unchanged.
Playwright contexts remain nonpersistent with explicit origin admission and pinned,
exclusive artifact creation. This remains trusted-host execution, not a sandbox.

Preflight uses the same command builder, interpreter and artifact cwd with
`--probe`, loads the actual worker and launches/closes headless Chromium without
opening a page. An eight-second subprocess deadline, bounded output and process-tree
cleanup apply. Missing Playwright, missing Chromium, worker import and launch errors
have distinct categories; an unavailable path never advertises `machine.browser`.
The harness checks this before starting desktop actions.

Browser failures emit category and exception class only. The Worker retains only
allowlisted categories/classes, exit code and byte count from bounded output;
arbitrary stderr, URLs, selectors, page contents, cookies and credentials are
discarded. The harness records a named `browser.*` failure instead of generic
`success: false`. Timeout/cancellation retain their existing runtime semantics.
There is no automatic retry of an action or mutation.

New automated regressions exercise an uninstalled source checkout, poisoned cwd/
`PYTHONPATH`, missing dependencies/executable, actual import failure, unavailable
capability advertisement, output bounds/redaction and scoped subprocess cwd.
Real synthetic Chromium execution independently checks download bytes and PNG
signature in a disposable artifact workspace, then rejects an overwrite through
the real failed Worker path. Existing origin/reparse-point/isolation, cancellation,
timeout and stale-owner-window protections remain in the suite. These automated
checks do not replace the owner's final manual acceptance.

Use the pinned acceptance interpreter from the repository root for the rerun:

```powershell
$root = ".oscar\manual-gate-b-" + (Get-Date -Format "yyyyMMdd-HHmmss")
& .\.oscar\gate-b-venv\Scripts\python.exe -m scripts.verify_gate_b_interactive --root $root --desktop
```

The general `python -m scripts.verify_gate_b_interactive` command remains valid
when `python` selects an interpreter with the browser extra and Chromium installed.
Slice 05 remains COMPLETE for the recorded Windows local-alpha scope; Slice 06 and
Gate B remain PARTIAL. OAuth and Slice 07 are NOT STARTED; PR 12 stays draft/unmerged.

Repair verification: **408 Windows tests pass in 97.392 seconds**, including all
real Chromium lifecycle tests; the focused selection passes 50 tests. Eleven new
regressions were added. Ruff, format, strict mypy (48 source files), repository
contracts, local Markdown links, value-silent secret scan and Git diff checks pass.
Ubuntu and external links must be checked on this repair's exact PR head.


## Subsequent owner physical/manual machine PASS

**FINAL PHYSICAL/MANUAL MACHINE ACCEPTANCE PASSED** in owner run
`.oscar/manual-gate-b-20261004-200734`. Desktop, local browser and public browser
phases are VERIFIED, with independent UIA/HTTP/HTTPS observations and owned cleanup.
The stale prior OSCAR fixture was reported and not mutated. See
[the preserved owner evidence summary](evidence/gate-b-owner-machine-pass-2026-10-04.json).
This supersedes the outstanding manual rerun status above; earlier failures remain
valid historical evidence. No agent physical rerun was needed.

[The owner OAuth/federation harness](GATE-B-OAUTH-ACCEPTANCE.md) is prepared using
existing OSCAR device flow/vault/connector/archive/federation components. Only
synthetic provider responses are exercised here. Real private OAuth and federation
remain outstanding; Slice 05 COMPLETE, Slice 06 PARTIAL and Gate B PARTIAL.

Preparation verification also reproduced a browser timeout cleanup race in the
existing Windows Job Object boundary. The result was correctly a timeout, but a
descendant could still hold the artifact directory after asynchronous job close.
The repair explicitly terminates the exact job and waits on bounded, membership-
checked process handles before release, with kill-on-close retained as a backstop.
Existing real cancellation/timeout tests pass without weaker cleanup assertions.
Contract regressions cover owned-process drain, foreign PID rejection, bounded
failure and idempotent close. No owner window or unrelated process is touched.


Preparation quality: **427 Windows tests pass in 108.682 seconds with no skips**;
91 focused OAuth/credential/connector/federation/job contract tests pass. Nineteen
regressions were added. Ruff, format, strict mypy (48 source files), repository
contracts, local Markdown links, secret scan and Git diff review pass. The native
vault process-reopen test uses only synthetic credentials/provider responses.
Real OAuth remains NOT AUTHORIZED; real private federation remains NOT EXERCISED.
Check Ubuntu/Windows/external-link CI at the final PR head.
