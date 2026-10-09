# OSCAR Expression System

Slice 11.3 reusable presentation foundation, derived from the owner-reviewed v3
character. Core retains all operational, permission, verification and audio truth.
No network, microphone, TTS, memory, native credential or capability executor.

Slice 12.1 adds an optional bounded local pointer target to the existing controller
and React presence (`gaze: {x, y}`, ±10/±7). It retargets through the same weighted
spring, preserving pose/velocity, operation, generation and expiry. Only idle/
attentive presentation responds; critical/privacy/activity states reject tracking.
Consumers that omit it retain the Slice 11 behaviour. No new wire field or engine.

- `core/contract.ts`: version-1 bounded event, strict validation and animation-only outcomes.
- `core/controller.ts`: source/generation/freshness admission, priority, state/accents,
  continuity, cancellation, expiry and lifecycle invalidation; no React dependency.
- `core/motion.ts` + `motion-v1.json`: reviewed geometry, spring/trajectory sampling.
- `react/`: reusable React/SVG projection and lifecycle/OS-motion-aware presence.
- `fixtures/reference-v1.json`: sixteen original v3 poses plus five shared traces.
- Android sibling: `mobile/expression/`, pure Kotlin controller/math plus native Compose.

The compiled ESM package exports `@oscar/expression`, `@oscar/expression/react` and
`@oscar/expression/motion`, with generated declarations. Core imports in plain
Node without React; the optional React entry requires the consumer's React peer.
The lab consumes the packaged entry for event-driven verification and the same
source for its legacy study controls. There is no build/runtime dependency on
unmerged Desktop PR #16.

## Trusted-source boundary

Bind `ExpressionController` to the source of an already authenticated adapter.
The `source.kind` field is provenance, never authentication. Use opaque IDs, no
private user content. Rejecting an event shows unknown and cancels presentation;
it never executes or cancels a Core task. Snapshot `generation` is last accepted
state; animation records have their own generation/transition ID and describe
only display completion/cancellation.

Each new accepted upstream snapshot has an increasing generation. Keep the same
`transitionId` for a freshness heartbeat with unchanged presentation; a new ID
expresses a new presentation request. Changing source/connection epoch requires
an explicitly rebound controller. Lifecycle stop invalidates presentation;
resuming cannot replay an old generation. Publish newer fresh state on resume.

The event expires within 30 seconds. Held-state renderers schedule expiry checks;
they do not keep a dead source falsely available. Clock skew allowance is 250ms;
the authenticated adapter must qualify/normalize observation time before framing
cross-node data. No expression layer invents freshness from cached/model state.

## Speech and activity

`kind: state, operation: speaking` settles and holds while that fresh state exists.
It does **not** start or loop the laboratory's finite speaking study. A permitted
`kind: accent, accent: phrase` performs one reviewed broad trajectory and returns
to the speaking posture. A changed upstream state ends/intercepts it. Engagement
accents require executing; blink does not start a phrase. Idle reactions recover
without changing operational truth. Reduced motion uses static equivalents.

Canonical Orb bytes remain unchanged. SVG and Compose preserve circle geometry,
unequal red marks, gradients/rim, gaze, second-eye opening and broad v3 travel.
Native blur/gradient rasterization differs; pixel-identical Android parity is not
claimed. See [engineering record](../docs/design/expression/ENGINE.md).

## Validate

```powershell
cd expression
npm ci
npm run build
cd ../design/expression-lab
npm ci
npm test
npm run build
```

Android: from `mobile/`, run `gradlew.bat :expression:testDebugUnitTest
:expression:assembleDebug :expression:connectedDebugAndroidTest` with SDK 36,
JDK 17+ and an emulator. The module is not added to `:app` dependencies.
Desktop integration is Slice 12; Mobile screen adoption is Slice 13.
