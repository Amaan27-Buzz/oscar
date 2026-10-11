# Group 1 — Desktop completion

Status: **SOFTWARE/REFERENCE COMPLETE CANDIDATE — NOT OWNER APPROVED OR PRODUCTION READY**.
Owner authorization 2026-10-11 covers Slice 12.2–12.6 and a draft PR only.
Manual/device acceptance is consolidated in the
[cumulative ledger](SOFTWARE-ALPHA-ACCEPTANCE-LEDGER.md); it no longer stops
authorized software work. Slice 13/Group 2 is not begun.

## Verified integration baseline

Repository: private `Amaan27-Buzz/oscar`. Fetched all branch heads into isolated
`buzz/*` remote-tracking refs without changing local branches or original origin.
Development branch: `build/slice-12-desktop-completion`, separate managed worktree.
Exact corrective base: `da8fddae50112c8859b21247d0cbaa617be8667e`.

Verified ancestry includes:

- Slice 10 Desktop runtime/concepts: `546310f254863d1073e21ce3eeb492770d8a7bcd`.
- Slice 11 shared expression candidate: `495c3324aabcd85b58438f3abb01500f37ee9baa`.
- Combined integration: `b9d3e049aef5148a10c710626b9e6b06771c9229`.
- Original presence: `5fea2071e891adf0fac7f9838ee556c9a60e1e1c`.
- Corrective draft PR #1 is OPEN/DRAFT at the exact requested base commit.
- Buzz `main` and `work`: `92a11aa05083f1983186976ba64bd30aa9f1f2a0`;
  neither is modified or merged.

No older branch merge is necessary: these dependencies are already reachable.
Original worktrees, their uncommitted files, draft PRs and migration backups are
preserved. Historical reports and PR #1 raw evidence remain unchanged.

## Composition decision

Extend the existing character and writing leaf, with deeper reading, text tools,
action and task views disclosed only when needed. Core owns tasks, reasoning,
memory, routing, policy and verification. Native Rust owns validated IPC, source
freshness, signing and window lifecycle. React owns draft/presentation state;
it gains no chat-memory, executor or authorization engine.

One admitted native readback should feed both compact and expanded candidate
composition, avoiding independent competing state inside an embedded old App.
Retain the current production entry point until software validation supports any
separate promotion decision. Token streaming is not supplied by the existing Core
contract; expose actual task/progress updates rather than fabricated text streaming.

## Stage checkpoints

12.2 Ask → 12.3 Dictate/Edit → 12.4 Act/context → 12.5 Activity/approvals →
12.6 motion/accessibility/polish. Each stage requires local regression proof and
independent review before the next; exact commits/results will be recorded here.

## Evidence policy

Keep only curated native screenshots, short GIFs, manifests/checksums, receipts
and design/review documentation in Git. New raw sequences belong in an organized
local archive outside the repository. Do not delete or rewrite earlier evidence.
Reference executors and temporary data never imply physical audio, owner approval
or production acceptance. No credentials, owner content or private recordings are
published. GitHub Actions remain disabled; all reported checks are local.

Final report will record each implementation, architecture change, exact tests,
cross-stage/native scenarios, independent findings/corrections, curated evidence,
deferred obligations, commits, draft PR and dependencies for Slice 13.

## 12.2 — Ask software checkpoint

Bounded compact answers expand into a keyboard-focusable native reading surface.
Ask continues through actual Core tasks, actual progress and advertised cancellation
review. Failed/blocked/unknown outcomes never imply a started task or blind retry.
Accepted submissions clear only their own draft; unfinished input survives retreat.
Plain-text response wrapping/scrolling remains safe against executable markup.

Core derives bounded working context from successful same-session transient Ask
tasks; it is labelled reported data and routes subsequent model reasoning privately.
Discard removes it; restart does not recreate private history. A read-only scoped
MemoryExecutor consumes the existing MemoryFabric/Controller route. Worker testimony
remains REPORTED; Core rechecks exact retained support before exposing RECALLED or
INFERRED and source event IDs. Forget withdraws support. No memory grant, auto-retention
or model-prior fallback is introduced. Missing capability stays blocked.

Local validation: Desktop **39 tests / 6 files**, TypeScript/build PASS; focused
Core/Desktop/Memory **93 tests, 0 failures/skips**; Rust **11 tests, 0 failed/ignored**,
fmt/Clippy/native debug build PASS; Ruff PASS; mypy **64 source files** PASS.
The native reference passed **nine assertions** plus reading/footer geometry, with
curated screenshots in [the evidence packet](../ui/desktop/completion/README.md).

Observed and repaired before advancement: missing reading size in historical
showcase type map; clean-worktree frontend build ordering before Rust context;
duplicate interact event/reply retaining a submitted draft; response actions
overlapping the footer; new-session same-node private readback; a failed native
runner incorrectly classifying a partial run as verified. Final native receipt is
complete and conditional failure classification is fixed. Failed reading receipt
is preserved in the separate local evidence archive, not copied as a new frame dump.

[Independent review](reviews/12-2-INDEPENDENT.md): initial HOLD, then **ACCEPT
bounded software closure** after fixes; independently **28 frontend + 34 Python
tests** and the original privacy reproduction passed. This does not certify real
inference, subjective motion, OS focus or owner/device use. Default production
entry/composition and immutable canonical SVG remain unchanged.

## 12.3 — Dictate/Edit software checkpoint

The same writing leaf expands into text tools with separate local mode drafts,
linked tab/panel semantics, explicit voice start/finish/cancel, supported context
capture on invocation, provenance/permission/retention/expiry disclosure and
selection/focused-field editing. Window identity alone is not editable text.
Unregistered/inaccessible targets and unsupported reliable replacement remain
unavailable. Preview is destination-specific: focused Dictate discloses the whole
appended field, not only its transcript. Apply checks current offered destination,
context/preview expiry and effective UNKNOWN feedback. Consumption retires the
preview; no automatic replay exists. Core/Worker still fence expected value and
independently read back the actual destination.

Voice uses the existing portable capture/Recognizer/Transcript/StopToken contract.
Finish publishes actual processing then preview; cancellation fences recognition
and removes any owned preview. No opening, panel switch or animation starts audio.
Capture/model absence is explicit. Tests use simulated audio and a scripted
recognizer; no microphone, physical speech quality or inference acceptance.

Discard clears all presentation drafts, context/preview/review/private responses,
including the temporarily embedded old workspace's local Act state. Native
content revisions reject obsolete command replies/errors; privacy suppression
also covers late snapshots and voice previews. Active work is not implicitly
cancelled: private output is hidden and released after completion. Concurrent
discard preserves independent verification without redisplaying private results.

Validation: Desktop **44 tests / 7 files**, TypeScript/build PASS; Rust **12 tests**,
fmt/Clippy/native debug build PASS; mypy **64 source files**, Ruff PASS. Focused
Core/Desktop/Voice tests are recorded in the final stage receipt (64 cases after
the completion/discard addition). Native text tools passed **12 assertions**,
including actual 15-second expiry, no implicit listening, no-target disable,
separate retained drafts, preview/surface scope, and clear-all without task/action.
The separate `desktop_tauri --self-check` passed real native CNG/PSS,
registered WPF field readback, typed file action, cancellation, reconnect and
restart continuity; transformation remained SIMULATED/REPORTED and GUI consent
was not exercised. Curated [text evidence](../ui/desktop/completion/README.md).

Independent review initially held the stage for local UNKNOWN IPC feedback not
reaching Apply's guard. Corrected with a thrown-port regression; final
[review](reviews/12-3-INDEPENDENT.md) **ACCEPTS bounded software closure** after
**33 frontend + 41 Python** independent checks. The successful concurrent-discard
test also closes its coverage advisory. No manual/device boundary becomes PASS.

## 12.4 — Act/context software checkpoint

A controlled typed action draft shares the writing leaf, current Catalog, scoped
Worker, explicit context capture and real TaskStage. Catalog permissions/risk and
worker identity are disclosed. Withdrawal clears the selection and private fields
without silently switching executors. Required resources must be entered; an
executing/awaiting/result/verifying task across any mode blocks a competing form.
The submitted action names the exact resource while owner review remains separate.
No second executor, client authorization or success inference is introduced.

Local checks: Desktop **49 tests / 9 files**, TypeScript/build PASS; focused
Desktop/completion/browser-launch **51 tests, 0 failures/skips**; Rust **12 tests**,
fmt/Clippy/debug build PASS; Ruff and mypy **64 files** PASS. Native **7 assertions**
passed through real WebView2/IPC, actual disposable file execution and independent
readback. Separate isolated Chromium local submit/download and public HTTPS marker
verification passed; its desktop GUI classification remains UNVERIFIED. Native
fixture progress uses trusted reference execution, not human consent.

The independent review found the cross-mode competing-proposal defect; its fix
and two component regressions passed. Initial locator failure and a deficient test
fixture were corrected before closure. The final complete receipt supersedes the
failed receipt preserved outside Git. See the stage review and curated evidence.

## 12.5 — Activity/approvals software checkpoint

The candidate now has one controlled Activity/decision surface, fed by the same
admitted native readback. It replaces the embedded App and its second subscription.
Current task is immediately deduplicated into shared history before polling catches
up. Active/waiting and completed/partial/failed work are progressively disclosed;
real Worker ownership, reported progress, results, execution evidence metadata and
canonical recall sources retain their distinct provenance. Artifact identifiers,
kind/status/hash omit private locations and are session-bound. No private replay or
fictional continuation is offered; a fresh scoped request is required.

Exact task/operation/target/capability/plan material precedes native confirmation.
Opening or dismissing never grants consent. Expiry/current-action guards disable
obsolete confirmation; native Inspect invalidates pending reviews even if its
readback fails. Native content revisions fence reordered replies. Discard/restart
withdraws approval when private inputs are gone, while safe denial remains offered.
No new client-side permission system exists.

Local validation: Desktop **55 tests / 10 files**, TypeScript/build PASS;
Desktop/completion/Mobile **56 tests, 0 failures/skips**; Rust **12 tests**,
fmt/Clippy PASS; Ruff/mypy **64 files** PASS. Native Activity **nine assertions**
PASS: planned exact review/focus, no consent on dismissal, task-change retirement,
verification disclosure, actual 30-second expiry, offline controls and reconnect.
The development binary requires `cargo +1.99.0 build --no-default-features`;
production custom-protocol intentionally rejects a development URL. An initial
wrong-mode native failure is archived separately; permissions were not widened.

Independent review found loss of recall provenance in the new inspector. Added
canonical source IDs and historical/inference warnings with RECALLED/INFERRED
regressions. Direct Rust pending-review invalidation covers failed task-switch
readback. Manual native consent, physical audio and OS configuration remain deferred.

## 12.6 — Motion/accessibility/software integration checkpoint

The shared ExpressionController and immutable Orb are reused without a replacement
engine. Weighted movement, asymmetric eyes, pointer attention, interruption and
recovery retain their approved semantics. Heartbeats do not replay accents. The
Orb now persists across Activity as well as compact, reading, text and action
surfaces. Activity uses a 620×760 logical writing leaf rather than the legacy
820-wide workspace. Focusable response/decision regions, Act entry focus, linked
text tabs, explicit preview destinations, contrast/forced-color rules and wrapping
support keyboard use. Reduced motion removes leaf travel while operational state
and expiry remain functional. Native work-area/DPI placement retains its existing
scale/negative-origin clamp contract. No wallpaper/blur/click-through promise.

Actual native recording: 47 archived captures, ~127ms median capture cadence,
zero animation callbacks during a settled 3.2-second idle measurement and ~0.020
seconds renderer task time in that interval. The ~106 SVG-unit puck range covers
the whole recorded invocation/attention/work sequence, not isolated work travel.
The GIF preserves recorded segment cadence with waits between segments cut; it is
WebView2 content, not a compositor recording or a 60fps measurement. Independent
review inspected multiple frames and verified all raw hashes. Owner naturalness,
OS compositor smoothness and physical DPI remain deferred.

Local checks: Desktop **56 / 10 files**, Expression Lab/shared engine **36 / 5**,
Rust **12**, all PASS; TypeScript/build, Rust fmt/Clippy/development build, Ruff
**145 files**, mypy **68 files**, repository links/secrets and WPF/native-CNG
reference PASS. Integrated native rerun passes Ask **9**, Text **12**, Act **7**,
Activity **9** assertions; polish **10**. Native self-check independently verifies
registered WPF expected-value/readback, typed files, cancellation, reconnect,
restart/shared-task continuity and real CNG/PSS. No owner consent, microphone,
provider inference or device PASS is inferred from those reference results.

Stage review ACCEPTS bounded software closure. A separate fresh final code/UX
review independently found and reproduced two defects: exact review material was
silently sliced, and Worker-output truncation used the wrong source length. Both
are corrected and independently reproduced again: complete review up to 24,000
UTF-8 bytes, fail closed before challenge creation above it; native matching bound;
excerpt flags from the actual selected output. Replacement-session key enrollment
also does not transfer prior private inputs: ordinary task metadata and safe
signed denial/cancellation remain available, but approval needs the original live
private request or a fresh request. This explicitly narrows an ambiguous review
boundary without creating new authority. Three regressions cover these paths.

Final independent assessment: **7.8/10, ACCEPT bounded software baseline**, no
remaining demonstrated P0/P1/P2 release blocker in the tested scope. Visual score
is advisory. Remaining design limits include dense consequential review text,
caption/background judgement on a real wallpaper, and motion cadence/compositor
acceptance. Only the owner approves the product; no default promotion or merge.


## Final integrated results and recommendation

The canonical full command `python -m unittest discover -s tests -t . -q` ran
**551 tests in 118.017 seconds:545 executed successfully, 6 skipped, 0 failures**.
All six skips are unrequested optional Windows/local-model/neural reference
executors. The earlier command without `-t .` failed 12 relative imports; it is
preserved as a validation failure, not CI or product success. ResourceWarnings
from disposable HTTP-error fixtures remain visible; no assertion failed.

Desktop56, Expression36 and Rust12 tests passed. Ruff checks and formatting for
`oscar tests scripts` (145 files), strict mypy68 files, TypeScript/production build,
Rust formatting/Clippy/development build, repository links/secrets and canonical
numbering tests passed. A broad `ruff check .` reports60 pre-existing formatting
violations in historical expression capture scripts outside the configured gate;
those unrelated historical scripts were not rewritten. No remote CI claim.

Cross-stage native runs verified a draft through invocation/reversal, bounded Ask
into reader, distinct Text drafts/preview/expiry/discard, a typed disposable-file
Act, exact owner review with no consent, task-change/expiry/offline/reconnect and
persistent Orb across Activity. The final Core corrections were independently
reproduced and followed by a full 551 run plus native Activity/CNG/UIA/lifecycle.
Registered WPF independent readback, signed cancellation, native restart/shared
tasks and safe scoped files passed. The owned uncommissioned lifecycle reference
passed close/hide, reveal and explicit exit. Human tray/hotkey foreground comfort,
real applications/audio and sustained owner use are still deferred.

Receipts: [local checks](../ui/desktop/completion/evidence/local-checks.json),
[native evidence packet](../ui/desktop/completion/README.md),
[root causes/regressions](DESKTOP-COMPLETION-REGRESSIONS.md),
[final independent review](reviews/GROUP-01-INDEPENDENT.md),
[owner verdict](../ui/desktop/completion/OWNER-VERDICT.md).
Original 12.1 captures/reports, foundation branches and migration backups are
preserved. Final-curated evidence is privacy-reviewed disposable content: synthetic
math/model/text, temporary paths and public reference markers; no owner content,
credentials, bootstrap tokens, private recordings or profile archives are included.
Curated PNGs/GIF and receipts are in Git; raw motion 47 frames/logs/prior-run captures
are in `D:\TheDawnlightGroup\DawnlightLabs\oscar-local-evidence\group-01-desktop-20261011`,
with an `archive-manifest.json` SHA256/byte manifest. This is a new evidence archive,
not a modification of migration backups.

### Commits and integration boundary

- Verified base: `da8fddae50112c8859b21247d0cbaa617be8667e`.
- Scope/ledger: `2701884c0de84e5eb5aa07e9a2025018f11a5734`.
- 12.2 Ask: `d1afb438a55bd8e329060e391405cd3ae2341f07`.
- 12.3 Text: `e4c5abdd61817f0101c43fbd8b60957a845d4f59`.
- 12.4 Act: `c2225f4fdf67a4d9fc748df597382c66c9b6d831`.
- 12.5 Activity: `0535d642bc6bb962102cd35f61cdd5d611469003`.
- 12.6 tested implementation: `2ddb8df73ca60517e4708a0f0163d0201f55d5fa`.
- Draft PR: [Buzz #2](https://github.com/Amaan27-Buzz/oscar/pull/2), targeting
  `fix/slice-12-1-presence-quality`; OPEN/DRAFT, not merged.
- Subsequent publication/report changes contain documentation only; final remote
  HEAD is provided in the task handoff and visible in the draft PR.

The production entry still renders App; Living remains a DEV opt-in and native
prototype flag. Shared typed Act validation, Core privacy/preview/voice fixes and
additive readback metadata improve existing functional paths, so production
controls are not claimed pixel-identical. No automatic default-presence promotion.
No second memory store, expression engine, action executor or authorization system.
Existing main/work and corrective/original candidates remain unmerged.

**Recommendation: ACCEPT bounded Group 1 software/reference candidate as the
baseline for the next authorized software group.** Independent review found no
remaining demonstrated software release blocker. This is not owner approval,
production readiness, distribution acceptance or an instruction to begin Group 2.

### Dependencies and deferred acceptance for Slice 13 / later groups

Use the same Core/Controller/Grid/session, portable Voice Core and shared expression
contract; additive Desktop result/evidence fields do not create mobile authority.
Mobile UI must bind approvals to current signed material and preserve context
freshness/source/privacy. Commission real adapters and credentials only under the
later authorized commissioning scope; unavailable providers stay blocked. No React
working-context history may be migrated as a second phone memory system.

Consolidated obligations remain in the ledger: owner visual/naturalness and actual
wallpaper/desktop comfort; OS focus/hotkey/tray/hit regions; physical 100/125/150%
DPI/multiple monitors/taskbar/fullscreen/compositor; screen readers; microphone,
room echo/barge-in/voice quality; phone/OEM and Edge hardware; strong critical-risk
confirmation and distribution. Critical actions stay unavailable; ordinary native
MessageBox/CNG reference is not Windows Hello. Gate C stays PARTIAL. Group 2 has not
started, and accepted main/work/default UI are not promoted by this candidate.

Publication: pushed only `build/slice-12-desktop-completion` to the Buzz repository.
Draft PR #2 is attached for review. Corrective base/main/work refs were independently
rechecked unchanged. No merge, default promotion or next group was performed.

Final export prerequisite: the resumed terminal had lost its owned Vite server.
An additional native receipt-export attempt was stopped before verification,
then rerun successfully after restarting Vite; its final CNG/UIA receipt is in
the curated packet. This is a development-harness prerequisite, not a physical
or production acceptance result. The owned helper was stopped after export.
