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

## Personal Policy and preferences

- Open-ended preferences rather than a fixed list of generic settings.
- Create/edit/remove preferences through ordinary voice or chat.
- Seed a small number of useful preferences during first-run setup.
- Scope policy to people, apps, projects, workers, devices, calls, meetings, locations, Sentry modes, times or arbitrary user-defined context.
- Distinguish memory, preference/policy, permission, routine and protocol.
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

See [COMMUNICATION.md](COMMUNICATION.md).

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

## ChatGPT integration

- ChatGPT can invoke OSCAR through Latch tools.
- OSCAR can wake/invoke ChatGPT through a Latch abstraction.
- Complex personal reasoning can be delegated to ChatGPT.
- Long-running Work-style investigations can return results to OSCAR.
- ChatGPT retains no special hardware-safety authority.
- Wake/trigger transport is replaceable when product capabilities evolve.

## SwitchRoute integration

- Autonomous cloud-model access without the laptop.
- Route by task, latency, capability and cost.
- Provider/model fallback.
- Small/fast model paths for classification and extraction.
- Stronger reasoning models only when needed.
- Speech-provider routing may use the same abstraction where useful.

## Intent and epistemic routing — Jev

- Fast typed intent recognition.
- Detect when OSCAR already has enough context.
- Decide when memory retrieval is necessary.
- Decide when a live source/tool should be inspected.
- Decide when to use ChatGPT, SwitchRoute or a specialist worker.
- Decide when deterministic execution is enough.
- Decide whether a blocked Worker can be repaired/rerouted safely.
- Ask the user only when ambiguity materially blocks safe/correct execution.
- Explicit `known / recall / verify / reason / delegate / ask` states.
- Avoid guessing personal/project context that can be retrieved.
- Avoid escalating recoverable worker/tool errors unnecessarily.

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

## Learning and procedural memory

- Capture successful novel execution paths.
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
- System-wide dictation.
- Meeting transcription/notes where supported.
- Avatar/presence state.
- Screen context.
- Cursor/focus context.
- Selected-text context.
- Active-window/app context.
- Notifications and task progress.
- Approval/permission surfaces.
- Machine-worker capability/health status.
- Sunday handoff.
- Searchable timeline/history rather than a giant chat sidebar.

## Machine Worker node

When online, a computer dynamically advertises capabilities to OSCAR.

Planned capabilities include:

- Codex
- computer use
- Antigravity
- terminal / PowerShell / shell
- browser
- IDEs/editors
- Git/GitHub workflows
- Python/scripts
- FFmpeg/media tooling
- Blender or other specialist desktop apps
- filesystem
- optional local models
- GPU-backed support jobs

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

See [WORKERS.md](WORKERS.md).

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
- Use API/plugin first; browser/desktop/Sunday fallback where legitimate and available.
- Personal Policy can differentiate ordinary posts, major announcements, controversial topics and account/security actions.

## Software-task orchestration

- Delegate repository work to Codex rather than reproducing a coding agent poorly.
- Preserve specialist project/workspace context where possible.
- Route design tasks through relevant plugins such as Impeccable when available.
- Use computer use for GUI operation and visual verification.
- Run tests/commands through the machine worker.
- Observe the result and feed failures back into the specialist agent.
- Continue until an objective completion condition is met or the user is needed.
- Prefer the best available software/tool for a task.
- Re-route on worker/tool failure.
- Verify independently where practical.

## Capability registry

- Dynamic node/app/plugin capability advertisement.
- Availability state.
- Task suitability metadata.
- Latency/cost metadata where useful.
- Permission requirements.
- Reliability/history metadata.
- Project/workspace context hints.
- Communication/app capability metadata.
- Ability for capabilities to disappear/reappear without killing OSCAR.

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

- identify connected components and sensors
- inspect telemetry while the user works
- correlate camera view with electronic state
- explain wiring/problems using actual device data
- route circuit/simulation work to Kinetable
- drive visual-debugging or CAD/workbench tools
- invoke specialist software rather than simulating it in chat
- maintain personal component inventory/context
- run safe physical protocols after authorization

## Protocols and routines

- Named protocols such as `leaving_home` or `release-watch`.
- Recurring routines.
- Time-triggered routines.
- Event-triggered routines.
- Multi-step stateful procedures.
- Wait states.
- Conditional branching.
- Background observation.
- Delegation to Workers/tools.
- Worker creation/termination as protocol steps.
- Cancellation and pause/resume.
- Preconditions and safety checks.
- Idempotency where appropriate.
- Recovery/retry policy.
- Escalation rules.
- Completion conditions.
- Human approval gates for consequential steps.
- Long-running responsibility over days/weeks/months when needed.

## Skills and plugins

- Support portable `SKILL.md`-style capability descriptions/contracts.
- Plugin/connector discovery.
- Tool capability metadata.
- OSCAR can identify when a specialist skill/plugin is better suited than its general path.
- OSCAR may create a reusable skill from a successful novel workflow.
- OSCAR may propose/create/refine skills after repeated workflows.
- Skills define required capabilities, inputs, preconditions, procedure, verification, risk and recovery.
- Generated skills remain permission-scoped, inspectable and versioned.
- Plugins/connectors become entries in the capability registry and can participate in Skills/Protocols/Workers.

## Self-created automation

- Create skill candidates from successful executions.
- Create Worker definitions from explicit delegation or persistent objectives.
- Create routine candidates from repeated recurring behavior.
- Create protocol candidates from persistent objective patterns.
- Validate generated definitions before activation.
- Preserve provenance to the executions that taught the workflow.
- Never grant new authority implicitly.
- Require explicit approval when generated automation would broaden permissions or risk.

## Research and analysis

- Search/retrieve information through approved sources.
- Compare multiple sources.
- Continue research asynchronously through Workers.
- Notify only on meaningful findings.
- Use structured tools/data rather than hallucinating unavailable state.

## Proactivity

- Report important changes without being prompted.
- Suggest an action when confidence and value are high enough.
- Continue delegated work after the user leaves.
- Notify when a task/Worker reaches a meaningful result or blocker.
- Avoid narrating routine background activity.
- Learn preferred interruption patterns over time without overriding user controls.
- Apply explicit Personal Policy before inferred preferences.

## Device and environment awareness

- Node-online/node-offline events.
- Capability discovery.
- Presence state.
- Device power/health state.
- Environmental state.
- User-configurable normal baselines.
- Anomaly detection from rules first; AI escalation when useful.

## Avatar and presence

- OSCAR's blue-shell / yellow-face avatar as a primary UI primitive.
- Yellow face behaves like a weighted joystick/puck inside the blue body.
- Directionality indicates attention/focus.
- Expression states for idle, listening, thinking, speaking, success, confusion, alert, sentry, sleeping, muted and error.
- Small-size/icon variants preserve silhouette and readability.
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
- Accounts/services.
- Permission matrix.
- Sentry configuration.
- Environment/room/workbench setup.
- Sunday pairing.
- Desktop/machine-worker pairing.
- Latch/ChatGPT/SwitchRoute setup.
- Kinetable connection where desired.
- Routines/protocol preferences.
- End-to-end calibration and health check.

## Permissions and security

- Capability-scoped permissions.
- Per-action authorization level.
- Voice Match as one signal, not sole high-risk auth.
- Strong confirmation through Sunday biometric/PIN or explicit approval for critical actions.
- Universal local emergency-stop capability.
- Audit log for consequential actions.
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
- Skill/protocol rollback when learned changes reduce reliability.
- Workers repair/reroute safe recoverable failures before escalating, without unbounded retry loops.
