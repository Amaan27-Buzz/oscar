# 10R.1 — Compact presence exploration

Three working, development-only concepts for owner visual review. No direction
is selected or promoted. PR #16 remains draft and unmerged. 10R.2 and Slice 11
are not started. Gate C and owner acceptance status are unchanged.

## Evidence and isolation

Starting branch: `club-d2/slice-10-desktop` at
`005ad3593879fd3d967bc920e7ee77bb12d40964`.
The 10R.0 compact screenshots and actual native tray-menu capture were inspected.
The manifest's older capture SHA is historical baseline evidence; current
`App.tsx`, styles and typed fixtures were inspected as the implementation truth.

All PNGs are actual Windows Chromium renders at the proposed logical viewport,
DPR 1, without full-page enlargement. They include 12 px of opaque neutral
backing around the shell to contain the CSS shadow. This is **SIMULATED
PRESENTATION**, not a transparent native window or WebView2/device acceptance.
The contact sheet places the original captures at 1:1 pixels. Additional images
emulate DPR 1.25, forced colors and reduced motion together; they do not change
Windows display settings.

`manifest.json` records dimensions, hashes, Orb identity and browser checks.
`transitions.gif` samples the working browser at 10 fps playback: idle → active →
waiting → offline → recovery → existing interaction expansion, for A/B/C.
It is an animation preview, not a frame-rate or native performance benchmark.

The dev-only `?presence=` route is tree-shaken out of production. It reuses
`View`, `Task`, status labels, compact baseline fixtures and the existing `App`.
Expansion uses an injected port that permits fixture readback/window selection
and rejects every execution command. No native event subscription, credential,
Core mutation, microphone or owner application is accessed. Capture permits only
loopback requests and refuses to attach to an existing port-1420 server.

Production `App`, `Act`, `style.css`, native window config/code and the canonical
Orb bytes are unchanged. Core, Runtime, Grid, permissions, signing, context,
Voice and Worker code are unchanged. No dependency was added.

## State and interaction contract

Idle is an online fixture with no tasks. Active reuses the baseline's executing
task plus a separate planned task exposing `approve`: **one task runs, one needs
review**. No simulated progress percentage or result is invented. Review opens
the existing interaction fixture; it never grants approval.

Waiting is an `awaiting_result` fixture with no approval action and no busy
animation. Offline deliberately retains stale active task records, suppresses
all current work/review claims and stops work motion. It says Core unavailable;
it does not claim cancellation, completion or continued execution. Recovery
comes only from choosing an online fixture, never a timed fake reconnect.

Every concept has an Orb opener, hover/press response, visible keyboard focus,
polite status announcements and Escape to compact with focus restoration.
Expansion shows the existing interaction UI, not a 10R.2 redesign. Native View
Transitions move the intact Orb between compact and interaction positions when
supported; ordinary CSS geometry transitions provide a fallback. Reduced motion
disables motion and preserves all controls. State controls in `&tools` are
explicitly labeled synthetic and sit outside the product object.

Dormant `data-signal` styling covers listening, thinking, speaking, waiting,
error and muted. There is no waveform, audio capture, TTS, face manipulation or
Slice 13 expressive system. Future runtime binding must use authoritative state.

## Concept A — Ambient Presence

**224 × 188 logical px** in all compact states; shell **200 × 164**.

A vertical perch: the intact Orb is the center of gravity, with OSCAR and one
short state line beneath. No permanent Open arrow or utility strip. A narrow
mark communicates work; a review control appears only for the approval fixture.
The whole Orb target opens interaction. It is still at idle; work shifts the
whole image by 2 px with a small weighted rotation. Offline settles lower and
stops animation while preserving identity.

Implementation complexity is low: one fixed shell and conditional attention.
Strengths: recognizable, calm, few controls, large 76 px Orb target. Weaknesses:
greater vertical footprint, little task context, Orb opening is less discoverable
than a labeled button (tooltip and accessible name help). Its status text is
12 px; verify readability on the owner's screen before promotion.

Suggested placement: free-standing near a side edge with breathing room. It
does not anchor itself, snap to edges or implement native dragging. An opaque
rectangle is the dependable current Tauri fallback; shaping the window to this
rounded object requires separate hit-test/shadow/monitor verification.

Screenshots: [idle](concept-a-idle.png), [active](concept-a-active.png),
[offline](concept-a-offline.png).

## Concept B — Living Instrument

**344 × 156 logical px** in all compact states; shell **320 × 132**.

A horizontal instrument: Orb seated to the left, small identity above a larger
state reading, explicit expansion arrow to the right. A fine rule separates the
state reading from a narrow work/availability strip and conditional review
control. Geometry stays stable; task motion remains confined to the Orb and
short activity mark. Waiting suspends the motion; offline changes material
slightly and shows Inspect before retry.

Implementation complexity is low. Strengths: stable target positions, clear
state hierarchy, most predictable native sizing, dedicated expansion control.
Weaknesses: larger permanent footprint, more utility-like than A, small 11 px
supporting text. The contrast is deliberately stronger than the canonical
Graphite token for these small operational labels.

Suggested placement: freely positioned above the taskbar or near an edge,
keeping a safe work-area inset. No taskbar anchoring is implemented. The current
opaque undecorated Tauri window can accommodate the rectangle; CSS contact
shadow is not proof of Windows DWM shadow. Arrow target is 32 × 36 px; Orb
target is 68 × 68 px. Focus and text carry meaning without color or animation.

Screenshots: [idle](concept-b-idle.png), [active](concept-b-active.png),
[offline](concept-b-offline.png).

## Concept C — Adaptive Presence

**192 × 112 idle**, **364 × 164 active/waiting or attention**, **304 × 156 offline**;
shells **168 × 88**, **340 × 140**, **280 × 132**, respectively.

A small horizontal presence at idle. Work enlarges the same object, adds an
expansion arrow, a shared-task line and an activity/review strip. Offline keeps
enough room for Execution status unknown and Inspect before retry. The Orb and
status stay in a continuous spatial relationship through native browser view
transitions and a 420 ms shell resize fallback. No percentage is fabricated.

Implementation complexity is medium: state-derived dimensions plus expansion
continuity. Strengths: smallest idle footprint, clear attention surface when
needed, strongest state transformation. Weaknesses: changing geometry can
obstruct nearby content; targets move, especially when expanding near a screen
edge. Idle secondary text is 11 px; requires owner readability review.

Suggested placement: future right/bottom anchoring with resize preserving that
corner, bounded by monitor work area. This browser study resizes from top-left;
it does not claim native anchoring or clamping. A promoted native implementation
must recalculate work area and logical/physical conversion on DPI/monitor changes,
and must not animate OS window size blindly. Keyboard, forced-color and reduced
motion behavior are implemented; geometry animation is not required for use.

Screenshots: [idle](concept-c-idle.png), [active](concept-c-active.png),
[offline](concept-c-offline.png).

## Comparison and recommendation

| Property | A — Ambient | B — Instrument | C — Adaptive |
|---|---|---|---|
| Composition | Vertical Orb perch | Horizontal reading + utility strip | Small row → task surface |
| Idle occupation | 224 × 188 | 344 × 156 | 192 × 112 |
| State prominence | Restrained | Immediate typographic reading | Context-dependent geometry |
| Opening | Orb | Orb or explicit arrow | Orb; arrow after expansion |
| Native promotion complexity | Low, unless shaped | Lowest | Medium; anchor/clamp work required |
| Primary tradeoff | Less context/discoverability | Permanent footprint | Moving geometry/targets |

**Recommend C for owner consideration**, because it most closely joins quiet
idle presence to a useful attention surface. B is the strongest alternative if
stable geometry and immediate legibility matter more. A is appropriate if the
owner wants presence to dominate utility. This recommendation selects nothing;
all concepts remain isolated and screenshots are preserved for later GPT Image
exploration. Owner visual review is the next boundary.

## Windows limitations and acceptance still required

No native window behavior changed. No transparency, acrylic, backdrop blur,
click-through, snapping, edge anchoring or Windows shadow was implemented or
claimed. Native title/menu/close/hide/tray semantics remain the 10R.0 behavior.
An isolated browser shell clamps width to the viewport and allows scrolling if
the containing viewport is smaller; it does not manage native monitor bounds.
Window movement should remain explicit, and control areas must not become drag
regions. Native drag region, multi-monitor boundaries, high-DPI rounding,
WebView2 View Transition support and owner screen readability require later
scoped testing before promoting a chosen concept.

CSS width/height transitions are deliberate for this bounded prototype. The
design detector flagged them (and the small state mark's width transition).
View Transition snapshots reduce visible discontinuity, but no sustained frame
rate or low-power measurement is claimed. No remote CI PASS is claimed; the
owner reported billing limits and workflows were not repeatedly rerun.

## Reproduce and review

From the repository root:

```powershell
python -m scripts.desktop_presence
```

For interactive browser review:

```powershell
cd desktop
npm run dev
# http://127.0.0.1:1420/?presence=a&tools
# Change Concept and Synthetic state. Click the Orb; Escape returns.
```

The clean URLs omit controls, e.g. `?presence=c&state=active`.
Deleting `desktop/src/presence/`, its guarded loader branch, this capture script
and exploration artifacts removes the experiment. Promotion is a separate
owner-authorized change, not a query-parameter switch in production.

## Validation

- TypeScript checking: PASS.
- Frontend: 11 tests across 3 files PASS, including 4 exploration contracts.
- Frontend production build: PASS; exploration JS/CSS and fixtures absent.
- Existing desktop/Core-boundary and baseline regressions: 31 tests PASS.
- Capture: all 9 PNG viewport sizes, nonblank content, visible-control/text fit,
  state identities and hashes checked; contact sheet and GIF generated.
- Browser: A/B/C state transitions, work-stop on waiting/offline, keyboard
  expansion/Escape/focus restoration PASS; no page errors or external requests.
- Emulated DPR 1.25, reduced motion and forced colors: PASS for A/B/C.
- Python capture/build script lint and formatting: PASS.
- Rust checks: not required; no native code/window behavior changed.
- Native owner acceptance, multi-monitor/DPI device behavior and remote CI: NOT RUN.

[Contact sheet](contact-sheet.png) · [Animation preview](transitions.gif) ·
[Capture manifest](manifest.json)

## Final review handoff

The fresh finish reviewer inspected all nine captures and requested one material
fix: A's active review control needed more bottom inset. A retained 224 × 188;
its Orb target/image became 76/70 px and top padding decreased by 3 px. After
recapture, the reviewer scored that fix **RESOLVED / SHIP AS BROWSER
EXPLORATIONS**. This verdict covers the listed fix, not native acceptance or a
winner selection. The documentation reviewer checked implementation, PNG
dimensions/hashes and Orb identity against this document; no mismatch required
a documentation change. Neither reviewer independently benchmarked animation.

## Changed files

- `desktop/src/main.tsx`: guarded development loader only.
- `desktop/src/presence/Exploration.tsx`: three concepts and fixture-only interaction.
- `desktop/src/presence/presence.css`: scoped material, geometry, motion and state hooks.
- `desktop/src/presence/Exploration.test.tsx`: truth, identity and isolation contracts.
- `scripts/desktop_presence.py`: owned loopback capture, browser assertions, GIF/contact sheet.
- `scripts/build_desktop.py`: production JS/CSS exclusion guard extended.
- `tests/test_desktop_presence.py`: independent artifact dimensions/hash verification.
- `docs/DESKTOP-UI-REDESIGN.md`: 10R.1 owner-review status and link.
- This directory: review, manifest, nine state PNGs, three DPR/reduced/forced-color
  PNGs, contact sheet and transition GIF.

