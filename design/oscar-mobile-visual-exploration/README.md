# OSCAR Mobile visual exploration

**Selected production baseline — owner decision 2026-10-14:** these original images are the visual authority for production `mobile/` Group 2.5B. The external Gemini Argon experiment was rejected. Originals remain unchanged; see [native implementation and comparisons](../../docs/ui/mobile/group25b/README.md). The exploration notes below record how these assets were generated.


21 separate images generated with ChatGPT's built-in `image_gen`: one design-system board, 15 Android screens and five component boards. Image-only concepts for a later Kotlin/Jetpack Compose mockup; not implementation or runtime evidence.

## Direction

**Quietly Alive + Playful Precision:** warm paper, graphite nights, functional paper-cut illustrations, expressive editorial typography and restrained tactile relief. The owner selected **06 — Worker Detail** as the sizing/style anchor. Earlier screens were revised to reduce oversized elements and excessive copy. Prefer a short label, one useful sentence and progressive disclosure.

Warm light uses `#F5F1E7` / `#FAF7EF`, graphite `#1A1B18`, secondary `#77766B`, blue `#2F8FF5`, yellow `#FFC83D` and red `#EF4348`. Supporting sage, clay, powder and lilac distinguish responsibilities and context. Intended typography: Manrope UI, Fraunces accent, tabular numerals. Generated lettering approximates these families.

Functional artwork changes with the feature: a notebook and agenda on Home, woven Worker identities, recognizable devices, an illustrated day path and an evening room for Awareness. Conversation and Reading emphasize text; Voice and Activity use quiet graphite.

## Full index

| File | Purpose |
| --- | --- |
| [00 — Design system](design-system/00-oscar-mobile-design-system.png) | Palette, materials, type, geometry, icons, control states and motion. |
| [01 — Home](screens/01-oscar-home.png) | Presence, one useful commitment and conversational entry. |
| [02 — Conversation](screens/02-continuous-conversation.png) | One continuous relationship and a calendar draft. |
| [03 — Expanded Reading](screens/03-expanded-reading.png) | Structured response, further reading and contextual actions. |
| [04 — Voice](screens/04-voice-interaction.png) | Active listening, visible microphone state and interruption. |
| [05 — Automations](screens/05-automations-overview.png) | Continuing responsibilities with distinct identities. |
| [06 — Worker Detail](screens/06-worker-detail.png) | Owner-selected style anchor; autonomy, access and next run. |
| [07 — Create Automation](screens/07-create-automation.png) | Natural-language request and structured review. |
| [08 — Activity](screens/08-activity-feed.png) | Graphite operational timeline with attention and outcomes. |
| [09 — Active Task](screens/09-active-task.png) | Remote proposal work, meaningful steps and controls. |
| [10 — Approval](screens/10-approval-decision.png) | Exact before/after, consequences and approve/deny. |
| [11 — Devices](screens/11-devices.png) | Recognizable embodiments and plain availability. |
| [12 — Awareness](screens/12-sentry-awareness.png) | Future Sentry concept; awareness/capture off and unavailable states. |
| [13 — Today](screens/13-today-chief-of-staff.png) | Illustrated commitments and one useful exception. |
| [14 — Access Modes](screens/14-access-modes.png) | Ask, Secure and genuine Full Access; activation unavailable. |
| [15 — Preferences](screens/15-preferences.png) | Persona, voice, privacy, memory, access, permissions and appearance. |
| [A — Navigation & Conversation](components/A-navigation-and-conversation.png) | App bars, navigation, composers, messages, menus and sheets. |
| [B — Presence & Expression](components/B-oscar-presence-and-expression.png) | Orb sizes, state compositions, privacy indicators and keyframes. |
| [C — Workers & Automations](components/C-workers-and-automations.png) | Identities, triggers, schedules, autonomy and lifecycle controls. |
| [D — Trust & Decisions](components/D-trust-sentry-and-decisions.png) | Access, awareness, permissions, approvals and capture states. |
| [E — Devices & System Patterns](components/E-devices-activity-and-system-patterns.png) | Devices, task states, timelines, errors, widgets and notifications. |

## Reuse in the mockup

- Three main destinations: Conversation / Automations / Activity. Devices and Preferences are secondary; detail screens use contextual back navigation.
- Moderate control geometry, shared light direction and clear boundaries; no shadow on every object. Target 48dp interactions, 4/8 spacing, 8/12/18dp radii; use the accepted screen as the visual scale reference.
- Morning Brief uses a woven sage/ochre bookmark, Proposal Watch a blue folded document, Weekly Reset a clay half-ring. None is another OSCAR mascot.
- Keep access, awareness, retention and Worker autonomy independent. Ask approves changes; Secure requires consequential consent; Full Access delegates unrestricted operation over available capabilities without OSCAR per-action prompts after activation.
- Secure/Full Access activation and Sentry remain unavailable in these concepts. Planned controls and illustrative schedules never establish runtime capability.
- Motion transforms existing geometry; the board illustrates timing and static reduced-motion fallbacks, not runnable animation.

## Review and remaining limits

All outputs were visually reviewed; excess copy, oversized early layouts, navigation on detail pages, Worker identity drift and misleading component labels received generation passes. Portrait originals are **841 × 1870**; landscape originals are **1672 × 941**. Files are native generator outputs, copied without resizing, upsampling or recompression.

Small variations remain in icon geometry, shadow strength, typography and Orb raster interpretation. The owner accepted the generated Orb direction during this exploration; it is not a pixel-exact reproduction or approved expressive renderer. The later mockup should use the canonical SVG/shared renderer and normalize one component library. The boards define intended tokens rather than measurable font/contrast/touch-target guarantees.

The canonical [Orb source](../../assets/brand/oscar-orb.svg) remains unchanged: SHA-256 `728AEAC3C9AA590B67D45C469735E919EDE93A8503964E24F0F4AF18CDA066C5`. No Android/Core code, existing design assets or Git history changed. No emulator, build, device, accessibility-runtime or animation testing was performed.

Product inputs: [Product](../../docs/PRODUCT.md), [Mobile design](../../docs/MOBILE-DESIGN.md), [Surfaces](../../docs/SURFACES.md), [authority decision](../../docs/decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md), [Expression](../../docs/EXPRESSION-CORE.md), [global design](../../DESIGN.md), and the existing [Desktop material captures](../../docs/ui/desktop/workspace/material-review/README.md).

Generation prompt set: established palette/material/type → supplied canonical Orb + owner-selected Worker-detail reference → individual feature composition with concise copy → targeted correction passes. Exact prompts and original-generation paths are preserved in the local [generation record](C:/Users/Amaan/.codex/generated_images/01a139ab-152f-78b1-a4c4-265a5107b644/oscar-mobile-generation-record.json).
