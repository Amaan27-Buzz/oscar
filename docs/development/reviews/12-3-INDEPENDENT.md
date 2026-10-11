# Slice 12.3 independent software review

Reviewed 2026-10-11 in the isolated desktop-completion worktree. Reviewer changed only this report.

**Final recommendation: ACCEPT bounded Slice 12.3 software closure.** The initial feedback finding is corrected and independently rechecked; the successful completion/discard coverage advisory is also addressed. This is not owner/device, physical voice, real inference or visual/motion acceptance.

## Finding

### Initial P2 — Unknown IPC outcome does not disable text application — RESOLVED

Living derives effective feedback from native `view.feedback` or its local `requestError` when the command port throws. TextTools receives the raw `view`, and its `canApply` checks only `view.feedback`. Therefore a rejected/uncertain Apply promise can leave the existing preview actionable once busy clears, even while Living reports that the outcome must be inspected before resubmission. Core consumed-preview fencing still prevents a repeated consumed application; the defect is the presented recovery affordance, not demonstrated authority bypass.

Pass effective feedback into TextTools and add a thrown-port regression establishing disabled Apply until fresh inspected state/new preview resolves the uncertainty. Do not add an automatic retry.

## Supported contracts

- Dictate/Edit drafts are controlled independently. Opening tools does not start capture. Fresh supported selected/focused context is required for Edit in both UI and Core; foreground identity cannot become editable text.
- Focused previews carry both the captured complete field and the complete replacement. Destination resets on a new preview, offered destinations are checked, expiry disables apply, and consumed previews retire on authoritative application response.
- Explicit start/finish/cancel uses existing Voice Core adapters. Capture and recognition cancellation tokens are separate; generation fencing suppresses late recognition; processing is published before transcription; unknown adapters remain blocked. Permission is rechecked at capture and final transcript boundaries, and recognition is local-only.
- Native content_revision fences obsolete private, context and review replies; local discard clears drafts immediately, remounts legacy Act, masks incoming private content and invalidates native pending reviews. Core marks still-executing discarded tasks hidden and removes their transient payload at terminal transition. Task execution truth is preserved independently of discarded content.
- Runtime/Dispatcher already hold bounded private references and sanitize persisted results. The reviewer examined their interaction with terminal cleanup; no new durable private-result leak was established.
- Parent workspace App now receives admitted/fenced readback through Living, rather than subscribing directly to unfenced state. Registered reference-target capture is explicitly limited to reference bootstrap.

## Independent verification

- `npm test -- --run src/presence/TextTools.test.tsx src/presence/Living.test.tsx src/App.test.tsx src/presence/ResultView.test.tsx`: **32 passed**, exit 0.
- `python -m unittest tests.test_desktop_completion tests.test_desktop -q`: **40 passed**, exit 0, 13.696 seconds.
- Inspected source for TextTools, Living/App handoff, native content revision/preview retirement, Desktop capture/preview/discard, DesktopVoice, Runtime result verification and Dispatcher private-result sanitization.
- Inspected native TextTools receipt: completed=true, failure_type=null, 12 assertions, actual disposable Core tasks empty/actions zero after preview/surface delivery. This supports explicit tools, separated drafts, retreat/reinvoke, absent microphone adapter, preview/expiry and discard at that reference boundary.
- Inspected separate CNG/UIA receipt: native CNG/PSS, registered-field independent readback, cancellation and restart/reconnect are classified separately from simulated transformation and unrun microphone/owner acceptance.
- Opened final preview, expired-preview and unavailable-microphone PNGs at original resolution. The expiry and blocked feedback are visible, the quiet single-leaf composition remains consistent, and scrolling is explicit. The captures do not show the below-fold Before/After/Apply together and do not establish physical insertion or subjective motion quality.

## Final correction recheck

- Living now supplies its effective feedback to TextTools with `view={{...view,feedback}}`. Native feedback and a local thrown-port UNKNOWN both reach the same Apply guard. The new regression rejects an Apply IPC promise, establishes the visible alert and disabled button, and verifies a further click sends no second apply command. No retry was introduced.
- Core discard now preserves hidden transient payloads through EXECUTING, AWAITING_RESULT, RESULT_RECEIVED and VERIFYING. The new integration regression holds a real arithmetic Dispatcher executor, discards concurrently, releases it and confirms the ordinary Runtime completes with independently VERIFIED task state while transient private data is removed and inspection reveals no private value. This resolves the original successful-completion coverage advisory without claiming external application/device acceptance.
- Independent final commands: the same four frontend files pass **33 tests**; desktop/completion Python modules pass **41 tests**, exit 0, 14.022 seconds. Reviewer inspected both added regressions and corresponding implementation changes. No new material source blocker was observed in this focused recheck.

The initial hold is lifted for the authorized stage's bounded software scope. The native 12-assertion TextTools and separate CNG/UIA receipts retain their previously reviewed reference limits; this recheck does not promote them into owner or physical voice acceptance.

Not independently executed: native capture runners, owner GUI/native confirmation, real microphone/STT/inference, OS focus/hit regions, tray behavior, phone/OEM/device acceptance, remote exact-head CI or subjective motion quality.
