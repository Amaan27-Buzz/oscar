# Companion interaction revision — 2026-10-13

The native Companion is a fixed 148 × 164 logical-pixel presence window.
At rest, only the shared Orb, truthful status dot and small toolbar handle
remain visible. Hover and keyboard focus reveal icon controls with a bounded
260 ms expansion. Pointer leave retracts them; the Orb and native window do not
shift. Reduced motion disables transitions. No transcripts, task lists or review
forms are added. The canonical Orb artwork and shared expression authority remain.

More/right-click requests a Windows-native menu for opening OSCAR, toggling the
actual global shortcut, cancelling a supported active voice turn and hiding
Companion. Unsupported mute and Sentry are explicitly disabled. Native requests
cannot supply arbitrary actions, review IDs or signing material. Companion still
receives only redacted shared state, with no private Workspace event permission.

[Hover recording](companion-hover.mp4), [idle](companion-rest.png),
[expanded controls](companion-hover.png), [attention](companion-attention.png)
and [working](companion-working.png) are actual owned native HWND evidence.
[Motion checks](motion.json) measure intermediate widths, fixed Orb position,
control reachability, retraction, keyboard focus and reduced motion. The recording
targets 20 fps and captures only the launched Companion, against a neutral backdrop.
[Two-window recording](companion-workspace.mp4) and
[native acceptance](acceptance.json) use the authenticated disposable Core.

Direct Computer Use menu/drag inspection was interrupted by the owner with
Escape; those interactions are not claimed as independently visually verified.
Native menu request security is covered by Rust tests. Owner interaction and
visual acceptance remain pending. No physical voice or real inference claim.
