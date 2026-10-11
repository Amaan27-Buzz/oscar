# Slice 12.2 independent software review

Reviewed 2026-10-11 against baseline `da8fddae50112c8859b21247d0cbaa617be8667e` and the uncommitted 12.2 candidate. Read-only implementation review; this reviewer changed only this report.

**Final recommendation: ACCEPT bounded Slice 12.2 software closure.** Both initial findings below are corrected and independently rechecked. Native evidence inspection supports the completed reference flow at its declared boundary. No owner/device, real inference, physical voice, remote CI or visual/motion approval is implied.

## Findings

### Initial P1 — A replacement session can read an earlier session's private response — RESOLVED

`oscar/desktop.py:196–202` admits private result presentation based on the originating node, but not the originating session. The new `desktop_task.session_id` correctly scopes follow-up assembly; it does not yet scope direct inspection. This conflicts with the adjacent originating surface session/node privacy comment.

Independent disposable reproduction: create and complete a model Ask with value `private-session-marker`; pair a new session for the same desktop node; inspect the old task. Observed `different_session=True`, `same_node=True`, `private_result_visible=True`. A follow-up from the replacement session correctly omits that context (`prior_context_attached=False`).

Fix the private response/worker-output and derived recall/truncation presentation gate to require the originating session as well as node. Keep shared task metadata and advertised controls available under existing grants. Add a same-node replacement-session regression. Older associations with no session provenance must fail closed for private material.

### Initial P2 — A failed native acceptance run writes a verified receipt — RESOLVED

`scripts/desktop_completion_acceptance.py` writes `classification: REFERENCE_VERIFIED` in its `finally` block regardless of assertion failure. At initial inspection the receipt contained only three checks: draft reversal, editable DOM focus and arithmetic verification. It therefore did not establish the later reading, reported-result, reconnect and blocked-state assertions.

Make receipt outcome reflect completion/failure and record the error without private content. Regenerate the complete native reference sequence and preserve its explicit OS-focus, programmatic-owner-progression and scripted-model limits.

## Supported implementation assessment

- AskComposer keeps input bounded and honors IME composition and Enter/Shift+Enter.
- ResultView offers a bounded excerpt and an explicit reading path; native Reading mode changes the actual window size. It keeps transport/model testimony REPORTED and separately exposes Core truncation and recall source IDs.
- TaskStage renders only provided finite bounded progress and routes cancellation through native/Core review rather than granting cancellation authority itself.
- Same-session follow-up uses existing transient Core task material, labels it untrusted/reported, limits request/result lengths and forces model follow-up into private routing. Discard removes the source transient payload. No separate desktop memory/history store is introduced.
- MemoryExecutor uses existing MemoryFabric retrieval and exact sourced context. Desktop re-retrieves and compares material before presenting RECALLED/INFERRED; forgotten material is withheld as UNKNOWN. Missing recall capability remains blocked rather than invoking model priors.
- Existing native signed review, Core grants, retry budget zero, transient payload/digest, independent task truth and private-provider boundaries are preserved.

## Independent checks

- `npm test -- --run src/presence/ResultView.test.tsx src/presence/Living.test.tsx src/App.test.tsx`: **27 passed**, exit 0.
- `python -m unittest tests.test_desktop_completion tests.test_desktop -q`: **33 passed**, exit 0, 11.284 seconds.
- Additional disposable session-isolation reproduction above: privacy failure confirmed; follow-up session isolation confirmed.
- Source inspection includes new React components, Living routing/focus, typed Rust Reading/TaskView additions, Runtime parameter selection, MemoryExecutor, Desktop assembly/recheck, MemoryFabric exact-claim validation and native acceptance script.

These checks prove their software contracts, not design quality or owner/device acceptance. Initial 12.3–12.6 baseline gaps remain for their authorized stages; they are not silently closed by this review.

## Correction recheck and bounded closure

- Desktop.inspect now requires both originating node and `desktop_task.session_id` before revealing private result/worker output. Truncation metadata requires an actually visible response; recall recheck requires one as well. Missing session provenance fails closed.
- Independently repeated the original disposable reproduction: originating session still receives its completed private response; replacement session receives the same task ID and shared metadata with response/value absent and no private sentinel. The new repository regression covers that boundary too.
- Native acceptance initializes `completed=False`, sets it only after the full flow, records exception type on failure and conditionally emits FAILED rather than REFERENCE_VERIFIED. Final curated receipt has `completed:true`, `failure_type:null`, all nine named assertions, and explicit limitations. Its additional geometry assertion checks response actions remain above the footer.
- Living's duplicate event/reply acknowledgement correction requires nonnull matching epoch, nonolder accepted generation and exact current task identity before accepting the submitted draft. The regression simulates emitted state arriving before the promise reply and verifies fresh composition afterward; unresolved requests retain their draft.
- Inspected final compact, bounded-result and expanded-response PNGs at original resolution. The character stays separate; response status remains REPORTED; the reading area is substantially larger and scrollable; result controls and footer are separated without the reported overlap. This is a bounded still-image assessment, not a new numerical design score or motion-quality approval.
- Independent final regressions: **28 frontend tests passed** across ResultView/Living/App; **34 Python tests passed** across desktop/completion (11.621 seconds); repeated direct privacy assertions passed. No implementation edits by this reviewer.

The original hold is lifted for this stage's bounded software scope. Missing physical/manual/native-OS acceptance and real inference remain declared boundaries; the upcoming 12.3–12.6 requirements remain separate work.

Not independently executed: the final native runner (its source, completed receipt and curated captures were inspected), owner GUI/native MessageBox consent, OS focus/hit regions, tray behavior, real prepared inference, microphone/audio, phone/OEM behavior, remote exact-head CI or subjective motion quality.
