# Root causes and regression evidence

## 1. Silent blocked requests

The old Core no-task `blocked` result populated a generic message but no task.
The expression adapter saw an online, idle Core; the presence composition did not
render that message. Polling then replaced transient presentation text. Native
command errors also failed to increment the expression generation unless they
were connectivity errors, so valid error feedback could be rejected as stale.

The fix preserves typed request feedback independently of task state, increments
freshness for every admitted failure, and retains feedback across polling/window
transitions. Desktop capability filtering now explains denial separately from
absence/ambiguity; authorization decisions are unchanged. HTTP 403 permission
responses are distinguished from malformed/conflicting request rejection. Bound,
credential-filtered response handling remains native.

| Failure | Presented behavior | Regression evidence |
|---|---|---|
| Capability absent/ambiguous | Specific blocker; nothing executed; Check availability / Edit request | Python proposal test; Rust no-task feedback; React feedback tests; native blocked screenshot/log with zero tasks/actions |
| Permission/Personal Policy denied | Specific denial; Inspect Activity / Edit request; no blind retry | Python policy test; Rust HTTP 403 distinction; React denied fixture; native denied capture |
| Other HTTP rejection | Core rejection stays distinct; inspection | Rust HTTP rejection test; native typed feedback |
| Timeout/server error/IPC uncertainty | Outcome UNKNOWN; inspect before retry; no automatic resubmission | Rust timeout/503 mapping and generation test; React IPC failure regression |
| Offline/readback unavailable | Withdraw current capabilities, rotate epoch, disable new requests | Native Core stop/restart; existing fenced voice/disconnect regression |

The old silent blocker was independently reproduced in the original native app:
[before](evidence/before-blocked.png) versus [corrected](evidence/after-blocked.png).
The original reinvocation warning was **not** reproduced in twelve new baseline
cycles ([receipt](evidence/baseline-cycles.json)); its preserved historical native
capture and deterministic sequencing regression establish the reported failure.

## 2. Stale window warning

An emitted native snapshot could be admitted before the equal command reply.
`run()` interpreted expression-fence rejection of that duplicate as failed window
confirmation. Native reinvocation while still in interaction mode also needed a
revision signal to cancel a pending retreat; a late rejected resize could obscure
the newer interaction.

Window revision and intent sequence now identify actual native changes. Equal
acknowledgements confirm the already-admitted epoch/generation/window. Newer
invocation cancels retreat and ignores obsolete presentation rejections. Genuine
resize errors stay visible until native recovery; Core denial remains visible.
React tests cover duplicate event/reply, delayed rejection, same-mode reinvocation,
draft/focus preservation and actual recovery. The final native run completed ten
mixed 40/240 ms cycles without the obsolete warning.

## 3. Approval and stale readback

Owner waiting arbitration selected subdued delivery, reducing attention before
opening. Generic task descriptions could obscure the locally submitted request.
Native polling could mutate current task before checking snapshot freshness and
leave cached review material after completion.

Owner waiting now selects shared attentive delivery; compact yellow attention is
readable. Submitted text is labelled and bound to the exact returned task, with
Core description used otherwise. Review opens the exact authoritative task route;
opening/retreat never sends `confirm`. Freshness now precedes mutation, and actual
actions/expiry retire stale reviews. React exact-route/no-confirm and task-binding
regressions plus Rust reordered-snapshot/completion regression cover these paths.
Native captures show attention, exact review and verified state after reference
progression; this does not prove human approval signing/dialog interaction.

The fresh review found an additional handoff defect: correct review data was
rendered below generic context/Ask in the existing workspace. An opt-in
`focusReview` prop, used only by Living's workspace, now focuses/scrolls the actual
approval section once per review id. The App regression proves focus without a
decision; four additional native assertions and the
[corrected destination](evidence/corrected-review-route.png) establish visible
details/exact material without confirming. The original first-viewport capture
and frozen review scores are preserved.

## 4. Weight and resting behavior

Explicit resting/curious delivery was overwritten by shared attentive arbitration.
The existing weighted engagement phrase was not exercised by the live presence.
The fix retains delivery semantics in both platform implementations and admits one
existing accent only for fresh executing transitions. Expression Lab tests and
regenerated cross-language reference traces cover quiet/owner poses. Native work
and interruption recordings show the actual shared renderer and Core transitions.
No idle animation loop or synthetic operational work was introduced.

## Additional failure found during native verification

Health/readback timeout errors did not always begin with the connectivity marker
used by `Bridge.fail`, allowing the link to remain online after lost readback.
`refresh()` now classifies any snapshot failure as Core unavailable. Native server
stop and genuine restoration pass, retaining a prior failed task. The initial
fixture also needed to re-advertise capabilities after Grid disconnect, and the
pin assertion needed to await native acknowledgement; those were test-harness
defects, not product fixes. Final receipts supersede the failed development run.
