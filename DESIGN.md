---
name: OSCAR
description: Quietly Alive + Playful Precision across native Desktop and Android surfaces.
colors:
  desktop-leaf: "#F8F9F6"
  desktop-surface: "#FFFFFF"
  desktop-ink: "#202923"
  mobile-paper: "#F5F1E7"
  mobile-surface: "#FFFDF8"
  mobile-ink: "#1A1B18"
  secondary-text: "#58635B"
  divider: "#D7DDD6"
  hover: "#E8EDE6"
  focus-blue: "#1969BC"
  oscar-yellow: "#FFC83D"
  decision: "#FFF0B7"
  mobile-container-high: "#EAE5DA"
  mobile-container-highest: "#E0E7DE"
  mobile-outline: "#78857A"
  mobile-error: "#B6322B"
  desktop-error: "#A1352D"
  selection: "#FFDD78"
  dark-leaf: "#1D2622"
  dark-surface: "#27312B"
  dark-ink: "#F2F5EE"
  dark-secondary-text: "#B6C3B9"
  dark-divider: "#3E4C42"
  dark-hover: "#303E35"
  dark-focus-blue: "#91C4FF"
  dark-yellow: "#FFCF5A"
  dark-decision: "#453C22"
  dark-decision-text: "#FFEAB0"
  dark-mobile-container-highest: "#30342D"
  dark-mobile-container-low: "#20231E"
  dark-mobile-container-lowest: "#151713"
  dark-mobile-outline: "#999D8D"
  dark-error: "#FFB4A9"
typography:
  desktop-headline:
    fontFamily: "'Source Serif 4', Georgia, serif"
    fontSize: "30px"
    fontWeight: 450
    lineHeight: 1.18
    letterSpacing: "-0.025em"
  desktop-activity-headline:
    fontFamily: "'Source Serif 4', Georgia, serif"
    fontSize: "34px"
    fontWeight: 450
    lineHeight: 1.18
    letterSpacing: "-0.025em"
  desktop-body:
    fontFamily: "'Source Sans 3', 'Segoe UI', sans-serif"
    fontSize: "16px"
    lineHeight: 1.5
  desktop-reading:
    fontFamily: "'Source Sans 3', 'Segoe UI', sans-serif"
    fontSize: "17px"
    lineHeight: 1.6
  desktop-label:
    fontFamily: "'Source Sans 3', 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: "18px"
  mobile-headline-large:
    fontFamily: "Source Sans 3"
    fontSize: "26sp"
    fontWeight: 600
    lineHeight: "32sp"
  mobile-headline-medium:
    fontFamily: "Source Sans 3"
    fontSize: "24sp"
    fontWeight: 600
    lineHeight: "30sp"
  mobile-title-large:
    fontFamily: "Source Sans 3"
    fontSize: "22sp"
    fontWeight: 600
    lineHeight: "28sp"
  mobile-title-medium:
    fontFamily: "Source Sans 3"
    fontSize: "18sp"
    fontWeight: 600
    lineHeight: "24sp"
  mobile-body-large:
    fontFamily: "Source Sans 3"
    fontSize: "18sp"
    lineHeight: "28sp"
  mobile-body:
    fontFamily: "Source Sans 3"
    fontSize: "16sp"
    lineHeight: "24sp"
  mobile-label:
    fontFamily: "Source Sans 3"
    fontSize: "14sp"
    fontWeight: 600
    lineHeight: "20sp"
rounded:
  desktop-control: "6px"
  desktop-disclosure: "8px"
  desktop-leaf: "16px"
  mobile-small: "6dp"
  mobile-medium: "12dp"
  mobile-large: "16dp"
spacing:
  desktop-xs: "4px"
  desktop-sm: "8px"
  desktop-md: "12px"
  desktop-lg: "16px"
  desktop-xl: "24px"
  desktop-leaf-inline: "28px"
  mobile-sm: "8dp"
  mobile-md: "12dp"
  mobile-lg: "16dp"
  mobile-xl: "24dp"
components:
  desktop-primary:
    backgroundColor: "{colors.desktop-ink}"
    textColor: "{colors.desktop-leaf}"
    rounded: "{rounded.desktop-control}"
    padding: "8px 14px"
  desktop-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.desktop-ink}"
    rounded: "{rounded.desktop-control}"
    padding: "8px 12px"
  desktop-ghost-hover:
    backgroundColor: "{colors.hover}"
    textColor: "{colors.desktop-ink}"
    rounded: "{rounded.desktop-control}"
  desktop-input:
    backgroundColor: "transparent"
    textColor: "{colors.desktop-ink}"
    padding: "8px 0"
  desktop-leaf:
    backgroundColor: "{colors.desktop-leaf}"
    textColor: "{colors.desktop-ink}"
    rounded: "{rounded.desktop-leaf}"
    padding: "24px 28px 92px"
  desktop-decision:
    backgroundColor: "{colors.decision}"
    textColor: "{colors.desktop-ink}"
    rounded: "{rounded.desktop-disclosure}"
    padding: "20px"
  mobile-primary:
    backgroundColor: "{colors.mobile-ink}"
    textColor: "{colors.desktop-surface}"
    rounded: "{rounded.mobile-small}"
  mobile-tonal:
    backgroundColor: "{colors.hover}"
    textColor: "{colors.mobile-ink}"
    rounded: "{rounded.mobile-small}"
  mobile-input:
    textColor: "{colors.mobile-ink}"
    typography: "{typography.mobile-body-large}"
    rounded: "{rounded.mobile-small}"
  mobile-input-dock:
    backgroundColor: "{colors.mobile-surface}"
    textColor: "{colors.mobile-ink}"
    padding: "12dp 24dp"
  mobile-consequence:
    backgroundColor: "{colors.decision}"
    textColor: "{colors.mobile-ink}"
    typography: "{typography.mobile-body-large}"
    rounded: "{rounded.mobile-small}"
    padding: "16dp"
---

# Design System: OSCAR

## Overview

**Creative North Star: "Quietly Alive + Playful Precision"**

OSCAR is a calm, responsive presence with one continuous relationship. Typography, spacing and contextual controls give useful work room to breathe. The blue shell and yellow puck supply character through the existing shared expression engine; surrounding UI stays restrained, practical and easy to inspect.

Desktop opens a cool near-white reading folio from a compact presence object. Android uses a warm canvas, operational Sans typography, native rows and a small Orb attached to the unified bottom input dock. The platforms share identity and truthful state while retaining their own interaction conventions.

This document captures the implemented 2026-10-12 redesign candidate, replacing the earlier general visual specification under the owner's redesign authorization. It is a candidate reference, not owner visual approval, merge authorization or physical acceptance. Native WebView2 and API35 emulator captures are reference evidence; microphone, biometric/OEM behavior and daily-use comfort remain deferred. Gate C remains PARTIAL. No Slice 14, merge or deployment follows from this document.

**Key Characteristics:**

- Small, responsive character connected to useful work.
- Typography and flat rows carry hierarchy before containers.
- Voice and text belong to one input surface and context.
- Consequences, scope and evidence remain inspectable.
- Platform-native interaction remains complete without motion.

## Colors

Desktop's cool leaf and Android's warm paper are deliberate platform interpretations. Frontmatter records literal implementation values; shared names have equal values where the code agrees.

### Primary

Ink carries main actions and content. Desktop uses `desktop-ink`; Android uses `mobile-ink` as Material `primary`, `onSurface` and `onBackground`. Main actions are restrained ink controls. `focus-blue` is Desktop focus and Android `secondary`.

The canonical [Orb SVG](assets/brand/oscar-orb.svg) owns the actual blue shell, yellow face, red eye and curved wink, including its painted variations. Preserve it unchanged. Interface tokens do not recolor the asset or replace the shared expression renderer. `oscar-yellow` also supplies Android's Material `tertiary`.

### Secondary

Warm `decision` is consequential review material: Desktop's decision sheet and Android's `tertiaryContainer`. It signals a decision to inspect, never granted permission. Dark review material uses `dark-decision`; Android supplies `dark-decision-text` for its foreground.

### Neutral

Desktop uses `desktop-leaf` with `desktop-surface` for the disclosed Presence menu. Android maps `mobile-paper` to `background`, `surface` and `surfaceContainerLow`; `mobile-surface` to `surfaceContainer`; `mobile-container-high` and `mobile-container-highest` to their matching Material roles; white to `surfaceContainerLowest`. `surfaceTint` is transparent.

`secondary-text` carries supporting copy, `divider` separates related rows and `hover` identifies hover/selected/tonal surfaces. Android uses `mobile-outline` for controls and `divider` as `outlineVariant`. Error colors stay platform-specific. Desktop uses `selection` for selected text.

Dark Desktop substitutes leaf, surface, ink, secondary text, divider, hover, focus and decision tokens. Dark Android maps the corresponding shared dark values to background/surface, primary/onSurface/onBackground, onSurfaceVariant, outlineVariant, secondaryContainer/surfaceContainerHigh and secondary. Its extra container low/lowest/highest and outline values are recorded explicitly. Main actions reverse foreground/background; Android system bars follow light/dark appearance. Android offers system/light/dark choices; Desktop follows OS appearance. Unspecified Material roles retain Material3 defaults and must not be represented as OSCAR overrides.

**The Identity Rule.** The canonical Orb's artwork owns its identity colors; surface tokens and theme changes must not repaint it.

## Typography

**Desktop heading font:** Source Serif 4, with Georgia fallback. **Body and control font:** Source Sans 3, with Segoe UI on Desktop and Android platform glyph fallback. **Technical values:** Desktop uses Consolas/monospace only for exact plan material; ordinary responses remain Sans.

Desktop headings are sparse Serif statements. Android's operational screens use Source Sans 3 throughout: headline roles are compact (22-26sp), body roles are readable (16-18sp). `headlineSmall` shares `mobile-title-large`; `titleSmall` is 15sp/20sp; `bodySmall` is 14sp/20sp; `labelLarge` is 16sp/22sp; `labelSmall` is 12sp/16sp. Android packages Source Serif 4 and declares a family, but no current screen uses it. Do not infer an Android Serif reading system from the bundled asset.

Desktop leaf headings use `desktop-headline`, Activity uses `desktop-activity-headline`, and narrow windows reduce the leaf heading to 27px. Base body uses `desktop-body`; composer text is 17px at 1.5 line height and response reading uses `desktop-reading`. Controls use 14px; supporting copy spans 12-14px according to role. Preserve selectable, wrapping content rather than fixed content cards.

Font provenance lives in [assets/fonts/README.md](assets/fonts/README.md). Source Sans 3 and Source Serif 4 are Adobe Originals under SIL Open Font License 1.1, with licenses beside the canonical and Desktop files. Canonical variable upright Sans was retrieved from Google Fonts; variable Roman Serif from Adobe's release repository on 2026-10-12. Identical TTF copies are packaged in Desktop `public/fonts` and Android `res/font`; there is no runtime font download. Desktop declares weights 200-900 and `font-display: swap`; Android binds Sans weights 400/500/600 explicitly. Physical variable-weight readability remains an owner review item.

**The Operational Type Rule.** Sans carries controls, evidence and Android operational screens; Desktop Serif is reserved for sparse headings.

## Layout

Desktop is a transparent native presence window. Its compact object is 92px wide, anchored 20px from the right and 25px from the bottom. Invocation reveals one folio inset 12px, with 24px vertical/28px horizontal content padding and room for the bottom margin. The object reduces to a 60px rendered Orb in that margin; Activity retains the same presence object. Activity, Text tools and Act are contextual shortcuts. Presence disclosure contains native hide/pin/float/edge controls and shortcut configuration.

At widths up to 400px, Desktop horizontal padding becomes 20px and decision definitions stack. Full reading removes the response preview height bound. Tools, Activity and exact material scroll; controls wrap. The native window owns geometry and recovery, while presentation preserves focus and drafts through invocation/retreat.

Android's scrollable content is centered with a 720dp maximum width. Horizontal padding is 24dp, reducing to 16dp below 360dp. The top bar carries OSCAR/connection status, a direct Activity shortcut and navigation disclosure. A native modal drawer reveals OSCAR, Activity, Devices and Settings, with a 320dp maximum width. Secondary destinations return through Android Back; drawer dismissal and voice cancellation respect the active layer.

The bottom input dock belongs to the OSCAR destination. A 56dp Orb sits inside a 64dp voice target beside the outlined multiline text field and 48dp Send control. The dock adds navigation-bar and IME insets to its padding; one row keeps voice/text close without an oversized character or microphone CTA. Input supports one to four lines and IME Send. Reading and consequential review use complete scrollable views with safe-drawing insets; confirmation actions remain separate from the reading body. Font sizes use sp and follow system scale. Native controls preserve at least 48dp touch targets, and device/preferences rows are 80dp/72dp minimum height.

**The Disclosure Rule.** Show the current work and the next useful action first; reveal scope, policy, evidence and settings through explicit inspection.

## Elevation & Depth

Depth is mostly tonal. Desktop uses one contained folio shadow (`0 6px 18px #15211c24`) and a smaller disclosed menu shadow (`0 5px 16px #15211c24`). Activity has no independent shadow inside its parent leaf. Android uses flat canvas/container separation and native Material3 drawer/dialog behavior, with transparent surface tint. The input dock is a tonal boundary.

Desktop invocation uses 220ms `cubic-bezier(.16,1,.3,1)` geometry interpolation from the Orb's corner and a 140ms opacity transition. Retreat uses 180ms; control background response is 120ms ease-out. Reduced motion removes surface interpolation and control transitions; retreat becomes immediate. Android respects OS animator availability plus its Reduce OSCAR motion preference and supplies that state to shared expressions. Native navigation/Back takes precedence over copied Desktop shrinking effects. Motion never owns verification, consent or correctness.

**The Continuity Rule.** Motion explains the transition from presence to work; state and controls must remain usable when motion is disabled.

## Shapes

Desktop controls use gently squared 6px corners, disclosed menus/review material use 8px, and the single folio uses 16px. Android explicitly defines Material shapes at 6dp/12dp/16dp; operational buttons, composer and consequence material use the small shape. Native drawer, chip and dialog geometry follows the installed Material3 implementation. The Orb retains its canonical curved silhouette. Divider-led rows replace repeated rounded containers.

## Components

### Buttons

Desktop main actions are ink with leaf text, 8px/14px padding and 38px minimum height. Ghost controls use 8px/12px padding, tonal hover, and a 2px focus outline with 3px offset. Disabled controls reduce opacity and remain inert. Android uses native Button, FilledTonalButton, TextButton and IconButton semantics with the explicit small shape where present. Decision confirmation has a 48dp minimum height and disables when busy, expired or no longer current. Platform focus/pressed/disabled states remain native.

### Chips

Activity's native FilterChip pair switches Active/Finished. Chips select a view of current readback; they do not invent work, erase cancelled history or promote reported progress into verification.

### Cards / Containers

The Desktop folio is the main contained surface. A yellow decision sheet groups consequence and exact material, with scope/evidence inspectable beneath. Android consequences use a small yellow native Surface; ordinary device/preferences entries are transparent ListItems. Do not turn every setting, result or capability into a separate card.

### Inputs / Fields

Desktop's composer is an open Sans writing field with one divider; focus replaces it with a blue underline. Enter sends and Shift+Enter adds a line. Text tools and scoped action forms reuse open field styling. Android uses a native OutlinedTextField with `outlineVariant` unfocused stroke, 18sp body, small corners and IME Send; Send only enables for a valid available interaction. Keep platform labels and semantics accessible.

### Navigation

Desktop Activity, Text tools and Act are immediately available in the folio margin. Presence disclosure holds window/shortcut controls. Android's direct Activity entry and contextual drawer keep secondary destinations available without four permanent equal tabs. Top-bar Back, system Back, keyboard dismissal and drawer dismissal retain their native roles.

### Reading and decisions

Response previews lead to full selectable reading. Android review gives consequence prominent warm material, preserves exact request/plan/reply, and discloses Scope & policy. Readback, reported testimony, partial results, unknown state and expiry keep their meaning. Opening a review grants no consent; genuine native owner confirmation remains the authority boundary. No visual redesign grants recording, retention or action authority.

### Shared character and input dock

Use the existing shared React/native Compose expression contract with fenced current source state. The same Orb is compact presence, an invoked margin object on Desktop, and a small voice affordance beside Android text input. A Persona preview is explicitly simulated and cannot change operational truth. Listening, muted, acoustic awareness disabled and typing remain distinct; Android's unavailable voice binding must remain visibly unavailable.

Source authority: [Desktop styles](desktop/src/presence/living.css), [Desktop presence](desktop/src/presence/Living.tsx), [Android app/theme](mobile/app/src/main/java/io/dawnlight/oscar/mobile/OscarApp.kt), [interaction/reading](mobile/app/src/main/java/io/dawnlight/oscar/mobile/InteractionScreens.kt), [settings](mobile/app/src/main/java/io/dawnlight/oscar/mobile/SettingsScreen.kt), [devices](mobile/app/src/main/java/io/dawnlight/oscar/mobile/DevicesScreen.kt) and [review](mobile/app/src/main/java/io/dawnlight/oscar/mobile/ApprovalDialog.kt). Desktop native reference captures live in `docs/design/cross-platform/desktop/`; final Android API35 reference captures in `.oscar/redesign/android-native-v2/OSCAR-Rebuild-1791793547555/`. Synthetic fixture content remains reference evidence. The sidecar contains HTML/CSS previews for design tooling; these are not native app acceptance evidence.

## Do's and Don'ts

### Do:

- **Do** preserve the canonical Orb and shared expression contract.
- **Do** keep character small and attached to the useful interaction surface.
- **Do** retain cool Desktop and warm Android materials with their actual native type roles.
- **Do** use flat rows, clear headings and contextual disclosure to expose features.
- **Do** preserve focus, Back, system text scale, input insets and reduced-motion usability.
- **Do** distinguish reported, verifying, verified, partial, blocked, failed and unknown states.
- **Do** keep scope, exact material and consequential confirmation inspectable.
- **Do** distinguish native/reference captures from owner quality and physical device acceptance.

### Don't:

- **Don't** repaint or recreate the canonical Orb, or substitute an oversized mascot.
- **Don't** promote rejected generated imagery or earlier Android top-shoulder/Serif concepts into final guidance.
- **Don't** introduce card walls, glass, neon, fake telemetry or permanent chat-sidebar gravity.
- **Don't** make every action blue or use color as a substitute for readable state.
- **Don't** let expression, animation or an API success imply consent or verified completion.
- **Don't** add recording, retention, routing or permission authority in presentation code.
- **Don't** claim physical/manual acceptance, owner approval, merge or later-slice authorization from this candidate.
