# Native OSCAR expression library

Isolated Slice 11.3 Compose renderer. `:app` does not depend on this module; no
screen redesign, Core/TTS/permission adapter or WebView is introduced.

`Contract` validates the same bounded version-1 wire event as TypeScript. Bind
`ExpressionController` to an already trusted source. `ExpressionPresence` consumes
fresh JSON events with native lifecycle/OS reduced-motion handling;
`ExpressionOrb` draws an already sampled snapshot. Outcomes describe animation
only. Publish a newer generation after lifecycle resume; stale input stays unknown.

`MotionData` loads the packaged shared `motion-v1.json`. Kotlin math and
TypeScript use the same spring, gaze, authored trajectories and recovery data.
Compose uses circles, paths, native gradients and a contact blur. Android blur,
gradient and anti-alias rasterization differ from SVG; pixel parity is not claimed.
The developer-only previews/test activity do not connect to owner capabilities.

From `mobile/` with JDK 17+, SDK 36 and an emulator:

```powershell
./gradlew.bat :expression:testDebugUnitTest :expression:assembleDebug :expression:assembleDebugAndroidTest
./gradlew.bat :expression:connectedDebugAndroidTest
# After successful instrumentation, pull the actual native atlas:
adb pull /data/local/tmp/oscar-expression-atlas.png expression-native-atlas.png
```

Shared fixture tests cover 16 poses, five controller traces and eight malformed
raw inputs. Instrumentation checks actual drawing at compact sizes, lifecycle,
mute/unknown accessibility semantics and strict Android JSON admission.
The test APK declares no microphone permission. This proves emulated rendering,
not physical-device performance or final owner visual acceptance.

Screen adoption remains Slice 13. Desktop renderer adoption remains Slice 12.
