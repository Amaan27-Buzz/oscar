# Group 1 — Desktop completion

Status: **IN PROGRESS / SOFTWARE CANDIDATE, NOT OWNER APPROVED**.
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
