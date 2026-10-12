# OSCAR — Group 2.5 Antigravity handoff

Prepared 2026-10-12 for the owner's planned Claude Opus 5.5 design work in
Antigravity. This document prepares that work; it does not start it or grant
production approval.

## Starting point

Repository: `Amaan27-Buzz/oscar`. Permanent checkout:
`D:\TheDawnlightGroup\DawnlightLabs\oscar`.
Groups 1 and 2 were consolidated by fast-forward into development `main` at
**`7773de8b794acf61ab6f035a28ada1fed98a3f77`**. Both Git refs and GitHub's API
confirmed that SHA. All 104 commits beyond the former `main` are preserved.
The handoff itself is a separate subsequent documentation commit; fetch and
branch from current verified `origin/main` when Group 2.5 is authorized.

PRs #1–3 were closed as incorporated/superseded, not individually merged through
GitHub. Their remote branches remain. [PR #4](https://github.com/Amaan27-Buzz/oscar/pull/4)
is **rejected visual design exploration**, excluded from this baseline. Its head
`86b874f15e1db671150f86e40beea3c7fd371ab6`, branch and evidence are historical
references only. Do not treat its visual decisions as design authority.

## Identity and design freedom

**Quietly Alive / Playful Precision:** one persistent intelligence, expressed as
a responsive object with restrained native clarity, deliberate gaze and timing,
and legible character at tiny sizes. Persona affects delivery, never operational
truth, permission or safety. The owner rejected static smiling Orbs on beige
card walls. Compilation and attractive screenshots do not establish owner
visual acceptance.

The canonical identity is [assets/brand/oscar-orb.svg](../../assets/brand/oscar-orb.svg).
It is immutable: do not redraw, replace or modify it. Expressive derivatives must
remain separate, preserve identity and receive review. Reuse the shared expression
engine and native renderer; do not introduce another animation/state authority.

Once the owner starts Group 2.5, Opus may explore Desktop and Android visual
hierarchy, typography, spacing, navigation, responsive composition, accessibility
and purposeful motion. Propose and validate small coherent changes, with owner
review before visual promotion. Existing palette/layout choices are starting
context, not a mandate to repeat rejected treatments. Avoid generic dashboards,
card walls, glass/neon decoration and fake telemetry.

## Implementation map and protected contracts

- Desktop React/TypeScript: `desktop/src/`, including `App.tsx`, `Act.tsx`,
  `presence/`, `DesktopExpression.tsx` and `style.css`. Native Tauri/Rust boundary:
  `desktop/src-tauri/src/`.
- Android Kotlin/Compose: `mobile/app/src/main/java/io/dawnlight/oscar/mobile/`,
  including `OscarApp.kt`, `InteractionScreens.kt`, `ActivityScreen.kt`,
  `DevicesScreen.kt`, privacy/settings and approval surfaces.
- Shared expression: `expression/core/`, `expression/react/`,
  `mobile/expression/`; exploration tool: `design/expression-lab/`.

Keep existing Core/Controller/Router/Grid ownership, signing and native approval
boundaries. Do not create an Android brain, alternate memory store or fake
operational state. Preserve exact task/operation/target/capability/plan review,
expiry and stale-callback guards, denial/discard/cancel behavior, session isolation,
private draft recovery, FLAG_SECURE, and independent perceive/retain/act grants.
UI must preserve reported/verifying/verified/failed/blocked/unknown distinctions.
Do not change providers, credentials, backend authority, runtime data, dependencies
or permission grants merely to simplify the design. No deployment, paid services,
Actions settings changes, Slice 14 or later groups.

## Focused reading and original evidence

Start with [DESIGN.md](../../DESIGN.md), [TASTE.md](../../TASTE.md),
[UI/avatar](../UI-AVATAR.md), [Mobile design](../MOBILE-DESIGN.md),
[Expression Core](../EXPRESSION-CORE.md), and
[expression validation](expression/VALIDATION.md). Consult the
[Group 1 ledger](../development/GROUP-01-DESKTOP-COMPLETION.md) and
[Group 2 ledger](../development/GROUP-02-MOBILE-COMPLETION.md) for functional
scope and evidence limits. These ledgers preserve historical candidate statements;
the consolidation disposition above is newer.

Inspect only a few original captures initially:

- [Desktop compact presence](../ui/desktop/completion/evidence/12-6-compact.png)
- [Desktop exact approval](../ui/desktop/completion/evidence/12-5-approval.png)
- [Android reference response](../ui/mobile/completion/captures/13-2-reference-home-response.png)
- [Android privacy](../ui/mobile/completion/captures/13-6-reference-privacy.png)

These are software/reference evidence, not owner quality approval. Load additional
source or captures only for the specific flow being changed; do not copy the
repository, raw logs or backend source into the design context.

## Acceptance still outstanding

Local consolidation checks passed: Core 553 executed/6 optional skips, Desktop 56,
Rust 12, shared expression 36, Android JVM/debug/instrumentation APK/lint,
lint/types and repository/secret checks. Retained reference emulator booted at
SDK 35. Remote exact-head CI remains **BLOCKED** (Actions disabled, zero checks);
its settings were preserved. This is a development baseline, not distribution.

Real phone/OEM, microphone/speech/audio routes, Windows physical interaction and
display, hardware, owner visual, production/distribution and security acceptance
remain outstanding. Critical-risk strong-confirmation implementation remains
**BLOCKED**. Group 2.5 design work cannot mark any of these complete.
