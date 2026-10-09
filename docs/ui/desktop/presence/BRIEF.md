# Slice 12.1 — Living Desktop Presence

Owner-authorized local prototype, based on clean integration commit
`b9d3e049aef5148a10c710626b9e6b06771c9229`. Default Desktop stays unchanged.
Mode: Operate, with character leading the peripheral resting surface.

## Research and interaction model

Inspected canonical SVG, shared controller/renderer and v3 small-scale captures;
old A/B/C sheet, native integration capture, tray screenshot and lifecycle code.
The old designs made containers the unit of personality. A permanent Open button
competed with a pasted smile. Preserve the native tray and authenticated bridge;
replace the surrounding composition, not the character.

[Windows flyouts](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/dialogs-and-flyouts/flyouts)
inform transient dismissal and focus recovery. [Raycast Windows](https://www.raycast.com/windows)
informs keyboard invocation and getting out of the way, not its command-list layout.
[Rive / Intercom](https://rive.app/blog/intercom-s-product-animation-evolution-embracing-rive)
informs responsive rather than passive animation. These are published interaction
references, not installed-app inspections or copied art. OSCAR retains its existing engine.

Three questions considered: a permanent status strip (too widget-like); an edge-only
hotspot (identity and recovery too hidden); a free Orb with a transient writing leaf
(chosen). No concept tournament: the owner asked for one reasoned proposal.

## Direction contract

THESIS: OSCAR is the thing you invoke. Controls grow from its location and leave
it there afterward. No status dashboard surrounding the character.

OWN-WORLD: canonical blue/yellow/red material, graphite words on warm paper only
when writing or reviewing. One flat writing leaf, precise small text actions,
76px expression, no decorative status chrome or endlessly looping motion.

STORY: presence → acknowledge → type → yield to actual work → review if needed →
retreat. Escape retreats without cancelling work; hiding remains distinct from Quit.

FIRST VIEWPORT: a transparent 132×148 logical-pixel window, 76px Orb near the lower
right, one short truthful caption. A 432×384 interaction window with a 400 by 256 writing leaf expands up and left;
the Orb keeps its screen location. Approval requests never steal focus.

FORM: code-led precise native prototype. No generated mockups; real rendered
captures are the visual authority for this candidate. Segoe UI inherits Windows
and the canonical system; no new branding, assets or dependencies.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish
review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## Scope and boundaries

Debug-only `--living-presence` and DEV `?living` route; synthetic `?living=preview`
fixtures visibly labelled. Native Rust owns supported transparency, size, placement,
pinning/hide and tray. IPC stays closed and bounded. Core owns operational state;
the adapter owns freshness; shared ExpressionController owns motion. Local hover/
invocation changes delivery only. Voice previews do not claim commissioned audio.

No Ask/Edit/Act/Activity redesign: the existing workspace handles deeper interaction
and exact approval/native signing. No inferred attention, screen sensing, auto-retreat
of drafts, automatic pinning, saved geometry, click-through or fullscreen heuristics.
Review must establish whether tiny captions and transparent edge placement work
on the owner's desktop. Native DPI/multi-monitor coverage is reported precisely.
