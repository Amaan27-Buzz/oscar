# Desktop Companion and Workspace — Group 2.5A

The Companion is a presence object, never a miniature application. The Workspace
is the place to converse, read, prepare work, inspect evidence and make decisions.

| Owner | Responsibilities |
|---|---|
| Companion (`companion`) | Unchanged shared Orb, bounded operational status, owner-attention signal, open Workspace, shortcut toggle, hide, cancel explicit voice capture |
| Workspace (`main`) | Ask conversation, reading, Dictate/Edit previews and destinations, advertised Act forms, Core activity/evidence, exact approvals, context, available executors, preferences |
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
advertised review. Text tools expose existing capture/preview/destination flows;
Activity retains Core tasks and evidence. Exact decision/signing still occurs in
Workspace/native UI. Companion's liked appearance remains unchanged, with
isolated styles. Reduced motion remains complete. Aperture `42b565c` remains an
assessed historical reference; its scripted content and expanding dock
architecture are not adopted.

## Native preferences and handoff

Theme and shortcut/enabled choices persist in native app configuration through
bounded, validated, atomic replacement. Review harnesses isolate owner settings;
reference clients cannot save them. Private content and capture choices remain
outside preferences. Ordinary reopen preserves the owner-selected page; the
Companion attention action opens Activity without retrieving or granting an
approval. Actual signed decisions remain in Workspace/native review.

Software, source checks and native evidence are complete for the candidate.
The owner inspects the live app and supplies visual/copy feedback before merge
or Group 2.5A closure. No physical voice/device or installer acceptance is claimed.

Implementation base: consolidated main `fd191a2d7ca7f98c456969c74173a0340f789578`.
Candidate stops at owner visual review; no merge, Mobile or Slice 14 work.

## Library controls — 2026-10-13

Radix Themes supplies non-modal choice popovers and radio groups; Radix
Collapsible supplies expandable sections. Native browser arrow markers are
replaced by consistent plus/minus state indicators. Values and authority remain
in the existing native/Core contracts. The CSP remains unchanged; native tests
verify keyboard focus return and no popup CSP violations.
