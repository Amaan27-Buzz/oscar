# Club B foundation checkpoint — 2026-10-03 IST

## Local Windows completion pass — 2026-10-04 IST

**Slice 05: PARTIAL. Slice 06: PARTIAL. Gate B: PARTIAL.**
The useful Windows machine/Codex/local-continuity scope below is VERIFIED; it does
not complete every slice or Gate B criterion. Gate A remains unchanged. No Slice
07, Sunday, voice or UI implementation was started.

Started from exact fetched remote `work` SHA
`1d3778370495a05a84ca0badfea943cd5fb6d5be`, after confirming PR #10 was MERGED into
`work` and its `cfa8c2fdeb2de0b4dbb2d912102be476f718ef4e` merge commit was an ancestor.
Branch: `overnight/club-b-windows`; checkpoint commits are pushed. The final branch
SHA/PR/CI conclusion are reported at delivery; this document cannot contain its
own final commit hash. Earlier reference evidence below remains historical.

[Machine-readable local evidence](evidence/club-b-windows-2026-10-04.json) records
Windows platform, real task/correlation IDs, independent file hash and Git baseline,
coordinator process IDs, failed attempts and limitations. Disposable repositories
and SQLite state remain under ignored `.oscar/` for local inspection. No provider
keys, authentication file or specialist transcript is committed.

### Observable acceptance and evidence

- **Windows Worker:** real file read/write/list/filename search and UTF-8 content;
  traversal/drive/UNC/ADS/device aliases, junctions and symlink parents reject;
  reparse entries are excluded from listings. `CreateFileW` ancestor handles with
  read access/no delete sharing pin paths; rename regression passes. Git
  status/diff/log/new-file commit is real, with independent bytes/HEAD-tree checks.
- **Native processes:** explicit absolute `.exe` allowlist, no shell shims,
  filtered environment, bounded timeout/output and `machine:host` permission.
  Suspended creation → Job assignment → resume prevents execution before tree
  control. Real descendants terminate on cancel, timeout, output overflow, parent
  exit and abrupt Worker process death. Job-assignment rejection never starts the
  child. Initial pause/resume is verified; Windows pause means before the next
  subprocess, **not suspension of a running arbitrary process**. HTTP acknowledgments
  qualify that behavior; paused wall time counts toward timeout.
- **Useful Codex specialist:** Jev structured coding objective → advertised Codex
  capability → separate Machine Worker → native authenticated Codex CLI → actual
  `intervals.py` repair in a disposable Git repo. Nested intervals formerly shrank
  the merged endpoint; the fix preserves the maximum. Core's separate inspector
  runs nine behavioral cases, input-immutability/invalid-input checks, sole-file
  Git diff and unchanged baseline HEAD. Baseline fails independently; corrected
  behavior passes. Result remains REPORTED; only independent evidence is VERIFIED.
- **Codex failure/cancel/recovery:** no-mutation success testimony was correctly
  FAILED by independent checks. An invalid real invocation FAILED without changing
  the verified file. A separate real Codex subprocess reached running state, then
  HTTP cancellation killed its job and task became CANCELLED with the same artifact
  hash. Lost-result recovery after Worker restart reused one completed execution.
  Initial wrong-specialist/timeout/read-only/extra-bytecode failures are preserved
  in the evidence rather than recast as successful acceptance.
- **Actual coordinator restart:** first coordinator PID `36760` exits, Worker exits,
  reconnect starts another Worker and coordinator PID `8068` recovers the same
  completed result. File/Git checks verify once; checkpoint stays identical and
  execution count stays one. This strengthens the earlier same-process composition
  restart proof without pretending to implement independent distributed stores.
- **Ambiguous mutation:** a disposable command actually writes a marker and starts
  a child; the Worker OS-process is terminated abruptly. The child dies, task
  BLOCKS, reconnect/reclaim cannot replay the started dedup action, and the existing
  marker remains one mutation. No repository or OS damage was induced.
- **Memory/Policy:** selected synthetic project memory and owner-confirmed policy
  survive actual coordinator process restart. Recall stays RECALLED; current file
  state outranks stale memory. Missing permission and equal-ranked conflicts block.
  Forget removes the live OSCAR memory row, with no disk/WAL/backup erasure claim.
- **Natural-language Policy:** exact message/send phrases produce a shown inactive
  structured candidate. Owner confirmation binds its review digest; wrong/stale/
  altered/duplicate confirmation and conflicting interpretations reject activation.
  Ambiguous/compound instructions remain unsupported. Later external-communication
  evaluation requires per-action confirmation while missing grants still block.
  This is a trusted local editor, not open-ended model authority or remote identity.
- **Future Sunday:** canonical design reaffirmed assistant role/voice-interaction,
  optional attention-aware Orb/hotspot/reappearance, configurable context widgets,
  permissioned notification summaries/RemoteInput, official API preference,
  Chief-of-Staff replanning and independent presence/awareness/retention/action
  controls. **Documentation only; target Samsung behavior is entirely unverified.**

### Final local quality checks

**319/319 tests PASS in 73.878 seconds**, including 14 actual Windows-specific
regressions and all existing baseline cases. Ruff PASS; format PASS (63 Python
files); strict mypy PASS (43 source/script files, Windows and Linux platform
targets). Repository required-file/local-link/value-silent secret scan and Git
diff checks PASS. Existing urllib HTTPError ResourceWarnings are non-fatal on local
Python 3.14. Windows and Ubuntu Python 3.12 CI are now separate jobs; CI conclusions
are reported independently from local evidence, using GitHub PR merge-ref checkout.

### Boundary and remaining acceptance

Trusted-host execution is not an OS sandbox. Approved interpreters/agents can
access host files/network as the laptop user; hostile repositories/local writers,
hard links, Git internal config/filter attacks, credential isolation and restricted
user/AppContainer/container execution remain unsafe/unverified. Codex's useful
acceptance explicitly used trusted `danger-full-access` in the disposable fixture
after workspace-write behaved as read-only. Its own auth home is supplied explicitly;
OSCAR provider environment keys are not inherited. See [SECURITY.md](SECURITY.md).

Gate B cannot PASS from unit-test volume. Browser/computer-use and broader installed
app execution, authenticated private connector accounts/OAuth, actual Supermemory
service, public remote TLS/rendezvous, independent node stores, secure platform
storage, remote power, Sunday/Android/phone supervision, voice and physical hardware
remain partial/unverified. Supermemory remains the existing `MemoryBackend`
boundary; no service was fabricated. Broad natural-language policy, calendar/task
automation and future World Model/Chief-of-Staff behavior are not implemented here.

### Morning physical/manual review

Inspect the retained Codex fixture `.oscar/codex-acceptance-05/repository`, its
single-file diff and `.oscar/windows-codex.json`; inspect local task/evidence/dedup
state before changing any ambiguous record. Re-run the documented local scripts
with a new empty state-root. Review the PR into `work`, particularly trusted-host
scope and cooperative pause semantics. Any browser/private account/Supermemory or
Samsung acceptance is separate work requiring real access/device evidence. Do not
merge automatically or start Slice 07 from this checkpoint.

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
