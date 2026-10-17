# Executive runtime — Group 3 software candidate

The Executive coordinates the existing Controller, Runtime, Grid, Dispatcher,
Personal Policy, Memory Fabric and independent verifier. It owns commitments and
schedules; canonical Tasks/Actions/Results/Evidence remain the execution truth.
It does not install a scheduler service or introduce another agent framework.

The normal `Harness` starts bounded World and Executive lifecycle services.
It also owns independent internal-session maintenance: credential expiry/rotation
does not wait for a long-running Executive executor. Credentials last at most one
hour and rotate while valid within the final 15 minutes, under a seven-day maximum
enrollment. Old tokens can drain only leases active at rotation, no later than
their original expiry. The current handle retains its session identity so real
leases, nonce fences and canonical task/action deduplication remain unchanged.
No credential enters Worker records or evidence. Revocation remains authoritative.
Normal trusted-local restart creates a new scoped enrollment and invalidates the
previous one. Expired/revoked managed enrollment requires explicit
`serve --reenroll-execution`; a revoked node cannot be repaired by this flag.
Long sleep/downtime can therefore require renewed local authorization.

`python -m oscar serve --seconds 60` keeps this laptop-local Core available;
shutdown closes its background services and canonical archive. Future schedules
persist and resume when this Core runs again. A sleeping/offline laptop does not
execute work. The local executor's historical ID `reference-cloud` is not a cloud
deployment claim.

## Runnable local verification

```powershell
python -m unittest tests.test_group03_runtime tests.test_executive -v
python -m oscar executive
python -m oscar --state .oscar/group03-local/core.sqlite --workspace .oscar/group03-local/files serve --seconds 60
```

The tests create disposable exact files and verified arithmetic, exercise actual
SQLite and authenticated loopback HTTP, and restart a separate Core process.
The phone enrollment and model planner output are explicitly reference fixtures;
no real microphone, environmental feed, owner account or device is implied.

## Trusted owner commands

Use `python -m oscar executive --config selected-command.json` with a deliberately
selected UTF-8 file. No secrets belong in it. Readback is available to separately
granted Desktop/Android `executive:read` surfaces; native creation/editing remains
unavailable until it has a signed review integration. Configuration is never an
authorization grant. Existing native exact-action signatures are unchanged.

Register a scoped Worker:

```json
{"operation":"worker","name":"Local calculations","capabilities":[["reference-cloud","math.add"]],"grants":["math"]}
```

Use the returned Worker ID to create an unapproved proposal:

```json
{"operation":"decompose","worker_id":"RETURNED_WORKER_ID","goal":"2 + 2 then 3 + 3","interval_seconds":60,"max_runs":3}
```

Review the complete returned steps, scope, schedule and `review_digest`; activate
that exact proposal with `accept`, supplying `goal_id` and `review_digest`.
`propose` also accepts an explicit topologically ordered list of typed steps:
`id`, `intent`, `depends_on`, `node_id`, `capability_id`. Every step must fit the
Worker's actual pinned capability contract and independent current permissions.
Priority, deadline, dependencies and one live reservation per Worker determine
admission; independent Workers retain failure isolation.

The arithmetic decomposer is deterministic. General model-assisted planning uses
`draft_plan`: it proposes a bounded call through the existing model capability
and Router. That planning call itself needs exact owner acceptance and a real
available provider. `propose_from_result` treats its result as **REPORTED**,
validates the typed graph and scope, records the source task, and requires another
owner review before any proposed step executes. A model's success message never
verifies its plan or the user's objective. Unavailable models remain unavailable.

`pause` stops future admission; already admitted work retains its current scoped
authority. `resume` re-enables future admission. `cancel` stops the commitment and
requests cancellation of its canonical tasks. `revoke_worker` invalidates that
Worker and cancels its commitments, preserving unrelated executor sessions.

Personal Policy ASK still needs exact next-attempt confirmation. `review_task`
returns a `digest`; submit it as `review_digest` to `confirm_task`. Confirmation
expires after ten minutes and binds the task generation, plan and policy. DENY,
changed policies, revoked scopes and capability withdrawal remain authoritative.
This does not implement Secure or standing Full Access delegation.

## Durability, current context and learning

Task creation and occurrence admission commit atomically with a stable key.
Concurrent runners and restarts reuse the same Task/Action/dedup identity.
Unavailable work waits without accumulating repeated ledger transitions; genuine
executor return can recover an unstarted task. `retry` reclaims the same task
within its budget. Started-but-ambiguous mutations stay blocked for inspection;
neither retry nor replan creates an automatic replacement mutation.

`replan` produces a new exact review. Acceptance supersedes only undispatched
prior work; it refuses to replace dispatched/ambiguous work. No forecast changes
an accepted commitment autonomously.

Optional `conditions` contain exact `entity_id`, `key`, `equals` predicates.
They require separate Worker `world:read`, current policy and non-simulated,
nonconflicting, sufficiently confident World observations. Unknown, stale, offline
or mismatching context defers admission. Pointer identity, source epoch,
freshness, connection and permission are rechecked during execution. A changed
context snapshot stops work at the next cooperative check. Focus/travel/weather
can constrain work only when a genuine authorized adapter supplies those facts;
none is invented from model priors or historical memory. The read-only `brief`
reports real commitments, verified runs and tasks needing attention. It does not
send an interruption; Sentry delivery requires its own authorization.

`learn` requires a completed exact commitment, independently verified source tasks
and a separate `retain_authorized: true` grant plus current retention policy.
It appends a **REPORTED workflow candidate** to the canonical Event Archive,
retained for at most seven days. Derived records contain canonical event refs.
`reuse` creates a fresh unapproved proposal under current Worker scope.
`evaluate_workflow` requires separate retention and a newly owner-reviewed,
independently verified replay. Its VERIFIED claim is limited to that exact local
replay; it grants no general reliability, new policy or autonomous authority.
Expiry/forget invalidates reuse. `rebuild_workflows` reconstructs the derived
index and evaluation refs from canonical events and real task evidence.

## Bounds and acceptance limits

At most 32 Workers, 64 commitments, 16 steps per DAG, 100 scheduled occurrences
per commitment and four dispatched steps per tick. Fixed UTC intervals and
one-time times are supported; missed intervals are skipped rather than replayed
as an unbounded catch-up queue. Deadlines are checked at dispatch and cooperative
execution checkpoints. Worker/task leases fence stale ownership.

The runner polls once per second. Native Presence leases last at most 30 seconds.
Presence publication generations are reserved in blocks of 1,024 to fence crash
replay. Read-only polls advance the publication generation and freshness without
changing the transition ID or persisted state generation. A meaningful state
change writes immediately; unchanged polls write only to reserve the next block.
Restart skips unused publication numbers and fences the retired publisher. The
existing Expression version 1 contract and renderers continue to admit refreshes.

The optional Android overlay polls every five seconds and rechecks its local
permissions, lock and pairing after acquisition. Cancellation is cooperative;
an indivisible external action cannot be undone. Shutdown lets admitted work
finish for up to ten seconds, then requests cancellation and waits again; an
executor that still cannot stop is reported, not silently detached as successful.

The accepted visual design and canonical Orb are preserved. Native build/JVM/
frontend tests do not establish owner, OEM, audio, physical Edge, Play distribution
or production acceptance. Gate C and Gate D remain PARTIAL until their separate
mandatory live/owner acceptance is recorded. Group 4 is not started.
