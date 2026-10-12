# Slice 12 — OSCAR Desktop Experience / Visual Redesign

**2026-10-12 redesign candidate:** [cross-platform rebuild](design/CROSS-PLATFORM-REDESIGN.md), [native evidence and regressions](design/cross-platform/README.md), [independent review](design/CROSS-PLATFORM-REVIEW.md). Branch `design/cross-platform-ui-rebuild`; draft into `build/slice-13-mobile-completion`. Current visual system is [DESIGN.md](../DESIGN.md). No merge/Slice14 or owner physical acceptance. Historical slice records below remain provenance.

**2026-10-11 current status:** Group 1 implements12.2–12.6 on
`build/slice-12-desktop-completion` from verified corrective `da8fddae`.
See [software completion](development/GROUP-01-DESKTOP-COMPLETION.md),
[curated native evidence](ui/desktop/completion/README.md) and
[deferred acceptance ledger](development/SOFTWARE-ALPHA-ACCEPTANCE-LEDGER.md).
Manual visual/physical/device acceptance is consolidated under the owner's
software-first authorization; it does not block this software scope. No default
promotion or accepted-baseline merge. Group2/Slice13 is not started.

**Earlier12.1 checkpoint:** owner-authorized Slice 12.1 quality recovery is isolated on
`fix/slice-12-1-presence-quality`, based on `5fea2071e891adf0fac7f9838ee556c9a60e1e1c`.
See [corrective native evidence and review](ui/desktop/presence/quality-recovery/README.md).
The prior 6.7/10 verdict and original captures are preserved. Default-presence
promotion and merge require owner approval. Slice 12.2 remains NOT STARTED.
The older status table below records the earlier exploratory checkpoint.

Future targeted design track on the accepted Tauri 2/Rust/React-TypeScript shell.
This Slice 10 run establishes functional surfaces and accessibility, not final
Opus/Antigravity visual polish. Canonical Orb geometry remains unchanged.

| Sub-slice | Scope | Status |
|---|---|---|
| 12.0 | Lifecycle stabilization and honest UI baseline capture | LOCAL baseline captured; remote CI billing-blocked |
| 12.1 | Presence / Orb / compact shell | A/B/C exploratory previews retained; **not approved or promoted**; resume after Slice 11 Expression System |
| 12.2 | Ask + interaction composition | NOT STARTED |
| 12.3 | Dictate + Edit | NOT STARTED |
| 12.4 | Act + context | NOT STARTED |
| 12.5 | Activity + approvals | NOT STARTED |
| 12.6 | Motion, accessibility and final polish | NOT STARTED |

**Owner order decision (2026-10-09):** before choosing or promoting a
12.1 compact concept, complete **11.1 expression vocabulary → 11.2
interactive Expression Lab → reviewed 11.3 shared state/render contract**.
The cross-platform plan is `docs/EXPRESSION-CORE.md` on accepted `work/main`;
pull/reconcile the updated accepted docs before implementing it. The full
Presence integration remains Slice 16 after World Model 14 / commissioning 15. None of the B/C or A
explorations is final design approval.

Refine section-by-section with owner review. Preserve typed/native security,
freshness, explicit context, signed approval, shared task truth and accessibility.
No frontend authority or separate OSCAR memory/history may be introduced.

See [historical 10R.1 concepts, captures and review](ui/desktop/explorations/10R.1/REVIEW.md).
Production compact UI remains unchanged; no concept is chosen or promoted.

Use the [12.0 baseline inventory](ui/desktop/BASELINE.md) for independent redesign
of existing states. Capturing this engineering UI does not perform 12.1–12.6.

Slice 12 may proceed alongside explicitly authorized backend work but must be owner-reviewed before Slice 20 Unified Alpha PASS. Mobile visual design is Slice 13. Gate C physical/device
acceptance is unaffected; it remains PARTIAL.


**Migration note:** older screenshots and docs under `docs/ui/desktop/`
retain the original `10R.0/10R.1` strings as immutable historical artifact paths.
The active Slice 12 stages map to those artifacts without renaming them.
Canonical crosswalk: `docs/SLICE-NUMBERING.md` on `origin/work`.
PR #16 remains an unmerged Slice 10 runtime + historical design experiment;
reconcile `origin/work` before new implementation work.
