# Software Alpha acceptance ledger

Owner strategy decision: 2026-10-11. Build and autonomously validate the software
first; consolidate manual visual, real-device and physical acceptance at the end
of Groups 1–6. Deferred acceptance does not block authorized software development
and never becomes physical or production PASS. Security and truthful state remain
mandatory. Group 2 / Slice 13.1–13.8 is separately authorized on 2026-10-11;
Slice 14 remains outside the assignment.

Allowed classifications: `SOFTWARE_VERIFIED`, `REFERENCE_VERIFIED`,
`SIMULATED_ONLY`, `OWNER_VERIFICATION_DEFERRED`,
`HARDWARE_VERIFICATION_DEFERRED`, `BLOCKED`, `FAILED`.
Update a requirement only from its actual test/evidence boundary. Keep failures
and later corrections linked; do not erase historical acceptance reports.

## Group 1 — Desktop Slice 12

Base: `da8fddae50112c8859b21247d0cbaa617be8667e`, branch
`build/slice-12-desktop-completion`. Candidate software/reference work is complete in the tested scope; owner/device/production approval is not given.
Future `BLOCKED` entries require a scoped engineering resolution; deferred acceptance never becomes physical PASS.

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
| D25-01 | Active/completed/blocked/failed tasks and pending decisions | REFERENCE_VERIFIED | Single controlled native Activity; current/shared dedup |
| D25-02 | Progress, ownership, artifacts/results and evidence | SOFTWARE_VERIFIED | Worker/progress and sanitized evidence; session-bound artifact metadata; recall sources and temporal warning |
| D25-03 | Advertised cancel/continuation only | SOFTWARE_VERIFIED | Signed deny/cancel only; no private retry/resume; missing payload withdraws approve |
| D25-04 | Reconnect, task switching and readback ordering | REFERENCE_VERIFIED | Native offline/reconnect; Rust switched-review invalidation and content fences |
| D25-05 | Exact task/action/scope-bound approval and native signing | REFERENCE_VERIFIED | Existing actual CNG/PSS reference; exact review; opening grants nothing |
| D25-06 | Denial, expiry, replay rejection and truthful attention | REFERENCE_VERIFIED | Native actual expiry/task-change; software signature/replay/grant regressions |
| D26-01 | Canonical identity and shared weighted responsive motion | REFERENCE_VERIFIED | Unchanged canonical SHA256; shared engine36 tests, actual native motion/multi-frame review |
| D26-02 | Spatial continuity, interruption and reduced motion | REFERENCE_VERIFIED | Native10 checks; preference emulated, draft/focus/recovery preserved |
| D26-03 | Keyboard/focus and semantic accessibility | SOFTWARE_VERIFIED | Desktop56 tests, native semantic focus/tab/expiry, real screen reader deferred |
| D26-04 | Contrast, long text, DPI-aware bounds and layout | REFERENCE_VERIFIED | Native wrapping/overflow and Rust100/125/150% placement math; physical configurations deferred |
| D26-05 | Idle stillness/resource work and coherent error/recovery | REFERENCE_VERIFIED | Idle RAF0/3.2s, native reconnect, source flags, stale presentation/error regressions |
| D26-06 | Final cross-stage native reference and independent code/UX review | REFERENCE_VERIFIED | Ask/Text/Act/Activity/Polish native receipts; fresh final review accepted after reproduced fixes |

## Consolidated manual / device acceptance

| ID | Requirement | Classification | Final acceptance obligation |
|---|---|---|---|
| OWNER-DESIGN | Owner visual judgement, natural movement and sustained use | OWNER_VERIFICATION_DEFERRED | Actual desktop distance/playback and real workflows |
| WIN-FOCUS | OS foreground/hotkey/focus stealing and human tray/exit recovery | OWNER_VERIFICATION_DEFERRED | Test owner Windows session without inferring DOM focus equals OS focus |
| WIN-DPI | 100%/125%/150%, multiple monitors, taskbar/fullscreen/compositor/hit regions | OWNER_VERIFICATION_DEFERRED | Real configurations; synthetic dimensions are reference only |
| WIN-ACCESS | Actual screen reader and OS accessibility preferences | OWNER_VERIFICATION_DEFERRED | Human assistive-technology acceptance |
| VOICE-PHYSICAL | Microphone/output/room AEC/barge-in/self-wake/naturalness | HARDWARE_VERIFICATION_DEFERRED | Existing consolidated Voice acceptance harness |
| STRONG-APPROVAL | Critical-risk native owner confirmation | BLOCKED | Not advertised/implemented; preserve rejection, revisit stronger confirmation in later authorized software hardening; ordinary MessageBox is not strong verification |
| EDGE-PHYSICAL | Edge UART/GPIO/watchdog/interlock/E-stop silicon | HARDWARE_VERIFICATION_DEFERRED | Preserve existing Gate C obligations; no Group 1 physical claim |
| MOBILE-DEVICE | Phone/OEM enrollment, assistant/overlay/audio/notification and owner controls | HARDWARE_VERIFICATION_DEFERRED | Consolidated real-device checks after software program |
| DISTRIBUTION | Installer, signing/update and deployed interoperability | OWNER_VERIFICATION_DEFERRED | No development binary equals production acceptance |

## Future group tracking

## Group 2 — Mobile Slice 13

Base: `dcfd31bca6fbd8080f4c20bebe3d448e4bd8dc2f`, separate branch
`build/slice-13-mobile-completion`. SOFTWARE / REFERENCE CANDIDATE; no owner/device acceptance.

| ID | Requirement | Classification | Evidence / remaining work |
|---|---|---|---|
| M00-01 | Verified Group 1 and accepted Mobile foundation | SOFTWARE_VERIFIED | Exact baseline551/6 optional skips; Android APK/JVM PASS, JVM/Core readback |
| M00-02 | Session-private discard/readback/approval and exact review | SOFTWARE_VERIFIED | Independent118 tests, regression reproductions and [review](reviews/GROUP-02-BASELINE.md) |
| M00-03 | API36.1 Compose reference | FAILED | Historical SurfaceFlinger DMA crash reproduced on separate AVD; API35 isolated fallback now passes; API36.1 historical platform failure retained |
| M31-01 | Shared native Orb, state truth, freshness, epoch and reduced motion | SOFTWARE_VERIFIED | App10+Expression5 JVM, expression3 API35 rendering tests; immutable canonical artwork |
| M31-02 | Native Home, one relevant item and unavailable/accessibility labels | REFERENCE_VERIFIED | App8 Compose/one optional fixture skip; actual Home capture, simulated verifying capture; independent13.1 review |
| M31-03 | Microphone denial and local revoke boundary | SOFTWARE_VERIFIED | Grant checked before every PCM delivery, service stop on revoke; denied Compose case; in-flight synthetic proof13.5 |
| M32-01 | Text continuity, short/long reading and epistemic labels | REFERENCE_VERIFIED | Real isolated Core native flow; long REPORTED reader SIMULATED_ONLY; JVM12+5/native11+1 extra |
| M32-02 | Draft encryption, source isolation, recreation and late callbacks | SOFTWARE_VERIFIED | AES-GCM source AAD; epoch/wire serialization; interrupted-save + native crypto/recreation regressions |
| M32-03 | Privacy-safe discard and foreground recovery | REFERENCE_VERIFIED | Real Core acknowledgement; atomic pending marker and new-ViewModel suppression; no implicit cancel/replay |
| M32-04 | Process replacement / encrypted draft recovery | REFERENCE_VERIFIED | Actual foreground force-stop/relaunch PID change and draft recovery; low-memory/OEM/phone acceptance remains deferred |
| M33-01 | Task supervision, real ownership, progress and evidence | SOFTWARE_VERIFIED | Current lease/action/time qualification; prior progress explicit; Core56/JVM20; selectable inspector |
| M33-02 | Complete exact review, scope, audience and generation | REFERENCE_VERIFIED | Native full review; length-framed signed display digest; changed material/generation/expiry regressions |
| M33-03 | Opening/dismissal/expiry/unavailable confirmation grants nothing | REFERENCE_VERIFIED | API35 actual review/expiry/readback; real Android unavailable handoff; separate reference-signed denial/no execution |
| M33-04 | Android owner biometric/PIN/signing and critical attestation | HARDWARE_VERIFICATION_DEFERRED | No biometric success fabricated; native owner commissioning deferred; STRONG-APPROVAL remains BLOCKED |

Every Group 1 consolidated obligation above carries forward unchanged, especially
STRONG-APPROVAL BLOCKED and Windows/Voice/phone/Edge/manual verification.

Group2 adds its separately authorized Mobile software/reference evidence here.
Groups3–6 remain unbegun and are not pre-certified by earlier groups. This
ledger follows the program through its final consolidated acceptance phase.

Group 1 publication: [draft PR #2](https://github.com/Amaan27-Buzz/oscar/pull/2)
against verified corrective base; software candidate accepted by independent review,
not owner approved or promoted. Final tests551 total/545 passed/6 skips; Desktop56,
Expression36, Rust12; native/reference receipts linked in the Group 1 report.

| M34-01 | Native Grid truth, progressive detail and local disconnect | REFERENCE_VERIFIED | API35 captured; JVM21 and Core56 PASS; no invented controls |
| M34-02 | Desktop origin / network interruption and recovery | REFERENCE_VERIFIED | Genuine isolated Core + Desktop adapter HTTP; same task readback, private source isolation; physical networking deferred |

| M35-01 | Explicit voice invocation/cancel/text continuity | REFERENCE_VERIFIED | API35 denied path PASS; no capture/owner permissions; real adapter status and epoch controls |
| M35-02 | Delayed starts/terminal failures/stale audio callbacks | SOFTWARE_VERIFIED | Four JVM regressions and native denial; independent13.5 review |
| M35-03 | Voice Core Android commissioning / actual room audio | HARDWARE_VERIFICATION_DEFERRED | Binding uncommissioned; no recognition/playback/enrollment PASS; existing Voice obligations unchanged |

| M36-01 | Independent grants / actual denied permission UI / explicit revoke | REFERENCE_VERIFIED | Native privacy3 + capture rerun; no OS grants; immediate voice epoch invalidation |
| M36-02 | Source exclusions, sensitive metadata and stale notification protection | SOFTWARE_VERIFIED | Source+fingerprint final reply gate; revision/epoch resets; synthetic metadata regressions |
| M36-03 | Real ingestion/reply/mic/OEM and person-level Core policy | HARDWARE_VERIFICATION_DEFERRED | Owner/device acceptance; unsupported Core policy authoring remains unavailable |

| M37-01 | Settings, appearance/reduced motion, diagnostics / system handoffs | REFERENCE_VERIFIED | JVM25; actual API35 platform and persisted reduced-motion recreation |
| M37-02 | Bounded Persona preview | SIMULATED_ONLY | Shared fixture expression; unsaved, no Core policy mutation |
| M37-03 | Overlay/widget / full Presence / mutable routing commissioning | BLOCKED | Absent platform implementation remains explicitly unavailable; owns Slice16 integration, no new runtime |

| M38-01 | Native narrow/landscape/large, font1.8, actual IME and cancellation | REFERENCE_VERIFIED | Three actual AVD size/density runs; keyboard-visible and field-bound assertions; phone/OEM NOT_RUN |
| M38-02 | Lifecycle/source restoration, epoch fences and process replacement | REFERENCE_VERIFIED | Full native app21/4 intentional skips; actual process replacement; no automatic task replay |
| M38-03 | Contrast, dark bars, TalkBack labels and restrained motion | SOFTWARE_VERIFIED | Independent contrast4.823:1; shared state/held motion contracts; actual renders; sustained assistive technology deferred |
| M38-04 | Final owner/device/physical/strong confirmation | OWNER_VERIFICATION_DEFERRED | All Group1 obligations preserved; strong critical-risk confirmation still BLOCKED; no production/owner approval |
