# Feature Inventory

This document is the comprehensive capability backlog for OSCAR. A feature being listed here does not mean it is implemented.

## Interaction

- Natural-language voice and text as equal first-class interfaces.
- Shared context between voice, text, Sunday, desktop, ChatGPT and physical surfaces.
- One continuous relationship/history rather than a mandatory chat-sidebar workflow.
- Short contextual commands: “mute”, “cancel that”, “leave Codex running”, “what did it find?”.
- Barge-in: interrupt speech instantly and resume listening.
- Streaming recognition, reasoning and speech output where supported.
- Configurable response style, verbosity and proactivity.
- Personality and expression without sacrificing clarity or speed.

## Interaction Runtime — Dictate / Edit / Ask / Act

- First-class system-wide interaction runtime rather than separate dictation, editing and agent modes.
- `Dictate`: literal or cleaned speech inserted into the current target.
- `Edit`: transform selected/recent text naturally.
- `Ask`: answer about the current screen, selection, cursor target or app context.
- `Act`: operate the current app/device/task through the best available capability.
- Focused app/window awareness.
- Focused control/text-field awareness.
- Selected-text context.
- Cursor target context.
- Accessibility-tree context.
- Screenshot/visual context when needed.
- Clipboard/input-method fallback where native insertion is unavailable.
- Point-and-talk requests such as “what is this?”, “reply to him” and “fix this button”.
- Undo surface connected to the Action Ledger when a real compensating action exists.

## Multi-device voice arbitration

- Sunday, desktop and physical OSCAR can all listen without all responding at once.
- Exactly one surface normally owns a voice turn.
- Arbitration inputs can include wake confidence, microphone signal quality, proximity, current active device, room/presence, explicit device priority and available interaction context.
- Explicit handoff between surfaces.
- Failover if the selected surface becomes unavailable.
- Shared turn/task state after arbitration so other surfaces remain synchronized.

## World Model / digital twin

- Live graph of people, places, devices, apps, projects, objects, tasks, Workers and Protocols.
- Relationships between those entities.
- Current state distinct from historical memory.
- Freshness, confidence and provenance metadata.
- Stale state becomes `stale/unknown` rather than being presented as current truth.
- Current observations can be reconciled with structured OSCAR state and live authoritative sources.
- World Model provides one coherent situation to Jev, Personal Policy and the Executive Planner.

## Perception Fabric

- Normalize current evidence from screens, accessibility trees, cursor/selection, cameras, microphones/audio events, apps, devices, phone context, location, sensors and Worker/Protocol state.
- Current evidence is separate from durable memory/retention.
- Fuse multiple signals where useful.
- Camera + sensor + screen/device-state correlation for workbench/spatial reasoning.
- Source/freshness/confidence metadata attached to observations.

## Universal live context/search

- Federated current-source retrieval rather than requiring Jev to know every connector directly.
- Search connected files/drives, mail, messages, notes/knowledge systems, browser state, GitHub, calendar, social accounts, Sunday, desktop nodes, Edge telemetry and Worker/Protocol state.
- Preserve source provenance.
- Prefer authoritative current state over stale recalled memory.
- Retrieve the smallest useful context rather than dumping all sources into every model call.

## Canonical entity / relationship graph

- Resolve one person across phone contact, email identity, messaging account and remembered relationship.
- Resolve organizations/companies/projects/accounts consistently.
- Track device/account ownership and relationship metadata where permitted.
- Link communication history, calendar context and project context to canonical entities.
- Avoid duplicate “John”/“same device” identities when evidence can resolve them.

## Personal Policy and preferences

- Open-ended preferences rather than a fixed list of generic settings.
- Create/edit/remove preferences through ordinary voice or chat.
- Seed a small number of useful preferences during first-run setup.
- Scope policy to people, apps, projects, Workers, devices, calls, meetings, locations, Sentry modes, times or arbitrary user-defined context.
- Distinguish memory, preference/policy, permission, routine and Protocol.
- Explicit policy overrides inferred preference suggestions.
- More-specific applicable policy normally overrides broader policy.
- Safety/legal/platform constraints and permissions remain authoritative.
- Explain which policy affected a decision and why.
- Inspectable/versionable durable policy with provenance.
- Inferred patterns can be proposed as preferences rather than silently gaining authority.
- Natural-language edits update existing rules instead of accumulating contradictory prompt fragments.

See [PERSONAL-POLICY.md](PERSONAL-POLICY.md).

## Communication

- OSCAR as the unified communication layer rather than separate call/meeting/dictation bots.
- Ordinary phone calls subject to platform support and permissions.
- WhatsApp calls/messages where technically available.
- Telegram calls/messages where technically available.
- Other phone communication apps through the strongest legitimate integration path.
- Zoom/Google Meet/Teams/Discord-style meeting participation where supported.
- In-person meeting capture through authorized microphones/devices.
- AI call answering on the user's behalf under explicit Personal Policy.
- Rules such as answer after N rings, exclude specific people, or adapt based on calendar/current context.
- Context-aware call handling using contacts, schedule, agenda, current task, relationship and user rules.
- Take messages, determine urgency, schedule callbacks and summarize calls.
- Meeting transcription, speaker labels where reliable, notes, decisions, action items and follow-ups.
- Meeting context linked back to people/projects/tasks through LRA.
- System-wide dictation comparable to dedicated dictation products, not limited to OSCAR's own text box.
- Literal/cleaned/rewrite/command dictation modes.
- Voice-note handling.
- App messaging: read/draft/send/reply subject to permissions.
- Native OS/official API first, then official connector/plugin, then device automation/computer-use fallback.
- Explicitly report unsupported capability instead of pretending an app exposes it.
- Raw audio/transcript retention controls.
- Permission/policy checks before speaking, publishing, sending or revealing private schedule context.
- Concrete capability mapping for Android cellular calls, third-party app calls, media/audio capture and VoIP gateway fallbacks instead of assuming uniform call control.

See [COMMUNICATION.md](COMMUNICATION.md).

## Universal Channel Gateway

- Normalize supported inbound/outbound communication across cellular/SMS where possible, WhatsApp, Telegram, Signal, Discord, Slack/Teams-like channels, email, social DMs/replies and future adapters.
- Common event envelope for channel/account/thread, canonical participant IDs, sender/recipients, direction, type, text/transcript/media refs, timestamps and source IDs.
- Per-channel capability advertisement rather than assumed feature parity.
- Native/official API path preferred over device/browser automation.
- Channel events linked to canonical entities, World Model, LRA and Personal Policy where appropriate.
- Unsupported actions remain explicitly unsupported rather than silently emulated.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Action Ledger + universal Undo

- Structured record for consequential actions.
- Initiating user/task/Protocol/Worker.
- Intent and target/resource.
- Tool/device/capability used.
- Permission + Personal Policy decision.
- Before-state reference where available.
- Resulting-state reference where available.
- Execution status.
- Verification status/method/evidence.
- Limitations/untested surfaces.
- Reversible/irreversible flag.
- Compensating/undo action when the capability supports one.
- Correlation ID + timestamp.
- Natural queries: “what did you change?”, “why did you do that?”, “did you actually verify it?”, “undo that”.
- Never claim reversibility for an irreversible action.

## Reflexes and local commands

- Local wake-word detection.
- Voice activity detection.
- Immediate `mute`, `stop`, `cancel`, `listen`, `sentry`, `stand down`-style commands.
- Simple local device controls without an LLM.
- Hardware emergency stop path.
- Active-task references such as “that”, “it”, and “stop this” resolved locally when unambiguous.

## Voice Match

- Speaker-profile enrollment during setup.
- Multiple enrollment phrases, distances, tones and noise conditions.
- Confidence-based speaker verification.
- Voice Match integrated with authorization policy.
- Different policies for owner, recognized user, guest and unknown speaker.
- Voice biometrics never treated as sufficient security for critical actions.

## Voice output

- Natural low-latency TTS.
- Stable OSCAR voice identity.
- Chunked/streamed speech.
- Immediate stop on barge-in.
- Audio ducking and acknowledgement cues.
- Phone-native speech path for Sunday where useful.
- Provider abstraction so TTS/STT engines can be swapped without rewriting OSCAR.

## Sentry Mode

- Always-on low-power awareness.
- Local wake-word/audio event processing rather than continuous cloud microphone streaming.
- Presence/motion monitoring.
- Environmental sensors: temperature, light, air/smoke/gas/water where hardware exists.
- Device/power-state monitoring.
- Workbench safety/anomaly events.
- Known/unknown voice classification when enabled.
- Event fusion across multiple signals.
- Importance, urgency, confidence and interruptibility scoring.
- Silent logging, notification, spoken alert or urgent interruption depending on policy.
- Modes: Passive, Aware, Guard, Away and Sleep.
- Natural transitions such as “I’m heading out” → Away behavior when configured.

## Predictive intelligence

- Forecast schedule conflicts before they occur.
- Estimate deadline/task risk from current progress.
- Detect abnormal device/sensor trends before obvious failure where evidence supports it.
- Prepare diagnostics/context when a build or service appears likely to fail.
- Prefetch relevant context for likely upcoming tasks/transitions.
- Predictions remain evidence, not authority; Personal Policy and permissions still govern action.

## ChatGPT integration

- ChatGPT can invoke OSCAR through Latch tools.
- OSCAR can wake/invoke ChatGPT through a Latch abstraction.
- Complex personal reasoning can be delegated to ChatGPT.
- Long-running Work-style investigations can return results to OSCAR.
- ChatGPT retains no special hardware-safety authority.
- Wake/trigger transport is replaceable when product capabilities evolve.
- ChatGPT/agent success reports enter as reported evidence until verified.

## SwitchRoute integration

- Autonomous cloud-model access without the laptop.
- Route by task, latency, capability and cost.
- Provider/model fallback.
- Small/fast model paths for classification and extraction.
- Stronger reasoning models only when needed.
- Speech-provider routing may use the same abstraction where useful.
- Model inference is never silently relabeled as verified fact.

## Intent and epistemic routing — Jev

- Fast typed intent recognition.
- Detect when OSCAR already has enough context.
- Query the World Model for current state.
- Decide when memory retrieval is necessary.
- Decide when a live source/tool should be inspected.
- Decide when to use ChatGPT, SwitchRoute or a specialist Worker.
- Decide when deterministic execution is enough.
- Decide whether a blocked Worker can be repaired/rerouted safely.
- Ask the user only when ambiguity materially blocks safe/correct execution.
- Explicit `known / world / recall / verify / reason / reported / delegate / ask` states.
- Avoid guessing personal/project context that can be retrieved.
- Avoid escalating recoverable Worker/tool errors unnecessarily.

## Epistemic Integrity

- Distinguish intention, execution, reported success, observed result and verified objective completion.
- Task states: planned, executing, result_received, verifying, verified, partially_verified, failed, blocked, cancelled, unknown.
- Evidence states: KNOWN, INFERRED, RECALLED, REPORTED, VERIFIED, UNKNOWN.
- Tool/Worker/model success is testimony/evidence, not automatically truth.
- Unqualified `Done`/`Fixed` requires verification where technically possible.
- Partial verification is reported as partial.
- Unknown is preferable to guessing.
- User confidence does not alter factual state; OSCAR can disagree when evidence/constraints require it.
- Corrections are explicit and propagated to affected state/docs/tasks.
- UI/avatar state reflects real execution/verification state rather than fake success.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## Memory and continuity — LRA + Supermemory

- LRA persistent single-conversation/history architecture.
- Supermemory semantic/profile-style backend.
- Active live context preserved separately from long-term recall.
- Episodic conversation/task history.
- Cross-device conversation/task continuity.
- Project/context retrieval.
- Device/environment context.
- User profile/relationship memory.
- Personal Policy stored as an authoritative behavior layer distinct from inferred memory.
- Procedural memory.
- Protocol/Worker state.
- Source/provenance metadata where possible.
- Confidence-aware use of recalled information.
- Retrieval ranking using relevance, recency, importance, scope, source authority and staleness.
- Searchable history/timeline instead of mandatory manual chat management.
- User controls to inspect, correct and forget memory.
- Current World Model state remains distinct from historical/semantic memory.
- Recalled memory remains explicitly recalled until verified against current authority where necessary.

## Learning and procedural memory

- Capture verified successful novel execution paths.
- Distill useful procedures from noisy exploratory runs.
- Parameterize reusable steps.
- Store required capabilities/preconditions.
- Store verification strategy.
- Reuse known procedures on similar tasks.
- Skip unnecessary discovery on repeated work.
- Convert stable paths toward deterministic execution where possible.
- Measure improvements in latency, cost and reliability over time.
- Version learned procedures.
- Roll back worse versions.
- Never let learned behavior self-grant permissions.
- Teach-by-demonstration: “watch me do this once” → observe authorized actions → infer intent/steps → clarify ambiguity → verify → create Skill candidate.

## Sunday — OSCAR on phone

- OSCAR avatar and voice on Android/mobile.
- Notifications and proactive alerts.
- Calls/messages subject to permissions.
- AI call answering when platform support and Personal Policy permit it.
- WhatsApp/Telegram/other app actions where supported.
- General phone-app actions/deep links where supported.
- Mobile meeting transcription/notes.
- System-wide dictation/input assistance.
- Camera and microphone access when authorized.
- Phone sensor/context access.
- On-device speech recognition where appropriate.
- Biometric/PIN confirmation for sensitive actions.
- Handoff between phone, desk, ChatGPT and desktop.
- Mobile Sentry participation.
- Rich lock-screen/notification actions where platform permits.

## OSCAR Desktop — Windows and macOS

- Native/lightweight Windows app.
- macOS app using the same surface/capability contracts with platform-specific adapters.
- Voice + text interaction.
- Push/hold-to-talk.
- Full `Dictate / Edit / Ask / Act` Interaction Runtime.
- System-wide dictation.
- Meeting transcription/notes where supported.
- Avatar/presence state.
- Screen context.
- Cursor/focus context.
- Selected-text context.
- Active-window/app context.
- Accessibility-tree + screenshot context.
- Point-and-talk interaction.
- Notifications and task progress.
- Approval/permission surfaces.
- Machine-Worker capability/health status.
- Sunday handoff.
- Searchable timeline/history rather than a giant chat sidebar.

## Machine Worker node

When online, a computer dynamically advertises capabilities to OSCAR.

Planned capabilities include:

- Codex;
- computer use;
- terminal / PowerShell / shell;
- browser;
- IDEs/editors;
- Git/GitHub workflows;
- Python/scripts;
- FFmpeg/media tooling;
- Blender or other specialist desktop apps;
- filesystem;
- optional local models;
- GPU-backed support jobs.

The PC is never required for OSCAR's basic availability.

## Delegated Workers / sub-agents

Workers are Grok-Bot-style delegated teammates owned by OSCAR, but they use the user's actual device/service mesh rather than requiring a separate cloud computer.

- Create Workers naturally by voice or chat.
- Temporary Workers for one-off research/tasks.
- Task Workers that live until a completion condition is met.
- Persistent Workers for continuing responsibilities.
- Worker goal/context/permissions/capabilities/verification/escalation state.
- Workers can use Sunday, desktop nodes, APIs/plugins, ChatGPT/SwitchRoute, Kinetable and OSCAR Edge.
- Workers can use Codex or other specialist agents rather than acting as generic LLM clones.
- Parallel Workers can collaborate, wait on dependencies and hand work off.
- Workers can use shared learned Skills.
- Protocols can create/stop/sleep Workers.
- Jev handles safe self-repair/rerouting before user escalation.
- Bounded retries and explicit blockers.
- Worker state survives restart when a responsibility is long-running.
- Create/pause/resume/edit/delete through UI or natural language.
- Lightweight Worker UI rather than a dense agent dashboard.
- Workers never self-grant permissions or bypass Personal Policy.
- Worker success remains REPORTED until objective verification.

See [WORKERS.md](WORKERS.md).

## Executive Planner

- One global executive above Workers/Protocols rather than independent agent silos.
- Consider priority, deadline, dependencies, resource/device availability, user interruptibility, risk and cost.
- Schedule and parallelize work.
- Pause/pre-empt lower-priority work when justified.
- Resolve conflicts when multiple Workers need the same device/tool.
- Reroute work when a device/specialist disappears.
- Defer work until prerequisites become available.
- Decide when the user actually needs to be interrupted.
- Never bypass Jev, Personal Policy or permissions.

## Durable Execution Runtime

- Durable task/objective IDs and lifecycle state.
- Persisted checkpoints/current step for long-running work.
- Executor leases/ownership.
- Heartbeats/last-progress tracking.
- Retry budget and bounded backoff.
- Cancellation state.
- Deadline/expiry.
- Required capabilities and current execution surface.
- Artifact/result references.
- Verification state.
- Blocker/escalation state.
- Lease expiry/reclaim of abandoned work.
- Zombie/stuck-work detection.
- Restart/resume after process/device loss.
- Idempotency/deduplication where needed.
- Durable queues/event delivery where justified.
- Never leave a task indefinitely `Working` because its executor vanished.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Social-media management

- Persistent Social Worker when the user wants one.
- Monitor mentions/replies.
- Research relevant developments.
- Draft posts.
- Prepare media/assets.
- Schedule content where supported.
- Publish content within configured autonomy.
- Answer permitted routine messages/comments.
- Coordinate release announcements with project state.
- Summarize community feedback/performance.
- Use Channel/API/plugin first; browser/desktop/Sunday fallback where legitimate and available.
- Personal Policy can differentiate ordinary posts, major announcements, controversial topics and account/security actions.

## Software-task orchestration

- Delegate repository work to Codex rather than reproducing a coding agent poorly.
- Preserve specialist project/workspace context where possible.
- Route design tasks through relevant plugins such as Impeccable when available.
- Use computer use for GUI operation and visual verification.
- Run tests/commands through the machine Worker.
- Observe the result and feed failures back into the specialist agent.
- Continue until an objective completion condition is met or the user is needed.
- Prefer the best available software/tool for a task.
- Re-route on Worker/tool failure.
- Verify independently where practical.
- Preserve reported-vs-verified distinction throughout orchestration.

## Capability Catalog + Dynamic Tool Search

- Dynamic node/app/plugin/Skill/channel capability advertisement.
- Lightweight searchable manifests.
- Availability state.
- Task suitability metadata.
- Latency/cost metadata where useful.
- Permission/risk requirements.
- Reliability/history metadata.
- Project/workspace context hints.
- Communication/app capability metadata.
- Reversal/undo capability metadata where applicable.
- Provider/plugin/version metadata.
- Search/rank by suitability + availability + policy + reliability + latency/cost.
- Load detailed contracts only for relevant finalists.
- Ability for capabilities to disappear/reappear without killing OSCAR.
- Avoid a mega-prompt containing every tool definition.

## Artifact / Result Model

- First-class records for documents, spreadsheets, slides, images/video/audio, code patches/commits/PRs, research reports, meeting notes, deployments, firmware builds, datasets/models/evaluations and other durable outputs.
- Artifact ID/kind/name.
- Owner task/Worker/Protocol.
- Producer capability.
- Location/reference.
- Version/hash where useful.
- Source/provenance.
- Verification status.
- Permissions/access scope.
- Project/entity/task relationships.
- `supersedes` / `derived-from` links.
- Workers pass artifact references rather than repeatedly copying opaque blobs through prompts.

## Edge / physical world

- ESP32 network gateway.
- RP2040/Pico deterministic GPIO controller.
- Buttons and physical controls.
- Displays/status surfaces.
- LEDs and expressive indicators.
- Sensors.
- Relays.
- Servos/motors/actuators.
- Cameras via suitable connected nodes.
- Workbench telemetry.
- Hardware-health monitoring.
- OTA/configuration management.
- Future smart-home/environment integrations.

## Kinetable integration

- Treat Kinetable as OSCAR's specialist hardware workshop.
- Route hardware design/visual wiring tasks into Kinetable.
- Use actual user component inventory/context.
- Simulation support.
- Firmware generation/programming path.
- Provision ESP32/Pico/new devices into OSCAR/Latch Edge.
- Generate capability metadata during provisioning.
- Avoid duplicating Kinetable inside OSCAR.

## Engineering/workbench capabilities

Long-term target capabilities include:

- identify connected components and sensors;
- inspect telemetry while the user works;
- correlate camera view with electronic state;
- explain wiring/problems using actual device data;
- route circuit/simulation work to Kinetable;
- drive visual-debugging or CAD/workbench tools;
- invoke specialist software rather than simulating it in chat;
- route CAD, 3D, numerical simulation, diagnostics, reconstruction and optimization to appropriate external/specialist tools;
- maintain personal component inventory/context;
- run safe physical Protocols after authorization.

## Protocols and routines

- Named Protocols such as `leaving_home` or `release-watch`.
- Recurring routines.
- Time-triggered routines.
- Event-triggered routines.
- Multi-step stateful procedures.
- Wait states.
- Conditional branching.
- Background observation.
- Delegation to Workers/tools.
- Worker creation/termination as Protocol steps.
- Cancellation and pause/resume.
- Preconditions and safety checks.
- Idempotency where appropriate.
- Recovery/retry policy.
- Escalation rules.
- Completion conditions.
- Human approval gates for consequential steps.
- Long-running responsibility over days/weeks/months when needed.
- Durable Execution Runtime used where restart/recovery matters.

## Skills and plugins

- Support portable `SKILL.md`-style capability descriptions/contracts.
- Plugin/connector discovery.
- Tool capability metadata.
- OSCAR can identify when a specialist Skill/plugin is better suited than its general path.
- OSCAR may create a reusable Skill candidate from a verified novel workflow.
- OSCAR may propose/create/refine Skills after repeated workflows.
- Skills define required capabilities, inputs, preconditions, procedure, verification, risk and recovery.
- Generated Skills remain permission-scoped, inspectable and versioned.
- Plugins/connectors become entries in the Capability Catalog and can participate in Skills/Protocols/Workers.

## Self-created automation

- Create Skill candidates from verified successful executions.
- Create Worker definitions from explicit delegation or persistent objectives.
- Create routine candidates from repeated recurring behavior.
- Create Protocol candidates from persistent objective patterns.
- Preserve provenance to the executions that taught the workflow.
- Never grant new authority implicitly.
- Require explicit approval when generated automation would broaden permissions or risk.

## Learned Automation Evaluation Pipeline

- One successful run creates a candidate, not automatically a trusted/default automation.
- Normalize/parameterize candidate steps.
- Replay/evaluate representative cases where possible.
- Verify expected output and safety properties.
- Compare new version with current trusted version.
- Review permission/Personal Policy requirements.
- Promote, reject or keep experimental.
- Preserve evaluation cases/results, assumptions, provenance, limitations and rollback target.
- Untestable candidates remain experimental/partially verified.
- Roll back versions that regress reliability/safety.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Research and analysis

- Search/retrieve information through approved sources.
- Compare multiple sources.
- Continue research asynchronously through Workers.
- Notify only on meaningful findings.
- Use structured tools/data rather than hallucinating unavailable state.
- Preserve source/provenance and distinguish inference from verified fact.

## Proactivity

- Report important changes without being prompted.
- Suggest an action when confidence/value are high enough.
- Continue delegated work after the user leaves.
- Notify when a task/Worker reaches a meaningful verified result or blocker.
- Avoid narrating routine background activity.
- Learn preferred interruption patterns without overriding user controls.
- Apply explicit Personal Policy before inferred preferences.
- Use predictive signals to prepare quietly without turning uncertain forecasts into authority.

## Device and environment awareness

- Node-online/node-offline events.
- Capability discovery.
- Presence state.
- Device power/health state.
- Environmental state.
- User-configurable normal baselines.
- Anomaly detection from rules first; AI escalation when useful.
- Feed current state into the World Model rather than leaving it as disconnected telemetry.

## Self-maintenance / diagnostics

- Detect expired authentication.
- Detect broken/missing connectors/channels.
- Detect stale/disappeared capabilities.
- Detect Edge-node disconnects.
- Detect provider/speech latency degradation.
- Detect storage/local-state health problems.
- Detect update failures.
- Detect repeated Worker/Protocol failures.
- Detect stuck/zombie durable tasks.
- Repair or roll back safe failures automatically when confidence/permissions allow.
- Ask the user only for minimum intervention when self-repair is not safe/possible.

## Avatar and presence

- OSCAR's blue-shell / yellow-face avatar as a primary UI primitive.
- Yellow face behaves like a weighted joystick/puck inside the blue body.
- Directionality indicates attention/focus.
- Expression states for idle, listening, thinking, speaking, success, confusion, alert, sentry, sleeping, muted and error.
- Runtime states include Working, Verifying, Waiting, Blocked, Done and Failed.
- Success animation/state only after verified completion where verification is applicable.
- Small-size/icon variants preserve silhouette/readability.
- “Serious” states become calmer/focused rather than cartoonishly expressive.
- Motion grammar tied to actual system state.

## First-run commissioning

- Identity and interaction preferences.
- Small high-value Personal Policy setup with explanation that any preference can later be changed through normal conversation.
- Calls/messaging autonomy defaults.
- Meeting transcription/retention defaults.
- Worker autonomy defaults.
- Voice Match enrollment.
- Wake/reflex command test.
- Device discovery.
- Accounts/services/channels.
- Permission matrix.
- Sentry configuration.
- Environment/room/workbench setup.
- Sunday pairing.
- Desktop/machine-Worker pairing.
- Latch/ChatGPT/SwitchRoute setup.
- Kinetable connection where desired.
- Routines/Protocol preferences.
- End-to-end calibration and verified health check.

## Permissions and security

- Capability-scoped permissions.
- Per-action authorization level.
- Voice Match as one signal, not sole high-risk auth.
- Strong confirmation through Sunday biometric/PIN or explicit approval for critical actions.
- Universal local emergency-stop capability.
- Audit log / Action Ledger for consequential actions.
- Device-scoped/rotatable credentials.
- Outbound edge connections rather than exposed home endpoints.
- Minimal cloud audio/video exposure.
- Data retention controls.
- Generated Skills/Workers/Protocols cannot self-elevate permissions.
- Communication actions remain attributable.
- Personal Policy may restrict authority but cannot create it.

## Reliability

- PC-independent operation.
- Local safety if cloud fails.
- Graceful capability loss when a node disappears.
- Retries with bounded backoff.
- Idempotent commands where possible.
- Action/result correlation IDs.
- Watchdogs for edge components.
- Health/status reporting.
- Recovery from partial task completion.
- Explicit blocker reporting rather than silent failure.
- Skill/Protocol rollback when learned changes reduce reliability.
- Workers repair/reroute safe recoverable failures before escalating, without unbounded retry loops.
- World Model state carries freshness so stale evidence is not mistaken for current truth.
- Durable tasks use checkpoint/lease/heartbeat/reclaim semantics where needed.
- Reported success cannot silently become verified completion.
- Partial/unknown/failed states are preserved and surfaced truthfully.

## Post-alpha expansion

- Optional health/wearable context with strict permission/privacy boundaries.
- Smart-home capability contracts.
- Robotics/camera/room-infrastructure contracts.
- Future vehicle/drone integration where safe and legally appropriate.
- Optional cloud Worker node as an advertised capability rather than a foundational dependency.
- These domains plug into existing Capability Catalog, World Model, Personal Policy, Durable Execution Runtime, Artifact Model, permissions and Action Ledger rather than creating parallel architectures.

See:

- [JARVIS-GAP-REVIEW.md](JARVIS-GAP-REVIEW.md)
- [COMPETITIVE-BENCHMARK.md](COMPETITIVE-BENCHMARK.md)
- [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md)
- [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md)
