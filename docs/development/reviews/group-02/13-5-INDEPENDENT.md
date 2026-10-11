# Slice 13.5 independent native voice review

Recommendation: accept the bounded **SOFTWARE_VERIFIED / REFERENCE_VERIFIED**
presentation and denied/unavailable path after the corrections below. Actual
Android Voice Core commissioning, speech recognition/playback, audio routing,
room AEC/barge-in and owner Match/Map enrollment remain unverified. No phone or
audio PASS is granted by this review.

## Native capture examined first

Independently ran `MobileCompletionTest#voiceInvocationCancellationPreservesTextWithoutCapture`
through `scripts.mobile_completion_android` on the isolated **API 35 Android 15
emulator-5582**. One test passed, zero failures/skips; testcase 8.754 seconds,
suite 10.294 seconds. The real native Compose capture
`13-5-voice-denied-reference.png` was pulled from the emulator and visually
examined: readable muted microphone/perception-grant state, canonical shared Orb,
explicit uncommissioned awareness/playback/enrollment, and clear cancellation/text
continuation. Text draft survives invocation and cancellation. The binding stayed
null; no audio or broad device permission was granted.

The denied-state test initially failed. First it asserted immediately against an
asynchronously collected StateFlow; after waiting for phase/rendered state it still
failed because `assertTextContains` defaults to an exact text match. Native XML
showed **MUTED** and the correct full message. It now waits for the actual state and
asserts the exact full text. An intervening retry was blocked by an unrelated new
Settings test's private helper access; the parent corrected that separate issue.
Neither failed attempt is recorded as a product PASS.

## Demonstrated defects corrected

- **P1 delayed service admission:** owner-started service intents had no live
  presentation-token check before opening audio. A canceled/source-replaced
  invocation could still reach capture. Both service admission and the final
  native pre-recording boundary now require the current STARTING epoch and actual
  platform/perception grants. Service callbacks also recheck the live binding and
  grant; withdrawal stops audio rather than silently keeping capture running.
- **P1 stale terminal callbacks:** FAILED/MUTED/UNAVAILABLE could be overwritten by
  same-token late LISTENING/SPEAKING or service destruction's IDLE. Terminal states
  retire the presentation epoch. Old callbacks and `onDestroy` cannot restore
  listening or erase the failure.
- **P1 native turn replacement:** an old AudioFocus callback could close a newer
  turn, and capture failure tested generation outside the cleanup boundary. Start,
  close and failure admission now serialize against generation plus the captured
  sink identity. Frame delivery rechecks generation/grants after blocking reads.
- Playback snapshots its sink/track/epoch and releases the lifecycle monitor during
  blocking writes, allowing cancellation to invalidate/release output. Playback
  failure preserves an explicit failed/stopped path, while obsolete cancellation
  errors do not report new-session failure. Stop-error callbacks snapshot the sink
  once, removing a check-then-dereference race.

CoreSession stop/connect/disconnect and OscarApp epoch disposal cancel voice.
Opening Voice itself only presents controls. Reasoning, continuity and model
routing remain in Core; this patch adds no recognition model, memory store or
frontend executor. Microphone recording remains owner-started, not sticky or
boot-started. The shared Orb maps real presentation state; unsupported identity and
enrollment remain explicit rather than decorated functional settings.

## Regression proof and limits

`VoicePresentationTest`: **4 JVM tests passed**, zero failures/skips. Synthetic
booleans exercise actual service admission logic for stale epochs, missing owner
invocation, missing grant and absent binding. Terminal-state regressions reject
late capture/speech and destruction callbacks. These are synthetic state tests;
they do not claim physical microphone, audio-route or OEM timing acceptance.

`:app:testDebugUnitTest`, `:app:assembleDebug`, and
`:app:assembleDebugAndroidTest` passed. The final selected native denied-flow run
rebuilt the changed voice service/adapter and passed. Existing deprecation warnings
for synthetic StatusBarNotification constructors are unrelated to audio admission.

No unresolved demonstrated P0/P1 remains within this review scope. The actual
native capture is coherent and legible, although explanatory text makes Voice a
long page; this is a UX refinement advisory, not fabricated capability. Subjective
motion quality, real acoustic behavior, physical phone/OEM permission revocation,
real Voice Core binding and owner identity calibration are deferred to consolidated
acceptance. This reviewer investigated and corrected these defects; fresh final
review should still challenge the candidate independently.
