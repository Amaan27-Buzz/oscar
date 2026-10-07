# Desktop Interaction Runtime — Slice 10

Starting authority: `main == work == 7043b9663fe6474e3457c7aa578e733f7a5a4c1a`.
Candidate branch: `club-d2/slice-10-desktop`, draft PR into `work`.
Status: **SOFTWARE / WINDOWS REFERENCE CANDIDATE; OWNER_ACCEPTANCE_NOT_RUN**.
Gate C remains **PARTIAL**. This candidate is not authorized to merge.

Slice 09 software is accepted. The separate 09R redesign, Slice 11, deployment,
Home Node and post-alpha work are outside this run. Physical Edge, Voice and
Mobile acceptance remain owner-deferred under the consolidated Gate C contract.

## Shell decision

Windows WPF, hosted by the installed Windows PowerShell/.NET runtime, is the
native presentation boundary. Python uses the existing Core and Windows adapters.
No new runtime dependency was added. Owner signing reuses the existing optional
`mobile` cryptography extra; Windows CNG signs the native surface's decisions.

Rust/Tauri would introduce a separate application build, browser host and bridge
to a Python Core that already owns these contracts. WinUI would also introduce
packaging/runtime requirements. WPF provides supported Windows controls, UIA,
keyboard focus, tray integration and window-message invocation at the current
boundary. A future shell can replace presentation without replacing Core tasks,
policy, evidence or the Windows Worker. This is a repository-run alpha foundation,
not an installer, portable executable or macOS/Linux acceptance.

`desktop/Presence.xaml` owns layout; `desktop/Presence.ps1` owns presentation and
native invocation. `oscar/desktop.py` is a scoped Core surface adapter. It reuses
Mobile's signed challenges, scoped sessions, receipt deduplication, task inspection
and cancellation. Legacy `sunday_*` record identities remain wire compatible;
they do not create another assistant. `DesktopContext`, `WindowsContext`,
`DesktopVerifier` and `DesktopVoice` separate context, Windows observation,
verification and audio from presentation.

```text
WPF presence / Windows context adapter
  ↔ authenticated loopback /v1/desktop
  ↔ Desktop Core surface admission
  ↔ Controller + Personal Policy + existing Runtime / Grid
  ↔ existing Dispatcher / Worker / UIA / browser / files / terminal
  → independent verification → shared task / Action Ledger
```

The local composition is not deployment. No ordinary PC becomes the permanent
Core host. Non-loopback transport, Windows Hello approval, packaging and device
acceptance are not represented as implemented.

## Observable interactions

| Mode | Implemented behavior | Limit |
|---|---|---|
| Ask | Typed question, explicit attached context, Core Controller routing, signed execution, response/evidence and cancellation | Missing memory/live/model capability blocks; model text remains REPORTED |
| Dictate | Typed text or final Voice Core transcript → preview → explicit destination | No implicit insertion or microphone opening; no provisional transcript application |
| Edit | Explicit fresh selected/focused text → Core transformation → result preview → accept → signed apply → independent readback | Model transformation is REPORTED; application verification proves destination text, not editorial quality |
| Act | Typed existing capability plans through Runtime/Dispatcher; GUI exposes exact file writing in approved workspace | No invented natural-language automation; advanced clients use existing typed Worker contracts |

Core task state is authoritative: planned/approval, executing, awaiting result,
verifying, verified, partially verified, blocked, failed, cancelled and unknown
stay distinct. Results are not promoted because an API returned success.
The UI shows only currently advertised task actions. Private requests have zero
automatic retries; an ambiguous outcome requires inspection and fresh intent.

The unchanged canonical SVG supplies the identity. WPF/tray reuse the existing
native PNG raster, checking both source and render digests against the existing
render receipt. The SVG and Mobile artwork were not edited. State mapping covers
idle, attentive, listening, thinking, speaking, waiting and error. No expressive
faces, simulated telemetry or Slice 13 motion system was added.

## Context, capture and insertion

Every context record has a typed source, ID, observation timestamp, scope,
provenance, permission state and freshness horizon. RAM-only capture expires after
15 seconds for execution purposes. Owner review rechecks freshness and grants.
No context capture runs on a background timer. Snapshot polling reads shared Core
task/node metadata, not app contents.
Attached private context uses the existing Model Router's Private mode, which
restricts reasoning to its eligible local/private providers. It cannot become an
external live-search query. An absent private provider remains BLOCKED; there is
no implicit cloud fallback. Typed Ask without an attachment follows the existing
Core routing policy.

- `GetForegroundWindow`, `GetWindowThreadProcessId` and `GetWindowTextW` observe
  explicitly requested foreground metadata.
- Content capture requires a registered/bound Worker app/window, validated
  executable, non-password accessible element and a separate `desktop:perceive:*`
  grant. UIA identity is read before content. Foreground identity is rechecked.
- UIA `TextPattern.GetSelection` reads structured selection. Empty or
  unsupported selection is unavailable. No screenshot is used to guess it.
  Selection-only capture does not read the whole document. This adapter therefore
  offers selected-text transformation previews to the surface/explicit clipboard;
  reliable in-app replacement requires an explicitly captured full focused field.
- Explicit focused-field capture can use the foreground element or a chosen
  registered `(handle, pid, runtime_id)` destination. Empty writable fields are
  supported. Hidden, password, unrelated and oversized content fails closed.
- Application uses **ValuePattern only**. `set_text_checked` compares the entire
  captured value immediately before `SetValue`. It never uses coordinates or a
  keyboard fallback. Selected-range replacements require matching structured
  offsets. Dictation appends to the reviewed captured value; it does not erase it.
- Unsupported reliable insertion offers explicit interaction-surface or clipboard
  choices. Clipboard write/readback requires `desktop:clipboard` independently;
  no startup/polling read of the owner's clipboard occurs.
- Browser/file/node/image context source types are represented, but this capture
  adapter does not advertise those captures. Browser, files, terminal, Git and
  installed-app action plans continue to use their existing Worker capabilities.
  Screenshot/image capture is not implemented or silently substituted.

`CAN PERCEIVE`, `CAN RETAIN` and `CAN ACT` are separate. There is no desktop
retention grant by default. Private selected text, clipboard text, transformations
and destination values never enter objectives, plans, action rows, result/dedup
rows or Memory Fabric automatically. Runtime's opt-in transient path persists
only metadata and a payload digest; private inputs/results/criteria stay in the
Core process's bounded RAM. Dispatcher resolves them only after durable action
identity, grants and payload integrity checks. Arbitrary private errors/artifacts
are not persisted. Existing non-transient Runtime behavior remains unchanged.

Restart loses private content, so a pending private task blocks instead of replaying.
Discard removes finished private interactions/contexts/previews while preserving
shared task/ledger metadata. Active work is cancelled through Core. Explicit file
actions may intentionally persist an owner-reviewed artifact in their scoped
workspace; that action does not promote its contents into canonical memory.

The private path currently requires the trusted Core/Dispatcher composition to
share a Store object. Independent remote Worker stores cannot resolve its private
payload and fail closed. This limitation is not hidden by cloud or deployment claims.

## Authority, continuity and ownership

Owner enrollment is a trusted composition API, never an HTTP operation. WPF's
ephemeral RSA key and scoped session bootstrap travel through inherited stdin,
not command-line arguments, files or logs. The key is imported into Windows CNG.
Challenges are session/node/operation/target/digest/expiry bound and single-use;
changed tasks/plans/signatures, revoked grants and replay are rejected. The native
review displays operation, target, capability, reason, consequence, policy and
current state plus the private parameters being reviewed. It creates no permanent
grant. Desktop-specific Personal Policy is rechecked as `source=desktop`.
Capabilities marked critical are not admitted without a later strong-approval
implementation/acceptance. This trusted local surface is not a hostile-host sandbox.

Grid stores expiring, generation-fenced interaction ownership. Text applications
bind ownership to one task, recheck before approval and again at Dispatcher, and
hold it during bounded execution. No conflicting second application is admitted;
executor loss leaves an expiring lease. Voice capture also claims shared ownership.
These claims do not grant perception/action authority.

Desktop tasks are ordinary Core tasks, visible on Mobile with its target inspect
grant even before execution. Disconnecting a surface does not alter task truth.
Mobile's existing own-plan approval boundary remains intact; cross-surface approval
transfer and real phone continuation are later owner acceptance, not a new grant.
No private desktop chat history, memory store or task scheduler exists.

Core/Worker loss withdraws interaction/executor capability. UI errors show degraded
UNKNOWN and require inspection before retry; nothing is fake-queued for later.
UIA readback unavailable after a mutation produces UNKNOWN; mismatched readback
fails. A bounded eight-second read-only verification window accommodates
asynchronous accessibility publication; the mutation is never retried.
Model-only responses remain REPORTED/partially verified.

## Invocation and voice

Native `RegisterHotKey`/`WM_HOTKEY` with `MOD_NOREPEAT`, default Ctrl+Alt+O,
invokes the compact presence. Modifier bits/key are configurable in the launcher.
Registration failure reports a collision/unavailable shortcut and retains tray/
presence clicks. No low-level keyboard/mouse hook is installed. Exit unregisters
the shortcut and disposes tray/key/audio resources.

Context source defaults to none. Choosing selection/focused/window on invocation
authorizes only that explicit requested capture, before OSCAR takes focus. The
attached source/content and permission/freshness are visible and discardable.

`DesktopVoice` accepts an explicitly installed Slice 08 capture/Recognizer adapter
(for example prepared `SoundDeviceCapture` and `FasterWhisper`). Push/release-to-talk
or keyboard Space on its native button captures at most 15 seconds, then a final
transcript becomes a Dictate preview. The adapter defaults to local recognition,
keeps no recordings and opens no device merely by importing/launching the UI.
The reference launcher has no voice adapter: it displays BLOCKED honestly.
Prepared models, microphone/output device routing, real-room AEC/barge-in/self-wake,
playback/naturalness and owner calibration remain independent Slice 08/Gate C
acceptance. No new voice model was researched and no physical voice PASS is claimed.

## Running the reference

From the repository root with its existing Python environment and optional
`mobile` extra available:

```powershell
python -m scripts.desktop_reference
python -m scripts.desktop_reference --hotkey-modifiers 3 --hotkey-key 79
python -m scripts.desktop_reference --self-check
python -m scripts.desktop_windows_reference
python -m unittest tests.test_desktop -v
```

The launcher visibly labels **REFERENCE / temporary Core**. It uses a disposable
database/workspace and scoped math/file capabilities, not owner credentials or
device enrollment. A trusted enrolled composition calls
`run_surface(core: Desktop, session: SessionHandle)` using its existing Runtime,
policy, Worker targets and optional WindowsContext/Voice adapters. No owner grant
is inferred from running the disposable reference.

UIA uses the source-anchored `oscar/windows_uia.ps1`, shipped as package data.
Private payloads cross a bounded anonymous stdin pipe. This removes Windows
command-length limits and private text from process command lines. Worker Job
Object timeout, cancellation and process-tree cleanup remain authoritative.

Reference checks render WPF and exercise Windows CNG→Core PSS signatures, real
registered WPF field capture, signed Dictate application through InteractiveWorker,
independent UIA readback, 8192-character Unicode pipes, stale-write rejection and
database content absence. They never operate the owner's applications/clipboard
or open a microphone. The render is visually inspected separately from those APIs.
Hosted cold-start preparation has a bounded 60-second reference deadline and may
retry read-only fixture discovery before any action. Individual observer calls
remain bounded to 15 seconds; mutation retries are never used to obtain a PASS.

See [reference evidence](evidence/desktop-reference-2026-10-07.json).
Exact-head CI is authoritative in the draft PR's checks and includes the new
Windows workflow alongside all existing repository, Core, Edge, Voice and Mobile
workflows. Remote CI success is not local owner/device acceptance.

## Next genuine owner/manual boundary

Review the draft; do not merge automatically. Owner acceptance must exercise:
normal presence/tray/hotkey collision and cleanup; intended real app registration;
foreground selection/focus and inaccessible/sensitive fields; Ask with a permitted
prepared provider; Dictate/Edit preview and destination readback; explicit clipboard
with owner state preservation; approvals/revocation; cancel/restart/reconnect and
UNKNOWN handling; eligible Mobile inspection/control of the same Core tasks;
explicit microphone and audio routing with the consolidated Voice harness.

Physical Edge/Voice/Mobile status is still deferred, so **Gate C is PARTIAL**.
Slice 11, 09R, deployment, Home Node and post-alpha work do not start here.
