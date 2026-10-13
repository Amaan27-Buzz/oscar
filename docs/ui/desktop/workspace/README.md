# Group 2.5A — Companion and Workspace owner review

**2026-10-13: software candidate ready for owner visual review.** The final
implementation preserves Companion, adds the complete Workspace, implements
paper light/warm graphite dark themes and persists native appearance/shortcut
preferences. Alignment and narrow-window checks cover every route. Owner visual
acceptance and merge remain separate; this document does not claim either.

This is a real bundled Tauri/WebView2 candidate on consolidated main, with two
native windows sharing one Rust Bridge and authenticated Core session. It is
not Aperture or the old living-presence development route. Aperture's local
`codex/desktop-reimagined` branch and `42b565c` commit remain preserved.

## Native captures

Companion: [idle](evidence/companion-idle.png) ·
[working](evidence/companion-working.png) ·
[owner attention](evidence/companion-attention.png) ·
[controls](evidence/companion-controls.png) ·
[Core unavailable](evidence/companion-unavailable.png).

Workspace: [home](evidence/workspace-home.png) ·
[conversation](evidence/conversation.png) · [reading](evidence/reading.png) ·
[activity](evidence/activity-working.png) · [approval](evidence/approval.png) ·
[text tools](evidence/text-tools.png) · [executors](evidence/devices.png) ·
[actions](evidence/actions.png) ·
[preferences](evidence/preferences.png) ·
[close/reopen](evidence/workspace-reopened.png) ·
[unavailable](evidence/workspace-unavailable.png).

Dark: [home](evidence/workspace-home-dark.png) ·
[conversation](conversation-review/conversation-dark.png) ·
[reading](evidence/reading-dark.png) · [text tools](evidence/text-tools-dark.png) ·
[actions](evidence/actions-dark.png) · [activity](evidence/activity-working-dark.png) ·
[approval](evidence/approval-dark.png) · [preferences](evidence/preferences-dark.png) ·
[executors](evidence/devices-dark.png).

Narrow: [paper Preferences](evidence/preferences-narrow.png) ·
[dark Preferences](evidence/preferences-narrow-dark.png).

[Native interaction recording](evidence/companion-workspace.mp4) continuously
captures the launched native HWNDs during Companion → Workspace → Companion.
The two owned windows are composed side by side; this is not a recording of the
owner's desktop or unrelated applications. Captures use Win32 PrintWindow;
transparent Companion areas appear against black in that capture API.

The [native receipt](evidence/acceptance.json) comes from the actual bundled
executable and a disposable authenticated Core. Arithmetic and task state are
real Core results. Long model text is explicitly SCRIPTED REFERENCE, not real
inference. Fixture task progression does not assert human approval. Native
confirmation/CNG-PSS, UIA readback and restart are independently checked by
`python -m scripts.desktop_tauri --self-check`.

## Reproduce

Use the existing dependencies and caches. From `desktop`, run:

```powershell
npm run build
npm run tauri build -- --debug --no-bundle
```

Then from repository root (only one native fixture at a time):

```powershell
python -m scripts.desktop_workspace_acceptance
python -m scripts.desktop_tauri --self-check
```

For interactive owner UI review with the same executable and a disposable Core:

```powershell
python -m scripts.desktop_presence_quality --workspace --open-workspace
```

The review Core is explicitly labeled. It uses temporary data, actual arithmetic
and scoped tasks; model responses are scripted and voice remains unavailable.
It does not commission a permanent Core or borrow owner credentials. Exit the
review helper with its `cleanup` command after closing the UI.

The ordinary executable starts Companion and tray without owner credentials;
Core remains unavailable until enrolled by the trusted native composition.
No microphone opens on launch. Mute, Sentry and wake-word capabilities remain
unavailable; explicit dictation is the existing start/stop/cancel contract.

## Review and limits

See [verification and independent-review record](REVIEW.md) for test counts,
review corrections and remaining acceptance boundaries.

The first native inspection caught and corrected a root CSS cascade conflict
and Companion control placement. Independent code review found event-channel
privacy, discard and capture-preference issues; all three were corrected and
independently rechecked. Real native tests deny Companion command/event access.

Owner visual acceptance, physical voice/device calibration, production enrollment,
installer/distribution acceptance and broad multimonitor interaction are NOT RUN.
No Mobile or Slice 14 work; no branch deletion or merge. Gate C remains PARTIAL.

**Latest owner-feedback revision:** [tactile Workspace](tactile-review/README.md)
replaces the earlier Devices/Preferences styling and applies the owner's
neumorphic button/material direction, Orb blue accents and spacing/motion fixes
across every Workspace page. Historical native packets above are preserved;
this revision has 64 frontend tests and 53 native checks passing.

**Current revision:** [Forms, Activity and product language](forms-activity-review/README.md)
supersedes the inset-control treatment above. It includes the corrected composer,
Act/Activity restructure and removal of developer banners/internal UI copy.
Runtime test provenance remains explicit in the evidence and launch helper.

**Latest Act revision:** [action editor](action-editor-review/README.md) replaces
the stacked Act form. File writing now uses a destination/content editor with
context and permission details in a compact support area. Other pages retain
the preceding revision. Owner visual acceptance is pending.

**Latest controls and palette:** [Radix library controls](library-controls-review/README.md)
replace browser dropdown arrows and triangle disclosures with plus/minus state
indicators. Light mode now uses warm chalk, white fields and slate-blue accents.
Native CSP and owner-review boundaries remain unchanged.
