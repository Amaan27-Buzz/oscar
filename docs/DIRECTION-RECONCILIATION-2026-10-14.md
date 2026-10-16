# OSCAR — Documentation reconciliation (2026-10-14)

**Later owner correction — Group 2.5B:** the Codex ImageGen/Figma baseline is selected for production Android; the Gemini Argon external prototype is rejected. Native implementation and phone evidence are recorded in [Group 2.5B](ui/mobile/group25b/README.md). The earlier documentation-only snapshot below is retained as historical context and does not describe the current implementation candidate.


**Status:** Active-direction documentation update on `main`. No application source, credentials, Git history, screenshot evidence, or acceptance receipts are changed by this pass.

## What supersedes what

| Topic | Earlier/outdated active assumption | Current authoritative direction | Primary source |
|---|---|---|---|
| Git/merge status | Desktop Group 1/2/2.5A treated as draft/unmerged | Software foundations and [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) merged to `main`; Group 2.5A owner **interim visual pass**, final integrated acceptance open | [README](../README.md), [Roadmap](ROADMAP.md) |
| Desktop UI | Companion expands into the entire chat/action app | **Tiny Orb Companion + separate full Workspace** (one Tauri process) | [Surfaces](SURFACES.md), [Desktop ownership](design/DESKTOP-COMPANION-WORKSPACE.md) |
| Text Tools / Act | Standalone primary product destinations and technical forms | **Contextual capabilities within continuous Conversation** | [Product direction](PRODUCT-DIRECTION.md), [Features](FEATURES.md) |
| Activity | Developer-facing task inspector as principal experience | Operational history, progress, outcomes, verified evidence and decisions in plain language | [Desktop ADR](decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) |
| Automations | Form-level immediate actions or fake scheduled Workers | User-friendly view of **actual** jobs, schedules, triggers, conditional watches, named subordinate Workers/Protocols as they become backed by Core | [Workers](WORKERS.md), [Product direction](PRODUCT-DIRECTION.md) |
| Full Access | Broad ordinary autonomy with protected-action confirmation | That definition is **Secure**. Full Access is unrestricted owner-delegated OSCAR action autonomy after explicit activation, without OSCAR per-action prompts, subject to genuine platform access/safety and revocation. **Not yet activated/implemented** | [Security](SECURITY.md), [Desktop ADR](decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) |
| Modes | One mixed access/listening/autonomy switch | Independent **Access**, **Awareness/Sentry**, **Worker autonomy**, and **observe/retain/action** grants | [Personal Policy](PERSONAL-POLICY.md), [Voice/Sentry](VOICE-SENTRY.md) |
| Visual style | Generic cards or anti-neumorphic wording | Owner-approved **restrained, accessible neumorphism** on Desktop; typography-forward, original illustrations and consistent Orb on Mobile | [Design](../DESIGN.md), [Taste](../TASTE.md) |
| Mobile scope | Finished new Mobile UI implied by existing reference baseline | Native Android foundation exists, but **new Group 2.5B visual direction still being explored**. 15 screen images, 1 design board, 5 component boards + separate UI-only Compose prototype (`oscar-ui-test`). The 56-experience inventory is not 56 production routes | [Mobile design](MOBILE-DESIGN.md) |
| Future adaptive UI | Static replies only or premature build in Mobile mockup | **Adaptive Interface Engine**, typed trusted interactive components inside one conversation; proposed Slice 16/17/19/20 rollout. **Not built** | [AIE](ADAPTIVE-INTERFACE.md) |
| Sentry & named Worker autonomy | UI implies always-on monitoring and persistent autonomous bots now | Slice 14 real awareness/World Model; Slice 17 executive/long-lived Worker scheduling, with truthful inactive states before integration | [Roadmap](ROADMAP.md), [Features](FEATURES.md) |
| Canonical slice numbering | Former 09R/10R/13A/13B, or old 00–17 map | **Exactly 00–20**; older IDs are provenance aliases, not active stages | [Slice numbering](SLICE-NUMBERING.md) |

## Document inventory for comparison

**New:** `docs/PRODUCT-DIRECTION.md`, `docs/ADAPTIVE-INTERFACE.md`, this reconciliation note.

**Updated active entry points:** `README.md`, `DESIGN.md`, `TASTE.md`, `docs/PRODUCT.md`, `docs/FEATURES.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/SLICE-NUMBERING.md`, `docs/SURFACES.md`, `docs/MOBILE-DESIGN.md`, `docs/DECISIONS.md`, `docs/design/DESKTOP-COMPANION-WORKSPACE.md`, `docs/decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md`.

**Not rewritten:** prior dated Gate receipts, native screenshots, old PR evidence, historical checkpoints and implementation source. Some past-tense passages or named legacy references are intentionally retained for provenance. They are **not** current task instructions if contradicted by the active documents above.

## Remaining implementation / acceptance gaps

- Secure/Full Access standing authority, target epoch/revocation and local/remote security enforcement are **not implemented**.
- Sentry/World Model, persistent named Worker scheduling and full Executive are **planned**.
- Adaptive UI is **planned**.
- Mobile experimental mockup/ImageGen visuals are **not** production Android integration.
- Desktop UI is **provisionally** accepted; final cross-device experience, physical phone/voice/Edge and production acceptance remain open.
- Remote CI may be unavailable; this docs-only GitHub update **does not assert passing builds/tests**.

## Maintainer pull and review

From a clean permanent checkout:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git log --oneline --max-count=25
git diff 43c15d37a6421d438b8101d5e322489ae452b20d..main -- README.md DESIGN.md TASTE.md docs/
```

Inspect the changed active documents and compare them with this table. Avoid interpreting archived dated sections as current directives. After pulling, run `python -m scripts.check_repository` and `python -m unittest tests.test_canonical_slice_docs` locally if the environment is available; these checks were **not run by the GitHub-only documentation editing session**.
