# Preferences owner-feedback revision — 2026-10-13

Preferences replaces the previous two-column form with visual appearance choices,
keycaps and a native-state shortcut switch, explicit voice availability, grouped
presence controls and a separate privacy/Quit footer. Existing commands and
permissions are preserved. Shortcut editing reflects the configured native value.

Motion is bounded: theme surfaces crossfade, selected appearance checks settle,
the shortcut thumb moves between native states, and controls acknowledge presses.
Reduced motion removes these transitions. No looping decoration or dependency.

Actual native WebView2 captures: [paper](preferences-light.png),
[graphite](preferences-dark.png), [lower controls](preferences-dark-lower.png),
[narrow paper](preferences-light-narrow.png),
[narrow graphite](preferences-dark-narrow.png).

The [receipt](receipt.json) records native shortcut toggling, real theme selection,
reduced-motion computed styles and no horizontal overflow at an 800px native
window. Frontend tests: 63 passed; TypeScript/Vite and Tauri debug build passed.
The Core is disposable and reference-labeled. Owner visual acceptance is pending.
Previous full-suite/native evidence remains historical for its recorded build;
this revision changes Workspace presentation only.
