# Slice 12.1 — Living Desktop Presence

**2026-10-11 corrective candidate:** see the [quality recovery review package](quality-recovery/README.md).
The original captures and assessments below are historical and preserved.

**LOCAL OWNER-REVIEW CANDIDATE / DEFAULT UI UNCHANGED.**
Built from clean `b9d3e049aef5148a10c710626b9e6b06771c9229` on
`codex/slice-12-1-living-presence`, isolated in `oscar-desktop-presence`.
Review date: 2026-10-10. No push, PR merge, CI result or production promotion.

Start with [before/after](before-after.png), the [review sheet](review-sheet.png), [native interaction](native-invoked.png),
[verified answer](native-verified.png) and [rendered window sequence](native-invoke-retreat-reinvoke.gif).
The sheet uses explicitly synthetic operational states. Native files use a real,
authenticated disposable Core and real Tauri/WebView2, not fabricated implementation evidence.

## Review paths

| Experience | Evidence |
|---|---|
| Previous actual compact UI | [integration baseline](../integration/native-available.png) |
| Historical A/B/C concepts | [historical sheet](../explorations/10R.1/contact-sheet.png) |
| Compact rest | [native HWND](native-idle.png), [WebView alpha](native-idle-alpha.png) |
| Attentive/invoked | [native screenshot](native-invoked.png) |
| Executing appearance | [synthetic executing render](fixture-working-expanded-1.png) |
| Actual active executor awaiting result | [native readback](native-awaiting-result.png) |
| Approval attention | [native screenshot](native-approval.png) |
| Completed answer | [native verified 5](native-verified.png) |
| Offline / restored | [offline](native-offline.png), [restored](native-restored.png) |
| Invoke → interrupted retreat → reinvoke → rest | [native rendered sequence](native-invoke-retreat-reinvoke.gif) |
| Retreat | [native content recording](native-retreat.gif) |
| Reduced motion / contrast | [reduced motion](reduced-motion.png), [forced colors](forced-colors.png) |

The shared adapter labels `awaiting_result` as Waiting, rather than claiming an
executor is still executing on every readback. The executing pose has a labelled
synthetic fixture. Speaking/listening are synthetic here: no audio commissioning,
prosody synchronization or microphone use is claimed.

## Try it locally

Use Node LTS 24.21.0 and Rust 1.99.0. Dependencies and binaries are already built
in this worktree. Keep the Vite server on its owned localhost port 1420:

```powershell
cd D:\TheDawnlightGroup\DawnlightLabs\oscar-desktop-presence\desktop
npm run dev
```

The non-executing browser review is `http://127.0.0.1:1420/?living=preview`.
Choose a labelled fixture, click the Orb, type, press Escape and reinvoke.
Fixtures reject execution, approval and native window commands.

For the actual native prototype, in a second terminal:

```powershell
cd D:\TheDawnlightGroup\DawnlightLabs\oscar-desktop-presence
cargo +1.99.0 build --manifest-path desktop/src-tauri/Cargo.toml --locked --no-default-features
& .\desktop\src-tauri\target\debug\oscar-desktop.exe --living-presence
```

This starts **uncommissioned/offline**. It cannot fabricate an online state.
Authenticated connection uses the existing native `--bootstrap-stdin` contract;
no credentials enter React. The reproducible disposable-Core acceptance is:

```powershell
python -m scripts.desktop_living_review
```

Do not run native acceptance harnesses concurrently: they share the Windows
global shortcut. The debug development build is required for the candidate.
A bundled custom-protocol build correctly denies localhost IPC; its normal
production frontend excludes the presence and fixtures. Release builds ignore
the prototype flag and reject the added bounded window command.

## Interactions

- Orb click / Enter / Space invokes the interaction. Native Ctrl+Alt+O and tray
  Open reveal it; the input receives focus when available.
- Enter submits Ask; Shift+Enter adds a line. Core decides work, authority and
  evidence. Requests are neither queued offline nor labelled Working from local busy state.
- Real tasks displace the composer. An asynchronous removal of a focused input
  recovers keyboard focus locally; background attention does not steal OS focus.
- Review opens existing exact approval material and native confirmation/signing.
  Opening the surface grants nothing. No approval pane redesign.
- Escape or Orb click retreats, preserving the draft and running tasks. Reinvocation
  interrupts retreat; a failed resize restores the open surface.
- Presence menu exposes explicit Pin on top / Unpin, To screen edge and Hide to
  tray. Drag the expanded OSCAR header for floating placement. Native tray Quit
  remains the exit; ordinary close hides.
- Completed values appear as a bounded, evidence-labelled excerpt. Inspect result
  opens the existing workspace; Ask again restores the draft/input.

## Evidence boundaries

Native HWND dimensions are **132×148 logical / 165×185 physical** at real 125%
scale; interaction is **432×384 / 540×480**. Native window resizing, focus recovery,
pin/float/edge request success, close/hide and shortcut restoration passed locally.
100%/125%/150% browser DPR and scaled/negative-coordinate work-area unit tests are
separate from actual OS scaling changes. Multiple monitors and alternate taskbar
configurations were not exercised on hardware.

`PrintWindow` paints transparent regions black in the HWND screenshots. The alpha
PNG verifies WebView alpha 0–255. A separate Windows screen-compositor capture over
an owned backdrop was inconclusive because the target could not be foregrounded;
wallpaper compositing, click footprint, fullscreen and owner-desktop quality need
owner review. No blur or DWM shadow effect is promised. The native window is a
rectangle; transparent margins are not promised to be click-through.

GIFs contain actual rendered WebView frame captures aligned at the bottom right
on a fixed neutral canvas. They are not an OS desktop recording. The receipt
distinguishes sampled frames from distinct encoded GIF frames.

Native idle measurement found **0 puck attribute mutations over 1.2 seconds**;
the shared renderer stops animation frames after settling. Native scheduling
samples were median 6.1ms / p95 6.3ms in this run; this is browser frame scheduling,
not whole-process CPU/GPU profiling or a universal frame-rate guarantee.

Owner visual acceptance, wallpaper/fullscreen behaviour, real speech/listening,
other native DPI and multi-monitor acceptance, and remote exact-head CI are not
complete. GitHub access restriction is owner-reported; no remote bypass was attempted.
Stop here for visual review. Slice 12.2 is not started.

See [direction/research](BRIEF.md), [validation receipt](receipt.json),
[native receipt](native-receipt.json) and [review/limitations](REVIEW.md).
