# Desktop completion — root causes and regression proof

This is Group 1 software/reference evidence, not owner or production acceptance.
Historical 12.1 recovery reports remain unchanged. Core/Action Ledger, native
signing and the shared expression engine remain authoritative.

| Root cause / effect | Correction | Regression evidence |
|---|---|---|
| Memory plan omitted query; repeated Ask lacked sourced working context | Read-only existing MemoryFabric executor, bounded same-session transient continuity, current provenance recheck | `tests/test_desktop_completion.py`: recall/forget, follow-up private routing, discard/restart, foreign-session readback |
| Emitted reply was consumed before returned acknowledgement; draft stayed submitted | Match exact task/epoch before clearing only acknowledged draft | Living test and native Ask fresh-composer assertion |
| Reader actions could overlap footer | Flex/min-height response region, bounded excerpt and explicit larger reader | Native reading/footer geometry; historical failure capture preserved |
| Dictate/Edit shared private draft state and weak destination preview | Controlled separate drafts, complete focused append/replacement, source/destination/expiry guards | TextTools tests; actual native text12 and registered WPF independent readback |
| Late recognition/IPC/content replies could restore discarded material | Voice tokens/generations, native content revision and privacy suppression; active-task private cleanup after terminal readback | Core cancellation/discard concurrency tests and Rust late-response tests |
| UNKNOWN Apply was effectively retryable | Pass effective feedback into Apply guard; consumed preview retired | Thrown-port Living regression; Core expected-value/consumption boundaries |
| Act guarded only current Act work | Guard authoritative executing/waiting/result/verifying work across modes/current/shared list | Current Ask/noncurrent Edit component regressions |
| Withdrawn capability could select another worker with old private form | Clear capability/resource/text; no implicit executor switch | Act withdrawal regression and native withdrawn-catalog assertion |
| Embedded Activity had a competing subscription/state | Single admitted parent view; controlled progressive task/decision surface | Activity/component and native task-switch/readback checks |
| Immediate current task absent from polled list showed Active0 | Deduplicate fresh current into shared list under native timestamp fence | Activity immediate-current regression and corrected native capture |
| Activity lost recalled source IDs and temporal caveat | Preserve canonical recall sources and historical/inference warning | RECALLED/INFERRED inspector tests |
| Cached review remained usable after task switch/readback failure | Invalidate native pending reviews before Inspect; exact current action/expiry gate | Rust fresh-review + failed Inspect regression; native expiry/task-change/disconnect9 |
| Exact review silently sliced valid private parameters | Full JSON up to24,000 UTF-8 bytes; reject above bound before creating challenge; matching native text bound | Roundtrip8192 context+4096 instruction; oversized multibyte creates no challenge; independent reproduction |
| Long Worker output used short Result value for excerpt flag | Compute truncation from actually selected displayed source |9000-character Worker output + short result shows8192 and explicit flag |
| New owner session/key had ambiguous access to prior private review | Private response/review/approval bound to originating session/node; preserve metadata and signed denial/cancel without private input | Legitimately enrolled replacement cannot approve/read prompt; denial review is empty |

No automatic retry or fake success was added. An overbound review is a visible
rejection requiring a shorter request/context, never an incomplete signed review.
An uncertain local IPC warning clears only after explicit task inspection;
genuine Core feedback remains governed by admitted readback. UI access itself
grants no permission. Opening/dismissing approvals creates no execution.

Validation mistakes are retained separately: initial unittest discovery omitted
`-t .` and failed relative imports; corrected canonical invocation passes. A
production-protocol binary correctly rejected development URL IPC; rebuilt with
existing development features, without broadening security. Whole-repo Ruff also
finds historical expression capture-script formatting outside the configured
`oscar tests scripts` gate; those unrelated scripts were not rewritten.

Native reference runners use disposable authenticated Core, registered WPF/UIA,
temporary files and an isolated Chromium service. Trusted scripted task progression
and CNG/PSS reference signatures do not establish human consent, real microphone,
provider inference, compositor smoothness, physical DPI or owner-machine quality.
