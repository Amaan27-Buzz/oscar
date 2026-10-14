# OSCAR Slice Numbering — canonical plan from 2026-10-09

**Status:** CURRENT NUMBERING AUTHORITY.

The owner rejected mixing numbered slices with 09R, 10R, 13A/13B and prematurely generated design explorations. **One sequential set of top-level slice numbers** is now authoritative. Preserve historical PRs, evidence, commit messages, branch names and captured assets verbatim; do not rewrite history or rename a working PR merely to match new identifiers.

## Canonical sequence

| Slice | Focus | Current state |
|---|---|---|
| 00 | Repository and architecture | Accepted |
| 01 | Core Loop | Accepted |
| 02 | Decision/Epistemic Controller | Accepted |
| 03 | Native Transport, Capability Catalog, Grid | Accepted |
| 04 | Model Router | Gate A accepted scope |
| 05 | Machine Worker and continuation | Gate B accepted |
| 06 | Memory Fabric, policy and federation | Gate B accepted |
| 07 | Edge + reflexes | Software simulated foundation accepted; physical deferred |
| 08 | Voice Core / Identity / Persona | Reference software accepted; physical deferred |
| 09 | OSCAR Mobile foundation | Software merged; device acceptance deferred |
| 10 | OSCAR Desktop runtime foundation | Integrated software foundation; physical acceptance deferred; old PR #16 archival |
| **11** | **OSCAR Expression / Character System** | Shared renderer foundation integrated into reference apps; final character/device acceptance deferred |
| **12** | OSCAR Desktop visual/interaction design | **Group 2.5A interim owner pass; merged PR #5**; final owner/physical acceptance deferred |
| **13** | OSCAR Mobile visual/interaction design | Software/reference baseline integrated; **Group 2.5B visual exploration**; final redesign and phone acceptance pending |
| 14 | World Model, Perception, Sentry, optional Journal | Planned |
| 15 | Commissioning and setup | Planned |
| 16 | Full cross-device Avatar/Presence + typed adaptive presentation | Planned; extends 11; initial AIE contract |
| 17 | Executive Planner / durable Workers / learning / adaptive UI composition | Planned |
| 18 | Physical expansion and Edge acceptance | Planned |
| 19 | Reliability / security / truthfulness / adaptive UI hardening | Planned |
| **20** | **Unified Alpha + adaptive interaction validation** | **Planned; cannot PASS until every mandatory acceptance is genuine** |

**Total:** 00–20 inclusive, 21 canonical top-level slices. Future work uses `11.1`, `11.2`, etc. for **stages inside a slice**, not new numbered slices. Historical 09R/10R and 13A/B designations are **aliases**, not additional slices.

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

For Slice 11 (and subsequent 12/13), the user will run **GPT-6.1 Sol with High thinking effort** where available. Prompts must ask for deep, considered design work rather than rushing to three superficial alternatives or optimizing for screenshot count.

1. Study actual screenshots, canonical artwork, existing DESIGN/TASTE guidance and interaction states **before** sketching.
2. Articulate how OSCAR should *behave* and what character it expresses before picking shapes, shadows, colors or library components. The reference images of a small expressive desktop companion demonstrate persistent personality, glanceable reactions and nonverbal communication; they are **inspiration for responsiveness and presence, not artwork to copy**.
3. Explore real character design: eye/mark geometry, gaze, asymmetry, temporal microexpression, idle behavior, anticipation, response to interruption, emotion-as-delivery (not human-emotion inference), sleep/rest, surprise, hesitation and recovery. Avoid generic static happy-face avatar and ornamental breathing effects. Remain restrained rather than juvenile.
4. **Keep `assets/brand/oscar-orb.svg` immutable** as canonical source; any new expression/animated derivation must be separate, identifiable, faithful to identity and subject to owner approval. Owner may later approve evolution of the visual identity, but no coding model assumes that permission.
5. Visual character is a **real system**, not fake states: authoritative Core operational state vs non-authoritative expressive delivery must remain separate and predictable; no fake listening/thinking/verification.
6. Produce focused high-fidelity examples with studied motion curves, transition storytelling, interruption and reduced motion, small-scale legibility and perceptual continuity. Present working prototypes and frame sequences rather than still mockups alone.
7. Explain design choices, constraints and tradeoffs. Identify mediocre/AI-generated-looking output and iterate substantively before reporting completion; do not claim design acceptance after automated checks.
8. Use only legitimate free/open design references where practical; do not copy third-party art or ship paid animation dependencies by accident.
9. No unapproved backend/Core/security/permission changes to make presentation easier. Stage work for visual owner review before production integration.

## Current workflow and Git hygiene — 2026-10-14

The consolidated software foundations and Desktop Group 2.5A [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) are on `main`. Old branch names, PRs, screenshots and earlier acceptance statements are retained **as history**, never current operating instructions. The owner has accepted the **neumorphic Desktop direction provisionally**; final cross-device UI and physical/production acceptance remain open.

Group 2.5B Mobile UI exploration proceeds against the current production foundation, using 15 individual visual screen references, one system board, five component boards and a **separate** UI-only native Compose prototype before production integration. Build/test with existing emulator/SDK and avoid redundant AVDs, worktrees and huge caches. All prototypes must clearly distinguish simulated controls from operational Sentry, Workers or Full Access.

AIE is **future** work integrated into Slices 16/17/19/20, not an extra canonical numbered slice. See [product direction](PRODUCT-DIRECTION.md) and [AIE plan](ADAPTIVE-INTERFACE.md).

## Maintainer verification

The lightweight repository test `tests/test_canonical_slice_docs.py`
guards unique current roadmap headings, character/UI dependencies and key
entrypoint links. Dated past-acceptance records are **not** globally
search-and-replaced because their original slice numbers and status
claims document the historical event. Future wording must use the new
numbering and explicitly mark any historical snapshot.
