# Slice 12.5 independent software review

Reviewed 2026-10-11 in the isolated desktop-completion worktree. Reviewer changed only this report.

**Final recommendation: ACCEPT bounded Slice 12.5 software closure.** The recall-provenance disclosure finding is corrected and independently rechecked, along with native task-switch invalidation. The inspected Activity/native/Core changes preserve signed authority, private evidence boundaries and honest task state. No owner/device, real inference, physical voice, native OS or motion acceptance is implied.

## Visual/native evidence inspected first

Before reading implementation, opened approval, verified, expired and offline PNGs at original resolution and inspected the native receipt. It reports completed=true and nine assertions; approval material identifies its task/target/capability/reason/consequence/policy, verified task discloses independent arithmetic verification, and offline history expressly grants no control. Expired and offline screenshots scroll before the lower confirmation area, so the captures alone do not prove button disablement; receipt assertions and source/regression evidence provide that boundary.

Initial approval capture showed zero active tasks while current was planned, before the shared poll. The implementation agent independently reported and corrected this: Activity now includes current, deduplicated against shared tasks. New captures were being regenerated at review time. The current-first merge is consistent with native Bridge.refresh: stale snapshots preserve newer current; fresh snapshots update current before emitting the View. Introducing independent frontend task truth would be unnecessary.

## Finding

### Initial P2 — Inspecting a recalled result drops recall source provenance — RESOLVED

Activity displays the response status but its evidence disclosure includes execution evidence IDs/metadata/artifacts only. `source_event_ids` and the historical-evidence/current-facts warning from ResultView are absent. A user following Inspect result therefore loses canonical recall provenance precisely on the detailed inspection surface. Execution evidence is not interchangeable with canonical historical source events.

Render source event identifiers and a historical freshness warning for recalled/inferred historical material in Activity; preserve the Core's RECALLED/INFERRED/UNKNOWN status without promotion. Add a sourced recall disclosure regression. No new archive access or retention grant is required.

## Supported contracts

- Activity uses one admitted Living view/run and no second subscription/state store. Opening Activity or selecting a task does not approve, deny, cancel or retry it.
- Review identifies exact task, operation, target, capability and material. Controls require current advertised action, online availability and unexpired review. Native confirmation/signing remains outside the WebView; dismissing creates no execution grant.
- Native Inspect invalidates cached pending reviews and clears current review before fetching another task. Starting Review invalidates previous pending material. Existing content revision rejects stale switched replies; Core signatures recheck task/target/digest/grant/state/expiry. No task-switch approval bypass was found.
- Completed/partial/failed states remain distinct from active work. Offline metadata remains inspectable without granting control; reconnect exposes fresh inspection/review rather than auto execution.
- Core exposes allowlisted verification metadata, excluding detail/private locations. Private artifacts require originating node/session and undiscarded transient material; only ID/kind/status/hash is projected. Missing/discarded private plans withdraw approve while retaining eligible denial/cancellation.
- Evidence transport testimony, independent verification and artifact hashes remain distinct; identifiers do not grant file access.

## Independent verification

- `npm test -- --run src/presence/Activity.test.tsx src/presence/Living.test.tsx src/presence/ActionSurface.test.tsx src/Act.test.tsx src/presence/TextTools.test.tsx src/presence/ResultView.test.tsx`: **35 passed**, exit 0 (before the newly added current-list regression).
- `python -m unittest tests.test_desktop_completion tests.test_desktop tests.test_mobile -q`: **56 passed**, exit 0, 20.705 seconds.
- Source review covers Activity semantics/expiry/focus, Living single view, TS/Rust task evidence fields, native review invalidation, Desktop evidence/artifact projection and private-plan approval withdrawal.
- Native completed nine-assertion receipt was inspected, not independently rerun. Source conditional completion classification is correct. Trusted fixture execution remains explicitly separate from owner GUI/native confirmation and OS foreground acceptance.

## Final correction recheck

- Activity now shows canonical `source_event_ids` separately from execution evidence and includes the earlier-retained/current-facts warning plus explicit inference qualification. Added RECALLED and INFERRED regressions retain the exact status, canonical source identifier and temporal uncertainty. No archive access or retention permission was added.
- Native pending-review invalidation now has a direct regression: seed a fresh pending review, inspect another task against unavailable readback, assert view review and native pending map are cleared, and make owner-dialog invocation panic. Independent `cargo test stale_reviews_and_offline_discard_fail_closed -- --nocapture` passed **1 test**, exit 0; 11 unrelated tests filtered. This also addresses the original advisory.
- Independent final frontend run across Activity/Living/ActionSurface/Act/TextTools/ResultView passed **37 tests**, exit 0. Earlier independent Desktop/completion/Mobile run passed **56 tests**. No further backend change requiring that suite to repeat was identified in this correction.
- Inspected regenerated approval PNG at original resolution: Active and waiting now shows 1 and the exact planned task. Final native receipt remains completed=true with all nine assertions and declared reference limits. It was inspected, not independently rerun.

The initial hold is lifted for this bounded software stage. No new material authority/privacy blocker was found in the focused recheck; final owner/native-OS/physical quality boundaries remain open.

Not checked: owner native confirmation, OS focus/hit regions, tray behavior, physical insertion into owner apps, real microphone/inference, phone/OEM/device acceptance, remote exact-head CI or subjective motion quality.
