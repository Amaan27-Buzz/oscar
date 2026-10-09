# Desktop consumes Expression — local integration candidate, 2026-10-09

Status: **LOCALLY VALIDATED INTEGRATION CANDIDATE**. This prepares Slice 12;
it does not close either foundation PR or approve a Desktop visual design.
Gate C remains PARTIAL. Owner/device acceptance and exact-head remote CI remain separate.

## 1. Verified local Git state

The original checkout remains on `design/slice-11-expression`, at
`495c3324aabcd85b58438f3abb01500f37ee9baa`. Its tracked tree was clean. Untracked
`.serena/` files and four generated Desktop schema files were preserved.
Local `main` and `work` both remain at `92a11aa05083f1983186976ba64bd30aa9f1f2a0`.
Cached `origin/main` and `origin/work` both point to
`45bb1459f61308291fec6e4e5885b6c77b707478`; the local branches are 61 commits behind.

Local Desktop branch: `546310f`, two commits behind its cached remote ref.
Cached Desktop head: `e334c858195091c21cee5aa35b308b5933cc44bd`.
Local/cached Expression head: `495c3324aabcd85b58438f3abb01500f37ee9baa`.
Neither foundation branch has commits absent from its cached remote tracking ref.
This comparison cannot establish whether GitHub currently holds those refs.
Both supplied dependency commits and the accepted baseline are present as local objects.

## 2. Remote GitHub access

`git ls-remote origin` for the four named branches and `gh pr view` for #16/#17
all failed with HTTP 403, account suspended. No alternate account/transport,
restriction bypass, push, PR update, merge, tag or CI run was attempted.
Current remote heads, PR states, mergeability and check results are **UNKNOWN**.
Historical billing-blocked records remain historical, not current CI success.

## 3. Reconciliation

Created from the verified Expression commit and merged the verified Desktop commit,
preserving both parent histories. Merge commit: `f8e9ed6`.
The accepted cached `origin/work` baseline is an ancestor of this merge.
There were no code conflicts. Eight documentation conflicts occurred in README,
CHANGELOG, AGENT-CONTEXT, ARCHITECTURE, DECISIONS, PRODUCT, ROADMAP and SURFACES.
Both foundation descriptions were retained; the newer canonical roadmap won over
duplicate obsolete Slice 10/future sequencing. Dated continuation guidance is historical.
Evidence files and original artwork were neither rewritten nor deleted.

## 4. Isolated candidate

Branch: `codex/desktop-expression-integration`.
Worktree: `D:/TheDawnlightGroup/DawnlightLabs/oscar-desktop-integration`.
Only this worktree contains the adapter changes. Original branches and checkout
remain untouched. The local merge does not merge GitHub PR #16 or #17.

## 5. Desktop runtime audit

The existing Tauri 2/Rust shell owns native credentials, CNG signing, typed IPC,
tray, global invocation, window lifecycle and authenticated loopback transport.
React remains presentation; Python Core/Controller/Runtime/Grid remain authoritative.
The existing bridge polls at two-second intervals. Task states, scoped approvals,
explicit context, UIA independent readback and degraded states remain intact.
No Core authority, Worker, policy, transport grant or microphone behavior changed.

Runtime corrections here: readback revisions and connection epochs; independent
snapshot/current-task/voice observation times; delayed voice-response fencing;
clear active voice on connection loss/reconnect; inspect active speech if an actual
publisher supplies it. Cached window commands and `ready` do not renew observation.
Native snapshots older than the last snapshot are ignored. Reconnect retains mute.

## 6. Expression compatibility

Uses the local `@oscar/expression` package and `ExpressionPresence`, with React
deduplication. Core, schema, JSON motion, React renderer and native Compose library
are byte-for-byte unchanged from the Expression dependency. V3 trajectories,
asymmetric marks, gaze, opening eye, performed-pose transitions, interruption,
priority and reduced motion are retained. State-only input does not invent a
phrase/engagement accent; broader authored trajectories remain available only
behind the existing validated explicit-accent contract.

Canonical Orb SHA-256 remains
`728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.

## 7. New adapter

`desktop/src/expression.ts` selects bounded presentation fields from trusted native
readback. `DesktopExpression.tsx` admits events into the shared controller;
App uses it in the existing Orb slot. No layout redesign or dependency on A/B/C.
Build script builds the shared ESM package before the Desktop bundle.
No context text, task IDs/descriptions, results, approval material or credentials
are serialized into expression events. No expression result mutates Core state.

## 8. Actual versus synthetic mappings

| Available readback | Expression | Evidence in this run |
|---|---|---|
| Fresh connected Core, no active work | attentive | Actual native disposable Core |
| executing | executing | Adapter unit tests / labelled React fixture |
| verifying | verifying | Adapter unit tests |
| result_received | processing | Adapter unit tests; no verification promotion |
| planned / approval action | waiting / owner attention | Actual native planned task; fixture for approve action |
| awaiting_result / blocked | waiting | Adapter unit tests |
| verified / partially_verified | attentive | Actual deterministic readback; no celebratory success invention |
| failed / unknown / unsupported state | error / unknown | Adapter unit tests |
| explicit fresh listening / processing | corresponding voice state | Existing Core capture boundary; fixture/unit evidence here |
| explicit fresh speaking | speaking | **Synthetic only; no TTS publisher exists in current Core composition** |
| explicit muted | muted; preserved across availability loss | Unit evidence; no new mute control/publisher |
| explicit interrupted / cancelled | interrupt / cancel presentation | Synthetic/unit evidence; actual task cancel separately passed native reference |
| link loss / reconnect | unavailable / fresh attentive | Actual native network interruption and restoration |

Historical completed tasks do not dominate current work. Unresolved unknown task
state remains unknown. Voice and task states are not inferred from opening a window,
Orb labels, Worker testimony, task descriptions, audio duration or sensed emotion.

## 9. Interruption, expiry and lifecycle

Native revision fences reject older/equal readbacks. Opaque source IDs include the
native connection epoch; retired epochs cannot return. Each admitted event receives
a monotonically increasing presentation generation. Unchanged heartbeats keep a
stable transition ID, so they do not replay gestures.

Observation leases are eight seconds, independently capped by the actual voice,
current-task and task-list readback times used. Polling tasks cannot renew speech;
voice responses cannot renew cached task activity. Expiry becomes UNKNOWN and cancels
choreography. A fresh new generation is needed to recover. Shared renderer visibility
suspension, OS reduced motion, urgent attention, mute and availability arbitration
remain authoritative presentation constraints. Actual interrupt/cancel replaces
queued choreography; animation cancellation never proves audio/task termination.

## 10. Voice and task integration

Task state is real Core readback. Existing explicitly commissioned DesktopVoice
capture/start/stop/inspect remains the only current voice path. The default reference
composition has no voice adapter. The adapter can hold fresh speaking beyond five
seconds and terminate on actual end/interruption/loss; no five-second TTS animation,
prosody inference, lip sync, synthesized speech publisher or Elocution work was added.
Full expressive speech/presentation accents and cross-device Presence remain later work.

## 11. Tauri smoke tests

The actual debug executable passed startup/WebView readiness, uncommissioned launch,
close/hide, reveal and explicit exit via the existing lifecycle harness. The native
Core reference passed CNG/PSS signing, deterministic Ask, Dictate preview, typed file
action/readback, registered UIA application/readback, cancellation, shortcut collision,
Core reconnect and native restart with shared tasks retained. Transformation text was
SIMULATED / REPORTED; no provider inference or physical microphone acceptance claim.
The controlled network-stop capture produced an expected aborted HTTP response
diagnostic when a timed-out client disconnected; restoration and page checks passed.

## 12. Visual packet and review

See [capture packet](ui/desktop/integration/README.md). Five owned native-window PNGs
show actual disposable-Core available, waiting, verified readback, unavailable and
reconnected states. One short native WebView attention-transition GIF is included.
Six separately labelled React fixtures cover all requested showcase states.

Inspected native waiting and the six-state sheet: asymmetric face and opening eye
remain legible at 58 logical pixels; waiting/unavailable withdraw, working concentrates,
speaking holds engaged, interruption cancels/reorients. Stable SVG geometry/IDs and
reduced-motion behavior are tested. This restrained existing shell still has its old
engineering canvas/layout; it is not a visually approved persistent-character product.
No broad motion-polish, continuous performance, cinematic interaction or owner
naturalness PASS is claimed. Fixture text was corrected after visual inspection.

## 13. Tests and builds

- Python full suite: **532 tests run: 526 passed, six optional skips**.
- Desktop frontend: **17 tests**, TypeScript and production Vite build PASS.
- Expression Lab/shared engine: **35 tests**, TypeScript and Vite build PASS.
- Rust: fmt, Clippy with warnings denied, **seven tests** PASS.
- Tauri debug `--no-bundle` build PASS, pinned Rust 1.99.0 / Node 24.21.0.
- Browser fixtures: six state labels/render captures, 6.1-second speech hold,
  8.3-second expiry, OS reduced motion and no page errors PASS.
- Actual native capture: readback of `2 + 3 = 5`, offline/reconnect epoch rotation,
  voice remaining idle and no page errors PASS.
- Ruff lint/format, mypy, repository/link/credential scan and whitespace checks PASS.

The inherited Expression documentation test import ordering was fixed locally so
repository lint passes. No source/package version upgrades or new third-party runtime
dependency were introduced. Android was not rebuilt because its library is unchanged.

## 14. Security and privacy

The production CSP, native command ACL and credential/signing boundaries are unchanged.
The production bundle guard excludes both historical showcase and new integration
fixtures. Adapter privacy tests assert private sentinel material/task identifiers never
enter events. Rust tests reject malformed commands, untrusted endpoints, stale reviews
and delayed voice responses. Existing Desktop privacy/revocation tests and native
reference durable-content-absence checks passed. Capture uses disposable DB/workspace,
ephemeral native key and anonymous bootstrap stdin; no owner applications, clipboard,
microphone, recordings, credentials or memory exports are accessed. Native screenshots
are confined to the launched test PID; WebView debugging is loopback/test-only with
a temporary user-data directory. Evidence receipts omit credentials and source IDs.

## 15. Remaining blockers

GitHub account recovery; fresh remote ref/PR inspection; required exact-head CI;
owner Desktop/runtime and Expression quality/device review. Actual TTS, mute and
barge-in publishers are absent from this composition, so their fixture tests are
not end-to-end voice acceptance. Production installer, signing/update distribution,
physical-device, continuous native performance and owner naturalness were not tested.
No safe merge is authorized while those required boundaries remain unresolved.

## 16. Closing PR #16 and #17 safely

After account recovery, fetch and inspect actual heads/base/checks before applying
anything. Preserve histories; do not force-push or copy this combined merge wholesale
onto either independent foundation branch.

- **#16 Desktop foundation:** reconcile against current `work`, retaining canonical
  00–20 docs plus Desktop runtime descriptions. Resolve the eight documented conflict
  locations as shown here. If epoch/voice fencing is split into #16, carry only native
  `ExpressionReadback`, bridge timestamps/fences and their Rust tests; the renderer and
  local Expression dependency belong to the integration candidate. Rerun all required
  Windows/Core/frontend/privacy/lifecycle checks on the resulting exact head and obtain
  the required owner/runtime review before an explicitly authorized merge.
- **#17 Expression foundation:** preserve all v3/shared-engine/render evidence. Carry
  the documentation-test import-order fix from `tests/test_canonical_slice_docs.py`.
  Obtain required owner quality/device review and exact-head repository, expression
  and native Android checks; do not treat previous local/emulated evidence as physical
  approval. Its dependency is reusable without Desktop-specific code changes.
- **Integration:** after the foundations are accepted, reconcile this candidate against
  their actual merged commits and rerun exact-head CI/Windows checks. Keep adapter,
  renderer-slot adoption, build order, scoped tests/capture scripts and this report
  together. No automatic close/merge is implied by the local result.

## 17. Local commits

Both foundation histories are reachable through `f8e9ed6`. The subsequent adapter
and evidence commit is the candidate branch HEAD, recorded in the final handoff.
No publish/push occurred. Ignored local logs retain the command output.

## 18. Slice 12.1 starting point

Use this isolated candidate's real shared `ExpressionPresence` and trusted adapter
as the functional baseline. Begin a separately reviewed compact-presence brief from
actual character behavior, 58px/DPI constraints, attention/privacy and Windows lifecycle.
Study ambient placement, interaction and motion with the owner; do not select an old
A/B/C layout or substitute a static avatar. Comprehensive Slice 12 visual redesign,
Slice 13, World Model/Sentry and post-alpha work remain outside this run.

## Reproduce

From this worktree with the supported Node/Rust/Python environment:

```powershell
python -m scripts.build_desktop --checks
python -m scripts.desktop_tauri --self-check
python -m scripts.desktop_baseline --lifecycle-only
python -m scripts.desktop_expression_capture
python -m scripts.desktop_expression_native
```

Capture scripts overwrite only this candidate's newly generated integration packet.
They require an unused owned local port / disposable WebView profile. Remote approval,
physical owner acceptance and deployment are not performed by these commands.
