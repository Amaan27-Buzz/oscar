# Forms, Activity and product-language correction — 2026-10-13

This revision responds to the owner's rejected inset-button treatment, raw
composer resize handle, Act/Activity structure and developer-facing copy.

The composer uses a labeled, content-sized textarea, a fixed Send control and
visible keyboard guidance. Resizing is disabled; long drafts scroll within a
bounded field. Controls share one subtle raised treatment. Fields have explicit
boundaries; selected controls use color/border rather than inset shadow effects.

Act groups executor/operation fields, exact input and permission/destination
review. Activity separates task selection from the focused result/decision pane.
Exact reviewed material, consequence, permission, expiry, changed-task checks and
Windows native confirmation remain intact. Identifiers and verification metadata
are inspectable details; they are not the default page hierarchy. Measured
progress outside the supported range is never rendered as a real progress bar.

The reference-session banner, implementation footer and internal connection
labels are removed from the product layout at the owner's request. Native state
still carries the reference flag; this QA packet and the launch helper explicitly
identify the disposable reference Core. No production enrollment, real model
inference or microphone/device acceptance is claimed. Actual outcome and voice
availability states remain truthful.

Design guidance: Microsoft's [Fluent 2 textarea](https://fluent2.microsoft.design/components/web/react/core/textarea/usage)
and [button hierarchy](https://fluent2.microsoft.design/components/web/react/core/button/usage/).
These patterns inform the existing React/HTML controls; no new component package,
CSP relaxation, external asset runtime or parallel application state was added.

Actual native captures: [composer](workspace-home-dark.png),
[Act](actions-dark.png), [Activity](activity-working-dark.png),
[approval](approval-dark.png), [paper approval](approval.png),
[Devices](devices-dark.png), [Preferences](preferences-dark.png),
[narrow Preferences](preferences-narrow-dark.png).

66 frontend tests and TypeScript/Vite/Tauri build pass.
[56 native checks](acceptance.json) cover developer-banner removal, resize-handle
removal, no inset button shadows, keyboard/contrast, both themes and all six
routes at narrow width, native lifecycle, reconnect and shared task continuity.
Security tests include expired/changed reviews, offline controls and unchanged
exact confirmation requests. Owner visual acceptance remains pending.
