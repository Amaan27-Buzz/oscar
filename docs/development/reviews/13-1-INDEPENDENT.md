# 13.1 independent software and native render review

Reviewed 2026-10-11 against the Group 1 baseline in the separate Mobile worktree.
This reviewer changed no application code. **ACCEPT bounded 13.1 software/reference
closure**, with microphone regression assertions recorded before checkpoint.
Owner visual and physical Android acceptance remain deferred.

## Evidence inspected

Inspected actual native Compose captures first: `13-1-home-unavailable.png` and
`13-1-verifying-simulated.png`. The first is the unpaired app; the second is a
disposable explicitly simulated verifying snapshot rendered by the app's actual
Compose components. Neither proves real network work, speech or physical device
acceptance. The blue shell/yellow weighted puck remains recognizable at 108 dp;
the unavailable pose and verifying marks differ. Typography, warm canvas and
compact voice/text controls are readable, with no card wall or giant microphone.
The Orb occupies a restrained fraction of the viewport. The disconnected Send
control is disabled. The verifying caption claims checking rather than success.

Instrumentation asserts production `FLAG_SECURE`, temporarily clears it only for
disposable test capture, then restores it. No production screenshot privacy change
was found. The API 36.1 SurfaceFlinger crash is an emulator platform failure; API 35
rendering is separate reference evidence and never physical phone/OEM PASS.

## Code and independent validation

Read the shared renderer/controller and changed app composition, expression
adapter, state timestamp, Gradle linkage and associated tests. The canonical SVG,
shared engine and expression library have no changes in this stage's diff.

Independently ran `gradlew.bat :app:testDebugUnitTest
:expression:testDebugUnitTest --console=plain`: **10 app tests and 5 expression
tests, zero failures/errors/skips**, build successful. The app tests reran; the
expression results were Gradle up-to-date, so this is not a fresh expression rerun.
Parent-run Android instrumentation, Core and live reference transport results are
not represented as this reviewer's independent execution.

The adapter sends no private task text/identifiers or signing material to animation.
Epoch changes produce a new source; stale operation admission becomes unknown.
Connected freshness expires rather than being refreshed by composition alone.
Heartbeats advance generation without replaying the same transition. The native
renderer retains lifecycle suspension and OS reduced-duration behavior. Owner
attention outranks work; verifying is distinct from executing; caption priority and
a single attention-prioritized home item now agree with expression arbitration.

## Findings and follow-up

- Initial P2: home caption ignored an open deny/cancel review while the Orb showed
  waiting. Fixed by including `state.approval` in caption priority.
- Initial P2: approval and active work could both occupy home. Fixed by selecting
  one attention-prioritized relevant item.
- Baseline P1 microphone revocation: local perception revocation previously did
  not stop an active adapter. Corrected by stopping the foreground service and
  rechecking Android/local grants before each PCM delivery. Denied/revoked grant
  regression assertions are required before checkpoint; actual in-flight synthetic
  adapter lifecycle coverage belongs to authorized 13.5 integration. No physical
  capture or acoustic quality is accepted here.
- Visual advisory: unpaired home repeats disconnected copy above and below the
  Orb. Consolidate during interaction refinement. Generic `Running` below the
  verifying caption should become an explicit task state during 13.3 refinement.

No remaining demonstrated P0/P1 defect in the bounded 13.1 expression integration.
The separate baseline exact-review and session/credential race obligations remain
open for 13.2/13.3; this stage does not clear them.

Not checked: real phone/OEM, microphone/audio, owner visual approval, sustained
motion/battery performance or consolidated accessibility acceptance. Remaining
risk: this stage's stills do not prove animation smoothness or final interaction.
