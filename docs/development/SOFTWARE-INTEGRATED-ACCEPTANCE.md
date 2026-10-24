# Integrated software acceptance traceability

2026-10-24. The owner's minimum 62 scenarios are tracked here without promoting
unit coverage into whole-product acceptance. **Overall PARTIAL.** This is an
execution ledger, not a software completion certificate. Current architecture,
source boundaries and commands are in the [completion ledger](OSCAR-FULL-SOFTWARE-COMPLETION.md).

`LOCAL` means matching synthetic integration/native evidence exists in the stated
scope. `PARTIAL` means only part of the requested scenario has matching evidence.
`OPEN` means the intended integrated scenario is not established. Owner/provider,
physical and deployment commissioning remain separate from executable gaps.
Earlier receipts qualify their own source snapshots; later aggregate regression
does not repeat their native UI, model or long-running acceptance.

| ID | Owner scenario | Current classification and matching evidence / gap |
| --- | --- | --- |
| 1 | Natural request → plan → tool → verified result | PARTIAL: installed Qwen + normal Cloud configuration + signed Ask/Full + real file readback passed; repeat Ask also failed structured output before effects. [Model receipt](../evidence/software-completion/local-model-authority-2026-10-24.json) |
| 2 | Multi-step contextual follow-up | PARTIAL: persisted current-owner planning follow-up and ambiguity/revocation tests; broader real-model multi-step native workflow unaccepted (`tests/test_conversation_planning.py`) |
| 3 | Historical recall | LOCAL: actual cached models/Qdrant/Graphiti + normal Harness; rendered Android sourced answer. [Memory acceptance](SOFTWARE-MEMORY-INDEX-ACCEPTANCE.md) |
| 4 | Correction / temporal supersession | LOCAL: canonical correction/temporal tests and rendered native exact review. [Memory management](SOFTWARE-MEMORY-MANAGEMENT.md) |
| 5 | Forget / rebuild | LOCAL: actual derived projection deletion/rebuild; Android answer withdrawal. Same memory receipts; no secure disk-erasure claim |
| 6 | Live vs memory disagreement | LOCAL Core tests and actual index fallback; broader native everyday disagreement scenario PARTIAL (`tests/test_memory_fabric.py`, `tests/test_local_memory.py`) |
| 7 | Two same-provider accounts | LOCAL account/Fabric isolation tests; real two-account provider commissioning OPEN (`tests/test_connector_mount.py`, `tests/test_auth_broker.py`) |
| 8 | OSCAR-owned vs owner-delegated identity | PARTIAL: explicit identity classification and signed authority enforced; no real OSCAR-owned provider account operation accepted |
| 9 | Cross-account workflow | PARTIAL: explicit account-bound operations and isolation; useful chained native cross-account outcome OPEN |
| 10 | OAuth refresh / expiry / revoke | LOCAL synthetic HTTP/broker tests; real provider interoperability OPEN. [MCP authorization](SOFTWARE-MCP-AUTHORIZATION.md) |
| 11 | MCP discovery / execution / cancellation / restart | LOCAL installed SDK and synthetic resource/stdio lifecycle tests. [MCP receipt](../evidence/software-completion/mcp-authorization-2026-10-23.json) |
| 12 | Removal blocks future plugin execution | LOCAL signed lifecycle, disable/remove and account-generation tests (`tests/test_connections.py`, `tests/test_mcp_client.py`) |
| 13 | No cross-account credential leakage | LOCAL negative isolation/redaction tests; no exhaustive leakage certification |
| 14 | Operate supported Windows app | LOCAL run-owned WPF UIA text/invoke and canvas fixture; owner installed apps uncommissioned. [Windows receipt](../evidence/software-completion/windows-visual-2026-10-24.json) |
| 15 | Browser form with authorized account | LOCAL explicit synthetic account/profile and signed Grid form; real provider browser consent OPEN. [Browser workflow](SOFTWARE-BROWSER-WORKFLOWS.md) |
| 16 | Screenshot / DOM / visual observation | LOCAL actual Chromium DOM/frame and selected Windows PNG; semantic vision/coordinate reasoning OPEN. Windows/browser receipts are separate |
| 17 | File upload / download | PARTIAL bounded scoped upload and anonymous HTTP-anchor download; authenticated/blob download unsupported |
| 18 | Terminal / Git development | PARTIAL actual scoped native processes and terminal tests; minimal constrained image lacks Git, so its failed Git-fixture campaign is not acceptance |
| 19 | Cross-application automation | OPEN broader useful application-to-application acceptance; individual app/browser/file executors do not establish it |
| 20 | Independent result verification | LOCAL files, UIA text, provider saved resources and fixture observers; generic screen/click/invoke outcomes remain PARTIAL |
| 21 | Operate actual emulator test app | LOCAL actual disposable API35 fixture. [Android conversation](../evidence/software-completion/android-conversation-2026-10-24.json) |
| 22 | Native capability admission | LOCAL actual OS-grant/session/source admission and withdrawal; physical OEM commissioning OPEN |
| 23 | Android UI / gestures | LOCAL actual exact-resource click/text/scroll subset; generic outcome PARTIAL, arbitrary app workflows unaccepted |
| 24 | Permission withdrawal | LOCAL actual emulator source/capture stop and scoped regression; no physical phone claim |
| 25 | Android-to-Desktop handoff | PARTIAL authenticated common Grid/remote tasks; current full ordinary native conversation-to-Desktop handoff scenario not freshly accepted |
| 26 | Process death / restore | LOCAL actual force-stop/relaunch, Keystore session, unchanged claims and fresh work. [Recovery receipt](../evidence/software-completion/android-recovery-2026-10-24.json) |
| 27 | Grid revocation | LOCAL actual emulator revoked-session notice withdrawal and native/Core tests |
| 28 | Ask confirmation | LOCAL actual two exact reviews/model/file and native signed effects; no opening/preview grants execution |
| 29 | Secure ordinary operation | LOCAL synthetic standing-authority regression; actual owner activation uncommissioned (`tests/test_authority.py`) |
| 30 | Secure protected operation | LOCAL exact-review and protected-policy negatives; stronger physical owner acceptance separate |
| 31 | Signed Full activation | LOCAL synthetic native contract/management review and signed owner key; actual owner Full remains inactive |
| 32 | Full autonomous operation | LOCAL signed Full conversation model/file readback without per-action prompts; model reliability PARTIAL. [Full receipt](../evidence/software-completion/full-planning-2026-10-24.json) |
| 33 | Downgrade / revoke | LOCAL grant epoch/policy/session/account race tests; no instantaneous remote process-kill guarantee |
| 34 | Stale / offline authority denial | LOCAL target checks and lease/revocation tests, actual recovery/no replay |
| 35 | Spoken task | LOCAL real prepared wake/VAD/STT models, synthetic audio → Core → real math/file → Kokoro PCM. [Voice integration](SOFTWARE-VOICE-INTEGRATION.md) |
| 36 | Barge-in | LOCAL synthetic audio and native bridge cancellation; room AEC/physical human acceptance OPEN |
| 37 | Mute / stop | LOCAL persisted mute/heartbeat and explicit native control contracts; defaults stay muted |
| 38 | Voice authorization | LOCAL source/speaker/grant rules; recognition never grants action authority; owner Voice Match uncommissioned |
| 39 | Sentry transitions | LOCAL actual emulator and Core mode/expiry/withdrawal tests. [Sentry delivery](SOFTWARE-SENTRY-DELIVERY.md) |
| 40 | Source capture / retention | LOCAL independent source grants, actual eight-source zero-retention run and explicit single-app frame retention |
| 41 | Multi-source day context | LOCAL clock/calendar/weather/phone source contracts and actual eight-source phone run; unified daily-use acceptance PARTIAL |
| 42 | Calendar / task coordination | PARTIAL observed overlap, signed calendar creation and Google Tasks/Microsoft To Do creation with independent saved-resource readback; automatic schedule coordination and daily-use acceptance OPEN. [Task contract](SOFTWARE-COMMUNICATION-INTEGRATION.md) |
| 43 | Create scheduled automation | LOCAL actual native conversation review/decline and signed Executive creation. [Authoring](SOFTWARE-EXECUTIVE-AUTHORING.md) |
| 44 | Persistent Worker after UI closure | LOCAL separate Core scheduled process test and outbound Worker acceptance; no desktop required as permanent Core |
| 45 | Conditional / schedule triggers | LOCAL Executive event/occurrence tests; richer real daily monitoring acceptance OPEN |
| 46 | Interrupt / recover / verify | LOCAL actual Core/Worker restart and 98 independently read-back effects; uncertain mutation never replayed. [Soak](../evidence/software-completion/soak-fbe12e3-2026-10-24.json) |
| 47 | Useful proactive notification | PARTIAL actual transient Sentry notices/quiet/expiry; usefulness and broader Chief-of-Staff follow-up acceptance OPEN |
| 48 | Same canonical task on Desktop / Android | LOCAL common Core task/readback contracts and historical native remote origin proof; full newest cross-device workflow PARTIAL |
| 49 | Core restart | LOCAL separate TLS Core death/restart, native Worker recovery and fresh clipboard verification |
| 50 | Worker disconnect | LOCAL actual stop/liveness expiry and cancellation; UI connectivity cannot preserve executor capability |
| 51 | Browser / MCP interruption | LOCAL actual browser children/profile cleanup, SDK lifecycle and durable uncertain-effect fencing |
| 52 | Provider outage | LOCAL synthetic provider loss/timeouts and fail-closed freshness; no real outage campaign |
| 53 | Backup / independent restore | LOCAL D1 offline backup/restore tests; hosted storage/keys/disaster acceptance OPEN |
| 54 | Uncertain mutation not duplicated | LOCAL actual after-effect Worker death/restart, provider mutation failures and claim journal tests |
| 55 | Revoked device cannot regain access | LOCAL signed session, enrollment/revocation and target pre-effect regressions; real owner commissioning separate |
| 56 | Desktop functional inspection | PARTIAL earlier actual native reviews/workflows plus current compiled/unit-tested controls; newest sharing controls lack rendered owner acceptance |
| 57 | Android functional inspection | LOCAL disposable native production navigation/reviews/recall and 11 captures; owner visual/physical acceptance OPEN |
| 58 | Accessibility / large text | PARTIAL prior API35 large-text/landscape/IME reference and native semantic tests; current full assistive-technology campaign OPEN |
| 59 | Workflow latency | LOCAL 80 samples/operation and raw plots; source checkpoint explicitly predates later changes. [Performance](../evidence/software-completion/performance-2026-10-24/performance.md) |
| 60 | Sustained operation soak | LOCAL ten-minute frozen restart soak, separate 65-second eight-source phone campaign; no newest-source or multi-day acceptance |
| 61 | Resource / memory reporting | LOCAL CPU/RSS/SQL and Core/Worker soak measurements; storage grows with retained tasks; no leak-free/battery claim |
| 62 | Visible error / recovery | LOCAL actual native revoked/offline/expired-source behavior; newest all-feature native error inspection PARTIAL |

## Active executable gaps

Useful chained cross-account/cross-application workflows, broader Chief-of-Staff
coordination, reliable general model planning and semantic
visual reasoning need further implementation or integration acceptance. They are
not reclassified as owner-only commissioning. API/OAuth consent, actual owner
activation, hosted Core, physical phone/audio and hardware remain separately
authorized commissioning. Group 6 and Slice 20 are not passed by this matrix.
