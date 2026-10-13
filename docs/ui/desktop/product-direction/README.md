# Group 2.5 — personal intelligence owner review

2026-10-14 candidate on `codex/desktop-companion-workspace`, draft [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) into main. Start: clean local/remote `180c84ec9bbb77fdb6bfed84ae5045062d83135a`; main `fd191a2d7ca7f98c456969c74173a0340f789578`. Aperture `42b565c` and all prior committed evidence are preserved. No new worktree, merge or branch cleanup.

The approved Companion remains small and unchanged. Workspace navigation is **Conversation / Automations / Activity / Devices / Preferences**. Writing/context/Dictate/Edit and exact immediate action preparation are contextual Conversation controls. Activity groups attention, running work and outcomes. Native signing and exact evidence stay intact.

[Architecture decision and feature ownership](../../../decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) · [Companion contract](../../../design/DESKTOP-COMPANION-WORKSPACE.md).

## Capability status

| Area | This candidate | Remaining boundary |
|---|---|---|
| Companion and native shell | Preserved; native lifecycle/privacy checks pass | Owner visual review; broad multimonitor/installer acceptance not run |
| Conversation | Core chronological history; task refs; paged older history; bounded recent model context; source-backed episodic recall | Persistence requires configured canonical Memory Fabric plus separately enrolled history-read/retain grants. No owner grants were changed |
| Capture / Dictate / Edit / immediate actions | Existing UIA/expected-value review, preview, apply, cancellation and native signatures preserved | Real screenshot perception is not advertised; physical microphone/voice not run |
| Access | Core reports Ask; exact-action review and critical blockers remain | Secure and Full Access activation unavailable. Genuine Full Access delegation/revocation is specified, not implemented |
| Awareness / autonomy | Core reports Trigger-only and Manual independently | Sentry/wake/persistent mute and supervised/autonomous Worker management unavailable |
| Automations | Truthful management entry and conversation handoff; existing immediate task/runtime foundations | Scheduled/event/watch/named persistent Worker/Protocol lifecycle integration remains future work. No dummy records or nonfunctional pause/resume controls |
| Activity | Real task outcomes, failures, attention, progress, exact review/signing and verification evidence | Trigger/Worker/Protocol correlation appears only once real backend records exist |

## Native captures

These are **actual bundled Tauri/WebView2 HWND captures** against an authenticated disposable Core. Owner settings, apps, recordings, credentials and data are untouched. Workspace history scopes are explicitly granted to synthetic fixture data; this does not provision an owner session. Arithmetic is executed/verified; model text is scripted reference content, never live inference.

| View | Light | Dark |
|---|---|---|
| Conversation home | [Native](evidence/workspace-home.png) | [Native](evidence/workspace-home-dark.png) |
| Chronological conversation | [Native](evidence/reading.png) | [Native](evidence/reading-dark.png) |
| Automations | [Native](evidence/actions.png) | [Native](evidence/actions-dark.png) |
| Activity | [Native](evidence/activity-working.png) | [Native](evidence/activity-working-dark.png) |
| Exact approval | [Native](evidence/approval.png) | [Native](evidence/approval-dark.png) |
| Contextual writing | [Native](evidence/text-tools.png) | [Native](evidence/text-tools-dark.png) |
| Devices | [Native](evidence/devices.png) | [Native](evidence/devices-dark.png) |
| Preferences | [Native](evidence/preferences.png) | [Native](evidence/preferences-dark.png) |

[Narrow Preferences](evidence/preferences-narrow.png) · [Companion idle](evidence/companion-idle.png) · [working](evidence/companion-working.png) · [attention](evidence/companion-attention.png) · [controls](evidence/companion-controls.png) · [native lifecycle recording](evidence/companion-workspace.mp4).

## Validation

- Core: `python -m unittest discover -s tests -t . -q` — 565 executed, 559 passed, six optional checks skipped; no failures. Includes authorization, replay/session isolation, Windows Worker/control, memory, retention/read separation, paging/restart/forget and archive thread cleanup.
- Frontend: 79 tests across 13 files; TypeScript/Vite production build passes.
- Rust/Tauri: 15 tests; fmt, Clippy with warnings denied and bundled debug build pass.
- [Native Workspace acceptance](evidence/acceptance.json): **60 checks PASS**, both themes, 800×620 logical window across all five pages, keyboard, contrast, reduced motion, reconnect, task/history continuity, tray/shortcut/collision/hide/reopen/Quit and Companion privacy. Programmatic fixture progression is distinct from owner GUI approval.
- [Native Core/CNG self-check](evidence/native-self-check.json): exact typed action, CNG-PSS signing, application readback, dictate preview, cancellation, reconnect and restart. Edit output is SIMULATED/REPORTED; microphone and owner acceptance are NOT RUN.
- Visual inspection: native light/dark Conversation, Automations, Preferences, narrow Preferences and unchanged Companion inspected. Retained history uses open typography; writing controls remain contextual. Review retirement preserves the manually selected page.
- Canonical Orb SHA256: `728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5` (unchanged). Companion artwork/styles and historical evidence were not edited.

The Event Archive integration surfaced a real HTTP threading defect; per-thread WAL connections plus request cleanup fix it without sharing transactions across request threads. Verbatim retained turns use the established MemoryWriter/FTS path, not a duplicate memory store. Capture context and execution payloads stay transient; restored history cannot replay an old action.

The access decision explicitly preserves present blockers while specifying an owner-authorized Full Access path with no OSCAR per-action prompts. No standing authority is active. Physical voice/device, Windows Hello attestation, owner visual acceptance and installer acceptance are not claimed. Stop for owner review before merge.
