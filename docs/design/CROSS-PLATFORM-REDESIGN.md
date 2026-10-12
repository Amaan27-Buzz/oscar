# OSCAR cross-platform rebuild

2026-10-12 owner-authorized redesign candidate. Baseline `7773de8b794acf61ab6f035a28ada1fed98a3f77`, branch `design/cross-platform-ui-rebuild`, draft target `build/slice-13-mobile-completion`. No merge, Slice14, deployment or physical acceptance.

## Direction exploration

Seven grounded systems considered: reading folio, compact utility tray, correspondence note, precision instrument, hinged pocket notebook, dispatch ledger, native system flyout. Three complete directions were evaluated:

| Direction | Desktop / Android interpretation | Tradeoff |
|---|---|---|
| Open folio | Orb joins the margin of one expandable reading surface / compact character shoulder, reading body, anchored voice-text composer, contextual drawer | Best continuous relationship and long reading; serif requires disciplined sparing use |
| Utility tray | Tight command palette with mode strip / compact action sheet and history list | Fast commands but risks making OSCAR a launcher; current-result reading secondary |
| Pocket notebook | Hinged leaf and sequential work entries / notebook sections and task index | Spatial continuity strong, but paper metaphor adds navigation ceremony |

Chosen **Open folio** under the owner's explicit instruction to choose the strongest direction. Impeccable seed `6965595c` assigned grounded #5 pocket notebook; the owner's selection delegation and product-clarity assessment govern the final choice. This is a code-led native implementation; generated screen comps are not native evidence.

Fused challengers were evaluated against identification and clarity: ticket wallet (competitive on traceable state, declined on everyday relationship); character catalog (declined on both, violates single identity); garden map (declined on both, wayfinding overwhelms compact tasks); star atlas (competitive on distinctiveness, weaker clarity); warm card app (declined on both, explicitly rejected incumbent pattern); type specimen (competitive on typographic discipline, weaker task topology). Raises: ticket wallet preserves cancelled/unknown history; atlas distinguishes prominence without card walls; type specimen demands a real licensed type system. No costumes, mascot artwork or brands copied.

## Direction contract

**THESIS:** one coherent presence opens into useful work. Refuse detached mascot-plus-form, transcript-first chat and four equal permanent mobile destinations.

**OWN-WORLD:** near-white folio, ink, cool neutral dividers; Source Sans3 controls/body and Source Serif4 sparse headings; original blue/yellow Orb; yellow decision material, blue focus. Flat rows and one contained composer replace card stacks.

**STORY:** observe current state, speak/type, read a result, inspect work, review consequence, confirm through native authority. Detail stays inspectable; history never implies live capability.

**FIRST VIEWPORT:** Desktop compact Orb anchored at lower right; expanded reading leaf fills the same native object and contains its Orb in the lower margin. Android small Orb at upper shoulder, task/status heading and current result in the body; composer above system/IME insets; Activity direct, secondary destinations in a native drawer.

**FORM:** Open folio, grounded rank1; pocket-notebook continuity retained structurally, seed6965595c. Signature interaction: invocation unfolds from the Orb's anchored corner and retreat returns focus/draft to the same presence. Android uses immediate native Back and drawer dismissal, never a shrinking Desktop panel.

**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## Functional reach and invariants

Desktop: LivingPresence, Activity, AskComposer, ResultView, TaskStage, TextTools, ActionSurface, native window geometry and startup composition. Android: OscarApp/theme, PresenceScreen/composer/reading, Activity, Devices, decisions, Voice and secondary settings presentation; Compose navigation callers/tests. Shared expression semantics/Core/session/signing/audio/permission contracts remain authoritative.

No new runtime dependencies. Licensed fonts are self-hosted under `assets/fonts`, copied to platform resources with OFL licenses. Sans handles controls; serif is never used for technical data. Platform fallback covers missing glyphs. Content remains selectable and large-text capable.

## Research

Pablooo searches used actual stories: invoke without leaving the current app; supervise a background task; review changes before permission; speak/type and read on a phone; manage device/microphone access; edit a long response. Six screenshots were visually inspected:

- [Raycast composer](https://pablooo.club/screen/ac4273ac329d99f2695640c982dc05f0e393b89353ae2053edb3abd72df95986): input and voice share one IME-adjacent surface. Borrow grouping, decline glass and oversized radii.
- [AI Edge Gallery voice/actions](https://pablooo.club/screen/873bb0375ef5af210ac10f853e5a567308d993406076202e53322c8c847396f6): separates response from executed functions; borrow inspectable action/result distinction, not unconditional success labels. Library capture appears iOS; it is not Android-native proof.
- [Monologue microphone consent](https://pablooo.club/screen/5c7e84627b31728d5da0c294f2164495d5c6e3ccaa0fdaee33c5f98da0fff7af): explain recording boundary adjacent to explicit action. Decline dark ornament and its privacy claims; OSCAR copy uses its own contracts.
- [Glaze plan review](https://pablooo.club/screen/085815d89cc66b789443591ae7dc5f93ab8f6ae7ab8d01a2179fdc5e51db5204): complete document plus distinct decision controls. Decline preselected consent; native confirmation stays separate.
- [Deezer device list](https://pablooo.club/screen/0a1c63114b567fe785692b4222a86cc711d77c791b05738d406e3aa6f0d20df0): identify this device before others; clear disclosure affordance. Decline plan quota/copy.
- [Claude Code task supervision](https://pablooo.club/screen/4d26a02d76a5c077c888f9b2e030f1ddcedb4165377fc304440ccbb3a4629065): background work remains inspectable without replacing primary content. Decline four-panel dashboard.

[Android adaptive navigation](https://developer.android.com/develop/adaptive-apps/guides/build-adaptive-navigation), [Windows keyboard interactions](https://learn.microsoft.com/en-us/windows/apps/design/input/keyboard-interactions) and [Windows design foundations](https://learn.microsoft.com/en-us/windows/apps/design/guidelines-overview) informed native Back, input/focus, insets and hierarchy. Android implementation uses installed Material3 components rather than ported iOS controls. These sources support platform conventions, not claims of OSCAR acceptance.

## Validation boundary

Actual WebView2 and existing API35 emulator captures, motion, regression results and independent findings are recorded in the audit/review packet. Synthetic states are labeled. Owner quality judgement, real microphone, biometric/OEM/phone behavior and daily-use comfort remain deferred.
