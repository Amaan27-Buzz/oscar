# Feature Inventory

**Current reading:** [Product direction](PRODUCT-DIRECTION.md) specifies accepted UI ownership; [Adaptive Interface Engine](ADAPTIVE-INTERFACE.md) describes **planned** adaptive interactive answers. This inventory is a **backlog**, not a list of shipped features. Read [checked status](CURRENT-STATUS.md) and [delivery plan](DELIVERY-PLAN.md) for accepted foundations and new delivery order. Desktop interim design is merged; Mobile Group 2.5B implements the selected Codex ImageGen/Figma baseline; the Gemini Argon prototype is rejected. See [Group 2.5B implementation and evidence](ui/mobile/group25b/README.md).

## Group 2.5 owner correction — 2026-10-14

Current Desktop navigation: Conversation, Automations, Activity, Devices, Preferences. Dictate/Edit/Act are underlying contextual operations inside Conversation, not primary utility pages. Activity groups attention, running work and outcomes with exact evidence/signing detail. Canonical history is available only with installed Memory Fabric and explicit read/retain grants; otherwise the UI reports session-only history.

Group 3 integrated **bounded Core durable Workers, one-time/recurring schedules and recovery**. Native creation/editing, broad real trigger delivery and fully autonomous cross-device management remain **unavailable Desktop features**, not rejected product requirements. The existing task/runtime foundation remains usable. Ask is the current supported access state; Secure and genuine Full Access activation are unavailable. A bounded Core Sentry software lifecycle exists; owner-commissioned environmental/acoustic delivery remains unavailable.

See [the interaction and authority decision](decisions/ADR-DESKTOP-PERSONAL-INTELLIGENCE.md) for ownership, implemented boundaries and required integrations. Earlier dated checkpoints remain historical.


This is OSCAR's capability backlog. Listing a feature here does **not** mean it is implemented.

## Interaction

- Natural-language voice and text as equal interfaces in one continuous relationship.
- No required `new chat` workflow for memory/context continuity.
- Short contextual commands such as `mute`, `cancel that`, `leave it running`, `what did it find?`.
- Immediate local wake/reflex acknowledgement.
- Barge-in while OSCAR is speaking.
- Streaming STT/reasoning/TTS where useful.
- Fluid state transitions rather than unrelated page swaps.
- Configurable Persona without sacrificing truth or speed.

## Contextual operations inside Conversation — Dictate / Edit / Ask / Act

- `Dictate`: literal/cleaned speech into focused target.
- `Edit`: transform selected/recent text.
- `Ask`: answer about current app/screen/selection/cursor context.
- `Act`: operate current app/device/task through the strongest legitimate capability.
- Accessibility tree, selected text, screenshots and clipboard/input-method fallbacks.
- Point-and-talk.
- Action-Ledger-backed Undo where real compensation exists.

## OSCAR Memory Fabric

### One persistent relationship

- One user-facing OSCAR interaction point across text, voice, OSCAR Mobile, desktop, communication, Workers and Edge.
- Internal turns/episodes/projects/objectives/entities remain structured without forcing chat-thread management on the user.
- Dynamic Active Context assembled from current objective/project/entities/commitments, recent conversation, retrieved history and World Model state.

### Canonical Event Archive

- SQLite + WAL initial canonical durable history.
- FTS5 exact/full-text historical retrieval.
- Stable event/turn/episode/entity/memory/source identifiers.
- Provenance/evidence state/retention metadata.
- Corrections and supersession links.
- Canonical history survives replacement/rebuild of derived indexes.

### Semantic retrieval

- Qdrant OSS derived semantic index.
- Dense retrieval.
- Sparse/lexical retrieval where useful.
- Hybrid retrieval.
- Project/entity/time/type filters.
- Local/replaceable embeddings.
- Local/replaceable reranker.
- Derived records always point to canonical archive IDs.

### Temporal/entity retrieval

- Graphiti OSS + Neo4j Community derived temporal/entity index.
- Canonical entities and aliases.
- Relationship graph.
- Valid-from/valid-to history.
- Current vs historical fact retrieval.
- Preference/decision supersession.
- Provenance to source events.
- Same-name/ambiguous identities remain separate without evidence.

### Controller Memory Preflight

- Cheap memory-dependency classification on each interaction.
- Mandatory retrieval for historical/personal/project/entity/artifact/preference references.
- Skip unnecessary memory work for deterministic unrelated requests.
- Retrieval ladder: Active Context → structured OSCAR state → FTS/archive → Qdrant hybrid → Graphiti temporal/entity → query expansion → bounded deep archive → UNKNOWN.
- Empty first retrieval is not treated as proof that memory does not exist.
- Expected-memory misses trigger bounded query broadening before UNKNOWN.

### Evidence-bound recall

- No `I remember X` without actual retrieved/active source evidence.
- Personal/historical claims bind to source event/memory IDs internally.
- Recalled history remains `RECALLED` in the current reasoning path.
- Live authoritative current state outranks stale memory.
- Reasoning models cannot promote inference into fact.
- Retrieval/index scores never become epistemic authority by themselves.

### Memory formation and consolidation

- Episodic, semantic, preference, project, relationship, decision and procedural candidates.
- Candidate extraction from source events, not free-floating model summaries.
- Scope/overgeneralization checks.
- Entity resolution.
- Contradiction/supersession handling.
- Background dedup/evidence merge/summary/index maintenance.
- Original source events always retained according to policy.

### Memory resilience/evaluation

- Qdrant rebuild from canonical archive.
- Graph/temporal rebuild from canonical events.
- Index drift/lag health checks.
- Fallback to archive/FTS/UNKNOWN when derived index unavailable.
- Exact recall tests.
- Paraphrase recall tests.
- Temporal correctness tests.
- Entity alias/disambiguation tests.
- False-recall tests.
- Expected-memory-miss escalation tests.
- Correction/forget/rebuild tests.
- Cross-process continuity tests.

### Privacy/control

- Inspect source/provenance.
- Correct/supersede.
- Forget/tombstone active OSCAR memory.
- Remove derived semantic/graph entries where required.
- Export where practical.
- Retention controls by type/source/sensitivity.
- No false claim of secure disk erasure or deletion from external source systems.
- Voice Match/Voice Map embeddings remain dedicated sensitive data, not generic memory.

Managed memory vendors are optional adapters only; none is a required OSCAR dependency.

See [MEMORY.md](MEMORY.md).

## Persona

- User-configurable OSCAR character.
- Natural-language Persona editing.
- Manual traits such as Humor, Candor, Warmth, Formality, Brevity, Playfulness, Initiative and Pushback.
- Context triggers for calls, Sentry/security, coding/deep work, quiet/night and specific relationships/projects.
- Text/voice/avatar preview.
- Truthfulness, safety, permissions and required confirmations remain fixed/non-configurable.
- Persona distinct from Personal Policy and memory.

## Personal Policy

- Open-ended user behavior rules editable by voice/text.
- Bounded structured interpretation shown before activation.
- Exact owner confirmation before a newly interpreted rule becomes authoritative.
- Scope to people, apps, projects, Workers, calls, meetings, locations, capture, Grid behavior, schedules and time windows.
- Conflicts/ambiguity block rather than silently pick a rule.
- Policy cannot grant missing permission.
- Inferred preferences can be suggested but do not silently become policy.

## Connection Grid / availability

- One availability/control fabric across OSCAR Mobile, cloud coordinator, desktop nodes and Edge.
- No ordinary laptop/desktop as permanent host.
- OSCAR Mobile as preferred everyday owner-control/kill-switch surface.
- Remote inspect/pause/cancel/revoke of authorized work.
- Replaceable cloud rendezvous/durable coordination.
- Desktop high-capability execution.
- Edge local awareness/reflex/safety.
- Explicit Full / Connected / Local / Reflex-only / Offline states.
- Per-node identity, capability advertisement, health and task leases.
- Graceful degradation/reconnect/resync without losing durable task state.

## Real machine / remote continuation

- Scoped filesystem/Git.
- Typed terminal/PowerShell.
- Coding agents as discovered specialists.
- Installed-app discovery as app capability rather than generic process guessing.
- Windows UI Automation structured computer use.
- Keyboard/mouse fallback only when structured automation unavailable.
- Typed browser runtime with isolated profiles and deterministic verification.
- Start long-running work and leave owner-control surface.
- Separate owner-control client reconnects to same task.
- Durable checkpoints/leases.
- Independent result verification.
- Ambiguous post-mutation crash blocks replay.
- Optional power actions only when real and explicitly confirmed.

## World Model

- Live graph of people, places, devices, apps, projects, objects, tasks, commitments, Workers and Protocols.
- Current state distinct from memory.
- Freshness/confidence/provenance.
- Stale state becomes stale/unknown.
- Device/Grid availability represented as current state.

## Perception Fabric

- Screens/accessibility/cursor/selection.
- Cameras/screenshots where authorized.
- Microphone/acoustic events and Voice Map.
- Calls/messages/mail/meeting events.
- Apps/devices/phone context/location.
- Edge sensors/presence.
- Worker/Protocol/task state.
- Perception separated from durable retention.

## Universal live context/search

- Federated current-source retrieval across files/drives, mail, messages, knowledge systems, browser, GitHub, calendar, OSCAR Mobile, desktops, Edge and Workers.
- Live authoritative state preferred over stale memory.
- Provenance/source authority/freshness preserved.
- Public search remains distinct from browser automation.

## Entity graph

- Resolve people across contacts/email/messaging/Voice Map only where evidence allows.
- Resolve organizations/projects/accounts/devices consistently.
- Link communication/calendar/project/task state to canonical entities.
- Memory Fabric temporal/entity index reuses canonical identity rather than inventing a second identity system.

## Communication

- Unified calls/messages/email/meetings/dictation layer.
- Cellular/SMS where platform permits.
- WhatsApp/Telegram/other app communication where legitimately available.
- Meeting support where integrations permit.
- Message taking, urgency, callback scheduling and summaries.
- Meeting transcription, diarization, decisions/actions/follow-up.
- Native OS/official API first, then connector/plugin, device automation, computer-use/accessibility fallback.
- Explicit capability limits per channel/app.

## Connector / OAuth

- Official authentication flows.
- PKCE/device/system-browser flows where provider supports/requires them.
- Minimal scopes.
- Expiry/refresh/revoke lifecycle.
- Secure OS credential-storage boundary where practical.
- Tokens never enter memory, model prompts, Action Ledger or logs.
- Mutation results remain REPORTED until independent readback/verification.

## Persistent Sentry

- Always-present local-first awareness when enabled.
- Wake/reflex commands.
- VAD/speech presence.
- Voice Map speaker events.
- Configured sound-event classes.
- Motion/environment/device/health events.
- Communication/context events.
- Passive/Aware/Guard/Away/Sleep modes.
- Importance/urgency/confidence/interruptibility scoring.
- Self-voice suppression.

## Context Capture / Daily Journal

Optional explicit continuity capture, not implied by Sentry awareness.

Potential sources where technically/legal/policy available include phone calls, supported app calls, messages, email, meetings, voice notes and in-person conversations.

Independent controls for raw audio, transcript, summary, derived memory, person/place/time/source exclusions and pause/delete/forget.

Unsupported capture remains unsupported. Capture is never designed as covert recording.

## Voice system

### Voice Input

- local wake + VAD;
- streaming STT abstraction;
- low first-action latency;
- barge-in;
- echo cancellation/playback reference;
- shared voice/text task state.

### Voice Identity

- stable provider-independent `VoiceProfile`;
- prosody/modulation/rate/rhythm/pronunciation policy;
- contextual speaking modes;
- streaming/chunked TTS;
- fallback mapping with explicit degradation.

### Voice Match / Voice Map

- authorization-oriented Voice Match;
- perception-oriented Voice Map;
- owner / known / recognized-unverified / unknown / multiple / uncertain states;
- confidence/provenance;
- recognition never grants permission;
- profiles/embeddings are sensitive;
- OSCAR TTS excluded from learning/matching.

## Controller

- Typed `known / world / recall / verify / reason / reported / specialist / worker / unknown` routing.
- Deterministic path where sufficient.
- Memory Preflight and retrieval escalation where personal/history context is required.
- Freshness-sensitive live-source routing.
- Repair/reroute recoverable problems before asking the user.
- Authority/evidence requirements established before final claims.

## Epistemic Integrity

- Intention, execution, result testimony, observation and verification remain distinct.
- KNOWN/INFERRED/RECALLED/REPORTED/VERIFIED/UNKNOWN preserved.
- Tool/Worker/model success is testimony, not objective proof.
- UI/avatar state follows real runtime state.

## Native Transport + Capability Fabric

- Typed task/event/action/result transport.
- Node/session identity and scoped pairing credentials.
- Capability advertisement.
- Correlation IDs, replay protection and idempotency.
- Reconnect/backoff/progress.
- Permission-aware dispatch.
- Outbound-first private-node rendezvous.
- No required Latch runtime.

## Native Model Router

- Provider/model registry and multiple credentials.
- Health/quota/rate/latency/cost state.
- Account-product/shared-pool semantics.
- Auto/Fast/Balanced/Heavy Duty/Free First/Cheap/Local/Private/Manual/Specialist profiles.
- Fallback/circuit behavior.
- Local runtimes as optional providers.
- Models remain reasoning sources, not authority.
- No required SwitchRoute runtime.

## Workers / Executive / durable runtime

- Temporary/task/persistent Workers.
- Goal/context/permissions/capabilities/verification/escalation state.
- Bounded retry/recovery/reroute.
- Durable task IDs/checkpoints/leases/heartbeats/cancellation/deadlines.
- Executive coordination across priority/deadline/dependency/resource/interruptibility/risk/cost.
- Never bypass Controller, Personal Policy or permissions.

## Capability Catalog

- Search lightweight manifests rather than preload every tool.
- Availability/suitability/latency/cost/permission/risk/reliability/project affinity/undo metadata.
- Load detailed contracts only for finalists.
- Capabilities can disappear/reappear without killing OSCAR.

## Action Ledger + Artifact Model

- Consequential actions record intent/initiator/target/capability/permission-policy decision/execution/verification/evidence.
- Real compensation only when supported.
- First-class docs, media, code changes, reports, meeting notes, deployments, firmware builds, datasets/models/evaluations with provenance/version/location/verification.

## OSCAR Mobile

- Native Android embodiment.
- Present-not-launched behavior.
- Assistant/voice-interaction role where supported.
- Optional OSCAR Orb overlay with attention-aware retreat.
- Widgets.
- Notification awareness and legitimate RemoteInput replies.
- Grid owner controls and remote supervision.
- Biometric/PIN sensitive approval.

## Desktop

- Native Windows Tauri software/reference foundation (macOS not yet accepted).
- **Small standalone Companion + full Workspace**, not an expanding mini-chat widget.
- Conversation embeds contextual Dictate/Edit/Ask/Act; no primary Text Tools/Act navigation.
- Current Workspace navigation: Conversation / Automations / Activity / Devices / Preferences.
- Group 2.5A restrained neumorphic direction provisionally owner-approved and merged; final hardware/visual acceptance deferred.
- Screen/cursor/selection/accessibility context.
- Machine capability/health state.
- Remote continuation and Grid visibility/control.

## Edge / physical world

- ESP32 networking/audio/event gateway.
- Pico deterministic controller where appropriate.
- Sensors/buttons/displays/LEDs/relays/actuators/cameras via suitable nodes.
- Deterministic watchdog/interlock/emergency behavior.
- Optional Wake-on-LAN helper where real.

## Learning / Skills / Protocols

- Capture verified successful novel paths.
- Distill/parameterize procedures.
- Evaluate before promotion.
- Version/rollback.
- Teach-by-demonstration where authorized.
- Learned behavior cannot self-grant permission.

## Self-maintenance

- Detect expired auth, provider degradation, broken adapters, disappearing Grid capabilities, Edge disconnects, task leases, storage/state health, Memory Fabric index drift and update failures.
- Safe bounded repair/rebuild/rollback where authorized.

## Adaptive Interface Engine — typed software foundation integrated, full product future

- OSCAR can eventually assemble and update **trusted interactive views inside its same conversation**: comparisons, calendars/timelines, diagrams/simulations, charts, task/Worker progress, contextual device controls and structured reviews.
- Shared versioned **typed presentation description**, native React/Tauri and Jetpack Compose renderers, Core-authorized actions and accessible text fallback. Never treat generated markup/code as authority.
- **Integrated foundations:** Slices 16–17 typed shared presentation/Worker views. **Remaining:** richer views, Slice 19 authorization/accessibility/privacy hardening, Slice 20 native cross-device verification. No Group 2.5 native-product acceptance was retroactively established.
- [Full proposed architecture](ADAPTIVE-INTERFACE.md).

## Design / product behavior

- Quietly Alive + Playful Precision.
- Restrained **accessible neumorphism**, tactile industrial precision, original contextual Mobile illustrations and approachable personality.
- Warm cream/off-white materials + graphite typography.
- Blue/yellow reserved for OSCAR identity/presence/state.
- Weighted blue-shell/yellow-puck presence object.
- Fluid shared-geometry transitions.
- No generic AI dashboard, permanent chat sidebar, card wall, glass/neon/purple-gradient slop or fake telemetry.
