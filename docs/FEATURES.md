# Feature Inventory

This document is the comprehensive capability backlog for OSCAR. A feature being listed here does not mean it is implemented.

## Interaction

- Natural-language voice and text as equal first-class interfaces.
- Shared context between voice, text, Sunday, desktop, ChatGPT and physical surfaces.
- One continuous relationship/history rather than a mandatory chat-sidebar workflow.
- Short contextual commands such as `mute`, `cancel that`, `leave Codex running`, `what did it find?`.
- Barge-in: interrupt speech instantly and resume listening.
- Streaming recognition, reasoning and speech output where supported.
- Configurable response style, verbosity and proactivity.
- Personality/expression without sacrificing clarity or speed.

## Interaction Runtime — Dictate / Edit / Ask / Act

- First-class system-wide interaction runtime rather than separate dictation/editing/agent silos.
- `Dictate`: literal or cleaned speech inserted into the current target.
- `Edit`: transform selected/recent text naturally.
- `Ask`: answer about current screen/selection/cursor/app context.
- `Act`: operate current app/device/task through the best available capability.
- Focused app/window/control/text-field awareness.
- Selected-text/cursor/accessibility-tree context.
- Screenshot/visual context when needed.
- Clipboard/input-method fallback where native insertion is unavailable.
- Point-and-talk: `what is this?`, `reply to him`, `fix this button`.
- Undo surface connected to Action Ledger when a real compensation exists.

## Multi-device voice arbitration

- Sunday, desktop and physical OSCAR can all listen without all responding at once.
- Exactly one surface normally owns a voice turn.
- Arbitration may use wake confidence, microphone quality, proximity, active device, room/presence, explicit priority and available context.
- Explicit handoff/failover.
- Shared turn/task state after arbitration.

## World Model / digital twin

- Live graph of people, places, devices, apps, projects, objects, tasks, Workers and Protocols.
- Relationships/current state distinct from historical memory.
- Freshness, confidence and provenance metadata.
- Stale state becomes `stale/unknown` rather than current truth.
- Reconcile current observations with structured state and authoritative sources.

## Perception Fabric

- Normalize current evidence from screens, accessibility trees, cursor/selection, cameras, microphones/audio events, Voice Map events, apps, devices, phone context, location, sensors and Worker/Protocol state.
- Current evidence separate from durable retention.
- Multimodal fusion where useful.
- Source/freshness/confidence metadata.

## Universal live context/search

- Federated current-source retrieval rather than hard-coding every connector into Jev.
- Search files/drives, mail, messages, knowledge systems, browser state, GitHub, calendar, social accounts, Sunday, desktop nodes, Edge telemetry and Worker/Protocol state.
- Preserve provenance and source authority.
- Prefer live authoritative state over stale recalled memory.

## Canonical entity / relationship graph

- Resolve one person across contacts, email, messaging identities, Voice Map identity and remembered relationship.
- Resolve organizations/projects/accounts/devices consistently.
- Link communication/calendar/project context to canonical entities.
- Avoid duplicate identities when evidence can resolve them.

## Personal Policy and preferences

- Open-ended preferences rather than a fixed settings list.
- Create/edit/remove through ordinary voice/chat.
- Scope to people, apps, projects, Workers, devices, calls, meetings, locations, Sentry modes, time windows and arbitrary user-defined context.
- Distinguish memory, policy, permission, routine and Protocol.
- Explicit policy overrides inferred suggestions.
- Safety/legal/platform constraints and permissions remain authoritative.
- Inspectable/versionable durable policy with provenance.
- Inferred patterns can be proposed rather than silently gaining authority.

See [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

## Communication

- OSCAR as unified communication layer rather than separate call/meeting/dictation bots.
- Phone calls/messages subject to platform support and permissions.
- WhatsApp/Telegram/other app communication where technically available.
- Zoom/Meet/Teams/Discord-style meeting participation where supported.
- In-person meeting capture through authorized microphones/devices.
- AI call answering under explicit Personal Policy.
- Rules such as answer after N rings, caller exceptions and context-aware handling.
- Take messages, determine urgency, schedule callbacks and summarize calls.
- Meeting transcription, diarization/speaker labels where reliable, notes, decisions, action items and follow-ups.
- System-wide dictation, voice notes and app messaging.
- Native OS/official API first, then connector/plugin, device automation/computer use fallback.
- Raw audio/transcript retention controls.
- Concrete capability mapping per platform/app instead of assumed call control.

See [COMMUNICATION.md](COMMUNICATION.md).

## Universal Channel Gateway

- Normalize supported inbound/outbound communication across cellular/SMS where possible, messaging apps, work channels, email, social DMs/replies and future adapters.
- Common event envelope for channel/account/thread/participants/direction/type/text/transcript/media/timestamps/source IDs.
- Per-channel capability advertisement rather than assumed parity.
- Channel events linked to entities, World Model, LRA and Personal Policy where appropriate.

## Action Ledger + universal Undo

- Structured record for consequential actions.
- Initiator/intent/target/capability/permission-policy decision.
- Before/result state references when available.
- Execution and verification state/evidence.
- Limitations/untested surfaces.
- Reversible/irreversible flag and real compensation when supported.
- Correlation ID + timestamp.
- Natural queries: `what did you change?`, `why?`, `did you verify it?`, `undo that`.

## Reflexes and local commands

- Local wake-word detection.
- Voice activity detection.
- Immediate `mute`, `stop`, `cancel`, `listen`, `sentry`, `stand down` commands.
- Simple local device controls without an LLM.
- Hardware emergency-stop path.
- Local resolution of active-task references when unambiguous.

# Voice system

## Voice Input

- Local wake word + VAD.
- Streaming STT abstraction.
- Low first-token/first-action latency.
- Barge-in while OSCAR is speaking.
- Echo cancellation and playback reference.
- Voice/text shared task state.

## OSCAR Voice Identity

- Natural low-latency TTS.
- **Stable OSCAR voice identity** across Sunday, desktop and desk surfaces.
- Provider-independent `VoiceProfile` rather than an arbitrary TTS-provider default.
- Prosody/modulation/pace/rhythm policy.
- Pronunciation lexicon/control.
- Contextual speaking modes: normal, quiet/night, focused/serious, alert and representative/call mode.
- Streaming/chunked speech.
- Provider fallback mapping that preserves identity as closely as possible.
- Report material degradation when a fallback cannot preserve voice quality/identity.
- Voice identity/version can evolve intentionally rather than changing because a vendor default changed.

## Self-voice suppression

- TTS-origin tagging.
- Known playback-reference audio.
- Hardware/software acoustic echo cancellation.
- Correlation between generated audio and microphone input.
- Exclude OSCAR's own voice from Voice Map enrollment/identity updates.
- Preserve real human barge-in while OSCAR speaks.

## Voice Match

- Owner/authorized-speaker enrollment during setup.
- Samples across phrases, distances, volumes and noise conditions.
- Confidence-based speaker verification.
- Voice Match integrated with authorization policy.
- Different policy for owner, authorized user, guest and unknown speaker.
- Voice biometrics never sufficient alone for critical actions.

## Voice Map

Voice Map is perception, not authorization.

- Local speaker-profile/embedding abstraction where feasible.
- States: `owner`, `known_person`, `recognized_but_unverified`, `unknown_speaker`, `multiple_speakers`, `uncertain`.
- Optional linkage from voice profile to canonical person/entity with provenance and confidence.
- Unknown voices remain unknown rather than guessed.
- Do not silently assign a real identity from a weak acoustic match.
- Speaker-change/presence events can exist without full transcription.
- Meeting/call diarization may reuse Voice Map signals but remains confidence-qualified.
- Voice Map recognition never grants permission by itself.
- Voice profiles/embeddings treated as sensitive biometric-like data with explicit retention controls.
- OSCAR's own synthesized voice excluded from learning/matching.

See [VOICE-SENTRY.md](VOICE-SENTRY.md).

## Sentry Mode

- Always-on low-power awareness.
- Local wake/audio-event processing rather than continuous cloud microphone streaming.
- **Always-on local acoustic Sentry plane when enabled**:
  - wake word;
  - speech/non-speech presence;
  - Voice Map known/unknown classification;
  - speaker-change/multiple-speaker events;
  - configured unusual sound classes;
  - barge-in while OSCAR speaks.
- Speech presence, speaker identity, transcription and transcript retention are separate policy decisions.
- Presence/motion/environment/device/workbench monitoring.
- Known/unknown voice events when enabled.
- Event fusion across signals.
- Importance, urgency, confidence and interruptibility scoring.
- Silent logging, notification, spoken alert or urgent interruption according to policy.
- Modes: Passive, Aware, Guard, Away and Sleep.
- Self-voice suppression so Sentry does not react to OSCAR's own speaker output.

## Predictive intelligence

- Forecast schedule conflicts/deadline risk.
- Detect abnormal device/sensor trends where evidence supports it.
- Prepare diagnostics/context for likely failures.
- Prefetch context for likely upcoming tasks/transitions.
- Predictions remain evidence, not authority.

# Native OSCAR infrastructure

## Native Transport + Capability Fabric

The useful architecture/logic from the separate Latch project is folded into OSCAR natively. Latch is not a required external runtime dependency.

- Typed bidirectional task/event/action/result transport.
- Node/session identity.
- Pairing/scoped credentials.
- Capability advertisement.
- Correlation IDs.
- Reconnect/backoff.
- Progress/stream callbacks.
- Permission-aware dispatch.
- Audit/provenance metadata.
- Secure outbound rendezvous for private devices.
- Small Edge transport client/protocol for embedded nodes.
- ChatGPT/provider-specific transport details hidden behind OSCAR-owned adapters.

## Native OSCAR Model Router

The useful architecture/logic from the separate SwitchRoute project is folded into OSCAR natively. SwitchRoute is not a required external runtime dependency.

- Provider/model registry.
- Route by task/capability, quality, latency and cost.
- Provider/model fallback.
- Health/availability state.
- Context-limit/capability metadata.
- Small/fast models for classification/extraction where useful.
- Stronger reasoning models only when needed.
- Routing telemetry/outcome history.
- Model inference never silently relabeled as verified fact.

## ChatGPT provider/surface

- ChatGPT can reason for OSCAR through OSCAR-owned provider/transport adapters.
- OSCAR can expose tools/capabilities to ChatGPT where supported.
- A ChatGPT-specific wake/trigger mechanism is replaceable behind OSCAR-owned infrastructure.
- ChatGPT has no special hardware-safety authority.
- Agent/model success reports remain reported/inferred until verified where needed.

See [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md).

## Intent and epistemic routing — Jev

- Fast typed intent recognition.
- Detect when OSCAR already has enough context.
- Query World Model for current state.
- Decide when memory/live verification/model reasoning/specialist delegation is necessary.
- Jev chooses the class of path; native Model Router chooses provider only after a model path is selected.
- Repair/reroute recoverable Worker/tool failures.
- Ask user only when ambiguity materially blocks safe/correct execution.
- Explicit `known / world / recall / verify / reason / reported / specialist / worker / unknown` states.

## Epistemic Integrity

- Distinguish intention, execution, reported success, observed result and verified completion.
- Task states include planned/executing/result_received/verifying/verified/partially_verified/failed/blocked/cancelled/unknown.
- Evidence states: KNOWN, INFERRED, RECALLED, REPORTED, VERIFIED, UNKNOWN.
- Tool/Worker/model success is testimony/evidence, not automatically truth.
- Unknown is preferable to guessing.
- UI/avatar state reflects real execution/verification state.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## Memory and continuity — LRA + Supermemory

- Persistent single-conversation/history architecture.
- Active context separate from long-term recall.
- Episodic conversation/task history.
- Cross-device continuity.
- Project/device/user/procedural memory.
- Profile/relationship memory.
- Personal Policy separate from inferred memory.
- Source/provenance/confidence metadata.
- Searchable history/timeline.
- User inspect/correct/forget controls.
- Current World Model state distinct from historical memory.

## Learning and procedural memory

- Capture verified successful novel execution paths.
- Distill/parameterize reusable procedures.
- Store capabilities/preconditions/verification strategy.
- Reuse known procedures on similar tasks.
- Measure latency/cost/reliability improvements.
- Version/rollback learned procedures.
- Teach-by-demonstration where authorized.
- Learned behavior never self-grants permissions.

## Sunday — OSCAR on phone

- OSCAR avatar + stable VoiceProfile.
- Voice/text interaction.
- Notifications/proactive alerts.
- Calls/messages/app actions subject to permissions/platform support.
- AI call answering where supported and policy allows.
- Mobile meeting transcription/notes.
- System-wide dictation/input assistance.
- Camera/microphone/sensors where authorized.
- Voice Match and Voice Map participation where supported.
- Biometric/PIN confirmation for sensitive actions.
- Handoff between phone, desk, ChatGPT and desktop.
- Mobile Sentry participation.

## OSCAR Desktop — Windows and macOS

- Native/lightweight app.
- Voice + text with stable VoiceProfile.
- Push/hold-to-talk.
- Full `Dictate / Edit / Ask / Act` runtime.
- System-wide dictation.
- Meeting transcription/notes.
- Screen/cursor/selection/app/accessibility context.
- Point-and-talk.
- Notifications/progress/approvals.
- Machine-node capability/health state.
- Searchable timeline/history.

## Machine Worker node

When online, a computer advertises capabilities such as Codex, computer use, terminal/PowerShell, browser, IDEs, Git/GitHub, Python, FFmpeg, Blender, filesystem, optional local models and GPU support.

The PC is never required for basic OSCAR availability.

## Delegated Workers / sub-agents

- Natural-language Worker creation.
- Temporary/task/persistent Workers.
- Worker goal/context/permissions/capabilities/verification/escalation state.
- Workers can use Sunday, desktop nodes, APIs/plugins, ChatGPT/native Model Router, installed/connected specialist applications and Edge.
- Parallel collaboration/handoffs/dependencies.
- Shared learned Skills.
- Protocol-driven Worker lifecycle.
- Jev repair/reroute before escalation.
- Bounded retries and explicit blockers.
- Durable state for long-running responsibilities.
- Worker success remains REPORTED until objective verification.

See [WORKERS.md](WORKERS.md).

## Executive Planner

- One global executive above Workers/Protocols.
- Consider priority/deadline/dependencies/resources/interruptibility/risk/cost.
- Schedule/parallelize/pause/pre-empt/reroute/defer.
- Never bypass Jev, Personal Policy or permissions.

## Durable Execution Runtime

- Durable task IDs/lifecycle/checkpoints.
- Leases/heartbeats/retry budget/cancellation/deadlines.
- Required capabilities/current execution surface.
- Artifact/result and verification state.
- Reclaim abandoned work, zombie detection, restart/resume.
- Idempotency/deduplication where needed.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Social-media management

- Persistent Social Worker when desired.
- Monitor/research/draft/prepare media/schedule/publish/reply within configured autonomy.
- Coordinate release announcements with project state.
- Summarize community feedback/performance.
- Prefer native API/channel adapters, then browser/desktop/Sunday fallback where legitimate.

## Software-task orchestration

- Delegate repository work to Codex or suitable coding specialist.
- Preserve specialist project/workspace context.
- Route design tasks through design specialists/plugins where available.
- Use computer use for GUI operation/visual verification.
- Run tests through machine nodes.
- Observe results, feed failures back, verify independently where practical.

## Capability Catalog + Dynamic Tool Search

- Dynamic node/app/plugin/Skill/channel capability advertisement.
- Lightweight searchable manifests.
- Availability, task suitability, latency/cost, permission/risk, reliability/history, project/workspace, undo and adapter/version metadata.
- Search/rank then load detailed contracts only for finalists.
- Capabilities can disappear/reappear without killing OSCAR.

## Artifact / Result Model

- First-class records for docs, spreadsheets, slides, media, code changes, research, meeting notes, deployments, firmware builds, datasets/models/evaluations and other durable outputs.
- Artifact ID/kind/name, owner, producer, location/reference, version/hash, provenance, verification, access scope and relationships.

## Edge / physical world

- ESP32 network gateway using native OSCAR Edge transport.
- RP2040/Pico deterministic GPIO controller.
- Buttons/displays/LEDs/sensors/relays/actuators/cameras through suitable nodes.
- Workbench telemetry, health and OTA/configuration.
- Future smart-home/environment integrations.

## Physical/device capability expansion

- Onboard and provision additional embedded/device nodes into native OSCAR transport.
- Advertise real sensors/actions/device health through the Capability Catalog.
- Support custom ESP32/Pico devices without changing OSCAR Core contracts.
- Integrate cameras, sensors, relays, displays, motors/actuators and environment controls through typed capabilities.
- Correlate device state with World Model/Perception.
- Run safe physical Protocols after authorization with local deterministic safety.

## Engineering/workbench capabilities

- Identify components/sensors and inspect telemetry.
- Correlate camera view with electronic state.
- Route circuit design/simulation, firmware and provisioning to suitable installed or connected specialist tools.
- Route CAD/3D/numerical simulation/diagnostics/reconstruction/optimization to specialist tools.
- Maintain inventory/context where useful.
- Treat engineering applications as replaceable capabilities rather than an OSCAR architectural dependency.

## Protocols and routines

- Named Protocols and recurring/event/time-triggered routines.
- Multi-step stateful procedures, wait states and branches.
- Background observation/delegation/recovery/escalation/completion conditions.
- Human approval gates for consequential steps.
- Durable Execution Runtime where restart/recovery matters.

## Skills and plugins

- Portable `SKILL.md`-style Skills.
- Plugin/connector discovery and capability metadata.
- OSCAR can identify when a specialist Skill/plugin is better than general reasoning.
- Generated Skills remain permission-scoped, inspectable and versioned.

## Self-created automation

- Skill/Worker/routine/Protocol candidates from explicit delegation or verified patterns.
- Preserve provenance.
- Never grant new authority implicitly.
- Explicit approval when automation broadens permissions/risk.

## Learned Automation Evaluation Pipeline

- Candidate, normalize/parameterize, replay/evaluate, verify safety/output, compare, policy review, promote/reject/experimental.
- Preserve evaluation cases/results/assumptions/limitations/rollback target.

## Research and analysis

- Search/retrieve approved sources.
- Compare sources.
- Async research Workers.
- Notify on meaningful findings.
- Preserve source/provenance and distinguish inference from verified fact.

## Proactivity

- Report meaningful changes without narration of routine background work.
- Suggest action when confidence/value are high.
- Continue delegated work after user leaves.
- Apply Personal Policy before inferred preferences.

## Device and environment awareness

- Node/capability/presence/device/environment state.
- User-configurable baselines and rule-first anomaly detection.
- Feed current state into World Model.

## Self-maintenance / diagnostics

- Detect expired auth, broken adapters/channels, stale capabilities, Edge disconnects, model/speech latency degradation, storage/state problems, update failures and stuck tasks.
- Repair/rollback safe failures where authorized.
- Ask user only for minimum intervention when necessary.

## Avatar and presence

- Blue-shell/yellow-face avatar as primary UI primitive.
- Weighted puck motion/directionality.
- Idle/listening/thinking/speaking/success/confusion/alert/sentry/sleeping/muted/error.
- Working/Verifying/Waiting/Blocked/Done/Failed runtime states.
- Success only after verified completion where applicable.

## First-run commissioning

- Identity and interaction preferences.
- Personal Policy starter rules.
- Communication/meeting/Worker autonomy defaults.
- Owner Voice Match enrollment.
- Optional known-person Voice Map enrollment/linking with explicit consent/retention.
- OSCAR Voice Identity listening/calibration/fallback test.
- Wake/reflex and self-voice-suppression test.
- Device discovery.
- Accounts/services/channels.
- Native transport/model-provider setup rather than separate Latch/SwitchRoute deployment.
- Permission matrix.
- Sentry configuration including acoustic awareness/transcription-retention choices.
- Environment setup.
- Sunday/desktop/Edge pairing.
- End-to-end verified health check.

## Permissions and security

- Capability-scoped permissions and action authorization classes.
- Voice Match as one signal, not sole high-risk auth.
- Voice Map never grants authority.
- Strong confirmation for critical actions.
- Universal local emergency stop.
- Action Ledger/audit for consequential actions.
- Device-scoped/rotatable credentials.
- Outbound Edge connections rather than exposed home endpoints.
- Minimal cloud audio/video exposure and explicit retention controls.
- Generated automation cannot self-elevate permissions.

## Reliability

- PC-independent operation.
- Local safety if cloud fails.
- Graceful capability loss.
- Bounded retries/backoff and idempotency where possible.
- Correlation IDs, watchdogs and health reporting.
- Recovery from partial task completion.
- Explicit blocker reporting.
- Durable tasks use checkpoints/leases/heartbeats/reclaim where needed.
- Reported success cannot silently become verified completion.
- Voice-provider fallback preserves OSCAR identity as closely as possible.
- Voice Map/speaker identity confidence remains explicit and unknown speakers remain unknown.
