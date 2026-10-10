# Local validation — 2026-10-11

All claims are local. GitHub Actions remain disabled; no remote CI or owner
approval is claimed. The recorded candidate is still a development prototype.

| Check | Actual result |
|---|---|
| Desktop TypeScript / React | Typecheck PASS; 36 tests, 5 files, 0 failed/skipped |
| Shared Expression Lab | 36 tests, 5 files, 0 failed/skipped |
| Rust/Tauri | 11 tests, 0 failed/ignored; fmt PASS; Clippy warnings denied PASS; locked debug native build PASS |
| Python/Core/Desktop/Mobile and slice docs | 50 tests, 0 failures/skips; final run 14.977 s |
| Python type/lint | mypy 63 source files PASS; Ruff changed Core/test/fixture files PASS |
| Kotlin shared expression | `:expression:testDebugUnitTest` BUILD SUCCESSFUL; JUnit 5 tests, 0 failures/errors/skips; no Android physical test |
| Production frontend | Build PASS; prototype/fixture markers absent from JS/CSS |
| Canonical branding | SVG unchanged: Git blob `cb38546cf40c585e1ea5a1f3000832ca10c92ba5` |
| Repository | Required docs/local links and value-silent secret scan PASS; diff whitespace PASS |
| Native reference interaction | 13 assertions PASS in final [receipt](evidence/native-suite.json) |
| Native interruption | 1 assertion PASS plus timed frame sequence in [receipt](evidence/native-interrupt-suite.json) |
| Post-review native handoff | 4 assertions PASS; focused/visible exact approval without deciding, [receipt](evidence/review-route-receipt.json) |
| Native lifecycle harness | `LIFECYCLE_REFERENCE_PASS: uncommissioned, close/hide, reveal, explicit quit`; process exit 0 |
| Evidence integrity | PNG/GIF files decode; nonempty multi-frame GIFs; size, dimensions, frame counts and SHA-256 in [manifest](artifacts.json) |

The lifecycle harness printed a WebView2 teardown warning (`Chrome_WidgetWin_0`
unregister error 1412), while its assertions and process exit passed. No claim of
clean human tray/Quit interaction is derived from that harness.

## Native coverage

The actual Tauri debug executable/WebView2 was connected through its existing
debug CDP endpoint. Requests reached an authenticated disposable Python Core.
The run exercised draft/focus, immediate and settled retreat/reinvocation,
blocked/denied feedback, pending approval, exact review, actual executing and
awaiting-result readback, verified arithmetic, scripted partially verified/failure
outcomes, HTTP disconnect/reconnect, pin/float/edge IPC acknowledgement, and
native media emulation for reduced motion/forced colors. The interruption run
changed real Core state while the accent was active, then retreated/reinvoked.

Programmatic Runtime approval/progression is labelled reference only. Model
answers are scripted; microphone, real listening/speech and prosody are absent.
WebView screenshots are real native content, not browser-only mockups. The raw
capture intervals are not a reliable GPU/CPU/frame-performance benchmark; no
idle power or sustained 60 fps claim is made.

## NOT VERIFIED

OS-level foreground/focus stealing, keyboard global invocation from another app,
human tray Hide/Quit, real owner confirmation dialog/signature acceptance,
whole-desktop transparency/shadows/fullscreen composition, click-through to
underlying windows, screen-reader use, multiple monitors and full 100%/125%/150%
Windows display scaling. Recorded WebView device scale 1.25 alone proves none
of the broader scaling/monitor acceptance. The owner asked to finish without
computer use; remaining native human/hardware checks were not substituted with
synthetic screenshots.
