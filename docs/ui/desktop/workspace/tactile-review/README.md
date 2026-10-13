# Tactile Workspace owner-feedback revision — 2026-10-13

Current owner direction: restrained neumorphism, more color, redesigned buttons,
consistent spacing and responsive motion across the Workspace. This packet
supersedes the rejected list-style Devices design in `../rhythm-review/`.

Devices is now an executor selector and capability inspector. Capability
selection changes the focused detail pane; preparing an action opens the existing
Act form with the selected capability. No operation is executed by browsing.
Only the real Core catalog is shown; stale observations remain labeled.

The paper/graphite palette remains. Orb blue provides accent and primary-action
color. Raised buttons and recessed fields/selected controls use paired soft
shadows while keeping explicit boundaries, readable labels and focus outlines.
The canonical Orb, native signing and permission authority are unchanged.

Shared spacing and motion apply to Conversation, Text tools, Act, Activity,
Devices and Preferences. The toolbar has balanced 24px edges; page content uses
one measure and stable scrollbar gutters. Navigation selection slides, pages
settle, capability changes reveal focused content, and controls acknowledge
presses. Reduced motion disables movement and smooth scrolling.

Actual native captures: [Devices paper](devices.png),
[Devices graphite](devices-dark.png), [Preferences](preferences-dark.png),
[Conversation](workspace-home.png), [Text tools](text-tools-dark.png),
[Act](actions-dark.png), [Approval](approval-dark.png),
[narrow Preferences](preferences-narrow-dark.png).

Validation: 64 frontend tests and TypeScript/Vite/Tauri build passed.
[53 native checks](acceptance.json) passed, including both themes on every route
at narrow width, contrast, keyboard access, reconnect, shortcut/lifecycle,
shared task continuity and Companion privacy restrictions.

The review run uses an authenticated disposable reference Core. Model text is
scripted, microphone/device acceptance is not claimed, and owner visual
acceptance remains pending. Historical evidence is preserved.
