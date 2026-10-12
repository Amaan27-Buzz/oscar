# Cross-platform redesign evidence

2026-10-12 draft candidate from baseline `7773de8b794acf61ab6f035a28ada1fed98a3f77`. Implementation is native Tauri/React and Kotlin/Compose. The owner requested quick closure and explicitly waived further visual review. This packet records existing captures and functional checks; it does not claim owner design approval.

## Comparisons and primary flows

- [Desktop before/after](desktop/before-after.png), [original annotated evidence](desktop/originals.png), [primary screen matrix](desktop/screen-matrix.png).
- [Android before/after](android/before-after.png), [original annotated evidence](android/originals.png), [primary screen matrix](android/screen-matrix.png).
- [Visual system](../../../DESIGN.md), [research and direction](../CROSS-PLATFORM-REDESIGN.md), [audit](../CROSS-PLATFORM-UI-AUDIT.md), [independent assessment](../CROSS-PLATFORM-REVIEW.md), [non-destructive storage manifest](../CROSS-PLATFORM-STORAGE.md).

| Platform / flow | Curated native capture | Evidence classification |
|---|---|---|
| Desktop idle / invocation / input | compact, invoked-reference, writing-reference | Actual Windows Tauri/WebView2, disposable reference Core |
| Desktop working / result / reader | working-reference, result-reference, reading-reference | Actual native pixels; arithmetic readback verified; long prose scripted/reported |
| Desktop decisions / supervision | approval-reference, activity-reference | Exact material over authenticated disposable Core; no owner approval taken |
| Desktop text / contextual action | editing-reference, dictation-unavailable, action-reference | Native preview / unavailable adapter / temporary file reference; no real microphone |
| Desktop recovery | offline-reference | Actual disposable Core loss and recovery |
| Desktop appearance / controls | dark-reference, reduced-motion-reference, forced-colors-reference, shortcut-reference | Actual WebView2 with emulated media preferences; real native shortcut registration |
| Desktop native confirmation | native-confirmation-unusable-fixture | Actual Win32 dialog; expired synthetic material cannot authorize or sign |
| Android presence / input | home-reference, text-ime-reference | API35 native compositor, actual Gboard/insets; disposable Core |
| Android voice / recovery | voice-reference, unavailable | Microphone-off / unavailable; no voice-provider inference |
| Android management | activity-reference, devices-reference, settings-reference, privacy-reference | Native Compose and system captures; current grants and capabilities |
| Android reader / decision | reading-simulated, approval-reference | Native Compose RenderNode; long response explicitly simulated/reported; exact pending reference approval |
| Android accessibility | dark-large-text-reference, ime-large-text-reference, voice-large-text-reference | Native rendering, test density fontScale1.8 and reduced motion; actual IME |

Desktop individual PNGs preserve transparent pixels. The contact sheets composite them on a neutral background and place labels outside the original pixels. Android primary captures use the actual system compositor; long-reader/approval/settings helpers use Compose's native RenderNode capture. All original captures remain in baseline provenance folders. No generated concept image is included.

[Desktop native motion](desktop/motion-reference.gif) and [sampled frames](desktop/motion-frames.png) show actual shared expression and surface playback. Recording cadence is approximately128–132ms, not a compositor-FPS claim. Settled idle recorded zero continuous animation callbacks over3.2seconds. Android character contracts are tested; additional Android motion recordings, narrow/landscape/tablet visual matrices and final visual inspection were waived for quick closure. Historical baseline matrices are not reused as redesign PASS.

## Regression and authority

Final results are in [validation.json](validation.json), with native Desktop stage receipts alongside the captures. Core/Python559 tests ran with7 optional skips and no failures. Desktop frontend58 tests and production TypeScript/Vite build passed. Shared expression36 tests passed. Rust/Tauri12 tests, formatting, Clippy and native builds passed. Android JVM20 app and5 expression tests passed; final native suite outcome is recorded in the validation receipt.

Real isolated Windows CNG/PSS signing, UIA independent readback, cancelled work, hotkey collision rejection, native restart/shared-task continuity and reconnect passed. A contended earlier UIA run stayed UNKNOWN; a fresh registered isolated readback passed. Native CDP startup races and one later offline wait timed out; bounded target discovery and an isolated rerun passed. No safety assertion was weakened.

No Core, session/signing, OwnerConfirmation, permission or shared-expression authority change. Canonical Orb is byte-identical to baseline. Critical-risk strong confirmation remains blocked without genuine attestation. Voice opening grants no recording; privacy perception, retention and action grants remain separate. Frontends add no memory store or automatic task replay.

## Deferred acceptance

GitHub Actions is disabled for `Amaan27-Buzz/oscar`: remote exact-head CI is NOT_RUN, not PASS. Physical phone/OEM/biometric/real microphone/voice-naturalness, owner daily use, TalkBack/screen reader, Windows DPI/multimonitor and compositor CPU/GPU profiling remain NOT_RUN. Further final visual/motion/matrix review is DEFERRED_BY_OWNER under the explicit quick-closure waiver. No merge, Slice14, deployment or physical acceptance. No storage cleanup deletion.
