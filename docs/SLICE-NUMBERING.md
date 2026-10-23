# OSCAR Slice Numbering — canonical plan (updated 2026-10-18)

The 2026-10-23 local continuation extends existing slices with executable
normal-runtime recall, native memory management, MCP resource authorization and
reviewed model/browser workflows. See the completion ledger for source-scoped
software evidence; the physical/hosted acceptance distinctions below remain.

**CURRENT NUMBERING AUTHORITY.** There are **21 slices, 00–20**, with exactly one top-level ID each. The owner reorganized the **delivery groups and execution order**, not the existing slice identifiers. New **D1–D4** and **C1–C4** are checklist stages, **not numbered slices**. Do not revive old 09R/10R/13A/13B names in current plans; retain their historical provenance.

Read [active delivery plan](DELIVERY-PLAN.md), [checked status](CURRENT-STATUS.md), [roadmap](ROADMAP.md) and [build gates](BUILD-GATES.md).

## Canonical sequence

| Slice | Focus | Current accepted scope / outstanding |
| --- | --- | --- |
| 00 | Repository / architecture | Accepted |
| 01 | Core Loop | Accepted |
| 02 | Epistemic Controller | Accepted |
| 03 | Native Transport/Catalog/Grid | Local accepted; Internet remote Group 4 |
| 04 | Model Router | Gate A accepted |
| 05 | Windows machine Worker/continuation | Gate B local accepted; broad remote computer use Group 5 |
| 06 | Memory Fabric/Policy/federation | Gate B local accepted; cloud/provider work pending |
| 07 | Edge/reflex | Simulated software accepted; real hardware Group 8 |
| 08 | Voice Core/Identity/Persona | Reference accepted; owner real audio Group 5 |
| 09 | Mobile | Software merged; real owner phone Group 5 |
| 10 | Desktop | Software merged; real remote PC Group 5 |
| 11 | Expression/Character | Shared software integrated; device review outstanding |
| 12 | Desktop design | Group 2.5A PR #5 merged; provisional approval |
| 13 | Mobile design | Group 2.5B PR #6 merged; owner-approved UI/UX |
| 14 | World Model/Perception/Sentry | Single Group 3 PR #7 software merged; live sources pending |
| 15 | Setup/commissioning | Single Group 3 software merged; owner remote setup pending |
| 16 | Presence/typed adaptive UI | Single Group 3 software merged; real device/widgets pending |
| 17 | Executive/Workers/learning | Single Group 3 software merged; native controls/live acceptance pending |
| 18 | Physical expansion/Edge | **DEFERRED to Group 8** |
| 19 | Reliability/security/truth/AIE | Applied throughout Groups 4–8, NOT PASS |
| 20 | Unified Alpha | Formal Gate E NOT PASSED; scoped Cloud/Desktop/Phone alpha in Group 6 |

Gate A 01–04 and Gate B 05–06: PASS for documented scope. Gate C 07–10: PARTIAL. Design 11–13: software/incremental owner approval. Gate D 14–17: **PARTIAL although Group 3 PR #7 is merged with green CI**. Gate E 18–20: NOT PASSED.

## Updated delivery groups

| Group | Scope | Sequence |
| --- | --- | --- |
| Earlier foundation / Groups 1–2 / Group 2.5A/B | Slices 00–13 software/UI | Integrated per evidence |
| **Group 3** | **One batch of Slices 14–17** | MERGED; Gate D PARTIAL |
| **Group 4** | D1 Cloud persistent Core; D2 authenticated remote Grid | **NEXT** |
| **Group 5** | D3/D4 real Desktop/Android and commissioning; C1 computer use; C2 MCP/plugins; C3 Secure/Full Access; C4 voice/Workers/Sentry/Chief of Staff/AIE | After Cloud/Grid |
| **Group 6** | Real scoped Cloud–Desktop–Phone operational alpha | Does not mean full Gate E PASS |
| **Group 7** | Home-server laptop as future local/hybrid node | When hardware available |
| **Group 8** | Physical ESP32/Pico Slice 18 and remaining Slice 19/20 acceptance | After operational alpha |

A currently unfinished task from Slice 05–17 remains part of its canonical slice even if its **deployment/acceptance** is scheduled in Groups 4–6. Earlier historical naming and evidence retain original meaning.

## Historical alias map

| Former identifier | Current identifier |
|---|---|
| 13A.1 expression vocabulary | 11.1 Character language and emotion/expression mechanics |
| 13A.2 interactive lab | 11.2 Expression Lab / owner visual review |
| 13A.3 shared contracts | 11.3 Shared Desktop/Android renderer contract |
| 10R.0 lifecycle/baseline | 12.0 Baseline (already captured as a Slice 10/PR #16 experiment) |
| 10R.1 compact explorations | 12.1 Desktop compact presence (A/B/C are **unapproved historical explorations**) |
| 10R.2–10R.6 | 12.2–12.6 |
| 09R.1–09R.8 | 13.1–13.8 |
| former Slice 11 World Model | 14 |
| former Slice 12 commissioning | 15 |
| former 13B / remaining Slice 13 Avatar | 16 |
| former Slice 14 Executive Planner | 17 |
| former Slice 15 Physical/device expansion | 18 |
| former Slice 16 hardening | 19 |
| former Slice 17 Unified Alpha | 20 |

Preserve raw image paths such as `docs/ui/desktop/explorations/10R.1/`, screenshots, reports and historical test receipts. Their *historical* names may remain unchanged, but active planning and new PR prompts must use canonical slice numbers.

## Acceptance gates

- **Gate A 01–04:** existing PASS unchanged.
- **Gate B 05–06:** existing PASS unchanged.
- **Gate C 07–10:** **PARTIAL**; software merged, physical Edge/Voice/Mobile/Desktop owner acceptance and broad native/CI evidence remain pending.
- **Design acceptance 11–13:** character/visual interactions and cross-surface consistency, with owner review; this is a design checkpoint, **not** a substitute for any physical/software Build Gate.
- **Gate D 14–17:** World Model/Sentry, commissioning, full Presence integration and Executive Planner.
- **Gate E 18–20:** physical expansion, integrated hardening and **Slice 20 Unified Alpha**.

Early design/prototype work may occur despite deferred Gate C physical acceptance by prior owner decision. This does not silently turn Gate C into PASS.


## Owner quality bar for future model instructions

Use the model and thinking effort appropriate to the actual work; the owner has used **GPT-6.1 Sol at Medium** for focused Group 2.5 engineering, alongside separate image-design and Kotlin/Compose experiments. No single model/effort setting is a canonical product requirement. Prompts must ask for careful design and inspected native results rather than rushing superficial alternatives or optimizing for screenshot count.

1. Study actual screenshots, canonical artwork, existing DESIGN/TASTE guidance and interaction states **before** sketching.
2. Articulate how OSCAR should *behave* and what character it expresses before picking shapes, shadows, colors or library components. The reference images of a small expressive desktop companion demonstrate persistent personality, glanceable reactions and nonverbal communication; they are **inspiration for responsiveness and presence, not artwork to copy**.
3. Explore real character design: eye/mark geometry, gaze, asymmetry, temporal microexpression, idle behavior, anticipation, response to interruption, emotion-as-delivery (not human-emotion inference), sleep/rest, surprise, hesitation and recovery. Avoid generic static happy-face avatar and ornamental breathing effects. Remain restrained rather than juvenile.
4. **Keep `assets/brand/oscar-orb.svg` immutable** as canonical source; any new expression/animated derivation must be separate, identifiable, faithful to identity and subject to owner approval. Owner may later approve evolution of the visual identity, but no coding model assumes that permission.
5. Visual character is a **real system**, not fake states: authoritative Core operational state vs non-authoritative expressive delivery must remain separate and predictable; no fake listening/thinking/verification.
6. Produce focused high-fidelity examples with studied motion curves, transition storytelling, interruption and reduced motion, small-scale legibility and perceptual continuity. Present working prototypes and frame sequences rather than still mockups alone.
7. Explain design choices, constraints and tradeoffs. Identify mediocre/AI-generated-looking output and iterate substantively before reporting completion; do not claim design acceptance after automated checks.
8. Use only legitimate free/open design references where practical; do not copy third-party art or ship paid animation dependencies by accident.
9. No unapproved backend/Core/security/permission changes to make presentation easier. Stage work for visual owner review before production integration.


## Active working rule

The old 2026-10-14 "Mobile approval pending, Group 3 not started" workflow notes were superseded by the 2026-10-17 merger and 2026-10-18 owner sequencing decision. The latest authoritative tasks are [current status](CURRENT-STATUS.md) and [delivery plan](DELIVERY-PLAN.md). Preserve `assets/brand/oscar-orb.svg`, approved visual direction and all historical receipts.

## Maintainer verification

`tests/test_canonical_slice_docs.py` verifies one roadmap heading for each 00–20, UI dependencies and canonical entrypoint references. Do not rewrite dated evidence or Git history.
