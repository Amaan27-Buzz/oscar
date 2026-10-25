# Integrated software acceptance traceability

2026-10-25. The owner's minimum 62 scenarios are tracked here without promoting
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
| 2 | Multi-step contextual follow-up | LOCAL scoped installed Qwen 9B Ask/Full arithmetic-result-to-file handoff, with reviewed provenance and source-change denial. Persisted contextual follow-up tests pass. Broader adaptive native workflow remains PARTIAL; 4B decoding failures retained. [Handoffs](../evidence/software-completion/worker-handoffs-2026-10-25.json) |
| 3 | Historical recall | LOCAL: actual cached models/Qdrant/Graphiti + normal Harness; rendered Android sourced answer. [Memory acceptance](SOFTWARE-MEMORY-INDEX-ACCEPTANCE.md) |
| 4 | Correction / temporal supersession | LOCAL: canonical correction/temporal tests and rendered native exact review. [Memory management](SOFTWARE-MEMORY-MANAGEMENT.md) |
| 5 | Forget / rebuild | LOCAL: actual derived projection deletion/rebuild; Android answer withdrawal. Same memory receipts; no secure disk-erasure claim |
| 6 | Live vs memory disagreement | LOCAL Core tests and actual index fallback; broader native everyday disagreement scenario PARTIAL (`tests/test_memory_fabric.py`, `tests/test_local_memory.py`) |
| 7 | Two same-provider accounts | LOCAL account/Fabric isolation tests; real two-account provider commissioning OPEN (`tests/test_connector_mount.py`, `tests/test_auth_broker.py`) |
| 8 | OSCAR-owned vs owner-delegated identity | PARTIAL: explicit identity classification and signed authority enforced; no real OSCAR-owned provider account operation accepted |
| 9 | Cross-account workflow | LOCAL explicit-ID synthetic registration in account A → fresh receipt read → verified scoped file → upload and fresh receipt in account B; isolated cookies and exact uploaded bytes checked. Broader account reasoning and real providers OPEN. [Receipt](../evidence/software-completion/browser-cross-account-2026-10-24.json) |
| 10 | OAuth refresh / expiry / revoke | LOCAL synthetic HTTP/broker tests; real provider interoperability OPEN. [MCP authorization](SOFTWARE-MCP-AUTHORIZATION.md) |
| 11 | MCP discovery / execution / cancellation / restart | LOCAL installed SDK and synthetic resource/stdio lifecycle tests. [MCP receipt](../evidence/software-completion/mcp-authorization-2026-10-23.json) |
| 12 | Removal blocks future plugin execution | LOCAL signed lifecycle, disable/remove and account-generation tests (`tests/test_connections.py`, `tests/test_mcp_client.py`) |
| 13 | No cross-account credential leakage | LOCAL negative isolation/redaction tests; no exhaustive leakage certification |
| 14 | Operate supported Windows app | LOCAL run-owned WPF UIA text/invoke and canvas fixture; installed Granite also completes scoped registered-app discovery/private continuation/fixture launch under synthetic Ask/Full with separate marker inspection. Canonical launch remains PARTIAL; owner installed apps uncommissioned. [Windows receipt](../evidence/software-completion/windows-visual-2026-10-24.json), [model app receipt](../evidence/software-completion/observation-decoding-2026-10-25.json) |
| 15 | Browser form with authorized account | LOCAL explicit synthetic account/profile and signed Grid form; real provider browser consent OPEN. [Browser workflow](SOFTWARE-BROWSER-WORKFLOWS.md) |
| 16 | Screenshot / DOM / visual observation | LOCAL actual Chromium DOM/frame and selected Windows PNG; private image continuation and local model metadata admission implemented, but actual model coordinate reasoning remains OPEN. Explicit selected-window focus has standalone native acceptance; combined native focus failures remain OPEN. [Image](../evidence/software-completion/screen-observations-2026-10-25.json), [focus](../evidence/software-completion/window-focus-2026-10-25.json) |
| 17 | File upload / download | PARTIAL bounded scoped upload and same-origin authenticated HTTP-anchor download through isolated profiles; real provider upload/download and blob/cross-origin authenticated transfers unaccepted or unsupported. [Browser contract](SOFTWARE-BROWSER-WORKFLOWS.md) |
| 18 | Terminal / Git development | LOCAL scoped signed phone/model → named remote coding/terminal Worker → real Python fixture child → independent exact-file read under Ask and synthetic Full. Authenticated coding-provider and broad development correctness remain PARTIAL; minimal constrained image Git failure remains unaccepted. [Remote artifacts](../evidence/software-completion/remote-artifacts-2026-10-25.json) |
| 19 | Cross-application automation | PARTIAL: signed browser submission → fresh exact receipt → dependent independently verified local confirmation file; broader installed-application workflows OPEN. [Browser contract](SOFTWARE-BROWSER-WORKFLOWS.md) |
| 20 | Independent result verification | LOCAL files, UIA text, provider saved resources and exact browser URL/element text through a fresh Chromium read; remote coding/terminal artifacts now use separately authorized file readback and exact Core comparison; generic screen/click/invoke outcomes remain PARTIAL. [Remote artifacts](../evidence/software-completion/remote-artifacts-2026-10-25.json) |
| 21 | Operate actual emulator test app | LOCAL actual disposable API35 fixture. [Android conversation](../evidence/software-completion/android-conversation-2026-10-24.json) |
| 22 | Native capability admission | LOCAL actual OS-grant/session/source admission and withdrawal; physical OEM commissioning OPEN |
| 23 | Android UI / gestures | LOCAL actual exact-resource click/text/scroll subset; generic outcome PARTIAL, arbitrary app workflows unaccepted |
| 24 | Permission withdrawal | LOCAL actual emulator source/capture stop and scoped regression; no physical phone claim |
| 25 | Android-to-Desktop handoff | LOCAL actual Android Activity/CoreSession conversation creates Worker through separate TLS Core and outbound Windows Worker; exact file independently verified and returned to Android. Synthetic model/native-session owner authority; broader model/native visual acceptance remains PARTIAL. [Receipt](../evidence/software-completion/android-conversation-handoff-2026-10-25.json) |
| 26 | Process death / restore | LOCAL actual force-stop/relaunch, Keystore session, unchanged claims and fresh work. [Recovery receipt](../evidence/software-completion/android-recovery-2026-10-24.json) |
| 27 | Grid revocation | LOCAL actual emulator revoked-session notice withdrawal and native/Core tests |
| 28 | Ask confirmation | LOCAL actual two exact reviews/model/file and native signed effects; no opening/preview grants execution |
| 29 | Secure ordinary operation | LOCAL synthetic standing-authority regression; actual owner activation uncommissioned (`tests/test_authority.py`) |
| 30 | Secure protected operation | LOCAL exact-review and protected-policy negatives; stronger physical owner acceptance separate |
| 31 | Signed Full activation | LOCAL synthetic native contract/management review and signed owner key; actual owner Full remains inactive |
| 32 | Full autonomous operation | LOCAL signed Full conversation model/file readback and phone/model-created outbound coding/terminal Workers with independent artifact inspection without per-action prompts; general model reliability PARTIAL. [Remote artifacts](../evidence/software-completion/remote-artifacts-2026-10-25.json). [Full receipt](../evidence/software-completion/full-planning-2026-10-24.json) |
| 33 | Downgrade / revoke | LOCAL grant epoch/policy/session/account race tests; no instantaneous remote process-kill guarantee |
| 34 | Stale / offline authority denial | LOCAL target checks and lease/revocation tests, actual recovery/no replay |
| 35 | Spoken task | LOCAL real prepared wake/VAD/STT models, synthetic audio → Core → real math/file → Kokoro PCM. [Voice integration](SOFTWARE-VOICE-INTEGRATION.md) |
| 36 | Barge-in | LOCAL synthetic audio and native bridge cancellation; room AEC/physical human acceptance OPEN |
| 37 | Mute / stop | LOCAL persisted mute/heartbeat and explicit native control contracts; defaults stay muted |
| 38 | Voice authorization | LOCAL source/speaker/grant rules; recognition never grants action authority; owner Voice Match uncommissioned |
| 39 | Sentry transitions | LOCAL actual emulator and Core mode/expiry/withdrawal tests. [Sentry delivery](SOFTWARE-SENTRY-DELIVERY.md) |
| 40 | Source capture / retention | LOCAL independent source grants, actual eight-source zero-retention run and explicit single-app frame retention |
| 41 | Multi-source day context | LOCAL clock/calendar/weather/phone/connected-task source contracts and actual eight-source phone run; unified daily-use acceptance PARTIAL |
| 42 | Calendar / task coordination | PARTIAL observed overlap, signed selected task-list briefing, signed calendar creation and Google Tasks/Microsoft To Do creation with independent saved-resource readback; read-only current task attention now orders overdue/today/reported importance and expires at source/deadline/date boundaries in both apps. Automatic schedule coordination and daily-use acceptance remain OPEN. [Attention](../evidence/software-completion/attention-2026-10-25.json). [Task contract](SOFTWARE-COMMUNICATION-INTEGRATION.md) |
| 43 | Create scheduled automation | LOCAL actual native conversation review/decline and signed Executive creation. [Authoring](SOFTWARE-EXECUTIVE-AUTHORING.md) |
| 44 | Persistent Worker after UI closure | LOCAL separate Core scheduled process and outbound Worker acceptance. Named temporary Workers retire after all responsibilities finish; 65 successive jobs preserve history without lifetime quota exhaustion. Synthetic model-created remote coding/terminal Workers also pass Ask/Full exact-file inspection; broader adaptive delegation remains PARTIAL. [Remote artifacts](../evidence/software-completion/remote-artifacts-2026-10-25.json). [Handoffs](../evidence/software-completion/worker-handoffs-2026-10-25.json) |
| 45 | Conditional / schedule triggers | LOCAL Executive event/occurrence tests; richer real daily monitoring acceptance OPEN |
| 46 | Interrupt / recover / verify | LOCAL actual Core/Worker restart and 98 independently read-back effects; uncertain mutation never replayed. [Soak](../evidence/software-completion/soak-fbe12e3-2026-10-24.json) |
| 47 | Useful proactive notification | PARTIAL actual transient Sentry notices/quiet/expiry; usefulness and broader Chief-of-Staff follow-up acceptance OPEN |
| 48 | Same canonical task on Desktop / Android | LOCAL signed synthetic phone → Core arithmetic → outbound Desktop file with exact independent readback and result provenance. Explicit device lists pin each executor. Actual Android conversation/native task readback now passed with synthetic model/authority; newest rendered Desktop workflow remains PARTIAL. [Android receipt](../evidence/software-completion/android-conversation-handoff-2026-10-25.json). [Handoffs](../evidence/software-completion/worker-handoffs-2026-10-25.json) |
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

Broader cross-account and installed-application workflows beyond the explicit
browser/file/browser transfer, richer Chief-of-Staff
coordination, reliable general model planning and semantic
visual reasoning need further implementation or integration acceptance. They are
not reclassified as owner-only commissioning. API/OAuth consent, actual owner
activation, hosted Core, physical phone/audio and hardware remain separately
authorized commissioning. Group 6 and Slice 20 are not passed by this matrix.
