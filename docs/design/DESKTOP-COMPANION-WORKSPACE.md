# Desktop Companion and Workspace — Group 2.5A

**Current status (2026-10-14):** [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) is **merged into main**; owner accepted the restrained neumorphic appearance provisionally. The final integrated design, actual physical voice/device, security and full product acceptance remain deferred. The original implementation-base SHA and earlier candidate notes below describe historical evidence, not an open PR. See [current product direction](../PRODUCT-DIRECTION.md).

The Companion is a presence object, never a miniature application. The Workspace
is the place to converse, read, prepare work, inspect evidence and make decisions.

| Owner | Responsibilities |
|---|---|
| Companion (`companion`) | Unchanged shared Orb, bounded operational status, attention, open Workspace, quick read-only Access/Sentry status and voice; shortcut management/secondary controls in overflow, hide, cancel explicit listening |
| Workspace (`main`) | Continuous Conversation with contextual Dictate/Edit and immediate actions; Automations availability/management; Activity outcomes, exact review/evidence; Devices; Preferences |
| Rust process | One authenticated Bridge/CoreClient, Core polling, private Workspace events, redacted Companion snapshots, native window/tray/shortcut lifecycle and CNG confirmation/signing |
| Core | Tasks, memory, routing, policy, authority, voice and verification |

The Companion receives a redacted state projection. It has no Desktop command
permission or event-listening permission. Native caller-label checks also reject
Workspace IPC from Companion. Tauri Any listeners can receive targeted events,
so target labels alone are not a privacy boundary. Companion requests the shared
native status projection every two seconds without polling Core again. No
responses, context, preview or exact review material are delivered to it.

Closing Workspace hides it without discarding drafts or ending the runtime.
Opening it never creates a second Core session. Tray/hotkey activation captures
only explicitly configured context before taking focus. Clicking Companion opens
Workspace without capturing whatever app happens to be in front. Explicit Quit
unregisters shortcuts and ends the process. Hiding Companion leaves tray/hotkey
available. Companion controls remain bounded in the same small window.

Persistent mute, acoustic disable, wake-word and Sentry contracts are unavailable.
Trigger-only means explicit activation. Cancel listening uses the existing voice
cancel contract; it makes no persistent mute claim. Slice 14 is outside scope.
The native typed `View.voice_support` projection reserves the integration point
for persistent mute, Sentry, acoustic awareness and wake-word support. Every
field currently serializes `unavailable`; extending it requires a real adapter
contract. It is independent of the actual current `View.voice` turn state.

## Direction

Operate and Read. Owner feedback rejected generic dark components, excess
rounded/modal containers and departure from OSCAR's canonical paper palette.
The owner refreshed Desktop light mode to warm chalk (`#F8F7F3`), white fields,
ink (`#252B2D`) and slate-blue accents on 2026-10-13. The Workspace uses compact
operational headings and open
reading/review pages. Matching dark mode uses the implemented warm-graphite token set.
See [individual screen references](../../desktop/design/workspace-screens/README.md).
Image references remain unapproved history; [the final native packet](../ui/desktop/workspace/README.md)
is the current owner-review candidate.

Conversation keeps its composer accessible and gives direct access to an
advertised review. Conversation exposes existing capture/preview/destination flows;
Activity retains Core tasks and evidence. Exact decision/signing still occurs in
Workspace/native UI. The canonical Orb remains unchanged, with isolated
Companion styles. Reduced motion remains complete. Aperture `42b565c` remains an
assessed historical reference; its scripted content and expanding dock
architecture are not adopted.

## Native preferences and handoff

Theme and shortcut/enabled choices persist in native app configuration through
bounded, validated, atomic replacement. Review harnesses isolate owner settings;
reference clients cannot save them. Private content and capture choices remain
outside preferences. Ordinary reopen preserves the owner-selected page; the
Companion attention action opens Activity without retrieving or granting an
approval. Actual signed decisions remain in Workspace/native review.

Software/source/native reference checks were completed for the candidate, and the owner supplied an **interim UI pass**. [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) has been merged, with final integrated visual and physical voice/device/installer acceptance still outstanding.

Historical implementation base: `fd191a2d7ca7f98c456969c74173a0340f789578`.
Desktop merge: `43c15d37a6421d438b8101d5e322489ae452b20d`. Mobile Group 2.5B visual design exploration is separate; Slice 14 is still planned.

## Library controls — 2026-10-13

Radix Themes supplies non-modal choice popovers and radio groups; Radix
Collapsible supplies expandable sections. Native browser arrow markers are
replaced by consistent plus/minus state indicators. Values and authority remain
in the existing native/Core contracts. The CSP remains unchanged; native tests
verify keyboard focus return and no popup CSP violations.

## Workspace material and continuity — 2026-10-13

The sidebar contains navigation and OSCAR presence, never a chat-thread list.
Core task history and outcomes remain available in Activity. Conversation is
one interaction point; Core projects authorized canonical Event Archive history or explicitly session-only history. There is no frontend history store.
Long-response scrolling spans the Workspace width, with its scrollbar at the
outer edge, a centered reading column and a separately anchored composer.

The owner requested stronger neumorphic material throughout the Workspace.
Shared paired upper-left highlights and lower-right shadows now give controls,
work panes, settings and the composer consistent relief in both themes. Inputs
retain clear white/graphite fields and focus borders. Buttons remain raised,
with modest corner radii; selected state and unavailable controls remain explicit.
See [native material and scrolling evidence](../ui/desktop/workspace/material-review/README.md).

Companion uses a fixed 148 × 164 logical-pixel window. Its icon toolbar expands
on hover or keyboard focus and retracts on pointer leave, without moving the Orb
or resizing the native window. More/right-click requests a bounded native menu;
no review/signing payload is accepted. Unsupported mute and Sentry stay disabled.
See [native hover evidence](../ui/desktop/companion-review/README.md).

## Product direction correction — 2026-10-14

The approved Companion is preserved. Workspace navigation is Conversation / Automations / Activity / Devices / Preferences. Contextual writing and immediate action review belong in Conversation; Automations does not reinterpret file-write forms as persistent Workers. Activity groups owner attention, running work and outcomes, with identifiers/evidence behind disclosure.

See [the ownership and authority decision](../decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) for the corrected Ask / Secure / Full Access model and current unavailable activation. History uses Core and the canonical archive with separately provisioned read/retain grants; no browser persistence or invented retention authority. New native evidence is recorded separately from historical captures. Owner visual acceptance and merge remain pending.

## Natural interaction and toolbar polish — 2026-10-14

Conversation has no utility launch buttons, redundant large title, raw epistemic/retention labels or session-store notices. The empty state is centered above a stable composer. Voice is offered only with real Core availability and microphone permission; contextual edits and explicit supported operations use existing private review and native signing. Direct controls remain in advanced Preferences. Memory/privacy settings describe saving, reopening and app context in plain language. Activity rows use balanced insets and compact selection styling; task evidence stays accessible through disclosure.

The approved Orb, motion, tray and 148 × 164 window are preserved. Toolbar icons are Open Workspace, Access, Sentry, voice and More. Global shortcut and Preferences live in More. Native Access inspection marks fresh Core authority; Secure and Full Access cannot activate. Sentry's Passive/Aware/Guard/Away/Sleep are unavailable and do not listen. Native popups are positioned inside the monitor's work area rather than clipped by the WebView or taskbar. A focused Workspace lowers Companion's always-on-top layer; hiding/closing Workspace restores it. Exact signing remains exclusive to Workspace/native owner review.

Current captures and validation: [interaction polish](../ui/desktop/interaction-polish/README.md). Older packets remain historical evidence. Broad multimonitor/DPI, physical microphone and owner visual acceptance remain separate.

Owner messages align to the right of the conversation column; OSCAR replies align left. Both restored and current turns use the same responsive styles.
