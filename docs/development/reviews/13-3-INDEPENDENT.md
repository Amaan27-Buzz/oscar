# 13.3 independent activity and consequential-review assessment

Reviewed 2026-10-11 in the Mobile completion worktree. This reviewer changed no
application or test code. **ACCEPT bounded software/reference closure.** No
remaining demonstrated P0/P1 defect in the reviewed paths. Human biometric/PIN,
physical phone/OEM and critical-risk strong confirmation are not accepted here.

## Native evidence first

Inspected `13-3-reference-approval.png` and `13-3-reference-denied-readback.png`
before the final implementation report. They are actual Compose output on API 35
from disposable reference content. The first is the native review dialog capture;
the second is the home readback after a separately signed reference denial.
The task target is `reference-cloud`, not a physically verified Desktop executor.

The review visibly includes consequence, target, permission scope, capability,
complete exact request and serialized plan material. Long scope identifiers wrap
rather than silently truncate. Typography and vertical hierarchy are readable;
the intentionally dense security review preserves material needed for an informed
decision. Back and confirmation remain separate controls. Opening the dialog is
not presented as consent. The post-denial home shows Cancelled, withdraws owner
attention and keeps the shared character identity. The old failure sentence
`No action is confirmed` needs the narrow origin qualification `This phone granted
no consent` when another reference source later cancels the task; this is a P3
copy correction, not an execution-authority defect.

## Security and state review

The earlier P1 omitted-review defect is closed: Android now carries and displays
full `exact_request`, `review` and permission `scope`. The UTF-8 length-framed
display digest binds operation, scope, target, exact request and plan material to
the signed Core claim. Oversized exact material fails closed; it is not shortened
and called exact. Source audience, nonce, generation, expiry and current action
are validated. CoreClient snapshots its session input so callers cannot mutate
the bound audience. The reply surface exposes the actual local reply text only
after matching its signed hash. No signature is fabricated by Android UI tests.

Native confirmation uses the existing legitimate Android handoff. Epoch/current
checks precede signing and Core completion; stale failure callbacks cannot dismiss
a newer review. Disposal cancels the old prompt. Core retains exact descriptor,
scope, policy, signature, replay and expiry authority. Critical capabilities remain
blocked rather than treating ordinary Android confirmation as stronger acceptance.

Activity exposes current actions, independent evidence references, session-scoped
artifact metadata without paths, and reported Worker checkpoints. Initial P2
findings are corrected: ownership requires an active unexpired online lease and
active task; progress must match current lease/action/freshness or is explicitly
labelled Previous checkpoint; changed task generation retires a review even if the
same action remains advertised. Offline executor work now presents UNKNOWN rather
than claiming execution. These changes do not create a second Worker/controller.

The clock correction uses the fresh admitted snapshot and its local receipt to
qualify Core-domain time for challenge parsing, current checks and dialog expiry.
A bounded 250 ms admission tolerance does not extend Core's actual expiry. Local
wall-clock jumps and transport delay can affect advisory presentation; execution
still fails closed against Core's signed deadline. Polling resumes after local
disconnect/reconnection rather than leaving the surface with a one-time snapshot.

## Independent checks and attributed reference results

- Independent fresh JVM recompilation initially passed **14 app + 5 expression
  tests**, zero failures/skips, all 46 Gradle tasks executed.
- After clock correction, independently forced both actual Test tasks to rerun:
  **15 app + 5 expression tests**, zero failures/skips. Cached dependencies were
  reused; both test tasks executed. Exact/multibyte material mutation, audience,
  expiry, action withdrawal, generation and clock-offset cases were inspected.
- Independent `python -m unittest tests.test_mobile -q`: **18 tests PASS**,
  29.102 seconds, zero failures/skips. Signed denial/retry, changed plan, expiry,
  replay, policy, session privacy, display digest and critical refusal exercised.
- Inspected the native scenario source and actual captures. Parent reports its
  serial API 35 scenario passed in 52 seconds: Core planned readback after opening,
  actual deadline/readback followed by explicit Compose test-clock dispatch,
  disabled expired confirmation, task inspection, genuine Android unavailable
  authentication and separately signed reference denial with cancelled readback.
  This reviewer did not launch that connected run; it is not independent execution.

The insecure emulator does not enroll an owner key or produce biometric success.
Reference denial is signed through the isolated reference control service after
Android correctly refuses the unavailable handoff. This proves reference Core
denial/readback, not owner denial through a commissioned phone. Earlier failed
native/clock and emulator receipts remain failures linked to subsequent correction;
they are not silently reclassified. Host resource pressure is not established as
their single cause.

Not checked: human biometrics/PIN, physical phone/OEM, real Desktop interoperability,
voice/audio or owner visual approval. Remaining risk: dense long reviews and
expiry/prompt behaviour still need consolidated real-device accessibility/use.
