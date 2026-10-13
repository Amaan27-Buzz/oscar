# Workspace material and conversation scrolling — 2026-10-13

Owner feedback requested OSCAR continuity, correctly positioned scrolling and
stronger neumorphism across the Desktop Workspace. The sidebar task list is
removed; Core history remains in Activity. No independent chat or memory store
was introduced. The scrollbar now occupies the outer Workspace edge; readable
content and composer retain a centered, aligned width. The composer stays visible
when a long response scrolls, including the narrow native window.

Paired relief shadows share one light direction, depth and material palette
across buttons, composer, work panes, appearance previews, settings and choices.
Inputs retain clear field boundaries. Reduced motion, visible keyboard focus,
unavailable states, exact review material and native signing remain supported.
The canonical Orb is unchanged.

Actual Tauri/WebView2 captures: [light Preferences](preferences-light.png),
[dark Preferences](preferences-dark.png), [long light response](long-response-light.png),
[long dark response](long-response-dark.png), [narrow reading](long-response-narrow.png),
[Act](act-light.png), [Activity](activity-dark.png), [Devices](devices-light.png),
[Text tools](text-tools-light.png). These are owned native HWND captures.

The [scrolling receipt](receipt.json) records both themes and every route using
an authenticated disposable Core. The long response is scripted and REPORTED;
it is test data, not model inference or owner conversation history.
The [architecture receipt](acceptance.json) covers the shared native lifecycle,
reconnect, shortcut collision, task continuity, security fences and accessibility.

Reproduce after building the existing Tauri debug candidate:
`python -m scripts.desktop_workspace_polish` and
`python -m scripts.desktop_workspace_acceptance` (the latter defaults to the
original evidence directory; direct its OUTPUT here to preserve older packets).

Verification: 74 frontend tests, 15 Rust tests, 36 shared Expression tests,
TypeScript/Vite/Tauri debug build, Rust fmt/Clippy, repository links/secret checks,
58 native architecture/layout checks, 22 scrolling/material checks and both-theme
Radix keyboard/CSP checks pass. Native CNG-PSS/action/restart self-check passes.
The broader Core run executed 559 tests: 552 passed, six skipped, and one
browser-navigation timeout case failed to reach its fixture within its three-second
budget. All three BrowserLifecycleTests pass on isolated rerun, including that
case. The full-suite failure remains recorded; no Core behavior or timeout was
changed, and a clean broader integration run is still required before merge.

Owner visual acceptance remains pending. No production enrollment, physical
voice/device, installer or multimonitor acceptance is claimed. This candidate
remains a draft PR; Group 2.5A is not closed or merged.
