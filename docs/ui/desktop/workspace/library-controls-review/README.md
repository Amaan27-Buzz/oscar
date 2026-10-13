# Library controls and light-mode palette — 2026-10-13

The owner explicitly requested real component libraries and plus/minus markers.
The active Workspace now uses pinned `@radix-ui/themes` 3.3.0 Popover/RadioGroup
and `@radix-ui/react-collapsible` 1.2.1. These replace native select arrows and
HTML summary triangles across Act, Text tools, Activity, Devices and reading.
Closed controls show plus; expanded controls show minus. Choices remain bound to
the existing values and native commands. No new capabilities or authority exist.

Radix Select was evaluated and rejected because its scroll-lock/scroll-area
runtime style tags were blocked by OSCAR's CSP. The shipped non-modal
Popover/RadioGroup picker uses the existing external stylesheet policy.
The Tauri CSP was not relaxed. Native tests record zero popup CSP violations,
keyboard selection, Escape focus return and keyboard disclosure expansion.

Light mode is now warm chalk `#F8F7F3`, rail `#EFEEE8`, white fields, ink
`#252B2D` and slate-blue primary `#2E667E`. Dark graphite and the Orb are unchanged.
Other platform palettes are not revised by this Desktop-only owner direction.

Actual native captures: [light action picker](action-picker-light.png),
[dark action picker](action-picker-dark.png), [light disclosure](disclosure-light.png),
[dark disclosure](disclosure-dark.png), [Act](actions.png),
[Preferences](preferences.png), [Text tools](text-tools.png),
[Approval](approval-dark.png).

Verification: 70 frontend tests; TypeScript/Vite/Tauri debug build; 56 native
[architecture/layout checks](acceptance.json); additional native
[library/CSP checks](library-receipt.json) in both themes. Body, metadata and
primary-action contrast meet 4.5:1; all six routes fit the narrow native window.
The contrast harness now accepts CSS's normalized three-digit hex values as well
as six-digit values, preserving the same required ratio.

Reproduce with `python -m scripts.desktop_library_acceptance` after the existing
native build. The existing workspace acceptance harness supports the library
pickers. npm audit reported zero vulnerabilities at install. Packages are MIT.
The library adds roughly 83 KB of compressed CSS and 34 KB of compressed JS to
the earlier bundle; this is the cost of adopting the actual styled components.

Sources: [Radix Popover](https://www.radix-ui.com/themes/docs/components/popover),
[RadioGroup](https://www.radix-ui.com/themes/docs/components/radio-group),
[Collapsible](https://www.radix-ui.com/primitives/docs/components/collapsible).

Evidence uses an authenticated disposable reference Core. Owner visual
acceptance and physical microphone/device acceptance are not claimed.
