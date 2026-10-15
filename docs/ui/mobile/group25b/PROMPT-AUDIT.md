# Original Group 2.5B prompt audit — 2026-10-15

**Result: IMPLEMENTATION COMPLETE / OWNER REVIEW PENDING, with the explicit
substitutions and capability/source limits below.** This is not a claim that
every literal emulator requirement or physical capability has passed.

The later [Preferences redesign](PREFERENCES-REVIEW.md) supersedes settings-page
screenshots and provides a fresh build/device receipt in `preferences-review.json`.
The original audit receipt below remains historical evidence of its own APKs.
The subsequent [integrated visual craft review](CRAFT-REVIEW.md) supersedes
visuals and installed APK hashes while retaining the capability/source limits.
The later [motion follow-up](MOTION-REVIEW.md) has the current installed-APK
receipt and native navigation/selection frame evidence.

The owner supplied the original 18-section prompt again after the whole-app
review. This audit compares it with production source, preserved assets,
verification receipts and the subsequent owner instructions in the same chat.
The audit found and corrected stale active guidance in `DESIGN.md`,
`docs/ARCHITECTURE.md` and `docs/ADAPTIVE-INTERFACE.md`: none may keep the rejected
Argon prototype as an active or future component source. A stale Devices artwork
description and the misleading label on the earlier test run were also corrected.

## Requirement reconciliation

| Original section | Result and evidence |
|---|---|
| 1. Production repository and references | Production `mobile/` on the existing checkout. All 21 original PNGs are tracked and hash-verified; ten illustration-only crops match `mobile/illustration-assets.json`. The rejected repository supplied no implementation. [Visual provenance](README.md#visual-authority-and-preservation) |
| 2. Read existing repository first | Baseline/main/toolchain and production architecture were recorded before implementation. Current audit verifies the actual source, artifacts and remote draft rather than relying on older screenshots. Figma screenshot retrieval succeeded; editable design context was unavailable, so the explicitly permitted local-source fallback was used. [Baseline and reference record](README.md) |
| 3. Git workflow and preservation | Integration base `b941357d6e0b88d61170f4895e6dbb1936202ed8`; branch `codex/mobile-group-2.5b`; same Windows checkout. Logical implementation/evidence commits, tracked source images, no history rewrite, new worktree or merge. [Draft PR #6](https://github.com/Amaan27-Buzz/oscar/pull/6) |
| 4. Product direction | One Core-owned OSCAR, native portable conversation/control surface. Later owner instructions explicitly replace promotional/dense layouts and duplicate navigation; those corrections take precedence over literal screenshot composition. [Whole-app review](SCREEN-REVIEW.md) |
| 5. Design system | Native theme, offline Manrope/Fraunces typography, tactile surfaces, glyphs, rows, status, dialogs, disclosures and feature compositions. Original illustration crops only; no screenshot-backed controls. [Components and hierarchy](README.md#native-composition-and-navigation-decision) |
| 6. Canonical Orb | SVG SHA-256 `728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`; source and packaged runtime data unchanged. Shared renderer/controller preserved; actual state and reduced motion retained. Major expression refinement remains deferred as requested. |
| 7. All 15 heroes | All 15 are native functioning or explicitly unavailable experiences, not just Home. Conversation, Reading, Voice, Automations, Worker/Create, Activity/Task/Decision, Devices/Awareness, Today, Access and Preferences are individually mapped and captured. [Hero implementation](README.md#hero-implementation-and-truth-boundaries), [15 comparisons](COMPARISONS.md) |
| 8. Broader IA and navigation | 25 implemented screens/routes reviewed; 56 derived experience mappings cover primary/secondary/contextual/system/unavailable surfaces. Three bottom tabs on primary destinations; Devices/Preferences in the app bar; one Back bar on secondary routes. **Exact original numbered 56-row reconciliation is source-limited**, as explained below. [Experience map](EXPERIENCES.md), [25-screen ledger](SCREEN-REVIEW.md) |
| 9. Core and architecture | CoreSession, transport, signing/confirmation/vault, native voice/services/notifications, shared Expression source and Core Python are unchanged from integration. `MobileState` changes only destination labels/adds Automations. Domain authority stays separate from UI navigation/ephemeral state; no second memory store, scheduler or reasoning service. |
| 10. Truth and security | Current state/readback, reported-vs-verified results, expiry, exact material and legitimate native confirmation retained. Review/tap is not consent or execution proof. No fabricated connections, microphones, progress, memory or completed mutations. Native/transport/security and privacy tests cover these boundaries. [Receipts](prompt-audit.json) |
| 11. Implementation stages | Baseline/mapping, shared system, conversation vertical slice, remaining heroes/supporting routes, visual refinement and integrated tests are delivered in the existing branch. Later owner review added native rich Markdown/JSON, a compact decision page, compact Devices and the whole-app navigation/density pass. [Implementation record](README.md), [screen corrections](SCREEN-REVIEW.md) |
| 12. Native verification | Builds, JVM/lint, instrumentation, launch/navigation, disposable real Core/Grid HTTP flows, disconnected/reconnect states, reading, decisions, privacy, Voice failure/cancel, theme, 1.8× text, keyboard/insets, landscape, recreation/recovery and motion verified. **Samsung phone substituted for emulator at the owner's request.** Current full rerun and exact APK hashes are in [the audit receipt](prompt-audit.json). |
| 13. Visual evidence | Original reference, native capture, differences/corrections and remaining discrepancies exist for every hero. Panels preserve aspect ratios and equal display widths; captures use production composables with disclosed synthetic/reference data. **These are phone captures, not emulator captures or owner visual approval.** [Comparisons](COMPARISONS.md), [capture manifest](capture-manifest.json) |
| 14. Documentation reconciliation | Active product, Mobile, surfaces, features and roadmap guidance use the selected baseline and reject Argon. This audit closes the three remaining stale design/architecture references. Canonical 00–20 numbering and historical exploration/test records remain preserved. |
| 15. Definition of done | Met for the implementation/owner-review candidate under the later phone and visual-refinement instructions. Owner visual, broader physical capability and remote-CI acceptance remain separate; no Slice 13/Gate C physical PASS is inferred. Source limitations and backend-unavailable items remain explicit. |
| 16. Delivery/integration | Builds/static checks/tests and source/asset/capture review recorded; logical commits pushed to the existing open draft into main. No merge without approval. Audit adds documentation/evidence only; installed app/source hashes remain the verified UI build. |
| 17. Engineering report | Integration base above; UI implementation `856f0f99a624dc2f78202d943f8f5e7dead07687`; prior screen-review delivery `b4bd2e78f8c28ee065700affd95c5eeb85b71d7b`. This audit is a subsequent documentation/evidence commit in the same PR. Screens, components, integrations, tests, fixes, discrepancies, acceptance limits and owner decisions are linked here and in the receipt. The final response identifies the audit delivery head. |
| 18. Autonomous execution | Implementation, native review, fixes, evidence and draft delivery completed within scope. Emulator remains off to honor the later RAM/study instruction. No new Full Access, Sentry, Executive or AIE backend; no physical PASS, release or merge. |

## Explicit substitutions and remaining limits

- **Emulator:** the original requested API36.1 emulator/native captures and a ready
  emulator. Its package-manager/memory failure was recorded, then the owner
  requested stopping it to preserve Chrome/study RAM and authorized the USB phone.
  Real Samsung native UI/instrumentation and comparison evidence replace that
  requirement in this run. Emulator acceptance remains incomplete; it is not
  silently counted as PASS or restarted for this audit.
- **56-experience source:** available active docs describe that scope but contain
  no original numbered 56-row inventory. `EXPERIENCES.md` explicitly derives 56
  mappings from those docs and existing native flows. It is useful coverage, not
  proof that every item in an unavailable original list has been reconciled.
- **Existing API limits:** Mobile `text` accepts exactly a text payload
  (`oscar/mobile.py`); it does not expose attachment submission or archive-history
  retrieval. The app supports bounded chronological session readback, task
  responses/results and artifact/evidence metadata. Attachments and full archive
  retrieval are not implemented or claimed. Persona/memory policy editing,
  persistent Workers/scheduling, provider briefs, playback/enrollment, Sentry and
  genuine Secure/Full Access activation remain unavailable. Later backend work
  must not be fabricated to make this visual task look complete.
- **Real capabilities:** reference Core/Grid tests execute actual production HTTP
  paths with disposable synthetic identities/tasks. They are not live provider
  inference, owner enrollment or owner execution/consent. Actual microphone,
  playback/AEC/barge-in/Match/Map, Bluetooth, assistant-role invocation,
  notification ingestion/replies, biometric/PIN and sustained TalkBack acceptance
  remain pending. Existing Android foundations are preserved; this audit does not
  grant permissions or pair an owner account.
- **Remote CI and owner review:** GitHub Actions remains disabled (`enabled:false`),
  so CI is BLOCKED. Owner visual approval and merge approval are still required.
  The intentionally skipped test conditions are itemized in the receipt; a skip
  is not PASS. Gate C remains PARTIAL.

No additional in-scope UI implementation gap was found in this reconciliation.
The newly found active-documentation gaps are corrected in the audit change.
