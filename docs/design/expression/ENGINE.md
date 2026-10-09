# Slice 11.3 engineering contract

Owner authorized continuing engineering from reviewed v3 movement. This does not
approve every visual detail or certify cross-device quality. No UI redesign,
Core mutation, PR #16 dependency, TTS integration or Elocution work.

## Ownership and layout

`expression/` owns plain TypeScript contract/controller, numeric pose and motion,
shared JSON motion data/reference fixtures, and a separate React/SVG renderer.
`mobile/expression/` is an isolated native Android library with equivalent Kotlin
controller and Compose drawing/lifecycle. The existing Mobile app is unchanged.
The lab imports the extracted engine/renderer and keeps its synthetic controls
and sequences locally. Shared fixtures test semantics and numeric sampling; they
do not demand identical browser/Android rasterization.

## Version 1 event

Strict bounded object, no arbitrary user content:

- `version: 1`; `source: {kind: core|lab|fixture, id: bounded ASCII identifier}`;
- increasing safe-integer `generation`, bounded `transitionId`;
- UTC millisecond `eventTime` and `expiresAt` (at most 30 seconds later);
- `kind: state|accent|interrupt|cancel`; `priority: normal|urgent`;
- `operation: idle|attentive|listening|processing|executing|verifying|waiting|speaking|muted|unavailable|error|unknown`;
- reviewed `delivery`, availability, `muted`, `attention: none|owner`, `reducedMotion`;
- optional `accent: phrase|engagement|blink`, only with an accent event.

Source metadata is provenance, **not authentication**. A controller is bound to
one upstream source; its integration must already authenticate/authorize that
publisher. Nothing in an expression grants permission or promotes task truth.

Unknown fields, malformed enums/types/IDs/times and mismatched source fail closed.
The contract schema is `expression/contract-v1.schema.json`; TypeScript and Kotlin
runtime validators additionally enforce relative freshness. Typed enum/state
validation rejects legacy lab-only `available` as a wire operation; use `idle`.
Older/equal generations cannot resurrect old activity. Invalid current input and
expiry cancel choreography and show unknown, retaining mute. A fresh explicit
new generation is required for restoration. Effective priority is derived from
availability, unknown, error, owner attention, mute and actual operation; a caller
cannot hide these with an expressive cue or a normal-priority hint.

Both languages require strict JSON syntax; Android's lenient `JSONObject` parser
is preceded by a bounded grammar check. Structural/source validation precedes
generation arbitration; freshness is checked for new events. Thus an expired
but structurally valid older packet cannot erase newer state. Eight shared raw
malformed fixtures exercise syntax, fields, enum/type and safe-integer boundaries.

## Event-driven motion

A production speaking state starts a settling transition and holds an engaged
pose while fresh speaking state remains authoritative. It does not run or repeat
the five-second demo. An explicit permitted `phrase` accent can perform the
reviewed finite trajectory, then hold the speaking pose. A newer upstream state
ends speech presentation; expiry/invalid input/lifecycle suppresses it as unknown.
Engagement accents likewise require actual executing
state; blink is a presentation event, never a perception claim.

Interruption/changes sample the actual performed pose and velocity, replace the
old transition and cancel queued accents/recovery immediately. Completion and
cancellation records describe **animation only**, never task success. Lifecycle
stop invalidates the presentation; resume requires newer fresh upstream input.
Reduced motion replaces travel/blink/accents with static poses and preserves
operational labels. No renderer reads a microphone or infers prosody/emotion.
Idle reactions retain their logical recovery timing as discrete static poses;
turning on reduced motion cannot leave surprise permanently held.

Freshness heartbeats retain a stable transition ID while increasing generation.
They renew state without replaying reactions. A new ID marks a new presentation
intent. The latest generation always wins; hard effective priority is derived
from availability/unknown/error, attention, privacy, urgency and actual activity.

## Implemented boundaries

The library is built as ESM with declarations and an optional React peer. Its
plain core has no React/runtime adapter dependencies. The lab's 22 v3 checks and
16 original numeric pose references remain unchanged in meaning. Five controller
trace files run in both TypeScript and Kotlin, including source mismatch, malformed
content, heartbeat/recovery, cancellation, lifecycle, expiry and reduced motion.

The native library compiles with the accepted Android toolchain. `:app` does not
depend on it; renderer adoption remains later UI work. See [integration](INTEGRATION.md).

## Acceptance

Preserve all v3 lab tests and normalized canonical rendering. Add contract,
generation/freshness, long-speaking hold, accent/stop, cancellation, lifecycle,
reduced-motion and renderer continuity tests. Execute the same JSON fixtures in
TypeScript and Kotlin. Compile isolated Compose code, run JVM/instrumentation
tests where available, and inspect a small browser/native capture set. Keep
emulated/synthetic/physical/CI evidence separate. Update PR #17 and stop before
Slice 12; owner questions and billing-blocked CI do not become merge approval.
