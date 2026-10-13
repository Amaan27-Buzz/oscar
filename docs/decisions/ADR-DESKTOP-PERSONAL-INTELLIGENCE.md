# Decision — one OSCAR, conversation, automations and delegated authority

Owner direction: 2026-10-14, Group 2.5. Candidate on `codex/desktop-companion-workspace`, draft PR #5 into main. No merge authorization.

## Interaction and ownership

OSCAR is one persistent multimodal intelligence. Core owns conversation, reasoning, historical memory, awareness, policy, task orchestration and executive decisions. Workers and specialists execute subordinate responsibilities; they do not acquire assistant identities or authority from their output.

| Feature | Authoritative owner | Desktop interaction | Present capability / next integration |
|---|---|---|---|
| Continuous relationship | Core + canonical Event Archive / Memory Fabric | Conversation; chronological turns, older history, related task inspection | Session history; retained history with explicit read/retain grants and installed archive. No frontend storage or chat threads |
| Text, dictation, app context, immediate operations | Controller + existing typed adapters | Contextual controls inside Conversation | Existing Dictate/Edit/Act, expected-value fencing, clipboard/UIA review. Screenshot understanding requires a real permissioned adapter |
| Immediate delegated tasks | Controller + Durable Runtime + Grid | Conversation; outcomes in Activity | Existing plan, exact approval, dispatch, cancellation, verification and recovery foundations |
| Routines, watches, named Workers, continuing Protocols | Controller + Executive + Durable Runtime | Conversation creates/instructs; Automations manages | Lifecycle/schema/scheduler/trigger and signed authority integration still required. No functioning named Worker controls in this candidate |
| Operational history | Core tasks / Action Ledger / evidence | Activity: attention, running work, outcomes; exact review on demand | Existing authoritative readback/signing, verification and failure states |
| Devices | Grid / capability catalog / target permission recheck | Devices inspects real advertised capabilities | Existing discovery and immediate action preparation; no invented screen or device capability |
| Companion | Redacted native projection / shared expression | Tiny presence, tray, shortcut and Workspace opening | Approved appearance preserved; no conversation, Worker UI or signing authority |
| Preferences | Native appearance settings; Core authority and permission state | Independent access/awareness/autonomy and retention status | Native appearance/shortcut working; no unsupported authority toggles |

## Three independent dimensions

Access is **Ask / Secure / Full Access**. Awareness is **Manual / Trigger-only / Sentry**; Sentry includes **Passive / Aware / Guard / Away / Sleep**. Worker autonomy is **Manual / Supervised / Autonomous**. Capture and retention are separate grants. None of these settings implies another.

Microphone permission, persistent mute, wake detection, conversational listening, acoustic processing, background transcription and retained audio are separate capabilities. This Desktop reports Trigger-only with explicit turns; persistent mute, wake and Sentry remain unavailable. No future capability is made operational by naming it.

## Corrected access contract

| Access | OSCAR operating authority | OSCAR per-action consent |
|---|---|---|
| Ask | Inspect authorized context, reason, propose | Required before external state changes |
| Secure | Broad ordinary operating capability | Protected/consequential actions still require consent |
| Full Access | Explicitly owner-activated unrestricted delegated autonomy over every technically available capability with necessary OS/service access | None, including supported consequential operations; activation is the owner consent |

The previous meaning of “Full Access” that retained consequential per-action consent is **Secure**. Full Access is not a larger Secure permission bundle. It cannot create OS permissions, defeat mandatory service confirmation or defeat local physical interlocks. It never removes audit, verification, provenance or failure handling.

## Mandatory enforcement conflict and legitimate delegation design

Today `Desktop.propose/catalog/complete` and `Mobile.complete` exclude critical capabilities; `PersonalPolicy.evaluate`, connector and Edge mutation paths enforce confirmation. Rust CNG signs an exact, immutable, expiring action challenge tied to node/session/target/task/digest. There is no signed standing delegation, mode epoch or distributed revocation fence. That path cannot legitimately activate Full Access. This candidate retains those blockers and reports **Ask only**; **Secure and Full Access activation are unavailable**, not silently implemented with Ask/Secure restrictions.

The next coherent authorization integration must introduce a distinct signed **owner delegation**, not a forged action approval:

1. Trusted owner activation binds owner identity, access mode, relationship, actual target/capability coverage, grant identity/revision, session/device bindings and lifetime. Full Access explicitly discloses irreversible supported operations and delegates all technically available action capabilities; underlying observe/retain grants remain independent. A Worker/model cannot request its own authority upgrade.
2. Core holds current mode/delegation and a monotonically increasing authority epoch. Each plan/action records grant, epoch, initiator, Worker/Protocol, target, capability and evidence references. Execution authorization is a typed reason such as `owner_delegation`, distinct from `owner_action_confirmation`.
3. All Controller, Runtime, Worker, connector, app and device paths consult the same Core authorization decision. Secure risk rules request protected-action consent. Full Access consumes valid standing authority without OSCAR action prompts, even for supported consequential operations. Owner activation explicitly resolves earlier per-action ASK policies; restrictions the owner retains are scope restrictions and must not be called unrestricted Full Access. Missing external/platform rights remain blocked with their actual source.
4. Owner revocation/downgrade increments the epoch atomically and stops new dispatch immediately. Targets recheck before every side effect, cancel active work where supported and reject expired/old epochs. Disconnected targets fail closed for delegated new mutations. No offline cached unrestricted authority. Already completed or indivisible operations cannot be undone by revocation; cancellation delivery and irreversible effects require honest readback.
5. Native activation uses a separate reviewed/signable claim. Companion and React possess no key or authority. Persisted grants require verified owner identity and expiry/restart rules; no default promotion from session settings or memory. Local safety remains deterministic. Platform-required confirmations are reported as external constraints, not relabeled OSCAR consent.

**Unresolved implementation decisions:** trusted activation identity strength (current CNG path has no verified Windows Hello attestation), distributed epoch propagation/atomic target fencing, credential/platform coverage, grant expiry/restart policy and in-flight cancellation semantics. Required tests include downgrade/revocation races, target loss, replay, changed scope, credential loss, restart, critical operation under each mode and absence of OSCAR prompts under genuine Full Access. Until all paths implement these together, no Full Access selector or grant endpoint is exposed.

## Conversation implementation and boundaries

`Desktop.conversation` projects authorized canonical conversation events plus originating-session transient turns. `desktop:conversation:read` permits relationship history read; `desktop:conversation:retain` plus Personal Policy permits owner/OSCAR turns to append to the existing archive. The relationship is chosen by the trusted Core composition, never client input. Ordinary text/action permission does not grant either scope. Attached private context, Dictate/Edit and tool payloads are excluded. Runtime private payloads remain transient and cannot replay after restart. Production provisioning must install Memory Fabric and separately enroll those scopes; this PR does not grant them to owner sessions.

History pages contain stable event/task references, source epistemic status and separate read/retention states. Event Archive uses one WAL connection/transaction per request thread; the HTTP adapter closes that thread connection after each request. Native history/snapshot parsing has a bounded 4 MiB response limit; other operations retain the 64 KiB limit. Archive revisions invalidate cached older pages on append/forget/revocation; history remains reloadable. Session-only turns disappear after restart. Recent model context uses a bounded 7,600-character evidence window plus current request; older material is omitted from active context and remains in authorized canonical history. This is deterministic context compaction, not a model-generated summary or model-extracted semantic memory formation. Verbatim retained turns use the existing MemoryWriter episodic path with source event IDs and REPORTED historical evidence, making archive FTS and existing Controller memory preflight available for contextual retrieval. Derived indexes remain rebuildable; no second memory system is introduced.

## Automation boundary

Automations includes one-time delegated jobs, schedules, event triggers, conditional watches, named persistent Workers, supervised/autonomous Workers and continuing Protocols. Immediate tool use remains in Conversation. Future records require responsibility/name, lifecycle, trigger/schedule/timezone, checkpoint/dependencies, task/Worker/Protocol correlation, access-grant/epoch and separate autonomy, cancellation, verification and source event references. Management mutations need Core commands with readback, replay fences, recovery and mode-aware authorization. Activity must link trigger → Worker/Protocol → task → result/evidence when these real records exist. This candidate exposes the unavailable integration honestly rather than synthesizing records or pause/resume controls.

## Acceptance boundary

Software and native reference evidence are recorded separately in the Group 2.5 product-direction packet. Preserve Orb, approved Companion, historical captures, Aperture and all branches. No Mobile redesign, backend framework rewrite, Slices 14–17 implementation, production promotion, merge or branch cleanup.
