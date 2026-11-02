# OSCAR — Alpha Packaging, Owner Acceptance and Final Main-Only Consolidation

**Status:** Owner-directed end-of-functional-alpha release protocol (2026-11-02); **do not execute branch deletion or remove local material now**.

OSCAR's source of truth is `main`. The goal is to complete actual non-deferred software, package both approved apps, let the owner use and inspect the application, then reduce the active Git branches to **only `main` locally and on GitHub**, while retaining recoverable historical work outside those active refs.

This is a **release-stage operation**. It must not interrupt Core/Desktop/model connectivity, real product implementation, the cinematic [First-Run Experience](../FIRST-RUN-EXPERIENCE.md), or packaging.

## Stage 1 — ship a usable owner-testable candidate

1. Bring the real Core and approved Desktop Workspace online, including live model inference, persistent conversations and honest capability state. Keep the disposable UIA reference visibly separate.
2. Implement actual user-facing paths through the non-deferred software families: model switching, authorized computer use, Workers, memory, voice, Android, Sentry/Chief of Staff, MCP/integrations and authority controls as available. Preserve safety-critical policy, secrets and uncertain-effect boundaries.
3. Build the actual Windows Desktop/Companion package or reproducible installable alpha, plus Android APK/debug/emulator installation path. No mock-only release.
4. Provide a simple launch/install and upgrade path; preserve user data across upgrades. Clearly distinguish local dev builds from signed/distributed builds.
5. Integrate cinematic first-run and optional Setup Studio into the packaged app, including progressive device/server/cloud commissioning without misrepresenting unavailable providers or physical hardware.
6. Verify at least one end-to-end live conversation, persistence after restart, real authorized action and relevant UI flows. Mark untested items PARTIAL/NOT_RUN rather than passing them by analogy.
7. Hand the owner a concise **manual acceptance checklist**: exact commands or installer paths, expected behavior, known bugs, local versus remote limitations, supported model/provider setup, logs/error capture, phone emulator access, and safe uninstall/recovery.

A functional alpha may have noncritical bugs. **Security/authority, source-of-truth integrity and honest outcome reporting are not optional.**

## Stage 2 — owner-driven manual test and package checkpoint

**Wait for explicit owner confirmation that the candidate is worth retaining before destructive consolidation.** Owner can report bugs and require iteration first; don't freeze feature development prematurely.

Before any pruning:
- Make actual working functionality and approved Windows/Android/Orb assets source-controlled on `main`.
- Inspect all modified, staged, untracked and ignored files for unique *source* or essential migration tooling. Keep credentials, local models, private databases and secrets **out of public GitHub** and preserve separately.
- Confirm the release candidate's exact commit SHA, all intended pushes and clean status.
- Review any outstanding PRs, including old draft PR #10; closing a PR or removing its branch is not evidence that its code has been accepted.
- Inventory every local and remote branch; classify **fully merged, unique/divergent, experimental, active worktree, and open PR** against actual latest `main`. Do not rely on older branch counts.
- Preserve divergent/unpublished studies (including `codex/desktop-reimagined` if present) only after deciding whether to integrate, explicitly reject or archive them.

## Stage 3 — recoverable backup and fresh-main verification

1. Create a verified Git bundle or equivalent historical ref backup **outside** the checkout, covering all valuable local/remotes refs and unique commits (a bundle excludes uncommitted/ignored files).
2. Separately preserve necessary uncommitted source, unpublished design exports, user-configurable local state, secrets/Vault references, databases and migration backups in appropriate private locations, never in a public repository or disposable cleanup directory.
3. Perform an independent restore/verification check on the backup, rather than trusting that the file was written.
4. Make a **fresh checkout of the approved latest GitHub `main`** into a distinct directory, restore only required non-Git configuration/runtime data, and repeat actual Desktop/package smoke tests. Verify the expected SHA, app assets, working packaging instructions and data continuity.
5. Do not delete the original checkout, active worktrees, Git branches or backups merely because the clean clone succeeded.

## Stage 4 — main-only active development (requires owner approval)

Only after the manual-test/packaging checkpoint, backup validation and **separate explicit owner approval for branch deletion**:

- Close or update superseded PRs with factual explanation; preserve relevant review context.
- Delete obsolete fully-merged remote branches, then delete or separately archive and remove unique/divergent remote branches according to the approved inventory. **Never merge divergences blindly or silently discard unique history.**
- Remove obsolete local branch refs and stale remote-tracking refs; resolve linked worktrees safely. Never delete the currently checked-out `main`.
- Keep `main` as the **only active local and GitHub development branch**. Git tags and external verified archives are allowed as recovery artifacts; no permanent forest of archive branches is required.
- Verify `git status`, `git branch -a`, latest `main` parity with GitHub, build/package/launch and recoverability.
- If Codex cannot perform authorized Windows cleanup because a policy blocks deletion, provide **exact verified PowerShell commands** for the owner; do not repeatedly retry or bypass the block. No `git clean -fdx`, force-push, rebase of public `main` or destructive blanket deletion.

The result is **one clean ongoing product branch with recoverable historical work**, not an erased history or a second software restart.

## Follow-on development

After branch consolidation, fix alpha bugs and extend features directly on `main` with ordinary cohesive commits and real user feedback. Do not restart the architecture, regenerate a giant `.oscar`/`.tmp` tree or treat another testing gate as product completion.

**Do not mark this protocol COMPLETE until the owner has actually reviewed a packaged alpha and approved final consolidation.**
