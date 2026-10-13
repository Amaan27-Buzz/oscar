# Desktop interaction polish — owner review

2026-10-14, `codex/desktop-companion-workspace`, draft [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) into main. No merge. Previous native packets and Aperture `42b565c` remain preserved.

Conversation now has a calm empty state, a stable composer and no utility-launch, session-store or retention-debugging labels. Owner messages appear on the right; OSCAR replies remain on the left. Restored turns keep their task references and Core evidence without implementation badges. Memory/privacy information belongs in Preferences. Supported voice turns use the existing microphone/start/finish/cancel and private preview path; no microphone appears when unavailable.

All five Workspace pages were reviewed for internal vocabulary and spacing. Activity keeps compact, evenly inset rows and readable outcomes; identifiers, raw failure reasons and evidence remain inspectable. Devices describes supported work in plain language. Preferences separates privacy, app context, appearance and invocation, with direct controls available under Advanced controls. Native approval/signing and expected-value text review remain intact.

Companion retains its approved Orb, expressive motion, tray and fixed 148 × 164 logical-pixel window. The compact toolbar contains Open, Access, Sentry, voice and More. Shortcut management and Preferences are in More. Ask is read from Core; Secure and Full Access are unavailable. The Full Access contract remains unrestricted owner-delegated autonomy, not Secure. Passive/Aware/Guard/Away/Sleep are unavailable and start no background recording. Native menus reserve usable monitor space above the fixed window, dismiss with Escape and cannot carry authority/signing payloads. A focused Workspace is no longer obscured by an always-on-top Companion; desktop presence returns after hiding/closing Workspace.

[Architecture decision](../../../decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) · [surface ownership](../../../design/DESKTOP-COMPANION-WORKSPACE.md)

## Current native captures

Actual bundled Tauri/WebView2 HWND captures against an authenticated disposable Core. No owner apps, settings, credentials, recordings or conversation archives were captured. Arithmetic is real and verified. Model text is scripted reference content, not inference. Fixture progression is separate from human native confirmation.

| View | Light | Dark |
|---|---|---|
| Conversation home | [Native](evidence/workspace-home.png) | [Native](evidence/workspace-home-dark.png) |
| Messages | [Native](evidence/conversation.png) | [Native](evidence/conversation-dark.png) |
| Restored/long conversation | [Native](evidence/reading.png) | [Native](evidence/reading-dark.png) |
| Activity | [Native](evidence/activity-working.png) | [Native](evidence/activity-working-dark.png) |
| Exact review | [Native](evidence/approval.png) | [Native](evidence/approval-dark.png) |
| Automations | [Native](evidence/actions.png) | [Native](evidence/actions-dark.png) |
| Devices | [Native](evidence/devices.png) | [Native](evidence/devices-dark.png) |
| Preferences | [Native](evidence/preferences.png) | [Native](evidence/preferences-dark.png) |
| Privacy | [Native](evidence/privacy.png) | [Native](evidence/privacy-dark.png) |

[Companion toolbar](evidence/companion-controls.png) · [Access selector](evidence/access-selector.png) · [Sentry selector](evidence/sentry-selector.png) · [overflow](evidence/overflow.png) · [narrow Preferences](evidence/preferences-narrow.png) · [native lifecycle recording](evidence/companion-workspace.mp4).

## Validation and limits

- Core: 569 tests executed, 563 passed, six optional checks skipped. Includes authorization, session isolation/replay, read/retain separation, history continuity, memory, existing computer control and bounded conversation action routing. Ruff and mypy pass.
- Frontend: 83 tests across 13 files; TypeScript/Vite and bundled debug Tauri build pass.
- Rust: 16 tests; rustfmt and Clippy with warnings denied pass using installed Rust 1.99.0.
- Native: **86 checks PASS** in the [acceptance record](evidence/acceptance.json) covers both themes, all five pages at 800 × 620 logical size, row insets, right/left message alignment, contrast, keyboard, unavailable microphone, privacy, task/history continuity, reconnect, native menus near the taskbar, focus layering, hotkey collision, close/reopen and Quit.
- Native Core/CNG: [separate self-check](evidence/native-self-check.json), including exact typed file mutation and readback, CNG-PSS signing, application readback, private dictate preview, cancellation, reconnect and restart. Edit output remains SIMULATED/REPORTED; microphone and owner acceptance remain NOT RUN.
- Canonical Orb SHA256 remains `728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5`.

Conversation action recognition is a bounded grammar for explicit file/project/browser operations with supplied arguments, not a general natural-language planner. Existing typed contracts and permissions still validate every proposal; unsupported or ambiguous executors cannot run. Secure/Full Access, persistent Workers, schedules, watches and Sentry require their actual Core integrations. Physical voice, broad multimonitor/DPI, installer and owner visual acceptance were not checked. No new worktree, Mobile changes, fake authority or merge.
