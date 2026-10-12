# OSCAR / Aperture

An isolated, interactive Windows Desktop design study. Branch:
`codex/desktop-reimagined`, based on local `main` at `fd191a2`.

## Run

The current preview is at http://127.0.0.1:1428/aperture.html.
From `desktop/`, run `npm run dev -- --port 1428` and open that address.
The existing local `@oscar/expression` dependency must be linked and built
(`npm run build` from `expression/`); no new packages are required.

Click OSCAR, or press Ctrl+Space. Try **Find the essential idea → Turn this
into a brief → Approve example → Back to your work**. Escape retreats and
restores focus to OSCAR. Click the example document to return to work;
pinning keeps the panel open. A pending decision opens directly from the dock.
The bottom strip jumps to each review state. The microphone demonstrates a
voice turn without requesting microphone access. Text tools edit a local draft
and can copy it to the real clipboard, only when Copy is clicked.

## Direction

Aperture is a compact presence that opens into a focused work surface. The
unchanged blue/yellow OSCAR supplies character; deep ink surfaces, cool blue
controls and a deliberate yellow approval edge give the surrounding UI its
identity. A restrained desktop backdrop demonstrates working alongside a
document. The backdrop and Fieldnotes are scenery, not connected applications.

The dock is the continuous anchor. Content unfolds above it in roughly 650 ms;
reading, preparation and decision live within the same surface. Reduced motion
removes those transitions. Existing shared expression rendering supplies gaze
and operational poses using explicitly labeled fixture events. No new Orb
artwork, geometry, colors or expression engine was introduced.

## Scope and evidence

- All assistant answers, voice transcripts, task work, approvals and file
  results are scripted examples. No Core calls, audio capture, file execution,
  signing or permission grants occur. Arbitrary questions receive the same
  illustrative document response; this is not connected inference.
- Existing production entry points, backend, security and Mobile are untouched.
  `aperture.html` is a separate Vite development entry and is absent from the
  normal production build. Its script additionally refuses production mode.
- TypeScript, production build and four focused interaction tests passed.
  Browser walkthrough covered the complete flow; 1440×960 and 1280×800 captures,
  Escape focus restoration, Ctrl+Space and reduced motion were checked.
- Independent review identified pending-decision routing and cosmetic pinning;
  both were corrected and covered by focused tests.
- Canonical Orb hash matches `main`:
  `cb38546cf40c585e1ea5a1f3000832ca10c92ba5` (Git blob hash).
- Native Windows placement, transparency, DPI/multimonitor behavior, real voice
  and owner visual acceptance remain untested. No production integration.

[Screenshot gallery](gallery.html) · [Source](../../src/aperture/main.tsx)

Focused check: `npx vitest run src/aperture/aperture.test.tsx` from `desktop/`.
