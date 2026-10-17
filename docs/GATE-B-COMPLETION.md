# Gate B completion ledger

> Original-repository PR/run URLs below are historical identifiers retained verbatim.
> They are no longer accessible after repository migration and are not current CI evidence.

> Current status reconciliation, 2026-10-05: PR #12 is merged at `97c0622507df3f724ecf0c8b74aa7f4ae7784b08`; Gate B is frozen PASS. Slice 05/06 COMPLETE. Slice 07 software is accepted for continuation; physical Edge acceptance is DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED. Slice 08 is authorized after integration. The dated evidence below retains its historical status wording.

Working branch: `gate-b/completion`. Baseline fetched on 2026-10-04:
`main=d90e3624d5e8cf68874c9bb136ed54a8ddbb6f9a`,
`work=a34844133e9fc7f81ca21f5bfec966ff819777d3` before authorized fast-forward.
`work` had zero unique commits and was fast-forwarded to `main`.

This ledger tracks mandatory acceptance; unchecked items remain current Gate B work.
Historical acceptance is not relabeled as current execution.

- [x] Useful Codex objective independently verified on current implementation
- [x] Scoped filesystem/Git work
- [x] Typed PowerShell, filtered environment, timeout and cancellation
- [x] Legitimate installed-app catalog and harmless Notepad launch
- [x] Bounded real UI Automation mutation and independent readback
- [x] Typed isolated browser: local interactive fixture and public page
- [x] Worker disconnect, actual process-tree cancellation and no duplicate recovery
- [x] Ambiguous interrupted mutation BLOCKS
- [x] Separate owner-control observation, disconnect/reconnect and continuation
- [x] One relationship, canonical SQLite WAL/FTS5 archive and restart
- [x] Source-bound Memory Writer and scoped preferences
- [x] Real Qdrant hybrid retrieval, scope filtering, restart and rebuild
- [x] Real Graphiti/Neo4j temporal/entity retrieval and rebuild
- [x] Replaceable local embeddings and reranker with truthful fallback
- [x] Jev preflight, bounded retrieval/context composition API
- [x] Exact evidence-bound recall and unsupported historical claims UNKNOWN
- [x] Temporal correction, current/history distinction, aliases and ambiguity
- [x] Forget across archive/FTS/vector/graph; no secure-erasure claim
- [x] Bounded consolidation preserves sources; durable atomic batch cursor
- [x] A–R memory evaluation with measured errors
- [x] Model policy candidate, exact fixture confirmation, conflict/expiry
- [x] Native secure credential write/read/rotate/expiry/delete/restart
- [x] Final physical/manual machine acceptance by owner (2026-10-04, run 200734)
- [x] Real owner-authorized OAuth/private read and lifecycle (run 234817)
- Optional, NOT AUTHORIZED: reversible private write/readback/cleanup; no `gist` grant
- [x] Live file/project/task/private/public federation beats stale recall
- [x] Full Windows suite, cross-platform CI, lint/types/repository/links/secrets

## Current official sources

Retrieved 2026-10-04. These define API choices; observed acceptance is separate.

- [Microsoft UI Automation](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-overview): structured elements/control patterns before coordinate fallback.
- [PowerShell security](https://learn.microsoft.com/en-us/powershell/scripting/security/security-features): execution policy is not containment; use fixed typed operations, existing host permission and Job Objects.
- [Credential Manager write](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew): per-user native credential storage, not plaintext SQLite tokens.
- [Playwright isolation](https://playwright.dev/python/docs/browser-contexts): new nonpersistent contexts; never borrow personal profiles.
- [SQLite WAL](https://sqlite.org/wal.html) and [FTS5](https://sqlite.org/fts5.html): durable canonical events plus bounded lexical retrieval.
- [Qdrant OSS quickstart](https://qdrant.tech/documentation/quickstart/): official client/local mode or scoped self-hosted server; derived references only.
- [Graphiti OSS source](https://github.com/getzep/graphiti) and [Neo4j Windows](https://neo4j.com/docs/operations-manual/current/installation/windows/): temporal index behind an adapter; no Zep Cloud requirement.
- [GitHub OAuth/device authorization](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps) and [Google installed-app OAuth](https://developers.google.com/identity/protocols/oauth2/native-app): registered client, minimal scopes, owner authorization, bounded lifecycle.

No Slice 07, Sunday, voice, polished UI or physical power action is authorized by this pass.

## Candidate decision and observed acceptance

Slice 05 **COMPLETE for Windows local-alpha acceptance**. Slice 06 **COMPLETE**.
Gate B **PASS for documented local-alpha acceptance**, following the independent
2026-10-05 review below. [Current machine-readable evidence](evidence/gate-b-final-acceptance-2026-10-05.json)
links the preserved prior implementation and owner acceptance records. Android
acceptance is not inferred. The earlier observations below retain their chronology.

| Capability | Actual laptop observation |
|---|---|
| Machine/Codex | Nested interval bug repaired in disposable Git repo; baseline fails, nine independent cases pass; sole-file diff/hash; failed invocation; actual cancel; restart/recovery without duplicate mutation |
| Files/process/Git | Existing native acceptance rerun; reparse-aware files, allowlists, filtered environment, native Job Objects, output/time bounds, Git commit; interrupted ambiguous mutation BLOCKED |
| PowerShell | Discovered real executable/version, typed UTF-8 write, environment/cwd, timeout and cancellation tests |
| Installed app/UIA | 87 registered records; explicitly allowlisted packaged Notepad; actual broker PID bound independently; observed element input/readback, keyboard/mouse, empty test-tab close; owner window preserved |
| Browser | Fresh isolated Chromium; local form submit confirmed by independent server GET; screenshot and anonymous bounded anchor download; example.com independently checked via HTTPS; real navigation followed by timeout/cancel |
| Owner control | Separate control/Core/Worker processes; control exit and Core termination leave permitted Worker running; unchanged lease/result recovered after natural expiry; pause/resume/cancel/revoke; no duplicate |
| Memory | Canonical SQLite WAL/FTS5; real Qdrant local disk and Graphiti SDK against Neo4j Community; CPU MiniLM embeddings and cross-encoder reranker; both derived indexes destroyed/rebuilt; canonical events preserved |
| Memory reliability | A–R 18 synthetic cases pass; five positive-query top-5 hits 5/5, unsupported claim acceptance 0/6, temporal 3/3, entity error cases 0; exact claim verifier, not universal hallucination proof |
| Policy | Real native Model Router candidate; ambiguous wording blocked; precise ASK rule remains inactive before synthetic owner confirmation; database reopen then actual Worker blocks write, independent absent file |
| Credentials | Actual Credential Manager write/read/rotate/expiry/separate-process reopen/delete; opaque SQLite references; device-flow protocol tests do not prove a private OAuth lifecycle |

## Runtime boundaries

`InteractiveWorker` composes existing leases/Dispatcher/dedup with typed Windows and
Playwright adapters. App discovery never grants launch authority. Browser support is
advertised only after selected-interpreter/Chromium probing. Native `CREATE_NEW`
artifact creation rejects even a dangling Windows symlink; directories are pinned.
Anonymous HTTP anchor downloads enforce a streaming bound; authenticated/blob/JS
downloads are unsupported. All meaningful executor receipts stay **REPORTED**;
independent UIA/HTTP/Git/files/tests determine verification.

Approved interpreters/agents/Git still run as the Windows user. Cwd/path scopes and
Job Objects **are not a sandbox**. UIA and broker app activation can touch an existing
user process; no elevation/UIPI bypass or broker-tree containment is claimed.
Windows pause is before the next subprocess, not arbitrary process suspension.
Local control still shares SQLite and loopback HTTP. Credentials do not isolate the
same host account. Private data must not enter the unauthenticated synthetic Neo4j fixture.

Archive-backed recall is an explicit composition API, with bounded source admission,
RECALLED/INFERRED/UNKNOWN preservation and terminal transient-context cleanup.
General model paraphrase entailment and an autonomous conversational memory product
remain unverified. Consolidation is batch-local, checkpointed atomically, and run by
one runner per relationship; original events remain intact. The pre-manual hardening
patch now fences outdated generations and physical projection loss before retrieval.
Supported BM25/IDF replaces hand-hashed lexical retrieval; FastEmbed is the selected
local ML default. The reproduced Graphiti missing `reference_time` property came from
our null-valued edge field and is corrected without warning suppression. See
[the hardening measurements and limitations](GATE-B-HARDENING.md).

## Historical owner/private acceptance boundary before owner run 234817

At the initial implementation acceptance, no configured registered OAuth client was found. The official GitHub device flow
uses a native vault, transaction nonce, bounded single polls, minimal initial
`user:email` scope, expiry checks and ambiguous-exchange blocking. GitHub OAuth App
device adapter does not implement refresh. GitHub now supports expiring OAuth App
tokens/refresh; this acceptance requires disabling token expiration on the registered
app. Native vault/SQLite updates cannot commit atomically;
durable enrollment/disconnect intents and restart reconciliation now recover known
references. Ambiguous provider exchanges still block rather than replay.
Local disconnect deletes the local credential and explicitly marks remote revocation
pending; actual provider revocation/private identity/read/federation remain unverified.
Do not borrow browser or gh credentials. A gist is unlisted rather than private and
its `gist` scope/write/delete acceptance requires separate approval.

Sunday future assistant role/overlay/attention retreat/widgets/notifications/RemoteInput
and Chief-of-Staff/privacy direction already lives in canonical design docs. No
Samsung/OEM, Sunday, voice, hardware or managed-memory acceptance is claimed.
Older failed Notepad acceptance attempts may leave empty synthetic OSCAR tabs for
manual review; never close the owner window or unrelated document to clean them up.

## Quality observation

The real laptop full suite passed **372 tests in 86.558 seconds**. Ruff and formatting
pass; mypy passes for 48 source files. Required repository files, local Markdown
links, value-silent secret scan and Git diff checks pass. Cross-platform CI and
external links are authoritative at draft PR 12 (historical reference: `https://github.com/amaansyed27/oscar/pull/12`).
Its checks must match the latest branch SHA; local Windows results do not prove Ubuntu.
The initial Ubuntu job caught platform-specific native handle stubs; the adapter now
loads its Windows-only module at the native boundary and keeps the public API typed.
Private OAuth remains unverified regardless of green quality checks.

The pre-manual patch is separately recorded in [the hardening ledger](GATE-B-HARDENING.md)
and its synthetic automated evidence. It does not repeat physical/manual desktop
acceptance, authorize OAuth, merge this PR or change Gate B to PASS.

CI snapshot on implementation commit `449aefc90ca6ae6d85bcb5181c892747d8a46ce6`:
Brain contracts run (historical reference: `https://github.com/amaansyed27/oscar/actions/runs/37190449095`)
passed Windows (372 tests, two optional browser skips) and Ubuntu (372 tests, 23
platform skips), lint/format/types and repository/secret checks. The optional browser
cases passed on the real laptop. External links (historical reference: `https://github.com/amaansyed27/oscar/actions/runs/37190449046`)
and repository contracts (historical reference: `https://github.com/amaansyed27/oscar/actions/runs/37190449068`)
also passed. This records an observed commit; PR checks remain the authority for later commits.


The owner manual attempt on 2026-10-04 failed after the click's independent focus
check and exposed invocation/diagnostic harness defects. It is not a capability
PASS. The [focused repair and failure evidence](GATE-B-HARDENING.md) document the
bounded independent focus wait and safe owner rerun. At that attempt, final manual acceptance was still outstanding; Slice 05 COMPLETE,
Slice 06 PARTIAL and Gate B PARTIAL were the recorded states. Later owner PASS
records below supersede those statuses.

The subsequent owner rerun `.oscar/manual-gate-b-20261004-190338` passed the owned
Notepad sub-phase and cleanup, then failed at the first local browser execution.
Source-checkout direct-file imports were independently reproduced and repaired;
preflight now exercises the real worker launch. See [the focused browser repair](GATE-B-HARDENING.md)
for diagnostics, automated evidence and the pinned-interpreter owner command.
At that failed attempt, overall manual acceptance remained outstanding. The later
owner PASS below supersedes that status. OAuth was unperformed at that point;
the final review below records the subsequent OAuth acceptance and Gate B PASS.


## Owner machine PASS and historical private acceptance preparation

**FINAL PHYSICAL/MANUAL MACHINE ACCEPTANCE PASSED.** The owner completed
`.oscar/manual-gate-b-20261004-200734`, fixture
`99e765885f3b4674bc7a517a4db2523d`: owned Notepad discovery/launch/binding, focus,
text mutation/readback, clear/readback and test-tab cleanup; local isolated Chromium,
independent HTTP state verification, bounded download/screenshot; public Example
Domain and independent HTTPS title/content verification. All three report phases
are VERIFIED. A prior OSCAR fixture window was reported and correctly not mutated.
The original root/file set/hashes are preserved; prior failed attempts remain historical
evidence. See [the owner PASS record](evidence/gate-b-owner-machine-pass-2026-10-04.json).

[The dedicated OAuth/federation harness](GATE-B-OAUTH-ACCEPTANCE.md) was prepared and
tested with synthetic providers/native vault fixtures. At preparation, real OAuth
was NOT AUTHORIZED and real private federation was NOT EXERCISED. Client ID and explicit owner GitHub
interaction are required. No borrowed credentials, client secret, gist scope or write
was used in preparation. At that point: Slice 05 COMPLETE; Slice 06 PARTIAL;
Gate B PARTIAL; Slice 07 NOT STARTED. The final review below supersedes that status.
No deployment, Sunday/Android implementation or PR merge is performed.

## Final owner OAuth acceptance and independent gate review — 2026-10-05

Starting reviewed implementation: `68305308105f3b9424451010d546e118fd5e2506`.
Owner root `.oscar/oauth-gate-b-20261004-234817` completed with
`PRIVATE_READ_LIFECYCLE_AND_FEDERATION_CHECKS_PASSED`. The owner manually authorized
the registered GitHub OAuth App; exact scope **user:email** is independently present
in the enrollment and connection metadata. Real `/user` and bounded page-one
`/user/emails` read contracts passed. Provider facts remain REPORTED.

A new process reopened SQLite/native Credential Manager and repeated both reads,
with the same salted identity digest. Raw private payloads remained transient;
no addresses/tokens/device codes are copied into committed evidence. Database
inspection used separate immutable copies, never opened the original root for
writing. Original file set and SHA256s were rechecked unchanged.

NOW selected current authenticated GitHub state; HISTORY retrieved the controlled
synthetic past `-1` event with its event/memory IDs and RECALLED state. Canonical
history is unchanged and public `python/cpython` source composition passed. This
proves bounded live/private/public composition, not arbitrary conversational recall.
The earlier local filesystem/project/task federation acceptance also remains valid.

Local disconnect deleted the credential and checked absence. This review separately
checked both owned credential/device references absent in native Credential Manager.
Persisted state is `locally_disconnected_provider_revocation_pending`, with remote
revocation **UNKNOWN_OWNER_ACTION_REQUIRED**. No provider revocation is claimed.
This provider flow requires legitimate owner settings/app action for remote revocation;
truthful disconnect semantics satisfy the scoped lifecycle contract. Refresh is not
implemented by this adapter; this run used the non-expiring app configuration.

| Mandatory group | Decision and evidence |
|---|---|
| B1 useful real machine work | ACCEPTED: independently tested Codex mutation, files/Git/PowerShell, owner Notepad/UIA and isolated local/public browser, actual cancellation, blocked ambiguity, no duplicate recovery |
| B2 continuation/owner control | ACCEPTED: separate control/Core/Worker processes, control disconnect and coordinator restart, existing authorization/lease/result recovered, cooperative pause/resume/cancel/revoke |
| B3 canonical memory | ACCEPTED: WAL/FTS5 provenance, real Qdrant/Graphiti/Neo4j retrieval, restart/rebuild, generation fencing, correction/alias/forget tests |
| B4 controller recall reliability | ACCEPTED: mandatory preflight, bounded expansion, evidence-bound claims, unsupported claims UNKNOWN, RECALLED distinct from VERIFIED |
| B5 writer/evaluation | ACCEPTED: scoped source-bound candidates, consolidation preserves events, A–R evaluation and hardening retrieval/temporal/entity/outage regressions |
| B6 Personal Policy | ACCEPTED: real model candidate plus exact trusted-owner confirmation, ambiguity/conflict/expiry blocking, restart and independently observed Worker enforcement; no permission creation |
| B7 private OAuth/lifecycle | ACCEPTED: registered owner device flow, exactly user:email, real read/restart/native-vault/local-delete checks; remote revocation explicitly unknown; conditional write NOT AUTHORIZED, optional |
| B8 live context versus memory | ACCEPTED: previous local file/project/task proof plus real private/public composition, NOW live authority, HISTORY RECALLED, unchanged canonical history |

**Slice 05 COMPLETE · Slice 06 COMPLETE · Gate B PASS** for the documented local-alpha
scope. No mandatory acceptance item remains outstanding. PR 12 stays draft/unmerged
pending owner review. Slice 07 is NOT STARTED. No new OAuth flow, private write,
deployment, Sunday/Android, decision-model evaluation or hardware work was performed.
Earlier failed attempts and original conservative report gate statuses are unchanged.

Non-blocking limitations: trusted-host execution is not a sandbox; cooperative pause;
shared SQLite/loopback control; no independent remote deployment; unauthenticated
synthetic Neo4j fixture; bounded structural claim verification, not arbitrary entailment;
no secure erasure; Android/OEM/voice/Edge, managed-memory services and broader private
connectors remain unverified. Owner may review/revoke GitHub authorization separately.

Final local verification: **427 Windows tests PASS, no skips, 107.321 seconds**.
Focused Gate B/OAuth/federation and quality results are recorded in the current
machine-readable record. Exact-head PR CI is required before merge readiness.
