# Slice 12.4 independent software review

Reviewed 2026-10-11 in the isolated desktop-completion worktree. Reviewer changed only this report.

**Final recommendation: ACCEPT bounded Slice 12.4 software closure.** The initial cross-mode active-task finding is corrected and independently rechecked. The typed native/Core execution and private-data boundaries remain intact in the inspected changes. This is not owner GUI/device, physical voice, real inference or motion acceptance.

## Finding

### Initial P2 — An active Ask/Edit task does not block a competing Act proposal — RESOLVED

ActionSurface selects a task only when `view.current.mode === 'Act'`, then derives its working guard from that task. An executing Ask/Edit task, or an active task present only in `view.tasks`, leaves the form enabled while work is already active. This contradicts the stage's stated active-task competing-proposal boundary. Core still controls execution; no authorization bypass is claimed.

Derive the displayed active task and disabled proposal state from authoritative current/shared tasks across modes. Add regressions for a non-Act current executing task and a noncurrent active shared task; assert neither can send an Act proposal. Preserve terminal-task inspection without permanently disabling new work.

## Supported contracts

- Existing Act forms remain bounded typed commands. No arbitrary JSON, executable, shell or second action engine was added. Core maps only admitted operations and validates required fields, workspace paths, registered programs/apps and isolated browser origins.
- Current Catalog supplies worker, risk and required scopes; no UI grant is created. Native permission fields are additive, and unavailable/critical capabilities remain excluded by existing Core catalog/policy admission.
- A controlled ActionDraft preserves unfinished local content across leaf retreat and clears with private discard. Mounted capability withdrawal clears private values and does not select a different worker automatically. Explicit capability/operation changes clear the prior fields.
- Proposal returns actual Core task identity; submitted action summary binds to that task and shows exact path/worker. Opening its review does not execute. Existing native signed confirmation remains required, and results retain independent verification status.
- Application context stays explicit and source-backed. Screenshot capture remains visibly unsupported; registered/permitted text/window observation is reused rather than reconstructed from screenshots.

## Independent verification

- `npm test -- --run src/Act.test.tsx src/presence/Living.test.tsx src/App.test.tsx src/presence/TextTools.test.tsx src/presence/ResultView.test.tsx`: **36 passed**, exit 0.
- `python -m unittest tests.test_desktop_completion tests.test_desktop -q`: **41 passed**, exit 0, 13.848 seconds.
- Inspected Act/ActionSurface/Living changes, typed TS/Rust catalog/window additions, and authoritative `desktop_actions.py` validation/form mapping. Existing Desktop catalog and proposal admission continue to recheck current target, capability, grants and policy.
- Inspected native Act receipt: completed=true, failure_type=null, seven assertions; actual disposable file execution/readback, blocked competing Act proposal, clear and withdrawn-worker states are explicitly separated from programmatic trusted progression and unrun GUI owner consent.
- Opened scoped-action, pending-decision and withdrawn-capability PNGs at original resolution. Pending action clearly identifies the reviewed path and worker and states opening review grants nothing. Withdrawn capability shows no eligible executor. The long form is scrollable; risk/scope/Prepare controls are below the inspected scoped-form first viewport, so that image alone does not prove their visible reviewability.
- Inspected the separate isolated-browser receipt: owned local fixture submit/download with independent HTTP server GET and separate example.com HTTPS marker readback. Its `desktop: UNVERIFIED` field correctly prevents borrowing this evidence as desktop GUI acceptance.

No new demonstrated privacy, arbitrary-execution or native-signing bypass was found in this focused review. Native receipts were inspected, not independently rerun, under the reviewer's report-only write scope.

## Final correction recheck

ActionSurface now derives active work from authoritative current and shared tasks across modes, covering EXECUTING, AWAITING_RESULT, RESULT_RECEIVED and VERIFYING. It displays the actual active task through TaskStage and disables preparation. Terminal Act results remain inspectable without permanently blocking new work; planned owner attention remains handled by Living's existing review-first branch.

The added component regression supplies an eligible, fully filled action form with either a current executing Ask or noncurrent verifying Edit. Both show the actual existing task and disable Prepare action. The shared Act handler also checks its disabled prop before sending, so disabled preparation cannot submit through its handler.

Independent final frontend run across ActionSurface/Act/Living/App/TextTools/ResultView: **38 tests passed**, exit 0. Desktop/completion Python recheck: **41 passed**, exit 0, 14.625 seconds. The initial hold is lifted at this stage's bounded software boundary. No native/manual/device or browser evidence classification was expanded by this correction.

Not checked: owner native confirmation, OS focus/hit regions, tray behavior, physical insertion into owner apps, real microphone/inference, phone/OEM/device acceptance, remote exact-head CI or subjective motion quality.
