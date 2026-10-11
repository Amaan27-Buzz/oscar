# Software Alpha acceptance ledger

Owner strategy decision: 2026-10-11. Build and autonomously validate the software
first; consolidate manual visual, real-device and physical acceptance at the end
of Groups 1–6. Deferred acceptance does not block authorized software development
and never becomes physical or production PASS. Security and truthful state remain
mandatory. Group 2 and Slice 13 are not authorized in this assignment.

Allowed classifications: `SOFTWARE_VERIFIED`, `REFERENCE_VERIFIED`,
`SIMULATED_ONLY`, `OWNER_VERIFICATION_DEFERRED`,
`HARDWARE_VERIFICATION_DEFERRED`, `BLOCKED`, `FAILED`.
Update a requirement only from its actual test/evidence boundary. Keep failures
and later corrections linked; do not erase historical acceptance reports.

## Group 1 — Desktop Slice 12

Base: `da8fddae50112c8859b21247d0cbaa617be8667e`, branch
`build/slice-12-desktop-completion`. Candidate software work is in progress.
`BLOCKED` below means proof has not yet been supplied, not permission to stop.

| ID | Requirement | Classification | Evidence / remaining work |
|---|---|---|---|
| D22-01 | Natural text input and response; repeated-interaction continuity | REFERENCE_VERIFIED | Native arithmetic/model fixture; Core same-session RAM continuity and private-mode regression |
| D22-02 | Current/private context and Controller Memory Preflight | SOFTWARE_VERIFIED | Existing Runtime preflight plus scoped MemoryExecutor; canonical FTS recall/source/forget tests; no React memory |
| D22-03 | Bounded compact results and readable expanded/long response | REFERENCE_VERIFIED | Native 600-character excerpt, 540×680 reading window, focus/overflow assertions |
| D22-04 | Real progress/waiting/completion and evidence distinctions | REFERENCE_VERIFIED | Actual task states; REPORTED versus VERIFIED; no Core token-stream contract exists |
| D22-05 | Keyboard interaction, interruption and authorized cancellation | SOFTWARE_VERIFIED | Reversal/draft/focus and duplicate reply tests; only advertised cancel review, not implicit consent |
| D22-06 | Offline/failure recovery; unavailable capability/model | REFERENCE_VERIFIED | Native Core loss/reconnect/withdrawn capability; no fake queue/retry/model prior fallback |
| D23-01 | Dictation entry/output and authoritative voice state | SOFTWARE_VERIFIED | Voice Core start/finish/cancel/late-recognition tests; simulated audio/transcript, physical acceptance deferred |
| D23-02 | Draft recovery and interruption/cancellation | REFERENCE_VERIFIED | Native separate mode drafts, retreat/reinvoke, clear-all; software session/generation cancellation tests |
| D23-03 | Focused/selection context where advertised | REFERENCE_VERIFIED | Real registered WPF/UIA and CNG native self-check; selection-only capture never promises unsupported insertion |
| D23-04 | Exact destination-aware preview and explicit selection | SOFTWARE_VERIFIED | Full focused append/replacement, expiry/destination/unknown-IPC regressions; native preview/expiry path |
| D23-05 | Authorized apply, expected-value conflict and independent readback | REFERENCE_VERIFIED | Existing real Tauri CNG/PSS + registered-field independent readback; consumed-preview fencing; no GUI consent claim |
| D23-06 | Denied mic/app permissions; no editable target | REFERENCE_VERIFIED | Native missing adapter/no target; software microphone denial opens zero capture; stale/foreign/context negatives |
| D24-01 | Current window/focus/selection and explicit supported capture | REFERENCE_VERIFIED | Registered WPF/UIA; explicit provenance/expiry; screenshot adapter unavailable |
| D24-02 | Live Catalog selection, typed requests and scope/risk disclosure | REFERENCE_VERIFIED | Native Catalog/form/withdrawal; typed Rust/Core permission regressions |
| D24-03 | Approval, task progress and cancellation | SOFTWARE_VERIFIED | Exact pending path, real TaskStage, advertised cancellation and cross-mode active guard |
| D24-04 | Failure/recovery and independently verified outcome | REFERENCE_VERIFIED | Native temporary file readback and separately isolated browser reference |
| D24-05 | Inspectable evidence, context freshness/provenance | SOFTWARE_VERIFIED | Current task evidence references; explicit captured source/permission/expiry |
| D24-06 | Suggested/planned/executing/blocked/reported/verified distinctions | REFERENCE_VERIFIED | Actual Core state; Prepare does not execute; Worker testimony stays REPORTED |
| D25-01 | Active/completed/blocked/failed tasks and pending decisions | BLOCKED | Unified progressive disclosure |
| D25-02 | Progress, ownership, artifacts/results and evidence | BLOCKED | Core task/action readback |
| D25-03 | Advertised cancel/continuation only | BLOCKED | No private replay or fictional resume |
| D25-04 | Reconnect, task switching and readback ordering | BLOCKED | Core/native/React regressions |
| D25-05 | Exact task/action/scope-bound approval and native signing | BLOCKED | Signed reference checks |
| D25-06 | Denial, expiry, replay rejection and truthful attention | BLOCKED | Negative-path tests |
| D26-01 | Canonical identity and shared weighted responsive motion | BLOCKED | Shared engine, no second renderer |
| D26-02 | Spatial continuity, interruption and reduced motion | BLOCKED | Native content captures and regressions |
| D26-03 | Keyboard/focus and semantic accessibility | BLOCKED | Component/native DOM evidence |
| D26-04 | Contrast, long text, DPI-aware bounds and layout | BLOCKED | Automated geometry/contrast reference checks |
| D26-05 | Idle stillness/resource work and coherent error/recovery | BLOCKED | Controller/rendering/runtime checks |
| D26-06 | Final cross-stage native reference and independent code/UX review | BLOCKED | Required before Group 1 software closure |

## Consolidated manual / device acceptance

| ID | Requirement | Classification | Final acceptance obligation |
|---|---|---|---|
| OWNER-DESIGN | Owner visual judgement, natural movement and sustained use | OWNER_VERIFICATION_DEFERRED | Actual desktop distance/playback and real workflows |
| WIN-FOCUS | OS foreground/hotkey/focus stealing and human tray/exit recovery | OWNER_VERIFICATION_DEFERRED | Test owner Windows session without inferring DOM focus equals OS focus |
| WIN-DPI | 100%/125%/150%, multiple monitors, taskbar/fullscreen/compositor/hit regions | OWNER_VERIFICATION_DEFERRED | Real configurations; synthetic dimensions are reference only |
| WIN-ACCESS | Actual screen reader and OS accessibility preferences | OWNER_VERIFICATION_DEFERRED | Human assistive-technology acceptance |
| VOICE-PHYSICAL | Microphone/output/room AEC/barge-in/self-wake/naturalness | HARDWARE_VERIFICATION_DEFERRED | Existing consolidated Voice acceptance harness |
| STRONG-APPROVAL | Critical-risk native owner confirmation | OWNER_VERIFICATION_DEFERRED | Remains unavailable until implemented and accepted; ordinary MessageBox is not strong verification |
| EDGE-PHYSICAL | Edge UART/GPIO/watchdog/interlock/E-stop silicon | HARDWARE_VERIFICATION_DEFERRED | Preserve existing Gate C obligations; no Group 1 physical claim |
| MOBILE-DEVICE | Phone/OEM enrollment, assistant/overlay/audio/notification and owner controls | HARDWARE_VERIFICATION_DEFERRED | Consolidated real-device checks after software program |
| DISTRIBUTION | Installer, signing/update and deployed interoperability | OWNER_VERIFICATION_DEFERRED | No development binary equals production acceptance |

## Future group tracking

Groups 2–6 will add their authorized canonical slice scopes, software evidence and
deferred acceptance here. They are not begun or pre-certified by Group 1. This
ledger follows the program through its final consolidated acceptance phase.
