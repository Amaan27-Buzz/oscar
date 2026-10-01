# Feature Inventory

This is OSCAR's capability backlog. Listing a feature here does **not** mean it is implemented.

## Interaction

- Natural-language voice and text as equal interfaces in one continuous context.
- Short contextual commands such as `mute`, `cancel that`, `leave it running`, `what did it find?`.
- Immediate local wake/reflex acknowledgement.
- Barge-in while OSCAR is speaking.
- Streaming STT/reasoning/TTS where useful.
- Fluid state transitions rather than unrelated page swaps.
- Configurable Persona without sacrificing clarity, truth or speed.

## Interaction Runtime — Dictate / Edit / Ask / Act

- `Dictate`: literal/cleaned speech into focused target.
- `Edit`: transform selected/recent text.
- `Ask`: answer about current app/screen/selection/cursor context.
- `Act`: operate current app/device/task through the strongest legitimate capability.
- Accessibility tree, selected text, screenshots and clipboard/input-method fallbacks.
- Point-and-talk.
- Action-Ledger-backed Undo where real compensation exists.

## Persona

- User-configurable OSCAR character.
- Natural-language Persona editing.
- Manual core traits such as Humor, Candor, Warmth, Formality, Brevity, Playfulness, Initiative and Pushback.
- Context triggers for calls, Sentry/security, coding/deep work, quiet/night and specific relationships/projects.
- Original starting profiles such as Wry, Steady, Spark, Formal and Custom.
- Text/voice/avatar preview.
- Truthfulness, safety, permissions and required confirmations remain fixed/non-configurable.
- Persona distinct from Personal Policy and memory.

See [PERSONA.md](PERSONA.md).

## Connection Grid / availability

- One availability/control fabric across Sunday, cloud coordinator, desktop nodes and Edge.
- No ordinary laptop/desktop as permanent host.
- Sunday as preferred everyday owner-control/kill-switch surface.
- Phone biometric/PIN for owner-critical approval/revocation.
- Remote inspect/pause/cancel/revoke of work and nodes.
- Replaceable cloud rendezvous/durable coordination.
- Free-tier, paid and bring-your-own-cloud deployment paths.
- Desktop high-capability execution.
- Edge local awareness/reflex/safety.
- Explicit availability states such as Full, Connected, Local, Reflex-only and Offline.
- Per-node identity, capability advertisement, health and task leases.
- Graceful degradation when a node/provider/network disappears.
- Reconnect/resync without losing durable task state.

See [CONNECTION-GRID.md](CONNECTION-GRID.md).

## Remote continuation

- Start a Codex/build/render/other long-running machine task and leave the computer physically unattended.
- Continue progress/event flow through the Connection Grid.
- Inspect/approve/pause/cancel from Sunday.
- Durable checkpoints/leases so executor loss is recoverable.
- Independent result verification where practical.
- Optional sleep/shutdown after verified completion when a real machine capability and Personal Policy permit it.
- Remote wake only where a real Wake-on-LAN/management/power capability exists.
- Never fabricate remote power/control for an offline node.

## Multi-device voice arbitration

- Sunday, desktop and physical OSCAR can hear the same wake/utterance without all responding.
- One surface normally owns a voice turn.
- Arbitration may use wake confidence, mic quality, proximity, active device, presence and explicit priority.
- Handoff/failover while preserving the same task/context.

## World Model

- Live graph of people, places, devices, apps, projects, objects, tasks, Workers and Protocols.
- Current state distinct from memory.
- Freshness/confidence/provenance.
- Stale state becomes stale/unknown.
- Device/Connection Grid availability represented as current state.

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

- Federated current-source retrieval across files/drives, mail, messages, knowledge systems, browser, GitHub, calendar, social accounts, Sunday, desktops, Edge and Workers.
- Live authoritative state preferred over stale memory.
- Provenance and source authority preserved.

## Entity graph

- Resolve people across contacts/email/messaging/Voice Map where evidence allows.
- Resolve organizations/projects/accounts/devices consistently.
- Link communication/calendar/project/task state to canonical entities.

## Personal Policy

- Open-ended user behavior rules editable by voice/text.
- Scope to people, apps, projects, Workers, calls, meetings, locations, Sentry/capture modes, Connection Grid behavior and time windows.
- Explicit policy distinct from Persona, memory and permission.
- Inferred preferences can be suggested but do not silently become authority.

See [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

## Communication

- Unified calls/messages/email/meetings/dictation layer.
- Cellular/SMS where platform permits.
- WhatsApp/Telegram/other app communication where legitimately available.
- Zoom/Meet/Teams/Discord-style meeting support where supported.
- AI call answering under explicit Personal Policy.
- Message taking, urgency, callback scheduling and call summaries.
- Meeting transcription, diarization, decisions/actions/follow-up.
- System-wide dictation and voice notes.
- Native OS/official API first, then connector/plugin, device automation, computer-use/accessibility fallback.
- Persona-aware professional/casual tone without changing authority.
- Explicit capability limits per channel/app.

See [COMMUNICATION.md](COMMUNICATION.md).

## Universal Channel Gateway

- Normalize supported communication into channel/account/thread/participant/direction/type/text/transcript/media/timestamp/source-ID envelopes.
- Preserve per-channel capabilities rather than pretending parity.
- Link communication events to entities, World Model, LRA and Personal Policy where permitted.

## Persistent Sentry

- Always-present local-first awareness when enabled.
- Wake/hot/reflex commands.
- VAD / speech presence.
- Voice Map speaker events.
- Configured sound-event classification.
- Motion/environment/device/health events.
- Communication/context events.
- Modes: Passive, Aware, Guard, Away, Sleep.
- Importance/urgency/confidence/interruptibility scoring.
- Silent context update, notification, speech or urgent interruption according to policy.
- Self-voice suppression.

### Product-facing acoustic states

- `Sentry Aware` — persistent local acoustic/event awareness may be active.
- `Listening` — active conversational STT.
- `Muted` — ordinary conversational listening suppressed; configured local reflex commands may remain.
- `Awareness Off` — local acoustic plane disabled.
- Typing remains another modality, not an automatic voice-off switch.

## Context Capture / Daily Journal

Optional explicit continuity capture, not implied by Sentry awareness.

Potential sources where technically/legally available:

- phone calls;
- supported app calls;
- SMS/messages;
- email;
- meetings;
- voice notes;
- ordinary in-person conversations;
- day-to-day environment/context events.

Capture levels:

```text
Awareness only
Context capture
Daily journal
```

Independent controls for:

- activated STT;
- ambient/context STT;
- raw audio retention;
- transcript retention;
- summary retention;
- memory extraction;
- person/place/time/source exclusions;
- pause/delete/forget.

Unsupported capture remains unsupported. Capture is never designed as covert recording.

See [VOICE-SENTRY.md](VOICE-SENTRY.md) and [COMMUNICATION.md](COMMUNICATION.md).

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
- normal, quiet/night, focused/serious, alert and representative modes;
- streaming/chunked TTS;
- fallback mapping with explicit degradation.

### Voice Match

- owner/authorized-speaker enrollment;
- confidence scores;
- authorization signal only;
- voice alone insufficient for critical actions.

### Voice Map

- owner / known / recognized-but-unverified / unknown / multiple / uncertain states;
- confidence/provenance;
- optional canonical-person linkage only with enough evidence/consent;
- recognition never grants permission;
- profiles/embeddings are sensitive;
- OSCAR TTS excluded from learning/matching.

## Native Transport + Capability Fabric

- Typed task/event/action/result transport.
- Node/session identity and scoped pairing credentials.
- Capability advertisement.
- Correlation IDs, replay protection and idempotency.
- Reconnect/backoff.
- Progress/stream callbacks.
- Permission-aware dispatch.
- Outbound-first private-node rendezvous.
- Small Edge client/protocol.
- No required Latch runtime.

## Native Model Router

- Provider/model registry.
- Multiple credentials per provider.
- Health/quota/rate/latency/cost state.
- Task/model affinity and capabilities.
- Auto, Fast, Balanced, Heavy Duty, Free First, Cheap, Local, Private, Manual and Specialist profiles.
- Fallback/circuit behavior.
- Local Ollama/LM Studio/vLLM-style runtimes.
- Usage/model/key-slot/routing history.
- Models remain reasoning sources, not authority.
- No required SwitchRoute runtime.

## Coding / executable specialists

- Codex, Claude Code, OpenCode and other installed coding agents as capabilities.
- Terminal/PowerShell/shell.
- Browser/computer-use.
- Filesystem/Git/IDE.
- Installed apps and specialist software.
- Capability selection distinct from model-provider routing.

## Jev

- Fast typed intent + epistemic routing.
- `known / world / recall / verify / reason / reported / specialist / worker / unknown`.
- Deterministic path where sufficient.
- Query current evidence/memory/live sources as needed.
- Repair/reroute recoverable problems before asking the user.

## Epistemic Integrity

- Intention, execution, reported result, observation and verified completion remain distinct.
- Explicit planned/executing/result_received/verifying/verified/partial/failed/blocked/cancelled/unknown states.
- Tool/Worker/model success is testimony, not objective proof.
- UI/avatar state follows real runtime state.

## LRA + Supermemory

- Persistent single relationship/history.
- Active context separate from long-term recall.
- Episodic/project/device/procedural/profile/relationship memory.
- Cross-device continuity.
- Searchable history/timeline.
- Correct/forget controls.
- Daily Journal artifacts/derived facts can feed memory only under retention policy.

## Workers

- Temporary/task/persistent Workers.
- Natural-language creation/control.
- Goal/context/permissions/capabilities/verification/escalation state.
- Use Sunday, desktop, APIs/plugins, model routing, installed apps and Edge.
- Bounded retry/recovery/reroute.
- Durable state for long-running responsibilities.
- Worker success remains `REPORTED` until objective verification.

## Executive Planner

- Coordinate priorities/deadlines/dependencies/resources/interruptibility/risk/cost.
- Schedule/parallelize/pause/pre-empt/reroute/defer.
- Never bypass Jev, Personal Policy or permissions.

## Durable Execution Runtime

- Durable task IDs/lifecycle/checkpoints.
- Leases/heartbeats/retry budgets/cancellation/deadlines.
- Executor/current surface.
- Artifact/result/verification state.
- Reclaim abandoned/zombie work.
- Idempotency/dedup where needed.

## Capability Catalog + Dynamic Tool Search

- Search lightweight manifests rather than preload every tool.
- Availability, suitability, latency/cost, permission/risk, reliability, project affinity, undo and adapter/version metadata.
- Load detailed contracts only for finalists.
- Capabilities can disappear/reappear without killing OSCAR.

## Action Ledger + Undo

- Consequential actions record intent/initiator/target/capability/permission-policy decision.
- Execution + verification state/evidence.
- Reversible/irreversible flag.
- Real compensation only when supported.
- Queries such as `what did you change?`, `why?`, `did you verify it?`, `undo that`.

## Artifact / Result Model

- First-class docs, media, code changes, reports, meeting/call notes, Daily Journals, deployments, firmware builds, datasets/models/evaluations.
- Artifact ID/kind/name, owner, producer, location/version/hash, provenance, verification, access scope and relationships.

## Sunday

- Native Android embodiment.
- Present-not-launched home state.
- Voice/text.
- Notifications/proactive alerts.
- Connection Grid owner controls.
- Remote task continuation/supervision.
- Calls/messages/email/meetings where supported.
- Sentry + Context Capture/Daily Journal controls.
- Persona configuration.
- Camera/sensors/location where authorized.
- Biometric/PIN sensitive approval.

## Desktop

- Native/lightweight Windows/macOS presence.
- Compact overlay + contextual expansion.
- Dictate/Edit/Ask/Act.
- Screen/cursor/selection/accessibility context.
- Machine capability/health state.
- Remote continuation after user leaves.
- Connection Grid visibility/control.
- Fluid state-driven motion.

## Edge / physical world

- ESP32 networking/audio/event gateway.
- Pico deterministic controller.
- Sensors/buttons/displays/LEDs/relays/actuators/cameras via suitable nodes.
- Workbench/environment telemetry.
- Deterministic watchdog/interlock/emergency behavior.
- Optional Wake-on-LAN LAN helper where supported.
- Device capability discovery/health/provisioning.

## Learning / Skills / Protocols

- Capture verified successful novel execution paths.
- Distill/parameterize procedures.
- Evaluate before promotion.
- Version/rollback.
- Teach-by-demonstration where authorized.
- Protocols can wait/observe/branch/delegate/retry/verify/escalate over time.
- Learned behavior cannot self-grant permission.

## Predictive intelligence

- Forecast schedule/deadline/device risk.
- Detect trends/anomalies when evidence supports them.
- Prefetch/prepare context.
- Predictions remain evidence, not authority.

## Self-maintenance

- Detect expired auth, provider degradation, broken adapters, disappearing Grid nodes/capabilities, Edge disconnects, task leases, storage/state health and update failures.
- Safe bounded repair/rollback where authorized.
- Minimum user intervention when genuinely blocked.

## Design / product behavior

- Quietly Alive + Playful Precision.
- 70% restraint/whitespace, 20% tactile industrial precision, 10% approachable personality.
- Warm cream/off-white materials + graphite typography.
- Blue/yellow reserved for OSCAR identity/presence/state.
- Weighted blue-shell/yellow-puck presence object.
- Fluid shared-geometry state transitions.
- Kaizen UI development: research real shipping patterns → build → inspect → improve → verify → expand.
- Image reference prompt library under `image-prompts/`; coded UI is source of truth.
- No generic AI dashboard, permanent chat sidebar, card walls, glass/neon/purple gradients or fake telemetry.
