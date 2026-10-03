# Club B foundation checkpoint — 2026-10-03 IST

**Slice 05: VERIFIED reference Worker foundation; full slice PARTIAL.**
**Slice 06: VERIFIED local/reference memory and policy foundation; full slice PARTIAL.**
**Gate B: PARTIAL, not PASS. Gate A PASS is preserved.**

Started by fetching all actual remote branches (the cloud checkout initially fetched
only main), confirming remote `work` at
`c12fc0ec48e24b68a5fd59b58931170982c6067c`, clean status and the latest Gate A PASS.
Created isolated **`overnight/club-b-foundation`** from that exact head. No main
modification and no merge into main/work. Periodic checkpoint commits were pushed.
Final remote head SHA and GitHub PR merge-ref SHA are reported separately at delivery;
this source cannot embed the hash of its own final commit. GitHub `pull_request` CI
uses the generated merge ref combining this branch head with the `work` base, via
`actions/checkout@v4`; it does **not** check out the exact raw branch head. The prior
delivery's raw-head CI wording was incorrect.

[Machine-readable evidence](evidence/club-b-reference-2026-10-03.json) preserves
task/correlation IDs, observation times, actual artifact commit, public URLs and
original limitations. These are bounded reference observations, not global success.

## Implemented and verified

1. **Connector Fabric:** typed manifests/instances/capabilities/auth/scopes/risk/
   connection state/results/events and opaque credential refs. Existing Grid is
   the executable catalog. Existing Dispatcher/Runtime/ledger/verifier semantics
   remain authoritative; provider facts are not hard-coded into Jev. TLS, bounded
   input/output and no redirects protect the real HTTP boundary. Private bodies
   and results are transient task context, while durable Actions use opaque input
   references. Restart expires private input rather than silently retaining it.
2. **Google:** 35 official-discovery-backed methods across Gmail search/read/threads/
   drafts/send/labels/history; Calendar list/get/create/patch/delete/freebusy; Drive
   search/metadata/download/export/metadata create/patch; Classroom courses/
   coursework/submissions/announcements; Docs get/create/batchUpdate; Sheets
   metadata/ranges get/update/create; Slides get/create/batchUpdate. All 35 traveled
   through the actual bounded adapter to a **synthetic local HTTP provider**.
   Contract bodies are bounded objects; full provider schemas remain provider-side.
   Caller pagination is explicit; no full-inbox inventory or media upload claim.
3. **Other providers:** concrete thin Graph mail/calendar/OneDrive/Teams/SharePoint,
   GitHub repositories/issues/PRs/commits/Actions/status, Slack channels/history/
   search/post, Notion pages/blocks/databases/data sources and reviewed MCP-session
   foundations. Cross-provider Grid discovery passes. MCP annotations cannot lower
   reviewed risk; Fabric requires scope/confirmation even for a server claiming
   a destructive tool is read-only. **Private/live account access is UNVERIFIED.**
4. **Connector verification:** mutation testimony remains REPORTED. Independent
   correlated resource GET and expected-field comparison can verify a scoped
   objective; missing read permission, another account, unrelated resource and
   mismatched fields cannot upgrade it. Gmail recipient/header and arbitrary
   Docs/Sheets/Slides nested/batch matching remain PARTIAL. Missing auth/scopes/
   availability/policy blocks rather than producing plausible data.
5. **Machine:** real POSIX FD-scoped file write/read/directory list/filename search;
   configured executable and coding-agent discovery; opt-in trusted-host terminal,
   Git status/diff/log/branches/commit and a bounded clean-repository new-file/commit
   objective. Explicit cwd/executables, environment filtering, process-group
   timeout/cancellation, bounded transient output, correlated metadata checkpoints,
   lease renewal and target policy checks. No fake power capability.
6. **Coding agents:** Codex executable was discovered and advertised in cloud;
   `--version` passed through a real Worker subprocess. Claude Code, OpenCode and
   Gemini CLI were absent/unadvertised. **No authenticated coding objective or
   model-generation request was run.** Installed version is not coding acceptance.
7. **Continuation:** Core and Worker ran as separate processes over actual loopback
   HTTP with SQLite and a temporary Git workspace. Worker made a real commit;
   the result was deliberately lost. Core/Worker restarted, durable checkpoint
   survived, reconnect/reclaim reused the original completed result, and mutation
   count stayed one. Core independently read bytes/HEAD tree/new commit/clean status
   before VERIFIED. HTTP pause/resume/cancel passed. Real mid-command node loss
   left BLOCKED/ambiguous state with automatic replay prohibited. Tests also cover
   lying executor, expiry/stale renewal, traversal/symlink/cwd violation, timeout,
   output bound, cancelled process and unavailable agents.
8. **Memory:** selected persistent episodic/project/device/procedural/profile/
   relationship/semantic/communication/Worker items with source/time/evidence/
   confidence/retention/expiry/entity references. Bounded lexical scoped retrieval
   survives restart. Explicit retention and forget/purge are implemented. Verified
   retained text must match actual independent evidence hash/time; recalled items
   always present as RECALLED. `MemoryBackend` is the semantic-service boundary,
   not a fake Supermemory integration.
9. **Policy:** explicit structured owner-authorized rules; scope/exact conditions,
   priority/specificity, source/timestamps, enabled/expiry and preferences. Hard
   constraints and missing permission/confirmation outrank policy; specific rules
   beat broad ones; equal-priority conflicts block. Deny survives confirmation.
   Inferred candidates cannot become authority. Preferences are evaluated but not
   automatically wired into the Model Router; arbitrary natural-language parsing
   and user quiet-hour interpretation are not implemented.
10. **Live context/entities:** scope-bound current-file/Grid/Worker-state, native
    search/freshness and authorized connector callback adapters. Current authoritative
    live sources outrank stale memory while preserving REPORTED status where needed.
    Canonical typed entities and a small relation vocabulary require matching
    evidence claim fields; same labels/unrelated evidence do not merge identities.
    Graph forget removes live relations/bindings, preserving unknown identities.
11. **Integrated acceptance:** structured Jev objective → existing catalog → target
    Personal Policy denial prevents file creation → explicit structured approval
    enables a new task → separate HTTP Worker/Git work → Core inspection/ledger →
    selected verified project retention → later RECALLED retrieval → actual file
    changes override historical memory → live-record forget. **PASS for this
    reference scenario**, not for all Gate B exit criteria.

## Final quality and network evidence

- **274/274 tests PASS in 38.441 seconds**, retaining all 227 baseline tests and
  adding 47 meaningful contract/failure/network/continuity cases. No Gate A
  assertion was weakened. A coherent earlier checkpoint passed 266 tests.
- Ruff check PASS; formatting PASS (**55 Python files**); strict mypy PASS
  (**30 OSCAR source files**). Repository/local-link and value-silent secret checks
  PASS after canonical documentation propagation. Full final diff was inspected.
- Separate `verify_worker_reference` and `verify_club_b` scripts PASS. CI includes
  those subprocess/network scenarios through unittest; public tests are opt-in.
- **Real public network:** official API/standard documents fetched with TLS through
  the configured cloud proxy; concise method/scope/version provenance is in
  [CONNECTOR-FABRIC.md](CONNECTOR-FABRIC.md). Public unauthenticated GitHub
  `https://api.github.com/repos/python/cpython` returned matching repository identity.
  The record retains URL/time/evidence ID and REPORTED provider testimony.
- GitHub's official current reference selected **2026-03-10** after research showed
  that as latest. A separate initially older-version public observation is retained.
  A guessed versioning-doc URL failed; the successful official repository reference
  supplied the correct version. No private authenticated GitHub claim is made.
- **Synthetic:** 35 Google HTTP calls plus fixture read-back, errors/scopes/risk,
  redirects, OAuth references/PKCE and MCP sessions. These are deliberately not
  described as live Google/Slack/Notion/Microsoft account verification.

## Remaining scope, architectural debt and security limits

Gate B requires actual useful coding-specialist work, Windows/real machine,
browser/computer-use and natural-language policy acceptance that were not verified.
Sunday/phone supervision, platform secure storage, provider account enrollment/
OAuth refresh/device-flow implementation, authenticated private Google/Graph/
GitHub/Slack/Notion/MCP, semantic Supermemory, independent Worker state stores,
public TLS/outbound rendezvous and all physical power/wake paths remain pending.
No UI, Sunday app, voice or Edge hardware slice was started.

The explicit trusted-host terminal grant is powerful: cwd is **not an OS sandbox**,
and an allowed Python/agent process can access host resources. Do not grant
`machine:host` to untrusted principals. A future OS/user/container boundary and
host supervisor must handle hostile repositories and abrupt Worker-process death;
current process-group cancellation handles normal controlled task loss. Reference
Grid reaping owns task lease/zombie detection, not OS-level crash supervision.

The reference intentionally shares coordinator SQLite. This proves process/network/
state contracts without pretending to solve independent node replication/public
pairing. Lost completed results are recoverable; started uncertain mutations require
manual resulting-state inspection. Connector inputs expire on restart and require
re-supply with fresh authorization. Deletion removes live rows/graph links, not
verified SQLite WAL/backups/connected-source erasure. Provider-specific read-back,
pagination orchestration, push-signature validation/subscription setup and richer
semantic retrieval are explicit follow-ups. No new runtime dependencies were added.
Known runtime credential values are rejected before durable plans/policy/memory/
entity retention and filtered from transient output; scans print no credential values.

## Files and checkpoint commits

New modules: `connectors.py`, `connector_providers.py`, `machine.py`,
`machine_node.py`, `policy.py`, `continuity.py`, `context_sources.py`, `entities.py`.
New Google manifest: `config/google-connectors.json`.
New scripts: `verify_worker_reference.py`, `verify_club_b.py`,
`verify_connector_public.py`. New tests: connector contracts/synthetic HTTP,
Worker, continuity/policy and integrated acceptance. Existing core contracts/Grid/
Runtime/Dispatcher/ScopedFiles/credential/storage modules received narrow additive
changes. Canonical docs and evidence were updated where materially affected.

Pushed implementation checkpoints before the final quality/docs commit:

- `a518e78` — Connector Fabric + official provider foundation.
- `d9ec03e` — machine Worker + durable network continuation.
- `ca0355b` — memory/policy/live context + integrated acceptance.
- `fc65875` — synthetic HTTP + current-version public GitHub acceptance.

## Morning review

```sh
python -m pip install '.[dev]'
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m unittest discover -s tests -t . -v
python -m scripts.check_repository
python -m scripts.verify_worker_reference --report .oscar/worker-review.json
python -m scripts.verify_club_b --report .oscar/club-b-review.json
python -m unittest tests.test_connectors tests.test_connector_http -v
python -m scripts.verify_connector_public --run-public --report .oscar/public-review.json
```

For retained local reference state, pass a **new empty path** with
`--state-root .oscar/morning-worker-unique`. Inspect the actual Git artifact/HEAD,
SQLite task/evidence/ledger and checkpoint; see documented API limitations before
supplying account credentials. No live credential material should enter fixtures,
command arguments, source files, reports or review screenshots.

Manual laptop acceptance must separately port the POSIX reference to Windows,
pair the real node with scoped grants, run a useful coding-agent objective and independently
test resulting changes, disconnect/reconnect/pause/cancel it, verify GUI/browser
work and platform storage. Remote power stays unavailable unless actually implemented.
Natural-language policies need owner-confirmed interpretation before activation.
**Next recommendation: finish Slice 05 Windows/isolated host execution and real
coding/browser acceptance, then Slice 06 semantic/authenticated continuity.**
Review the PR into `work`; do not merge automatically or advance to later slices.

## PR #10 pre-merge review follow-up

The lifecycle, trusted-manifest readback, and composite consequence corrections are
specified in [CONNECTOR-FABRIC.md](CONNECTOR-FABRIC.md). They stay within the existing
foundation: no new slice and no merge. Regression coverage includes 120 sequential
Runtime connector tasks with no retained prior payloads; cancellation before/during
execution, provider/permission/endpoint/routing failure, verifier errors, restart,
unchanged active-context bounds, cancellation races across Store instances, readback capability/resource/account/executor attacks,
and additive permission/policy/confirmation checks across current communicating mutations.
The historical 274-test checkpoint above is preserved. This follow-up passed **295/295
tests in 38.910 seconds**, including 21 new regressions; 105 focused connector/Core/Grid/
policy-continuity cases passed. Ruff lint/format (55 files), strict mypy (38 OSCAR/script
files), repository/local-link checks and value-silent source/patch secret scans passed.
Final head/base/merge SHAs and workflow conclusions are recorded in the PR delivery report.
