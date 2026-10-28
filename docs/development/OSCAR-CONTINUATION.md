# OSCAR continuation guide

This is the entry point for a fresh ChatGPT web/Work development conversation
connected to `Amaan27-Buzz/oscar`. The oversized Codex session is closed. This
closeout preserves unfinished work; it is not software completion or release.

## Establish current truth

1. Read [session state](OSCAR-SESSION-STATE.md), [capability ledger](OSCAR-CAPABILITY-LEDGER.json)
   and [publication readiness](../../PUBLICATION-READINESS.md).
2. Inspect the actual branch, HEAD, tree, remote refs and PR #9 before editing.
   Use `codex/software-completion`; do not restart from main and lose the unmerged
   D2 dependency. A GitHub connection that can read files is not an execution
   environment: use a Work checkout for implementation/tests; report unavailable
   native tooling rather than inventing results.
3. Read `AGENTS.md`, `ENGINEERING.md`, `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`,
   `docs/DELIVERY-PLAN.md`, `docs/SLICE-NUMBERING.md`, `docs/ROADMAP.md`,
   `docs/BUILD-GATES.md`, `docs/EPISTEMIC-INTEGRITY.md` and the relevant domain docs.
   See [historical completion ledger](OSCAR-FULL-SOFTWARE-COMPLETION.md),
   [62-scenario acceptance](SOFTWARE-INTEGRATED-ACCEPTANCE.md) and preserved
   [engineering handoff](SOFTWARE-COMPLETION-HANDOFF.md).
4. New instructions from the owner determine the next task. This closeout itself
   authorizes no new features, release, merge, visibility change or commissioning.

## Product vision

OSCAR is one persistent multimodal personal intelligence: a continuing relationship
that remembers with provenance, understands current context, reasons, acts through
available software/devices, delegates, learns evaluated procedures and helps
coordinate the owner's day. Voice and text share history and tasks. Desktop and
Android embody the same OSCAR; the user should not have to manage separate chats,
manually spawn every Worker or choose every internal tool. Preserve the approved
Quietly Alive + Playful Precision UI and canonical `assets/brand/oscar-orb.svg`.

The goal remains complete nondeferred Groups 4-6 software, not another foundation
handoff or a handful of successful scripted examples. Group7 home-server and
Group8 physical Edge/physical Slice18 are explicitly deferred. Real accounts,
host provisioning, physical phone/audio and privileged activation need separate
owner consent; their absence does not excuse unfinished software. Do not add
new delivery groups or rename the canonical slices 00-20.

## Architecture and invariants

One existing Python `Harness` composes Controller (`oscar/jev.py`), Runtime,
Executive, Grid, Model Router, Personal Policy, canonical SQLite WAL/FTS5 Event
Archive/Memory Fabric and World Model. Qdrant and Graphiti/Neo4j are replaceable,
rebuildable derived indexes. Current state belongs to World Model; recalled
history is not automatically current truth. Context-dependent requests require
Controller memory preflight and provenance-bound retrieval before answering.

Tauri/Rust/React Desktop, Kotlin/Java/Compose Android and outbound Windows Workers
connect to the same authenticated Core. Clients own no second canonical archive,
scheduler or policy authority. Persistent Cloud Core packaging exists; Oracle is
not commissioned. Ordinary desktops are optional executors, not permanent hosts.
Do not replace this infrastructure with a required external agent framework.

Controller decides action/evidence class; Capability Fabric chooses executor;
Model Router chooses reasoning provider/model. These remain separate decisions.
Signed owner authority, scopes, current session/account generations, policy,
leases, expiry and revocation are rechecked before dispatch and at the effect.
Ask/Secure/Full and Worker autonomy do not imply perception or retention rights.
Full Access needs genuine signed standing owner delegation and permits no OSCAR
per-action prompt inside its grant, while OS/provider mandates and deterministic
hardware safety still apply. Recognition/Voice Match is not authorization.

Tools, web pages, documents, remembered material and Worker/model reports are
untrusted data. They cannot expand permission, become instructions or promote
reported results into verified facts. Independent authoritative readback must
match the owner's objective. Unknown effects are fenced against automatic replay.
Keep proposed/pending/running/reported/verifying/verified/partial/blocked/failed/
unknown/cancelled states distinct. No fake connected state, telemetry or success.

## What already exists

The branch includes authenticated enrollment/TLS Grid and no-replay journals;
scoped files/PowerShell/Git/UIA/browser control; Android native execution and
Keystore owner control; multi-account identity/vault/OAuth; reviewed MCP lifecycle;
signed authority; durable Workers/schedules; private planning observations and
bounded model correction; sourced recall/correction/forgetting; voice/Sentry/day
context; typed shared Presence/AIE; selected provider actions and independent
resource verification. Existing native app designs must be preserved.

Evidence includes real installed local-model inference, real loopback provider
HTTP with synthetic accounts, native Windows fixtures, disposable Android
emulators, separate Core/Worker processes and short restart soaks. These are not
all real-provider, physical-owner or hosted production acceptance. Read each
source-qualified receipt before making a claim.

## Highest-impact unfinished work

**First: owner-goal correctness in general planning.** Two named account aliases
currently constrain a union of accounts, not source/destination roles. The latest
installed Qwen Ask/Full cross-service campaign passed 0/2 owner objectives. One
wrong-service creation had verified substeps yet did not create the requested
Microsoft resource. Guarding account membership or schema shape alone is
insufficient. Bind requested operation/provider/account/list/resource/field roles
before effects, preserve private observed values and independently verify the
original objective. Ambiguity must remain explicit. Do not hide failure by
substituting a canned command grammar or weakening the acceptance harness.

Read `planning_contract.exact_account_aliases`,
`PlannerConnectors.goal_accounts/check_goal_accounts`, their callers in `Harness`
and `PlanningAuthoring`, and existing private expectations/readback. Reuse those
boundaries. Add adversarial role-swap tests, then rerun the real local-model
synthetic-provider campaign under signed Ask and synthetic Full. Do not chase
passes with repeated prompt-only trials or treat model-chosen steps as the goal.

Workers must be created/delegated autonomously when an objective benefits from
specialist execution: Core owns decomposition, dependency graph, scope, progress,
leases, cancellation, recovery, audit and independent verification. Bounded
phone/model-to-remote coding/terminal/file handoffs already exist. General
reliable delegation, cross-app semantics and useful persistent monitoring remain
partial. Do not ask the owner to manually orchestrate the internals.

Other active work: general image-grounded computer use; useful service-specific
workflows rather than manifests alone; MCP dynamic registration/automatic resource
refresh/challenges; authenticated Blob/cross-origin downloads; Microsoft sent-copy
verification and calendar concurrency; richer Chief-of-Staff priorities,
flexibility and coordination; current native accessibility/text scaling/screen
reader acceptance; foreground root cause; broader sustained operational testing.
Only approved hardware is deferred. Unsupported software remains NOT_RUN/PARTIAL,
not DEFERRED. Formal Gate C/D stay partial and Gate E is not passed.

## Capability ledger workflow

The JSON contains 21 canonical slice records, Groups4-6, subsystem/service
capabilities, stable requirement IDs and the 62 scenario IDs. Each capability has
source references, independent implementation/integration/testing/CI/live states,
acceptance criteria, evidence, commands, dependencies, blockers, owner action and
next action. Requirements reference their responsible capability; use that
record for execution dependencies and test scope. Some requirement clauses are
also represented in multiple canonical sources; this is traceability, not
multiple completed features. NOT_RUN at a criterion means it has not been
individually certified, even if broader parent tests pass.

Update an existing ID when its requirement persists; add a new ID only for a new
requirement. Keep dated receipts and source hashes. Never promote an entire
capability because one narrow test passes. Add specific failing cases and exact
readback conditions before claiming completion. Refresh coverage counts when
adding/removing criteria and validate all references. Historical GateA/B local
acceptance and approved UI do not imply present whole-product acceptance.

## Testing and security

Use focused behavioral tests while developing and full regressions at meaningful
integration checkpoints. The last full Python run has 1,400 passes, ten skips and
one native foreground failure; the later undated parser has 127 focused passes.
Do not rerun the whole suite for this documentation-only closeout or suppress the
foreground guard to get green. Linux/headless Work environments cannot establish
Windows UIA, CNG/DPAPI, rendered native, Android OEM or physical audio acceptance.

Use synthetic identities and run-owned fixtures. Never access the physical phone,
real mic/camera, owner accounts, public deployment, billing or privileged owner
activation without explicit consent. Native Windows tests create temporary visible
fixture windows. Only explicitly identified disposable Android emulators may be
used. Do not publish logs, tokens, browser profiles, conversation archives, local
recordings or model caches. Local trusted MCP stdio is not an OS sandbox.

Preserve main and draft D2 PR #9. Never force-push/rewrite history or merge without
separate authorization. The owner changed repository visibility to PUBLIC and
explicitly requested the checked branch push during closeout. The publication
report still records incomplete licensing, asset-rights and privacy clearance.

## End every future conversation with durable context

Commit cohesive authorized work, validate the ledger and repository links, and
update session state with the actual branch/source HEAD, changed capabilities,
passing/failing/skipped checks, exact reproduction commands, blockers and one
next action. Reference immutable receipts rather than copying huge raw logs.
State the exact resulting remote/local SHA in the conversation handoff; a file
cannot embed the hash of its own containing commit. Confirm remote equality after
any authorized push. Do not claim CI until the exact SHA has matching receipts.
Keep all prior evidence and reconcile superseded statements in a current note.
