# Shared engine integration boundary

Slice 11.3 supplies reusable source and an isolated native library. It does not
wire the unmerged Desktop runtime or replace any accepted Mobile screen.

## Desktop — Slice 12

The read-only PR #16 reference has a Rust-owned typed `desktop-state` bridge and
fields including `link`, `orb`, `voice`, `observed_at_ms` and task state. The
future adapter must authenticate/scoped-read that existing bridge, preserve
its unknown/degraded meanings, and publish a bounded expression snapshot.
Do not serialize context, task descriptions, responses, credentials or approval
payloads. Do not map Worker testimony or a pleasant cue to VERIFIED.

Use an opaque source ID including the current connection epoch. Maintain a
monotonic event generation for the whole presentation stream; a task's generation
alone is not a stream generation. Use a stable transition ID for unchanged-state
freshness heartbeats. Only actual upstream listening/speaking activates those
states; attention or an open eye does not. Renew state before expiry, and publish
newer state on resume. A cached view is not a fresh event.

Import the source package's React entry with the existing Vite/TypeScript toolchain
(React peer/deduplication supplied by the surface):

```tsx
<ExpressionPresence source={trustedSource} event={validatedUpstreamEvent} size={64} />
```

The controller validates again at admission. The SVG node and gradient IDs stay
stable while frames update. Animation callbacks describe presentation only;
never turn them into Core task completion, consent or audio state.

## Mobile — Slice 13

Add `implementation(project(":expression"))` only during separately authorized
screen adoption. Today `:app` retains its accepted canonical PNG and layout.
Create frames from current CoreSession readback through a small trusted adapter,
not a phone reasoning system. Apply the same source-epoch, generation, time and
privacy rules. Use native `ExpressionPresence` for event-driven UI or
`ExpressionOrb` for an already sampled snapshot. No WebView is needed.

The composable respects STARTED lifecycle and animation-disabled scale. Stop
invalidates presentation and cancels pending motion; a stale resume event cannot
reopen listening/speech. A newer fresh source event restores it. Android previews
and the isolated test APK are explicit fixtures, not owner/device acceptance.

## Platform parity and future surfaces

The same JSON data and reference cases verify poses, priorities, admission,
generation/freshness, reaction recovery, long-speaking hold, explicit accents,
interruptions, reduced motion and animation-only records in TypeScript/Kotlin.
Canvas/Skia blur and radial-gradient rasterization differ from SVG filtering;
source colors, circle/rim geometry and unequal marks are preserved, but exact
pixel parity is not claimed. Review real target DPI, reduced-motion preferences,
TalkBack, power/performance and owner naturalness when adopting a real surface.

Future Presence implementations consume this versioned contract and port the
numeric mechanics if appropriate; no future surface, TTS/prosody binding, widget,
World Model, Sentry or commissioning is implemented here.
