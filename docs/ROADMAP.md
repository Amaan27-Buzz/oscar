# OSCAR — Canonical Roadmap

**Active local work, 2026-10-21:**
[full software completion](development/OSCAR-FULL-SOFTWARE-COMPLETION.md)
supersedes the earlier C1/C2-only scope. Groups 4–6 remain in progress; canonical
Slices 00–20 and deferred hardware boundaries are preserved.

**Current roadmap — 2026-10-18.** Exactly 21 top-level slices (00–20), preserved for historical compatibility. **Groups 4–8 now determine execution order**, not the old numerical "physical hardware next" sequence. Read [active delivery plan](DELIVERY-PLAN.md), [checked capability status](CURRENT-STATUS.md), [canonical numbering](SLICE-NUMBERING.md) and [build gates](BUILD-GATES.md). Historic detailed slices/PR instructions remain available in Git history and dated evidence, not active here.

**Truth:** software integrated ≠ owner/device verified ≠ remote deployed. Gate A/B scoped PASS, Gate C/D PARTIAL, Gate E NOT PASSED.

## Development principle

Current local software work: [Group 5 C1/C2 foundation and acceptance](development/GROUP-05-CAPABILITY-IDENTITY.md),
based on the unmerged D2 candidate. This adds no slice numbers or gate promotion.

One OSCAR identity and continuous relationship → Controller/Personal Policy → canonical Event Archive and Memory Fabric → authorized Grid and Worker/Executive → evidence and independent verification → native Desktop and Android Presence. Perception ≠ retention ≠ action. No fake success; no alternative Core.

## Slice 00 — Repository / architecture foundation

**SOFTWARE ACCEPTED.** Product, security, evidence and modular runtime contracts.

## Slice 01 — OSCAR Core Loop

**SOFTWARE ACCEPTED / Gate A.** Objective → bounded action → result → independent verification.

## Slice 02 — OSCAR Decision / Epistemic Controller

**SOFTWARE ACCEPTED / Gate A.** Deterministic epistemic routing, evidence and freshness.

## Slice 03 — Native Transport + Capability Catalog + Connection Grid foundation

**LOCAL SOFTWARE ACCEPTED / Gate A.** Group 4/D2 now implements authenticated TLS transport and independent Core/Worker processes in the current draft candidate. Independent hosted Internet acceptance remains NOT_RUN; see the [connected evidence ledger](development/GROUP-04-D2.md).

## Slice 04 — Native Model Router

**SOFTWARE ACCEPTED / Gate A.** Model/provider selection and fallback, not proof of hosted production models.

## Slice 05 — Real machine Worker + remote continuation

**LOCAL-ALPHA SOFTWARE ACCEPTED / Gate B.** Files/Git, PowerShell, UIA, isolated browser and durable continuation verified within bounded scope; broad computer use and remote Worker **Group 5 C1**.

## Slice 06 — OSCAR Memory Fabric + Personal Policy + live context

**LOCAL-ALPHA SOFTWARE ACCEPTED / Gate B.** SQLite WAL/FTS5 canonical archive, Qdrant/Graphiti/Neo4j derived indexes, personal policy and accepted GitHub OAuth/federation. Hosted memory and broad live providers **Groups 4–5**.

## Slice 07 — OSCAR Edge + reflexes

**SIMULATED SOFTWARE ACCEPTED / physical DEFERRED.** No real ESP32/Pico GPIO/UART/watchdog/E-stop evidence. Resume in **Group 8 / Slice 18**.

## Slice 08 — Voice Core + Voice Identity + Voice Match/Map + Persona runtime

**REFERENCE SOFTWARE ACCEPTED / owner audio PARTIAL.** Real Android/Windows voice wake, STT/TTS, AEC/barge-in and Match/Map **Group 5 C4**.

## Slice 09 — OSCAR Mobile + communication + Connection Grid owner controls

**SOFTWARE MERGED / physical device PARTIAL.** Native Compose and scoped owner control; hosted-Core/phone pairing **Group 5 D3/D4**.

## Slice 10 — OSCAR Desktop runtime foundation

**SOFTWARE MERGED / everyday remote use PARTIAL.** Tauri/Rust/React Companion/Workspace; real installed remote Worker and broad native capability acceptance **Group 5**.

## Slice 11 — OSCAR Expression / Character System

**SHARED SOFTWARE INTEGRATED, final character/device review OPEN.** Keep canonical Orb immutable and state truthful.

## Slice 12 — OSCAR Desktop experience and visual system

**Group 2.5A [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) MERGED, provisional owner visual PASS.** Full physical/use acceptance open.

## Slice 13 — OSCAR Mobile experience and visual system

**Group 2.5B [PR #6](https://github.com/Amaan27-Buzz/oscar/pull/6) MERGED, owner UI/UX APPROVED.** Real phone/OEM/voice/biometric acceptance pending.

## Slice 14 — World Model + Perception Fabric + Sentry + optional Journal

**Group 3 [PR #7](https://github.com/Amaan27-Buzz/oscar/pull/7) SOFTWARE INTEGRATED, Gate D PARTIAL.** Local authorized perception and Sentry state/recovery. Live external environmental source and owner capture acceptance **Group 5 C4**.

## Slice 15 — Commissioning / setup

**Group 3 SOFTWARE INTEGRATED, Gate D PARTIAL.** Trusted-local enrollment, Vault, Persona, policy and logical Voice composition. Hosted remote pairing, actual accounts/owner hardware **Groups 4–5 D2–D4**.

## Slice 16 — Full Avatar / Presence integration

**Group 3 SOFTWARE INTEGRATED, Gate D PARTIAL.** Shared leased Presence, typed AIE/native presentation and guarded optional Android overlay. Real multi-device/OEM/widgets/accessible AIE **Group 5**.

## Slice 17 — Executive Planner + durable Workers + learning

**Group 3 SOFTWARE INTEGRATED, Gate D PARTIAL.** Bounded reviewed DAGs, persistent scheduling, scopes, idempotent recovery and typed Worker/task views. Remote Workers, native creation/editing, live providers and evaluated learning **Group 5**.

## Slice 18 — Physical/device expansion + specialist engineering

**DEFERRED TO GROUP 8.** ESP32/Pico physical/safety acceptance and optional additional devices when available. **Not a prerequisite for narrower Group 6 operational alpha**, but still required for unamended full physical Gate C/E claims.

## Slice 19 — Reliability/security/truthfulness hardening

**IN PROGRESS THROUGHOUT GROUPS 4–8; NOT PASSED.** TLS/secret/revocation/remote privacy for Group 4; OS controls, Full Access, plugin isolation, voice and AIE for Group 5; recovery/soak for Group 6; local/cloud migration and physical safety for Groups 7–8. Internet-facing hardening cannot wait until the end.

## Slice 20 — Unified Alpha + adaptive interaction validation

**FORMAL PASS NOT EARNED.** Group 6 can verify an explicitly **scoped Cloud–Desktop–Phone operational alpha** with real devices, memory, authorized action, verification, voice and continuity. Formal Slice 20/Gate E PASS must not omit still-mandatory physical Edge and other Gate C/D/E requirements absent a separate explicit gate revision.

## Review clubs / checkpoints

| Group / gate | Coverage | Current state |
| --- | --- | --- |
| Gate A / foundation | Slices 01–04 | Scoped **PASS** |
| Gate B / foundation | Slices 05–06 | Local-alpha **PASS** |
| Gate C | Slices 07–10 | **PARTIAL**; physical/owner acceptance outstanding |
| Character/Design | Slices 11–13 | Software/UI merged; Desktop provisional, Mobile owner approved |
| **Group 3 / Gate D** | **All Slices 14–17** | PR #7 **MERGED**, Gate D **PARTIAL** |
| Gate E | Slices 18–20 | **NOT PASSED** |
| **Group 4** | Delivery D1/D2; existing slices' remote obligations | D1 PR #8 merged; connected D2 software candidate under verification |
| **Group 5** | Delivery D3/D4/C1–C4; existing slices' live obligations | Connected/native/computer use/plugins/access/voice |
| **Group 6** | Narrow Slice 20 operational-alpha evidence | Daily owner acceptance; **not** full gate PASS |
| **Group 7** | Dedicated home-server laptop | Later, hardware-dependent |
| **Group 8** | Slice 18 and residual Slices 19/20 | Later, physical/full gate evidence |

**Current checkpoint:** Group 4/D2 + Group 5/D3–D4 connected software, with a bounded C1 scoped-file vertical slice, in one draft PR. Oracle hosting and owner-device commissioning remain separately authorized. Do not reopen merged PR #7 or begin ESP32/Pico work. [Delivery groups and checklist](DELIVERY-PLAN.md).

## Historical scope codes (preserved for acceptance tooling)

Slice 07 was recorded as **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**, with real firmware/silicon status **DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED**. The original plan's former Slice 17 “Unified Alpha” is canonical **Slice 20** today; the new Group 6 scoped alpha does not erase these deferred physical obligations. See [Group 8 plan](DELIVERY-PLAN.md).
