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
