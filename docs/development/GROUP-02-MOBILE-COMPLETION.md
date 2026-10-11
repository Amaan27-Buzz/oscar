# Group 2 — Mobile software completion

Owner authorization: 2026-10-11, Slice 13.1–13.8, autonomous software validation,
independent review, checkpoint commits and a draft PR only. Slice 14 is not begun.
Status: **IN PROGRESS / NOT OWNER APPROVED / NOT PRODUCTION READY**.

## Baseline and boundaries

Separate worktree `mobile-completion/oscar`, branch
`build/slice-13-mobile-completion`, exact Group 1 base
`dcfd31bca6fbd8080f4c20bebe3d448e4bd8dc2f`. GitHub readback confirms that
head and Group 1 PR #2 remains open/draft. Original worktrees, origin, main/work,
older PRs and evidence remain untouched.

Read the Group 1 report, independent review, security regressions and cumulative
ledger. Slice 09's Kotlin/Compose `:app`, existing `CoreSession`, scoped
`CoreClient`, Keystore, native confirmation, notification, assistant and audio
adapters are present. `:expression` is the shared native renderer/controller.
No second Android reasoning, memory, task or routing runtime will be created.

Dependency baseline: AGP 8.13.2, Gradle 8.13, Kotlin 2.3.20, Compose BOM
2026.03.00, compile/target SDK 36, min SDK 30, Java 17 bytecode. Versions are
preserved; this is compatibility evidence, not a newest-version claim.

## Design hypothesis

Operate inside Quietly Alive + Playful Precision: one state-driven shared Orb,
restrained native typography, a compact writing surface, one relevant current
item, and deeper task/device/privacy detail on request. Home is not a transcript
or dashboard. The object persists as screens change. Real waiting, execution,
verification, attention, unavailable and mute remain distinct. Character delivery
never creates operational facts. No continuous decorative animation.

Canonical SVG is immutable. Existing shared weighted, interruptible native
expression motion is reused. Android screenshot protection, denial paths,
permission separation and Core signing/authorization remain mandatory.

## Validation policy

Each stage records build, JVM, Compose/emulator, security/Core readback,
lifecycle/stale-callback checks, rendered captures and independent review before
checkpoint. Synthetic screen states are SIMULATED_ONLY; actual isolated
Core/Android readback is REFERENCE_VERIFIED. No phone/OEM/audio/owner PASS.
Curated captures go in `docs/ui/mobile/completion`; raw sequences remain outside
Git with hashes. Sensitive production screens retain FLAG_SECURE.

All unresolved Group 1 manual/device and critical-confirmation obligations carry
forward in the cumulative ledger. A draft candidate is not merge or release
authorization.

## Checkpoints

Phase 0 and 13.1–13.8 results and commits are appended after observable proof.

## Phase 0 — integrity and security

Exact Group 1 baseline rerun in its unchanged worktree: **551 tests, 6 optional
skips, zero failures**. Native Android baseline debug/test APK builds and JVM
checks PASS. Real JVM RSA-PSS/isolated Core readback PASS. The initial concurrent
new-worktree run intentionally saw the newly added discard regression fail;
that red reproduction is not the exact-baseline result.

Independent security review confirmed unintended node-wide Desktop discard and
Mobile private request/result disclosure to replacement sessions. Desktop discard
now matches session and node. New Mobile requests reuse existing Runtime transient
privacy, session provenance, same-session reported context and discard; no parallel
runtime or chat archive. Legacy durable private content is withheld; no destructive
history migration. Full bounded review/request/scope binds the signed descriptor;
oversized review fails before challenge creation. Critical authority remains
BLOCKED because the current Core cannot attest strong owner confirmation.

Independent **118 tests PASS**, Ruff/mypy PASS. See
[baseline review](reviews/GROUP-02-BASELINE.md). Android API 36.1 reference AVD
reproduced the historical SurfaceFlinger `hasReadColorBufferDma` platform crash;
its failed activity/Compose runs are FAILED platform evidence. A separate API 35
reference image is being prepared. No phone acceptance or test PASS inferred.

## 13.1 — Presence / Home

Replaced the static Home image with the existing shared Compose ExpressionPresence.
An opaque epoch-bound adapter maps admitted local readback to resting, attentive,
processing, executing, verifying, waiting and unavailable/error presentation.
Private text/IDs never enter motion events; observations expire, heartbeat updates
do not replay transitions, OS duration scaling and shared reduced-motion/lifecycle
behavior remain intact. One approval-prioritized ongoing item is shown on Home.
The same object persists above secondary screens; no fabricated awareness/voice.

Independent review corrected mismatched decision captions and competing Home
items. It also found the inherited active-microphone revoke gap: capture now checks
both OS and local grants before each delivery, and local revocation stops the
foreground service. Denied-permission Compose regression checks that boundary.
Full synthetic in-flight Voice adapter exercise belongs to 13.5.

Validation: **10 app + 5 expression JVM tests**, **8 app Compose tests** with one
unrequested optional fixture skip, **3 expression emulator tests**, **54 focused
Core/security/Grid tests**, and real JVM/Core readback PASS. A fresh API35 AVD
uses the preserved earlier reference system image via supported `-sysdir`, with
its own data directory. No original AVD reset or cached-user state is reused.
The first API35 install raced initial boot and failed; after boot/unlock readback,
serial module runs pass. API36.1's compositor crash remains failed evidence.

Actual [native captures](../ui/mobile/completion/captures/13-1-home-unavailable.png),
[simulated verification render](../ui/mobile/completion/captures/13-1-verifying-simulated.png),
[receipt](../ui/mobile/completion/evidence/13-1.json) and
[independent review](reviews/13-1-INDEPENDENT.md). Captures assert production
FLAG_SECURE and temporarily clear it only inside disposable instrumentation.
Duplicate disconnected copy and detailed task labeling remain scoped later-stage
refinements, not privacy or execution defects. Phone/motion quality approval is deferred.
