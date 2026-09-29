# Roadmap

This roadmap is slice-based. Each slice should leave OSCAR in a coherent, testable state and update the README plus affected docs in the same change.

All implementation slices are also governed by `ENGINEERING.md`: keep scope coherent, boundaries explicit, failure behavior intentional and code simple enough to evolve safely.

The JARVIS/VoiceOS benchmark in `docs/JARVIS-GAP-REVIEW.md` is also part of roadmap planning. The immediate goal is not to add random integrations; it is to make existing capabilities behave like one coherent ambient intelligence.

## Status legend

- ✅ Complete
- 🚧 In progress
- ⏭️ Next
- ◻️ Planned

## Slice 00 — Repository foundation ✅

**Goal:** establish the product, design, engineering and agent-development contract before implementation.

Deliverables:

- canonical OSCAR product definition
- architecture plan
- comprehensive feature inventory
- LRA/Supermemory/Jev memory plan
- Personal Policy/preference model
- communication layer plan for calls, meetings, messaging and dictation
- delegated Worker/sub-agent model
- orchestration/learning/skills/protocol plan
- JARVIS/VoiceOS gap benchmark covering World Model, Perception Fabric, Executive Planner, Action Ledger/Undo and Interaction Runtime
- Sunday/desktop/edge surface plan
- voice/Sentry design
- onboarding/Voice Match plan
- avatar interaction language
- **Quietly Alive** design system in `DESIGN.md`
- qualitative design/taste rules in `TASTE.md`
- canonical engineering/system-design quality bar in `ENGINEERING.md`
- Sunday mobile visual direction
- canonical `AGENTS.md` plus Claude, Gemini, Copilot and Cursor adapters
- portable `SKILL.md` workflows for OSCAR UI and slice delivery
- coding-agent context documentation
- security model
- brand assets under `assets/brand/`
- repository support files and GitHub templates/checks
- README status table and documentation links

Exit condition: repository clearly defines what OSCAR is, what it is not, how it should look/feel, how it should be engineered, how coding agents should work in it, and the planned implementation order.

## Slice 01 — Edge runtime skeleton ⏭️

**Goal:** create the always-on local runtime boundary.

Deliverables:

- ESP32 gateway project structure
- Pico/RP2040 controller project structure
- explicit event/message schema between them
- device identity and version reporting
- health/status heartbeat
- basic command/response path
- local watchdog and safe-default behavior
- host-side simulator/tests where practical

Exit condition: ESP32 and Pico can boot, identify themselves, exchange typed events/commands and report health without cloud intelligence.

## Slice 02 — Reflex engine ◻️

**Goal:** make immediate deterministic behavior real.

Deliverables:

- local intent/reflex state machine
- mute/stop/cancel primitives
- simple local device commands
- active-task cancellation IDs
- emergency-stop path
- latency instrumentation
- safety validation on Pico

Exit condition: reflex actions work without Internet/model calls and meet latency targets.

## Slice 03 — Latch Edge + capability registry ◻️

**Goal:** securely connect OSCAR Edge to Latch without exposing the local network.

Deliverables:

- persistent outbound secure session
- device pairing/identity
- scoped credentials
- capability advertisement
- event correlation IDs
- reconnect/backoff
- remote command/result transport
- audit metadata

Exit condition: Latch can discover the edge node's capabilities and call safe test tools end to end.

## Slice 04 — Voice core + multi-device arbitration ◻️

**Goal:** establish low-latency natural voice interaction that behaves like one assistant across multiple listening surfaces.

Deliverables:

- microphone/audio pipeline
- local wake word + VAD
- streaming STT abstraction
- TTS abstraction
- streaming/chunked playback
- barge-in
- echo cancellation strategy
- first-audio/command latency metrics
- wake/listen event identity across devices
- multi-device voice arbitration using confidence, proximity, active-device context and explicit priority
- one-owner-per-turn rule with handoff/failover

Exit condition: user can wake OSCAR, speak a request, receive a spoken reply, interrupt it naturally, and avoid multiple Sunday/desktop/Edge surfaces replying to the same utterance.

## Slice 05 — OSCAR core router / Jev + policy + Action Ledger foundation ◻️

**Goal:** create the decision layer that chooses the right execution, knowledge and policy path while making consequential actions attributable and reversible where possible.

Deliverables:

- typed intent model
- task/context state
- Personal Policy evaluation hook
- permission/policy hooks
- capability selection
- deterministic vs tool vs model vs Worker routing
- Jev integration for intent + epistemic decisions
- explicit `known / recall / verify / reason / delegate / ask` states
- safe Worker repair/reroute decision path
- Action Ledger event model for consequential actions
- before/after/verification metadata where available
- compensating/undo action contract where a capability can support one
- latency instrumentation for routing

Exit condition: representative requests route correctly without unnecessarily invoking heavy models, guessing missing context or bypassing explicit user policy; consequential actions are attributable and can expose a real undo path when one exists.

## Slice 06 — Cloud brains ◻️

**Goal:** give OSCAR autonomous reasoning without depending on the laptop.

Deliverables:

- SwitchRoute integration
- route/fallback policy
- ChatGPT through Latch
- OSCAR → ChatGPT wake abstraction
- ChatGPT → OSCAR tool path
- async task callbacks
- graceful provider failure

Exit condition: OSCAR can choose ChatGPT or SwitchRoute, receive results and continue a task with the PC off.

## Slice 07 — Sunday + communication runtime ◻️

**Goal:** ship OSCAR's mobile embodiment and prove the first real communication surface.

Deliverables:

- Android app shell
- OSCAR identity/avatar
- voice + text session
- notifications
- Latch connection
- task continuity
- phone capability advertisement
- initial safe phone/app actions
- native/official call + message integration boundaries
- concrete capability study for Android cellular calls, WhatsApp/Telegram-style app calls, audio access/loopback and VoIP gateway fallbacks
- AI call-handling policy hooks where the platform permits
- mobile meeting transcription/notes boundary
- system-wide dictation/input path where practical
- biometric confirmation surface

Exit condition: a task can move between Sunday and another OSCAR surface without becoming a separate assistant/session silo, and Sunday exposes only communication capabilities that are actually supported on the device/platform.

## Slice 08 — Desktop + Interaction Runtime + machine Worker nodes ◻️

**Goal:** create native desktop presence, match the practical VoiceOS interaction baseline and turn online computers into specialist execution nodes.

Deliverables:

- Windows native/lightweight app shell
- macOS-compatible surface plan and adapter boundary
- voice/text interaction + OSCAR presence UI
- first-class `Dictate / Edit / Ask / Act` interaction runtime
- focused app/window/text-field context
- selected-text operations
- cursor target + accessibility-tree context
- screenshot/visual context
- point-and-talk flows such as “what is this?”, “reply to him”, “fix this button”
- text insertion/rewrite with clipboard/accessibility fallbacks
- user-visible undo when the Action Ledger exposes a compensating action
- system-wide dictation path
- desktop meeting transcription/notes boundary
- machine-worker pairing and dynamic capability discovery
- filesystem/terminal primitives
- Codex integration
- computer-use integration
- browser/IDE/app launching
- Antigravity/specialist adapters where feasible
- progress/result callbacks
- cancellation and disconnect recovery

Exit condition: OSCAR can understand and act on the current desktop target with VoiceOS-grade interaction friction, delegate specialist software work, observe it, verify it and survive the machine node disappearing.

## Slice 09 — Memory, live context, entity graph + Personal Policy ◻️

**Goal:** provide durable cross-device continuity, authoritative preferences and a live-source-aware context layer without a conventional chat-sidebar dependency.

Deliverables:

- LRA integration boundary
- active-context + episodic-history model
- Supermemory backend
- Jev retrieval/verification decisions
- task/project/device/procedural memory types
- Personal Policy store distinct from inferred memory
- natural-language preference create/edit/remove flow
- policy scoping, precedence and conflict resolution
- provenance/confidence metadata
- remember/forget/update flows
- context handoff between Sunday, desktop, ChatGPT, edge and Workers
- searchable history/timeline surface
- inspectable Personal Policy surface
- universal live context/search abstraction over connected authoritative sources
- source-authority and staleness rules
- canonical entity/relationship graph for people, contacts, accounts, companies, devices, projects and identities

Exit condition: OSCAR can recover historical context, query current authoritative sources, resolve identities consistently across systems and apply explicit preferences reliably without confusing inferred memory with authority.

## Slice 10 — World Model + Perception Fabric + Sentry intelligence ◻️

**Goal:** give OSCAR a coherent live representation of what is happening across the user's digital and physical environment.

Deliverables:

- World Model graph for people, places, devices, apps, projects, objects, tasks and relationships
- separation of current evidence vs historical memory
- Perception Fabric ingesting screen/accessibility state, app/device events, sensors, location, audio events and authorized camera observations
- state freshness/confidence/provenance
- fusion of phone, desktop, Edge, calendar, communication and Worker state
- Passive/Aware/Guard/Away/Sleep Sentry modes
- local rules/baselines
- importance/urgency/confidence/interruptibility scoring
- Personal Policy-aware interruption decisions
- predictive signals for obvious schedule/task/device risk where confidence can be measured
- notification/speech escalation policy
- Sunday alerts

Exit condition: OSCAR can answer “what is true now?” from a coherent live model, react to meaningful events and surface only configured, high-value interruptions.

## Slice 11 — First-run commissioning + Voice Match ◻️

**Goal:** make setup comprehensive enough for safe personalized autonomy without forcing the user through endless settings.

Deliverables:

- identity/basic interaction preferences
- small high-value Personal Policy setup with open-ended later editing by voice/chat
- call/message autonomy defaults
- meeting transcription/retention defaults
- Worker autonomy defaults
- multi-condition voice enrollment
- speaker verification profile
- authorization classes
- device/environment discovery
- service connections
- Sentry configuration
- Sunday/desktop pairing
- permission matrix
- end-to-end calibration

Exit condition: a new installation ends with verified health/permission/voice status and understandable initial policy rather than untested configuration.

## Slice 12 — Avatar / presence UI ◻️

**Goal:** turn the OSCAR character into a coherent state-driven interface.

Deliverables:

- reusable avatar component
- joystick/puck motion physics
- expression/state system
- listening/thinking/speaking choreography
- serious/Sentry states
- reduced-motion accessibility
- compact/icon variants

Exit condition: avatar motion always maps to actual OSCAR state and works across Sunday, desktop and suitable desk displays.

## Slice 13 — Executive Planner + Workers + learning / protocols ◻️

**Goal:** make OSCAR a single executive system that can create/manage delegated teammates, prioritize concurrent objectives and learn reusable procedures.

Deliverables:

- Executive Planner over Workers/Protocols/tasks
- priority/deadline/dependency/resource/risk/interruptibility model
- scheduling, parallelization, pause/pre-emption and rerouting
- delegated Worker schema/lifecycle/state
- voice/chat Worker creation/editing
- temporary, task and persistent Worker types
- Worker capability/permission/context envelope
- Worker collaboration/handoff/dependency model
- Jev self-repair/reroute/escalation loop
- simple Worker management UI
- social-media Worker reference implementation using scoped connectors/device capabilities
- procedural memory capture from successful executions
- route/tool outcome history
- reusable procedure distillation
- `SKILL.md`-style portable skill contract
- “watch me do this once” teach-by-demonstration flow for supported desktop/phone workflows
- plugin/tool discovery
- protocol schema + durable state
- routine/time/event triggers
- protocol-driven Worker creation/termination
- pause/resume/cancel
- self-created skill/routine/protocol candidate flow
- permission review for generated automation
- verification requirements
- versioning and rollback
- measurable repeated-task latency/cost improvement

Exit condition: OSCAR can coordinate multiple objectives as one executive system, create a Worker from natural language, learn or be taught a workflow, reuse it later and recover from routine problems without self-granting authority.

## Slice 14 — Kinetable + spatial/workbench + general engineering ◻️

**Goal:** connect hardware engineering, richer physical perception and specialist engineering/simulation tools.

Deliverables:

- Kinetable integration contract
- hardware project/inventory handoff
- firmware/provisioning path into OSCAR/Latch Edge
- camera-capable node path
- component/workbench telemetry
- device state correlation
- physical protocol execution
- environment/device inventory
- spatial perception experiments combining camera + sensor + World Model state
- specialist visual/engineering tool hooks
- general routing boundary for CAD, 3D, numerical simulation, diagnostics, reconstruction and optimization tools instead of trying to reimplement them inside OSCAR

Exit condition: OSCAR can route engineering work to the appropriate specialist, reason from actual workbench/environment data, correlate perception with telemetry and onboard an approved device as a capability-bearing OSCAR node.

## Slice 15 — Self-maintenance, reliability and security pass ◻️

**Goal:** prove the system can diagnose itself and behaves correctly under failure and attack-relevant conditions.

Deliverables:

- self-health model for auth, connectors, providers, device capabilities, storage and latency
- stale/broken capability detection
- safe automatic repair/rollback where confidence and permission allow
- credential rotation/revocation
- replay/idempotency checks
- Action Ledger integrity + undo/compensation tests
- audit trail
- provider/node outage tests
- partial-task recovery
- Worker retry/reroute/escalation tests
- communication-action attribution tests
- Personal Policy conflict/permission regression tests
- Voice Match spoof-resistance evaluation
- local safety tests
- rate limiting
- privacy/retention controls
- generated-skill/protocol/Worker safety tests

Exit condition: OSCAR can detect its own degraded state, repair safe failures when possible, ask for the minimum intervention otherwise, and has major failure/security modes tested rather than assumed.

## Slice 16 — Unified alpha ◻️

**Goal:** demonstrate the complete product loop.

Reference scenario:

```text
Perception/Sentry/communication/device event occurs
→ Perception Fabric updates World Model
→ OSCAR/Jev evaluates current truth + memory
→ Personal Policy + permissions applied
→ Executive Planner prioritizes objective/resources
→ retrieves live or historical context if needed
→ invokes ChatGPT/SwitchRoute if reasoning is needed
→ creates/delegates Worker when the objective warrants it
→ involves user through Sunday/desktop only when required
→ delegates specialist work to the best tool/device
→ controls safe edge action if relevant
→ Action Ledger records consequential changes
→ verifies outcome / offers undo when real compensation exists
→ stores important + procedural memory
→ improves reusable skill/protocol if appropriate
→ reports succinctly
```

Exit condition: edge + voice + communication + Sunday + desktop Interaction Runtime + World Model + Perception Fabric + Executive Planner + Action Ledger + Workers + cloud + memory/policy + learning + Sentry + Kinetable integration operate as one coherent OSCAR system.

## Post-alpha horizon — P2 domains

These are intentionally deferred until the unified alpha is coherent:

- health/wearable context with strict permission/privacy boundaries
- smart-home capability contracts
- robotics/camera/room-infrastructure contracts
- future vehicle/drone integration where safe and legally appropriate

These should plug into the same capability, World Model, policy, permission and Action Ledger abstractions rather than creating parallel architectures.

## Slice definition of done

Every slice must include:

- implementation complete for the scoped deliverable
- design remains no more complex than the current requirement justifies
- responsibilities/boundaries and authoritative state ownership are clear
- tests for important behavior and meaningful failure modes
- timeout/retry/reconnect/cancellation/idempotency behavior addressed where relevant
- explicit limitations/follow-ups
- security/safety review where relevant
- critical-path performance measured/budgeted where relevant
- README status update
- affected docs updated
- next slice clearly identified
