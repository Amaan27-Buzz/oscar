# 10R.0 — Desktop engineering UI baseline

Starting head: `5f46f8b195ab557c85d66dec70eddf665cd3e3de`.
This set records the existing engineering/reference interface. **No UI redesign
was performed.** Existing layout, CSS, typography, Orb and product components
are preserved. Screenshots are synthetic presentation evidence, not capability,
owner, microphone or physical-device acceptance.

See the [complete visual inventory](inventory.md) and
[per-image manifest](baseline/manifest.json). The inventory table includes all
52 PNGs: 47 required states, two additional Act families and three 125% DPR views.
Every entry records source, state, logical viewport, physical PNG dimensions,
controls, backend state represented, capture method, native UI and limitations.
Hashes protect the receipt without creating pixel-perfect regression tests.

## Visual inventory

<!-- inventory:start -->
| ID | Screenshot | Surface | State | Why it exists |
|---|---|---|---|---|
| 00-tray-menu | [PNG](baseline/00-tray-menu.png) | Tray | actual Windows fixture UI | Inspect existing state composition |
| 01-compact-idle-125pct | [PNG](baseline/01-compact-idle-125pct.png) | Presence | connected idle | Inspect existing state composition |
| 01-compact-idle | [PNG](baseline/01-compact-idle.png) | Presence | connected idle | Inspect existing state composition |
| 02-compact-active | [PNG](baseline/02-compact-active.png) | Presence | running with owner attention | Inspect existing state composition |
| 03-compact-offline | [PNG](baseline/03-compact-offline.png) | Presence | Core unavailable | Inspect existing state composition |
| 10-ask-empty | [PNG](baseline/10-ask-empty.png) | Ask | empty | Inspect existing state composition |
| 11-ask-context | [PNG](baseline/11-ask-context.png) | Ask | attached explicit context | Inspect existing state composition |
| 12-ask-working | [PNG](baseline/12-ask-working.png) | Ask | running | Inspect existing state composition |
| 13-ask-result-reported | [PNG](baseline/13-ask-result-reported.png) | Ask | reported response | Inspect existing state composition |
| 14-ask-result-verified | [PNG](baseline/14-ask-result-verified.png) | Ask | verified result | Inspect existing state composition |
| 15-ask-unknown | [PNG](baseline/15-ask-unknown.png) | Ask | unknown outcome | Inspect existing state composition |
| 20-dictate-idle | [PNG](baseline/20-dictate-idle.png) | Dictate | idle | Inspect existing state composition |
| 21-dictate-listening | [PNG](baseline/21-dictate-listening.png) | Dictate | listening fixture | Inspect existing state composition |
| 22-dictate-processing | [PNG](baseline/22-dictate-processing.png) | Dictate | processing fixture | Inspect existing state composition |
| 23-dictate-preview | [PNG](baseline/23-dictate-preview.png) | Dictate | final transcript preview | Inspect existing state composition |
| 24-dictate-destination | [PNG](baseline/24-dictate-destination.png) | Dictate | explicit clipboard choice | Inspect existing state composition |
| 30-edit-context | [PNG](baseline/30-edit-context.png) | Edit | fresh focused context | Inspect existing state composition |
| 31-edit-working | [PNG](baseline/31-edit-working.png) | Edit | transform running | Inspect existing state composition |
| 32-edit-before-after-125pct | [PNG](baseline/32-edit-before-after-125pct.png) | Edit | before/after review | Inspect existing state composition |
| 32-edit-before-after | [PNG](baseline/32-edit-before-after.png) | Edit | before/after review | Inspect existing state composition |
| 33-edit-destination | [PNG](baseline/33-edit-destination.png) | Edit | captured field choice | Inspect existing state composition |
| 34-edit-unsupported | [PNG](baseline/34-edit-unsupported.png) | Edit | reliable insertion unavailable | Inspect existing state composition |
| 40-act-files | [PNG](baseline/40-act-files.png) | Act | bounded file write | Inspect existing state composition |
| 41-act-git | [PNG](baseline/41-act-git.png) | Act | Git operations | Inspect existing state composition |
| 42-act-powershell | [PNG](baseline/42-act-powershell.png) | Act | typed PowerShell | Inspect existing state composition |
| 43-act-browser | [PNG](baseline/43-act-browser.png) | Act | isolated browser | Inspect existing state composition |
| 44-act-apps | [PNG](baseline/44-act-apps.png) | Act | registered application | Inspect existing state composition |
| 45-act-no-capability | [PNG](baseline/45-act-no-capability.png) | Act | no advertised capability | Inspect existing state composition |
| 46-act-terminal | [PNG](baseline/46-act-terminal.png) | Act | fixed registered program version | Inspect existing state composition |
| 47-act-worker-tools | [PNG](baseline/47-act-worker-tools.png) | Act | Worker tools discovery | Inspect existing state composition |
| 50-activity-empty | [PNG](baseline/50-activity-empty.png) | Activity | empty | Inspect existing state composition |
| 51-activity-running | [PNG](baseline/51-activity-running.png) | Activity | running and selected progress | Inspect existing state composition |
| 52-activity-mixed | [PNG](baseline/52-activity-mixed.png) | Activity | mixed shared task truth | Inspect existing state composition |
| 60-approval-standard-125pct | [PNG](baseline/60-approval-standard-125pct.png) | Approval | standard owner review | Inspect existing state composition |
| 60-approval-standard | [PNG](baseline/60-approval-standard.png) | Approval | standard owner review | Inspect existing state composition |
| 61-approval-detailed | [PNG](baseline/61-approval-detailed.png) | Approval | exact detailed review | Inspect existing state composition |
| 62-native-owner-confirmation | [PNG](baseline/62-native-owner-confirmation.png) | Native confirmation | actual Windows fixture UI | Inspect existing state composition |
| 70-context-none | [PNG](baseline/70-context-none.png) | Context | none | Inspect existing state composition |
| 71-context-selection | [PNG](baseline/71-context-selection.png) | Context | selection | Inspect existing state composition |
| 72-context-focused | [PNG](baseline/72-context-focused.png) | Context | focused field | Inspect existing state composition |
| 73-context-window | [PNG](baseline/73-context-window.png) | Context | foreground metadata | Inspect existing state composition |
| 74-context-stale | [PNG](baseline/74-context-stale.png) | Context | stale | Inspect existing state composition |
| 75-context-denied | [PNG](baseline/75-context-denied.png) | Context | permission denied | Inspect existing state composition |
| 76-context-unavailable | [PNG](baseline/76-context-unavailable.png) | Context | structured selection unavailable | Inspect existing state composition |
| 80-invocation | [PNG](baseline/80-invocation.png) | Invocation | shortcut registered | Inspect existing state composition |
| 81-shortcut-collision | [PNG](baseline/81-shortcut-collision.png) | Invocation | registration collision | Inspect existing state composition |
| 90-core-unavailable | [PNG](baseline/90-core-unavailable.png) | Degraded | Core unavailable | Inspect existing state composition |
| 91-worker-unavailable | [PNG](baseline/91-worker-unavailable.png) | Degraded | Worker unavailable | Inspect existing state composition |
| 92-capability-withdrawn | [PNG](baseline/92-capability-withdrawn.png) | Degraded | capability withdrawn | Inspect existing state composition |
| 93-request-rejected | [PNG](baseline/93-request-rejected.png) | Degraded | Core rejected request | Inspect existing state composition |
| 94-stale-context | [PNG](baseline/94-stale-context.png) | Degraded | stale context rejected | Inspect existing state composition |
| 95-offline-discard | [PNG](baseline/95-offline-discard.png) | Degraded | offline local discard | Inspect existing state composition |
<!-- inventory:end -->

## Lifecycle findings and behavior

The previous product did **not** automatically exit solely because bootstrap was
missing: an ordinary launch with closed stdin remained alive during investigation.
The following coupled paths made inspection unreliable:

- Core bootstrap was read unconditionally from inherited stdin; normal expanded
  startup was behind that read. An ordinary interactive stdin could wait forever.
- Close requests had no hide/preserve handler. Destroying the only product window
  removed the target that tray/shortcut reveal expected to reuse.
- The explicit `--reference-check` path intentionally ended the native process
  after its checks; it is a test harness, not the normal product launch.
- The debug executable used the Windows console subsystem (PE value 3), coupling
  GUI lifetime to console closure. Debug and release product executables now use
  the GUI subsystem (PE value 2); reference bootstrap/output use explicit pipes.

The owner's particular opening/closing incident was not independently reproduced
with its original invocation. These mechanisms were identified from the actual
entry path; no missing-bootstrap process-exit cause is invented.

Normal product launch now ignores stdin and remains uncommissioned/degraded until
trusted enrollment is supplied. Window close/Alt+F4 hides the same window and keeps
OSCAR/tray alive. Open OSCAR, tray click or registered global shortcut reveals it.
Compact presence changes the existing window mode. Hide OSCAR hides it. Quit is
explicit process termination. Genuine failures remain failures.

`scripts.desktop_tauri` explicitly opts into `--bootstrap-stdin` for its disposable
Core. Credentials/key authority remain native; no permanent test credential is
introduced. Self-check is debug-only and deliberately terminates when finished.
Missing/malformed bootstrap in a non-check launch does not terminate the shell.

The Windows lifecycle check exercises ordinary no-bootstrap startup/close/hide,
then the real close handler, shared tray/shortcut reveal function and explicit
quit path with no Core. Owned-process cleanup is distinguished from product Quit.

## Reproduce

With Windows/WebView2, the existing Python environment, Node LTS/Rust/MSVC, the
repository's optional Playwright browser extra and Pillow available:

```powershell
python -m scripts.build_desktop --checks
python -m scripts.desktop_baseline --lifecycle-only
python -m scripts.desktop_baseline
```

The capture command owns its Vite process and isolated browser, refuses to attach
an existing port-1420 server, and never commissions Core. The development-only
`?showcase=<inventory ID>` route dynamically imports typed fixtures and renders
the real `App`/`Act`. Its port rejects execution. It has no native IPC, credential,
provider, filesystem, owner application or microphone path. Production Vite
bundles remove that route and fixture module; the build checks their absence.
Native capture/check CLI flags are gated by Rust debug assertions and absent
from release behavior.

For individual fixture inspection:

```powershell
cd desktop
npm run dev
# Open http://127.0.0.1:1420/?showcase=32-edit-before-after
```

## Dimensions and capture evidence

| Window mode | Logical viewport |
|---|---|
| Compact | 300 × 126 |
| Interaction | 580 × 760 |
| Approval | 620 × 780 |
| Activity | 820 × 780 |

These are current baseline dimensions, not future design targets. React captures
use Windows Chromium at DPR 1 and PNG full-scroll-content capture: physical image
height may exceed viewport height so below-fold controls remain visible. They
render real components but are not a WebView2 screenshot/device acceptance claim.
The three `-125pct` images emulate DPR 1.25 without changing owner display settings.
Actual native menu/dialog captures use the host's Windows scale (125% in this run).
Their dimensions include native framing; PrintWindow can show black invisible
resize-border pixels around the dialog. No product content is cropped.

`24` and `33` show distinct selected destinations; native select-popup chrome is
not fabricated or composited into the React screenshot. Options come from the
typed preview fixture. `75`/`76` show existing notice/no-attachment behavior,
because dedicated permission-denied/unavailable panels do not exist. `95` preserves
verified task metadata after local private contents are discarded.

## Native Windows capture and manual alternatives

`00-tray-menu.png` is the **same actual native menu attached to the tray**, opened
at OSCAR's own window via Tauri for deterministic capture. Notification-area
positioning, tray overflow placement and an actual taskbar-anchored invocation
were not automatically captured. No fake WebView menu is used.

To capture the taskbar-anchored variant manually, launch:

```powershell
.\desktop\src-tauri\target\debug\oscar-desktop.exe
```

Right-click OSCAR's actual notification-area icon (use Windows tray overflow if
hidden), then Win+Shift+S and save only the menu as
`docs/ui/desktop/baseline/00-tray-menu-manual.png`. Do not include personal taskbar
notifications. Record it as manual in the manifest if adding it to the baseline.

`62-native-owner-confirmation.png` is the actual product Windows MessageBox using
a synthetic review. It cannot sign or execute: the debug path has no Core/client,
credentials or signing key. For manual recapture:

```powershell
.\desktop\src-tauri\target\debug\oscar-desktop.exe --baseline-dialog
```

Capture only the dialog with Win+Shift+S to
`docs/ui/desktop/baseline/62-native-owner-confirmation-manual.png`, dismiss with No,
then use tray Quit. No owner approval or Windows Hello acceptance is implied.

## Surfaces that do not exist

No full Settings screen, production commissioning UI, chat-history manager,
expressive Slice 13 faces, audio-device settings, microphone permission dialog,
Windows Hello confirmation, screenshot/image-context picker, remote approval
transfer UI or general unrestricted terminal exists. Unsupported insertion uses
current notices and destination choices. No new screens were invented to fill
this inventory.

## Validation and stop boundary

**LOCAL PASS / REMOTE CI NOT EXECUTED DUE ACCOUNT BILLING LIMIT**.
Local validation covers typed fixture rendering, all PNG/manifest records,
production fixture exclusion, actual native lifecycle and existing Core/Worker/
UIA references. Remote billing blockage is not reported as a code failure.
The full Python suite passed 527 checks (six optional prepared voice-model skips),
plus six Rust and seven frontend checks. Some native reference attempts returned
UNKNOWN UIA readback; subsequent isolated normal runs passed signed apply/readback
and restart. Those failures were not promoted to success, no ambiguous mutation
was replayed, and Core's observer timeout/fail-closed semantics were not changed.
Normal owner UIA reliability remains a separate acceptance boundary.
The existing Mobile JVM/Core loopback regression also passed. A supplementary
Android APK rebuild could not fetch the pinned Gradle distribution (network
connection timeout); it did not reach compilation. Android emulator and Linux
firmware cross-build jobs were not run locally. Those unchanged platform-matrix
checks remain required when remote CI becomes available; they are not claimed
as local PASS or physical acceptance.
Exact-head CI must run after billing restoration and before final Slice 10
integration. PR #16 stays draft/unmerged, Gate C PARTIAL. No Slice 11 or redesign
sub-slice is started beyond this authorized 10R.0 baseline work.
